"""
Unit tests for fractional solar disk visibility, DTE, operational states, and interval metrics.
"""

import numpy as np
from app.core.visibility import (
    fractional_solar_visibility,
    evaluate_dte_visibility,
    classify_operational_states,
    compute_interval_metrics
)
from app.core.ephemeris import SOLAR_RADIUS_DEG


def test_fractional_solar_visibility_boundaries():
    horizon = np.zeros(360)
    
    # Well above horizon (u >= 1.0)
    f_above = fractional_solar_visibility([0.0], [SOLAR_RADIUS_DEG + 0.1], horizon)
    assert f_above[0] == 1.0
    
    # Well below horizon (u <= -1.0)
    f_below = fractional_solar_visibility([0.0], [-SOLAR_RADIUS_DEG - 0.1], horizon)
    assert f_below[0] == 0.0
    
    # Exactly on horizon (u == 0.0) -> half disk exposed
    f_half = fractional_solar_visibility([0.0], [0.0], horizon)
    assert abs(f_half[0] - 0.5) < 0.01


def test_dte_visibility():
    horizon = np.zeros(360)
    
    # Earth above horizon
    c1 = evaluate_dte_visibility([90.0], [2.0], horizon, margin_deg=0.0)
    assert c1[0] == 1
    
    # Earth below horizon
    c2 = evaluate_dte_visibility([90.0], [-1.0], horizon, margin_deg=0.0)
    assert c2[0] == 0
    
    # Earth above horizon but below margin
    c3 = evaluate_dte_visibility([90.0], [0.5], horizon, margin_deg=1.0)
    assert c3[0] == 0


def test_operational_states():
    # 4 regimes:
    # f=1, c=1 -> 1 (Nominal Science)
    # f=1, c=0 -> 2 (Autonomous Day)
    # f=0, c=1 -> 3 (Tethered Eclipse)
    # f=0, c=0 -> 4 (Total Blackout)
    solar_fractions = [1.0, 1.0, 0.0, 0.0]
    dte = [1, 0, 1, 0]
    states = classify_operational_states(solar_fractions, dte, sun_threshold=0.10)
    assert states == [1, 2, 3, 4]


def test_interval_metrics():
    solar_fractions = [1.0, 1.0, 0.0, 0.0, 1.0]  # 3 sunlit hours, 2 shadow hours
    dte = [1, 1, 1, 0, 0]                        # 3 visible hours, 2 outage hours
    m = compute_interval_metrics(solar_fractions, dte, step_hours=1.0, sun_threshold=0.10)
    
    assert m["total_duration_hours"] == 5.0
    assert m["sun_availability_pct"] == 60.0
    assert m["longest_shadow_gap_hours"] == 2.0
    assert m["earth_availability_pct"] == 60.0
    assert m["longest_earth_outage_hours"] == 2.0
    # Overlap is at step 0 and 1 -> 2 steps -> 40%
    assert m["joint_availability_pct"] == 40.0
    assert m["longest_joint_window_hours"] == 2.0
