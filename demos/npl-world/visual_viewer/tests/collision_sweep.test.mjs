import test from 'node:test';
import assert from 'node:assert/strict';
import {sweptCircleHitsSegment,pointSegmentDistance} from '../collision_sweep.mjs';
const e={ax:0,az:0,bx:10,bz:0},r=.58;
const hit=(x,z,xx,zz,wall=e)=>sweptCircleHitsSegment(x,z,xx,zz,wall,r);
test('no wall tunnelling through opposite side in one <=1m physics frame',()=>{
 assert.equal(hit(5,-.45,5,.55),true);
 assert.equal(hit(5,-.7,5,.3),true);
});
test('approach to real segment capsule blocked',()=>assert.equal(hit(5,-.9,5,-.4),true));
test('parallel movement and escape from spawn overlap permitted',()=>{
 assert.equal(hit(5,-.9,5.5,-.9),false);
 assert.equal(hit(5,-.4,5,-.7),false);
 assert.equal(hit(5,-.3,5,-.3),false);
});
test('already overlapping wall cannot deepen penetration',()=>assert.equal(hit(5,-.5,5,-.1),true));
test('finite endpoint collision and non-wall passage',()=>{
 assert.equal(hit(10.65,-.65,10.35,-.35),true);
 assert.equal(hit(12,-.8,12,.2),false);
});
test('distances and nonfinite fail closed',()=>{
 assert.equal(pointSegmentDistance(5,1,0,0,10,0),1);
 assert.equal(pointSegmentDistance(12,0,0,0,10,0),2);
 assert.throws(()=>hit(NaN,0,1,1),RangeError);
 assert.throws(()=>pointSegmentDistance(0,0,NaN,0,1,1),RangeError);
});
