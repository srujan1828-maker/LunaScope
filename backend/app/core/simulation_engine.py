"""
NASA-data Real-Time Lunar Simulation Engine.
Manages live simulation sessions, computes high-frequency topocentric frames,
instantaneous solar flux, battery dynamics, predictive event horizons, and geometric Earth visibility. DSN scheduling remains unknown.
"""

from threading import RLock
from functools import wraps
import math
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

from app.core.coordinates import R_MOON
from app.core.horizon import compute_horizon_360
from app.core.ephemeris import (
    datetime_to_jd,

    get_subsolar_coordinates,
    get_subearth_coordinates,
    topocentric_az_el,
    SOLAR_RADIUS_DEG,
    EARTH_RADIUS_DEG,
    AU_METERS,
    MEAN_LUNAR_DIST_METERS
)
from app.core.visibility import fractional_solar_visibility, evaluate_dte_visibility
from app.core.ground_stations import evaluate_dsn_coverage
from app.data.sites_catalog import get_site_by_id
from app.core.spice_geometry import body_vectors
from app.core.nasa_data import provenance

SOLAR_CONSTANT_W_M2: float = 1361.0


def synchronized(method):
    @wraps(method)
    def wrapped(self,*args,**kwargs):
        with self.lock:return method(self,*args,**kwargs)
    return wrapped

