#!/usr/bin/env python3
"""Synthetic, geographically consistent fixture for end-to-end Blender Catastro QA."""
import argparse
import json
import math
from pathlib import Path
from urllib.parse import urlencode
from pyproj import Transformer
from catastro_parts import compile_overlay

p=argparse.ArgumentParser();p.add_argument('--workspace',required=True)
a=p.parse_args()
ws=Path(a.workspace);inp=ws/'input';out=ws/'output'
inp.mkdir(parents=True,exist_ok=True);out.mkdir(parents=True,exist_ok=True)
center=(-.48322,38.34402);r=6378137.
origin=[r*math.radians(center[0]),r*math.log(math.tan(math.pi/4+math.radians(center[1])/2))]
def square(x,y,w,h):
    return [(x,y),(x+w,y),(x+w,y+h),(x,y+h),(x,y)]
a=square(-.48355,38.34390,.00010,.000075)
b=square(-.48275,38.34420,.00009,.00007)
def way(idx,first,ring):
    nd=''.join(f'<node id="{first+i}" lon="{x:.9f}" lat="{y:.9f}"/>' for i,(x,y) in enumerate(ring[:-1]))
    w=f'<way id="{idx}">'+''.join(f'<nd ref="{i}"/>' for i in list(range(first,first+len(ring)-1))+[first])+'<tag k="building" v="yes"/></way>'
    return nd,w
n1,w1=way(101,1,a);n2,w2=way(102,11,b)
(inp/'alicante.osm').write_text('<osm version="0.6">'+n1+n2+w1+w2+'</osm>')
tr=Transformer.from_crs('EPSG:4326','EPSG:25830',always_xy=True)
pos=' '.join(f'{x:.6f} {y:.6f}' for x,y in (tr.transform(lon,lat) for lon,lat in a))
gml=f'''<wfs:FeatureCollection xmlns:wfs="http://www.opengis.net/wfs/2.0" xmlns:bu="http://inspire.jrc.ec.europa.eu/schemas/bu-ext2d/2.0" xmlns:gml="http://www.opengis.net/gml/3.2">
<bu:BuildingPart gml:id="SECRET_SHOULD_NEVER_APPEAR"><bu:numberOfFloorsAboveGround>5</bu:numberOfFloorsAboveGround>
<bu:geometry><gml:Polygon srsName="EPSG::25830"><gml:exterior><gml:LinearRing><gml:posList>{pos}</gml:posList></gml:LinearRing></gml:exterior></gml:Polygon></bu:geometry></bu:BuildingPart>
</wfs:FeatureCollection>'''
(inp/'catastro_building_parts.gml').write_text(gml)
coords=[(r*math.radians(v[0])-origin[0],r*math.log(math.tan(math.pi/4+math.radians(v[1])/2))-origin[1]) for v in [(-.4862,38.3418),(-.4795,38.347)]]
manifest={'center_mercator':origin,'bbox_local_m':[coords[0][0],coords[0][1],coords[1][0],coords[1][1]],
 'real_orthophoto':False}
(inp/'source_manifest.json').write_text(json.dumps(manifest))
url='https://ovc.catastro.meh.es/INSPIRE/wfsBU.aspx?'+urlencode({
 'service':'wfs','request':'getfeature','typenames':'BU.BUILDINGPART',
 'bbox':'719600,4246700,720300,4247400','srsname':'EPSG::25830'})
source=compile_overlay(gml=inp/'catastro_building_parts.gml',osm=inp/'alicante.osm',manifest=inp/'source_manifest.json',official_url=url)
assert source['matched_osm_count']==1,source
(inp/'catastro_building_parts.json').write_text(json.dumps(source))
print('PASS: 2 synthetic OSM outlines, exactly 1 with matched official-style BU geometry, 1 original fallback')
