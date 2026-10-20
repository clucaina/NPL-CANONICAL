import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import {enhanceMappedBuildingFacades,isSourceBuildingWall,FACADE_SURFACE_SOURCE} from '../facade_stucco.mjs';
import {installCoveredOSMMask} from '../osm_building_mask.mjs';
test('world-projected Mediterranean material keeps exact OSM building mesh and roads',()=>{
 const city=new THREE.Group();
 const make=name=>{const obj=new THREE.Mesh(
   new THREE.BoxGeometry(3,8,3),new THREE.MeshStandardMaterial({color:0x777777}));
   obj.name=name;city.add(obj);return obj;};
 const wall=make('OSM_Real_Building_Walls_UNTEXTURED');
 const road=make('OSM_REAL_vehicular_ways_not_surveyed_width');
 const aerial=make('PNOA_ORTHOPHOTO_GROUND');
 const geo=wall.geometry,old=wall.material,asphalt=road.material,pnoa=aerial.material;
 const report=enhanceMappedBuildingFacades(city);
 assert.equal(report.source,FACADE_SURFACE_SOURCE);
 assert.equal(report.meshCount,1);
 assert.equal(report.extraVertices,0);
 assert.equal(report.colorsSurveyed,false);
 assert.equal(report.photoMatched,false);
 assert.equal(report.shopsFabricated,0);
 assert.equal(geo,wall.geometry);
 assert.notEqual(wall.material,old);
 assert.equal(road.material,asphalt);
 assert.equal(aerial.material,pnoa);
 const shader={uniforms:{},
  vertexShader:'start\n#include <worldpos_vertex>\nend',
  fragmentShader:'start\n#include <color_fragment>\nend'};
 wall.material.onBeforeCompile(shader);
 assert.match(shader.vertexShader,/ncFacadeWorld/);
 assert.match(shader.fragmentShader,/plinth/);
 assert.match(shader.fragmentShader,/diffuseColor\.rgb\*=ceramic/);
 const covered=installCoveredOSMMask(city);
 const maskedShader={uniforms:{},
  vertexShader:'begin\n#include <worldpos_vertex>\nend',
  fragmentShader:'begin\n#include <color_fragment>\n#include <clipping_planes_fragment>\nend'};
 wall.material.onBeforeCompile(maskedShader);
 assert.match(maskedShader.fragmentShader,/ncFacadeWorld/);
 assert.match(maskedShader.fragmentShader,/ncMasterTileBoxes/);
 covered.restore();
 assert.match(wall.material.name,/STUCCO/);
 report.restore();
 assert.equal(wall.material,old);
});
test('source OSM only, invalid tier blocked',()=>{
 assert.equal(isSourceBuildingWall('random fake brand'),false);
 assert.equal(isSourceBuildingWall('OSM_Real_Building_Walls_UNTEXTURED.001'),true);
 const city=new THREE.Group();
 assert.equal(enhanceMappedBuildingFacades(city).meshCount,0);
 assert.throws(()=>enhanceMappedBuildingFacades(city,{tier:'fake'}),RangeError);
});
