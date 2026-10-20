import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import {buildCityWallCollision} from '../city_collision.mjs';
test('actual Three wall geometry blocks a complete crossing',()=>{
 const root=new THREE.Group();
 const mesh=new THREE.Mesh(new THREE.BufferGeometry(),new THREE.MeshBasicMaterial());
 mesh.name='OSM_Real_Building_Walls_UNTEXTURED';
 mesh.geometry.setAttribute('position',new THREE.Float32BufferAttribute([0,0,0,10,0,0,10,5,0,0,0,0,10,5,0,0,5,0],3));
 root.add(mesh);
 const c=buildCityWallCollision(root);
 assert.equal(c.stats().wallSegments,1);
 assert.equal(c.hitsWall(5,-.45,5,.55),true);
 assert.equal(c.move(5,-.45,0,1).z,-.45);
});
