"""
NASA Deep Space Network (DSN) Ground Stations & RF Link Geometry Module.
Evaluates Earth diurnal rotation, sidereal time, and topocentric Moon visibility
from Goldstone, Madrid, and Canberra ground stations with minimum dish elevation masks.
"""

import math
from datetime import datetime, timezone
from typing import Dict, List, Any, Tuple

# NASA Deep Space Network Primary Complexes
DSN_STATIONS: List[Dict[str, Any]] = [
    {
        "station_id": "goldstone",
        "name": "Goldstone DSN (California, USA)",
        "lat_deg": 35.4267,
        "lon_deg": -116.8900,
        "elevation_m": 1000.0,
        "min_mask_deg": 10.0
    },
    {
        "station_id": "madrid",
        "name": "Madrid DSN (Robledo, Spain)",
        "lat_deg": 40.4272,
        "lon_deg": -4.2500,
        "elevation_m": 800.0,
        "min_mask_deg": 10.0
    },
    {
        "station_id": "canberra",
        "name": "Canberra DSN (Tidbinbilla, Australia)",
        "lat_deg": -35.4014,
        "lon_deg": 148.9817,
        "elevation_m": 650.0,
        "min_mask_deg": 10.0
    }
]


def greenwich_mean_sidereal_time_deg(jd: float) -> float:
    """
    Computes Greenwich Mean Sidereal Time (GMST) in degrees for a given Julian Date.
    Reference: Jean Meeus, Astronomical Algorithms, Chapter 12.
    """
    t = (jd - 2451545.0) / 36525.0
    # GMST at 0h UT in degrees + rotational rate
    gmst0 = 280.46061837 + 360.98564736629 * (jd - 2451545.0) + 0.000387933 * t**2 - (t**3 / 38710000.0)
    return gmst0 % 360.0


def station_moon_elevation(
    station_lat_deg: float,
    station_lon_deg: float,
    subearth_lat_deg: float,
    subearth_lon_deg: float,
    gmst_deg: float
) -> float:
    """
    Computes elevation angle of the Moon as seen from a terrestrial ground station dish.
    """
    # Local sidereal time of station
    local_sidereal = (gmst_deg + station_lon_deg) % 360.0

    phi_st = math.radians(station_lat_deg)
    # The sub-Earth point on the Moon points back to the center of Earth.
    # The geocentric declination of the Moon is approximately -subearth_lat_deg
    # and right ascension is linked to the Moon's orbital position.
    # For relative station line-of-sight:
    # Earth rotates underneath the sub-Moon geocentric direction.
    dec_moon = -math.radians(subearth_lat_deg)
    ha_moon = math.radians((local_sidereal - subearth_lon_deg) % 360.0)

    sin_el = math.sin(phi_st) * math.sin(dec_moon) + math.cos(phi_st) * math.cos(dec_moon) * math.cos(ha_moon)
    sin_el = max(-1.0, min(1.0, sin_el))
    return math.degrees(math.asin(sin_el))


def evaluate_dsn_coverage(
    unix_time: float,
    subearth_lat_deg: float,
    subearth_lon_deg: float,
    lander_dte_los: bool
) -> Dict[str, Any]:
    """
    Evaluates instantaneous NASA DSN ground network contact opportunities.
    """
    dt = datetime.fromtimestamp(unix_time, tz=timezone.utc)
    from app.core.ephemeris import datetime_to_jd
    jd = datetime_to_jd(dt)
    gmst = greenwich_mean_sidereal_time_deg(jd)

    active_stations = []
    station_details = {}

    for st in DSN_STATIONS:
        el = station_moon_elevation(
            st["lat_deg"], st["lon_deg"],
            subearth_lat_deg, subearth_lon_deg,
            gmst
        )
        is_in_view = el >= st["min_mask_deg"]
        has_closed_link = is_in_view and lander_dte_los

        station_details[st["station_id"]] = {
            "name": st["name"],
            "elevation_deg": round(el, 1),
            "in_view": is_in_view,
            "link_closed": has_closed_link
        }

        if has_closed_link:
            active_stations.append(st["name"])

    return {
        "timestamp_unix": unix_time,
        "lander_dte_los": lander_dte_los,
        "active_stations_count": len(active_stations),
        "active_stations": active_stations,
        "is_network_closed": len(active_stations) > 0,
        "stations": station_details
    }
