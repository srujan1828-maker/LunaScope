"""Measured LOLA topography and exact input provenance. Missing data is an error."""
from functools import lru_cache
from pathlib import Path
import json,math,re,threading
import numpy as np
from scipy.ndimage import map_coordinates

ROOT=Path(__file__).resolve().parents[3]
RAW=ROOT/'data'/'nasa'
R_MOON=1737400.0
class DataUnavailable(RuntimeError):pass

def manifest():
    path=RAW/'manifest.json'
    if not path.exists():raise DataUnavailable('NASA data is not installed. Run python backend/scripts/fetch_nasa_data.py and python backend/scripts/prepare_nasa_data.py.')
    return json.loads(path.read_text(encoding='utf-8'))

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

def sample_xy(x,y):
    x,y=np.broadcast_arrays(np.asarray(x,dtype=float),np.asarray(y,dtype=float))
    row=3799.5-y/80;col=3799.5+x/80
    if np.any(~np.isfinite(row)) or np.any(~np.isfinite(col)) or np.any(row<0) or np.any(row>7599) or np.any(col<0) or np.any(col>7599):
        raise DataUnavailable('Requested terrain lies outside the downloaded NASA LOLA raster')
    values=map_coordinates(terrain_grid(),[row.ravel(),col.ravel()],order=1,mode='nearest',output=np.float64).reshape(x.shape)*.5
    return float(values) if values.ndim==0 else values

def elevation(lat,lon):return sample_xy(*latlon_to_xy(lat,lon))

def terrain_slope(lat,lon):
    x,y=latlon_to_xy(lat,lon)
    dx=(sample_xy(x+80,y)-sample_xy(x-80,y))/160
    dy=(sample_xy(x,y+80)-sample_xy(x,y-80))/160
    return np.degrees(np.arctan(np.hypot(dx,dy)))

def provenance():
    data=manifest()
    return {'mode':'nasa-official','terrain':'NASA LRO/LOLA LDEM_80S_80M V2.1; measured altimetry gridded at 80 m/pixel',
        'terrain_url':data['sources']['LDEM_80S_80M.JP2']['url'],
        'terrain_sha256':data['sources']['LDEM_80S_80M.JP2']['sha256'],
        'frame':'MOON_ME_DE421','ephemeris':'NASA/JPL NAIF SPICE: DE421 SPK and DE421 lunar orientation',
        'catalog':'Analysis locations deterministically selected from NASA LOLA cells, not official NASA landing-site approvals',
        'limitations':'80 m pixels do not resolve lander-scale hazards. Horizon results use sampled rays and time intervals. Terrain safety and DSN scheduling are not certified.'}

def readiness():
    required=['manifest.json','LDEM_80S_80M.npy','de421.bsp','moon_pa_de421_1900-2050.bpc','moon_080317.tf','naif0012.tls','pck00011.tpc']
    missing=[name for name in required if not (RAW/name).exists()]
    return {'ready':not missing,'mode':'nasa-official','missing_files':missing,'synthetic_fallback':False}
