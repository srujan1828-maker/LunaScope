"""LunaScope Test Suite: Mathematical, Ephemeris, Raycaster, and Monte Carlo Validation.

Verifies:
1. Coordinate projections (forward, inverse round-trip, lunar radius scale).
2. Synthetic candidate sites database schema and 2025-2032 models.
3. Raycaster physics: lunar curvature drop d^2 / (2 * R_Moon), mast height effects.
4. Ephemeris: Sun 360 deg sweep, Earth libration bounds (+/- 7.9 deg lon, +/- 6.7 deg lat).
5. Solar disk penumbra: exact boundary conditions (u<=-1 => 0.0, u>=1 => 1.0, u=0 => 0.5).
6. Contingency matcher: pass/fail criteria and backup ranking.
7. Monte Carlo performance: 250-point landing ellipse simulation < 200ms.
"""

from datetime import datetime, timezone
import os
import sys
import time
from pathlib import Path
import numpy as np
import pytest

# Ensure lunascope directory is on sys.path
_current_dir = Path(__file__).resolve().parent
_lunascope_root = _current_dir.parent
if str(_lunascope_root) not in sys.path:
    sys.path.insert(0, str(_lunascope_root))

from core.projections import latlon_to_xy, xy_to_latlon, great_circle_distance, R_MOON
from core.synthetic_data import (
    load_candidate_sites,
    generate_procedural_dem_patch,
    get_elevation_profile,
    CANDIDATE_SITES_METADATA,
)
from core.raycaster import compute_horizon_mask, interpolate_horizon
from core.ephemeris import (
    calculate_subsolar_coordinates,
    calculate_subearth_librations,
    get_topocentric_sun,
    get_topocentric_earth,
    get_sun_trajectory_series,
    SOLAR_ANGULAR_RADIUS_DEG,
)
from core.visibility import (
    calculate_fractional_solar_illumination,
    calculate_dte_status,
    evaluate_site_timeline,
)
from core.contingency import evaluate_contingency
from plugins.dispersion_monte_carlo import run_dispersion_monte_carlo


# ---------------------------------------------------------------------------
# 1. Coordinate Projections Tests
# ---------------------------------------------------------------------------
def test_south_pole_origin():
    """At South Pole (-90 deg lat), stereographic X, Y must be 0, 0."""
    x, y = latlon_to_xy(-90.0, 0.0)
    assert abs(x) < 1e-4
    assert abs(y) < 1e-4


def test_projection_roundtrip():
    """Test round-trip lat/lon -> x/y -> lat/lon precision."""
    test_lats = [-89.9, -88.5, -86.0, -84.0]
    test_lons = [0.0, 45.0, 129.78, 222.65, -120.0]

    for lat in test_lats:
        for lon in test_lons:
            x, y = latlon_to_xy(lat, lon)
            lat_rec, lon_rec = xy_to_latlon(x, y)
            assert abs(lat - lat_rec) < 1e-4, f"Lat mismatch at {lat}, {lon}: got {lat_rec}"
            lon_diff = (lon - lon_rec + 180.0) % 360.0 - 180.0
            assert abs(lon_diff) < 1e-4, f"Lon mismatch at {lat}, {lon}: got {lon_rec}"


def test_vectorized_projections():
    """Vectorized inputs must produce matching numpy array shapes."""
    lats = np.array([-89.5, -88.0, -85.5])
    lons = np.array([30.0, 90.0, 180.0])
    x, y = latlon_to_xy(lats, lons)
    assert isinstance(x, np.ndarray) and x.shape == (3,)
    assert isinstance(y, np.ndarray) and y.shape == (3,)

    lat_rec, lon_rec = xy_to_latlon(x, y)
    np.testing.assert_allclose(lats, lat_rec, atol=1e-4)


# ---------------------------------------------------------------------------
# 2. Synthetic Data & Candidates Database Tests
# ---------------------------------------------------------------------------
def test_candidate_sites_count_and_columns():
    """Verify all 15 candidate landing sites load with 2025-2032 consecutive days."""
    df, is_synthetic = load_candidate_sites()
    assert len(df) >= 15
    expected_cols = [
        "site_id", "name", "lat_deg", "lon_deg", "x_m", "y_m",
        "elevation_m", "avg_slope_deg", "annual_illum_pct", "annual_dte_pct",
    ]
    for c in expected_cols:
        assert c in df.columns, f"Missing expected column {c}"

    for yr in range(2025, 2033):
        assert f"consec_days_{yr}" in df.columns, f"Missing year {yr} consecutive days"


