import importlib.util
import pathlib
import unittest
MODULE=pathlib.Path(__file__).resolve().parents[1]/"integration_rehearsal.py"
spec=importlib.util.spec_from_file_location("neurocity_integration_rehearsal",MODULE)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class TestRehearsalSecurity(unittest.TestCase):
    def test_private_model_never_marked_source_only(self):
        self.assertIn("world-master/assets/source.glb",m.suspicious_paths(["world-master/assets/source.glb"]))
        self.assertEqual([],m.suspicious_paths(["app.js","tests/new.test.mjs",".github/workflows/qa.yml"]))
    def test_sensitive_paths_flagged(self):
        self.assertIn("data/peritado123.json",m.suspicious_paths(["data/peritado123.json"]))
        self.assertIn("data/clinical-record.json",m.suspicious_paths(["data/clinical-record.json"]))
    def test_references_are_only_known_read_only_prs(self):
        self.assertEqual(["29","36","33"],[num for _,num in m.CANDIDATES])
    def test_no_untrusted_shell_or_push(self):
        source=MODULE.read_text(encoding="utf8")
        self.assertNotIn("shell=True",source)
        self.assertNotIn('"push"',source)

if __name__=="__main__":
    unittest.main()
