"""Measured LOLA topography and exact input provenance. Missing data is an error."""
from functools import lru_cache
from pathlib import Path
import json,re,os
import numpy as np
from scipy.ndimage import map_coordinates

ROOT=Path(__file__).resolve().parents[3]
RAW=Path(os.environ.get('LUNASCOPE_DATA_DIR',str(ROOT/'data'/'nasa'))).expanduser().resolve()
R_MOON=1737400.0
class DataUnavailable(RuntimeError):pass

def manifest():
    path=RAW/'manifest.json'
    if not path.exists():raise DataUnavailable('NASA data is not installed. Run python backend/scripts/fetch_nasa_data.py and python backend/scripts/prepare_nasa_data.py.')
    return json.loads(path.read_text(encoding='utf-8'))

@lru_cache(maxsize=1)
def terrain_metadata():
    """Read the installed product label rather than infer georeferencing from its name."""
    path=RAW/'LDEM_80S_80M_JP2.LBL'
    if not path.exists():raise DataUnavailable('The original NASA PDS terrain label is missing')
    label=path.read_text()
    def number(key):
        match=re.search(r'^\s*'+key+r'\s*=\s*([+\-\d.]+)',label,re.M)
        if not match:raise DataUnavailable(f'PDS metadata is missing {key}')
        return float(match.group(1))
    if 'POLAR STEREOGRAPHIC' not in label or 'MEAN EARTH/POLAR AXIS OF DE421' not in label:
        raise DataUnavailable('Unsupported lunar terrain projection or reference frame')
    return {'id':'lola80','dataset':'NASA LRO/LOLA LDEM_80S_80M','version':'V2.1',
        'frame':'MOON_ME_DE421','projection':'South polar stereographic','units':'m',
        'pixel_scale_m':number('MAP_SCALE'),'height_scale':number('SCALING_FACTOR'),
        'reference_radius_m':number('OFFSET'),'line_offset':number('LINE_PROJECTION_OFFSET'),
        'sample_offset':number('SAMPLE_PROJECTION_OFFSET'),'nodata':-32768,
        'height_uncertainty_m':None,'effective_resolution_m':None,
        'source_url':manifest()['sources']['LDEM_80S_80M.JP2']['url']}

@lru_cache(maxsize=1)
def terrain_grid():
    manifest()
    path=RAW/'LDEM_80S_80M.npy'
    if not path.exists():raise DataUnavailable('The official LOLA raster has not been prepared. Run python backend/scripts/prepare_nasa_data.py.')
    grid=np.load(path,mmap_mode='r')
    if grid.shape!=(7600,7600):raise DataUnavailable('LOLA raster dimensions do not match the published PDS label')
    return grid

def latlon_to_xy(lat,lon):
    lat=np.asarray(lat,dtype=float);lon=np.asarray(lon,dtype=float)
    r=2*R_MOON*np.tan(np.pi/4+np.radians(lat)/2)
    return r*np.sin(np.radians(lon)),r*np.cos(np.radians(lon))

def sample_xy(x,y,allow_missing=False):
    x,y=np.broadcast_arrays(np.asarray(x,dtype=float),np.asarray(y,dtype=float))
    meta=terrain_metadata();spacing=meta['pixel_scale_m']
    row=meta['line_offset']-y/spacing;col=meta['sample_offset']+x/spacing
    invalid=~np.isfinite(row)|~np.isfinite(col)|(row<0)|(row>7599)|(col<0)|(col>7599)
    if np.any(invalid) and not allow_missing:
        raise DataUnavailable('Requested terrain lies outside the downloaded NASA LOLA raster')
    grid=terrain_grid()
    coords=[np.nan_to_num(row).clip(0,7599).ravel(),np.nan_to_num(col).clip(0,7599).ravel()]
    values=map_coordinates(grid,coords,order=1,mode='nearest',output=np.float64).reshape(x.shape)*meta['height_scale']
    # A bilinear footprint touching NoData is unknown, never an invented height.
    for dr,dc in [(0,0),(0,1),(1,0),(1,1)]:
        rr=np.clip(np.floor(np.nan_to_num(row)).astype(int)+dr,0,7599)
        cc=np.clip(np.floor(np.nan_to_num(col)).astype(int)+dc,0,7599)
        invalid|=grid[rr,cc]==meta['nodata']
    values=np.where(invalid,np.nan,values)
    if not allow_missing and np.any(~np.isfinite(values)):raise DataUnavailable('NASA terrain contains NoData at the requested location')
    return float(values) if values.ndim==0 else values

def elevation(lat,lon):return sample_xy(*latlon_to_xy(lat,lon))

def terrain_slope(lat,lon):
    x,y=latlon_to_xy(lat,lon)
    dx=(sample_xy(x+80,y)-sample_xy(x-80,y))/160
    dy=(sample_xy(x,y+80)-sample_xy(x,y-80))/160
    return np.degrees(np.arctan(np.hypot(dx,dy)))

def provenance():
    data=manifest()
    from datetime import datetime,timezone
    return {'mode':'nasa-official','terrain':'NASA LRO/LOLA LDEM_80S_80M V2.1; measured altimetry gridded at 80 m/pixel',
        'terrain_url':data['sources']['LDEM_80S_80M.JP2']['url'],
        'terrain_sha256':data['sources']['LDEM_80S_80M.JP2']['sha256'],
        'frame':'MOON_ME_DE421','ephemeris':'NASA/JPL NAIF SPICE: DE421 SPK and DE421 lunar orientation',
        'catalog':'Analysis locations deterministically selected from NASA LOLA cells, not official NASA landing-site approvals',
        'limitations':'80 m pixels do not resolve lander-scale hazards. Horizon results use sampled rays and time intervals. Terrain safety and DSN scheduling are not certified.',
        'dataset_version':'LDEM_80S_80M V2.1','terrain_resolution_m':80,'projection':'South polar stereographic, lunar radius 1737400 m',
        'kernel_files':{name:record for name,record in data['sources'].items() if name.endswith(('.bsp','.bpc','.tf','.tls','.tpc'))},
        'calculated_at_utc':datetime.now(timezone.utc).isoformat(),
        'data_categories':{'terrain':'REAL DATA (gridded/interpolated altimetry)','directions':'CALCULATED from SPICE','horizons_and_visibility':'APPROXIMATION (sampled spherical geometry)','power_hardware':'USER ASSUMPTIONS'},
        'height_uncertainty_m':None,'effective_resolution_m':None}

def readiness():
    required=['manifest.json','LDEM_80S_80M.npy','de421.bsp','moon_pa_de421_1900-2050.bpc','moon_080317.tf','naif0012.tls','pck00011.tpc']
    missing=[name for name in required if not (RAW/name).exists()]
    return {'ready':not missing,'mode':'nasa-official','missing_files':missing,'synthetic_fallback':False}
