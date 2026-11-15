"""Bounded sub-hour visibility sampling with adaptive refinement of transitions."""
from functools import lru_cache
import numpy as np
from app.core.horizon import horizon_profile
from app.core.ephemeris import ephemeris_at_times
from app.core.visibility import fractional_solar_visibility,evaluate_dte_visibility,classify_operational_states,interpolate_horizon,compute_interval_metrics


@lru_cache(maxsize=18)
def visibility_series(lat,lon,start,end,mast=2.,margin=0.,threshold=.1,source='lola80',max_step=600.,tolerance=30.):
    if end<=start or max_step<=0 or tolerance<=0:raise ValueError('Invalid visibility sampling interval')
    profile=horizon_profile(lat,lon,mast,source=source);horizon=profile['elevations_deg']
    height=profile['observer_elevation_m']+mast
    def evaluate(times):
        eph=ephemeris_at_times(lat,lon,tuple(times),height)
        sun=fractional_solar_visibility(eph['sun_azimuth'],eph['sun_elevation'],horizon,angular_radius_deg=eph['solar_angular_radius_deg'])
        earth=evaluate_dte_visibility(eph['earth_azimuth'],eph['earth_elevation'],horizon,margin)
        return eph,sun,earth,classify_operational_states(sun,earth,threshold)
    times=np.unique(np.r_[np.arange(start,end,max_step),end])
    eph,sun,earth,states=evaluate(times)
    # Refine all changed-state and solar limb grazing intervals in batched rounds.
    records={float(t):(f,c,s) for t,f,c,s in zip(times,sun,earth,states)}
    for _ in range(8):
        ordered=sorted(records);pairs=[]
        for a,b in zip(ordered,ordered[1:]):
            fa,ca,sa=records[a];fb,cb,sb=records[b]
            grazing=(fa is not None and 0<fa<1) or (fb is not None and 0<fb<1)
            if b-a>tolerance and (sa!=sb or ca!=cb or grazing):pairs.append((a,b))
        if not pairs:break
        mid=[(a+b)/2 for a,b in pairs];_,f,c,s=evaluate(mid)
        records.update({t:(ff,cc,ss) for t,ff,cc,ss in zip(mid,f,c,s)})
    times=np.asarray(sorted(records));eph,sun,earth,states=evaluate(times)
    hours=np.r_[np.diff(times)/3600,0.]
    events=[]
    for i in range(1,len(times)):
        if states[i]!=states[i-1]:events.append({'timestamp_unix':float(times[i]),'from_state':states[i-1],'to_state':states[i],
            'bracket_seconds':float(times[i]-times[i-1])})
    return {'timestamps':times.tolist(),'ephemeris':eph,'solar_fractions':sun,'dte_visibility':earth,'operational_states':states,
        'sample_hours':hours.tolist(),'horizon_360':horizon,'horizon_profile':profile,'events':events,
        'interval_metrics':compute_interval_metrics(sun,earth,sun_threshold=threshold,sample_hours=hours),
        'sampling':{'max_step_seconds':max_step,'transition_tolerance_seconds':tolerance,'method':'10-minute baseline with bisection around changed states and solar-limb grazing',
            'limitation':'Interruptions shorter than the baseline may still be missed; event times are brackets, not exact roots.'}}


def window_metrics(series,start,end,threshold=.1):
    times=np.asarray(series['timestamps']);weights=np.maximum(0,np.minimum(np.r_[times[1:],times[-1]],end)-np.maximum(times,start))/3600
    return compute_interval_metrics(series['solar_fractions'],series['dte_visibility'],sun_threshold=threshold,sample_hours=weights)
