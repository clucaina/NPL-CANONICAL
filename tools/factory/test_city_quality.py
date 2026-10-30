import json
import struct
import tempfile
import unittest
from pathlib import Path
from city_quality import audit, valid_building_footprint

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
            payload = {"asset":{"version":"2.0"},
                       "meshes":[{"primitives":[{"attributes":{"POSITION":0}}]}],
                       "accessors":[{"bufferView":0,"componentType":5126,"count":3,"type":"VEC3"}],
                       "bufferViews":[{"buffer":0,"byteOffset":0,"byteLength":36}],
                       "buffers":[{"byteLength":36}]}
            chunk = json.dumps(payload).encode()
            chunk += b" " * (-len(chunk)%4)
            binary = b"\x00" * 36
            glb.write_bytes(b"glTF" + struct.pack("<II",2,20+len(chunk)+8+len(binary))
                + struct.pack("<I4s",len(chunk),b"JSON") + chunk
                + struct.pack("<I4s",len(binary),b"BIN\x00") + binary)
            result = audit(osm,manifest,scene,glb)
            self.assertEqual(result["gate"],"PASS_PROVENANCE_ONLY")
            self.assertEqual(result["evidence"]["glb_drawable_primitives"],1)
            self.assertEqual(result["evidence"]["osm_buildings_with_no_valid_measured_height"],0)
            scene.write_text(json.dumps({"real_osm_buildings":1,"heights_directly_measured":2}))
            self.assertEqual(audit(osm,manifest,scene,glb)["gate"],"FAIL")
            valid_scene = {"real_osm_buildings":1,"heights_directly_measured":1,
                           "facades_photogrammetric":False,"private_avatar_included":False}
            invalid_scenes = [
                {}, {"real_osm_buildings":0,"heights_directly_measured":0},
                {"real_osm_buildings":-1,"heights_directly_measured":0},
                {"real_osm_buildings":True,"heights_directly_measured":0},
                {"real_osm_buildings":1.0,"heights_directly_measured":0},
                {"real_osm_buildings":2,"heights_directly_measured":0},
                {"real_osm_buildings":1,"heights_directly_measured":-1},
                {"real_osm_buildings":1,"heights_directly_measured":True},
            ]
            for bad_scene in invalid_scenes:
                with self.subTest(scene=bad_scene):
                    scene.write_text(json.dumps(bad_scene))
                    self.assertEqual(audit(osm,manifest,scene,glb)["gate"],"FAIL")
            scene.write_text(json.dumps(valid_scene))
            # Falsy non-booleans must never certify the absence of private
            # assets or unsupported facade photogrammetry.
            for field in ("private_avatar_included", "facades_photogrammetric"):
                for invalid in (0, None, "", [], {}, "false"):
                    with self.subTest(field=field, invalid=invalid):
                        scene.write_text(json.dumps({**valid_scene, field: invalid}))
                        self.assertEqual(audit(osm, manifest, scene, glb)["gate"], "FAIL")
            scene.write_text(json.dumps(valid_scene))
            for invalid in (0, None, "", [], {}, "false"):
                with self.subTest(manifest_facades=invalid):
                    manifest.write_text(json.dumps({"bbox_local_m": [0, 0, 10, 10],
                                                    "real_orthophoto": False,
                                                    "building_facades_photogrammetric": invalid}))
                    self.assertEqual(audit(osm, manifest, scene, glb)["gate"], "FAIL")
            manifest.write_text(json.dumps({"bbox_local_m": [0, 0, 10, 10],
                                            "real_orthophoto": False}))
            self.assertEqual(audit(osm, manifest, scene, glb)["gate"], "PASS_PROVENANCE_ONLY")
            invalid_bounds = [
                [0,0,"10",10], [0,0,float("nan"),10],
                [0,0,float("inf"),10], [False,0,10,10], [0,0,10**1000,10],
                [0,0,0,10], [0,0,10,-1],
            ]
            for bbox in invalid_bounds:
                with self.subTest(bbox=bbox):
                    manifest.write_text(json.dumps({"bbox_local_m":bbox,"real_orthophoto":False}))
                    self.assertEqual(audit(osm,manifest,scene,glb)["gate"],"FAIL")
            manifest.write_text(json.dumps({"bbox_local_m":[0,0,10,10],"real_orthophoto":"false"}))
            self.assertEqual(audit(osm,manifest,scene,glb)["gate"],"FAIL")
            manifest.write_text(json.dumps({"bbox_local_m":[0,0,10,10],"real_orthophoto":False}))
            self.assertEqual(audit(osm,manifest,scene,glb)["gate"],"PASS_PROVENANCE_ONLY")
            # A closed list of node IDs is not necessarily a georeferenced footprint.
            original_osm = osm.read_text()
            invalid_footprints = {
                "two_distinct_nodes": original_osm.replace('<nd ref="3"/>', '<nd ref="2"/>'),
                "nonfinite_latitude": original_osm.replace('lat="38.35"', 'lat="nan"'),
                "latitude_outside_earth": original_osm.replace('lat="38.35"', 'lat="100"'),
                "missing_latitude": original_osm.replace('lat="38.35"', 'lat=""'),
                "collinear_nodes": original_osm.replace('lat="38.35" lon="-0.48"', 'lat="38.34" lon="-0.46"'),
                "same_position_twice": original_osm.replace('lat="38.35" lon="-0.48"', 'lat="38.34" lon="-0.48"'),
            }
            for reason, bad_osm in invalid_footprints.items():
                with self.subTest(reason=reason):
                    self.assertNotEqual(bad_osm, original_osm)
                    osm.write_text(bad_osm)
                    result = audit(osm,manifest,scene,glb)
                    self.assertEqual(result["gate"], "FAIL")
                    self.assertEqual(result["evidence"]["closed_node_complete_ways"], 0)
            osm.write_text(original_osm)
            self.assertEqual(audit(osm,manifest,scene,glb)["gate"],"PASS_PROVENANCE_ONLY")
            # A height tag on a degenerate footprint cannot substantiate a
            # measured-height claim for a different, complete building.
            no_height = original_osm.replace('<tag k="height" v="11"/>', '')
            self.assertNotEqual(no_height, original_osm)
            invalid_height_way = ('<way id="6"><nd ref="1"/><nd ref="2"/>'
                                  '<nd ref="2"/><nd ref="1"/>'
                                  '<tag k="building" v="yes"/>'
                                  '<tag k="height" v="12"/></way>')
            osm.write_text(no_height.replace("</osm>", invalid_height_way + "</osm>"))
            result = audit(osm, manifest, scene, glb)
            self.assertEqual(result["evidence"]["closed_node_complete_ways"], 1)
            self.assertEqual(result["evidence"]["osm_explicit_height_tags_valid"], 0)
            self.assertEqual(result["gate"], "FAIL")
            scene.write_text(json.dumps({**valid_scene, "heights_directly_measured": 0}))
            self.assertEqual(audit(osm, manifest, scene, glb)["gate"], "PASS_PROVENANCE_ONLY")
    def test_crossing_osm_building_with_nonzero_area_is_rejected(self):
        # Synthetic polygon: its signed area is nonzero but two walls cross.
        crossing = [(0, 0), (4, 4), (0, 4), (4, 0), (5, 3)]
        concave = [(0, 0), (4, 0), (4, 4), (2, 2), (0, 4)]
        def footprint(vertices):
            nodes = {str(i): (38.3 + x / 10000, -0.48 + y / 10000)
                     for i, (x, y) in enumerate(vertices)}
            refs = list(nodes) + ["0"]
            return valid_building_footprint(refs, nodes)
        self.assertFalse(footprint(crossing))
        self.assertTrue(footprint(concave))
        self.assertFalse(footprint([(0, 0), (4, 0), (4, 4), (0, 4), (4, 0)]))

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
