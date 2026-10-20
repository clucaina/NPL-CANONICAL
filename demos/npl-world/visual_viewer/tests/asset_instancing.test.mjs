import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import {instantiateMasterPalms} from '../asset_instancing.mjs';

function sourcePhoenix(){
 const scene=new THREE.Group();scene.name='real-archival-fixture';
 const stem=new THREE.Mesh(new THREE.CylinderGeometry(.15,.18,6,7),
                          new THREE.MeshStandardMaterial({color:0x715039}));
 stem.position.y=3;
 const canopy=new THREE.Mesh(new THREE.IcosahedronGeometry(2,1),
    new THREE.MeshStandardMaterial({color:0x46864b}));
 canopy.position.y=7;
 scene.add(stem,canopy);return scene;
}
const poses=[{x:23,y:1,z:1419,scale:.9,rotation:0},
             {x:28,y:1,z:1409,scale:1.2,rotation:Math.PI/2},
             {x:39,y:2,z:1400,scale:.8,rotation:Math.PI}];
test('original multimesh Phoenix geometry is instanced with precisely 2 GPU calls',()=>{
 const original=sourcePhoenix();
 const priorParts=original.children.map(m=>[m.geometry,m.material]);
 const {group,report}=instantiateMasterPalms(original,poses);
 assert.equal(report.palms,3);assert.equal(report.uniqueOriginalMeshes,2);
 assert.equal(report.drawCallsUpperBound,2);
 assert.equal(group.children.length,2);
 assert.equal(report.geometryRecreated,false);
 assert.ok(group.children.every(m=>m.isInstancedMesh&&m.count===3));
 group.children.forEach((m,i)=>{
    assert.equal(m.geometry,priorParts[i][0]);assert.equal(m.material,priorParts[i][1]);
 });
 const matrix=new THREE.Matrix4(),p=new THREE.Vector3(),q=new THREE.Quaternion(),scale=new THREE.Vector3();
 group.children[0].getMatrixAt(1,matrix);matrix.decompose(p,q,scale);
 assert.ok(Math.abs(p.x-28)<.001);
 assert.ok(Math.abs(p.y-(1+3*1.2))<.001);
 assert.ok(Math.abs(p.z-1409)<.001);
 assert.ok(Math.abs(scale.x-1.2)<.001);
 assert.equal(report.originalPositionsUsed,true);
 assert.equal(report.locationSurveyed,false);
});
test('mobile only displays a bounded half of actual authored placements',()=>{
 const {group,report}=instantiateMasterPalms(sourcePhoenix(),poses,{mobile:true});
 assert.equal(report.palms,2);
 assert.equal(report.mobileStride,2);
 assert.ok(group.children.every(m=>m.count===2));
});
test('reject impossible fake palm locations and animated rigs',()=>{
 assert.throws(()=>instantiateMasterPalms(sourcePhoenix(),[{x:Infinity,y:0,z:0,rotation:0,scale:1}]),RangeError);
 assert.throws(()=>instantiateMasterPalms(sourcePhoenix(),[{x:0,y:0,z:0,rotation:0,scale:0}]),RangeError);
 assert.throws(()=>instantiateMasterPalms(sourcePhoenix(),Array(161).fill(poses[0])),TypeError);
 const empty=new THREE.Group();assert.throws(()=>instantiateMasterPalms(empty,poses));
});
