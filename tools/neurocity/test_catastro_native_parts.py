import math
import unittest

from shapely.geometry import box
from catastro_native_parts import collect_native_parts,MAX_NATIVE_PARTS

R=6378137.
ORIGIN=[R*math.radians(-.48322),R*math.log(math.tan(math.pi/4+math.radians(38.34402)/2))]
BBOX=(-.4862,38.3418,-.4795,38.347)

def part(x1,y1,x2,y2,floors=5):
    return {'poly':box(x1,y1,x2,y2),'floors':floors}

class IndependentOfficialParts(unittest.TestCase):
    def test_supplements_only_source_footprints_far_from_osm_buildings(self):
        osm=[('900',box(0,0,16,16))]
        source=[part(25,20,34,30,5),part(15.0,10,25,20,3),part(40,60,42,61,2)]
        native,stats=collect_native_parts(source,osm,ORIGIN,BBOX)
        self.assertEqual(len(native),1)
        self.assertEqual(native[0]['height_estimated_m'],15)
        self.assertEqual(stats['near_or_overlapping_osm'],1)
        self.assertEqual(stats['too_small'],1)
        self.assertFalse(stats['metric_height_verified'])
    def test_never_renders_overlapping_duplicate_stacks(self):
        source=[part(50,50,65,65),part(51,51,66,66),part(110,80,120,90)]
        native,stats=collect_native_parts(source,[],ORIGIN,BBOX)
        self.assertEqual(len(native),1)
        self.assertEqual(stats['overlapping_other_official_sections'],2)
    def test_rejects_beyond_geographically_original_city(self):
        native,stats=collect_native_parts([part(700,700,720,720)],[],ORIGIN,BBOX)
        self.assertEqual(native,[])
        self.assertEqual(stats['outside_public_city_bounds'],1)
    def test_render_budget_is_explicit_not_a_claim_of_full_coverage(self):
        source=[part(x,100,x+7,107) for x in (30,45,60,75)]
        native,stats=collect_native_parts(source,[],ORIGIN,BBOX,max_parts=2)
        self.assertEqual(len(native),2)
        self.assertEqual(stats['render_budget_deferred'],2)
        with self.assertRaises(ValueError):collect_native_parts(source,[],ORIGIN,BBOX,max_parts=MAX_NATIVE_PARTS+1)

if __name__=='__main__':unittest.main()
