import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[0] / "produccion"
MOD = BASE / "exportar_guiones.py"
spec = importlib.util.spec_from_file_location("exportar_guiones", MOD)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
DATA = json.loads((BASE / "guiones-audiovisuales.json").read_text(encoding="utf-8"))

class VideoTeachingExportsTest(unittest.TestCase):
    def test_export_source_contract(self):
        mod.validate(DATA)
        self.assertEqual(len(DATA["videos"]), 2)
        self.assertEqual(sum(len(x["scenes"]) for x in DATA["videos"]), 12)

    def test_dry_run_is_pure(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "never-created"
            values = mod.convert(DATA, output, dry_run=True)
            self.assertEqual(len(values), 2)
            self.assertFalse(output.exists())

    def test_generates_real_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            manifest = mod.convert(DATA, out)
            self.assertEqual(len(manifest), 2)
            for video in manifest:
                for f in video["files"]:
                    self.assertTrue((out / f).is_file(), f)
                    self.assertGreater((out / f).stat().st_size, 80)
            self.assertIn("00:00:00,000", (out / "tasa-base.srt").read_text(encoding="utf-8"))
            self.assertIn("00:01:10,000", (out / "tasa-base.srt").read_text(encoding="utf-8"))

    def test_invalid_duration_rejected(self):
        broken = copy.deepcopy(DATA)
        broken["videos"][0]["scenes"][0]["seconds"] = -1
        with self.assertRaisesRegex(ValueError, "Duración"):
            mod.validate(broken)

    def test_timing_mismatch_rejected(self):
        broken = copy.deepcopy(DATA)
        broken["videos"][0]["target_seconds"] = 12
        with self.assertRaisesRegex(ValueError, "duración total"):
            mod.validate(broken)

    def test_formula_sanitization(self):
        self.assertEqual(mod.sanitized_csv("=SUM(A1:B2)"), "'=SUM(A1:B2)")
        self.assertEqual(mod.sanitized_csv("@x"), "'@x")
        self.assertEqual(mod.sanitized_csv("Una fuente"), "Una fuente")

if __name__ == "__main__":
    unittest.main()
