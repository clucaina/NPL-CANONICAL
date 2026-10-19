import * as THREE from 'three';

/**
 * OSM road surface material enhancement.
 * Geometry comes EXCLUSIVELY from georeferenced OSM highway centerline ribbons
 * exported inside alicante.glb. Widths/kerbs remain estimated, not surveyed.
 * Generated albedo texture is an original reproducible procedural material.
 */
export const SURFACE_SOURCE='OSM_centerline_width_estimated_not_surveyed';
export const SURFACE_NAMES=Object.freeze({
  vehicular:'OSM_REAL_vehicular_ways_not_surveyed_width',
  service:'OSM_REAL_service_ways_not_surveyed_width',
  pedestrian:'OSM_REAL_pedestrian_ways_not_surveyed_width'
});

function hash(x,y,seed=31){
  let n=(Math.imul(x|0,374761393)+Math.imul(y|0,668265263)+Math.imul(seed|0,2246822519))|0;
  n=Math.imul(n^(n>>>13),1274126177);return ((n^(n>>>16))>>>0)/4294967295;
}

export function pixelsForSurface(kind,side=256){
  if(!['asphalt','stone'].includes(kind)||!Number.isInteger(side)||side<8||side>1024)
    throw RangeError('Unsupported ground texture');
  const data=new Uint8Array(side*side*4);
  for(let y=0;y<side;y++)for(let x=0;x<side;x++){
    const n=hash(x,y,kind==='asphalt'?43:91);
    const micro=hash(Math.floor(x/5),Math.floor(y/5),37);
    const speck=n>.988?20:n<.012?-16:0;
    const idx=(y*side+x)*4;
    let channels;
    if(kind==='asphalt'){
      const v=Math.max(24,Math.min(130,73+(n-.5)*27+(micro-.5)*12+speck));
      channels=[v+2,v+3,v+5];
    }else{
      const seam=x%64<2||y%64<2;
      const v=Math.max(42,Math.min(225,170+(n-.5)*13+(micro-.5)*22));
      channels=seam?[v*.72,v*.70,v*.68]:[v,v*.95,v*.83];
    }
    for(let k=0;k<3;k++)data[idx+k]=Math.round(Math.max(0,Math.min(255,channels[k])));
    data[idx+3]=255;
  }
  return data;
}

export function createSurfaceTexture(kind,side=256){
  const texture=new THREE.DataTexture(pixelsForSurface(kind,side),side,side,THREE.RGBAFormat);
  texture.colorSpace=THREE.SRGBColorSpace;
  texture.wrapS=THREE.RepeatWrapping;texture.wrapT=THREE.RepeatWrapping;
  texture.generateMipmaps=true;
  texture.minFilter=THREE.LinearMipmapLinearFilter;
  texture.magFilter=THREE.LinearFilter;
  texture.anisotropy=4;
  texture.needsUpdate=true;
  texture.name='NEUROCITY_ORIGINAL_PROCEDURAL_'+kind;
  return texture;
}

export function classifyOSMSurface(name){
  if(typeof name!=='string')return null;
  for(const [kind,exact] of Object.entries(SURFACE_NAMES)){
    // glTF exporter may add suffixes to object names; require exact OSM marker prefix.
    if(name===exact||name.startsWith(exact+'.'))return kind;
  }
  return null;
}

export function generateWorldPlaneUV(mesh,metresPerTile=3.2){
  if(!Number.isFinite(metresPerTile)||metresPerTile<=0)throw RangeError('Texture scale');
  mesh.updateWorldMatrix(true,false);
  const pos=mesh.geometry?.getAttribute('position');
  if(!pos||pos.count<3)throw Error('Cannot project empty road geometry');
  const buffer=new Float32Array(pos.count*2);
  const world=new THREE.Vector3();
  for(let i=0;i<pos.count;i++){
    world.fromBufferAttribute(pos,i).applyMatrix4(mesh.matrixWorld);
    buffer[2*i]=world.x/metresPerTile;
    buffer[2*i+1]=world.z/metresPerTile;
  }
  const clone=mesh.geometry.clone();
  clone.setAttribute('uv',new THREE.Float32BufferAttribute(buffer,2));
  return clone;
}

export function enhanceMappedOSMRoads(city,{mobile=false}={}){
  if(!city?.traverse)throw new TypeError('An actual GLTF scene is required');
  const tex=createSurfaceTexture('asphalt',mobile?128:256);
  const paving=createSurfaceTexture('stone',mobile?128:256);
  const asphalt=new THREE.MeshStandardMaterial({
    name:'NEUROCITY_VERIFIED_OSM_ASPHALT',
    map:tex,color:0xffffff,metalness:0,roughness:.96
  });
  const stone=new THREE.MeshStandardMaterial({
    name:'NEUROCITY_OSM_PEDESTRIAN_PAVING',
    map:paving,color:0xffffff,metalness:0,roughness:.93
  });
  const counts={vehicular:0,service:0,pedestrian:0};
  let vertices=0;
  city.traverse(mesh=>{
    if(!mesh.isMesh)return;
    const type=classifyOSMSurface(mesh.name);
    if(!type)return;
    const geometry=generateWorldPlaneUV(mesh,type==='pedestrian'?2.5:3.2);
    vertices+=geometry.getAttribute('position').count;
    mesh.geometry=geometry;
    mesh.material=type==='pedestrian'?stone:asphalt;
    mesh.receiveShadow=true;
    mesh.castShadow=false;
    mesh.userData.roadSurface=type;
    mesh.userData.provenance=SURFACE_SOURCE;
    counts[type]++;
  });
  return Object.freeze({
    counts,vertices,source:SURFACE_SOURCE,
    asphaltMaterialApplied:counts.vehicular+counts.service>0,
    originalSourceChanged:false,textureKinds:2
  });
}
