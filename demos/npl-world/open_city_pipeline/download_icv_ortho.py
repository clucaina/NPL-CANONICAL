#!/usr/bin/env python3
"""Try official 2024 Valencian Institute Cartographic orthophoto. No paid service."""
import json,math,time,xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,urlopen
from PIL import Image
from io import BytesIO
D=Path('input');mp=D/'source_manifest.json';manifest=json.loads(mp.read_text())
if (D/'PNOA_ground.jpg').exists():
 print('Already has genuine ortho imagery.');quit()
R=6378137
west,south,east,north=manifest['bbox']
def merc(lon,lat):return (R*math.radians(lon),R*math.log(math.tan(math.pi/4+math.radians(lat)/2)))
x0,y0=merc(west,south);x1,y1=merc(east,north)
base='https://terramapas.icv.gva.es/0202_2024CVAL0025'
def req(url,seconds=22):
 with urlopen(Request(url,headers={'User-Agent':'NPL-World-Geodata/0.1 (github.com/clucaina/NPL-CANONICAL)'}),timeout=seconds) as r:
  return r.read(5*1024*1024)
try:
 capabilities=req(base+'?'+urlencode({'service':'WMS','request':'GetCapabilities','version':'1.3.0'}))
 root=ET.fromstring(capabilities)
 names=[x.text for x in root.iter() if x.tag.split('}')[-1]=='Name' and x.text]
 print('Official ICV layers',names[:20],flush=True)
 layers=[n for n in names if '0202' in n or 'ort' in n.lower()]
 layer=layers[0] if layers else (names[1] if len(names)>1 else '0202_2024CVAL0025')
except Exception as ex:
 print('ICV GetCapabilities failed',str(ex),'will attempt documented layer name',flush=True)
 layer='0202_2024CVAL0025'
# Fetch modest 2x2 small WMS tiles to avoid 504.
target=Image.new('RGB',(2048,1536))
ok=0
for row in range(2):
 for col in range(2):
  xa=x0+(x1-x0)*col/2;xb=x0+(x1-x0)*(col+1)/2
  # top row north -> bottom row south, correct geographic image orientation
  ya=y1-(y1-y0)*(row+1)/2;yb=y1-(y1-y0)*row/2
  params={'SERVICE':'WMS','VERSION':'1.1.1','REQUEST':'GetMap','LAYERS':layer,
          'STYLES':'','SRS':'EPSG:3857','BBOX':f'{xa},{ya},{xb},{yb}',
          'WIDTH':1024,'HEIGHT':768,'FORMAT':'image/jpeg','TRANSPARENT':'FALSE'}
  url=base+'?'+urlencode(params)
  for attempt in range(2):
   try:
    d=req(url,25)
    if d[:3]!=b'\xff\xd8\xff':raise ValueError('not JPEG: '+d[:100].decode(errors='replace'))
    im=Image.open(BytesIO(d)).convert('RGB')
    target.paste(im,(col*1024,row*768))
    ok+=1;break
   except Exception as ex:
    print('ICV tile',row,col,'attempt',attempt+1,str(ex)[:180],flush=True)
    time.sleep(2)
if ok==4:
 target.save(D/'PNOA_ground.jpg',quality=95,subsampling=0)
 manifest['real_orthophoto']=True
 manifest['orthophoto_source']='© Generalitat Valenciana / Institut Cartogràfic Valencià — ortofoto RGBI 2024 (25 cm)'
 mp.write_text(json.dumps(manifest,indent=2))
 print('SUCCESS: ICV RGB ortho JPG bytes',(D/'PNOA_ground.jpg').stat().st_size,flush=True)
else:print('No complete official orthophoto. Do not invent or mislabel imagery.',flush=True)
