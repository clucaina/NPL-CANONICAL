export const PUBLIC_SCHEMA = 'neurocity.public-aggregates.v1';
const origins=new Set(['NPL','CONFLICTOMETRO']);
const resolutions=new Set(['municipality','province','autonomous_community','country']);
const units=new Set(['count','percent','rate_per_100k','index','euros','years']);
const top=new Set(['schema','origin','dataset_id','published_at','license','source_url','records']);
const recordFields=new Set(['id','indicator','label','value','unit','year','geography_code','geography_label','resolution','source_url','scope']);
const ident=s=>typeof s==='string' && /^[a-z0-9][a-z0-9._-]{1,79}$/i.test(s);
const label=(s,n=140)=>typeof s==='string'&&s.trim().length>0&&s.length<=n&&!/[\u0000-\u001f\u007f]/.test(s);
const source=s=>{try{if(typeof s!=='string'||s.length>2048||/[\u0000-\u0020\u007f]/.test(s))return false;const u=new URL(s);return u.protocol==='https:'&&!!u.hostname&&!u.username&&!u.password;}catch{return false;}};
function only(o,allowed,where){
 if(!o||typeof o!=='object'||Array.isArray(o))throw Error(where+': objeto inválido');
 for(const k of Object.keys(o))if(!allowed.has(k))throw Error(where+': campo no permitido '+k);
}
function date(s){if(typeof s!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(s))return false;const d=new Date(s+'T00:00:00Z');return !Number.isNaN(d.getTime())&&d.toISOString().slice(0,10)===s;}
export function parsePublicAggregate(raw){
 if(typeof raw!=='string'||raw.length>1_000_000)throw Error('JSON ausente o superior a 1 MB');
 let data;try{data=JSON.parse(raw);}catch{throw Error('JSON inválido');}
 only(data,top,'Conjunto');
 if(data.schema!==PUBLIC_SCHEMA||!origins.has(data.origin)||!ident(data.dataset_id))throw Error('Contrato, origen o identificador inválido');
 if(!date(data.published_at)||!label(data.license,90)||!source(data.source_url))throw Error('Fecha, licencia o fuente inválida');
 if(!Array.isArray(data.records)||data.records.length<1||data.records.length>500)throw Error('Se requieren entre 1 y 500 registros');
 const seen=new Set();
 data.records.forEach((r,i)=>{
  only(r,recordFields,'Registro '+i);
  if(!ident(r.id)||seen.has(r.id))throw Error('Identificador de registro inválido o duplicado');
  seen.add(r.id);
  if(!ident(r.indicator)||!label(r.label)||typeof r.value!=='number'||!Number.isFinite(r.value))throw Error('Indicador o valor inválido');
  if(!units.has(r.unit)||!Number.isInteger(r.year)||r.year<1900||r.year>2100)throw Error('Unidad o año inválido');
  if((r.unit==='percent'&&(r.value<0||r.value>100))||(r.unit==='count'&&(!Number.isSafeInteger(r.value)||r.value<0)))throw Error('Valor fuera de rango');
  if(!label(r.geography_code,24)||!label(r.geography_label,90)||!resolutions.has(r.resolution))throw Error('Ámbito inválido');
  if(r.scope!=='public_aggregate'||!source(r.source_url))throw Error('Fuente pública obligatoria');
 });
 return data;
}
export function isAlicanteMunicipalAggregate(r){return r?.geography_code==='03014'&&r?.resolution==='municipality';}
export function summarizeLayers(layers){return ['NPL','CONFLICTOMETRO'].map(origin=>{const data=layers.get(origin);return {origin,loaded:!!data,count:data?.records.length||0,local:data?.records.filter(isAlicanteMunicipalAggregate).length||0};});}
