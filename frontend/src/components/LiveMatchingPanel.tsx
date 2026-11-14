import React, { useEffect, useRef, useState } from 'react';
import { PowerConfig } from '../types';

type MatchRow = {site_id: string; name: string; passed: boolean; score: number; explanation: string;
  metrics: {sun_availability_pct: number; earth_availability_pct: number; longest_shadow_gap_hours: number; longest_sun_window_hours: number}};
type MatchResult = {rankings: MatchRow[]; passing_count: number; evaluated_count: number; runtime_ms: number;
  recommended_primary: MatchRow | null; backup_sites: MatchRow[]; provenance: string; generated_at_utc: string};
type Props = {startDateIso: string; durationDays: number; mastHeightM: number; antennaMarginDeg: number;
  primaryId: string; powerConfig: PowerConfig; onSelect: (id: string) => void};

export function LiveMatchingPanel(props: Props) {
  const [sun, setSun] = useState(60);
  const [earth, setEarth] = useState(50);
  const [shadow, setShadow] = useState(48);
  const [consecutive, setConsecutive] = useState(0);
  const [comms, setComms] = useState(true);
  const [reserve, setReserve] = useState(false);
  const [search, setSearch] = useState('');
  const [sort, setSort] = useState<'score' | 'name' | 'sun' | 'earth'>('score');
  const [result, setResult] = useState<MatchResult | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [transport, setTransport] = useState('Connecting');
  const revision = useRef(0);
  const {startDateIso, durationDays, mastHeightM, antennaMarginDeg, primaryId, powerConfig} = props;

  useEffect(() => {
    const current = ++revision.current;
    setBusy(true); setError(''); setResult(null);
    const controller = new AbortController();
    let ws: WebSocket | undefined;
    let fallbackStarted = false;
    let timeout: ReturnType<typeof setTimeout>;
    const accept = (value: MatchResult) => {
      if (current !== revision.current || controller.signal.aborted) return;
      clearTimeout(timeout); setResult(value); setBusy(false); setError('');
    };
    const timer = setTimeout(() => {
      const start = new Date(startDateIso).getTime();
      if (!Number.isFinite(start) || !Number.isFinite(durationDays) || durationDays <= 0) {
        setError('Enter a valid mission start and positive duration.'); setBusy(false); return;
      }
      const parameters = {start_time_iso: startDateIso, end_time_iso: new Date(start+durationDays*86400000).toISOString(),
        mast_height_m: mastHeightM, antenna_margin_deg: antennaMarginDeg, primary_site_id: primaryId,
        power_config: powerConfig, min_sun_pct: sun, min_earth_pct: earth,
        max_shadow_gap_hours: shadow, min_consecutive_sun_days: consecutive,
        communication_required: comms, require_battery_reserve: reserve};
      const base = (import.meta.env.VITE_API_URL || window.location.origin).replace(/\/$/, '');
      const fallback = async () => {
        if (fallbackStarted || controller.signal.aborted) return;
        fallbackStarted = true; setTransport('HTTP fallback');
        try {
          const res = await fetch(`${base}/api/matches/evaluate`, {method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(parameters), signal: controller.signal});
          if (!res.ok) { const body = await res.json(); throw new Error(typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail)); }
          accept(await res.json());
        } catch (e) { if (current === revision.current && !controller.signal.aborted) {setError(String(e)); setBusy(false);} }
      };
      ws = new WebSocket(`${base.replace(/^http/, 'ws')}/api/ws/matches`);
      timeout = setTimeout(() => {ws?.close(); void fallback();}, 15000);
      ws.onopen = () => {setTransport('WebSocket'); ws?.send(JSON.stringify({revision: current, parameters}));};
      ws.onmessage = event => {
        const message = JSON.parse(event.data);
        if (message.revision !== current || revision.current !== current) return;
        clearTimeout(timeout);
        if (message.type === 'match_result') accept(message.result);
        else {setError(message.message || 'Matching failed'); setBusy(false);}
      };
      ws.onerror = () => {void fallback();};
    }, 400);
    return () => {clearTimeout(timer); clearTimeout(timeout); controller.abort(); ws?.close();};
  }, [startDateIso, durationDays, mastHeightM, antennaMarginDeg, primaryId, powerConfig, sun, earth, shadow, consecutive, comms, reserve]);

  const rows = (result?.rankings || []).filter(r => r.name.toLowerCase().includes(search.toLowerCase())).slice().sort((a,b) => {
    if (sort === 'name') return a.name.localeCompare(b.name);
    if (sort === 'sun') return b.metrics.sun_availability_pct-a.metrics.sun_availability_pct;
    if (sort === 'earth') return b.metrics.earth_availability_pct-a.metrics.earth_availability_pct;
    return Number(b.passed)-Number(a.passed) || b.score-a.score;
  });
  const inputClass = 'bg-slate-950 border border-slate-700 rounded px-2 py-1 w-full mt-1';
  return <section className="glass-panel rounded-2xl p-4 flex flex-col gap-3" aria-label="Live mission matching">
    <div className="flex flex-wrap justify-between gap-2"><h2 className="font-bold text-cyan-200">Live mission matching</h2>
      <span role="status" className="text-xs text-slate-400">{busy ? 'Updating matches…' : `${transport} · ${result?.runtime_ms ?? '—'} ms`}</span></div>
    <p className="text-xs text-amber-200">Demonstration analysis · procedural terrain · approximate ephemeris · terrain safety unknown. Results update when mission settings change.</p>
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
      <label>Minimum sunlight %<input className={inputClass} type="number" min="0" max="100" value={sun} onChange={e => setSun(Number(e.target.value))}/></label>
      <label>Minimum Earth visibility %<input className={inputClass} type="number" min="0" max="100" value={earth} onChange={e => setEarth(Number(e.target.value))}/></label>
      <label>Maximum shadow gap (hours)<input className={inputClass} type="number" min="0" max="8784" value={shadow} onChange={e => setShadow(Number(e.target.value))}/></label>
      <label>Consecutive sunlight (days)<input className={inputClass} type="number" min="0" max="366" value={consecutive} onChange={e => setConsecutive(Number(e.target.value))}/></label>
    </div>
    <div className="flex flex-wrap gap-4 text-xs"><label><input type="checkbox" checked={comms} onChange={e=>setComms(e.target.checked)}/> Require communications</label>
      <label><input type="checkbox" checked={reserve} onChange={e=>setReserve(e.target.checked)}/> Maintain configured battery reserve</label></div>
    {error && <p role="alert" className="text-sm text-rose-300">{error}</p>}
    {result && <><p className="text-sm">{result.passing_count} of {result.evaluated_count} sites pass · Recommended primary: <strong>{result.recommended_primary?.name || 'No site meets every constraint'}</strong></p>
      <p className="text-xs text-slate-400">Passing backups: {result.backup_sites.map(r=>r.name).join(', ') || 'None'} · Score measures modeled coverage, not probability of safe landing.</p></>}
    <div className="flex gap-3 text-xs"><input aria-label="Search matching sites" placeholder="Search sites" className={inputClass} value={search} onChange={e=>setSearch(e.target.value)}/>
      <select aria-label="Sort matches" className={inputClass} value={sort} onChange={e=>setSort(e.target.value as typeof sort)}><option value="score">Compatibility score</option><option value="name">Name</option><option value="sun">Sunlight</option><option value="earth">Earth visibility</option></select></div>
    <div className="overflow-x-auto"><table className="w-full text-xs text-left"><thead><tr className="text-slate-400"><th className="p-2">Site / result</th><th>Sun</th><th>Earth</th><th>Shadow gap</th><th>Score</th><th>Selection</th></tr></thead>
      <tbody>{rows.map(r=><tr key={r.site_id} className="border-t border-slate-800"><td className="p-2"><strong>{r.name}</strong><div className={r.passed ? 'text-emerald-300' : 'text-rose-300'}>{r.passed ? 'PASS' : 'FAIL'} · {r.explanation}</div></td>
        <td>{r.metrics.sun_availability_pct.toFixed(1)}%</td><td>{r.metrics.earth_availability_pct.toFixed(1)}%</td><td>{r.metrics.longest_shadow_gap_hours.toFixed(1)}h</td><td>{r.score.toFixed(1)}</td>
        <td><button className="px-2 py-1 border border-cyan-700 rounded" onClick={()=>props.onSelect(r.site_id)}>Set primary</button></td></tr>)}</tbody></table></div>
  </section>;
}
