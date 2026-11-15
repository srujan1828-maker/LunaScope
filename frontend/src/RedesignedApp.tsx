import React,{useEffect,useState} from 'react';
import {Moon,ArrowUpRight,Menu,X,User} from 'lucide-react';
import {VideoBackground} from './components/VideoBackground';
import {useMission,missionStart} from './mission';
import {Home,Planner,Horizon,Timeline,Educator,Sources,Page,pageNames} from './pages';
import {WindowFinderModal} from './components/WindowFinderModal';
import {BackupDialog} from './components/BackupDialog';
import {PowerSimulationDrawer} from './components/PowerSimulationDrawer';
import {ScenarioExportModal} from './components/ScenarioExportModal';
import {DispersionModal} from './components/DispersionModal';
import {MastSensitivityModal} from './components/MastSensitivityModal';
import {RealtimeSimulationBar} from './components/RealtimeSimulationBar';

const routes: { page: Page; label: string }[] = [
  { page: 'home', label: 'Home' },
  { page: 'planner', label: 'Mission Planner' },
  { page: 'horizon', label: 'Horizon Simulator' },
  { page: 'timeline', label: 'Timeline' },
  { page: 'educator', label: 'Learn' },
  { page: 'sources', label: 'Data' },
];

const validPages = Object.keys(pageNames) as Page[];
const currentPage = (): Page => {
  const page = location.hash.replace('#/', '').split('?')[0] as Page;
  return validPages.includes(page) ? page : 'home';
};

