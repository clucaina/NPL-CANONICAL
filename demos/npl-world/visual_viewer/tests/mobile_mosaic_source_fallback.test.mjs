import test from 'node:test';
import assert from 'node:assert/strict';
import {plannedLayers,assertTileManifest} from '../city_tiles.mjs';
const source='assets/selected/Explanada_v50_PBR_1024.glb';
const physical='assets/selected/Explanada_V50_Surgical_4cm_STONES_PRIVATE.glb';
const hash='a'.repeat(64);
const mk=(role,path,triangles,more={})=>({role,path,sha256:hash,bytes:50000,
 triangle_estimate:triangles,embedded_images:2,...more});
const mobile={path:source,sha256:'b'.repeat(64),bytes:3568880,triangle_estimate:5225,embedded_images:2};
const assets=[mk('terrain','assets/source/ASSETS/tiles/r02_c00/terrain.glb',7470,{local:true}),
 mk('geo','assets/source/ASSETS/tiles/r02_c00/geo.glb',7310,{local:true}),
 mk('mosaic',physical,105345,{mobile_fallback:mobile}),
 mk('architecture','assets/source/ASSETS/tiles/r02_c00/architecture.glb',148554),
 mk('urban','assets/source/ASSETS/tiles/r02_c00/urban.glb',354),
 mk('environment','assets/source/ASSETS/tiles/r02_c00/environment.glb',60953)];
const manifest=()=>({schema:'neurocity.local-worldmaster-tiles.v1',crs:'EPSG:25830',vertical_datum_verified:false,
 public_redistribution_allowed:false,tiles:[{id:'r02_c00',assets:structuredClone(assets)}]});
test('desktop loads physical stones, mobile loads ORIGINAL signed V50 lighter mesh',()=>{
 const m=manifest();assertTileManifest(m);
 const desktop=plannedLayers(m.tiles[0],'desktop');const mob=plannedLayers(m.tiles[0],'mobile');
 assert.equal(desktop.find(a=>a.role==='mosaic').path,physical);
 assert.equal(mob.find(a=>a.role==='mosaic').path,source);
 assert.equal(mob.find(a=>a.role==='mosaic').sha256,mobile.sha256);
 assert.equal(mob.find(a=>a.role==='mosaic').mobileFallbackApplied,true);
 assert.ok(mob.reduce((s,a)=>s+(a.triangle_estimate||0),0)<=290000);
 assert.equal(m.tiles[0].assets[2].path,physical,'do not mutate original manifest');
});
test('unconditional core layers cannot silently exceed mobile triangle budget',()=>{
 const m=manifest();m.tiles[0].assets.find(a=>a.role==='architecture').triangle_estimate=390000;
 assertTileManifest(m);const loaded=plannedLayers(m.tiles[0],'mobile');
 assert.equal(loaded.some(a=>a.role==='architecture'),false);
 assert.ok(loaded.find(a=>a.role==='mosaic'));
 assert.ok(loaded.reduce((s,a)=>s+(a.triangle_estimate||0),0)<=290000);
});
test('unsafe mobile path, forged digest or unrelated fallback role fail closed',()=>{
 for(const bad of [
   {path:'../../secret.glb'},
   {sha256:'x'.repeat(64)},
   {bytes:-1},
   {triangle_estimate:5_000_000},
   {embedded_images:NaN},
   {path:physical}
 ]){const m=manifest();Object.assign(m.tiles[0].assets[2].mobile_fallback,bad);
  assert.throws(()=>assertTileManifest(m));}
 const m=manifest();m.tiles[0].assets[2].role='landmark';
 assert.throws(()=>assertTileManifest(m));
});
test('extreme texture budget and costly mandatory mosaic fail closed, not overcommit',()=>{
 const m=manifest();m.tiles[0].assets[2].mobile_fallback.triangle_estimate=290001;
 assertTileManifest(m);
 const sel=plannedLayers(m.tiles[0],'mobile');assert.equal(sel.some(a=>a.role==='mosaic'),false);
 assert.ok(sel.reduce((s,a)=>s+(a.triangle_estimate||0),0)<=290000);
});
