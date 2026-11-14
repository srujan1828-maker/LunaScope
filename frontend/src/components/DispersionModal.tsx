import React, { useState, useEffect } from 'react';
import { LandingSite } from '../types';
import { Target, X, ShieldAlert, Sparkles, RefreshCw } from 'lucide-react';

interface DispersionModalProps {
  isOpen: boolean;
  onClose: () => void;
  site: LandingSite | null;
  startDateIso: string;
  durationDays: number;
  mastHeightM: number;
}

export const DispersionModal: React.FC<DispersionModalProps> = ({
  isOpen,
  onClose,
  site,
  startDateIso,
  durationDays,
  mastHeightM,
}) => {
  const [semiMajorM, setSemiMajorM] = useState<number>(250.0);
  const [semiMinorM, setSemiMinorM] = useState<number>(120.0);
  const [numSamples, setNumSamples] = useState<number>(17);

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [result, setResult] = useState<any>(null);

  const fetchDispersion = async () => {
    if (!site) return;
    setIsLoading(true);
    try {
      const startDt = new Date(startDateIso);
      const endDt = new Date(startDt.getTime() + durationDays * 86400 * 1000);
      const res = await fetch('/api/simulation/dispersion', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          site_id: site.site_id,
          start_time_iso: startDt.toISOString(),
          end_time_iso: endDt.toISOString(),
          semi_major_m: semiMajorM,
          semi_minor_m: semiMinorM,
          num_samples: numSamples,
          mast_height_m: mastHeightM,
        }),
      });
      const data = await res.json();
      setResult(data);
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && site) {
      fetchDispersion();
    }
  }, [isOpen, site]);

  if (!isOpen || !site) return null;

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4 overflow-y-auto">
      <div className="glass-panel w-full max-w-3xl rounded-2xl border border-cyan-500/30 p-6 flex flex-col gap-5 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-cyan-500/20 border border-cyan-500/30 flex items-center justify-center">
              <Target className="w-5 h-5 text-cyan-400" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-100">
                Monte Carlo Landing Dispersion & Terrain Sensitivity
              </h2>
              <p className="text-xs text-slate-400">
                Evaluate shadow gradient & mission risk bounds across the touchdown error ellipse
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

        {/* Controls */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 bg-slate-900/60 border border-slate-800 p-3 rounded-xl text-xs">
          <div className="flex flex-col gap-1">
            <label className="text-slate-300 font-medium flex justify-between">
              <span>Semi-Major Axis:</span>
              <span className="text-cyan-300 font-mono">{semiMajorM} m</span>
            </label>
            <input
              type="range"
              min="50"
              max="600"
              step="25"
              value={semiMajorM}
              onChange={(e) => setSemiMajorM(Number(e.target.value))}
            />
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-slate-300 font-medium flex justify-between">
              <span>Semi-Minor Axis:</span>
              <span className="text-cyan-300 font-mono">{semiMinorM} m</span>
            </label>
            <input
              type="range"
              min="25"
              max="400"
              step="25"
              value={semiMinorM}
              onChange={(e) => setSemiMinorM(Number(e.target.value))}
            />
          </div>

          <div className="flex items-end">
            <button
              onClick={fetchDispersion}
              disabled={isLoading}
              className="w-full py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg font-semibold flex items-center justify-center gap-1.5 transition-all shadow"
            >
              {isLoading ? (
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Sparkles className="w-3.5 h-3.5" />
              )}
              <span>Sample Ellipse</span>
            </button>
          </div>
        </div>

        {/* Results */}
        {result && (
          <div className="flex flex-col gap-4">
            {/* Robustness badge */}
            <div className="p-3 bg-slate-900/80 border border-slate-800 rounded-xl flex items-center justify-between">
              <div>
                <span className="text-xs text-slate-400 block">Landing Site Robustness:</span>
                <span className="text-sm font-bold text-cyan-300">{result.robustness}</span>
              </div>
              <p className="text-xs text-slate-300 max-w-sm text-right">
                {result.robustness_notes}
              </p>
            </div>

            {/* Dispersion Envelope Metrics */}
            <div className="grid grid-cols-3 gap-3 text-xs font-mono">
              <div className="bg-slate-900/60 border border-slate-800 p-3 rounded-xl flex flex-col gap-1">
                <span className="text-[11px] font-sans text-amber-400">Sun Availability Bounds</span>
                <span className="text-sm font-bold text-amber-300">
                  {result.envelope.sun_availability_pct.min}% – {result.envelope.sun_availability_pct.max}%
                </span>
                <span className="text-[10px] text-slate-400">
                  Median: {result.envelope.sun_availability_pct.median}% (Spread: {result.envelope.sun_availability_pct.spread}%)
                </span>
              </div>

              <div className="bg-slate-900/60 border border-slate-800 p-3 rounded-xl flex flex-col gap-1">
                <span className="text-[11px] font-sans text-rose-400">Longest Shadow Gap</span>
                <span className="text-sm font-bold text-rose-300">
                  {result.envelope.longest_shadow_gap_hours.min}h – {result.envelope.longest_shadow_gap_hours.max}h
                </span>
                <span className="text-[10px] text-slate-400">
                  Median gap: {result.envelope.longest_shadow_gap_hours.median}h
                </span>
              </div>

              <div className="bg-slate-900/60 border border-slate-800 p-3 rounded-xl flex flex-col gap-1">
                <span className="text-[11px] font-sans text-cyan-400">Earth LOS Availability</span>
                <span className="text-sm font-bold text-cyan-300">
                  {result.envelope.earth_availability_pct.min}% – {result.envelope.earth_availability_pct.max}%
                </span>
                <span className="text-[10px] text-slate-400">
                  Median: {result.envelope.earth_availability_pct.median}%
                </span>
              </div>
            </div>

            {/* Ellipse Dispersion Visual Plot */}
            <div className="h-52 bg-slate-950 rounded-xl border border-slate-800 p-2 flex items-center justify-center relative">
              <svg viewBox="-300 -180 600 360" className="w-full h-full">
                {/* Ellipse boundary */}
                <ellipse
                  cx="0"
                  cy="0"
                  rx={semiMajorM}
                  ry={semiMinorM}
                  fill="none"
                  stroke="#38bdf8"
                  strokeWidth="1.5"
                  strokeDasharray="4 4"
                />
                <circle cx="0" cy="0" r="3" fill="#ffffff" />
                <text x="5" y="-5" fill="#94a3b8" fontSize="10" fontFamily="monospace">Target Touchdown</text>

                {/* Sample points */}
                {result.sample_points.map((pt: any, i: number) => {
                  const sunPct = pt.metrics.sun_availability_pct;
                  const color = sunPct >= 70 ? '#10b981' : (sunPct >= 50 ? '#f59e0b' : '#ef4444');
                  return (
                    <g key={i}>
                      <circle cx={pt.dx_m} cy={pt.dy_m} r={pt.is_center ? 6 : 4} fill={color} />
                    </g>
                  );
                })}
              </svg>
              <div className="absolute bottom-2 right-2 text-[10px] text-slate-400 font-mono bg-slate-900/80 px-2 py-0.5 rounded border border-slate-800">
                Green: &gt;70% Sun | Amber: 50–70% | Red: &lt;50%
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
