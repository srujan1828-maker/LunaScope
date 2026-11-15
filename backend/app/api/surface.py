"""Thread-pooled surface data routes. Bounded meshes never send the full DEM."""
from datetime import datetime
from typing import Literal
from fastapi import APIRouter,Query,Response
from pydantic import Field,model_validator
from app.api.schemas import ValidatedRequest
from app.core.terrain import crop,sources
from app.core.surface import surface_frame
from app.core.events import visibility_series
from app.core.nasa_data import DataUnavailable

router=APIRouter()

class SurfaceRequest(ValidatedRequest):
    lat_deg:float=Field(ge=-90,le=-80)
    lon_deg:float=Field(ge=0,le=360)
    time_iso:str='2027-01-01T00:00:00Z'
    mast_height_m:float=Field(2,ge=.5,le=30)
    source:str='lola80'
    @model_validator(mode='after')
    def utc(self):
        dt=datetime.fromisoformat(self.time_iso.replace('Z','+00:00'))
        if dt.tzinfo is None or not 2025<=dt.year<=2032:raise ValueError('Choose UTC with offset, between 2025 and 2032')
        return self

@router.get('/terrain/sources')
def terrain_sources():return sources()

@router.get('/terrain/crop')
def terrain_crop(response:Response,lat_deg:float=Query(ge=-90,le=-80),lon_deg:float=Query(ge=0,le=360),
                 width_km:float=Query(12.8,ge=.2,le=40),samples:int=Query(129,ge=17,le=257),source:str='lola80'):
    response.headers['Cache-Control']='private, max-age=300'
    return crop(lat_deg,lon_deg,width_km,samples,source)

@router.post('/surface/frame')
def frame(req:SurfaceRequest):
    t=datetime.fromisoformat(req.time_iso.replace('Z','+00:00')).timestamp()
    return surface_frame(req.lat_deg,req.lon_deg,t,req.mast_height_m,req.source)

class SurfaceTimeline(SurfaceRequest):
    days:float=Field(1,ge=.01,le=31)

@router.post('/surface/timeline')
def timeline(req:SurfaceTimeline):
    start=datetime.fromisoformat(req.time_iso.replace('Z','+00:00')).timestamp()
    return visibility_series(req.lat_deg,req.lon_deg,start,start+req.days*86400,req.mast_height_m,source=req.source)
