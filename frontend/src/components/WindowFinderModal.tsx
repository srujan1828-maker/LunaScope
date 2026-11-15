import React, { useState } from 'react';
import { LandingSite, WindowSearchResult, CandidateWindow } from '../types';
import { searchMissionWindows } from '../api/client';
import {
  Compass,
  X,
  Search,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Sun,
  Radio,
  Clock,
} from 'lucide-react';

interface WindowFinderModalProps {
  isOpen: boolean;
  onClose: () => void;
  selectedSites: LandingSite[];
  mastHeightM: number;
  onApplyWindow: (startIso: string, durationDays: number) => void;
}

export const WindowFinderModal: React.FC<WindowFinderModalProps> = ({
  isOpen,
  onClose,
  selectedSites,
  mastHeightM,
  onApplyWindow,
}) => {
  const [searchStart, setSearchStart] = useState('2027-01-01T00:00:00Z');
  const [searchEnd, setSearchEnd] = useState('2027-02-15T00:00:00Z');
  const [durationDays, setDurationDays] = useState(7.0);
  const [priority, setPriority] = useState('balanced');
  const [strideHours,setStrideHours]=useState(12);

  // Hard constraints
  const [minSunPct, setMinSunPct] = useState(65.0);
  const [maxShadowGapHours, setMaxShadowGapHours] = useState(16.0);
  const [minEarthPct, setMinEarthPct] = useState(55.0);
  const [maxEarthOutageHours, setMaxEarthOutageHours] = useState(30.0);
  const [minJointPct, setMinJointPct] = useState(45.0);

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<WindowSearchResult | null>(null);

  if (!isOpen) return null;

  const handleSearch = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await searchMissionWindows({
        site_ids: selectedSites.map((s) => s.site_id),
        search_start_iso: searchStart,
        search_end_iso: searchEnd,
        mission_duration_days: durationDays,
        stride_hours: strideHours,
        min_sun_pct: minSunPct,
        max_shadow_gap_hours: maxShadowGapHours,
        min_earth_pct: minEarthPct,
        max_earth_outage_hours: maxEarthOutageHours,
        min_joint_pct: minJointPct,
        priority,
        mast_height_m: mastHeightM,
      });
      setResult(res);
    } catch (err: any) {
      setError(err.message || 'Window search failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4 overflow-y-auto">
      <div className="glass-panel w-full max-w-4xl rounded-2xl border border-cyan-500/30 p-6 flex flex-col gap-6 max-h-[90vh] overflow-y-auto shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-amber-500/20 border border-amber-500/30 flex items-center justify-center">
              <Compass className="w-5 h-5 text-amber-400" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-100">
                Find Better Surface Operation Windows
              </h2>
              <p className="text-xs text-slate-400">
                Apply hard constraints across full mission durations, then rank by your priority
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Input Parameters */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 bg-slate-900/60 border border-slate-800 p-4 rounded-xl">
          <div className="flex flex-col gap-1.5">
            <label className="text-xs text-slate-300 font-medium">Search Date Range</label>
            <div className="flex flex-col gap-1 text-xs">
              <input
                type="datetime-local"
                value={searchStart.slice(0, 16)}
                onChange={(e) => setSearchStart(`${e.target.value}:00Z`)}
                className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-slate-200 font-mono"
              />
              <span className="text-[10px] text-slate-500 text-center">to</span>
              <input
                type="datetime-local"
                value={searchEnd.slice(0, 16)}
                onChange={(e) => setSearchEnd(`${e.target.value}:00Z`)}
                className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-slate-200 font-mono"
              />
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-xs text-slate-300 font-medium flex justify-between">
              <span>Mission Duration</span>
              <span className="text-amber-300 font-mono">{durationDays} Days</span>
            </label>
            <input
              type="range"
              min="1"
              max="30"
              step=".25"
              value={durationDays}
              onChange={(e) => setDurationDays(Number(e.target.value))}
              className="mt-2"
            />
            <label className="text-xs text-slate-300 font-medium mt-2">Priority Preset</label>
            <select
              value={priority}
              onChange={(e) => setPriority(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-slate-200 font-mono focus:outline-none focus:border-cyan-500"
            >
              <option value="balanced">Balanced Trade-off</option>
              <option value="favour_sun">Favour Sunlight Exposure</option>
              <option value="favour_earth">Favour Earth Visibility</option>
              <option value="minimise_interruptions">Minimise Outage Gaps</option>
            </select>
          </div>

          <div className="flex flex-col gap-1.5 text-xs font-mono">
            <span className="text-slate-300 font-sans font-medium text-xs">Hard Constraints:</span>
            <div className="flex justify-between items-center text-[11px]">
              <span className="text-slate-400">Min Sun:</span>
              <span className="text-amber-300">{minSunPct}%</span>
            </div>
            <div className="flex justify-between items-center text-[11px]">
              <span className="text-slate-400">Max Shadow Gap:</span>
              <span className="text-rose-300">{maxShadowGapHours}h</span>
            </div>
            <div className="flex justify-between items-center text-[11px]">
              <span className="text-slate-400">Min Earth LOS:</span>
              <span className="text-cyan-300">{minEarthPct}%</span>
            </div>
            <div className="flex justify-between items-center text-[11px]">
              <span className="text-slate-400">Max Earth Outage:</span>
              <span className="text-indigo-300">{maxEarthOutageHours}h</span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {([
            ['Minimum sunlight (%)',minSunPct,setMinSunPct,0,100],['Maximum shadow gap (h)',maxShadowGapHours,setMaxShadowGapHours,0,200],
            ['Minimum Earth-center visibility (%)',minEarthPct,setMinEarthPct,0,100],['Maximum Earth outage (h)',maxEarthOutageHours,setMaxEarthOutageHours,0,200],
            ['Minimum joint visibility (%)',minJointPct,setMinJointPct,0,100],['Candidate start stride (h)',strideHours,setStrideHours,1,48]
          ] as const).map(([label,value,set,min,max])=><label className="field" key={label}>{label}<input type="number" aria-label={label} value={value} min={min} max={max} step=".25" onChange={e=>{const n=e.target.valueAsNumber;if(Number.isFinite(n)&&n>=min&&n<=max)set(n);}}/></label>)}
        </div>
        <button
          onClick={handleSearch}
          disabled={isLoading}
          className="w-full py-2.5 rounded-xl bg-gradient-to-r from-cyan-600 via-sky-600 to-amber-500 hover:from-cyan-500 hover:to-amber-400 text-white font-semibold text-xs transition-all shadow-lg flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
        >
          {isLoading ? (
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            <Search className="w-4 h-4" />
          )}
          <span>Search Surface Operation Windows</span>
        </button>

        {error && (
          <div className="p-3 bg-red-950/60 border border-red-500/30 rounded-xl text-red-200 text-xs flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Results */}
        {result && (
          <div className="flex flex-col gap-4">
            {/* Top Narrative Explanation */}
            <div className="p-3.5 bg-slate-900/90 border border-cyan-500/30 rounded-xl text-xs text-cyan-200 flex items-start gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold block mb-0.5">Evaluated {result.total_evaluated_windows} candidate windows:</span>
                <span>{result.explanation}</span><p className="mt-2">Ten-minute baseline; detected transitions refined to 30-second brackets. Shorter unsampled events may be missed. Applying a window updates its UTC start and duration; the planner then evaluates its own configured constraints.</p>
              </div>
            </div>

            {/* Recommended Windows Cards */}
            <div className="flex flex-col gap-2.5">
              <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Top Passing Windows ({result.passing_windows_count} found):
              </span>

              {result.recommended_windows.length === 0 ? (
                <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-xl text-xs text-slate-400 text-center">
                  No candidate window met 100% of the strict hard constraints. Check alternative windows below or slightly relax thresholds.
                </div>
              ) : (
                result.recommended_windows.slice(0, 5).map((win, idx) => (
                  <div
                    key={idx}
                    className="p-3 bg-slate-900/80 hover:bg-slate-900 border border-slate-800 hover:border-cyan-500/40 rounded-xl flex flex-wrap items-center justify-between gap-3 transition-all"
                  >
                    <div className="flex items-center gap-3">
                      <span className="w-6 h-6 rounded-full bg-cyan-950 border border-cyan-500/40 text-cyan-300 text-xs font-mono flex items-center justify-center font-bold">
                        #{idx + 1}
                      </span>
                      <div>
                        <div className="text-xs font-semibold text-slate-100 font-mono">
                          {win.start_time_iso.slice(0, 16)} UTC → {win.end_time_iso.slice(0, 16)} UTC
                        </div>
                        <div className="flex flex-wrap items-center gap-3 text-[11px] text-slate-400 mt-1 font-mono">
                          {Object.entries(win.site_evaluations).map(([sid, se]) => (
                            <span key={sid} className="flex items-center gap-1.5">
                              <span className="text-slate-300 font-sans">{se.site_name}:</span>
                              <span className="text-amber-300">{se.metrics.sun_availability_pct}% Sun</span>
                              <span className="text-slate-600">|</span>
                              <span className="text-cyan-300">{se.metrics.earth_availability_pct}% DTE</span>
                              <span className="text-slate-600">|</span>
                              <span className="text-rose-300">{se.metrics.longest_shadow_gap_hours}h gap</span>
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>

                    <button
                      onClick={() => {
                        onApplyWindow(win.start_time_iso, win.duration_days);
                        onClose();
                      }}
                      className="px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-medium flex items-center gap-1.5 shadow transition-all cursor-pointer"
                    >
                      <span>Apply Window</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))
              )}
            </div>
            <details className="text-xs text-slate-400"><summary>Transparent ranking formula</summary><p className="mt-2">{result.provenance?.ranking||'Hard constraints first, then the selected priority score.'}</p></details>
            {result.alternative_windows.length>0&&<section className="flex flex-col gap-3"><h3 className="text-xs text-amber-300">Closest alternatives — constraints remain unmet or unknown</h3>{result.alternative_windows.map((win,i)=><article key={win.start_time_iso} className="p-3 border border-slate-800 rounded-xl text-xs"><strong>{win.start_time_iso.slice(0,16)} UTC · score {win.composite_score}</strong>{Object.entries(win.site_evaluations).map(([id,se])=><p className="mt-2 text-slate-400" key={id}>{se.site_name}: {se.passed?'Pass':se.metrics.coverage==='unknown'?'Unknown':'Fail'} — {se.violations.length?se.violations.join('; '):'Meets configured window constraints'}</p>)}</article>)}</section>}
          </div>
        )}
      </div>
    </div>
  );
};
