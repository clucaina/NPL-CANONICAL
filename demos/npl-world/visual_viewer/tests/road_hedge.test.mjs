import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import {pixelsForSurface,classifyOSMSurface,generateWorldPlaneUV,enhanceMappedOSMRoads,SURFACE_SOURCE} from '../road_surfaces.mjs';
import {planHedges,buildHedgeLayer,HEDGE_SOURCE} from '../hedge_layer.mjs';

test('real OSM surface markers only: no invented street layouts or private models',()=>{
 assert.equal(classifyOSMSurface('OSM_REAL_vehicular_ways_not_surveyed_width'),'vehicular');
 assert.equal(classifyOSMSurface('OSM_REAL_service_ways_not_surveyed_width'),'service');
 assert.equal(classifyOSMSurface('OSM_REAL_pedestrian_ways_not_surveyed_width'),'pedestrian');
 for(const item of ['OSM_Real_Building_Walls_UNTEXTURED','PERSON_Road','public_fake_road',''])
   assert.equal(classifyOSMSurface(item),null,item);
});

test('asphalt and masonry paving have deterministic non-uniform albedo with pixel budget',()=>{
 const a=pixelsForSurface('asphalt',64),b=pixelsForSurface('asphalt',64),c=pixelsForSurface('stone',64);
 assert.equal(a.length,64*64*4);
 assert.deepEqual(a,b);
 assert.notDeepEqual(a,c);
 assert.ok(new Set(a.filter((_,i)=>i%4===0)).size>25);
 assert.ok(a.every(Number.isFinite));
 assert.throws(()=>pixelsForSurface('medical',64),RangeError);
 assert.throws(()=>pixelsForSurface('asphalt',2048),RangeError);
});

test('source road coordinates project onto world UV; source position geometry stays untouched',()=>{
 const original=new THREE.PlaneGeometry(5,7);
 const mesh=new THREE.Mesh(original,new THREE.MeshBasicMaterial());
 mesh.rotation.x=-Math.PI/2;mesh.position.set(12,.015,-7);
 const transformed=generateWorldPlaneUV(mesh,2);
 assert.notEqual(original,transformed);
 assert.deepEqual([...transformed.getAttribute('position').array],[...original.getAttribute('position').array]);
 const uv=transformed.getAttribute('uv');
 assert.equal(uv.count,original.getAttribute('position').count);
 assert.ok(Number.isFinite(uv.getX(0))&&Number.isFinite(uv.getY(0)));
 assert.ok(uv.getX(0)>1);
});

test('scene applies real stone and asphalt only to source-classified OSM roads',()=>{
 const scene=new THREE.Group();
 function make(name){
  const g=new THREE.PlaneGeometry(5,7),mesh=new THREE.Mesh(g,new THREE.MeshBasicMaterial());
  mesh.name=name;scene.add(mesh);return mesh;
 }
 const road=make('OSM_REAL_vehicular_ways_not_surveyed_width');
 const paved=make('OSM_REAL_pedestrian_ways_not_surveyed_width');
 const building=make('OSM_Real_Building_Walls_UNTEXTURED');
 const before=building.material;
 const report=enhanceMappedOSMRoads(scene,{mobile:true});
 assert.equal(report.counts.vehicular,1);
 assert.equal(report.counts.pedestrian,1);
 assert.equal(report.asphaltMaterialApplied,true);
 assert.equal(report.source,SURFACE_SOURCE);
 assert.equal(report.originalSourceChanged,false);
 assert.match(road.material.name,/ASPHALT/);
 assert.match(paved.material.name,/PEDESTRIAN/);
 assert.equal(building.material,before);
 assert.equal(road.userData.roadSurface,'vehicular');
 assert.ok(road.geometry.getAttribute('uv').count>0);
});

test('hedge locations are deterministic and outside pedestrian center corridor',()=>{
 const desktop=planHedges('desktop'),mobile=planHedges('mobile');
 assert.deepEqual(desktop,planHedges('desktop'));
 assert.ok(desktop.count>190&&desktop.count<260,desktop.count);
 assert.ok(mobile.count<desktop.count&&mobile.count>=100);
 assert.equal(desktop.origin,HEDGE_SOURCE);
 assert.equal(desktop.privateImagesUsed,false);
 for(const p of desktop.hedges){
  assert.ok(p.x < -19 || p.x>6.8);
  assert.ok(p.z>=-135&&p.z<=104);
  assert.ok(p.height>=.7&&p.height<=1.1);
 }
 assert.throws(()=>planHedges('illegal'),RangeError);
});

test('3D hedges are actual GPU instanced meshes with triangle and draw call caps',()=>{
 for(const tier of ['desktop','mobile']){
  const {group,stats}=buildHedgeLayer(tier);
  assert.equal(group.children.length,5);
  assert.equal(stats.meshGroups,5);
  assert.equal(stats.allInstanced,true);
  assert.equal(stats.exactLocations,false);
  assert.equal(stats.sourceDataAltered,false);
  assert.ok(stats.totalTriangles>1000&&stats.totalTriangles<100000,stats.totalTriangles);
  for(const m of group.children){
   assert.ok(m.geometry.getAttribute('position').count>0);
   assert.ok(m.material.isMeshStandardMaterial);
   assert.equal(m.castShadow,false);
   assert.equal(m.count,stats.count);
  }
 }
});
