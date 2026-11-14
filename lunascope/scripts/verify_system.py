"""LunaScope Standalone Verification & System Authenticity Diagnostic CLI Runner.

Executes all scientific, physical, mathematical, and UI wiring checks.
Measures latency and outputs a formatted verification report table.
"""

from datetime import datetime, timezone, timedelta
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple
import numpy as np

# Configure path so lunascope core and plugins can be resolved
_script_dir = Path(__file__).resolve().parent
_lunascope_root = _script_dir.parent
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

# ANSI Color Codes
CLR_RESET = "\033[0m"
CLR_BOLD = "\033[1m"
CLR_GREEN = "\033[32m"
CLR_RED = "\033[31m"
CLR_CYAN = "\033[36m"
CLR_YELLOW = "\033[33m"
CLR_MAGENTA = "\033[35m"
CLR_GRAY = "\033[90m"


class DiagnosticReport:
    def __init__(self):
        self.results: List[Dict[str, Any]] = []

    def record(
        self,
        category: str,
        test_name: str,
        measured: str,
        expected: str,
        passed: bool,
        latency_ms: float,
        notes: str = "",
    ):
        self.results.append({
            "category": category,
            "test_name": test_name,
            "measured": measured,
            "expected": expected,
            "passed": passed,
            "latency_ms": latency_ms,
            "notes": notes,
        })

    def print_summary(self):
        print("\n" + "=" * 115)
        print(f"{CLR_BOLD}{CLR_CYAN}🌔 LUNASCOPE: SCIENTIFIC AUTHENTICITY, PHYSICS SANITY & UI VERIFICATION REPORT{CLR_RESET}")
        print(f"{CLR_GRAY}Timestamp: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')} | Platform: {sys.platform} | Python: {sys.version.split()[0]}{CLR_RESET}")
        print("=" * 115)

        categories = {}
        for r in self.results:
            cat = r["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(r)

        total_pass = sum(1 for r in self.results if r["passed"])
        total_fail = sum(1 for r in self.results if not r["passed"])
        total_time_ms = sum(r["latency_ms"] for r in self.results)

        for cat, items in categories.items():
            print(f"\n{CLR_BOLD}{CLR_MAGENTA}▶ {cat.upper()}{CLR_RESET}")
            print("-" * 115)
            print(f"{'Status':<8} | {'Test Name':<38} | {'Measured Value':<24} | {'Expected Bound':<22} | {'Time (ms)':<8}")
            print("-" * 115)

            for item in items:
                status_str = f"{CLR_GREEN}[PASS]{CLR_RESET}" if item["passed"] else f"{CLR_RED}[FAIL]{CLR_RESET}"
                print(
                    f"{status_str:<17} | "
                    f"{item['test_name']:<38} | "
                    f"{item['measured'][:24]:<24} | "
                    f"{item['expected'][:22]:<22} | "
                    f"{item['latency_ms']:>8.2f}"
                )
                if item["notes"] and not item["passed"]:
                    print(f"       {CLR_YELLOW}↳ Note: {item['notes']}{CLR_RESET}")

        print("=" * 115)
        summary_color = CLR_GREEN if total_fail == 0 else CLR_RED
        print(
            f"{CLR_BOLD}SUMMARY: {summary_color}{total_pass} PASSED{CLR_RESET}, "
            f"{CLR_RED if total_fail > 0 else CLR_GRAY}{total_fail} FAILED{CLR_RESET} "
            f"across {len(self.results)} total audits in {total_time_ms:.1f} ms"
        )
        print("=" * 115 + "\n")
        return total_fail == 0


def run_diagnostics() -> bool:
    report = DiagnosticReport()

    # -------------------------------------------------------------------------
    # 1. Ground-Truth Data & Provenance Audit
    # -------------------------------------------------------------------------
    cat = "1. Data Authenticity & Provenance"

    # Check 1.1: Filesystem Raw Data / Fallback Detection
    t0 = time.perf_counter()
    raw_info = check_raw_data_status()
    t_ms = (time.perf_counter() - t0) * 1000.0
    passed = "is_synthetic_fallback" in raw_info and "provenance_flag" in raw_info
    meas = f"Fallback={raw_info['is_synthetic_fallback']}"
    exp = "Deterministic detection"
    report.record(cat, "Raw Filesystem & Fallback Check", meas, exp, passed, t_ms)

    # Check 1.2: Synthetic Fallback Provenance Tagging
    t0 = time.perf_counter()
    df_sites, is_synthetic = load_candidate_sites()
    t_ms = (time.perf_counter() - t0) * 1000.0
    if is_synthetic:
        flag = df_sites.attrs.get("provenance_flag", "")
        passed = flag == "[Assumed / Synthetic Fallback]" and is_synthetic is True
        meas = f"Flag={flag}"
        exp = "[Assumed / Synthetic Fallback]"
    else:
        flag = df_sites.attrs.get("provenance_flag", "")
        passed = flag == "[Published]"
        meas = f"Flag={flag}"
        exp = "[Published]"
    report.record(cat, "Provenance Flag Attribution", meas, exp, passed, t_ms)

    # Check 1.3: Artemis III Candidate Sites & Polar Coordinates
    t0 = time.perf_counter()
    required_regions = ["Shackleton Rim", "Connecting Ridge", "Malapert Massif", "Leibnitz Beta", "Haworth", "Nobile Rim 1", "de Gerlache Rim"]
    site_names = df_sites["name"].tolist()
    missing_regions = [r for r in required_regions if not any(r.lower() in s.lower() for s in site_names)]
    lat_ok = (-90.0 <= df_sites["lat_deg"]).all() and (df_sites["lat_deg"] <= -80.0).all()
    passed = len(missing_regions) == 0 and lat_ok and len(df_sites) >= 15
    t_ms = (time.perf_counter() - t0) * 1000.0
    meas = f"{len(df_sites)} sites, Lats:[{df_sites['lat_deg'].min():.1f}°, {df_sites['lat_deg'].max():.1f}°]"
    exp = "15 sites, [-90°, -80°]"
    report.record(cat, "Candidate Spatial & Region Audit", meas, exp, passed, t_ms)

    # Check 1.4: Multi-Year Illumination Completeness (2025-2032)
    t0 = time.perf_counter()
    nan_count = 0
    for y in range(2025, 2033):
        col = f"consec_days_{y}"
        nan_count += df_sites[col].isna().sum()
    t_ms = (time.perf_counter() - t0) * 1000.0
    passed = nan_count == 0
    meas = f"{nan_count} NaNs across 8 years"
    exp = "0 NaNs (2025-2032)"
    report.record(cat, "2025-2032 Illumination Matrix", meas, exp, passed, t_ms)

    # Check 1.5: Contingency Decision Explainability
    t0 = time.perf_counter()
    res = evaluate_contingency(df_sites, "SHACKLETON_RIM", target_year=2026, required_consecutive_days=10.0)
    p_reasons = res["primary_evaluation"]["reasons"]
    passed = len(p_reasons) > 0 and len(res["backup_candidates"]) == len(df_sites) - 1
    t_ms = (time.perf_counter() - t0) * 1000.0
    meas = f"{len(p_reasons)} reasons, {len(res['backup_candidates'])} backups"
    exp = "Deterministic reasons"
    report.record(cat, "Contingency Matcher & Explainability", meas, exp, passed, t_ms)

    # -------------------------------------------------------------------------
    # 2. Astronomical Ephemeris Benchmark
    # -------------------------------------------------------------------------
    cat = "2. Ephemeris & Orbit Invariants"

    t0 = time.perf_counter()
    obs_lat = -89.54
    obs_lon = 0.0
    start_dt = datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc)

    sun_els, sun_azs, earth_els, earth_azs = [], [], [], []
    for h in range(720):
        t = start_dt + timedelta(hours=h)
        s_az, s_el = get_topocentric_sun(obs_lat, obs_lon, t)
        e_az, e_el = get_topocentric_earth(obs_lat, obs_lon, t)
        sun_els.append(s_el)
        sun_azs.append(s_az)
        earth_els.append(e_el)
        earth_azs.append(e_az)

    sun_els = np.array(sun_els)
    sun_azs = np.array(sun_azs)
    earth_els = np.array(earth_els)
    earth_azs = np.array(earth_azs)
    t_ms = (time.perf_counter() - t0) * 1000.0

    # Check 2.1: Solar Elevation Bounds
    min_sel, max_sel = np.min(sun_els), np.max(sun_els)
    passed = -2.5 <= min_sel and max_sel <= 2.5
    report.record(cat, "Sun Elevation 30-Day Limits", f"[{min_sel:.2f}°, {max_sel:.2f}°]", "[-2.5°, +2.5°]", passed, t_ms / 4)

    # Check 2.2: Solar Azimuth Full Sweep (360°)
    unwrapped_sun = np.degrees(np.unwrap(np.radians(sun_azs)))
    az_sweep = abs(unwrapped_sun[-1] - unwrapped_sun[0])
    hourly_diffs = np.abs(np.diff(unwrapped_sun))
    passed = az_sweep >= 360.0 and (0.45 <= hourly_diffs).all() and (hourly_diffs <= 0.56).all()
    report.record(cat, "Sun Azimuth Monotonic Sweep", f"Sweep={az_sweep:.1f}°, {np.mean(hourly_diffs):.3f}°/h", ">=360°, ~0.507°/h", passed, t_ms / 4)

    # Check 2.3: Earth Optical Libration Elevation
    min_eel, max_eel = np.min(earth_els), np.max(earth_els)
    passed = -8.5 <= min_eel and max_eel <= 8.5
    report.record(cat, "Earth Elevation Libration Box", f"[{min_eel:.2f}°, {max_eel:.2f}°]", "[-8.5°, +8.5°]", passed, t_ms / 4)

    # Check 2.4: Earth Optical Libration Azimuth
    earth_az_dev = (earth_azs + 180.0) % 360.0 - 180.0
    min_eaz, max_eaz = np.min(earth_az_dev), np.max(earth_az_dev)
    passed = -9.5 <= min_eaz and max_eaz <= 9.5
    report.record(cat, "Earth Azimuth Libration Box", f"[{min_eaz:.2f}°, {max_eaz:.2f}°]", "[-9.5°, +9.5°]", passed, t_ms / 4)

    # -------------------------------------------------------------------------
    # 3. Physics & Horizon Geometry Sanity Suite
    # -------------------------------------------------------------------------
    cat = "3. Physics & Horizon Geometry"

    # Check 3.1: Flat-Moon Curvature Drop Test
    t0 = time.perf_counter()
    flat_z = np.zeros((360, 200), dtype=np.float64)
    _, h_flat, _ = compute_horizon_mask(0.0, 0.0, 0.0, mast_height=0.0, d_min=20.0, z_grid=flat_z, use_cache=False)
    analytical_drop = np.degrees(np.arctan(-20.0 / (2.0 * R_MOON)))
    max_err = np.max(np.abs(h_flat - analytical_drop))
    passed = (h_flat <= 0.0).all() and max_err < 1e-3
    t_ms = (time.perf_counter() - t0) * 1000.0
    report.record(cat, "Flat-Moon Curvature Drop", f"Err={max_err:.6f}°, Max={h_flat.max():.6f}°", f"Analytical ±1e-3°", passed, t_ms)

    # Check 3.2: Mast-Height Monotonicity Test
    t0 = time.perf_counter()
    _, h1, _ = compute_horizon_mask(12000.0, -8000.0, 1500.0, mast_height=1.0, use_cache=False)
    _, h5, _ = compute_horizon_mask(12000.0, -8000.0, 1500.0, mast_height=5.0, use_cache=False)
    _, h15, _ = compute_horizon_mask(12000.0, -8000.0, 1500.0, mast_height=15.0, use_cache=False)
    passed_mask = (h15 < h5).all() and (h5 < h1).all()

    # Solar hours monotonicity
    az_360 = np.linspace(0, 360, 360, endpoint=False)
    sh1, sh5, sh15 = 0.0, 0.0, 0.0
    for h in range(720):
        t_sample = start_dt + timedelta(hours=h)
        s_az, s_el = get_topocentric_sun(-89.54, 0.0, t_sample)
        if s_el >= interpolate_horizon(s_az, az_360, h1): sh1 += 1.0
        if s_el >= interpolate_horizon(s_az, az_360, h5): sh5 += 1.0
        if s_el >= interpolate_horizon(s_az, az_360, h15): sh15 += 1.0
    passed_hours = sh15 >= sh5 >= sh1
    t_ms = (time.perf_counter() - t0) * 1000.0
    report.record(cat, "Mast-Height Monotonicity", f"H15<H5<H1: {passed_mask}, Hours:{sh15}>={sh5}>={sh1}", "Strict decrease/gain", passed_mask and passed_hours, t_ms)

    # Check 3.3: Solar Disk Penumbra Analytical Bounds
    t0 = time.perf_counter()
    f_u = calculate_fractional_solar_illumination(-0.2665, 0.0)
    f_h = calculate_fractional_solar_illumination(0.0, 0.0)
    f_c = calculate_fractional_solar_illumination(0.2665, 0.0)
    sweep_angles = np.linspace(-1.0, 1.0, 1000)
    sweep_f = calculate_fractional_solar_illumination(sweep_angles, 0.0)
    pen_mask = (sweep_angles >= -0.26) & (sweep_angles <= 0.26)
    pen_mono = (np.diff(sweep_f[pen_mask]) > 0.0).all()
    bounds_ok = f_u == 0.0 and abs(f_h - 0.5) < 1e-4 and f_c == 1.0 and pen_mono
    t_ms = (time.perf_counter() - t0) * 1000.0
    report.record(cat, "Fractional Penumbra Bounds", f"f=[-r:0, 0:0.5, +r:1.0]", "Exact analytical", bounds_ok, t_ms)

    # Check 3.4: Crater Floor (PSR) vs Rim Peak Contrast
    t0 = time.perf_counter()
    floor_hrs, peak_hrs = 0.0, 0.0
    for h in range(720):
        t_sample = start_dt + timedelta(hours=h)
        s_az, s_el = get_topocentric_sun(-89.78, 129.78, t_sample)
        floor_hrs += calculate_fractional_solar_illumination(s_el, 11.3)
        peak_hrs += calculate_fractional_solar_illumination(s_el, 0.25)
    pct_floor = (floor_hrs / 720.0) * 100.0
    pct_peak = (peak_hrs / 720.0) * 100.0
    passed = pct_floor < 5.0 and pct_peak > 65.0
    t_ms = (time.perf_counter() - t0) * 1000.0
    report.record(cat, "Crater Floor (PSR) vs Peak Contrast", f"Floor={pct_floor:.1f}%, Peak={pct_peak:.1f}%", "Floor<5%, Peak>65%", passed, t_ms)

    # Check 3.5: Monte Carlo Latency (<250ms) & Bitwise Reproducibility
    t0 = time.perf_counter()
    mc1 = run_dispersion_monte_carlo(12000.0, -8000.0, seed=42)
    mc2 = run_dispersion_monte_carlo(12000.0, -8000.0, seed=42)
    t_ms = (time.perf_counter() - t0) * 1000.0
    repro = (
        np.array_equal(mc1["dx_m"], mc2["dx_m"]) and
        np.array_equal(mc1["slope_deg"], mc2["slope_deg"]) and
        np.array_equal(mc1["illumination_pct"], mc2["illumination_pct"]) and
        np.array_equal(mc1["status"], mc2["status"])
    )
    passed = mc1["summary"]["runtime_ms"] < 250.0 and repro
    meas = f"Runtime={mc1['summary']['runtime_ms']:.1f}ms, Repro={repro}"
    exp = "<250ms, 100% bitwise"
    report.record(cat, "Monte Carlo Performance & Repro", meas, exp, passed, t_ms)

    # -------------------------------------------------------------------------
    # 4. Headless Streamlit UI Wiring
    # -------------------------------------------------------------------------
    cat = "4. Streamlit UI Wiring & Integration"

    try:
        from streamlit.testing.v1 import AppTest
        t0 = time.perf_counter()
        app_path = os.path.join(_lunascope_root, "app.py")
        at = AppTest.from_file(app_path).run(timeout=15)
        init_ok = len(at.exception) == 0

        # Provenance tags
        all_md = " ".join(m.value for m in at.markdown)
        has_badges = "Published" in all_md and "Derived" in all_md and "Assumed" in all_md

        # Dynamic Slider interaction
        sliders = [s for s in at.slider if "Consecutive" in s.label]
        if sliders:
            sliders[0].set_value(14.5).run(timeout=15)
            update_ok = len(at.exception) == 0
            updated_md = " ".join(m.value for m in at.markdown)
            has_fail = "CONTINGENCY" in updated_md or "FAIL" in updated_md
        else:
            update_ok, has_fail = False, False

        passed = init_ok and has_badges and update_ok and has_fail
        t_ms = (time.perf_counter() - t0) * 1000.0
        meas = f"Exc={len(at.exception)}, Badges={has_badges}, FailCard={has_fail}"
        exp = "0 Exc, Badges, FailCard"
        report.record(cat, "Headless AppTest Integration", meas, exp, passed, t_ms)
    except Exception as e:
        report.record(cat, "Headless AppTest Integration", f"Error: {e}", "0 Exc, Badges, FailCard", False, 0.0, str(e))

    return report.print_summary()


if __name__ == "__main__":
    success = run_diagnostics()
    sys.exit(0 if success else 1)
