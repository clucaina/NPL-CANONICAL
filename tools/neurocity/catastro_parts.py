#!/usr/bin/env python3
"""DG Catastro INSPIRE BU BuildingPart -> conservative, public-only OSM overlay.

Offline by design: only processes an operator-provided GML snapshot. Never
exports identifiers, addresses, parcels, or any personal information.
A floor count multiplied by 3m is an ESTIMATE, not LiDAR measured height.
"""
import argparse
import hashlib
import json
import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from pyproj import Transformer
from shapely.geometry import Polygon
from shapely.ops import unary_union
from shapely.strtree import STRtree

MAX_GML_BYTES=16*1024*1024
MAX_PARTS=5000
LICENSE='https://www.catastro.hacienda.gob.es/webinspire/documentos/Licencia.pdf'
SOURCE_DOC='https://www.catastro.hacienda.gob.es/webinspire/documentos/inspire-bu-wfs.pdf'
R=6378137.

def local_name(tag):
    return tag.rsplit('}',1)[-1]

def validate_official_url(url):
    u=urlsplit(url)
    if (u.scheme!='https' or u.netloc.lower()!='ovc.catastro.meh.es'
        or u.path.lower()!='/inspire/wfsbu.aspx' or u.username or u.password):
        raise ValueError('Only official Catastro BU WFS over HTTPS')
    q={k.lower():v[0].lower() for k,v in parse_qs(u.query).items() if len(v)==1}
    if (q.get('request')!='getfeature' or q.get('typenames') not in ('bu.buildingpart','bu:buildingpart')
        or q.get('srsname','').replace(':','')!='epsg25830'):
        raise ValueError('Expected bounded BU.BUILDINGPART EPSG::25830 GetFeature')
    bb=q.get('bbox','').split(',')
    if len(bb)!=4:raise ValueError('WFS BBOX missing')
    try:x1,y1,x2,y2=map(float,bb)
    except ValueError as exc:raise ValueError('Bad BBOX') from exc
    if (not all(map(math.isfinite,(x1,y1,x2,y2))) or
        not (719000<x1<x2<721000 and 4246000<y1<y2<4248000) or
        (x2-x1)*(y2-y1)>4_000_000):
        raise ValueError('BBOX outside audited Alicante or WFS cap')
    return x1,y1,x2,y2

def load_xml(path):
    p=Path(path)
    if not (10<=p.stat().st_size<=MAX_GML_BYTES):raise ValueError('Invalid GML byte cap')
    data=p.read_bytes()
    if b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper():
        raise ValueError('DTD/entity prohibited')
    if b'ExceptionReport' in data or b'exceptionReport' in data:
        raise ValueError('WFS exception is not source data')
    root=ET.fromstring(data)
    if local_name(root.tag)!='FeatureCollection':raise ValueError('Not a WFS FeatureCollection')
    return root,hashlib.sha256(data).hexdigest()

def read_parts(root,bbox,origin):
    tr=Transformer.from_crs('EPSG:25830','EPSG:3857',always_xy=True)
    x1,y1,x2,y2=bbox;parts=[]
    skipped={'unknown_floors':0,'invalid_geometry':0,'unsupported_crs':0,'outside_area':0,'holes':0}
    features=[e for e in root.iter() if local_name(e.tag)=='BuildingPart']
    if len(features)>MAX_PARTS:raise ValueError('WFS returned >5000 parts')
    for feature in features:
        floors=[e.text for e in feature.iter() if local_name(e.tag)=='numberOfFloorsAboveGround']
        if len(floors)!=1 or not floors[0] or not re.fullmatch(r'\d{1,2}',floors[0].strip()) or not 1<=int(floors[0])<=30:
            skipped['unknown_floors']+=1;continue
        polygons=[e for e in feature.iter() if local_name(e.tag) in ('Polygon','PolygonPatch')]
        if len(polygons)!=1:skipped['invalid_geometry']+=1;continue
        poly=polygons[0]
        crs=next((e.attrib['srsName'] for e in [poly]+list(feature.iter()) if 'srsName' in e.attrib),'')
        if '25830' not in crs:skipped['unsupported_crs']+=1;continue
        if any(local_name(e.tag)=='interior' for e in poly.iter()):
            skipped['holes']+=1;continue
        pos=[e for e in poly.iter() if local_name(e.tag)=='posList']
        if len(pos)!=1 or not pos[0].text:skipped['invalid_geometry']+=1;continue
        try:
            nums=list(map(float,pos[0].text.split()))
            dim=int(pos[0].attrib.get('srsDimension','2'))
            coords=list(zip(nums[0::2],nums[1::2])) if dim==2 and len(nums)%2==0 else []
        except ValueError:coords=[];nums=[]
        if (len(nums)>1600 or len(coords)<4 or coords[0]!=coords[-1]
            or not all(math.isfinite(t) for xy in coords for t in xy)):
            skipped['invalid_geometry']+=1;continue
        if not all(x1-40<=x<=x2+40 and y1-40<=y<=y2+40 for x,y in coords):
            skipped['outside_area']+=1;continue
        ring=[(mx-origin[0],my-origin[1]) for mx,my in (tr.transform(x,y) for x,y in coords)]
        geom=Polygon(ring)
        if not geom.is_valid or not 4<=geom.area<=50000 or len(geom.interiors):
            skipped['invalid_geometry']+=1;continue
        parts.append({'poly':geom,'floors':int(floors[0])})
    return parts,skipped,len(features)

