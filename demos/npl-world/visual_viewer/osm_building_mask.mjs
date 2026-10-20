import * as THREE from 'three';
import {A} from './geo_alignment.mjs';
import {tileBounds,ALLOWED_TILES} from './city_tiles.mjs';

/** Retain georeferenced aerial PNOA and asphalt everywhere, suppress only
 * overlapping old OSM wall/roof pixels where recovered 3D tiles are ready. */
const NAMES=['OSM_Real_Building_Walls_UNTEXTURED','OSM_Real_Building_Roofs'];
const det=A.xx*A.zz-A.xz*A.zx;
const f=x=>Number(x).toFixed(10);
const glslProjection='vec2 ncViewerToMaster(vec2 p){'+
  'vec2 d=p-vec2('+f(A.tx)+','+f(A.tz)+');'+
  'return vec2(('+f(A.zz)+'*d.x-'+f(A.xz)+'*d.y)/'+f(det)+
  ',(-'+f(A.zx)+'*d.x+'+f(A.xx)+'*d.y)/'+f(det)+');}';
export function maskableOSMName(name){
 return typeof name==='string'&&NAMES.some(n=>name===n||name.startsWith(n+'.'));
}
export function installCoveredOSMMask(city){
 if(!city?.traverse)throw TypeError('Actual Three OSM scene missing');
 const materials=[];
 let maskedMeshes=0;
 city.traverse(mesh=>{
   if(!mesh.isMesh||!maskableOSMName(mesh.name))return;
   const source=Array.isArray(mesh.material)?mesh.material:[mesh.material];
   const decorated=source.map(raw=>{
     const material=raw.clone();
     const count={value:0};
     const vectors=Array.from({length:4},()=>new THREE.Vector4());
     const regions={value:vectors};
     const previous=material.onBeforeCompile;
     material.onBeforeCompile=shader=>{
       previous?.(shader);
       shader.uniforms.ncMasterTileCount=count;
       shader.uniforms.ncMasterTileBoxes=regions;
       const v='#include <worldpos_vertex>';
       const q='#include <clipping_planes_fragment>';
       if(!shader.vertexShader.includes(v)||!shader.fragmentShader.includes(q))
         throw Error('Three r169 shader includes changed');
       shader.vertexShader='varying vec2 ncMasterWorldXZ;\n'+
         shader.vertexShader.replace(v,v+'\n ncMasterWorldXZ=(modelMatrix*vec4(transformed,1.0)).xz;');
       shader.fragmentShader='varying vec2 ncMasterWorldXZ;\n'+
         'uniform float ncMasterTileCount;\n'+
         'uniform vec4 ncMasterTileBoxes[4];\n'+glslProjection+'\n'+
         shader.fragmentShader.replace(q,q+'\n'+
         'vec2 ncP=ncViewerToMaster(ncMasterWorldXZ);\n'+
         'for(int i=0;i<4;i++){\n'+
         'if(float(i)>=ncMasterTileCount)break;\n'+
         'vec4 box=ncMasterTileBoxes[i];\n'+
         'if(ncP.x>=box.x&&ncP.x<=box.y&&ncP.y>=box.z&&ncP.y<=box.w)discard;\n'+
         '}');
     };
     material.customProgramCacheKey=()=> 'neurocity-covered-real-osm-v1';
     materials.push({material,raw,count,vectors});
     return material;
   });
   mesh.material=Array.isArray(mesh.material)?decorated:decorated[0];
   maskedMeshes++;
 });
 let covered=[];
 return {
   update(ids){
     if(!Array.isArray(ids)||ids.length>4||
         ids.some(x=>!ALLOWED_TILES.includes(x))||new Set(ids).size!==ids.length)
       throw new Error('Untrusted tile coverage');
     covered=ids.slice();
     for(const item of materials){
       item.count.value=covered.length;
       for(let i=0;i<4;i++){
         const bb=i<covered.length?tileBounds(covered[i]):null;
         item.vectors[i].set(bb?.minX??0,bb?.maxX??0,bb?.minZ??0,bb?.maxZ??0);
       }
     }
     return this.status();
   },
   status(){return {coveredTiles:covered.slice(),maskableOSMMeshes:maskedMeshes,
     pnOAerialPreserved:true,osmAsphaltPreserved:true,buildingClippingOnly:true};},
   restore(){
     this.update([]);
     city.traverse(mesh=>{
       if(!mesh.isMesh||!maskableOSMName(mesh.name))return;
       const current=Array.isArray(mesh.material)?mesh.material:[mesh.material];
       const original=current.map(mat=>materials.find(x=>x.material===mat)?.raw??mat);
       mesh.material=Array.isArray(mesh.material)?original:original[0];
     });
     materials.forEach(x=>x.material.dispose());
   }
 };
}
