"""LunaScope Scientific Authenticity, Physics Sanity & UI Wiring Verification Suite.

Verification Protocol:
1. Ground-Truth Data & Provenance Audit (test_data_authenticity)
2. Astronomical Ephemeris Benchmark (test_ephemeris_bounds)
3. Physics & Horizon Geometry Sanity (test_physics_invariants):
   - Flat-Moon Spherical Curvature Drop Test
   - Mast-Height Monotonicity Test
   - Fractional Solar Disk Penumbra Analytical Bounds Test
   - Crater Floor (PSR) vs. Illuminated Peak Contrast Test
   - Monte Carlo Performance (<250ms) & Bitwise Reproducibility Test
4. Headless Streamlit UI Wiring & End-to-End Integration (test_streamlit_ui_wiring)
"""

from datetime import datetime, timezone, timedelta
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

from core.projections import latlon_to_xy, xy_to_latlon, R_MOON
from core.synthetic_data import (
    load_candidate_sites,
    check_raw_data_status,
    CANDIDATE_SITES_METADATA,
)
from core.raycaster import compute_horizon_mask, interpolate_horizon
from core.ephemeris import (
    get_topocentric_sun,
    get_topocentric_earth,
    SOLAR_ANGULAR_RADIUS_DEG,
)
from core.visibility import (
    calculate_fractional_solar_illumination,
    calculate_dte_status,
    evaluate_site_timeline,
)
from core.contingency import evaluate_contingency
from plugins.dispersion_monte_carlo import run_dispersion_monte_carlo


# =============================================================================
# 1. Ground-Truth Data & Provenance Audit
# =============================================================================
def test_data_authenticity():
    """Verify data authenticity, synthetic fallback detection, and provenance tagging."""
    # 1. Inspect raw filesystem data status
    raw_status = check_raw_data_status()
    assert "is_synthetic_fallback" in raw_status
    assert "provenance_flag" in raw_status

    # 2. Load candidate sites DataFrame
    df_sites, is_synthetic = load_candidate_sites()
    assert len(df_sites) >= 15, f"Expected at least 15 candidate landing sites, found {len(df_sites)}"

    # If raw files are missing from data/raw/, verify fallback flag and provenance
    if raw_status["is_synthetic_fallback"]:
        assert is_synthetic is True, "Expected is_synthetic=True when raw data is missing"
        assert df_sites.attrs.get("is_synthetic_fallback") is True
        assert df_sites.attrs.get("provenance_flag") == "[Assumed / Synthetic Fallback]"
        assert (df_sites["provenance_flag"] == "[Assumed / Synthetic Fallback]").all(), \
            "All candidate rows must be labeled with fallback provenance flag"

    # 3. Verify all required Artemis III candidate regions are present
    required_regions = [
        "Shackleton Rim",
        "Connecting Ridge",
        "Malapert Massif",
        "Leibnitz Beta",
        "Haworth",
        "Nobile Rim 1",
        "de Gerlache Rim",
    ]
    site_names_str = " ".join(df_sites["name"].tolist())
    for region in required_regions:
        assert any(region.lower() in name.lower() for name in df_sites["name"]), \
            f"Missing required Artemis III candidate region: {region} in {df_sites['name'].tolist()}"

    # 4. Verify coordinates, elevation bounds, and non-NaN values across 2025-2032
    for _, row in df_sites.iterrows():
        lat = row["lat_deg"]
        lon = row["lon_deg"]
        assert -90.0 <= lat <= -80.0, f"Site {row['name']} lat {lat} out of south polar bounds [-90, -80]"
        assert -180.0 <= lon <= 360.0, f"Site {row['name']} lon {lon} out of standard longitude bounds"
        assert row["elevation_m"] > 0, f"Site {row['name']} elevation {row['elevation_m']} must be positive"

        # Check all modelled years 2025 to 2032
        for year in range(2025, 2033):
            col_name = f"consec_days_{year}"
            assert col_name in row, f"Missing {col_name} for site {row['name']}"
            val = row[col_name]
            assert not np.isnan(val), f"NaN consecutive days for {row['name']} in year {year}"
            assert val > 0.0, f"Consecutive days for {row['name']} in year {year} must be positive"

    # 5. Verify deterministic Primary vs Backup pass/fail evaluation
    result_eval = evaluate_contingency(
        df_sites=df_sites,
        primary_site_id="SHACKLETON_RIM",
        target_year=2026,
        required_consecutive_days=10.0,
    )
    p_eval = result_eval["primary_evaluation"]
    assert "passed" in p_eval
    assert len(p_eval["reasons"]) > 0, "Primary evaluation must provide clear engineering explainability"
    assert "summary_stats" in result_eval
    assert result_eval["summary_stats"]["is_synthetic_fallback"] == is_synthetic
    assert result_eval["summary_stats"]["provenance_flag"] in ["[Published]", "[Assumed / Synthetic Fallback]"]


