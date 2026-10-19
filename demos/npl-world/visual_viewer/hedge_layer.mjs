import * as THREE from 'three';

export const HEDGE_SOURCE='illustrative_landscaping_not_surveyed';
const round=n=>Math.round(n*1000)/1000;
function noise(k){const v=Math.sin(k*76.283+4.5)*25731.721;return v-Math.floor(v);}

/** Planting alignment is approximate, and NEVER a claim of surveyed tree locations. */
export function planHedges(tier='desktop'){
  if(tier!=='mobile'&&tier!=='desktop')throw RangeError('Unknown foliage tier');
  const step=tier==='mobile'?3.8:2.2, hedges=[];
  for(const [row,x] of [[0,-20.15],[1,7.0]]){
    for(let z=-134;z<=103;z+=step){
      const phase=noise(z+row*73);
      hedges.push({
        x:round(x+(phase-.5)*.22),
        z:round(z+(noise(z+13)-.5)*.42),
        width:round(.92+noise(z+row*13)*.24),
        height:round(.72+noise(z+row*31)*.35),
        variant:row
      });
    }
  }
  return Object.freeze({
    tier,origin:HEDGE_SOURCE,hedges,
    count:hedges.length,plantingsSurveyed:false,privateImagesUsed:false
  });
}

function instanced(group,name,geo,mat,hedges,transform){
  const mesh=new THREE.InstancedMesh(geo,mat,hedges.length);
  mesh.name='NEUROCITY_ART_HEDGE_'+name;
  const temp=new THREE.Object3D();
  hedges.forEach((p,i)=>{temp.position.set(0,0,0);temp.rotation.set(0,0,0);temp.scale.set(1,1,1);
    transform(temp,p,i);temp.updateMatrix();mesh.setMatrixAt(i,temp.matrix);
  });
  mesh.instanceMatrix.needsUpdate=true;
  mesh.castShadow=false;mesh.receiveShadow=true;mesh.computeBoundingSphere();
  group.add(mesh);
  return mesh;
}

/** Real GPU instancing; three-dimensional plant crowns, not flat green cards or fake photos. */
export function buildHedgeLayer(tier='desktop'){
 const plan=planHedges(tier);
 const group=new THREE.Group();group.name='NEUROCITY_ARTISTIC_HEDGES';
 const coreMat=new THREE.MeshStandardMaterial({color:0x385b39,roughness:.98});
 const lightMat=new THREE.MeshStandardMaterial({color:0x648a43,roughness:.94});
 const darkMat=new THREE.MeshStandardMaterial({color:0x244b31,roughness:.96});
 const soilMat=new THREE.MeshStandardMaterial({color:0x66513b,roughness:1});
 const edgeMat=new THREE.MeshStandardMaterial({color:0xb8ad94,roughness:.94});
 const geoMain=new THREE.DodecahedronGeometry(.61,1);
 const geoLobe=new THREE.IcosahedronGeometry(.41,tier==='mobile'?0:1);
 const geoEdge=new THREE.BoxGeometry(1.1,.16,tier==='mobile'?3.5:2.15);
 const geoSoil=new THREE.BoxGeometry(1.35,.055,tier==='mobile'?3.6:2.3);
 instanced(group,'soil',geoSoil,soilMat,plan.hedges,(o,p)=>{
   o.position.set(p.x,.052,p.z);
 });
 instanced(group,'edging',geoEdge,edgeMat,plan.hedges,(o,p)=>{
   o.position.set(p.x+.68,.12,p.z);o.scale.x=.085;
 });
 instanced(group,'bush_mass',geoMain,coreMat,plan.hedges,(o,p)=>{
   o.position.set(p.x,p.height*.47+.08,p.z);o.scale.set(p.width,p.height,1.32);
 });
 instanced(group,'foliage_sunlit',geoLobe,lightMat,plan.hedges,(o,p)=>{
   o.position.set(p.x-.20,p.height*.77+.08,p.z-.24);o.scale.set(p.width*.72,.69,1.0);
 });
 instanced(group,'foliage_shadow',geoLobe,darkMat,plan.hedges,(o,p)=>{
   o.position.set(p.x+.28,p.height*.45+.07,p.z+.33);o.scale.set(.8,.73,1.0);
 });
 const totalTriangles=group.children.reduce((sum,mesh)=>{
   const geo=mesh.geometry;
   return sum+(geo.index?geo.index.count/3:geo.getAttribute('position').count/3)*mesh.count;
 },0);
 const stats={
   tier,count:plan.count,meshGroups:group.children.length,
   totalTriangles:Math.round(totalTriangles),
   origin:HEDGE_SOURCE,allInstanced:group.children.every(m=>m.isInstancedMesh),
   exactLocations:false,sourceDataAltered:false
 };
 group.userData={...stats};
 return {group,stats};
}