def test_procedural_dem_patch():
    """Verify procedural DEM generates valid 2D elevation grid."""
    x_v, y_v, z_grid = generate_procedural_dem_patch(center_x=0.0, center_y=0.0, size_m=2000.0, resolution_m=20.0)
    assert len(x_v) == 101
    assert len(y_v) == 101
    assert z_grid.shape == (101, 101)
    assert not np.isnan(z_grid).any()
    assert np.all(z_grid > 500.0)  # Reasonable elevation bounds


# ---------------------------------------------------------------------------
# 3. Raycaster & Curvature Drop Tests
# ---------------------------------------------------------------------------
def test_raycaster_horizon_output_shape():
    """Horizon mask must produce 360 azimuths with valid elevation metrics."""
    az, horiz, metrics = compute_horizon_mask(x0=1000.0, y0=2000.0, z0=1500.0, mast_height=2.0, use_cache=False)
    assert len(az) == 360
    assert len(horiz) == 360
    assert not np.isnan(horiz).any()
    assert "mean_horizon_deg" in metrics
    assert "sky_view_factor" in metrics
    assert 0.0 <= metrics["sky_view_factor"] <= 1.0


def test_mast_height_lowers_horizon():
    """Raising the mast height must lower or equal the terrain horizon mask."""
    _, horiz_0m, _ = compute_horizon_mask(x0=0.0, y0=0.0, z0=1500.0, mast_height=0.0, use_cache=False)
    _, horiz_15m, _ = compute_horizon_mask(x0=0.0, y0=0.0, z0=1500.0, mast_height=15.0, use_cache=False)
    # At every azimuth, a higher mast yields an elevation angle <= lower mast
    diff = horiz_15m - horiz_0m
    assert np.all(diff <= 1e-4), "Higher mast height failed to lower horizon mask"


def test_interpolate_horizon_periodic():
    """Periodic interpolation at 0 and 360 deg must be identical."""
    az = np.linspace(0, 360, 360, endpoint=False)
    horiz = 2.0 + 1.5 * np.sin(np.radians(az))
    h0 = interpolate_horizon(0.0, az, horiz)
    h360 = interpolate_horizon(360.0, az, horiz)
    assert abs(h0 - h360) < 1e-6


# ---------------------------------------------------------------------------
# 4. Ephemeris & Optical Libration Tests
# ---------------------------------------------------------------------------
def test_solar_elevation_oscillations():
    """Solar elevation near south pole must stay within ~ +/- 1.7 deg (lunar obliquity ~1.54 deg)."""
    dt = datetime(2026, 12, 1, 0, 0, tzinfo=timezone.utc)
    az, el = get_topocentric_sun(obs_lat_deg=-89.5, obs_lon_deg=0.0, dt=dt)
    assert 0.0 <= az <= 360.0
    assert -2.0 <= el <= 2.0, f"Solar elevation {el} exceeds physical bounds"


def test_earth_libration_bounds():
    """Sub-Earth librations must remain within physical optical limits (+/- 7.9 deg lon, +/- 6.7 deg lat)."""
    jd_test = 2461000.5
    b_E, l_E = calculate_subearth_librations(jd_test)
    assert -7.0 <= b_E <= 7.0, f"Latitude libration {b_E} exceeded +/-6.7 deg bounds"
    assert -8.2 <= l_E <= 8.2, f"Longitude libration {l_E} exceeded +/-7.9 deg bounds"


def test_sun_trajectory_sweep():
    """A full synodic month series must sweep through all 360 degrees of azimuth."""
    dt = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
    traj = get_sun_trajectory_series(obs_lat_deg=-89.78, obs_lon_deg=129.78, start_dt=dt, n_steps=60)
    azimuths = traj["azimuth_deg"]
    assert len(azimuths) == 60
    # Difference between min and max azimuth across a month must span near 360
    assert (np.max(azimuths) - np.min(azimuths)) > 300.0


