import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import {buildCityWallCollision} from '../city_collision.mjs';

function actualWallStrip(count=50){
 const root=new THREE.Group();
 const positions=[];
 for(let i=0;i<count;i++){
  const x=i*3;
  positions.push(
    x,0,0, x+2,0,0, x+2,5,0,
    x,0,0, x+2,5,0, x,5,0
  );
 }
 const wall=new THREE.Mesh(new THREE.BufferGeometry(),new THREE.MeshBasicMaterial());
 wall.name='OSM_Real_Building_Walls_UNTEXTURED';
 wall.geometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));
 root.add(wall);
 return root;
}

test('combines existing PR41 acceptance with G19 swept walls: 48/48 checks',()=>{
 const collision=buildCityWallCollision(actualWallStrip());
 const before=collision.stats().blockedMoves;
 const audit=collision.auditSourceWallBlocking({samples:48});
 assert.equal(collision.stats().wallSegments,50);
 assert.equal(audit.examined,48);
 assert.equal(audit.blocked,48);
 assert.equal(audit.failed,0);
 assert.equal(audit.fullCrossingsBlocked,48);
 assert.equal(audit.allSampledBlocked,true);
 assert.equal(collision.stats().blockedMoves,before);
 assert.equal(audit.originalOwner,'G19_V50_swept_collision');
 assert.equal(audit.physicalHardwareCertified,false);
});

test('full wall crossing prohibited even when both endpoints are clear of wall',()=>{
 const collision=buildCityWallCollision(actualWallStrip(1));
 assert.equal(collision.hitsWall(1,-.8,1,.2),true);
 assert.equal(collision.move(1,-.45,0,1).z,-.45);
});
test('source acceptance refuses false positives from empty city',()=>{
 const collision=buildCityWallCollision(new THREE.Group());
 const audit=collision.auditSourceWallBlocking();
 assert.equal(audit.examined,0);
 assert.equal(audit.allSampledBlocked,false);
 assert.equal(audit.fullCrossingsBlocked,0);
});
test('sample budget is bounded and nonfinite input rejected',()=>{
 const collision=buildCityWallCollision(actualWallStrip(1));
 for(const value of [0,-1,257,NaN,Infinity,1.3])
  assert.throws(()=>collision.auditSourceWallBlocking({samples:value}),RangeError);
});
