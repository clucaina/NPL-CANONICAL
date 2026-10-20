/**
 * NeuroCity is a CONSUMER of the original protected NPL brain, not its owner.
 *
 * Canonical archive: NPL-CANONICAL-C14-R3-NEUROVISUAL-SYSTEMS-OS
 * Source: ORIGINAL public/assets/brain/brain.glb and manifest.json.
 * Rendering belongs exclusively to the original BrainViewer.tsx in a
 * same-origin, sandboxed iframe; NEVER draw a procedural replacement.
 *
 * The original 3D model is CC BY-SA 4.0 (Z-Anatomy / BodyParts3D upstream
 * attribution in provenance.json). These model bytes must not be added to the
 * public GitHub branch. The local owner-owned archive carries its provenance.
 */
export const CANONICAL_NPL = Object.freeze({
   schema:'npl.canonical-anatomical-brain.v3',
   source:'NPL-CANONICAL-C14-R3',
   glb:'./assets/brain/brain.glb',
   manifest:'./assets/brain/manifest.json',
   provenance:'./assets/brain/provenance.json',
   originalViewer:'src/components/BrainViewer.tsx',
   expectedStructures:437,
   expectedPrimitives:563,
   glbBytes:4650816,
   glbSHA256:'76a49ea4526a4880613aec7a02756bd7301b0b9d0680d7cae33e197b672c5453',
   manifestBytes:137895,
   manifestSHA256:'36385df49ce862455b864c7ea25e405badab2bd4953a949a2fa4240b1ff549ad',
   sourceViewerSHA256:'bc9f607da0dbc9a321dce9ed2df74d3ffc4670a1c07558951d84e493092a46d8',
   runtimeVersions:{three:'0.167.1',draco:'r167',react:'18.2.0'},
   viewer:'./canonical-npl/brain.html',
   originalModelNeverModified:true,notClinicalImagingOfPlayer:true
});
export function validateCanonicalManifest(doc){
 if(!doc||!Array.isArray(doc.nodes)||doc.nodes.length!==CANONICAL_NPL.expectedStructures)
  throw new Error('NPL original 437-structure manifest required');
 const ids=new Set(),glbIndices=new Set();
 for(const n of doc.nodes){
   if(!n || !Number.isInteger(n.id) ||n.id<0 ||
     !Number.isInteger(n.gltfNodeIndex)||n.gltfNodeIndex<0 ||
     typeof n.label!=='string'||!n.label.trim()||
     ids.has(n.id)||glbIndices.has(n.gltfNodeIndex))
    throw new Error('NPL canonical structure / glTF mesh correspondence invalid');
   ids.add(n.id);glbIndices.add(n.gltfNodeIndex);
 }
 return Object.freeze({
   structures:ids.size,
   mappedModelNodes:glbIndices.size,
   meshPrimitivesExpected:CANONICAL_NPL.expectedPrimitives,
   fromOriginalAtlas:true,
   source:CANONICAL_NPL.source
 });
}
export async function sha256Hex(bytes,cryptoSubtle=globalThis.crypto?.subtle){
 if(!bytes?.byteLength || typeof cryptoSubtle?.digest!=='function')
  throw new Error('SHA256 browser integrity unavailable');
 const digest=new Uint8Array(await cryptoSubtle.digest('SHA-256',bytes));
 return [...digest].map(x=>x.toString(16).padStart(2,'0')).join('');
}
async function verifiedBytes(path,bytesExpected,shaExpected,{fetcher,cryptoSubtle}){
 const res=await fetcher(path,{cache:'no-store',credentials:'omit'});
 if(!res?.ok)throw new Error('Canonical NPL source not installed: '+path);
 const data=await res.arrayBuffer();
 if(data.byteLength!==bytesExpected||await sha256Hex(data,cryptoSubtle)!==shaExpected)
  throw new Error('NPL canonical source mismatch; refusing substitute brain');
 return data;
}
export async function verifyCanonicalNPLSource({
 fetcher=globalThis.fetch?.bind(globalThis),
 cryptoSubtle=globalThis.crypto?.subtle
}={}){
 if(typeof fetcher!=='function')throw new TypeError('Local fetch required');
 const manifestRaw=await verifiedBytes(CANONICAL_NPL.manifest,
   CANONICAL_NPL.manifestBytes,CANONICAL_NPL.manifestSHA256,{fetcher,cryptoSubtle});
 const manifest=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(manifestRaw));
 const index=validateCanonicalManifest(manifest);
 const glb=await verifiedBytes(CANONICAL_NPL.glb,
   CANONICAL_NPL.glbBytes,CANONICAL_NPL.glbSHA256,{fetcher,cryptoSubtle});
 const header=new DataView(glb);
 if(header.getUint32(0,true)!==0x46546c67||
    header.getUint32(4,true)!==2 ||
    header.getUint32(8,true)!==glb.byteLength)
   throw new Error('NPL source is not valid GLB v2');
 return {...index,verified:true,
   originalViewerRequired:true,neurocityHasNoProceduralBrain:true,
   anatomyFromOriginalGLB:true,patientDataUsed:false,
   remoteUpload:false
 };
}
export function validateCanonicalFrameMessage(evt,expectedOrigin,frameWindow){
 if(!evt||evt.origin!==expectedOrigin||evt.source!==frameWindow)return null;
 const m=evt.data;
 if(!m||m.type!=='NPL_CANONICAL_BRAIN_STATUS_V1'||
    m.source!=='NPL-CANONICAL-C14-R3')return null;
 if(m.state==='READY'&&
    (!Number.isInteger(m.meshCount)||m.meshCount<437||m.meshCount>1500||
     m.modelSource!=='ORIGINAL_PROTECTED_GLB'))return null;
 if(!['LOADING','READY','ERROR'].includes(m.state))return null;
 return {state:m.state,meshCount:m.state==='READY'?m.meshCount:null,
  source:m.source};
}
export function attachCanonicalNPLDialog({openButton,closeButton,dialog,frame,status}){
 if(!openButton||!closeButton||!dialog||!frame||!status)
  throw TypeError('Original NPL atlas controls missing');
 let verified=false,busy=false;
 const msg=event=>{
   const parsed=validateCanonicalFrameMessage(event,location.origin,frame.contentWindow);
   if(!parsed)return;
   status.textContent=parsed.state==='READY'
      ?'NPL canónico cargado · '+parsed.meshCount+' mallas anatómicas'
      :parsed.state==='ERROR'?'El atlas original no pudo renderizarse.': 'Cargando atlas original…';
   status.dataset.state=parsed.state;
   if(parsed.state==='READY')window.NPL_CANONICAL_STATUS={
      source:CANONICAL_NPL.source,
      structures:437,meshesLoaded:parsed.meshCount,
      actualOriginalAnatomicalGLB:true,notNeuralMeasurement:true
   };
 };
 const click=async()=>{
   if(busy)return;
   dialog.hidden=false;openButton.setAttribute('aria-expanded','true');
   if(verified){frame.hidden=false;frame.focus();return;}
   busy=true;status.textContent='Verificando originales NPL (437 estructuras) con SHA-256…';
   try{
      const manifest=await verifyCanonicalNPLSource();
      window.NPL_CANONICAL_STATUS={...manifest,state:'ASSETS_VERIFIED_RUNTIME_PENDING'};
      verified=true;frame.src=CANONICAL_NPL.viewer;frame.hidden=false;
      status.textContent='Abriendo BrainViewer.tsx original · Three 0.167.1 + Draco r167…';
   }catch(error){
      status.textContent=String(error?.message||error).slice(0,190);
      status.dataset.state='UNAVAILABLE_NO_TOY_FALLBACK';
      frame.hidden=true;
      window.NPL_CANONICAL_STATUS={state:'SOURCE_NOT_PRESENT_OR_INTEGRITY_FAILED',
        reason:status.textContent};
   }finally{busy=false;}
 };
 const close=()=>{dialog.hidden=true;openButton.setAttribute('aria-expanded','false');openButton.focus();};
 const escape=e=>{if(e.key==='Escape'&&!dialog.hidden)close();};
 openButton.addEventListener('click',click);
 closeButton.addEventListener('click',close);
 window.addEventListener('keydown',escape);
 window.addEventListener('message',msg);
 status.textContent='Atlas anatómico canónico (437 estructuras) · carga privada bajo demanda.';
 dialog.hidden=true;frame.hidden=true;frame.title='Atlas NPL original · 437 estructuras anatómicas 3D';
 return {open:click,close,dispose(){
   openButton.removeEventListener('click',click);
   closeButton.removeEventListener('click',close);
   window.removeEventListener('keydown',escape);
   window.removeEventListener('message',msg);
 }};
}
