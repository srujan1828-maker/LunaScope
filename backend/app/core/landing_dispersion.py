"""
Landing Dispersion & Terrain Sensitivity Analysis (Monte Carlo Sampling).
Evaluates operational risk bounds across a landing dispersion ellipse (100m to 500m)
accounting for local micro-topography, horizon shifts, and shadow gradients.
"""

import math
from typing import Dict, List, Any
import numpy as np

from app.core.coordinates import latlon_to_stereo, stereo_to_latlon, R_MOON
from app.core.horizon import compute_horizon_360
from app.core.ephemeris import compute_ephemeris_track
from app.core.visibility import fractional_solar_visibility, evaluate_dte_visibility, compute_interval_metrics
from app.data.sites_catalog import get_site_by_id


def evaluate_landing_dispersion(
    site_id: str,
    start_unix: float,
    end_unix: float,
    semi_major_m: float = 200.0,
    semi_minor_m: float = 100.0,
    num_samples: int = 24,
    mast_height_m: float = 2.0
) -> Dict[str, Any]:
    """
    Evaluates sensitivity and dispersion envelope for a candidate landing ellipse.
    """
    site_info = get_site_by_id(site_id)
    if not site_info:
        raise ValueError(f"Site '{site_id}' not found.")

    lat0 = site_info["lat_deg"]
    lon0 = site_info["lon_deg"]
    x0, y0 = latlon_to_stereo(lat0, lon0)
    base_elev = site_info["elevation_m"]

    # Ephemeris at nominal center
    step_seconds = 3600.0
    eph = compute_ephemeris_track(lat0, lon0, start_unix, end_unix, step_seconds=step_seconds)

    # Sample dispersion points in concentric rings around nominal landing target
    sample_points = []
    
    # Center point (sample 0)
    sample_points.append({
        "dx_m": 0.0,
        "dy_m": 0.0,
        "lat_deg": lat0,
        "lon_deg": lon0,
        "is_center": True
    })

    # Elliptical samples
    for ring_idx, ring_fraction in enumerate([0.5, 1.0]):
        n_ring = (num_samples - 1) // 2 + (1 if ring_idx == 1 and num_samples % 2 == 0 else 0)
        for i in range(n_ring):
            angle = (2.0 * math.pi * i) / n_ring
            dx = ring_fraction * semi_major_m * math.cos(angle)
            dy = ring_fraction * semi_minor_m * math.sin(angle)
            
            x_sample = x0 + dx
            y_sample = y0 + dy
            lat_s, lon_s = stereo_to_latlon(x_sample, y_sample)
            
            sample_points.append({
                "dx_m": round(dx, 1),
                "dy_m": round(dy, 1),
                "lat_deg": round(lat_s, 4),
                "lon_deg": round(lon_s, 4),
                "is_center": False
            })

    # Evaluate each dispersion sample
    results = []
    sun_avail_list = []
    shadow_gap_list = []
    dte_avail_list = []

    for pt in sample_points:
        horizon = compute_horizon_360(
            lat_deg=pt["lat_deg"],
            lon_deg=pt["lon_deg"],
            base_elevation_m=base_elev,
            mast_height_m=mast_height_m
        )
        eph = compute_ephemeris_track(pt["lat_deg"], pt["lon_deg"], start_unix, end_unix, step_seconds=step_seconds)
        f_sun = fractional_solar_visibility(eph["sun_azimuth"], eph["sun_elevation"], horizon)
        c_dte = evaluate_dte_visibility(eph["earth_azimuth"], eph["earth_elevation"], horizon)
        m = compute_interval_metrics(f_sun, c_dte, sample_hours=[max(0,min(3600,end_unix-t))/3600 for t in eph["timestamps"]])

        sun_avail_list.append(m["sun_availability_pct"])
        shadow_gap_list.append(m["longest_shadow_gap_hours"])
        dte_avail_list.append(m["earth_availability_pct"])

        results.append({
            **pt,
            "metrics": m
        })

    # Envelope bounds
    envelope = {
        "sun_availability_pct": {
            "min": round(float(np.min(sun_avail_list)), 1),
            "median": round(float(np.median(sun_avail_list)), 1),
            "max": round(float(np.max(sun_avail_list)), 1),
            "spread": round(float(np.max(sun_avail_list) - np.min(sun_avail_list)), 1)
        },
        "longest_shadow_gap_hours": {
            "min": round(float(np.min(shadow_gap_list)), 1),
            "median": round(float(np.median(shadow_gap_list)), 1),
            "max": round(float(np.max(shadow_gap_list)), 1)
        },
        "earth_availability_pct": {
            "min": round(float(np.min(dte_avail_list)), 1),
            "median": round(float(np.median(dte_avail_list)), 1),
            "max": round(float(np.max(dte_avail_list)), 1)
        }
    }

    # Robustness rating
    spread = envelope["sun_availability_pct"]["spread"]
    if spread < 5.0:
        robustness = "High (Homogeneous Terrain)"
        robustness_notes = "Minor illumination variance across the dispersion ellipse. This describes illumination spread in the demonstration surface; landing hazard risk is unknown."
    elif spread < 15.0:
        robustness = "Moderate (Ridge Sensitivity)"
        robustness_notes = "Terrain ridges cause up to 15% illumination variance depending on touchdown location."
    else:
        robustness = "Low (High Shadow Gradient)"
        robustness_notes = "Severe shadow gradient across the ellipse. Touchdown location significantly affects mission duration."

    return {
        "site_id": site_id,
        "provenance": "Derived from procedural demonstration terrain; not a validated landing safety estimate",
        "site_name": site_info["name"],
        "dispersion_parameters": {
            "semi_major_axis_m": semi_major_m,
            "semi_minor_axis_m": semi_minor_m,
            "num_samples": len(sample_points),
            "mast_height_m": mast_height_m
        },
        "envelope": envelope,
        "robustness": robustness,
        "robustness_notes": robustness_notes,
        "sample_points": results
    }
