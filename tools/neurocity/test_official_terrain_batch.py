import json
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs,urlsplit

from official_terrain_batch import TILES,MAX_TILES,run
from official_terrain_probe import request_url

def fake_cog(url):
    import numpy as np
    from rasterio.io import MemoryFile
    from rasterio.transform import from_origin
    params=parse_qs(urlsplit(url).query)
    bb=tuple(map(int,params["bbox"][0].split(",")))
    a=np.fromfunction(lambda r,c: 2+.013*r+.025*c,(101,101),dtype=float).astype("float32")
    a[0,0]=-9999
    with MemoryFile() as t:
        with t.open(driver="GTiff",width=101,height=101,count=1,
                    crs="EPSG:3042",transform=from_origin(bb[0],bb[3],5,5),
                    nodata=-9999,dtype="float32") as dst:
            dst.write(a,1)
        return t.read()

class FourOriginalTileTests(unittest.TestCase):
    def test_01_four_verified_tiles_exactly_no_new_cities(self):
        self.assertEqual(len(TILES),MAX_TILES)
        self.assertEqual(len({t[0] for t in TILES}),4)
        self.assertEqual(TILES[-1],("r01_c02",(720700,4247300,721200,4247800)))
        for _,box in TILES:self.assertIn("bbox-crs=25830",request_url(box))

    def test_02_four_geotiffs_generate_twelve_lods_with_no_private_glbs(self):
        with tempfile.TemporaryDirectory() as td:
            report=run(td,fetch=fake_cog)
            self.assertEqual(report["tiles_with_three_real_source_lods"],4)
            self.assertEqual(report["mesh_candidates_created"],12)
            self.assertTrue(report["all_tiles_height_validated"])
            self.assertTrue(report["not_live_in_game"])
            self.assertFalse(report["vertical_reference_to_original_G19_approved"])
            for tile,_ in TILES:
                self.assertEqual(len(list((Path(td)/tile/"glb").glob("*.glb"))),3)
                m=json.loads((Path(td)/tile/"glb/SOURCE_LICENSE_QA.json").read_text())
                self.assertEqual(m["tile_id"],tile)
                self.assertTrue(m["G19_horizontal_axis_convention_used"])

    def test_03_failed_official_tile_does_not_invent_3d_or_fake_green(self):
        def intermittent(url):
            if "719700,4246800" in url:
                raise ConnectionError("Official service unavailable")
            return fake_cog(url)
        with tempfile.TemporaryDirectory() as td:
            report=run(td,fetch=intermittent)
            self.assertFalse(report["all_tiles_height_validated"])
            self.assertEqual(report["tiles_with_three_real_source_lods"],3)
            self.assertEqual(report["mesh_candidates_created"],9)
            self.assertEqual(report["results"][0]["status"],"BLOCKED_REAL_SOURCE_NOT_VALIDATED")
            self.assertEqual(report["results"][0]["models_created"],0)
            self.assertFalse(list((Path(td)/"r02_c00").rglob("*.glb")))
            self.assertTrue((Path(td)/"FOUR_TILE_IGN_COVERAGE_QA.json").exists())

if __name__=="__main__":
    unittest.main()
