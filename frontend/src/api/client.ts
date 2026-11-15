import {
  LandingSite,
  ScenarioEvaluationResult,
  WindowSearchResult,
  ContingencyResult,
} from '../types';

const BASE_URL = (import.meta as any).env?.VITE_API_URL || '';
function detailMessage(detail:unknown,fallback:string){return typeof detail==='string'?detail:Array.isArray(detail)?detail.map(item=>item.msg||'Invalid request').join('; '):fallback;}

export async function fetchSites(): Promise<LandingSite[]> {
  const res = await fetch(`${BASE_URL}/api/sites`);
  if (!res.ok) throw new Error(`Failed to fetch sites: ${res.statusText}`);
  return res.json();
}

export async function evaluateScenario(payload: {
  site_ids: string[];
  start_time_iso: string;
  end_time_iso: string;
  mast_height_m: number;
  antenna_margin_deg: number;
  sun_threshold: number;
  power_config?: any;
}, signal?:AbortSignal): Promise<ScenarioEvaluationResult> {
  const res = await fetch(`${BASE_URL}/api/scenarios/evaluate`, {signal,
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(detailMessage(err.detail,'Evaluation failed'));
  }
  return res.json();
}

export async function searchMissionWindows(payload: {
  site_ids: string[];
  search_start_iso: string;
  search_end_iso: string;
  mission_duration_days: number;
  stride_hours: number;
  min_sun_pct: number;
  max_shadow_gap_hours: number;
  min_earth_pct: number;
  max_earth_outage_hours: number;
  min_joint_pct: number;
  priority: string;
  mast_height_m: number;
}, signal?:AbortSignal): Promise<WindowSearchResult> {
  const res = await fetch(`${BASE_URL}/api/windows/search`, {signal,
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(detailMessage(err.detail,'Search failed'));
  }
  return res.json();
}

export async function runContingencyAnalysis(payload: {
  primary_site_id: string;
  year: number;
  min_sun_days: number;
  min_joint_days: number;
}): Promise<ContingencyResult> {
  const res = await fetch(`${BASE_URL}/api/contingency/evaluate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(detailMessage(err.detail,'Contingency analysis failed'));
  }
  return res.json();
}

export async function saveScenario(payload: any): Promise<{ scenario_id: string }> {
  const res = await fetch(`${BASE_URL}/api/scenarios`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to save scenario');
  return res.json();
}

export function getExportUrl(scenarioId: string, format: 'json' | 'csv'): string {
  return `${BASE_URL}/api/export/${scenarioId}/${format}`;
}
