#!/usr/bin/env python3
"""Build LOCAL user-owned NeuroCity v6 from the pre-existing private checkpoint
and independently tested PUBLIC code/city artifacts.

Important real regression: older v5 launchers used ?worldmaster=1, but v5
index.html DID NOT define NPL_PUBLIC_REVIEW; the G19 loader returned early,
leaving the user in the simplified city despite 76 original GLBs in the ZIP.

This builder fixes that mismatch and verifies that source-private bytes and
NPL/Conflictómetro originals are preserved. Do not commit generated output.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED

FLAG='<script>window.NPL_PUBLIC_REVIEW=true;</script>'
SCRIPT='<script src="./game.js"></script>'
INDEX='index.html'
COUNT_MIN=70
MAX_SOURCE=110_000_000

def assert_private_preserved(base:ZipFile):
    entries=set(base.namelist())
    if 'world-master/manifest.json' not in entries or 'assets/conflictometro_public_verified.json' not in entries:
        raise ValueError('Existing private pack or original reviewed NPL/Conflictometro missing')
    manifest=json.loads(base.read('world-master/manifest.json'))
    if manifest.get('public_redistribution_allowed') is not False or manifest.get('crs')!='EPSG:25830':
        raise ValueError('Missing ETRS89 source contract or private reuse notice')
    originals=manifest.get('asset_hashes')
    if not isinstance(originals,dict) or len(originals)<COUNT_MIN:
        raise ValueError('Original G19/V50 source model inventory too small')
    for relative,record in originals.items():
        if not isinstance(relative,str) or '..' in Path(relative).parts or not relative.startswith('assets/'):
            raise ValueError('Unsafe original relative asset path')
        path='world-master/'+relative
        if path not in entries:raise ValueError('Missing original GLB in local pack: '+path)
        content=base.read(path)
        if len(content)!=record.get('bytes') or hashlib.sha256(content).hexdigest()!=record.get('sha256'):
            raise ValueError('Original G19 model checksum changed: '+path)
    physics=[n for n in entries if n.startswith('world-master/geo/data/physical_') and n.endswith('.json')]
    if len(physics)!=12:raise ValueError('Physical G13 grid source continuity broken')
    return manifest,physics

def make_public_entrypoint(data:bytes)->bytes:
    html=data.decode('utf-8')
    if SCRIPT not in html:raise ValueError('Runtime HTML missing game.js launch point')
    html=html.replace(FLAG,'')
    html=html.replace(SCRIPT,FLAG+SCRIPT)
    if html.count(FLAG)!=1 or not html.index(FLAG)<html.index(SCRIPT):
        raise ValueError('G19 public-preview opt-in flag was not initialized before JavaScript')
    return html.encode('utf-8')

def build_private_local_checkpoint(base_zip:Path,runtime_zip:Path,city_zip:Path,output:Path):
    output.parent.mkdir(parents=True,exist_ok=True)
    overrides={}
    with ZipFile(base_zip) as original, ZipFile(runtime_zip) as runtime, ZipFile(city_zip) as city:
        manifest,physical=assert_private_preserved(original)
        binary=city.read('output/Alicante_REAL_OSM_PNOA.glb')
        if len(binary)<50000 or len(binary)>MAX_SOURCE or binary[:4]!=b'glTF':
            raise ValueError('Source city GLB corrupt or implausible')
        meta=json.loads(city.read('output/QA_source_report.json'))
        coast=meta.get('coastal_and_vegetation_visual_objects',{})
        if coast.get('mapped_tree_nodes',0)<1 or coast.get('rounded_tree_canopy_lobes')!=3*coast.get('mapped_tree_nodes',0):
            raise ValueError('Regressed back to Roblox pyramid trees')
        if coast.get('shrub_clusters_within_osm_polygon',0)<1:
            raise ValueError('New OSM shrub map layer missing')
        if meta.get('private_avatar_included') is not False or meta.get('facades_photogrammetric') is not False:
            raise ValueError('Official source incorrectly claims private user data or photogrammetry')
        app=runtime.read('game.js')
        if len(app)<50000 or b'NPL_BRAIN3D' not in app or b'brainActivityMeasured' not in app:
            raise ValueError('Compiled 3D brain missing in viewer bundle')
        html=make_public_entrypoint(runtime.read('index.html'))
        if b'id="nplBrainCanvas"' not in html or b'id="nplMethods"' not in html:
            raise ValueError('3D right-side neural panel missing')
        overrides={
          INDEX:html,'game.js':app,'assets/alicante.glb':binary,
          'QA_SOURCE.json':city.read('output/QA_independent_provenance.json'),
          'QA_OSM_VEGETATION_v6.json':json.dumps(meta,ensure_ascii=False,indent=2).encode()
        }
        records={}
        for item in original.infolist():
            if item.is_dir():continue
            name=item.filename
            if name in records:raise ValueError('Duplicate source ZIP path')
            records[name]=original.read(name)
        records.update(overrides)
        qa={
          'schema':'neurocity.recovered-G19-live-NPL3D-v6.v1',
          'local_owned_originals_preserved':True,
          'source_archive_sha256':manifest.get('source_archive_sha256'),
          'existing_v5_sha256':hashlib.sha256(base_zip.read_bytes()).hexdigest(),
          'existing_reviewed_conflictometro_sha256':hashlib.sha256(original.read('assets/conflictometro_public_verified.json')).hexdigest(),
          'private_source_GLBs_verified':len(manifest['asset_hashes']),
          'G13_signed_2m_grid_count':len(physical),
          'launcher_includes_worldmaster_query':b'?worldmaster=1' in original.read('ABRIR_NEUROCITY_MUNDO_RECUPERADO_WINDOWS.bat'),
          'actual_loader_flag_before_game_js':True,
          'new_source_city_sha256':hashlib.sha256(binary).hexdigest(),
          'new_runtime_sha256':hashlib.sha256(app).hexdigest(),
          'source_greenery':coast,
          'real_public_shops_invented':False,
          'clinical_data_loaded':False,
          'independent_3d_browser_validation_with_all_76_private_glbs':False,
          'public_repo_owns_original_archive':False,
          'realistic_GTA_quality_certified':False
        }
        if not qa['launcher_includes_worldmaster_query']:raise ValueError('Original G19 launcher does not request worldmaster')
        records['QA_NEUROCITY_NPL3D_LOCAL_v6.json']=json.dumps(qa,ensure_ascii=False,indent=2).encode()
        records['LEER_NEUROCITY_NPL3D_V6.txt']=(
          'NEUROCITY NPL 3D v6 LOCAL, EXTRAER ZIP COMPLETO.\n'
          'Abrir ABRIR_NEUROCITY_MUNDO_RECUPERADO_WINDOWS.bat en Windows.\n'
          'Corregido el bloqueo v5: ?worldmaster=1 y NPL_PUBLIC_REVIEW ahora se activan JUNTOS.\n'
          'Reaprovecha 76 modelos G19/V50 originales y 12 cuadriculas fisicas G13.\n'
          'El panel derecho ahora es una escena 3D funcional basada en acciones locales del juego.\n'
          'Escala visual y geometria aun interpretativas, no MRI o medicion de cognicion real.\n'
          'Arboles de posicion OSM con copas redondeadas artisticas y arbustos sobre poligonos OSM.\n'
          'No publicar este ZIP en repositorios abiertos; verificar licencias por archivo.\n'
          'La carga conjunta de 76 GLBs en Windows sigue por validar en hardware real.\n'
        ).encode()
        with ZipFile(output,'w',compression=ZIP_DEFLATED,compresslevel=6) as dest:
            for name,data in sorted(records.items()):
                dest.writestr(name,data)
    with ZipFile(output) as built:
        if built.testzip() is not None:raise ValueError('Output CRC failed')
        assert_private_preserved(built)
        assert built.read('assets/conflictometro_public_verified.json')==records['assets/conflictometro_public_verified.json']
        if built.read(INDEX).count(FLAG.encode())!=1:raise ValueError('Preview flag not unique')
        if built.read('assets/alicante.glb')!=overrides['assets/alicante.glb']:raise ValueError('New OSM city was not installed')
    return qa

if __name__=='__main__':
 p=argparse.ArgumentParser()
 p.add_argument('--base-zip',type=Path,required=True)
 p.add_argument('--runtime-zip',type=Path,required=True)
 p.add_argument('--city-zip',type=Path,required=True)
 p.add_argument('--output',type=Path,required=True)
 a=p.parse_args()
 result=build_private_local_checkpoint(a.base_zip,a.runtime_zip,a.city_zip,a.output)
 print(json.dumps({
  'public_preview_enabled_for_g19':result['actual_loader_flag_before_game_js'],
  'source_G19_original_models':result['private_source_GLBs_verified'],
  'source_G13_grids':result['G13_signed_2m_grid_count'],
  'new_OSM_trees':result['source_greenery'].get('mapped_tree_nodes'),
  'new_bush_clusters':result['source_greenery'].get('shrub_clusters_within_osm_polygon'),
  'browser_all_originals_certified':False
 },indent=2))
