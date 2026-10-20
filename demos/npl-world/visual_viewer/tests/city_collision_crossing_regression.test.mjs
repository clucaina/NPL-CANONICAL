import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import {buildCityWallCollision} from '../city_collision.mjs';

test('a player near a real wall must not cross its plane in one frame',()=>{
 const root=new THREE.Group();
 const mesh=new THREE.Mesh(new THREE.BufferGeometry(),new THREE.MeshBasicMaterial());
 mesh.name='OSM_Real_Building_Walls_UNTEXTURED';
 mesh.geometry.setAttribute('position',new THREE.Float32BufferAttribute([0,0,0,10,0,0,10,5,0,0,0,0,10,5,0,0,5,0],3));
 root.add(mesh);
 const collision=buildCityWallCollision(root);
 assert.equal(collision.hitsWall(5,-.45,5,.55),true);
});
