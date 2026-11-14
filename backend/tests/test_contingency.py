"""
Unit tests for Tier 1 contingency evaluation.
"""

from app.core.contingency import evaluate_contingency


def test_contingency_passing_primary():
    # Malapert Mountain is renowned for high sunlight and joint visibility
    res = evaluate_contingency("malapert-mountain", year=2027, min_sun_days=10.0, min_joint_days=8.0)
    assert res["primary_passed"] is True
    assert len(res["recommended_backups"]) > 0


def test_contingency_failing_primary():
    # Haworth crater has low consecutive sun days (around 6 days in 2027)
    res = evaluate_contingency("haworth-crater-rim", year=2027, min_sun_days=12.0, min_joint_days=6.0)
    assert res["primary_passed"] is False
    assert "Fails sunlight requirement" in res["primary_site"]["explanation"]
    # Backups should include Malapert Mountain, Nobile Rim, etc.
    backup_ids = [b["site_id"] for b in res["recommended_backups"]]
    assert "malapert-mountain" in backup_ids
