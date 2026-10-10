#!/usr/bin/env python3
"""Public geodata download for Alicante. No private content."""
import json,math,time,xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,urlopen
D=Path("input"); D.mkdir(exist_ok=True)
bounds=(-0.4862,38.3418,-0.4795,38.3470)
center=(-0.48322,38.34402)
R=6378137.
def m(lon,lat):return (R*math.radians(lon),R*math.log(math.tan(math.pi/4+math.radians(lat)/2)))
def get(url,target,validator):
    last=None
    for i in range(3):
        try:
            req=Request(url,headers={"User-Agent":"NPL-World-OpenData/0.1 (github.com/clucaina/NPL-CANONICAL)"})
            with urlopen(req,timeout=55) as resp:
                if resp.status!=200:raise RuntimeError("HTTP "+str(resp.status))
                data=resp.read(25*1024*1024)
            if not validator(data):raise RuntimeError("Invalid content returned")
            target.write_bytes(data)
            return len(data)
        except Exception as ex:
            last=ex;time.sleep(2*(i+1))
    raise RuntimeError(str(last))
west,south,east,north=bounds
url="https://api.openstreetmap.org/api/0.6/map?"+urlencode({"bbox":",".join(map(str,bounds))})
print("Downloading REAL OSM",url,flush=True)
sz=get(url,D/"alicante.osm",lambda b:b"<osm" in b[:300])
ET.parse(D/"alicante.osm")
cx,cy=m(*center);x1,y1=m(west,south);x2,y2=m(east,north)
params={"SERVICE":"WMS","VERSION":"1.3.0","REQUEST":"GetMap","LAYERS":"OI.OrthoimageCoverage","STYLES":"",
"CRS":"EPSG:3857","BBOX":f"{x1},{y1},{x2},{y2}","WIDTH":2048,"HEIGHT":1536,"FORMAT":"image/jpeg"}
ortho="https://www.ign.es/wms-inspire/pnoa-ma?"+urlencode(params)
try:
    get(ortho,D/"PNOA_ground.jpg",lambda b:b[:3]==b"\xff\xd8\xff")
    have=True
except Exception as ex:
    have=False;print("PNOA not downloaded, real aerial ground absent:",ex,flush=True)
manifest={"bbox":bounds,"center":center,"center_mercator":[cx,cy],
"bbox_local_m":[x1-cx,y1-cy,x2-cx,y2-cy],"real_orthophoto":have,
"osm_bytes":sz,"building_facades_photogrammetric":False,
"data_attributions":["© OpenStreetMap contributors - ODbL","© IGN - PNOA"]}
(D/"source_manifest.json").write_text(json.dumps(manifest,indent=2))
print(json.dumps(manifest,indent=2),flush=True)