# =============================================================================
# 2. Astronomical Ephemeris Benchmark
# =============================================================================
def test_ephemeris_bounds():
    """Verify Sun and Earth trajectories over 720 hourly steps (30 synodic days) at the Lunar South Pole."""
    obs_lat = -89.54  # Shackleton region colatitude
    obs_lon = 0.0     # Prime meridian
    start_dt = datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc)

    sun_elevations = []
    sun_azimuths = []
    earth_elevations = []
    earth_azimuths = []

    for h in range(720):
        t_sample = start_dt + timedelta(hours=h)
        s_az, s_el = get_topocentric_sun(obs_lat, obs_lon, t_sample)
        e_az, e_el = get_topocentric_earth(obs_lat, obs_lon, t_sample)
        sun_azimuths.append(s_az)
        sun_elevations.append(s_el)
        earth_azimuths.append(e_az)
        earth_elevations.append(e_el)

    sun_elevations = np.array(sun_elevations)
    sun_azimuths = np.array(sun_azimuths)
    earth_elevations = np.array(earth_elevations)
    earth_azimuths = np.array(earth_azimuths)

    # 1. Sun Trajectory Invariant:
    # Solar elevation remains strictly bounded within [-2.5°, +2.5°]
    assert np.all(sun_elevations >= -2.5), f"Sun elevation dropped below -2.5°: {np.min(sun_elevations)}°"
    assert np.all(sun_elevations <= 2.5), f"Sun elevation exceeded +2.5°: {np.max(sun_elevations)}°"

    # Solar azimuth sweeps monotonically through a full 360° cycle
    unwrapped_sun_deg = np.degrees(np.unwrap(np.radians(sun_azimuths)))
    total_az_sweep = abs(unwrapped_sun_deg[-1] - unwrapped_sun_deg[0])
    assert total_az_sweep >= 360.0, f"Solar azimuth sweep {total_az_sweep:.1f}° was less than 360° over 30 days"

    # Hourly azimuth delta: monotonic at approx 0.507°/hour
    hourly_diffs = np.abs(np.diff(unwrapped_sun_deg))
    assert np.all(hourly_diffs > 0.45) and np.all(hourly_diffs < 0.56), \
        f"Hourly solar azimuth sweep outside [0.45°, 0.56°]: min={np.min(hourly_diffs):.3f}°, max={np.max(hourly_diffs):.3f}°"

    # 2. Earth Optical Libration Invariant:
    # Earth does NOT sweep 360° around the horizon; stays within libration box
    # Elevation bounded within ±8.5°
    assert np.all(earth_elevations >= -8.5), f"Earth elevation dropped below -8.5°: {np.min(earth_elevations)}°"
    assert np.all(earth_elevations <= 8.5), f"Earth elevation exceeded +8.5°: {np.max(earth_elevations)}°"

    # Azimuth deviation from near-side meridian (0°) bounded within ±9.5°
    earth_az_dev = (earth_azimuths + 180.0) % 360.0 - 180.0
    assert np.all(earth_az_dev >= -9.5), f"Earth azimuth libration west exceeded 9.5°: {np.min(earth_az_dev)}°"
    assert np.all(earth_az_dev <= 9.5), f"Earth azimuth libration east exceeded 9.5°: {np.max(earth_az_dev)}°"


