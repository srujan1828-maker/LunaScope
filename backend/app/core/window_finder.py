"""
Signature Feature: Find Better Mission Windows.
Searches across a candidate date interval for optimal surface operation windows,
evaluating hard constraints and ranking non-dominated operational trade-offs.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any
import numpy as np

from app.data.sites_catalog import get_site_by_id
from app.core.horizon import compute_horizon_360
from app.core.ephemeris import compute_ephemeris_track
from app.core.events import visibility_series,window_metrics
from app.core.nasa_data import provenance
from app.core.visibility import (
    fractional_solar_visibility,
    evaluate_dte_visibility,
    compute_interval_metrics
)


def search_mission_windows(
    site_ids: List[str],
    search_start_iso: str,
    search_end_iso: str,
    mission_duration_days: float = 7.0,
    stride_hours: float = 12.0,
    min_sun_pct: float = 60.0,
    max_shadow_gap_hours: float = 18.0,
    min_earth_pct: float = 50.0,
    max_earth_outage_hours: float = 36.0,
    min_joint_pct: float = 40.0,
    priority: str = "balanced",
    mast_height_m: float = 2.0
) -> Dict[str, Any]:
    """
    Search candidate surface operation start dates for one or more landing sites.
    """
    start_dt = datetime.fromisoformat(search_start_iso.replace("Z", "+00:00"))
    end_dt = datetime.fromisoformat(search_end_iso.replace("Z", "+00:00"))
    
    start_unix = start_dt.timestamp()
    end_unix = end_dt.timestamp()
    
    duration_seconds = mission_duration_days * 86400.0
    step_seconds = 600.0
    step_hours = 1.0
    
    # Precompute horizons and continuous ephemeris for each site
    site_data = {}
    total_eval_end_unix = end_unix + duration_seconds
    
    for sid in site_ids:
        site_info = get_site_by_id(sid)
        if not site_info:
            raise ValueError(f"Unknown site: {sid}")
        horizon = compute_horizon_360(
            lat_deg=site_info["lat_deg"],
            lon_deg=site_info["lon_deg"],
            base_elevation_m=site_info["elevation_m"],
            mast_height_m=mast_height_m
        )
        series=visibility_series(site_info['lat_deg'],site_info['lon_deg'],start_unix,total_eval_end_unix,mast_height_m)
        
        site_data[sid] = {
            "info": site_info,
            "horizon": horizon,
            "series":series
        }
        
    candidate_windows = []
    current_start_unix = start_unix
    
    # Window index in the precomputed array
    while current_start_unix <= end_unix:
        win_end_unix = current_start_unix + duration_seconds
        
        win_start_iso = datetime.fromtimestamp(current_start_unix, tz=timezone.utc).isoformat()
        win_end_iso = datetime.fromtimestamp(win_end_unix, tz=timezone.utc).isoformat()
        
        site_metrics = {}
        all_sites_passed = True
        
        for sid, sdata in site_data.items():
            m=window_metrics(sdata['series'],current_start_unix,win_end_unix)
            if m['coverage']!='complete':
                all_sites_passed=False
                site_metrics[sid]={'site_name':sdata['info']['name'],'metrics':m,'passed':False,'status':'Unknown','violations':['Incomplete terrain or time coverage; cannot pass']}
                continue
            
            # Constraint check
            violations = []
            if m["sun_availability_pct"] < min_sun_pct:
                violations.append(f"Sun {m['sun_availability_pct']}% < {min_sun_pct}%")
            if m["longest_shadow_gap_hours"] > max_shadow_gap_hours:
                violations.append(f"Shadow gap {m['longest_shadow_gap_hours']}h > {max_shadow_gap_hours}h")
            if m["earth_availability_pct"] < min_earth_pct:
                violations.append(f"Earth {m['earth_availability_pct']}% < {min_earth_pct}%")
            if m["longest_earth_outage_hours"] > max_earth_outage_hours:
                violations.append(f"Earth outage {m['longest_earth_outage_hours']}h > {max_earth_outage_hours}h")
            if m["joint_availability_pct"] < min_joint_pct:
                violations.append(f"Joint {m['joint_availability_pct']}% < {min_joint_pct}%")
                
            site_passed = len(violations) == 0
            if not site_passed:
                all_sites_passed = False
                
            site_metrics[sid] = {
                "site_name": sdata["info"]["name"],
                "metrics": m,
                "passed": site_passed,
                "status":'Pass' if site_passed else 'Fail',
                "violations": violations
            }
            
        # Composite score according to priority
        # Normalize: sun %, earth %, joint % contribute positively; shadow & outage negatively
        def average(key,fallback):return float(np.mean([sm['metrics'].get(key) if sm['metrics'].get(key) is not None else fallback for sm in site_metrics.values()])) if site_metrics else fallback
        avg_sun=average('sun_availability_pct',0);avg_earth=average('earth_availability_pct',0);avg_joint=average('joint_availability_pct',0)
        avg_shadow=average('longest_shadow_gap_hours',duration_seconds/3600);avg_outage=average('longest_earth_outage_hours',duration_seconds/3600)
        
        if priority == "favour_sun":
            score = avg_sun * 0.6 + avg_joint * 0.3 - (avg_shadow * 1.5)
        elif priority == "favour_earth":
            score = avg_earth * 0.6 + avg_joint * 0.3 - (avg_outage * 1.5)
        elif priority == "minimise_interruptions":
            score = avg_joint * 0.5 - (avg_shadow * 2.0) - (avg_outage * 1.0)
        else:  # balanced
            score = (avg_sun * 0.35 + avg_earth * 0.35 + avg_joint * 0.30) - (avg_shadow * 0.8 + avg_outage * 0.5)
            
        candidate_windows.append({
            "start_time_iso": win_start_iso,
            "end_time_iso": win_end_iso,
            "start_unix": current_start_unix,
            "duration_days": mission_duration_days,
            "all_sites_passed": all_sites_passed,
            "composite_score": round(float(score), 2),
            "site_evaluations": site_metrics
        })
        
        current_start_unix += stride_hours*3600

    # Sort passing windows first, then by composite score descending
    passing_windows = [w for w in candidate_windows if w["all_sites_passed"]]
    passing_windows.sort(key=lambda x: x["composite_score"], reverse=True)
    
    failing_windows = [w for w in candidate_windows if not w["all_sites_passed"]]
    failing_windows.sort(key=lambda x: x["composite_score"], reverse=True)
    
    # Generate comparative narrative insight
    best_window = passing_windows[0] if passing_windows else (failing_windows[0] if failing_windows else None)
    explanation = ""
    if best_window:
        if best_window["all_sites_passed"]:
            explanation = (
                f"Top Recommended Window begins {best_window['start_time_iso'][:16]} UTC. "
                f"Satisfies all constraints with high joint Sun+Earth coverage."
            )
        else:
            explanation = (
                f"No candidate start date fully met all strict criteria. "
                f"Closest option begins {best_window['start_time_iso'][:16]} UTC."
            )
            
    return {
        "search_parameters": {
            "site_ids": site_ids,
            "search_start": search_start_iso,
            "search_end": search_end_iso,
            "duration_days": mission_duration_days,
            "priority": priority,
            "constraints": {
                "min_sun_pct": min_sun_pct,
                "max_shadow_gap_hours": max_shadow_gap_hours,
                "min_earth_pct": min_earth_pct,
                "max_earth_outage_hours": max_earth_outage_hours,
                "min_joint_pct": min_joint_pct
            }
        },
        "total_evaluated_windows": len(candidate_windows),
        "passing_windows_count": len(passing_windows),
        "recommended_windows": passing_windows[:10],
        "alternative_windows": failing_windows[:5],
        "best_window": best_window,
        "explanation": explanation
        ,"provenance":{**provenance(),'calculated_at_utc':datetime.now(timezone.utc).isoformat(),'time_range_utc':[search_start_iso,datetime.fromtimestamp(total_eval_end_unix,tz=timezone.utc).isoformat()],
            'sampling':next(iter(site_data.values()))['series']['sampling'],
            'ranking':'Hard constraints first. Balanced = .35 Sun% + .35 Earth% + .30 Joint% - .8 shadow hours - .5 outage hours; favour Sun = .6 Sun% + .3 Joint% - 1.5 shadow hours; favour Earth analogous; interruptions = .5 Joint% - 2 shadow hours - outage hours.'}
    }
