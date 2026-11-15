"""Sampled spherical terrain horizons, local compass bearings and obstruction points."""
from functools import lru_cache
import math
import numpy as np
from app.core.nasa_data import R_MOON,DataUnavailable
from app.core.terrain import combined_elevation,finite_list,source_info


def evaluate_lunar_terrain_elevation(lat_deg,lon_deg,base_elev_m=None):
    value=float(combined_elevation(lat_deg,lon_deg))
    if not np.isfinite(value):raise DataUnavailable('Missing terrain at observer')
    return value


@lru_cache(maxsize=128)
def horizon_profile(lat,lon,mast=2.,max_distance=150000.,step=500.,source='lola80'):
    if not all(math.isfinite(v) for v in [lat,lon,mast,max_distance,step]) or not -90<=lat<=-80 or mast<0 or max_distance<80 or step<=0:
        raise ValueError('Invalid LOLA horizon inputs')
    resolution=source_info(source)['pixel_scale_m'];near=max(5.,min(80.,resolution))
    d=np.unique(np.r_[np.arange(near,min(8000,max_distance),near),np.arange(8000,max_distance,step),max_distance])
    angular=d[None,:]/R_MOON;bearing=np.radians(np.arange(360))[:,None]
    phi,lam=np.radians([lat,lon])
    ray_lat=np.arcsin(np.clip(np.sin(phi)*np.cos(angular)+np.cos(phi)*np.sin(angular)*np.cos(bearing),-1,1))
    ray_lon=lam+np.arctan2(np.sin(bearing)*np.sin(angular)*np.cos(phi),np.cos(angular)-np.sin(phi)*np.sin(ray_lat))
    latitudes,longitudes=np.degrees(ray_lat),np.degrees(ray_lon)%360
    ground=combined_elevation(latitudes,longitudes,source)
    observer=float(combined_elevation(lat,lon,source))
    if not np.isfinite(observer):raise DataUnavailable('Missing terrain at observer; horizon unknown')
    radius=R_MOON+ground
    angles=np.degrees(np.arctan2(radius*np.cos(angular)-(R_MOON+observer+mast),radius*np.sin(angular)))
    complete=np.all(np.isfinite(ground),axis=1)
    indices=np.argmax(np.where(np.isfinite(angles),angles,-np.inf),axis=1);rows=np.arange(360)
    skyline=angles[rows,indices];skyline[~complete]=np.nan
    points=[]
    for i,j in enumerate(indices):
        points.append({'azimuth_deg':i,'known':bool(complete[i]),'horizon_elevation_deg':float(skyline[i]) if complete[i] else None,
            'distance_m':float(d[j]) if complete[i] else None,'lat_deg':float(latitudes[i,j]) if complete[i] else None,
            'lon_deg':float(longitudes[i,j]) if complete[i] else None,'elevation_m':float(ground[i,j]) if complete[i] else None})
    return {'elevations_deg':finite_list(skyline,8),'obstruction_points':points,'coverage':'complete' if complete.all() else 'incomplete',
        'known_azimuth_fraction':float(complete.mean()),'azimuth_spacing_deg':1,'ray_limit_m':max_distance,
        'near_spacing_m':near,'far_spacing_m':step,'observer_elevation_m':observer,'mast_height_m':mast,
        'reference_meridian_deg':lon if lat==-90 else None,
        'compass_convention':'Clockwise from local north toward east. At the exact south pole north follows the selected longitude meridian.',
        'sources':[source_info(source)] if source=='lola80' else [source_info(source),source_info('lola80')],
        'method':'Spherical great-circle rays, terrain vectors projected into observer east/north/up; sampled azimuth maxima.',
        'limitations':'1-degree angular sampling and finite radial sampling can miss narrow ridges; NoData sectors remain unknown.'}


def compute_horizon_360(lat_deg,lon_deg,base_elevation_m=None,mast_height_m=2.0,max_distance_m=150000.0,step_distance_m=500.0):
    return horizon_profile(lat_deg,lon_deg,mast_height_m,max_distance_m,step_distance_m)['elevations_deg'].copy()
