import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import {buildUrbanKit} from '../urban_kit.mjs';
import {injectPalmWindShader,animateExistingPublicPalmFronds,PALM_WIND_SOURCE,PALM_WIND_TIERS} from '../palm_canopy_wind.mjs';

const mock=()=>({
 uniforms:{},
 vertexShader:'void main(){\n#include <begin_vertex>\n#include <project_vertex>\n}',
 fragmentShader:'void main(){}'
});
test('wind alters only original 3D GPU-instanced palm fronds, not benches, trunks or ground',()=>{
 const {group,stats}=buildUrbanKit({tier:'desktop'});
 const geometries=new Map(group.children.map(m=>[m.name,m.geometry]));
 const materials=new Map(group.children.map(m=>[m.name,m.material]));
 const result=animateExistingPublicPalmFronds(group,{tier:'desktop'});
 assert.equal(result.source,PALM_WIND_SOURCE);
 assert.equal(result.canopyGroups,3);
 assert.equal(result.geometryAdded,0);
 assert.equal(result.drawCallsAdded,0);
 assert.equal(result.G19SourcePalmsAltered,false);
 assert.equal(group.children.length,11);
 assert.ok(stats.instances>0);
 for(const m of group.children){
   assert.equal(m.geometry,geometries.get(m.name));
   assert.equal(m.material,materials.get(m.name));
   if(m.name.includes('palm_canopies_')){
     const shader=mock();m.material.onBeforeCompile(shader);
     assert.match(shader.vertexShader,/ncPalmWindTime/);
     assert.match(shader.vertexShader,/smoothstep/);
     assert.match(shader.vertexShader,/transformed.x \+= sin/);
     assert.equal(shader.uniforms.ncPalmWindAmplitude.value,PALM_WIND_TIERS.desktop.amplitude);
   }else assert.equal(m.material.userData.ncPalmWind,undefined);
 }
 result.restore();
});
test('clock is bounded, animated material receives live uniform without recreating meshes',()=>{
 const {group}=buildUrbanKit({tier:'desktop'});
 const wind=animateExistingPublicPalmFronds(group);
 const canopy=group.children.find(x=>x.name.includes('palm_canopies_'));
 const shader=mock();canopy.material.onBeforeCompile(shader);
 wind.update(2.7);assert.equal(shader.uniforms.ncPalmWindTime.value,2.7);
 wind.update(2049);assert.equal(shader.uniforms.ncPalmWindTime.value,1);
 wind.pause(true);assert.equal(shader.uniforms.ncPalmWindAmplitude.value,0);
 wind.pause(false);assert.equal(shader.uniforms.ncPalmWindAmplitude.value,PALM_WIND_TIERS.desktop.amplitude);
 assert.throws(()=>wind.update(-3),RangeError);
 assert.throws(()=>wind.pause('pause'),TypeError);
 wind.restore();
 assert.equal(canopy.material.userData.ncPalmWind,undefined);
});
test('mobile LOD and reduced-motion keeps still silhouettes, no hidden avatar data',()=>{
 const {group}=buildUrbanKit({tier:'mobile'});
 const wind=animateExistingPublicPalmFronds(group,{tier:'mobile',reducedMotion:true});
 assert.equal(wind.canopyGroups,3);
 assert.equal(wind.isPaused(),true);
 assert.equal(wind.privateAvatarAssetsUsed,false);
 const canopy=group.children.find(x=>x.name.includes('palm_canopies_'));
 const shader=mock();canopy.material.onBeforeCompile(shader);
 assert.equal(shader.uniforms.ncPalmWindAmplitude.value,0);
 wind.update(3.5);
 assert.equal(shader.uniforms.ncPalmWindTime.value,3.5);
 wind.pause(false);
 assert.equal(shader.uniforms.ncPalmWindAmplitude.value,0);
 const desktopShader=mock(),mobileShader=mock();
 injectPalmWindShader(desktopShader,{tier:'desktop'});
 injectPalmWindShader(mobileShader,{tier:'mobile'});
 assert.ok(PALM_WIND_TIERS.mobile.amplitude<PALM_WIND_TIERS.desktop.amplitude);
 assert.notEqual(desktopShader.vertexShader,mobileShader.vertexShader);
 wind.restore();
});
test('missing shader hook or incorrect scene refuses mutation instead of faking motion',()=>{
 assert.throws(()=>animateExistingPublicPalmFronds({},{}),TypeError);
 assert.throws(()=>injectPalmWindShader({vertexShader:'abc'}),/marker missing/);
 assert.throws(()=>injectPalmWindShader(mock(),{tier:'ultra'}),RangeError);
});
test('idempotent wind registration and full restore preserves same material/mesh identity',()=>{
 const {group}=buildUrbanKit();
 const canopy=group.children.find(x=>x.name.includes('palm_canopies_'));
 const shaderOriginal=canopy.material.onBeforeCompile;
 const boundingRadius=canopy.boundingSphere.radius;
 const first=animateExistingPublicPalmFronds(group);
 const second=animateExistingPublicPalmFronds(group);
 assert.equal(first.canopyGroups,3);
 assert.equal(second.canopyGroups,0);
 second.restore();assert.ok(canopy.material.userData.ncPalmWind);
 first.restore();
 assert.equal(canopy.material.onBeforeCompile,shaderOriginal);
 assert.equal(canopy.boundingSphere.radius,boundingRadius);
});
