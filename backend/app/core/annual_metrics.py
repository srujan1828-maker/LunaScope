"""Annual statistics computed from NASA terrain and SPICE, never a fabricated year table."""
from datetime import datetime,timezone
from functools import lru_cache
from app.data.sites_catalog import get_sites_catalog
from app.core.horizon import compute_horizon_360
from app.core.ephemeris import compute_ephemeris_track
from app.core.visibility import fractional_solar_visibility,evaluate_dte_visibility,compute_interval_metrics

@lru_cache(maxsize=8)
def annual_statistics(year):
    start=datetime(year,1,1,tzinfo=timezone.utc).timestamp();end=datetime(year+1,1,1,tzinfo=timezone.utc).timestamp()
    results={}
    for site in get_sites_catalog():
        h=compute_horizon_360(site['lat_deg'],site['lon_deg'],mast_height_m=2)
        track=compute_ephemeris_track(site['lat_deg'],site['lon_deg'],start,end)
        sun=fractional_solar_visibility(track['sun_azimuth'],track['sun_elevation'],h)
        earth=evaluate_dte_visibility(track['earth_azimuth'],track['earth_elevation'],h)
        durations=[max(0,min(3600,end-t))/3600 for t in track['timestamps']]
        metrics=compute_interval_metrics(sun,earth,sample_hours=durations)
        longest=current=0
        for f,hours in zip(sun,durations):
            if hours==0:continue
            current=current+hours if f>=.1 else 0;longest=max(longest,current)
        results[site['site_id']]={'max_consec_sun_days':float(longest/24),'max_consec_joint_days':float(metrics['longest_joint_window_hours']/24),
            'annual_illum_fraction':float(metrics['equivalent_sun_hours']/metrics['total_duration_hours'])}
    return results
