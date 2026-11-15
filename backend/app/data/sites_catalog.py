"""Dataset-derived locations from actual NASA LOLA cells; no fabricated annual table."""
from pathlib import Path
import json
from functools import lru_cache
from copy import deepcopy
from app.core.nasa_data import DataUnavailable
@lru_cache(maxsize=1)
def _catalog():
    path=Path(__file__).with_name('nasa_sites.json')
    if not path.exists():raise DataUnavailable('Prepare the official NASA data before requesting analysis locations')
    return json.loads(path.read_text(encoding='utf-8'))
def get_sites_catalog():return deepcopy(_catalog())
def get_site_by_id(site_id):return next((s for s in get_sites_catalog() if s['site_id']==site_id),None)
