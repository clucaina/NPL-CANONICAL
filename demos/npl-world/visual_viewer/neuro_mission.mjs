// NPL WORLD public teaching loop: descriptive data -> cognitive metaphor -> game mission.
// IMPORTANT: not a clinical brain model, not a causal prediction, not a population diagnosis.
// No networking, no accounts, no tracking and no client data.
export const STAGES=Object.freeze(["observar","comparar","interpretar","decidir"]);
const SAFE_GEO=/^ES(?:[0-9A-Z]{2,6})?$/;
export function inspectDataset(payload){
  if(!payload||typeof payload!=="object"||!Array.isArray(payload.observations))
    return {usable:false,reason:"no_public_dataset",entries:[]};
  if(payload.license_verified!==true||payload.provenance_reviewed!==true)
    return {usable:false,reason:"provenance_not_verified",entries:[]};
  const seen=new Set(), entries=[];
  for(const item of payload.observations){
    if(!item||typeof item!=="object")return {usable:false,reason:"invalid_row",entries:[]};
    const {indicator_id,geo_code,period,value,unit,source_url,denominator,source_id}=item;
    if(!indicator_id||!SAFE_GEO.test(geo_code||"")||!/^20\d\d(?:-\d\d)?$/.test(period||"")
      ||typeof value!=="number"||!Number.isFinite(value)||typeof unit!=="string"
      ||!unit||typeof denominator!=="string"||!denominator
      ||typeof source_url!=="string"||!source_url.startsWith("https://")
      ||typeof source_id!=="string"||!source_id){
        return {usable:false,reason:"missing_comparable_evidence",entries:[]};
    }
    const key=[indicator_id,geo_code,period,denominator].join("|");
    if(seen.has(key))return {usable:false,reason:"duplicate_row",entries:[]};
    seen.add(key);
    entries.push({indicator_id,geo_code,period,value,unit,denominator,source_url,source_id});
  }
  if(entries.length<2)return {usable:false,reason:"insufficient_rows",entries:[]};
  return {usable:true,reason:"public_verified_data",entries,
          updated_at:typeof payload.updated_at==="string"?payload.updated_at:null};
}
export function compareObservation(validated,indicator,regionalCode){
  if(!validated?.usable)return {comparable:false,reason:validated?.reason||"no_public_dataset"};
  const region=validated.entries.find(x=>x.indicator_id===indicator&&x.geo_code===regionalCode);
  if(!region)return {comparable:false,reason:"region_missing"};
  const base=validated.entries.find(x=>x.indicator_id===indicator&&x.geo_code==="ES"&&x.period===region.period
        &&x.unit===region.unit&&x.denominator===region.denominator&&x.source_id===region.source_id);
  if(!base||base.value===0)return {comparable:false,reason:"baseline_missing_or_zero"};
  return {comparable:true,region:region.value,national:base.value,
      difference:region.value-base.value,relative_percent:(region.value/base.value-1)*100,
      unit:region.unit,period:region.period,denominator:region.denominator,
      source_url:region.source_url,interpretation:"descriptive_not_causal"};
}
export function missionStart(validated){
  return {stage:0,completed:false,attempts:0,mode:validated?.usable?"source_based":"training_without_data",
          insight:null,choices:[]};
}
export function missionStep(mission,option,validated){
  const state={...mission,choices:[...(mission?.choices||[])],attempts:(mission?.attempts||0)+1};
  if(state.completed)return state;
  const criteria=[
    option==="verificar_fuente",
    option==="comparar_misma_poblacion",
    option==="separar_correlacion_causalidad",
    option==="proponer_intervencion_evaluable"
  ];
  if(!criteria[state.stage]){
    state.insight="Esta decisión necesita una comprobación adicional. Puedes intentarlo de nuevo.";
    return state;
  }
  state.choices.push(option);
  state.stage++;
  state.completed=state.stage===STAGES.length;
  state.insight=[
    "Primero comprobamos la procedencia, la fecha y los límites de una observación.",
    "Nunca comparamos poblaciones, periodos ni unidades incompatibles.",
    "Una diferencia territorial no demuestra por sí sola su causa.",
    "La propuesta se puede ensayar y evaluar antes de atribuirle eficacia."
  ][state.stage-1];
  if(state.completed&&state.mode!=="source_based")
    state.insight+=" Has completado el entrenamiento metodológico, NO una misión basada en datos sociales reales.";
  return state;
}
export function cognitivePulse({moving=false,sourceReady=false,mission=missionStart(null)}={}){
  return {
    senses:moving?"Movimiento y orientación espacial":"Entorno visual disponible",
    attention:sourceReady?"Seleccionar un dato con procedencia":"Identificar qué datos aún faltan",
    memory:mission.choices.length+" pasos metodológicos practicados",
    inference:mission.stage>=2?"Contrastar explicaciones alternativas":"Evitar inferencias sin contraste",
    decision:mission.completed?"Diseñar una evaluación":"Elegir siguiente comprobación",
    disclaimer:"Simulación pedagógica de operaciones cognitivas; no mide el cerebro real del jugador."
  };
}
