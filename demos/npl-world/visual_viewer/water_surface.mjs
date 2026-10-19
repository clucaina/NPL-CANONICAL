import * as THREE from 'three';
export const WATER_SOURCE='artistic_mediterranean_surface_not_surveyed';
const vertexShader=`
varying vec2 vLocal;
varying vec3 vWorld;
#include <fog_pars_vertex>
void main(){
 vLocal=position.xy;
 vWorld=(modelMatrix*vec4(position,1.0)).xyz;
 vec4 mvPosition=modelViewMatrix*vec4(position,1.0);
 gl_Position=projectionMatrix*mvPosition;
 #include <fog_vertex>
}`;
const fragmentShader=`
uniform float uTime;
uniform float uDetail;
varying vec2 vLocal;
varying vec3 vWorld;
#include <fog_pars_fragment>
void main(){
 vec2 p=vLocal;
 float a=p.x*.18+p.y*.065+uTime*.72;
 float b=p.x*-.075+p.y*.23-uTime*.48;
 vec2 slope=vec2(.00648*cos(a)-.00165*cos(b),.00234*cos(a)+.00506*cos(b));
 float swell=sin(a)*.55+sin(b)*.35;
 if(uDetail>.5){
  float c=p.x*.61-p.y*.37+uTime*1.18;
  slope+=vec2(.61,-.37)*(.006*cos(c));
  swell+=sin(c)*.08;
 }
 vec3 n=normalize(mat3(modelMatrix)*vec3(-slope.x*3.0,-slope.y*3.0,1.0));
 vec3 eye=normalize(cameraPosition-vWorld);
 vec3 sun=normalize(vec3(-.38,.75,.53));
 float fresnel=.035+.77*pow(1.0-clamp(dot(n,eye),0.0,1.0),5.0);
 float light=max(dot(n,sun),0.0);
 vec3 color=mix(vec3(.012,.145,.208),vec3(.020,.285,.335),clamp(.57+.20*swell+.15*light,0.0,1.0));
 color=mix(color,vec3(.39,.57,.66),clamp(fresnel,0.0,.82));
 float glint=pow(max(dot(reflect(-sun,n),eye),0.0),92.0);
 float fade=clamp(1.0-length(cameraPosition-vWorld)/360.0,0.0,1.0);
 float ripple=sin(p.x*.87+uTime*1.4)*sin(p.y*.63-uTime*.93);
 float micro=uDetail>.5?fade*fade*max(0.0,ripple-.62)*.065:0.0;
 color+=vec3(1.0,.86,.63)*(glint*.68+micro);
 gl_FragColor=vec4(color,1.0);
 #include <tonemapping_fragment>
 #include <colorspace_fragment>
 #include <fog_fragment>
}`;
export function createWaterSurface({tier='desktop',reducedMotion=false}={}){
 if(!['desktop','mobile'].includes(tier))throw new RangeError('Invalid water tier');
 if(typeof reducedMotion!=='boolean')throw new TypeError('Invalid motion preference');
 const geometry=new THREE.PlaneGeometry(750,1050,1,1);
 const material=new THREE.ShaderMaterial({
  name:'NEUROCITY_PROCEDURAL_SEA',uniforms:{uTime:{value:0},uDetail:{value:tier==='desktop'?1:0}},
  vertexShader,fragmentShader,fog:true,depthWrite:true,transparent:false
 });
 const mesh=new THREE.Mesh(geometry,material);
 mesh.name='NEUROCITY_ARTISTIC_MEDITERRANEAN_WATER';
 mesh.rotation.x=-Math.PI/2;mesh.position.set(395,-.17,-15);
 mesh.castShadow=false;mesh.receiveShadow=false;
 mesh.userData.waterQA=Object.freeze({
  source:WATER_SOURCE,tier,reducedMotion,triangleCount:2,drawCalls:1,
  textures:0,geometrySurveyed:false,originalOSMModified:false,noPrivateAssets:true,animated:!reducedMotion
 });
 return mesh;
}
export function advanceWaterSurface(mesh,elapsedSeconds){
 if(mesh?.userData?.waterQA?.source!==WATER_SOURCE)throw new TypeError('Not a NeuroCity water mesh');
 if(!Number.isFinite(elapsedSeconds)||elapsedSeconds<0)throw new RangeError('Invalid elapsed time');
 if(!mesh.userData.waterQA.reducedMotion)mesh.material.uniforms.uTime.value=elapsedSeconds%2048;
 return mesh.material.uniforms.uTime.value;
}
