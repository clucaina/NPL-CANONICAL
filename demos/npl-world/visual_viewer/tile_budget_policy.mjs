/**
 * NeuroCity recovered GLB streaming guard: conservative, deterministic
 * per-tile geometry and embedded-image budgets. These are estimated costs,
 * NOT measurements of GPU memory, draw calls or real FPS.
 *
 * Essential geometry is NOT exempt: if it cannot fit, the existing OSM city
 * remains the fallback instead of forcing an oversized archived tile to load.
 */
export const TILE_BUDGETS=Object.freeze({
  mobile:Object.freeze({triangles:290_000,images:30}),
  desktop:Object.freeze({triangles:1_500_000,images:140})
});

export function selectTileAssetsWithinBudget(candidates,profile='desktop'){
  const budget=TILE_BUDGETS[profile];
  if(!budget||!Array.isArray(candidates))throw new RangeError('Invalid tile budget request');
  let triangles=0,images=0;
  const selected=[];
  for(const asset of candidates){
    const cost=asset?.triangle_estimate??Math.ceil(asset?.bytes/20);
    const imageCost=asset?.embedded_images??1;
    if(!Number.isSafeInteger(cost)||cost<1||!Number.isSafeInteger(imageCost)||imageCost<0)
      throw new RangeError('Unverified tile geometry or image cost');
    if(triangles+cost>budget.triangles||images+imageCost>budget.images)continue;
    selected.push(asset);triangles+=cost;images+=imageCost;
  }
  return selected;
}
