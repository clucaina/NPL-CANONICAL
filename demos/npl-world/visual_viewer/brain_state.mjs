// Independent public educational state machine for the procedural 3D brain.
// These values reflect GAME ACTIONS only and are not neurophysiological measures.
const clamp=n=>Math.max(0,Math.min(1,Number.isFinite(n)?n:0));
export function brainActivity({moving=false,stage=0,dataReady=false,completed=false,interaction=false}={}){
 return {
  sensory:clamp(0.24+(moving?0.62:0.06)),
  attention:clamp(0.25+(dataReady?0.36:0.08)+(interaction?0.19:0)),
  temporal:clamp(0.2+Math.min(4,Math.max(0,stage))*0.16),
  inference:clamp(0.12+(stage>=2?0.55:0.07)),
  choice:clamp(0.17+(stage>=3?0.53:0.07)+(completed?0.1:0)),
  social:0.18
 };
}
export function historySample(history,secondsBack,now){
 if(!Array.isArray(history)||history.length===0)return null;
 const n=Math.max(0,Number.isFinite(secondsBack)?secondsBack:0);
 const time=now-n*1000;
 return [...history].reverse().find(x=>x.t<=time)||history[0];
}
