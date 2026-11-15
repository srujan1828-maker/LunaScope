"""Terrain disk quadrature, Earth-center geometry and duration-weighted metrics.

Uniform circular disk approximation in the local angular tangent plane. No atmosphere.
Unknown sectors propagate as None and operational state zero, never darkness or Pass.
"""
import numpy as np
from app.core.ephemeris import SOLAR_RADIUS_DEG

NODES,WEIGHTS=np.polynomial.legendre.leggauss(48)


def interpolate_horizon(azimuth,horizon):
    h=np.asarray(horizon,dtype=float)
    return np.interp(np.asarray(azimuth)%360,np.arange(len(h)+1)*360/len(h),np.r_[h,h[0]])


def fractional_solar_visibility(sun_az_deg,sun_el_deg,horizon_360,limb_darkening=False,angular_radius_deg=SOLAR_RADIUS_DEG):
    az,el,r=np.broadcast_arrays(np.asarray(sun_az_deg,dtype=float),np.asarray(sun_el_deg,dtype=float),np.asarray(angular_radius_deg,dtype=float))
    offsets=r[...,None]*NODES
    az_offsets=offsets/np.maximum(.01,np.cos(np.radians(el)))[...,None]
    horizon=interpolate_horizon(az[...,None]+az_offsets,horizon_360)
    half=np.sqrt(np.maximum(0,r[...,None]**2-offsets**2))
    low=el[...,None]-half;high=el[...,None]+half
    length=np.clip(high-np.maximum(horizon,low),0,2*half)
    if limb_darkening:
        c=.6;yc=np.clip(horizon-el[...,None],-half,half)
        root=np.sqrt(np.maximum(0,half**2-yc**2))
        area=.5*(half**2*(np.pi/2-np.arcsin(np.clip(yc/np.maximum(half,1e-20),-1,1)))-yc*root)
        integral=(1-c)*length+c*area/r[...,None]
        full_integral=(1-c)*2*half+c*(np.pi*.5*half**2)/r[...,None]
        fractions=np.sum(integral*WEIGHTS,axis=-1)/np.sum(full_integral*WEIGHTS,axis=-1)
    else:fractions=np.sum(length*WEIGHTS,axis=-1)/np.sum(2*half*WEIGHTS,axis=-1)
    full=np.all(horizon<=low,axis=-1);blocked=np.all(horizon>=high,axis=-1)
    fractions=np.where(full,1,np.where(blocked,0,np.clip(fractions,0,1)))
    return [round(float(f),6) if np.isfinite(f) else None for f in np.atleast_1d(fractions)]


def evaluate_dte_visibility(earth_az_deg,earth_el_deg,horizon_360,margin_deg=0.):
    margin=np.asarray(earth_el_deg)-interpolate_horizon(earth_az_deg,horizon_360)-margin_deg
    return [int(v>0) if np.isfinite(v) else None for v in np.atleast_1d(margin)]


def classify_operational_states(solar_fractions,dte_visibility,sun_threshold=.10):
    return [0 if f is None or c is None or not np.isfinite(f) else (1 if f>=sun_threshold and c else 2 if f>=sun_threshold else 3 if c else 4)
        for f,c in zip(solar_fractions,dte_visibility)]


def compute_interval_metrics(solar_fractions,dte_visibility,step_hours=1.,sun_threshold=.10,sample_hours=None):
    if len(solar_fractions)!=len(dte_visibility):raise ValueError('Mismatched visibility arrays')
    weights=np.asarray(sample_hours if sample_hours is not None else [step_hours]*len(solar_fractions),dtype=float)
    if len(weights)!=len(solar_fractions) or np.any(~np.isfinite(weights)) or np.any(weights<0):raise ValueError('Invalid interval durations')
    total=float(weights.sum());fractions=np.asarray(solar_fractions,dtype=float);contacts=np.asarray(dte_visibility,dtype=float)
    known=np.isfinite(fractions)&np.isfinite(contacts);sun=fractions>=sun_threshold;earth=contacts==1
    def longest(mask):
        best=current=0.
        for active,hours in zip(mask&known,weights):
            if hours==0:continue
            current=current+hours if active else 0.;best=max(best,current)
        return float(best)
    def pct(mask):return float(weights[mask&known].sum())/total*100 if total else None
    complete=bool(np.all(known|(weights==0))) and total>0
    return {'total_duration_hours':total,'sun_availability_pct':pct(sun) if complete else None,
        'equivalent_sun_hours':float(np.dot(np.nan_to_num(fractions),weights)) if complete else None,
        'longest_shadow_gap_hours':longest(~sun) if complete else None,'earth_availability_pct':pct(earth) if complete else None,
        'longest_earth_outage_hours':longest(~earth) if complete else None,'joint_availability_pct':pct(sun&earth) if complete else None,
        'longest_joint_window_hours':longest(sun&earth) if complete else None,'coverage':'complete' if complete else 'unknown',
        'known_duration_hours':float(weights[known].sum()),'unknown_duration_hours':float(weights[~known].sum())}
