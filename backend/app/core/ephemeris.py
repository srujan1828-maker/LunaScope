"""
Approximate Astronomical Ephemeris Engine for Lunar South Pole Operations.
Implements the Jean Meeus / IAU Cartographic Coordinates and Rotational Elements
for true sub-solar position, lunar optical and physical librations, topocentric parallax,
and local East-North-Up (ENU) coordinate frame transformations.
"""

import math
from datetime import datetime, timezone
from typing import Dict, List, Tuple
import numpy as np

# Astronomical Constants
AU_METERS: float = 149597870700.0        # Astronomical Unit in meters
R_MOON: float = 1737400.0               # Mean lunar radius in meters (1737.4 km)
R_SUN_METERS: float = 696340000.0       # Solar radius in meters (696,340 km)
R_EARTH_METERS: float = 6371000.0       # Mean Earth radius in meters (6,371 km)
MEAN_LUNAR_DIST_METERS: float = 384400000.0 # Mean Earth-Moon distance

SOLAR_RADIUS_DEG: float = 0.266         # Mean apparent solar angular radius from Moon
EARTH_RADIUS_DEG: float = 0.950         # Mean apparent Earth angular radius from Moon

# Lunar Orbital & Rotational Elements (IAU 2000 / Meeus Chapter 53)
LUNAR_OBLIQUITY_DEG: float = 1.54242    # Inclination of Moon's equator to ecliptic (I = 1° 32' 32.7")
LUNAR_SYNODIC_DAYS: float = 29.530588853 # Synodic month
LIB_LON_AMP_DEG: float = 7.90           # Max optical libration in longitude
LIB_LAT_AMP_DEG: float = 6.68           # Max optical libration in latitude


