#!/usr/bin/env python3
"""Grid regressions only use synthetic OSM and anonymous BU geometry."""
import hashlib
import json
import math
import tempfile
import unittest
from pathlib import Path
from pyproj import Transformer

from catastro_grid import source_plan, compile_grid

R=6378137
BBOX=(-.4862,38.3418,-.4795,38.347)
TR=Transformer.from_crs('EPSG:4326','EPSG:25830',always_xy=True)
BACK=Transformer.from_crs('EPSG:25830','EPSG:4326',always_xy=True)
CENTER=(-.48322,38.34402)
ORIGIN=[R*math.radians(CENTER[0]),R*math.log(math.tan(math.pi/4+math.radians(CENTER[1])/2))]

class GridTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.plan=source_plan(BBOX)
        self.origin=self.root/'source_manifest.json'
        self.origin.write_text(json.dumps({'bbox':BBOX,'center_mercator':ORIGIN}))
        # The ring straddles one official grid boundary so at least two
        # sources return exactly the same GML BuildingPart object.
        b0=self.plan[0]['bbox'];xx=b0[2]-35;yy=b0[3]-35
        ring=[(xx-4,yy-4),(xx+4,yy-4),(xx+4,yy+4),(xx-4,yy+4),(xx-4,yy-4)]
        coords=[BACK.transform(x,y) for x,y in ring]
        nd=''.join(f'<node id="{i+1}" lon="{x:.10f}" lat="{y:.10f}"/>' for i,(x,y) in enumerate(coords[:-1]))
        way='<way id="1001">'+''.join(f'<nd ref="{i+1}"/>' for i in range(4))+'<nd ref="1"/><tag k="building" v="yes"/></way>'
        self.osm=self.root/'osm.xml';self.osm.write_text('<osm>'+nd+way+'</osm>')
        pos=' '.join(f'{x} {y}' for x,y in ring)
        self.gml='<wfs:FeatureCollection xmlns:wfs="http://www.opengis.net/wfs/2.0" xmlns:bu="http://inspire.jrc.ec.europa.eu/schemas/bu-ext2d/2.0" xmlns:gml="http://www.opengis.net/gml/3.2"><bu:BuildingPart gml:id="PERSONAL_LOOKING_ID_TO_REMOVE"><bu:numberOfFloorsAboveGround>4</bu:numberOfFloorsAboveGround><bu:geometry><gml:Polygon srsName="EPSG::25830"><gml:exterior><gml:LinearRing><gml:posList>'+pos+'</gml:posList></gml:LinearRing></gml:exterior></gml:Polygon></bu:geometry></bu:BuildingPart></wfs:FeatureCollection>'
        self.sources=[]
        for item in self.plan:
            path=self.root/item['name']
            path.write_text(self.gml)
            self.sources.append((item['id'],item['url'],path))

    def tearDown(self):self.temp.cleanup()

    def test_plan_is_nine_valid_bounded_utm_tiles_and_covers_all_corners(self):
        self.assertEqual(len(self.plan),9)
        self.assertEqual(len({t['url'] for t in self.plan}),9)
        self.assertLess(max((x['bbox'][2]-x['bbox'][0])*(x['bbox'][3]-x['bbox'][1]) for x in self.plan),120_000)
        for x in self.plan:self.assertRegex(x['id'],r'^r[0-2]_c[0-2]$')
        with self.assertRaisesRegex(ValueError,'Outside audited'):source_plan((-4.,40.,-3.,41.))
    def test_nine_identical_sources_deduplicate_and_never_leak_gml_identity(self):
        src_hash=hashlib.sha256(self.osm.read_bytes()).hexdigest()
        result=compile_grid(samples=self.sources,osm=self.osm,manifest=self.origin,
            expected_ids=[x['id'] for x in self.plan])
        self.assertTrue(result['coverage_complete'])
        self.assertEqual(result['verified_tile_count'],9)
        self.assertEqual(result['matched_osm_count'],1)
        self.assertEqual(result['matched_bu_part_count'],1)
        self.assertEqual(result['matched'][0]['sections'][0]['height_estimated_m'],12.0)
        self.assertGreater(result['source_duplicates'],0)
        self.assertNotIn('PERSONAL_LOOKING_ID_TO_REMOVE',json.dumps(result))
        self.assertEqual(src_hash,hashlib.sha256(self.osm.read_bytes()).hexdigest())
        self.assertFalse(result['height_is_surveyed'])
    def test_missing_cells_refuse_full_coverage_claim(self):
        r=compile_grid(samples=self.sources[:2],osm=self.osm,manifest=self.origin)
        self.assertFalse(r['coverage_complete'])
        self.assertEqual(r['verified_tile_count'],2)
        with self.assertRaisesRegex(ValueError,'Missing official grid'):
            compile_grid(samples=self.sources[:2],osm=self.osm,manifest=self.origin,
                expected_ids=[x['id'] for x in self.plan])
    def test_duplicate_tile_id_refused(self):
        with self.assertRaisesRegex(ValueError,'duplicate tile'):
            compile_grid(samples=[self.sources[0],self.sources[0]],osm=self.osm,manifest=self.origin)
    def test_wrong_source_file_and_wfs_url_refused(self):
        tile,url,path=self.sources[0]
        with self.assertRaisesRegex(ValueError,'source filename'):
            compile_grid(samples=[(tile,url,self.osm)],osm=self.osm,manifest=self.origin)
        with self.assertRaises(ValueError):
            compile_grid(samples=[(tile,url.replace('ovc.catastro.meh.es','fake.invalid'),path)],
                osm=self.osm,manifest=self.origin)

if __name__=='__main__':unittest.main()
