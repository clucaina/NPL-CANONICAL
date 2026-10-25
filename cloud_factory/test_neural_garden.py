import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from neural_garden import ROOTS, EDGES, transmit, choose_turns, assemble, save

class NeuralGardenTests(unittest.TestCase):
    def test_roots_isolated_and_npl_conflictometro_inside_neurocity(self):
        names=[p["id"] for p in ROOTS]
        self.assertEqual(len(names),len(set(names)))
        self.assertNotIn("npl",names)
        self.assertNotIn("conflictometro",names)
        neu=next(p for p in ROOTS if p["id"]=="neurocity")
        self.assertEqual(neu["modules"],["NPL","Conflictómetro"])
        self.assertNotEqual(next(p for p in ROOTS if p["id"]=="apj")["id"],
                            next(p for p in ROOTS if p["id"]=="sicnar")["id"])
    def test_synapses_deny_all_until_explicit_approval(self):
        for edge in EDGES:
            self.assertFalse(edge["enabled"])
            with self.assertRaises(PermissionError):
                transmit(edge,{"edge_type":edge["type"],"source_id":edge["from"],"target_id":edge["to"]})
    def test_approved_metadata_only_even_after_enabling_one_edge(self):
        e=EDGES[0];before=e["enabled"];e["enabled"]=True
        valid={"edge_type":e["type"],"source_id":e["from"],"target_id":e["to"],
               "review_status":"APPROVED_PUBLIC_METADATA","observation_hash":hashlib.sha256(b"public-only").hexdigest(),
               "public_citation":"https://doi.org/10.1234/abc"}
        try:
            self.assertEqual(transmit(e,valid),valid)
            with self.assertRaises(PermissionError):transmit(e,{**valid,"clinical_case":"PRIVATE"})
            with self.assertRaises(PermissionError):transmit(e,{**valid,"review_status":"DRAFT"})
            with self.assertRaises(PermissionError):transmit(e,{**valid,"public_citation":"file:///etc/passwd"})
            with self.assertRaises(PermissionError):transmit(e,{**valid,"observation_hash":"NOT-A-HASH"})
        finally:e["enabled"]=before
    def test_only_public_sources_are_queried_and_ci_is_not_a_product_certificate(self):
        seen=[]
        def evidence(repo):
            seen.append(repo)
            return [{"name":"QA only","status":"completed","conclusion":"success",
                     "time":"2026-10-19T13:00:00Z","url":"https://github.com/clucaina/NPL-CANONICAL/actions/runs/100"}]
        r=assemble(fetcher=evidence)
        self.assertEqual(set(seen),{"clucaina/NPL-CANONICAL","clucaina/psicologia-politica"})
        self.assertFalse(any(x["achievements_verified"] for x in r["roots"]))
        self.assertEqual(r["safety"]["client_records_read"],0)
        self.assertEqual(r["safety"]["cross_project_signals_enabled"],0)
        self.assertTrue(any(x["status"]=="NEEDS_PRIVATE_CANONICAL_SOURCE" for x in r["roots"]))
    def test_unavailable_github_never_claims_success(self):
        r=assemble(fetcher=lambda _:(_ for _ in ()).throw(OSError("offline")))
        self.assertEqual(r["roots"][0]["status"],"SOURCE_UNREACHABLE")
        self.assertEqual(len(r["active_turns"]),2)
    def test_failed_tests_attention_and_aging_fairness(self):
        s={p["id"]:{"status":"CHECKS_FAILED" if p["id"]=="psicologia_politica" else "CI_PRESENT_NOT_PRODUCT_VALIDATION"} for p in ROOTS}
        turn=choose_turns(s,budget=2,previous={"psicologia_politica":4,"neurocity":3})
        self.assertEqual(turn[0]["id"],"psicologia_politica")
        self.assertEqual(turn[0]["turn"],"VERIFY_FAILURE")
        self.assertEqual(len({x["id"] for x in turn}),2)
    def test_public_pulse_outputs_evidence_without_commenting_or_emailing(self):
        workflow=(Path(__file__).parent.parent/".github"/"workflows"/"neural-garden.yml").read_text(encoding="utf-8")
        self.assertIn("SILENT_EVIDENCE_DELIVERY=WORKFLOW_SUMMARY_AND_ARTIFACTS_ONLY",workflow)
        self.assertIn("actions/upload-artifact@v4",workflow)
        self.assertIn("garden-output/status.md",workflow)
        self.assertNotIn("createComment",workflow)
        self.assertNotIn("issues: write",workflow)
        self.assertNotIn("sendmail",workflow)
        self.assertNotIn("gmail",workflow.casefold())
    def test_export_is_standalone_and_escapes_html_data(self):
        report=assemble(fetcher=lambda _:[])
        report["roots"][0]["title"]='</script><img src=x onerror=alert(1)>'
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);t=base/"template.html"
            t.write_text('<script type="application/json">__GARDEN_DATA__</script>',encoding="utf-8")
            save(report,base/"output",t)
            body=(base/"output"/"index.html").read_text()
            self.assertNotIn("</script><img",body)
            self.assertIn("\\u003c",body)
            self.assertTrue((base/"output"/"status.md").is_file())
            self.assertIn("roots",json.loads((base/"output"/"snapshot.json").read_text()))
if __name__=="__main__":unittest.main()
