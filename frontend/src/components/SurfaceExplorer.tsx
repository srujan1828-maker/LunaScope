import {useEffect,useRef,useState} from 'react';
import {Play,Pause,SkipBack,SkipForward,RotateCcw,Download,Compass,Sun,Globe,ArrowUpRight} from 'lucide-react';
import {API,MissionState,missionStart} from '../mission';
import {TerrainViewport} from './TerrainViewport';
import {MoonGlobe} from './MoonGlobe';
import type {TerrainCrop,TerrainSource,SurfaceFrame,PickedPoint} from './surfaceTypes';

async function json(url:string,init?:RequestInit){const res=await fetch(API+url,init);const body=await res.json();if(!res.ok)throw new Error(typeof body.detail==='string'?body.detail:'Scientific data could not be evaluated. Check location, UTC and installed inputs.');return body;}
const labels=['Unknown','Sun visible · Earth visible','Sun visible · Earth blocked','Sun below threshold · Earth visible','Sun below threshold · Earth blocked'];
const numeric=(value:number|null|undefined,digits=2,suffix='')=>value==null||!Number.isFinite(value)?'Unknown':value.toFixed(digits)+suffix;

export function ScientificHorizon({frame,compact=false}:{frame:SurfaceFrame;compact?:boolean}){
  const [inspect,setInspect]=useState<number|null>(null);
  const h=frame.horizon.elevations_deg;
  const values=[...h,frame.sun.elevation_deg-frame.sun.angular_radius_deg,frame.earth.elevation_deg-frame.earth.angular_radius_deg,frame.sun.elevation_deg+1,frame.earth.elevation_deg+1].filter((v):v is number=>v!==null);
  const low=Math.min(-4,...values)-.5,high=Math.max(8,...values)+.5,y=(v:number)=>180-(v-low)/(high-low)*155;
  let gap=true;const path=h.concat(h[0]).map((v,i)=>{if(v==null){gap=true;return '';}const command=gap?'M':'L';gap=false;return `${command}${35+i*2.55},${y(v)}`;}).join(' ');
  const obstruction=inspect===null?null:frame.horizon.obstruction_points[inspect];
  return <div className={compact?'scientific-horizon compact-horizon':'scientific-horizon'}>
    <svg viewBox="0 0 1000 215" role="img" aria-label="Measured 360 degree terrain horizon, Sun and Earth disk positions" onPointerMove={e=>{const rect=e.currentTarget.getBoundingClientRect();setInspect(Math.max(0,Math.min(359,Math.round(((e.clientX-rect.left)/rect.width*1000-35)/2.55))));}} onPointerLeave={()=>setInspect(null)}>
      {[0,.25,.5,.75,1].map(f=><g key={f}><path d={`M35 ${25+f*155}H953`} stroke="#ffffff12"/><text x="30" y={29+f*155} textAnchor="end" fill="#929fac" fontSize="10">{numeric(high-f*(high-low),1)}°</text></g>)}
      {[0,60,120,180,240,300,360].map(a=><g key={a}><path d={`M${35+a*2.55} 25V180`} stroke="#ffffff0b"/><text x={35+a*2.55} y="204" textAnchor="middle" fill="#929fac" fontSize="10">{a}°</text></g>)}
      <path d={path} stroke="#abb4a6" strokeWidth="1.3" fill="none"/>
      {[[frame.sun,'#dfb665','Sun'],[frame.earth,'#63c9c0','Earth']] .map(([body,color,label])=>{const b=body as SurfaceFrame['sun'];return <g key={String(label)}><ellipse cx={35+b.azimuth_deg*2.55} cy={y(b.elevation_deg)} rx={Math.max(2,b.angular_radius_deg*2.55/Math.cos(b.elevation_deg*Math.PI/180))} ry={Math.max(2,b.angular_radius_deg/(high-low)*155)} fill={String(color)} fillOpacity=".7"/><text x={40+b.azimuth_deg*2.55} y={y(b.elevation_deg)-10} fill={String(color)} fontSize="11">{String(label)}</text></g>;})}
      {inspect!==null&&<path d={`M${35+inspect*2.55} 20V180`} stroke="#d8b36a" strokeDasharray="3 3"/>}
    </svg>
    {!compact&&<p className="chart-caption">{obstruction?`${inspect}°: horizon ${numeric(obstruction.horizon_elevation_deg,2,'°')} · blocker ${numeric(obstruction.distance_m==null?null:obstruction.distance_m/1000,2,' km')} away · ${numeric(obstruction.lat_deg,5,'°')}, ${numeric(obstruction.lon_deg,5,'°E')}`:'Move across the chart to inspect the measured obstruction. Azimuth is clockwise from local north; gaps mean missing terrain.'}</p>}
  </div>;
}

