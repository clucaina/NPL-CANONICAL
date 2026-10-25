#!/usr/bin/env python3
"""Read-only Site release parity in the EXISTING public Huerto pulse.

Three bounded GETs against the public Neuropsicolucia origin, every six hours.
No private GitHub source, account access, analytics, user data, ad calls,
scheduler, emails, persistence, screenshots or full HTML in logs.
"""
import argparse
from datetime import datetime, timezone
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ORIGIN = "https://neuropsicolucia.com"
PROBES = (
    ("newsroom", "/noticias", ("nn-ribbon-front", "nn-claim-head"), None),
    ("lab_retired", "/laboratorio-de-decisiones", ("El conocimiento no termina",), "/proyectos"),
    ("news_rss", "/noticias/feed.xml", ('<rss version="2.0"', "NeuroNews"), None),
)
MAX_BYTES = 192_000


def fetch_public(path, opener=urlopen):
    """A fixed same-origin public GET, never a private proxy or state mutation."""
    if path not in {p[1] for p in PROBES}:
        raise ValueError("Unapproved URL")
    request = Request(ORIGIN + path, method="GET", headers={
        "User-Agent": "NeuroHuertoPublicReleaseParity/1.0 (read-only)",
        "Accept": "text/html,application/rss+xml",
    })
    try:
        with opener(request, timeout=10) as response:
            return {
                "status": response.status,
                "final_url": response.geturl(),
                "text": response.read(MAX_BYTES).decode("utf-8", errors="replace"),
            }
    except HTTPError as error:
        return {"status": error.code, "final_url": error.geturl(), "text": ""}
    except (OSError, URLError, TimeoutError) as error:
        return {"status": None, "final_url": None, "text": "", "error": type(error).__name__}


def evaluate_probe(probe, observation):
    name, path, markers, destination = probe
    # Prevent 200 results from a third-party redirect looking like a Site release.
    if observation.get("error") or not observation.get("final_url"):
        return {"id": name, "status": "UNVERIFIED"}
    target = urlsplit(str(observation["final_url"]))
    if target.scheme != "https" or target.netloc != urlsplit(ORIGIN).netloc:
        return {"id": name, "status": "UNVERIFIED"}
    code = observation.get("status")
    if not isinstance(code, int) or code < 200 or code >= 300:
        return {"id": name, "status": "MISSING"}
    if destination is not None and target.path != destination:
        return {"id": name, "status": "STALE"}
    if not all(marker in observation.get("text", "") for marker in markers):
        return {"id": name, "status": "STALE"}
    return {"id": name, "status": "VERIFIED"}


def observe(fetcher=fetch_public):
    checks = []
    for probe in PROBES:
        try:
            observation = fetcher(probe[1])
            checks.append(evaluate_probe(probe, observation))
        except Exception:
            checks.append({"id": probe[0], "status": "UNVERIFIED"})
    statuses = {x["status"] for x in checks}
    verdict = ("LIVE_RELEASE_VISIBLE" if statuses == {"VERIFIED"}
               else "UNVERIFIED" if "UNVERIFIED" in statuses
               else "NEEDS_ORIGINAL_SITES_SAVE")
    return {"schema": "neurohuerto.public_site_parity.v1",
            "origin": ORIGIN,
            "checks": checks,
            "verdict": verdict,
            "read_only": True,
            "does_not_deploy": True}


def markdown(report):
    label = {"LIVE_RELEASE_VISIBLE": "New Site release visible",
             "UNVERIFIED": "Network/redirect prevents verification",
             "NEEDS_ORIGINAL_SITES_SAVE": "Original Site still needs release"}
    lines = [
        "### Neuropsicolucía · publicación pública (solo lectura)",
        "**Estado:** " + label[report["verdict"]] + " · " + report["verdict"],
        "",
        "| Comprobación | Resultado |", "|---|---|",
    ]
    for record in report["checks"]:
        lines.append("| " + record["id"] + " | " + record["status"] + " |")
    lines.append("")
    lines.append("This public-only probe does not deploy, validate private code, access user data or load ads.")
    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()
    status = observe()
    print(markdown(status) if args.summary else status["verdict"])
