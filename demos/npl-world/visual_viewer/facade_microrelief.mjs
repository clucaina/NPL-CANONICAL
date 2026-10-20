/** Microrelief on existing PUBLIC OSM wall material, not a new facade/building.

   A small, screen-derivative PBR normal perturbation: closer-up plaster catches
   sun differently at each point, with no texture download, no UV requirement,
   no new vertices, no new architecture and no private avatar/GLB access.

   IMPORTANT: This is plausible ARTISTIC plaster, never a survey or image match.
 */
import {isSourceBuildingWall} from './facade_stucco.mjs';

export const MICRORELIEF_SOURCE='OSM_ACTUAL_WALLS_PROCEDURAL_PBR_DETAIL_NOT_SURVEYED';
export const MICRORELIEF_VERSION='npl-wall-pbr-2026-10-20-v1';
export const MICRORELIEF_LIMITS=Object.freeze({
 desktop:Object.freeze({normalStrength:.12,detailScale:18.0,roughnessMin:.73}),
 mobile:Object.freeze({normalStrength:.035,detailScale:10.0,roughnessMin:.78})
});

/**
 * PBR shader injection WITHOUT changing the Three mesh geometry, positioning,
 * architecture coverage mask, camera or original GLB. Runs after the existing
 * stucco shader, before optional G19 geometry mask.
 */
export function patchMicroreliefShader(shader,{tier='desktop'}={}){
 const cfg=MICRORELIEF_LIMITS[tier];
 if(!cfg)throw RangeError('Unsupported microrelief quality tier');
 if(!shader || typeof shader.fragmentShader!=='string' ||
    !shader.fragmentShader.includes('#include <normal_fragment_maps>') ||
    !shader.fragmentShader.includes('#include <roughnessmap_fragment>') ||
    !shader.fragmentShader.includes('ncFacadeWorld')){
   throw Error('Three shader or real OSM world projection missing; no silent material fallback');
 }
 const shape=cfg.detailScale.toFixed(1),strength=cfg.normalStrength.toFixed(3);
 const inject=[
  'vec3 ncViewDX = dFdx(ncFacadeWorld);',
  'vec3 ncViewDY = dFdy(ncFacadeWorld);',
  'vec3 ncSurfaceDX = normalize(ncViewDX + vec3(1e-6));',
  'vec3 ncSurfaceDY = normalize(ncViewDY + vec3(1e-6));',
  'float ncWave = sin(ncFacadeWorld.x * '+shape+' + ncFacadeWorld.y * 13.0) *',
  '               sin(ncFacadeWorld.y * '+shape+' + ncFacadeWorld.z * 11.0);',
  'vec3 ncBump = dFdx(ncWave) * ncSurfaceDX + dFdy(ncWave) * ncSurfaceDY;',
  'normal = normalize(normal - mat3(viewMatrix) * ncBump * '+strength+');'
 ].join('\n');
 const rough=[
  'float ncVariation = fract(sin(dot(floor(ncFacadeWorld.xy * 13.0),',
  '  vec2(17.17,43.91))) * 53724.13);',
  'roughnessFactor = clamp(roughnessFactor * (.94 + ncVariation*.08), '+cfg.roughnessMin.toFixed(2)+', 1.0);'
 ].join('\n');
 shader.fragmentShader=shader.fragmentShader.replace(
  '#include <normal_fragment_maps>','#include <normal_fragment_maps>\n'+inject
 ).replace('#include <roughnessmap_fragment>',
  '#include <roughnessmap_fragment>\n'+rough);
 return shader;
}

export function enhanceRealOSMWallMicrorelief(city,{tier='desktop'}={}){
 if(!city?.traverse)throw TypeError('Public source scene required');
 if(!MICRORELIEF_LIMITS[tier])throw RangeError('Unsupported render tier');
 const entries=[],meshes=new Set();
 city.traverse(mesh=>{
   if(!mesh.isMesh||!isSourceBuildingWall(mesh.name))return;
   meshes.add(mesh);
   const materials=Array.isArray(mesh.material)?mesh.material:[mesh.material];
   for(const material of materials){
     // Only after facade_stucco has made an independent artistic clone.
     if(!material?.isMeshStandardMaterial||
         material.name!=='NEUROCITY_ART_STUCCO_ON_ACTUAL_OSM_WALLS')continue;
     if(material.userData?.ncMicrorelief)continue;
     const original=material.onBeforeCompile;
     const originalCache=material.customProgramCacheKey;
     material.onBeforeCompile=(shader,renderer)=>{
       original?.(shader,renderer);
       patchMicroreliefShader(shader,{tier});
     };
     material.customProgramCacheKey=()=>String(originalCache?.call(material)||'stucco')+'|'+MICRORELIEF_VERSION+'|'+tier;
     material.userData.ncMicrorelief={version:MICRORELIEF_VERSION,tier};
     material.needsUpdate=true;
     entries.push({material,original,originalCache});
   }
 });
 const report={source:MICRORELIEF_SOURCE,tier,
   wallMeshes:meshes.size,enhancedMaterials:entries.length,
   addedGeometryTriangles:0,textureDownloads:0,assetLicenseRequired:false,
   scientificallyMatchedFacades:false,avatarAssetsTouched:0,
   worldmasterGeometryModified:false,visualCertification:false};
 return {
   ...report,
   restore(){
     for(const {material,original,originalCache} of entries){
       material.onBeforeCompile=original;
       material.customProgramCacheKey=originalCache;
       delete material.userData.ncMicrorelief;
       material.needsUpdate=true;
     }
   }
 };
}
