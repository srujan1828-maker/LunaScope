import React from 'react';
import { EvaluatedSiteData } from '../types';
import {
  Sun,
  Radio,
  Clock,
  Zap,
  ShieldAlert,
  AlertCircle,
  Lightbulb,
} from 'lucide-react';

interface InsightPanelProps {
  evaluatedSites: Record<string, EvaluatedSiteData>;
  selectedSiteIds: string[];
  comparativeInsights: string[];
}

export const InsightPanel: React.FC<InsightPanelProps> = ({
  evaluatedSites,
  selectedSiteIds,
  comparativeInsights,
}) => {
  const siteColors = ['#38bdf8', '#fbbf24', '#c084fc'];

  return (
    <div className="glass-panel rounded-2xl p-4 flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Lightbulb className="w-4 h-4 text-cyan-400" />
          <h2 className="text-sm font-semibold text-slate-200">
            Mission Metrics & Comparative Analysis
          </h2>
        </div>
        <span className="text-[10px] text-slate-400 font-mono">
          Rigorous interval integrations [Derived]
        </span>
      </div>

      {/* Comparative Metrics Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-slate-800 text-slate-400 font-medium">
              <th className="py-2 px-3">Metric Definition</th>
              {selectedSiteIds.map((sid, idx) => {
                const sdata = evaluatedSites[sid];
                const name = sdata?.site_info?.name || sid;
                const color = siteColors[idx % siteColors.length];
                return (
                  <th key={sid} className="py-2 px-3">
                    <span className="flex items-center gap-1.5" style={{ color }}>
                      <span className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
                      {name}
                    </span>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-mono">
            {/* Sun Availability */}
            <tr className="hover:bg-slate-900/40">
              <td className="py-2 px-3 text-slate-300 font-sans flex items-center gap-2">
                <Sun className="w-3.5 h-3.5 text-amber-400" />
                <span>Sun Availability (% of mission)</span>
              </td>
              {selectedSiteIds.map((sid) => {
                const m = evaluatedSites[sid]?.interval_metrics;
                return (
                  <td key={sid} className="py-2 px-3 font-semibold text-amber-300">
                    {m ? `${m.sun_availability_pct.toFixed(1)}%` : '—'}
                  </td>
                );
              })}
            </tr>

            {/* Equivalent Full-Sun Hours */}
            <tr className="hover:bg-slate-900/40">
              <td className="py-2 px-3 text-slate-300 font-sans flex items-center gap-2">
                <Zap className="w-3.5 h-3.5 text-yellow-400" />
                <span>Equivalent Full-Sun Exposure</span>
              </td>
              {selectedSiteIds.map((sid) => {
                const m = evaluatedSites[sid]?.interval_metrics;
                return (
                  <td key={sid} className="py-2 px-3 text-yellow-200">
                    {m ? `${m.equivalent_sun_hours.toFixed(1)} hrs` : '—'}
                  </td>
                );
              })}
            </tr>

            {/* Longest Shadow Gap */}
            <tr className="hover:bg-slate-900/40">
              <td className="py-2 px-3 text-slate-300 font-sans flex items-center gap-2">
                <Clock className="w-3.5 h-3.5 text-rose-400" />
                <span>Longest Shadow Gap (Battery drain risk)</span>
              </td>
              {selectedSiteIds.map((sid) => {
                const m = evaluatedSites[sid]?.interval_metrics;
                return (
                  <td key={sid} className="py-2 px-3 text-rose-300">
                    {m ? `${m.longest_shadow_gap_hours.toFixed(1)} hrs` : '—'}
                  </td>
                );
              })}
            </tr>

            {/* Earth Availability */}
            <tr className="hover:bg-slate-900/40">
              <td className="py-2 px-3 text-slate-300 font-sans flex items-center gap-2">
                <Radio className="w-3.5 h-3.5 text-cyan-400" />
                <span>Earth Geometric Visibility (% DTE)</span>
              </td>
              {selectedSiteIds.map((sid) => {
                const m = evaluatedSites[sid]?.interval_metrics;
                return (
                  <td key={sid} className="py-2 px-3 font-semibold text-cyan-300">
                    {m ? `${m.earth_availability_pct.toFixed(1)}%` : '—'}
                  </td>
                );
              })}
            </tr>

            {/* Longest Earth Outage */}
            <tr className="hover:bg-slate-900/40">
              <td className="py-2 px-3 text-slate-300 font-sans flex items-center gap-2">
                <ShieldAlert className="w-3.5 h-3.5 text-indigo-400" />
                <span>Longest Comms Blackout Outage</span>
              </td>
              {selectedSiteIds.map((sid) => {
                const m = evaluatedSites[sid]?.interval_metrics;
                return (
                  <td key={sid} className="py-2 px-3 text-indigo-300">
                    {m ? `${m.longest_earth_outage_hours.toFixed(1)} hrs` : '—'}
                  </td>
                );
              })}
            </tr>

            {/* Joint Availability */}
            <tr className="hover:bg-slate-900/40">
              <td className="py-2 px-3 text-slate-300 font-sans flex items-center gap-2">
                <AlertCircle className="w-3.5 h-3.5 text-emerald-400" />
                <span>Joint Sunlight + Earth DTE Availability</span>
              </td>
              {selectedSiteIds.map((sid) => {
                const m = evaluatedSites[sid]?.interval_metrics;
                return (
                  <td key={sid} className="py-2 px-3 font-semibold text-emerald-300">
                    {m ? `${m.joint_availability_pct.toFixed(1)}%` : '—'}
                  </td>
                );
              })}
            </tr>

            {/* Longest Joint Window */}
            <tr className="hover:bg-slate-900/40">
              <td className="py-2 px-3 text-slate-300 font-sans flex items-center gap-2">
                <Clock className="w-3.5 h-3.5 text-emerald-400" />
                <span>Longest Continuous Joint Window</span>
              </td>
              {selectedSiteIds.map((sid) => {
                const m = evaluatedSites[sid]?.interval_metrics;
                return (
                  <td key={sid} className="py-2 px-3 text-emerald-200">
                    {m ? `${m.longest_joint_window_hours.toFixed(1)} hrs` : '—'}
                  </td>
                );
              })}
            </tr>
          </tbody>
        </table>
      </div>

      {/* Deterministic Comparative Insights */}
      {comparativeInsights.length > 0 && (
        <div className="bg-slate-900/80 border border-cyan-500/20 rounded-xl p-3 flex flex-col gap-2">
          <span className="text-xs font-semibold text-cyan-300 uppercase tracking-wider flex items-center gap-1.5">
            <Lightbulb className="w-3.5 h-3.5" />
            Deterministic Trade-off Findings:
          </span>
          <ul className="flex flex-col gap-1.5 text-xs text-slate-300">
            {comparativeInsights.map((insight, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="text-cyan-400 mt-0.5">•</span>
                <span>{insight}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
