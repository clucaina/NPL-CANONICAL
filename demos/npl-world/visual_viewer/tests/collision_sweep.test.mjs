import test from 'node:test';
import assert from 'node:assert/strict';
import {sweptCircleHitsSegment,withinLocalFloorTolerance,pointSegmentDistance} from '../collision_sweep.mjs';

const edge={ax:0,az:0,bx:10,bz:0},r=.58;
const hit=(x,z,xx,zz,e=edge)=>sweptCircleHitsSegment(x,z,xx,zz,e,r);

test('regression: crossing source wall from overlapping spawn is blocked',()=>{
 assert.equal(hit(5,-.45,5,.55),true);
});
test('tunnelling free-side to free-side in one step is blocked',()=>{
 assert.equal(hit(5,-.7,5,.3),true);
 assert.equal(hit(5,-.8,5,.2),true);
});
test('approaching collision capsule from outside is blocked',()=>{
 assert.equal(hit(5,-.9,5,-.4),true);
});
test('parallel travel outside and escape from already-overlapped walls are allowed',()=>{
 assert.equal(hit(5,-.9,5.5,-.9),false);
 assert.equal(hit(5,-.4,5,-.7),false);
 assert.equal(hit(5,-.3,5,-.3),false);
});
test('already embedded spawn cannot penetrate deeper into wall',()=>{
 assert.equal(hit(5,-.5,5,-.1),true);
 assert.equal(hit(5,-.4,5,-.4),false);
});
test('finite wall endpoint blocks close approach but not distant travel',()=>{
 assert.equal(hit(10.65,-.65,10.35,-.35),true);
 assert.equal(hit(12,-.8,12,.2),false);
});
test('closest-segment geometry handles projections and endpoints',()=>{
 assert.equal(pointSegmentDistance(5,1,0,0,10,0),1);
 assert.equal(pointSegmentDistance(12,0,0,0,10,0),2);
});
test('local vertical mismatch above 2m is rejected without altitude claims',()=>{
 assert.equal(withinLocalFloorTolerance(-2.2,-.1),false);
 assert.equal(withinLocalFloorTolerance(-2.1,-.1),true);
 assert.equal(withinLocalFloorTolerance(0,0),true);
 assert.equal(withinLocalFloorTolerance(2.01,0),false);
 assert.throws(()=>withinLocalFloorTolerance(0,0,3),RangeError);
});
test('nonfinite geometry cannot bypass QA',()=>{
 assert.throws(()=>hit(NaN,0,1,1),RangeError);
 assert.throws(()=>pointSegmentDistance(0,0,NaN,0,1,1),RangeError);
});