class RealtimeSimulationSession:
    """
    Stateful real-time simulation session for continuous lunar surface operations.
    """

    def __init__(
        self,
        site_ids: List[str],
        start_unix: float,
        mast_height_m: float = 2.0,
        antenna_margin_deg: float = 0.0,
        speed_multiplier: float = 60.0,  # 1 real second = 60 simulation seconds (1 min/sec)
        spacecraft_load_w: float = 120.0,
        panel_area_m2: float = 3.5,
        battery_capacity_wh: float = 2400.0,
        initial_soc_pct: float = 100.0
    ):
        self.lock=RLock()
        self.site_ids = site_ids
        self.current_unix = start_unix
        self.mast_height_m = mast_height_m
        self.antenna_margin_deg = antenna_margin_deg
        self.speed_multiplier = speed_multiplier
        self.spacecraft_load_w = spacecraft_load_w
        self.panel_area_m2 = panel_area_m2
        self.battery_capacity_wh = battery_capacity_wh
        self.is_running = False
        self.last_tick_time = time.time()

        # Battery charge state per site
        self.battery_energy_wh: Dict[str, float] = {
            sid: battery_capacity_wh * (initial_soc_pct / 100.0) for sid in site_ids
        }

        # Cache horizons per site
        self.site_horizons: Dict[str, List[float]] = {}
        self.site_info_cache: Dict[str, Any] = {}
        for sid in site_ids:
            sinfo = get_site_by_id(sid)
            if sinfo:
                self.site_info_cache[sid] = sinfo
                self.site_horizons[sid] = compute_horizon_360(
                    lat_deg=sinfo["lat_deg"],
                    lon_deg=sinfo["lon_deg"],
                    base_elevation_m=sinfo["elevation_m"],
                    mast_height_m=mast_height_m
                )

    @synchronized
    def update_mast_height(self, new_mast_m: float):
        """Dynamically adjust mast height and recompute horizons."""
        self.mast_height_m = new_mast_m
        for sid in self.site_ids:
            sinfo = self.site_info_cache.get(sid)
            if sinfo:
                self.site_horizons[sid] = compute_horizon_360(
                    lat_deg=sinfo["lat_deg"],
                    lon_deg=sinfo["lon_deg"],
                    base_elevation_m=sinfo["elevation_m"],
                    mast_height_m=new_mast_m
                )

    @synchronized
    def advance_time(self, delta_sim_seconds: float) -> Dict[str, Any]:
        """Advance simulation time by delta_sim_seconds and return rich telemetry frame."""
        if not math.isfinite(delta_sim_seconds) or not 0 <= delta_sim_seconds <= 86400:
            raise ValueError("Step must be between 0 and 86400 seconds")
        self.current_unix += delta_sim_seconds
        return self.compute_frame(delta_sim_seconds)

    @synchronized
    def compute_frame(self, dt_seconds: float = 0.0) -> Dict[str, Any]:
        """
        Compute instantaneous physics, geometry, power, DSN status, and event forecasts.
        """
        t = self.current_unix
        dt_hours = dt_seconds / 3600.0
        dt_obj = datetime.fromtimestamp(t, tz=timezone.utc)
        jd = datetime_to_jd(dt_obj)

        # 1. Official NASA/JPL SPICE vectors in the LOLA DE421 lunar frame
        import numpy as np
        sun_vector, earth_vector = body_vectors((float(t),))
        sun_dist_m = float(np.linalg.norm(sun_vector[0]))
        earth_dist_m = float(np.linalg.norm(earth_vector[0]))
        r_au = sun_dist_m / AU_METERS
        instant_flux = 1361.0 / (r_au**2)

        sub_sun_lat, sub_sun_lon = get_subsolar_coordinates(t)
        sub_earth_lat, sub_earth_lon = get_subearth_coordinates(t)

        iso_time = dt_obj.isoformat()
        site_telemetry = {}

        for sid in self.site_ids:
            sinfo = self.site_info_cache.get(sid)
            horizon = self.site_horizons.get(sid)
            if not sinfo or not horizon:
                continue

            # Topocentric Sun
            sun_az, sun_el = topocentric_az_el(
                sinfo["lat_deg"], sinfo["lon_deg"], sub_sun_lat, sub_sun_lon,
                body_distance_m=sun_dist_m, site_elevation_m=sinfo["elevation_m"]
            )
            sun_az_idx = int(round(sun_az)) % 360
            import numpy as np
            h_sun = float(np.interp(sun_az % 360, np.arange(361), horizon + [horizon[0]]))

            # Fractional solar disk exposure
            f_sun=fractional_solar_visibility([sun_az],[sun_el],horizon,angular_radius_deg=math.degrees(math.asin(695700000/sun_dist_m)))[0]
            if f_sun is None:raise ValueError('Terrain coverage unknown for streamed simulation')

            # Topocentric Earth
            earth_az, earth_el = topocentric_az_el(
                sinfo["lat_deg"], sinfo["lon_deg"], sub_earth_lat, sub_earth_lon,
                body_distance_m=earth_dist_m, site_elevation_m=sinfo["elevation_m"]
            )
            earth_az_idx = int(round(earth_az)) % 360
            h_earth = float(np.interp(earth_az % 360, np.arange(361), horizon + [horizon[0]]))
            dte_margin_actual = earth_el - h_earth
            dte_visible = int(dte_margin_actual > self.antenna_margin_deg)

            # NASA DSN Ground Network Link
            dsn_status = evaluate_dsn_coverage(
                unix_time=t,
                subearth_lat_deg=sub_earth_lat,
                subearth_lon_deg=sub_earth_lon,
                lander_dte_los=bool(dte_visible)
            )

            # Operational Regime (State 1..4)
            has_sun = (f_sun >= 0.10)
            has_earth = (dte_visible == 1)
            if has_sun and has_earth:
                state = 1
                state_name = "Nominal Science"
                state_badge = "NOMINAL"
            elif has_sun and not has_earth:
                state = 2
                state_name = "Autonomous Day"
                state_badge = "COMMS OCCULTED"
            elif not has_sun and has_earth:
                state = 3
                state_name = "Tethered Eclipse"
                state_badge = "BATTERY DRAIN"
            else:
                state = 4
                state_name = "Total Blackout"
                state_badge = "CRITICAL RISK"

            # Instantaneous Power & Battery Dynamics
            cos_inc = max(0.0, math.cos(math.radians(max(0.0, sun_el)))) if f_sun > 0 else 0.0
            if getattr(self,"panel_orientation","tracking") == "fixed_vertical":
                cos_inc *= max(0,math.cos(math.radians(sun_az-getattr(self,'fixed_azimuth_deg',0))))
            p_gen = instant_flux * self.panel_area_m2 * getattr(self,"panel_efficiency",0.28) * f_sun * cos_inc * getattr(self,'derating_factor',.85)
            p_net = p_gen - self.spacecraft_load_w

            curr_batt = self.battery_energy_wh[sid]
            if p_net >= 0:
                curr_batt = min(self.battery_capacity_wh, curr_batt + (p_net * dt_hours * getattr(self,'charge_efficiency',.92)))
                unmet_w = 0.0
            else:
                deficit = abs(p_net) * dt_hours / getattr(self,'discharge_efficiency',.95)
                if curr_batt >= deficit:
                    curr_batt -= deficit
                    unmet_w = 0.0
                else:
                    unmet_w = (deficit - curr_batt) * getattr(self,'discharge_efficiency',.95) / max(1e-4, dt_hours)
                    curr_batt = 0.0

            self.battery_energy_wh[sid] = curr_batt
            soc_pct = (curr_batt / self.battery_capacity_wh) * 100.0

            # Event Horizon Forecast
            upcoming_events = self._detect_upcoming_events(sinfo, horizon, t)

            site_telemetry[sid] = {
                "site_id": sid,
                "name": sinfo["name"],
                "sun": {
                    "azimuth_deg": round(sun_az, 2),
                    "elevation_deg": round(sun_el, 2),
                    "horizon_elevation_deg": round(h_sun, 2),
                    "visible_fraction": round(f_sun, 4),
                    "clearance_deg": round(sun_el - h_sun, 2),
                    "flux_w_m2": round(instant_flux, 1)
                },
                "earth": {
                    "azimuth_deg": round(earth_az, 2),
                    "elevation_deg": round(earth_el, 2),
                    "horizon_elevation_deg": round(h_earth, 2),
                    "visible": bool(dte_visible),
                    "clearance_margin_deg": round(dte_margin_actual, 2)
                },
                "dsn_network": dsn_status,
                "regime": {
                    "state": state,
                    "name": state_name,
                    "badge": state_badge
                },
                "power": {
                    "generated_w": round(p_gen, 1),
                    "net_w": round(p_net, 1),
                    "battery_energy_wh": round(curr_batt, 1),
                    "battery_soc_pct": round(soc_pct, 1),
                    "unmet_load_w": round(unmet_w, 1),
                    "reserve_breached": bool(soc_pct < getattr(self,"reserve_margin_pct",20.0))
                },
                "upcoming_events": upcoming_events
            }

        return {
            "type": "telemetry_frame",
            "provenance": provenance(),
            "timestamp_unix": t,
            "timestamp_iso": iso_time,
            "speed_multiplier": self.speed_multiplier,
            "mast_height_m": self.mast_height_m,
            "subsolar_point": {
                "latitude_deg": round(sub_sun_lat, 3),
                "longitude_deg": round(sub_sun_lon, 3),
                "distance_au": round(r_au, 5)
            },
            "subearth_point": {
                "latitude_deg": round(sub_earth_lat, 3),
                "longitude_deg": round(sub_earth_lon, 3)
            },
            "sites": site_telemetry
        }

    def _detect_upcoming_events(self, sinfo, horizon, current_t):
        from app.core.events import visibility_series
        bucket=math.floor(current_t/1800)*1800
        series=visibility_series(sinfo['lat_deg'],sinfo['lon_deg'],bucket,bucket+48*3600,self.mast_height_m,self.antenna_margin_deg)
        for event in series['events']:
            if event['timestamp_unix']<=current_t:continue
            before=event['from_state'] in (1,2);after=event['to_state'] in (1,2)
            if before!=after:
                hours=(event['timestamp_unix']-current_t)/3600
                return [{'event_type':'sunrise_egress' if after else 'shadow_ingress','hours_away':round(hours,2),
                    'description':('Sun threshold rise' if after else 'Sun threshold fall')+f" in ~{hours:.2f}h (30-second event bracket)",
                    'bracket_seconds':event['bracket_seconds']}]
        return []
