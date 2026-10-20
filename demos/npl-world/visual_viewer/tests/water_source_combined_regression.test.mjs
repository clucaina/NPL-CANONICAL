import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import {createWaterSurface,enhanceSourceMappedWater,advanceWaterSurface,VERIFIED_WATER_NAME} from '../water_surface.mjs';

test('actual archived r169 ShaderMaterial always has fog uniforms',()=>{
 for(const tier of ['desktop','mobile']){
  const model=createWaterSurface({tier});
  for(const key of ['fogColor','fogDensity','fogNear','fogFar'])
   assert.ok(model.material.uniforms[key] && 'value' in model.material.uniforms[key],key);
  assert.equal(model.material.fog,true);
  model.geometry.dispose();model.material.dispose();
 }
});
test('real coastline mesh topology and buffer positions remain unchanged',()=>{
 const scene=new THREE.Group();
 const geometry=new THREE.BufferGeometry();
 geometry.setAttribute('position',new THREE.Float32BufferAttribute([0,0,0,8,0,0,8,8,0,0,8,0],3));
 geometry.setIndex([0,1,2,0,2,3]);
 const material=new THREE.MeshBasicMaterial();
 const mesh=new THREE.Mesh(geometry,material);
 mesh.name=VERIFIED_WATER_NAME;scene.add(mesh);
 const positions=new Float32Array(geometry.attributes.position.array);
 const op=enhanceSourceMappedWater(scene,{tier:'mobile',reducedMotion:true});
 assert.equal(op.originalVertices,4);assert.equal(op.addedSeaPlanes,0);
 assert.equal(mesh.geometry,geometry);
 assert.deepEqual(mesh.geometry.attributes.position.array,positions);
 op.advance(31);
 assert.equal(mesh.material.uniforms.uTime.value,0);
 op.restore();
 assert.equal(mesh.material,material);
 assert.equal(mesh.geometry,geometry);
 geometry.dispose();material.dispose();
});
