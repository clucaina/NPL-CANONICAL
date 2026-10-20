import {viewerToMaster,matrixElementsForTile} from './geo_alignment.mjs';

export const PHYSICAL_SOURCE='G13_G16_USER_ARCHIVED_2M_PROVISIONAL';
export const PHYSICAL_STEP_M=2;
export const PHYSICAL_TILE_CELLS=251;
export const PHYSICAL_WALKABLE=Object.freeze([1,2,3,4]);
export const PHYSICAL_TILES=Object.freeze([
 'r00_cm01','r00_c00','r00_c01','r00_c02',
 'r01_cm01','r01_c00','r01_c01','r01_c02',
 'r02_c00','r02_c01','r03_c00','r03_c01'
]);
const allowed=new Set(PHYSICAL_TILES),walkable=new Set(PHYSICAL_WALKABLE);
function tileId(x,z){
 if(!Number.isFinite(x)||!Number.isFinite(z))return null;
 const row=Math.floor(z/500),col=Math.floor(x/500);
 const result='r'+String(row).padStart(2,'0')+'_'+(col<0?'cm'+String(-col).padStart(2,'0'):'c'+String(col).padStart(2,'0'));
 return allowed.has(result)?result:null;
}
export function sourceTileId(x,z){return tileId(x,z);}
export function decodePhysicalGrid(raw,expectedId){
 if(!raw || !allowed.has(expectedId) ||raw.tile!==expectedId||raw.step!==2||
    raw.count!==PHYSICAL_TILE_CELLS||!Array.isArray(raw.originLocal)||
    raw.originLocal.length!==2)throw Error('Unexpected physical tile grid contract');
 const match=/^r(\d\d)_(?:c(\d\d)|cm(\d\d))$/.exec(expectedId);
 if(!match)throw Error('Invalid original source tile id');
 const ix=match[2]!==undefined?Number(match[2]):-Number(match[3]);
 const row=Number(match[1]);
 if(raw.originLocal[0]!==ix*500||raw.originLocal[1]!==row*500)
   throw Error('Physical grid coordinate origin mismatch');
 if(!Array.isArray(raw.surface)||raw.surface.length!==251 ||
    !Array.isArray(raw.height)||raw.height.length!==251)
   throw Error('Incomplete physical grid');
 const surface=new Uint8Array(251*251);
 const height=new Float32Array(251*251);
 let unknown=0,water=0,buildings=0;
 for(let z=0;z<251;z++){
   const rows=[raw.surface[z],raw.height[z]];
   if(rows.some(r=>!Array.isArray(r)||r.length!==251))
     throw Error('Malformed physical grid rows');
   for(let x=0;x<251;x++){
     const index=z*251+x,code=rows[0][x],h=rows[1][x];
     if(!Number.isInteger(code)||code<0||code>7)throw Error('Unknown physical surface type');
     if(h!==null&&(!Number.isFinite(h)||Math.abs(h)>2500))
       throw Error('Impossible elevation field');
     surface[index]=code;height[index]=h===null?NaN:h;
     if(code===0)unknown++;
     if(code===6)water++;
     if(code===7)buildings++;
   }
 }
 return {tile:expectedId,x0:raw.originLocal[0],z0:raw.originLocal[1],
  step:2,count:251,surface,height,unknown,water,buildings,
  verifiedElevationDatum:false,simulatedBathymetryNotTrusted:true};
}
function projectionMatrixForTile(tile){
 const e=matrixElementsForTile(tile);
 const det=e[0]*e[10]-e[8]*e[2];
 if(Math.abs(det)<1e-6)throw Error('Noninvertible PROJ tile transform');
 return {xx:e[0],xz:e[8],zx:e[2],zz:e[10],tx:e[12],tz:e[14],det};
}
function inversePoint(x,z,tile){
 const m=projectionMatrixForTile(tile),dx=x-m.tx,dz=z-m.tz;
 return {x:(m.zz*dx-m.xz*dz)/m.det,z:(m.xx*dz-m.zx*dx)/m.det};
}
function sampleTile(grid,x,z){
 const fx=(x-grid.x0)/2,fz=(z-grid.z0)/2;
 if(fx<0||fx>250||fz<0||fz>250)return null;
 const ix=Math.round(fx),iz=Math.round(fz),k=iz*251+ix;
 return {code:grid.surface[k],height:Number.isFinite(grid.height[k])?grid.height[k]:null,
  grid:grid.tile,source:PHYSICAL_SOURCE};
}
/** Physical source has 12 sectors, while G19 visual archive has only four. */
export class RecoveredPhysicalAtlas{
 constructor({base='./world-master/geo/data',maxTiles=5}={}){
  if(base!=='./world-master/geo/data'||!Number.isInteger(maxTiles)||maxTiles<2||maxTiles>8)
   throw Error('Local user-owned source only; invalid physical cache');
  this.base=base;this.maxTiles=maxTiles;this.cache=new Map();this.pending=new Map();
  this.diagnostics={loaded:0,hashRejected:0,unknown:0,blocked:0,accepted:0,errors:[]};
  this.index=null;this.sourceIds=new Map();this.disposed=false;
 }
 async initialize(){
  if(this.disposed)throw Error('Physical atlas disposed');
  const response=await fetch('./world-master/SOURCE_SIDECARS_INDEX.json',{credentials:'omit',cache:'no-store'});
  if(!response.ok)throw Error('Source provenance index missing');
  const report=await response.json();
  if(report.original_files_modified>0 || report.private_real_workers_or_patients===true)
   throw Error('Untrusted source archive provenance');
  const entries=report.signed_source_files_recovered_in_sidecars;
  if(!Array.isArray(entries))throw Error('Signed 2m source manifest missing');
  for(const item of entries){
   if(!item || !/^geo\/data\/physical_r\d\d_(?:c|cm)\d\d\.json$/.test(item.path) ||
      !Number.isSafeInteger(item.bytes)||item.bytes<1000||item.bytes>4_000_000||
      !/^[a-f0-9]{64}$/.test(item.sha256))continue;
   const id=item.path.slice('geo/data/physical_'.length,-'.json'.length);
   if(allowed.has(id))this.sourceIds.set(id,{bytes:item.bytes,sha256:item.sha256});
  }
  if(this.sourceIds.size!==PHYSICAL_TILES.length)throw Error('Not all 12 source rasters signed');
  this.index=true;return this.status();
 }
 _remember(id,grid){
  this.cache.delete(id);this.cache.set(id,grid);
  while(this.cache.size>this.maxTiles)this.cache.delete(this.cache.keys().next().value);
  this.diagnostics.loaded=this.cache.size;
 }
 async load(id){
  if(this.disposed||!this.index||!allowed.has(id)||!this.sourceIds.has(id))
   throw Error('Unavailable physical source');
  if(this.cache.has(id)){const g=this.cache.get(id);this._remember(id,g);return g;}
  if(this.pending.has(id))return this.pending.get(id);
  const pending=(async()=>{
    const meta=this.sourceIds.get(id);
    const path=this.base+'/physical_'+id+'.json';
    const uri=new URL(path,document.baseURI);
    if(uri.origin!==location.origin)throw Error('Cross origin physical source forbidden');
    const response=await fetch(uri.href,{credentials:'omit',cache:'force-cache'});
    if(!response.ok)throw Error('Missing original 2m physical tile');
    const bytes=await response.arrayBuffer();
    if(bytes.byteLength!==meta.bytes)throw Error('Original physical bytes length mismatch');
    if(!globalThis.crypto?.subtle?.digest)throw Error('No WebCrypto SHA256 verification');
    const digest=new Uint8Array(await crypto.subtle.digest('SHA-256',bytes));
    const sha=Array.from(digest,x=>x.toString(16).padStart(2,'0')).join('');
    if(sha!==meta.sha256){this.diagnostics.hashRejected++;throw Error('Physical SHA256 mismatch');}
    const raw=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes));
    const decoded=decodePhysicalGrid(raw,id);
    if(!this.disposed)this._remember(id,decoded);
    return decoded;
  })().catch(error=>{
    this.diagnostics.errors.push({tile:id,reason:String(error?.message||error).slice(0,130)});
    if(this.diagnostics.errors.length>12)this.diagnostics.errors.shift();
    throw error;
  }).finally(()=>this.pending.delete(id));
  this.pending.set(id,pending);return pending;
 }
 async prefetch(viewerX,viewerZ){
  if(!this.index||this.disposed)return this.status();
  const center=viewerToMaster(viewerX,viewerZ);
  const locations=[[0,0],[320,0],[-320,0],[0,320],[0,-320]];
  const ids=[...new Set(locations.map(([dx,dz])=>tileId(center.x+dx,center.z+dz)).filter(Boolean))];
  // Prefetch without exposing any personal location to the network, local files only.
  await Promise.allSettled(ids.map(id=>this.load(id)));
  return this.status();
 }
 sampleMaster(x,z){
  const id=tileId(x,z);if(!id)return null;
  const g=this.cache.get(id);return g?sampleTile(g,x,z):null;
 }
 sampleViewer(x,z){
  const approx=viewerToMaster(x,z);
  const candidates=[tileId(approx.x,approx.z),
    tileId(approx.x-1,approx.z),tileId(approx.x+1,approx.z),
    tileId(approx.x,approx.z-1),tileId(approx.x,approx.z+1)].filter(Boolean);
  for(const id of new Set(candidates)){
    const grid=this.cache.get(id);if(!grid)continue;
    const corrected=inversePoint(x,z,id);
    const result=sampleTile(grid,corrected.x,corrected.z);
    if(result)return result;
  }
  return null;
 }
 canOccupy(x,z,{radius=.32,from=null,maxStep=.64}={}){
  if(!Number.isFinite(x)||!Number.isFinite(z)||!Number.isFinite(radius) ||
     radius<.1||radius>1.3)throw RangeError('Invalid pedestrian query');
  const samples=[[0,0],[radius,0],[-radius,0],[0,radius],[0,-radius]]
    .map(([dx,dz])=>this.sampleViewer(x+dx,z+dz));
  // Missing grids may NOT be interpreted as mapped free ground. Preserve
  // the existing OSM controller as a declared, uncertified fallback instead.
  if(samples.some(s=>!s||s.height===null)){
    this.diagnostics.unknown++;return {allowed:null,reason:'PHYSICAL_SOURCE_UNAVAILABLE'};
  }
  if(samples.some(s=>!walkable.has(s.code))){
    this.diagnostics.blocked++;return {allowed:false,reason:'WATER_BUILDING_OR_UNMAPPED'};
  }
  const heights=samples.map(s=>s.height);
  if(Math.max(...heights)-Math.min(...heights)>Math.max(.75,radius*1.1)){
    this.diagnostics.blocked++;return {allowed:false,reason:'STEEP_OR_DISCONTINUOUS'};
  }
  if(from){
    const previous=this.sampleViewer(from.x,from.z);
    if(previous?.height!==null&&previous?.height!==undefined &&
       Math.abs(heights[0]-previous.height)>maxStep){
      this.diagnostics.blocked++;return {allowed:false,reason:'STEP_TOO_HIGH'};
    }
  }
  this.diagnostics.accepted++;
  return {allowed:true,reason:'PROVISIONAL_GEO_SURFACE',surface:samples[0].code,
    physicalHeightProvisional:heights[0],tile:samples[0].grid};
 }
 /** A normalized swept capsule root check; both axes can slide if blocked. */
 move(current,dx,dz,{radius=.32,fallbackCollision=null}={}){
  // Optional safety net from source wall segments ALREADY loaded by Gameplay.
  // This never grants access where signed G13 says the surface is blocked.
  if(fallbackCollision!==null&&typeof fallbackCollision!=='function')
    throw TypeError('Fallback collision must be a synchronous wall query');
  if(!current||![current.x,current.z,dx,dz].every(Number.isFinite))
    throw TypeError('Bad movement vector');
  const distance=Math.hypot(dx,dz),n=Math.max(1,Math.ceil(distance/.22));
  const position={x:current.x,z:current.z};
  let blocked=0,fallback=0,wallFallbackChecks=0,wallFallbackBlocks=0,unverifiedFallback=0;
  for(let i=0;i<n;i++){
    const x=dx/n,z=dz/n;
    const move=(a,b)=>{
      // Zero-vector cannot count as successful obstacle sliding: otherwise
      // frontal collision is silently reported as movement along the wall.
      if(Math.abs(a)+Math.abs(b)<1e-10)return false;
      const next={x:position.x+a,z:position.z+b};
      const check=this.canOccupy(next.x,next.z,{radius,from:position});
      if(check.allowed===false)return false;
      if(check.allowed===null){
        fallback++;
        if(fallbackCollision){
          wallFallbackChecks++;
          const hit=fallbackCollision(position.x,position.z,next.x,next.z);
          if(typeof hit!=='boolean')throw TypeError('Wall fallback must return a boolean');
          if(hit){wallFallbackBlocks++;return false;}
        }else{
          // Preserve historical movement when no genuine source-wall geometry
          // exists, but NEVER misreport it as a certified pass.
          unverifiedFallback++;
        }
      }
      position.x=next.x;position.z=next.z;
      return true;
    };
    if(move(x,z))continue;
    if(move(x,0)||move(0,z))continue;
    blocked++;
  }
  return {x:position.x,z:position.z,blockedSubsteps:blocked,
    fallbackSubsteps:fallback,source:PHYSICAL_SOURCE,
    wallFallbackChecks,wallFallbackBlocks,unverifiedFallbackSubsteps:unverifiedFallback,
    wallFallbackAvailable:!!fallbackCollision,
    verifiedVerticalDatum:false,swept:true};
 }
 status(){
  return {source:PHYSICAL_SOURCE,loadedTiles:[...this.cache.keys()],
    totalSignedTiles:this.sourceIds.size,maxCachedTiles:this.maxTiles,
    verifiedVerticalDatum:false,offlineOnly:true,drawsNoImagery:true,
    physicalCoverageCertified:false,
    diagnostics:{...this.diagnostics,errors:this.diagnostics.errors.slice()}};
 }
 dispose(){this.disposed=true;this.pending.clear();this.cache.clear();}
}
