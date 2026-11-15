import React,{useEffect,useState} from 'react';
import {Moon,ArrowUpRight,Menu,X} from 'lucide-react';
import {VideoBackground} from './components/VideoBackground';
import {useMission} from './mission';
import {Home,Planner,Horizon,Timeline,Educator,Sources,Page,pageNames} from './pages';
import {WindowFinderModal} from './components/WindowFinderModal';
import {PowerSimulationDrawer} from './components/PowerSimulationDrawer';
import {ScenarioExportModal} from './components/ScenarioExportModal';
import {DispersionModal} from './components/DispersionModal';
import {MastSensitivityModal} from './components/MastSensitivityModal';
import {RealtimeSimulationBar} from './components/RealtimeSimulationBar';
const routes=Object.keys(pageNames) as Page[];
const currentPage=():Page=>{const page=location.hash.replace('#/','').split('?')[0] as Page;return routes.includes(page)?page:'home';};
export const App:React.FC=()=>{
  const state=useMission();
  const [page,setPage]=useState<Page>(currentPage),[menu,setMenu]=useState(false);
  const [modal,setModal]=useState<''|'window'|'power'|'export'|'dispersion'|'mast'>('');
  const [notice,setNotice]=useState('');
  useEffect(()=>{const change=()=>{setPage(currentPage());setMenu(false);window.scrollTo({top:0,behavior:'instant'});};window.addEventListener('hashchange',change);return()=>window.removeEventListener('hashchange',change);},[]);
  useEffect(()=>{if(page==='planner'||page==='horizon'||page==='timeline')state.activate();document.title=`${pageNames[page]} — LunaScope`;},[page]);
  const navigate=(target:Page)=>{if(target===page){window.scrollTo({top:0,behavior:'smooth'});setMenu(false);}else location.hash='/'+target;};
  const site=state.sites.find(s=>s.site_id===state.primary)||null;
  return <div className={`lunascope-app page-${page}`}><a className="skip-link" href="#main-content" onClick={e=>{e.preventDefault();document.getElementById("main-content")?.focus();}}>Skip to content</a><VideoBackground page={page}/>
    <header className="site-header"><button className="brand" aria-label="LunaScope home" onClick={()=>navigate('home')}><span className="brand-symbol"><Moon size={25} strokeWidth={1.4}/><i/></span><span>LunaScope<small>LUNAR EXPLORATION</small></span></button><nav className={menu?'nav-open':''} aria-label="Main navigation">{routes.map(p=><button key={p} className={page===p?'current':''} aria-current={page===p?'page':undefined} onClick={()=>navigate(p)}>{pageNames[p]}</button>)}</nav><div className="header-actions"><span className="header-status"><i className="signal-dot"/> NASA SPACE APPS</span><button className="nav-planner" onClick={()=>navigate('planner')} aria-label="Open Mission Planner"><ArrowUpRight size={18}/></button><button className="mobile-menu icon-button" aria-expanded={menu} aria-label={menu?'Close navigation':'Open navigation'} onClick={()=>setMenu(v=>!v)}>{menu?<X size={21}/>:<Menu size={21}/>}</button></div></header>
    <main id="main-content" tabIndex={-1}>{page==='home'&&<Home navigate={navigate} count={state.sites.length} year={state.mission.start.slice(0,4)}/>}{page==='planner'&&<Planner state={state} navigate={navigate} onWindows={()=>setModal('window')} onExport={()=>{if(state.evaluation)setModal('export');else setNotice('Run site analysis before exporting a scenario.');}}/>}{page==='horizon'&&<><Horizon state={state} onPower={()=>setModal('power')} onDispersion={()=>setModal('dispersion')} onMast={()=>setModal('mast')}/><div className="page-shell advanced-stream"><details><summary>Advanced streamed simulation <span>Geometric telemetry, power and event forecasts</span></summary><div className="tool-host"><RealtimeSimulationBar selectedSiteIds={state.ids} currentUnix={new Date(state.mission.start+'T00:00:00Z').getTime()/1000} mastHeightM={state.mission.mast} antennaMarginDeg={state.mission.margin} powerConfig={state.power} onTimeUpdate={()=>{}}/></div></details></div></>}{page==='timeline'&&<Timeline state={state}/>}{page==='educator'&&<Educator navigate={navigate}/>}{page==='sources'&&<Sources/>}</main>
    <footer className="site-footer"><button className="brand" onClick={()=>navigate('home')}><Moon size={21} strokeWidth={1.4}/><span>LunaScope</span></button><p>A clearer perspective on the next frontier.</p><div><span>NASA DATA / SPACE APPS PROJECT</span><button onClick={()=>navigate('sources')}>Science, with transparency <ArrowUpRight size={13}/></button></div></footer>
    {notice&&<div className="toast" role="status">{notice}<button className="icon-button" onClick={()=>setNotice('')} aria-label="Dismiss message"><X size={15}/></button></div>}
    <div className="tool-host"><WindowFinderModal isOpen={modal==='window'} onClose={()=>setModal('')} selectedSites={state.sites.filter(s=>state.ids.includes(s.site_id))} mastHeightM={state.mission.mast} onApplyWindow={(start,days)=>{state.setMission({...state.mission,start:start.slice(0,10),days});state.analyze();setModal('');}}/><PowerSimulationDrawer isOpen={modal==='power'} onClose={()=>setModal('')} evaluatedSites={state.evaluation?.evaluated_sites||{}} selectedSiteIds={state.ids} powerConfig={state.power} onUpdatePowerConfig={state.setPower}/><ScenarioExportModal isOpen={modal==='export'} onClose={()=>setModal('')} scenarioPayload={state.evaluation||{}}/><DispersionModal isOpen={modal==='dispersion'} onClose={()=>setModal('')} site={site} startDateIso={state.mission.start+'T00:00:00Z'} durationDays={state.mission.days} mastHeightM={state.mission.mast}/><MastSensitivityModal isOpen={modal==='mast'} onClose={()=>setModal('')} site={site} startDateIso={state.mission.start+'T00:00:00Z'} durationDays={state.mission.days} currentMastHeightM={state.mission.mast} onApplyMastHeight={h=>{state.update('mast',h);setModal('');}}/></div>
  </div>;
};
