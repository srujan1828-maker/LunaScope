import React, { useState, useEffect } from 'react';
import { LandingSite } from '../types';
import { ArrowUpCircle, X, Sparkles, Check, TrendingUp } from 'lucide-react';

interface MastSensitivityModalProps {
  isOpen: boolean;
  onClose: () => void;
  site: LandingSite | null;
  startDateIso: string;
  durationDays: number;
  currentMastHeightM: number;
  onApplyMastHeight: (height: number) => void;
}

export const MastSensitivityModal: React.FC<MastSensitivityModalProps> = ({
  isOpen,
  onClose,
  site,
  startDateIso,
  durationDays,
  currentMastHeightM,
  onApplyMastHeight,
}) => {
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [sweepData, setSweepData] = useState<any[]>([]);

  useEffect(() => {
    if (isOpen && site) {
      setIsLoading(true);
      const startDt = new Date(startDateIso);
      const endDt = new Date(startDt.getTime() + durationDays * 86400 * 1000);

      fetch('/api/simulation/mast-sensitivity', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          site_id: site.site_id,
          start_time_iso: startDt.toISOString(),
          end_time_iso: endDt.toISOString(),
          mast_heights: [0.5, 1.0, 2.0, 3.5, 5.0, 7.5, 10.0, 15.0],
        }),
      })
        .then((res) => res.json())
        .then((data) => setSweepData(data.sweep || []))
        .catch((e) => console.error(e))
        .finally(() => setIsLoading(false));
    }
  }, [isOpen, site, startDateIso, durationDays]);

  if (!isOpen || !site) return null;

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4 overflow-y-auto">
      <div className="glass-panel w-full max-w-3xl rounded-2xl border border-emerald-500/30 p-6 flex flex-col gap-5 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center">
              <ArrowUpCircle className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-100">
                Lander Mast Height Sensitivity Sweep
              </h2>
              <p className="text-xs text-slate-400">
                Parametric analysis showing how mast height clears crater rim shadow obstructions
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

        {/* Target Site Info */}
        <div className="flex items-center justify-between p-3 bg-slate-900/60 border border-slate-800 rounded-xl text-xs">
          <div className="flex items-center gap-2">
            <span className="text-slate-400">Selected Site:</span>
            <span className="font-bold text-emerald-300">{site.name}</span>
          </div>
          <div className="flex items-center gap-2 font-mono text-slate-400">
            <span>Base Elevation: {site.elevation_m > 0 ? `+${site.elevation_m}` : site.elevation_m}m</span>
            <span>•</span>
            <span>Current Mast: {currentMastHeightM}m</span>
          </div>
        </div>

        {/* Sweep Table */}
        {isLoading ? (
          <div className="py-12 flex flex-col items-center justify-center gap-2 text-xs text-slate-400 font-mono">
            <Sparkles className="w-5 h-5 text-emerald-400 animate-spin" />
            <span>Raycasting horizons across 8 mast heights...</span>
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 font-medium">
                    <th className="py-2 px-3">Mast Height</th>
                    <th className="py-2 px-3">Sun Hours Gain</th>
                    <th className="py-2 px-3">Shadow Reduction</th>
                    <th className="py-2 px-3">Sun Avail (%)</th>
                    <th className="py-2 px-3">Mean Horizon El</th>
                    <th className="py-2 px-3 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  {sweepData.map((row) => {
                    const isCurrent = Math.abs(row.mast_height_m - currentMastHeightM) < 0.1;
                    return (
                      <tr
                        key={row.mast_height_m}
                        className={`hover:bg-slate-900/40 ${isCurrent ? 'bg-emerald-950/20' : ''}`}
                      >
                        <td className="py-2.5 px-3 font-semibold text-slate-200">
                          {row.mast_height_m} m
                          {isCurrent && (
                            <span className="ml-2 text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-normal">
                              Active
                            </span>
                          )}
                        </td>
                        <td className="py-2.5 px-3 text-amber-300">
                          {row.sun_gain_hours > 0 ? `+${row.sun_gain_hours} h` : 'Baseline'}
                        </td>
                        <td className="py-2.5 px-3 text-emerald-400">
                          {row.shadow_reduction_hours > 0 ? `-${row.shadow_reduction_hours} h` : '—'}
                        </td>
                        <td className="py-2.5 px-3 text-slate-300">
                          {row.metrics.sun_availability_pct.toFixed(1)}%
                        </td>
                        <td className="py-2.5 px-3 text-slate-400">
                          {row.horizon_mean_elevation_deg}°
                        </td>
                        <td className="py-2.5 px-3 text-right">
                          <button
                            onClick={() => {
                              onApplyMastHeight(row.mast_height_m);
                              onClose();
                            }}
                            disabled={isCurrent}
                            className={`px-2.5 py-1 rounded text-[11px] font-sans font-medium transition-all ${
                              isCurrent
                                ? 'bg-slate-800 text-slate-500 cursor-default'
                                : 'bg-emerald-600 hover:bg-emerald-500 text-white cursor-pointer shadow'
                            }`}
                          >
                            {isCurrent ? 'Current' : 'Apply'}
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            <div className="p-3 bg-slate-900/40 border border-slate-800 rounded-xl text-[11px] text-slate-400 flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-emerald-400 shrink-0" />
              <span>
                Raising mast height decreases the apparent skyline elevation angle, enabling the lander solar array and antenna to clear local crater ridges and shadows.
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
