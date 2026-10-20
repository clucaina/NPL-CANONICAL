import copy
import json
import tempfile
import unittest
from pathlib import Path

from source_admission import (evaluate, validate_registry, profile_preexisting_kenney,
                              trusted_url, run)

HERE=Path(__file__).resolve().parent
SOURCE=HERE/"public_free_sources_20261020.json"

class SourceAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.registry=json.loads(SOURCE.read_text(encoding="utf8"))

    def test_01_11_real_public_metadata_sources_and_zero_imports(self):
        result=validate_registry(self.registry)
        self.assertEqual(result["discovered"],11)
        self.assertEqual(result["admitted"],0)
        self.assertEqual(result["generated_world_glbs"],0)
        self.assertTrue(all(not r["runtime_admitted"] for r in result["records"]))

    def test_02_legal_unresolved_mirror_never_admitted(self):
        x=next(x for x in self.registry["records"] if x["id"]=="kenney_third_party_catalog")
        self.assertIn("LICENSE_REVIEW_REQUIRED",evaluate(x)["reasons"])

    def test_03_no_lidar_without_sha_crs_and_verified_vertical_datum(self):
        x=next(x for x in self.registry["records"] if x["id"]=="ign_lidar_pnoa3")
        reasons=evaluate(x)["reasons"]
        for key in ("SOURCE_FILE_SHA256_MISSING","VERTICAL_DATUM_UNVERIFIED",
                    "ALICANTE_ETRS89_CRS_UNVERIFIED","SURVEY_DATE_UNVERIFIED"):
            self.assertIn(key,reasons)

    def test_04_reject_non_https_private_and_deceptive_provider_hosts(self):
        for url in ("http://github.com/NASA-AMMOS","https://github.com.evil.com/a",
                    "https://user:pw@github.com/a","https://drive.google.com/file/d/xyz",
                    "https://github.com/a?token=SECRETS", "https://github.com/a#fragment"):
            self.assertFalse(trusted_url(url),url)

    def test_05_reject_duplicate_ids(self):
        x=copy.deepcopy(self.registry)
        x["records"].append(copy.deepcopy(x["records"][0]))
        with self.assertRaisesRegex(ValueError,"Duplicate"):
            validate_registry(x)

    def test_06_must_preserve_metadata_only_and_private_firewall(self):
        for field in ("metadata_only","private_assets_never_public"):
            x=copy.deepcopy(self.registry);x[field]=False
            with self.assertRaises(ValueError):
                validate_registry(x)

    def test_07_license_scope_and_attribution_enforced(self):
        x=copy.deepcopy(self.registry)
        x["records"][0]["license_scope"]="software"
        with self.assertRaisesRegex(ValueError,"LICENSE_SCOPE_MISMATCH"):
            validate_registry(x)
        y=copy.deepcopy(self.registry["records"][0]);y["attribution"]=""
        self.assertIn("ATTRIBUTION_REQUIRED",evaluate(y)["reasons"])

    def test_08_missing_license_file_sha_cannot_be_invented(self):
        x=copy.deepcopy(self.registry["records"][3])
        x["artifact_sha256"]="f"*63
        self.assertIn("SOURCE_FILE_SHA256_INVALID",evaluate(x)["reasons"])

    def test_09_existing_legacy_catalogue_counts_locations_not_glbs(self):
        data=[
          {"id":"nature-kit/tree-palm","bytes_declared":30000,"status":"located_only"},
          {"id":"furniture-kit/bench","bytes_declared":12000,"status":"located_only"},
          {"id":"city-kit-roads/road-sign","bytes_declared":14000,"status":"located_only"},
          {"id":"foo/plant","bytes_declared":9000,"status":"loaded"}]
        p=profile_preexisting_kenney(data,limit=3)
        self.assertEqual(p["located"],4)
        self.assertEqual(p["matching_street_assets"],3)
        self.assertEqual(p["models_placed"],0)
        self.assertTrue(all(not x["admitted"] for x in p["sample"]))

    def test_10_duplicate_old_catalogue_fails_instead_of_1883_fake_models(self):
        data=[{"id":"nature-kit/tree-palm","bytes_declared":2,"status":"located_only"}]*2
        with self.assertRaisesRegex(ValueError,"Repeated"):
            profile_preexisting_kenney(data)

    def test_12_sha_and_license_never_make_metadata_only_runtime_live(self):
        tool=copy.deepcopy(next(x for x in self.registry["records"] if x["id"]=="gltf_transform"))
        tool["artifact_sha256"]="b"*64
        self.assertTrue(evaluate(tool)["eligible_for_manual_import"])
        self.assertFalse(evaluate(tool)["runtime_admitted"])

    def test_11_actual_generated_report_contains_no_binary_links(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/"report.json"
            got=run(SOURCE,out)
            self.assertEqual(got["admitted"],0)
            self.assertEqual(json.loads(out.read_text())["discovered"],11)
            self.assertNotIn("drive.google",out.read_text())

if __name__=="__main__":
    unittest.main()
