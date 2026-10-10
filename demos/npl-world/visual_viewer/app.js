import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

// NPL WORLD - real GLB integration. No placeholder people, no pay-per-map API.
// Local public cartographic geometry + separate PRIVATE human GLB. Offline runtime.
const $=id=>document.getElementById(id);
const loading=$('loading'), info=$('info'), stat=$('stat'), progress=$('progress');
const view=$('game');
const display=(message,problem=false)=>{info.textContent=message;info.classList.toggle('error',problem)};
const renderer=new THREE.WebGLRenderer({canvas:view, antialias:true,alpha:false,powerPreference:'high-performance'});
renderer.setPixelRatio(Math.min(devicePixelRatio,1.75));
renderer.shadowMap.enabled=true;
renderer.shadowMap.type=THREE.PCFSoftShadowMap;
renderer.outputColorSpace=THREE.SRGBColorSpace;
renderer.toneMapping=THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure=1.27;
const scene=new THREE.Scene();
scene.background=new THREE.Color('#9fbed3');
scene.fog=new THREE.FogExp2(0xa4bfd0,0.00165);
const camera=new THREE.PerspectiveCamera(61,1,.08,2200);
const ambient=new THREE.HemisphereLight(0xdff3ff,0x90765b,2.4);
scene.add(ambient);
const sun=new THREE.DirectionalLight(0xffe5b8,3.1);
sun.position.set(-90,180,125);
sun.castShadow=true;
sun.shadow.mapSize.set(2048,2048);
sun.shadow.camera.left=-110;sun.shadow.camera.right=110;
sun.shadow.camera.top=110;sun.shadow.camera.bottom=-110;
sun.shadow.camera.near=.5;sun.shadow.camera.far=500;
sun.shadow.bias=-.000035;
scene.add(sun,sun.target);
const origin=new THREE.Vector3(0,0,0);
sun.target.position.copy(origin);
const floor=new THREE.Mesh(new THREE.PlaneGeometry(2000,2000),new THREE.MeshStandardMaterial({color:0xb5ada1,roughness:.98}));
floor.rotation.x=-Math.PI/2;floor.position.y=-.135;floor.receiveShadow=true;scene.add(floor);

// Approximate decorative material ONLY, not a surveyed/photographed pavement.
// This is kept separate from the true OpenStreetMap building geometry.
const cv=document.createElement('canvas');cv.width=512;cv.height=512;
const ctx=cv.getContext('2d');
ctx.fillStyle='#d0c6a7';ctx.fillRect(0,0,512,512);
for(let y=0;y<512;y+=4){for(let x=0;x<512;x+=4){
 const v=Math.sin(x*.079+Math.sin(y*.026)*1.65);
 ctx.fillStyle=v<-.31?'#52696c':v>.48?'#eadfca':'#bb7362';
 ctx.fillRect(x,y,3.3,3.3);
}}
const waveTex=new THREE.CanvasTexture(cv);
waveTex.colorSpace=THREE.SRGBColorSpace;waveTex.wrapS=waveTex.wrapT=THREE.RepeatWrapping;
waveTex.repeat.set(1.0,22);
waveTex.anisotropy=Math.min(renderer.capabilities.getMaxAnisotropy(),8);
const promenade=new THREE.Mesh(new THREE.PlaneGeometry(14,480),new THREE.MeshStandardMaterial({map:waveTex,roughness:.92}));
promenade.rotation.x=-Math.PI/2;
promenade.position.set(0,-.109,0);
promenade.receiveShadow=true;
// Reference corridor only, NOT a surveyed pavement boundary.
scene.add(promenade);
// Sea is also an illustrative placeholder, distinguish from georeferenced OSM geometry.
const sea=new THREE.Mesh(new THREE.PlaneGeometry(980,1500),new THREE.MeshPhysicalMaterial({
 color:0x08758d,roughness:.26,metalness:.05,transparent:true,opacity:.96
}));
sea.rotation.x=-Math.PI/2;sea.position.set(655,-.16,0);sea.receiveShadow=true;scene.add(sea);

