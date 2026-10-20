import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { nextCameraMode, canNavigate } from './navigation_policy.mjs';
import {normalizedStick,combineMovement} from './mobile_navigation.mjs';
import {buildUrbanKit} from './urban_kit.mjs';
import {RecoveredMasterTiles} from './world_master_loader.mjs';
import {RecoveredPhysicalAtlas} from './world_physics.mjs';
import {installCoveredOSMMask} from './osm_building_mask.mjs';
import {buildHedgeLayer} from './hedge_layer.mjs';
import {createSurfaceTexture,enhanceMappedOSMRoads} from './road_surfaces.mjs';
import {enhanceSourceMappedWater} from './water_surface.mjs';
import {createExplanadaMosaic} from './explanada_mosaic.mjs';
import {mountBrain3D} from './npl_brain3d.mjs';
import {startBehaviorSession,selectProcess,sampleBehavior,publicBehaviorSnapshot,NPL_PROCESS_IDS} from './npl_behavior.mjs';
import {inspectDataset,compareObservation,missionStart,missionStep,cognitivePulse,STAGES} from './neuro_mission.mjs';

// NPL WORLD - real GLB integration. No placeholder people, no pay-per-map API.
// Local public cartographic geometry + separate PRIVATE human GLB. Offline runtime.
const $=id=>document.getElementById(id);
const loading=$('loading'), info=$('info'), stat=$('stat'), progress=$('progress');
const view=$('game');
const publicPreview=window.NPL_PUBLIC_REVIEW===true;
const display=(message,problem=false)=>{$('messageText').textContent=message;info.classList.toggle('error',problem)};
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
// True archival G19/V50 ceramics win when the owner enables worldmaster=1;
// the public city gets a high-frequency original trencadís study, not LEGO pixels.
const mosaicKit=createExplanadaMosaic({
 tier:window.matchMedia?.('(pointer:coarse)')?.matches?'mobile':'desktop',
 renderer
});
const matStone=new THREE.MeshStandardMaterial({color:0xcbbda0,roughness:.94});
const matAsphalt=new THREE.MeshStandardMaterial({name:'NEUROCITY_ARTISTIC_ASPHALT',map:createSurfaceTexture('asphalt',256),color:0xffffff,roughness:.97,metalness:0});
const matMosaic=mosaicKit.material;
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
sea.rotation.x=-Math.PI/2;sea.position.set(395,-.17,-15);
// The public version now uses ONLY the truly mapped OSM harbor water mesh.
// Never lay this older approximate 750×1050m polygon over mapped coastal details.
sea.visible=!publicPreview;scene.add(sea);
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
function addFacadeDetail(group,maxDistance=Infinity){
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
   // LOD: public GPU budget limits artistic windows to nearby actual OSM walls.
   // These motifs are illustrative, not surveyed facade/window measurements.
   if(Math.hypot(mx+10.664,mz-113.546)>maxDistance)continue;
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
  mesh.instanceMatrix.needsUpdate=true;
  // Decorative details need no individual shadow pass on low-end/mobile GPUs.
  mesh.castShadow=false;mesh.receiveShadow=true;scene.add(mesh);
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
let osmCover=null;
let physicalAtlas=null,physicalPrefetchBusy=false,physicalLastPrefetch=0;
let recoveredMaster=null,masterNextUpdate=0,masterBusy=false;
const keys=new Set();
const touchStick={forward:0,strafe:0};
let yaw=-.65,pitch=.14,zoom=2.95,mode='back',actorHeading=0,moving=false;
let lastBehaviorYaw=yaw;
const loader=new GLTFLoader();
const model=(url)=>new Promise((resolve,reject)=>loader.load(url,resolve,undefined,reject));
const showLoad=(text)=>{progress.textContent=text;};
// Public preview deliberately excludes optional private human GLBs.
// The view-only city never reads personal avatars or patient records.

let nplEvidence={usable:false,reason:"no_public_dataset",entries:[]};
let behaviorSession=startBehaviorSession();
let brainRenderer=null,brainInspectPending=false,brainDecisionCount=0;
function updateBrainPanel(){
 const snapshot=publicBehaviorSnapshot(behaviorSession);
 const title=$('nplActiveTitle'),description=$('nplActiveDescription'),metrics=$('nplLiveMetrics');
 if(title)title.textContent=snapshot.selectedTitle;
 if(description)description.textContent=snapshot.selectedBasis+'. '+snapshot.disclaimer+' '+snapshot.nextAction;
 if(metrics)metrics.textContent='Recorrido '+snapshot.distanceMeters.toFixed(1)+' m · '+
   'Cámara '+snapshot.steeringRadians.toFixed(1)+' rad · Decisiones '+snapshot.choices;
 for(const button of document.querySelectorAll('#nplBrainProcesses [data-brain-process]'))
   button.setAttribute('aria-pressed',String(button.dataset.brainProcess===snapshot.selected));
 if(brainRenderer?.available)brainRenderer.update(snapshot.scores,snapshot.selected);
 window.NPL_BRAIN3D={
   mode:brainRenderer?.available?'REAL_INTERACTIVE_THREEJS':'ACCESSIBLE_FALLBACK',
   ...snapshot,brainActivityMeasured:false,
   onlyLocalObservedGameActions:true
 };
}
function chooseBrainProcess(id){
 behaviorSession=selectProcess(behaviorSession,id);
 brainRenderer?.select?.(id);brainInspectPending=true;updateBrainPanel();
}
let nplMission=missionStart(nplEvidence);
let lastMissionButtonsKey=null;
const taskChoices=[
  [["verificar_fuente","Comprobar procedencia, fecha y límites"],["suponer_sin_fuente","Aceptar sin comprobar"]],
  [["comparar_misma_poblacion","Comparar mismo periodo, unidad y población"],["mezclar_poblaciones","Comparar poblaciones distintas"]],
  [["separar_correlacion_causalidad","Explorar hipótesis alternativas"],["atribuir_causa_directa","Afirmar una causa sin contrastar"]],
  [["proponer_intervencion_evaluable","Proponer y evaluar una intervención"],["aplicar_sin_evaluar","Afirmar que funcionará"]]
];
function refreshNPL(moving=false){
 const flow=$('nplFlow');if(!flow)return;
 const p=cognitivePulse({moving,sourceReady:nplEvidence.usable,mission:nplMission});
 const operations=[["Entrada sensorial",p.senses],["Atención",p.attention],["Memoria de trabajo",p.memory],["Inferencia",p.inference],["Decisión",p.decision]];
 // Safe textContent: no raw HTML from data source or player.
 flow.replaceChildren(...operations.map(([k,v])=>{
   const d=document.createElement('div');d.className='npl-step';
   const left=document.createElement('span');left.textContent=k;
   const right=document.createElement('b');right.textContent=v;
   d.append(left,right);return d;
 }));
 const state=$('nplDataState');state.dataset.ready=String(nplEvidence.usable);
 state.textContent=nplEvidence.usable
  ? 'Fuente pública revisada disponible · '+nplEvidence.entries.length+' observaciones'
  : 'Sin base de datos pública aprobada · entrenamiento metodológico, NO indicador social real';
 $('nplMode').textContent=nplEvidence.usable?'Evidencia':'Entrenamiento';
 $('nplBrainLabel').textContent=p.disclaimer;
 $('nplMissionStage').textContent=nplMission.completed?'Misión completada · reflexión crítica'
  : 'Paso '+(nplMission.stage+1)+' de '+STAGES.length+' · '+STAGES[nplMission.stage];
 $('nplFeedback').textContent=nplMission.insight||'Investiga, contrasta y decide; no confundas percepción y evidencia.';
 const options=$('nplOptions');
 // Rendering a 3D city at low FPS must not detach active mission buttons every second.
 // Only replace their DOM nodes when the mission step actually changes.
 const key=nplMission.stage+':'+String(nplMission.completed);
 if(key!==lastMissionButtonsKey){
   options.replaceChildren();
   if(!nplMission.completed){
     for(const [code,label] of taskChoices[nplMission.stage]){
       const btn=document.createElement('button');btn.type='button';btn.textContent=label;
       btn.addEventListener('click',()=>{brainDecisionCount++;nplMission=missionStep(nplMission,code,nplEvidence);refreshNPL(moving);});
       options.appendChild(btn);
     }
   }else{
     const reset=document.createElement('button');reset.type='button';reset.textContent='↻ Nueva misión de investigación';
     reset.addEventListener('click',()=>{brainDecisionCount++;nplMission=missionStart(nplEvidence);refreshNPL(moving);});
     options.appendChild(reset);
   }
   lastMissionButtonsKey=key;
 }
 const summary=$('nplConflictSummary');
 if(!nplEvidence.usable){
   summary.textContent='Conflictos: no se presentan cifras sin procedencia revisada. NPL puede enseñar metodología mientras faltan datos.';
 }else{
   const indicator=nplEvidence.entries.find(x=>x.geo_code!=='ES');
   const v=indicator&&compareObservation(nplEvidence,indicator.indicator_id,indicator.geo_code);
   summary.textContent=v?.comparable
      ? 'Comparación descriptiva '+indicator.geo_code+' frente a España: '+v.difference.toFixed(2)+' '+v.unit+
        ' ('+v.period+'). No demuestra causalidad.'
      : 'Fuente revisada, pero faltan comparaciones homologables para este territorio.';
 }
 updateBrainPanel();
 window.NPL_MISSION={
    mode:nplMission.mode,stage:nplMission.stage,completed:nplMission.completed,
    publicEvidenceReady:nplEvidence.usable,noTracking:true,noSocialNetworking:true
 };
}
async function loadNPLOpenData(){
 // The file is optional and must be packaged ONLY after independent provenance review.
 // Any malformed, missing or unreviewed source keeps the training-only mode.
 if(!publicPreview){refreshNPL(false);return;}
 try{
   const response=await fetch('./assets/conflictometro_public_verified.json',{cache:'no-store'});
   if(!response.ok)throw new Error('dataset unavailable');
   nplEvidence=inspectDataset(await response.json());
 }catch(_){nplEvidence={usable:false,reason:'no_public_dataset',entries:[]};}
 nplMission=missionStart(nplEvidence);
 refreshNPL(false);
}
refreshNPL(false);
loadNPLOpenData();
let lastNplDraw=0;

// Public city decor: original CC0 procedural asset library, never a private GLB.
const visualTier=window.matchMedia?.('(pointer:coarse)')?.matches?'mobile':'desktop';
brainRenderer=mountBrain3D({
 canvas:$('nplBrainCanvas'),details:$('neurohud'),
 tier:visualTier,
 reducedMotion:window.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches===true,
 onSelect:chooseBrainProcess
});
for(const button of document.querySelectorAll('#nplBrainProcesses [data-brain-process]')){
 button.addEventListener('click',()=>chooseBrainProcess(button.dataset.brainProcess));
}
if($('nplBrainStatus'))$('nplBrainStatus').textContent=brainRenderer.available?
 'Gira y selecciona regiones · analogía funcional':'Vista 3D no disponible · controles accesibles activos';
updateBrainPanel();
const urbanKit=publicPreview?buildUrbanKit({tier:visualTier}):null;
const hedgeLayer=publicPreview?buildHedgeLayer(visualTier):null;
let roadStatus=null,coastalWater=null;
if(urbanKit){decorGroup.add(urbanKit.group);palmCount=urbanKit.stats.palmCount;}
if(hedgeLayer)decorGroup.add(hedgeLayer.group);

// Loading older Drive GEO is strictly LOCAL and opt-in; public artifacts NEVER
// fetch/copy privately-held geometry or replace native game actors/controllers.
let showingArchivedMaster=true;
function makeSourceComparisonControl(){
 let button=document.getElementById('ncCompareOriginalSources');
 if(button)return button;
 button=document.createElement('button');
 button.type='button';button.id='ncCompareOriginalSources';
 button.setAttribute('aria-label','Alternar entre la ciudad OSM PNOA y el mundo maestro 3D recuperado');
 button.style.cssText='position:fixed;right:16px;bottom:82px;z-index:45;background:#4d192a;color:#fff9ef;border:1px solid #f3dfcc;border-radius:12px;padding:12px 16px;font:600 12px system-ui;max-width:270px;box-shadow:0 10px 28px #0006;cursor:pointer;';
 const redraw=()=>{
   const ready=!!recoveredMaster?.status().active;
   if(recoveredMaster)recoveredMaster.root.visible=showingArchivedMaster;
   decorGroup.visible=!(ready&&showingArchivedMaster);
   osmCover?.update(ready&&showingArchivedMaster?recoveredMaster.status().tiles:[]);
   button.textContent=showingArchivedMaster?'Vista: mundo original G19 / V50  ·  Cambiar a OSM':'Vista: OSM / PNOA  ·  Cambiar a G19 / V50';
   button.setAttribute('aria-pressed',String(showingArchivedMaster));
   window.NPL_COMPARISON={originalMaster:showingArchivedMaster,
     fallbackGeography:true,privateImageryPublished:false};
 };
 button.addEventListener('click',()=>{
   showingArchivedMaster=!showingArchivedMaster;
   redraw();
 });
 document.body.appendChild(button);
 redraw();
 return button;
}
function startRecoveredMasterIfRequested(){
 if(!publicPreview || new URLSearchParams(location.search).get('worldmaster')!=='1')return;
 recoveredMaster=new RecoveredMasterTiles({
   scene,loader:new GLTFLoader(),profile:visualTier,
   onVisibility:(active)=>{
     // Never hide ALL Alicante because only one of four original tiles arrived.
     // PNOA ground and mapped asphalt remain visible; clip only covered walls.
     decorGroup.visible=!(active&&showingArchivedMaster);
   },
   onCoverage:(tileIds)=>{osmCover?.update(showingArchivedMaster?tileIds:[]);}
 });
 recoveredMaster.initialize().then(()=>recoveredMaster.update(player.position)).then(()=>{
   makeSourceComparisonControl();
   // SOURCE G13–G16 physics is local-only, hashed and independent of archived 3D.
   // Never use provisional G05 height as a certified terrain/sea elevation.
   physicalAtlas=new RecoveredPhysicalAtlas({maxTiles:visualTier==='mobile'?3:5});
   physicalAtlas.initialize()
     .then(()=>physicalAtlas.prefetch(player.position.x,player.position.z))
     .then(()=>{window.NPL_PHYSICS=physicalAtlas.status();})
     .catch(error=>{
       window.NPL_PHYSICS={status:'UNAVAILABLE_OSM_FALLBACK',
         reason:String(error?.message||error).slice(0,130),
         certifiedTerrain:false};
       physicalAtlas.dispose();physicalAtlas=null;
     });
   window.NPL_RECOVERED_GEO=recoveredMaster.status();
   if(recoveredMaster.status().active)
      display('Mundo maestro Drive recuperado: mosaico V50, fachada y vegetación original por teselas. Alturas y licencias pendientes de aprobación pública.');
 }).catch(err=>{
   window.NPL_RECOVERED_GEO={installed:false,error:String(err?.message||err).slice(0,160)};
   if(city)city.visible=true;decorGroup.visible=true;
   osmCover?.update([]);
   display('Mundo Drive opcional no instalado o no validado. Continúa Alicante OSM: '+String(err?.message||err).slice(0,110));
 });
}
function enterPublicCity(){
 $('face').disabled=true;
 $('face').title='Solo disponible cuando exista un avatar privado local';
 mode='first';
 $('cameraMode').textContent='Primera persona · ciudad pública';
 window.NPL_READY={cityMeshes:city?.children?.length||0,cityOnly:true,privateAvatarLoaded:false,
  explanadaCoords:[38.34318,-0.48326],windows:windowCount,facadeStyle:'artistic_not_surveyed',palms:palmCount,urbanKit:urbanKit?.stats||null,hedges:hedgeLayer?.stats||null,roadSurface:roadStatus,mosaic:mosaicKit.report,brain3D:{available:!!brainRenderer?.available,modelIsMetaphor:true},water:coastalWater?{
   waterMeshes:coastalWater.waterMeshes,addedSeaPlanes:coastalWater.addedSeaPlanes,
   sourceGeometryReplaced:coastalWater.sourceGeometryReplaced,
   reducedMotion:coastalWater.reducedMotion}:null,skins:0,clips:[]};
 loading.remove();
 showLoad('Ciudad pública geográfica lista');
 display('Alicante 3D OSM: asfalto en calles cartografiadas y setos ilustrativos. Fachadas no fotogramétricas; geometría y FPS reales sin certificar.');
}

async function loadWorld(){
 showLoad('Cargando modelo geográfico real de Alicante…');
 try{
  const data=await model('./assets/alicante.glb');
  city=data.scene;scene.add(city);
  if(publicPreview)osmCover=installCoveredOSMMask(city);
  // The source-matched asphalt texture belongs on OSM highway ribbon meshes, not on invented roads.
  if(publicPreview)roadStatus=enhanceMappedOSMRoads(city,{mobile:visualTier==='mobile'});
  if(publicPreview)coastalWater=enhanceSourceMappedWater(city,{
    tier:visualTier,reducedMotion:window.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches===true
  });
  // Public-only, bounded artistic facade detail on verifiable OSM wall geometry.
  // Never loads the optional private facade GLB.
  if(publicPreview)addFacadeDetail(city,170);
  // v11 architectural detail baked on exactly 150 ACTUAL OSM building-wall edges.
  // Geometry intentionally separate from the PNOA georeferenced base.
  if(!publicPreview) try {
    const decorData=await model('./assets/facades.glb');
    const facades=decorData.scene;
    facades.traverse(n=>{if(n.isMesh){n.castShadow=false;n.receiveShadow=true;}});
    scene.add(facades);
    windowCount=3679;
  }catch(err){display('Los edificios base se han cargado, pero falta el detalle GLB: '+err.message,true);}
  if(!publicPreview) await addRealPalmObjects();
  city.traverse(n=>{if(n.isMesh){n.receiveShadow=true;n.castShadow=true;if(n.material?.name?.includes('NO_photo')) n.material.roughness=.9;}});
  showLoad('Alicante 3D cargada: edificios reales y calle a nivel humano. Cargando cuerpo humano animado…');
 }catch(err){display('No se ha podido cargar la ciudad GLB: '+(err?.message||err),true);showLoad('ERROR: falta assets/alicante.glb');return;}
 if(publicPreview){enterPublicCity();startRecoveredMasterIfRequested();return;}
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
  enterPublicCity();
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
 const beforeX=player.position.x,beforeZ=player.position.z,beforeYaw=lastBehaviorYaw;
 if(recoveredMaster?.manifest && !masterBusy && clock.elapsedTime>=masterNextUpdate){
   masterNextUpdate=clock.elapsedTime+1.2;masterBusy=true;
   recoveredMaster.update(player.position).then(()=>{
      window.NPL_RECOVERED_GEO=recoveredMaster.status();
   }).catch(()=>{}).finally(()=>{masterBusy=false;});
 }
 if(physicalAtlas?.index && !physicalPrefetchBusy &&
    clock.elapsedTime-physicalLastPrefetch>2.5){
   physicalLastPrefetch=clock.elapsedTime;physicalPrefetchBusy=true;
   physicalAtlas.prefetch(player.position.x,player.position.z)
     .then(()=>{window.NPL_PHYSICS=physicalAtlas?.status()||null;})
     .catch(()=>{}).finally(()=>{physicalPrefetchBusy=false;});
 }
 const input=combineMovement(
  Number(keys.has('KeyW')||keys.has('ArrowUp'))-Number(keys.has('KeyS')||keys.has('ArrowDown')),
  Number(keys.has('KeyD')||keys.has('ArrowRight'))-Number(keys.has('KeyA')||keys.has('ArrowLeft')),
  touchStick.forward,touchStick.strafe
 );
 const {forward,strafe}=input, total=input.magnitude;
 moving=total>0.01 && canNavigate(city);
 if(clock.elapsedTime-lastNplDraw>=1){lastNplDraw=clock.elapsedTime;refreshNPL(moving);}
 const fast=keys.has('ShiftLeft')||keys.has('ShiftRight');
 if(moving){
  const speed=(fast?6.6:2.6)*dt;
  const dx=Math.sin(yaw)*forward-Math.cos(yaw)*strafe;
  const dz=Math.cos(yaw)*forward+Math.sin(yaw)*strafe;
  const deltaX=dx*speed,deltaZ=dz*speed;
  if(showingArchivedMaster && physicalAtlas?.index){
    const moved=physicalAtlas.move(player.position,deltaX,deltaZ);
    player.position.x=Math.max(-318,Math.min(402,moved.x));
    player.position.z=Math.max(-411,Math.min(304,moved.z));
    window.NPL_LAST_PHYSICS_MOVE={blockedSubsteps:moved.blockedSubsteps,
      fallbackSubsteps:moved.fallbackSubsteps,verticalDatumVerified:false};
  }else{
    player.position.x=Math.max(-318,Math.min(402,player.position.x+deltaX));
    player.position.z=Math.max(-411,Math.min(304,player.position.z+deltaZ));
  }
  actorHeading=Math.atan2(Math.sin(yaw)*Math.sign(forward),Math.cos(yaw)*Math.sign(forward));
  if(avatar&&Math.abs(forward)>.05){const headingDelta=Math.atan2(Math.sin(actorHeading-avatar.rotation.y),Math.cos(actorHeading-avatar.rotation.y));
    avatar.rotation.y+=headingDelta*Math.min(1,dt*7);}
  // Lateral input remains strafe rather than forcing a 90-degree turn.
 }
 // Every displayed NPL change follows ACTUAL movement/camera/choices in-session,
 // never fabricated brain-state or a diagnosis based on a game input.
 const actualDistance=Math.hypot(player.position.x-beforeX,player.position.z-beforeZ);
 const deltaTurn=Math.abs(Math.atan2(Math.sin(yaw-beforeYaw),Math.cos(yaw-beforeYaw)));
 behaviorSession=sampleBehavior(behaviorSession,{
   dt,movementMeters:actualDistance,cameraTurnRadians:deltaTurn,
   observed:brainInspectPending,
   obstructed:moving&&actualDistance<.0001,
   choices:brainDecisionCount,missionStage:nplMission.stage,
   sourceVerified:nplEvidence.usable
 });
 brainInspectPending=false;
 lastBehaviorYaw=yaw;
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
 if(coastalWater)coastalWater.advance(clock.elapsedTime);
 renderer.render(scene,camera);
 brainRenderer?.tick(clock.elapsedTime);
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
// One pointer steers the camera, another independently drives the virtual joystick.
let lookPointer=null,lastX=0,lastY=0;
view.addEventListener('pointerdown',e=>{
 if(lookPointer!==null)return;
 lookPointer=e.pointerId;lastX=e.clientX;lastY=e.clientY;
 view.setPointerCapture(e.pointerId);
});
function endLook(e){if(e.pointerId===lookPointer)lookPointer=null;}
view.addEventListener('pointerup',endLook);
view.addEventListener('pointercancel',endLook);
view.addEventListener('lostpointercapture',endLook);
view.addEventListener('pointermove',e=>{
 if(lookPointer!==e.pointerId)return;
 const dx=e.clientX-lastX,dy=e.clientY-lastY;lastX=e.clientX;lastY=e.clientY;
 yaw+=dx*.006;pitch=Math.max(-.08,Math.min(.92,pitch+dy*.004));
});
const pad=$('walkPad'),knob=$('walkKnob');
let walkPointer=null;
function setStickPosition(e){
 const bounds=pad.getBoundingClientRect();
 const radius=Math.min(bounds.width,bounds.height)*.34;
 const v=normalizedStick(e.clientX-(bounds.left+bounds.width/2),
                          e.clientY-(bounds.top+bounds.height/2),radius);
 touchStick.strafe=v.x;touchStick.forward=-v.y;
 knob.style.transform='translate('+Math.round(v.x*radius)+'px,'+Math.round(v.y*radius)+'px)';
 window.NEUROCITY_INPUT={...touchStick};
}
function releaseStick(e){
 if(e && e.pointerId!==walkPointer)return;
 walkPointer=null;touchStick.forward=0;touchStick.strafe=0;
 knob.style.transform='translate(0px,0px)';
 window.NEUROCITY_INPUT={...touchStick};
}
pad.addEventListener('pointerdown',e=>{
 if(walkPointer!==null)return;
 e.preventDefault();walkPointer=e.pointerId;
 pad.setPointerCapture(e.pointerId);setStickPosition(e);
});
pad.addEventListener('pointermove',e=>{if(walkPointer===e.pointerId)setStickPosition(e);});
pad.addEventListener('pointerup',releaseStick);
pad.addEventListener('pointercancel',releaseStick);
pad.addEventListener('lostpointercapture',releaseStick);
window.addEventListener('blur',()=>releaseStick());
window.NEUROCITY_INPUT={...touchStick};
view.addEventListener('wheel',e=>{e.preventDefault();zoom=Math.max(1.85,Math.min(28,zoom+Math.sign(e.deltaY)*.65));},{passive:false});
const cycleCamera=()=>{mode=nextCameraMode(mode,!!avatar);$('cameraMode').textContent=mode==='back'?'Tercera persona':mode==='face'?'Inspección facial':'Primera persona · ciudad pública';};
$('cam').onclick=cycleCamera;
$('reset').onclick=()=>{player.position.set(-10.664,0,113.546);yaw=-.65;mode=avatar?'back':'first';};
$('fidelity').onclick=()=>{let hi=renderer.getPixelRatio()<1.7;renderer.setPixelRatio(hi?Math.min(devicePixelRatio,2):1);sun.shadow.mapSize.set(hi?2048:1024,hi?2048:1024);sun.shadow.map?.dispose();sun.shadow.map=null;};
frame();
loadWorld();
