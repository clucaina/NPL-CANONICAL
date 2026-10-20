import test from 'node:test';
import assert from 'node:assert/strict';
import {qualityProfile} from '../render_quality_policy.mjs';

test('pixel ratio 1 still switches between explicit high and low quality',()=>{
 const high=qualityProfile({high:true,coarse:false,devicePixelRatio:1});
 const low=qualityProfile({high:false,coarse:false,devicePixelRatio:1});
 assert.equal(high.pixelRatio,1);assert.equal(low.pixelRatio,1);
 assert.equal(high.shadowSize,2048);assert.equal(low.shadowSize,512);
 assert.equal(high.waterDetail,1);assert.equal(low.waterDetail,0);
 assert.equal(high.high,true);assert.equal(low.high,false);
});

test('mobile caps fill rate and disables high-frequency marine detail',()=>{
 const q=qualityProfile({high:true,coarse:true,devicePixelRatio:3});
 assert.deepEqual({tier:q.tier,pixelRatio:q.pixelRatio,shadowSize:q.shadowSize,waterDetail:q.waterDetail},
  {tier:'mobile',pixelRatio:1.35,shadowSize:1024,waterDetail:0});
 const reduced=qualityProfile({high:false,coarse:true,devicePixelRatio:2});
 assert.deepEqual({pixelRatio:reduced.pixelRatio,shadowSize:reduced.shadowSize,waterDetail:reduced.waterDetail},
  {pixelRatio:1,shadowSize:512,waterDetail:0});
});

test('desktop respects device scale within bounded optical budget',()=>{
 assert.equal(qualityProfile({high:true,coarse:false,devicePixelRatio:3}).pixelRatio,1.75);
 assert.equal(qualityProfile({high:false,coarse:false,devicePixelRatio:3}).pixelRatio,1);
});

test('bad values cannot silently enable extreme rendering settings',()=>{
 for(const args of [{high:'true',coarse:false,devicePixelRatio:1},{high:true,coarse:0,devicePixelRatio:1}])
  assert.throws(()=>qualityProfile(args),TypeError);
 for(const ratio of [0,-1,Number.NaN,Infinity])
  assert.throws(()=>qualityProfile({high:true,coarse:false,devicePixelRatio:ratio}),RangeError);
});
