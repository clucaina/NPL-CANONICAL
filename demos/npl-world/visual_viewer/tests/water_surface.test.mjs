import test from 'node:test';
import assert from 'node:assert/strict';
import {createWaterSurface,advanceWaterSurface,WATER_SOURCE} from '../water_surface.mjs';

test('Water shader uses two GPU triangles, no external images and no invented coastline',()=>{
 for(const tier of ['desktop','mobile']){
  const sea=createWaterSurface({tier});
  assert.ok(sea.isMesh&&sea.material.isShaderMaterial);
  assert.equal(sea.geometry.getAttribute('position').count,4);
  assert.equal(sea.geometry.index.count,6);
  assert.equal(sea.userData.waterQA.triangleCount,2);
  assert.equal(sea.userData.waterQA.drawCalls,1);
  assert.equal(sea.userData.waterQA.textures,0);
  assert.equal(sea.userData.waterQA.source,WATER_SOURCE);
  assert.equal(sea.userData.waterQA.geometrySurveyed,false);
  assert.equal(sea.userData.waterQA.originalOSMModified,false);
  assert.equal(sea.userData.waterQA.noPrivateAssets,true);
  assert.equal(sea.material.uniforms.uDetail.value,tier==='desktop'?1:0);
  assert.equal(sea.material.fog,true);
  assert.ok(sea.material.fragmentShader.includes('fog_fragment'));
  assert.ok(sea.material.fragmentShader.includes('colorspace_fragment'));
  assert.ok(sea.material.vertexShader.includes('fog_vertex'));
  sea.geometry.dispose();sea.material.dispose();
 }
});
test('Motion is bounded, optional and does not rebuild geometry',()=>{
 const sea=createWaterSurface();
 const geometry=sea.geometry;
 assert.equal(advanceWaterSurface(sea,17.5),17.5);
 assert.equal(advanceWaterSurface(sea,2050),2);
 assert.equal(sea.geometry,geometry);
 assert.throws(()=>advanceWaterSurface(sea,Infinity),RangeError);
 assert.throws(()=>advanceWaterSurface(sea,-1),RangeError);
 assert.throws(()=>advanceWaterSurface({},1),TypeError);
 const still=createWaterSurface({tier:'mobile',reducedMotion:true});
 assert.equal(advanceWaterSurface(still,90),0);
 assert.equal(still.userData.waterQA.animated,false);
});
test('Invalid quality and motion options are rejected',()=>{
 assert.throws(()=>createWaterSurface({tier:'ultra'}),RangeError);
 assert.throws(()=>createWaterSurface({reducedMotion:'no'}),TypeError);
});
