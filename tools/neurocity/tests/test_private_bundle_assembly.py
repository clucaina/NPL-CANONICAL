import importlib.util
import json
import pathlib
import tempfile
import unittest
import warnings
import zipfile

P=pathlib.Path(__file__).resolve().parents[1]/'private_bundle_assembly.py'
spec=importlib.util.spec_from_file_location('private_bundle_assembly',P)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class TestPrivateAssembler(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory()
  self.root=pathlib.Path(self.tmp.name)
  self.base=self.root/'original.zip'
  self.compiled=self.root/'app.zip'
  self.output=self.root/'output.zip'
  self.model=b'glTF'+b'\0'*256
  self.manifest={'schema':'neurocity.local-worldmaster-tiles.v1',
   'public_redistribution_allowed':False,'tiles':[{'id':'r02_c00',
   'assets':[{'path':'assets/selected/a.glb','sha256':m.SHA(self.model),'bytes':len(self.model)}]}]}
  self.base_build()
  self.compiled_build()
 def tearDown(self):self.tmp.cleanup()
 def base_build(self):
  with zipfile.ZipFile(self.base,'w') as z:
   for path,data in {
    'world-master/manifest.json':json.dumps(self.manifest).encode(),
    'world-master/assets/selected/a.glb':self.model,
    'world-master/manifest_V50_before_surgical_candidate.json':b'{}',
    'assets/alicante.glb':self.model,
    'game.js':b'world-master original',
    'index.html':b'old', 'assets/original.txt':b'preserved'
   }.items():z.writestr(path,data)
 def compiled_build(self,extra=None):
  with zipfile.ZipFile(self.compiled,'w') as z:
   z.writestr('game.js',b'var v="world-master NPL water";'+b' '*210000)
   z.writestr('index.html',b'new HTML')
   for path,data in (extra or {}).items():z.writestr(path,data)
 def test_original_bytes_preserved_and_exact_runtime_replaced(self):
  audit=m.assemble(self.base,self.compiled,self.output)['audit']
  self.assertEqual(audit['manifest_model_records_verified'],1)
  self.assertFalse(audit['runtime_compatibility_verified_in_browser'])
  with zipfile.ZipFile(self.base) as a,zipfile.ZipFile(self.compiled) as p,zipfile.ZipFile(self.output) as b:
   for name in a.namelist():
    self.assertEqual(b.read(name),p.read(name) if name in ('game.js','index.html') else a.read(name))
 def test_determinism_across_distinct_output_times(self):
  first=m.assemble(self.base,self.compiled,self.output)
  second=m.assemble(self.base,self.compiled,self.root/'second.zip')
  self.assertEqual(first['sha256'],second['sha256'])
 def test_private_local_launchers_are_sanitized(self):
  with zipfile.ZipFile(self.base) as z: files={k:z.read(k) for k in z.namelist()}
  files['INICIAR_WINDOWS.bat']=b'@echo off\r\npy -3 -m http.server 8766\r\n'
  files['INICIAR_LINUX_MAC.sh']=b'#!/bin/sh\npython3 -m http.server 8766\n'
  with zipfile.ZipFile(self.base,'w') as z:
   for name,data in files.items(): z.writestr(name,data)
  report=m.assemble(self.base,self.compiled,self.output)['audit']
  self.assertEqual(len(report['security_fixed_local_only_launchers']),2)
  with zipfile.ZipFile(self.output) as z:
   for name in ['INICIAR_WINDOWS.bat','INICIAR_LINUX_MAC.sh']:
    self.assertIn(b'--bind 127.0.0.1',z.read(name))
 def test_tampered_model_fails(self):
  self.manifest['tiles'][0]['assets'][0]['sha256']='f'*64;self.base_build()
  with self.assertRaisesRegex(ValueError,'hash/size'):
   m.assemble(self.base,self.compiled,self.output)
 def test_missing_model_fails(self):
  self.manifest['tiles'][0]['assets'][0]['path']='assets/selected/missing.glb';self.base_build()
  with self.assertRaisesRegex(ValueError,'Missing referenced GLBs'):
   m.assemble(self.base,self.compiled,self.output)
 def test_public_or_unexpected_license_fails(self):
  self.manifest['public_redistribution_allowed']=True;self.base_build()
  with self.assertRaisesRegex(ValueError,'PRIVATE'):
   m.assemble(self.base,self.compiled,self.output)
 def test_traversal_archive_rejected(self):
  self.compiled_build({'../../keys.txt':b'leak'})
  with self.assertRaisesRegex(ValueError,'Invalid archive path'):
   m.assemble(self.base,self.compiled,self.output)
 def test_model_in_public_source_artifact_rejected(self):
  self.compiled_build({'private.glb':self.model})
  with self.assertRaisesRegex(ValueError,'Unexpected compiled payload'):
   m.assemble(self.base,self.compiled,self.output)
 def test_unsafe_in_place_overwrite_rejected(self):
  with self.assertRaisesRegex(ValueError,'overwrite'):
   m.assemble(self.base,self.compiled,self.base)
 def test_duplicate_names_rejected(self):
  with zipfile.ZipFile(self.compiled,'w') as z:
   z.writestr('game.js',b'world-master NPL water'+b' '*210000)
   z.writestr('index.html',b'html')
   with warnings.catch_warnings():
    warnings.simplefilter('ignore');z.writestr('index.html',b'html2')
  with self.assertRaisesRegex(ValueError,'Duplicate'):
   m.assemble(self.base,self.compiled,self.output)
 def test_non_runtime_compiled_artifact_rejected(self):
  with zipfile.ZipFile(self.compiled,'w') as z:
   z.writestr('game.js',b'foo');z.writestr('index.html',b'html')
  with self.assertRaisesRegex(ValueError,'lacks expected'):
   m.assemble(self.base,self.compiled,self.output)
if __name__=='__main__':unittest.main()