# ---------------------------------------------------------------------------
# 5. Visibility & Penumbra Math Tests
# ---------------------------------------------------------------------------
def test_penumbra_exact_boundary_conditions():
    """Test mathematical exactness of circular segment exposure equation."""
    r_sun = SOLAR_ANGULAR_RADIUS_DEG  # 0.2665 deg

    # 1. Full sun (u >= 1): clearance >= +r_sun
    f_full = calculate_fractional_solar_illumination(sun_elevation_deg=5.0, horizon_elevation_deg=0.0)
    assert abs(f_full - 1.0) < 1e-6

    # 2. Umbra (u <= -1): clearance <= -r_sun
    f_umbra = calculate_fractional_solar_illumination(sun_elevation_deg=-5.0, horizon_elevation_deg=0.0)
    assert abs(f_umbra - 0.0) < 1e-6

    # 3. Center on horizon (u = 0): clearance = 0 -> exactly 0.5
    f_half = calculate_fractional_solar_illumination(sun_elevation_deg=1.5, horizon_elevation_deg=1.5)
    assert abs(f_half - 0.5) < 1e-4

    # 4. Monotonic increase in penumbra
    u_vals = np.linspace(-r_sun * 0.95, r_sun * 0.95, 20)
    f_vals = calculate_fractional_solar_illumination(sun_elevation_deg=u_vals, horizon_elevation_deg=0.0)
    assert np.all(np.diff(f_vals) > 0.0), "Penumbra curve is not strictly monotonically increasing"
    assert np.all((f_vals >= 0.0) & (f_vals <= 1.0))


def test_dte_status_logic():
    """Verify DTE connection logic based on margin threshold."""
    # Earth above horizon by 2 deg, margin 1 deg -> CONNECTED
    conn, margin = calculate_dte_status(earth_elevation_deg=3.0, horizon_elevation_deg=1.0, margin_threshold_deg=1.0)
    assert conn is True
    assert abs(margin - 2.0) < 1e-5

    # Earth below margin threshold -> DISCONNECTED
    conn, margin = calculate_dte_status(earth_elevation_deg=1.2, horizon_elevation_deg=1.0, margin_threshold_deg=1.0)
    assert conn is False
    assert abs(margin - 0.2) < 1e-5


# ---------------------------------------------------------------------------
# 6. Contingency Engine Tests
# ---------------------------------------------------------------------------
def test_contingency_evaluation():
    """Verify Primary site and ranked Backups evaluation."""
    df, _ = load_candidate_sites()
    result = evaluate_contingency(
        df_sites=df,
        primary_site_id="SHACKLETON_RIM",
        target_year=2026,
        required_consecutive_days=10.0,
        min_dte_pct=48.0,
        max_slope_deg=8.0,
    )
    p_eval = result["primary_evaluation"]
    assert p_eval["site_id"] == "SHACKLETON_RIM"
    assert p_eval["consecutive_days"] >= 10.0
    assert p_eval["passed"] is True
    assert len(p_eval["reasons"]) > 0

    backups = result["backup_candidates"]
    assert len(backups) == len(df) - 1
    # First backup should be sorted by passed status and score
    assert "rank" in backups[0]
    assert backups[0]["rank"] == 1


# ---------------------------------------------------------------------------
# 7. Monte Carlo Landing Ellipse Performance Benchmark (<200ms)
# ---------------------------------------------------------------------------
def test_monte_carlo_execution_speed_and_shapes():
    """Verify 250-point Monte Carlo simulation executes strictly under 200 milliseconds."""
    t0 = time.perf_counter()
    mc = run_dispersion_monte_carlo(
        site_x=12000.0,
        site_y=-8000.0,
        dispersion_radius_m=100.0,
        n_samples=250,
        seed=42,
    )
    t1 = time.perf_counter()
    duration_ms = (t1 - t0) * 1000.0

    # Strict performance verification: < 200 ms (typically < 15ms)
    assert duration_ms < 200.0, f"Monte Carlo took {duration_ms:.2f} ms (expected < 200 ms)"

    # Verify output structure and data shapes
    assert mc["n_samples"] == 250
    assert len(mc["dx_m"]) == 250
    assert len(mc["dy_m"]) == 250
    assert len(mc["slope_deg"]) == 250
    assert len(mc["illumination_pct"]) == 250
    assert len(mc["dte_pct"]) == 250
    assert len(mc["status"]) == 250

    # Verify status labels
    valid_statuses = {"PASS", "MARGINAL", "FAIL"}
    assert set(mc["status"]).issubset(valid_statuses)

    # Verify summary metrics
    summary = mc["summary"]
    assert 0.0 <= summary["survival_probability_pct"] <= 100.0
    assert summary["n_pass"] + summary["n_marginal"] + summary["n_fail"] == 250
