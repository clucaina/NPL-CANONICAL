import importlib.util
import hashlib,json,tempfile,unittest
from pathlib import Path
from zipfile import ZipFile
spec=importlib.util.spec_from_file_location('recover_worldmaster_sidecars',
 Path(__file__).with_name('recover_worldmaster_sidecars.py'))
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

def make_fixture(folder,tampered=False):
    original=Path(folder)/'original.zip'
    ground={'tile':'r02_c00','step':2.0,'count':251,
      'surface':[[1]*251 for _ in range(251)],
      'height':[[2.4]*251 for _ in range(251)]}
    data={
      'geo/data/physical_r02_c00.json':json.dumps(ground).encode(),
      'assets/prefabs/Farola_Globo_Simple_4m.glb':b'glTF' +b'INERT_SYNTHETIC_BINARY'
    }
    sources=[{'file':path,'size':len(raw),
              'sha256':hashlib.sha256(raw).hexdigest()} for path,raw in data.items()]
    if tampered:sources[0]['sha256']='0'*64
    with ZipFile(original,'w') as z:
      z.writestr('NEUROCITY_WORLD_MASTER/source-hashes.json',json.dumps(sources))
      for path,raw in data.items():
        z.writestr('NEUROCITY_WORLD_MASTER/'+path,raw)
    target=Path(folder)/'local-world-master'
    target.mkdir()
    (target/'manifest.json').write_text(json.dumps({'asset_hashes':{}}))
    return original,target

class LocalSidecarRecovery(unittest.TestCase):
 def test_only_source_verified_files_copied_without_change(self):
  with tempfile.TemporaryDirectory() as t:
   src,dst=make_fixture(t)
   out=mod.recover(src,dst)
   self.assertEqual(out['files_copied_to_local_only'],2)
   self.assertEqual(out['collision_grid_count'],1)
   self.assertFalse(out['redistribution_approved'])
   self.assertEqual(out['original_files_modified'],0)
   self.assertEqual((dst/'assets/prefabs/Farola_Globo_Simple_4m.glb').read_bytes(),
                    b'glTF'+b'INERT_SYNTHETIC_BINARY')
 def test_metadata_only_never_materializes_binary(self):
  with tempfile.TemporaryDirectory() as t:
   src,dst=make_fixture(t)
   out=mod.recover(src,dst,metadata_only=True)
   self.assertEqual(out['files_copied_to_local_only'],0)
   self.assertFalse((dst/'assets').exists())
 def test_tampering_or_private_path_fails_closed(self):
  with tempfile.TemporaryDirectory() as t:
   src,dst=make_fixture(t,tampered=True)
   with self.assertRaises(ValueError):mod.recover(src,dst)
  for name in ['geo/data/patient_secret.json',
               'assets/people/worker_face.glb','../../private.glb',
               'assets/prefabs/malware.glb']:
   self.assertFalse(mod.permitted(name))
if __name__=='__main__':unittest.main()
