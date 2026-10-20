import test from 'node:test';
import assert from 'node:assert/strict';
import {plannedLayers} from '../city_tiles.mjs';

const asset=(role,name,triangle_estimate,embedded_images=1)=>({
 role,path:'assets/selected/'+name+'.glb',
 bytes:triangle_estimate*20,triangle_estimate,embedded_images,
 sha256:'a'.repeat(64)
});
test('V7 portable LOD: mandatory G19 layers cannot bypass 290k mobile budget (ported PR35)',()=>{
 const tile={assets:[
   asset('terrain','terrain',210000,12),
   asset('geo','geo',175000,7),
   asset('architecture','architecture',240000,9),
   asset('landmark','landmark',30000,5)
 ]};
 const layers=plannedLayers(tile,'mobile');
 assert.ok(layers.reduce((n,a)=>n+a.triangle_estimate,0)<=290000);
 assert.ok(layers.reduce((n,a)=>n+a.embedded_images,0)<=30);
 assert.ok(layers.some(a=>a.role==='terrain'));
 assert.ok(!layers.some(a=>a.role==='geo'));
});
test('V7 fallback never selects mobile mosaic physical 105k if signed low-LOD original available',()=>{
 const mosaic=asset('mosaic','mosaic4cm',105345,0);
 mosaic.mobile_fallback={path:'assets/selected/v50_original.glb',sha256:'b'.repeat(64),
   bytes:10000,triangle_estimate:5225,embedded_images:0};
 const [picked]=plannedLayers({assets:[mosaic]},'mobile');
 assert.equal(picked.mobileV50Fallback,true);
 assert.equal(picked.path,'assets/selected/v50_original.glb');
 assert.equal(picked.triangle_estimate,5225);
 assert.equal(picked.archaeologicalModelSource,'original_V50_PBR_not_procedural');
});
test('desktop V7 LOD priorities unchanged by mobile-only guard',()=>{
 const tile={assets:[asset('terrain','terrain',210000,12),asset('geo','geo',175000,7)]};
 const layers=plannedLayers(tile,'desktop');
 assert.equal(layers.length,2);
});
test('mobile floor is not marked ready by exceeding all mandatory layer budgets',()=>{
 const tile={assets:[asset('terrain','terrain',500000,18),asset('architecture','arch',600000,10)]};
 assert.equal(plannedLayers(tile,'mobile').length,0);
});
