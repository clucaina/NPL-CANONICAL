import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {wantsRecoveredWorldmaster,shouldLoadOwnerArchive} from '../owner_worldmaster_policy.mjs';

test('V8 local owner can explicitly activate true G19 V50 even without public review mode',()=>{
 assert.equal(shouldLoadOwnerArchive(false,'?worldmaster=1'),true);
 assert.equal(shouldLoadOwnerArchive(false,'?worldmaster=0'),false);
 assert.equal(shouldLoadOwnerArchive(false,''),false);
 assert.equal(shouldLoadOwnerArchive(true,'?worldmaster=1'),false);
 assert.equal(wantsRecoveredWorldmaster('?worldmaster=1&setting=desktop'),true);
});
test('No loose truthiness or malformed local bootstrap',()=>{
 for(const q of ['?worldmaster=true','?worldmaster=2','?worldmaster=yes','?worldmaster=01'])
  assert.equal(wantsRecoveredWorldmaster(q),false);
 assert.throws(()=>shouldLoadOwnerArchive('false','?worldmaster=1'),TypeError);
 assert.throws(()=>wantsRecoveredWorldmaster(7),TypeError);
 assert.throws(()=>wantsRecoveredWorldmaster('x'.repeat(3000)),TypeError);
});
test('Actual runtime calls owner G19 installer after public-only branch returns',async()=>{
 const source=await readFile(new URL('../app.js',import.meta.url),'utf8');
 assert.match(source,/const ownerWorldRequested=shouldLoadOwnerArchive\(publicPreview,location\.search\)/);
 assert.match(source,/if\(publicPreview\)\{enterPublicCity\(\);startRecoveredMasterIfRequested\(\);return;\}\s*\/\/ Previously private avatar mode returned without ever loading the 86 owner GLBs\.\s*if\(ownerWorldRequested\)startRecoveredMasterIfRequested\(\);/);
 assert.match(source,/if\(publicPreview \|\| ownerWorldRequested\)\{\s*try\{\s*cityCollision=buildCityWallCollision\(city\)/);
 assert.match(source,/if\(showingArchivedMaster && physicalAtlas\?\.index\)/,
  'Signed physical G13 atlas must retain priority over OSM fallback');
 assert.doesNotMatch(source,/if\(!publicPreview \|\| new URLSearchParams\(location\.search\)/,
  'Archived G19 loader must not be gated behind publicPreview');
});
test('Never fetch protected models from nonlocal networks or public CDN',async()=>{
 const source=await readFile(new URL('../app.js',import.meta.url),'utf8');
 assert.match(source,/loader:new GLTFLoader\(\),profile:visualTier/);
 assert.match(source,/new RecoveredMasterTiles/);
 assert.match(source,/startRecoveredMasterIfRequested\(\)/);
 assert.doesNotMatch(source,/fetch\(['"]https?:\/\/[^'"]+world-master/);
});
