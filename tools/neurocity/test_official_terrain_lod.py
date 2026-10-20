import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from official_terrain_lod import glb_bytes,validate_glb_header,candidate_lods

class OfficialTerrainLodTests(unittest.TestCase):
    def test_01_glb_y_up_local_terrain_has_valid_header_and_licence(self):
        verts=[(0,4,0),(5,4,0),(0,4,-5),(5,4,-5)]
        data=glb_bytes(verts,[(0,1,2),(1,3,2)],origin=(720700,4247300),
                       source_hash="a"*64,step=1)
        hdr=validate_glb_header(data)
        self.assertEqual(hdr["vertices"],4)
        self.assertEqual(hdr["indices"],6)
        self.assertIn("CC-BY 4.0",hdr["attribution"])
        self.assertTrue(hdr["not_approved"])

    def test_02_invalid_vertices_and_faces_rejected(self):
        v=[(0,4,0),(5,4,0),(0,4,-5),(5,4,-5)]
        kw={"origin":(720700,4247300),"source_hash":"a"*64,"step":1}
        with self.assertRaisesRegex(ValueError,"Invalid"):
            glb_bytes(v,[(0,0,2)],**kw)
        with self.assertRaisesRegex(ValueError,"Nonfinite"):
            glb_bytes(v+[(float("nan"),0,0)],[(0,1,2)],**kw)

    @staticmethod
    def real_geotiff_fixture():
        import numpy as np
        from rasterio.io import MemoryFile
        from rasterio.transform import from_origin
        arr=np.fromfunction(lambda r,c: 3+0.01*r+0.018*c,(101,101),dtype=float).astype("float32")
        arr[0,0]=-9999
        with MemoryFile() as buf:
            with buf.open(driver="GTiff",width=101,height=101,count=1,
                          crs="EPSG:3042",transform=from_origin(720700,4247800,5,5),
                          nodata=-9999,dtype="float32") as ds:
                ds.write(arr,1)
            return buf.read()

    def test_03_three_real_pixel_lods_reversible_and_not_live(self):
        raw=self.real_geotiff_fixture()
        q={"status":"OFFICIAL_RASTER_PIXELS_VALIDATED_DATUM_PENDING",
           "source_file_sha256":hashlib.sha256(raw).hexdigest()}
        with tempfile.TemporaryDirectory() as d:
            out=candidate_lods(raw,d,q)
            self.assertEqual(len(out["lods"]),3)
            self.assertTrue(out["not_live_in_game"])
            self.assertFalse(out["baseline_G19_ground_alignment_verified"])
            self.assertTrue(out["terrain_elevation_from_real_pixels"])
            tris=[i["triangles_real"] for i in out["lods"]]
            self.assertGreater(tris[0],tris[1])
            self.assertGreater(tris[1],tris[2])
            for x in out["lods"]:
                source=(Path(d)/x["file"]).read_bytes()
                self.assertEqual(x["file_sha256"],hashlib.sha256(source).hexdigest())
                self.assertEqual(validate_glb_header(source)["indices"]//3,x["triangles_real"])
            audit=json.loads((Path(d)/"SOURCE_LICENSE_QA.json").read_text())
            self.assertEqual(audit["license"],"CC-BY-4.0")

    def test_04_unverified_sha_must_not_make_fake_glb(self):
        data=self.real_geotiff_fixture()
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError,"SHA mismatch"):
                candidate_lods(data,d,{"status":"OFFICIAL_RASTER_PIXELS_VALIDATED_DATUM_PENDING",
                                     "source_file_sha256":"0"*64})
            self.assertFalse(list(Path(d).glob("*.glb")))

    def test_05_reject_unverified_source_status(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError,"No verified"):
                candidate_lods(self.real_geotiff_fixture(),d,{"status":"BLOCKED_REAL_SOURCE_NOT_VALIDATED"})

if __name__=="__main__":
    unittest.main()
