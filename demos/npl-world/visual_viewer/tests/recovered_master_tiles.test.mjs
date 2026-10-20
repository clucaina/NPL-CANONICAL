import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import {
  masterToViewer,viewerToMaster,matrixElementsForMaster,
  SOURCE_CRS,VIEWER_CRS,OBSERVED_MAX_AFFINE_RESIDUAL_M
} from '../geo_alignment.mjs';
import {
  assertTileManifest,planActiveTiles,plannedLayers,safeTilePath,tileBounds
} from '../city_tiles.mjs';
import {RecoveredMasterTiles} from '../world_master_loader.mjs';

const D='a'.repeat(64);
const asset=(name,role,local=false)=>({path:'assets/source/ASSETS/tiles/r02_c00/'+name+'.glb',
  role,sha256:D,bytes:400,local});
const fixture=()=>({
 schema:'neurocity.local-worldmaster-tiles.v1',crs:'EPSG:25830',
 viewer_crs:'EPSG:3857',vertical_datum_verified:false,
 public_redistribution_allowed:false,
 tiles:[
  {id:'r02_c00',assets:[asset('terrain','terrain',true),asset('architecture','architecture')]},
  {id:'r02_c01',assets:[{...asset('terrain','terrain',true),path:'assets/source/ASSETS/tiles/r02_c01/terrain.glb'}]},
  {id:'r01_c01',assets:[{...asset('terrain','terrain',true),path:'assets/source/ASSETS/tiles/r01_c01/terrain.glb'}]},
  {id:'r01_c02',assets:[{...asset('terrain','terrain',true),path:'assets/source/ASSETS/tiles/r01_c02/terrain.glb'}]}
 ]
});

test('ETRS89 UTM30 and Mercator inverse are finite and within documented approximation',()=>{
 assert.equal(SOURCE_CRS,'EPSG:25830');assert.equal(VIEWER_CRS,'EPSG:3857');
 assert.ok(OBSERVED_MAX_AFFINE_RESIDUAL_M>0.3);
 const pt=masterToViewer(240.783,1405.092);
 assert.ok(Math.abs(pt.x-(-10.664))<0.02,pt.x);
 assert.ok(Math.abs(pt.z-113.546)<0.02,pt.z);
 for(const [x,z] of [[0,0],[500,0],[0,500],[240,1400],[1200,1000]]){
   const a=masterToViewer(x,z),b=viewerToMaster(a.x,a.z);
   assert.ok(Math.abs(b.x-x)<1e-6 && Math.abs(b.z-z)<1e-6);
 }
 const m=new THREE.Matrix4().fromArray(matrixElementsForMaster());
 const v=new THREE.Vector3(240.783,4,1405.092).applyMatrix4(m);
 assert.ok(Math.abs(v.x-pt.x)<1e-6&&Math.abs(v.z-pt.z)<1e-6);
 assert.equal(v.y,4);
 assert.throws(()=>viewerToMaster(NaN,0));
});

test('manifest rejects unsafe assets, invented rights and suspect georeferencing',()=>{
 const base=fixture();assertTileManifest(base);
 assert.equal(safeTilePath('assets/source/ASSETS/G15/phoenix/Phoenix_DatePalm_Variant_06.glb'),true);
 for(const path of ['https://evil/a.glb','assets/../../private.glb','assets/source/ASSETS/G15/face.jpg',
  'assets/selected/../avatar.glb','/assets/selected/road.glb'])assert.equal(safeTilePath(path),false);
 let copy=structuredClone(base);copy.public_redistribution_allowed=true;assert.throws(()=>assertTileManifest(copy));
 copy=structuredClone(base);copy.tiles[0].assets[0].bytes=-1;assert.throws(()=>assertTileManifest(copy));
 copy=structuredClone(base);copy.tiles[0].assets[0].path='https://evil/a.glb';assert.throws(()=>assertTileManifest(copy));
 copy=structuredClone(base);copy.vertical_datum_verified=true;assert.throws(()=>assertTileManifest(copy));
});

