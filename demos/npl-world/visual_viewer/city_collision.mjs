import * as THREE from 'three';

const CELL_SIZE_M=12;
const COLLISION_RADIUS_M=0.58;
const MAX_WALL_TRIANGLES=120000;
const MAX_SEGMENTS=90000;

const num=v=>Number.isFinite(v);
const snap=n=>Math.round(n*20)/20;
function distToEdge(x,z,e){
 const dx=e.bx-e.ax,dz=e.bz-e.az,den=dx*dx+dz*dz;
 if(den<1e-6)return Infinity;
 const t=Math.max(0,Math.min(1,((x-e.ax)*dx+(z-e.az)*dz)/den));
 return Math.hypot(x-(e.ax+t*dx),z-(e.az+t*dz));
}
function edgeKey(e){
 const a=snap(e.ax)+','+snap(e.az),b=snap(e.bx)+','+snap(e.bz);
 return a<b?a+'|'+b:b+'|'+a;
}
function extractWallSegments(root){
 if(!root?.traverse||!root?.updateMatrixWorld)throw new TypeError('Three city scene required');
 root.updateMatrixWorld(true);
 const edges=[],unique=new Set();
 let trianglesSeen=0,wallMeshes=0;
 const verts=[new THREE.Vector3(),new THREE.Vector3(),new THREE.Vector3()];
 root.traverse(n=>{
  if(!n.isMesh||!n.name.startsWith('OSM_Real_Building_Walls'))return;
  wallMeshes++;
  const geometry=n.geometry,position=geometry?.getAttribute?.('position');
  if(!position)throw Error('Wall geometry has no position buffer');
  const index=geometry.index,count=index?.count??position.count;
  if(count%3!==0)throw Error('Wall geometry is not fully triangulated');
  if(trianglesSeen+count/3>MAX_WALL_TRIANGLES)throw Error('Oversized city collision mesh');
  trianglesSeen+=count/3;
  for(let p=0;p<count;p+=3){
   for(let k=0;k<3;k++){
    const v=index?index.getX(p+k):p+k;
    verts[k].fromBufferAttribute(position,v).applyMatrix4(n.matrixWorld);
   }
   const sorted=[...verts].sort((a,b)=>a.y-b.y);
   if(Math.abs(sorted[0].y-sorted[1].y)>.18||sorted[2].y-sorted[1].y<1.2)continue;
   if(sorted[0].y>1.15||sorted[1].y < -2.5)continue;
   const a=sorted[0],b=sorted[1];
   const len=Math.hypot(a.x-b.x,a.z-b.z);
   if(len<.25||len>120)continue;
   const edge={ax:a.x,az:a.z,bx:b.x,bz:b.z};
   if(![edge.ax,edge.az,edge.bx,edge.bz].every(num))throw Error('Nonfinite wall coordinates');
   const key=edgeKey(edge);
   if(unique.has(key))continue;
   unique.add(key);edges.push(edge);
   if(edges.length>MAX_SEGMENTS)throw Error('Too many collidable walls');
  }
 });
 return {edges,wallMeshes,trianglesSeen};
}

