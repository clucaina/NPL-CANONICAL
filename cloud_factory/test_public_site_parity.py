import unittest
from pathlib import Path
from unittest.mock import patch
from public_site_parity import (
    ORIGIN, PROBES, MAX_BYTES, evaluate_probe, observe, markdown, fetch_public
)


def page(path, text, status=200, host=ORIGIN):
    return {"status": status, "final_url": host + path, "text": text}


def success_map():
    return {
        "/noticias": page("/noticias", '<header class="nn-ribbon-front nn-claim-head">News</header>'),
        "/laboratorio-de-decisiones": page("/proyectos", "El conocimiento no termina"),
        "/noticias/feed.xml": page("/noticias/feed.xml", '<rss version="2.0">NeuroNews</rss>'),
    }


class SiteParityTests(unittest.TestCase):
    def test_all_three_live_signals_on_original_domain(self):
        states = success_map()
        report = observe(fetcher=lambda path: states[path])
        self.assertEqual(report["verdict"], "LIVE_RELEASE_VISIBLE")
        self.assertTrue(all(x["status"] == "VERIFIED" for x in report["checks"]))
        self.assertTrue(report["read_only"])
        self.assertTrue(report["does_not_deploy"])

    def test_old_newspaper_and_old_laboratory_cannot_pass(self):
        current = success_map()
        current["/noticias"] = page("/noticias", "82 piezas · archivo completo")
        current["/laboratorio-de-decisiones"] = page(
            "/laboratorio-de-decisiones", "NEURODECISIÓN / EXPERIENCIA")
        current["/noticias/feed.xml"] = page("/noticias/feed.xml", "", status=404)
        report = observe(lambda path: current[path])
        self.assertEqual(report["verdict"], "NEEDS_ORIGINAL_SITES_SAVE")
        self.assertEqual([x["status"] for x in report["checks"]], ["STALE", "STALE", "MISSING"])

    def test_redirect_must_reach_same_origin_project_content(self):
        spec = PROBES[1]
        self.assertEqual(evaluate_probe(spec, page("/proyectos", "El conocimiento no termina"))["status"], "VERIFIED")
        self.assertEqual(evaluate_probe(spec, page("/laboratorio-de-decisiones", "El conocimiento no termina"))["status"], "STALE")
        self.assertEqual(evaluate_probe(spec, page("/proyectos", "Proyectos"))["status"], "STALE")
        self.assertEqual(evaluate_probe(spec, page("/proyectos", "El conocimiento no termina", host="https://example.net"))["status"], "UNVERIFIED")
        self.assertEqual(evaluate_probe(spec, page("/proyectos", "El conocimiento no termina", host="http://neuropsicolucia.com"))["status"], "UNVERIFIED")

    def test_neuronews_requires_both_real_masthead_markers(self):
        probe = PROBES[0]
        self.assertEqual(evaluate_probe(probe, page("/noticias", "nn-ribbon-front"))["status"], "STALE")
        self.assertEqual(evaluate_probe(probe, page("/noticias", "nn-claim-head"))["status"], "STALE")

    def test_unknown_status_network_failure_must_not_look_like_stale_content(self):
        states = success_map()
        states["/noticias"] = {"error": "TimeoutError", "final_url": None}
        self.assertEqual(observe(lambda path: states[path])["verdict"], "UNVERIFIED")
        self.assertEqual(evaluate_probe(PROBES[2], page("/noticias/feed.xml", "", status=429))["status"], "MISSING")

    def test_exception_does_not_break_other_checks_or_trigger_side_effects(self):
        states = success_map()
        def fetcher(path):
            if path == "/noticias":
                raise RuntimeError("network unavailable")
            return states[path]
        report = observe(fetcher)
        self.assertEqual(report["checks"][0]["status"], "UNVERIFIED")
        self.assertEqual(report["checks"][1]["status"], "VERIFIED")
        self.assertEqual(report["checks"][2]["status"], "VERIFIED")
        text = markdown(report)
        self.assertNotIn("network unavailable", text)
        self.assertNotIn("<html", text)
        self.assertIn("does not deploy", text)

    def test_no_extra_network_destination_and_no_persistent_storage_or_email(self):
        with self.assertRaises(ValueError):
            fetch_public("/api/admin")
        self.assertEqual(len(PROBES), 3)
        self.assertLess(MAX_BYTES, 200_000)
        script=(Path(__file__).parent / "public_site_parity.py").read_text(encoding="utf-8")
        for forbidden in (
            "requests.post(", "os.system(", "sendmail", "createComment",
            "smtplib", "gmail", "write_text(", "write_bytes(",
            "upload-artifact", "setInterval", "adsbygoogle",
        ):
            self.assertNotIn(forbidden, script)


if __name__ == "__main__":
    unittest.main()
