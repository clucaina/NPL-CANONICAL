import * as THREE from 'three';
import {brainActivity,historySample} from './brain_state.mjs';
// Illustrative procedural surface, not anatomical/clinical imaging.
// Temporal dimension: interactive replay of the last ~12 seconds of game-state activity.
export function createBrain4D(canvas,label){
 if(!canvas)return {available:false,tick:()=>{},setTimeAgo:()=>{},dispose:()=>{}};
 let renderer=null;
 try {
   renderer=new THREE.WebGLRenderer({canvas,alpha:true,antialias:true,powerPreference:'low-power'});
 } catch(_) {
   if(label)label.textContent='WebGL cerebral no disponible: modo textual accesible.';
   return {available:false,tick:()=>{},setTimeAgo:()=>{},dispose:()=>{}};
 }
 renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,1.5));
 renderer.setClearColor(0x000000,0);
 renderer.outputColorSpace=THREE.SRGBColorSpace;
 const scene=new THREE.Scene();
 const camera=new THREE.PerspectiveCamera(32,1,.1,30);
 camera.position.set(0,.1,6.0);
 scene.add(new THREE.AmbientLight(0xffd9cc,1.12));
 const key=new THREE.DirectionalLight(0xffe7da,2.5);key.position.set(-3,4,7);scene.add(key);
 const cool=new THREE.PointLight(0xb36cba,12);cool.position.set(2,-2,3);scene.add(cool);
 const brain=new THREE.Group();scene.add(brain);
 const cerebral=new THREE.Group();brain.add(cerebral);
 const hemiMat=new THREE.MeshPhysicalMaterial({
   color:0xc99b95,roughness:.65,metalness:0,transparent:false,clearcoat:.22,clearcoatRoughness:.6
 });
 function hemisphere(side){
   const geo=new THREE.SphereGeometry(1,42,28);
   const pos=geo.attributes.position;
   for(let i=0;i<pos.count;i++){
     const x=pos.getX(i),y=pos.getY(i),z=pos.getZ(i);
     const fold=.045*Math.sin(14*y+5*x)*Math.sin(10*z+4*y)
                 +.03*Math.cos(21*x+8*z);
     pos.setXYZ(i,x*(.72+fold),y*(.95+fold),z*(.86+fold));
   }
   geo.computeVertexNormals();
   const mesh=new THREE.Mesh(geo,hemiMat.clone());
   mesh.position.set(side*.55,.12,0);
   cerebral.add(mesh);
   return mesh;
 }
 hemisphere(-1);hemisphere(1);
 // Gyral folds are approximate surface curves: this is not a clinical atlas.
 const foldMat=new THREE.MeshBasicMaterial({color:0x6d4057,transparent:true,opacity:.46});
 for(const side of [-1,1]){
   for(let k=0;k<14;k++){
     const curve=[];
     const lat=-.72+k*.105;
     for(let i=0;i<=23;i++){
       const a=i/23*Math.PI;
       const x=side*(.55+.69*Math.sin(a)*Math.cos(lat*2.15));
       const y=.12+lat*.95+.025*Math.sin(a*6+k);
       const z=.86*Math.sin(a)*Math.sin(lat*2.15+.35)+.12;
       curve.push(new THREE.Vector3(x,y,z));
     }
     const line=new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(curve),33,.011,3,false),foldMat);
     cerebral.add(line);
   }
 }
 const cerebellum=new THREE.Mesh(new THREE.SphereGeometry(.39,24,16),
   new THREE.MeshStandardMaterial({color:0xae827e,roughness:.77}));
 cerebellum.scale.set(1,.64,.66);cerebellum.position.set(0,-.75,-.48);
 brain.add(cerebellum);
 const stem=new THREE.Mesh(new THREE.CylinderGeometry(.12,.16,.65,16),
   new THREE.MeshStandardMaterial({color:0xab8184,roughness:.85}));
 stem.position.set(0,-1.04,-.28);stem.rotation.x=.21;brain.add(stem);
 const sites=[
  ["sensory",new THREE.Vector3(-.89,.38,.72),0xf5c47c],
  ["attention",new THREE.Vector3(.82,.54,.67),0xe47f9b],
  ["temporal",new THREE.Vector3(-.88,-.24,.75),0x89cbd4],
  ["inference",new THREE.Vector3(.88,.15,.74),0xf7afc9],
  ["choice",new THREE.Vector3(.54,-.25,.79),0xd2bbff],
  ["social",new THREE.Vector3(-.48,.73,.53),0xa8d2a6]
 ];
 const points=[];
 const sphere=new THREE.SphereGeometry(.092,12,9);
 for(const [name,p,color] of sites){
   const mat=new THREE.MeshBasicMaterial({color,transparent:true,opacity:.8});
   const glow=new THREE.Mesh(sphere,mat);glow.position.copy(p);glow.userData.name=name;brain.add(glow);
   points.push({name,mesh:glow,color});
 }
 const axons=[];
 for(let i=0;i<sites.length;i++){
  for(let j=i+1;j<sites.length;j++){
    if(j-i>3)continue;
    const start=sites[i][1],end=sites[j][1];
    const mid=start.clone().lerp(end,.5);mid.z+=.36;
    const curve=new THREE.QuadraticBezierCurve3(start,mid,end);
    const tube=new THREE.Mesh(new THREE.TubeGeometry(curve,25,.008,4,false),
      new THREE.MeshBasicMaterial({color:0xf9b2b2,transparent:true,opacity:.15}));
    brain.add(tube);axons.push(tube);
  }
 }
 const trails=[];
 const trailMat=new THREE.MeshBasicMaterial({color:0xffd2d5,transparent:true,opacity:.84});
 const particle=new THREE.SphereGeometry(.038,8,8);
 for(let i=0;i<12;i++){
   const orb=new THREE.Mesh(particle,trailMat.clone());
   brain.add(orb);trails.push(orb);
 }
 const ray=new THREE.Raycaster(),mouse=new THREE.Vector2();
 let startX=null,dragAngle=0,dragged=false;
 function onDown(e){startX=e.clientX;dragged=false;canvas.setPointerCapture?.(e.pointerId)}
 function onMove(e){if(startX!==null){let d=(e.clientX-startX)*.012;if(Math.abs(d)>.06)dragged=true;dragAngle+=d;startX=e.clientX;}}
 function onUp(e){
   if(!dragged){
     const b=canvas.getBoundingClientRect();mouse.set((e.clientX-b.left)/b.width*2-1,-(e.clientY-b.top)/b.height*2+1);
     ray.setFromCamera(mouse,camera);
     const hit=ray.intersectObjects(points.map(p=>p.mesh))[0];
     if(hit&&label)label.textContent='Señal didáctica seleccionada: '+hit.object.userData.name+' · no es una lectura cerebral.';
   }
   startX=null;
 }
 canvas.addEventListener('pointerdown',onDown);canvas.addEventListener('pointermove',onMove);canvas.addEventListener('pointerup',onUp);
 const history=[];
 let previous=-Infinity,secondsBack=0;
 const maxHistory=65;
 function tick(game,timeMs){
   if(canvas.clientWidth<=0||canvas.clientHeight<=0)return;
   const w=Math.max(100,Math.round(canvas.clientWidth)),h=Math.max(100,Math.round(canvas.clientHeight));
   if(canvas.width!==Math.round(w*renderer.getPixelRatio())||canvas.height!==Math.round(h*renderer.getPixelRatio()))
     renderer.setSize(w,h,false);
   if(timeMs-previous>170){
     previous=timeMs;
     history.push({t:timeMs,signal:brainActivity(game)});
     while(history.length>maxHistory)history.shift();
   }
   const selected=historySample(history,secondsBack,timeMs)?.signal||brainActivity(game);
   const l=Object.values(selected);
   brain.rotation.y=dragAngle+Math.sin(timeMs*.0003)*.18-.1;
   brain.rotation.x=Math.sin(timeMs*.00022)*.05;
   points.forEach((p,i)=>{
     const power=selected[p.name]||0;
     const v=.75+.4*power+Math.sin(timeMs*.004+i)*.07;
     p.mesh.scale.setScalar(v);
     p.mesh.material.opacity=.28+power*.7;
   });
   axons.forEach((x,i)=>{
     const level=(l[i%l.length]+l[(i+2)%l.length])/2;
     x.material.opacity=.08+level*.35;
   });
   trails.forEach((p,i)=>{
     const k=(timeMs*.00025+i/12)%1;
     const from=sites[i%sites.length][1],to=sites[(i+2)%sites.length][1];
     p.position.copy(from.clone().lerp(to,k));
     p.position.z+=Math.sin(k*Math.PI)*.24;
     p.material.opacity=.18+.6*(selected[sites[i%sites.length][0]]||0);
   });
   renderer.render(scene,camera);
   window.NPL_BRAIN_3D={visible:true,animated:true,historySamples:history.length,timeOffsetSeconds:secondsBack,
      nonclinical:true,regions:points.length,clickedRegions:points.map(p=>p.name)};
 }
 function setTimeAgo(n){secondsBack=Math.max(0,Math.min(12,Number(n)||0));}
 return {available:true,tick,setTimeAgo,dispose(){
   canvas.removeEventListener('pointerdown',onDown);
   canvas.removeEventListener('pointermove',onMove);
   canvas.removeEventListener('pointerup',onUp);
   renderer.dispose();
 }};
}
