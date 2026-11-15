"""
Integration tests for FastAPI endpoints.
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_get_sites():
    response = client.get("/api/sites")
    assert response.status_code == 200
    sites = response.json()
    assert len(sites) >= 10
    site_ids = [s["site_id"] for s in sites]
    assert "lola-sp-001" in site_ids
    assert "lola-sp-002" in site_ids


def test_evaluate_scenario():
    payload = {
        "site_ids": ["lola-sp-001", "lola-sp-002"],
        "start_time_iso": "2027-01-01T00:00:00Z",
        "end_time_iso": "2027-01-04T00:00:00Z",
        "mast_height_m": 2.5,
        "antenna_margin_deg": 0.5,
        "sun_threshold": 0.10,
        "power_config": {
            "enabled": True,
            "panel_area_m2": 3.5,
            "battery_capacity_wh": 2400.0
        }
    }
    response = client.post("/api/scenarios/evaluate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "evaluated_sites" in data
    assert "lola-sp-001" in data["evaluated_sites"]
    assert "comparative_insights" in data


def test_contingency_evaluate():
    payload = {
        "primary_site_id": "lola-sp-003",
        "year": 2027,
        "min_sun_days": 10.0,
        "min_joint_days": 5.0
    }
    response = client.post("/api/contingency/evaluate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["primary_passed"] == (data["primary_site"]["max_consec_sun_days"] >= 10 and data["primary_site"]["max_consec_joint_days"] >= 5)
    assert all(b["is_viable"] for b in data["recommended_backups"])


def test_scenario_save_and_export():
    # 1. Save
    save_payload = {
        "title": "Test Scenario",
        "notes": "Testing persistence and export",
        "site_ids": ["lola-sp-002"],
        "inputs": {"year": 2027},
        "sites_evaluation": {
            "lola-sp-002": {
                "timestamps": [1735689600.0, 1735693200.0],
                "ephemeris": {
                    "sun_azimuth": [10.0, 15.0],
                    "sun_elevation": [1.2, 1.3],
                    "earth_azimuth": [5.0, 5.1],
                    "earth_elevation": [4.0, 4.1]
                },
                "solar_fractions": [1.0, 1.0],
                "dte_visibility": [1, 1],
                "operational_states": [1, 1]
            }
        },
        "comparative_insights": ["High solar exposure."],
        "provenance": {"source": "Test"}
    }
    save_res = client.post("/api/scenarios", json=save_payload)
    assert save_res.status_code == 200
    scenario_id = save_res.json()["scenario_id"]

    # 2. Get
    get_res = client.get(f"/api/scenarios/{scenario_id}")
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "Test Scenario"

    # 3. Export JSON
    json_res = client.get(f"/api/export/{scenario_id}/json")
    assert json_res.status_code == 200
    assert "Test Scenario" in json_res.text

    # 4. Export CSV
    csv_res = client.get(f"/api/export/{scenario_id}/csv")
    assert csv_res.status_code == 200
    assert "timestamp_unix" in csv_res.text
