"""Fetch independent JPL Horizons observer tables; retain responses and actual errors."""
from pathlib import Path
from datetime import datetime,timezone
import csv,io,json,sys,urllib.parse,urllib.request
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'backend'))
from app.data.sites_catalog import get_sites_catalog
from app.core.ephemeris import ephemeris_at_times
OUT=ROOT/'data'/'validation';OUT.mkdir(parents=True,exist_ok=True)


def main():
    rows=[];queries=[]
    for site in get_sites_catalog()[:2]:
        height=site['elevation_m']+2
        for target,name in [('10','sun'),('399','earth')]:
            q={'format':'json','COMMAND':f"'{target}'",'CENTER':"'coord@301'",'COORD_TYPE':"'GEODETIC'",
                'SITE_COORD':f"'{site['lon_deg']},{site['lat_deg']},{height/1000}'",'START_TIME':"'2027-01-01 00:00'",
                'STOP_TIME':"'2027-01-01 02:00'",'STEP_SIZE':"'1 h'",'QUANTITIES':"'4,13,20'",'CSV_FORMAT':"'YES'",'EXTRA_PREC':"'YES'",'OBJ_DATA':"'NO'"}
            url='https://ssd.jpl.nasa.gov/api/horizons.api?'+urllib.parse.urlencode(q)
            response=json.load(urllib.request.urlopen(url,timeout=60));raw=response.get('result','')
            if '$$SOE' not in raw:raise RuntimeError(response)
            filename=site['site_id']+'-'+name+'-horizons.json';(OUT/filename).write_text(json.dumps({'url':url,'response':response},indent=2))
            queries.append({'file':filename,'url':url,'frame_note':'Horizons DE441 / MEAN_ME; application DE421 / MOON_ME_DE421. Comparison is cross-ephemeris, not an exact identity.'})
            values=list(csv.reader(io.StringIO(raw.split('$$SOE')[1].split('$$EOE')[0].strip())))
            times=[datetime.strptime(v[0].strip(),'%Y-%b-%d %H:%M').replace(tzinfo=timezone.utc).timestamp() for v in values]
            track=ephemeris_at_times(site['lat_deg'],site['lon_deg'],times,height)
            for i,v in enumerate(values):
                az=float(v[3]);el=float(v[4]);calcaz=track[name+'_azimuth'][i];calcel=track[name+'_elevation'][i]
                rows.append({'site_id':site['site_id'],'body':name,'utc':datetime.fromtimestamp(times[i],tz=timezone.utc).isoformat(),
                    'horizons_azimuth_deg':az,'horizons_elevation_deg':el,'calculated_azimuth_deg':calcaz,'calculated_elevation_deg':calcel,
                    'azimuth_error_deg':abs((calcaz-az+180)%360-180),'elevation_error_deg':abs(calcel-el)})
    maximum=max(max(r['azimuth_error_deg'],r['elevation_error_deg']) for r in rows)
    result={'retrieved_at_utc':datetime.now(timezone.utc).isoformat(),'source':'NASA/JPL Horizons observer API','queries':queries,'comparisons':rows,
        'acceptance_tolerance_deg':.02,'maximum_direction_error_deg':maximum,'passed':maximum<.02,
        'scope':'12 Sun/Earth topocentric direction checks, two measured locations, three UTC epochs on 2027-01-01; no terrain or power validation is implied.'}
    (OUT/'horizons_report.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
    if not result['passed']:raise SystemExit('Direction validation exceeded documented tolerance')

if __name__=='__main__':main()
