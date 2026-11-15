"""Register an inspected lunar south-polar GeoTIFF and optional uncertainty raster.

Example: python backend/scripts/ingest_terrain.py --pgda-site01
Or pass --file, --id, --source-url, --version and the documented --frame.
No kernel/frame conversion or Earth CRS substitution is performed implicitly.
"""
import argparse,hashlib,json,shutil,sys,urllib.request
from pathlib import Path
from datetime import datetime,timezone
import rasterio
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'backend'))
from app.core.nasa_data import RAW,DataUnavailable
from app.core.terrain import inverse_xy


def register(path,identifier,url,version,frame,uncertainty=None):
    if frame!='MOON_ME_DE421':raise ValueError('Only documented MOON_ME_DE421 products can be combined with the installed regional DEM')
    with rasterio.open(path) as ds:
        params=ds.crs.to_dict() if ds.crs else {}
        if params.get('proj')!='stere' or abs(float(params.get('lat_0',0))+90)>1e-8 or abs(float(params.get('lon_0',0)))>1e-8:
            raise ValueError('Expected documented lunar south polar stereographic CRS, longitude origin 0')
        if abs(float(params.get('R',params.get('a',0)))-1737400)>1:
            raise ValueError('Lunar radius does not match the installed DE421/LOLA product')
        if float(params.get('x_0',0))!=0 or float(params.get('y_0',0))!=0 or float(params.get('k',1))!=1:
            raise ValueError('Reproject explicitly to the documented LOLA polar origin and scale before ingestion')
        if params.get('units')!='m' or ds.count!=1 or ds.transform.b or ds.transform.d:
            raise ValueError('Expected one elevation band in metres and an unrotated pixel grid')
        if ds.scales[0]!=1 or ds.offsets[0]!=0:raise ValueError('Normalize explicitly documented height scale/offset before ingestion')
        destination=RAW/path.name
        if path.resolve()!=destination.resolve():shutil.copy2(path,destination)
        error_name=None
        if uncertainty:
            with rasterio.open(uncertainty) as error:
                if (error.crs,error.transform,error.width,error.height)!=(ds.crs,ds.transform,ds.width,ds.height):
                    raise ValueError('Uncertainty raster must align with the terrain raster')
            error_dest=RAW/uncertainty.name
            if error_dest.resolve()!=uncertainty.resolve():shutil.copy2(uncertainty,error_dest)
            error_name=error_dest.name
        cx=(ds.bounds.left+ds.bounds.right)/2;cy=(ds.bounds.bottom+ds.bounds.top)/2;lat,lon=inverse_xy(cx,cy)
        record={'id':identifier,'dataset':path.stem,'version':version,'source_url':url,'frame':frame,'units':'m',
            'projection':'South polar stereographic','pixel_scale_m':float(max(ds.res)),'crs_wkt':ds.crs.to_wkt(),
            'transform':list(ds.transform),'bounds_m':list(ds.bounds),'width':ds.width,'height':ds.height,'nodata':ds.nodata,
            'path':destination.name,'uncertainty_path':error_name,'height_uncertainty_m':None,'effective_resolution_m':None,
            'center_lat_deg':float(lat),'center_lon_deg':float(lon),'sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),
            'registered_at_utc':datetime.now(timezone.utc).isoformat(),
            'limitations':'Gridded/interpolated altimetry. Pixel spacing is not effective resolution; do not infer lander-scale safety.'}
    registry=RAW/'terrain_registry.json';records=json.loads(registry.read_text()) if registry.exists() else []
    records=[r for r in records if r['id']!=identifier]+[record]
    registry.write_text(json.dumps(records,indent=2),encoding='utf-8')
    report=ROOT/'data'/'optional_terrain_provenance.json';report.write_text(json.dumps(records,indent=2),encoding='utf-8')
    print(json.dumps(record,indent=2))


def main():
    p=argparse.ArgumentParser();p.add_argument('--pgda-site01',action='store_true');p.add_argument('--file',type=Path);p.add_argument('--uncertainty',type=Path)
    p.add_argument('--id',default='custom');p.add_argument('--source-url');p.add_argument('--version');p.add_argument('--frame',default='MOON_ME_DE421');a=p.parse_args()
    RAW.mkdir(parents=True,exist_ok=True)
    if a.pgda_site01:
        base='https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/Site01/';names=['Site01_final_adj_5mpp_surf.tif','Site01_final_adj_5mpp_toterr.tif']
        for name in names:
            target=RAW/name
            if not target.exists() or not target.stat().st_size:
                try:
                    with urllib.request.urlopen(base+name,timeout=25) as r,(RAW/(name+'.part')).open('wb') as out:
                        while chunk:=r.read(1024*1024):out.write(chunk)
                    (RAW/(name+'.part')).replace(target)
                except Exception as exc:raise SystemExit('PGDA download unavailable: '+str(exc)+'. Existing official 80 m PDS terrain remains available; no 5 m data is substituted. Retry or download the GeoTIFFs manually and use --file.')
        register(RAW/names[0],'pgda-site01',base+names[0],'Barker et al. 2021 / PGDA product 78',a.frame,RAW/names[1])
    else:
        if not a.file or not a.source_url or not a.version:p.error('--file, --source-url and --version are required')
        register(a.file,a.id,a.source_url,a.version,a.frame,a.uncertainty)

if __name__=='__main__':main()
