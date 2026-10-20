import * as THREE from 'three';
import {NPL_PROCESS_IDS,NPL_PROCESS_INFO} from './npl_behavior.mjs';

/**
 * Procedural spatial cortex *visual analogy*. Not an MRI, a clinical brain
 * atlas, live neural activity, functional anatomy or a diagnostic instrument.
 * One small, rate-limited WebGL view and raycast clickable functional nodes.
 */
export const BRAIN3D_STATUS='interactive_3d_educational_model_not_medical_imaging';
const COLORS=Object.freeze({
 perception:0x5ebfd1,attention:0xe3b873,memory:0xdba4a0,
 reasoning:0xb3a3df,decision:0x8bbda0
});
const POINTS=Object.freeze({
 perception:[1.09,.24,.91],
 attention:[.55,.70,.76],
 memory:[-1.11,-.43,.76],
 reasoning:[-.77,.54,.93],
 decision:[-.22,.26,1.12]
});
function cerebralHemisphere(side,quality='desktop'){
 const detail=quality==='mobile'?20:38,geometry=new THREE.SphereGeometry(1,detail,Math.ceil(detail*.72));
 const p=geometry.getAttribute('position');
 const x=new THREE.Vector3();
 for(let i=0;i<p.count;i++){
  x.fromBufferAttribute(p,i);
  const wave=.035*Math.sin(x.x*21+x.y*8+side*.6)*Math.cos(x.z*19-x.x*5);
  const fold=.019*Math.sin(x.x*37+x.y*26);
  const r=1+wave+fold;
  p.setXYZ(i,x.x*.65*r,x.y*.88*r,x.z*1.02*r);
 }
 p.needsUpdate=true;geometry.computeVertexNormals();
 const mesh=new THREE.Mesh(geometry,new THREE.MeshStandardMaterial({
  color:0xbe9d90,roughness:.84,metalness:0,flatShading:false,
  transparent:false,side:THREE.FrontSide
 }));
 mesh.position.x=side*.69;
 mesh.rotation.y=side*.06;
 mesh.name=side<0?'NPL_illustrative_left_hemisphere':'NPL_illustrative_right_hemisphere';
 return mesh;
}
export function buildBrainModel({tier='desktop'}={}){
 if(!['desktop','mobile'].includes(tier))throw new RangeError('Invalid NPL brain LOD');
 const root=new THREE.Group();root.name='NPL_3D_INTERACTIVE_BRAIN_METAPHOR';
 const hemispheres=[cerebralHemisphere(-1,tier),cerebralHemisphere(1,tier)];
 root.add(...hemispheres);
 // Two separated cortical hemispheres and a clear longitudinal fissure.
 // This is illustrative geography, NEVER human MRI/clinical anatomy.
 const fissure=new THREE.Mesh(new THREE.CapsuleGeometry(.040,1.32,6,12),
   new THREE.MeshStandardMaterial({color:0x4e3039,roughness:1}));
 fissure.position.set(0,.03,.73);root.add(fissure);

 // Actual geometry of sulcal surface-following 3D tubes, not a 2D brain icon.
 // The lines are authored illustration and not reconstructed from a scan.
 const gyri=[];
 const sulcusMat=new THREE.MeshStandardMaterial({
   color:0x644a49,roughness:.98,transparent:true,opacity:.67,
   depthWrite:false
 });
 for(const side of [-1,1]){
  for(let band=0;band<(tier==='mobile'?7:12);band++){
   const pts=[],initial=-.70+band*(tier==='mobile'?.22:.128);
   for(let k=0;k<=20;k++){
    const t=k/20;
    const localX=-.52+t*1.04;
    const localY=initial+Math.sin(t*9.8+band*.7)*.052;
    const norm=(localX/.66)**2+(localY/.9)**2;
    if(norm>=.92)continue;
    const z=1.04*Math.sqrt(Math.max(.04,1-norm))+.027;
    pts.push(new THREE.Vector3(side*.69+localX,localY,z));
   }
   if(pts.length<4)continue;
   const curve=new THREE.CatmullRomCurve3(pts);
   const groove=new THREE.Mesh(new THREE.TubeGeometry(curve,25,.0095,5,false),sulcusMat);
   groove.name='NPL_STYLIZED_SULCUS_'+side+'_'+band;
   root.add(groove);gyri.push(groove);
  }
 }
 // Cerebellar lobes and brainstem remain non-interpretable sculptural context.
 const tissue=new THREE.MeshStandardMaterial({color:0xb58b81,roughness:.93});
 const cerebellum=new THREE.Group();cerebellum.name='NPL_ILLUSTRATIVE_CEREBELLUM';
 for(const side of [-1,1]){
  const lobe=new THREE.Mesh(new THREE.SphereGeometry(.34,tier==='mobile'?13:20,12),tissue);
  lobe.position.set(side*.27,-.72,-.78);lobe.scale.set(1.05,.72,.80);
  cerebellum.add(lobe);
 }
 const stem=new THREE.Mesh(new THREE.CylinderGeometry(.115,.18,.72,10),tissue);
 stem.position.set(0,-.94,-.38);stem.rotation.x=-.18;
 root.add(cerebellum,stem);
 const nodes=new Map(),glows=new Map();
 for(const id of NPL_PROCESS_IDS){
  const anchor=POINTS[id],location=new THREE.Vector3(...anchor);
  const material=new THREE.MeshStandardMaterial({
    color:COLORS[id],emissive:COLORS[id],emissiveIntensity:.28,
    metalness:.05,roughness:.33
  });
  const mesh=new THREE.Mesh(new THREE.SphereGeometry(tier==='mobile'?.105:.112,12,10),material);
  mesh.name='NPL_NODE_'+id;mesh.position.copy(location);
  mesh.userData={operation:id,scientificStatus:BRAIN3D_STATUS};
  const halo=new THREE.Mesh(new THREE.RingGeometry(.15,.205,24),
    new THREE.MeshBasicMaterial({color:COLORS[id],side:THREE.DoubleSide,
      transparent:true,opacity:.38,depthWrite:false}));
  halo.position.copy(location);halo.rotation.x=-.10;halo.name='NPL_HALO_'+id;
  root.add(mesh,halo);nodes.set(id,mesh);glows.set(id,halo);
 }
 const links=[['perception','attention'],['attention','memory'],
   ['memory','reasoning'],['reasoning','decision'],['perception','decision']];
 for(const [a,b] of links){
  const from=new THREE.Vector3(...POINTS[a]),to=new THREE.Vector3(...POINTS[b]);
  const middle=from.clone().add(to).multiplyScalar(.5);
  middle.z+=.22;
  const curve=new THREE.QuadraticBezierCurve3(from,middle,to);
  const tube=new THREE.Mesh(new THREE.TubeGeometry(curve,12,.012,5,false),
    new THREE.MeshBasicMaterial({color:0xe5c9ac,transparent:true,
      opacity:.26,depthWrite:false}));
  tube.name='NPL_illustrative_association_'+a+'_'+b;root.add(tube);
 }
 const snapshot={};
 function update(scores={},selected='perception'){
  if(!NPL_PROCESS_IDS.includes(selected))throw new RangeError('Invalid process selection');
  for(const id of NPL_PROCESS_IDS){
   const value=scores[id]??.12;
   if(!Number.isFinite(value)||value<0||value>1)throw new RangeError('Invalid observed input');
   const mesh=nodes.get(id),halo=glows.get(id);
   mesh.scale.setScalar((id===selected?1.24:1)+.23*value);
   mesh.material.emissiveIntensity=.18+.95*value;
   halo.material.opacity=(id===selected?.79:.20)+.30*value;
   halo.scale.setScalar(id===selected?1.18:1);
   snapshot[id]=value;
  }
  return {...snapshot,selected};
 }
 update();
 return {root,nodes,glows,hemispheres,links,gyri,cerebellum,
   metadata:Object.freeze({source:BRAIN3D_STATUS,tier,
     functionalNodes:5,drawOnlyWhenPanelOpen:true,
     anatomyValidated:false,brainActivityMeasured:false,
     realUserIdentityRequired:false}),
   update,
   dispose(){
    root.traverse(object=>{
     object.geometry?.dispose?.();
     const ms=Array.isArray(object.material)?object.material:[object.material];
     for(const m of ms)m?.dispose?.();
    });
   }
 };
}
export function mountBrain3D({canvas,details,onSelect,tier='desktop',reducedMotion=false}={}){
 if(!canvas||!details||typeof onSelect!=='function')throw TypeError('Brain canvas, panel and callback required');
 const model=buildBrainModel({tier});
 let renderer;
 try{
  renderer=new THREE.WebGLRenderer({
   canvas,alpha:true,antialias:tier==='desktop',powerPreference:'low-power'
  });
 }catch(error){
  model.dispose();
  return {available:false,status:'3D_UNAVAILABLE_ACCESSIBLE_TEXT_FALLBACK',
    error:String(error?.message||error).slice(0,95),
    update:()=>{},tick:()=>{},dispose:()=>{}};
 }
 renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,tier==='mobile'?1:1.25));
 renderer.setClearColor(0x18202c,0);
 renderer.outputColorSpace=THREE.SRGBColorSpace;
 const scene=new THREE.Scene();
 scene.add(model.root);
 scene.add(new THREE.HemisphereLight(0xe4e8ff,0x4f3034,1.8));
 const keylight=new THREE.DirectionalLight(0xffead0,2.7);
 keylight.position.set(-2,4,7);scene.add(keylight);
 const camera=new THREE.PerspectiveCamera(38,1,.1,100);
 camera.position.set(0,0.31,5.65);
 let orbit=-.12,tilt=-.08,frameTime=-1,dirty=true,lastWidth=0,lastHeight=0;
 const raycaster=new THREE.Raycaster(),pointer=new THREE.Vector2();
 let pointerState=null,selected='perception';
 const rotate=()=>{
  model.root.rotation.y=orbit;
  model.root.rotation.x=tilt;
 };
 const pointerXY=e=>{
  const r=canvas.getBoundingClientRect();
  return [(e.clientX-r.left)/Math.max(1,r.width),(e.clientY-r.top)/Math.max(1,r.height)];
 };
 const down=e=>{
  const [x,y]=pointerXY(e);
  pointerState={id:e.pointerId,x,y,lastX:x,lastY:y,moved:false};
  canvas.setPointerCapture?.(e.pointerId);
 };
 const move=e=>{
  if(!pointerState||pointerState.id!==e.pointerId)return;
  const [x,y]=pointerXY(e),diffX=x-pointerState.lastX,diffY=y-pointerState.lastY;
  if(Math.abs(x-pointerState.x)+Math.abs(y-pointerState.y)>.022)pointerState.moved=true;
  if(pointerState.moved){
   orbit=Math.max(-.9,Math.min(.9,orbit+diffX*3.5));
   tilt=Math.max(-.45,Math.min(.5,tilt+diffY*2.5));
   rotate();dirty=true;
  }
  pointerState.lastX=x;pointerState.lastY=y;
 };
 const up=e=>{
  if(!pointerState||pointerState.id!==e.pointerId)return;
  const previous=pointerState;pointerState=null;
  if(previous.moved)return;
  const [x,y]=pointerXY(e);
  pointer.set(x*2-1,-y*2+1);
  raycaster.setFromCamera(pointer,camera);
  const hits=raycaster.intersectObjects([...model.nodes.values()]);
  if(hits.length){
   const id=hits[0].object.userData.operation;
   selected=id;onSelect(id);
   dirty=true;
  }
 };
 canvas.addEventListener('pointerdown',down);
 canvas.addEventListener('pointermove',move);
 canvas.addEventListener('pointerup',up);
 canvas.addEventListener('pointercancel',()=>{pointerState=null;});
 canvas.setAttribute('role','img');
 canvas.setAttribute('aria-label','Cerebro 3D interactivo didáctico: selecciona regiones y gira con el puntero. No mide tu cerebro.');
 canvas.style.touchAction='none';
 return {
  available:true,model,status:BRAIN3D_STATUS,
  select(id){if(!NPL_PROCESS_IDS.includes(id))throw RangeError('Unknown brain process');
   selected=id;dirty=true;},
  update(scores,active=selected){model.update(scores,active);selected=active;dirty=true;},
  tick(seconds){
   if(!details.open||document.hidden||!Number.isFinite(seconds))return false;
   // Separate small 3D canvas should not steal the city's GPU budget.
   if(frameTime>=0&&seconds-frameTime<.085)return false;
   const w=Math.max(1,canvas.clientWidth),h=Math.max(1,canvas.clientHeight);
   if(w!==lastWidth||h!==lastHeight){
    lastWidth=w;lastHeight=h;
    renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();
    dirty=true;
   }
   if(!reducedMotion && !pointerState){
    model.root.rotation.y=orbit+Math.sin(seconds*.12)*.075;
    dirty=true;
   }
   if(!dirty)return false;
   renderer.render(scene,camera);frameTime=seconds;dirty=false;
   return true;
  },
  dispose(){
   canvas.removeEventListener('pointerdown',down);
   canvas.removeEventListener('pointermove',move);
   canvas.removeEventListener('pointerup',up);
   model.dispose();renderer.dispose();
  }
 };
}
