export function inspectPublicCityModel(scene){
 if(!scene?.traverse || !scene?.updateMatrixWorld)throw new TypeError('Three scene missing');
 scene.updateMatrixWorld(true);
 const result={meshCount:0,triangleCount:0,wallTriangles:0,roofTriangles:0,roadTriangles:0,
  decorativeSurveyed:false,privateAvatarObjects:0,invalidGeometry:0};
 const forbidden=/(^|[_-])(maya|avatar|person|patient|private|face_scan)([_-]|$)/i;
 scene.traverse(node=>{
  if(!node?.isMesh)return;
  result.meshCount++;
  if(forbidden.test(node.name))result.privateAvatarObjects++;
  const position=node.geometry?.getAttribute?.('position');
  const count=node.geometry?.index?.count??position?.count??0;
  if(!Number.isFinite(count)||count<3||count%3!==0){result.invalidGeometry++;return;}
  const tris=count/3;
  result.triangleCount+=tris;
  if(node.name.startsWith('OSM_Real_Building_Walls'))result.wallTriangles+=tris;
  if(node.name.startsWith('OSM_Real_Building_Roofs'))result.roofTriangles+=tris;
  if(node.name.startsWith('OSM_REAL_'))result.roadTriangles+=tris;
 });
 if(result.invalidGeometry||result.privateAvatarObjects||
    !result.wallTriangles||!result.roofTriangles)
   throw Error('Public GLB missing valid roof and wall meshes or contains private geometry: '+JSON.stringify(result));
 return Object.freeze(result);
}
