import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path

PATH=Path(__file__).with_name("cross_chat_lineage.py")
spec=importlib.util.spec_from_file_location("cross_chat_lineage",PATH)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def run(repo,*args):
    return subprocess.run(["git","-C",str(repo),*args],capture_output=True,
                          text=True,check=True).stdout.strip()
class SourceLineageTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.repo=Path(self.tmp.name)
        run(self.repo,"init","-b","main")
        run(self.repo,"config","user.email","ci@example.invalid")
        run(self.repo,"config","user.name","CI fixture")
        for path in module.REQUIRED_AT_LEAST_ONE.values():
            f=self.repo/path;f.parent.mkdir(parents=True,exist_ok=True)
            f.write_text("real fixture code\n",encoding="utf-8")
        run(self.repo,"add",".");run(self.repo,"commit","-m","base")
        self.base=run(self.repo,"rev-parse","HEAD")
        run(self.repo,"update-ref","refs/remotes/origin/main",self.base)
    def tearDown(self):
        self.tmp.cleanup()
    def make_branch(self,name,files):
        run(self.repo,"checkout","-b",name,"main")
        for path,content in files.items():
            f=self.repo/path;f.parent.mkdir(parents=True,exist_ok=True)
            f.write_text(content)
        run(self.repo,"add",".");run(self.repo,"commit","-m","one feature")
        sha=run(self.repo,"rev-parse","HEAD")
        run(self.repo,"update-ref","refs/remotes/origin/"+name,sha)
        run(self.repo,"checkout","main")
        return sha
    def test_detects_real_current_heads_and_overlap_without_merging(self):
        name1="feat/v7"
        name2="feat/cadastre"
        self.make_branch(name1,{"demos/npl-world/visual_viewer/app.js":"v7\n"})
        self.make_branch(name2,{"demos/npl-world/visual_viewer/app.js":"catastro\n",
                                "tools/neurocity/catastro_parts.py":"verify\n"})
        sources=(("g19",name1,True),("cadastre",name2,True))
        report=module.audit(self.repo,sources)
        self.assertFalse(report["required_source_gaps"])
        self.assertEqual(report["overlaps"][0]["overlapping_paths"],
                         ["demos/npl-world/visual_viewer/app.js"])
        self.assertTrue(report["no_merges_or_deployments"])
        self.assertFalse(report["semantic_integration_certified"])
        self.assertEqual(run(self.repo,"rev-parse","HEAD"),self.base)
        self.assertIn("requieren decisión",module.markdown(report))
    def test_required_missing_source_fails_closed_but_optional_is_traceable(self):
        sources=(("exists","feat/unknown",True),("optional","feat/future",False))
        report=module.audit(self.repo,sources)
        self.assertIn("exists",report["required_source_gaps"])
        self.assertNotIn("optional",report["required_source_gaps"])
        self.assertFalse(report["required_sources_available"])
    def test_original_binary_gml_is_never_allowed_into_public_candidate(self):
        self.make_branch("feat/raw-gml",{"tools/neurocity/data.gml":"unsafe source data"})
        with self.assertRaisesRegex(RuntimeError,"privacy-sensitive"):
            module.audit(self.repo,(("secret","feat/raw-gml",True),))
    def test_harmless_private_named_code_does_not_trigger_asset_block(self):
        self.make_branch("feat/assembly",{"tools/neurocity/private_playable_review.py":"source-only"})
        report=module.audit(self.repo,(("assembler","feat/assembly",True),))
        self.assertTrue(report["required_sources_available"])
        self.assertEqual(report["sources"][0]["state"],"FOUND_SOURCE")
    def test_source_name_injection_rejected(self):
        with self.assertRaisesRegex(ValueError,"unsafe source"):
            module.audit(self.repo,(("evil","x;touch /tmp/harm",True),))

if __name__=="__main__":
    unittest.main()
