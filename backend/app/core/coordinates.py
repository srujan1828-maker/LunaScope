"""
Lunar coordinate transformations between Selenographic (lat, lon) and South Polar Stereographic (X, Y).
Reference: NASA LRO LOLA & JPL NAIF standard Moon Mean Earth / Polar Axis frame (MOON_ME).
"""

import math
from typing import Tuple

R_MOON: float = 1737400.0  # Mean lunar radius in meters (1737.4 km)


def latlon_to_stereo(lat_deg: float, lon_deg: float) -> Tuple[float, float]:
    """
    Convert selenographic coordinates (latitude, longitude) in degrees
    to South Polar Stereographic coordinates (X, Y) in meters.
    
    Standard convention:
      - Latitude: South is negative (-90° at pole, -80° at edge of polar region).
      - Longitude: East positive [0°, 360°) or [-180°, +180°].
      - X points towards longitude 90°E.
      - Y points towards longitude 0° (Prime Meridian).
    """
    phi = math.radians(lat_deg)
    lam = math.radians(lon_deg)
    
    # Colatitude angle from south pole: (pi/2 + phi)
    colat = math.pi / 2.0 + phi
    if colat < 0.0:
        colat = 0.0
    
    r = 2.0 * R_MOON * math.tan(colat / 2.0)
    x = r * math.sin(lam)
    y = r * math.cos(lam)
    return float(x), float(y)


def stereo_to_latlon(x: float, y: float) -> Tuple[float, float]:
    """
    Convert South Polar Stereographic coordinates (X, Y) in meters
    back to selenographic (latitude, longitude) in degrees.
    """
    r = math.hypot(x, y)
    if r == 0.0:
        return -90.0, 0.0
    
    colat = 2.0 * math.atan(r / (2.0 * R_MOON))
    lat_rad = colat - math.pi / 2.0
    lon_rad = math.atan2(x, y)
    
    lat_deg = math.degrees(lat_rad)
    lon_deg = (math.degrees(lon_rad) + 360.0) % 360.0
    return float(lat_deg), float(lon_deg)


def surface_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in meters between two points on the lunar sphere."""
    phi1, lam1 = math.radians(lat1), math.radians(lon1)
    phi2, lam2 = math.radians(lat2), math.radians(lon2)
    
    dphi = phi2 - phi1
    dlam = lam2 - lam1
    
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2.0) ** 2
    a = min(1.0, max(0.0, a))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return float(R_MOON * c)
