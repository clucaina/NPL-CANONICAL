import importlib.util
import unittest
from pathlib import Path
spec = importlib.util.spec_from_file_location("curate_cc0_assets", Path(__file__).with_name("curate_cc0_assets.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class TestCuration(unittest.TestCase):
    def make(self):
        return {
          "palm_tree_01": {"name": "Mediterranean Palm Tree", "category":"Nature/Trees", "tags":["tree","palm"],"date_published":1000},
          "bench_01": {"name": "Urban Bench", "category":"Furniture/Urban","tags":["wood"],"date_published":1000},
          "patient_record": {"name": "Patient Face", "category":"People","tags":["patient"],"date_published":1000},
          "future_tree": {"name": "Tree", "category":"Nature","tags":["tree"],"date_published":9999999999},
          "irrelevant": {"name": "Crystal", "category":"Geology","tags":["mineral"],"date_published":1000},
          "../escape": {"name":"Street", "category":"City","tags":["street"],"date_published":1000}
        }
    def test_public_relevance_and_privacy_filters(self):
        report = module.rank_assets(self.make(), now=2000)
        self.assertEqual(report["count"],2)
        self.assertEqual(report["candidates"][0]["id"],"palm_tree_01")
        self.assertEqual(report["candidates"][1]["id"],"bench_01")
        self.assertTrue(all(x["candidate_only"] and not x["binary_downloaded"] for x in report["candidates"]))
        self.assertEqual(report["models_downloaded"],0)
        self.assertFalse(any("patient" in x["id"] for x in report["candidates"]))
    def test_determinism_and_bounds(self):
        payload=self.make()
        a=module.rank_assets(payload,limit=1,now=2000)
        b=module.rank_assets(payload,limit=1,now=2000)
        self.assertEqual(a,b)
        self.assertEqual(a["count"],1)
        with self.assertRaises(ValueError): module.rank_assets(payload,limit=100000)
        with self.assertRaises(ValueError): module.rank_assets([])
    def test_reject_garbage_metadata(self):
        source={"okay_tree":{"name":"Tree","category":"Nature","tags":["tree"],"date_published":100},
                "bad_meta":"string",
                "missing_tags":{"name":"Tree","category":"Nature","date_published":100},
                "wrong_date":{"name":"Tree","category":"Nature","tags":["tree"],"date_published":True}}
        result=module.rank_assets(source,now=200)
        self.assertEqual(result["count"],1)

if __name__ == "__main__":
    unittest.main()
