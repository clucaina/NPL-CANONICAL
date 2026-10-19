/**
 * NeuroCity / Mediterranean promenade design kit
 * All placements are ARTISTIC, not surveyed features or points of interest.
 * Local axes: x across the illustrated corridor, z along it.
 * No network, location/person data or random nondeterministic behaviour.
 */
export const KIT_LICENSE='CC0-1.0';
export const ARTISTIC_SCOPE='illustrative_placement_not_surveyed';
export const KIT_TIERS=Object.freeze({
  mobile:Object.freeze({palmStep:44,benchStep:74,planterStep:58,cycleStep:122,fronds:8,segments:5}),
  desktop:Object.freeze({palmStep:22,benchStep:37,planterStep:29,cycleStep:61,fronds:12,segments:7})
});
const valid=(x)=>Number.isFinite(x);
const round=(n)=>Math.round(n*1000)/1000;
const variation=(n)=>{const t=Math.sin(n*12.9898+78.233)*43758.5453;return t-Math.floor(t);};
export function planUrbanKit(tier='desktop'){
 if(!Object.hasOwn(KIT_TIERS,tier))throw new RangeError('Unknown 3D quality tier');
 const config=KIT_TIERS[tier],palms=[],benches=[],planters=[],cycles=[];
 for(let z=-136;z<=106;z+=config.palmStep){
   for(const [i,x,offset] of [[0,-18.4,0],[1,5.8,5.2]]){
     const zz=z+offset,seed=variation(zz+i*11.31);
     palms.push({x, z:round(zz), scale:round(0.91+seed*0.15), heading:round(seed*6.283)});
   }
 }
 for(let z=-118,i=0;z<=105;z+=config.benchStep,i++){
    benches.push({x:i%2===0?8.7:-13.6,z,heading:i%2===0?0:Math.PI});
 }
 for(let z=-128,i=0;z<=110;z+=config.planterStep,i++){
    planters.push({x:i%2===0?7.5:-16.0,z,heading:0});
 }
 for(let z=-104;z<=95;z+=config.cycleStep){
    cycles.push({x:9.3,z,heading:0});
 }
 for(const item of [...palms,...benches,...planters,...cycles]){
   if(!valid(item.x)||!valid(item.z)||!valid(item.heading??0))throw Error('Invalid urban kit placement');
   if(item.z < -142||item.z>114)throw Error('Urban kit outside documented corridor');
 }
 const instances=palms.length+benches.length+planters.length+cycles.length;
 return Object.freeze({tier,scope:ARTISTIC_SCOPE,license:KIT_LICENSE,config,
   palms,benches,planters,cycles,instances});
}
export function makeKitReport(plan){
 return {tier:plan.tier,scope:plan.scope,license:plan.license,
  palmCount:plan.palms.length,benchCount:plan.benches.length,
  planterCount:plan.planters.length,cycleCount:plan.cycles.length,
  instances:plan.instances,drawCallGroupsBudget:12,geodataSourceModified:false};
}
