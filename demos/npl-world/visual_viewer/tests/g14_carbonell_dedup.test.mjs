import test from 'node:test';
import assert from 'node:assert/strict';
import {hideCarbonellG19Duplicate} from '../g14_carbonell_dedup.mjs';
const ORIGINAL='assets/source/ASSETS/G14/G14_historic_carbonell_244990.glb';
const NEW='assets/selected/G14_CASA_CARBONELL_SOURCE_PRESERVED_L2_PRIVATE.glb';
function group(){
 const root={name:'WORLDMASTER_r02_c00',children:[],traverse(fn){function rec(n){fn(n);for(const c of n.children||[])rec(c);}rec(this);}};
 const arch={name:'MASTER_architecture',parent:root,children:[]};
 const real={name:'MASTER_landmark',parent:root,children:[]};
 root.children=[arch,real];
 for(const n of ['BU_244990_WALL','BU_244990_ROOF','BU_244990_GLASS','BU_244990_FRAMES','BU_244990_RAILS','BU_245010_WALL']){
  arch.children.push({name:n,isMesh:true,visible:true,parent:arch,userData:{}});
 }
 real.children.push({name:'G14_glass',isMesh:true,visible:true,parent:real,userData:{}});
 return {root,arch,real};
}
test('five generic BU_244990 meshes hide after signed original landmark arrives',()=>{
 const {root,arch,real}=group();
 const s=hideCarbonellG19Duplicate(root,{tileId:'r02_c00',landmarkPath:ORIGINAL,verifiedBytesLoaded:true});
 assert.equal(s.hidden,5);
 assert.equal(arch.children.filter(n=>!n.visible).length,5);
 assert.equal(arch.children[5].visible,true);
 assert.equal(real.children[0].visible,true);
});
test('G14 private L2 replaces same five meshes, not a new city or generic buildings',()=>{
 const {root}=group();
 const s=hideCarbonellG19Duplicate(root,{tileId:'r02_c00',landmarkPath:NEW,verifiedBytesLoaded:true});
 assert.equal(s.hidden,5);
});
test('failed or missing model keeps every fallback mesh',()=>{
 for(const path of [ORIGINAL,NEW]){
  const {root,arch}=group();
  const s=hideCarbonellG19Duplicate(root,{tileId:'r02_c00',landmarkPath:path,verifiedBytesLoaded:false});
  assert.equal(s.hidden,0);
  assert.ok(arch.children.every(n=>n.visible));
 }
});
test('not activated on another sector or unlisted model',()=>{
 for(const opt of [{tileId:'r02_c01',landmarkPath:NEW,verifiedBytesLoaded:true},{tileId:'r02_c00',landmarkPath:'assets/selected/fake.glb',verifiedBytesLoaded:true}]){
  const {root,arch}=group();
  assert.equal(hideCarbonellG19Duplicate(root,opt).hidden,0);
  assert.ok(arch.children.every(n=>n.visible));
 }
});
test('dedup is idempotent; no hidden actor counted twice',()=>{
 const {root}=group(),opt={tileId:'r02_c00',landmarkPath:NEW,verifiedBytesLoaded:true};
 assert.equal(hideCarbonellG19Duplicate(root,opt).hidden,5);
 assert.equal(hideCarbonellG19Duplicate(root,opt).hidden,0);
});
