import * as THREE from 'three';

/**
 * Wind motion on EXISTING original CC0 procedural Mediterranean canopy meshes.
 *
 * No replacement of the six PRIVATE Phoenix assets in G19/V50, no additional
 * geometry, draw calls, network textures or real-tree-location claims.
 */
export const PALM_WIND_SOURCE='CC0_PUBLIC_ARTISTIC_PALM_CANOPIES_NOT_SURVEYED';
export const PALM_WIND_TIERS=Object.freeze({
  desktop:Object.freeze({amplitude:.095,speed:.78}),
  mobile:Object.freeze({amplitude:.028,speed:.48})
});
const MATCH='NEUROCITY_CC0_ART_palm_canopies_';

/** Modify only the begin_vertex chunk in Three v0.169 ShaderMaterials. */
export function injectPalmWindShader(shader,{tier='desktop',uniforms=null}={}){
 const cfg=PALM_WIND_TIERS[tier];
 if(!cfg)throw RangeError('Invalid animated vegetation GPU tier');
 if(!shader?.vertexShader?.includes('#include <begin_vertex>'))
   throw Error('Original Three palm vertex shader marker missing; fail closed');
 if(!shader.uniforms)shader.uniforms={};
 const windTime=uniforms?.time||{value:0};
 const windAmplitude=uniforms?.amplitude||{value:cfg.amplitude};
 shader.uniforms.ncPalmWindTime=windTime;
 shader.uniforms.ncPalmWindAmplitude=windAmplitude;
 shader.vertexShader='uniform float ncPalmWindTime;\nuniform float ncPalmWindAmplitude;\n'+
  shader.vertexShader.replace('#include <begin_vertex>',
  '#include <begin_vertex>\n'+[
    // Frond bases (radius <=0.5) remain attached to each original trunk.
    'float ncRadius=length(position.xz);',
    'float ncWeight=smoothstep(.55,4.25,ncRadius);',
    'float ncPhase=ncPalmWindTime*'+cfg.speed.toFixed(2)+'+position.x*.38+position.z*.57;',
    'transformed.x += sin(ncPhase)*ncPalmWindAmplitude*ncWeight;',
    'transformed.z += cos(ncPhase*.82)*ncPalmWindAmplitude*.38*ncWeight;'
   ].join('\n'));
 return shader;
}

/** Single uniform update per frame across only 3 frond material variants. */
export function animateExistingPublicPalmFronds(group,{tier='desktop',reducedMotion=false}={}){
 if(!group?.isGroup)throw TypeError('Original urban kit group required');
 if(!PALM_WIND_TIERS[tier]||typeof reducedMotion!=='boolean')
   throw RangeError('Invalid motion or quality tier');
 const entries=[],affected=[];
 group.traverse(mesh=>{
   if(!mesh.isInstancedMesh||!mesh.name.startsWith(MATCH))return;
   if(!mesh.material?.isMeshStandardMaterial||!mesh.geometry)return;
   const material=mesh.material;
   if(material.userData?.ncPalmWind)return;
   const original=material.onBeforeCompile,originalCache=material.customProgramCacheKey;
   const uniforms={time:{value:0},amplitude:{value:reducedMotion?0:PALM_WIND_TIERS[tier].amplitude}};
   material.onBeforeCompile=(shader,renderer)=>{
     original?.(shader,renderer);
     injectPalmWindShader(shader,{tier,uniforms});
   };
   material.customProgramCacheKey=()=>String(originalCache?.call(material)||'palm')+'|ncPublicWindV1|'+tier;
   material.userData.ncPalmWind={tier,reducedMotion,source:PALM_WIND_SOURCE};
   material.needsUpdate=true;
   if(!mesh.boundingSphere)mesh.computeBoundingSphere();
   const originalRadius=mesh.boundingSphere?.radius;
   if(Number.isFinite(originalRadius))mesh.boundingSphere.radius=originalRadius+PALM_WIND_TIERS[tier].amplitude*2;
   entries.push({material,original,originalCache,uniforms,mesh,originalRadius});
   affected.push(mesh.name);
 });
 let lastSeconds=0,paused=false;
 const report={
   source:PALM_WIND_SOURCE,tier,reducedMotion,
   canopyGroups:entries.length,
   sourceMeshNames:affected,geometryAdded:0,verticesReplaced:0,
   drawCallsAdded:0,textureDownloads:0,privateAvatarAssetsUsed:false,
   G19SourcePalmsAltered:false,treeLocationsSurveyed:false
 };
 return {
   ...report,
   update(seconds){
     if(!Number.isFinite(seconds)||seconds<0)throw RangeError('Invalid animation clock');
     lastSeconds=seconds%1024;
     for(const e of entries)e.uniforms.time.value=lastSeconds;
     return lastSeconds;
   },
   pause(value){
     if(typeof value!=='boolean')throw TypeError('Pause must be boolean');
     paused=value;
     for(const e of entries)e.uniforms.amplitude.value=paused||reducedMotion?0:PALM_WIND_TIERS[tier].amplitude;
     return paused;
   },
   isPaused(){return paused||reducedMotion;},
   restore(){
     for(const e of entries){
       e.material.onBeforeCompile=e.original;
       e.material.customProgramCacheKey=e.originalCache;
       delete e.material.userData.ncPalmWind;
       e.material.needsUpdate=true;
       if(Number.isFinite(e.originalRadius)&&e.mesh.boundingSphere)e.mesh.boundingSphere.radius=e.originalRadius;
     }
   }
 };
}
