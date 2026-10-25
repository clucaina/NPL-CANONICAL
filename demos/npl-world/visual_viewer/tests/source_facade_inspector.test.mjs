import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import {nearestSourceFacadeView,placeInspectionCamera,WALL_INSPECTION_SOURCE} from '../source_facade_inspector.mjs';
const make=()=>{
 const city=new THREE.Group();
 const wall=new THREE.Mesh(new THREE.BoxGeometry(9,8,5),new THREE.MeshStandardMaterial());
 wall.name='OSM_Real_Building_Walls_UNTEXTURED';
 wall.position.set(-22,4,94);city.add(wall);
 const off=new THREE.Mesh(new THREE.BoxGeometry(6,8,6),new THREE.MeshStandardMaterial());
 off.name='G19_PRIVATE_ARCH_DO_NOT_TOUCH';off.position.set(-9,4,112);city.add(off);
 return {city,wall,off};
};
test('near-field camera comes exclusively from source OSM 3D triangles',()=>{
 const {city,wall,off}=make();
 const reference=new THREE.Vector3(-10.664,0,113.546);
 const oldMatrix=wall.matrixWorld.clone(),oldGeo=wall.geometry;
 const selected=nearestSourceFacadeView(city,reference,{maxDistance:90});
 assert.equal(selected.source,WALL_INSPECTION_SOURCE);
 assert.equal(selected.originalMesh,wall.name);
 assert.equal(selected.facadeSourceVerified,true);
 assert.equal(selected.geometryInvented,0);
 assert.equal(selected.surfaceVisualsArtisticNotSurveyed,true);
 assert.equal(wall.geometry,oldGeo);
 assert.equal(off.material.name,'');
 assert.ok(selected.distanceToObserver<40);
 assert.ok(selected.position.distanceTo(selected.target)<7);
 const camera=new THREE.PerspectiveCamera();
 const answer=placeInspectionCamera(camera,selected);
 assert.equal(answer.cameraMovedForQA,true);
 assert.equal(answer.playerMoved,false);
 assert.ok(camera.position.distanceTo(selected.position)<.0001);
});
test('missing source wall rejects invented/private geometry',()=>{
 const {city}=make();
 city.children.find(m=>m.name.startsWith('OSM_Real')).name='OWNER_PRIVATE_WALL';
 assert.equal(nearestSourceFacadeView(city,new THREE.Vector3(-10,0,100)),null);
});
test('faraway inspector returns no candidate instead of teleporting to false data',()=>{
 const {city}=make();
 assert.equal(nearestSourceFacadeView(city,new THREE.Vector3(800,0,800),{maxDistance:10}),null);
});
test('reject malformed camera or scene and preserve transforms',()=>{
 const {city}=make();
 assert.throws(()=>nearestSourceFacadeView(null,new THREE.Vector3()),TypeError);
 assert.throws(()=>nearestSourceFacadeView(city,new THREE.Vector3(),{maxDistance:-1}),TypeError);
 assert.throws(()=>placeInspectionCamera({},{}),TypeError);
});
