import React, { useState } from 'react';
import { EvaluatedSiteData, PowerConfig } from '../types';
import {
  BatteryCharging,
  X,
  Zap,
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  Sliders,
} from 'lucide-react';

interface PowerSimulationDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  evaluatedSites: Record<string, EvaluatedSiteData>;
  selectedSiteIds: string[];
  powerConfig: PowerConfig;
  onUpdatePowerConfig: (cfg: PowerConfig) => void;
}

export const PowerSimulationDrawer: React.FC<PowerSimulationDrawerProps> = ({
  isOpen,
  onClose,
  evaluatedSites,
  selectedSiteIds,
  powerConfig,
  onUpdatePowerConfig,
}) => {
  if (!isOpen) return null;

  const siteColors = ['#38bdf8', '#fbbf24', '#c084fc'];
  const primarySiteId = selectedSiteIds[0];
  const primaryData = evaluatedSites[primarySiteId];
  const powerSim = primaryData?.power_simulation;

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4 overflow-y-auto">
      <div className="glass-panel w-full max-w-4xl rounded-2xl border border-emerald-500/30 p-6 flex flex-col gap-6 max-h-[90vh] overflow-y-auto shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center">
              <BatteryCharging className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-slate-100">
                  Solar Array & Battery Sandbox
                </h2>
                <span className="text-[10px] bg-emerald-950 px-2 py-0.5 rounded font-mono text-emerald-300 border border-emerald-800">
                  [Assumed] Hardware Model
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Model instantaneous generation, charge/discharge cycles, and battery depth of discharge
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

        {/* Sliders Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 bg-slate-900/60 border border-slate-800 p-4 rounded-xl">
          {/* Panel Area */}
          <div className="flex flex-col gap-1">
            <label className="text-xs text-slate-300 font-medium flex justify-between">
              <span>Array Surface Area</span>
              <span className="text-emerald-300 font-mono">{powerConfig.panel_area_m2} m²</span>
            </label>
            <input
              type="range"
              min="1.0"
              max="10.0"
              step="0.5"
              value={powerConfig.panel_area_m2}
              onChange={(e) =>
                onUpdatePowerConfig({
                  ...powerConfig,
                  panel_area_m2: Number(e.target.value),
                })
              }
            />
          </div>

          {/* Spacecraft Base Load */}
          <div className="flex flex-col gap-1">
            <label className="text-xs text-slate-300 font-medium flex justify-between">
              <span>Spacecraft Base Load</span>
              <span className="text-amber-300 font-mono">{powerConfig.spacecraft_load_w} W</span>
            </label>
            <input
              type="range"
              min="40"
              max="400"
              step="10"
              value={powerConfig.spacecraft_load_w}
              onChange={(e) =>
                onUpdatePowerConfig({
                  ...powerConfig,
                  spacecraft_load_w: Number(e.target.value),
                })
              }
            />
          </div>

          {/* Battery Capacity */}
          <div className="flex flex-col gap-1">
            <label className="text-xs text-slate-300 font-medium flex justify-between">
              <span>Battery Capacity</span>
              <span className="text-cyan-300 font-mono">{powerConfig.battery_capacity_wh} Wh</span>
            </label>
            <input
              type="range"
              min="800"
              max="6000"
              step="200"
              value={powerConfig.battery_capacity_wh}
              onChange={(e) =>
                onUpdatePowerConfig({
                  ...powerConfig,
                  battery_capacity_wh: Number(e.target.value),
                })
              }
            />
          </div>
        </div>

        {/* Results & Metrics */}
        {powerSim ? (
          <div className="flex flex-col gap-4">
            {/* KPI Cards */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="bg-slate-900/80 border border-slate-800 p-3 rounded-xl flex flex-col gap-1">
                <span className="text-[11px] text-slate-400">Minimum Battery SoC</span>
                <span
                  className={`text-lg font-bold font-mono ${
                    powerSim.summary.min_soc_pct < 20
                      ? 'text-rose-400'
                      : (powerSim.summary.min_soc_pct < 40 ? 'text-amber-400' : 'text-emerald-400')
                  }`}
                >
                  {powerSim.summary.min_soc_pct.toFixed(1)}%
                </span>
                <span className="text-[10px] text-slate-500 font-mono">
                  {powerSim.summary.min_energy_wh.toFixed(0)} Wh remaining
                </span>
              </div>

              <div className="bg-slate-900/80 border border-slate-800 p-3 rounded-xl flex flex-col gap-1">
                <span className="text-[11px] text-slate-400">Reserve Margin Hours</span>
                <span className="text-lg font-bold font-mono text-cyan-300">
                  {powerSim.summary.reserve_breach_hours.toFixed(1)} h
                </span>
                <span className="text-[10px] text-slate-500 font-mono">below 20% reserve</span>
              </div>

              <div className="bg-slate-900/80 border border-slate-800 p-3 rounded-xl flex flex-col gap-1">
                <span className="text-[11px] text-slate-400">Unmet Energy Demand</span>
                <span
                  className={`text-lg font-bold font-mono ${
                    powerSim.summary.total_unmet_demand_wh > 0 ? 'text-rose-400' : 'text-emerald-400'
                  }`}
                >
                  {powerSim.summary.total_unmet_demand_wh.toFixed(1)} Wh
                </span>
                <span className="text-[10px] text-slate-500 font-mono">blackout shortfall</span>
              </div>

              <div className="bg-slate-900/80 border border-slate-800 p-3 rounded-xl flex flex-col gap-1">
                <span className="text-[11px] text-slate-400">Survival Status</span>
                {powerSim.summary.total_unmet_demand_wh === 0 ? (
                  <span className="text-xs font-semibold text-emerald-300 flex items-center gap-1 mt-1">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    Load Fully Met
                  </span>
                ) : (
                  <span className="text-xs font-semibold text-rose-300 flex items-center gap-1 mt-1">
                    <ShieldAlert className="w-4 h-4 text-rose-400" />
                    Unmet Demand
                  </span>
                )}
                <span className="text-[10px] text-slate-500 font-mono">under inputs</span>
              </div>
            </div>

            {/* Battery SoC Curve SVG */}
            <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-xl flex flex-col gap-2">
              <span className="text-xs font-semibold text-slate-200">
                Battery State of Charge (%) vs Mission Timeline
              </span>
              <div className="h-28 w-full">
                <svg viewBox="0 0 600 100" className="w-full h-full">
                  <line x1="0" y1="80" x2="600" y2="80" stroke="#ef4444" strokeWidth="0.8" strokeDasharray="3 3" />
                  <text x="5" y="76" fill="#ef4444" fontSize="8" fontFamily="monospace">20% Reserve Margin</text>
                  
                  {/* SoC polyline */}
                  <polyline
                    fill="none"
                    stroke="#10b981"
                    strokeWidth="1.5"
                    points={powerSim.time_series.battery_soc_pct
                      .map((soc, i, arr) => `${(i / Math.max(1, arr.length - 1)) * 600},${100 - soc}`)
                      .join(' ')}
                  />
                </svg>
              </div>
            </div>

            <div className="p-3 bg-slate-900/50 border border-slate-800 rounded-xl text-[11px] text-slate-400">
              <strong>Scientific Disclosure:</strong> This figure models assumed electrical energy balance given user-declared hardware efficiency. It is an operational planning aid, not an agency-certified flight survival model.
            </div>
          </div>
        ) : (
          <div className="p-6 bg-slate-900/40 border border-slate-800 rounded-xl text-center text-xs text-slate-400">
            Evaluating power model against current mission horizon...
          </div>
        )}
      </div>
    </div>
  );
};
