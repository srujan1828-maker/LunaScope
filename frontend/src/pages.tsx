import React,{useEffect,useState,lazy,Suspense} from 'react';
import {
  ArrowUpRight,
  ArrowRight,
  Compass,
  MapPin,
  Sun,
  Radio,
  ShieldCheck,
  ChevronRight,
  Search,
  SlidersHorizontal,
  Check,
  Plus,
  X,
  Orbit,
  CalendarDays,
  Clock,
  ExternalLink,
  Info,
  Download,
  Play,
  Pause,
  RotateCcw,
  Target,
  Calendar,
  Antenna,
  Layers,
  Mountain,
  Database,
  Box,
  BarChart3,
  Globe2,
  Lightbulb,
  CheckCircle2,
} from 'lucide-react';
import {MissionState,useStored} from './mission';
import {LunarMap} from './components/LunarMap';
import {HorizonGraph} from './components/HorizonGraph';
const SurfaceExplorer=lazy(()=>import('./components/SurfaceExplorer').then(m=>({default:m.SurfaceExplorer})));
import {MissionFeedback} from './components/MissionFeedback';
import {SolarElevationDistribution} from './components/SolarElevationDistribution';
import {TimelineInteractive} from './components/TimelineInteractive';
import {LearnInteractive} from './components/LearnInteractive';
import {DataSourcesInteractive} from './components/DataSourcesInteractive';
import {LandingSite} from './types';

export type Page='home'|'planner'|'horizon'|'timeline'|'educator'|'sources';
export const pageNames:Record<Page,string>={home:'Home',planner:'Mission Planner',horizon:'Horizon Simulator',timeline:'Timeline',educator:'Educator Mode',sources:'Data & Sources'};
export function PageTitle({number,title,description,children}:{number:string;title:string;description:string;children?:React.ReactNode}){return <div className="page-title"><div><div className="eyebrow">LUNASCOPE / {number}</div><h1>{title}<span>.</span></h1><p>{description}</p></div>{children}</div>;}
export function DemoNote(){return <div className="demo-note"><Info size={14}/><span>NASA LOLA terrain and JPL SPICE geometry. Derived analysis points; landing safety remains unassessed.</span><span className="demo-label">NASA INPUTS</span></div>;}
export function Status({value}:{value:string}){return <span className={`status ${value.toLowerCase()}`}><i/>{value}</span>;}

