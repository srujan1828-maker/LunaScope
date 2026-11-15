"""Bounded measured-terrain crops and explicit optional GeoTIFF sources."""
from functools import lru_cache
from pathlib import Path
import json
import numpy as np
from scipy.ndimage import map_coordinates
from app.core import nasa_data
from app.core.nasa_data import DataUnavailable,R_MOON,latlon_to_xy


def sources():
    records=[nasa_data.terrain_metadata()]
    registry=nasa_data.RAW/'terrain_registry.json'
    if registry.exists():records+=json.loads(registry.read_text())
    return records


def source_info(source):
    for info in sources():
        if info['id']==source:return info
    raise DataUnavailable(f'Terrain source {source} is not installed')


def inverse_xy(x,y):
    x,y=np.asarray(x),np.asarray(y)
    return np.degrees(2*np.arctan(np.hypot(x,y)/(2*R_MOON))-np.pi/2),np.degrees(np.arctan2(x,y))%360


def basis(lat,lon):
    """ENU at the observer; at the south pole longitude selects the north meridian."""
    p,l=np.radians([lat,lon])
    return np.array([[-np.sin(l),np.cos(l),0],[-np.sin(p)*np.cos(l),-np.sin(p)*np.sin(l),np.cos(p)],
        [np.cos(p)*np.cos(l),np.cos(p)*np.sin(l),np.sin(p)]])


def cartesian(lat,lon,height):
    p,l=np.radians(lat),np.radians(lon);r=R_MOON+np.asarray(height)
    return np.stack([r*np.cos(p)*np.cos(l),r*np.cos(p)*np.sin(l),r*np.sin(p)],axis=-1)


def sample(x,y,source='lola80',uncertainty=False):
    """Read only the GeoTIFF window containing samples. Keep masked cells as NaN."""
    x,y=np.broadcast_arrays(np.asarray(x,dtype=float),np.asarray(y,dtype=float))
    if source=='lola80':
        return np.full(x.shape,np.nan) if uncertainty else nasa_data.sample_xy(x,y,allow_missing=True)
    info=source_info(source)
    filename=info.get('uncertainty_path' if uncertainty else 'path')
    if not filename:return np.full(x.shape,np.nan)
    import rasterio
    from rasterio.windows import Window
    from rasterio.warp import transform
    path=nasa_data.RAW/filename
    if not path.is_file():raise DataUnavailable('Installed terrain file is missing: '+filename)
    try:dataset=rasterio.open(path)
    except rasterio.errors.RasterioIOError as exc:raise DataUnavailable('Installed terrain raster is unreadable: '+filename) from exc
    with dataset as ds:
        lat,lon=inverse_xy(x,y)
        xx,yy=transform('+proj=longlat +R=1737400 +no_defs',ds.crs,lon.ravel().tolist(),lat.ravel().tolist())
        inv=~ds.transform;xx,yy=np.asarray(xx),np.asarray(yy)
        col=inv.a*xx+inv.b*yy+inv.c-.5;row=inv.d*xx+inv.e*yy+inv.f-.5
        inside=np.isfinite(row)&np.isfinite(col)&(row>=0)&(row<=ds.height-1)&(col>=0)&(col<=ds.width-1)
        result=np.full(row.shape,np.nan)
        if inside.any():
            r0=max(0,int(np.floor(row[inside].min())));r1=min(ds.height,int(np.ceil(row[inside].max()))+2)
            c0=max(0,int(np.floor(col[inside].min())));c1=min(ds.width,int(np.ceil(col[inside].max()))+2)
            data=ds.read(1,window=Window(c0,r0,c1-c0,r1-r0),masked=True).astype(float).filled(np.nan)
            result[inside]=map_coordinates(data,[row[inside]-r0,col[inside]-c0],order=1,mode='constant',cval=np.nan,prefilter=False)
        return result.reshape(x.shape)


def combined_elevation(lat,lon,source='lola80'):
    """High-resolution within its footprint, regional measured terrain outside it.

    Internal missing high-resolution cells remain missing; footprint edges are explicit.
    """
    x,y=latlon_to_xy(lat,lon)
    if source=='lola80':return sample(x,y)
    info=source_info(source);fine=sample(x,y,source)
    # The source bounds are in the same documented polar projection (registered on ingestion).
    left,bottom,right,top=info['bounds_m']
    inside=(x>=left)&(x<=right)&(y>=bottom)&(y<=top)
    return np.where(inside,fine,sample(x,y))


def finite_list(array,precision=4):
    a=np.asarray(array)
    return np.where(np.isfinite(a),np.round(a,precision),None).tolist()


@lru_cache(maxsize=24)
def crop(lat,lon,width_km=12.8,samples=129,source='lola80'):
    info=source_info(source);cx,cy=latlon_to_xy(lat,lon)
    offsets=np.linspace(-width_km*500,width_km*500,samples)
    x,y=np.meshgrid(cx+offsets,cy+offsets[::-1])
    heights=sample(x,y,source);latitudes,longitudes=inverse_xy(x,y)
    valid=np.isfinite(heights)
    center=float(combined_elevation(lat,lon,source))
    if not np.isfinite(center):raise DataUnavailable('Selected observer has no terrain elevation')
    enu=(cartesian(latitudes,longitudes,np.nan_to_num(heights))-cartesian(lat,lon,center))@basis(lat,lon).T
    # Three.js: east +X, up +Y, north -Z. Distances are kilometres, scale is 1:1.
    vertices=np.stack([enu[...,0],enu[...,2],-enu[...,1]],axis=-1)/1000
    vertices[~valid]=np.nan
    errors=sample(x,y,source,uncertainty=True)
    return {'source':info,'center':{'lat_deg':lat,'lon_deg':lon,'elevation_m':center},
        'width_km':width_km,'samples':samples,'mesh_spacing_m':width_km*1000/(samples-1),
        'vertical_exaggeration':1,'vertices_km':finite_list(vertices.reshape(-1,3),7),
        'elevations_m':finite_list(heights.ravel()),'latitudes':finite_list(latitudes.ravel(),8),
        'longitudes':finite_list(longitudes.ravel(),8),'uncertainty_m':finite_list(errors.ravel()),
        'coverage_fraction':float(valid.mean()),'elevation_range_m':finite_list([np.nanmin(heights),np.nanmax(heights)]) if valid.any() else [None,None],
        'frame':'MOON_ME_DE421','axes':'east +X / up +Y / north -Z; km; no vertical exaggeration',
        'limitations':'Triangulated sampled terrain; holes preserve NoData. Pixel spacing is not effective resolution. Shadows cover displayed crop only.'}
