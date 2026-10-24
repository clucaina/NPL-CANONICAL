"""Only synthetic records are used: no originals, people, user photographs or weights."""
import hashlib
import math
import struct
import unittest

from splat_candidate_gate import inspect_splat

SAMPLE = struct.pack("<6f8B", 1., 2., 3., .1, .2, .3, 200, 100, 70, 255, 128, 128, 128, 255)


def manifest(data=SAMPLE):
    return {
        "splat_sha256": hashlib.sha256(data).hexdigest(),
        "format": "antimatter15-splat32",
        "source_code_repo": "https://github.com/localai-org/free-splatter.cpp",
        "source_image_sha256": ["1" * 64, "2" * 64],
        "rights_approved": True,
        "model_license_reviewed": True,
        "model_sha256": "3" * 64,
    }


class SplatCandidateGateTests(unittest.TestCase):
    def test_01_valid_synthetic_splat_is_only_structural(self):
        result = inspect_splat(SAMPLE, manifest())
        self.assertEqual(result["status"], "STRUCTURAL_ONLY_NOT_CITY_ASSET")
        self.assertEqual(result["splat_count"], 1)
        for key in ("runtime_admitted", "geolocation_verified", "collision_mesh_verified",
                    "photorealism_verified", "browser_render_verified", "license_verified",
                    "input_rights_verified"):
            self.assertIs(result[key], False)
        self.assertNotIn("positions", result)

    def test_02_bad_format_and_missing_original_are_rejected(self):
        for raw in (b"", b"glTF", SAMPLE + b"x", b"x" * 33):
            self.assertEqual(inspect_splat(raw, manifest(raw))["status"], "REJECTED")
        self.assertIn("MISSING_EVIDENCE_MANIFEST", inspect_splat(SAMPLE, None)["reasons"])

    def test_03_nan_infinity_and_invalid_scales_are_rejected(self):
        for numbers in ((math.nan, 2., 3., .1, .2, .3),
                        (1., 2., 3., 0., .2, .3),
                        (1., 2., 3., -1., .2, .3),
                        (1., 2., 3., math.inf, .2, .3)):
            raw = struct.pack("<6f8B", *numbers, 200, 100, 70, 255, 128, 128, 128, 255)
            self.assertEqual(inspect_splat(raw, manifest(raw))["status"], "REJECTED")

    def test_04_hash_rights_weights_and_claims_fail_closed(self):
        for key, value in (("splat_sha256", "0" * 64),
                           ("rights_approved", False),
                           ("model_license_reviewed", False),
                           ("source_image_sha256", ["1" * 64, "1" * 64]),
                           ("model_sha256", None),
                           ("source_code_repo", "https://github.com.evil.net/fake"),
                           ("runtime_admitted", True),
                           ("published", True),
                           ("collision_mesh_verified", True)):
            m = manifest()
            m[key] = value
            self.assertEqual(inspect_splat(SAMPLE, m)["status"], "REJECTED", key)

    def test_05_invisible_data_is_not_promoted(self):
        raw = SAMPLE[:27] + bytes([0]) + SAMPLE[28:]
        result = inspect_splat(raw, manifest(raw))
        self.assertIn("NO_VISIBLE_SPLAT", result["reasons"])
        self.assertEqual(result["generated_world_glbs"], 0)


if __name__ == "__main__":
    unittest.main()
