"""
REST API route definitions for LunaScope 3.0.
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
from app.core.events import visibility_series
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
from app.core.nasa_data import readiness,provenance,manifest,DataUnavailable

@router.get('/data/status')
def data_status():return readiness()

@router.get('/data/provenance')
def data_provenance():return {**provenance(), 'manifest':manifest()}

@router.get('/data/validation')
def data_validation():
    from pathlib import Path
    import json
    path=Path(__file__).resolve().parents[3]/'data'/'validation'/'horizons_report.json'
    return json.loads(path.read_text()) if path.exists() else {'passed':False,'scope':'Independent Horizons comparison has not been installed or run'}



@router.get("/health")
def health_check() -> Dict[str, Any]:
    return {"status": "ok" if readiness()["ready"] else "data_required", "data": readiness(), "app": "LunaScope 3.0", "timestamp_utc": datetime.now(timezone.utc).isoformat()}

@router.get('/live')
def liveness():return {'status':'alive'}

@router.get('/ready')
def readiness_check(response:Response):
    state=readiness()
    if not state['ready']:response.status_code=503
    return state


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

        series=visibility_series(site_info['lat_deg'],site_info['lon_deg'],start_unix,end_unix,req.mast_height_m,req.antenna_margin_deg,req.sun_threshold)
        eph=series['ephemeris'];sample_hours=series['sample_hours'];f_sun=series['solar_fractions'];c_dte=series['dte_visibility']
        states=series['operational_states'];metrics=series['interval_metrics'].copy()

        # 4. Optional power simulation
        power_sim = None
        if req.power_config and req.power_config.enabled and metrics['coverage']=='complete':
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
                fixed_azimuth_deg=req.power_config.fixed_azimuth_deg,
                derating_factor=req.power_config.derating_factor,
                charge_efficiency=req.power_config.charge_efficiency,
                discharge_efficiency=req.power_config.discharge_efficiency,
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
            ,"events":series['events'],"sampling":series['sampling'],"horizon_profile":series['horizon_profile']
        }

    # Generate comparative insights
    insights = []
    if len(req.site_ids) >= 2 and all(r['interval_metrics']['coverage']=='complete' for r in sites_result.values()):
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
        "provenance": {**provenance(),"calculated_at_utc":datetime.now(timezone.utc).isoformat(),"time_range_utc":[req.start_time_iso,req.end_time_iso],
            "calculation_method":"Spherical terrain rays, SPICE LT+S topocentric directions, angular disk quadrature and adaptive time brackets", "power_model": "User-specified hardware assumptions applied to NASA-data illumination"}
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
    except DataUnavailable:
        raise
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
    except DataUnavailable:
        raise
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
    except DataUnavailable:
        raise
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
    except DataUnavailable:
        raise
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
