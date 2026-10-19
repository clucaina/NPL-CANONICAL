import json
import unittest
from pathlib import Path
from data_garden import audit_batch,run,open_public_source
class SourceGardenTests(unittest.TestCase):
    def setUp(self):
        self.spec={"batch_id":"T_TEST","license":"CC BY 4.0","source_family":"INE","public_path":"database/T_TEST.json","raw_url":"https://raw.githubusercontent.com/clucaina/psicologia-politica/test/database/T_TEST.json"}
        self.row={"indicator_id":"SALARIO_M", "geo_code":"ES30","period":"2024","subgroup":"Ambos sexos","value":34410.01,"unit":"EUR/año","source_url":"https://www.ine.es/","source_id":"INE"}
        self.batch={"batch_id":"T_TEST","observations":[self.row,dict(self.row,geo_code="ES",value=29540.26)],"new_indicators":[{"indicator_id":"SALARIO_M"}]}
    def test_valid_format_never_means_auto_publication_or_clinical_validity(self):
        result=audit_batch(self.batch,self.spec)
        self.assertEqual(result["status"],"REVIEW_REQUIRED")
        self.assertEqual(result["rows"],2)
        self.assertFalse(result["ready_for_publication"])
        self.assertFalse(result["human_source_review_completed"])
    def test_rejects_duplicates_future_invalid_and_incompatible_source(self):
        from datetime import date
        batch={**self.batch,"observations":[self.row,self.row]}
        self.assertIn("duplicate_indicator_geography_period_population",audit_batch(batch,self.spec)["flags"])
        bad=dict(self.row,geo_code="ES<script>",value=True,source_url="javascript:bad",period="2099")
        report=audit_batch({**self.batch,"observations":[bad]},self.spec,date(2026,10,19))
        for flag in ("invalid_geo","non_finite_measurement","missing_https_source","future_period"):
            self.assertIn(flag,report["flags"])
        wrong=audit_batch(self.batch,{**self.spec,"batch_id":"OTHER"})
        self.assertIn("unexpected_batch_id",wrong["flags"])
    def test_source_fetch_allowlist_and_metadata_only_reports(self):
        with self.assertRaises(ValueError):
            open_public_source("https://other.example/private.json")
        report=run({"sources":[self.spec]},fetcher=lambda url:(self.batch,"a"*64))
        serialized=json.dumps(report)
        self.assertEqual(report["candidates_requiring_review"],1)
        self.assertNotIn("34410.01",serialized)
        self.assertIn("a"*64,serialized)
    def test_fails_closed_on_network_and_keeps_clean_schema(self):
        report=run({"sources":[self.spec]},fetcher=lambda url: (_ for _ in ()).throw(OSError("username:secret")))
        self.assertEqual(report["sources_with_errors"],1)
        self.assertEqual(report["candidates"][0]["status"],"SOURCE_UNAVAILABLE")
        self.assertNotIn("secret",json.dumps(report))
if __name__=="__main__":unittest.main()