# =============================================================================
# 3. Physics & Horizon Geometry Sanity Suite
# =============================================================================
def test_physics_flat_moon_curvature_drop():
    """Physics Invariant 1: Flat elevation grid with h_mast=0m must match analytical curvature drop."""
    n_az = 360
    n_dist = 200
    d_min = 20.0
    d_max = 25000.0

    # Completely flat elevation grid (Z = 0m everywhere)
    flat_z_grid = np.zeros((n_az, n_dist), dtype=np.float64)

    az_out, horiz_out, metrics = compute_horizon_mask(
        x0=0.0,
        y0=0.0,
        z0=0.0,
        mast_height=0.0,
        r_moon=R_MOON,
        n_azimuths=n_az,
        d_min=d_min,
        d_max=d_max,
        n_distances=n_dist,
        z_grid=flat_z_grid,
        use_cache=False,
    )

    # 1. Horizon angle must be <= 0° across all 360° azimuths
    assert np.all(horiz_out <= 0.0), f"Flat-moon horizon exceeded 0°: max={np.max(horiz_out)}°"

    # 2. Analytical maximum elevation angle occurs at d_min:
    # theta(d) = arctan(-d / (2 * R_Moon))
    analytical_drop_rad = np.arctan(-d_min / (2.0 * R_MOON))
    analytical_drop_deg = np.degrees(analytical_drop_rad)

    # Assert match within 1e-3 degrees
    max_err = np.max(np.abs(horiz_out - analytical_drop_deg))
    assert max_err < 1e-3, f"Curvature drop mismatch: max_error={max_err}° (expected < 1e-3°)"


def test_physics_mast_height_monotonicity():
    """Physics Invariant 2: Higher mast strictly lowers horizon mask and never decreases solar hours."""
    x0, y0, z0 = 12000.0, -8000.0, 1500.0

    # Compute horizon profiles for 1m, 5m, 15m
    _, h1, _ = compute_horizon_mask(x0=x0, y0=y0, z0=z0, mast_height=1.0, use_cache=False)
    _, h5, _ = compute_horizon_mask(x0=x0, y0=y0, z0=z0, mast_height=5.0, use_cache=False)
    _, h15, _ = compute_horizon_mask(x0=x0, y0=y0, z0=z0, mast_height=15.0, use_cache=False)

    # Strict monotonicity across all 360 azimuths: H_15m(alpha) < H_5m(alpha) < H_1m(alpha)
    assert np.all(h15 < h5), "Mast height 15m did not strictly lower horizon mask compared to 5m"
    assert np.all(h5 < h1), "Mast height 5m did not strictly lower horizon mask compared to 1m"

    # Integrated solar hours over 720 hours must never decrease with higher mast
    start_dt = datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc)
    az_360 = np.linspace(0, 360, 360, endpoint=False)

    hours_1m, hours_5m, hours_15m = 0.0, 0.0, 0.0
    for h in range(720):
        t_sample = start_dt + timedelta(hours=h)
        s_az, s_el = get_topocentric_sun(-89.54, 0.0, t_sample)
        horiz_1m_at_sun = interpolate_horizon(s_az, az_360, h1)
        horiz_5m_at_sun = interpolate_horizon(s_az, az_360, h5)
        horiz_15m_at_sun = interpolate_horizon(s_az, az_360, h15)

        if s_el >= horiz_1m_at_sun:
            hours_1m += 1.0
        if s_el >= horiz_5m_at_sun:
            hours_5m += 1.0
        if s_el >= horiz_15m_at_sun:
            hours_15m += 1.0

    assert hours_15m >= hours_5m >= hours_1m, \
        f"Monotonicity violation in solar hours: 1m={hours_1m}h, 5m={hours_5m}h, 15m={hours_15m}h"


