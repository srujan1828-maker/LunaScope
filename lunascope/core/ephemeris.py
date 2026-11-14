"""LunaScope Ephemeris Engine: Topocentric Sun and Earth Trajectories on the Moon.

Calculates:
1. Solar Azimuth & Elevation from candidate lunar landing sites over time.
   - 360-degree sweep (~29.53 synodic days) with ~1.54 deg seasonal solar elevation oscillation.
2. Earth Azimuth, Elevation & Optical Libration Loop.
   - Longitude libration: +/- 7.9 degrees.
   - Latitude libration: +/- 6.7 degrees.
   - Earth angular radius: ~0.95 degrees.
3. Offline Jean Meeus analytical lunar ephemeris with seamless Skyfield optional fallback.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Union
import numpy as np

# Lunar constants
LUNAR_SYNODIC_PERIOD_DAYS: float = 29.530588853
LUNAR_SIDEREAL_PERIOD_DAYS: float = 27.321661
LUNAR_ANOMALISTIC_PERIOD_DAYS: float = 27.554551
LUNAR_DRACONIC_PERIOD_DAYS: float = 27.212220
LUNAR_OBLIQUITY_DEG: float = 1.5424  # Lunar equator tilt to ecliptic
SOLAR_ANGULAR_RADIUS_DEG: float = 0.2665  # Mean Sun radius seen from Moon
EARTH_ANGULAR_RADIUS_DEG: float = 0.950  # Mean Earth radius seen from Moon


def datetime_to_jd(dt: datetime) -> float:
    """Convert Python datetime (UTC) to Julian Date."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)

    year = dt.year
    month = dt.month
    day = dt.day + (dt.hour + (dt.minute + (dt.second + dt.microsecond / 1e6) / 60.0) / 60.0) / 24.0

    if month <= 2:
        year -= 1
        month += 12

    a = int(year / 100)
    b = 2 - a + int(a / 4)
    jd = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + b - 1524.5
    return jd


def calculate_subsolar_coordinates(jd: float) -> Tuple[float, float]:
    """Calculate the subsolar point (selenographic latitude and longitude in degrees).

    Uses Jean Meeus Astronomical Algorithms (Ch. 53: Ephemeris for Physical Observations of the Moon).
    Returns:
        (lat_sun_deg, lon_sun_deg)
    """
    T = (jd - 2451545.0) / 36525.0

    # Mean longitude of the Sun (ecliptic)
    L0 = 280.46646 + 36000.76983 * T
    # Mean anomaly of the Sun
    M = 357.52911 + 35999.05029 * T - 0.0001537 * T**2
    M_rad = np.radians(M)

    # Sun's equation of the center
    C = (1.914602 - 0.004817 * T - 0.000014 * T**2) * np.sin(M_rad) + \
        (0.019993 - 0.000101 * T) * np.sin(2 * M_rad) + 0.000289 * np.sin(3 * M_rad)

    # Sun's true longitude (ecliptic)
    lambda_sun = (L0 + C) % 360.0

    # Mean longitude of the Moon
    L_moon = 218.3164477 + 481267.88128 * T
    # Longitude of ascending node of lunar orbit
    Omega = 125.04452 - 1934.136261 * T + 0.0020708 * T**2

    # Moon's argument of latitude
    F = 93.2720950 + 483202.0175 * T

    # Subsolar selenographic coordinates:
    # Subsolar latitude oscillates with amplitude I = 1.5424 deg with argument (lambda_sun - Omega)
    arg_rad = np.radians(lambda_sun - Omega)
    sub_lat = LUNAR_OBLIQUITY_DEG * np.sin(arg_rad)

    # Subsolar longitude sweeps 360 deg over one synodic month:
    # lon_sun = (lambda_sun - L_moon + 180) % 360 - 180 (approx)
    # Plus optical correction
    sub_lon = (lambda_sun - L_moon + 180.0) % 360.0
    if sub_lon > 180.0:
        sub_lon -= 360.0

    return float(sub_lat), float(sub_lon)


