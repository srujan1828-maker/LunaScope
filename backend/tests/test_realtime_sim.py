"""
Unit tests for the real-time simulation engine, WebSocket streaming, landing dispersion, and mast sensitivity.
"""

import pytest
from app.core.simulation_engine import RealtimeSimulationSession
from app.core.landing_dispersion import evaluate_landing_dispersion
from app.core.mast_sensitivity import evaluate_mast_sensitivity
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_realtime_simulation_session():
    session = RealtimeSimulationSession(
        site_ids=["lola-sp-001", "lola-sp-002"],
        start_unix=1735689600.0,
        mast_height_m=2.0,
        speed_multiplier=60.0
    )
    frame0 = session.compute_frame(dt_seconds=1.0)
    assert frame0["type"] == "telemetry_frame"
    assert "lola-sp-001" in frame0["sites"]
    assert "lola-sp-002" in frame0["sites"]

    s1 = frame0["sites"]["lola-sp-001"]
    assert "sun" in s1
    assert "earth" in s1
    assert "regime" in s1
    assert "power" in s1
    assert s1["power"]["battery_soc_pct"] > 90.0

    # Advance simulation by 3600 seconds (1 hour)
    frame1 = session.advance_time(3600.0)
    assert frame1["timestamp_unix"] == 1735689600.0 + 3600.0


def test_landing_dispersion():
    res = evaluate_landing_dispersion(
        site_id="lola-sp-001",
        start_unix=1735689600.0,
        end_unix=1735689600.0 + (3 * 86400.0),
        semi_major_m=200.0,
        semi_minor_m=100.0,
        num_samples=9,
        mast_height_m=2.0
    )
    assert "envelope" in res
    assert "robustness" in res
    assert len(res["sample_points"]) == 9
    assert res["sample_points"][0]["is_center"] is True


def test_mast_sensitivity_sweep():
    res = evaluate_mast_sensitivity(
        site_id="lola-sp-002",
        start_unix=1735689600.0,
        end_unix=1735689600.0 + (3 * 86400.0),
        mast_heights=[1.0, 5.0, 10.0]
    )
    assert len(res["sweep"]) == 3
    # Higher mast should lower average horizon elevation
    assert res["sweep"][-1]["horizon_mean_elevation_deg"] < res["sweep"][0]["horizon_mean_elevation_deg"]


def test_dispersion_api_endpoint():
    payload = {
        "site_id": "lola-sp-002",
        "start_time_iso": "2027-01-01T00:00:00Z",
        "end_time_iso": "2027-01-04T00:00:00Z",
        "semi_major_m": 150.0,
        "semi_minor_m": 75.0,
        "num_samples": 9
    }
    res = client.post("/api/simulation/dispersion", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "envelope" in data
    assert data["site_id"] == "lola-sp-002"


def test_mast_sensitivity_api_endpoint():
    payload = {
        "site_id": "lola-sp-001",
        "start_time_iso": "2027-01-01T00:00:00Z",
        "end_time_iso": "2027-01-04T00:00:00Z",
        "mast_heights": [2.0, 10.0]
    }
    res = client.post("/api/simulation/mast-sensitivity", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert len(data["sweep"]) == 2


def test_websocket_simulation():
    with client.websocket_connect("/api/ws/simulation") as ws:
        init_msg = ws.receive_json()
        assert init_msg["type"] == "session_init"

        # Send step command
        ws.send_json({"command": "step", "dt_seconds": 1800.0})
        frame = ws.receive_json()
        assert frame["type"] == "telemetry_frame"

        # Send set_speed command
        ws.send_json({"command": "set_speed", "speed": 120.0})
        status_msg = ws.receive_json()
        assert status_msg["type"] == "status"
        assert status_msg["speed_multiplier"] == 120.0
