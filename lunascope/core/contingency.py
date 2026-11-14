"""LunaScope Contingency Engine: Primary vs Backup Candidate Evaluator & Matcher.

Filters and ranks candidate lunar south pole landing sites across target years (2025-2032)
and mission duration constraints (e.g. 6.0 to 14.0 consecutive days of continuous solar power).

Features:
- Deterministic Pass/Fail mission qualification gate.
- Detailed engineering explainability logs for mission flight directors.
- Provenance tagging: Published (Wueller 2026), Derived (LunaScope margin), Assumed (thresholds).
- Ranked backup candidate recommendations.
"""

from typing import Any, Dict, List, Optional, Tuple
import pandas as pd


def evaluate_contingency(
    df_sites: pd.DataFrame,
    primary_site_id: str,
    target_year: int = 2026,
    required_consecutive_days: float = 10.0,
    min_dte_pct: float = 48.0,
    max_slope_deg: float = 8.0,
) -> Dict[str, Any]:
    """Evaluate candidate sites against mission constraints and rank backups.

    Args:
        df_sites: DataFrame of candidate sites with columns 'site_id', 'name',
                  'consec_days_<year>', 'annual_illum_pct', 'annual_dte_pct', 'avg_slope_deg'.
        primary_site_id: Identifier of the primary landing candidate.
        target_year: Exploration campaign year in [2025, 2032].
        required_consecutive_days: Minimum uninterrupted solar illumination span in days.
        min_dte_pct: Minimum direct-to-Earth communication visibility threshold.
        max_slope_deg: Maximum allowable topographic slope for safe lander landing.

    Returns:
        Dict containing:
            - 'primary_evaluation': Dict of primary site results and engineering rationale
            - 'backup_candidates': List of ranked backup sites with metrics and recommendations
            - 'summary_stats': Aggregated fleet compliance metrics
    """
    col_days = f"consec_days_{target_year}"
    if col_days not in df_sites.columns:
        # Fallback to general or nearest
        available_cols = [c for c in df_sites.columns if c.startswith("consec_days_")]
        col_days = available_cols[0] if available_cols else "annual_illum_pct"

    # Evaluate each site in DataFrame
    evaluations: List[Dict[str, Any]] = []

    for _, row in df_sites.iterrows():
        sid = str(row["site_id"])
        name = str(row["name"])
        c_days = float(row.get(col_days, 0.0))
        illum_pct = float(row.get("annual_illum_pct", 0.0))
        dte_pct = float(row.get("annual_dte_pct", 0.0))
        slope = float(row.get("avg_slope_deg", 0.0))
        elev = float(row.get("elevation_m", 0.0))
        lat = float(row.get("lat_deg", 0.0))
        lon = float(row.get("lon_deg", 0.0))

        margin_days = c_days - required_consecutive_days
        illum_pass = margin_days >= 0.0
        dte_pass = dte_pct >= min_dte_pct
        slope_pass = slope <= max_slope_deg

        passed = illum_pass and dte_pass and slope_pass

        # Engineering explanation
        reasons = []
        if not illum_pass:
            reasons.append(f"Insufficient illumination span: {c_days:.1f}d available vs {required_consecutive_days:.1f}d required ({margin_days:+.1f}d deficit)")
        else:
            reasons.append(f"Exceeds illumination requirement: {c_days:.1f}d available ({margin_days:+.1f}d margin)")

        if not dte_pass:
            reasons.append(f"DTE visibility {dte_pct:.1f}% below minimum threshold ({min_dte_pct:.1f}%)")

        if not slope_pass:
            reasons.append(f"Mean slope {slope:.1f}° exceeds terrain landing safety limit ({max_slope_deg:.1f}°)")

        # Composite score for ranking: prioritize margin_days, then illumination, then DTE, penalize steep slope
        score = (margin_days * 10.0) + (illum_pct * 0.5) + (dte_pct * 0.3) - (slope * 2.0)

        evaluations.append({
            "site_id": sid,
            "name": name,
            "lat_deg": lat,
            "lon_deg": lon,
            "elevation_m": elev,
            "consecutive_days": c_days,
            "margin_days": round(margin_days, 2),
            "annual_illum_pct": illum_pct,
            "annual_dte_pct": dte_pct,
            "avg_slope_deg": slope,
            "passed": passed,
            "illum_pass": illum_pass,
            "dte_pass": dte_pass,
            "slope_pass": slope_pass,
            "reasons": reasons,
            "score": round(score, 2),
        })

    # Find primary site
    primary_eval = next((e for e in evaluations if e["site_id"] == primary_site_id), None)
    if primary_eval is None and evaluations:
        primary_eval = evaluations[0]

    # Filter and rank backups (all sites except primary)
    backups = [e for e in evaluations if e["site_id"] != primary_eval["site_id"]]
    # Sort backups: passed sites first, then by descending score
    backups.sort(key=lambda x: (x["passed"], x["score"]), reverse=True)

    for rank_idx, b in enumerate(backups, start=1):
        b["rank"] = rank_idx
        if b["passed"]:
            b["recommendation"] = f"Top-Tier Backup: +{b['margin_days']:.1f}d solar margin, {b['annual_dte_pct']:.1f}% DTE, stable {b['avg_slope_deg']:.1f}° slopes."
        else:
            b["recommendation"] = f"Contingency with Trade-offs: {b['reasons'][0]}"

    is_synthetic = getattr(df_sites, "attrs", {}).get(
        "is_synthetic_fallback",
        bool(df_sites["is_synthetic_fallback"].iloc[0]) if "is_synthetic_fallback" in df_sites.columns else True
    )
    prov_flag = getattr(df_sites, "attrs", {}).get(
        "provenance_flag",
        "[Assumed / Synthetic Fallback]" if is_synthetic else "[Assumed / Unverified local input]"
    )

    n_passed = sum(1 for e in evaluations if e["passed"])

    return {
        "primary_evaluation": primary_eval,
        "backup_candidates": backups,
        "all_evaluations": evaluations,
        "summary_stats": {
            "total_sites": len(evaluations),
            "passed_sites": n_passed,
            "failed_sites": len(evaluations) - n_passed,
            "pass_rate_pct": round((n_passed / len(evaluations)) * 100.0, 1) if evaluations else 0.0,
            "target_year": target_year,
            "required_consecutive_days": required_consecutive_days,
            "is_synthetic_fallback": is_synthetic,
            "provenance_flag": prov_flag,
        }
    }
