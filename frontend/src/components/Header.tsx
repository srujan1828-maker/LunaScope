import React from 'react';
import {
  Compass,
  ArrowRightLeft,
  BatteryCharging,
  BookOpen,
  Download,
  Moon,
  Layers,
  Sparkles,
  Target,
  ArrowUpCircle,
} from 'lucide-react';

interface HeaderProps {
  mode: 'explore' | 'plan';
  onToggleMode: (mode: 'explore' | 'plan') => void;
  onOpenWindowFinder: () => void;
  onOpenContingency: () => void;
  onOpenPower: () => void;
  onOpenDispersion: () => void;
  onOpenMastSensitivity: () => void;
  onOpenProvenance: () => void;
  onOpenExport: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  mode,
  onToggleMode,
  onOpenWindowFinder,
  onOpenContingency,
  onOpenPower,
  onOpenDispersion,
  onOpenMastSensitivity,
  onOpenProvenance,
  onOpenExport,
}) => {
  return (
    <header className="sticky top-0 z-40 bg-slate-950/80 backdrop-blur-md border-b border-cyan-900/30 px-6 py-3 flex flex-wrap items-center justify-between gap-4">
      {/* Brand & Subtitle */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-600 via-sky-500 to-amber-400 p-0.5 shadow-lg shadow-cyan-500/20 flex items-center justify-center">
          <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
            <Moon className="w-5 h-5 text-cyan-400" />
          </div>
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold tracking-tight bg-gradient-to-r from-cyan-200 via-sky-300 to-amber-200 bg-clip-text text-transparent">
              LunaScope 2.0
            </h1>
            <span className="text-xs px-2 py-0.5 rounded-full bg-cyan-950/80 border border-cyan-700/50 text-cyan-300 font-mono">
              Live Real-Time Engine
            </span>
          </div>
          <p className="text-xs text-slate-400 hidden sm:block">
            Lunar South Pole Real-Time Simulation • Ephemerides • Horizon Raycasting
          </p>
        </div>
      </div>

      {/* Center: Mode Switcher */}
      <div className="flex items-center bg-slate-900/90 border border-slate-800 rounded-lg p-1 text-xs">
        <button
          onClick={() => onToggleMode('explore')}
          className={`px-3 py-1.5 rounded-md font-medium transition-all ${
            mode === 'explore'
              ? 'bg-cyan-600 text-white shadow-sm'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <span className="flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5" />
            Explore Mode
          </span>
        </button>
        <button
          onClick={() => onToggleMode('plan')}
          className={`px-3 py-1.5 rounded-md font-medium transition-all ${
            mode === 'plan'
              ? 'bg-cyan-600 text-white shadow-sm'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <span className="flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5" />
            Plan Mode
          </span>
        </button>
      </div>

      {/* Right: Signature Tools & Action Buttons */}
      <div className="flex items-center flex-wrap gap-2">
        <button
          onClick={onOpenWindowFinder}
          className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border border-amber-500/30 transition-all flex items-center gap-1.5 shadow-sm"
        >
          <Compass className="w-3.5 h-3.5 text-amber-400" />
          Find Windows
        </button>

        <button
          onClick={onOpenContingency}
          className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 transition-all flex items-center gap-1.5"
        >
          <ArrowRightLeft className="w-3.5 h-3.5 text-indigo-400" />
          Contingency
        </button>

        <button
          onClick={onOpenPower}
          className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 transition-all flex items-center gap-1.5"
        >
          <BatteryCharging className="w-3.5 h-3.5 text-emerald-400" />
          Power
        </button>

        {mode === 'plan' && (
          <>
            <button
              onClick={onOpenDispersion}
              className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-sky-500/10 hover:bg-sky-500/20 text-sky-300 border border-sky-500/30 transition-all flex items-center gap-1.5"
            >
              <Target className="w-3.5 h-3.5 text-sky-400" />
              Dispersion
            </button>

            <button
              onClick={onOpenMastSensitivity}
              className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-teal-500/10 hover:bg-teal-500/20 text-teal-300 border border-teal-500/30 transition-all flex items-center gap-1.5"
            >
              <ArrowUpCircle className="w-3.5 h-3.5 text-teal-400" />
              Mast Sweep
            </button>
          </>
        )}

        <button
          onClick={onOpenProvenance}
          className="p-1.5 text-xs rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 transition-all"
          title="Data Provenance & Citations"
        >
          <BookOpen className="w-4 h-4 text-slate-400" />
        </button>

        <button
          onClick={onOpenExport}
          className="p-1.5 text-xs rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 transition-all"
          title="Export Scenario (JSON / CSV)"
        >
          <Download className="w-4 h-4 text-cyan-400" />
        </button>
      </div>
    </header>
  );
};