test('nearby original four GEO tiles are selected with bounded mobile and desktop LOD',()=>{
 const m=fixture();
 assert.deepEqual(planActiveTiles(m,-10.664,113.546,'mobile').slice(0,1),['r02_c00']);
 assert.ok(planActiveTiles(m,-10.664,113.546,'mobile').length<=2);
 assert.ok(planActiveTiles(m,-10.664,113.546,'desktop').length<=3);
 assert.deepEqual(planActiveTiles(m,12000,12000,'desktop'),[]);
 assert.deepEqual(tileBounds('r02_c00'),{minX:0,maxX:500,minZ:1000,maxZ:1500});
 assert.throws(()=>tileBounds('r99_c99'));
 const detailed={assets:[
  asset('palms','palm_variants'),asset('furniture','furniture'),asset('terrain','terrain'),
  asset('building','architecture'),asset('monument','landmark')]};
 assert.ok(plannedLayers(detailed,'desktop').length>plannedLayers(detailed,'mobile').length);
});

test('real Three scene uses local GLBs only; native loader and original city fallback survive errors',async()=>{
 const scene=new THREE.Scene();
 const seen=[];
 const loader={loadAsync:async(url)=>{
   seen.push(url);
   const root=new THREE.Group();
   root.add(new THREE.Mesh(new THREE.BoxGeometry(1,1,1),new THREE.MeshStandardMaterial()));
   return {scene:root};
 }};
 const previousFetch=globalThis.fetch,previousDoc=globalThis.document,previousLoc=globalThis.location;
 globalThis.document={baseURI:'http://127.0.0.1:8766/'};
 globalThis.location={origin:'http://127.0.0.1:8766'};
 globalThis.fetch=async()=>({ok:true,json:async()=>fixture()});
 const visible=[];
 try{
   const streamer=new RecoveredMasterTiles({scene,loader,onVisibility:x=>visible.push(x)});
   await streamer.initialize();
   const stats=await streamer.update({x:-10.664,z:113.546});
   assert.equal(stats.active,true);
   assert.ok(stats.tiles.includes('r02_c00'));
   assert.equal(stats.millimetreFidelityCertified,false);
   assert.equal(stats.verticalDatumVerified,false);
   assert.equal(stats.privateAvatarsLoaded,false);
   assert.ok(stats.assetsLoaded>=2);
   assert.ok(seen.length>=2);
   assert.ok(seen.every(x=>x.startsWith('http://127.0.0.1:8766/world-master/assets/')));
   assert.deepEqual(visible,[true]);
   await streamer.update({x:100000,z:100000});
   assert.equal(streamer.status().active,false);
   assert.equal(scene.children.length,1);
   streamer.dispose();
   assert.equal(scene.children.length,0);
   assert.equal(visible.at(-1),false);
 }finally{globalThis.fetch=previousFetch;globalThis.document=previousDoc;globalThis.location=previousLoc;}
});
test('partial failed master tiles do not hide official OSM baseline',async()=>{
 const scene=new THREE.Scene(),base=fixture();
 const loader={loadAsync:async(url)=>{
   if(url.includes('architecture'))throw Error('decoding failed');
   return {scene:new THREE.Group()};
 }};
 const oldFetch=globalThis.fetch,oldDoc=globalThis.document,oldLoc=globalThis.location;
 globalThis.fetch=async()=>({ok:true,json:async()=>base});
 globalThis.document={baseURI:'http://localhost:8766/'};
 globalThis.location={origin:'http://localhost:8766'};
 let hidden=false;
 try{
   const engine=new RecoveredMasterTiles({scene,loader,onVisibility:x=>{hidden=x;}});
   await engine.initialize();await engine.update({x:-10.664,z:113.546});
   assert.equal(hidden,false);
   assert.equal(engine.status().active,false);
   assert.ok(engine.status().errors.length>=1);
   engine.dispose();
 }finally{globalThis.fetch=oldFetch;globalThis.document=oldDoc;globalThis.location=oldLoc;}
});
