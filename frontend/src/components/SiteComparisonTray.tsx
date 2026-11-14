import React from 'react';
import { LandingSite } from '../types';
import { X, Calendar, Clock, ArrowUpCircle, Radio } from 'lucide-react';

interface SiteComparisonTrayProps {
  selectedSites: LandingSite[];
  onRemoveSite: (siteId: string) => void;
  startDateIso: string;
  onStartDateChange: (val: string) => void;
  durationDays: number;
  onDurationChange: (val: number) => void;
  mastHeightM: number;
  onMastHeightChange: (val: number) => void;
  antennaMarginDeg: number;
  onAntennaMarginChange: (val: number) => void;
  mode: 'explore' | 'plan';
}

export const SiteComparisonTray: React.FC<SiteComparisonTrayProps> = ({
  selectedSites,
  onRemoveSite,
  startDateIso,
  onStartDateChange,
  durationDays,
  onDurationChange,
  mastHeightM,
  onMastHeightChange,
  antennaMarginDeg,
  onAntennaMarginChange,
  mode,
}) => {
  const siteColors = ['#38bdf8', '#fbbf24', '#c084fc'];

  return (
    <div className="glass-panel rounded-2xl p-4 flex flex-col gap-3">
      {/* Top row: Site selection pills & status */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
            Comparison Tray:
          </span>
          <div className="flex flex-wrap items-center gap-2">
            {selectedSites.map((site, index) => {
              const color = siteColors[index % siteColors.length];
              return (
                <div
                  key={site.site_id}
                  className="flex items-center gap-2 px-3 py-1 rounded-lg text-xs font-medium border"
                  style={{
                    backgroundColor: `${color}15`,
                    borderColor: `${color}40`,
                    color: color,
                  }}
                >
                  <span
                    className="w-2.5 h-2.5 rounded-full"
                    style={{ backgroundColor: color }}
                  />
                  <span>{site.name}</span>
                  <span className="text-[10px] text-slate-400 font-mono">
                    ({site.elevation_m > 0 ? `+${site.elevation_m}` : site.elevation_m}m)
                  </span>
                  {selectedSites.length > 1 && (
                    <button
                      onClick={() => onRemoveSite(site.site_id)}
                      className="hover:text-red-400 transition-colors ml-1 p-0.5"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        <span className="text-[11px] text-slate-400">
          Comparing {selectedSites.length} of max 3 sites
        </span>
      </div>

      {/* Controls row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 pt-2 border-t border-slate-800/80">
        {/* Start Date */}
        <div className="flex flex-col gap-1">
          <label className="text-[11px] text-slate-400 flex items-center gap-1.5 font-medium">
            <Calendar className="w-3.5 h-3.5 text-cyan-400" />
            UTC Start Date
          </label>
          <input
            type="datetime-local"
            value={startDateIso.slice(0, 16)}
            onChange={(e) => onStartDateChange(e.target.value ? `${e.target.value}:00Z` : startDateIso)}
            className="bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-cyan-500"
          />
        </div>

        {/* Mission Duration */}
        <div className="flex flex-col gap-1">
          <label className="text-[11px] text-slate-400 flex items-center justify-between font-medium">
            <span className="flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-amber-400" />
              Duration
            </span>
            <span className="text-amber-300 font-mono text-xs">{durationDays} Days</span>
          </label>
          <input
            type="range"
            min="1"
            max="28"
            step="1"
            value={durationDays}
            onChange={(e) => onDurationChange(Number(e.target.value))}
            className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer"
          />
        </div>

        {/* Mast Height */}
        <div className="flex flex-col gap-1">
          <label className="text-[11px] text-slate-400 flex items-center justify-between font-medium">
            <span className="flex items-center gap-1.5">
              <ArrowUpCircle className="w-3.5 h-3.5 text-emerald-400" />
              Lander Mast Height
            </span>
            <span className="text-emerald-300 font-mono text-xs">{mastHeightM.toFixed(1)} m</span>
          </label>
          <input
            type="range"
            min="0.5"
            max="20.0"
            step="0.5"
            value={mastHeightM}
            onChange={(e) => onMastHeightChange(Number(e.target.value))}
            className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer"
          />
        </div>

        {/* Antenna Margin (Disclosed in Plan Mode) */}
        {mode === 'plan' ? (
          <div className="flex flex-col gap-1">
            <label className="text-[11px] text-slate-400 flex items-center justify-between font-medium">
              <span className="flex items-center gap-1.5">
                <Radio className="w-3.5 h-3.5 text-indigo-400" />
                DTE Clearance Margin
              </span>
              <span className="text-indigo-300 font-mono text-xs">{antennaMarginDeg.toFixed(1)}°</span>
            </label>
            <input
              type="range"
              min="0.0"
              max="5.0"
              step="0.25"
              value={antennaMarginDeg}
              onChange={(e) => onAntennaMarginChange(Number(e.target.value))}
              className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer"
            />
          </div>
        ) : (
          <div className="flex items-center justify-center p-2 rounded-lg bg-slate-900/50 border border-slate-800/50 text-[11px] text-slate-400">
            <span>Switch to <strong>Plan Mode</strong> for RF margins & sensitivity</span>
          </div>
        )}
      </div>
    </div>
  );
};