def test_physics_penumbra_analytical_bounds():
    """Physics Invariant 3: Fractional solar disk penumbra analytical bounds and monotonicity."""
    r_sun = SOLAR_ANGULAR_RADIUS_DEG  # 0.2665°

    # 1. Boundary condition checks against 0° flat horizon
    # Umbra: theta <= -r_sun -> f = 0.0
    f_umbra = calculate_fractional_solar_illumination(sun_elevation_deg=-0.2665, horizon_elevation_deg=0.0)
    assert f_umbra == 0.0, f"Expected f=0.0 in full umbra, got {f_umbra}"

    # Bisected disk: theta = 0.0° -> f = 0.50 ± 1e-4
    f_half = calculate_fractional_solar_illumination(sun_elevation_deg=0.0, horizon_elevation_deg=0.0)
    assert abs(f_half - 0.50) < 1e-4, f"Expected f=0.50 for bisected disk, got {f_half}"

    # Full clearance: theta >= +r_sun -> f = 1.0
    f_full = calculate_fractional_solar_illumination(sun_elevation_deg=0.2665, horizon_elevation_deg=0.0)
    assert f_full == 1.0, f"Expected f=1.0 for full clearance, got {f_full}"

    # 2. Continuous sweep of 1,000 points in [-1.0°, +1.0°]
    test_angles = np.linspace(-1.0, 1.0, 1000)
    f_sweep = calculate_fractional_solar_illumination(sun_elevation_deg=test_angles, horizon_elevation_deg=0.0)

    # Assert bounded, no NaN or Inf
    assert not np.isnan(f_sweep).any(), "Found NaN in solar penumbra sweep"
    assert not np.isinf(f_sweep).any(), "Found Inf in solar penumbra sweep"
    assert np.all(f_sweep >= 0.0) and np.all(f_sweep <= 1.0), "f(t) out of [0, 1] bounds"

    # Assert non-decreasing across entire range
    assert np.all(np.diff(f_sweep) >= 0.0), "Penumbra sweep must be monotonically non-decreasing"

    # Assert strictly increasing inside penumbra (-0.26°, +0.26°)
    pen_mask = (test_angles >= -0.26) & (test_angles <= 0.26)
    f_pen = f_sweep[pen_mask]
    assert np.all(np.diff(f_pen) > 0.0), "Penumbra segment must be strictly increasing"


def test_physics_crater_psr_vs_peak_contrast():
    """Physics Invariant 4: Deep crater bowl floor (<5% illum / PSR) vs elevated rim peak (>65% illum)."""
    # 720 hours in southern summer (January 2026)
    start_dt = datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc)
    az_360 = np.linspace(0, 360, 360, endpoint=False)

    # 1. Deep crater floor: rim elevated 2,000m at 10km distance -> H(alpha) >= 11.3°
    h_crater_floor = np.full(360, 11.3)

    # 2. Elevated rim peak: low horizon mask H(alpha) <= 0.3°
    h_rim_peak = np.full(360, 0.25)

    floor_illuminated_hours = 0.0
    peak_illuminated_hours = 0.0

    for h in range(720):
        t_sample = start_dt + timedelta(hours=h)
        s_az, s_el = get_topocentric_sun(-89.78, 129.78, t_sample)

        f_floor = calculate_fractional_solar_illumination(s_el, 11.3)
        f_peak = calculate_fractional_solar_illumination(s_el, 0.25)

        floor_illuminated_hours += f_floor
        peak_illuminated_hours += f_peak

    pct_floor = (floor_illuminated_hours / 720.0) * 100.0
    pct_peak = (peak_illuminated_hours / 720.0) * 100.0

    # Deep crater bowl must evaluate to < 5% (PSR behavior)
    assert pct_floor < 5.0, f"Crater floor illumination {pct_floor:.2f}% exceeded 5% PSR limit"

    # Elevated rim peak must evaluate to > 65%
    assert pct_peak > 65.0, f"Rim peak illumination {pct_peak:.2f}% was below 65% target"


