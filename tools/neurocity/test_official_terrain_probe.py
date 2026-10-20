import json
import tempfile
import unittest
from pathlib import Path
from official_terrain_probe import inspect_raster,probe,TILE,BBOX,MAX_BYTES,URL

class OfficialTerrainProbeTests(unittest.TestCase):
    def test_01_uses_one_existing_G12_alicante_tile_with_bounded_download(self):
        self.assertEqual(TILE,"r01_c02")
        self.assertEqual(BBOX,(720700,4247300,721200,4247800))
        self.assertEqual(MAX_BYTES,20_000_000)
        self.assertIn("bbox-crs=25830",URL)
        self.assertIn("api-coverages.idee.es",URL)

    def test_02_rejects_fake_200_HTML_as_height_pixels(self):
        with self.assertRaisesRegex(ValueError,"not TIFF"):
            inspect_raster(b"<!DOCTYPE html>Temporarily unavailable")

    def test_03_failed_network_never_promotes_legacy_flat_terrain(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"qa.json"
            def offline():
                raise ConnectionError("Name resolution failed")
            r=probe(p,fetch=offline)
            self.assertEqual(r["status"],"BLOCKED_REAL_SOURCE_NOT_VALIDATED")
            self.assertFalse(r["game_runtime_modified"])
            self.assertEqual(json.loads(p.read_text())["reason_type"],"ConnectionError")

    def test_04_no_silent_accept_of_empty_cog(self):
        with tempfile.TemporaryDirectory() as d:
            r=probe(Path(d)/"qa.json",fetch=lambda:b"")
            self.assertEqual(r["status"],"BLOCKED_REAL_SOURCE_NOT_VALIDATED")
            self.assertNotIn("source_file_sha256",r)

if __name__=="__main__":
    unittest.main()
