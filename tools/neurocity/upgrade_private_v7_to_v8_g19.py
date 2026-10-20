"""Owner-only pinned NeuroCity V7 -> V8 G19 continuous wall-sweep upgrade.

Use ONLY the original owner V7 archive and source-only GitHub Action artifact.
Do not publish, upload, or deploy the produced private file.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import pathlib
import re
import zipfile

from private_bundle_assembly import assemble, SHA

V7='8abd0c0ea2601d913a4c52618101a6712af85228133b61dd34759f0749836403'
CODE_ZIP='2f746acbf4d2ef1b1342b1fe5722c582d899f452ae90f27ea7fe6257cd06bc8a'
CODE_JS='722b6b0bde72cfc347a5b101c5d6fac86db25f647b6ca3bedd7ec823f79b905d'
V7_AUDIT='INTEGRACION_WEBGL_V7_REVISABLE.json'
V8_AUDIT='INTEGRACION_WEBGL_V8_G19_SWEEP_REVISABLE.json'
SOURCE_RUN='39430608426'

def validate_inputs(base,compiled,expected_v7=V7,expected_code=CODE_ZIP,expected_js=CODE_JS):
    base=pathlib.Path(base);compiled=pathlib.Path(compiled)
    if SHA(base.read_bytes())!=expected_v7:raise ValueError('Wrong owner V7 source SHA')
    if SHA(compiled.read_bytes())!=expected_code:raise ValueError('Wrong verified G19 source-artifact SHA')
    with zipfile.ZipFile(base) as old,zipfile.ZipFile(compiled) as new:
        names=old.namelist()
        if names.count(V7_AUDIT)!=1 or V8_AUDIT in names:
            raise ValueError('V7 checkpoint missing or V8 already exists')
        prior=json.loads(old.read(V7_AUDIT))
        if prior.get('status')!='ASSEMBLED_NOT_WEBGL_APPROVED':
            raise ValueError('Invalid predecessor QA contract')
        code=new.read('game.js')
        if SHA(code)!=expected_js or len(code)<200000:
            raise ValueError('Compiled source mismatch')
        if not all(marker in code.lower() for marker in (b'world-master',b'collision',b'sweep',b'npl',b'water')):
            raise ValueError('G19 collision sweep or canonical game subsystem missing')
        if set(new.namelist())!={'game.js','index.html'}:
            raise ValueError('Source-only artifact polluted with models')
        for name in [n for n in names if n.lower().endswith(('.bat','.sh'))]:
            raw=old.read(name)
            if b'http.server ' in raw and b'--bind 127.0.0.1' not in raw:
                raise ValueError('Private launcher is not bound to loopback')
    return {'v7_sha256':expected_v7,'source_sha256':expected_code,'js_sha256':expected_js}

def upgrade(base,compiled,output):
    validate_inputs(base,compiled)
    result=assemble(base,compiled,output,manifest_name=V8_AUDIT,compiled_ci_run=SOURCE_RUN)
    # This wrapper shares the original v7 assembler's report format; its ZIP
    # is separately reproducible but does not claim the exact local V8 audit SHA.
    with zipfile.ZipFile(output) as out:
        if out.namelist().count(V7_AUDIT)!=1 or out.namelist().count(V8_AUDIT)!=1:
            raise ValueError('Version history lost or duplicated')
        with zipfile.ZipFile(base) as predecessor:
            preserved = out.read(V7_AUDIT)==predecessor.read(V7_AUDIT)
        if not preserved:
            raise ValueError('V7 audit changed during upgrade')
        if len([n for n in out.namelist() if n.endswith('.glb')])!=86:
            raise ValueError('G19 GLB asset coverage changed')
        report=json.loads(out.read(V8_AUDIT))
        if report['status']!='ASSEMBLED_NOT_WEBGL_APPROVED':
            raise ValueError('Unauthorized WEBGL approval')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--v7',required=True);p.add_argument('--source',required=True);p.add_argument('--output',required=True)
    q=p.parse_args()
    x=upgrade(q.v7,q.source,q.output)
    print(json.dumps({k:v for k,v in x.items() if k!='audit'},ensure_ascii=False,indent=2))
