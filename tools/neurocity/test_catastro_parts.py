#!/usr/bin/env python3
"""Synthetic-only Catastro BU/OSM join tests. No network or personal data."""
import json
import math
import tempfile
import unittest
from pathlib import Path
from urllib.parse import urlencode
from pyproj import Transformer
from catastro_parts import compile_overlay,validate_official_url

R=6378137.
CENTER=(-.48322,38.34402)
ORIGIN=[R*math.radians(CENTER[0]),R*math.log(math.tan(math.pi/4+math.radians(CENTER[1])/2))]
URL='https://ovc.catastro.meh.es/INSPIRE/wfsBU.aspx?'+urlencode({
 'service':'wfs','version':'2','request':'getfeature','typenames':'BU.BUILDINGPART',
 'bbox':'719600,4246700,720300,4247400','srsname':'EPSG::25830'})
transform=Transformer.from_crs('EPSG:4326','EPSG:25830',always_xy=True)

def square(x,y,w=.00010,h=.000075):
    return [(x,y),(x+w,y),(x+w,y+h),(x,y+h),(x,y)]

def part(coords,floors='5',epsg='EPSG::25830'):
    pos=' '.join(f'{x:.6f} {y:.6f}' for x,y in (transform.transform(*xy) for xy in coords))
    return (f'<bu:BuildingPart xmlns:bu="http://inspire.jrc.ec.europa.eu/schemas/bu-ext2d/2.0" xmlns:gml="http://www.opengis.net/gml/3.2" gml:id="SECRET_REF_NOT_TO_EXPORT">'
     f'<bu:numberOfFloorsAboveGround>{floors}</bu:numberOfFloorsAboveGround><bu:geometry>'
     f'<gml:Polygon srsName="{epsg}"><gml:exterior><gml:LinearRing>'
     f'<gml:posList>{pos}</gml:posList></gml:LinearRing></gml:exterior></gml:Polygon>'
     f'</bu:geometry></bu:BuildingPart>')

def wrap(content):
    return '<wfs:FeatureCollection xmlns:wfs="http://www.opengis.net/wfs/2.0">'+content+'</wfs:FeatureCollection>'

def way(i,first,coords):
    refs=list(range(first,first+len(coords)-1))
    nodes=''.join(f'<node id="{j}" lon="{x:.9f}" lat="{y:.9f}"/>' for j,(x,y) in zip(refs,coords[:-1]))
    return nodes,f'<way id="{i}">'+''.join(f'<nd ref="{j}"/>' for j in refs+[first])+'<tag k="building" v="yes"/></way>'

class CatastroBuildingTests(unittest.TestCase):
 def setUp(self):
    self.tmp=tempfile.TemporaryDirectory();d=Path(self.tmp.name)
    self.a=square(-.48355,38.34390)
    n1,w1=way('101',1,self.a)
    n2,w2=way('102',11,square(-.48275,38.34420))
    self.osm=d/'map.osm';self.osm.write_text('<osm>'+n1+n2+w1+w2+'</osm>')
    self.gml=d/'catastro.gml';self.gml.write_text(wrap(part(self.a)))
    self.manifest=d/'manifest.json';self.manifest.write_text(json.dumps({'center_mercator':ORIGIN}))
 def tearDown(self):self.tmp.cleanup()
 def run_join(self):
    return compile_overlay(gml=self.gml,osm=self.osm,manifest=self.manifest,official_url=URL)

 def test_real_original_source_files_preserved_and_only_unique_full_match_replaced(self):
    before=(self.osm.read_bytes(),self.gml.read_bytes())
    v=self.run_join()
    self.assertEqual(v['matched_osm_count'],1)
    self.assertEqual(v['matched'][0]['osm_way_id'],'101')
    self.assertEqual(v['matched'][0]['sections'][0]['height_estimated_m'],15)
    self.assertFalse(v['height_is_surveyed'])
    self.assertNotIn('SECRET_REF_NOT_TO_EXPORT',json.dumps(v))
    self.assertEqual(before,(self.osm.read_bytes(),self.gml.read_bytes()))

 def test_partial_footprint_refused(self):
    self.gml.write_text(wrap(part(square(-.48355,38.34390,w=.00004))))
    self.assertEqual(self.run_join()['matched_osm_count'],0)

 def test_wrong_crs_and_unknown_floors_refused(self):
    self.gml.write_text(wrap(part(self.a,epsg='EPSG::4326')))
    self.assertEqual(self.run_join()['skipped']['unsupported_crs'],1)
    self.gml.write_text(wrap(part(self.a,floors='unknown')))
    self.assertEqual(self.run_join()['skipped']['unknown_floors'],1)

 def test_official_source_and_small_bbox_are_mandatory(self):
    self.assertEqual(len(validate_official_url(URL)),4)
    for u in [URL.replace('https:','http:'),URL.replace('ovc.catastro.meh.es','evil.org'),
      URL.replace('BU.BUILDINGPART','BU.OTHERCONSTRUCTION'),
      URL.replace('719600%2C4246700%2C720300%2C4247400','0%2C0%2C100%2C100')]:
      with self.subTest(u=u),self.assertRaises(ValueError):validate_official_url(u)

 def test_reject_dtd_and_wfs_exception_without_modifying_baseline(self):
    self.gml.write_text('<!DOCTYPE x [<!ENTITY bad "secret">]>'+wrap(''))
    with self.assertRaisesRegex(ValueError,'DTD'):self.run_join()
    self.gml.write_text('<ExceptionReport>too many objects</ExceptionReport>')
    with self.assertRaisesRegex(ValueError,'exception'):self.run_join()

 def test_nonlocal_feature_is_excluded(self):
    self.gml.write_text(wrap(part(square(-.55,38.35))))
    report=self.run_join()
    self.assertEqual(report['matched_osm_count'],0)
    self.assertEqual(report['skipped']['outside_area'],1)

if __name__=='__main__':unittest.main()
