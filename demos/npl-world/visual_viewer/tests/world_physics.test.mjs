import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {masterTileToViewer} from '../geo_alignment.mjs';
import {
  decodePhysicalGrid,sourceTileId,RecoveredPhysicalAtlas,
  PHYSICAL_SOURCE,PHYSICAL_TILES
} from '../world_physics.mjs';

const SID='r02_c00',START={x:240,z:1400};
function grid(id=SID,code=2){
 const m=/^r(\d\d)_(?:c(\d\d)|cm(\d\d))$/.exec(id);
 const c=m[2]!==undefined?Number(m[2]):-Number(m[3]);
 const row=Number(m[1]);
 return {tile:id,originLocal:[c*500,row*500],step:2,count:251,
  surface:Array.from({length:251},()=>Array(251).fill(code)),
  height:Array.from({length:251},()=>Array(251).fill(2.47)),
  waterDepthSource:'SIMULATED',verticalAccuracy:'UNVERIFIED_G05'};
}
function setCode(d,x,z,code){
 const ix=Math.round((x-d.originLocal[0])/2),iz=Math.round((z-d.originLocal[1])/2);
 d.surface[iz][ix]=code;
}
function toViewer(x,z=START.z){return masterTileToViewer(SID,x,z);}
function mockLocalAtlas(data,{badHash=false}={}){
 const text=new TextEncoder().encode(JSON.stringify(data));
 const h=createHash('sha256').update(text).digest('hex');
 const index={
   private_real_workers_or_patients:false,
   signed_source_files_recovered_in_sidecars:PHYSICAL_TILES.map(id=>({
    path:'geo/data/physical_'+id+'.json',
    bytes:text.byteLength,
    sha256:(badHash?'0'.repeat(64):h)
   }))
 };
 const restore=[globalThis.document,globalThis.location,globalThis.fetch];
 globalThis.document={baseURI:'http://127.0.0.1:8766/'};
 globalThis.location={origin:'http://127.0.0.1:8766'};
 let readCount=0;
 globalThis.fetch=async(url)=>{
   if(String(url).endsWith('SOURCE_SIDECARS_INDEX.json'))return {ok:true,json:async()=>index};
   readCount++;
   return {ok:true,arrayBuffer:async()=>text.buffer.slice(0)};
 };
 return {restore:()=>{[globalThis.document,globalThis.location,globalThis.fetch]=restore;},
    get reads(){return readCount;}};
}
test('recovered 2m physical atlas decodes original EPSG25830 tiles and negative columns',()=>{
 assert.equal(sourceTileId(240,1400),'r02_c00');
 assert.equal(sourceTileId(-250,250),'r00_cm01');
 assert.equal(sourceTileId(3000,3000),null);
 const ordinary=decodePhysicalGrid(grid(),SID);
 assert.equal(ordinary.surface.length,63001);
 assert.equal(ordinary.height.length,63001);
 assert.equal(ordinary.verifiedElevationDatum,false);
 const negative=decodePhysicalGrid(grid('r00_cm01'), 'r00_cm01');
 assert.equal(negative.x0,-500);
 assert.throws(()=>decodePhysicalGrid(grid('r00_cm01'),SID));
});
test('ocean, unknown cell and building cannot be falsely made walkable',()=>{
 for(const code of [0,6,7]){
   const item=grid(SID,2);setCode(item,244,1400,code);
   const atlas=new RecoveredPhysicalAtlas();
   atlas._remember(SID,decodePhysicalGrid(item,SID));
   const p=toViewer(244);
   const verdict=atlas.canOccupy(p.x,p.z);
   assert.equal(verdict.allowed,code===0?false:false,'surface '+code);
   assert.equal(verdict.reason,'WATER_BUILDING_OR_UNMAPPED');
 }
});
test('real signed source SHA256 is verified before any geometry used, no private requests',async()=>{
 const fixture=grid(),env=mockLocalAtlas(fixture);
 try{
   const atlas=new RecoveredPhysicalAtlas({maxTiles:3});
   await atlas.initialize();
   const tile=await atlas.load(SID);
   assert.equal(tile.tile,SID);
   const initial=toViewer(START.x);
   const verdict=atlas.canOccupy(initial.x,initial.z);
   assert.equal(verdict.allowed,true);
   assert.equal(verdict.source,undefined); // only audit-approved 2m model fields exposed
   assert.equal(atlas.status().offlineOnly,true);
   assert.equal(atlas.status().verifiedVerticalDatum,false);
   await atlas.load(SID);
   assert.equal(env.reads,1,'one network source file, cached');
   atlas.dispose();
 }finally{env.restore();}
});
test('a tampered physical grid is not silently loaded or treated as navigable',async()=>{
 const env=mockLocalAtlas(grid(),{badHash:true});
 try{
   const atlas=new RecoveredPhysicalAtlas();
   await atlas.initialize();
   await assert.rejects(()=>atlas.load(SID),/SHA256 mismatch/);
   assert.equal(atlas.status().diagnostics.hashRejected,1);
   assert.equal(atlas.status().loadedTiles.length,0);
   assert.equal(atlas.canOccupy(1,1).allowed,null);
 }finally{env.restore();}
});
test('swept collision prevents entering source building and slides along original boundary',()=>{
 const data=grid();
 for(let z=1390;z<=1410;z+=2)for(let x=246;x<=252;x+=2)setCode(data,x,z,7);
 const atlas=new RecoveredPhysicalAtlas({maxTiles:3});
 atlas._remember(SID,decodePhysicalGrid(data,SID));
 const begin=toViewer(240);
 const finish=toViewer(255);
 const direction={dx:finish.x-begin.x,dz:finish.z-begin.z};
 const output=atlas.move(begin,direction.dx,direction.dz);
 const location=atlas.sampleViewer(output.x,output.z);
 assert.ok(location,'still in known physical grid');
 assert.notEqual(location.code,7);
 assert.ok(output.blockedSubsteps>0);
 assert.equal(output.verifiedVerticalDatum,false);
 assert.equal(output.swept,true);
});
test('missing physical data falls back transparently, rather than inventing false collisions',()=>{
 const atlas=new RecoveredPhysicalAtlas();
 const original={x:10,z:20};
 const moved=atlas.move(original,1,0.5);
 assert.ok(Math.abs(moved.x-11)<1e-6);
 assert.ok(Math.abs(moved.z-20.5)<1e-6);
 assert.ok(moved.fallbackSubsteps>0);
 assert.equal(atlas.status().physicalCoverageCertified,false);
});
