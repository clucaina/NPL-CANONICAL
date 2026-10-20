import * as THREE from 'three';
import {matrixElementsForTile} from './geo_alignment.mjs';
import {tileBounds,ALLOWED_TILES} from './city_tiles.mjs';

// The archive's architecture is sometimes ONE mesh for many separate blocks.
// Tile-level AABB masking removes unrelated OSM buildings up to 500 m away.
// Rasterize the verified world-space triangles at ~1.95m/cell instead.
// This is a conservative visual mask, NOT Catastro, LiDAR or source licensing.
export const ARCH_CELLS=256;
const MAX_TRIANGLES=250000;
const MAX_SPAN_CELLS=12000;
const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
const finite=(x)=>Number.isFinite(x);
function isInside(x,z,a,b,c){
 const v=(p,q,r)=>(q.x-p.x)*(r.z-p.z)-(q.z-p.z)*(r.x-p.x);
 const p={x,z},d1=v(a,b,p),d2=v(b,c,p),d3=v(c,a,p);
 return !(d1<0||d2<0||d3<0) || !(d1>0||d2>0||d3>0);
}
function paintLine(data,x0,y0,x1,y1){
 let dx=x1-x0,dy=y1-y0;
 const steps=Math.max(1,Math.ceil(Math.hypot(dx,dy)*2));
 if(steps>3500)return;
 for(let i=0;i<=steps;i++){
  const x=Math.floor(x0+dx*i/steps),y=Math.floor(y0+dy*i/steps);
  if(x>=0&&x<ARCH_CELLS&&y>=0&&y<ARCH_CELLS)
   data[y*ARCH_CELLS+x]=255;
 }
}
export function architectureMaskFromLoadedGLB(tileGroup,tileId){
 if(!ALLOWED_TILES.includes(tileId)||!tileGroup?.traverse||!tileGroup?.updateMatrixWorld)
  throw new TypeError('Source G19 tile and verified ID required');
 tileGroup.updateMatrixWorld(true);
 const bb=tileBounds(tileId);
 const inverse=new THREE.Matrix4().fromArray(matrixElementsForTile(tileId)).invert();
 const data=new Uint8Array(ARCH_CELLS*ARCH_CELLS);
 const v=[new THREE.Vector3(),new THREE.Vector3(),new THREE.Vector3()];
 let triangles=0,meshes=0,skipped=0;
 // Only loaded authenticated architecture, never terrain/mosaic/prop models.
 tileGroup.traverse(n=>{
  if(!n.isMesh||!n.visible)return;
  let p=n.parent,belongs=false;
  while(p&&p!==tileGroup){if(p.name==='MASTER_architecture'){belongs=true;break;}p=p.parent;}
  if(!belongs)return;
  meshes++;
  const pos=n.geometry?.getAttribute?.('position'),idx=n.geometry?.index;
  if(!pos)throw Error('G19 architecture mesh missing coordinates');
  const count=idx?.count??pos.count;
  if(count%3!==0||triangles+count/3>MAX_TRIANGLES)
   throw Error('Oversized/non-triangulated G19 architecture');
  triangles+=count/3;
  for(let i=0;i<count;i+=3){
   for(let j=0;j<3;j++){
    const ix=idx?idx.getX(i+j):i+j;
    v[j].fromBufferAttribute(pos,ix).applyMatrix4(n.matrixWorld).applyMatrix4(inverse);
   }
   if(!v.every(p=>finite(p.x)&&finite(p.z)&&finite(p.y)))throw Error('Nonfinite architecture vertices');
   const p=v.map(t=>({x:(t.x-bb.minX)*ARCH_CELLS/500,z:(t.z-bb.minZ)*ARCH_CELLS/500}));
   const minX=clamp(Math.floor(Math.min(...p.map(a=>a.x))-1),0,ARCH_CELLS-1);
   const maxX=clamp(Math.ceil(Math.max(...p.map(a=>a.x))+1),0,ARCH_CELLS-1);
   const minZ=clamp(Math.floor(Math.min(...p.map(a=>a.z))-1),0,ARCH_CELLS-1);
   const maxZ=clamp(Math.ceil(Math.max(...p.map(a=>a.z))+1),0,ARCH_CELLS-1);
   if(maxX<minX||maxZ<minZ)continue;
   if((maxX-minX+1)*(maxZ-minZ+1)>MAX_SPAN_CELLS){skipped++;continue;}
   const area=Math.abs((p[1].x-p[0].x)*(p[2].z-p[0].z)-
                       (p[1].z-p[0].z)*(p[2].x-p[0].x));
   if(area<.1){
    paintLine(data,p[0].x,p[0].z,p[1].x,p[1].z);
    paintLine(data,p[1].x,p[1].z,p[2].x,p[2].z);
    continue;
   }
   for(let zz=minZ;zz<=maxZ;zz++)for(let xx=minX;xx<=maxX;xx++)
    if(isInside(xx+.5,zz+.5,p[0],p[1],p[2]))data[zz*ARCH_CELLS+xx]=255;
  }
 });
 // Dilation 1 cell (~2m) accounts for sparse roof/wall seams and approx CRS
 // viewer->master discrepancy, without hiding an entire 500m grid.
 const dilated=data.slice();
 for(let z=1;z<ARCH_CELLS-1;z++)for(let x=1;x<ARCH_CELLS-1;x++){
  const k=z*ARCH_CELLS+x;if(!data[k])continue;
  for(let dz=-1;dz<=1;dz++)for(let dx=-1;dx<=1;dx++)
   dilated[k+dz*ARCH_CELLS+dx]=255;
 }
 let coveredCells=0;for(const n of dilated)if(n)coveredCells++;
 return Object.freeze({tileId,cells:ARCH_CELLS,data:dilated,coveredCells,sourceMeshes:meshes,
  sourceTriangles:triangles,skippedTriangles:skipped,
  certifiedGroundDatum:false,sourcePhotogrammetryCertified:false,
  source:'SIGNED_G19_GLTF_RENDERED_ARCHITECTURE'});
}
