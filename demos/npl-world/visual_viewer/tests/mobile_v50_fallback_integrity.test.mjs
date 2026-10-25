import test from "node:test";
import assert from "node:assert/strict";
import {assertTileManifest,plannedLayers,verifiedMosaicFallback} from "../city_tiles.mjs";

const M='a'.repeat(64),F='b'.repeat(64);
const master=()=>({
 role:"mosaic",path:"assets/selected/Explanada_V50_Surgical_4cm_STONES_PRIVATE.glb",
 sha256:M,bytes:11_176_704,triangle_estimate:105_345,embedded_images:2,
 mobile_fallback:{
  path:"assets/selected/Explanada_v50_PBR_1024.glb",sha256:F,
  bytes:3_568_880,triangle_estimate:5_225,embedded_images:2
 }
});
const manifest=asset=>({
 schema:"neurocity.local-worldmaster-tiles.v1",crs:"EPSG:25830",
 vertical_datum_verified:false,public_redistribution_allowed:false,
 tiles:[{id:"r02_c00",assets:[asset]}]
});
test("signed original v50 fallback has a distinct safe asset, finite image count and bounded triangles",()=>{
 const a=master(),f=verifiedMosaicFallback(a);
 assert.equal(f.path,a.mobile_fallback.path);
 assertTileManifest(manifest(a));
 const out=plannedLayers({assets:[a]},"mobile");
 assert.equal(out.length,1);
 assert.equal(out[0].path,f.path);
 assert.equal(out[0].sha256,F);
 assert.equal(out[0].embedded_images,2);
 assert.equal(out[0].mobileV50Fallback,true);
 assert.equal(out[0].archaeologicalModelSource,"original_V50_PBR_not_procedural");
 const desktop=plannedLayers({assets:[a]},"desktop");
 assert.equal(desktop[0].path,a.path);
});
test("invalid fallback cannot pass manifest or direct LOD selection",()=>{
 const unsafe=[
  {path:"../private.glb"},
  {path:"https://another-server.invalid/avatar.glb"},
  {path:master().path},
  {sha256:"x".repeat(64)},
  {sha256:F.toUpperCase()},
  {sha256:null},
  {bytes:-1},
  {bytes:0},
  {bytes:90_000_001},
  {bytes:Infinity},
  {triangle_estimate:0},
  {triangle_estimate:4_000_001},
  {triangle_estimate:NaN},
  {embedded_images:-1},
  {embedded_images:1025},
  {embedded_images:1.5},
  {embedded_images:NaN},
  {embedded_images:Infinity},
  {embedded_images:undefined}
 ];
 for(const patch of unsafe){
  const a=master();Object.assign(a.mobile_fallback,patch);
  assert.throws(()=>assertTileManifest(manifest(a)),{message:/Unsafe|Unsupported/},JSON.stringify(patch));
  assert.throws(()=>plannedLayers({assets:[a]},"mobile"),{message:/Unsafe/},JSON.stringify(patch));
 }
});
test("fallback only for mosaic, budget never bypassed by its apparently mandatory role",()=>{
 const a=master();a.role="architecture";
 assert.throws(()=>assertTileManifest(manifest(a)));
 assert.throws(()=>plannedLayers({assets:[a]},"mobile"));
 const huge=master();huge.mobile_fallback.triangle_estimate=290_001;
 assert.equal(plannedLayers({assets:[huge]},"mobile").length,0);
 const imageHeavy=master();imageHeavy.mobile_fallback.embedded_images=31;
 assert.equal(plannedLayers({assets:[imageHeavy]},"mobile").length,0);
 const valid=master();valid.mobile_fallback.embedded_images=0;
 assert.equal(plannedLayers({assets:[valid]},"mobile").length,1);
});
test("manifest ignores unauthorized fallback copies only when property genuinely absent",()=>{
 const a=master();delete a.mobile_fallback;
 assertTileManifest(manifest(a));
 assert.equal(plannedLayers({assets:[a]},"desktop")[0].path,a.path);
 const invalid=master();invalid.mobile_fallback=null;
 assert.throws(()=>assertTileManifest(manifest(invalid)));
});
