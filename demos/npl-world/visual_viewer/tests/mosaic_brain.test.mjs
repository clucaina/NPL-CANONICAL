import test from 'node:test';
import assert from 'node:assert/strict';
import {
  MOSAIC_SOURCE,MOSAIC_PALETTE,tileVariation,waveBand,
  mosaicDesign,paintMosaic
} from '../explanada_mosaic.mjs';
import {
  NPL_PROCESS_IDS,startBehaviorSession,sampleBehavior,selectProcess,
  publicBehaviorSnapshot,NPL_PROCESS_INFO
} from '../npl_behavior.mjs';
import {buildBrainModel,BRAIN3D_STATUS} from '../npl_brain3d.mjs';

test('ceramic wave has three shaded families and changes continuously along paseo',()=>{
 const info=mosaicDesign('desktop');
 assert.equal(info.source,MOSAIC_SOURCE);
 assert.ok(info.estimatedPieces>14000);
 assert.equal(info.photoDerived,false);
 assert.equal(info.historicalV50PreferredWhenAvailable,true);
 const samples=new Set();
 for(let x=0;x<1024;x+=20)for(let y=0;y<1536;y+=190)
   samples.add(waveBand(x,y));
 assert.deepEqual([...samples].sort(),['cream','slate','terracotta']);
 assert.notEqual(waveBand(150,100),waveBand(150,900));
 assert.equal(tileVariation(17,8),tileVariation(17,8));
 assert.notEqual(tileVariation(17,8),tileVariation(18,8));
 assert.equal(Object.keys(MOSAIC_PALETTE).length,3);
 assert.throws(()=>mosaicDesign('unknown'),RangeError);
});
test('real canvas tesserae cover thousands of irregular grout-separated polygons',()=>{
 let paths=0,fills=0,strokes=0,rects=0;const shades=new Set();
 const fakeCtx={
   fillStyle:'#000',strokeStyle:'',lineWidth:1,
   fillRect(){rects++;},
   beginPath(){paths++;},moveTo(){},lineTo(){},closePath(){},
   fill(){fills++;shades.add(this.fillStyle);},
   stroke(){strokes++}
 };
 const result=paintMosaic(fakeCtx,{tier:'desktop'});
 assert.equal(result.painted,result.estimatedPieces);
 assert.equal(fills,result.painted);
 assert.ok(paths>result.painted);
 assert.ok(strokes>result.painted/2);
 assert.equal(rects,1);
 assert.ok(shades.size>=10);
 assert.equal(result.surfaceEstimated,true);
 assert.equal(result.photoDerived,false);
});
test('NPL responds to REAL local walking, looking, obstacles and methodological choices',()=>{
 let session=startBehaviorSession();
 const before=publicBehaviorSnapshot(session);
 assert.equal(before.distanceMeters,0);
 assert.equal(before.patientData,false);
 assert.equal(before.diagnosticClaims,false);
 for(let i=0;i<50;i++)
   session=sampleBehavior(session,{
     dt:.1,movementMeters:.26,cameraTurnRadians:.04,
     obstructed:i===25,observed:i===30,
     missionStage:2,choices:3,sourceVerified:true
   });
 const after=publicBehaviorSnapshot(session);
 assert.equal(after.steps,2);
 assert.equal(after.choices,3);
 assert.equal(after.obstaclesObserved,1);
 assert.equal(after.distanceMeters,13);
 assert.ok(after.scores.perception>before.scores.perception);
 assert.ok(after.scores.attention>before.scores.attention);
 assert.ok(after.scores.memory>before.scores.memory);
 assert.equal(after.sourceVerified,true);
 assert.equal(after.personalDataPersisted,false);
 assert.match(after.interpretation,/NOT_NEURAL_MEASUREMENT/);
 session=selectProcess(session,'reasoning');
 const selected=publicBehaviorSnapshot(session);
 assert.equal(selected.selectedTitle,NPL_PROCESS_INFO.reasoning.title);
 assert.match(selected.disclaimer,/no mide/i);
 assert.throws(()=>selectProcess(session,'impulsivity_diagnosis'),RangeError);
 assert.throws(()=>sampleBehavior(session,{dt:-3}),RangeError);
});
test('3D cortex is a genuine selectable triangle mesh with 5 independently adjustable operations',()=>{
 for(const tier of ['mobile','desktop']){
   const brain=buildBrainModel({tier});
   assert.equal(brain.hemispheres.length,2);
   assert.equal(brain.nodes.size,5);
   assert.equal(brain.metadata.anatomyValidated,false);
   assert.equal(brain.metadata.brainActivityMeasured,false);
   assert.equal(brain.metadata.source,BRAIN3D_STATUS);
   const stats=brain.update({perception:.82,attention:.3,memory:.2,reasoning:.48,decision:.15},'reasoning');
   assert.equal(stats.selected,'reasoning');
   assert.deepEqual([...brain.nodes.keys()],NPL_PROCESS_IDS);
   const cortex=brain.hemispheres[0];
   assert.ok(cortex.isMesh&&cortex.geometry.getAttribute('position').count>100);
   assert.ok(cortex.geometry.index.count>1000);
   const sum=[...brain.nodes.values()].reduce((n,m)=>n+m.material.emissiveIntensity,0);
   assert.ok(sum>2);
   assert.throws(()=>brain.update({decision:3},'decision'),RangeError);
   brain.dispose();
 }
});
