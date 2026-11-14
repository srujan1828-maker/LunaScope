"""
End-to-End Integration & Static Asset Serving Tests.
Verifies both frontend build serving and full API execution.
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_frontend_serving():
    # Root path should return index.html
    res = client.get("/")
    assert res.status_code == 200
    assert '<div id="root"></div>' in res.text
    assert "LunaScope 2.0" in res.text


def test_frontend_asset_serving():
    # Asset files mounted under /assets
    res_html = client.get("/")
    assert res_html.status_code == 200
    # Find asset script or css link
    import re
    asset_match = re.search(r'/assets/index-[a-zA-Z0-9_\-]+\.js', res_html.text)
    if asset_match:
        asset_url = asset_match.group(0)
        asset_res = client.get(asset_url)
        assert asset_res.status_code == 200
        assert len(asset_res.content) > 1000


def test_full_scenario_workflow():
    # 1. Query sites
    sites_res = client.get("/api/sites")
    assert sites_res.status_code == 200
    sites = sites_res.json()
    assert len(sites) >= 2
    s1 = sites[0]["site_id"]
    s2 = sites[1]["site_id"]

    # 2. Evaluate scenario with power simulation
    eval_payload = {
        "site_ids": [s1, s2],
        "start_time_iso": "2027-01-01T00:00:00Z",
        "end_time_iso": "2027-01-08T00:00:00Z",
        "mast_height_m": 2.5,
        "antenna_margin_deg": 0.5,
        "sun_threshold": 0.10,
        "power_config": {
            "enabled": True,
            "panel_area_m2": 4.0,
            "spacecraft_load_w": 120.0,
            "battery_capacity_wh": 2400.0
        }
    }
    eval_res = client.post("/api/scenarios/evaluate", json=eval_payload)
    assert eval_res.status_code == 200
    eval_data = eval_res.json()
    assert s1 in eval_data["evaluated_sites"]
    assert s2 in eval_data["evaluated_sites"]

    s1_data = eval_data["evaluated_sites"][s1]
    assert len(s1_data["horizon_360"]) == 360
    assert len(s1_data["solar_fractions"]) > 0
    assert len(s1_data["operational_states"]) > 0
    assert s1_data["power_simulation"] is not None
    assert "battery_soc_pct" in s1_data["power_simulation"]["time_series"]

    # 3. Save scenario
    save_payload = {
        "title": "E2E Test Scenario",
        "notes": "Automated build verification",
        "site_ids": [s1, s2],
        "inputs": eval_data["inputs"],
        "sites_evaluation": eval_data["evaluated_sites"],
        "comparative_insights": eval_data["comparative_insights"],
        "provenance": eval_data["provenance"]
    }
    save_res = client.post("/api/scenarios", json=save_payload)
    assert save_res.status_code == 200
    sc_id = save_res.json()["scenario_id"]

    # 4. Export JSON & CSV
    json_export = client.get(f"/api/export/{sc_id}/json")
    assert json_export.status_code == 200
    assert "E2E Test Scenario" in json_export.text

    csv_export = client.get(f"/api/export/{sc_id}/csv")
    assert csv_export.status_code == 200
    assert "operational_state" in csv_export.text