def datetime_to_jd(dt: datetime) -> float:
    """
    Convert UTC datetime to Julian Date (JD).
    Valid for any Gregorian calendar date.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)

    year = dt.year
    month = dt.month
    day = dt.day + (dt.hour + dt.minute / 60.0 + dt.second / 3600.0 + dt.microsecond / 3.6e9) / 24.0

    if month <= 2:
        year -= 1
        month += 12

    a = math.floor(year / 100)
    b = 2 - a + math.floor(a / 4)
    jd = math.floor(365.25 * (year + 4716)) + math.floor(30.6001 * (month + 1)) + day + b - 1524.5
    return float(jd)


def solar_coordinates_meeus(jd: float) -> Tuple[float, float, float]:
    """
    Computes simulated ecliptic longitude (lambda_sun in deg), ecliptic latitude (approx 0),
    and distance (R in AU) of the Sun from the Earth-Moon barycenter.
    Reference: Jean Meeus, Astronomical Algorithms, Chapter 25.
    """
    t = (jd - 2451545.0) / 36525.0  # Julian centuries from J2000.0

    # Geometric mean longitude of the Sun (deg)
    l0 = (280.46646 + 36000.76983 * t + 0.0003032 * t**2) % 360.0

    # Mean anomaly of the Sun (deg)
    m = (357.52911 + 35999.05029 * t - 0.0001537 * t**2) % 360.0
    m_rad = math.radians(m)

    # Sun's equation of the center (deg)
    c = (
        (1.914602 - 0.004817 * t - 0.000014 * t**2) * math.sin(m_rad)
        + (0.019993 - 0.000101 * t) * math.sin(2.0 * m_rad)
        + 0.000289 * math.sin(3.0 * m_rad)
    )

    # True geometric longitude of the Sun (deg)
    sun_lon = (l0 + c) % 360.0

    # Distance to the Sun in AU
    e = 0.016708634 - 0.000042037 * t - 0.0000001267 * t**2
    v = m + c
    r_au = (1.000001018 * (1.0 - e**2)) / (1.0 + e * math.cos(math.radians(v)))

    return sun_lon, 0.0, r_au


def lunar_fundamental_arguments(t: float) -> Dict[str, float]:
    """
    Computes fundamental Delaunay arguments of lunar motion (in degrees).
    Reference: Meeus Chapter 47.
    """
    # Moon's mean longitude
    lp = (218.3164477 + 481267.88123421 * t - 0.0015786 * t**2 + t**3 / 538841.0) % 360.0

    # Mean elongation of the Moon
    d = (297.8501921 + 445267.1114034 * t - 0.0018819 * t**2 + t**3 / 545868.0) % 360.0

    # Sun's mean anomaly
    m = (357.5291092 + 35999.0502909 * t - 0.0001536 * t**2 + t**3 / 24490000.0) % 360.0

    # Moon's mean anomaly
    mp = (134.9633964 + 477198.8675055 * t + 0.0087414 * t**2 + t**3 / 69699.0) % 360.0

    # Moon's argument of latitude (distance from ascending node)
    f = (93.2720950 + 483202.0175233 * t - 0.0036539 * t**2 - t**3 / 3526000.0) % 360.0

    # Longitude of the ascending node of the Moon's orbit
    omega = (125.04452 - 1934.13626 * t + 0.0020708 * t**2 + t**3 / 450000.0) % 360.0

    return {"Lp": lp, "D": d, "M": m, "Mp": mp, "F": f, "Omega": omega}


def get_subsolar_coordinates(unix_time: float) -> Tuple[float, float]:
    """
    Estimates selenographic latitude and longitude of the sub-solar point
    in the Moon Mean Earth / Polar Axis frame (MOON_ME).
    Reference: Meeus Chapter 53 (Ephemeris for Physical Observations of the Moon).
    """
    dt = datetime.fromtimestamp(unix_time, tz=timezone.utc)
    jd = datetime_to_jd(dt)
    t = (jd - 2451545.0) / 36525.0

    args = lunar_fundamental_arguments(t)
    omega = math.radians(args["Omega"])
    f = math.radians(args["F"])
    i = math.radians(LUNAR_OBLIQUITY_DEG)

    sun_lon_deg, _, _ = solar_coordinates_meeus(jd)
    lambda_sun = math.radians(sun_lon_deg)

    # Sub-solar selenographic latitude (tilt oscillates between -1.542° and +1.542°)
    # sin(b_sun) = -sin(lambda_sun - Omega) * sin(I)
    sin_b = -math.sin(lambda_sun - omega) * math.sin(i)
    sin_b = max(-1.0, min(1.0, sin_b))
    b_sun_deg = math.degrees(math.asin(sin_b))

    # Sub-solar selenographic longitude
    # tan(l_sun + F) = (sin(lambda_sun - Omega) * cos(I)) / cos(lambda_sun - Omega)
    y = math.sin(lambda_sun - omega) * math.cos(i)
    x = math.cos(lambda_sun - omega)
    l_plus_f = math.atan2(y, x)
    l_sun_deg = (math.degrees(l_plus_f - f) + 360.0) % 360.0

    return b_sun_deg, l_sun_deg


def get_subearth_coordinates(unix_time: float) -> Tuple[float, float]:
    """
    Estimates sub-Earth selenographic coordinates (optical + physical libration).
    Center is around (0°, 0°); wobbles by ±7.9° in longitude and ±6.68° in latitude.
    Reference: Meeus Chapter 53.
    """
    dt = datetime.fromtimestamp(unix_time, tz=timezone.utc)
    jd = datetime_to_jd(dt)
    t = (jd - 2451545.0) / 36525.0

    args = lunar_fundamental_arguments(t)
    d = math.radians(args["D"])
    m = math.radians(args["M"])
    mp = math.radians(args["Mp"])
    f = math.radians(args["F"])

    # Optical libration in longitude (l') and latitude (b')
    # Principal terms of optical libration
    lib_lon = (
        -1.274 * math.sin(mp - 2.0 * d)
        + 0.658 * math.sin(2.0 * d)
        - 0.186 * math.sin(m)
        - 0.059 * math.sin(2.0 * mp - 2.0 * d)
        - 0.057 * math.sin(mp - 2.0 * d + m)
        + 6.289 * math.sin(mp)  # Equation of center in longitude
    )

    lib_lat = (
        5.128 * math.sin(f)
        + 0.281 * math.sin(mp + f)
        - 0.278 * math.sin(f - mp)
        + 0.173 * math.sin(2.0 * d - f)
        - 0.055 * math.sin(2.0 * d - f - mp)
        + 0.046 * math.sin(2.0 * d + f - mp)
    )

    # Physical libration corrections (rho, sigma, tau)
    # tau (longitude), rho (latitude)
    tau = (
        0.0275 * math.sin(mp)
        - 0.0224 * math.sin(f)
        + 0.0084 * math.sin(mp - 2.0 * d)
    )
    rho = (
        -0.0357 * math.sin(f)
        + 0.0107 * math.sin(2.0 * d - f)
    )

    subearth_lon = max(-9.0, min(9.0, lib_lon + tau))
    subearth_lat = max(-7.5, min(7.5, lib_lat + rho))

    return subearth_lat, subearth_lon


def body_cartesian_vector(lat_deg: float, lon_deg: float, distance_m: float = 1.0) -> np.ndarray:
    """Computes Moon-centered Cartesian vector [X, Y, Z] in meters."""
    phi = math.radians(lat_deg)
    lam = math.radians(lon_deg)
    return np.array([
        distance_m * math.cos(phi) * math.cos(lam),
        distance_m * math.cos(phi) * math.sin(lam),
        distance_m * math.sin(phi)
    ], dtype=np.float64)


def topocentric_az_el(
    site_lat_deg: float,
    site_lon_deg: float,
    body_lat_deg: float,
    body_lon_deg: float,
    body_distance_m: float = AU_METERS,
    site_elevation_m: float = 0.0
) -> Tuple[float, float]:
    """
    Computes topocentric azimuth and elevation in the local East-North-Up (ENU) frame
    accounting for topocentric parallax vector offset from lunar center:
      r_topocentric = r_body - r_observer
    """
    phi0 = math.radians(site_lat_deg)
    lam0 = math.radians(site_lon_deg)
    r_obs = R_MOON + site_elevation_m

    # Observer position in Moon-fixed Cartesian frame
    obs_cartesian = np.array([
        r_obs * math.cos(phi0) * math.cos(lam0),
        r_obs * math.cos(phi0) * math.sin(lam0),
        r_obs * math.sin(phi0)
    ], dtype=np.float64)

    # Celestial body position in Moon-fixed Cartesian frame
    body_cartesian = body_cartesian_vector(body_lat_deg, body_lon_deg, body_distance_m)

    # Topocentric displacement vector from observer to celestial body
    topo_vec = body_cartesian - obs_cartesian
    dist_topo = float(np.linalg.norm(topo_vec))
    topo_unit = topo_vec / dist_topo

    # Local ENU basis vectors
    up = np.array([
        math.cos(phi0) * math.cos(lam0),
        math.cos(phi0) * math.sin(lam0),
        math.sin(phi0)
    ], dtype=np.float64)

    east = np.array([
        -math.sin(lam0),
        math.cos(lam0),
        0.0
    ], dtype=np.float64)

    north = np.array([
        -math.sin(phi0) * math.cos(lam0),
        -math.sin(phi0) * math.sin(lam0),
        math.cos(phi0)
    ], dtype=np.float64)

    # Projections into ENU
    u = float(np.dot(topo_unit, up))
    e = float(np.dot(topo_unit, east))
    n = float(np.dot(topo_unit, north))

    # Topocentric elevation and azimuth
    elevation_deg = math.degrees(math.asin(max(-1.0, min(1.0, u))))
    azimuth_deg = (math.degrees(math.atan2(e, n)) + 360.0) % 360.0

    return azimuth_deg, elevation_deg


def compute_ephemeris_track(
    site_lat_deg: float,
    site_lon_deg: float,
    start_unix: float,
    end_unix: float,
    step_seconds: float = 3600.0,
    site_elevation_m: float = 0.0
) -> Dict[str, List[float]]:
    """
    Computes approximate time series trajectories of Sun and Earth topocentric positions.
    """
    times = []
    sun_az = []
    sun_el = []
    earth_az = []
    earth_el = []
    solar_flux = []

    current_t = start_unix
    while current_t <= end_unix + 1e-3:
        times.append(current_t)
        dt = datetime.fromtimestamp(current_t, tz=timezone.utc)
        jd = datetime_to_jd(dt)

        # 1. Sun topocentric position & distance
        _, _, r_au = solar_coordinates_meeus(jd)
        sun_dist_m = r_au * AU_METERS
        s_lat, s_lon = get_subsolar_coordinates(current_t)
        s_az, s_el = topocentric_az_el(
            site_lat_deg, site_lon_deg, s_lat, s_lon,
            body_distance_m=sun_dist_m, site_elevation_m=site_elevation_m
        )
        sun_az.append(round(s_az, 2))
        sun_el.append(round(s_el, 2))

        # Solar constant scaled by inverse-square distance
        flux = 1361.0 / (r_au**2)
        solar_flux.append(round(flux, 1))

        # 2. Earth topocentric position
        e_lat, e_lon = get_subearth_coordinates(current_t)
        e_az, e_el = topocentric_az_el(
            site_lat_deg, site_lon_deg, e_lat, e_lon,
            body_distance_m=MEAN_LUNAR_DIST_METERS, site_elevation_m=site_elevation_m
        )
        earth_az.append(round(e_az, 2))
        earth_el.append(round(e_el, 2))

        current_t += step_seconds

    return {
        "timestamps": times,
        "sun_azimuth": sun_az,
        "sun_elevation": sun_el,
        "earth_azimuth": earth_az,
        "earth_elevation": earth_el,
        "solar_flux_w_m2": solar_flux
    }
