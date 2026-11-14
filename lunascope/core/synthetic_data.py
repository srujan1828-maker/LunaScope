"""LunaScope Synthetic Data & DEM Generator.

Generates:
1. Artemis III candidate landing sites database (15 sites) with modeled 2025-2032
   consecutive-day illumination windows, DTE visibility, and terrain stats.
   Modeled in alignment with Wueller et al. (2026) / Zenodo record 17084058.
2. Deterministic procedural South Pole DEM generator (crater bowls, raised rims,
   multi-frequency terrain noise) with graceful offline fallback when LOLA
   GeoTIFFs are not yet downloaded in data/raw/.
"""

import os
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd

from core.projections import latlon_to_xy, R_MOON

RAW_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw")
CACHE_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "cache")

# 15 Artemis III candidate landing sites with illustrative, unverified coordinates
CANDIDATE_SITES_METADATA: List[Dict[str, Any]] = [
    {
        "site_id": "SHACKLETON_RIM",
        "name": "Shackleton Rim",
        "lat_deg": -89.78,
        "lon_deg": 129.78,
        "elevation_m": 1250.0,
        "avg_slope_deg": 6.8,
        "annual_illum_pct": 86.4,
        "annual_dte_pct": 53.2,
        "consecutive_days_by_year": {
            2025: 11.8, 2026: 12.4, 2027: 13.6, 2028: 14.2,
            2029: 13.9, 2030: 12.8, 2031: 11.5, 2032: 10.9
        },
        "description": "Connecting ridge peak on the rim of Shackleton Crater; exceptional summer illumination."
    },
    {
        "site_id": "CONNECTING_RIDGE",
        "name": "Connecting Ridge",
        "lat_deg": -89.44,
        "lon_deg": 222.65,
        "elevation_m": 1420.0,
        "avg_slope_deg": 5.2,
        "annual_illum_pct": 82.1,
        "annual_dte_pct": 51.8,
        "consecutive_days_by_year": {
            2025: 10.5, 2026: 11.2, 2027: 12.4, 2028: 12.9,
            2029: 12.6, 2030: 11.4, 2031: 10.2, 2032: 9.8
        },
        "description": "Prominent high saddle between Shackleton and de Gerlache craters."
    },
    {
        "site_id": "MALAPERT_MASSIF",
        "name": "Malapert Massif",
        "lat_deg": -85.99,
        "lon_deg": 2.94,
        "elevation_m": 5100.0,
        "avg_slope_deg": 4.5,
        "annual_illum_pct": 91.5,
        "annual_dte_pct": 58.7,
        "consecutive_days_by_year": {
            2025: 13.4, 2026: 14.1, 2027: 15.0, 2028: 15.5,
            2029: 15.2, 2030: 14.3, 2031: 13.1, 2032: 12.6
        },
        "description": "Highest mountain peak in south polar region; continuous direct-to-Earth line of sight."
    },
    {
        "site_id": "LEIBNITZ_BETA",
        "name": "Leibnitz Beta Plateau",
        "lat_deg": -85.78,
        "lon_deg": 30.82,
        "elevation_m": 3300.0,
        "avg_slope_deg": 5.8,
        "annual_illum_pct": 87.2,
        "annual_dte_pct": 54.0,
        "consecutive_days_by_year": {
            2025: 11.9, 2026: 12.6, 2027: 13.8, 2028: 14.3,
            2029: 14.0, 2030: 12.9, 2031: 11.7, 2032: 11.1
        },
        "description": "Spacious elevated plateau with mild slopes and long solar visibility spans."
    },
    {
        "site_id": "HAWORTH_RIM",
        "name": "Haworth Rim",
        "lat_deg": -87.45,
        "lon_deg": 354.80,
        "elevation_m": 1900.0,
        "avg_slope_deg": 7.9,
        "annual_illum_pct": 74.3,
        "annual_dte_pct": 49.5,
        "consecutive_days_by_year": {
            2025: 8.4, 2026: 9.1, 2027: 10.2, 2028: 10.7,
            2029: 10.4, 2030: 9.3, 2031: 8.2, 2032: 7.8
        },
        "description": "Rim segment overlooking cold-trap PSR within Haworth crater."
    },
    {
        "site_id": "NOBILE_RIM_1",
        "name": "Nobile Rim 1",
        "lat_deg": -85.25,
        "lon_deg": 37.85,
        "elevation_m": 2150.0,
        "avg_slope_deg": 6.1,
        "annual_illum_pct": 79.8,
        "annual_dte_pct": 52.3,
        "consecutive_days_by_year": {
            2025: 9.6, 2026: 10.3, 2027: 11.5, 2028: 12.0,
            2029: 11.7, 2030: 10.6, 2031: 9.4, 2032: 8.9
        },
        "description": "Northwest rim crest of Nobile Crater, VIPER rover primary study target."
    },
    {
        "site_id": "NOBILE_RIM_2",
        "name": "Nobile Rim 2",
        "lat_deg": -85.40,
        "lon_deg": 35.80,
        "elevation_m": 2080.0,
        "avg_slope_deg": 5.9,
        "annual_illum_pct": 78.4,
        "annual_dte_pct": 51.6,
        "consecutive_days_by_year": {
            2025: 9.2, 2026: 9.9, 2027: 11.1, 2028: 11.6,
            2029: 11.3, 2030: 10.2, 2031: 9.0, 2032: 8.6
        },
        "description": "Southwest terrace of Nobile rim with wide landing zone radius."
    },
    {
        "site_id": "DE_GERLACHE_RIM_1",
        "name": "de Gerlache Rim 1",
        "lat_deg": -88.71,
        "lon_deg": 271.60,
        "elevation_m": 1800.0,
        "avg_slope_deg": 7.4,
        "annual_illum_pct": 81.0,
        "annual_dte_pct": 50.8,
        "consecutive_days_by_year": {
            2025: 10.1, 2026: 10.8, 2027: 12.0, 2028: 12.5,
            2029: 12.2, 2030: 11.0, 2031: 9.8, 2032: 9.3
        },
        "description": "Sharp ridge on eastern crest of de Gerlache crater."
    },
    {
        "site_id": "DE_GERLACHE_RIM_2",
        "name": "de Gerlache Rim 2",
        "lat_deg": -88.34,
        "lon_deg": 291.50,
        "elevation_m": 1650.0,
        "avg_slope_deg": 6.3,
        "annual_illum_pct": 76.5,
        "annual_dte_pct": 48.9,
        "consecutive_days_by_year": {
            2025: 8.8, 2026: 9.5, 2027: 10.7, 2028: 11.2,
            2029: 10.9, 2030: 9.7, 2031: 8.5, 2032: 8.0
        },
        "description": "Secondary plateau north-west of de Gerlache crater rim."
    },
    {
        "site_id": "PEAK_NEAR_SHACKLETON",
        "name": "Peak Near Shackleton",
        "lat_deg": -89.54,
        "lon_deg": 125.10,
        "elevation_m": 1380.0,
        "avg_slope_deg": 6.5,
        "annual_illum_pct": 83.5,
        "annual_dte_pct": 52.4,
        "consecutive_days_by_year": {
            2025: 10.9, 2026: 11.6, 2027: 12.8, 2028: 13.3,
            2029: 13.0, 2030: 11.8, 2031: 10.6, 2032: 10.1
        },
        "description": "Isolated topographic high 15km north of Shackleton rim."
    },
    {
        "site_id": "AMUNDSEN_RIM",
        "name": "Amundsen Rim",
        "lat_deg": -84.45,
        "lon_deg": 82.50,
        "elevation_m": 2400.0,
        "avg_slope_deg": 8.5,
        "annual_illum_pct": 71.0,
        "annual_dte_pct": 47.1,
        "consecutive_days_by_year": {
            2025: 7.5, 2026: 8.2, 2027: 9.3, 2028: 9.8,
            2029: 9.5, 2030: 8.4, 2031: 7.2, 2032: 6.8
        },
        "description": "Southern rim massif of Amundsen impact basin."
    },
    {
        "site_id": "FAUSTINI_RIM_A",
        "name": "Faustini Rim A",
        "lat_deg": -87.15,
        "lon_deg": 77.20,
        "elevation_m": 1550.0,
        "avg_slope_deg": 7.0,
        "annual_illum_pct": 75.8,
        "annual_dte_pct": 50.1,
        "consecutive_days_by_year": {
            2025: 8.7, 2026: 9.4, 2027: 10.6, 2028: 11.1,
            2029: 10.8, 2030: 9.6, 2031: 8.4, 2032: 8.0
        },
        "description": "Elevated ridge segment bordering Faustini crater floor."
    },
    {
        "site_id": "SHOEMAKER_RIM",
        "name": "Shoemaker Rim",
        "lat_deg": -88.10,
        "lon_deg": 45.30,
        "elevation_m": 1620.0,
        "avg_slope_deg": 7.7,
        "annual_illum_pct": 73.2,
        "annual_dte_pct": 48.2,
        "consecutive_days_by_year": {
            2025: 8.0, 2026: 8.7, 2027: 9.8, 2028: 10.3,
            2029: 10.0, 2030: 8.9, 2031: 7.7, 2032: 7.3
        },
        "description": "Crater rim adjacent to deep permanently shadowed region."
    },
    {
        "site_id": "SLATER_PLAIN",
        "name": "Slater Plain",
        "lat_deg": -88.08,
        "lon_deg": 111.40,
        "elevation_m": 1100.0,
        "avg_slope_deg": 3.8,
        "annual_illum_pct": 69.5,
        "annual_dte_pct": 46.5,
        "consecutive_days_by_year": {
            2025: 7.1, 2026: 7.8, 2027: 8.9, 2028: 9.4,
            2029: 9.1, 2030: 8.0, 2031: 6.9, 2032: 6.4
        },
        "description": "Smooth, low-slope plain between Faustini and Shoemaker craters."
    },
    {
        "site_id": "GERLACHE_KOCHER",
        "name": "Gerlache-Kocher Massif",
        "lat_deg": -86.55,
        "lon_deg": 225.40,
        "elevation_m": 2750.0,
        "avg_slope_deg": 6.4,
        "annual_illum_pct": 80.2,
        "annual_dte_pct": 51.2,
        "consecutive_days_by_year": {
            2025: 9.8, 2026: 10.5, 2027: 11.7, 2028: 12.2,
            2029: 11.9, 2030: 10.8, 2031: 9.6, 2032: 9.1
        },
        "description": "High relief massif between de Gerlache and Kocher craters."
    }
]


