import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
import sys
sys.path.insert(0,str(Path(__file__).parent))
import oci_supervisor as s

class SupervisorTests(unittest.TestCase):
    def test_focus_only_known_words(self):
        self.assertEqual(s.parse_focus("FOCO: VISUAL"),"VISUAL")
        self.assertEqual(s.parse_focus("FOCO: BORRAR_TODO"),"GENERAL")
        self.assertEqual(s.parse_focus("random\nFOCO: DATOS\n"),"DATOS")
    def test_repeat_rotates_roles_and_persists_without_model(self):
        with tempfile.TemporaryDirectory() as td:
            def read(name):return ("SEGURIDAD","2026-10-19T10:00:00Z","https://github.com/example")
            a=s.once(home=Path(td),reader=read,model=lambda prompt:None)
            b=s.once(home=Path(td),reader=read,model=lambda prompt:None)
            self.assertEqual(len(a),2)
            self.assertNotEqual(a[0]["shift"],b[0]["shift"])
            self.assertEqual(a[0]["state"],"NO_MODEL_CONFIGURED")
            db=sqlite3.connect(str(Path(td)/"factory.sqlite3"))
            self.assertEqual(db.execute("SELECT COUNT(*) FROM findings").fetchone()[0],4)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM projects").fetchone()[0],2)
            self.assertTrue((Path(td)/"last_run.json").is_file())
    def test_explicitly_unverified_model_drafts(self):
        with tempfile.TemporaryDirectory() as td:
            a=s.once(Path(td),reader=lambda name:("VISUAL","",""),model=lambda prompt:"DRAFT")
            self.assertEqual(a[0]["state"],"PROPOSAL_UNVERIFIED_REQUIRES_REVIEW")
            db=sqlite3.connect(str(Path(td)/"factory.sqlite3"))
            self.assertEqual(db.execute("SELECT content FROM findings LIMIT 1").fetchone()[0],"DRAFT")

if __name__=="__main__":unittest.main()
