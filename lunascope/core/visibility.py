"""LunaScope Visibility Engine: Fractional Solar Disk Penumbra & DTE Comms Line-of-Sight.

Mathematical Formulation:
1. Solar disk penumbra:
   Solar angular radius r_sun = 0.2665 deg.
   Clearance Delta theta = theta_sun - H(alpha_sun)
   When -r_sun < Delta theta < r_sun:
       u = Delta theta / r_sun
       f(t) = (1 / pi) * (arccos(-u) + u * sqrt(1 - u^2))
   When Delta theta <= -r_sun: f(t) = 0.0
   When Delta theta >= +r_sun: f(t) = 1.0

2. Direct-to-Earth (DTE) comms link:
   Earth angular radius r_earth = 0.950 deg.
   Clearance Delta theta_earth = theta_earth - H(alpha_earth)
   DTE active if Delta theta_earth >= dte_margin_deg (default 1.0 deg).
"""

from typing import Dict, Tuple, Union
import numpy as np

from core.ephemeris import SOLAR_ANGULAR_RADIUS_DEG, EARTH_ANGULAR_RADIUS_DEG
from core.raycaster import interpolate_horizon


def calculate_fractional_solar_illumination(
    sun_elevation_deg: Union[float, np.ndarray],
    horizon_elevation_deg: Union[float, np.ndarray],
    r_sun_deg: float = SOLAR_ANGULAR_RADIUS_DEG,
) -> Union[float, np.ndarray]:
    """Calculate fractional solar disk illumination f(t) in [0.0, 1.0].

    Accounts for the finite solar angular disk radius (penumbra).

    Args:
        sun_elevation_deg: Solar center elevation in degrees.
        horizon_elevation_deg: Local terrain horizon mask elevation in degrees.
        r_sun_deg: Solar angular radius in degrees (default 0.2665 deg).

    Returns:
        Fractional illumination in range [0.0, 1.0].
    """
    elev = np.asarray(sun_elevation_deg, dtype=np.float64)
    horiz = np.asarray(horizon_elevation_deg, dtype=np.float64)

    delta_theta = elev - horiz

    # Normalized clearance u in [-1, 1]
    u = delta_theta / r_sun_deg

    is_scalar = np.isscalar(sun_elevation_deg) and np.isscalar(horizon_elevation_deg)

    # Vectorized piecewise evaluation
    f = np.zeros_like(u, dtype=np.float64)

    # Full sun (u >= 1.0)
    full_mask = u >= 1.0
    f[full_mask] = 1.0

    # Penumbra (-1.0 < u < 1.0)
    penumbra_mask = (u > -1.0) & (u < 1.0)
    if np.any(penumbra_mask):
        u_pen = u[penumbra_mask]
        # Circular segment area formula
        f[penumbra_mask] = (1.0 / np.pi) * (np.arccos(-u_pen) + u_pen * np.sqrt(1.0 - u_pen**2))

    # Umbra (u <= -1.0) remains 0.0

    # Ensure strict numerical bounds [0.0, 1.0]
    f = np.clip(f, 0.0, 1.0)

    if is_scalar:
        return float(f)
    return f


def calculate_dte_status(
    earth_elevation_deg: Union[float, np.ndarray],
    horizon_elevation_deg: Union[float, np.ndarray],
    margin_threshold_deg: float = 1.0,
    r_earth_deg: float = EARTH_ANGULAR_RADIUS_DEG,
) -> Tuple[Union[bool, np.ndarray], Union[float, np.ndarray]]:
    """Determine Direct-to-Earth (DTE) RF communication line-of-sight status.

    Args:
        earth_elevation_deg: Earth center elevation in degrees.
        horizon_elevation_deg: Local terrain horizon elevation in degrees.
        margin_threshold_deg: Minimum multipath/RF clearance angle in degrees (default 1.0 deg).
        r_earth_deg: Earth angular radius in degrees (default 0.950 deg).

    Returns:
        (is_dte_connected, clearance_margin_deg)
    """
    elev = np.asarray(earth_elevation_deg, dtype=np.float64)
    horiz = np.asarray(horizon_elevation_deg, dtype=np.float64)

    # Top edge of Earth disk or center clearance
    clearance = elev - horiz

    # Link requires clearance >= margin threshold
    connected = clearance >= margin_threshold_deg

    if np.isscalar(earth_elevation_deg) and np.isscalar(horizon_elevation_deg):
        return bool(connected), float(clearance)
    return connected, clearance


def evaluate_site_timeline(
    sun_azimuth_deg: np.ndarray,
    sun_elevation_deg: np.ndarray,
    earth_azimuth_deg: np.ndarray,
    earth_elevation_deg: np.ndarray,
    horizon_azimuths_deg: np.ndarray,
    horizon_elevations_deg: np.ndarray,
    dte_margin_deg: float = 1.0,
) -> Dict[str, np.ndarray]:
    """Evaluate synchronized illumination and DTE timeline over time series.

    Returns:
        Dict with keys:
            - 'solar_fraction': array of f(t) in [0, 1]
            - 'sun_horizon_deg': horizon elevation at Sun azimuths
            - 'earth_clearance_deg': Earth clearance above horizon
            - 'dte_connected': boolean array of RF link status
    """
    # Sample horizon at Sun positions
    sun_horiz = interpolate_horizon(sun_azimuth_deg, horizon_azimuths_deg, horizon_elevations_deg)
    solar_fraction = calculate_fractional_solar_illumination(sun_elevation_deg, sun_horiz)

    # Sample horizon at Earth positions
    earth_horiz = interpolate_horizon(earth_azimuth_deg, horizon_azimuths_deg, horizon_elevations_deg)
    dte_connected, earth_clearance = calculate_dte_status(
        earth_elevation_deg, earth_horiz, margin_threshold_deg=dte_margin_deg
    )

    return {
        "solar_fraction": solar_fraction,
        "sun_horizon_deg": sun_horiz,
        "earth_clearance_deg": earth_clearance,
        "dte_connected": dte_connected,
    }
