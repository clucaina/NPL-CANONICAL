#!/usr/bin/env python3
"""NeuroCity: inventory of open street-level photographic SEQUENCES near Alicante.
Fetches STAC public metadata ONLY, never faces/photos, patients, usernames or tokens.
This is input discovery for future permission-checked COLMAP reconstruction, NOT a 3D mesh.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,urlopen

PANORAMAX="https://panoramax.ign.fr/api"
FEDERATION="https://api.panoramax.xyz/api"
KARTAVIEW="https://api.openstreetcam.org/2.0/photo/"
ALICANTE_BBOX=(-0.4862,38.3418,-0.4795,38.3470)
MAX_JSON=3_000_000
MAX_ITEMS=100
SOURCE_LICENCE="etalab-2.0"
def inside(lon,lat,bbox=ALICANTE_BBOX):
    return (math.isfinite(lon) and math.isfinite(lat) and
            bbox[0]<=lon<=bbox[2] and bbox[1]<=lat<=bbox[3])

def classify_response(data,bbox=ALICANTE_BBOX,provider="Panoramax IGN",license_hint=SOURCE_LICENCE):
    # Some Panoramax federation versions return a STAC feature list without
    # the optional top-level type key. Do not confuse that shape with no coverage.
    if not isinstance(data,dict) or "features" not in data or data.get("type","FeatureCollection")!="FeatureCollection":
        raise ValueError("Unexpected non-STAC feature collection")
    features=data.get("features")
    if not isinstance(features,list) or len(features)>MAX_ITEMS:
        raise ValueError("Too many or invalid street image records")
    results=[]
    for feature in features:
        if not isinstance(feature,dict):continue
        geom=feature.get("geometry")
        if not isinstance(geom,dict) or geom.get("type")!="Point":continue
        xy=geom.get("coordinates")
        if not isinstance(xy,list) or len(xy)<2 or any(
            isinstance(x,(bool,str)) or not isinstance(x,(int,float)) for x in xy[:2]):
            continue
        lon,lat=xy[:2]
        if not inside(lon,lat,bbox):continue
        uid=feature.get("id")
        collection=feature.get("collection")
        if not isinstance(uid,str) or len(uid)>100 or not isinstance(collection,str) or len(collection)>100:
            continue
        if not all(c.isalnum() or c in "-_" for c in uid+collection):continue
        # Only reuse metadata; imagery does not become usable until checked separately.
        results.append({"image_id":uid,"sequence_id":collection,
                        "longitude":round(lon,6),"latitude":round(lat,6),
                        "photogrammetry_ready":False})
    results.sort(key=lambda v:(v["sequence_id"],v["image_id"]))
    seq={}
    for feature in results:
        seq[feature["sequence_id"]]=seq.get(feature["sequence_id"],0)+1
    return {
        "schema":"neurocity.street-imagery-inventory.v1",
        "bounds_wgs84":list(bbox),"provider":provider,
        "api":PANORAMAX if provider=="Panoramax IGN" else FEDERATION,"license_hint":license_hint,
        "pictures_downloaded":0,"geometry_created":0,
        "photos_reconstruction_approved":False,
        "image_count":len(results),
        "sequence_count":len(seq),
        "candidate_sequences":[{"id":k,"count":v,"needs_pose_overlap_review":True}
                               for k,v in sorted(seq.items())],
        "results":results}

def load_public_api(url,allow_hostname):
    from urllib.parse import urlsplit
    p=urlsplit(url)
    if p.scheme!="https" or p.hostname!=allow_hostname or p.username or p.password:
        raise ValueError("Unapproved source host")
    req=Request(url,headers={"Accept":"application/geo+json, application/json",
                             "User-Agent":"NeuroCity-Open-Street-Image-QA/1.0"})
    with urlopen(req,timeout=25) as resp:
        if urlsplit(resp.url).hostname!=allow_hostname:raise ValueError("Source redirected outside official host")
        if resp.status!=200:raise RuntimeError("Street image API HTTP "+str(resp.status))
        raw=resp.read(MAX_JSON+1)
    if len(raw)>MAX_JSON:raise ValueError("Oversized public image metadata")
    return json.loads(raw)

def query_live():
    license_catalog=load_public_api(PANORAMAX+"/", "panoramax.ign.fr")
    licenses=[x.get("href","") for x in license_catalog.get("links",[])
              if isinstance(x,dict) and x.get("rel")=="license"]
    if not any("licence-ouverte" in x or "etalab" in x for x in licenses):
        raise RuntimeError("No independently declared open imagery metadata license")
    url=PANORAMAX+"/search?"+urlencode({"bbox":",".join(str(x) for x in ALICANTE_BBOX),"limit":MAX_ITEMS})
    report=classify_response(load_public_api(url,"panoramax.ign.fr"))
    report["declared_license_urls"]=licenses[:3]
    report["endpoint_checked"]=url
    # The federated catalog also covers non-IGN sequences worldwide.
    # Its root license is mixed; NEVER treat federated photos as individually cleared.
    federated_url=FEDERATION+"/search?"+urlencode({"bbox":",".join(str(x) for x in ALICANTE_BBOX),"limit":MAX_ITEMS})
    federated_payload=load_public_api(federated_url,"api.panoramax.xyz")
    if isinstance(federated_payload.get("features"),list):
        federation=classify_response(federated_payload,
            provider="Panoramax Federation",license_hint="PER_IMAGE_LICENSE_REVIEW_REQUIRED")
        report["federation_discovery"]={
            "status":"STAC_METADATA_DISCOVERED",
            "records":federation["image_count"],"sequences":federation["sequence_count"],
            "records_license_approved_for_reconstruction":0,
            "source":federated_url,
            "candidate_sequences":federation["candidate_sequences"]
        }
    else:
        # Federated API schema may differ. Record safe structure only; do not fake zero coverage.
        report["federation_discovery"]={
            "status":"UNSUPPORTED_RESPONSE_SHAPE_NOT_A_NO_COVERAGE_CLAIM",
            "source":federated_url,
            "response_type":str(federated_payload.get("type","missing"))[:55],
            "response_keys":sorted(k for k in federated_payload if isinstance(k,str))[:16],
            "records":None,"records_license_approved_for_reconstruction":0
        }
    # Independent, open CC-BY-SA street-level imagery API. This is discovery
    # only; KartaView records must be checked for license, dates and overlap.
    kartaview_url=KARTAVIEW+"?"+urlencode({"lat":38.34318,"lng":-0.48326,
                                            "zoomLevel":16,"join":"sequence"})
    try:
        k=load_public_api(kartaview_url,"api.openstreetcam.org")
        result=k.get("result") if isinstance(k,dict) else None
        entries=result.get("data") if isinstance(result,dict) else None
        if isinstance(entries,list):
            report["kartaview_discovery"]={
                "status":"PUBLIC_RECORDS_DISCOVERED","record_count":len(entries),
                "records_approved_for_reconstruction":0,
                "source":kartaview_url,"license":"CC-BY-SA-4.0"
            }
        elif isinstance(entries,dict):
            report["kartaview_discovery"]={
                "status":"POSSIBLE_PAGINATED_PUBLIC_RECORDS_NEEDS_SCHEMA_REVIEW",
                "response_keys":sorted(entries.keys())[:16],
                "record_count":None,"source":kartaview_url
            }
        else:
            report["kartaview_discovery"]={
                "status":"UNSUPPORTED_RESPONSE_SHAPE",
                "response_keys":sorted(k.keys())[:16] if isinstance(k,dict) else [],
                "record_count":None,"source":kartaview_url
            }
    except Exception as exc:
        report["kartaview_discovery"]={
            "status":"SOURCE_UNAVAILABLE_NOT_ZERO_COVERAGE",
            "error_type":type(exc).__name__,"source":kartaview_url
        }
    return report

def main():
    parser=argparse.ArgumentParser()
    q=parser.add_mutually_exclusive_group(required=True)
    q.add_argument('--live',action='store_true')
    q.add_argument('--fixture',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    raw=query_live() if args.live else classify_response(json.loads(args.fixture.read_text()))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(raw,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    print("Panoramax Alicante: %d public image metadata records in %d sequences; 0 downloaded"%
          (raw["image_count"],raw["sequence_count"]))
if __name__=="__main__":
    main()
