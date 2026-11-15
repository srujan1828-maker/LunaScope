"""No DSN schedule feed is integrated; network availability cannot be inferred from lunar libration."""
def evaluate_dsn_coverage(unix_time,subearth_lat_deg,subearth_lon_deg,lander_dte_los):
    return {'timestamp_unix':unix_time,'lander_dte_los':lander_dte_los,'active_stations_count':None,
        'active_stations':[],'is_network_closed':None,'stations':{},'status':'unknown',
        'reason':'No authoritative DSN scheduling or station link-budget dataset is connected. Earth-center visibility is computed separately from NASA SPICE.'}
