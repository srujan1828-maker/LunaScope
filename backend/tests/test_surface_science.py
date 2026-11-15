"""Physics/coverage regressions; artificial landscapes are confined to these tests."""
import json,math
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core import horizon,terrain,nasa_data
from app.core.visibility import fractional_solar_visibility,interpolate_horizon,classify_operational_states,compute_interval_metrics
from app.core.events import visibility_series,window_metrics
from app.core.ephemeris import ephemeris_at_times
from app.core.power_model import simulate_power_and_battery
client=TestClient(app)


@pytest.mark.parametrize('kind',['flat','ridge','crater','missing'])
def test_isolated_landscape_horizons_and_missing_sectors(monkeypatch,kind):
    lat,lon=-89.,0.
    def fake(latitudes,longitudes,source='lola80'):
        a,b=np.asarray(latitudes),np.asarray(longitudes)
        # Angular distances approximate local northing for this unit-test landscape.
        north=np.radians(a-lat)*nasa_data.R_MOON
        east=np.radians(b)*nasa_data.R_MOON*math.cos(math.radians(lat))
        if kind=='flat':return np.zeros(np.broadcast(a,b).shape)
        if kind=='ridge':return np.where((north>900)&(north<1300)&(np.abs(east)<500),200.,0.)
        if kind=='crater':return np.where((np.hypot(north,east)>900)&(np.hypot(north,east)<1400),100.,0.)
        return np.where(north>500,np.nan,0.)
    monkeypatch.setattr(horizon,'combined_elevation',fake);horizon.horizon_profile.cache_clear()
    try:
        p=horizon.horizon_profile(lat,lon,2.,3000.,80.)
        if kind=='flat':assert max(p['elevations_deg'])<0
        if kind=='ridge':assert p['elevations_deg'][0]>7 and p['elevations_deg'][180]<0
        if kind=='crater':assert p['elevations_deg'][0]>3 and p['elevations_deg'][180]>3
        if kind=='missing':assert p['elevations_deg'][0] is None and p['coverage']=='incomplete'
        if kind in ('ridge','crater'):assert 900<=p['obstruction_points'][0]['distance_m']<=1400
    finally:horizon.horizon_profile.cache_clear()


def test_compass_rotation_and_pole_meridian():
    np.testing.assert_allclose(terrain.basis(-90,90)@terrain.basis(-90,90).T,np.eye(3),atol=1e-12)
    p=horizon.horizon_profile(-90,90)
    assert p['reference_meridian_deg']==90
    assert p['obstruction_points'][0]['lon_deg']==pytest.approx(90,abs=1e-7)


def test_disk_integrates_varying_horizon_and_wraps_without_filling_unknown():
    h=[0.]*360;h[0]=.1
    assert interpolate_horizon([359.5],h)[0]==pytest.approx(.05)
    f=fractional_solar_visibility([359.9,.1],[0,0],h)
    assert f[0]==pytest.approx(f[1],abs=2e-5)
    assert f[0]<.5
    h[0]=None
    assert fractional_solar_visibility([0],[0],h)==[None]
    assert classify_operational_states([None,1],[1,None])==[0,0]
    m=compute_interval_metrics([None,1],[1,1])
    assert m['coverage']=='unknown' and m['sun_availability_pct'] is None


def test_real_mesh_values_scale_and_bounded_api():
    site=client.get('/api/sites').json()[0]
    data=client.get('/api/terrain/crop',params={'lat_deg':site['lat_deg'],'lon_deg':site['lon_deg'],'samples':33,'width_km':6.4}).json()
    i=33*16+16
    assert data['elevations_m'][i]==pytest.approx(site['elevation_m'],abs=1e-5)
    np.testing.assert_allclose(data['vertices_km'][i],[0,0,0],atol=1e-7)
    assert data['vertical_exaggeration']==1 and len(data['vertices_km'])==1089
    assert client.get('/api/terrain/crop',params={'lat_deg':-89,'lon_deg':0,'samples':1025}).status_code==422


def test_surface_frame_scene_vectors_and_geometric_disk_states():
    res=client.post('/api/surface/frame',json={'lat_deg':-89,'lon_deg':0,'time_iso':'2027-01-01T00:00:00Z'})
    assert res.status_code==200,res.text
    f=res.json()
    for name in ['sun','earth']:
        v=np.asarray(f[name]['direction_scene']);assert np.linalg.norm(v)==pytest.approx(1)
        assert np.degrees(np.arcsin(v[1]))==pytest.approx(f[name]['elevation_deg'])
        assert np.degrees(np.arctan2(v[0],-v[2]))%360==pytest.approx(f[name]['azimuth_deg'])
    assert 0<=f['earth']['illuminated_fraction']<=1
    assert f['earth']['angular_radius_deg']>f['sun']['angular_radius_deg']
    assert 'calculated_at_utc' in f['provenance']
    assert client.post('/api/surface/frame',json={'lat_deg':-89,'lon_deg':0,'time_iso':'2027-01-01'}).status_code==422


