import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import {RecoveredPhysicalAtlas} from '../world_physics.mjs';
import {buildCityWallCollision} from '../city_collision.mjs';

function sourceWall(){
 const root=new THREE.Group();
 const mesh=new THREE.Mesh(new THREE.BufferGeometry(),new THREE.MeshBasicMaterial());
 mesh.name='OSM_Real_Building_Walls_UNTEXTURED';
 mesh.geometry.setAttribute('position',new THREE.Float32BufferAttribute([
   0,0,0,10,0,0,10,5,0,
   0,0,0,10,5,0,0,5,0
 ],3));
 root.add(mesh);
 return buildCityWallCollision(root);
}
const atlasWith=(result)=>{
 const atlas=new RecoveredPhysicalAtlas();
 atlas.canOccupy=()=>result;
 return atlas;
};

test('signed G13 unavailable: real Three mesh wall blocks movement without tunnelling',()=>{
 const wall=sourceWall();
 assert.equal(wall.stats().wallSegments,1);
 const atlas=atlasWith({allowed:null,reason:'PHYSICAL_SOURCE_UNAVAILABLE'});
 const result=atlas.move({x:5,z:-.8},0,.44,{
  fallbackCollision:(x,z,toX,toZ)=>wall.hitsWall(x,z,toX,toZ)
 });
 assert.ok(result.z<=-.58,'crossing into real source wall capsule is forbidden');
 assert.ok(result.wallFallbackChecks>=2);
 assert.ok(result.wallFallbackBlocks>=1);
 assert.equal(result.unverifiedFallbackSubsteps,0);
 assert.equal(result.verifiedVerticalDatum,false);
});

test('known G13 blocking has priority, fallback wall is never consulted',()=>{
 const atlas=atlasWith({allowed:false,reason:'WATER_BUILDING_OR_UNMAPPED'});
 let calls=0;
 const result=atlas.move({x:5,z:-.8},0,.22,{
   fallbackCollision:()=>{calls++;return false;}
 });
 assert.equal(calls,0);
 assert.equal(result.z,-.8);
 assert.equal(result.wallFallbackChecks,0);
});

test('known walkable G13 has priority; source-wall fallback only checks missing coverage',()=>{
 const atlas=atlasWith({allowed:true,reason:'PROVISIONAL_GEO_SURFACE'});
 let calls=0;
 const result=atlas.move({x:5,z:-.8},0,.22,{
  fallbackCollision:()=>{calls++;return true;}
 });
 assert.equal(result.z,-.58);
 assert.equal(calls,0);
});

test('missing G13 with no wall source remains navigable but explicitly unverified',()=>{
 const atlas=atlasWith({allowed:null,reason:'PHYSICAL_SOURCE_UNAVAILABLE'});
 const result=atlas.move({x:5,z:3},.22,0);
 assert.ok(result.x>5);
 assert.equal(result.wallFallbackAvailable,false);
 assert.ok(result.unverifiedFallbackSubsteps>=1);
 assert.equal(result.verifiedVerticalDatum,false);
});

test('diagonal motion slides along actual GLB wall when signed G13 absent',()=>{
 const wall=sourceWall();
 const atlas=atlasWith({allowed:null,reason:'PHYSICAL_SOURCE_UNAVAILABLE'});
 const result=atlas.move({x:5,z:-.65},.4,.4,{
  fallbackCollision:(x,z,toX,toZ)=>wall.hitsWall(x,z,toX,toZ)
 });
 assert.ok(result.x>5.2);
 assert.equal(result.z,-.65);
 assert.ok(result.wallFallbackBlocks>=1);
});

test('source-wall safety callback must be synchronous boolean, rejects untrusted results',()=>{
 const atlas=atlasWith({allowed:null});
 assert.throws(()=>atlas.move({x:0,z:0},.1,0,{fallbackCollision:'yes'}),TypeError);
 assert.throws(()=>atlas.move({x:0,z:0},.1,0,{fallbackCollision:()=>null}),TypeError);
});