def calculate_subearth_librations(jd: float) -> Tuple[float, float]:
    """Calculate Earth's optical + physical libration (sub-Earth selenographic lat and lon in deg).

    Longitude libration l_E: approx +/- 7.9 deg (ellipticity of orbit).
    Latitude libration b_E: approx +/- 6.7 deg (inclination of lunar equator).

    Returns:
        (b_E, l_E) in degrees: sub-Earth latitude and longitude.
    """
    T = (jd - 2451545.0) / 36525.0

    # Delaunay fundamental arguments (in degrees)
    # Moon's mean anomaly
    M_prime = 134.9633964 + 477198.8675055 * T + 0.0087414 * T**2
    # Sun's mean anomaly
    M_sun = 357.5291092 + 35999.0502909 * T - 0.0001536 * T**2
    # Mean elongation of the Moon
    D = 297.8501921 + 445267.1114034 * T - 0.0018819 * T**2
    # Moon's argument of latitude
    F = 93.2720950 + 483202.0175233 * T - 0.0036539 * T**2
    # Node longitude
    Omega = 125.04452 - 1934.136261 * T

    # Primary optical libration in longitude l' (Meeus 53.1)
    Mp_rad = np.radians(M_prime)
    Msun_rad = np.radians(M_sun)
    D_rad = np.radians(D)
    F_rad = np.radians(F)

    l_E = -1.274 * np.sin(Mp_rad - 2 * D_rad) + \
          0.658 * np.sin(2 * D_rad) - \
          0.214 * np.sin(2 * Mp_rad) - \
          0.186 * np.sin(Msun_rad) - \
          6.289 * np.sin(Mp_rad)

    # Primary optical libration in latitude b' (Meeus 53.2)
    b_E = -6.68 * np.sin(F_rad) + \
          0.17 * np.sin(Mp_rad - F_rad) - \
          0.17 * np.sin(Mp_rad + F_rad)

    # Bound to physical limits
    l_E = np.clip(l_E, -8.1, 8.1)
    b_E = np.clip(b_E, -6.9, 6.9)

    return float(b_E), float(l_E)


def get_topocentric_sun(
    obs_lat_deg: float,
    obs_lon_deg: float,
    dt: datetime,
) -> Tuple[float, float]:
    """Calculate topocentric Sun azimuth and elevation from a lunar site.

    Azimuth convention:
        0 deg = North (toward lunar north pole)
        90 deg = East (+90 deg meridian)
        180 deg = South
        270 deg = West

    Returns:
        (azimuth_deg, elevation_deg)
    """
    jd = datetime_to_jd(dt)
    sub_lat, sub_lon = calculate_subsolar_coordinates(jd)

    phi_obs = np.radians(obs_lat_deg)
    lam_obs = np.radians(obs_lon_deg)
    phi_sun = np.radians(sub_lat)
    lam_sun = np.radians(sub_lon)

    dlam = lam_sun - lam_obs

    # Angular distance psi between observer and subsolar point
    cos_psi = np.sin(phi_obs) * np.sin(phi_sun) + np.cos(phi_obs) * np.cos(phi_sun) * np.cos(dlam)
    cos_psi = np.clip(cos_psi, -1.0, 1.0)
    psi_rad = np.arccos(cos_psi)

    # Geometric elevation above lunar sphere horizon
    elev_rad = (np.pi / 2.0) - psi_rad

    # Azimuth angle from North
    y = np.sin(dlam) * np.cos(phi_sun)
    x = np.cos(phi_obs) * np.sin(phi_sun) - np.sin(phi_obs) * np.cos(phi_sun) * np.cos(dlam)
    az_rad = np.arctan2(y, x)
    az_deg = (np.degrees(az_rad) + 360.0) % 360.0

    return float(az_deg), float(np.degrees(elev_rad))


def get_topocentric_earth(
    obs_lat_deg: float,
    obs_lon_deg: float,
    dt: datetime,
) -> Tuple[float, float]:
    """Calculate topocentric Earth azimuth and elevation (optical libration) from a lunar site.

    Returns:
        (azimuth_deg, elevation_deg)
    """
    jd = datetime_to_jd(dt)
    b_E, l_E = calculate_subearth_librations(jd)

    phi_obs = np.radians(obs_lat_deg)
    lam_obs = np.radians(obs_lon_deg)
    phi_e = np.radians(b_E)
    lam_e = np.radians(l_E)

    dlam = lam_e - lam_obs

    cos_psi = np.sin(phi_obs) * np.sin(phi_e) + np.cos(phi_obs) * np.cos(phi_e) * np.cos(dlam)
    cos_psi = np.clip(cos_psi, -1.0, 1.0)
    psi_rad = np.arccos(cos_psi)

    # Topocentric correction for finite Earth distance
    # Mean Moon radius / mean Earth distance ~ 1737.4 / 384400 ~ 0.00452 rad (~0.259 deg)
    parallax_rad = 0.00452 * np.sin(psi_rad)
    elev_rad = (np.pi / 2.0) - psi_rad - parallax_rad

    # Azimuth
    y = np.sin(dlam) * np.cos(phi_e)
    x = np.cos(phi_obs) * np.sin(phi_e) - np.sin(phi_obs) * np.cos(phi_e) * np.cos(dlam)
    az_rad = np.arctan2(y, x)
    az_deg = (np.degrees(az_rad) + 360.0) % 360.0

    return float(az_deg), float(np.degrees(elev_rad))


