import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import {enhanceMappedBuildingFacades} from '../facade_stucco.mjs';
import {installCoveredOSMMask} from '../osm_building_mask.mjs';
import {patchMicroreliefShader,enhanceRealOSMWallMicrorelief,MICRORELIEF_SOURCE,MICRORELIEF_VERSION} from '../facade_microrelief.mjs';
const mock=()=>({
 uniforms:{},
 vertexShader:'void main(){\n#include <worldpos_vertex>\n}',
 fragmentShader:'void main(){\n#include <color_fragment>\n#include <normal_fragment_maps>\n#include <roughnessmap_fragment>\n#include <clipping_planes_fragment>\n}'
});
const world=()=>{
 const group=new THREE.Group();
 const build=name=>{
  const mesh=new THREE.Mesh(new THREE.BoxGeometry(8,18,5),
    new THREE.MeshStandardMaterial({name:'SOURCE',roughness:.87,color:0xf6dcc0}));
  mesh.name=name;group.add(mesh);return mesh;
 };
 const wall=build('OSM_Real_Building_Walls_UNTEXTURED');
 const road=build('OSM_REAL_vehicular_ways_not_surveyed_width');
 const archival=build('G19_ARCH_SOURCE_OWNER_PRIVATE_NO_TOUCH');
 return {group,wall,road,archival};
};
test('mapped OSM walls receive real PBR normal perturbation without geometry changes',()=>{
 const {group,wall,road,archival}=world();
 const wallGeo=wall.geometry,roadMaterial=road.material,archivalMaterial=archival.material;
 const stucco=enhanceMappedBuildingFacades(group,{tier:'desktop'});
 const originalStucco=wall.material,enhanced=enhanceRealOSMWallMicrorelief(group,{tier:'desktop'});
 assert.equal(enhanced.source,MICRORELIEF_SOURCE);
 assert.equal(enhanced.wallMeshes,1);
 assert.equal(enhanced.enhancedMaterials,1);
 assert.equal(enhanced.addedGeometryTriangles,0);
 assert.equal(enhanced.textureDownloads,0);
 assert.equal(enhanced.worldmasterGeometryModified,false);
 assert.equal(enhanced.avatarAssetsTouched,0);
 assert.equal(enhanced.scientificallyMatchedFacades,false);
 assert.equal(wall.geometry,wallGeo);
 assert.equal(road.material,roadMaterial);
 assert.equal(archival.material,archivalMaterial);
 const shader=mock();wall.material.onBeforeCompile(shader);
 assert.match(shader.fragmentShader,/ncFacadeWorld/);
 assert.match(shader.fragmentShader,/ncBump/);
 assert.match(shader.fragmentShader,/roughnessFactor = clamp/);
 assert.match(shader.fragmentShader,/plinth/);
 assert.match(wall.material.customProgramCacheKey(),new RegExp(MICRORELIEF_VERSION));
 enhanced.restore();
 const revert=mock();wall.material.onBeforeCompile(revert);
 assert.doesNotMatch(revert.fragmentShader,/ncBump/);
 assert.match(revert.fragmentShader,/plinth/);
 stucco.restore();assert.notEqual(wall.material,originalStucco);
});
test('G19 partial geometry mask remains chained after visual microrelief',()=>{
 const {group,wall}=world();
 const stucco=enhanceMappedBuildingFacades(group);
 const pbr=enhanceRealOSMWallMicrorelief(group);
 const coverage=installCoveredOSMMask(group);
 const shader=mock();wall.material.onBeforeCompile(shader);
 assert.match(shader.fragmentShader,/ncBump/);
 assert.match(shader.fragmentShader,/ncMasterTileBoxes/);
 assert.match(shader.fragmentShader,/clipping_planes_fragment/);
 coverage.restore();pbr.restore();stucco.restore();
});
test('mobile has lower PBR detail and guards shader incompatibility',()=>{
 const a=mock(),b=mock();
 a.fragmentShader+='\nvarying vec3 ncFacadeWorld;';
 b.fragmentShader+='\nvarying vec3 ncFacadeWorld;';
 patchMicroreliefShader(a,{tier:'desktop'});
 patchMicroreliefShader(b,{tier:'mobile'});
 assert.match(a.fragmentShader,/0\.120/);
 assert.match(b.fragmentShader,/0\.035/);
 assert.notEqual(a.fragmentShader,b.fragmentShader);
 assert.throws(()=>patchMicroreliefShader(mock(),{tier:'unknown'}),RangeError);
 assert.throws(()=>patchMicroreliefShader({fragmentShader:'void main(){}'}),/shader/);
});
test('no source-wall initialization means no visual modifications',()=>{
 const {group,wall}=world();const original=wall.material;
 const report=enhanceRealOSMWallMicrorelief(group);
 assert.equal(report.enhancedMaterials,0);
 assert.equal(wall.material,original);report.restore();
});
test('repeated activation is idempotent and reversible',()=>{
 const {group,wall}=world();
 const stucco=enhanceMappedBuildingFacades(group);
 const first=enhanceRealOSMWallMicrorelief(group);
 const second=enhanceRealOSMWallMicrorelief(group);
 assert.equal(first.enhancedMaterials,1);assert.equal(second.enhancedMaterials,0);
 assert.ok(wall.material.userData.ncMicrorelief);
 second.restore();assert.ok(wall.material.userData.ncMicrorelief);
 first.restore();assert.equal(wall.material.userData.ncMicrorelief,undefined);
 stucco.restore();
});
