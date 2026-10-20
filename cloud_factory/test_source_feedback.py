import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from source_feedback import reconcile
def proposal(id="T25_SCIENCE_TEST"):
 return {"id":id,"source_blob_sha":"a"*40,"raw_sha256":"b"*64,
         "data_quality":"REJECTED_FORMAT","source_path":"database/"+id+".json",
         "release_gate":"NO_AUTO_IMPORT_NO_AUTO_DEPLOY","raw_values_copied":False}
def led():
 return {"schema":"neurohuerto.candidate_ledger.v1","repository":"clucaina/psicologia-politica",
         "source_ref":"integracion/v78-maestro-sin-despliegue",
         "candidates":[proposal()],"candidate_count":1,"publication_authorized":False}
def reviewed(assessment="BLOCK_FORMAT_OR_ID",blob="a"*40):
 return {"schema":"neurohuerto.independent_reviewer.v1","reviews":[{
    "id":"T25_SCIENCE_TEST","source_blob_sha":blob,"upstream_sha256":"b"*64,
    "independent_check":{"status":assessment,"digest_match":True}}]}
class FeedbackTests(unittest.TestCase):
 def test_invalid_dataset_becomes_research_reference_not_fake_observation(self):
  x=reconcile(led(),reviewed())
  c=x["candidates"][0]
  self.assertEqual(c["candidate_type"],"PUBLIC_RESEARCH_DOCUMENT_NOT_STATISTICAL_OBSERVATIONS")
  self.assertEqual(c["routing"],"RESEARCH_REVIEW_NOT_DATA_IMPORT")
  self.assertTrue(c["independent_source_checked"])
  self.assertFalse(x["publication_authorized"])
  self.assertFalse(c["raw_values_copied"])
 def test_stale_or_changed_metadata_fails_closed(self):
  x=reconcile(led(),reviewed(blob="f"*40))
  c=x["candidates"][0]
  self.assertNotIn("candidate_type",c)
  self.assertEqual(c["feedback_warning"],"UPSTREAM_DIGEST_OR_BLOB_MISMATCH")
  self.assertFalse(x["publication_authorized"])
 def test_reconciliation_is_idempotent_except_ephemeral_count(self):
  a=reconcile(led(),reviewed())
  b=reconcile(a,reviewed())
  self.assertEqual(a["candidates"],b["candidates"])
  self.assertEqual(b["feedback_changed"],0)
 def test_unknown_schema_rejected(self):
  with self.assertRaises(ValueError):reconcile({"schema":"other"},reviewed())
if __name__=="__main__":unittest.main()
