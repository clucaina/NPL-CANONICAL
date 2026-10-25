import {viewerToMaster} from './geo_alignment.mjs';

export const TILEPACK_SCHEMA='neurocity.local-worldmaster-tiles.v1';
export const TILE_SPAN_M=500;
export const ROLES=Object.freeze(['terrain','geo','urban','environment','driving','beach',
   'architecture','lod','palm_variants','facade','landmark','coast','mosaic','furniture','street','streetlamp']);
export const ALLOWED_TILES=Object.freeze(['r02_c00','r02_c01','r01_c01','r01_c02']);
export const ASSET_ROOT='world-master/';
const SAFE_PATH=/^(assets\/(?:selected|prefabs|source\/ASSETS\/(?:tiles|G14|G15|G17))\/[A-Za-z0-9_./-]+)\.glb$/;
export function safeTilePath(path){
  return typeof path==='string' && path.length<220 && SAFE_PATH.test(path) &&
      !path.split('/').includes('..') && !path.startsWith('/') && !path.includes('//');
}
/** Fail closed on all original mobile-GLB fallback metadata before LOD or loads.
 * A fallback must be a distinct allowlisted signed GLB. Never silently copy
 * unchecked image counts into the GPU scheduler. */
export function verifiedMosaicFallback(a){
  const f=a?.mobile_fallback;
  if(!a||a.role!=='mosaic'||!f||typeof f!=='object'||
     !safeTilePath(f.path)||f.path===a.path||
     typeof f.sha256!=='string'||!/^[a-f0-9]{64}$/.test(f.sha256)||
     !Number.isSafeInteger(f.bytes)||f.bytes<=0||f.bytes>90_000_000||
     !Number.isSafeInteger(f.triangle_estimate)||
     f.triangle_estimate<1||f.triangle_estimate>4_000_000||
     !Number.isSafeInteger(f.embedded_images)||
     f.embedded_images<0||f.embedded_images>1024)
     throw new Error('Unsupported asset source: Unsafe original V50 mobile mosaic fallback');
  return f;
}
export function tileBounds(id){
  const match=/^r(\d{2})_c(\d{2})$/.exec(id);
  if(!match||!ALLOWED_TILES.includes(id))throw new Error('Unknown recovered tile');
  const row=Number(match[1]),col=Number(match[2]);
  return Object.freeze({minX:col*500,maxX:(col+1)*500,
                        minZ:row*500,maxZ:(row+1)*500});
}
export function distanceToBounds(x,z,bounds){
  if(!Number.isFinite(x)||!Number.isFinite(z))throw new TypeError('Nonfinite coordinates');
  return Math.hypot(Math.max(bounds.minX-x,0,x-bounds.maxX),
                    Math.max(bounds.minZ-z,0,z-bounds.maxZ));
}
export function assertTileManifest(m){
  if(!m||m.schema!==TILEPACK_SCHEMA || m.crs!=='EPSG:25830' ||
     m.vertical_datum_verified!==false||m.public_redistribution_allowed!==false||
     !Array.isArray(m.tiles)||m.tiles.length<1||m.tiles.length>4)
     throw new Error('Unverified or incorrectly licensed private citypack');
  const seen=new Set();
  for(const tile of m.tiles){
    if(!tile||!ALLOWED_TILES.includes(tile.id)||seen.has(tile.id)||
        !Array.isArray(tile.assets)||tile.assets.length>100)
        throw new Error('Invalid tile ID or excessive data');
    seen.add(tile.id);
    for(const a of tile.assets){
      if(!a||!ROLES.includes(a.role)||!safeTilePath(a.path)||
          typeof a.sha256!=='string'||!/^[a-f0-9]{64}$/.test(a.sha256)||
          !Number.isSafeInteger(a.bytes)||a.bytes<=0||a.bytes>90_000_000||
          (a.role==='streetlamp'&&a.path!=='assets/prefabs/Farola_Globo_Simple_4m.glb')||
          (a.local===true&&!['terrain','geo','street','beach','coast'].includes(a.role)) ||
          (a.triangle_estimate!==undefined && (!Number.isSafeInteger(a.triangle_estimate)||a.triangle_estimate<1||a.triangle_estimate>4_000_000)) ||
          (a.embedded_images!==undefined && (!Number.isSafeInteger(a.embedded_images)||a.embedded_images<0||a.embedded_images>1024)) ||
          (a.mobile_fallback!==undefined && !a.mobile_fallback))
       throw new Error('Unsupported asset source, integrity claim or local-space transform');
      if(a.mobile_fallback!==undefined)verifiedMosaicFallback(a);
    }
  }
  return m;
}
export function planActiveTiles(manifest,viewerX,viewerZ,profile='desktop'){
  assertTileManifest(manifest);
  if(!['desktop','mobile'].includes(profile))throw RangeError('Invalid viewport profile');
  const local=viewerToMaster(viewerX,viewerZ);
  const radius=profile==='mobile'?160:340;
  const cap=profile==='mobile'?2:3;
  const entries=manifest.tiles.map(t=>({
    tile:t.id,distance:distanceToBounds(local.x,local.z,tileBounds(t.id))
  })).filter(t=>t.distance<=radius).sort((a,b)=>a.distance-b.distance||a.tile.localeCompare(b.tile));
  return Object.freeze(entries.slice(0,cap).map(o=>o.tile));
}
export function plannedLayers(tile,profile='desktop'){
  if(!tile?.assets||!['mobile','desktop'].includes(profile))throw RangeError('Invalid layer request');
  const priority={terrain:0,geo:1,mosaic:2,street:3,coast:4,beach:5,
    architecture:6,landmark:7,facade:8,palm_variants:9,streetlamp:9,urban:10,
    driving:11,environment:12,lod:13,furniture:14};
  const hasV50Furniture=tile.assets.some(a=>a.role==='furniture');
  const candidates=tile.assets.filter(a=>{
    if(profile==='desktop')return !(a.role==='streetlamp'&&hasV50Furniture);
    return !['facade','furniture'].includes(a.role);
  }).map(a=>{
    // Fail closed in direct LOD calls, even without the full manifest preflight.
    if(a.mobile_fallback!==undefined)verifiedMosaicFallback(a);
    // Original V50 4cm relief: ~105k triangles on 16m2 patch. Preserve its
    // authentic 5k-triangle PBR source GLB for mobile instead of loading both.
    if(profile==='mobile'&&a.role==='mosaic'&&a.mobile_fallback){
      const fb=verifiedMosaicFallback(a);
      return {...a,...fb,mobileV50Fallback:true,
        archaeologicalModelSource:'original_V50_PBR_not_procedural'};
    }
    return a;
  }).sort((a,b)=>(priority[a.role]??99)-(priority[b.role]??99)||a.path.localeCompare(b.path));
  // Original 2026 checkpoint: r02_c00 alone has >600k triangles. Loading
  // every old GLB on low-end mobile without LOD is NOT acceptable.
  const cap=profile==='mobile'?290_000:1_500_000;
  let triangles=0,images=0;
  const selected=[];
  for(const asset of candidates){
    // Conservative proxy for backward-compatible manifests with no audited
    // geometry metadata; regeneration populates the actual GLB counts.
    const cost=asset.triangle_estimate ?? Math.ceil(asset.bytes/20);
    const imageCost=asset.embedded_images ?? 1;
    if(profile==='mobile' && ['environment','driving','lod'].includes(asset.role))continue;
    // Enforce one exact GPU proxy budget for ALL layers (including mandatory).
    // If this excludes a required source layer, tile.ready stays false and
    // georeferenced OSM keeps rendering rather than faking a complete city.
    if(triangles+cost>cap||images+imageCost>(profile==='mobile'?30:140))continue;
    selected.push(asset);triangles+=cost;images+=imageCost;
  }
  return selected;
}
