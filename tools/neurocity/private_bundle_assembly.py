#!/usr/bin/env python3
"""Reversible private G19/V50 bundle assembly. NEVER publish the output to Github.

Input archives are owned/private; the build tool contains no model data.
It checks every copied GLB and all original manifest file references without
mutating the source archive, and records limitations of software-only QA.
"""
import argparse
import hashlib
import json
import pathlib
import zipfile
import os

MAX_COMPILED_UNCOMPRESSED=12*1024*1024
MAX_BYTES=150*1024*1024
SHA=lambda b:hashlib.sha256(b).hexdigest()

def inspect_path(s):
    p=pathlib.PurePosixPath(s)
    if not s or s.startswith(('/', '\\')) or '\\' in s or '..' in p.parts or ':' in p.parts[0]:
        raise ValueError(f'Invalid archive path: {s!r}')
    return s

def assemble(base,compiled,dest,manifest_name='INTEGRACION_WEBGL_V7_REVISABLE.json',compiled_ci_run=None):
    base=pathlib.Path(base); compiled=pathlib.Path(compiled);dest=pathlib.Path(dest)
    if base.resolve()==dest.resolve() or compiled.resolve()==dest.resolve():raise ValueError('Never overwrite inputs')
    with zipfile.ZipFile(base) as original,zipfile.ZipFile(compiled) as patch:
        if sum(i.file_size for i in original.infolist())>MAX_BYTES or sum(i.file_size for i in patch.infolist())>MAX_COMPILED_UNCOMPRESSED:
            raise ValueError('Input ZIP uncompressed size exceeds bounded private builder policy')
        for z in (original,patch):
            if any((i.external_attr >> 16) & 0o170000 == 0o120000 for i in z.infolist()):
                raise ValueError('Symlink ZIP entry forbidden')
        if original.testzip() is not None or patch.testzip() is not None:raise ValueError('CRC integrity failure')
        basepaths=original.namelist(); changed=set(patch.namelist()); newpaths=patch.namelist()
        for p in basepaths+newpaths:inspect_path(p)
        if len(basepaths)!=len(set(basepaths)) or len(newpaths)!=len(set(newpaths)):raise ValueError('Duplicate ZIP entries')
        if changed!={'game.js','index.html'}:raise ValueError(f'Unexpected compiled payload {sorted(changed)}')
        manifest=json.loads(original.read('world-master/manifest.json'))
        if manifest.get('public_redistribution_allowed') is not False:raise ValueError('Expected PRIVATE license policy')
        if manifest.get('schema')!='neurocity.local-worldmaster-tiles.v1':raise ValueError('Unexpected baseline world')
        oldjs=original.read('game.js');newjs=patch.read('game.js')
        if len(newjs)<200_000 or b'world-master' not in newjs or b'world-master' not in oldjs:raise ValueError('Runtime lacks expected G19 loader')
        all_glb={p for p in basepaths if p.endswith('.glb')}
        audited=[];missing=[]
        for tile in manifest['tiles']:
          for asset in tile['assets']:
            f='world-master/'+asset['path']
            if f not in all_glb:missing.append(f);continue
            actual=original.read(f)
            if SHA(actual)!=asset['sha256'] or len(actual)!=asset['bytes']:
              raise ValueError('Private asset hash/size does not match manifest: '+f)
            audited.append(f)
        if missing:raise ValueError('Missing referenced GLBs: '+repr(missing))
        for f in ['assets/alicante.glb','world-master/manifest_V50_before_surgical_candidate.json']:
          if f not in basepaths:raise ValueError('Lost preserved asset '+f)
        checks=[('JS: loading source world-master',b'world-master' in newjs),
                ('JS: brain NPL',b'NPL' in newjs or b'npl' in newjs),
                ('JS: coastline graphics',b'WATER' in newjs or b'water' in newjs)]
        if not all(k for _,k in checks):raise ValueError('Compiled module misses minimum features')
        safe_launchers={}
        # Legacy start scripts without --bind expose the PRIVATE GLBs to the LAN.
        # Repair only the two unsafe entry points; keep bytes of all other assets.
        for name in ['INICIAR_WINDOWS.bat','INICIAR_LINUX_MAC.sh']:
            if name in basepaths:
                source=original.read(name)
                if b'--bind 127.0.0.1' not in source:
                    replacement=source.replace(b'python3 -m http.server 8766',b'python3 -m http.server 8766 --bind 127.0.0.1')
                    replacement=replacement.replace(b'py -3 -m http.server 8766',b'py -3 -m http.server 8766 --bind 127.0.0.1')
                    if replacement==source or b'--bind 127.0.0.1' not in replacement:
                        raise ValueError('Cannot safely confine private launcher '+name)
                    safe_launchers[name]=replacement
        preserved_except=changed|set(safe_launchers)
        before={n:SHA(original.read(n)) for n in basepaths if n not in preserved_except}
        audit={'schema':'neurocity.private-world-runtime-assembly.v1','status':'ASSEMBLED_NOT_WEBGL_APPROVED',
         'date':'2026-10-20','source_archive_sha256':SHA(base.read_bytes()),'compiled_artifact_sha256':SHA(compiled.read_bytes()),
         'compiled_bundle_sha256':SHA(newjs),'compiled_html_sha256':SHA(patch.read('index.html')),
         'compiled_ci_run':compiled_ci_run,
         'base_private_entry_count':len(basepaths),'original_glb_count':len(all_glb),'manifest_model_records_verified':len(audited),
         'original_bytes_preserved_except_allowlisted_runtime_and_launchers':True,
         'security_fixed_local_only_launchers':sorted(safe_launchers),
         'original_unsafe_launcher_sha256':{n:SHA(original.read(n)) for n in sorted(safe_launchers)},
         'source_manifest_sha256':SHA(original.read('world-master/manifest.json')),
         'original_3d_assets_sha256':{n:before[n] for n in sorted(before) if n.endswith('.glb')},
         'runtime_compatibility_verified_in_browser':False, 'visual_match_to_real_Alicante_approved':False,
         'topographic_vertical_datum_verified':False,'latency_FPS_GPU_measured':False,
         'models_private_do_not_upload_to_public_git':True,
         'merges_remain_pending_review':True,'checks_passed':[x for x,v in checks if v]}
        tmp=dest.with_suffix('.tmp');tmp.parent.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(tmp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as out:
            for info in original.infolist():
                payload=patch.read(info.filename) if info.filename in changed else safe_launchers.get(info.filename,original.read(info.filename))
                out.writestr(info,payload)
            stable=zipfile.ZipInfo(manifest_name,date_time=(2026,10,20,0,0,0))
            stable.compress_type=zipfile.ZIP_DEFLATED
            stable.external_attr=0o644<<16
            out.writestr(stable,json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
        os.replace(tmp,dest)
    with zipfile.ZipFile(dest) as joined,zipfile.ZipFile(base) as original:
        if joined.testzip() is not None:raise ValueError('Output CRC invalid')
        if SHA(joined.read('game.js'))!=SHA(newjs):raise ValueError('Compiled runtime overwritten')
        for p in basepaths:
            if p not in preserved_except and SHA(joined.read(p))!=SHA(original.read(p)):
                raise ValueError('Preservation fail '+p)
            if p in safe_launchers and joined.read(p)!=safe_launchers[p]:
                raise ValueError('Private local-only launcher regressed: '+p)
        if len(joined.namelist())!=len(basepaths)+1:raise ValueError('Unexpected output entries')
    return {'zip':str(dest),'bytes':dest.stat().st_size,'sha256':SHA(dest.read_bytes()),'audit':audit}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--base',required=True);p.add_argument('--compiled',required=True);p.add_argument('--output',required=True);p.add_argument('--ci-run')
    opts=p.parse_args();d=assemble(opts.base,opts.compiled,opts.output,compiled_ci_run=opts.ci_run)
    print(json.dumps({k:v for k,v in d.items() if k!='audit'},indent=2))
    print('Original assets verified:',d['audit']['manifest_model_records_verified'],'of',d['audit']['original_glb_count'])
