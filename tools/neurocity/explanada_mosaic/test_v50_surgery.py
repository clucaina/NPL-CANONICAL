"""Synthetic public tests, with optional private local archived-asset tests.
No source GLBs or customer data included in repository or CI output.
"""
import io, os, tempfile, unittest, zipfile, json
from pathlib import Path
import numpy as np
import trimesh
from PIL import Image
from trimesh.visual.material import PBRMaterial
from trimesh.visual.texture import TextureVisuals
from v50_surgical_tessera import RECT,SourceSampler,split_source,cut,area,triangulate,build_patch,load_original,sha

ROOT=Path(__file__).resolve().parent
class SurgicalTests(unittest.TestCase):
    def synthetic(self):
        x0,z0,x1,z1=RECT
        v=np.array([[x0-2,2.3,z0-2],[x0-2,2.3,z1+2],[x1+2,2.3,z1+2],[x1+2,2.3,z0-2]],dtype=float)
        mesh=trimesh.Trimesh(vertices=v,faces=[[0,1,2],[0,2,3]],process=False)
        tex=Image.new('RGB',(32,32),(180,80,73))
        mesh.visual=TextureVisuals(uv=np.array([[0,0],[0,1],[1,1],[1,0]],dtype=float),material=PBRMaterial(baseColorTexture=tex,metallicFactor=0,roughnessFactor=.92))
        return mesh
    def test_clip_conserves_surface_and_16m2_hole(self):
        mesh=self.synthetic();outer,inner,r=split_source(mesh)
        self.assertAlmostEqual(r['removed_projected_area_m2'],16,delta=.0001)
        self.assertLess(r['area_error_m2'],1e-6)
        self.assertGreater(len(outer[2]),0)
        self.assertGreater(len(inner[2]),0)
        self.assertEqual(len(outer[1]),len(outer[0]))
    def test_sampling_maintains_source_height(self):
        ss=SourceSampler(self.synthetic())
        points=np.array([[319,1379],[320.1,1380.8],[321.5,1381.5]])
        h,g,c,uv=ss.sample(points)
        self.assertTrue(np.allclose(h,2.3,atol=1e-6))
        self.assertTrue(np.allclose(g,0,atol=1e-6))
        self.assertEqual(c.shape,(3,3));self.assertEqual(uv.shape,(3,2))
    def test_geometry_builder_samples_corners_not_cell_center(self):
        mesh=self.synthetic();modpath=os.environ.get('MOSAIC_BUILDER_PATH')
        if not modpath:
            # The existing builder is in the same repo and the test fixture can
            # be run from either the v6 directory or its canonical repo folder.
            modpath=ROOT/'build_mosaic.py'
        if not Path(modpath).is_file():self.skipTest('4cm tessera builder not installed')
        m,stats=build_patch(mesh,modpath)
        self.assertEqual(len(m.faces),100000)
        self.assertEqual(stats['source_corner_uvs_interpolated'],40000)
        self.assertIsInstance(m.visual,TextureVisuals)
        self.assertTrue(m.visual.material.baseColorTexture)
        self.assertAlmostEqual(float(m.bounds[0,0]),RECT[0]+0.00055,delta=.003)
        self.assertAlmostEqual(float(m.bounds[1,2]),RECT[3]-0.00055,delta=.003)
    def test_rejects_unknown_mesh(self):
        m=self.synthetic();m.visual=trimesh.visual.ColorVisuals(m,vertex_colors=[255,255,255,255])
        with self.assertRaises(Exception):split_source(m)
    def test_private_asset_when_explicitly_present(self):
        path=os.environ.get('NEUROCITY_PRIVATE_ARCHIVE')
        if not path:self.skipTest('No user-owned private archive on CI, as required')
        mesh,data=load_original(path)
        _,_,r=split_source(mesh)
        self.assertEqual(sha(data),'02b44285e3bc478310e3b86d939b45e90ff80359ddfc57a759bf72803556a710')
        self.assertAlmostEqual(r['removed_projected_area_m2'],16,delta=.01)

if __name__=='__main__':unittest.main()