"""Private G14 Casa Carbonell L2 overlay for verified NeuroCity V7.
Never upload source GLB/ZIP to GitHub, deploy or overwrite V7. Python stdlib.
Run locally: python tools/neurocity/apply_carbonell_l2_owner.py OWNER_V7.zip G14_L2_PRIVATE.glb DEST.zip
"""
from pathlib import Path
import copy, hashlib, json, sys, zipfile

V7='75fbe60079c0f02c4c0d9263ed8803a4882b95402dda4345c21d883fe2090775'
OLD='assets/source/ASSETS/G14/G14_historic_carbonell_244990.glb'
OLD_SHA='ceb9728f29ebe402ae1a4c7dda63790f67ab2985d6df7837bf31146caa8c5ece'
NEW='assets/selected/G14_CASA_CARBONELL_SOURCE_PRESERVED_L2_PRIVATE.glb'
NEW_SHA='ac82b798d5bc9cc0680f25d4325e94f65622bd8d0989a809dc7474c43931c678'
MANIFEST='world-master/manifest.json'
def sha(data): return hashlib.sha256(data).hexdigest()

def apply(v7,detail,output):
    v7,detail,output=map(Path,(v7,detail,output))
    if v7.resolve()==output.resolve(): raise ValueError('Never overwrite original V7')
    if sha(v7.read_bytes())!=V7: raise ValueError('Source owner ZIP digest mismatch')
    model=detail.read_bytes()
    if sha(model)!=NEW_SHA: raise ValueError('Private G14 L2 digest mismatch')
    with zipfile.ZipFile(v7) as original:
        if original.testzip() is not None: raise ValueError('Original archive CRC failure')
        paths=set(original.namelist())
        if 'world-master/'+NEW in paths: raise ValueError('Original already patched')
        if sha(original.read('world-master/'+OLD))!=OLD_SHA:
            raise ValueError('Old G14 GLB source hash mismatch')
        manifest=json.loads(original.read(MANIFEST))
        if (manifest.get('schema')!='neurocity.local-worldmaster-tiles.v1' or
            manifest.get('vertical_datum_verified') is not False or
            manifest.get('public_redistribution_allowed') is not False):
            raise ValueError('Incompatible owner-only manifest')
        target=[a for tile in manifest['tiles'] if tile['id']=='r02_c00'
                for a in tile['assets'] if a.get('path')==OLD]
        if len(target)!=1 or target[0]['sha256']!=OLD_SHA or target[0]['role']!='landmark':
            raise ValueError('Expected one and only one original Casa Carbonell landmark')
        target[0].update(path=NEW,sha256=NEW_SHA,bytes=len(model),
                         triangle_estimate=56305,mesh_count=11,embedded_images=0,
                         G14_local_detail_candidate=True,
                         surveyed_faithfulness=False,local_ground_datum_verified=False,
                         original_source_preserved=OLD)
        manifest_bytes=json.dumps(manifest,ensure_ascii=False,indent=2).encode('utf8')
        output.parent.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(output,'w') as candidate:
            for entry in original.infolist():
                candidate.writestr(copy.copy(entry),
                    manifest_bytes if entry.filename==MANIFEST else original.read(entry))
            candidate.writestr('world-master/'+NEW,model,
                               compress_type=zipfile.ZIP_DEFLATED,compresslevel=6)
        with zipfile.ZipFile(output) as candidate:
            if candidate.testzip() is not None:raise ValueError('Candidate ZIP CRC failure')
            if set(candidate.namelist())!=paths|{'world-master/'+NEW}:
                raise ValueError('Unexpected output assets')
            for path in paths-{MANIFEST}:
                if sha(original.read(path))!=sha(candidate.read(path)):
                    raise ValueError('Owner-original file altered: '+path)
            current=json.loads(candidate.read(MANIFEST))
            active=[a for t in current['tiles'] for a in t['assets']
                    if a['path'] in (OLD,NEW)]
            if len(active)!=1 or active[0]['path']!=NEW:
                raise ValueError('Overlapping duplicate landmark')
            if sha(candidate.read('world-master/'+NEW))!=NEW_SHA:
                raise ValueError('New asset corrupted')
        return {'status':'PASS_LOCAL_OWNER_ONLY','archive_sha256':sha(output.read_bytes()),
                'originals_preserved':len(paths)-1,'new_asset_count':1,
                'duplicate_landmark':False,'certified_real_world_faithfulness':False,
                'vertical_datum_verified':False,'webgl_gameplay_acceptance':False}

if __name__=='__main__':
    if len(sys.argv)!=4:
        raise SystemExit('Usage: python apply_carbonell_l2_owner.py OWNER_V7.zip G14_L2_PRIVATE.glb DEST.zip')
    print(json.dumps(apply(*sys.argv[1:]),ensure_ascii=False,indent=2))
