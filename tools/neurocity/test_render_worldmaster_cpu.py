import importlib.util
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

file=Path(__file__).with_name("render_worldmaster_cpu.py")
spec=importlib.util.spec_from_file_location("render_worldmaster_cpu",file)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class OfflineSourceRenderTests(unittest.TestCase):
 def test_can_select_only_original_3d_and_no_people(self):
  report={"schema":"neurocity.local-worldmaster-tiles.v1",
          "public_redistribution_allowed":False,
          "tiles":[{"id":"r02_c00","assets":[
              {"role":"architecture","path":"assets/selected/arch.glb"},
              {"role":"palm_variants","path":"assets/selected/palm.glb"},
              {"role":"avatar","path":"assets/selected/lucia_face.glb"}]}]}
  selected=mod.select_qa_assets(report)
  self.assertEqual(len(selected),2)
  self.assertEqual({x["role"] for x in selected},{"architecture","palm_variants"})
  report["public_redistribution_allowed"]=True
  with self.assertRaises(ValueError):mod.select_qa_assets(report)
 def test_verifies_real_archive_bytes_before_cpu_render(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);sample=root/"assets/selected/house.glb"
   sample.parent.mkdir(parents=True)
   sample.write_bytes(b'glTF-FIXTURE')
   item={"path":"assets/selected/house.glb","bytes":sample.stat().st_size,
         "sha256":hashlib.sha256(sample.read_bytes()).hexdigest()}
   self.assertEqual(mod.audit_file(root,item),sample)
   sample.write_bytes(b'glTF-TAMPERED')
   with self.assertRaises(ValueError):mod.audit_file(root,item)
 def test_forbid_private_models_and_uri_path_escape(self):
  with tempfile.TemporaryDirectory() as t:
   for p in ["assets/../../client.glb","https://example.org/assets/person.glb",
             "assets/selected/patient_face.glb","assets/selected/avatar.glb"]:
    with self.assertRaises((ValueError,IndexError)):mod.audit_file(Path(t),{"path":p,"bytes":5,"sha256":"x"*64})

if __name__=="__main__":unittest.main()
