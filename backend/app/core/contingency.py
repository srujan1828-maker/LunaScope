"""
Tier 1: Contingency Planner & Backup Candidate Finder.
Evaluates NASA LOLA analysis locations against annual statistics computed using official terrain and JPL SPICE.
"""

from typing import Dict, List, Any
from app.data.sites_catalog import get_sites_catalog, get_site_by_id


def evaluate_contingency(
    primary_site_id: str,
    year: int = 2027,
    min_sun_days: float = 7.0,
    min_joint_days: float = 5.0
) -> Dict[str, Any]:
    """
    Evaluate the selected primary site against user criteria for a given year (2025-2032)
    and rank viable backup candidates with deterministic pass/fail explanations.
    """
    from app.core.annual_metrics import annual_statistics
    yearly=annual_statistics(year)
    year_str = str(year)
    catalog = get_sites_catalog()
    
    primary_site = get_site_by_id(primary_site_id)
    if not primary_site:
        raise ValueError(f"Site '{primary_site_id}' not found in catalog.")
        
    evaluated_candidates = []
    
    for site in catalog:
        site_annual = yearly.get(site["site_id"])
        if not site_annual:
            continue
            
        sun_days = site_annual["max_consec_sun_days"]
        joint_days = site_annual["max_consec_joint_days"]
        illum_frac = site_annual["annual_illum_fraction"]
        
        passes_sun = sun_days >= min_sun_days
        passes_joint = joint_days >= min_joint_days
        is_viable = passes_sun and passes_joint
        
        reasons = []
        if not passes_sun:
            reasons.append(f"Fails sunlight requirement ({sun_days:.1f} d < {min_sun_days:.1f} d)")
        if not passes_joint:
            reasons.append(f"Fails joint visibility requirement ({joint_days:.1f} d < {min_joint_days:.1f} d)")
            
        if is_viable:
            explanation = (
                f"Passes all constraints ({sun_days:.1f} d continuous sunlight, "
                f"{joint_days:.1f} d joint Sun+Earth visibility)"
            )
        else:
            explanation = "; ".join(reasons)
            
        evaluated_candidates.append({
            "site_id": site["site_id"],
            "name": site["name"],
            "region": site["region"],
            "lat_deg": site["lat_deg"],
            "lon_deg": site["lon_deg"],
            "elevation_m": site["elevation_m"],
            "year": year,
            "max_consec_sun_days": sun_days,
            "max_consec_joint_days": joint_days,
            "annual_illum_fraction": illum_frac,
            "passes_sun": passes_sun,
            "passes_joint": passes_joint,
            "is_viable": is_viable,
            "explanation": explanation
        })
        
    # Extract primary evaluation
    primary_eval = next((c for c in evaluated_candidates if c["site_id"] == primary_site_id), None)
    
    # Filter and rank backups
    other_candidates = [c for c in evaluated_candidates if c["site_id"] != primary_site_id]
    passing_backups = [c for c in other_candidates if c["is_viable"]]
    # Rank by joint visibility margin, then sun margin
    passing_backups.sort(
        key=lambda x: (x["max_consec_joint_days"], x["max_consec_sun_days"]),
        reverse=True
    )
    
    failing_candidates = [c for c in other_candidates if not c["is_viable"]]
    
    return {
        "year": year,
        "criteria": {
            "min_sun_days": min_sun_days,
            "min_joint_days": min_joint_days
        },
        "primary_site": primary_eval,
        "primary_passed": primary_eval["is_viable"] if primary_eval else False,
        "recommended_backups": passing_backups,
        "failing_candidates": failing_candidates,
        "provenance": {
            "annual_metrics": "Derived from NASA LOLA terrain and JPL SPICE for the requested full calendar year, 2m mast, hourly intervals",
            "contingency_ranking": "Derived (LunaScope deterministic threshold comparison)",
            "criteria_thresholds": "Assumed (User planning constraints)"
        }
    }
