import {MissionState} from '../mission';
export function MissionFeedback({state,compact=false}:{state:MissionState;compact?:boolean}){
 const r=state.rank(state.primary);
 return <section className="mission-feedback" aria-live="polite">
  <div className="integration-status"><span className="signal-dot"/>{state.connection}<span>{state.busy?'Calculating current mission…':state.matches?`${state.matches.passing_count} passing / ${state.matches.evaluated_count} evaluated`:'Waiting for evaluation'}</span></div>
  {(state.error||state.chartError)&&<p role="alert" className="error-message">{state.error||state.chartError}<button className="text-link" onClick={state.analyze}>Retry analysis</button></p>}
  {!compact&&<><h3>{state.sites.find(s=>s.site_id===state.primary)?.name||'Loading NASA catalog…'}</h3><div className="selected-metric-grid">{[['Sun available',r?.metrics.sun_availability_pct,'%'],['Earth available',r?.metrics.earth_availability_pct,'%'],['Longest sunlight',r? r.metrics.longest_sun_window_hours/24:undefined,' days'],['Longest shadow',r?.metrics.longest_shadow_gap_hours,' h']].map(([label,value,unit])=><div key={String(label)}><span>{label}</span><strong>{typeof value==='number'?value.toFixed(2)+unit:'Pending'}</strong></div>)}</div><p>{r?.explanation||'Results will appear after the current inputs have been evaluated.'}</p></>}
  <small>LOLA analysis locations are derived raster cells, not approved Artemis landing sites. Terrain safety and DSN scheduling are unassessed.</small>
 </section>;
}
