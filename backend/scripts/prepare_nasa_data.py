"""Decode the verified PDS raster, create a real hillshade and dataset-derived locations."""
from pathlib import Path
import sys,json,hashlib,warnings
import numpy as np
import rasterio
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'backend'))
from app.core.nasa_data import RAW,R_MOON

metadata=json.loads((RAW/'manifest.json').read_text())
src=RAW/'LDEM_80S_80M.JP2'
assert hashlib.sha256(src.read_bytes()).hexdigest()==metadata['sources'][src.name]['sha256']
label=(RAW/'LDEM_80S_80M_JP2.LBL').read_text()
assert 'LRO-L-LOLA-4-GDR-V1.0' in label and 'SCALING_FACTOR' in label and 'MEAN EARTH/POLAR AXIS OF DE421' in label
with warnings.catch_warnings():
 warnings.simplefilter('ignore')
 with rasterio.open(src) as dataset:
  grid=dataset.read(1)
assert grid.shape==(7600,7600) and grid.dtype==np.int16,(grid.shape,grid.dtype)
np.save(RAW/'LDEM_80S_80M.npy',grid)
print(f'PDS raster decoded: {grid.shape}, scaled elevation range {grid.min()*.5} to {grid.max()*.5} m',flush=True)

# A hillshade is a visualization derived from measured elevations, not procedural relief.
small=grid[::5,::5].astype(np.float64)*.5
dy,dx=np.gradient(small,400,400)
normal=np.sqrt(1+dx*dx+dy*dy)
light=np.clip((-dx*.5+dy*.5+.70710678)/normal,0,1)
shade=np.clip(20+light*185,0,255).astype(np.uint8)
assets=ROOT/'frontend'/'public'/'assets';assets.mkdir(parents=True,exist_ok=True)
Image.fromarray(shade).save(assets/'nasa-lola-hillshade.png',optimize=True)

# Reproducible real DEM-cell selection: high ground, regional slope <8 degrees,
# 20 km separation, within 120 km of pole; these are analysis points, not NASA approvals.
cells=[]
for row in range(2320,5280,80):
 for col in range(2320,5280,80):
  x=(col-3799.5)*80;y=(3799.5-row)*80
  if not 8000<np.hypot(x,y)<120000:continue
  dzdx=(float(grid[row,col+1])-float(grid[row,col-1]))*.5/160
  dzdy=(float(grid[row+1,col])-float(grid[row-1,col]))*.5/160
  slope=float(np.degrees(np.arctan(np.hypot(dzdx,dzdy))))
  if slope<=8:cells.append((float(grid[row,col])*.5,row,col,x,y,slope))
cells.sort(key=lambda c:(-c[0],c[1],c[2]))
selected=[]
for cell in cells:
 if all(np.hypot(cell[3]-other[3],cell[4]-other[4])>=20000 for other in selected):selected.append(cell)
 if len(selected)==13:break
assert len(selected)==13
catalog=[]
for i,(height,row,col,x,y,slope) in enumerate(selected,1):
 lat=float(np.degrees(2*np.arctan(np.hypot(x,y)/(2*R_MOON))-np.pi/2));lon=float(np.degrees(np.arctan2(x,y))%360)
 catalog.append({'site_id':f'lola-sp-{i:03d}','name':f'LOLA South Pole {i:02d}','region':'NASA LOLA south-polar grid',
  'lat_deg':lat,'lon_deg':lon,'elevation_m':height,'grid_slope_deg':slope,'terrain_safety':'unknown',
  'description':f'Actual NASA LOLA cell row {row}, column {col}; 80 m/pixel. Selected by a documented high-ground and spatial-separation rule. Not a NASA-approved landing location.',
  'scientific_significance':'Real terrain analysis point for comparing mission windows using NASA data.',
  'psr_distance_km':None,'annual_data':{},'provenance':'Derived from NASA LRO/LOLA LDEM_80S_80M',
  'source_pixel':{'row':row,'column':col,'product':'LDEM_80S_80M','height_scale':.5},
  'source_url':metadata['sources'][src.name]['url']})
(ROOT/'backend'/'app'/'data'/'nasa_sites.json').write_text(json.dumps(catalog,indent=2),encoding='utf-8')
(ROOT/'data'/'nasa_provenance.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
print('Prepared NASA hillshade, 13 measured analysis locations and provenance',flush=True)
