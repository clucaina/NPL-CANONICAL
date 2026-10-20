import * as THREE from 'three';

/** Public OSM geometry only. Camera inspection never guesses a building, height,
 * texture, address, occupant or ownership. No private G19/V50 GLB bytes touched.
 */
export const WALL_INSPECTION_SOURCE='OSM_REAL_BUILDING_WALLS_PUBLIC_GEOMETRY';
const WALL_NAME='OSM_Real_Building_Walls_UNTEXTURED';

export function nearestSourceFacadeView(city,eyeReference,{maxDistance=95}={}){
 if(!city?.traverse||!eyeReference?.isVector3||!Number.isFinite(maxDistance)||maxDistance<=0)
   throw TypeError('Real city scene and world reference required');
 const a=new THREE.Vector3(),b=new THREE.Vector3(),c=new THREE.Vector3(),center=new THREE.Vector3();
 const ab=new THREE.Vector3(),ac=new THREE.Vector3(),normal=new THREE.Vector3(),toViewer=new THREE.Vector3();
 let best=null,score=Infinity,facesChecked=0;
 city.updateMatrixWorld(true);
 city.traverse(mesh=>{
   if(!mesh.isMesh||!(mesh.name===WALL_NAME||mesh.name.startsWith(WALL_NAME+'.')))return;
   const geometry=mesh.geometry,pos=geometry?.getAttribute('position'),indices=geometry?.index;
   if(!pos||!Number.isInteger(pos.count)||pos.count<3)return;
   const triangles=(indices?indices.count:pos.count)/3;
   if(!Number.isInteger(triangles)||triangles>150_000)return;
   for(let i=0;i<triangles;i++){
     const pick=j=>indices?indices.getX(i*3+j):i*3+j;
     a.fromBufferAttribute(pos,pick(0)).applyMatrix4(mesh.matrixWorld);
     b.fromBufferAttribute(pos,pick(1)).applyMatrix4(mesh.matrixWorld);
     c.fromBufferAttribute(pos,pick(2)).applyMatrix4(mesh.matrixWorld);
     if(![a.x,a.y,a.z,b.x,b.y,b.z,c.x,c.y,c.z].every(Number.isFinite))continue;
     ab.subVectors(b,a);ac.subVectors(c,a);
     normal.crossVectors(ab,ac);
     if(normal.lengthSq()<.02)continue;
     normal.normalize();
     center.copy(a).add(b).add(c).multiplyScalar(1/3);
     if(center.y<2.8||center.y>18.0||Math.abs(normal.y)>.15)continue;
     facesChecked++;
     const dist=Math.hypot(eyeReference.x-center.x,eyeReference.z-center.z);
     if(dist>maxDistance)continue;
     toViewer.subVectors(eyeReference,center);
     const facing=normal.x*toViewer.x+normal.z*toViewer.z;
     const cost=dist+(facing<0?maxDistance:0);
     if(cost>=score)continue;
     const lookTarget=center.clone();
     const position=center.clone().addScaledVector(normal,4.1);
     position.y=Math.max(2,center.y-.3);
     best={source:WALL_INSPECTION_SOURCE,originalMesh:mesh.name,
       target:lookTarget,position,normal:normal.clone(),
       distanceToObserver:dist,facadeSourceVerified:true,
       surfaceVisualsArtisticNotSurveyed:true,sourceGeometryUnchanged:true,
       geometryInvented:0};
     score=cost;
   }
 });
 return best?{...best,facesChecked}:null;
}

/** Camera pose preserving exploration actor/player state. */
export function placeInspectionCamera(camera,view){
 if(!camera?.isPerspectiveCamera||!view?.position?.isVector3||!view.target?.isVector3)
   throw TypeError('A genuine 3D camera and source-wall pose are required');
 camera.position.copy(view.position);
 camera.lookAt(view.target);
 camera.updateMatrixWorld(true);
 return {cameraMovedForQA:true,source:view.source,playerMoved:false};
}
