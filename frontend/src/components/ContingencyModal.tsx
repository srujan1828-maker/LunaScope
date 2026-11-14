import React, { useState, useEffect } from 'react';
import { LandingSite, ContingencyResult } from '../types';
import { runContingencyAnalysis } from '../api/client';
import {
  ArrowRightLeft,
  X,
  CheckCircle2,
  XCircle,
  ShieldAlert,
  Calendar,
  Sun,
  Radio,
  ExternalLink,
} from 'lucide-react';

interface ContingencyModalProps {
  isOpen: boolean;
  onClose: () => void;
  sites: LandingSite[];
  currentPrimarySiteId: string;
  onSelectBackup: (siteId: string) => void;
}

export const ContingencyModal: React.FC<ContingencyModalProps> = ({
  isOpen,
  onClose,
  sites,
  currentPrimarySiteId,
  onSelectBackup,
}) => {
  const [primarySiteId, setPrimarySiteId] = useState(currentPrimarySiteId);
  const [year, setYear] = useState<number>(2027);
  const [minSunDays, setMinSunDays] = useState<number>(8.0);
  const [minJointDays, setMinJointDays] = useState<number>(6.0);

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [result, setResult] = useState<ContingencyResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      setPrimarySiteId(currentPrimarySiteId);
      handleRunContingency(currentPrimarySiteId, year, minSunDays, minJointDays);
    }
  }, [isOpen, currentPrimarySiteId]);

  const handleRunContingency = async (pId: string, yr: number, sunD: number, jointD: number) => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await runContingencyAnalysis({
        primary_site_id: pId,
        year: yr,
        min_sun_days: sunD,
        min_joint_days: jointD,
      });
      setResult(res);
    } catch (err: any) {
      setError(err.message || 'Contingency evaluation failed');
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4 overflow-y-auto">
      <div className="glass-panel w-full max-w-4xl rounded-2xl border border-indigo-500/30 p-6 flex flex-col gap-6 max-h-[90vh] overflow-y-auto shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center">
              <ArrowRightLeft className="w-5 h-5 text-indigo-400" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-slate-100">
                  Tier 1 Macro Contingency Planner
                </h2>
                <span className="text-[10px] bg-indigo-950 px-2 py-0.5 rounded font-mono text-indigo-300 border border-indigo-800">
                  Wueller et al. (2026)
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Identify passing backup landing sites when the primary site encounters shadow or DTE failures
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

        {/* Inputs */}
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 bg-slate-900/60 border border-slate-800 p-4 rounded-xl">
          {/* Primary site selection */}
          <div className="flex flex-col gap-1">
            <label className="text-xs text-slate-300 font-medium">Primary Site</label>
            <select
              value={primarySiteId}
              onChange={(e) => {
                setPrimarySiteId(e.target.value);
                handleRunContingency(e.target.value, year, minSunDays, minJointDays);
              }}
              className="bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-indigo-500"
            >
              {sites.map((s) => (
                <option key={s.site_id} value={s.site_id}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>

          {/* Modelled Year */}
          <div className="flex flex-col gap-1">
            <label className="text-xs text-slate-300 font-medium flex items-center gap-1">
              <Calendar className="w-3.5 h-3.5 text-indigo-400" />
              Modelled Year
            </label>
            <select
              value={year}
              onChange={(e) => {
                const yr = Number(e.target.value);
                setYear(yr);
                handleRunContingency(primarySiteId, yr, minSunDays, minJointDays);
              }}
              className="bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-indigo-500"
            >
              {[2025, 2026, 2027, 2028, 2029, 2030, 2031, 2032].map((yr) => (
                <option key={yr} value={yr}>
                  {yr} Midsummer Period
                </option>
              ))}
            </select>
          </div>

          {/* Min Continuous Sun Days */}
          <div className="flex flex-col gap-1">
            <label className="text-xs text-slate-300 font-medium flex justify-between">
              <span className="flex items-center gap-1">
                <Sun className="w-3.5 h-3.5 text-amber-400" /> Min Sun
              </span>
              <span className="text-amber-300 font-mono">{minSunDays} d</span>
            </label>
            <input
              type="range"
              min="2.0"
              max="20.0"
              step="0.5"
              value={minSunDays}
              onChange={(e) => {
                const val = Number(e.target.value);
                setMinSunDays(val);
                handleRunContingency(primarySiteId, year, val, minJointDays);
              }}
            />
          </div>

          {/* Min Joint Days */}
          <div className="flex flex-col gap-1">
            <label className="text-xs text-slate-300 font-medium flex justify-between">
              <span className="flex items-center gap-1">
                <Radio className="w-3.5 h-3.5 text-cyan-400" /> Min Joint
              </span>
              <span className="text-cyan-300 font-mono">{minJointDays} d</span>
            </label>
            <input
              type="range"
              min="1.0"
              max="18.0"
              step="0.5"
              value={minJointDays}
              onChange={(e) => {
                const val = Number(e.target.value);
                setMinJointDays(val);
                handleRunContingency(primarySiteId, year, minSunDays, val);
              }}
            />
          </div>
        </div>

        {/* Primary Site Assessment Card */}
        {result?.primary_site && (
          <div
            className={`p-4 rounded-xl border flex flex-col gap-2 ${
              result.primary_passed
                ? 'bg-emerald-950/30 border-emerald-500/40 text-emerald-200'
                : 'bg-rose-950/30 border-rose-500/40 text-rose-200'
            }`}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {result.primary_passed ? (
                  <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                ) : (
                  <XCircle className="w-5 h-5 text-rose-400" />
                )}
                <span className="font-bold text-sm text-slate-100">
                  Primary Candidate: {result.primary_site.name}
                </span>
                <span
                  className={`text-xs px-2 py-0.5 rounded font-mono font-semibold ${
                    result.primary_passed ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/20 text-rose-300'
                  }`}
                >
                  {result.primary_passed ? 'PASSES CRITERIA' : 'FAILS CRITERIA — CONTINGENCY TRIGGERED'}
                </span>
              </div>
              <span className="text-xs font-mono text-slate-400">
                Year {result.year} Benchmark
              </span>
            </div>

            <p className="text-xs text-slate-300">
              {result.primary_site.explanation}
            </p>

            <div className="flex flex-wrap gap-4 text-xs font-mono pt-1 text-slate-300">
              <span>Consecutive Sun: <strong>{result.primary_site.max_consec_sun_days} d</strong></span>
              <span>Joint Sun+Earth: <strong>{result.primary_site.max_consec_joint_days} d</strong></span>
              <span>Annual Illumination: <strong>{(result.primary_site.annual_illum_fraction * 100).toFixed(0)}%</strong></span>
            </div>
          </div>
        )}

        {/* Recommended Backups List */}
        {result && (
          <div className="flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Recommended Passing Backup Candidates ({result.recommended_backups.length}):
              </span>
              <span className="text-[11px] text-slate-400 font-mono">
                Ranked by Joint Visibility Margin [Derived]
              </span>
            </div>

            {result.recommended_backups.length === 0 ? (
              <div className="p-4 bg-slate-900/50 border border-slate-800 rounded-xl text-xs text-slate-400 text-center">
                No backup sites met the requested duration criteria in {year}. Consider adjusting thresholds.
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {result.recommended_backups.map((backup, idx) => (
                  <div
                    key={backup.site_id}
                    className="p-3 bg-slate-900/80 hover:bg-slate-900 border border-slate-800 hover:border-indigo-500/40 rounded-xl flex flex-col justify-between gap-2 transition-all"
                  >
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-semibold text-xs text-indigo-300 flex items-center gap-1.5">
                          <span className="w-5 h-5 rounded-full bg-indigo-950 border border-indigo-500/40 text-indigo-300 text-[10px] flex items-center justify-center font-bold">
                            #{idx + 1}
                          </span>
                          {backup.name}
                        </span>
                        <span className="text-[10px] font-mono text-slate-400">
                          {backup.elevation_m > 0 ? `+${backup.elevation_m}` : backup.elevation_m}m
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-300 leading-snug">
                        {backup.explanation}
                      </p>
                    </div>

                    <div className="flex items-center justify-between pt-2 border-t border-slate-800/60 mt-1">
                      <div className="flex items-center gap-2 text-[10px] font-mono text-slate-400">
                        <span className="text-amber-300">{backup.max_consec_sun_days}d Sun</span>
                        <span>•</span>
                        <span className="text-cyan-300">{backup.max_consec_joint_days}d Joint</span>
                      </div>

                      <button
                        onClick={() => {
                          onSelectBackup(backup.site_id);
                          onClose();
                        }}
                        className="px-2.5 py-1 rounded bg-indigo-600/80 hover:bg-indigo-600 text-white text-[11px] font-medium flex items-center gap-1 transition-all cursor-pointer"
                      >
                        <span>Select as Backup</span>
                        <ExternalLink className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
