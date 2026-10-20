import importlib.util
import tempfile
import unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('spain_tile_factory',Path(__file__).with_name('spain_tile_factory.py'))
factory=importlib.util.module_from_spec(spec);spec.loader.exec_module(factory)

class NationalProductionPlan(unittest.TestCase):
 def seed(self):
  return {'city':'alicante','crs':25830,'bbox_projected_m':[719000,4247000,720000,4248000],
          'sources':{'osm':{'verified':True,'license_approved':True,'sha256':'a'*64}}}
 def test_bounded_four_500m_tiles_no_fictitious_city_generation(self):
  p=factory.build_plan(self.seed())
  self.assertEqual(p['tiles_planned'],4)
  self.assertEqual(p['models_generated'],0)
  self.assertEqual(p['stages_per_tile'],8)
  self.assertEqual(p['original_files_modified'],0)
  for tile in p['tiles']:
   self.assertFalse(tile['mm_fidelity_claimed'])
   self.assertFalse(tile['real_employee_identities_present'])
   self.assertFalse(tile['real_interior_claimed'])
   self.assertEqual(tile['tasks'][0]['source_status'],'READY_FOR_COMPUTE')
   self.assertEqual(tile['tasks'][2]['source_status'],'BLOCKED_UNVERIFIED_SOURCE')
   self.assertIn('lidar',tile['tasks'][2]['missing_verified_sources'])
 def test_respects_crs_per_region(self):
  for crs in [25828,25829,25830,25831,4083]:
   p=factory.build_plan({**self.seed(),'city':'canarias','crs':crs})
   self.assertEqual(p['crs'],'EPSG:'+str(crs))
 def test_refuses_huge_jobs_unsafe_names_missing_rights(self):
  for seed in [
    {**self.seed(),'city':'../../patient'},
    {**self.seed(),'bbox_projected_m':[0,0,300000,300000]},
    {**self.seed(),'sources':{'person_records':{'verified':True}}},
    {**self.seed(),'sources':{'lidar':{'verified':True,'license_approved':False,'sha256':'a'*64}}}
  ]:
   if seed['sources'].get('lidar'):
    p=factory.build_plan(seed)
    self.assertEqual(p['tiles'][0]['tasks'][2]['source_status'],'BLOCKED_UNVERIFIED_SOURCE')
   else:
    with self.assertRaises(ValueError):factory.build_plan(seed)
 def test_partial_coverage_cache_immutable_and_deterministic(self):
  one=factory.build_plan(self.seed(),max_tiles=4)
  two=factory.build_plan(self.seed(),max_tiles=4)
  self.assertEqual(one,two)
  self.assertEqual(len({t['id'] for t in one['tiles']}),4)
  with self.assertRaises(ValueError):factory.build_plan(self.seed(),max_tiles=2)

if __name__=='__main__':unittest.main()
