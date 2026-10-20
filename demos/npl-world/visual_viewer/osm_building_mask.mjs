import * as THREE from 'three';
import {A} from './geo_alignment.mjs';
import {tileBounds,ALLOWED_TILES} from './city_tiles.mjs';
import {ARCH_CELLS} from './g19_architecture_coverage.mjs';

/** Retain georeferenced aerial PNOA and asphalt everywhere, suppress only
 * overlapping old OSM wall/roof pixels where recovered 3D tiles are ready. */
const NAMES=['OSM_Real_Building_Walls_UNTEXTURED','OSM_Real_Building_Roofs'];
const det=A.xx*A.zz-A.xz*A.zx;
const f=x=>Number(x).toFixed(10);
const coveredOrId=(ids,id)=>typeof id==='string'&&ids.includes(id);
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
 // Four 256x256 byte occupancy layers, packed in a single 512x512 texture.
 // Missing geometry is transparent by default: never hide OSM for empty tiles.
 const atlasBytes=new Uint8Array(ARCH_CELLS*2*ARCH_CELLS*2*4);
 const atlas=new THREE.DataTexture(atlasBytes,ARCH_CELLS*2,ARCH_CELLS*2,THREE.RGBAFormat);
 atlas.magFilter=THREE.NearestFilter;atlas.minFilter=THREE.NearestFilter;
 atlas.wrapS=THREE.ClampToEdgeWrapping;atlas.wrapT=THREE.ClampToEdgeWrapping;
 atlas.generateMipmaps=false;atlas.flipY=false;atlas.needsUpdate=true;
 let coveragePixels=0;
 let maskedMeshes=0;
 city.traverse(mesh=>{
   if(!mesh.isMesh||!maskableOSMName(mesh.name))return;
   const source=Array.isArray(mesh.material)?mesh.material:[mesh.material];
   const decorated=source.map(raw=>{
     const material=raw.clone();
     const count={value:0};
     const vectors=Array.from({length:4},()=>new THREE.Vector4());
     const regions={value:vectors};
     const previous=raw.onBeforeCompile;
     material.onBeforeCompile=shader=>{
       previous?.(shader);
       shader.uniforms.ncMasterTileCount=count;
       shader.uniforms.ncMasterTileBoxes=regions;
       shader.uniforms.ncArchitectureAtlas={value:atlas};
       const v='#include <worldpos_vertex>';
       const q='#include <clipping_planes_fragment>';
       if(!shader.vertexShader.includes(v)||!shader.fragmentShader.includes(q))
         throw Error('Three r169 shader includes changed');
       shader.vertexShader='varying vec2 ncMasterWorldXZ;\n'+
         shader.vertexShader.replace(v,v+'\n ncMasterWorldXZ=(modelMatrix*vec4(transformed,1.0)).xz;');
       shader.fragmentShader='varying vec2 ncMasterWorldXZ;\n'+
         'uniform float ncMasterTileCount;\n'+
         'uniform vec4 ncMasterTileBoxes[4];\n'+
         'uniform sampler2D ncArchitectureAtlas;\n'+glslProjection+'\n'+
         shader.fragmentShader.replace(q,q+'\n'+
         'vec2 ncP=ncViewerToMaster(ncMasterWorldXZ);\n'+
         'for(int i=0;i<4;i++){\n'+
         'if(float(i)>=ncMasterTileCount)break;\n'+
         'vec4 box=ncMasterTileBoxes[i];\n'+
         'if(ncP.x>=box.x&&ncP.x<box.y&&ncP.y>=box.z&&ncP.y<box.w){\n'+
         'vec2 cell=(ncP-vec2(box.x,box.z))/vec2(box.y-box.x,box.w-box.z);\n'+
         'vec2 atlasUV=(vec2(mod(float(i),2.0),floor(float(i)/2.0))+cell)*0.5;\n'+
         'if(texture2D(ncArchitectureAtlas,atlasUV).r>0.5)discard;\n'+
         '}\n'+
         '}');
     };
     material.customProgramCacheKey=()=> 'neurocity-covered-real-osm-real-triangle-occupancy-v2';
     materials.push({material,raw,count,vectors});
     return material;
   });
   mesh.material=Array.isArray(mesh.material)?decorated:decorated[0];
   maskedMeshes++;
 });
 let covered=[];
 return {
   update(ids,geometryMasks=[]){
     if(!Array.isArray(ids)||ids.length>4||
         ids.some(x=>!ALLOWED_TILES.includes(x))||new Set(ids).size!==ids.length)
       throw new Error('Untrusted tile coverage');
     if(!Array.isArray(geometryMasks)||geometryMasks.length>4||
        geometryMasks.some(m=>!m||!coveredOrId(ids,m.tileId)||m.cells!==ARCH_CELLS||
          !(m.data instanceof Uint8Array)||m.data.length!==ARCH_CELLS*ARCH_CELLS)||
        new Set(geometryMasks.map(m=>m.tileId)).size!==geometryMasks.length)
       throw new Error('Untrusted or unavailable source geometry mask');
     covered=ids.slice();
     atlasBytes.fill(0);coveragePixels=0;
     for(const m of geometryMasks){
       const i=covered.indexOf(m.tileId),ox=(i%2)*ARCH_CELLS,oz=Math.floor(i/2)*ARCH_CELLS;
       for(let z=0;z<ARCH_CELLS;z++)for(let x=0;x<ARCH_CELLS;x++){
         const strength=m.data[z*ARCH_CELLS+x];if(!strength)continue;
         atlasBytes[4*((oz+z)*ARCH_CELLS*2+ox+x)]=255;coveragePixels++;
       }
     }
     atlas.needsUpdate=true;
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
     pnOAerialPreserved:true,osmAsphaltPreserved:true,buildingClippingOnly:true,
     geometryOccupancyPixels:coveragePixels,wholeTileClipping:false};},
   restore(){
     this.update([]);
     city.traverse(mesh=>{
       if(!mesh.isMesh||!maskableOSMName(mesh.name))return;
       const current=Array.isArray(mesh.material)?mesh.material:[mesh.material];
       const original=current.map(mat=>materials.find(x=>x.material===mat)?.raw??mat);
       mesh.material=Array.isArray(mesh.material)?original:original[0];
     });
     materials.forEach(x=>x.material.dispose());atlas.dispose();
   }
 };
}
