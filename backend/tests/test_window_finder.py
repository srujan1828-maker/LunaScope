"""
Unit tests for mission window search and ranking.
"""

from app.core.window_finder import search_mission_windows


def test_search_mission_windows():
    res = search_mission_windows(
        site_ids=["shackleton-connecting-ridge", "malapert-mountain"],
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
