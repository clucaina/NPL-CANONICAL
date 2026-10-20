import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import {inspectPublicCityModel} from '../city_geometry_qa.mjs';

const scene=()=>{
 const root=new THREE.Group();
 for(const name of ['OSM_Real_Building_Walls_UNTEXTURED','OSM_Real_Building_Roofs','OSM_REAL_vehicular_ways_not_surveyed_width']){
  const m=new THREE.Mesh(new THREE.BoxGeometry(3,4,5),new THREE.MeshBasicMaterial());m.name=name;root.add(m);
 }
 return root;
};
test('measures real mesh topology and mapped buildings without relying on declared counts',()=>{
 const qa=inspectPublicCityModel(scene());
 assert.equal(qa.meshCount,3);
 assert.equal(qa.triangleCount,36);
 assert.equal(qa.wallTriangles,12);
 assert.equal(qa.roofTriangles,12);
 assert.equal(qa.roadTriangles,12);
 assert.equal(qa.privateAvatarObjects,0);
 assert.ok(Object.isFrozen(qa));
});
test('rejects missing roof and wall geometry rather than accepting metadata claims',()=>{
 const root=scene();root.remove(root.children[1]);
 assert.throws(()=>inspectPublicCityModel(root),/missing valid roof and wall/);
});
test('never silently includes a private human or patient avatar in public geometry',()=>{
 const root=scene();
 const m=new THREE.Mesh(new THREE.BoxGeometry(1,1,1),new THREE.MeshBasicMaterial());
 m.name='PRIVATE_AVATAR_FACE_SCAN';root.add(m);
 assert.throws(()=>inspectPublicCityModel(root),/private geometry/);
});
test('rejects invalid graph and degenerate buffers',()=>{
 assert.throws(()=>inspectPublicCityModel(null),TypeError);
 const root=scene();
 root.children[0].geometry=new THREE.BufferGeometry();
 assert.throws(()=>inspectPublicCityModel(root),/missing valid roof and wall/);
});
