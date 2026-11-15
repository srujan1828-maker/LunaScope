"""Reactive mission-window matching using computed, explicitly simulated inputs."""
from datetime import datetime, timezone
from time import perf_counter
from pydantic import Field
from app.api.schemas import EvaluateScenarioRequest
from app.data.sites_catalog import get_sites_catalog, get_site_by_id
from app.core.visibility import compute_interval_metrics
from app.core.nasa_data import provenance


class MatchRequest(EvaluateScenarioRequest):
    site_ids: list[str] = Field(default_factory=lambda: [s['site_id'] for s in get_sites_catalog()], min_length=1, max_length=20)
    min_sun_pct: float = Field(60, ge=0, le=100)
    min_earth_pct: float = Field(50, ge=0, le=100)
    max_shadow_gap_hours: float = Field(48, ge=0, le=8784)
    min_consecutive_sun_days: float = Field(0, ge=0, le=366)
    communication_required: bool = True
    require_battery_reserve: bool = False
    primary_site_id: str | None = None


def match_sites(req: MatchRequest):
    # Local import keeps the scenario API as the single computation path.
    from app.api.routes import evaluate_scenario
    started = perf_counter()
    if req.primary_site_id and not get_site_by_id(req.primary_site_id):
        raise ValueError('Unknown primary site')
    rows = []
    for sid in dict.fromkeys(req.site_ids):
        payload = req.model_dump(include=set(EvaluateScenarioRequest.model_fields))
        payload['site_ids'] = [sid]
        result = evaluate_scenario(EvaluateScenarioRequest(**payload))['evaluated_sites'][sid]
        m = result['interval_metrics']
        longest = current = 0.0
        for f, hours in zip(result['solar_fractions'], result['sample_hours']):
            current = current + hours if f >= req.sun_threshold else 0.0
            longest = max(longest, current)
        m['longest_sun_window_hours'] = round(longest, 4)
        violations = []
        if m['sun_availability_pct'] < req.min_sun_pct:
            violations.append(f"Sun coverage {m['sun_availability_pct']:.1f}% is below {req.min_sun_pct:g}%")
        if req.communication_required and m['earth_availability_pct'] < req.min_earth_pct:
            violations.append(f"Earth coverage {m['earth_availability_pct']:.1f}% is below {req.min_earth_pct:g}%")
        if m['longest_shadow_gap_hours'] > req.max_shadow_gap_hours:
            violations.append(f"Shadow gap {m['longest_shadow_gap_hours']:g}h exceeds {req.max_shadow_gap_hours:g}h")
        if longest + 1e-9 < req.min_consecutive_sun_days * 24:
            violations.append(f"Consecutive sunlight {longest / 24:.2f} days is below {req.min_consecutive_sun_days:g} days")
        power = result['power_simulation']
        if req.require_battery_reserve and (power is None or power['summary']['min_soc_pct'] < (req.power_config.reserve_margin_pct if req.power_config else 20)):
            violations.append('Battery reserve requirement is unmet or power simulation is disabled')
        weights = (0.5, 0.3, 0.2) if req.communication_required else (0.8, 0, 0.2)
        score = sum(w * m[k] for w, k in zip(weights, ['sun_availability_pct', 'earth_availability_pct', 'joint_availability_pct']))
        rows.append({'site_id': sid, 'name': result['site_info']['name'], 'passed': not violations,
                     'score': round(score, 2), 'metrics': m, 'violations': violations,
                     'explanation': '; '.join(violations) if violations else 'Meets configured constraints in this NASA-data calculation window.',
                     'terrain_safety': 'unknown', 'power_summary': power['summary'] if power else None})
    rows.sort(key=lambda r: (not r['passed'], -r['score'], r['site_id']))
    passing = [r for r in rows if r['passed']]
    primary = next((r for r in rows if r['site_id'] == req.primary_site_id), None)
    recommended = primary if primary and primary['passed'] else (passing[0] if passing else None)
    return {'generated_at_utc': datetime.now(timezone.utc).isoformat(), 'runtime_ms': round((perf_counter()-started)*1000, 2),
            'inputs': req.model_dump(), 'rankings': rows, 'evaluated_count': len(rows), 'passing_count': len(passing),
            'recommended_primary': recommended, 'backup_sites': [r for r in passing if not recommended or r['site_id'] != recommended['site_id']],
            'provenance': provenance(),
            'sampling': 'Hourly left-endpoint intervals, clipped at mission end; transitions may differ by up to one sample.'}
