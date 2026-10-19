import json,sys,tempfile
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).parent))
from coast_inventory import audit
class CoastAuditTests(unittest.TestCase):
 def make(self,xml):
  f=tempfile.NamedTemporaryFile(suffix=".osm",delete=False)
  f.write(xml.encode());f.close()
  self.addCleanup(lambda:Path(f.name).unlink(missing_ok=True))
  return Path(f.name)
 def test_does_not_invent_sea_or_boats(self):
  osm=self.make('<osm><node id="1" lat="38.34" lon="-0.48"/><node id="2" lat="38.33" lon="-0.48"/><way id="9"><nd ref="1"/><nd ref="2"/><tag k="natural" v="coastline"/></way><way id="10"><nd ref="1"/><nd ref="2"/><tag k="man_made" v="pier"/></way></osm>')
  r=audit(osm,{"bbox":[-0.49,38.33,-0.47,38.35]})
  self.assertTrue(r["coastline_geometry_source_available"])
  self.assertTrue(r["piers_source_available"])
  self.assertEqual(r["coverage_counts"]["pier"]["objects"],1)
  self.assertFalse(r["coastal_rendering_verified"])
  self.assertFalse(r["maritime_boats_verified"])
  self.assertFalse(r["visual_assets_actually_created"]["sea_surface_mesh"])
 def test_missing_source_is_not_presented_as_valid_3d(self):
  osm=self.make('<osm><node id="1" lat="38.34" lon="-0.48"/></osm>')
  r=audit(osm,{"bbox":[-0.49,38.33,-0.47,38.35]})
  self.assertTrue(r["manual_source_expansion_review_required"])
  self.assertEqual(r["coverage_counts"]["marina"]["objects"],0)
 def test_incomplete_node_references_not_buildable(self):
  osm=self.make('<osm><node id="1" lat="38.34" lon="-0.48"/><way id="7"><nd ref="1"/><nd ref="404"/><tag k="natural" v="coastline"/></way></osm>')
  r=audit(osm,{"bbox":[-0.49,38.33,-0.47,38.35]})
  self.assertEqual(r["coverage_counts"]["coastline"]["objects"],1)
  self.assertEqual(r["coverage_counts"]["coastline"]["with_nodes"],0)
  self.assertFalse(r["coastline_geometry_source_available"])
if __name__=="__main__":unittest.main()
