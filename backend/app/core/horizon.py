"""
Approximate Topographic Horizon Raycaster for Lunar South Pole Operations.
Raymarches along 360 azimuths up to 120 km away accounting for true lunar spherical
curvature drop (d^2 / 2R), crater rim massifs, and user-configured mast/antenna heights.
"""

import math
from typing import Dict, List, Tuple
import numpy as np

from app.core.coordinates import R_MOON, surface_distance_m

# Assumed landmark parameters used only to construct demonstration terrain
LUNAR_SOUTH_POLE_LANDMARKS = [
    {
        "name": "Malapert Massif Peak",
        "lat": -85.99, "lon": 0.05,
        "elevation_m": 5050.0,
        "sigma_major_m": 35000.0, "sigma_minor_m": 22000.0,
        "theta_deg": 45.0
    },
    {
        "name": "Shackleton Crater Rim Crest",
        "lat": -89.70, "lon": 128.00,
        "elevation_m": 1450.0,
        "sigma_major_m": 12000.0, "sigma_minor_m": 10000.0,
        "theta_deg": 0.0
    },
    {
        "name": "Connecting Ridge High Massif",
        "lat": -89.44, "lon": 222.70,
        "elevation_m": 1920.0,
        "sigma_major_m": 15000.0, "sigma_minor_m": 7000.0,
        "theta_deg": 120.0
    },
    {
        "name": "Nobile Western Massif",
        "lat": -85.25, "lon": 35.80,
        "elevation_m": 3700.0,
        "sigma_major_m": 28000.0, "sigma_minor_m": 18000.0,
        "theta_deg": 80.0
    },
    {
        "name": "Leibnitz Beta Ridge",
        "lat": -85.80, "lon": 330.50,
        "elevation_m": 4400.0,
        "sigma_major_m": 30000.0, "sigma_minor_m": 20000.0,
        "theta_deg": 30.0
    },
    {
        "name": "Amundsen North Wall",
        "lat": -84.50, "lon": 85.00,
        "elevation_m": 2100.0,
        "sigma_major_m": 25000.0, "sigma_minor_m": 15000.0,
        "theta_deg": 15.0
    },
    {
        "name": "Faustini Eastern Rim",
        "lat": -87.18, "lon": 84.34,
        "elevation_m": 1240.0,
        "sigma_major_m": 16000.0, "sigma_minor_m": 10000.0,
        "theta_deg": 90.0
    },
    {
        "name": "de Gerlache Eastern Rim",
        "lat": -88.71, "lon": 291.62,
        "elevation_m": 750.0,
        "sigma_major_m": 14000.0, "sigma_minor_m": 8000.0,
        "theta_deg": 40.0
    },
    # Deep Crater Depressions
    {
        "name": "Haworth Crater Deep Floor",
        "lat": -87.87, "lon": 354.71,
        "elevation_m": -320.0,
        "sigma_major_m": 20000.0, "sigma_minor_m": 16000.0,
        "theta_deg": 0.0
    },
    {
        "name": "Slater Basin Depression",
        "lat": -88.10, "lon": 115.00,
        "elevation_m": -1100.0,
        "sigma_major_m": 22000.0, "sigma_minor_m": 18000.0,
        "theta_deg": 60.0
    }
]


def evaluate_lunar_terrain_elevation(lat_deg: float, lon_deg: float, base_elev_m: float) -> float:
    """
    Evaluates realistic lunar south polar elevation at any (lat, lon)
    using multi-scale elliptical massifs and crater rim topography.
    """
    elev = base_elev_m

    for lm in LUNAR_SOUTH_POLE_LANDMARKS:
        d_m = surface_distance_m(lat_deg, lon_deg, lm["lat"], lm["lon"])
        if d_m < 120000.0:  # within 120 km reach
            # Rotated 2D Gaussian profile
            sigma = (lm["sigma_major_m"] + lm["sigma_minor_m"]) / 2.0
            weight = math.exp(-0.5 * (d_m / sigma) ** 2)
            elev += (lm["elevation_m"] - base_elev_m) * weight * 0.70

    # High-frequency crater rim harmonics
    lam = math.radians(lon_deg)
    phi = math.radians(lat_deg)
    micro_relief = (
        95.0 * math.sin(5.0 * lam + 2.0 * phi)
        + 60.0 * math.cos(11.0 * lam - 4.0 * phi)
        + 35.0 * math.sin(23.0 * lam)
    )
    return elev + micro_relief


