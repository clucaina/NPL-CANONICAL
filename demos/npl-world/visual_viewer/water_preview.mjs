import * as THREE from 'three';
import {createWaterSurface,advanceWaterSurface} from './water_surface.mjs';
const canvas=document.querySelector('#water');
const renderer=new THREE.WebGLRenderer({canvas,antialias:true,powerPreference:'high-performance'});
renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));
renderer.outputColorSpace=THREE.SRGBColorSpace;
renderer.toneMapping=THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure=1.1;
const scene=new THREE.Scene();
scene.background=new THREE.Color('#a5c4d6');
scene.fog=new THREE.FogExp2(0xa5c4d6,.002);
const camera=new THREE.PerspectiveCamera(60,1,.1,1600);
camera.position.set(0,6,28);camera.lookAt(0,0,-70);
const reducedMotion=matchMedia('(prefers-reduced-motion: reduce)').matches;
const tier=matchMedia('(pointer:coarse)').matches?'mobile':'desktop';
const water=createWaterSurface({tier,reducedMotion});
water.position.set(0,-.4,-140);scene.add(water);
const clock=new THREE.Clock();
function resize(){
 const w=canvas.clientWidth,h=canvas.clientHeight;
 camera.aspect=w/Math.max(1,h);camera.updateProjectionMatrix();
 renderer.setSize(w,h,false);
}
addEventListener('resize',resize);resize();
function frame(){
 requestAnimationFrame(frame);
 advanceWaterSurface(water,clock.getElapsedTime());
 renderer.render(scene,camera);
 window.NEUROCITY_WATER_QA={...water.userData.waterQA,
  programCount:renderer.info.programs?.length||0,
  elapsed:water.material.uniforms.uTime.value,
  canvasWidth:canvas.width,canvasHeight:canvas.height};
}
frame();
