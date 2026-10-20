import * as THREE from 'three';

/**
 * World-projected Mediterranean stucco on already-mapped OSM wall geometry.
 * All paint and stone are artistic, not photogrammetry or surveyed materials.
 * No buildings, brands, real shop occupants, vertices or source data invented.
 */
export const FACADE_SURFACE_SOURCE='OSM_BUILDING_WALLS_ARTISTIC_MEDITERRANEAN_STUCCO';
export function isSourceBuildingWall(name){
 return typeof name==='string'&&(name==='OSM_Real_Building_Walls_UNTEXTURED'||
    name.startsWith('OSM_Real_Building_Walls_UNTEXTURED.'));
}
export function enhanceMappedBuildingFacades(city,{tier='desktop'}={}){
 if(!city?.traverse)throw TypeError('Real OSM 3D city scene required');
 if(!['desktop','mobile'].includes(tier))throw RangeError('Invalid facade LOD');
 const entries=[];
 city.traverse(mesh=>{
  if(!mesh.isMesh||!isSourceBuildingWall(mesh.name))return;
  const original=Array.isArray(mesh.material)?mesh.material:[mesh.material];
  const decorated=original.map(source=>{
    if(!source?.isMeshStandardMaterial)return source;
    const material=source.clone();
    material.name='NEUROCITY_ART_STUCCO_ON_ACTUAL_OSM_WALLS';
    material.color=new THREE.Color(0xffffff);
    material.roughness=.90;material.metalness=0;
    const former=material.onBeforeCompile;
    material.onBeforeCompile=(shader,renderer)=>{
      former?.(shader,renderer);
      const hook='#include <color_fragment>',worldHook='#include <worldpos_vertex>';
      if(!shader.vertexShader.includes(worldHook)||!shader.fragmentShader.includes(hook))
        throw Error('Three.js facade shader source changed');
      shader.vertexShader='varying vec3 ncFacadeWorld;\n'+shader.vertexShader
        .replace(worldHook,worldHook+'\n ncFacadeWorld=(modelMatrix*vec4(transformed,1.0)).xyz;');
      shader.fragmentShader='varying vec3 ncFacadeWorld;\n'+shader.fragmentShader
        .replace(hook,hook+'\n'+[
         'vec3 pp=ncFacadeWorld;',
         'vec2 block=floor(vec2(pp.x*.047+pp.z*.011,pp.z*.052-pp.x*.009));',
         'float palette=fract(sin(dot(block,vec2(127.1,311.7)))*43758.54);',
         'vec3 limestone=mix(vec3(.91,.85,.74),vec3(.78,.82,.78),smoothstep(.18,.82,palette));',
         'vec3 plaster=mix(limestone,vec3(.86,.73,.65),smoothstep(.77,1.0,palette)*.37);',
         'float grain=fract(sin(dot(floor(pp.xy*16.0+pp.z*.11),vec2(19.53,73.17)))*38971.232);',
         'float plinth=1.0-smoothstep(1.15,1.8,pp.y);',
         'vec3 stone=mix(vec3(.54,.51,.45),vec3(.64,.61,.54),grain*.5);',
         'float cornice=1.0-smoothstep(.045,.12,abs(mod(pp.y+.025,3.15)-.075));',
         'vec3 ceramic=plaster*(.925+.13*grain);',
         'ceramic=mix(ceramic,stone,plinth*.68);',
         'ceramic=mix(ceramic,vec3(.80,.78,.70),cornice*.12);',
         'diffuseColor.rgb*=ceramic;'
        ].join('\n'));
    };
    material.customProgramCacheKey=()=> 'neurocity-osm-stucco-'+tier+'-v2';
    entries.push({mesh,source,material});
    return material;
  });
  mesh.material=Array.isArray(mesh.material)?decorated:decorated[0];
 });
 return {
  source:FACADE_SURFACE_SOURCE,meshCount:new Set(entries.map(x=>x.mesh)).size,
  adjustedMaterials:entries.length,extraVertices:0,
  geometricFootprintsPreserved:true,textureDownloads:0,
  colorsSurveyed:false,photoMatched:false,shopsFabricated:0,
  restore(){
   for(const entry of entries){
    const originals=Array.isArray(entry.mesh.material)?entry.mesh.material:[entry.mesh.material];
    const index=originals.indexOf(entry.material);
    if(index<0)continue;
    originals[index]=entry.source;
    entry.mesh.material=Array.isArray(entry.mesh.material)?originals:originals[0];
    entry.material.dispose();
   }
  }
 };
}
