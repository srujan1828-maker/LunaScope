"""Spherical terrain horizons sampled exclusively from published NASA LOLA measurements."""
from functools import lru_cache
import math
import numpy as np
from app.core.nasa_data import elevation,R_MOON
def evaluate_lunar_terrain_elevation(lat_deg,lon_deg,base_elev_m=None):return elevation(lat_deg,lon_deg)
@lru_cache(maxsize=256)
def _cached_horizon(lat,lon,mast,max_distance,step):
    # Resolution is 80m; no sub-pixel procedural roughness is invented.
    d=np.unique(np.r_[np.arange(80,min(8000,max_distance),80),np.arange(8000,max_distance,step),max_distance])
    angular=d[None,:]/R_MOON;bearing=np.radians(np.arange(360))[:,None]
    phi,lam=np.radians([lat,lon])
    ray_lat=np.arcsin(np.clip(np.sin(phi)*np.cos(angular)+np.cos(phi)*np.sin(angular)*np.cos(bearing),-1,1))
    ray_lon=lam+np.arctan2(np.sin(bearing)*np.sin(angular)*np.cos(phi),np.cos(angular)-np.sin(phi)*np.sin(ray_lat))
    ground=elevation(np.degrees(ray_lat),np.degrees(ray_lon))
    observer=elevation(lat,lon)
    radius=R_MOON+ground
    vertical=radius*np.cos(angular)-(R_MOON+observer+mast)
    horizontal=radius*np.sin(angular)
    return tuple(np.degrees(np.arctan2(vertical,horizontal)).max(axis=1).tolist())
def compute_horizon_360(lat_deg,lon_deg,base_elevation_m=None,mast_height_m=2.0,max_distance_m=150000.0,step_distance_m=500.0):
    values=[lat_deg,lon_deg,mast_height_m,max_distance_m,step_distance_m]
    if not all(math.isfinite(v) for v in values) or not -90<=lat_deg<=-80 or mast_height_m<0 or max_distance_m<80 or step_distance_m<=0:
        raise ValueError('Invalid LOLA horizon inputs')
    return list(_cached_horizon(lat_deg,lon_deg,mast_height_m,max_distance_m,step_distance_m))
