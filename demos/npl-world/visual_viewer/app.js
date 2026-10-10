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

// The public-city source is a real georeferenced building GLB, not a fabricated map.
// These street props remain a documented ARTISTIC ground-level presentation layer.
const promenadeColor=new THREE.CanvasTexture((()=>{
 const c=document.createElement('canvas');c.width=768;c.height=768;
 const q=c.getContext('2d');q.fillStyle='#e8dfc7';q.fillRect(0,0,768,768);
 for(let y=0;y<768;y+=4){for(let x=0;x<768;x+=4){
  const w=Math.sin(x*.055+2.1*Math.sin(y*.022));
  const type=w<-.22?'#264b53':w>.36?'#efe0c9':'#ba7262';
  q.fillStyle=type;q.fillRect(x,y,3.75,3.75);
 }}
 return c;
})());
promenadeColor.colorSpace=THREE.SRGBColorSpace;
promenadeColor.wrapS=THREE.RepeatWrapping;promenadeColor.wrapT=THREE.RepeatWrapping;
promenadeColor.repeat.set(1.0,12);
promenadeColor.anisotropy=Math.min(8,renderer.capabilities.getMaxAnisotropy());
const matStone=new THREE.MeshStandardMaterial({color:0xcbbda0,roughness:.94});
const matAsphalt=new THREE.MeshStandardMaterial({color:0x383c42,roughness:.91});
const matMosaic=new THREE.MeshStandardMaterial({map:promenadeColor,roughness:.81});
function horizontalPlane(w,h,x,z,y,material){
 const o=new THREE.Mesh(new THREE.PlaneGeometry(w,h),material);
 o.rotation.x=-Math.PI/2;o.position.set(x,y,z);o.receiveShadow=true;
 scene.add(o);return o;
}
horizontalPlane(18,285,-9,-25,-.073,matMosaic); // accurately styled Alicante tile motif; corridor outline approximate
horizontalPlane(13,285,17.5,-25,-.085,matAsphalt);
horizontalPlane(3,285,29.0,-25,-.073,matStone);
horizontalPlane(4,285,-20.5,-25,-.069,matStone);
for(let z=-160;z<125;z+=10){
 const dash=new THREE.Mesh(new THREE.BoxGeometry(.13,.013,3.2),new THREE.MeshStandardMaterial({color:0xe6dcd0}));
 dash.position.set(18,-.047,z);scene.add(dash);
}
// Clean horizon above the marina, not a false aerial replacement.
const sea=new THREE.Mesh(new THREE.PlaneGeometry(750,1050),new THREE.MeshPhysicalMaterial({
 color:0x06738a,metalness:.02,roughness:.23,clearcoat:1,clearcoatRoughness:.16
}));
sea.rotation.x=-Math.PI/2;sea.position.set(395,-.17,-15);scene.add(sea);
const matIron=new THREE.MeshStandardMaterial({color:0x1b2528,metalness:.72,roughness:.32});
const matLamp=new THREE.MeshStandardMaterial({color:0xfff1ca,roughness:.38,emissive:0xffc673,emissiveIntensity:.13});
function cityLamp(x,z){
 const grp=new THREE.Group();grp.position.set(x,0,z);
 const pole=new THREE.Mesh(new THREE.CylinderGeometry(.068,.092,4.4,12),matIron);
 pole.position.y=2.2;grp.add(pole);
 const arm=new THREE.Mesh(new THREE.BoxGeometry(1.65,.07,.08),matIron);arm.position.set(0,4.32,0);grp.add(arm);
 for(const t of [-.63,.63]){
  const globe=new THREE.Mesh(new THREE.SphereGeometry(.23,16,12),matLamp);globe.position.set(t,4.24,0);grp.add(globe);
 }
 grp.traverse(n=>{if(n.isMesh)n.castShadow=true});scene.add(grp);
}
for(let z=-143;z<114;z+=19)cityLamp(3.9,z);
let palmCount=0,windowCount=0;
async function addRealPalmObjects(){
 try{
  const data=await model('./assets/palm.glb');
  const cells=[];
  for(let z=-140;z<=112;z+=16.5){cells.push([-18.8,z],[5.8,z+4.2]);}
  const transform=new THREE.Object3D();
  data.scene.updateMatrixWorld(true);
  data.scene.traverse(part=>{
   if(!part.isMesh)return;
   const mesh=new THREE.InstancedMesh(part.geometry,part.material,cells.length);
   mesh.castShadow=true;mesh.receiveShadow=true;
   for(let i=0;i<cells.length;i++){
    transform.position.set(cells[i][0],-.05,cells[i][1]);
    transform.rotation.set(0,i*.81,0);transform.scale.setScalar(.88+(i%5)*.035);
    transform.updateMatrix();
    mesh.setMatrixAt(i,new THREE.Matrix4().multiplyMatrices(transform.matrix,part.matrixWorld));
   }
   mesh.instanceMatrix.needsUpdate=true;
   scene.add(mesh);
  });
  palmCount=cells.length;
 }catch(err){display('Ciudad cargada; palmeras 3D opcionales no disponibles: '+err.message,true)}
}
// Construct facade detail only on ACTUAL OSM walls: no fabricated building footprints.
function addFacadeDetail(group){
 let buildingWall=null;
 group.traverse(o=>{if(o.isMesh&&o.name.includes('Building_Walls'))buildingWall=o;});
 if(!buildingWall)return;
 buildingWall.updateWorldMatrix(true,false);
 const geo=buildingWall.geometry, pos=geo.getAttribute('position'),idx=geo.index;
 if(!pos)return;
 const edges=new Map();
 const count=idx?idx.count:pos.count;
 const p=[new THREE.Vector3(),new THREE.Vector3(),new THREE.Vector3()];
 for(let k=0;k<count;k+=3){
  for(let q=0;q<3;q++){
   const ix=idx?idx.getX(k+q):k+q;
   p[q].fromBufferAttribute(pos,ix).applyMatrix4(buildingWall.matrixWorld);
  }
  for(let q=0;q<3;q++){
   const a=p[q],b=p[(q+1)%3];
   if(Math.abs(a.y-b.y)>.03 || a.y<4.3)continue;
   const length=Math.hypot(a.x-b.x,a.z-b.z);
   if(length<2.7||length>37)continue;
   const mx=(a.x+b.x)/2,mz=(a.z+b.z)/2;
   if(Math.abs(mx+35)>116||Math.abs(mz+35)>150)continue;
   const key=[Math.round(a.x*10),Math.round(a.z*10),Math.round(b.x*10),Math.round(b.z*10)].sort((x,y)=>x-y).join(':')+':'+a.y.toFixed(0);
   if(!edges.has(key))edges.set(key,{ax:a.x,az:a.z,bx:b.x,bz:b.z,h:a.y,len:length});
  }
 }
 const windows=[],frames=[],balconies=[];
 for(const edge of edges.values()){
  const floors=Math.min(7,Math.floor(edge.h/3.05));
  const along=Math.floor(edge.len/2.85);
  if(along<1)continue;
  const dx=(edge.bx-edge.ax)/edge.len,dz=(edge.bz-edge.az)/edge.len;
  const az=-Math.atan2(dz,dx);
  for(let level=1;level<floors;level++){
   for(let u=0;u<along;u++){
    const v=(u+.5)/along;
    const x=edge.ax+(edge.bx-edge.ax)*v,z=edge.az+(edge.bz-edge.az)*v;
    const y=level*3.05+1.40;
    windows.push([x,y,z,az]);
    frames.push([x,y+1.03,z,az]);
    if(level>1&&u%2===0)balconies.push([x,y-1.03,z,az]);
   }
  }
 }
 const make=(points,geometry,material)=> {
  if(points.length===0)return;
  const mesh=new THREE.InstancedMesh(geometry,material,points.length);
  const obj=new THREE.Object3D();
  points.forEach(([x,y,z,rot],i)=>{obj.position.set(x,y,z);obj.rotation.y=rot;obj.updateMatrix();mesh.setMatrixAt(i,obj.matrix)});
  mesh.instanceMatrix.needsUpdate=true;mesh.castShadow=true;scene.add(mesh);
 };
 make(windows,new THREE.BoxGeometry(1.35,1.86,.11),new THREE.MeshPhysicalMaterial({color:0x163240,metalness:.32,roughness:.16,clearcoat:.53}));
 make(frames,new THREE.BoxGeometry(1.61,.15,.18),new THREE.MeshStandardMaterial({color:0xe5d6bd,roughness:.67}));
 make(balconies,new THREE.BoxGeometry(1.55,.11,.82),matStone);
 windowCount=windows.length;
}

