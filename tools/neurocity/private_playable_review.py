"""Private, temporary browser QA of the ACTUAL Catastro+OSM-derived 3D GLB.

This is NOT a website publication. The browser binds to localhost only.
Only aggregate scene metrics and public source hashes leave /tmp; no source
GML or real-property-specific GLB is uploaded to CI artifacts.
"""
import hashlib
import json
import os
import shutil
import subprocess
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def run_playable_review(work,qa,report):
    root=Path(__file__).resolve().parents[2]
    viewer=root/'demos/npl-world/visual_viewer'
    built=viewer/'dist/game.js'
    city=Path(work)/'output/Alicante_REAL_OSM_PNOA.glb'
    if not built.is_file() or not city.is_file():
        raise ValueError('Expected bundled public viewer and source-verified GLB')
    preview=Path(work)/'private-browser-preview'
    assets=preview/'assets';assets.mkdir(parents=True)
    shutil.copyfile(built,preview/'game.js')
    shutil.copyfile(city,assets/'alicante.glb')
    index=(viewer/'index.html').read_text()
    needle='<script src="./game.js"></script>'
    if index.count(needle)!=1:
        raise ValueError('Cannot safely select public-only viewer startup')
    index=index.replace(needle,'<script>window.NPL_PUBLIC_REVIEW=true;</script>'+needle)
    (preview/'index.html').write_text(index)
    shutil.copyfile(viewer/'public_context/ine_eaes2024_3_territories.json',
        assets/'conflictometro_public_verified.json')
    for name in ['observatory.html','observatory.css','observatory.mjs','public_layers.mjs']:
        shutil.copyfile(viewer/name,preview/name)

    public_qa={
      'real_osm_buildings':qa['real_osm_buildings'],
      'matched_osm_buildings':qa['cadastre_original_osm_footprints_replaced'],
      'matched_official_parts':qa['cadastre_building_parts_geometry'],
      'native_official_parts':qa['cadastre_native_official_parts_added'],
      'verified_source_tiles':qa['cadastre_verified_source_tiles'],
      'coverage_complete':qa['cadastre_coverage_complete'],
      'height_is_surveyed':False,
      'private_avatar_included':False,
      'model_glb_sha256':hashlib.sha256(city.read_bytes()).hexdigest()
    }
    assert public_qa['matched_official_parts']==report['matched_official_parts']
    assert public_qa['native_official_parts']==report['native_official_parts_eligible']
    (preview/'QA_CADASTRE_PUBLIC.json').write_text(json.dumps(public_qa))

    class QuietHandler(SimpleHTTPRequestHandler):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,directory=str(preview),**kwargs)
        def log_message(self,*args):pass

    # Only local loopback. Use a random OS-selected ephemeral port to avoid
    # collisions with concurrent CI jobs; nothing is published externally.
    server=ThreadingHTTPServer(('127.0.0.1',0),QuietHandler)
    port=server.server_address[1]
    worker=threading.Thread(target=server.serve_forever,daemon=True)
    worker.start()
    try:
        js=viewer/'tests/browser_cadastre_real.mjs'
        env={**os.environ,'NEUROCITY_PRIVATE_REVIEW_URL':f'http://127.0.0.1:{port}/',
             'NEUROCITY_PRIVATE_PREVIEW_DIR':str(preview)}
        p=subprocess.run(['node',str(js)],cwd=root,env=env,capture_output=True,
                         text=True,timeout=110,check=False)
        if p.returncode:
            raise RuntimeError('Chromium private review failed: '+p.stderr[-1800:])
        browser_qa=json.loads((preview/'QA_PRIVATE_BROWSER.json').read_text())
        if browser_qa.get('status')!='PASS':
            raise RuntimeError('Chromium private review did not validate scene')
        report['private_webgl_qa']='PASS'
        report['private_webgl_meshes']=browser_qa['model']['meshCount']
        report['private_webgl_triangles']=browser_qa['model']['triangleCount']
        report['private_webgl_collision_segments']=browser_qa['collision']['wallSegments']
        report['private_webgl_collision_cells']=browser_qa['collision']['spatialCells']
        report['private_webgl_official_building_parts']=(
            public_qa['matched_official_parts']+public_qa['native_official_parts'])
        report['private_webgl_npl_mission']=browser_qa['nplMissionVerified']
        report['private_webgl_browser']='Chromium_SwiftShader_not_hardware_fps'
        report['private_webgl_screenshot_saved_to_artifact']=False
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=3)
