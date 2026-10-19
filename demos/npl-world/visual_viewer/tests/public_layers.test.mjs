import test from 'node:test';
import assert from 'node:assert/strict';
import {PUBLIC_SCHEMA,parsePublicAggregate,isAlicanteMunicipalAggregate,summarizeLayers} from '../public_layers.mjs';
const record=()=>({id:'aggregate_2025',indicator:'test_index',label:'Índice de prueba ficticio',value:42,unit:'index',year:2025,geography_code:'03014',geography_label:'Alicante municipio',resolution:'municipality',source_url:'https://example.org/public',scope:'public_aggregate'});
const fixture=()=>({schema:PUBLIC_SCHEMA,origin:'NPL',dataset_id:'qa_fixture',published_at:'2026-10-19',license:'TEST ONLY',source_url:'https://example.org/public',records:[record()]});
const parse=x=>parsePublicAggregate(JSON.stringify(x));
test('valid NPL and Conflictometro contracts',()=>{
 const npl=parse(fixture());assert.equal(npl.records.length,1);assert.equal(isAlicanteMunicipalAggregate(npl.records[0]),true);
 const cm=fixture();cm.origin='CONFLICTOMETRO';assert.equal(parse(cm).origin,'CONFLICTOMETRO');
 assert.deepEqual(summarizeLayers(new Map([['NPL',npl],['CONFLICTOMETRO',parse(cm)]])).map(x=>x.local),[1,1]);
});
test('reject extra fields including personal and precise location fields',()=>{
 for(const key of ['name','email','lat','lon','address','notes']){
  const d=fixture();d.records[0][key]='NOT_ALLOWED';assert.throws(()=>parse(d),/campo no permitido/);
 }
 const d=fixture();d.unexpected=[];assert.throws(()=>parse(d),/campo no permitido/);
});
test('reject invalid provenance, origin, dates and values',()=>{
 for(const change of [
  d=>{d.origin='OTHER';},d=>{d.source_url='javascript:alert(1)';},
  d=>{d.records[0].source_url='http://example.org';},d=>{d.published_at='2026-02-31';},
  d=>{d.records[0].scope='individual';},d=>{d.records[0].value='unknown';}
 ]){const d=fixture();change(d);assert.throws(()=>parse(d));}
});
test('reject duplicates, bad percentage and oversized files',()=>{
 const d=fixture();d.records.push({...record()});assert.throws(()=>parse(d),/duplicado/);
 const e=fixture();e.records[0].unit='percent';e.records[0].value=105;assert.throws(()=>parse(e),/rango/);
 assert.throws(()=>parsePublicAggregate('x'.repeat(1_000_001)),/1 MB/);
});
test('province values do not imply street precision',()=>{
 const d=fixture();d.records[0].resolution='province';assert.equal(isAlicanteMunicipalAggregate(parse(d).records[0]),false);
});

test('reject unsafe numeric counts and malformed provenance URLs',()=>{
 for(const value of [-1,1.5,Number.MAX_SAFE_INTEGER+1]){
  const d=fixture();d.records[0].unit='count';d.records[0].value=value;
  assert.throws(()=>parse(d),/rango/);
 }
 for(const url of ['https://example.org/a b','https://example.org/\\n','https://example.org/'+ 'a'.repeat(2050)]){
  const d=fixture();d.records[0].source_url=url;
  assert.throws(()=>parse(d),/Fuente pública/);
 }
});
