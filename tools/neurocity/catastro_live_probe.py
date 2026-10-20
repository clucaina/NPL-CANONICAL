#!/usr/bin/env python3
"""One bounded, anonymous public-source probe for Alicante Catastro BU/OSM.
Never stores a GML, cadastral reference, address or individual model in artifacts.
No credentials, no Google Drive, no patient or private avatar data.
"""
import json
import math
import hashlib
import shutil
import subprocess
import tempfile
from pathlib import Path
from time import sleep
from http.client import RemoteDisconnected
from urllib.error import URLError
from urllib.parse import urlencode,urlsplit
from urllib.request import Request,urlopen
from catastro_parts import compile_overlay,validate_official_url

BBOX_UTM=(719820,4246800,720100,4247110)
BBOX_OSM=(-.4862,38.3418,-.4795,38.347)
CENTER=(-.48322,38.34402)
R=6378137.
WFS='https://ovc.catastro.meh.es/INSPIRE/wfsBU.aspx?'+urlencode({
 'service':'wfs','version':'2.0.0','request':'getfeature','typenames':'BU.BUILDINGPART',
 'bbox':','.join(map(str,BBOX_UTM)),'srsname':'EPSG::25830'})
OSM='https://api.openstreetmap.org/api/0.6/map?'+urlencode({'bbox':','.join(map(str,BBOX_OSM))})
USER_AGENT='NeuroCity-OpenData-Source-Audit/1.0 (+https://github.com/clucaina/NPL-CANONICAL)'

def receive(url,cap,path,host):
    req=Request(url,headers={'User-Agent':USER_AGENT,'Accept':'application/xml,text/xml;q=0.8,*/*;q=0.1'})
    # A refused TCP connection or early remote disconnect is transient.
    # At most TWO total attempts, fixed 4 s pause. Never retry invalid
    # source URLs, unexpected hosts, oversized payloads or WFS exceptions.
    for attempt in range(2):
        try:
            with urlopen(req,timeout=32) as rsp:
                dest=urlsplit(rsp.url)
                if dest.scheme!='https' or dest.hostname!=host or rsp.status!=200:
                    raise RuntimeError('source_redirect_or_http_error')
                data=rsp.read(cap+1)
                if len(data)>cap or len(data)<80:
                    raise RuntimeError('source_invalid_byte_count')
            Path(path).write_bytes(data)
            return len(data)
        except (RemoteDisconnected,ConnectionResetError,TimeoutError,URLError):
            if attempt==1:raise
            sleep(4)

