import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import {enhanceSourceMappedWater,VERIFIED_WATER_NAME,WATER_SOURCE} from '../water_surface.mjs';

test('only actually mapped source-water geometry becomes animated Mediterranean sea',()=>{
 const city=new THREE.Group();
 const mapped=new THREE.Mesh(new THREE.PlaneGeometry(24,70),
       new THREE.MeshStandardMaterial({color:0x174d78}));
 mapped.name=VERIFIED_WATER_NAME;
 mapped.rotation.x=-Math.PI/2;
 const road=new THREE.Mesh(new THREE.BoxGeometry(3,.2,24),
       new THREE.MeshStandardMaterial({color:0x555555}));
 road.name='OSM_REAL_vehicular_ways_not_surveyed_width';
 city.add(mapped,road);
 const source=mapped.geometry,original=mapped.material,asphalt=road.material;
 const water=enhanceSourceMappedWater(city,{tier:'desktop'});
 assert.equal(water.waterMeshes,1);
 assert.equal(water.addedSeaPlanes,0);
 assert.equal(water.boatsInvented,0);
 assert.equal(water.sourceGeometryReplaced,false);
 assert.equal(mapped.geometry,source);
 assert.equal(road.material,asphalt);
 assert.equal(city.children.length,2);
 assert.ok(mapped.material.isShaderMaterial);
 assert.equal(mapped.userData.waterQA.source,WATER_SOURCE);
 assert.equal(mapped.userData.waterQA.attachedToRealOSMPolygon,true);
 assert.ok(mapped.material.vertexShader.includes('vLocal=vWorld.xz'));
 assert.ok(mapped.material.fragmentShader.includes('vec3(-3.0*slope.x,1.0,-3.0*slope.y)'));
 water.advance(17);
 assert.equal(mapped.material.uniforms.uTime.value,17);
 water.restore();
 assert.equal(mapped.material,original);
 assert.equal(road.material,asphalt);
 assert.equal(mapped.geometry,source);
});

test('reduced-motion mobile water is still and unaffected by camera frames',()=>{
 const scene=new THREE.Scene();
 const osm=new THREE.Mesh(new THREE.PlaneGeometry(2,2),
   new THREE.MeshStandardMaterial());osm.name=VERIFIED_WATER_NAME+'.001';
 scene.add(osm);
 const water=enhanceSourceMappedWater(scene,{tier:'mobile',reducedMotion:true});
 assert.equal(water.waterMeshes,1);
 assert.equal(water.tier,'mobile');
 assert.equal(water.reducedMotion,true);
 water.advance(100.3);
 assert.equal(osm.material.uniforms.uTime.value,0);
 assert.equal(osm.material.uniforms.uDetail.value,0);
 assert.throws(()=>water.advance(-10),RangeError);
 water.restore();
});

test('without OSM water shape do not create fake sea geometry',()=>{
 const city=new THREE.Scene();
 const old=new THREE.Mesh(new THREE.PlaneGeometry(1,1),new THREE.MeshBasicMaterial());
 old.name='OSM_mapped_coastline_NOT_VALID_WATER_POLYGON';
 city.add(old);
 const result=enhanceSourceMappedWater(city);
 assert.equal(result.waterMeshes,0);
 assert.equal(result.originalVertices,0);
 assert.equal(result.addedSeaPlanes,0);
 assert.equal(city.children.length,1);
 assert.equal(old.material.isMeshBasicMaterial,true);
 result.restore();
});
