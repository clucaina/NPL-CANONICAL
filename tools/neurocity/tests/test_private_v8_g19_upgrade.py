import importlib.util
import json
import pathlib
import sys
import tempfile
import unittest
import zipfile

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
M=ROOT/'upgrade_private_v7_to_v8_g19.py'
spec=importlib.util.spec_from_file_location('g19_v8_upgrade',M)
q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)

class V8SourceUpgradeTests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup)
  self.path=pathlib.Path(self.t.name);self.base=self.path/'v7.zip';self.ci=self.path/'code.zip'
  self.script=b'world-master collision sweep NPL water'+b' '*220000
  self.base_build()
  self.ci_build()
 def base_build(self,change=None):
  files={'INTEGRACION_WEBGL_V7_REVISABLE.json':json.dumps({'status':'ASSEMBLED_NOT_WEBGL_APPROVED'}).encode(),
   'game.js':b'old world-master', 'INICIAR_LINUX_MAC.sh':b'python3 -m http.server 8766 --bind 127.0.0.1'}
  files.update(change or {})
  with zipfile.ZipFile(self.base,'w') as z:
   for k,v in files.items():z.writestr(k,v)
 def ci_build(self,change=None):
  files={'game.js':self.script,'index.html':b'<main>test</main>'}
  files.update(change or {})
  with zipfile.ZipFile(self.ci,'w') as z:
   for k,v in files.items():z.writestr(k,v)
 def verify(self):
  return q.validate_inputs(self.base,self.ci,q.SHA(self.base.read_bytes()),
                           q.SHA(self.ci.read_bytes()),q.SHA(self.script))
 def test_valid_ci_and_v7_lineage(self):
  x=self.verify()
  self.assertEqual(x['js_sha256'],q.SHA(self.script))
 def test_reject_lan_server_not_owner_only(self):
  self.base_build({'INICIAR_LINUX_MAC.sh':b'python3 -m http.server 8766'})
  with self.assertRaisesRegex(ValueError,'loopback'):self.verify()
 def test_reject_already_built_v8(self):
  self.base_build({q.V8_AUDIT:b'{}'})
  with self.assertRaisesRegex(ValueError,'already exists'):self.verify()
 def test_reject_unapproved_predecessor(self):
  self.base_build({q.V7_AUDIT:json.dumps({'status':'APPROVED'}).encode()})
  with self.assertRaisesRegex(ValueError,'predecessor'):self.verify()
 def test_reject_source_artifact_with_model(self):
  self.ci_build({'private.glb':b'glTF'})
  with self.assertRaisesRegex(ValueError,'noncode'):self.verify()
 def test_reject_non_sweep_runtime_even_with_signed_hash(self):
  self.script=b'world-master collision NPL water'+b' '*220000
  self.ci_build()
  with self.assertRaisesRegex(ValueError,'G19 collision sweep'):self.verify()
 def test_wrong_checkpoint_hash_never_bypassed(self):
  with self.assertRaisesRegex(ValueError,'owner V7 source SHA'):
   q.validate_inputs(self.base,self.ci,'f'*64,q.SHA(self.ci.read_bytes()),q.SHA(self.script))
 def test_source_artifact_commit_pin_matches_G19_sweep_PR46(self):
  self.assertEqual(q.SOURCE_RUN,'39430608426')
  self.assertEqual(q.CODE_JS,'722b6b0bde72cfc347a5b101c5d6fac86db25f647b6ca3bedd7ec823f79b905d')

if __name__=='__main__':unittest.main()