def check_raw_data_status() -> Dict[str, Any]:
    """Check whether raw published Zenodo data or LOLA GeoTIFFs are present in data/raw/.

    Returns:
        Dict with file presence status, paths, and active fallback mode.
    """
    zenodo_csv = os.path.join(RAW_DATA_DIR, "wueller2026_candidates.csv")
    lola_tif = os.path.join(RAW_DATA_DIR, "LDEM_80S_20M.tif")

    has_zenodo = os.path.exists(zenodo_csv)
    has_lola = os.path.exists(lola_tif)
    is_synthetic_active = not (has_zenodo and has_lola)

    return {
        "raw_dir": RAW_DATA_DIR,
        "zenodo_csv_path": zenodo_csv,
        "has_zenodo_csv": has_zenodo,
        "lola_tif_path": lola_tif,
        "has_lola_tif": has_lola,
        "is_synthetic_fallback": is_synthetic_active,
        "provenance_flag": "[Assumed / Synthetic Fallback]" if is_synthetic_active else "[Assumed / Unverified local input]",
    }


def load_candidate_sites(raw_csv_path: Optional[str] = None) -> Tuple[pd.DataFrame, bool]:
    """Load Artemis III candidate landing sites.

    If a real Zenodo CSV exists at raw_csv_path or data/raw/wueller2026_candidates.csv,
    reads it. Otherwise falls back to deterministic synthetic database.

    Returns:
        (DataFrame of candidate sites, is_synthetic boolean flag)
    """
    if raw_csv_path is None:
        raw_csv_path = os.path.join(RAW_DATA_DIR, "wueller2026_candidates.csv")

    if os.path.exists(raw_csv_path):
        try:
            df = pd.read_csv(raw_csv_path)
            df.attrs["is_synthetic_fallback"] = False
            df.attrs["provenance_flag"] = "[Assumed / Unverified local input]"
            df["is_synthetic_fallback"] = False
            df["provenance_flag"] = "[Assumed / Unverified local input]"
            df["provenance"] = "[Assumed / Unverified local input]"
            return df, False
        except Exception:
            pass

    # Build DataFrame from synthetic metadata
    records = []
    for s in CANDIDATE_SITES_METADATA:
        x, y = latlon_to_xy(s["lat_deg"], s["lon_deg"])
        row = {
            "site_id": s["site_id"],
            "name": s["name"],
            "lat_deg": s["lat_deg"],
            "lon_deg": s["lon_deg"],
            "x_m": round(x, 1),
            "y_m": round(y, 1),
            "elevation_m": s["elevation_m"],
            "avg_slope_deg": s["avg_slope_deg"],
            "annual_illum_pct": s["annual_illum_pct"],
            "annual_dte_pct": s["annual_dte_pct"],
            "description": s["description"],
        }
        for yr, val in s["consecutive_days_by_year"].items():
            row[f"consec_days_{yr}"] = val
        records.append(row)

    df = pd.DataFrame(records)
    df.attrs["is_synthetic_fallback"] = True
    df.attrs["provenance_flag"] = "[Assumed / Synthetic Fallback]"
    df["is_synthetic_fallback"] = True
    df["provenance_flag"] = "[Assumed / Synthetic Fallback]"
    df["provenance"] = "[Assumed / Synthetic Fallback]"
    return df, True


