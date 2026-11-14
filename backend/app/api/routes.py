"""
REST API route definitions for LunaScope 2.0.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import PlainTextResponse

from app.api.schemas import (
    EvaluateScenarioRequest,
    SearchWindowsRequest,
    ContingencyRequest,
    SaveScenarioRequest,
    DispersionRequest,
    MastSensitivityRequest
)
from app.data.sites_catalog import get_sites_catalog, get_site_by_id
from app.core.horizon import compute_horizon_360
from app.core.ephemeris import compute_ephemeris_track, topocentric_az_el, get_subsolar_coordinates, get_subearth_coordinates, SOLAR_RADIUS_DEG
from app.core.visibility import (
    fractional_solar_visibility,
    evaluate_dte_visibility,
    classify_operational_states,
    compute_interval_metrics
)
from app.core.contingency import evaluate_contingency
from app.core.window_finder import search_mission_windows
from app.core.power_model import simulate_power_and_battery
from app.core.landing_dispersion import evaluate_landing_dispersion
from app.core.mast_sensitivity import evaluate_mast_sensitivity
from app.core.scenario_store import (
    save_scenario,
    get_scenario,
    export_scenario_to_json,
    export_scenario_to_csv
)

router = APIRouter()


@router.get("/health")
def health_check() -> Dict[str, Any]:
    return {"status": "ok", "app": "LunaScope 2.0", "timestamp_utc": datetime.now(timezone.utc).isoformat()}


@router.get("/sites")
def list_sites() -> List[Dict[str, Any]]:
    return get_sites_catalog()


@router.post("/scenarios/evaluate")
def evaluate_scenario(req: EvaluateScenarioRequest) -> Dict[str, Any]:
    try:
        start_dt = datetime.fromisoformat(req.start_time_iso.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(req.end_time_iso.replace("Z", "+00:00"))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")

    if end_dt <= start_dt:
        raise HTTPException(status_code=400, detail="end_time_iso must be strictly after start_time_iso")

    start_unix = start_dt.timestamp()
    end_unix = end_dt.timestamp()
    step_seconds = 3600.0  # 1 hour steps
    step_hours = 1.0

    sites_result = {}
    sample_hours = None

    for sid in req.site_ids:
        site_info = get_site_by_id(sid)
        if not site_info:
            raise HTTPException(status_code=404, detail=f"Site '{sid}' not found.")

        # 1. Horizon mask
        horizon = compute_horizon_360(
            lat_deg=site_info["lat_deg"],
            lon_deg=site_info["lon_deg"],
            base_elevation_m=site_info["elevation_m"],
            mast_height_m=req.mast_height_m
        )

        # 2. Ephemeris
        eph = compute_ephemeris_track(
            site_lat_deg=site_info["lat_deg"],
            site_lon_deg=site_info["lon_deg"],
            start_unix=start_unix,
            end_unix=end_unix,
            step_seconds=step_seconds
        )

        sample_hours = [max(0.0, min(step_seconds, end_unix-t)) / 3600 for t in eph["timestamps"]]

        # 3. Visibility & States
        f_sun = fractional_solar_visibility(eph["sun_azimuth"], eph["sun_elevation"], horizon)
        c_dte = evaluate_dte_visibility(
            eph["earth_azimuth"],
            eph["earth_elevation"],
            horizon,
            margin_deg=req.antenna_margin_deg
        )
        states = classify_operational_states(f_sun, c_dte, sun_threshold=req.sun_threshold)
        metrics = compute_interval_metrics(f_sun, c_dte, step_hours=step_hours, sun_threshold=req.sun_threshold, sample_hours=sample_hours)

        # 4. Optional power simulation
        power_sim = None
        if req.power_config and req.power_config.enabled:
            power_sim = simulate_power_and_battery(
                timestamps=eph["timestamps"],
                solar_fractions=f_sun,
                sun_elevations=eph["sun_elevation"],
                sun_azimuths=eph["sun_azimuth"],
                panel_area_m2=req.power_config.panel_area_m2,
                panel_efficiency=req.power_config.panel_efficiency,
                panel_orientation=req.power_config.panel_orientation,
                spacecraft_load_w=req.power_config.spacecraft_load_w,
                battery_capacity_wh=req.power_config.battery_capacity_wh,
                initial_soc_pct=req.power_config.initial_soc_pct,
                reserve_margin_pct=req.power_config.reserve_margin_pct,
                solar_flux_w_m2=eph.get("solar_flux_w_m2"),
                step_hours=step_hours,
                sample_hours=sample_hours
            )

        sites_result[sid] = {
            "site_info": site_info,
            "sample_hours": sample_hours,
            "horizon_360": horizon,
            "timestamps": eph["timestamps"],
            "ephemeris": eph,
            "solar_fractions": f_sun,
            "dte_visibility": c_dte,
            "operational_states": states,
            "interval_metrics": metrics,
            "power_simulation": power_sim
        }

    # Generate comparative insights
    insights = []
    if len(req.site_ids) >= 2:
        s1_id = req.site_ids[0]
        s2_id = req.site_ids[1]
        m1 = sites_result[s1_id]["interval_metrics"]
        m2 = sites_result[s2_id]["interval_metrics"]
        name1 = sites_result[s1_id]["site_info"]["name"]
        name2 = sites_result[s2_id]["site_info"]["name"]

        sun_diff = m1["sun_availability_pct"] - m2["sun_availability_pct"]
        if abs(sun_diff) > 2.0:
            winner = name1 if sun_diff > 0 else name2
            insights.append(f"{winner} delivers {abs(sun_diff):.1f}% higher solar availability during this mission window.")

        earth_diff = m1["earth_availability_pct"] - m2["earth_availability_pct"]
        if abs(earth_diff) > 2.0:
            winner = name1 if earth_diff > 0 else name2
            insights.append(f"{winner} provides {abs(earth_diff):.1f}% greater direct-to-Earth line-of-sight coverage.")

        shadow_diff = m1["longest_shadow_gap_hours"] - m2["longest_shadow_gap_hours"]
        if abs(shadow_diff) >= 1.0:
            safer = name2 if shadow_diff > 0 else name1
            gap = abs(shadow_diff)
            insights.append(f"{safer} experiences a {gap:.1f}h shorter continuous shadow gap, reducing battery drain risk.")

    return {
        "inputs": req.model_dump(),
        "evaluated_sites": sites_result,
        "comparative_insights": insights,
        "provenance": {
            "site_catalog": "Assumed: illustrative hard-coded catalog; not extracted from Wueller/Zenodo",
            "topography": "Derived from procedural demonstration terrain; no LOLA raster integrated",
            "sky_geometry": "Approximate analytical model; not validated against SPICE/Horizons",
            "visibility_model": "Derived (Penumbral solar disk grazing & geometric DTE)",
            "power_model": "Assumed (User panel/battery hardware parameters)"
        }
    }


@router.post("/windows/search")
def search_windows(req: SearchWindowsRequest) -> Dict[str, Any]:
    try:
        res = search_mission_windows(
            site_ids=req.site_ids,
            search_start_iso=req.search_start_iso,
            search_end_iso=req.search_end_iso,
            mission_duration_days=req.mission_duration_days,
            stride_hours=req.stride_hours,
            min_sun_pct=req.min_sun_pct,
            max_shadow_gap_hours=req.max_shadow_gap_hours,
            min_earth_pct=req.min_earth_pct,
            max_earth_outage_hours=req.max_earth_outage_hours,
            min_joint_pct=req.min_joint_pct,
            priority=req.priority,
            mast_height_m=req.mast_height_m
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/contingency/evaluate")
def run_contingency(req: ContingencyRequest) -> Dict[str, Any]:
    try:
        res = evaluate_contingency(
            primary_site_id=req.primary_site_id,
            year=req.year,
            min_sun_days=req.min_sun_days,
            min_joint_days=req.min_joint_days
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/scenarios")
def save_scenario_endpoint(req: SaveScenarioRequest) -> Dict[str, Any]:
    scenario_id = save_scenario(req.model_dump())
    return {"scenario_id": scenario_id, "status": "saved"}


@router.get("/scenarios/{scenario_id}")
def get_scenario_endpoint(scenario_id: str) -> Dict[str, Any]:
    rec = get_scenario(scenario_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Scenario not found.")
    return rec


@router.get("/export/{scenario_id}/json")
def export_json_endpoint(scenario_id: str):
    try:
        json_str = export_scenario_to_json(scenario_id)
        return Response(
            content=json_str,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=lunascope_scenario_{scenario_id}.json"}
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/simulation/dispersion")
def run_dispersion_analysis(req: DispersionRequest) -> Dict[str, Any]:
    try:
        start_unix = datetime.fromisoformat(req.start_time_iso.replace("Z", "+00:00")).timestamp()
        end_unix = datetime.fromisoformat(req.end_time_iso.replace("Z", "+00:00")).timestamp()
        return evaluate_landing_dispersion(
            site_id=req.site_id,
            start_unix=start_unix,
            end_unix=end_unix,
            semi_major_m=req.semi_major_m,
            semi_minor_m=req.semi_minor_m,
            num_samples=req.num_samples,
            mast_height_m=req.mast_height_m
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/simulation/mast-sensitivity")
def run_mast_sensitivity(req: MastSensitivityRequest) -> Dict[str, Any]:
    try:
        start_unix = datetime.fromisoformat(req.start_time_iso.replace("Z", "+00:00")).timestamp()
        end_unix = datetime.fromisoformat(req.end_time_iso.replace("Z", "+00:00")).timestamp()
        return evaluate_mast_sensitivity(
            site_id=req.site_id,
            start_unix=start_unix,
            end_unix=end_unix,
            mast_heights=req.mast_heights
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/export/{scenario_id}/csv")
def export_csv_endpoint(scenario_id: str):
    try:
        csv_str = export_scenario_to_csv(scenario_id)
        return PlainTextResponse(
            content=csv_str,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=lunascope_scenario_{scenario_id}.csv"}
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