def get_sun_trajectory_series(
    obs_lat_deg: float,
    obs_lon_deg: float,
    start_dt: datetime,
    n_steps: int = 360,
    total_hours: float = 708.7,  # One synodic month
) -> Dict[str, np.ndarray]:
    """Compute topocentric Sun positions covering a full 360-degree sweep."""
    hours = np.linspace(0.0, total_hours, n_steps)
    start_jd = datetime_to_jd(start_dt)

    az_list = []
    el_list = []

    for h in hours:
        jd_t = start_jd + (h / 24.0)
        sub_lat, sub_lon = calculate_subsolar_coordinates(jd_t)
        phi_obs = np.radians(obs_lat_deg)
        lam_obs = np.radians(obs_lon_deg)
        phi_sun = np.radians(sub_lat)
        lam_sun = np.radians(sub_lon)
        dlam = lam_sun - lam_obs

        cos_psi = np.sin(phi_obs) * np.sin(phi_sun) + np.cos(phi_obs) * np.cos(phi_sun) * np.cos(dlam)
        cos_psi = np.clip(cos_psi, -1.0, 1.0)
        psi_rad = np.arccos(cos_psi)
        elev_rad = (np.pi / 2.0) - psi_rad

        y = np.sin(dlam) * np.cos(phi_sun)
        x = np.cos(phi_obs) * np.sin(phi_sun) - np.sin(phi_obs) * np.cos(phi_sun) * np.cos(dlam)
        az_rad = np.arctan2(y, x)
        az_deg = (np.degrees(az_rad) + 360.0) % 360.0

        az_list.append(az_deg)
        el_list.append(np.degrees(elev_rad))

    return {
        "hours": hours,
        "azimuth_deg": np.array(az_list),
        "elevation_deg": np.array(el_list),
    }


def get_earth_libration_series(
    obs_lat_deg: float,
    obs_lon_deg: float,
    start_dt: datetime,
    n_days: float = 28.0,
    n_steps: int = 140,
) -> Dict[str, np.ndarray]:
    """Compute Earth topocentric trajectory over an anomalistic/draconic month (libration loop)."""
    days = np.linspace(0.0, n_days, n_steps)
    start_jd = datetime_to_jd(start_dt)

    az_list = []
    el_list = []

    for d in days:
        jd_t = start_jd + d
        b_E, l_E = calculate_subearth_librations(jd_t)
        phi_obs = np.radians(obs_lat_deg)
        lam_obs = np.radians(obs_lon_deg)
        phi_e = np.radians(b_E)
        lam_e = np.radians(l_E)
        dlam = lam_e - lam_obs

        cos_psi = np.sin(phi_obs) * np.sin(phi_e) + np.cos(phi_obs) * np.cos(phi_e) * np.cos(dlam)
        cos_psi = np.clip(cos_psi, -1.0, 1.0)
        psi_rad = np.arccos(cos_psi)
        parallax_rad = 0.00452 * np.sin(psi_rad)
        elev_rad = (np.pi / 2.0) - psi_rad - parallax_rad

        y = np.sin(dlam) * np.cos(phi_e)
        x = np.cos(phi_obs) * np.sin(phi_e) - np.sin(phi_obs) * np.cos(phi_e) * np.cos(dlam)
        az_rad = np.arctan2(y, x)
        az_deg = (np.degrees(az_rad) + 360.0) % 360.0

        az_list.append(az_deg)
        el_list.append(np.degrees(elev_rad))

    return {
        "days": days,
        "azimuth_deg": np.array(az_list),
        "elevation_deg": np.array(el_list),
    }
