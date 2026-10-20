import * as THREE from 'three';
import {planUrbanKit,makeKitReport} from './urban_kit_layout.mjs';

/**
 * Lightweight, original parametric models. CC0-1.0 dedication; geometry authored
 * for NeuroCity. Not imported photographic, photogrammetric or surveyed props.
 * Eleven InstancedMesh draw groups: 5 palm + 3 bench + 2 planter + 1 cycle rack.
 * Building and street geodata meshes remain unchanged.
 */
function frondGeometry(config,variant=0){
 const vertices=[],indices=[],uv=[];
 const N=config.fronds+(variant===2?4:0),S=config.segments+2;
 const canopyLength=[3.75,4.42,3.10][variant];
 const arch=[1.20,1.72,.83][variant];
 const droop=[1.9,2.55,1.24][variant];
 const bladeWidth=[.42,.33,.57][variant];
 const put=(p,u,v)=>{vertices.push(...p);uv.push(u,v);};
 for(let j=0;j<N;j++){
  const angle=j*2*Math.PI/N+.17*Math.sin(j*1.9);
  const dx=Math.cos(angle),dz=Math.sin(angle),tx=-dz,tz=dx;
  const length=canopyLength*(.88+.12*Math.sin(j*2.77+variant));
  const base=vertices.length/3;
  for(let i=0;i<=S;i++){
   const t=i/S;
   const radius=.26+length*t;
   const y=.26+arch*Math.sin(Math.PI*t*.90)-droop*t*t;
   const width=(.035+bladeWidth*Math.pow(Math.sin(Math.PI*t),.83))*(1-.10*Math.sin(j));
   for(const side of [-1,1]){
    put([dx*radius+tx*width*side,y+side*.022,dz*radius+tz*width*side],t,side>0?1:0);
   }
  }
  for(let i=0;i<S;i++){
   const k=base+i*2;
   indices.push(k,k+1,k+2,k+1,k+3,k+2);
  }
  // Narrow paired leaflets along the date-palm rachis create recognizable
  // feathery silhouettes, not opaque solid triangular LEGO palm leaves.
  const leafletCount=variant===2?6:9;
  for(let n=1;n<=leafletCount;n++){
   const t=n/(leafletCount+1),radius=.26+length*t;
   const y=.26+arch*Math.sin(Math.PI*t*.90)-droop*t*t;
   const segment=.38+(.48* Math.sin(Math.PI*t));
   const span=[.47,.35,.60][variant]*Math.sin(Math.PI*t);
   for(const side of [-1,1]){
    const k=vertices.length/3;
    const cx=dx*radius,cz=dz*radius;
    put([cx-tx*span*.04*side,y,cz-tz*span*.04*side],t,0);
    put([cx+tx*span*side,y+.045,cz+tz*span*side],t,.5);
    put([cx+tx*(span+segment)*side+dx*.13,y-.26*t,
         cz+tz*(span+segment)*side+dz*.13],t,1);
    indices.push(k,k+1,k+2);
   }
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
 const palmCore=new THREE.IcosahedronGeometry(.38,1);
 instanced(group,'palm_trunks',palmTrunk,bark,plan.palms,(o,p)=>{o.position.set(p.x,3.25*p.scale-.06,p.z);o.scale.setScalar(p.scale);}, {shadow:tier==='desktop'});
 const frondColors=[0x315e40,0x44734a,0x507547];
 for(let variant=0;variant<3;variant++){
   const palms=plan.palms.filter(p=>p.variant===variant);
   const shape=frondGeometry(plan.config,variant);
   const green=new THREE.MeshStandardMaterial({color:frondColors[variant],
     roughness:.84,metalness:0,side:THREE.DoubleSide});
   instanced(group,'palm_canopies_'+variant,shape,green,palms,(o,p)=>{
     o.position.set(p.x,6.55*p.scale-.06,p.z);
     o.rotation.y=p.heading;o.scale.setScalar(p.scale);
     o.scale.x*=variant===1?.87:variant===2?1.12:1;
   });
 }
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