def generate_procedural_dem_patch(
    center_x: float,
    center_y: float,
    size_m: float = 6000.0,
    resolution_m: float = 20.0,
    base_elevation: float = 1500.0,
    seed: int = 42,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Generate a realistic 20m procedural Lunar South Pole elevation patch.

    Synthesizes:
    - Primary crater bowl with raised rim rampart
    - Secondary micro-craters
    - Multi-frequency fractal roughness
    - Regional regional slope gradient

    Args:
        center_x: Stereographic X center in meters.
        center_y: Stereographic Y center in meters.
        size_m: Total patch width and height in meters (default 6000m = 6km).
        resolution_m: Pixel pitch in meters (default 20m, matching LOLA LDEM 20M).
        base_elevation: Regional elevation offset in meters.
        seed: Random seed for deterministic reproducibility.

    Returns:
        (x_grid_1d, y_grid_1d, z_elevation_2d_array)
    """
    rng = np.random.RandomState(seed + int(abs(center_x) + abs(center_y)) % 10000)

    n_pts = int(size_m / resolution_m) + 1
    half_size = size_m / 2.0

    x_vec = np.linspace(center_x - half_size, center_x + half_size, n_pts)
    y_vec = np.linspace(center_y - half_size, center_y + half_size, n_pts)
    xx, yy = np.meshgrid(x_vec, y_vec)

    # Base elevation with smooth regional tilt
    z = np.full_like(xx, base_elevation, dtype=np.float64)
    z += 0.003 * (xx - center_x) - 0.002 * (yy - center_y)

    # Main local crater morphology (rim ~ 1800m offset from center)
    crater_r = 1600.0
    dx_c = xx - (center_x + 350.0)
    dy_c = yy - (center_y - 200.0)
    dist_c = np.sqrt(dx_c**2 + dy_c**2)

    # Inside crater bowl: parabolic depression
    bowl_mask = dist_c < crater_r
    depth = 380.0
    z[bowl_mask] -= depth * (1.0 - (dist_c[bowl_mask] / crater_r) ** 2)

    # Crater rim uplift: Gaussian annular ring
    rim_width = 320.0
    rim_height = 140.0
    z += rim_height * np.exp(-((dist_c - crater_r) / rim_width) ** 2)

    # Secondary impact craters
    n_secondary = 6
    for i in range(n_secondary):
        sc_x = center_x + (rng.uniform(-0.4, 0.4) * size_m)
        sc_y = center_y + (rng.uniform(-0.4, 0.4) * size_m)
        sc_r = rng.uniform(200.0, 500.0)
        sc_d = rng.uniform(40.0, 110.0)
        dist_s = np.sqrt((xx - sc_x) ** 2 + (yy - sc_y) ** 2)
        s_mask = dist_s < sc_r
        z[s_mask] -= sc_d * (1.0 - (dist_s[s_mask] / sc_r) ** 2)
        z += (sc_d * 0.35) * np.exp(-((dist_s - sc_r) / (sc_r * 0.25)) ** 2)

    # Multi-scale fractal roughness (harmonics at 1200m, 400m, 120m, 40m)
    scales = [1200.0, 400.0, 120.0, 40.0]
    amplitudes = [35.0, 12.0, 4.0, 1.2]
    for s_len, amp in zip(scales, amplitudes):
        phase_x = rng.uniform(0, 2 * np.pi)
        phase_y = rng.uniform(0, 2 * np.pi)
        angle = rng.uniform(0, np.pi)
        rot_x = xx * np.cos(angle) + yy * np.sin(angle)
        rot_y = -xx * np.sin(angle) + yy * np.cos(angle)
        z += amp * (np.sin(rot_x / s_len * 2 * np.pi + phase_x) *
                    np.cos(rot_y / s_len * 2 * np.pi + phase_y))

    return x_vec, y_vec, z


def get_elevation_profile(
    x0: float,
    y0: float,
    distances_m: np.ndarray,
    azimuths_deg: np.ndarray,
    geotiff_path: Optional[str] = None,
    site_elevation: float = 1500.0,
) -> np.ndarray:
    """Sample elevations Z(alpha, d) along ray paths.

    If a real GeoTIFF is found, samples from raster.
    Otherwise uses an analytical procedural South Pole terrain function.

    Args:
        x0, y0: Observer position in polar stereographic meters.
        distances_m: 1D array of radial distances from observer (shape [M]).
        azimuths_deg: 1D array of azimuths in degrees (shape [N], 0 to 360).
        geotiff_path: Optional path to LOLA GeoTIFF.
        site_elevation: Base elevation of the site.

    Returns:
        2D array of elevations Z with shape (len(azimuths_deg), len(distances_m)).
    """
    n_az = len(azimuths_deg)
    n_dist = len(distances_m)

    az_rad = np.radians(azimuths_deg)[:, np.newaxis]  # (N, 1)
    dist = distances_m[np.newaxis, :]  # (1, M)

    # Ray points coordinates
    ray_x = x0 + dist * np.sin(az_rad)  # (N, M)
    ray_y = y0 + dist * np.cos(az_rad)  # (N, M)

    # Check for real GeoTIFF
    if geotiff_path is None:
        geotiff_path = os.path.join(RAW_DATA_DIR, "LDEM_80S_20M.tif")

    if os.path.exists(geotiff_path):
        try:
            import rasterio
            with rasterio.open(geotiff_path) as src:
                flat_x = ray_x.ravel()
                flat_y = ray_y.ravel()
                sampled = np.array(list(src.sample(zip(flat_x, flat_y))))
                z = sampled.reshape((n_az, n_dist)).astype(np.float64)
                # Filter no-data
                valid_mask = (z > -10000) & (z < 15000)
                if np.mean(valid_mask) > 0.8:
                    return z
        except Exception:
            pass

    # Analytical deterministic procedural elevation
    # Uses deterministic wave synthesis based on coordinate hashing
    z = np.full((n_az, n_dist), site_elevation, dtype=np.float64)

    # Regional slope
    z += 0.002 * (ray_x - x0) - 0.0015 * (ray_y - y0)

    # Prominent ridge structures in typical south pole orientation
    # Ridge at 45 deg azimuth, ridge at 220 deg azimuth
    dist_norm = dist / 1000.0  # in km
    z += 220.0 * np.sin(az_rad * 2.0 + 0.5) * np.exp(-((dist_norm - 4.0) / 2.5) ** 2)
    z += 160.0 * np.cos(az_rad * 3.0 - 1.2) * np.exp(-((dist_norm - 8.0) / 4.0) ** 2)
    z += 90.0 * np.sin(az_rad * 5.0) * np.sin(dist_norm * 0.8)

    # Local rim peak near origin
    z += 60.0 * np.exp(-((dist_norm - 1.2) / 0.8) ** 2)

    return z
