import test from 'node:test';
import assert from 'node:assert/strict';
import {choosePixelRatio,nextAutoScale,qualityBudget,QUALITY_MODES} from './quality.mjs';
test('four quality modes and no implicit external data',()=>{
 assert.deepEqual(QUALITY_MODES,['auto','ultra','balanced','economy']);
 assert.equal(qualityBudget('economy').shadow,512);
 assert.equal(qualityBudget('ultra').shadow,2048);
});
test('pixel budget is respected at large 4K viewport',()=>{
 for(const mode of QUALITY_MODES){
   const ratio=choosePixelRatio({width:3840,height:2160,deviceRatio:3,mode});
   const max=qualityBudget(mode).maxPixels;
   assert.ok(3840*2160*ratio*ratio<=max*1.04,{mode,ratio});
 }
});
test('retina scales correctly and clamps invalid values',()=>{
 assert.equal(choosePixelRatio({width:390,height:844,deviceRatio:3,mode:'auto'}),2);
 assert.equal(choosePixelRatio({width:0,height:0,deviceRatio:2}),1);
 assert.equal(choosePixelRatio({width:100,height:100,deviceRatio:0}),1);
});
test('auto fidelity declines under sustained low fps, recovers only with headroom',()=>{
 assert.equal(nextAutoScale(1,24),.9);
 assert.equal(nextAutoScale(.6,20),.6);
 assert.equal(nextAutoScale(.9,60),.95);
 assert.equal(nextAutoScale(1,80),1);
 assert.equal(nextAutoScale(.85,45),.85);
});
