import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {
 CANONICAL_NPL,sha256Hex,validateCanonicalManifest,
 validateCanonicalFrameMessage,verifyCanonicalNPLSource
} from '../canonical_npl_contract.mjs';

const fixture=()=>({nodes:Array.from({length:437},(_,id)=>({
 id,gltfNodeIndex:id+30,label:'Original NPL test anatomical structure '+id,
 name:'fixture structure',region:'cortex'}))});
test('restored ORIGINAL atlas contract explicitly rejects procedural 2-egg brain',()=>{
 assert.equal(CANONICAL_NPL.expectedStructures,437);
 assert.equal(CANONICAL_NPL.expectedPrimitives,563);
 assert.equal(CANONICAL_NPL.glbBytes,4650816);
 assert.equal(CANONICAL_NPL.runtimeVersions.three,'0.167.1');
 assert.equal(CANONICAL_NPL.runtimeVersions.draco,'r167');
 assert.equal(CANONICAL_NPL.originalModelNeverModified,true);
 const ok=validateCanonicalManifest(fixture());
 assert.equal(ok.structures,437);
 assert.equal(ok.mappedModelNodes,437);
 assert.equal(ok.fromOriginalAtlas,true);
 assert.throws(()=>validateCanonicalManifest({nodes:fixture().nodes.slice(0,2)}),/437/);
 const duplicate=fixture();duplicate.nodes[1].gltfNodeIndex=duplicate.nodes[0].gltfNodeIndex;
 assert.throws(()=>validateCanonicalManifest(duplicate),/correspondence/);
});
test('SHA256 is real cryptographic digest, fail closed on tampered original metadata',async()=>{
 const buffer=new TextEncoder().encode('original NPL protected');
 const result=await sha256Hex(buffer.buffer,globalThis.crypto.subtle);
 assert.equal(result,createHash('sha256').update(buffer).digest('hex'));
 assert.rejects(()=>sha256Hex(new Uint8Array().buffer,globalThis.crypto.subtle),/integrity/);
});
test('private locally installed NPL source must match SHA256 BEFORE frame executes',async()=>{
 const manifest=new TextEncoder().encode(JSON.stringify(fixture()));
 const model=new Uint8Array(CANONICAL_NPL.glbBytes);
 const view=new DataView(model.buffer);view.setUint32(0,0x46546c67,true);
 view.setUint32(4,2,true);view.setUint32(8,model.byteLength,true);
 const pseudoDigest={
  async digest(_algorithm,buf){
   const hash=buf.byteLength===model.byteLength?CANONICAL_NPL.glbSHA256:CANONICAL_NPL.manifestSHA256;
   return Uint8Array.from(hash.match(/../g).map(x=>parseInt(x,16))).buffer;
  }
 };
 let requests=0;
 const fetcher=async path=>{
  requests++;
  if(path===CANONICAL_NPL.manifest)return {ok:true,arrayBuffer:async()=>manifest.buffer};
  if(path===CANONICAL_NPL.glb)return {ok:true,arrayBuffer:async()=>model.buffer};
  return {ok:false};
 };
 // Synthetic binary differs from original: its literal byte-size / SHA checks
 // should reject it; this is NOT a tested canonical model, only a rejection QA.
 await assert.rejects(()=>verifyCanonicalNPLSource({fetcher,cryptoSubtle:pseudoDigest}),
                      /NPL canonical source mismatch/);
 assert.equal(requests,1);
});
test('iframe only trusts its OWN origin, original viewer and plausible 563 primitive count',()=>{
 const frame={};
 const good={origin:'http://127.0.0.1:8766',source:frame,data:{
  type:'NPL_CANONICAL_BRAIN_STATUS_V1',source:'NPL-CANONICAL-C14-R3',
  state:'READY',meshCount:563,modelSource:'ORIGINAL_PROTECTED_GLB'}};
 assert.equal(validateCanonicalFrameMessage(good,good.origin,frame).meshCount,563);
 assert.equal(validateCanonicalFrameMessage({...good,origin:'https://evil.example'},good.origin,frame),null);
 assert.equal(validateCanonicalFrameMessage({...good,source:{}},good.origin,frame),null);
 assert.equal(validateCanonicalFrameMessage({...good,data:{...good.data,meshCount:5}},good.origin,frame),null);
 assert.equal(validateCanonicalFrameMessage({...good,data:{...good.data,source:'procedural_egg'}},good.origin,frame),null);
});
