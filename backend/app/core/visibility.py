"""
Visibility Evaluation & Operational Regime Classifier.
Implements fractional solar disk penumbral grazing with Eddington limb darkening,
geometric Direct-to-Earth (DTE) line-of-sight tracking, and interval metric integrations.
"""

import math
from typing import Dict, List, Any
import numpy as np

from app.core.ephemeris import SOLAR_RADIUS_DEG


def fractional_solar_visibility(
    sun_az_deg: List[float] | np.ndarray,
    sun_el_deg: List[float] | np.ndarray,
    horizon_360: List[float] | np.ndarray,
    limb_darkening: bool = False
) -> List[float]:
    """
    Computes exposed solar disk fraction f(t) in [0.0, 1.0] accounting for
    penumbral ridge grazing and optional solar limb darkening.
    
    Formula:
      u = (elevation - horizon) / solar_radius
      u >= 1.0  -> 1.0 (Full disk)
      u <= -1.0 -> 0.0 (Total shadow)
      -1.0 < u < 1.0 -> circular segment area integration with limb darkening profile:
        I(r) = 1 - u_coeff * (1 - sqrt(1 - r^2))
    """
    az_arr = np.asarray(sun_az_deg, dtype=np.float64)
    el_arr = np.asarray(sun_el_deg, dtype=np.float64)
    h_arr = np.asarray(horizon_360, dtype=np.float64)

    h_local = np.interp(az_arr % 360, np.arange(361), np.append(h_arr, h_arr[0]))

    # Normalized vertical offset: u = (sun_elevation - horizon) / solar_radius
    u = (el_arr - h_local) / SOLAR_RADIUS_DEG

    f = np.zeros_like(u, dtype=np.float64)
    f[u >= 1.0] = 1.0

    partial = (u > -1.0) & (u < 1.0)
    if np.any(partial):
        u_p = u[partial]
        # Standard geometric circular segment area fraction
        f_geom = (np.arccos(-u_p) + u_p * np.sqrt(1.0 - u_p ** 2)) / np.pi

        if limb_darkening:
            # Linear limb darkening correction (u_coeff = 0.6 for solar photosphere)
            u_coeff = 0.6
            # Weight disk center higher than grazing limbs
            moment = 0.5 * (2/3 + u_p - u_p**3/3)
            f_val = ((1-u_coeff) * f_geom + u_coeff * moment) / (1-u_coeff/3)
            f[partial] = np.clip(f_val, 0.0, 1.0)
        else:
            f[partial] = f_geom

    return [round(float(val), 4) for val in f]


def evaluate_dte_visibility(
    earth_az_deg: List[float] | np.ndarray,
    earth_el_deg: List[float] | np.ndarray,
    horizon_360: List[float] | np.ndarray,
    margin_deg: float = 0.0
) -> List[int]:
    """
    Evaluates geometric Direct-to-Earth (DTE) visibility C(t) in {0, 1}.
    C(t) = 1 if Earth center elevation clears local terrain horizon + margin.
    """
    az_arr = np.asarray(earth_az_deg, dtype=np.float64)
    el_arr = np.asarray(earth_el_deg, dtype=np.float64)
    h_arr = np.asarray(horizon_360, dtype=np.float64)

    h_local = np.interp(az_arr % 360, np.arange(361), np.append(h_arr, h_arr[0]))

    visible = el_arr > (h_local + margin_deg)
    return [int(val) for val in visible]


def classify_operational_states(
    solar_fractions: List[float],
    dte_visibility: List[int],
    sun_threshold: float = 0.10
) -> List[int]:
    """
    Classify each timestep into one of four operational regimes:
      - State 1: Nominal Science (f >= thresh and DTE == 1)
      - State 2: Autonomous Day (f >= thresh and DTE == 0)
      - State 3: Tethered Eclipse (f < thresh and DTE == 1)
      - State 4: Total Blackout (f < thresh and DTE == 0)
    """
    states = []
    for f, c in zip(solar_fractions, dte_visibility):
        has_sun = (f >= sun_threshold)
        has_comms = (c == 1)
        if has_sun and has_comms:
            states.append(1)
        elif has_sun and not has_comms:
            states.append(2)
        elif not has_sun and has_comms:
            states.append(3)
        else:
            states.append(4)
    return states


def compute_interval_metrics(solar_fractions, dte_visibility, step_hours=1.0, sun_threshold=0.10, sample_hours=None):
    if len(solar_fractions) != len(dte_visibility):
        raise ValueError('Mismatched visibility arrays')
    weights = np.asarray(sample_hours if sample_hours is not None else [step_hours]*len(solar_fractions), dtype=float)
    if len(weights) != len(solar_fractions) or np.any(~np.isfinite(weights)) or np.any(weights < 0):
        raise ValueError('Invalid interval durations')
    total = float(weights.sum())
    sun = np.asarray(solar_fractions) >= sun_threshold
    earth = np.asarray(dte_visibility) == 1
    def longest(mask):
        best = current = 0.0
        for active, hours in zip(mask, weights):
            if hours == 0: continue
            current = current + hours if active else 0.0
            best = max(best, current)
        return best
    def pct(mask): return float(weights[mask].sum())/total*100 if total else 0.0
    return {'total_duration_hours': total, 'sun_availability_pct': pct(sun),
            'equivalent_sun_hours': float(np.dot(solar_fractions,weights)),
            'longest_shadow_gap_hours': longest(~sun), 'earth_availability_pct': pct(earth),
            'longest_earth_outage_hours': longest(~earth), 'joint_availability_pct': pct(sun & earth),
            'longest_joint_window_hours': longest(sun & earth), 'coverage': 'complete' if total else 'unknown'}