def test_adaptive_transition_brackets_and_partial_duration():
    start=datetime(2027,1,1,tzinfo=timezone.utc).timestamp()
    series=visibility_series(-86.56848542390216,45.03113900753911,start,start+14*86400)
    gaps=np.diff(series['timestamps'])
    assert max(gaps)<=600
    assert series['events'] and all(e['bracket_seconds']<=30 for e in series['events'])
    assert sum(series['sample_hours'])==pytest.approx(336)
    assert window_metrics(series,start+123,start+86400+234)['total_duration_hours']==pytest.approx((86400+111)/3600)


def test_saved_independent_horizons_agreement():
    directory=Path(__file__).resolve().parents[2]/'data'/'validation'
    report=json.loads((directory/'horizons_report.json').read_text())
    assert report['passed'] and len(report['comparisons'])==12
    for row in report['comparisons']:
        site=next(s for s in client.get('/api/sites').json() if s['site_id']==row['site_id'])
        t=datetime.fromisoformat(row['utc']).timestamp()
        eph=ephemeris_at_times(site['lat_deg'],site['lon_deg'],(t,),site['elevation_m']+2)
        assert abs(eph[row['body']+'_elevation'][0]-row['horizons_elevation_deg'])<report['acceptance_tolerance_deg']


def test_configurable_power_efficiencies_and_unknown_terrain():
    p=simulate_power_and_battery([0],[0],[0],[0],spacecraft_load_w=100,battery_capacity_wh=100,initial_soc_pct=100,discharge_efficiency=.5,sample_hours=[1])
    assert p['summary']['total_unmet_demand_wh']==50
    assert p['summary']['longest_without_generation_hours']==1
    assert p['summary']['total_consumed_wh']==100
    assert math.isnan(nasa_data.sample_xy(1e7,1e7,allow_missing=True))
    with pytest.raises(nasa_data.DataUnavailable):nasa_data.sample_xy(1e7,1e7)


def test_geotiff_ingestion_metadata_and_nodata_window_reader(monkeypatch,tmp_path):
    import importlib.util,rasterio
    from rasterio.transform import from_origin
    script=Path(__file__).resolve().parents[1]/'scripts'/'ingest_terrain.py'
    spec=importlib.util.spec_from_file_location('ingest_test',script);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.ROOT=tmp_path;module.RAW=tmp_path/'raw';module.RAW.mkdir();(tmp_path/'data').mkdir()
    path=tmp_path/'isolated-test-terrain.tif';values=np.arange(100,dtype=np.float32).reshape(10,10);values[4,4]=-9999
    with rasterio.open(path,'w',driver='GTiff',width=10,height=10,count=1,dtype='float32',
            crs='+proj=stere +lat_0=-90 +lon_0=0 +R=1737400 +units=m +no_defs',transform=from_origin(-400,400,80,80),nodata=-9999) as ds:ds.write(values,1)
    module.register(path,'test-grid','https://example.invalid/unit-test-only','unit-test','MOON_ME_DE421')
    record=json.loads((module.RAW/'terrain_registry.json').read_text())[0]
    assert record['pixel_scale_m']==80 and record['nodata']==-9999
    monkeypatch.setattr(nasa_data,'RAW',module.RAW)
    monkeypatch.setattr(terrain,'source_info',lambda source:record)
    missing=terrain.sample(-40,40,'test-grid')
    assert np.isnan(missing)
    valid=terrain.sample(-280,280,'test-grid')
    assert valid==pytest.approx(11.)
    with pytest.raises(ValueError,match='MOON_ME_DE421'):module.register(path,'bad','x','x','IAU_MOON')


def test_unreadable_kernel_set_has_actionable_error(monkeypatch,tmp_path):
    from app.core import spice_geometry
    for name in spice_geometry.KERNELS:(tmp_path/name).write_bytes(b'not a scientific kernel')
    monkeypatch.setattr(spice_geometry,'RAW',tmp_path);spice_geometry.spice.cache_clear()
    try:
        with pytest.raises(nasa_data.DataUnavailable,match='unreadable or incompatible'):spice_geometry.spice()
    finally:spice_geometry.spice.cache_clear()
