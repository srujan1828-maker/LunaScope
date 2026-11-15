import {useEffect, useRef, useState} from 'react';
import {LandingSite, PowerConfig, ScenarioEvaluationResult} from './types';
import {fetchSites, evaluateScenario} from './api/client';
import {restoreValue,restoreMission,restorePower} from './settings';

export const API = import.meta.env.VITE_API_URL || '';
export type Mission = {start: string; utcTime?:string; days: number; sunlight: number; earth: number; mast: number; margin: number; comms: boolean; terrain: string};
export type Ranking = {site_id:string; name:string; passed:boolean; score:number; explanation:string; terrain_safety:string; metrics:{sun_availability_pct:number; earth_availability_pct:number; joint_availability_pct:number; longest_shadow_gap_hours:number; longest_sun_window_hours:number}};
export type Matches = {rankings:Ranking[]; passing_count:number; evaluated_count:number; runtime_ms:number; recommended_primary:Ranking|null; backup_sites:Ranking[]};
export const powerDefaults:PowerConfig={enabled:true,panel_area_m2:3.5,panel_efficiency:.28,panel_orientation:'tracking',spacecraft_load_w:120,battery_capacity_wh:2400,initial_soc_pct:100,reserve_margin_pct:20};
export const initialMission:Mission={start:'2027-01-01',days:14,sunlight:7,earth:50,mast:2,margin:0,comms:true,terrain:'unassessed'};
export function stored<T>(key:string, fallback:T,restore:(value:unknown,fallback:T)=>T=restoreValue):T {try{return restore(JSON.parse(localStorage.getItem(key)||'null')??fallback,fallback);}catch{return fallback;}}
export function useStored<T>(key:string, initial:T,restore?:(value:unknown,fallback:T)=>T) {const [value,setValue]=useState<T>(()=>stored(key,initial,restore));useEffect(()=>{try{localStorage.setItem(key,JSON.stringify(value));}catch{/* Storage is optional. */}},[key,value]);return [value,setValue] as const;}
export function missionStart(m:Mission){const t=m.utcTime||'00:00:00';return m.start+'T'+(t.length===5?t+':00':t)+'Z';}
export function missionEnd(m:Mission){return new Date(new Date(missionStart(m)).getTime()+m.days*86400000).toISOString();}
export function useMission(){
  const [mission,setMission]=useStored('lunascope.mission.v4',initialMission,restoreMission);
  const [primary,setPrimary]=useStored('lunascope.primary.v4','lola-sp-001');
  const [backups,setBackups]=useStored<string[]>('lunascope.backups.v4',[]);
  const [compare,setCompare]=useStored<string[]>('lunascope.compare.v4',['lola-sp-002']);
  const [power,setPower]=useStored('lunascope.power.v4',powerDefaults,restorePower);
  const [sites,setSites]=useState<LandingSite[]>([]);
  const [selected,setSelected]=useState(primary);
  const [matches,setMatches]=useState<Matches|null>(null);
  const [evaluation,setEvaluation]=useState<ScenarioEvaluationResult|null>(null);
  const [busy,setBusy]=useState(false),[chartBusy,setChartBusy]=useState(false);
  const [error,setError]=useState(''),[chartError,setChartError]=useState('');
  const [catalogError,setCatalogError]=useState('');
  const [refresh,setRefresh]=useState(0),[connection,setConnection]=useState('Connecting');
  const [enabled,setEnabled]=useState(false);
  const revision=useRef(0);
  useEffect(()=>{
    let active=true;
    fetchSites().then(value=>{
      if(!active)return;
      if(!value.length)throw new Error('No measured locations are available. Retry when the NASA catalog is ready.');
      const valid=new Set(value.map(s=>s.site_id));
      setSites(value);setCatalogError('');
      setPrimary(prev=>valid.has(prev)?prev:value[0].site_id);
      setSelected(prev=>valid.has(prev)?prev:value[0].site_id);
      setCompare(prev=>prev.filter(id=>valid.has(id)));setBackups(prev=>prev.filter(id=>valid.has(id)));
    }).catch(e=>{if(active)setCatalogError(e.message);});
    return()=>{active=false;};
  },[refresh]);
  useEffect(()=>{
    if(!enabled||!sites.length||catalogError)return;
    const rev=++revision.current;setBusy(true);setError('');setMatches(null);
    const controller=new AbortController();let ws:WebSocket|undefined;let deadline:ReturnType<typeof setTimeout>;let fallback=false;let received=false;
    const timer=setTimeout(()=>{
      let end:string;
      try{end=missionEnd(mission);}catch{setError('Choose a valid mission date and duration.');setBusy(false);return;}
      const parameters={start_time_iso:missionStart(mission),end_time_iso:end,mast_height_m:mission.mast,antenna_margin_deg:mission.margin,
        min_consecutive_sun_days:mission.sunlight,min_sun_pct:0,min_earth_pct:mission.earth,communication_required:mission.comms,
        max_shadow_gap_hours:8784,primary_site_id:primary,power_config:power};
      const accept=(value:Matches)=>{if(revision.current!==rev||controller.signal.aborted)return;clearTimeout(deadline);received=true;setMatches(value);setBusy(false);};
      const fail=(message:string)=>{if(revision.current===rev&&!controller.signal.aborted){setError(message);setBusy(false);}};
      async function requestHTTP(){if(fallback||controller.signal.aborted)return;fallback=true;setConnection('HTTP connected');try{
        const response=await fetch(`${API}/api/matches/evaluate`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(parameters),signal:controller.signal});
        const body=await response.json();if(!response.ok)throw new Error(typeof body.detail==='string'?body.detail:'Check mission values: duration 1–366 days, mast 0.5–30 m, visibility 0–100%.');accept(body);
      }catch(e){fail(String(e));}}
      const base=API||location.origin;ws=new WebSocket(base.replace(/^http/,'ws')+'/api/ws/matches');
      deadline=setTimeout(()=>{ws?.close();void requestHTTP();},120000);
      ws.onopen=()=>{setConnection('Live matching connected');ws?.send(JSON.stringify({revision:rev,parameters}));};
      ws.onmessage=e=>{const message=JSON.parse(e.data);if(message.revision!==rev)return;clearTimeout(deadline);if(message.type==='match_result')accept(message.result);else fail(message.message);};
      ws.onerror=()=>{void requestHTTP();};
      ws.onclose=()=>{if(!controller.signal.aborted&&!received)void requestHTTP();};
    },450);
    return()=>{clearTimeout(timer);clearTimeout(deadline);controller.abort();ws?.close();++revision.current;};
  },[mission,primary,power,refresh,enabled,sites.length,catalogError]);
  const ids=[primary,...compare.filter(id=>id!==primary)].slice(0,3);
  const idsKey=ids.join(',');
  useEffect(()=>{
    if(!enabled||!sites.length||catalogError)return;const controller=new AbortController();let active=true;setChartBusy(true);setChartError('');setEvaluation(null);
    const timer=setTimeout(()=>{let end:string;try{end=missionEnd(mission);}catch{setChartBusy(false);return;}
      evaluateScenario({site_ids:idsKey.split(','),start_time_iso:missionStart(mission),end_time_iso:end,mast_height_m:mission.mast,antenna_margin_deg:mission.margin,sun_threshold:.1,power_config:power},controller.signal)
        .then(value=>{if(active)setEvaluation(value);}).catch(e=>{if(active){setChartError(e.message);setEvaluation(null);}}).finally(()=>{if(active)setChartBusy(false);});
    },500);return()=>{active=false;controller.abort();clearTimeout(timer);};
  },[idsKey,mission.start,mission.utcTime,mission.days,mission.mast,mission.margin,power,enabled,refresh,sites.length,catalogError]);
  const update=<K extends keyof Mission>(key:K,value:Mission[K])=>setMission(prev=>({...prev,[key]:value}));
  const setAsPrimary=(id:string)=>{setPrimary(id);setSelected(id);setBackups(prev=>prev.filter(x=>x!==id));};
  const toggleCompare=(id:string)=>{if(id===primary)return;setCompare(prev=>{const extras=prev.filter(x=>x!==primary);return extras.includes(id)?extras.filter(x=>x!==id):[...extras.slice(-1),id];});};
  const toggleBackup=(id:string)=>{if(id!==primary)setBackups(prev=>prev.includes(id)?prev.filter(x=>x!==id):[...prev,id]);};
  const rank=(id:string)=>matches?.rankings.find(r=>r.site_id===id);
  const status=(id:string)=>mission.terrain!=='unassessed'?'UNKNOWN':(rank(id)?(rank(id)!.passed?'PASSING':'FAILING'):'UNEVALUATED');
  return {mission,update,setMission,primary,setAsPrimary,backups,toggleBackup,compare,toggleCompare,ids,sites,selected,setSelected,matches,evaluation,busy,chartBusy,error:catalogError||error,chartError,power,setPower,rank,status,connection,
    analyze:()=>{setEnabled(true);setRefresh(x=>x+1);},activate:()=>setEnabled(true)};
}
export type MissionState=ReturnType<typeof useMission>;
