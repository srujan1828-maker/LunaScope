"""
Unit tests for lunar topocentric ephemeris calculations.
"""

from app.core.ephemeris import (
    get_subsolar_coordinates,
    get_subearth_coordinates,
    topocentric_az_el,
    compute_ephemeris_track,
    LUNAR_OBLIQUITY_DEG,
    LIB_LON_AMP_DEG,
    LIB_LAT_AMP_DEG
)


def test_subsolar_coordinates():
    lat, lon = get_subsolar_coordinates(1735689600.0)
    assert abs(lat) <= LUNAR_OBLIQUITY_DEG + 0.01
    assert 0.0 <= lon < 360.0


def test_subearth_libration():
    lat, lon = get_subearth_coordinates(1735689600.0)
    assert abs(lat) <= LIB_LAT_AMP_DEG + 0.01
    assert abs(lon) <= LIB_LON_AMP_DEG + 0.01


def test_topocentric_az_el():
    # Observer at -85° lat, 0° lon; body at 0° lat, 0° lon (towards equator, due north)
    az, el = topocentric_az_el(
        site_lat_deg=-85.0,
        site_lon_deg=0.0,
        body_lat_deg=0.0,
        body_lon_deg=0.0
    )
    # Looking from -85° to 0° lat along meridian: Azimuth should be due North (0° or 360°)
    assert (abs(az - 0.0) < 1.0) or (abs(az - 360.0) < 1.0)
    # Elevation should be roughly 90 - 85 = 5°
    assert abs(el - 5.0) < 1.0


def test_ephemeris_track():
    start_t = 1735689600.0
    end_t = start_t + 24 * 3600.0  # 24 hours
    track = compute_ephemeris_track(-89.44, 222.70, start_t, end_t, step_seconds=3600.0)
    
    assert len(track["timestamps"]) == 25
    assert len(track["sun_azimuth"]) == 25
    assert len(track["sun_elevation"]) == 25
    assert len(track["earth_azimuth"]) == 25
    assert len(track["earth_elevation"]) == 25
