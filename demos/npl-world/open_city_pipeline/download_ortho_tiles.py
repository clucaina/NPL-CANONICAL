#!/usr/bin/env python3
"""Fetch genuine PNOA orthophoto as public WMTS 256px tiles; mosaic into geographic JPEG."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlencode
from urllib.request import urlopen,Request
from PIL import Image
from io import BytesIO
import math,json,time
D=Path("input");manifest_path=D/"source_manifest.json"
manifest=json.loads(manifest_path.read_text())
w,s,e,n=manifest["bbox"]
if (D/"PNOA_ground.jpg").exists():
    print("Real PNOA WMS imagery already available");quit()
Z=17; N=2**Z
def xy(lon,lat):
    return ((lon+180)/360*N,(1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*N)
tlx,tly=xy(w,n);brx,bry=xy(e,s)
xa,xb=math.floor(tlx),math.floor(brx)
ya,yb=math.floor(tly),math.floor(bry)
print("PNOA WMTS tile grid",Z,xa,xb,ya,yb,flush=True)
if (xb-xa+1)*(yb-ya+1)>150:raise RuntimeError("Too many imagery tiles")
def fetch_tile(coord):
    xx,yy=coord
    params={"SERVICE":"WMTS","REQUEST":"GetTile","VERSION":"1.0.0",
    "LAYER":"OI.OrthoimageCoverage","STYLE":"default","TILEMATRIXSET":"GoogleMapsCompatible",
    "TILEMATRIX":Z,"TILEROW":yy,"TILECOL":xx,"FORMAT":"image/jpeg"}
    url="https://www.ign.es/wmts/pnoa-ma?"+urlencode(params)
    for t in range(3):
        try:
            req=Request(url,headers={"User-Agent":"NPL-World-Research/0.1 (github.com/clucaina/NPL-CANONICAL)"})
            with urlopen(req,timeout=20) as r:
                d=r.read(2*1024*1024)
            if d[:3]!=b"\xff\xd8\xff":raise RuntimeError("Tile is not JPEG")
            return xx,yy,Image.open(BytesIO(d)).convert("RGB")
        except Exception as ex:
            if t==2:print("Failed WMTS tile",coord,str(ex),flush=True)
            time.sleep(1+t)
    return xx,yy,None
width=(xb-xa+1)*256;height=(yb-ya+1)*256
mosaic=Image.new("RGB",(width,height),(80,80,80))
coords=[(x,y) for y in range(ya,yb+1) for x in range(xa,xb+1)]
success=0
with ThreadPoolExecutor(max_workers=4) as ex:
    futures=[ex.submit(fetch_tile,coord) for coord in coords]
    for fut in as_completed(futures):
        x,y,img=fut.result()
        if img is not None:
            mosaic.paste(img,((x-xa)*256,(y-ya)*256));success+=1
# Do not ship a fake ortho when even one of the required tiles is missing.
print("WMTS imagery received",success,"/",len(coords),flush=True)
if success!=len(coords):
    print("Incomplete PNOA image; no photographic ground material will be claimed",flush=True)
    quit()
box=((tlx-xa)*256,(tly-ya)*256,(brx-xa)*256,(bry-ya)*256)
resample=Image.Resampling.LANCZOS if hasattr(Image,"Resampling") else Image.LANCZOS
mosaic=mosaic.crop(tuple(round(v) for v in box)).resize((2048,1536),resample)
mosaic.save(D/"PNOA_ground.jpg",quality=93,subsampling=0)
manifest["real_orthophoto"]=True
manifest["orthophoto_source"]="© IGN PNOA Máxima Actualidad / WMTS GoogleMapsCompatible z17"
manifest_path.write_text(json.dumps(manifest,indent=2))
print("Real PNOA image saved", (D/"PNOA_ground.jpg").stat().st_size,flush=True)
