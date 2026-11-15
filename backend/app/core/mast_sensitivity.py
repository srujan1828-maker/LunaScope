"""
Parametric Mast Height Sensitivity Analysis.
Evaluates how increasing solar array or antenna height (0.5m to 15m)
progressively clears local terrain obstructions and extends mission duration.
"""

from typing import Dict, List, Any
from app.core.horizon import compute_horizon_360
from app.core.ephemeris import compute_ephemeris_track
from app.core.visibility import fractional_solar_visibility, evaluate_dte_visibility, compute_interval_metrics
from app.data.sites_catalog import get_site_by_id
from app.core.nasa_data import provenance


def evaluate_mast_sensitivity(
    site_id: str,
    start_unix: float,
    end_unix: float,
    mast_heights: List[float] = [0.5, 1.0, 2.0, 3.5, 5.0, 7.5, 10.0, 15.0]
) -> Dict[str, Any]:
    """
    Parametric sweep of observer/mast height.
    """
    site_info = get_site_by_id(site_id)
    if not site_info:
        raise ValueError(f"Site '{site_id}' not found.")

    step_seconds = 3600.0
    eph = compute_ephemeris_track(
        site_info["lat_deg"],
        site_info["lon_deg"],
        start_unix,
        end_unix,
        step_seconds=step_seconds
    )

    sweep_results = []
    base_metrics = None

    for h in sorted(mast_heights):
        horizon = compute_horizon_360(
            lat_deg=site_info["lat_deg"],
            lon_deg=site_info["lon_deg"],
            base_elevation_m=site_info["elevation_m"],
            mast_height_m=h
        )
        f_sun = fractional_solar_visibility(eph["sun_azimuth"], eph["sun_elevation"], horizon,angular_radius_deg=eph['solar_angular_radius_deg'])
        c_dte = evaluate_dte_visibility(eph["earth_azimuth"], eph["earth_elevation"], horizon)
        m = compute_interval_metrics(f_sun, c_dte, sample_hours=[max(0,min(3600,end_unix-t))/3600 for t in eph["timestamps"]])

        if base_metrics is None:
            base_metrics = m

        sun_gain_hours = round(m["equivalent_sun_hours"] - base_metrics["equivalent_sun_hours"], 1)
        shadow_reduction_hours = round(base_metrics["longest_shadow_gap_hours"] - m["longest_shadow_gap_hours"], 1)

        sweep_results.append({
            "mast_height_m": h,
            "metrics": m,
            "sun_gain_hours": sun_gain_hours,
            "shadow_reduction_hours": shadow_reduction_hours,
            "horizon_mean_elevation_deg": round(sum(horizon) / len(horizon), 2)
        })

    return {
        "site_id": site_id,
        "provenance": {**provenance(),'time_range_unix':[start_unix,end_unix],
            'method':'Spherical horizon recalculated at each mast height; hourly temporal sampling'},
        "site_name": site_info["name"],
        "baseline_mast_m": min(mast_heights) if mast_heights else 0.5,
        "sweep": sweep_results
    }
