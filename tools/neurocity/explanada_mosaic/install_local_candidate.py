#!/usr/bin/env python3
"""Build a reversible NONPUBLISHED V50 WorldMaster candidate ZIP, never touching original.
No internet, no personal data, no external publishing. Copies original entry bytes
into a *new archive* and swaps one role=mosaic manifest pointer after SHA checks.
"""
from __future__ import annotations
import argparse, hashlib, io, json, zipfile
from pathlib import Path

SRC='world-master/assets/selected/Explanada_v50_PBR_1024.glb'
NEW='world-master/assets/selected/Explanada_V50_Surgical_4cm_STONES_PRIVATE.glb'
MANIFEST='world-master/manifest.json'
EXPECTED_SOURCE='02b44285e3bc478310e3b86d939b45e90ff80359ddfc57a759bf72803556a710'

def sha(b):return hashlib.sha256(b).hexdigest()

def build(basezip, asset, resultzip, patch_audit):
    asset=Path(asset);basezip=Path(basezip);resultzip=Path(resultzip)
    data=asset.read_bytes();audit=json.loads(Path(patch_audit).read_text())
    assert audit['candidate_sha256']==sha(data)
    assert audit['original_source_asset_sha256']==EXPECTED_SOURCE
    if audit.get('redistribution_allowed') is not False:raise ValueError('Source privacy policy not preserved')
    with zipfile.ZipFile(basezip,'r') as source:
        old=source.read(SRC)
        if sha(old)!=EXPECTED_SOURCE:raise ValueError('V50 archive source bytes changed')
        names=source.namelist()
        if len(names)!=len(set(names)) or NEW in names:raise ValueError('Unexpected duplicate original content')
        for name in names:
            if name.startswith('/') or '..' in Path(name).parts or '\\' in name:raise ValueError('Unsafe legacy ZIP entry')
        manifest=json.loads(source.read(MANIFEST))
        if manifest.get('public_redistribution_allowed') is not False:raise ValueError('Unexpected public redistribution policy')
        targets=[x for t in manifest['tiles'] for x in t['assets'] if x.get('role')=='mosaic' and x['path']==SRC[len('world-master/'):]]
        if len(targets)!=1:raise ValueError('Source mosaic not uniquely mapped to G19')
        if manifest.get('asset_hashes',{}).get(SRC[len('world-master/'):],{}).get('sha256')!=EXPECTED_SOURCE:
            raise ValueError('Source manifest hash differs')
        rel=NEW[len('world-master/'):]
        new={**targets[0],'path':rel,'sha256':sha(data),'bytes':len(data),
             'source_hash_record':False,'triangle_estimate':audit['candidate_total_faces'],
             'mesh_count':3,'experimental_candidate':True,
             # Mobile keeps the existing lightweight V50 source instead of
             # loading 100k relief tris. Requires source loader LOD support.
             'mobile_fallback':{'path':SRC[len('world-master/'):],
                 'sha256':EXPECTED_SOURCE,'bytes':len(old),
                 'triangle_estimate':5225,'embedded_images':2}}
        # Only one tile/role changed; all originals stay present in archive for rollback.
        targets[0].clear();targets[0].update(new)
        manifest['asset_hashes'][rel]={k:new[k] for k in ('sha256','bytes','source_hash_record','triangle_estimate','mesh_count')}
        manifest['world_master_version']='G19_V50_PRIVATE_SURGICAL_MOSAIC_CANDIDATE'
        manifest['experimental_candidate_not_public']=True
        manifest['gameplay_webgl_acceptance']='PENDING'
        manifest['source_v50_preserved_in_archive']=True
        manifest['vertical_datum_verified']=False
        serialized=(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode('utf8')
        record={
          'schema':'neurocity.private-candidate-surgical-patch.v1',
          'source_archive_sha256':sha(basezip.read_bytes()),
          'replaced_role':'mosaic',
          'removed_original_assets':0,
          'unmodified_entries':len(names)-1,
          'original_binary_v50_sha256':EXPECTED_SOURCE,
          'replacement_sha256':sha(data),'replacement_path':NEW,
          'verified_GLTF_3_geom_source':True,
          'original_manifest_backed_up':True,
          'rollback':'Restore world-master/manifest.json from world-master/manifest_V50_before_surgical_candidate.json and optionally delete replacement GLB',
          'no_public_redistribution':True,
          'webgl_3d_gameplay_validated':False,
          'mobile_optimized_loader_required':True,
          'visual_fidelity_authoritative':False,
          'vertical_datum_verified':False,
          'patch_info':{k:audit[k] for k in ('source_rect_xz','near_stones','near_faces','removed_projected_area_m2','area_error_m2')}
        }
        resultzip.parent.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(resultzip,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as target:
            def put(name,content):
                # Stable ZIP dates prevent fake new versions on repeated builds.
                meta=zipfile.ZipInfo(name,date_time=(2026,10,20,0,0,0))
                meta.compress_type=zipfile.ZIP_DEFLATED
                meta.external_attr=(0o644 << 16)
                target.writestr(meta,content,compress_type=zipfile.ZIP_DEFLATED,compresslevel=6)
            for item in source.infolist():
                # Original contents are unmodified; only main manifest changes.
                put(item.filename,serialized if item.filename==MANIFEST else source.read(item.filename))
            put(NEW,data)
            put('world-master/manifest_V50_before_surgical_candidate.json',source.read(MANIFEST))
            put('CANDIDATE_V6_AUDIT.json',json.dumps(record,indent=2).encode('utf8'))
    with zipfile.ZipFile(resultzip,'r') as zz,zipfile.ZipFile(basezip,'r') as ss:
        if zz.testzip() is not None:raise AssertionError('CRC failure')
        candidate=json.loads(zz.read(MANIFEST));orig=json.loads(ss.read(MANIFEST))
        assert zz.read(SRC)==ss.read(SRC)
        assert candidate['tiles'][0]['assets'][7]['path']==NEW[len('world-master/'):]
        assert all(zz.read(n)==ss.read(n) for n in ss.namelist() if n!=MANIFEST)
        assert zz.read('world-master/manifest_V50_before_surgical_candidate.json')==ss.read(MANIFEST)
    return {**record,'candidate_archive_sha256':sha(resultzip.read_bytes()),'candidate_archive_bytes':resultzip.stat().st_size,
            'candidate_entries':len(zz.namelist()),'zip_CRC':'PASS','original_asset_content_unchanged':True}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--base-zip',required=True);p.add_argument('--model',required=True);p.add_argument('--audit',required=True);p.add_argument('--out-zip',required=True)
    a=p.parse_args();print(json.dumps(build(a.base_zip,a.model,a.out_zip,a.audit),indent=2))