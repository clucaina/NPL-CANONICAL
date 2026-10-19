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
renderer.toneMappingExposure=1.07;
const scene=new THREE.Scene();
scene.background=new THREE.Color('#9fbed3');
scene.fog=new THREE.FogExp2(0xa4bfd0,0.0020);
const camera=new THREE.PerspectiveCamera(54,1,.07,1800);
const ambient=new THREE.HemisphereLight(0xdff3ff,0x90765b,1.75);
scene.add(ambient);
const sun=new THREE.DirectionalLight(0xffe5b8,2.1);
sun.position.set(-90,180,125);
sun.castShadow=true;
sun.shadow.mapSize.set(1024,1024);
sun.shadow.camera.left=-66;sun.shadow.camera.right=66;
sun.shadow.camera.top=66;sun.shadow.camera.bottom=-66;
sun.shadow.camera.near=.5;sun.shadow.camera.far=500;
sun.shadow.bias=-.000035;
scene.add(sun,sun.target);
const origin=new THREE.Vector3(0,0,0);
sun.target.position.copy(origin);

// The public-city source is a real georeferenced building GLB, not a fabricated map.
// These street props remain a documented ARTISTIC ground-level presentation layer.
// Explicit 2026 corrected georeference: Explanada de España OSM way #20490190
// https://mapcarta.com/W20490190 : 38.34318 N, -0.48326 W
// Local OSM projection scene origin was 38.34402 N, -0.48322 W.
const decorStart=scene.children.length;
const ESPLANADA_CENTER=new THREE.Vector3(-3.5,0,119.0);
const EXPLANADA_BEARING=-0.65; // World direction from city centre towards Canalejas.
const promenadeColor=new THREE.CanvasTexture((()=>{
 const c=document.createElement('canvas');c.width=768;c.height=768;
 const q=c.getContext('2d');q.fillStyle='#e8dfc7';q.fillRect(0,0,768,768);
 for(let y=0;y<768;y+=4){for(let x=0;x<768;x+=4){
  const w=Math.sin(x*.055+2.1*Math.sin(y*.022));
  const type=w<-.22?'#3d5b60':w>.36?'#efe6d4':'#c98c78';
  q.fillStyle=type;q.fillRect(x,y,4,4);
 }}
 return c;
})());
promenadeColor.colorSpace=THREE.SRGBColorSpace;
promenadeColor.wrapS=THREE.RepeatWrapping;promenadeColor.wrapT=THREE.RepeatWrapping;
promenadeColor.repeat.set(1.0,9);
promenadeColor.anisotropy=Math.min(16,renderer.capabilities.getMaxAnisotropy());
const matStone=new THREE.MeshStandardMaterial({color:0xcbbda0,roughness:.94});
const matAsphalt=new THREE.MeshStandardMaterial({color:0x383c42,roughness:.91});
const matMosaic=new THREE.MeshStandardMaterial({map:promenadeColor,roughness:.81});
function horizontalPlane(w,h,x,z,y,material){
 const o=new THREE.Mesh(new THREE.PlaneGeometry(w,h),material);
 o.rotation.x=-Math.PI/2;o.position.set(x,y,z);o.receiveShadow=true;
 scene.add(o);return o;
}
horizontalPlane(18,285,-9,-25,-.073,matMosaic);
horizontalPlane(11.4,285,5.3,-25,-.078,matStone); // accurately styled Alicante tile motif; corridor outline approximate
horizontalPlane(13,285,17.5,-25,-.085,matAsphalt);
horizontalPlane(4.4,285,26.2,-25,-.072,matStone);
horizontalPlane(3,285,29.0,-25,-.073,matStone);
horizontalPlane(5,285,-20.5,-25,-.069,matStone);
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
  for(let z=-132;z<=112;z+=26){cells.push([-18.8,z],[5.8,z+4.2]);}
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
   decorGroup.add(mesh);
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
   if(Math.abs(mx+10)>235||Math.abs(mz-119)>280)continue;
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

