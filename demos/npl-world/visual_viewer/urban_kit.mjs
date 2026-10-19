import * as THREE from 'three';
import {planUrbanKit,makeKitReport} from './urban_kit_layout.mjs';

/**
 * Lightweight, original parametric models. CC0-1.0 dedication; geometry authored
 * for NeuroCity. Not imported photographic, photogrammetric or surveyed props.
 * Ten InstancedMesh draw groups: 3 palm + 3 bench + 2 planter + 1 cycle rack.
 * Building and street geodata meshes remain unchanged.
 */
function frondGeometry(config){
 const vertices=[],indices=[],uv=[];
 const N=config.fronds, S=config.segments;
 for(let j=0;j<N;j++){
  const a=j*2*Math.PI/N,dx=Math.cos(a),dz=Math.sin(a),tx=-dz,tz=dx;
  const length=3.6+0.48*Math.sin(j*2.7);
  const base=vertices.length/3;
  for(let i=0;i<=S;i++){
   const t=i/S, r=.38+length*t;
   const h=.54+1.25*Math.sin(Math.PI*t*.85)-1.9*t*t;
   const width=.02+.43*Math.pow(Math.sin(Math.PI*t),.8);
   for(const side of [-1,1]){
    vertices.push(dx*r+tx*width*side,h,dz*r+tz*width*side);
    uv.push(t,side>0?1:0);
   }
  }
  for(let i=0;i<S;i++){
   const k=base+i*2;
   indices.push(k,k+1,k+2,k+1,k+3,k+2);
  }
 }
 const geo=new THREE.BufferGeometry();
 geo.setAttribute('position',new THREE.Float32BufferAttribute(vertices,3));
 geo.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));
 geo.setIndex(indices);geo.computeVertexNormals();
 return geo;
}

function instanced(group,name,geometry,material,items,transform,{shadow=false}={}){
 if(!items.length)return null;
 const mesh=new THREE.InstancedMesh(geometry,material,items.length),v=new THREE.Object3D();
 mesh.name='NEUROCITY_CC0_ART_'+name;
 items.forEach((p,i)=>{
   v.position.set(0,0,0);v.rotation.set(0,0,0);v.scale.set(1,1,1);
   transform(v,p,i);v.updateMatrix();mesh.setMatrixAt(i,v.matrix);
 });
 mesh.instanceMatrix.needsUpdate=true;
 mesh.castShadow=shadow;mesh.receiveShadow=false;
 mesh.computeBoundingSphere();
 group.add(mesh);return mesh;
}

export function buildUrbanKit({tier='desktop'}={}){
 const plan=planUrbanKit(tier),group=new THREE.Group();
 group.name='NEUROCITY_MEDITERRANEAN_KIT_CC0_ARTISTIC';
 const bark=new THREE.MeshStandardMaterial({color:0x8b6646,roughness:.96});
 const foliage=new THREE.MeshStandardMaterial({color:0x386443,roughness:.88,side:THREE.DoubleSide});
 const collar=new THREE.MeshStandardMaterial({color:0x52673a,roughness:.98});
 const timber=new THREE.MeshStandardMaterial({color:0x987257,roughness:.83});
 const iron=new THREE.MeshStandardMaterial({color:0x263b40,metalness:.65,roughness:.4});
 const ceramic=new THREE.MeshStandardMaterial({color:0xb89d82,roughness:.9});
 const shrub=new THREE.MeshStandardMaterial({color:0x4d7251,roughness:.93});
 const palmTrunk=new THREE.CylinderGeometry(.17,.31,6.5,9,6);
 const palmFronds=frondGeometry(plan.config),palmCore=new THREE.IcosahedronGeometry(.38,1);
 instanced(group,'palm_trunks',palmTrunk,bark,plan.palms,(o,p)=>{o.position.set(p.x,3.25*p.scale-.06,p.z);o.scale.setScalar(p.scale);}, {shadow:tier==='desktop'});
 instanced(group,'palm_canopies',palmFronds,foliage,plan.palms,(o,p)=>{
   o.position.set(p.x,6.55*p.scale-.06,p.z);o.rotation.y=p.heading;o.scale.setScalar(p.scale);
 });
 instanced(group,'palm_crowns',palmCore,collar,plan.palms,(o,p)=>{o.position.set(p.x,6.55*p.scale-.06,p.z);o.scale.setScalar(p.scale);});
 const seat=new THREE.BoxGeometry(1.9,.13,.59),back=new THREE.BoxGeometry(1.9,.7,.11),leg=new THREE.BoxGeometry(.13,.81,.13);
 instanced(group,'bench_seats',seat,timber,plan.benches,(o,p)=>{o.position.set(p.x,.82,p.z);o.rotation.y=p.heading;});
 instanced(group,'bench_backs',back,timber,plan.benches,(o,p)=>{o.position.set(p.x,1.19,p.z-.26);o.rotation.y=p.heading;});
 const benchLegs=plan.benches.flatMap(p=>[-.76,.76].map(offset=>({...p,offset})));
 instanced(group,'bench_legs',leg,iron,benchLegs,(o,p)=>{
  o.position.set(p.x+p.offset,.43,p.z);
  o.rotation.y=p.heading;
 });
 instanced(group,'planter_pots',new THREE.CylinderGeometry(.70,.55,.56,10),ceramic,plan.planters,(o,p)=>o.position.set(p.x,.28,p.z));
 instanced(group,'planter_shrubs',new THREE.DodecahedronGeometry(.65,1),shrub,plan.planters,(o,p)=>{
  o.position.set(p.x,.92,p.z);o.scale.set(1.08,.72,1.08);
 });
 // Industrial black-metal inverted U bicycle racks, without any personal bicycles.
 instanced(group,'cycle_racks',new THREE.TorusGeometry(.43,.041,6,16,Math.PI),iron,plan.cycles,(o,p)=>{
   o.position.set(p.x,.57,p.z);o.rotation.y=p.heading;
 });
 const stats={...makeKitReport(plan),meshGroups:group.children.length,
   totalTriangles:group.children.reduce((sum,m)=>{
      const g=m.geometry,triangles=g.index?g.index.count/3:g.getAttribute('position').count/3;
      return sum+Math.round(triangles*m.count);
   },0),usesInstanceMeshes:group.children.every(o=>o.isInstancedMesh)};
 group.userData={...stats};
 return {group,stats};
}
