import React from 'react';
import { BookOpen, X, ExternalLink, ShieldCheck, Database, FileText } from 'lucide-react';

interface ProvenanceDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ProvenanceDrawer: React.FC<ProvenanceDrawerProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4 overflow-y-auto">
      <div className="glass-panel w-full max-w-3xl rounded-2xl border border-cyan-500/30 p-6 flex flex-col gap-6 max-h-[90vh] overflow-y-auto shadow-2xl">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-cyan-500/20 border border-cyan-500/30 flex items-center justify-center">
              <BookOpen className="w-5 h-5 text-cyan-400" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-100">
                Data Provenance & Scientific Methodology
              </h2>
              <p className="text-xs text-slate-400">
                Complete transparency for mission planners, researchers, and reviewers
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

        {/* Provenance Badge Taxonomy */}
        <div className="flex flex-col gap-2">
          <h3 className="text-xs font-semibold text-slate-200 uppercase tracking-wider">
            Provenance Badge Taxonomy
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="bg-slate-900/80 border border-slate-800 p-3 rounded-xl flex flex-col gap-1">
              <span className="text-xs font-bold text-emerald-400 font-mono">[Reference only]</span>
              <p className="text-[11px] text-slate-300 leading-snug">
                References identify possible future inputs. The current catalog uses illustrative values; no published site metrics have been verified or imported.
              </p>
            </div>
            <div className="bg-slate-900/80 border border-slate-800 p-3 rounded-xl flex flex-col gap-1">
              <span className="text-xs font-bold text-cyan-400 font-mono">[Derived]</span>
              <p className="text-[11px] text-slate-300 leading-snug">
                Quantities calculated from procedural terrain and approximate analytical astronomy. Derived outputs inherit the limits of those inputs.
              </p>
            </div>
            <div className="bg-slate-900/80 border border-slate-800 p-3 rounded-xl flex flex-col gap-1">
              <span className="text-xs font-bold text-amber-400 font-mono">[Assumed]</span>
              <p className="text-[11px] text-slate-300 leading-snug">
                User-configured hardware assumptions (e.g. solar panel area, battery capacity, spacecraft load, RF Fresnel clearance margin).
              </p>
            </div>
          </div>
        </div>

        {/* Authoritative Datasets & Citations */}
        <div className="flex flex-col gap-3">
          <h3 className="text-xs font-semibold text-slate-200 uppercase tracking-wider">
            References & Integration Status
          </h3>

          <div className="space-y-3 text-xs">
            <div className="p-3 bg-slate-900/60 border border-slate-800 rounded-xl flex flex-col gap-1">
              <div className="flex items-center justify-between font-semibold text-slate-200">
                <span className="flex items-center gap-1.5 text-cyan-300">
                  <Database className="w-4 h-4" /> 1. Candidate Sites & Illumination Benchmark
                </span>
                <span className="text-[10px] font-mono text-emerald-400">[Reference only]</span>
              </div>
              <p className="text-slate-300 leading-relaxed">
                Wueller et al. (2026), <em>"Assessing Potential Landing Sites With Favorable Illumination and Accessible, Potentially Volatile-Rich Permanently Shadowed Regions Within Artemis Candidate Landing Regions,"</em> Journal of Geophysical Research: Planets (DOI: 10.1029/2025JE009434). Zenodo Record 17084058. Reference only: hard-coded annual demonstration values are not a transcription of this dataset.
              </p>
            </div>

            <div className="p-3 bg-slate-900/60 border border-slate-800 rounded-xl flex flex-col gap-1">
              <div className="flex items-center justify-between font-semibold text-slate-200">
                <span className="flex items-center gap-1.5 text-cyan-300">
                  <Database className="w-4 h-4" /> 2. Lunar South Pole Topography (LOLA DEM)
                </span>
                <span className="text-[10px] font-mono text-cyan-400">[Derived]</span>
              </div>
              <p className="text-slate-300 leading-relaxed">
                NASA Lunar Reconnaissance Orbiter (LRO) Lunar Orbiter Laser Altimeter (LOLA) South Polar Stereographic DEMs (LDEM_80S_20M.tif, LDEM_85S_10M.tif). NASA Planetary Geodata Archive (PGDA Product 90). NOT integrated: this application generates procedural terrain.
              </p>
            </div>

            <div className="p-3 bg-slate-900/60 border border-slate-800 rounded-xl flex flex-col gap-1">
              <div className="flex items-center justify-between font-semibold text-slate-200">
                <span className="flex items-center gap-1.5 text-cyan-300">
                  <Database className="w-4 h-4" /> 3. Planetary Ephemerides & Lunar Orientation
                </span>
                <span className="text-[10px] font-mono text-cyan-400">[Derived]</span>
              </div>
              <p className="text-slate-300 leading-relaxed">
                NOT integrated: JPL Horizons, SPICE, DE421 and DE440 kernels. The active engine uses approximate analytical formulas without an independent accuracy benchmark.
              </p>
            </div>
          </div>
        </div>

        {/* Operational Guardrails */}
        <div className="p-3 bg-slate-900/40 border border-slate-800 rounded-xl text-[11px] text-slate-400 flex flex-col gap-1.5">
          <span className="font-semibold text-slate-300 flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
            Scope & Operational Boundaries:
          </span>
          <p>
            Geometric solar exposure does not equal flight-qualified power generation, and geometric Earth line-of-sight is a direct-to-Earth proxy rather than a booked DSN ground station pass. Incomplete coverage intervals are flagged as Unknown, never Pass.
          </p>
        </div>
      </div>
    </div>
  );
};
