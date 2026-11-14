"""LunaScope Coordinate Projections: Lunar Selenographic <-> South Polar Stereographic.

Uses the IAU standard Moon sphere radius R_MOON = 1,737,400 meters.
Conforms to standard LOLA (Lunar Orbiter Laser Altimeter) polar stereographic projection
centered at the South Pole (-90 deg lat).
"""

from typing import Tuple, Union
import numpy as np

R_MOON: float = 1737400.0  # meters (IAU mean lunar radius)


def latlon_to_xy(
    lat_deg: Union[float, np.ndarray],
    lon_deg: Union[float, np.ndarray],
    r_moon: float = R_MOON,
    lon_0: float = 0.0,
) -> Tuple[Union[float, np.ndarray], Union[float, np.ndarray]]:
    """Convert Selenographic latitude and longitude (degrees) to South Polar Stereographic (meters).

    Origin (0, 0) is at the South Pole (-90 deg).
    +Y axis points along lon_0 (default 0 deg longitude).
    +X axis points along lon_0 + 90 deg (90 deg E).

    Args:
        lat_deg: Latitude in degrees (typically negative in south pole region, e.g. -85 to -90).
        lon_deg: Longitude in degrees (-180 to 180 or 0 to 360).
        r_moon: Lunar radius in meters (default 1737400.0).
        lon_0: Reference longitude meridian in degrees (default 0.0).

    Returns:
        (x, y) coordinates in meters.
    """
    lat = np.asarray(lat_deg, dtype=np.float64)
    lon = np.asarray(lon_deg, dtype=np.float64)

    # Colatitude from south pole: colat = 90 + lat (in degrees)
    # At lat = -90 (South Pole), colat = 0 deg.
    colat_rad = np.radians(np.clip(90.0 + lat, 0.0, 90.0))
    lon_diff_rad = np.radians(lon - lon_0)

    # Polar stereographic radial distance from south pole
    # r = 2 * R * tan(colat / 2)
    r = 2.0 * r_moon * np.tan(colat_rad / 2.0)

    x = r * np.sin(lon_diff_rad)
    y = r * np.cos(lon_diff_rad)

    if np.isscalar(lat_deg) and np.isscalar(lon_deg):
        return float(x), float(y)
    return x, y


def xy_to_latlon(
    x_m: Union[float, np.ndarray],
    y_m: Union[float, np.ndarray],
    r_moon: float = R_MOON,
    lon_0: float = 0.0,
) -> Tuple[Union[float, np.ndarray], Union[float, np.ndarray]]:
    """Convert South Polar Stereographic (meters) to Selenographic latitude and longitude (degrees).

    Args:
        x_m: X coordinate in meters.
        y_m: Y coordinate in meters.
        r_moon: Lunar radius in meters (default 1737400.0).
        lon_0: Reference longitude meridian in degrees (default 0.0).

    Returns:
        (lat_deg, lon_deg) in degrees.
    """
    x = np.asarray(x_m, dtype=np.float64)
    y = np.asarray(y_m, dtype=np.float64)

    r = np.sqrt(x**2 + y**2)

    # colat_rad = 2 * arctan(r / (2 * R_MOON))
    colat_rad = 2.0 * np.arctan(r / (2.0 * r_moon))
    lat_deg = np.degrees(colat_rad) - 90.0

    # lon_diff_rad = arctan2(x, y)
    lon_diff_rad = np.arctan2(x, y)
    lon_deg = np.degrees(lon_diff_rad) + lon_0

    # Normalize longitude to [-180, 180]
    lon_deg = (lon_deg + 180.0) % 360.0 - 180.0

    if np.isscalar(x_m) and np.isscalar(y_m):
        return float(lat_deg), float(lon_deg)
    return lat_deg, lon_deg


def great_circle_distance(
    lat1_deg: Union[float, np.ndarray],
    lon1_deg: Union[float, np.ndarray],
    lat2_deg: Union[float, np.ndarray],
    lon2_deg: Union[float, np.ndarray],
    r_moon: float = R_MOON,
) -> Union[float, np.ndarray]:
    """Calculate great circle distance (arc length in meters) between two points on the Moon."""
    phi1 = np.radians(lat1_deg)
    phi2 = np.radians(lat2_deg)
    dphi = phi2 - phi1
    dlambda = np.radians(lon2_deg - lon1_deg)

    a = np.sin(dphi / 2.0)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2.0)**2
    c = 2.0 * np.arctan2(np.sqrt(a), np.sqrt(1.0 - a))
    dist = r_moon * c

    if np.isscalar(lat1_deg) and np.isscalar(lat2_deg):
        return float(dist)
    return dist