def probe():
    validate_official_url(WFS)
    result={'schema':'neurocity.public-cadastre-probe.v1',
     'source':'DG_CATASTRO_INSPIRE_BU_BUILDINGPART',
     'region':'Alicante Explanada bounded public data only',
     'wfs_bbox_utm':BBOX_UTM,'osm_bbox_degrees':BBOX_OSM,
     'real_geometries_verified':False,'actual_city_models_generated':0,
     'private_or_property_identifiers_exported':False,
     'probe_status':'BLOCKED_NOT_TESTED'}
    with tempfile.TemporaryDirectory(prefix='neurocity_public_cadastre_') as directory:
        p=Path(directory)
        try:
            result['osm_bytes']=receive(OSM,8*1024*1024,p/'city.osm','api.openstreetmap.org')
        except Exception as e:
            result['probe_status']='BLOCKED_OSM_SOURCE'
            result['blocker_class']=type(e).__name__
            return result
        try:
            result['wfs_bytes']=receive(WFS,12*1024*1024,p/'part.gml','ovc.catastro.meh.es')
        except Exception as e:
            result['probe_status']='BLOCKED_CATASTRO_WFS'
            result['blocker_class']=type(e).__name__
            return result
        origin=[R*math.radians(CENTER[0]),R*math.log(math.tan(math.pi/4+math.radians(CENTER[1])/2))]
        (p/'manifest.json').write_text(json.dumps({'center_mercator':origin}))
        try:
            review=compile_overlay(gml=p/'part.gml',osm=p/'city.osm',manifest=p/'manifest.json',official_url=WFS)
        except Exception as e:
            result['probe_status']='BLOCKED_WFS_GML_OR_GEO_MATCH'
            result['blocker_class']=type(e).__name__
            return result
        result.update({
          'probe_status':'OFFICIAL_GML_PARSED',
          'real_geometries_verified':review['matched_osm_count']>0,
          'official_source_sha256':review['source_sha256'],
          'returned_features':review['returned_features'],
          'candidate_parts':review['candidate_parts'],
          'matched_osm_count':review['matched_osm_count'],
          'matched_bu_part_count':review['matched_bu_part_count'],
          'total_osm_buildings':review['total_osm_buildings'],
          'height_is_surveyed':False,
          'height_method':review['height_method'],
          'skipped':review['skipped'],
          'matching':review['matching']})
        # Full real-world Blender 3D export, but ONLY into a temporary folder.
        # Never publish the government-provided GML or this unreleased GLB.
        if review['matched_osm_count']>0:
            work=p/'scene'
            scene_input=work/'input'
            scene_input.mkdir(parents=True)
            (work/'output').mkdir()
            shutil.copyfile(p/'city.osm',scene_input/'alicante.osm')
            shutil.copyfile(p/'part.gml',scene_input/'catastro_building_parts.gml')
            (scene_input/'catastro_building_parts.json').write_text(json.dumps(review))
            west,south,east,north=BBOX_OSM
            def web_xy(lon,lat):
                return R*math.radians(lon),R*math.log(math.tan(math.pi/4+math.radians(lat)/2))
            minx,miny=web_xy(west,south);maxx,maxy=web_xy(east,north)
            (scene_input/'source_manifest.json').write_text(json.dumps({
                'center_mercator':origin,'bbox_local_m':[
                    minx-origin[0],miny-origin[1],maxx-origin[0],maxy-origin[1]
                ],'real_orthophoto':False
            }))
            script=Path(__file__).resolve().parents[2]/'demos/npl-world/open_city_pipeline/build_blender.py'
            try:
                subprocess.run(['blender','-b','--factory-startup','-t','2',
                    '--python-exit-code','1','-P',str(script)],
                    cwd=work,timeout=180,check=True,capture_output=True)
                qa=json.loads((work/'output/QA_source_report.json').read_text())
                glb=work/'output/Alicante_REAL_OSM_PNOA.glb'
                if (qa.get('cadastre_original_osm_footprints_replaced')!=review['matched_osm_count']
                    or qa.get('cadastre_building_parts_geometry')!=review['matched_bu_part_count']
                    or not glb.exists() or glb.stat().st_size<1000):
                    raise ValueError('Blender real-world source-volume contract failed')
                result.update({
                    'actual_city_models_generated':1,
                    'real_official_buildings_replaced_in_temporary_3d':qa['cadastre_original_osm_footprints_replaced'],
                    'real_official_building_parts_rendered':qa['cadastre_building_parts_geometry'],
                    'temporary_unreleased_glb_sha256':hashlib.sha256(glb.read_bytes()).hexdigest(),
                    'temporary_3d_export_size_bytes':glb.stat().st_size,
                    'original_source_redistributed':False
                })
            except Exception as exc:
                result['probe_status']='BLOCKED_ACTUAL_3D_EXPORT'
                result['export_blocker_class']=type(exc).__name__
        # The original public source files remain in /tmp and are
        # deleted automatically, never committed or uploaded.
    return result

if __name__=='__main__':
    report=probe()
    d=Path('/tmp/neurocity-cadastre-public-evidence')
    d.mkdir(exist_ok=True,parents=True)
    (d/'OFFICIAL_WFS_ACCESS_PROBE.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
    print(json.dumps(report,ensure_ascii=False,indent=2))
