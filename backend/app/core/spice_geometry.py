"""NASA/JPL SPICE geometry in the exact DE421 lunar frame used by the LOLA DEM."""
from datetime import datetime,timezone
from functools import lru_cache
from threading import RLock
import numpy as np
from app.core.nasa_data import RAW,DataUnavailable,manifest

FRAME='MOON_ME_DE421'
LOCK=RLock()
KERNELS=['naif0012.tls','pck00011.tpc','de421.bsp','moon_pa_de421_1900-2050.bpc','moon_080317.tf']
KERNEL_TYPES={'naif0012.tls':('KPL','LSK'),'pck00011.tpc':('KPL','PCK'),'de421.bsp':('DAF','SPK'),
    'moon_pa_de421_1900-2050.bpc':('DAF','PCK'),'moon_080317.tf':('KPL','FK')}
@lru_cache(maxsize=1)
def spice():
    manifest()
    try:import spiceypy as api
    except ImportError as exc:raise DataUnavailable('Install backend/requirements.txt; spiceypy is required') from exc
    try:
        with LOCK:
            for name in KERNELS:
                if not (RAW/name).is_file():raise DataUnavailable(f'Missing NASA SPICE kernel: {name}')
                if tuple(api.getfat(str(RAW/name)))!=KERNEL_TYPES[name]:
                    raise DataUnavailable('The installed SPICE kernel set is unreadable or incompatible: '+name)
                api.furnsh(str(RAW/name))
            if api.namfrm(FRAME)!=31007:raise DataUnavailable('DE421 lunar frame is unavailable')
    except api.utils.exceptions.SpiceyError as exc:
        raise DataUnavailable('The installed SPICE kernel set is unreadable or incompatible. Reinstall the official kernels using fetch_nasa_data.py.') from exc
    return api

@lru_cache(maxsize=12)
def body_vectors(timestamps):
    api=spice()
    try:
        with LOCK:
            ets=[api.str2et(datetime.fromtimestamp(t,tz=timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')) for t in timestamps]
            sun=np.asarray(api.spkpos('SUN',ets,FRAME,'LT+S','MOON')[0],dtype=float).reshape(-1,3)*1000
            earth=np.asarray(api.spkpos('EARTH',ets,FRAME,'LT+S','MOON')[0],dtype=float).reshape(-1,3)*1000
    except api.utils.exceptions.SpiceyError as exc:
        raise DataUnavailable('SPICE cannot evaluate this UTC interval with the installed kernels: '+str(exc).splitlines()[-2]) from exc
    sun.setflags(write=False);earth.setflags(write=False)
    return sun,earth

def subpoint(vector):
    v=np.asarray(vector,dtype=float)
    return float(np.degrees(np.arctan2(v[2],np.hypot(v[0],v[1])))),float(np.degrees(np.arctan2(v[1],v[0]))%360)

def topocentric_track(lat,lon,height,vectors):
    phi,lam=np.radians([lat,lon])
    up=np.array([np.cos(phi)*np.cos(lam),np.cos(phi)*np.sin(lam),np.sin(phi)])
    east=np.array([-np.sin(lam),np.cos(lam),0])
    north=np.array([-np.sin(phi)*np.cos(lam),-np.sin(phi)*np.sin(lam),np.cos(phi)])
    relative=np.asarray(vectors)-(1737400+height)*up
    norm=np.linalg.norm(relative,axis=1)
    elevation=np.degrees(np.arcsin(np.clip(relative@up/norm,-1,1)))
    azimuth=np.degrees(np.arctan2(relative@east,relative@north))%360
    return azimuth,elevation,norm
