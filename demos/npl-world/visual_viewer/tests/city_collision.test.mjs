import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import {buildCityWallCollision} from '../city_collision.mjs';

const wall=(x=0)=>{
 const root=new THREE.Group();
 const mesh=new THREE.Mesh(new THREE.BufferGeometry(),new THREE.MeshBasicMaterial());
 mesh.name='OSM_Real_Building_Walls_UNTEXTURED';
 mesh.geometry.setAttribute('position',new THREE.Float32BufferAttribute([
  0,0,0, 10,0,0, 10,5,0,
  0,0,0, 10,5,0, 0,5,0
 ],3));
 mesh.position.x=x;root.add(mesh);
 return root;
};
test('physical wall segments derive from real Three building mesh faces, not invented maps',()=>{
 const c=buildCityWallCollision(wall());
 assert.equal(c.stats().wallMeshes,1);
 assert.equal(c.stats().wallSegments,1);
 assert.equal(c.stats().trianglesScanned,2);
 assert.ok(c.stats().spatialCells>=1);
 assert.equal(c.stats().inventedBarriers,0);
});
test('walking toward actual wall is blocked and sliding along it is permitted',()=>{
 const c=buildCityWallCollision(wall());
 assert.equal(c.hitsWall(4,-.9,4,-.4),true);
 assert.equal(c.hitsWall(4,-.9,4,-1.5),false);
 const moved=c.move(4,-.9,.3,.5);
 assert.equal(moved.collided,true);
 assert.equal(moved.x,4.3);
 assert.equal(moved.z,-.9);
 assert.equal(c.stats().blockedMoves,1);
});
test('world-transformed geometry collides only at its real coordinates',()=>{
 const c=buildCityWallCollision(wall(15));
 assert.equal(c.hitsWall(20,-.8,20,-.4),true);
 assert.equal(c.hitsWall(5,-.8,5,-.4),false);
});
test('moves away from a spawn near walls are not frozen',()=>{
 const c=buildCityWallCollision(wall());
 assert.equal(c.move(5,-.4,0,-.3).collided,false);
 assert.equal(c.move(5,-.3,0,-.25).collided,false);
});
test('empty source falls back safely and unsafe nonlocal jumps fail',()=>{
 const c=buildCityWallCollision(new THREE.Group());
 assert.equal(c.stats().wallSegments,0);
 assert.equal(c.move(0,0,.2,.1).collided,false);
 assert.throws(()=>c.move(0,0,500,0),RangeError);
 assert.throws(()=>buildCityWallCollision(wall(),{radius:25}),RangeError);
 assert.throws(()=>c.move(NaN,0,0,0),RangeError);
});
