import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from source_expander import discover,source_listing,DIR_API,RAW_PREFIX,FILENAME
def row(stem,geo):
 return {"indicator_id":"AROPE_TOTAL","period":"2025","geo_code":geo,"subgroup":"Todos",
         "value":27.4,"unit":"%","source_id":"INE","source_url":"https://www.ine.es/"}
def catalog():
 return {"sources":[{"public_path":"database/T27_SALARIOS_CCAA_2024.json"}]}
def listing():
 return [
 {"type":"file","path":"database/T27_SALARIOS_CCAA_2024.json","size":500,"sha":"abc"},
 {"type":"file","path":"database/T26_VULNERABILIDAD_SEGURIDAD_2025.json","size":1800,"sha":"def"},
 {"type":"file","path":"database/T30_ABANDONO_2025.json","size":1300,"sha":"ghi"},
 {"type":"file","path":"database/SECRET_CLIENT_DATA.json","size":300,"sha":"private"},
 {"type":"file","path":"database/T40_LARGE_DATA.json","size":900000000,"sha":"large"},
 {"type":"dir","path":"database/T31_NOT_A_FILE.json","size":300,"sha":"bad"},
 ]
class PublicDiscoveryTests(unittest.TestCase):
 def test_names_restrict_to_public_batch_and_size(self):
  names=source_listing(lambda url:listing())
  self.assertEqual(set(names),{"T27_SALARIOS_CCAA_2024","T26_VULNERABILIDAD_SEGURIDAD_2025","T30_ABANDONO_2025"})
  self.assertFalse(FILENAME.fullmatch("database/../.env"))
 def test_discovery_does_not_copy_measurement_values_or_promote_rights(self):
  calls=[]
  def fetch(url):
   calls.append(url)
   self.assertTrue(url.startswith(RAW_PREFIX))
   stem=Path(url).stem
   batch={"batch_id":stem,"observations":[row(stem,"ES"),row(stem,"ES30")],"new_indicators":[]}
   return batch,"a"*64
  result=discover(catalog(),{},lambda _:listing(),fetch,limit=1)
  self.assertEqual(result["new_candidates"],1)
  self.assertEqual(result["remaining_unexamined"],1)
  first=list(result["candidates"].values())[0]
  self.assertEqual(first["id"],"T26_VULNERABILIDAD_SEGURIDAD_2025")
  self.assertFalse(first["raw_values_copied"])
  self.assertEqual(first["review_state"],"NEEDS_INDEPENDENT_LICENSE_AND_METHOD_REVIEW")
  self.assertNotIn("27.4",json.dumps(result))
  self.assertFalse(first["source_exists_in_catalog"])
  again=discover(catalog(),result["candidates"],lambda _:listing(),fetch,limit=5)
  self.assertEqual(again["new_candidates"],1)
  self.assertEqual(again["candidates"]["T30_ABANDONO_2025"]["data_quality"],"REVIEW_REQUIRED")
 def test_network_errors_are_redacted(self):
  result=discover(catalog(),{},lambda _:listing(),
    lambda url:(_ for _ in ()).throw(ValueError("token secret patient")),limit=1)
  data=json.dumps(result)
  self.assertIn("SOURCE_UNAVAILABLE",data)
  self.assertNotIn("secret",data)
  self.assertNotIn("patient",data)
 def test_invalid_or_excessive_batch_limit(self):
  with self.assertRaises(ValueError):discover(catalog(),{},lambda _:listing(),lambda _:None,limit=100)
if __name__=="__main__":unittest.main()
