import test from 'node:test';
import assert from 'node:assert/strict';
import {planUrbanKit,makeKitReport,KIT_LICENSE,ARTISTIC_SCOPE} from '../urban_kit_layout.mjs';
import {buildUrbanKit} from '../urban_kit.mjs';

test('3D Mediterranean assets: determinism, location bounds, no surveyed claims',()=>{
 const a=planUrbanKit(),b=planUrbanKit();
 assert.deepEqual(a,b);
 assert.equal(a.license,KIT_LICENSE);
 assert.equal(a.scope,ARTISTIC_SCOPE);
 for(const group of [a.palms,a.benches,a.planters,a.cycles])
  for(const item of group){
   assert.ok(Number.isFinite(item.x)&&Number.isFinite(item.z));
   assert.ok(item.z>=-142&&item.z<=114);
  }
 assert.equal(makeKitReport(a).geodataSourceModified,false);
});
test('mobile reduces asset count and canopy polygon complexity without private models',()=>{
 const a=planUrbanKit('desktop'),b=planUrbanKit('mobile');
 assert.ok(a.instances>b.instances);
 assert.ok(a.config.fronds>b.config.fronds);
 assert.ok(a.config.segments>b.config.segments);
 assert.throws(()=>planUrbanKit('unsupported'),RangeError);
});
test('real Three.js mesh generation produces bounded instanced PBR geometry',()=>{
 for(const tier of ['desktop','mobile']){
  const {group,stats}=buildUrbanKit({tier});
  assert.equal(group.userData.instances,stats.instances);
  assert.ok(stats.palmCount>=10);
  assert.equal(stats.usesInstanceMeshes,true);
  assert.equal(stats.meshGroups,11);
  assert.equal(stats.palmSilhouettes,3);
  assert.equal(new Set(planUrbanKit(tier).palms.map(p=>p.variant)).size,3);
  assert.ok(stats.totalTriangles>0&&stats.totalTriangles<100000,stats.totalTriangles);
  assert.ok(group.children.every(o=>o.isInstancedMesh&&o.count>0&&o.geometry.boundingSphere));
  for(const mesh of group.children){
   const array=mesh.geometry.getAttribute('position').array;
   for(const v of array)assert.ok(Number.isFinite(v),'No infinite or NaN 3D vertices');
   assert.ok(mesh.material.isMeshStandardMaterial);
   assert.ok(!String(mesh.name).includes('PERSON'));
  }
 }
});
