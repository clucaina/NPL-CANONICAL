#!/usr/bin/env python3
"""NeuroCity Alicante: deterministic 3x3 public cadastral-volume grid.

Never guesses survey height or publishes government GML. Inputs are bounded,
read-only WFS snapshots. Outputs are provenance-bearing 3D build instructions
for use in a LOCAL, non-deployed Blender build.
"""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path
from urllib.parse import urlencode

from pyproj import Transformer
from catastro_parts import (
    MAX_PARTS, LICENSE, SOURCE_DOC, load_xml, read_parts, read_osm,
    safe_matches, validate_official_url,
)
from catastro_native_parts import collect_native_parts

GRID_ROWS=3
GRID_COLS=3
PADDING_METERS=35
MAX_TOTAL_PARTS=30000
ID_RE=re.compile(r"^r[0-2]_c[0-2]$")
BASE="https://ovc.catastro.meh.es/INSPIRE/wfsBU.aspx"

def source_plan(bounds,rows=GRID_ROWS,cols=GRID_COLS,padding=PADDING_METERS):
    if rows!=3 or cols!=3 or not isinstance(bounds,(list,tuple)) or len(bounds)!=4:
        raise ValueError("Only audited Alicante 3x3 cells are supported")
    west,south,east,north=map(float,bounds)
    if not all(math.isfinite(x) for x in (west,south,east,north)) or not (
        -.49<west<east<-.47 and 38.33<south<north<38.36):
        raise ValueError("Outside audited Alicante bounds")
    tr=Transformer.from_crs('EPSG:4326','EPSG:25830',always_xy=True)
    corners=[tr.transform(x,y) for x in (west,east) for y in (south,north)]
    lo_x=min(x for x,_ in corners)-3;hi_x=max(x for x,_ in corners)+3
    lo_y=min(y for _,y in corners)-3;hi_y=max(y for _,y in corners)+3
    width=(hi_x-lo_x)/cols;height=(hi_y-lo_y)/rows
    plan=[]
    for row in range(rows):
        for col in range(cols):
            rect=(round(lo_x+col*width-padding,2),
                  round(lo_y+row*height-padding,2),
                  round(lo_x+(col+1)*width+padding,2),
                  round(lo_y+(row+1)*height+padding,2))
            url=BASE+'?'+urlencode({
                'service':'WFS','version':'2.0.0','request':'GetFeature',
                'typenames':'BU.BUILDINGPART',
                'bbox':','.join(map(str,rect)),'srsname':'EPSG::25830'
            })
            validate_official_url(url)
            plan.append({'id':f'r{row}_c{col}','bbox':rect,'url':url,'name':f'r{row}_c{col}.gml'})
    return plan

def compile_grid(*,samples,osm,manifest,expected_ids=None):
    """samples are (grid_id, official WFS URL, local GML path)."""
    manifest_data=json.loads(Path(manifest).read_text(encoding='utf-8'))
    origin=manifest_data.get('center_mercator')
    if (not isinstance(origin,list) or len(origin)!=2 or
        not all(type(x) in (int,float) and math.isfinite(x) for x in origin)):
        raise ValueError('Original Mercator origin must be finite')
    source=[]
    seen_tiles=set()
    unique={}
    conflict=set()
    duplicate_count=0
    skipped={}
    count=0
    for tile_id,url,path in samples:
        if not isinstance(tile_id,str) or not ID_RE.fullmatch(tile_id) or tile_id in seen_tiles:
            raise ValueError('Unexpected or duplicate tile')
        seen_tiles.add(tile_id)
        bbox=validate_official_url(url)
        path=Path(path)
        if path.name!=tile_id+'.gml':
            raise ValueError('Unsafe or mismatched source filename')
        root,digest=load_xml(path)
        parts,source_skipped,returned=read_parts(root,bbox,origin)
        count+=len(parts)
        if count>MAX_TOTAL_PARTS:raise ValueError('Excessive cumulative building parts')
        for key,val in source_skipped.items():
            skipped[key]=skipped.get(key,0)+val
        source.append({'tile_id':tile_id,'gml_name':path.name,'url':url,
                       'sha256':digest,'returned':returned,'candidates':len(parts)})
        for part in parts:
            # Canonical polygon geometry is stable across repeated WFS tiles:
            # only its geometry and public storey count enter the deduplicator.
            geom=part['poly']
            key=hashlib.sha256(geom.normalize().wkb).hexdigest()
            if key in conflict:continue
            if key in unique:
                duplicate_count+=1
                if unique[key]['floors']!=part['floors']:
                    conflict.add(key);del unique[key]
            else:
                unique[key]=part
    if not source:raise ValueError('No verified tile snapshots')
    if expected_ids is not None:
        if set(expected_ids)!={x['tile_id'] for x in source}:
            raise ValueError('Missing official grid cells; no full coverage claim')
    parts=list(unique.values())
    buildings=read_osm(osm,origin)
    matched,stats=safe_matches(parts,buildings)
    # Different, stricter path: geometries verified to be independent of
    # EVERY existing OSM footprint are added rather than made into false joins.
    m_bbox=manifest_data.get('bbox')
    native_parts,native_stats=collect_native_parts(parts,buildings,origin,m_bbox)
    result={
        'schema':'neurocity.catastro-building-grid.v2',
        'source':'DG_CATASTRO_INSPIRE_BU_BUILDINGPART',
        'license_url':LICENSE,'source_documentation':SOURCE_DOC,
        'crs':'EPSG:3857_local','height_is_surveyed':False,
        'height_method':'official_floors_times_3m_ESTIMATE',
        'no_parcel_or_person_identifiers_exported':True,
        'expected_tile_count':GRID_ROWS*GRID_COLS,
        'verified_tile_count':len(source),
        'coverage_complete':len(source)==GRID_ROWS*GRID_COLS,
        'source_tiles':source,'source_candidate_parts':count,
        'unique_candidate_parts':len(parts),
        'source_duplicates':duplicate_count,'conflicting_duplicates_rejected':len(conflict),
        'skipped':skipped,'total_osm_buildings':len(buildings),
        'matched_osm_count':len(matched),
        'matched_bu_part_count':sum(len(m['sections']) for m in matched),
        'matching':stats,'matched':matched,
        'independent_official_parts':native_parts,
        'independent_official_part_count':len(native_parts),
        'independent_official_selection_qa':native_stats
    }
    if len(json.dumps(result).encode())>4*1024*1024:
        raise ValueError('Public geometric instructions exceed 4 MiB')
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--osm',required=True)
    p.add_argument('--manifest',required=True)
    p.add_argument('--source-dir',required=True)
    p.add_argument('--output',required=True)
    p.add_argument('--require-complete',action='store_true')
    a=p.parse_args()
    src=Path(a.source_dir)
    m=json.loads(Path(a.manifest).read_text())
    plan=source_plan(m['bbox'])
    sources=[(item['id'],item['url'],src/item['name']) for item in plan if (src/item['name']).is_file()]
    result=compile_grid(samples=sources,osm=a.osm,manifest=a.manifest,
        expected_ids=[i['id'] for i in plan] if a.require_complete else None)
    Path(a.output).write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k not in ('matched','source_tiles')},indent=2))

if __name__=='__main__':main()
