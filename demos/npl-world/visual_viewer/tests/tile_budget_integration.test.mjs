import test from 'node:test';
import assert from 'node:assert/strict';
import {plannedLayers} from '../city_tiles.mjs';
import {TILE_BUDGETS} from '../tile_budget_policy.mjs';

const asset=(role,triangles,images=1)=>({
 role,bytes:triangles*20,triangle_estimate:triangles,embedded_images:images,
 path:`assets/selected/${role}.glb`
});
const cost=(items)=>items.reduce((n,a)=>n+a.triangle_estimate,0);
const images=(items)=>items.reduce((n,a)=>n+a.embedded_images,0);

test('actual mobile planner does not exempt mandatory source geometry from budgets',()=>{
 const items=[asset('terrain',220_000),asset('architecture',200_000),asset('mosaic',40_000)];
 const before=structuredClone(items);
 const selected=plannedLayers({assets:items},'mobile');
 assert.deepEqual(selected.map(a=>a.role),['terrain','mosaic']);
 assert.ok(cost(selected)<=TILE_BUDGETS.mobile.triangles);
 assert.deepEqual(items,before,'source metadata must remain untouched');
});

test('oversized recovered terrain cannot bypass caps, allowing original OSM city fallback',()=>{
 const items=[asset('terrain',400_000),asset('architecture',10_000)];
 const selected=plannedLayers({assets:items},'mobile');
 assert.deepEqual(selected.map(a=>a.role),['architecture']);
 assert.ok(!selected.some(a=>a.role==='terrain'),
  'RecoveredMasterTiles requires terrain plus built geometry before hiding the OSM baseline');
});

test('large source images cannot bypass the policy because an asset is essential',()=>{
 const items=[asset('terrain',100,31),asset('architecture',100,30),asset('mosaic',100,1)];
 const selected=plannedLayers({assets:items},'mobile');
 assert.deepEqual(selected.map(a=>a.role),['architecture']);
 assert.ok(images(selected)<=TILE_BUDGETS.mobile.images);
});

test('original mobile restrictions still remove optional expensive GLB roles',()=>{
 const roles=['terrain','architecture','environment','driving','lod','facade','furniture','street'];
 const selected=plannedLayers({assets:roles.map(r=>asset(r,100))},'mobile');
 assert.deepEqual(selected.map(a=>a.role),['terrain','street','architecture']);
});

test('desktop preserves useful geometry while limiting it to its own budget',()=>{
 const items=[asset('terrain',850_000),asset('architecture',650_000),asset('urban',1)];
 const selected=plannedLayers({assets:items},'desktop');
 assert.deepEqual(selected.map(a=>a.role),['terrain','architecture']);
 assert.ok(cost(selected)<=TILE_BUDGETS.desktop.triangles);
});

test('invalid budget profile fails closed',()=>{
 assert.throws(()=>plannedLayers({assets:[asset('terrain',100)]},'tablet'),RangeError);
});
