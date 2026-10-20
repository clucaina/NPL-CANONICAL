import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import {architectureMaskFromLoadedGLB,ARCH_CELLS} from '../g19_architecture_coverage.mjs';
import {installCoveredOSMMask} from '../osm_building_mask.mjs';
import {matrixElementsForTile} from '../geo_alignment.mjs';

function tileWithRoofs(){
 const tile=new THREE.Group();tile.matrix.fromArray(matrixElementsForTile('r02_c00'));
 tile.matrixAutoUpdate=false;
 const architecture=new THREE.Group();architecture.name='MASTER_architecture';
 tile.add(architecture);
 const roof=new THREE.BufferGeometry();
 roof.setAttribute('position',new THREE.Float32BufferAttribute([
  100,5,1100, 120,5,1100, 120,5,1120,
  100,5,1100, 120,5,1120, 100,5,1120
 ],3));
 const mesh=new THREE.Mesh(roof,new THREE.MeshStandardMaterial());mesh.name='G19_ARCH_ROOFS';
 architecture.add(mesh);
 const terrain=new THREE.Mesh(new THREE.PlaneGeometry(500,500),new THREE.MeshStandardMaterial());
 terrain.name='TERRAIN_NOT_BUILDING';tile.add(terrain);
 return {tile,mesh};
}
test('original G19 sparse roofs clip a few local cells, never a 500m OSM tile',()=>{
 const {tile}=tileWithRoofs();
 const report=architectureMaskFromLoadedGLB(tile,'r02_c00');
 assert.equal(report.sourceMeshes,1);
 assert.equal(report.sourceTriangles,2);
 assert.ok(report.coveredCells>40,report);
 assert.ok(report.coveredCells<750,report);
 assert.equal(report.data[55*ARCH_CELLS+55],255);
 assert.equal(report.data[240*ARCH_CELLS+240],0);
 assert.equal(report.certifiedGroundDatum,false);
});
test('missing or invisible source geometry does not hide OSM walls',()=>{
 const {tile,mesh}=tileWithRoofs();mesh.visible=false;
 const report=architectureMaskFromLoadedGLB(tile,'r02_c00');
 assert.equal(report.coveredCells,0);
 assert.equal(report.sourceMeshes,0);
});
test('wrong tile, nonfinite vertices and malformed geometry fail closed',()=>{
 const {tile,mesh}=tileWithRoofs();
 assert.throws(()=>architectureMaskFromLoadedGLB(tile,'r88_c88'));
 mesh.geometry.attributes.position.array[0]=NaN;
 assert.throws(()=>architectureMaskFromLoadedGLB(tile,'r02_c00'),/Nonfinite/);
});
test('new shader samples signed triangle occupancy, not whole-tile rectangles',()=>{
 const scene=new THREE.Group(),wall=new THREE.Mesh(new THREE.BoxGeometry(1,2,1),new THREE.MeshStandardMaterial());
 wall.name='OSM_Real_Building_Walls_UNTEXTURED';scene.add(wall);
 const original=wall.material,mask=installCoveredOSMMask(scene);
 const coverage=architectureMaskFromLoadedGLB(tileWithRoofs().tile,'r02_c00');
 const status=mask.update(['r02_c00'],[coverage]);
 assert.equal(status.geometryOccupancyPixels,coverage.coveredCells);
 assert.equal(status.wholeTileClipping,false);
 const shader={uniforms:{},vertexShader:'#include <worldpos_vertex>',
  fragmentShader:'#include <clipping_planes_fragment>'};
 wall.material.onBeforeCompile(shader);
 assert.match(shader.fragmentShader,/ncArchitectureAtlas/);
 assert.match(shader.fragmentShader,/texture2D\(ncArchitectureAtlas/);
 assert.equal(shader.uniforms.ncMasterTileCount.value,1);
 assert.ok(shader.uniforms.ncArchitectureAtlas.value.image.data.some(n=>n!==0));
 mask.update([]);
 assert.equal(mask.status().geometryOccupancyPixels,0);
 mask.restore();assert.equal(wall.material,original);
});
test('mask rejects forged mask dimensions or tile identifiers',()=>{
 const scene=new THREE.Group(),mask=installCoveredOSMMask(scene);
 assert.throws(()=>mask.update(['r02_c00'],[{tileId:'r02_c01',cells:256,data:new Uint8Array(256*256)}]));
 assert.throws(()=>mask.update(['r02_c00'],[{tileId:'r02_c00',cells:256,data:new Uint8Array(55)}]));
 mask.restore();
});
