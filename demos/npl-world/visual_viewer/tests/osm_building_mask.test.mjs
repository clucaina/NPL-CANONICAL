import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import {installCoveredOSMMask,maskableOSMName} from '../osm_building_mask.mjs';
import {plannedLayers} from '../city_tiles.mjs';

test('Original PNOA aerial and all real OSM streets survive a partial original-world tile',()=>{
 const scene=new THREE.Group();
 const make=name=>{
  const mesh=new THREE.Mesh(new THREE.PlaneGeometry(4,4),new THREE.MeshStandardMaterial());
  mesh.name=name;scene.add(mesh);return mesh;
 };
 const road=make('OSM_REAL_vehicular_ways_not_surveyed_width');
 const pedestrian=make('OSM_REAL_pedestrian_ways_not_surveyed_width');
 const aerial=make('ENV_Real_PNOA_Aerial_Not_Street_Facades');
 const wall=make('OSM_Real_Building_Walls_UNTEXTURED');
 const roof=make('OSM_Real_Building_Roofs');
 const originals=[wall.material,roof.material,road.material,pedestrian.material,aerial.material];
 const cover=installCoveredOSMMask(scene);
 assert.equal(cover.status().maskableOSMMeshes,2);
 assert.equal(wall.visible,true);assert.equal(roof.visible,true);
 assert.equal(road.material,originals[2]);
 assert.equal(pedestrian.material,originals[3]);
 assert.equal(aerial.material,originals[4]);
 assert.notEqual(wall.material,originals[0]);
 let status=cover.update(['r02_c00']);
 assert.deepEqual(status.coveredTiles,['r02_c00']);
 assert.equal(status.pnOAerialPreserved,true);
 assert.equal(status.osmAsphaltPreserved,true);
 const shader={
   uniforms:{},vertexShader:'before\n#include <worldpos_vertex>\nafter',
   fragmentShader:'before\n#include <clipping_planes_fragment>\nafter'
 };
 wall.material.onBeforeCompile(shader);
 assert.match(shader.vertexShader,/ncMasterWorldXZ/);
 assert.match(shader.fragmentShader,/discard/);
 assert.equal(shader.uniforms.ncMasterTileCount.value,1);
 assert.equal(shader.uniforms.ncMasterTileBoxes.value[0].z,1000);
 cover.update(['r02_c00','r02_c01']);
 assert.equal(shader.uniforms.ncMasterTileCount.value,2);
 assert.equal(shader.uniforms.ncMasterTileBoxes.value[1].x,500);
 cover.restore();
 assert.equal(wall.material,originals[0]);assert.equal(roof.material,originals[1]);
 assert.equal(road.material,originals[2]);
 assert.equal(road.visible,true);
});
test('Cannot silently clip the sea or any unpublished extra area',()=>{
 assert.equal(maskableOSMName('PNOA_ground_mesh'),false);
 assert.equal(maskableOSMName('OSM_Real_Building_Roofs'),true);
 const scene=new THREE.Group();
 const cover=installCoveredOSMMask(scene);
 assert.throws(()=>cover.update(['r99_c99']));
 assert.throws(()=>cover.update(['r02_c00','r02_c00']));
 assert.throws(()=>cover.update([{},'r02_c00']));
 cover.restore();
});
test('Mobile original 3D LOD maintains mapped core and rejects costly optional geometry',()=>{
 const asset=(role,tri,images=0)=>({
  role,path:'assets/selected/'+role+'.glb',bytes:tri*18,
  sha256:'a'.repeat(64),triangle_estimate:tri,embedded_images:images
 });
 const tile={assets:[
  asset('terrain',5000),asset('geo',4000),asset('urban',6000),
  asset('architecture',150000),asset('mosaic',10000,2),
  asset('landmark',320000,14),asset('facade',120000,12),
  asset('palm_variants',6500,0),asset('furniture',15000,3)
 ]};
 const mobile=plannedLayers(tile,'mobile');
 assert.ok(mobile.some(a=>a.role==='mosaic'));
 assert.ok(mobile.some(a=>a.role==='architecture'));
 assert.ok(mobile.some(a=>a.role==='palm_variants'));
 assert.ok(!mobile.some(a=>a.role==='landmark'));
 assert.ok(!mobile.some(a=>a.role==='facade'));
 assert.ok(!mobile.some(a=>a.role==='furniture'));
 const desktop=plannedLayers(tile,'desktop');
 assert.ok(desktop.some(a=>a.role==='landmark'));
 assert.ok(desktop.some(a=>a.role==='facade'));
});

test('original 18MB V50 furniture and 33KB source globe lamps are mutually exclusive per device',()=>{
 const common={sha256:'a'.repeat(64),triangle_estimate:100,embedded_images:0,bytes:33428};
 const tile={assets:[
  {...common,role:'terrain',path:'assets/source/ASSETS/tiles/r02_c00/terrain.glb'},
  {...common,role:'architecture',path:'assets/source/ASSETS/tiles/r02_c00/architecture.glb'},
  {...common,role:'furniture',path:'assets/selected/MASTER_EXPLANADA_FURNITURE_V50.glb',bytes:18_071_240},
  {...common,role:'streetlamp',path:'assets/prefabs/Farola_Globo_Simple_4m.glb',
   placements:[{x:280,y:2,z:1405,scale:1,rotation:0}]}
 ]};
 const mobile=plannedLayers(tile,'mobile').map(x=>x.role);
 const desktop=plannedLayers(tile,'desktop').map(x=>x.role);
 assert.ok(mobile.includes('streetlamp'));
 assert.ok(!mobile.includes('furniture'));
 assert.ok(desktop.includes('furniture'));
 assert.ok(!desktop.includes('streetlamp'));
});