const player=new THREE.Group();scene.add(player);
let avatar=null, city=null,mixer=null,animations={},current=null;
const keys=new Set();
let yaw=0.0,pitch=.24,zoom=5.8,mode='back',actorHeading=0,moving=false;
const loader=new GLTFLoader();
const model=(url)=>new Promise((resolve,reject)=>loader.load(url,resolve,undefined,reject));
const showLoad=(text)=>{progress.textContent=text;};
async function loadWorld(){
 showLoad('Cargando modelo geográfico real de Alicante…');
 try{
  const data=await model('./assets/alicante.glb');
  city=data.scene;scene.add(city);
  city.traverse(n=>{if(n.isMesh){n.receiveShadow=true;n.castShadow=true;if(n.material?.name?.includes('NO_photo')) n.material.roughness=.9;}});
  showLoad('614 edificios: datos OSM cargados. Cargando avatar GLB privado…');
 }catch(err){display('No se ha podido cargar la ciudad GLB: '+(err?.message||err),true);showLoad('ERROR: falta assets/alicante.glb');return;}
 try{
  const data=await model('./assets/lucia.glb');
  avatar=data.scene;
  const box=new THREE.Box3().setFromObject(avatar),dim=new THREE.Vector3();
  box.getSize(dim);
  const scale=1.69/Math.max(0.001,dim.y);
  avatar.scale.setScalar(scale);
  avatar.position.y=-box.min.y*scale;
  player.add(avatar);
  avatar.traverse(n=>{if(n.isMesh||n.isSkinnedMesh){n.frustumCulled=false;n.castShadow=true;n.receiveShadow=true;
    if(n.material){n.material.side=THREE.DoubleSide;n.material.needsUpdate=true;}}});
  mixer=new THREE.AnimationMixer(avatar);
  for(const a of data.animations||[])animations[a.name.toLowerCase()]=mixer.clipAction(a);
  current=animations.idle||data.animations?.length&&mixer.clipAction(data.animations[0]);
  if(current)current.play();
  loading.remove();
  display('Ciudad real (614 edificios OSM) + personaje GLB propio. Fachadas sin fotogrametría. Cámara: C.');
 }catch(err){display('No se ha podido cargar el avatar GLB: '+(err?.message||err),true);showLoad('Avatar ausente. Debe existir assets/lucia.glb');return;}
}
function animateState(key){
 const next=animations[key]||animations.walk||animations.idle;
 if(!next||next===current)return;
 next.reset().play();
 if(current)current.crossFadeTo(next,.22,false);
 current=next;
}
const clock=new THREE.Clock();
function frame(){
 requestAnimationFrame(frame);
 const dt=Math.min(clock.getDelta(),.045);
 const forward=Number(keys.has('KeyW')||keys.has('ArrowUp'))-Number(keys.has('KeyS')||keys.has('ArrowDown'));
 const strafe=Number(keys.has('KeyD'))-Number(keys.has('KeyA'));
 const total=Math.hypot(forward,strafe);
 moving=total>0.01 && !!avatar;
 const fast=keys.has('ShiftLeft')||keys.has('ShiftRight');
 if(moving){
  const speed=(fast?6.6:2.6)*dt/total;
  const dx=Math.sin(yaw)*forward+Math.cos(yaw)*strafe;
  const dz=Math.cos(yaw)*forward-Math.sin(yaw)*strafe;
  player.position.x+=dx*speed;player.position.z+=dz*speed;
  actorHeading=Math.atan2(dx,dz);
  const headingDelta=Math.atan2(Math.sin(actorHeading-avatar.rotation.y),Math.cos(actorHeading-avatar.rotation.y));
  avatar.rotation.y+=headingDelta*Math.min(1,dt*12);
 }
 if(mixer){animateState(moving?(fast?'run':'walk'):'idle');mixer.update(dt);}
 const target=player.position.clone().add(new THREE.Vector3(0,1.32,0));
 const actualYaw=mode==='face'?avatar?.rotation.y||0:yaw;
 if(mode==='face'&&avatar){
   const ang=avatar.rotation.y;
   camera.position.set(player.position.x+Math.sin(ang)*2.5,player.position.y+1.64,player.position.z+Math.cos(ang)*2.5);
   camera.lookAt(target.x,target.y+.16,target.z);
 }else if(mode==='first'){
   camera.position.set(player.position.x,player.position.y+1.58,player.position.z);
   camera.lookAt(target.x+Math.sin(yaw)*3,target.y+Math.sin(pitch)*3,target.z+Math.cos(yaw)*3);
 }else{
   camera.position.set(target.x-Math.sin(actualYaw)*zoom*Math.cos(pitch),
    target.y+zoom*Math.sin(pitch)+.7,target.z-Math.cos(actualYaw)*zoom*Math.cos(pitch));
   camera.lookAt(target);
 }
 // Sun follows the player so shadows stay stable during local inspection.
 sun.position.set(player.position.x-90,180,player.position.z+125);
 sun.target.position.set(player.position.x,0,player.position.z);
 sun.target.updateMatrixWorld();
 renderer.render(scene,camera);
 if(Math.floor(clock.elapsedTime*3)!==Math.floor((clock.elapsedTime-dt)*3)){
   stat.textContent='x '+player.position.x.toFixed(0)+' m · z '+player.position.z.toFixed(0)+' m · '+mode;
 }
}
function resize(){const width=view.clientWidth,height=view.clientHeight;
 camera.aspect=width/Math.max(1,height);camera.updateProjectionMatrix();
 renderer.setSize(width,height,false);
}
window.addEventListener('resize',resize);resize();
window.addEventListener('keydown',e=>{if(['KeyW','KeyA','KeyS','KeyD','ArrowUp','ArrowDown','ShiftLeft','ShiftRight'].includes(e.code))e.preventDefault();keys.add(e.code);if(e.code==='KeyC')cycleCamera();});
window.addEventListener('keyup',e=>keys.delete(e.code));
window.addEventListener('blur',()=>keys.clear());
let dragging=false,lastX=0,lastY=0;
view.addEventListener('pointerdown',e=>{dragging=true;lastX=e.clientX;lastY=e.clientY;view.setPointerCapture(e.pointerId);});
view.addEventListener('pointerup',()=>dragging=false);
view.addEventListener('pointermove',e=>{if(!dragging)return;
 const dx=e.clientX-lastX,dy=e.clientY-lastY;lastX=e.clientX;lastY=e.clientY;
 yaw+=dx*.006;pitch=Math.max(-.08,Math.min(.92,pitch+dy*.004));});
view.addEventListener('wheel',e=>{e.preventDefault();zoom=Math.max(1.85,Math.min(28,zoom+Math.sign(e.deltaY)*.65));},{passive:false});
const cycleCamera=()=>{mode=mode==='back'?'face':mode==='face'?'first':'back';$('cameraMode').textContent=mode==='back'?'Tercera persona':mode==='face'?'Inspección facial':'Primera persona';};
$('cam').onclick=cycleCamera;
$('reset').onclick=()=>{player.position.set(0,0,0);yaw=0;mode='back';};
$('fidelity').onclick=()=>{let hi=renderer.getPixelRatio()<1.7;renderer.setPixelRatio(hi?Math.min(devicePixelRatio,2):1);sun.shadow.mapSize.set(hi?2048:1024,hi?2048:1024);sun.shadow.map?.dispose();sun.shadow.map=null;};
frame();
loadWorld();
