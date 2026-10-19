import json
import struct
import tempfile
import unittest
from pathlib import Path
from city_quality import audit

class CityQualityTests(unittest.TestCase):
    def test_real_provenance_pass_and_false_height_claim_fails(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            osm = p/"city.osm"
            osm.write_text('<osm><node id="1" lat="38.34" lon="-0.48"/><node id="2" lat="38.34" lon="-0.47"/><node id="3" lat="38.35" lon="-0.48"/><way id="4"><nd ref="1"/><nd ref="2"/><nd ref="3"/><nd ref="1"/><tag k="building" v="yes"/><tag k="height" v="11"/></way><way id="5"><nd ref="1"/><nd ref="2"/><tag k="highway" v="residential"/></way></osm>')
            manifest = p/"manifest.json"
            manifest.write_text(json.dumps({"bbox_local_m":[0,0,10,10],"real_orthophoto":False}))
            scene = p/"scene.json"
            scene.write_text(json.dumps({"real_osm_buildings":1,"heights_directly_measured":1,"facades_photogrammetric":False,"private_avatar_included":False}))
            glb = p/"scene.glb"
            chunk = json.dumps({"asset":{"version":"2.0"},"meshes":[{"primitives":[]}]}).encode()
            chunk += b" " * (-len(chunk)%4)
            glb.write_bytes(b"glTF" + struct.pack("<II",2,20+len(chunk)) + struct.pack("<I4s",len(chunk),b"JSON") + chunk)
            self.assertEqual(audit(osm,manifest,scene,glb)["gate"],"PASS_PROVENANCE_ONLY")
            scene.write_text(json.dumps({"real_osm_buildings":1,"heights_directly_measured":2}))
            self.assertEqual(audit(osm,manifest,scene,glb)["gate"],"FAIL")
    def test_empty_or_invalid_glb_fails(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            (p/"city.osm").write_text("<osm></osm>")
            (p/"manifest.json").write_text(json.dumps({"bbox_local_m":[0,0,1,1]}))
            (p/"scene.json").write_text(json.dumps({"real_osm_buildings":0}))
            (p/"scene.glb").write_bytes(b"bad")
            self.assertEqual(audit(p/"city.osm",p/"manifest.json",p/"scene.json",p/"scene.glb")["gate"],"FAIL")

if __name__ == "__main__":
    unittest.main()
