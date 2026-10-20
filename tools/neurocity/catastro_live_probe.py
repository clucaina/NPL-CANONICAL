#!/usr/bin/env python3
"""One bounded, anonymous public-source probe for Alicante Catastro BU/OSM.
Never stores a GML, cadastral reference, address or individual model in artifacts.
No credentials, no Google Drive, no patient or private avatar data.
"""
import json
import math
import tempfile
from pathlib import Path
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
    with urlopen(req,timeout=32) as rsp:
        dest=urlsplit(rsp.url)
        if dest.scheme!='https' or dest.hostname!=host or rsp.status!=200:
            raise RuntimeError('source_redirect_or_http_error')
        data=rsp.read(cap+1)
        if len(data)>cap or len(data)<80:
            raise RuntimeError('source_invalid_byte_count')
    Path(path).write_bytes(data)
    return len(data)

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
        # The original private/public source files remain in /tmp and are
        # deleted automatically, never committed or uploaded.
    return result

if __name__=='__main__':
    report=probe()
    d=Path('/tmp/neurocity-cadastre-public-evidence')
    d.mkdir(exist_ok=True,parents=True)
    (d/'OFFICIAL_WFS_ACCESS_PROBE.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
    print(json.dumps(report,ensure_ascii=False,indent=2))
