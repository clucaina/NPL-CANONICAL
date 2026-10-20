// NeuroCity: never render the generic G19 architecture of Casa Carbonell
// over its SIGNED original G14 landmark. This is a rendering LOD deduplication,
// not a destructive change to any source mesh or to G13 collision authority.
const ORIGINAL='assets/source/ASSETS/G14/G14_historic_carbonell_244990.glb';
const PRIVATE_L2='assets/selected/G14_CASA_CARBONELL_SOURCE_PRESERVED_L2_PRIVATE.glb';
const BU_PREFIX='BU_244990_';
export function hideCarbonellG19Duplicate(tileGroup,{landmarkPath,verifiedBytesLoaded=false,tileId}={}){
 if(tileId!=='r02_c00'||!verifiedBytesLoaded||
    ![ORIGINAL,PRIVATE_L2].includes(landmarkPath)||
    typeof tileGroup?.traverse!=='function'){
  return Object.freeze({hidden:0,active:false,reason:'G14_NOT_SIGNED_OR_NOT_LOADED'});
 }
 let hidden=0;
 tileGroup.traverse(n=>{
  if(!n?.isMesh||!n.name?.startsWith(BU_PREFIX))return;
  // Never hide the newly loaded G14 object, nor another tile or neighbour.
  let parent=n.parent,underOriginalArchitecture=false;
  while(parent && parent!==tileGroup){
   if(parent.name==='MASTER_architecture'){underOriginalArchitecture=true;break;}
   parent=parent.parent;
  }
  if(underOriginalArchitecture&&n.visible!==false){
   n.visible=false;hidden++;
   n.userData={...n.userData,neurocityDedup:'G14_CARBONELL_SIGNED_LANDMARK'};
  }
 });
 return Object.freeze({hidden,active:hidden>0,reason:hidden?'SIGNED_G14_REPLACES_BU_244990':'NO_BU_244990_IN_TILE'});
}
