#!/usr/bin/env python3
"""Prepare a nine-tile synthetic official-style 3D Blender smoke fixture."""
import argparse
import json
import subprocess
import sys
from pathlib import Path

from catastro_grid import compile_grid,source_plan

BBOX=(-.4862,38.3418,-.4795,38.347)

def main():
    a=argparse.ArgumentParser()
    a.add_argument('--workspace',required=True)
    args=a.parse_args()
    root=Path(args.workspace)
    original=Path(__file__).with_name('catastro_blender_smoke.py')
    subprocess.run([sys.executable,str(original),'--workspace',str(root)],check=True)
    inp=root/'input'
    m=inp/'source_manifest.json'
    manifest=json.loads(m.read_text());manifest['bbox']=BBOX
    m.write_text(json.dumps(manifest))
    original_gml=inp/'catastro_building_parts.gml'
    tiles=inp/'catastro_grid_tiles'
    tiles.mkdir(exist_ok=True)
    plan=source_plan(BBOX)
    sources=[]
    for q in plan:
        file=tiles/q['name'];file.write_bytes(original_gml.read_bytes())
        sources.append((q['id'],q['url'],file))
    overlay=compile_grid(samples=sources,osm=inp/'alicante.osm',manifest=m,
        expected_ids=[x['id'] for x in plan])
    assert overlay['matched_osm_count']==1,overlay
    assert overlay['coverage_complete'],overlay
    (inp/'catastro_building_parts.json').write_text(json.dumps(overlay))
    original_gml.unlink()
    print('PASS: nine source snapshots, one synthetic verified building replacement, immutable OSM fallback')

if __name__=='__main__':main()
