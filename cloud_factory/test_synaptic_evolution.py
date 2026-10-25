import copy
import unittest

from synaptic_evolution import (
    SCHEMA,EXPERIMENTS,MAX_HISTORY,MAX_CANDIDATES,
    evolve,markdown,_observed_run
)

RUN="https://github.com/clucaina/NPL-CANONICAL/actions/runs/40188427617"
PP="https://github.com/clucaina/psicologia-politica/actions/runs/40188427619"

def job(name,url,conclusion="success",when="2026-10-25T11:20:09Z"):
    return {"name":name,"url":url,"status":"completed","conclusion":conclusion,
            "time":when,"branch":"main"}
def root(id_,source,runs):
    return {"id":id_,"source":source,"privacy":"public","recent_runs":runs,
            "status":"CHECKS_FAILED" if any(x["conclusion"]=="failure" for x in runs) else "CI_PRESENT_NOT_PRODUCT_VALIDATION"}
def report():
    return {"roots":[
      root("neurocity","clucaina/NPL-CANONICAL",[job("viewer",RUN)]),
      root("psicologia_politica","clucaina/psicologia-politica",[job("data",PP)]),
      {"id":"apj","source":None,"recent_runs":[],"privacy":"private"},
    ]}

class TestEvolution(unittest.TestCase):
    def test_only_two_public_roots_and_bounded_proposals(self):
        d=evolve(report())
        self.assertEqual(d["schema"],SCHEMA)
        self.assertEqual(d["evidence_roots"],2)
        self.assertEqual(d["unproven_hypotheses_created"],2)
        self.assertEqual(d["active_workers_claimed"],0)
        self.assertEqual(d["private_data_transferred"],0)
        self.assertFalse(d["originality_verified"])
        self.assertFalse(d["publication_authorized"])
        self.assertFalse(d["last_pulse_made_code_changes"])
        self.assertTrue(all(p["root"] in ("neurocity","psicologia_politica") for p in d["hypotheses"]))
    def test_real_source_type_and_approval_contracts_are_explicit(self):
        r=evolve(report())
        for p in r["hypotheses"]:
            self.assertTrue(p["evidence_url"].startswith("https://github.com/clucaina/"))
            self.assertIn("propuesta".upper(),"PROPUESTA")
            self.assertFalse(p["scientific_validation"])
            self.assertFalse(p["is_global_invention"])
            self.assertFalse(p["code_changed"])
            self.assertFalse(p["deployment"])
            self.assertGreater(len(p["falsifier"]),30)
            self.assertGreater(len(p["test_to_run"]),30)
            self.assertNotIn("pub-",str(p))
    def test_prior_snapshot_deduplicates_on_second_and_third_pulse(self):
        a=evolve(report())
        b=evolve(report(),{"evolution":a})
        c=evolve(report(),{"evolution":b})
        first={x["id"] for x in a["hypotheses"]}
        second={x["id"] for x in b["hypotheses"]}
        third={x["id"] for x in c["hypotheses"]}
        self.assertFalse(first&second)
        self.assertFalse(first&third)
        self.assertFalse(second&third)
        self.assertEqual(len(b["recent_ids"]),4)
        self.assertEqual(len(c["recent_ids"]),6)
        self.assertGreater(b["repeat_candidates_pruned"],0)
    def test_memory_eventually_exhausts_without_faking_new_progress(self):
        previous=None
        accepted=set()
        for _ in range(8):
            result=evolve(report(),previous)
            ids={x["id"] for x in result["hypotheses"]}
            self.assertFalse(ids&accepted)
            accepted.update(ids)
            previous={"evolution":result}
        self.assertEqual(len(accepted),sum(len(x) for x in EXPERIMENTS.values()))
        self.assertEqual(result["hypotheses"],[])
        self.assertEqual(result["last_pulse_result"],"NO_NEW_VERIFIABLE_HYPOTHESIS")
    def test_changed_public_ci_evidence_can_reopen_experiment_without_false_promotion(self):
        before=evolve(report())
        later=report()
        later["roots"][0]["recent_runs"][0]["url"]=RUN[:-2]+"20"
        other=evolve(later,{"evolution":before})
        self.assertTrue(all(x["status"]=="ENGINEERING_HYPOTHESIS_REQUIRES_REAL_TEST" for x in other["hypotheses"]))
        self.assertFalse(other["real_world_effect_verified"])
    def test_injection_and_data_from_private_roots_cannot_leak(self):
        bad=report()
        bad["roots"][2]={"id":"apj","source":"clucaina/neuropsicolucia",
                        "recent_runs":[job("private@patient.test",RUN,"failure")],
                        "client_record":"confidential"}
        bad["roots"][0]["recent_runs"][0]["name"]="data <script>alert(1)</script>"
        out=evolve(bad)
        rendered=markdown(out)
        self.assertNotIn("patient.test",str(out))
        self.assertNotIn("confidential",str(out))
        self.assertNotIn("<script>",str(out)+rendered)
    def test_wrong_repository_host_or_url_never_counts_as_evidence(self):
        for url in [
            "https://evil.invalid/clucaina/NPL-CANONICAL/actions/runs/4",
            "file:///tmp/client.json",
            "https://github.com/other/NPL-CANONICAL/actions/runs/4",
            "https://github.com/clucaina/psicologia-politica/actions/runs/40188427619",
            "https://github.com/clucaina/NPL-CANONICAL/actions/runs/123?token=abc",
        ]:
            d=report()
            d["roots"][0]["recent_runs"][0]["url"]=url
            res=evolve(d)
            self.assertFalse(any(x["root"]=="neurocity" for x in res["hypotheses"]),url)
    def test_failure_first_but_never_fabricates_a_fix(self):
        d=report()
        d["roots"][0]["recent_runs"][0]["conclusion"]="failure"
        o=evolve(d)
        self.assertEqual(o["hypotheses"][0]["root"],"neurocity")
        self.assertEqual(o["hypotheses"][0]["evidence_kind"],"LATEST_PER_WORKFLOW_FAILED_CI")
        self.assertFalse(o["hypotheses"][0]["code_changed"])
    def test_latest_success_overrules_superseded_failure_of_same_workflow(self):
        d=report()
        d["roots"][0]["recent_runs"].append(job("viewer",RUN[:-2]+"21","failure","2026-10-24T11:20:09Z"))
        self.assertEqual(_observed_run(d["roots"][0])["conclusion"],"success")
    def test_other_workflow_failure_remains_visible(self):
        d=report()
        d["roots"][0]["recent_runs"].append(job("3D renderer",RUN[:-2]+"21","failure","2026-10-24T11:20:09Z"))
        self.assertEqual(_observed_run(d["roots"][0])["conclusion"],"failure")
    def test_malformed_or_oversized_previous_is_ignored_fail_closed(self):
        baseline=evolve(report())
        for corrupted in [
          "string",{},{"evolution":{"schema":SCHEMA,"recent_ids":[42]}},
          {"evolution":{"schema":SCHEMA,"recent_ids":["../../secrets"]}},
          {"evolution":{"schema":SCHEMA,"recent_ids":["1"*20]*40}},
          {"evolution":{"schema":SCHEMA,"recent_ids":[],"bloat":"x"*100_000}},
        ]:
            self.assertEqual([x["id"] for x in evolve(report(),corrupted)["hypotheses"]],
                             [x["id"] for x in baseline["hypotheses"]])
    def test_invalid_budget_or_snapshot_rejected(self):
        for limit in (-1,3,4.5,True,"2"):
            with self.assertRaises(ValueError):evolve(report(),budget=limit)
        with self.assertRaises(TypeError):evolve({"roots":{}})
    def test_skips_any_root_without_completed_genuine_ci(self):
        d=report()
        for rt in d["roots"][:2]:
            rt["recent_runs"][0]["status"]="queued"
        result=evolve(d)
        self.assertEqual(result["evidence_roots"],0)
        self.assertEqual(result["unproven_hypotheses_created"],0)
        self.assertEqual(result["last_pulse_result"],"NO_NEW_VERIFIABLE_HYPOTHESIS")
    def test_summary_and_history_stay_small(self):
        x=evolve(report())
        self.assertLess(len(str(x).encode()),13000)
        self.assertLessEqual(len(x["recent_ids"]),MAX_HISTORY)
        m=markdown(x)
        self.assertIn("NO validadas",m)
        self.assertIn("no ejecuta",m)
        self.assertNotIn("1000 descubrimientos",m)
if __name__=="__main__":unittest.main()
