import React, { useState, useEffect, useRef } from 'react';
import { EvaluatedSiteData } from '../types';
import {
  Play,
  Pause,
  RotateCcw,
  FastForward,
  Clock,
  Sun,
  Radio,
  Activity,
} from 'lucide-react';

interface SynchronizedTimelineProps {
  evaluatedSites: Record<string, EvaluatedSiteData>;
  selectedSiteIds: string[];
  currentStepIndex: number;
  onStepChange: (index: number) => void;
}

export const SynchronizedTimeline: React.FC<SynchronizedTimelineProps> = ({
  evaluatedSites,
  selectedSiteIds,
  currentStepIndex,
  onStepChange,
}) => {
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [speedMultiplier, setSpeedMultiplier] = useState<number>(1);

  // Reference timestamps from first site
  const primarySiteId = selectedSiteIds[0];
  const primaryData = evaluatedSites[primarySiteId];
  const timestamps = primaryData?.timestamps || [];
  const totalSteps = timestamps.length;

  const currentStepRef = useRef(currentStepIndex);
  currentStepRef.current = currentStepIndex;

  // Animation player loop
  useEffect(() => {
    let timer: any;
    if (isPlaying && totalSteps > 0) {
      timer = setInterval(() => {
        const next = currentStepRef.current + 1;
        if (next >= totalSteps) {
          setIsPlaying(false);
          onStepChange(totalSteps - 1);
        } else {
          onStepChange(next);
        }
      }, 1000 / (speedMultiplier * 2));
    }
    return () => clearInterval(timer);
  }, [isPlaying, speedMultiplier, totalSteps, onStepChange]);

  const currentTs = timestamps[currentStepIndex] || (Date.now() / 1000);
  const currentIso = new Date(currentTs * 1000).toISOString().replace('.000Z', ' UTC');

  const siteColors = ['#38bdf8', '#fbbf24', '#c084fc'];

  const getStateColor = (state: number) => {
    switch (state) {
      case 1: return '#10b981'; // Nominal Science
      case 2: return '#f59e0b'; // Autonomous Day
      case 3: return '#8b5cf6'; // Tethered Eclipse
      case 4: return '#ef4444'; // Total Blackout
      default: return '#334155';
    }
  };

  const getStateName = (state: number) => {
    switch (state) {
      case 1: return 'State 1: Nominal Science (Sun + Earth)';
      case 2: return 'State 2: Autonomous Day (Sun Only)';
      case 3: return 'State 3: Tethered Eclipse (Earth Only)';
      case 4: return 'State 4: Total Blackout (Neither)';
      default: return 'Unknown';
    }
  };

  return (
    <div className="glass-panel rounded-2xl p-4 flex flex-col gap-3">
      {/* Playback Controls & Scrubber Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsPlaying(!isPlaying)}
            className="w-8 h-8 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white flex items-center justify-center transition-all shadow-md"
            title={isPlaying ? "Pause simulation" : "Play simulation"}
          >
            {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 ml-0.5" />}
          </button>
          <button
            onClick={() => {
              setIsPlaying(false);
              onStepChange(0);
            }}
            className="w-8 h-8 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 flex items-center justify-center transition-all"
            title="Reset to mission start"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>

          {/* Speed multiplier selector */}
          <div className="flex items-center bg-slate-900 border border-slate-800 rounded-lg p-0.5 text-xs font-mono">
            {[1, 5, 24].map((spd) => (
              <button
                key={spd}
                onClick={() => setSpeedMultiplier(spd)}
                className={`px-2 py-0.5 rounded ${
                  speedMultiplier === spd
                    ? 'bg-cyan-600 text-white'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {spd}x
              </button>
            ))}
          </div>

          <div className="flex items-center gap-1.5 text-xs font-mono text-cyan-300 bg-slate-900/90 px-3 py-1 rounded-lg border border-cyan-900/40">
            <Clock className="w-3.5 h-3.5 text-cyan-400" />
            <span>{currentIso}</span>
          </div>
        </div>

        {/* State Regime Legend */}
        <div className="hidden xl:flex items-center gap-3 text-[11px]">
          <span className="flex items-center gap-1.5 text-emerald-300">
            <span className="w-2.5 h-2.5 rounded-sm bg-emerald-500" />
            Nominal Science
          </span>
          <span className="flex items-center gap-1.5 text-amber-300">
            <span className="w-2.5 h-2.5 rounded-sm bg-amber-500" />
            Autonomous Day
          </span>
          <span className="flex items-center gap-1.5 text-purple-300">
            <span className="w-2.5 h-2.5 rounded-sm bg-purple-500" />
            Tethered Eclipse
          </span>
          <span className="flex items-center gap-1.5 text-rose-300">
            <span className="w-2.5 h-2.5 rounded-sm bg-rose-500" />
            Total Blackout
          </span>
        </div>
      </div>

      {/* Interactive Time Scrubber Slider */}
      <div className="relative w-full">
        <input
          type="range"
          min="0"
          max={Math.max(0, totalSteps - 1)}
          value={currentStepIndex}
          onChange={(e) => onStepChange(Number(e.target.value))}
          className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer"
        />
      </div>

      {/* Synchronized Multi-Row Gantt Bars Per Site */}
      <div className="flex flex-col gap-3 pt-1">
        {selectedSiteIds.map((sid, idx) => {
          const sdata = evaluatedSites[sid];
          if (!sdata) return null;
          const site = sdata.site_info;
          const color = siteColors[idx % siteColors.length];
          const currState = sdata.operational_states[currentStepIndex] || 4;

          return (
            <div
              key={sid}
              className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-3 flex flex-col gap-2"
            >
              {/* Site row header */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span
                    className="w-2 h-2 rounded-full"
                    style={{ backgroundColor: color }}
                  />
                  <span className="text-xs font-semibold text-slate-200">
                    {site.name}
                  </span>
                  <span className="text-[10px] text-slate-400 font-mono">
                    ({site.region})
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <span
                    className="text-[10px] px-2 py-0.5 rounded font-mono font-medium border"
                    style={{
                      backgroundColor: `${getStateColor(currState)}15`,
                      borderColor: `${getStateColor(currState)}40`,
                      color: getStateColor(currState),
                    }}
                  >
                    {getStateName(currState)}
                  </span>
                </div>
              </div>

              {/* Row 1: Solar Disk Exposure Fraction f(t) */}
              <div className="flex items-center gap-2 text-[10px]">
                <span className="w-16 text-amber-400 flex items-center gap-1 font-mono">
                  <Sun className="w-3 h-3" /> Sun f(t)
                </span>
                <div className="flex-1 h-3.5 bg-slate-950 rounded flex overflow-hidden relative">
                  {sdata.solar_fractions.map((f, i) => (
                    <div
                      key={i}
                      className="flex-1 h-full"
                      style={{
                        backgroundColor: '#f59e0b',
                        opacity: f,
                      }}
                      title={`Step ${i}: Sun fraction ${(f * 100).toFixed(0)}%`}
                    />
                  ))}
                  {/* Current step cursor line */}
                  <div
                    className="absolute top-0 bottom-0 w-0.5 bg-white z-10 pointer-events-none shadow"
                    style={{
                      left: `${(currentStepIndex / Math.max(1, totalSteps - 1)) * 100}%`,
                    }}
                  />
                </div>
              </div>

              {/* Row 2: Direct-to-Earth Geometric Visibility C(t) */}
              <div className="flex items-center gap-2 text-[10px]">
                <span className="w-16 text-cyan-400 flex items-center gap-1 font-mono">
                  <Radio className="w-3 h-3" /> Earth DTE
                </span>
                <div className="flex-1 h-3.5 bg-slate-950 rounded flex overflow-hidden relative">
                  {sdata.dte_visibility.map((c, i) => (
                    <div
                      key={i}
                      className="flex-1 h-full"
                      style={{
                        backgroundColor: c === 1 ? '#06b6d4' : '#020617',
                        opacity: c === 1 ? 0.9 : 0.4,
                      }}
                      title={`Step ${i}: Earth ${c === 1 ? 'Visible' : 'Occulted'}`}
                    />
                  ))}
                  {/* Current step cursor line */}
                  <div
                    className="absolute top-0 bottom-0 w-0.5 bg-white z-10 pointer-events-none shadow"
                    style={{
                      left: `${(currentStepIndex / Math.max(1, totalSteps - 1)) * 100}%`,
                    }}
                  />
                </div>
              </div>

              {/* Row 3: 4 Operational Regimes States Bar */}
              <div className="flex items-center gap-2 text-[10px]">
                <span className="w-16 text-slate-400 flex items-center gap-1 font-mono">
                  <Activity className="w-3 h-3" /> State 1-4
                </span>
                <div className="flex-1 h-3.5 bg-slate-950 rounded flex overflow-hidden relative">
                  {sdata.operational_states.map((st, i) => (
                    <div
                      key={i}
                      className="flex-1 h-full"
                      style={{
                        backgroundColor: getStateColor(st),
                      }}
                      title={`Step ${i}: ${getStateName(st)}`}
                    />
                  ))}
                  {/* Current step cursor line */}
                  <div
                    className="absolute top-0 bottom-0 w-0.5 bg-white z-10 pointer-events-none shadow"
                    style={{
                      left: `${(currentStepIndex / Math.max(1, totalSteps - 1)) * 100}%`,
                    }}
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