export function Home({navigate,count,year}:{navigate:(p:Page)=>void;count:number;year:string}){
  const features=[{icon:Compass,title:'Mission Planning',body:'Define mission parameters and identify suitable landing locations based on sunlight, terrain, and communication constraints.',page:'planner' as Page},{icon:MapPin,title:'Site Selection',body:'Compare candidate lunar landing locations using geographic and environmental conditions.',page:'planner' as Page},{icon:Orbit,title:'Horizon Simulation',body:'Explore sunlight conditions, illumination windows, and Earth visibility throughout the mission.',page:'horizon' as Page}];
  return <><section className="home-hero"><div className="hero-content"><div className="eyebrow"><i className="signal-dot"/> LUNAR SOUTH POLE EXPLORATION</div><h1>Plan the window.<br/><em>Prepare the backup.</em></h1><p>Explore lunar landing opportunities, evaluate surface conditions, and identify locations for further study with intelligent lunar mission planning.</p><div className="hero-buttons"><button className="button primary" onClick={()=>navigate('planner')}>Start Mission Planning <ArrowUpRight size={17}/></button><button className="button secondary" onClick={()=>{navigate('planner');setTimeout(()=>document.getElementById('candidate-sites')?.scrollIntoView({behavior:'smooth'}),120);}}>Explore Lunar Sites <ArrowRight size={16}/></button></div>
    <div className="hero-facts"><div><strong>{count}<span> / LOLA</span></strong><p>Candidate sites</p></div><div><strong>{year}</strong><p>Mission window</p></div><div><strong>South Pole</strong><p>Exploration region</p></div></div></div>
    <div className="hero-coordinate"><span>THE NEXT FRONTIER</span><strong>90°00′00″ S</strong><small>Explore with clarity. Plan with confidence.</small></div><div className="hero-bottom"><span>MISSION PLANNING, WITH PERSPECTIVE</span><a href="#capabilities">SCROLL TO EXPLORE <span>↓</span></a></div>
  </section><section id="capabilities" className="home-section"><div className="section-heading"><div><span className="eyebrow">BUILT FOR THE NEXT STEP</span><h2>Every possibility. A clearer plan.</h2></div><p>A connected workspace for exploring<br/>the possibilities of the lunar south pole.</p></div><div className="feature-grid">{features.map((f,i)=><button className="feature-card" key={f.title} onClick={()=>navigate(f.page)}><div className="feature-top"><f.icon size={25} strokeWidth={1.3}/><span>0{i+1}</span></div><h3>{f.title}</h3><p>{f.body}</p><span className="text-link">Explore tool <ArrowUpRight size={15}/></span></button>)}</div></section>
  <section className="home-section steps-section"><span className="eyebrow">FROM QUESTION TO MISSION</span><h2>A considered path forward.</h2><div className="steps">{[['Define Mission','Configure mission duration, sunlight requirements, and lander parameters.'],['Analyze Sites','Evaluate lunar locations using mission feasibility criteria.'],['Select & Prepare','Choose a primary landing location and identify backup sites.']].map(([title,body],i)=><div key={title}><span className="step-number">0{i+1}</span><div><h3>{title}</h3><p>{body}</p></div>{i<2&&<ArrowRight size={20}/>}</div>)}</div></section>
  <section className="final-cta"><span className="eyebrow">THE RIGHT PLACE. THE RIGHT TIME.</span><h2>Your next mission starts<br/>with the right location.</h2><button className="button primary" onClick={()=>navigate('planner')}>Open Mission Planner <ArrowUpRight size={17}/></button></section></>;
}

function Numeric({label,value,onChange,min,max,step=1,hint}:{label:string;value:number;onChange:(n:number)=>void;min:number;max:number;step?:number;hint?:string}){return <label className="field">{label}<input type="number" required value={value} min={min} max={max} step={step} onChange={e=>onChange(e.target.valueAsNumber)}/>{hint&&<small>{hint}</small>}</label>;}

