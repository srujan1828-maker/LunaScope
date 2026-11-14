"""
Unit tests for 360-degree topographic horizon generation and mast sensitivity.
"""

import pytest
from app.core.horizon import compute_horizon_360


def test_horizon_length_and_range():
    # Compute for Shackleton connecting ridge
    horizon = compute_horizon_360(
        lat_deg=-89.44,
        lon_deg=222.70,
        base_elevation_m=1920.0,
        mast_height_m=2.0
    )
    assert len(horizon) == 360
    # Values should be reasonable lunar skyline angles (-10° to +20°)
    for val in horizon:
        assert -10.0 <= val <= 25.0


def test_mast_height_sensitivity():
    # Higher mast should lower or keep equal the skyline elevation
    h_low = compute_horizon_360(-89.44, 222.70, 1920.0, mast_height_m=1.0)
    h_high = compute_horizon_360(-89.44, 222.70, 1920.0, mast_height_m=15.0)
    
    avg_low = sum(h_low) / len(h_low)
    avg_high = sum(h_high) / len(h_high)
    assert avg_high < avg_low
