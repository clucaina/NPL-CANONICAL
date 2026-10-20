/**
 * NeuroCity -> NPL action-observation model.
 * Five FUNCTIONAL metaphors (not neuroanatomical localisation, clinical
 * interpretation, physiological activity, stress or emotion detection).
 * INPUTS are actions the player actually performs in the local game.
 * No storage, names, location uploads, network requests or diagnoses.
 */
export const NPL_PROCESS_IDS=Object.freeze(['perception','attention','memory','reasoning','decision']);
export const NPL_PROCESS_INFO=Object.freeze({
 perception:Object.freeze({
  title:'Percepción espacial',basis:'Orientación y movimiento registrados durante la partida',
  truth:'No mide la corteza visual ni la percepción humana.',
  prompt:'Explora un camino real de Alicante y compara el espacio visible con el mapa.'}),
 attention:Object.freeze({
  title:'Exploración atencional',basis:'Cambios voluntarios de dirección de la cámara',
  truth:'Girar la cámara no mide atención clínica.',
  prompt:'Observa una fachada desde dos ángulos. ¿Qué detalles son verificables?'}),
 memory:Object.freeze({
  title:'Memoria de la actividad',basis:'Etapas de la misión metodológica completadas',
  truth:'El historial de decisiones no es una prueba de memoria.',
  prompt:'Recuerda qué dato comprobaste antes y por qué.'}),
 reasoning:Object.freeze({
  title:'Contraste de hipótesis',basis:'Decisiones metodológicas de comparación y causalidad',
  truth:'Una elección no mide inteligencia ni función ejecutiva.',
  prompt:'Contrasta dos explicaciones antes de atribuir una causa.'}),
 decision:Object.freeze({
  title:'Decisión y acción',basis:'Desplazamientos y respuestas voluntarias observados',
  truth:'La frecuencia de acciones no determina impulsividad ni autocontrol.',
  prompt:'Elige una acción verificable que tenga consecuencias reversibles.'})
});
const finite=n=>typeof n==='number'&&Number.isFinite(n);
const clamp=(n,a,b)=>Math.max(a,Math.min(b,n));
const eased=(from,target,dt,tau)=>from+(target-from)*(1-Math.exp(-dt/tau));
export function startBehaviorSession(){
 return {schema:'neurocity.npl-observed-actions.v1',
  elapsed:0,distanceMeters:0,cameraTurnRadians:0,
  obstructionEvents:0,observationEvents:0,choices:0,
  correctMethodSteps:0,stage:0,sourceVerified:false,
  scores:Object.fromEntries(NPL_PROCESS_IDS.map(id=>[id,.12])),
  selected:'perception',sampleCount:0,
  modelIsMetaphor:true,hasBiometricData:false,storesNothing:false};
}
export function selectProcess(session,id){
 if(!session||!NPL_PROCESS_IDS.includes(id))throw new RangeError('Unknown cognitive operation');
 return {...session,selected:id};
}
export function sampleBehavior(session,input){
 if(!session||!input||typeof input!=='object')throw new TypeError('Missing local NPL sample');
 const {dt=0,movementMeters=0,cameraTurnRadians=0,
  obstructed=false,observed=false,missionStage=session.stage,
  choices=session.choices,sourceVerified=false}=input;
 if(![dt,movementMeters,cameraTurnRadians,missionStage,choices].every(finite)||
    dt<0||dt>1||movementMeters<0||movementMeters>8||
    cameraTurnRadians<0||cameraTurnRadians>Math.PI||
    !Number.isInteger(choices)||choices<0||choices>200||
    !Number.isInteger(missionStage)||missionStage<0||missionStage>4 ||
    typeof obstructed!=='boolean'||typeof observed!=='boolean'||
    typeof sourceVerified!=='boolean')throw RangeError('Unverified or impossible local action');
 const activity=movementMeters/(Math.max(.02,dt));
 const turns=cameraTurnRadians/(Math.max(.02,dt));
 const progress=clamp(missionStage/4,0,1);
 const newChoices=Math.max(0,choices-session.choices);
 const stages=Math.max(0,missionStage-session.stage);
 const goal={
  perception:.11+clamp(activity/5,0,.55)+(observed?.15:0),
  attention:.10+clamp(turns/3.5,0,.62)+(observed?.14:0),
  memory:.10+progress*.68,
  reasoning:.10+clamp(progress*1.12-.18,0,.65)+(newChoices>0?.12:0),
  decision:.13+clamp(activity/8,0,.4)+(newChoices>0?.24:0)
 };
 const scores={};
 for(const id of NPL_PROCESS_IDS){
  scores[id]=Math.round(clamp(eased(session.scores[id],goal[id],dt, id==='memory'?3.5:.8),0,1)*1000)/1000;
 }
 return {...session,elapsed:session.elapsed+dt,distanceMeters:session.distanceMeters+movementMeters,
  cameraTurnRadians:session.cameraTurnRadians+cameraTurnRadians,
  obstructionEvents:session.obstructionEvents+(obstructed?1:0),
  observationEvents:session.observationEvents+(observed?1:0),
  choices:Math.max(session.choices,choices),
  correctMethodSteps:session.correctMethodSteps+stages,
  stage:missionStage,sourceVerified,
  scores,sampleCount:session.sampleCount+1};
}
export function publicBehaviorSnapshot(session){
 if(!session?.modelIsMetaphor)throw TypeError('No valid action model');
 const info=NPL_PROCESS_INFO[session.selected];
 const n=x=>Math.round(x*10)/10;
 return Object.freeze({
  schema:session.schema,selected:session.selected,
  selectedTitle:info.title,selectedBasis:info.basis,
  disclaimer:info.truth,
  nextAction:info.prompt,
  elapsedSeconds:n(session.elapsed),distanceMeters:n(session.distanceMeters),
  steeringRadians:n(session.cameraTurnRadians),obstaclesObserved:session.obstructionEvents,
  choices:session.choices,steps:session.correctMethodSteps,
  sourceVerified:session.sourceVerified,
  scores:Object.freeze({...session.scores}),
  interpretation:'LOCAL_GAME_ACTIONS_ONLY_NOT_NEURAL_MEASUREMENT',
  patientData:false,diagnosticClaims:false,personalDataPersisted:false
 });
}
