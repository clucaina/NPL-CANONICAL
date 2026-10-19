import importlib.util
import json
import struct
import unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location("fetch_cc0_glb",Path(__file__).with_name("fetch_cc0_glb.py"))
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def synthetic_glb(index_count=6):
    scene={"asset":{"version":"2.0"},"meshes":[{"primitives":[{"indices":0}]}],"accessors":[{"count":index_count}]}
    raw=json.dumps(scene).encode()
    raw+=b' ' *((-len(raw))%4)
    return b'glTF'+struct.pack('<II',2,20+len(raw))+struct.pack('<I4s',len(raw),b'JSON')+raw

class TestVerified3DAcquisition(unittest.TestCase):
    def test_safe_hosts(self):
        self.assertTrue(module.permitted('https://dl.polyhaven.org/foo.glb'))
        for uri in ['http://dl.polyhaven.org/a.glb','https://dl.polyhaven.org.evil.test/a.glb',
                    'https://user:pass@dl.polyhaven.org/a.glb','https://dl.polyhaven.org/a.glb#section',
                    'https://evil.test/asset.glb']:
            self.assertFalse(module.permitted(uri),uri)
    def test_nested_file_resolution(self):
        tree={'1k':{'gltf':{'url':'https://dl.polyhaven.org/model.glb','size':2020}},
              '4k':{'glb':{'url':'https://evil.test/file.glb','size':2020}},
              'oversized':{'glb':{'url':'https://dl.polyhaven.org/big.glb','size':100_000_000}},
              'other':{'blend':{'url':'https://dl.polyhaven.org/model.blend','size':4000}}}
        results=module.collect_glbs(tree)
        self.assertEqual(len(results),1)
        self.assertEqual(results[0]['size'],2020)
    def test_mesh_validation(self):
        self.assertEqual(module.validate_glb(synthetic_glb())['triangles_indexed'],2)
        with self.assertRaises(ValueError):module.validate_glb(b'bad-format')
        with self.assertRaises(ValueError):module.validate_glb(synthetic_glb(1_000_000))
        corrupt=bytearray(synthetic_glb());corrupt[8:12]=(55).to_bytes(4,'little')
        with self.assertRaises(ValueError):module.validate_glb(bytes(corrupt))

if __name__=='__main__': unittest.main()