export function Planner({
  state,
  navigate,
  onWindows,
  onExport,
  onContingency
}: {
  state: MissionState;
  navigate: (p: Page) => void;
  onWindows: () => void;
  onExport: () => void;
  onContingency?: () => void;
}) {
  const [search, setSearch] = useState('');
  const [sort, setSort] = useState<'name' | 'lat' | 'lon' | 'sun' | 'joint'>('sun');
  const [ascending, setAscending] = useState(false);
  const m = state.mission;

  const getSiteDisplayName = (s:LandingSite)=>s.name;
  const getSunDays=(s:LandingSite)=>state.rank(s.site_id)?.metrics.longest_sun_window_hours==null?null:state.rank(s.site_id)!.metrics.longest_sun_window_hours/24;
  const getJointDays=(s:LandingSite)=>state.rank(s.site_id)?.metrics.joint_availability_pct==null?null:state.rank(s.site_id)!.metrics.joint_availability_pct/100*m.days;
  const daysLabel=(n:number|null)=>n==null?'Pending':n.toFixed(2)+' days';
  const filteredSites = state.sites.filter(s => {
    const disp = getSiteDisplayName(s).toLowerCase();
    const orig = s.name.toLowerCase();
    const query = search.toLowerCase();
    return disp.includes(query) || orig.includes(query);
  });

  const sortedSites = [...filteredSites].sort((a, b) => {
    let diff = 0;
    if (sort === 'name') diff = getSiteDisplayName(a).localeCompare(getSiteDisplayName(b));
    else if (sort === 'lat') diff = a.lat_deg - b.lat_deg;
    else if (sort === 'lon') diff = a.lon_deg - b.lon_deg;
    else if (sort === 'sun') diff = (getSunDays(a)??-1) - (getSunDays(b)??-1);
    else if (sort === 'joint') diff = (getJointDays(a)??-1) - (getJointDays(b)??-1);
    return ascending ? diff : -diff;
  });

  const sortBy = (key: 'name' | 'lat' | 'lon' | 'sun' | 'joint') => {
    if (key === sort) {
      setAscending(x => !x);
    } else {
      setSort(key);
      setAscending(false);
    }
  };

  const handleSelectSite = (siteId: string) => {
    state.setAsPrimary(siteId);
    state.setSelected(siteId);
  };

  const handleInspectSite = (siteId: string) => {
    state.setAsPrimary(siteId);
    state.setSelected(siteId);
    navigate('horizon');
  };

  return (
    <div className="planner-page-layout">

      {/* Main Workspace Column */}
      <div className="planner-main-column">
        {/* Header */}
        <div className="planner-view-header">
          <h1>Mission Planner</h1>
          <p>Select a landing site and mission constraints to evaluate feasibility and find automatic backup candidates.</p>
        </div>

        {/* Top 2-Column Grid */}
        <div className="planner-top-row">
          {/* Left Block: Mission Parameters */}
          <div className="mission-parameters-card">
            <div className="card-top-title">
              <SlidersHorizontal size={18} />
              <span>Mission Parameters</span>
            </div>

            <label className="param-field-row"><span className="param-label">Mission start (UTC)</span><div className="param-input-box"><input aria-label="Mission start date" type="date" value={m.start} min="2025-01-01" max="2032-12-31" onChange={e=>{if(e.target.value)state.update('start',e.target.value);}}/></div></label>
            <label className="param-field-row"><span className="param-label">Start time (UTC)</span><div className="param-input-box"><input aria-label="Mission start time" type="time" step="1" value={m.utcTime||'00:00:00'} onChange={e=>state.update('utcTime',e.target.value)}/></div></label>
            <label className="param-field-row"><span className="param-label">Mission duration (days)</span><div className="param-input-box"><input aria-label="Mission duration" type="number" min="1" max="366" step="0.1" value={m.days} onChange={e=>{if(e.target.validity.valid&&Number.isFinite(e.target.valueAsNumber))state.update('days',e.target.valueAsNumber);}}/></div></label>
            <label className="param-field-row"><span className="param-label">Consecutive sunlight (days)</span><div className="param-input-box"><input aria-label="Consecutive sunlight" type="number" min="0" max="366" step="0.1" value={m.sunlight} onChange={e=>{if(e.target.validity.valid&&Number.isFinite(e.target.valueAsNumber))state.update('sunlight',e.target.valueAsNumber);}}/></div></label>
            <label className="param-field-row"><span className="param-label">Minimum Earth visibility (%)</span><div className="param-input-box"><input aria-label="Minimum Earth visibility" type="number" min="0" max="100" value={m.earth} onChange={e=>{if(e.target.validity.valid&&Number.isFinite(e.target.valueAsNumber))state.update('earth',e.target.valueAsNumber);}}/></div></label>
            <label className="param-field-row"><span className="param-label">Direct-to-Earth link</span><div className="param-input-box"><select aria-label="Communication requirement" value={String(m.comms)} onChange={e=>state.update('comms',e.target.value==='true')}><option value="true">Required</option><option value="false">Optional</option></select></div></label>
            {/* Lander Mast Height */}
            <div className="param-field-row">
              <span className="param-label">Lander Mast Height</span>
              <div className="mast-input-group">
                <div className="param-input-box">
                  <Antenna size={14} className="param-icon" />
                  <input
                    type="number"
                    step="0.5"
                    min="0.5"
                    max="30"
                    value={m.mast}
                    onChange={e => {if(Number.isFinite(e.target.valueAsNumber)&&e.target.validity.valid)state.update('mast', e.target.valueAsNumber);}}
                    className="param-num-input"
                  />
                  <span className="unit-label">m</span>
                </div>
                <button
                  type="button"
                  className="mast-info-btn"
                  title="Mast height above ground enables line-of-sight elevation over local terrain features."
                  onClick={()=>navigate('horizon')}
                >
                  <Info size={13} />
                </button>
              </div>
            </div>

            {/* Analyze Sites CTA */}
            <button
              className="analyze-cta-btn"
              onClick={() => state.analyze()}
              disabled={state.busy}
            >
              {state.busy ? (
                <>
                  <span className="spinner" />
                  <span>Analyzing Sites...</span>
                </>
              ) : (
                <>
                  <span>Analyze Sites</span>
                  <ArrowRight size={16} />
                </>
              )}
            </button>
          </div>

          {/* Right Block: Circular Polar Map */}
          <div className="polar-atlas-card">
            <LunarMap state={state} />
          </div>
        </div>

        <MissionFeedback state={state}/>
        <div className="integration-actions"><button className="button secondary compact" onClick={onWindows}>Find mission windows</button><button className="button secondary compact" onClick={onContingency}>Prepare backups</button><button className="button secondary compact" onClick={onExport} disabled={state.chartBusy||!state.evaluation}>Export analysis</button><button className="button primary compact" onClick={()=>navigate('horizon')}>Explore selected site in 3D</button></div>
        {/* Measured analysis locations */}
        <div className="candidate-sites-card" id="candidate-sites">
          <div className="candidate-table-header">
            <div className="table-title">
              <Layers size={18} className="table-layers-icon" />
              <span>LOLA Analysis Locations ({state.sites.length})</span>
            </div>
            <div className="table-search-box">
              <Search size={14} className="search-icon" />
              <input
                type="text"
                placeholder="Search LOLA location"
                value={search}
                onChange={e => setSearch(e.target.value)}
                className="search-input"
              />
            </div>
          </div>

          <div className="candidate-table-wrapper">
            <table className="candidate-data-table">
              <thead>
                <tr>
                  <th style={{ width: '40px' }}></th>
                  <th onClick={() => sortBy('name')} className="sortable-th">
                    Site {sort === 'name' ? (ascending ? '↑' : '↓') : ''}
                  </th>
                  <th onClick={() => sortBy('lat')} className="sortable-th">
                    Latitude {sort === 'lat' ? (ascending ? '↑' : '↓') : ''}
                  </th>
                  <th onClick={() => sortBy('lon')} className="sortable-th">
                    Longitude {sort === 'lon' ? (ascending ? '↑' : '↓') : ''}
                  </th>
                  <th onClick={() => sortBy('sun')} className="sortable-th">
                    Consecutive Sunlight {sort === 'sun' ? (ascending ? '↑' : '↓') : ''}
                  </th>
                  <th onClick={() => sortBy('joint')} className="sortable-th">
                    Sun + Earth Visibility {sort === 'joint' ? (ascending ? '↑' : '↓') : ''}
                  </th>
                  <th className="status-th">
                    <span>Status</span>
                    <span className="info-th" title="Evaluation status under configured mission constraints.">
                      <Info size={12} />
                    </span>
                  </th>
                  <th style={{ width: '44px' }}></th>
                </tr>
              </thead>
              <tbody>
                {sortedSites.map(s => {
                  const isPrimary = s.site_id === state.primary;
                  const ranking = state.rank(s.site_id);
                  const isPassingBackup = state.backups.includes(s.site_id) && ranking?.passed;
                  const isFailingBackup = state.backups.includes(s.site_id) && ranking && !ranking.passed;

                  return (
                    <tr
                      key={s.site_id}
                      className={`table-site-row ${isPrimary ? 'row-selected' : ''}`}
                      onClick={() => handleSelectSite(s.site_id)}
                    >
                      <td>
                        <div className={`custom-radio ${isPrimary ? 'checked' : ''}`}>
                          {isPrimary && <div className="radio-dot" />}
                        </div>
                      </td>
                      <td className="site-name-cell">
                        <strong>{getSiteDisplayName(s)}</strong><label className="compare-location" onClick={e=>e.stopPropagation()}><input type="checkbox" aria-label={`Compare ${s.name}`} checked={state.ids.includes(s.site_id)} disabled={isPrimary} onChange={()=>state.toggleCompare(s.site_id)}/> Compare</label>
                      </td>
                      <td>{Math.abs(s.lat_deg).toFixed(1)}° S</td>
                      <td>{s.lon_deg >= 0 ? s.lon_deg.toFixed(1) : (360 + s.lon_deg).toFixed(1)}° E</td>
                      <td>{daysLabel(getSunDays(s))}</td>
                      <td>{daysLabel(getJointDays(s))}</td>
                      <td>
                        {isPrimary ? (
                          <span className="badge-primary">Primary · {state.status(s.site_id)}</span>
                        ) : isPassingBackup ? (
                          <span className="badge-passing">Backup (Passing)</span>
                        ) : isFailingBackup ? (
                          <span className="badge-failing">Backup (Fail)</span>
                        ) : (
                          <span className={ranking?(ranking.passed?'badge-passing':'badge-failing'):'badge-candidate'}>{state.status(s.site_id)}</span>
                        )}
                      </td>
                      <td>
                        <button
                          className="row-chevron-btn"
                          title={`Inspect ${s.name} in Horizon Simulator`}
                          onClick={(e) => {
                            e.stopPropagation();
                            handleInspectSite(s.site_id);
                          }}
                          aria-label={`Inspect ${s.name} in Horizon Simulator`}
                        >
                          <ChevronRight size={17} />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

export function Horizon({
  state,
  navigate,
  onPower,
  onDispersion,
  onMast,
  onContingency
}: {
  state: MissionState;
  navigate?: (p: Page) => void;
  onPower?: () => void;
  onDispersion?: () => void;
  onMast: () => void;
  onContingency?: () => void;
}) {
  const [viewMode, setViewMode] = useState<'horizon' | '3d'>('3d');
  const [compareSiteId, setCompareSiteId] = useState<string>(state.compare.find(id=>id!==state.primary)||'lola-sp-002');
  const [tableTab, setTableTab] = useState<'primary' | 'backup' | 'difference'>('primary');
  const [index, setIndex] = useState(0);

  useEffect(()=>{if(compareSiteId===state.primary){setCompareSiteId(state.sites.find(s=>s.site_id!==state.primary)?.site_id||'');return;}if(compareSiteId&&!state.ids.includes(compareSiteId))state.toggleCompare(compareSiteId);},[compareSiteId,state.primary,state.ids.join(','),state.sites]);
  const data = state.chartBusy?undefined:state.evaluation?.evaluated_sites[state.primary];
  const step = Math.min(index, Math.max(0, (data?.timestamps.length || 1) - 1));

  const getSiteDisplayName=(id:string)=>state.sites.find(s=>s.site_id===id)?.name||id;
  const getSiteMetrics=(id:string)=>{
    const site=state.sites.find(s=>s.site_id===id), d=state.chartBusy?undefined:state.evaluation?.evaluated_sites[id], r=state.rank(id);
    const ext=(values:(number|null)[]|undefined,min=false)=>{const v=(values||[]).filter((v):v is number=>v!=null&&Number.isFinite(v));return v.length?(min?Math.min(...v):Math.max(...v)):null;};
    const fmt=(v:number|null)=>v==null?'Pending':v.toFixed(2)+'°';
    const max=ext(d?.ephemeris.sun_elevation),min=ext(d?.ephemeris.sun_elevation,true),emin=ext(d?.ephemeris.earth_elevation,true),emax=ext(d?.ephemeris.earth_elevation),hmin=ext(d?.horizon_360,true);
    return {name:getSiteDisplayName(id),coords:site?`${site.lat_deg.toFixed(3)}°, ${site.lon_deg.toFixed(3)}°E`:'Pending',maxSun:fmt(max),minSun:fmt(min),earthRange:fmt(emin)+' to '+fmt(emax),horizonMin:fmt(hmin),sunDays:r?(r.metrics.longest_sun_window_hours/24).toFixed(2):'Pending',jointDays:r?(r.metrics.joint_availability_pct/100*state.mission.days).toFixed(2):'Pending',maxElevationRange:fmt(min)+' to '+fmt(max),raw:[max,min,emin,emax,hmin]};
  };
  const primaryMetrics = getSiteMetrics(state.primary);
  const compareMetrics = getSiteMetrics(compareSiteId);

  const formatDateDisplay = (isoDate: string) => {
    try {
      const d = new Date(isoDate + 'T00:00:00Z');
      return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' });
    } catch {
      return 'Invalid date';
    }
  };

  const handleNav = (p: Page) => {
    if (navigate) navigate(p);
    else location.hash = '/' + p;
  };

  return (
    <div className="horizon-page-layout">
      {/* Left Navigation Sidebar */}


      {/* Main Workspace Column */}
      <div className="horizon-main-column">
        {/* Top Header */}
        <div className="horizon-header-bar">
          <div className="header-title-group">
            <Mountain size={28} className="horizon-mountain-icon" />
            <div>
              <h1>360° Horizon Simulator</h1>
              <p>Visualize the local terrain horizon and adaptive Sun–Earth trajectories for the selected site and date.</p>
            </div>
          </div>

          {/* View Mode Toggle: Horizon View | 3D Terrain */}
          <div className="view-mode-pill">
            <button
              className={`mode-btn ${viewMode === 'horizon' ? 'active' : ''}`}
              onClick={() => setViewMode('horizon')}
            >
              <Mountain size={14} />
              <span>Horizon View</span>
            </button>
            <button
              className={`mode-btn ${viewMode === '3d' ? 'active' : ''}`}
              onClick={() => setViewMode('3d')}
            >
              <Box size={14} />
              <span>3D Moon & Surface</span>
            </button>
          </div>
        </div>

        {/* Configuration / Filter Bar */}
        <div className="horizon-filter-bar">
          {/* Primary Site */}
          <div className="filter-group">
            <span className="filter-label">Primary Site</span>
            <div className="filter-select-wrapper">
              <select
                value={state.primary}
                onChange={e => state.setAsPrimary(e.target.value)}
                className="filter-select"
              >
                {state.sites.map(s => (
                  <option key={s.site_id} value={s.site_id}>
                    {getSiteDisplayName(s.site_id)}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Compare With */}
          <div className="filter-group">
            <span className="filter-label">Compare With</span>
            <div className="filter-select-wrapper">
              <select
                aria-label="Compare horizon location" value={compareSiteId}
                onChange={e => setCompareSiteId(e.target.value)}
                className="filter-select"
              >
                {state.sites.filter(s => s.site_id !== state.primary).map(s => (
                  <option key={s.site_id} value={s.site_id}>
                    {getSiteDisplayName(s.site_id)}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Date Picker */}
          <div className="filter-group">
            <span className="filter-label">Date</span>
            <div className="filter-date-wrapper">
              <span className="date-display-text">{formatDateDisplay(state.mission.start)}</span>
              <Calendar size={14} className="calendar-icon" />
              <input
                type="date"
                value={state.mission.start}
                onChange={e => {if(e.target.value)state.update('start', e.target.value);}}
                className="hidden-date-input"
              />
            </div>
          </div>

          {/* Mast Height */}
          <div className="filter-group">
            <span className="filter-label">Mast Height</span>
            <div className="mast-filter-wrapper">
              <div className="filter-select-wrapper">
                <select
                  value={state.mission.mast}
                  onChange={e => state.update('mast', Number(e.target.value))}
                  className="filter-select"
                >
                  {Array.from(new Set([0.5,1,1.5,2,2.5,3,5,10,20,30,state.mission.mast])).sort((a,b)=>a-b).map(h => (
                    <option key={h} value={h}>{h.toFixed(1)} m</option>
                  ))}
                </select>
              </div>
              <button
                type="button"
                className="mast-info-button"
                onClick={onMast}
                title="Open Mast Sensitivity Sweep"
              >
                <Info size={14} />
              </button>
            </div>
          </div>
        </div>

        {/* Middle Two-Column Section */}
        <MissionFeedback state={state} compact/><div className={`horizon-middle-row ${viewMode==='3d'?'surface-expanded':''}`}>
          {/* Main Graph Card */}
          <div className="horizon-graph-card">
            {viewMode === 'horizon' ? (
              <HorizonGraph
                data={data}
                siteId={state.primary}
                stepIndex={step}
                missionDate={state.mission.start}
                onSeekStep={setIndex}
              />
            ) : (
              <Suspense fallback={<p role="status">Loading 3D explorer…</p>}><SurfaceExplorer state={state} onPower={onPower||(()=>{})} onDispersion={onDispersion||(()=>{})} onMast={onMast}/></Suspense>
            )}
          </div>

          {/* Right Metrics Sidebar (3 Cards) */}
          <div className="horizon-metrics-sidebar">
            {/* Card 1: Site Overview */}
            <div className="overview-card">
              <div className="card-header">
                <MapPin size={14} className="icon-amber" />
                <span>Site Overview</span>
              </div>
              <div className="overview-content">
                <div>
                  <strong className="site-title">{primaryMetrics.name}</strong>
                  <div className="site-coords">{primaryMetrics.coords}</div>
                </div>
                <MapPin size={38} className="gold-icon"/>
              </div>
            </div>

            {/* Card 2: Visibility Summary */}
            <div className="overview-card">
              <div className="card-header">
                <Sun size={14} className="icon-amber" />
                <span>Visibility Summary (Mission Window)</span>
              </div>
              <div className="metric-row-list">
                <div className="metric-row">
                  <div className="metric-label">
                    <Sun size={13} className="text-amber-400" />
                    <span>Consecutive Sunlight</span>
                  </div>
                  <strong className="metric-value">{primaryMetrics.sunDays} days</strong>
                </div>
                <div className="metric-row">
                  <div className="metric-label">
                    <Radio size={13} className="text-cyan-400" />
                    <span>Sun + Earth Visibility</span>
                  </div>
                  <strong className="metric-value">{primaryMetrics.jointDays} days</strong>
                </div>
              </div>
            </div>

            {/* Card 3: Solar Elevation Distribution */}
            <div className="overview-card">
              <div className="card-header">
                <BarChart3 size={14} className="icon-amber" />
                <span>Solar Elevation Distribution</span>
              </div>
              <div className="chart-body">
                <SolarElevationDistribution data={data} />
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Two-Column Section */}
        <div className="horizon-bottom-row">
          {/* Bottom-Left: Site Comparison Table */}
          <div className="comparison-table-card">
            {/* Table Tabs */}
            <div className="table-tabs-bar">
              <button
                className={`tab-btn ${tableTab === 'primary' ? 'active' : ''}`}
                onClick={() => setTableTab('primary')}
              >
                Primary Site
              </button>
              <button
                className={`tab-btn ${tableTab === 'backup' ? 'active' : ''}`}
                onClick={() => setTableTab('backup')}
              >
                Backup Site
              </button>
              <button
                className={`tab-btn ${tableTab === 'difference' ? 'active' : ''}`}
                onClick={() => setTableTab('difference')}
              >
                Difference
              </button>
            </div>

            {/* Comparison Data Table */}
            <table className="comparison-table">
              <thead>
                <tr>
                  <th style={{ width: '36px' }}></th>
                  <th>
                    <div className="th-with-icon">
                      <Sun size={12} />
                      <span>Site</span>
                    </div>
                  </th>
                  <th>
                    <div className="th-with-icon">
                      <Sun size={12} className="text-amber-400" />
                      <span>Max Sun Elev.</span>
                    </div>
                  </th>
                  <th>
                    <div className="th-with-icon">
                      <Sun size={12} className="text-orange-400" />
                      <span>Min Sun Elev.</span>
                    </div>
                  </th>
                  <th>
                    <div className="th-with-icon">
                      <Globe2 size={12} className="text-cyan-400" />
                      <span>Earth Elev. (range)</span>
                    </div>
                  </th>
                  <th>
                    <div className="th-with-icon">
                      <Mountain size={12} />
                      <span>Horizon Min.</span>
                    </div>
                  </th>
                </tr>
              </thead>
              <tbody>
                {/* Primary Site Row */}
                <tr
                  className={`site-row ${tableTab === 'primary' ? 'highlighted' : ''}`}
                  onClick={() => {
                    setTableTab('primary');
                    state.setAsPrimary(state.primary);
                  }}
                >
                  <td>
                    <div className={`radio-circle ${tableTab === 'primary' ? 'checked' : ''}`}>
                      {tableTab === 'primary' && <div className="dot" />}
                    </div>
                  </td>
                  <td><strong>{primaryMetrics.name}</strong></td>
                  <td>{primaryMetrics.maxSun}</td>
                  <td>{primaryMetrics.minSun}</td>
                  <td>{primaryMetrics.earthRange}</td>
                  <td>{primaryMetrics.horizonMin}</td>
                </tr>

                {/* Compare / Backup Site Row */}
                <tr
                  className={`site-row ${tableTab === 'backup' ? 'highlighted' : ''}`}
                  onClick={() => {
                    setTableTab('backup');
                  }}
                >
                  <td>
                    <div className={`radio-circle ${tableTab === 'backup' ? 'checked' : ''}`}>
                      {tableTab === 'backup' && <div className="dot" />}
                    </div>
                  </td>
                  <td><strong>{compareMetrics.name}</strong></td>
                  <td>{compareMetrics.maxSun}</td>
                  <td>{compareMetrics.minSun}</td>
                  <td>{compareMetrics.earthRange}</td>
                  <td>{compareMetrics.horizonMin}</td>
                </tr>

                {/* Difference Row (When Difference Tab Active) */}
                {tableTab === 'difference' && (
                  <tr className="site-row diff-row">
                    <td>Δ</td>
                    <td><strong className="text-amber-400">Difference (Primary − Backup)</strong></td>
                    {[0,1,2,4].map(i=><td key={i}>{primaryMetrics.raw[i]==null||compareMetrics.raw[i]==null?'Pending':(primaryMetrics.raw[i]!-compareMetrics.raw[i]!).toFixed(2)+'°'+(i===2&&primaryMetrics.raw[3]!=null&&compareMetrics.raw[3]!=null?' / '+(primaryMetrics.raw[3]!-compareMetrics.raw[3]!).toFixed(2)+'°':'')}</td>)}
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Bottom-Right: Key Insights */}
          <div className="insights-card">
            <div className="card-header">
              <Lightbulb size={16} className="icon-amber" />
              <span>Key Insights</span>
            </div>
            <div className="insights-list">
              <div className="insight-item">
                <CheckCircle2 size={16} className="text-emerald-400 flex-shrink-0" />
                <span>Computed solar elevation range: {primaryMetrics.maxElevationRange}.</span>
              </div>
              <div className="insight-item">
                <CheckCircle2 size={16} className="text-emerald-400 flex-shrink-0" />
                <span>Sun and Earth simultaneously available for {primaryMetrics.jointDays} total days.</span>
              </div>
              <div className="insight-item">
                <Info size={16} className="text-amber-400 flex-shrink-0" />
                <span>{state.rank(state.primary)?.explanation||'Waiting for the current mission evaluation.'}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

type Phase={name:string;start:string;days:number;status:string};
const phaseNames=['Mission Configuration','Site Evaluation','Primary Site Selection','Backup Site Selection','Launch Window Preparation','Lunar Transfer','Landing Operations','Surface Mission'];
export function Timeline({
  state,
  navigate,
  onContingency
}: {
  state: MissionState;
  navigate?: (p: Page) => void;
  onContingency?: () => void;
}) {
  return <TimelineInteractive state={state} navigate={navigate} onContingency={onContingency} />;
}

export function Educator({navigate}:{navigate:(p:Page)=>void}){
  return <LearnInteractive navigate={navigate} />;
}

export function Sources({
  state,
  navigate
}: {
  state?: MissionState;
  navigate?: (p: Page) => void;
}) {
  return <DataSourcesInteractive state={state} navigate={navigate} />;
}
