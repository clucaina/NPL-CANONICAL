"""Independent release gates for generated Explanada 3D patch."""
import hashlib,json,math,subprocess,sys,tempfile,unittest
from pathlib import Path
import numpy as np
import trimesh
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_mosaic import N, SIZE_M, TESSERA_M, kind, texture_image
ROOT=Path(__file__).parent/'asset'

class TestMosaic(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m=json.loads((ROOT/'mosaic_manifest.json').read_text())
        cls.near=trimesh.load(ROOT/'explanada_4x4m_near_real_geometry.glb',force='scene')
        cls.far=trimesh.load(ROOT/'explanada_4x4m_far_textured.glb',force='scene')
    def test_glb2_parseable_nonempty(self):
        for k in ('near','far'):
            data=(ROOT/('explanada_4x4m_near_real_geometry.glb' if k=='near' else 'explanada_4x4m_far_textured.glb')).read_bytes()
            self.assertEqual(data[:4],b'glTF');self.assertEqual(int.from_bytes(data[4:8],'little'),2)
            self.assertEqual(int.from_bytes(data[8:12],'little'),len(data))
            self.assertTrue(any(len(m.faces)>0 for m in getattr(self,k).geometry.values()))
    def test_real_modelled_tesserae_faces(self):
        self.assertEqual(self.m['near']['tesserae'],10000)
        mesh=self.near.geometry['tesserae_4cm_individual_extruded']
        self.assertEqual(len(mesh.faces),100000)
        self.assertEqual(len(mesh.vertices),200000)
        self.assertTrue(mesh.visual.kind=='vertex')
        self.assertGreaterEqual(float(mesh.bounds[0,1]),0)
        self.assertLess(float(mesh.bounds[1,1]),.006)
        self.assertAlmostEqual(float(mesh.bounds[1,0]),4-GROUT_APPROX,places=2)
    def test_actual_material_texture_far(self):
        self.assertEqual(sum(len(m.faces) for m in self.far.geometry.values()),2)
        mesh=next(iter(self.far.geometry.values()))
        self.assertTrue(mesh.visual.kind=='texture')
        self.assertEqual(mesh.visual.material.baseColorTexture.size,(2400,2400))
    def test_color_palette_not_monochrome(self):
        img=Image.open(ROOT/'explanada_diffuse_original_generated.png')
        sample=[img.getpixel((int((i+.5)*24),int((j+.5)*24))) for i in range(100) for j in range(100)]
        self.assertGreater(len(set(sample)),120)
        self.assertTrue(all(0<=x<=255 for rgb in sample for x in rgb))
    def test_repeatability_x_and_z_edge(self):
        for t in [0,.03,.2,.5,1.1,2.3,3.97]:
            self.assertEqual(kind(0,t),kind(4,t))
            self.assertEqual(kind(t,0),kind(t,4))
    def test_no_source_photo_embedded(self):
        self.assertFalse(self.m['external_images_copied'])
        self.assertFalse(self.m['publish_allowed'])
        self.assertFalse(self.m['visual_fidelity_approved'])
        self.assertFalse(self.m['world_master_georeference_verified'])
    def test_manifest_sha256_bytes(self):
        for name,record in self.m['files'].items():
            p=ROOT/name
            self.assertEqual(p.stat().st_size,record['bytes'])
            self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),record['sha256'])
    def test_texture_recreated_identically(self):
        expected=(ROOT/'explanada_diffuse_original_generated.png').read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'test.png'
            texture_image(2400).save(p,optimize=True)
            self.assertEqual(p.read_bytes(),expected)

GROUT_APPROX=.0011
if __name__=='__main__':unittest.main(verbosity=2)