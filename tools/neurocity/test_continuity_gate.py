import importlib.util
import tempfile,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('continuity_gate',Path(__file__).with_name('continuity_gate.py'))
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
class ContinuityTests(unittest.TestCase):
 def make(self,root):
  for rel,needles in mod.CONTRACTS.values():
   p=root/rel;p.parent.mkdir(parents=True,exist_ok=True)
   p.write_text('\n'.join(needles)+'\n',encoding='utf8')
 def test_unchanged_cross_chat_source_contracts_pass(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);self.make(p)
   audit=mod.verify(p)
   self.assertEqual(audit['failed'],0)
   self.assertEqual(audit['passed'],len(mod.CONTRACTS)+1)
   self.assertTrue(audit['source_only'])
 def test_losing_one_module_fails_not_merely_warns(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);self.make(p)
   rel=mod.CONTRACTS['G13_signed_walking_physics'][0]
   (p/rel).unlink()
   audit=mod.verify(p)
   self.assertEqual(audit['failed'],1)
   self.assertEqual(next(x for x in audit['checks_by_capability']
      if x['capability']=='G13_signed_walking_physics')['status'],'MISSING_SOURCE')
 def test_public_repo_cannot_store_original_private_glbs(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);self.make(p)
   (p/'demos/npl-world/visual_viewer/world-master').mkdir()
   audit=mod.verify(p)
   self.assertEqual(audit['failed'],1)
   self.assertEqual(audit['checks_by_capability'][-1]['status'],'PRIVATE_ARCHIVE_IN_PUBLIC_SOURCE')
if __name__=='__main__':unittest.main()
