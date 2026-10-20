import {parsePublicAggregate,summarizeLayers} from './public_layers.mjs';
const $=id=>document.getElementById(id),datasets=new Map();
let active=null;
function el(tag,text){const x=document.createElement(tag);x.textContent=text;return x;}
function show(origin){
 active=origin;
 const data=datasets.get(origin),view=$('dataView');view.replaceChildren();
 if(!data)return;
 view.append(el('h2',origin+' · '+data.records.length+' registros'));
 const years=[...new Set(data.records.map(r=>r.year))].sort((a,b)=>b-a);
 const filter=el('select','');filter.setAttribute('aria-label','Año');
 const all=el('option','Todos los años');all.value='all';filter.append(all);
 for(const y of years){const option=el('option',String(y));option.value=y;filter.append(option);}
 view.append(filter);
 const list=el('div','');view.append(list);
 function render(){
  list.replaceChildren();
  const records=data.records.filter(r=>filter.value==='all'||String(r.year)===filter.value);
  list.append(el('p',records.length+' valores públicos agregados; ninguna localización de sucesos.'));
  for(const r of records.slice(0,40)){
   const article=el('article','');
   article.append(el('strong',r.label),el('span',String(r.value)+' '+r.unit),el('small',r.year+' · '+r.geography_label+' · '+r.resolution));
   const a=el('a','Fuente');a.href=r.source_url;a.target='_blank';a.rel='noopener noreferrer';article.append(a);
   list.append(article);
  }
 }
 filter.addEventListener('change',render);render();
 $('tabNpl').setAttribute('aria-pressed',String(origin==='NPL'));
 $('tabConflict').setAttribute('aria-pressed',String(origin==='CONFLICTOMETRO'));
 window.NEUROCITY_DATA_STATUS={active,summary:summarizeLayers(datasets)};
}
$('aggregateFile').addEventListener('change',async e=>{
 const file=e.target.files?.[0];if(!file)return;
 try{
  if(file.size>1_000_000)throw Error('Archivo mayor de 1 MB');
  const data=parsePublicAggregate(await file.text());
  datasets.set(data.origin,data);
  $('tabNpl').disabled=!datasets.has('NPL');$('tabConflict').disabled=!datasets.has('CONFLICTOMETRO');
  $('status').textContent=data.origin+': '+data.records.length+' registros validados localmente. Sin sincronización.';
  show(data.origin);
 }catch(error){$('status').textContent='Rechazado: '+String(error.message||error);}
 e.target.value='';
});
$('tabNpl').onclick=()=>show('NPL');
$('tabConflict').onclick=()=>show('CONFLICTOMETRO');
window.NEUROCITY_DATA_STATUS={active:null,summary:summarizeLayers(datasets)};
