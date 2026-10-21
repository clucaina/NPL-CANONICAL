import test from 'node:test';
import assert from 'node:assert/strict';
import { nextCameraMode, canNavigate } from '../navigation_policy.mjs';
test('city without private avatar remains navigable', () => {
 assert.equal(canNavigate({children:[1]}),true);
 assert.equal(canNavigate(null),false);
});
test('public camera never selects face inspection', () => {
 assert.equal(nextCameraMode('first',false),'back');
 assert.equal(nextCameraMode('back',false),'first');
 assert.equal(nextCameraMode('face',false),'first');
});
test('private avatar supports camera variants without regression',()=>{
 assert.equal(nextCameraMode('back',true),'face');
 assert.equal(nextCameraMode('face',true),'first');
 assert.equal(nextCameraMode('first',true),'back');
});