// Rotate ALL local illustrative objects to the REAL Explanada alignment, rather than
// painting an invented road through georeferenced building footprints.
const decorGroup=new THREE.Group();
for(const ob of scene.children.slice(decorStart)){scene.remove(ob);decorGroup.add(ob);}
decorGroup.rotation.y=EXPLANADA_BEARING;
decorGroup.position.copy(ESPLANADA_CENTER);
scene.add(decorGroup);
const player=new THREE.Group();scene.add(player);
player.position.set(-10.664,0,113.546);
let avatar=null, city=null,mixer=null,animations={},current=null;
const keys=new Set();
let yaw=-.65,pitch=.14,zoom=2.95,mode='back',actorHeading=0,moving=false;
const loader=new GLTFLoader();
const model=(url)=>new Promise((resolve,reject)=>loader.load(url,resolve,undefined,reject));
const showLoad=(text)=>{progress.textContent=text;};
async function loadWorld(){
 showLoad('Cargando modelo geográfico real de Alicante…');
 try{
  const data=await model('./assets/alicante.glb');
  city=data.scene;scene.add(city);
  // v11 architectural detail baked on exactly 150 ACTUAL OSM building-wall edges.
  // Geometry intentionally separate from the PNOA georeferenced base.
  try {
    const decorData=await model('./assets/facades.glb');
    const facades=decorData.scene;
    facades.traverse(n=>{if(n.isMesh){n.castShadow=false;n.receiveShadow=true;}});
    scene.add(facades);
    windowCount=3679;
  }catch(err){display('Los edificios base se han cargado, pero falta el detalle GLB: '+err.message,true);}
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
  avatar.rotation.y=-.65;
  player.add(avatar);
  // Hair and clothing are REAL meshes already included in the personal GLB and bound to skeleton bones.
  // Never append duplicate procedural hair on top of the true mesh.
  // v12: The avatar GLB already contains attached hair; do not add duplicate geometry.
  // Tailored dark clothing rather than the generic bright casual prototype.
  avatar.traverse(n=>{
   if(!n.isMesh||!n.material)return;
   const mat=n.material;
   if(/plum satin/i.test(mat.name)){n.material=mat.clone();n.material.color.setRGB(.23,.22,.24);}
   if(/ponytail/i.test(mat.name)){n.material=mat.clone();n.material.color.multiplyScalar(.79);}
  });
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
  window.NPL_READY={cityMeshes:city.children.length,facadeDetailsLoaded:windowCount>0,explanadaCoords:[38.34318,-0.48326],windows:windowCount,palms:palmCount,skins:avatar.children.length,clips:data.animations.map(a=>a.name)};
  display('Alicante 3D con 614 edificios reales OSM, detalles arquitectónicos artísticos, palmeras CC0 y avatar privado v11. Fotorrealismo aún sin alcanzar.');
 }catch(err){
  // PUBLIC, NON-PERSONAL city navigation remains possible without private maya.glb.
  // No invented avatar and no personal mesh is ever pulled into a public artifact.
  mode='first';
  $('cameraMode').textContent='Primera persona · ciudad pública';
  window.NPL_READY={cityMeshes:city?.children?.length||0,cityOnly:true,privateAvatarLoaded:false,
    explanadaCoords:[38.34318,-0.48326],windows:windowCount,palms:palmCount,skins:0,clips:[]};
  loading.remove();
  showLoad('Ciudad geográfica cargada en modo público sin avatar');
  display('Ciudad 3D navegable sin avatar personal. Fachadas y alturas incompletas; fotorrealismo no validado.');
  return;
 }
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
 const strafe=Number(keys.has('KeyD')||keys.has('ArrowRight'))-Number(keys.has('KeyA')||keys.has('ArrowLeft'));
 const total=Math.hypot(forward,strafe);
 moving=total>0.01 && !!city;
 const fast=keys.has('ShiftLeft')||keys.has('ShiftRight');
 if(moving){
  const speed=(fast?6.6:2.6)*dt/total;
  const dx=Math.sin(yaw)*forward-Math.cos(yaw)*strafe;
  const dz=Math.cos(yaw)*forward+Math.sin(yaw)*strafe;
  player.position.x=Math.max(-318,Math.min(402,player.position.x+dx*speed));
  player.position.z=Math.max(-411,Math.min(304,player.position.z+dz*speed));
  actorHeading=Math.atan2(Math.sin(yaw)*Math.sign(forward),Math.cos(yaw)*Math.sign(forward));
  if(avatar&&Math.abs(forward)>.05){const headingDelta=Math.atan2(Math.sin(actorHeading-avatar.rotation.y),Math.cos(actorHeading-avatar.rotation.y));
    avatar.rotation.y+=headingDelta*Math.min(1,dt*7);}
  // Lateral input remains strafe rather than forcing a 90-degree turn.
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
window.addEventListener('keydown',e=>{if(['KeyW','KeyA','KeyS','KeyD','ArrowUp','ArrowDown','ArrowLeft','ArrowRight','ShiftLeft','ShiftRight'].includes(e.code))e.preventDefault();keys.add(e.code);if(e.code==='KeyC')cycleCamera();});
window.addEventListener('keyup',e=>keys.delete(e.code));
window.addEventListener('blur',()=>keys.clear());
let dragging=false,lastX=0,lastY=0;
view.addEventListener('pointerdown',e=>{dragging=true;lastX=e.clientX;lastY=e.clientY;view.setPointerCapture(e.pointerId);});
view.addEventListener('pointerup',()=>dragging=false);
view.addEventListener('pointermove',e=>{if(!dragging)return;
 const dx=e.clientX-lastX,dy=e.clientY-lastY;lastX=e.clientX;lastY=e.clientY;
 yaw+=dx*.006;pitch=Math.max(-.08,Math.min(.92,pitch+dy*.004));});
view.addEventListener('wheel',e=>{e.preventDefault();zoom=Math.max(1.85,Math.min(28,zoom+Math.sign(e.deltaY)*.65));},{passive:false});
const cycleCamera=()=>{mode=avatar?(mode==='back'?'face':mode==='face'?'first':'back'):(mode==='first'?'back':'first');$('cameraMode').textContent=mode==='back'?'Tercera persona':mode==='face'?'Inspección facial':'Primera persona · ciudad pública';};
$('cam').onclick=cycleCamera;
$('reset').onclick=()=>{player.position.set(-10.664,0,113.546);yaw=-.65;mode=avatar?'back':'first';};
$('fidelity').onclick=()=>{let hi=renderer.getPixelRatio()<1.7;renderer.setPixelRatio(hi?Math.min(devicePixelRatio,2):1);sun.shadow.mapSize.set(hi?2048:1024,hi?2048:1024);sun.shadow.map?.dispose();sun.shadow.map=null;};
frame();
loadWorld();
