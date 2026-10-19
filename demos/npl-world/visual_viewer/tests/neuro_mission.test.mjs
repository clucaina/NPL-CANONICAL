import test from 'node:test';
import assert from 'node:assert/strict';
import {inspectDataset,compareObservation,missionStart,missionStep,cognitivePulse,STAGES} from '../neuro_mission.mjs';

const rows=[
  {indicator_id:'SALARIOS',geo_code:'ES',period:'2024',value:29000,unit:'EUR/año',denominator:'personas asalariadas',source_id:'INE',source_url:'https://www.ine.es/'},
  {indicator_id:'SALARIOS',geo_code:'ES30',period:'2024',value:32000,unit:'EUR/año',denominator:'personas asalariadas',source_id:'INE',source_url:'https://www.ine.es/'}
];
const dataset={license_verified:true,provenance_reviewed:true,observations:rows};
test('refuses public social claims from missing or unreviewed data',()=>{
 assert.equal(inspectDataset(null).usable,false);
 assert.equal(inspectDataset({...dataset,provenance_reviewed:false}).usable,false);
 assert.equal(inspectDataset({...dataset,license_verified:false}).usable,false);
 assert.equal(inspectDataset({...dataset,observations:[...rows,rows[1]]}).usable,false);
 assert.equal(inspectDataset({...dataset,observations:[{...rows[0],value:NaN},rows[1]]}).usable,false);
});
test('compares only same indicator, denominator, unit and period',()=>{
 const d=inspectDataset(dataset);
 assert.equal(d.usable,true);
 const r=compareObservation(d,'SALARIOS','ES30');
 assert.equal(r.comparable,true);
 assert.equal(r.difference,3000);
 assert.ok(Math.abs(r.relative_percent-10.3448276)<1e-5);
 assert.equal(r.interpretation,'descriptive_not_causal');
 const nonComparable=inspectDataset({...dataset,observations:[rows[0],{...rows[1],denominator:'hogares'}]});
 assert.equal(compareObservation(nonComparable,'SALARIOS','ES30').comparable,false);
});
test('mission teaches validation without claiming scientific or clinical validation',()=>{
 const absent=inspectDataset(null);
 let m=missionStart(absent);
 assert.equal(m.mode,'training_without_data');
 assert.equal(m.stage,0);
 const wrong=missionStep(m,'suponer_sin_fuente',absent);
 assert.equal(wrong.stage,0);
 assert.equal(wrong.attempts,1);
 for(const correct of ['verificar_fuente','comparar_misma_poblacion','separar_correlacion_causalidad','proponer_intervencion_evaluable']){
  m=missionStep(m,correct,absent);
 }
 assert.equal(m.stage,STAGES.length);
 assert.equal(m.completed,true);
 assert.match(m.insight,/NO una misión basada en datos sociales reales/);
 assert.equal(missionStep(m,'verificar_fuente',absent).stage,STAGES.length);
});
test('brain pulse is expressly a teaching metaphor, responsive to movement and stage',()=>{
 const stationary=cognitivePulse();
 const walking=cognitivePulse({moving:true,sourceReady:false,mission:missionStart(null)});
 assert.notEqual(stationary.senses,walking.senses);
 assert.match(walking.disclaimer,/no mide el cerebro real/);
});
