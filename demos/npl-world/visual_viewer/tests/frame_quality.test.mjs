import test from 'node:test';
import assert from 'node:assert/strict';
import {createFrameGovernor,qualityPlan} from '../frame_quality.mjs';
function stream(governor,{fps=30,seconds=16,start=0}={}){
 let changed=0;
 for(let t=start;t<start+seconds-1e-8;t+=1/fps)
   if(governor.sample(1000/fps,t))changed++;
 return changed;
}
test('all quality budgets preserve original 3D meshes, no private model changes',()=>{
 const ratios=['economy','balanced','detail'].map(t=>qualityPlan(t,{mobile:true,devicePixelRatio:3}).pixelRatio);
 assert.deepEqual(ratios,[.75,1,1.35]);
 assert.equal(qualityPlan('detail',{mobile:false,devicePixelRatio:2}).shadowSize,1536);
 assert.equal(qualityPlan('detail',{mobile:false,devicePixelRatio:1}).pixelRatio,1);
 for(const level of ['economy','balanced','detail']){
   const plan=qualityPlan(level);
   assert.equal(plan.geometryUnchanged,true);
   assert.equal(plan.privateAssetsTouched,false);
 }
 assert.throws(()=>qualityPlan('unbounded'),RangeError);
 assert.throws(()=>qualityPlan('balanced',{devicePixelRatio:-2}),RangeError);
});
test('sustained slow frames step down, not straight to zero quality',()=>{
 const g=createFrameGovernor({mobile:false,devicePixelRatio:2});
 const changes=stream(g,{fps:25,seconds:17});
 assert.equal(changes,1);
 assert.equal(g.snapshot().tier,'economy');
 assert.equal(g.snapshot().mode,'auto');
 assert.equal(g.snapshot().telemetryNetwork,false);
});
test('sustained smooth frames step UP without remeshing and with cooldown',()=>{
 const g=createFrameGovernor({mobile:false});
 stream(g,{fps:90,seconds:18});
 assert.equal(g.snapshot().tier,'detail');
 assert.equal(g.snapshot().noGLBMutation,true);
 assert.equal(g.snapshot().measuredInCurrentSession,true);
});
test('manual preference does not get overridden even with bad frames',()=>{
 const g=createFrameGovernor();
 g.setMode('detail');
 stream(g,{fps:15,seconds:28});
 assert.equal(g.snapshot().mode,'detail');
 assert.equal(g.snapshot().tier,'detail');
 g.setMode('economy');
 assert.equal(g.snapshot().tier,'economy');
 assert.equal(g.setMode('auto').mode,'auto');
 assert.throws(()=>g.setMode('CINEMATIC'),RangeError);
});
test('background tabs and scheduling stalls never produce fake low FPS promotions',()=>{
 const g=createFrameGovernor();
 for(let i=0;i<300;i++)g.sample(1000,i/60,{visible:false});
 assert.equal(g.snapshot().frameSamples,0);
 g.sample(800,6);
 assert.equal(g.snapshot().unclassifiedStalls,1);
 assert.equal(g.snapshot().observedFrameRateApprox,null);
 assert.equal(g.snapshot().tier,'balanced');
 stream(g,{fps:30,start:7,seconds:1});
 assert.equal(g.snapshot().tier,'balanced');
 assert.throws(()=>g.sample(NaN,10),RangeError);
 assert.throws(()=>g.sample(16,-1),RangeError);
});
test('small devices use different slowdown thresholds for software/hardware variation',()=>{
 const g=createFrameGovernor({mobile:true});
 // 32 ms is not a critical mobile frame budget, and must not trigger downshift.
 stream(g,{fps:31.25,seconds:19});
 assert.equal(g.snapshot().tier,'balanced');
 assert.ok(g.snapshot().observedP75FrameMs>=31);
});
