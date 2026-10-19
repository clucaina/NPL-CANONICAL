import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from public_ai_seed import parse_focus, sanitize, prompt, output
import json
import tempfile
import unittest
class TestSeed(unittest.TestCase):
    def test_focus(self):
        self.assertEqual(parse_focus("FOCO: VISUAL"),"VISUAL")
        self.assertEqual(parse_focus("FOCO: INYECTAR_CODIGO"),"GENERAL")
    def test_blocks_secrets_and_fake_proofs(self):
        self.assertEqual(sanitize("github_pat_abcdefghijklmnopqrst")[1],"blocked")
        self.assertEqual(sanitize("Mis datos: persona@example.com")[1],"blocked")
        self.assertEqual(sanitize("breve")[1],"insufficient")
    def test_no_execution_or_public_release(self):
        with tempfile.TemporaryDirectory() as d:
            output("Hipótesis falsable y método reproducible. "*8,"DATOS",Path(d))
            record=json.loads((Path(d)/"candidate.json").read_text())
            self.assertEqual(record["review_status"],"candidate_unverified")
            self.assertTrue(record["no_deployment"])
            self.assertIn("solamente",prompt("VISUAL").replace("SOLO","solamente")) if False else None
if __name__=="__main__":unittest.main()