def read_osm(osm,origin):
    root=ET.parse(osm).getroot()
    def xy(lon,lat):
        lon=float(lon);lat=float(lat)
        return R*math.radians(lon)-origin[0],R*math.log(math.tan(math.pi/4+math.radians(lat)/2))-origin[1]
    nodes={n.attrib['id']:xy(n.attrib['lon'],n.attrib['lat']) for n in root.findall('node')}
    result=[]
    for way in root.findall('way'):
        tags={t.attrib.get('k'):t.attrib.get('v') for t in way.findall('tag')}
        if tags.get('building') in (None,'no'):continue
        ids=[n.attrib['ref'] for n in way.findall('nd')]
        if len(ids)<4 or ids[0]!=ids[-1] or any(i not in nodes for i in ids):continue
        geom=Polygon([nodes[i] for i in ids])
        if geom.is_valid and 4<=geom.area<=80000 and not geom.interiors:
            result.append((way.attrib['id'],geom))
    return result

def safe_matches(parts,buildings):
    if not parts:return [],{'ambiguous':0,'unmatched_osm':len(buildings)}
    geometries=[p['poly'] for p in parts]
    tree=STRtree(geometries)
    matched=[];ambiguous=0
    for way_id,osm in buildings:
        ids=[int(i) for i in tree.query(osm) if geometries[int(i)].intersection(osm).area/geometries[int(i)].area>=.98]
        if not ids:continue
        shapes=[geometries[i] for i in ids]
        combined=unary_union(shapes)
        if (osm.intersection(combined).area/osm.area<.90 or
            (sum(g.area for g in shapes)-combined.area)/combined.area>.025 or
            combined.difference(osm).area/combined.area>.03):
            ambiguous+=1;continue
        sections=[]
        for i in ids:
            ring=list(geometries[i].exterior.coords)[:-1]
            sections.append({'floors':parts[i]['floors'],'height_estimated_m':parts[i]['floors']*3.,
                'ring':[[round(x,4),round(y,4)] for x,y in ring]})
        matched.append({'osm_way_id':way_id,'sections':sections})
    return matched,{'ambiguous':ambiguous,'unmatched_osm':len(buildings)-len(matched)}

def compile_overlay(*,gml,osm,manifest,official_url):
    bbox=validate_official_url(official_url)
    m=json.loads(Path(manifest).read_text())
    origin=m.get('center_mercator')
    if not isinstance(origin,list) or len(origin)!=2 or not all(isinstance(x,(int,float)) and math.isfinite(x) for x in origin):
        raise ValueError('Expected original OSM geographic origin')
    root,digest=load_xml(gml)
    parts,skipped,returned=read_parts(root,bbox,origin)
    buildings=read_osm(osm,origin)
    matched,stats=safe_matches(parts,buildings)
    result={
      'schema':'neurocity.catastro-building-parts.v1','source':'DG_CATASTRO_INSPIRE_BU_BUILDINGPART',
      'source_sha256':digest,'source_url':official_url,'license_url':LICENSE,
      'source_documentation':SOURCE_DOC,'crs':'EPSG:3857_local',
      'height_is_surveyed':False,'height_method':'official_floors_times_3m_ESTIMATE',
      'no_parcel_or_person_identifiers_exported':True,
      'returned_features':returned,'candidate_parts':len(parts),
      'total_osm_buildings':len(buildings),'matched_osm_count':len(matched),
      'matched_bu_part_count':sum(len(v['sections']) for v in matched),
      'skipped':skipped,'matching':stats,'matched':matched}
    if len(json.dumps(result).encode())>2*1024*1024:raise ValueError('Output oversized')
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['gml','osm','manifest','official-url','output']:p.add_argument('--'+name,required=True)
    a=p.parse_args()
    report=compile_overlay(gml=a.gml,osm=a.osm,manifest=a.manifest,official_url=a.official_url)
    Path(a.output).write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='matched'},indent=2))

if __name__=='__main__':main()
