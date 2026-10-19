import test from 'node:test';
import assert from 'node:assert/strict';
import {brainActivity,historySample} from '../brain_state.mjs';
test('game actions drive distinct synthetic activation components',()=>{
 const idle=brainActivity({moving:false,stage:0,dataReady:false});
 const walk=brainActivity({moving:true,stage:2,dataReady:true});
 assert.ok(walk.sensory>idle.sensory);
 assert.ok(walk.attention>idle.attention);
 assert.ok(walk.inference>idle.inference);
 assert.equal(walk.social,idle.social);
 for(const v of Object.values(walk))assert.ok(v>=0&&v<=1);
});
test('time selection returns earlier states without hallucinating historical observations',()=>{
 const hist=[{t:1000,signal:{sensory:.1}},{t:2000,signal:{sensory:.4}},{t:3000,signal:{sensory:.9}}];
 assert.equal(historySample(hist,0,3000).signal.sensory,.9);
 assert.equal(historySample(hist,1,3000).signal.sensory,.4);
 assert.equal(historySample(hist,2,3000).signal.sensory,.1);
 assert.equal(historySample(hist,0,100),hist[0]);
 assert.equal(historySample([],0,2000),null);
});
test('nonnumeric input never creates NaN activity',()=>{
 const values=brainActivity({stage:NaN,moving:true});
 assert.ok(Object.values(values).every(Number.isFinite));
});