export const App: React.FC = () => {
  const state = useMission();
  const [page, setPage] = useState<Page>(currentPage);
  const [menu, setMenu] = useState(false);
  const [modal, setModal] = useState<'' | 'window' | 'power' | 'export' | 'dispersion' | 'mast' | 'contingency'>('');
  const [streamOpen,setStreamOpen]=useState(false);
  const [notice, setNotice] = useState('');

  useEffect(() => {
    const change = () => {
      setPage(currentPage());
      setMenu(false);
      window.scrollTo({ top: 0, behavior: 'instant' });
    };
    window.addEventListener('hashchange', change);
    return () => window.removeEventListener('hashchange', change);
  }, []);

  useEffect(() => {
    if (page !== 'horizon') setStreamOpen(false);
    if (page === 'planner' || page === 'horizon' || page === 'timeline') state.activate();
    document.title = `${pageNames[page]} — LunaScope`;
  }, [page]);

  const navigate = (target: Page) => {
    if(target==='horizon'&&state.selected!==state.primary)state.setAsPrimary(state.selected);
    if (target === page) {
      window.scrollTo({ top: 0, behavior: 'smooth' });
      setMenu(false);
    } else {
      location.hash = '/' + target;
    }
  };

  const site = state.sites.find(s => s.site_id === state.primary) || null;

  return (
    <div className={`lunascope-app page-${page}`}>
      <a className="skip-link" href="#main-content" onClick={e => { e.preventDefault(); document.getElementById("main-content")?.focus(); }}>
        Skip to content
      </a>
      <VideoBackground page={page} />

      {/* Top Header */}
      <header className="site-header">
        <button className="brand" aria-label="LunaScope home" onClick={() => navigate('home')}>
          <span className="brand-symbol">
            <Moon size={24} strokeWidth={1.5} />
            <i />
          </span>
          <span>LunaScope<small>LUNAR EXPLORATION</small></span>
        </button>

        <nav className={menu ? 'nav-open' : ''} aria-label="Main navigation">
          {routes.map(r => (
            <button
              key={r.page}
              className={`${page === r.page ? 'current nav-pill-active' : ''}`}
              aria-current={page === r.page ? 'page' : undefined}
              onClick={() => navigate(r.page)}
            >
              {r.label}
            </button>
          ))}
        </nav>

        <div className="header-actions">
          {/* Segmented Mode Selector: Planner Mode | Educator Mode */}
          <div className="mode-toggle-segmented">
            <button
              className={`mode-toggle-btn ${page !== 'educator' ? 'active' : ''}`}
              onClick={() => navigate('planner')}
              title="Switch to Mission Planner Mode"
            >
              Planner Mode
            </button>
            <button
              className={`mode-toggle-btn ${page === 'educator' ? 'active' : ''}`}
              onClick={() => navigate('educator')}
              title="Switch to Educator Mode"
            >
              Educator Mode
            </button>
          </div>

          {/* User Profile Icon */}
          <button className="profile-circle-btn" aria-label="Data provenance" title="Data provenance" onClick={()=>navigate('sources')}>
            <User size={18} />
          </button>

          {/* Mobile Menu Toggle */}
          <button className="mobile-menu icon-button" aria-expanded={menu} aria-label={menu ? 'Close navigation' : 'Open navigation'} onClick={() => setMenu(v => !v)}>
            {menu ? <X size={21} /> : <Menu size={21} />}
          </button>
        </div>
      </header>

      {/* Main Workspace */}
      <main id="main-content" tabIndex={-1}>
        {page === 'home' && <Home navigate={navigate} count={state.sites.length} year={state.mission.start.slice(0, 4)} />}
        {page === 'planner' && (
          <Planner
            state={state}
            navigate={navigate}
            onWindows={() => setModal('window')}
            onExport={() => {
              if (state.evaluation) setModal('export');
              else setNotice('Run site analysis before exporting a scenario.');
            }}
            onContingency={() => setModal('contingency')}
          />
        )}
        {page === 'horizon' && (
          <>
            <Horizon
              state={state}
              navigate={navigate}
              onPower={() => setModal('power')}
              onDispersion={() => setModal('dispersion')}
              onMast={() => setModal('mast')}
              onContingency={() => setModal('contingency')}
            />
            <div className="page-shell advanced-stream">
              <details onToggle={e=>setStreamOpen(e.currentTarget.open)}>
                <summary>Advanced streamed simulation <span>Geometric telemetry, power and event forecasts</span></summary>
                <div className="tool-host">
                  {streamOpen&&<RealtimeSimulationBar
                    selectedSiteIds={state.ids}
                    currentUnix={new Date(missionStart(state.mission)).getTime() / 1000}
                    mastHeightM={state.mission.mast}
                    antennaMarginDeg={state.mission.margin}
                    powerConfig={state.power}
                    onTimeUpdate={() => {}}
                  />}
                </div>
              </details>
            </div>
          </>
        )}
        {page === 'timeline' && (
          <Timeline
            state={state}
            navigate={navigate}
            onContingency={() => setModal('contingency')}
          />
        )}
        {page === 'educator' && <Educator navigate={navigate} />}
        {page === 'sources' && <Sources state={state} navigate={navigate} />}
      </main>

      {/* Footer */}
      <footer className="site-footer">
        <button className="brand" onClick={() => navigate('home')}>
          <Moon size={21} strokeWidth={1.4} />
          <span>LunaScope</span>
        </button>
        <p>A clearer perspective on the next frontier.</p>
        <div>
          <span>NASA DATA / SPACE APPS PROJECT</span>
          <button onClick={() => navigate('sources')}>
            Science, with transparency <ArrowUpRight size={13} />
          </button>
        </div>
      </footer>

      {notice && (
        <div className="toast" role="status">
          {notice}
          <button className="icon-button" onClick={() => setNotice('')} aria-label="Dismiss message">
            <X size={15} />
          </button>
        </div>
      )}

      {/* Tool & Modal Host */}
      <div className="tool-host">
        <WindowFinderModal missionStart={missionStart(state.mission)} missionDays={state.mission.days} missionEarth={state.mission.comms?state.mission.earth:0}
          isOpen={modal === 'window'}
          onClose={() => setModal('')}
          selectedSites={state.sites.filter(s => state.ids.includes(s.site_id))}
          mastHeightM={state.mission.mast}
          onApplyWindow={(start, days) => {
            state.setMission({ ...state.mission, start: start.slice(0, 10), utcTime:start.slice(11,19), days });
            state.analyze();
            setModal('');
          }}
        />
        <BackupDialog isOpen={modal==='contingency'} onClose={()=>setModal('')} state={state}/>
        <PowerSimulationDrawer
          isOpen={modal === 'power'}
          onClose={() => setModal('')}
          evaluatedSites={state.chartBusy?{}:state.evaluation?.evaluated_sites || {}}
          selectedSiteIds={state.ids}
          powerConfig={state.power}
          onUpdatePowerConfig={state.setPower}
        />
        <ScenarioExportModal
          isOpen={modal === 'export'}
          onClose={() => setModal('')}
          scenarioPayload={state.evaluation || {}}
        />
        <DispersionModal
          isOpen={modal === 'dispersion'}
          onClose={() => setModal('')}
          site={site}
          startDateIso={missionStart(state.mission)}
          durationDays={state.mission.days}
          mastHeightM={state.mission.mast}
        />
        <MastSensitivityModal
          isOpen={modal === 'mast'}
          onClose={() => setModal('')}
          site={site}
          startDateIso={missionStart(state.mission)}
          durationDays={state.mission.days}
          currentMastHeightM={state.mission.mast}
          onApplyMastHeight={h => {
            state.update('mast', h);
            setModal('');
          }}
        />
      </div>
    </div>
  );
};