export function SurfaceExplorer({state,onPower,onDispersion,onMast}:{state:MissionState;onPower:()=>void;onDispersion:()=>void;onMast:()=>void}){
  const primary=state.sites.find(s=>s.site_id===state.selected);
  const [point,setPoint]=useState<PickedPoint|null>(null),[source,setSource]=useState('lola80'),[sources,setSources]=useState<TerrainSource[]>([]);
  const center=point||primary;
  const start=new Date(missionStart(state.mission)).getTime()/1000;
  const [time,setTime]=useState(start),[playing,setPlaying]=useState(false),[speed,setSpeed]=useState(600),[step,setStep]=useState(600);
  const [mesh,setMesh]=useState<TerrainCrop|null>(null),[frames,setFrames]=useState<Record<string,SurfaceFrame>>({});
  const [loading,setLoading]=useState(false),[terrainLoading,setTerrainLoading]=useState(false),[error,setError]=useState(''),[terrainError,setTerrainError]=useState('');
  const [width,setWidth]=useState(25.6),[view,setView]=useState<'orbit'|'ground'|'sun'|'earth'>('orbit'),[colored,setColored]=useState(false),[compare,setCompare]=useState(false);
  const [picked,setPicked]=useState<PickedPoint|null>(null);const sequence=useRef(0);
  const [inspectionLight,setInspectionLight]=useState(true);
  const [wholeMoon,setWholeMoon]=useState(true);
  const latitude=center?.lat_deg,longitude=center?.lon_deg,candidate=frames[state.primary];
  const frame=candidate&&latitude!=null&&longitude!=null&&Math.abs(candidate.location.lat_deg-latitude)<1e-7&&Math.abs((candidate.location.lon_deg-longitude+540)%360-180)<1e-7?candidate:null;
  const ids=(compare?state.ids:[state.primary]).join(',');
  useEffect(()=>{json('/api/terrain/sources').then(setSources).catch(e=>setTerrainError(e.message));},[]);
  useEffect(()=>{setPoint(null);setPicked(null);setSource('lola80');setPlaying(false);},[state.primary]);
  useEffect(()=>{setTime(start);setPlaying(false);},[start]);
  useEffect(()=>{
    if(latitude==null||longitude==null)return;const controller=new AbortController();let active=true;setMesh(null);setTerrainLoading(true);setTerrainError('');
    const load=async()=>{
      try{const query=`lat_deg=${latitude}&lon_deg=${longitude}&width_km=${width}&source=${encodeURIComponent(source)}`;
        const coarse=await json('/api/terrain/crop?'+query+'&samples=33',{signal:controller.signal});if(active)setMesh(coarse);
        const fine=await json('/api/terrain/crop?'+query+'&samples=257',{signal:controller.signal});if(active)setMesh(fine);
      }catch(e){if(active)setTerrainError(String(e));}finally{if(active)setTerrainLoading(false);}
    };void load();return()=>{active=false;controller.abort();};
  },[latitude,longitude,width,source]);
  useEffect(()=>{
    if(latitude==null||longitude==null)return;const controller=new AbortController();const revision=++sequence.current;setLoading(true);setError('');
    const requests=ids.split(',').map(async id=>{
      const site=state.sites.find(s=>s.site_id===id);const lat=id===state.primary?latitude:site?.lat_deg,lon=id===state.primary?longitude:site?.lon_deg;
      if(lat==null||lon==null)return null;
      const body=await json('/api/surface/frame',{method:'POST',headers:{'Content-Type':'application/json'},signal:controller.signal,
        body:JSON.stringify({lat_deg:lat,lon_deg:lon,time_iso:new Date(time*1000).toISOString(),mast_height_m:state.mission.mast,source:id===state.primary?source:'lola80'})});return [id,body] as const;
    });
    Promise.all(requests).then(rows=>{if(sequence.current===revision&&!controller.signal.aborted)setFrames(Object.fromEntries(rows.filter((r):r is readonly [string,SurfaceFrame]=>r!==null)));})
      .catch(e=>{if(!controller.signal.aborted){setError(String(e));setPlaying(false);setFrames({});}}).finally(()=>{if(!controller.signal.aborted)setLoading(false);});
    return()=>controller.abort();
  },[latitude,longitude,source,time,state.mission.mast,ids,state.sites]);
  useEffect(()=>{
    if(!playing||loading||!frame)return;
    const timer=setTimeout(()=>setTime(t=>t+speed*.35),350);return()=>clearTimeout(timer);
  },[playing,loading,frame,speed]);
  const chooseTime=(t:number)=>{if(Number.isFinite(t)){setPlaying(false);setTime(t);}};
  const selectSource=(id:string)=>{const info=sources.find(s=>s.id===id);setSource(id);if(info?.center_lat_deg!=null&&info.center_lon_deg!=null){setPoint({lat_deg:info.center_lat_deg,lon_deg:info.center_lon_deg,elevation_m:0,uncertainty_m:null});setWidth(1.28);}else{setPoint(null);setWidth(25.6);}};
  const download=()=>{if(!frame)return;const blob=new Blob([JSON.stringify(frame,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='lunascope-surface-reading.json';a.click();URL.revokeObjectURL(url);};
  const currentEvaluation=state.evaluation?.evaluated_sites[state.primary];
  const end=start+state.mission.days*86400;
  return <>
    <section className="panel surface-explorer" aria-label="Data driven 3D lunar surface simulator">
      <div className="panel-heading"><div><span className="eyebrow">MEASURED TERRAIN / LIVE GEOMETRY</span><h3>Lunar surface explorer</h3></div><span className="data-label">1:1 ELEVATION SCALE</span></div>
      <div className="surface-settings">
        <label className="field">Analysis location<select aria-label="Surface location" value={state.selected} onChange={e=>state.setAsPrimary(e.target.value)}>{state.sites.map(s=><option key={s.site_id} value={s.site_id}>{s.name}</option>)}</select></label>
        <label className="field">Terrain source<select aria-label="Surface terrain source" value={source} onChange={e=>selectSource(e.target.value)}>{sources.map(s=><option key={s.id} value={s.id}>{s.dataset} · {s.pixel_scale_m} m</option>)}</select></label>
        <label className="field">Displayed region<select aria-label="Terrain crop width" value={width} onChange={e=>setWidth(Number(e.target.value))}>{[1.28,6.4,12.8,25.6].map(w=><option key={w} value={w}>{w} km across</option>)}</select></label>
        <label className="field">Observer mast (m)<input aria-label="Surface observer mast" type="number" min=".5" max="30" step=".5" value={state.mission.mast} onChange={e=>{if(e.target.valueAsNumber>=.5&&e.target.valueAsNumber<=30)state.update('mast',e.target.valueAsNumber);}}/></label>
      </div>
      <div className="moon-mode-tabs"><button className={`button compact ${wholeMoon?'primary':'secondary'}`} onClick={()=>setWholeMoon(true)}>Whole Moon</button><button className={`button compact ${!wholeMoon?'primary':'secondary'}`} onClick={()=>setWholeMoon(false)}>Local surface</button><span>Full globe or detailed south-pole terrain</span></div>
      <div className="terrain-stage">{wholeMoon?<MoonGlobe frame={frame} lat={latitude??-90} lon={longitude??0}/>:<TerrainViewport mesh={mesh} frame={frame} onPick={setPicked} view={view} colored={colored} inspectionLight={inspectionLight}/>}
        {!wholeMoon&&<div className="terrain-caption"><span>{terrainLoading?'Loading terrain detail…':mesh?`${mesh.samples} × ${mesh.samples} measured/interpolated grid samples`:'Terrain unavailable'}</span><strong>{mesh?.source.dataset||'NASA LOLA'}</strong><span>North: teal arrow · East: gold arrow</span></div>}
        {!wholeMoon&&<div className="terrain-view-buttons">{(['orbit','ground','sun','earth'] as const).map(v=><button key={v} className={`button compact ${view===v?'primary':'secondary'}`} onClick={()=>setView(v)}>{v==='orbit'?'Orbit terrain':v==='ground'?'Observer view':v==='sun'?'Look at Sun':'Look at Earth'}</button>)}</div>}
        {picked&&<div className="terrain-pick"><span className="eyebrow">NEAREST DISPLAYED DEM SAMPLE</span><strong>{numeric(picked.lat_deg,5)}° / {numeric(picked.lon_deg,5)}° E</strong><span>{numeric(picked.elevation_m,1)} m elevation · height error {numeric(picked.uncertainty_m,2,' m')}</span><button className="text-link" onClick={()=>{setPoint(picked);setPicked(null);setPlaying(false);}}>Analyze this location <ArrowUpRight size={13}/></button></div>}
      </div>
      {wholeMoon&&<p className="chart-caption">Whole-Moon context: NASA SVS LROC color mosaic (visualization-optimized) and global LOLA elevation overview. The detailed 80 m south-pole data remains the analysis source. <a href="https://svs.gsfc.nasa.gov/4720/" target="_blank" rel="noreferrer">NASA source & credits</a></p>}
      {(terrainError||error)&&<p className="error-message" role="alert">{terrainError||error}</p>}
      <div className="terrain-legend"><label><input type="checkbox" checked={colored} onChange={e=>setColored(e.target.checked)}/> Elevation colors</label><label><input type="checkbox" aria-label="Inspection fill light" checked={inspectionLight} onChange={e=>setInspectionLight(e.target.checked)}/> Inspection fill light</label><span className="height-gradient"/><span>{numeric(mesh?.elevation_range_m[0],0)} to {numeric(mesh?.elevation_range_m[1],0)} m</span><span>DEM {mesh?.source.pixel_scale_m??'—'} m/pixel · mesh {numeric(mesh?.mesh_spacing_m,0)} m · known terrain {numeric(mesh?mesh.coverage_fraction*100:null,1)}%</span></div>
      <p className="chart-caption">Drag to orbit · wheel to zoom · shift-drag to pan · click terrain to inspect. Shapes come from elevation data. Lighting and local shadow maps use the calculated Sun direction; shadows are limited to the displayed crop. Soft edges and a small viewing fill light are visual approximations. Sky disks use their calculated angular sizes; Earth is a phase-lit sphere, without weather imagery.</p>
      <div className="surface-time-controls">
        <label className="field">Simulation date & time (UTC)<input aria-label="Surface UTC time" type="datetime-local" step="1" min="2025-01-01T00:00:00" max="2032-12-31T23:59:59" value={new Date(time*1000).toISOString().slice(0,19)} onChange={e=>chooseTime(new Date(e.target.value+'Z').getTime()/1000)}/></label>
        <div className="surface-transport"><button className="icon-button" aria-label="Step surface backward" onClick={()=>chooseTime(time-step)}><SkipBack size={17}/></button><button className="button primary compact" disabled={!frame||!!error} onClick={()=>setPlaying(v=>!v)} aria-label={playing?'Pause surface simulation':'Play surface simulation'}>{playing?<Pause size={16}/>:<Play size={16}/>}</button><button className="icon-button" aria-label="Step surface forward" onClick={()=>chooseTime(time+step)}><SkipForward size={17}/></button><button className="icon-button" aria-label="Reset surface time" onClick={()=>chooseTime(start)}><RotateCcw size={16}/></button></div>
        <label className="field">Time step<select aria-label="Surface time step" value={step} onChange={e=>setStep(+e.target.value)}>{[60,600,3600,21600].map(s=><option key={s} value={s}>{s<3600?s/60+' min':s/3600+' h'}</option>)}</select></label>
        <label className="field">Playback speed<select aria-label="Surface playback speed" value={speed} onChange={e=>setSpeed(+e.target.value)}>{[60,600,3600,21600].map(s=><option key={s} value={s}>{s}×</option>)}</select></label>
      </div>
      <div className="surface-timestamp" role="status">{loading?'Computing requested time… ':''}{frame?'Displayed scene & readings: '+frame.utc.replace('T',' '):'Readings unavailable'}<button className="text-link" disabled={!frame} onClick={download}><Download size={13}/> Export readings & provenance</button></div>
      <input className="surface-time-range" aria-label="Surface mission time" type="range" min={start} max={end} step="60" value={Math.max(start,Math.min(end,time))} onChange={e=>chooseTime(+e.target.value)}/>
    </section>
    <div className="surface-readings">{[
      ['Sun elevation',numeric(frame?.sun.elevation_deg,3,'°')],['Sun azimuth',numeric(frame?.sun.azimuth_deg,3,'°')],['Solar disk exposed',numeric(frame?.sun.visible_fraction==null?null:frame.sun.visible_fraction*100,2,'%')],
      ['Earth-center elevation',numeric(frame?.earth.elevation_deg,3,'°')],['Earth azimuth',numeric(frame?.earth.azimuth_deg,3,'°')],['Earth center clears terrain',frame?.earth.center_visible==null?'Unknown':frame.earth.center_visible?'Yes':'No'],
      ['Visible Earth disk',numeric(frame?.earth.visible_disk_fraction==null?null:frame.earth.visible_disk_fraction*100,2,'%')],['Entire Earth disk clear',frame?.earth.complete_disk_visible==null?'Unknown':frame.earth.complete_disk_visible?'Yes':'No'],
      ['Local elevation',numeric(frame?.location.elevation_m,1,' m')],['Sun terrain horizon',numeric(frame?.sun.horizon_elevation_deg,3,'°')],['Earth terrain horizon',numeric(frame?.earth.horizon_elevation_deg,3,'°')],['Earth illuminated phase',numeric(frame?.earth.illuminated_fraction==null?null:frame.earth.illuminated_fraction*100,1,'%')]
    ].map(([label,value])=><div className="panel" key={label}><span>{label}</span><strong>{value}</strong></div>)}</div>
    <div className="surface-state"><span className={`status ${frame?.state===1?'passing':'unknown'}`}>{labels[frame?.state??0]}</span><span>Sun threshold: 10% of disk · Earth-center visibility is geometry; a communications link remains unverified.</span></div>
    {frame&&<section className="panel skyline-panel"><div className="panel-heading"><div><span className="eyebrow">360° MEASURED TERRAIN HORIZON</span><h3>{point?'Selected surface location':primary?.name}</h3></div><span className="data-label">{numeric(frame.horizon.known_azimuth_fraction*100,1)}% KNOWN AZIMUTHS</span></div><ScientificHorizon frame={frame}/><p className="chart-caption">{frame.horizon.compass_convention} {frame.horizon.reference_meridian_deg!==null&&`Reference meridian: ${frame.horizon.reference_meridian_deg}° E.`} Rays extend 150 km. Angular sampling is 1°; narrow ridges can be missed.</p></section>}
    <section className="panel surface-comparison"><div className="panel-heading"><div><span className="eyebrow">SYNCHRONIZED SITE COMPARISON</span><h3>Same time. Different terrain.</h3></div><label><input type="checkbox" aria-label="Compare surface locations" checked={compare} onChange={e=>setCompare(e.target.checked)}/> Compare selected sites</label></div>
      <p className="chart-caption">Select up to three locations in the planner. Horizons and sky readings share one UTC; period metrics cover the configured mission window. {point?'The picked-point view uses its own horizon; catalog period metrics below retain their labeled catalog location.':''}</p>
      <div className="surface-compare-grid">{(compare?state.ids:[state.primary]).map(id=>{
        const f=frames[id],data=state.evaluation?.evaluated_sites[id],m=data?.interval_metrics;return <article key={id}><h4>{state.sites.find(s=>s.site_id===id)?.name}</h4>{f&&<ScientificHorizon frame={f} compact/>}<dl>
          <div><dt>Sun / Earth elevation now</dt><dd>{numeric(f?.sun.elevation_deg,2,'°')} / {numeric(f?.earth.elevation_deg,2,'°')}</dd></div>
          <div><dt>Terrain elevation</dt><dd>{numeric(data?.site_info.elevation_m,1,' m')}</dd></div>
          <div><dt>Mission Sun / Earth / joint</dt><dd>{numeric(m?.sun_availability_pct,1,'%')} / {numeric(m?.earth_availability_pct,1,'%')} / {numeric(m?.joint_availability_pct,1,'%')}</dd></div>
          <div><dt>Longest shadow / Earth outage</dt><dd>{numeric(m?.longest_shadow_gap_hours,2,' h')} / {numeric(m?.longest_earth_outage_hours,2,' h')}</dd></div>
          <div><dt>Equivalent full-Sun exposure</dt><dd>{numeric(m?.equivalent_sun_hours,2,' h')}</dd></div>
          <div><dt>Minimum battery / unmet demand</dt><dd>{numeric(data?.power_simulation?.summary.min_soc_pct,1,'%')} / {numeric(data?.power_simulation?.summary.total_unmet_demand_wh,1,' Wh')}</dd></div>
          <div><dt>Coverage / height uncertainty</dt><dd>{m?.coverage??'Computing'} / Unknown</dd></div></dl>
          {data&&<svg viewBox="0 0 600 130" role="img" aria-label={`Synchronized Sun, Earth and joint timeline for ${data.site_info.name}`} onClick={e=>{const rect=e.currentTarget.getBoundingClientRect();chooseTime(start+(e.clientX-rect.left)/rect.width*(end-start));}}>
            {[data.solar_fractions,data.dte_visibility,data.operational_states.map(v=>v===1?1:0)].map((arr,j)=><path key={j} d={arr.map((v,i)=>i%Math.max(1,Math.floor(arr.length/500))===0?`${i?'L':'M'}${(data.timestamps[i]-start)/(end-start)*600},${35+j*40-v*28}`:'').join(' ')} fill="none" stroke={['#d8b36a','#63c9c0','#a0adcc'][j]} strokeWidth="1.2"/>)}
            <path d={`M${(time-start)/(end-start)*600} 0V125`} stroke="#f5f5f5" strokeDasharray="3 3"/>
          </svg>}<p className="chart-caption">Gold: Sun · teal: Earth · silver: joint. Click a timeline to seek. Unknown = no certified height-error product for this regional grid.</p></article>;
      })}</div>
      {state.evaluation?.comparative_insights.map(text=><p className="chart-caption" key={text}>{text}</p>)}
      {state.chartBusy&&<p className="chart-caption">Computing mission-period metrics… Live scene geometry is available independently.</p>}{state.chartError&&<p className="error-message">{state.chartError}</p>}
    </section>
    <div className="surface-tools"><button className="button secondary" onClick={onPower}>Power & battery model <ArrowUpRight size={14}/></button><button className="button secondary" onClick={onMast}>Mast sensitivity <ArrowUpRight size={14}/></button><button className="button secondary" onClick={onDispersion}>Landing dispersion <ArrowUpRight size={14}/></button></div>
    {frame&&<details className="panel surface-provenance"><summary>Scientific provenance, coverage & assumptions</summary><dl>{Object.entries(frame.provenance).map(([key,value])=><div key={key}><dt>{key.replace(/_/g,' ')}</dt><dd>{typeof value==='string'?value:JSON.stringify(value)}</dd></div>)}</dl></details>}
  </>;
}