def test_physics_monte_carlo_performance_and_reproducibility():
    """Physics Invariant 5: 250-point Monte Carlo runs in <250ms and is 100% bitwise reproducible."""
    # Run 1
    t0 = time.perf_counter()
    mc1 = run_dispersion_monte_carlo(
        site_x=12000.0,
        site_y=-8000.0,
        dispersion_radius_m=100.0,
        n_samples=250,
        seed=42,
    )
    t1 = time.perf_counter()
    runtime1_ms = (t1 - t0) * 1000.0

    # Run 2
    t2 = time.perf_counter()
    mc2 = run_dispersion_monte_carlo(
        site_x=12000.0,
        site_y=-8000.0,
        dispersion_radius_m=100.0,
        n_samples=250,
        seed=42,
    )
    t3 = time.perf_counter()
    runtime2_ms = (t3 - t2) * 1000.0

    # 1. Performance verification: < 250 ms (typically < 20 ms)
    assert runtime1_ms < 250.0, f"Monte Carlo Run 1 took {runtime1_ms:.2f} ms (expected < 250 ms)"
    assert runtime2_ms < 250.0, f"Monte Carlo Run 2 took {runtime2_ms:.2f} ms (expected < 250 ms)"

    # 2. 100% Bitwise Reproducibility across identical seeds
    np.testing.assert_array_equal(mc1["dx_m"], mc2["dx_m"])
    np.testing.assert_array_equal(mc1["dy_m"], mc2["dy_m"])
    np.testing.assert_array_equal(mc1["slope_deg"], mc2["slope_deg"])
    np.testing.assert_array_equal(mc1["illumination_pct"], mc2["illumination_pct"])
    np.testing.assert_array_equal(mc1["dte_pct"], mc2["dte_pct"])
    np.testing.assert_array_equal(mc1["status"], mc2["status"])
    np.testing.assert_array_equal(mc1["status_code"], mc2["status_code"])
    assert mc1["summary"]["survival_probability_pct"] == mc2["summary"]["survival_probability_pct"]


# =============================================================================
# 4. Headless Streamlit UI Wiring & End-to-End Integration
# =============================================================================
def test_streamlit_ui_wiring():
    """Verify Streamlit app renders headlessly with zero exceptions, responds to sliders, and displays provenance."""
    from streamlit.testing.v1 import AppTest

    app_path = os.path.join(_lunascope_root, "app.py")
    assert os.path.exists(app_path), f"app.py not found at {app_path}"

    # 1. Initial Headless Render
    at = AppTest.from_file(app_path)
    at.run(timeout=120)
    assert len(at.exception) == 0, f"Streamlit raised exceptions on load: {[e.message for e in at.exception]}"

    # Verify provenance badges rendered in markdown
    all_markdown = " ".join(m.value for m in at.markdown)
    assert "Demonstration" in all_markdown, "Demonstration disclosure not rendered in UI"
    assert "Derived" in all_markdown, "Provenance badge [Derived] not rendered in UI"
    assert "Assumed" in all_markdown, "Provenance badge [Assumed] not rendered in UI"

    # 2. Test Slider Interaction: Increase consecutive days requirement to 14.5 days
    day_sliders = [s for s in at.slider if "Consecutive" in s.label]
    assert len(day_sliders) > 0, "Could not find Required Consecutive Days slider"
    consec_slider = day_sliders[0]

    # Set to strict 14.5 days requirement (which triggers FAIL for sites with < 14.5d)
    consec_slider.set_value(14.5).run(timeout=120)
    assert len(at.exception) == 0, f"Exceptions after slider update: {[e.message for e in at.exception]}"

    # 3. Assert Contingency / Fail status is triggered and backup candidates populated
    updated_markdown = " ".join(m.value for m in at.markdown)
    has_contingency_state = "CONTINGENCY" in updated_markdown or "FAIL" in updated_markdown
    assert has_contingency_state, "Expected CONTINGENCY REQUIRED or FAIL card to display for 14.5d requirement"

    # Verify backup recommendations table exists
    assert len(at.dataframe) > 0, "Expected backup candidate dataframe table to render in UI"