def _terrain_array(lat, lon, base):
    """Vectorized procedural surface. All landmarks remain demonstration inputs."""
    phi, lam = np.radians(lat), np.radians(lon)
    z = np.zeros_like(phi) + base
    for lm in LUNAR_SOUTH_POLE_LANDMARKS:
        p2, l2 = np.radians(lm['lat']), np.radians(lm['lon'])
        a = np.sin((phi-p2)/2)**2 + np.cos(phi)*np.cos(p2)*np.sin((lam-l2)/2)**2
        d = 2*R_MOON*np.arcsin(np.sqrt(np.clip(a,0,1)))
        sigma = (lm['sigma_major_m']+lm['sigma_minor_m'])/2
        z += (lm['elevation_m']-base)*0.70*np.exp(-0.5*(d/sigma)**2)
    return z + 95*np.sin(5*lam+2*phi)+60*np.cos(11*lam-4*phi)+35*np.sin(23*lam)


from functools import lru_cache

@lru_cache(maxsize=256)
def _cached_horizon(lat_deg, lon_deg, base_elevation_m, mast_height_m, max_distance_m, step_distance_m):
    # Great-circle destination remains defined at the pole and across longitude wrap.
    d = np.unique(np.r_[np.geomspace(20, min(1000,max_distance_m),40),
                         np.arange(step_distance_m,max_distance_m,step_distance_m), max_distance_m])
    angular = d[None,:]/R_MOON
    bearing = np.radians(np.arange(360))[:,None]
    phi, lam = np.radians(lat_deg), np.radians(lon_deg)
    lat = np.arcsin(np.clip(np.sin(phi)*np.cos(angular)+np.cos(phi)*np.sin(angular)*np.cos(bearing),-1,1))
    lon = lam + np.arctan2(np.sin(bearing)*np.sin(angular)*np.cos(phi), np.cos(angular)-np.sin(phi)*np.sin(lat))
    surface = _terrain_array(np.degrees(lat), np.degrees(lon), base_elevation_m)
    observer_surface = float(_terrain_array(np.asarray(lat_deg), np.asarray(lon_deg), base_elevation_m))
    # Absolute datum is normalized to the observer; spherical ray geometry, no smoothing.
    radius = R_MOON + base_elevation_m + surface-observer_surface
    vertical = radius*np.cos(angular)-(R_MOON+base_elevation_m+mast_height_m)
    horizontal = radius*np.sin(angular)
    return tuple(np.degrees(np.arctan2(vertical,horizontal)).max(axis=1).tolist())


def compute_horizon_360(lat_deg, lon_deg, base_elevation_m, mast_height_m=2.0,
                        max_distance_m=120000.0, step_distance_m=1000.0):
    """360 local compass skyline samples from a procedural surface, not NASA LOLA.

    Samples nearby terrain from 20m, then up to 120km. This is a demonstration
    horizon with spherical geometry; no claim of actual lunar terrain accuracy.
    """
    if not all(math.isfinite(v) for v in [lat_deg,lon_deg,base_elevation_m,mast_height_m,max_distance_m,step_distance_m]):
        raise ValueError('Horizon inputs must be finite')
    if not -90 <= lat_deg <= 90 or mast_height_m < 0 or max_distance_m < 20 or step_distance_m <= 0:
        raise ValueError('Invalid horizon geometry')
    return list(_cached_horizon(lat_deg,lon_deg,base_elevation_m,mast_height_m,max_distance_m,step_distance_m))
