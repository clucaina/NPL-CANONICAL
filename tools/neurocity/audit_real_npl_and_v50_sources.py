#!/usr/bin/env python3
"""Read-only proof that prior USER OWNED sources are intact and not replaced.
No patient material, screenshots, network, exporting, or automatic publication.
This MUST be run locally against copies of the owner's two historic ZIP files.
"""
from __future__ import annotations
import argparse,hashlib,json,re,struct,zipfile
from pathlib import Path

NPL={
 'public/assets/brain/brain.glb':(4650816,'76a49ea4526a4880613aec7a02756bd7301b0b9d0680d7cae33e197b672c5453'),
 'public/assets/brain/manifest.json':(137895,'36385df49ce862455b864c7ea25e405badab2bd4953a949a2fa4240b1ff549ad'),
 'src/components/BrainViewer.tsx':(9160,'bc9f607da0dbc9a321dce9ed2df74d3ffc4670a1c07558951d84e493092a46d8')
}
SURGICAL_PATH='assets/selected/Explanada_V50_Surgical_4cm_STONES_PRIVATE.glb'
SURGICAL_SHA='6a7be6245c7680ea73154a6e90d448af27e3b5abd0859f8ef96368e495601636'
SURGICAL_BYTES=11176704
def sha(data):return hashlib.sha256(data).hexdigest()
def glb_json(blob):
 if len(blob)<20 or blob[:4]!=b'glTF':raise ValueError('Not a GLB 2.0')
 version,size=struct.unpack_from('<II',blob,4)
 chunk_size=struct.unpack_from('<I',blob,12)[0]
 if version!=2 or size!=len(blob) or blob[16:20]!=b'JSON' or chunk_size>len(blob)-20:
  raise ValueError('Invalid original GLB chunk header')
 return json.loads(blob[20:20+chunk_size])
def audit(npl_archive:Path,city_archive:Path):
 report={'schema':'neurocity.restore-authentic-NPL-and-V50.v1',
   'canonical_original_protected_unchanged':False,
   'published_original_files':0,'source_license_requires_review':True}
 with zipfile.ZipFile(npl_archive) as npl:
  original={}
  for path,(size,digest) in NPL.items():
   data=npl.read('NPL-CANONICAL/'+path)
   if len(data)!=size or sha(data)!=digest:
    raise ValueError('Protected NPL source is NOT the authentic expected version: '+path)
   original[path]=data
  m=json.loads(original['public/assets/brain/manifest.json'])
  if len(m.get('nodes',[]))!=437:raise ValueError('Brain missing original 437 structures')
  if len(set(n['id'] for n in m['nodes']))!=437 or len(set(n['gltfNodeIndex'] for n in m['nodes']))!=437:
   raise ValueError('NPL original structure-to-geometry mapping ambiguous')
  gltf=glb_json(original['public/assets/brain/brain.glb'])
  count=sum(len(mesh.get('primitives',[])) for mesh in gltf.get('meshes',[]))
  if len(gltf.get('nodes',[]))!=437 or len(gltf.get('meshes',[]))!=437 or count!=563:
   raise ValueError('Original Draco mesh primitives mismatch')
  if 'KHR_draco_mesh_compression' not in gltf.get('extensionsRequired',[]):
   raise ValueError('NPL expects original Draco mesh data; no toy alternative')
  upstream=json.loads(npl.read('NPL-CANONICAL/public/assets/brain/provenance.json'))
  if upstream.get('canonicalAsset',{}).get('sha256')!=NPL['public/assets/brain/brain.glb'][1]:
   raise ValueError('Brain original provenance integrity missing')
  report.update(canonical_original_protected_unchanged=True,
    structures=437,mesh_primitives=563,npl_brain_sha=NPL['public/assets/brain/brain.glb'][1],
    original_brainviewer_sha=NPL['src/components/BrainViewer.tsx'][1])
 with zipfile.ZipFile(city_archive) as city:
  raw=city.read('world-master/manifest.json')
  city_manifest=json.loads(raw)
  if city_manifest.get('public_redistribution_allowed') is not False:
   raise ValueError('Private source must remain PRIVATE')
  assets=city_manifest['asset_hashes']
  for path,row in assets.items():
   content=city.read('world-master/'+path)
   if len(content)!=row['bytes'] or sha(content)!=row['sha256']:
    raise ValueError('Historic geometry damaged: '+path)
  if len(assets)<77 or SURGICAL_PATH not in assets:
   raise ValueError('Previously completed V50 ceramic relief unavailable')
  mosaic=city.read('world-master/'+SURGICAL_PATH)
  if len(mosaic)!=SURGICAL_BYTES or sha(mosaic)!=SURGICAL_SHA:
   raise ValueError('Original 10,000-stone V50 candidate altered')
  tile_mosaics=[a for t in city_manifest.get('tiles',[]) for a in t.get('assets',[]) if a['role']=='mosaic']
  if len(tile_mosaics)!=1 or tile_mosaics[0]['path']!=SURGICAL_PATH:
   raise ValueError('The historical 4cm geometry is not the active source')
  fb=tile_mosaics[0].get('mobile_fallback')
  if not fb or 'Explanada_v50_PBR_1024.glb' not in fb.get('path',''):
   raise ValueError('Original V50 mobile fallback is not installed')
  if sum(a['role']=='mosaic' for t in city_manifest['tiles'] for a in t['assets'])!=1:
   raise ValueError('Double-loaded mosaic geometry')
  report.update(archived_G19_GLBS=len(assets),
    original_v50_mosaic_sha=SURGICAL_SHA,
    original_v50_surface_preserved=True,
    original_pbr_mobile_fallback=True,
    physical_grids_verified=len([x for x in city.namelist() if re.fullmatch(
      r'world-master/geo/data/physical_r\\d{2}_(?:cm|c)\\d{2}\\.json',x)]),
    new_city_meshes_rendered_in_WebGL=False)
 if report['physical_grids_verified']!=12:
  raise ValueError('G13 geometry/physical original source lost')
 return report
def main():
 parser=argparse.ArgumentParser()
 parser.add_argument('--npl-archive',type=Path,required=True)
 parser.add_argument('--worldmaster-archive',type=Path,required=True)
 parser.add_argument('--json-report',type=Path,required=True)
 args=parser.parse_args()
 data=audit(args.npl_archive,args.worldmaster_archive)
 args.json_report.parent.mkdir(parents=True,exist_ok=True)
 args.json_report.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps({k:data[k] for k in ['canonical_original_protected_unchanged','structures','mesh_primitives','archived_G19_GLBS','physical_grids_verified']},indent=2))
if __name__=='__main__':main()
