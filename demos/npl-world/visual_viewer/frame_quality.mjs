/**
 * NeuroCity frame-budget governor. Session-only measurements from THIS browser;
 * no remote tracking, artificial FPS claims, GLB changes or baked asset edits.
 * The governor only changes renderer pixel ratio and the shadow-map budget.
 */
export const QUALITY_LEVELS=Object.freeze(['economy','balanced','detail']);
const KNOWN_MODES=new Set(['auto','economy','detail']);
const FRAME_WINDOW=90;
const MIN_WARMUP_SECONDS=7;
const COOLDOWN_SECONDS=12;
const cut=(n,low,high)=>Math.max(low,Math.min(high,n));

export function qualityPlan(tier,{mobile=false,devicePixelRatio=1}={}){
 if(!QUALITY_LEVELS.includes(tier))throw new RangeError('Unknown quality tier');
 if(!Number.isFinite(devicePixelRatio)||devicePixelRatio<=0)
   throw new RangeError('Device pixel ratio must be positive');
 const cap=cut(devicePixelRatio,0.5,3);
 const configs={
   economy:{pixelRatio:0.75,shadowSize:512},
   balanced:{pixelRatio:mobile?1:1.25,shadowSize:mobile?768:1024},
   detail:{pixelRatio:mobile?1.35:1.75,shadowSize:mobile?1024:1536}
 };
 const config=configs[tier];
 return Object.freeze({...config,pixelRatio:Math.min(cap,config.pixelRatio),
   tier,geometryUnchanged:true,privateAssetsTouched:false});
}
function percentile75(samples){
 const a=[...samples].sort((x,y)=>x-y);
 return a[Math.floor((a.length-1)*0.75)];
}
export function createFrameGovernor({mobile=false,devicePixelRatio=1}={}){
 const plan=tier=>qualityPlan(tier,{mobile,devicePixelRatio});
 let tier='balanced',mode='auto';
 let frames=[],started=null,lastChange=-Infinity,highWindows=0,lowWindows=0;
 let p75=null,windows=0,stalls=0,paused=false,rendered=0;
 const limits=mobile?{slow:35,fast:20}:{slow:28,fast:16.5};
 function resetCounter(){frames=[];highWindows=0;lowWindows=0;}
 function setMode(next){
   if(!KNOWN_MODES.has(next))throw new RangeError('Invalid quality mode');
   mode=next;
   if(next!=='auto')tier=next;
   resetCounter();
   return snapshot();
 }
 function sample(frameMs,nowSeconds,{visible=true}={}){
   if(!Number.isFinite(frameMs)||frameMs<0||
      !Number.isFinite(nowSeconds)||nowSeconds<0)
     throw new RangeError('Expected nonnegative real frame timing');
   if(!visible){paused=true;resetCounter();return false;}
   if(paused){paused=false;resetCounter();started=nowSeconds;return false;}
   if(started===null)started=nowSeconds;
   if(frameMs>=250){stalls++;resetCounter();started=nowSeconds;return false;}
   if(frameMs===0)return false;
   rendered++;
   frames.push(frameMs);
   if(frames.length<FRAME_WINDOW)return false;
   p75=percentile75(frames);windows++;
   frames=[];
   if(mode!=='auto')return false;
   if(nowSeconds-started<MIN_WARMUP_SECONDS)return false;
   if(p75>limits.slow){highWindows++;lowWindows=0;}
   else if(p75<limits.fast){lowWindows++;highWindows=0;}
   else {lowWindows=0;highWindows=0;}
   if(nowSeconds-lastChange<COOLDOWN_SECONDS)return false;
   const index=QUALITY_LEVELS.indexOf(tier);
   let next=tier;
   if(highWindows>=2&&index>0)next=QUALITY_LEVELS[index-1];
   else if(lowWindows>=4&&index<2)next=QUALITY_LEVELS[index+1];
   if(next===tier)return false;
   tier=next;lastChange=nowSeconds;resetCounter();
   return true;
 }
 function snapshot(){
   return Object.freeze({
     mode,tier,plan:plan(tier),frameSamples:rendered,completedWindows:windows,
     observedP75FrameMs:p75===null?null:Math.round(p75*10)/10,
     observedFrameRateApprox:p75===null?null:Math.round(1000/p75),
     unclassifiedStalls:stalls,paused,
     source:'browser_requestAnimationFrame_intervals_not_GPU_profiling',
     measuredInCurrentSession:windows>0,
     noGLBMutation:true,telemetryNetwork:false
   });
 }
 return Object.freeze({sample,setMode,snapshot});
}
