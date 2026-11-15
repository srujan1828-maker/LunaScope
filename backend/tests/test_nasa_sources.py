"""Verify real input provenance, raster decoding, kernel geometry and failure behavior."""
from pathlib import Path
import hashlib,json
import numpy as np
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core import nasa_data
from app.core.spice_geometry import spice,LOCK,body_vectors,FRAME
from app.core.ephemeris import compute_ephemeris_track
from app.data.sites_catalog import get_sites_catalog
client=TestClient(app)

def test_official_downloads_are_real_files_with_recorded_hashes():
    manifest=nasa_data.manifest()
    for name,record in manifest['sources'].items():
        path=nasa_data.RAW/name
        assert path.stat().st_size==record['bytes']
        assert hashlib.sha256(path.read_bytes()).hexdigest()==record['sha256']
        assert record['url'].startswith(('https://imbrium.mit.edu/','https://naif.jpl.nasa.gov/'))
    assert nasa_data.readiness()['synthetic_fallback'] is False

def test_catalog_values_trace_to_actual_pds_pixels():
    import rasterio
    from rasterio.windows import Window
    catalog=get_sites_catalog()
    with rasterio.open(nasa_data.RAW/'LDEM_80S_80M.JP2') as raster:
        for site in catalog:
            row=site['source_pixel']['row'];col=site['source_pixel']['column']
            original=float(raster.read(1,window=Window(col,row,1,1))[0,0])*.5
            assert site['elevation_m']==original
            assert nasa_data.elevation(site['lat_deg'],site['lon_deg'])==pytest.approx(original,abs=1e-5)
            assert site['annual_data']=={}
            assert site['terrain_safety']=='unknown'

def test_spice_track_matches_direct_naif_vector_projection():
    api=spice();time=1798761600.0;site=get_sites_catalog()[0]
    with LOCK:
        et=api.str2et('2027-01-01T00:00:00')
        original=np.asarray(api.spkpos('SUN',et,FRAME,'LT+S','MOON')[0])*1000
    vectors=body_vectors((time,))[0][0]
    np.testing.assert_allclose(vectors,original,atol=1e-4)
    track=compute_ephemeris_track(site['lat_deg'],site['lon_deg'],time,time)
    phi,lam=np.radians([site['lat_deg'],site['lon_deg']])
    up=np.array([np.cos(phi)*np.cos(lam),np.cos(phi)*np.sin(lam),np.sin(phi)])
    delta=original-(1737400+site['elevation_m'])*up
    expected=np.degrees(np.arcsin(np.dot(delta,up)/np.linalg.norm(delta)))
    assert track['sun_elevation'][0]==pytest.approx(expected,abs=1e-7)
    assert track['frame']=='MOON_ME_DE421'

def test_missing_nasa_files_return_unavailable_without_fabricating(monkeypatch,tmp_path):
    monkeypatch.setattr(nasa_data,'RAW',tmp_path)
    nasa_data.terrain_grid.cache_clear()
    res=client.post('/api/scenarios/evaluate',json={'site_ids':['lola-sp-001']})
    assert res.status_code==503
    assert res.json()['synthetic_fallback'] is False
    assert client.get('/api/data/status').json()['ready'] is False
    nasa_data.terrain_grid.cache_clear()

def test_provenance_and_no_fake_dsn_contacts():
    res=client.get('/api/data/provenance')
    assert res.status_code==200 and res.json()['mode']=='nasa-official'
    assert res.headers['X-LunaScope-Data-Mode']=='nasa-official'
    from app.core.ground_stations import evaluate_dsn_coverage
    status=evaluate_dsn_coverage(1798761600,0,0,True)
    assert status['status']=='unknown' and status['is_network_closed'] is None
