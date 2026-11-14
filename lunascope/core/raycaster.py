"""LunaScope 360-Degree Vectorized Terrain Horizon Raycaster.

Computes the local 360-degree topographic horizon mask H(alpha) accounting for:
1. User-configured lander mast height h_mast in [0, 20] meters.
2. Lunar spherical curvature drop (d^2 / (2 * R_Moon)), R_Moon = 1,737,400 meters.
3. High-performance vectorized NumPy array evaluation across all 360 azimuths.
4. Optional file-backed disk caching in data/cache/.
"""

import json
import os
from typing import Dict, Optional, Tuple, Union
import numpy as np

from core.projections import R_MOON
from core.synthetic_data import CACHE_DATA_DIR, get_elevation_profile


def compute_horizon_mask(
    x0: float,
    y0: float,
    z0: float = 1500.0,
    mast_height: float = 2.0,
    r_moon: float = R_MOON,
    n_azimuths: int = 360,
    d_min: float = 20.0,
    d_max: float = 25000.0,
    n_distances: int = 200,
    geotiff_path: Optional[str] = None,
    z_grid: Optional[np.ndarray] = None,
    use_cache: bool = True,
    cache_key: Optional[str] = None,
) -> Tuple[np.ndarray, np.ndarray, Dict[str, float]]:
    """Compute vectorized 360-degree horizon profile H(alpha).

    Mathematical Formulation:
        Delta Z(d) = Z(X_d, Y_d) - (Z_0 + h_mast)
        theta(alpha, d) = arctan( (Delta Z(d) - d^2 / (2 * R_Moon)) / d )
        H(alpha) = max_d theta(alpha, d)

    Args:
        x0: Observer stereographic X position in meters.
        y0: Observer stereographic Y position in meters.
        z0: Observer ground surface elevation in meters.
        mast_height: Sensor / solar array height above surface in meters (e.g. 2m).
        r_moon: Lunar radius in meters (1,737,400 m).
        n_azimuths: Number of angular slices around 360 degrees (default 360).
        d_min: Minimum raycast distance in meters (default 20m).
        d_max: Maximum raycast distance in meters (default 25km).
        n_distances: Radial sampling points along each ray (default 200).
        geotiff_path: Optional path to LOLA GeoTIFF raster.
        z_grid: Optional pre-computed 2D elevation grid of shape (n_azimuths, n_distances).
        use_cache: Whether to read/write results from data/cache/.
        cache_key: Optional identifier for cache file (e.g. site_id).

    Returns:
        (azimuths_deg, horizon_elevations_deg, summary_metrics)
    """
    # Check cache if key provided and no custom z_grid passed
    if use_cache and cache_key and z_grid is None:
        cache_file = os.path.join(CACHE_DATA_DIR, f"{cache_key}_mast_{int(mast_height*10)}.json")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r") as f:
                    data = json.load(f)
                return (
                    np.array(data["azimuths_deg"], dtype=np.float64),
                    np.array(data["horizon_elevations_deg"], dtype=np.float64),
                    data["metrics"],
                )
            except Exception:
                pass

    # Azimuth vector [0, 360)
    azimuths_deg = np.linspace(0.0, 360.0, n_azimuths, endpoint=False, dtype=np.float64)

    # Distances vector: log/geometric spacing gives higher resolution near observer
    distances_m = np.geomspace(d_min, d_max, n_distances, dtype=np.float64)

    # Elevation grid Z(alpha, d) of shape (n_azimuths, n_distances)
    if z_grid is None:
        z_grid = get_elevation_profile(
            x0=x0,
            y0=y0,
            distances_m=distances_m,
            azimuths_deg=azimuths_deg,
            geotiff_path=geotiff_path,
            site_elevation=z0,
        )
    else:
        z_grid = np.asarray(z_grid, dtype=np.float64)
        if z_grid.shape != (n_azimuths, n_distances):
            raise ValueError(f"Custom z_grid shape {z_grid.shape} must match ({n_azimuths}, {n_distances})")

    # Delta Z relative to elevated sensor position
    sensor_z = z0 + mast_height
    delta_z = z_grid - sensor_z  # Shape: (n_azimuths, n_distances)

    # Curvature drop d^2 / (2 * R_MOON)
    curvature_drop = (distances_m ** 2) / (2.0 * r_moon)  # Shape: (n_distances,)

    # Elevation angle theta(alpha, d)
    # theta = arctan( (Delta Z - curvature_drop) / d )
    numerator = delta_z - curvature_drop[np.newaxis, :]
    theta_rad = np.arctan(numerator / distances_m[np.newaxis, :])

    # Horizon mask H(alpha) = max_d theta(alpha, d)
    horizon_rad = np.max(theta_rad, axis=1)
    horizon_deg = np.degrees(horizon_rad)

    # Summary metrics
    metrics = {
        "min_horizon_deg": float(np.min(horizon_deg)),
        "max_horizon_deg": float(np.max(horizon_deg)),
        "mean_horizon_deg": float(np.mean(horizon_deg)),
        "sky_view_factor": float(np.mean(np.cos(horizon_rad) ** 2)),
        "mast_height_m": float(mast_height),
        "observer_elev_m": float(z0),
    }

    # Save cache if key provided
    if use_cache and cache_key:
        try:
            os.makedirs(CACHE_DATA_DIR, exist_ok=True)
            cache_file = os.path.join(CACHE_DATA_DIR, f"{cache_key}_mast_{int(mast_height*10)}.json")
            with open(cache_file, "w") as f:
                json.dump({
                    "azimuths_deg": azimuths_deg.tolist(),
                    "horizon_elevations_deg": horizon_deg.tolist(),
                    "metrics": metrics,
                }, f)
        except Exception:
            pass

    return azimuths_deg, horizon_deg, metrics


def interpolate_horizon(
    query_azimuths_deg: Union[float, np.ndarray],
    azimuths_deg: np.ndarray,
    horizon_deg: np.ndarray,
) -> Union[float, np.ndarray]:
    """Linearly interpolate the horizon elevation at arbitrary azimuths with periodic 360 wrap."""
    q_az = np.asarray(query_azimuths_deg, dtype=np.float64) % 360.0
    # Append wrap point for periodic interpolation
    extended_az = np.append(azimuths_deg, 360.0)
    extended_horiz = np.append(horizon_deg, horizon_deg[0])

    res = np.interp(q_az, extended_az, extended_horiz)
    if np.isscalar(query_azimuths_deg):
        return float(res)
    return res
