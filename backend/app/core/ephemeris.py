"""Sun/Earth ephemerides from official NASA/JPL SPICE kernels, with no analytic fallback."""
from datetime import datetime,timezone
import math
import numpy as np
from app.core.spice_geometry import body_vectors,subpoint,topocentric_track
from app.core.nasa_data import elevation
AU_METERS=149597870700.0
R_MOON=1737400.0
R_SUN_METERS=696340000.0
R_EARTH_METERS=6371000.0
MEAN_LUNAR_DIST_METERS=384400000.0
SOLAR_RADIUS_DEG=.266
EARTH_RADIUS_DEG=.950
LUNAR_OBLIQUITY_DEG=1.55
LIB_LON_AMP_DEG=8.2
LIB_LAT_AMP_DEG=7.0
def datetime_to_jd(dt):return dt.timestamp()/86400+2440587.5
def get_subsolar_coordinates(unix_time):return subpoint(body_vectors((float(unix_time),))[0][0])
def get_subearth_coordinates(unix_time):
    lat,lon=subpoint(body_vectors((float(unix_time),))[1][0])
    return lat,(lon+180)%360-180
def body_cartesian_vector(lat_deg,lon_deg,distance_m=1.0):
    phi,lam=np.radians([lat_deg,lon_deg]);return np.array([np.cos(phi)*np.cos(lam),np.cos(phi)*np.sin(lam),np.sin(phi)])*distance_m
def topocentric_az_el(site_lat_deg,site_lon_deg,body_lat_deg,body_lon_deg,body_distance_m=AU_METERS,site_elevation_m=0):
    az,el,_=topocentric_track(site_lat_deg,site_lon_deg,site_elevation_m,body_cartesian_vector(body_lat_deg,body_lon_deg,body_distance_m).reshape(1,3))
    return float(az[0]),float(el[0])
def compute_ephemeris_track(site_lat_deg,site_lon_deg,start_unix,end_unix,step_seconds=3600.0,site_elevation_m=None):
    if not all(math.isfinite(v) for v in [start_unix,end_unix,step_seconds]) or step_seconds<=0 or end_unix<start_unix:
        raise ValueError('Invalid ephemeris interval')
    times=tuple(np.arange(start_unix,end_unix+1e-3,step_seconds).tolist())
    sun,earth=body_vectors(times)
    height=elevation(site_lat_deg,site_lon_deg) if site_elevation_m is None else site_elevation_m
    saz,sel,sd=topocentric_track(site_lat_deg,site_lon_deg,height,sun)
    eaz,eel,ed=topocentric_track(site_lat_deg,site_lon_deg,height,earth)
    return {'timestamps':list(times),'sun_azimuth':saz.tolist(),'sun_elevation':sel.tolist(),
        'earth_azimuth':eaz.tolist(),'earth_elevation':eel.tolist(),
        'solar_flux_w_m2':(1361/(sd/AU_METERS)**2).tolist(),
        'solar_angular_radius_deg':np.degrees(np.arcsin(R_SUN_METERS/sd)).tolist(),
        'earth_distance_m':ed.tolist(),'frame':'MOON_ME_DE421','aberration_correction':'LT+S'}
