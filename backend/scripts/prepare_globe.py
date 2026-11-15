"""Prepare a longitude-aligned global overview from the original LOLA LDEM_4 label/IMG."""
from pathlib import Path
import json,re,hashlib
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];RAW=ROOT/'data/nasa';ASSETS=ROOT/'frontend/public/assets'
label=(RAW/'LDEM_4.LBL').read_text()
def number(key):return float(re.search(r'^\s*'+key+r'\s*=\s*([-\d.]+)',label,re.M).group(1))
assert 'LSB_INTEGER' in label and 'SIMPLE CYLINDRICAL' in label and 'MEAN EARTH/POLAR AXIS OF DE421' in label
assert number('CENTER_LONGITUDE')==180 and number('WESTERNMOST_LONGITUDE')==0 and number('EASTERNMOST_LONGITUDE')==360
grid=np.fromfile(RAW/'LDEM_4.IMG',dtype='<i2').reshape(int(number('LINES')),int(number('LINE_SAMPLES')))*number('SCALING_FACTOR')/1000
# Original IMG spans 0..360 E; the NASA color mosaic spans -180..180 E.
grid=np.roll(grid,grid.shape[1]//2,axis=1)
overview=grid.reshape(180,4,360,4).mean(axis=(1,3));low=float(grid.min());high=float(grid.max())
Image.fromarray(np.round((grid-low)/(high-low)*255).astype('uint8')).save(ASSETS/'moon-global-bump.png')
(ASSETS/'moon-global-height.json').write_text(json.dumps({'width':360,'height':180,'heights_km':np.round(overview,5).ravel().tolist(),'source':'NASA LOLA LDEM_4 V3.0','source_pixel_spacing_deg':.25,'overview_spacing_deg':1,'height_range_km':[low,high],'reference_radius_km':number('OFFSET')/1000,'frame':'MOON_ME_DE421'},separators=(',',':')))
record={'dataset':'LDEM_4 V3.0','use':'Whole-Moon shape and shading overview; local mission analysis retains LDEM_80S_80M',
    'source_pixel_spacing_deg':number('MAP_RESOLUTION')**-1,'overview_spacing_deg':1,'height_scale_m':number('SCALING_FACTOR'),
    'reference_radius_m':number('OFFSET'),'frame':'MOON_ME_DE421','files':{}}
for name in ['LDEM_4.LBL','LDEM_4.IMG']:
    data=(RAW/name).read_bytes();record['files'][name]={'url':'https://imbrium.mit.edu/DATA/LOLA_GDR/CYLINDRICAL/IMG/'+name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
(ROOT/'data/moon_global_dem_provenance.json').write_text(json.dumps(record,indent=2))
print('Prepared actual global LOLA overview:',overview.shape,'range km:',low,high)
