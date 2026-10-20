import * as THREE from 'three';
import {assertTileManifest,planActiveTiles,plannedLayers,tileBounds,safeTilePath} from './city_tiles.mjs';
import {matrixElementsForMaster,VERTICAL_DATUM_VERIFIED} from './geo_alignment.mjs';
import {instantiateMasterPalms} from './asset_instancing.mjs';

/**
 * Optional local GLB recovery layer compatible with Three.js r169.
 * NOT the archived r128 renderer: reuse the caller's GLTFLoader and camera.
 * No new controls/NPCs/cars/network service; existing gameplay remains authoritative.
 * GlTF bytes are loaded only from same-origin localhost on explicit opt-in.
 */
export class RecoveredMasterTiles {
 constructor({scene,loader,profile='desktop',base='./world-master',onVisibility=()=>{}}){
   if(!scene?.add||!loader?.loadAsync)throw new TypeError('Need existing Three.js scene and GLTFLoader');
   if(!['desktop','mobile'].includes(profile)||base!=='./world-master')
     throw new Error('Invalid local-only tilepack configuration');
   this.scene=scene;this.loader=loader;this.profile=profile;this.base=base;
   this.onVisibility=onVisibility;
   this.root=new THREE.Group();this.root.name='RECOVERED_G19_WORLD_MASTER';
   this.root.matrix.fromArray(matrixElementsForMaster());
   this.root.matrixAutoUpdate=false;
   this.root.userData={crs:'EPSG:25830',verticalDatumVerified:VERTICAL_DATUM_VERIFIED,
     originalGameplayReplaced:false,source:'previous user-owned Drive world master'};
   this.states=new Map();this.inflight=new Map();
   this.errors=[];this.manifest=null;this.disposed=false;this.recoveredVisible=false;
   this.lastRequested=[];this.epoch=0;
 }
 async initialize(){
   if(this.disposed)throw new Error('Layer disposed');
   const r=await fetch(this.base+'/manifest.json',{cache:'no-store',credentials:'omit'});
   if(!r.ok)throw Error('Local recovered tilepack missing (HTTP '+r.status+')');
   const metadata=await r.json();
   this.manifest=assertTileManifest(metadata);
   this.scene.add(this.root);
   return this.status();
 }
 _tileAssetGroup(model,asset,tileId){
   const node=model.scene;
   if(!node?.isObject3D)throw Error('GLTF lacks scene');
   const obj=new THREE.Group();obj.name='MASTER_'+asset.role;
   if(asset.placements?.length){
     // Each archived palm is a genuine multi-part GLB. GPU instancing retains
     // the original geometry, UVs and materials and scales by validated poses.
     const instanced=instantiateMasterPalms(node,asset.placements,{mobile:this.profile==='mobile'});
     obj.add(instanced.group);
     obj.userData.palmInstancing=instanced.report;
   }else{
     obj.add(node);
     if(asset.local===true){
       const b=tileBounds(tileId);
       node.position.set(b.minX,0,b.minZ);
     }
   }
   obj.traverse(child=>{
     if(child.isMesh){child.castShadow=false;child.receiveShadow=true;
       child.frustumCulled=true;}
   });
   return obj;
 }
 async _loadAsset(asset,tileId,signal){
   if(this.disposed||signal.cancelled)return null;
   if(!safeTilePath(asset.path))throw Error('Untrusted GLB path');
   const source=this.base+'/'+asset.path;
   const parsed=new URL(source,document.baseURI);
   if(parsed.origin!==location.origin)throw Error('Cross-origin asset requests prohibited');
   const model=await this.loader.loadAsync(parsed.href);
   if(this.disposed||signal.cancelled)return null;
   return this._tileAssetGroup(model,asset,tileId);
 }
 async _ensureTile(id){
   if(this.states.has(id))return this.states.get(id).promise;
   const tile=this.manifest.tiles.find(t=>t.id===id);
   if(!tile)return false;
   const signal={cancelled:false};const group=new THREE.Group();
   group.name='WORLDMASTER_'+id;
   const state={id,group,signal,ready:false,loaded:0,errors:0,roles:new Set()};
   this.states.set(id,state);this.root.add(group);
   const layers=plannedLayers(tile,this.profile);
   const core=layers.filter(a=>['terrain','geo','architecture','mosaic','urban'].includes(a.role));
   const details=layers.filter(a=>!core.includes(a));
   const batch=async(list)=>{
     for(let n=0;n<list.length&&!signal.cancelled;n+=3){
       const segment=list.slice(n,n+3);
       const loaded=await Promise.all(segment.map(asset=>this._loadAsset(asset,id,signal)
           .catch(e=>{state.errors++;this.errors.push({tile:id,role:asset.role,
                  reason:String(e?.message||e).slice(0,160)});return null;})));
       loaded.forEach((node,i)=>{
         if(!node||signal.cancelled)return;
         node.visible=segment[i].role!=='lod';group.add(node);
         state.loaded++;state.roles.add(segment[i].role);
       });
     }
   };
   state.promise=(async()=>{
     // Geometry first: the starter region can become navigable before the large
     // original V50 mosaic, decoration and 24 optional architectural frontages.
     await batch(core);
     state.ready=!signal.cancelled && state.roles.has('terrain') &&
       (state.roles.has('architecture')||state.roles.has('mosaic')||state.roles.has('urban'));
     // No fake success if only a few assets load. Original OSM remains fallback.
     if(state.ready){
       state.detailsPromise=batch(details).catch(e=>{
         state.errors++;this.errors.push({tile:id,role:'details',reason:String(e).slice(0,160)});
       });
     }
     return state.ready;
   })();
   return state.promise;
 }
 _retire(id){
   const s=this.states.get(id);if(!s)return;
   s.signal.cancelled=true;this.root.remove(s.group);
   // GLB clones do not share cached renderer assets across tiles in this module.
   s.group.traverse(n=>{
     if(n.isMesh){n.geometry?.dispose?.();
       const mats=Array.isArray(n.material)?n.material:[n.material];
       mats.forEach(m=>{for(const prop of ['map','normalMap','roughnessMap','metalnessMap'])m?.[prop]?.dispose?.();m?.dispose?.();});
     }
   });
   this.states.delete(id);
 }
 async update(position){
   if(!this.manifest||this.disposed)return this.status();
   const x=position?.x,z=position?.z;
   if(!Number.isFinite(x)||!Number.isFinite(z))throw TypeError('Player location not finite');
   const desired=planActiveTiles(this.manifest,x,z,this.profile);
   const set=new Set(desired);this.lastRequested=desired;
   // Purge stale tiles before scheduling new ones; limit memory to two mobile/three desktop.
   for(const id of Array.from(this.states.keys()))if(!set.has(id))this._retire(id);
   await Promise.all(desired.map(id=>this._ensureTile(id)));
   const active=Array.from(this.states.values()).some(s=>s.ready&&s.loaded>0);
   if(active!==this.recoveredVisible){
     this.recoveredVisible=active;this.onVisibility(active);
   }
   return this.status();
 }
 status(){
   return {
     active:this.recoveredVisible,installed:!!this.manifest,profile:this.profile,
     tiles:Array.from(this.states.values()).filter(x=>x.ready).map(x=>x.id),
     assetsLoaded:Array.from(this.states.values()).reduce((n,s)=>n+s.loaded,0),
     errors:this.errors.slice(-12),
     georeferencedTo:'EPSG:3857_affine_approximate',
     millimetreFidelityCertified:false,verticalDatumVerified:false,
     privateAvatarsLoaded:false,publicRedistributionApproved:false
   };
 }
 dispose(){
   if(this.disposed)return;
   this.disposed=true;
   for(const id of [...this.states.keys()])this._retire(id);
   this.scene.remove(this.root);
   this.onVisibility(false);
 }
}
