"""Regression checks for scientific accounting and reactive matching contracts."""
import math
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.visibility import fractional_solar_visibility, compute_interval_metrics
from app.core.power_model import simulate_power_and_battery
from app.core.scenario_store import save_scenario, get_scenario

client = TestClient(app)
WINDOW = {'start_time_iso':'2027-01-01T00:00:00Z','end_time_iso':'2027-01-02T00:30:00Z'}

def test_clipped_interval_and_empty_endpoint():
    data = client.post('/api/scenarios/evaluate',json={**WINDOW,'site_ids':['lola-sp-002']}).json()
    site = data['evaluated_sites']['lola-sp-002']
    assert sum(site['sample_hours']) == 24.5
    assert site['interval_metrics']['total_duration_hours'] == 24.5
    assert data['provenance']['mode']=='nasa-official' and 'NASA' in data['provenance']['terrain']

def test_power_conservation_at_load_and_no_endpoint_extra_energy():
    p=simulate_power_and_battery([0,3600],[0,0],[0,0],[0,0],spacecraft_load_w=100,battery_capacity_wh=100,
        initial_soc_pct=0,sample_hours=[1,0])
    assert p['summary']['total_unmet_demand_wh'] == 100

@pytest.mark.parametrize('limb',[True,False])
def test_solar_disk_complement_and_continuity(limb):
    values=fractional_solar_visibility([0]*5,[-.266001,-.266+1e-6,0,.266-1e-6,.266001],[0]*360,limb_darkening=limb)
    assert values[0] == 0 and values[-1] == 1 and values[2] == .5
    assert abs(values[1]+values[-2]-1) < 1e-4

@pytest.mark.parametrize('patch',[{'power_config':{'battery_capacity_wh':0}}, {'site_ids':['missing']},
    {'start_time_iso':'2027-01-01'}, {'end_time_iso':'2026-01-01T00:00:00Z'}, {'mast_height_m':-2}])
def test_invalid_scenario_returns_validation_error(patch):
    res=client.post('/api/scenarios/evaluate',json={**WINDOW,'site_ids':['lola-sp-002'],**patch})
    assert res.status_code == 422

def test_match_constraints_and_no_false_recommendation():
    payload={**WINDOW,'min_sun_pct':0,'min_earth_pct':0,'max_shadow_gap_hours':1000}
    res=client.post('/api/matches/evaluate',json=payload)
    assert res.status_code == 200
    loose=res.json()
    assert loose['passing_count'] == loose['evaluated_count'] == len(client.get('/api/sites').json())
    strict=client.post('/api/matches/evaluate',json={**payload,'min_consecutive_sun_days':120}).json()
    assert strict['passing_count'] == 0 and strict['recommended_primary'] is None and not strict['backup_sites']
    assert all(r['violations'] and r['terrain_safety']=='unknown' for r in strict['rankings'])

def test_websocket_matches_same_as_rest_and_recovers_after_error():
    payload={**WINDOW,'site_ids':['lola-sp-002']}
    rest=client.post('/api/matches/evaluate',json=payload).json()
    with client.websocket_connect('/api/ws/matches') as ws:
        ws.send_json({'revision':1,'parameters':{'mast_height_m':-1}})
        assert ws.receive_json()['type']=='error'
        ws.send_json({'revision':2,'parameters':payload})
        result=ws.receive_json()
        assert result['revision']==2 and result['result']['rankings']==rest['rankings']

def test_snapshot_is_immutable():
    original={'inputs':{'value':1}}
    sid=save_scenario(original)
    original['inputs']['value']=2
    copy=get_scenario(sid); copy['inputs']['value']=3
    assert get_scenario(sid)['inputs']['value']==1

def test_stream_selection_and_bad_command_recovery():
    with client.websocket_connect('/api/ws/simulation') as ws:
        ws.receive_json()
        ws.send_json({'command':'select_sites','site_ids':['lola-sp-004']})
        assert 'lola-sp-004' in ws.receive_json()['sites']
        ws.send_json({'command':'step','dt_seconds':-1})
        assert ws.receive_json()['type']=='error'
        ws.send_json({'command':'step','dt_seconds':3600})
        assert ws.receive_json()['type']=='telemetry_frame'

def test_live_hardware_configuration_survives_site_change():
    with client.websocket_connect('/api/ws/simulation') as ws:
        ws.receive_json()
        ws.send_json({'command':'configure','antenna_margin_deg':10,'power_config':{
            'panel_area_m2':1,'panel_efficiency':0.01,'spacecraft_load_w':321,'battery_capacity_wh':100,
            'initial_soc_pct':25,'reserve_margin_pct':30}})
        first=ws.receive_json()
        assert all(v['power']['battery_soc_pct']==25 for v in first['sites'].values())
        ws.send_json({'command':'select_sites','site_ids':['lola-sp-002']})
        site=ws.receive_json()['sites']['lola-sp-002']
        assert site['power']['battery_soc_pct']==25
        assert site['power']['reserve_breached']
        assert site['power']['generated_w'] < 20
