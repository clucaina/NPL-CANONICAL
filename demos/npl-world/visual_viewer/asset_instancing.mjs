import * as THREE from 'three';

/**
 * Reuse ORIGINAL archived Phoenix geometry/materials. Every palm variant is
 * instantiated without rebuilding an invented palm. The 2026 Drive source
 * contains 6 distinct geometries; 63 placements are approximate OSM pathways.
 * This module never publishes those source GLB bytes.
 */
export function instantiateMasterPalms(scene,placements,{mobile=false}={}){
 if(!scene?.isObject3D||!Array.isArray(placements)||placements.length>160)
   throw new TypeError('Valid source mesh and bounded positions required');
 scene.updateMatrixWorld(true);
 const sourceMeshes=[];
 scene.traverse(node=>{
   if(node.isMesh){
     if(node.isSkinnedMesh||node.morphTargetInfluences?.length)
       throw new Error('Unbaked skinned/morph palm cannot be instanced');
     sourceMeshes.push(node);
   }
 });
 if(!sourceMeshes.length||sourceMeshes.length>12)throw new Error('Unverified Phoenix topology');
 const group=new THREE.Group();
 group.name='RECOVERED_REAL_SIX_VARIANT_PHOENIX_INSTANCES';
 const ordered=placements.map((p,i)=>({p,i})).filter(({i})=>!mobile||i%2===0);
 const q=new THREE.Quaternion(),pos=new THREE.Vector3(),scale=new THREE.Vector3();
 const local=new THREE.Matrix4(),final=new THREE.Matrix4();
 for(const part of sourceMeshes){
   const mesh=new THREE.InstancedMesh(part.geometry,part.material,ordered.length);
   mesh.name='RECOVERED_PHOENIX_'+(part.name||'mesh');
   mesh.castShadow=false;mesh.receiveShadow=true;
   for(let j=0;j<ordered.length;j++){
     const p=ordered[j].p;
     if (![p.x,p.y,p.z,p.rotation,p.scale].every(Number.isFinite) ||
           p.scale<=0||p.scale>4)
        throw new RangeError('Unsafe Phoenix placement');
     pos.set(p.x,p.y,p.z);
     q.setFromAxisAngle(new THREE.Vector3(0,1,0),p.rotation);
     scale.setScalar(p.scale);
     local.compose(pos,q,scale);
     final.multiplyMatrices(local,part.matrixWorld);
     mesh.setMatrixAt(j,final);
   }
   mesh.instanceMatrix.needsUpdate=true;
   mesh.computeBoundingSphere();
   group.add(mesh);
 }
 const report={
   renderer:'InstancedMesh',uniqueOriginalMeshes:sourceMeshes.length,
   palms:ordered.length,drawCallsUpperBound:sourceMeshes.length,
   originalPositionsUsed:true,locationSurveyed:false,geometryRecreated:false,
   mobileStride:mobile?2:1
 };
 group.userData={...report};
 return {group,report};
}

/**
 * Additional REAL archived 4-metre globe-lamp prefab discovered in the source
 * SHA manifest. Its GLB coordinates are Z-UP (unlike our Y-UP Phoenix source).
 * Convert source-axis orientation BEFORE the authored, provisional G16 pose.
 * No claim that the 5 fixture positions/style exactly match Alicante street lamps.
 */
export function instantiateArchivedStreetlights(scene,placements,{mobile=false}={}){
 if(!scene?.isObject3D)throw new TypeError('Source archived lamp scene required');
 const axis=new THREE.Group();axis.name='SOURCE_Z_UP_TO_THREE_Y_UP';
 axis.rotation.x=-Math.PI/2;
 axis.add(scene);
 const {group,report}=instantiateMasterPalms(axis,placements,{mobile});
 group.name='RECOVERED_ARCHIVED_GLOBE_LAMPS_GPU';
 for(const mesh of group.children)mesh.name=mesh.name.replace('PHOENIX','ORIGINAL_STREETLAMP');
 return {group,report:{...report,modelClass:'archived_globe_lamp',
    sourceAxis:'Z_UP_TO_Y_UP',locationSurveyed:false,originalDesignPreserved:true}};
}
