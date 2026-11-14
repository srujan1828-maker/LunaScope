"""
Unit tests for coordinate transformations and distance metrics.
"""

import math
import pytest
from app.core.coordinates import latlon_to_stereo, stereo_to_latlon, surface_distance_m, R_MOON


def test_pole_coordinates():
    # South pole is -90° lat
    x, y = latlon_to_stereo(-90.0, 0.0)
    assert abs(x) < 1e-3
    assert abs(y) < 1e-3
    
    lat, lon = stereo_to_latlon(0.0, 0.0)
    assert abs(lat - (-90.0)) < 1e-3


def test_roundtrip_transformation():
    test_points = [
        (-89.44, 222.70),  # Shackleton Connecting Ridge
        (-85.99, 0.05),    # Malapert Mountain
        (-87.87, 354.71),  # Haworth
        (-84.50, 85.00),   # Amundsen
    ]
    for lat_in, lon_in in test_points:
        x, y = latlon_to_stereo(lat_in, lon_in)
        lat_out, lon_out = stereo_to_latlon(x, y)
        assert abs(lat_out - lat_in) < 1e-4
        assert abs(lon_out - (lon_in % 360.0)) < 1e-4


def test_surface_distance():
    # Distance from South Pole (-90°) to -89° is 1 degree of latitude
    # 1 deg = pi / 180 * R_MOON approx 30323 meters
    dist = surface_distance_m(-90.0, 0.0, -89.0, 0.0)
    expected = (math.pi / 180.0) * R_MOON
    assert abs(dist - expected) < 10.0
