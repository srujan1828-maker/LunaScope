"""
Immutable Scenario Store and JSON/CSV Exporter.
Preserves complete reproducibility, parameters, and calculation outputs with full provenance tags.
"""

import io
from copy import deepcopy
import csv
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List

_SCENARIO_DB: Dict[str, Dict[str, Any]] = {}


def save_scenario(scenario_data: Dict[str, Any]) -> str:
    """Save an immutable scenario and return its unique ID."""
    scenario_id = str(uuid.uuid4())
    scenario_record = {
        "id": scenario_id,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "schema_version": "2.0.0",
        "engine": "LunaScope-NASA-Data-Engine-v3.0",
        "data_mode": "nasa-official",
        "limitations": "NASA LOLA 80 m grid and JPL SPICE ephemerides; sampled derived visibility; terrain safety and DSN scheduling remain uncertified. Scenarios are held in memory until server restart.",
        **scenario_data
    }
    _SCENARIO_DB[scenario_id] = deepcopy(scenario_record)
    return scenario_id


def get_scenario(scenario_id: str) -> Dict[str, Any] | None:
    """Retrieve saved scenario by ID."""
    return deepcopy(_SCENARIO_DB.get(scenario_id))


def export_scenario_to_json(scenario_id: str) -> str:
    """Export scenario record as formatted JSON string."""
    rec = get_scenario(scenario_id)
    if not rec:
        raise ValueError(f"Scenario {scenario_id} not found.")
    return json.dumps(rec, indent=2)


def export_scenario_to_csv(scenario_id: str) -> str:
    """
    Export scenario time series data as CSV string.
    Includes timestamps, azimuths, elevations, solar fraction, DTE comms, and operational state.
    """
    rec = get_scenario(scenario_id)
    if not rec:
        raise ValueError(f"Scenario {scenario_id} not found.")
        
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write metadata headers as comments
    writer.writerow(["# LunaScope Scenario Export"])
    writer.writerow(["# Scenario ID", rec.get("id")])
    writer.writerow(["# Created At UTC", rec.get("created_at_utc")])
    writer.writerow(["# Selected Sites", ", ".join(rec.get("site_ids", []))])
    writer.writerow([])
    
    # Header row
    headers = [
        "timestamp_unix",
        "timestamp_iso",
        "site_id",
        "sun_azimuth_deg",
        "sun_elevation_deg",
        "earth_azimuth_deg",
        "earth_elevation_deg",
        "solar_fraction",
        "dte_visibility",
        "operational_state"
    ]
    writer.writerow(headers)
    
    sites_eval = rec.get("sites_evaluation", {})
    for sid, sdata in sites_eval.items():
        ts_list = sdata.get("timestamps", [])
        eph = sdata.get("ephemeris", {})
        sun_az = eph.get("sun_azimuth", [])
        sun_el = eph.get("sun_elevation", [])
        earth_az = eph.get("earth_azimuth", [])
        earth_el = eph.get("earth_elevation", [])
        f_sun = sdata.get("solar_fractions", [])
        c_dte = sdata.get("dte_visibility", [])
        states = sdata.get("operational_states", [])
        
        for i in range(len(ts_list)):
            ts = ts_list[i]
            iso = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
            writer.writerow([
                ts,
                iso,
                sid,
                sun_az[i] if i < len(sun_az) else "",
                sun_el[i] if i < len(sun_el) else "",
                earth_az[i] if i < len(earth_az) else "",
                earth_el[i] if i < len(earth_el) else "",
                f_sun[i] if i < len(f_sun) else "",
                c_dte[i] if i < len(c_dte) else "",
                states[i] if i < len(states) else ""
            ])
            
    return output.getvalue()
