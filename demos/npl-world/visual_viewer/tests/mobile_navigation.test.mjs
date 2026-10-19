import test from 'node:test';
import assert from 'node:assert/strict';
import {normalizedStick,combineMovement} from '../mobile_navigation.mjs';

test('a touch joystick is bounded to a unit disk',()=>{
 assert.deepEqual(normalizedStick(0,0,50),{x:0,y:0});
 assert.deepEqual(normalizedStick(25,-25,50),{x:0.5,y:-0.5});
 const out=normalizedStick(200,-200,50);
 assert.ok(Math.abs(Math.hypot(out.x,out.y)-1)<1e-12);
 assert.deepEqual(normalizedStick(2,3,0),{x:0,y:0});
 assert.deepEqual(normalizedStick(NaN,3,40),{x:0,y:0});
});
test('analog input keeps precision while keyboard diagonal cannot sprint faster',()=>{
 assert.deepEqual(combineMovement(0,0,0.25,0),{forward:0.25,strafe:0,magnitude:0.25});
 const v=combineMovement(1,1,0,0);
 assert.ok(Math.abs(Math.hypot(v.forward,v.strafe)-1)<1e-12);
 const mixed=combineMovement(1,0,1,1);
 assert.ok(Math.hypot(mixed.forward,mixed.strafe)<=1.000001);
});
test('invalid input cannot propagate NaN to Three.js camera',()=>{
 assert.deepEqual(combineMovement(NaN,0,1,0),{forward:0,strafe:0,magnitude:0});
 assert.deepEqual(combineMovement(0,0,0,0),{forward:0,strafe:0,magnitude:0});
});