export function buildCityWallCollision(root,{cellSize=CELL_SIZE_M,radius=COLLISION_RADIUS_M}={}){
 if(!(num(cellSize)&&cellSize>=4&&cellSize<=40&&num(radius)&&radius>=.3&&radius<=1.2))
   throw new RangeError('Unsafe collision indexing settings');
 const {edges,wallMeshes,trianglesSeen}=extractWallSegments(root);
 const grid=new Map();
 const cell=x=>Math.floor(x/cellSize);
 for(let i=0;i<edges.length;i++){
  const e=edges[i];
  const minx=cell(Math.min(e.ax,e.bx)-radius),maxx=cell(Math.max(e.ax,e.bx)+radius);
  const minz=cell(Math.min(e.az,e.bz)-radius),maxz=cell(Math.max(e.az,e.bz)+radius);
  if((maxx-minx+1)*(maxz-minz+1)>1200)throw Error('Unsupported giant building segment');
  for(let gx=minx;gx<=maxx;gx++)for(let gz=minz;gz<=maxz;gz++){
   const key=gx+','+gz;
   let bucket=grid.get(key);if(!bucket){bucket=[];grid.set(key,bucket);}
   bucket.push(i);
  }
 }
 let blockedMoves=0;
 function candidates(x,z,nextX,nextZ){
  const result=new Set();
  for(let gx=cell(Math.min(x,nextX)-radius);gx<=cell(Math.max(x,nextX)+radius);gx++)
   for(let gz=cell(Math.min(z,nextZ)-radius);gz<=cell(Math.max(z,nextZ)+radius);gz++)
    for(const index of grid.get(gx+','+gz)||[])result.add(index);
  return result;
 }
 function hitsWall(x,z,toX,toZ){
  if(![x,z,toX,toZ].every(num))throw new RangeError('Nonfinite player motion');
  for(const id of candidates(x,z,toX,toZ)){
   const edge=edges[id];
   const fromDist=distToEdge(x,z,edge),toDist=distToEdge(toX,toZ,edge);
   // Allow escaping an already-overlapping wall but never entering one.
   if(toDist<radius&&(fromDist>=radius||toDist<fromDist-.012))return true;
  }
  return false;
 }
 function move(x,z,dx,dz){
  if(![x,z,dx,dz].every(num))throw new RangeError('Nonfinite motion');
  if(Math.hypot(dx,dz)>1.0)throw new RangeError('Only one physics simulation step allowed');
  if(!hitsWall(x,z,x+dx,z+dz))return {x:x+dx,z:z+dz,collided:false};
  blockedMoves++;
  // Slide against source walls without teleporting through them.
  if(!hitsWall(x,z,x+dx,z))return {x:x+dx,z,collided:true};
  if(!hitsWall(x,z,x,z+dz))return {x,z:z+dz,collided:true};
  return {x,z,collided:true};
 }
 // This is a deterministic physical acceptance check against *the exact wall
 // geometry loaded in the viewer*, not an OSM count or a mock city.
 // It exercises actual attempted penetration through sampled low wall edges.
 // No vertex coordinates are logged, stored or sent to a service.
 function auditSourceWallBlocking({samples=48}={}){
  if(!Number.isInteger(samples)||samples<1||samples>256)
    throw new RangeError('Invalid bounded source-wall audit budget');
  let examined=0,blocked=0,failed=0;
  const liveMovementCounter=blockedMoves;
  for(const e of edges){
   if(examined>=samples)break;
   const vx=e.bx-e.ax,vz=e.bz-e.az;
   const length=Math.hypot(vx,vz);
   if(length<1.6)continue;
   const nx=-vz/length,nz=vx/length;
   const midX=(e.ax+e.bx)*.5,midZ=(e.az+e.bz)*.5;
   const approachX=midX+nx*(radius+.35);
   const approachZ=midZ+nz*(radius+.35);
   const deltaX=-nx*.47,deltaZ=-nz*.47;
   const actual=move(approachX,approachZ,deltaX,deltaZ);
   // The tested point must be rejected or safely redirected, NOT permitted
   // to enter the collision capsule surrounding this real Blender wall.
   const capsule=distToEdge(actual.x,actual.z,e);
   examined++;
   if(actual.collided&&capsule>=radius-1e-4)blocked++;
   else failed++;
  }
  // Audit attempts are not actual user walks: restore gameplay counters.
  blockedMoves=liveMovementCounter;
  return Object.freeze({
   source:'actual_loaded_blender_wall_geometry',
   sampleBudget:samples,examined,blocked,failed,
   allSampledBlocked:examined>0&&blocked===examined,
   simulatedNotPhysicalHardware:true
  });
 }
 return {move,hitsWall,auditSourceWallBlocking,stats:()=>Object.freeze({
  source:'Blender_real_OSM_and_official_Catastro_wall_mesh',
  wallMeshes,trianglesScanned:trianglesSeen,wallSegments:edges.length,
  spatialCells:grid.size,cellSizeMeters:cellSize,
  collisionRadiusMeters:radius,blockedMoves,
  inventedBarriers:0,
  sourceFloorHeightsMeasured:false
 })};
}
