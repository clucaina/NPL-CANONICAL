import importlib.util
import unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location("open_imagery_inventory",Path(__file__).with_name("open_imagery_inventory.py"))
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class PanoramaxStacTests(unittest.TestCase):
    def item(self,uid,lon=-0.4832,lat=38.344,collection="seq_public_12"):
        return {"id":uid,"collection":collection,
                "type":"Feature","geometry":{"type":"Point","coordinates":[lon,lat]}}
    def test_location_filter_no_photo_or_person_payload(self):
        records={"type":"FeatureCollection","features":[
            self.item("image_02"),self.item("image_01"),
            self.item("too_far",-0.50,38.344),
            {"id":"face_04","collection":"seq_public_12","geometry":{"type":"Point","coordinates":[-0.482,38.344]},
             "properties":{"person":"REDACT_ME","email":"REDACT_ME"}},
        ]}
        out=mod.classify_response(records)
        self.assertEqual(out["image_count"],3)
        self.assertEqual(out["sequence_count"],1)
        self.assertEqual(out["pictures_downloaded"],0)
        self.assertFalse(out["photos_reconstruction_approved"])
        self.assertTrue(all("properties" not in x and "person" not in x for x in out["results"]))
        self.assertEqual(out["results"][0]["image_id"],"face_04")
    def test_invalid_coordinates_rejected(self):
        raw={"type":"FeatureCollection","features":[
            self.item("boolean",True),self.item("string","-0.4832"),
            self.item("nan",float("nan")),self.item("valid")]}
        self.assertEqual(mod.classify_response(raw)["image_count"],1)
    def test_source_and_count_guardrails(self):
        with self.assertRaises(ValueError):mod.classify_response({})
        with self.assertRaises(ValueError):mod.classify_response({"type":"FeatureCollection","features":[{}]*101})
        with self.assertRaises(ValueError):mod.load_public_api("http://evil.test/search","panoramax.ign.fr")
        with self.assertRaises(ValueError):mod.load_public_api("https://panoramax.ign.fr.evil.test/search","panoramax.ign.fr")
    def test_per_photo_license_no_catalog_assumption(self):
        ok=self.item("licensed")
        ok["links"]=[{"rel":"license","href":"https://creativecommons.org/licenses/by-sa/4.0/"}]
        no=self.item("unverified")
        no["links"]=[{"rel":"license","href":"https://example.net/proprietary"}]
        report=mod.license_audit([ok,no])
        self.assertEqual(report["license_link_approved_count"],1)
        self.assertEqual(report["license_unknown_or_incompatible_count"],1)
        self.assertEqual(report["image_bytes_downloaded"],0)
        self.assertFalse(report["sfm_model_created"])
    def test_zero_images_does_not_fabricate_reconstruction(self):
        out=mod.classify_response({"type":"FeatureCollection","features":[]})
        self.assertEqual(out["image_count"],0)
        self.assertEqual(out["sequence_count"],0)
        self.assertEqual(out["geometry_created"],0)

if __name__=="__main__":unittest.main()
