"""Download the published NASA/PDS inputs; never generate substitute measurements."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import hashlib,json,urllib.request,time,os

ROOT=Path(__file__).resolve().parents[2]
RAW=Path(os.environ.get('LUNASCOPE_DATA_DIR',str(ROOT/'data'/'nasa'))).expanduser().resolve();RAW.mkdir(parents=True,exist_ok=True)
BASE='https://naif.jpl.nasa.gov/pub/naif/generic_kernels/'
FILES={
 'LDEM_80S_80M.JP2':'https://imbrium.mit.edu/DATA/LOLA_GDR/POLAR/JP2/LDEM_80S_80M.JP2',
 'LDEM_80S_80M_JP2.LBL':'https://imbrium.mit.edu/DATA/LOLA_GDR/POLAR/JP2/LDEM_80S_80M_JP2.LBL',
 'de421.bsp':BASE+'spk/planets/a_old_versions/de421.bsp',
 'moon_pa_de421_1900-2050.bpc':BASE+'pck/moon_pa_de421_1900-2050.bpc',
 'moon_080317.tf':BASE+'fk/satellites/moon_080317.tf',
 'naif0012.tls':BASE+'lsk/naif0012.tls',
 'pck00011.tpc':BASE+'pck/pck00011.tpc',
}
def download(item):
 name,url=item;target=RAW/name
 if not target.exists():
  for attempt in range(3):
   try:
    with urllib.request.urlopen(url,timeout=90) as response, (RAW/(name+'.part')).open('wb') as output:
     total=int(response.headers.get('Content-Length',0));written=0
     while chunk:=response.read(1024*1024):output.write(chunk);written+=len(chunk)
    if total and written!=total:raise IOError('Incomplete response')
    (RAW/(name+'.part')).replace(target);break
   except Exception:
    if attempt==2:raise
    time.sleep(2)
 data=target.read_bytes()
 if name.endswith(('.bsp','.bpc')) and not data.startswith(b'DAF/'):
  raise ValueError(f'{name}: not a SPICE DAF kernel')
 if name.endswith('.JP2') and data[:12]!=b'\x00\x00\x00\x0cjP  \r\n\x87\n':
  raise ValueError(f'{name}: invalid JPEG2000 signature')
 print(f'NASA input ready: {name} ({len(data):,} bytes)',flush=True)
 return name,{'url':url,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
if __name__=='__main__':
 with ThreadPoolExecutor(max_workers=4) as pool:records=dict(pool.map(download,FILES.items()))
 manifest={'retrieved_at_utc':datetime.now(timezone.utc).isoformat(),'terrain_product':'LRO-L-LOLA-4-GDR-V1.0 / LDEM_80S_80M V2.1',
  'frame':'MOON_ME_DE421','pixel_scale_m':80,'height_scale_m':0.5,'reference_radius_m':1737400,
  'sources':records,'citations':['https://imbrium.mit.edu/BROWSE/LOLA_GDR/POLAR/SOUTH_POLE/',
  'https://naif.jpl.nasa.gov/naif/data.html']}
 (RAW/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
 print('Official input manifest recorded',flush=True)
