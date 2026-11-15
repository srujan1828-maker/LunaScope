"""
Unit tests for mission window search and ranking.
"""

from app.core.window_finder import search_mission_windows
import pytest


def test_search_mission_windows():
    res = search_mission_windows(
        site_ids=["lola-sp-001", "lola-sp-002"],
        search_start_iso="2027-01-01T00:00:00Z",
        search_end_iso="2027-01-10T00:00:00Z",
        mission_duration_days=3.0,
        stride_hours=24.0,
        min_sun_pct=50.0,
        max_shadow_gap_hours=24.0,
        min_earth_pct=40.0,
        priority="balanced"
    )
    assert res["total_evaluated_windows"] > 0
    assert "best_window" in res
    assert res["best_window"] is not None


def test_fractional_stride_preserves_candidate_utc_and_entire_duration():
    res=search_mission_windows(['lola-sp-001'],'2027-01-01T12:00:00Z','2027-01-01T15:00:00Z',
        mission_duration_days=1.125,stride_hours=1.25,min_sun_pct=0,min_earth_pct=0,min_joint_pct=0,
        max_shadow_gap_hours=200,max_earth_outage_hours=200)
    windows=sorted(res['recommended_windows']+res['alternative_windows'],key=lambda r:r['start_unix'])
    assert len(windows)==3
    assert windows[1]['start_unix']-windows[0]['start_unix']==4500
    assert all(w['site_evaluations']['lola-sp-001']['metrics']['total_duration_hours']==pytest.approx(27,abs=1e-9) for w in windows)
