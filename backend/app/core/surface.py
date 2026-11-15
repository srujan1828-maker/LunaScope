"""Traceable instantaneous scene readings for the measured terrain explorer."""
from datetime import datetime,timezone
import numpy as np
from app.core.horizon import horizon_profile
from app.core.ephemeris import ephemeris_at_times
from app.core.visibility import fractional_solar_visibility,evaluate_dte_visibility,classify_operational_states,interpolate_horizon
from app.core.spice_geometry import body_vectors
from app.core.terrain import basis,cartesian,source_info,sample
from app.core.nasa_data import latlon_to_xy
from app.core.nasa_data import provenance


def surface_frame(lat,lon,timestamp,mast=2.,source='lola80'):
    profile=horizon_profile(lat,lon,mast,source=source);h=profile['elevations_deg'];height=profile['observer_elevation_m']
    height_error=float(sample(*latlon_to_xy(lat,lon),source,uncertainty=True))
    height_error=height_error if np.isfinite(height_error) else None
    track=ephemeris_at_times(lat,lon,(timestamp,),height+mast)
    f=fractional_solar_visibility(track['sun_azimuth'],track['sun_elevation'],h,angular_radius_deg=track['solar_angular_radius_deg'])[0]
    earth=evaluate_dte_visibility(track['earth_azimuth'],track['earth_elevation'],h)[0]
    earth_disk=fractional_solar_visibility(track['earth_azimuth'],track['earth_elevation'],h,angular_radius_deg=track['earth_angular_radius_deg'])[0]
    sv,ev=body_vectors((float(timestamp),));observer=cartesian(lat,lon,height+mast)
    sun_relative=sv[0]-observer;earth_relative=ev[0]-observer
    # Physical illuminated fraction of a spherical Earth from the observer.
    to_sun=sv[0]-ev[0];to_observer=observer-ev[0]
    phase=float((1+np.dot(to_sun/np.linalg.norm(to_sun),to_observer/np.linalg.norm(to_observer)))/2)
    def body(name):
        az=track[name+'_azimuth'][0];el=track[name+'_elevation'][0];skyline=float(interpolate_horizon([az],h)[0])
        vector=(sun_relative if name=='sun' else earth_relative)@basis(lat,lon).T
        direction=vector/np.linalg.norm(vector)
        return {'azimuth_deg':az,'elevation_deg':el,'angular_radius_deg':track[('solar' if name=='sun' else 'earth')+'_angular_radius_deg'][0],
            'horizon_elevation_deg':skyline if np.isfinite(skyline) else None,
            'direction_scene':[float(direction[0]),float(direction[2]),float(-direction[1])],
            'obstruction':profile['obstruction_points'][int(round(az))%360]}
    return {'timestamp_unix':timestamp,'utc':datetime.fromtimestamp(timestamp,tz=timezone.utc).isoformat(),
        'location':{'lat_deg':lat,'lon_deg':lon,'elevation_m':height,'mast_height_m':mast,'uncertainty_m':height_error},
        'sun':{**body('sun'),'visible_fraction':f,'irradiance_w_m2':track['solar_flux_w_m2'][0]},
        'earth':{**body('earth'),'center_visible':earth,'visible_disk_fraction':earth_disk,
            'complete_disk_visible':None if earth_disk is None else earth_disk>=.999999,'illuminated_fraction':phase},
        'state':classify_operational_states([f],[earth])[0],'horizon':profile,
        'provenance':{**provenance(),'calculated_at_utc':datetime.now(timezone.utc).isoformat(),'time_range_utc':[datetime.fromtimestamp(timestamp,tz=timezone.utc).isoformat()]*2,
            'dataset':source_info(source),'calculation':'SPICE LT+S vectors, spherical topocentric ENU and 48-strip angular disk quadrature against sampled terrain skyline',
            'coverage':profile['coverage'],'categories':{'terrain':'REAL DATA','ephemeris':'CALCULATED','disk_and_shadow_rendering':'APPROXIMATION','hardware':'USER ASSUMPTIONS'},
            'assumptions':'No refraction; spherical Sun/Earth; Moon-centered light-time corrections followed by observer translation, not full observer-centered relativistic corrections.',
            'height_error_at_observer_m':height_error,
            'uncertainty':'Height error is reported only where the supplied uncertainty raster is valid. Pixel spacing and 1-degree rays cannot resolve all terrain hazards.'}}