const player=new THREE.Group();scene.add(player);
player.position.set(-10,0,-33);
let avatar=null, city=null,mixer=null,animations={},current=null;
const keys=new Set();
let yaw=.15,pitch=.16,zoom=4.1,mode='back',actorHeading=0,moving=false;
const loader=new GLTFLoader();
const model=(url)=>new Promise((resolve,reject)=>loader.load(url,resolve,undefined,reject));
const showLoad=(text)=>{progress.textContent=text;};
async function loadWorld(){
 showLoad('Cargando modelo geográfico real de Alicante…');
 try{
  const data=await model('./assets/alicante.glb');
  city=data.scene;scene.add(city);
  addFacadeDetail(city);
  await addRealPalmObjects();
  city.traverse(n=>{if(n.isMesh){n.receiveShadow=true;n.castShadow=true;if(n.material?.name?.includes('NO_photo')) n.material.roughness=.9;}});
  showLoad('Alicante 3D cargada: edificios reales y calle a nivel humano. Cargando cuerpo humano animado…');
 }catch(err){display('No se ha podido cargar la ciudad GLB: '+(err?.message||err),true);showLoad('ERROR: falta assets/alicante.glb');return;}
 try{
  const data=await model('./assets/maya.glb');
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
  for(const a of data.animations||[]){
   const nm=a.name.toLowerCase();
   const state=nm.includes('run')?'run':nm.includes('walk')?'walk':nm.includes('idle')?'idle':nm;
   if(!animations[state])animations[state]=mixer.clipAction(a);
  }
  current=animations.idle||(data.animations?.length?mixer.clipAction(data.animations[0]):null);
  if(current)current.play();
  loading.remove();
  window.NPL_READY={cityMeshes:city.children.length,windows:windowCount,palms:palmCount,skins:avatar.children.length,clips:data.animations.map(a=>a.name)};
  display('Explanada: OSM + escena detallada, palmeras CC0 y cuerpo humano articulado. ROSTRO GENÉRICO: todavía no es Lucía.');
 }catch(err){display('No se ha podido cargar el avatar GLB: '+(err?.message||err),true);showLoad('Modelo femenino 3D ausente. Debe existir assets/maya.glb');return;}
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
$('reset').onclick=()=>{player.position.set(-10,0,-33);yaw=.15;mode='back';};
$('fidelity').onclick=()=>{let hi=renderer.getPixelRatio()<1.7;renderer.setPixelRatio(hi?Math.min(devicePixelRatio,2):1);sun.shadow.mapSize.set(hi?2048:1024,hi?2048:1024);sun.shadow.map?.dispose();sun.shadow.map=null;};
frame();
loadWorld();
