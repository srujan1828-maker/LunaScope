import React, { useState } from 'react';
import { saveScenario, getExportUrl } from '../api/client';
import { Download, X, FileJson, FileSpreadsheet, Check, Sparkles } from 'lucide-react';

interface ScenarioExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  scenarioPayload: any;
}

export const ScenarioExportModal: React.FC<ScenarioExportModalProps> = ({
  isOpen,
  onClose,
  scenarioPayload,
}) => {
  const [title, setTitle] = useState('Artemis South Pole Mission Scenario');
  const [notes, setNotes] = useState('Comparative evaluation for surface operations');
  const [savedId, setSavedId] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  if (!isOpen) return null;

  const handleSaveAndPrepareExport = async () => {
    setIsSaving(true);
    try {
      const fullPayload = {
        title,
        notes,
        site_ids: scenarioPayload.inputs?.site_ids || [],
        inputs: scenarioPayload.inputs || {},
        sites_evaluation: scenarioPayload.evaluated_sites || {},
        comparative_insights: scenarioPayload.comparative_insights || [],
        provenance: scenarioPayload.provenance || {},
      };
      const res = await saveScenario(fullPayload);
      setSavedId(res.scenario_id);
    } catch (e) {
      console.error(e);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4 overflow-y-auto">
      <div className="glass-panel w-full max-w-lg rounded-2xl border border-cyan-500/30 p-6 flex flex-col gap-5 shadow-2xl">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-cyan-500/20 border border-cyan-500/30 flex items-center justify-center">
              <Download className="w-4 h-4 text-cyan-400" />
            </div>
            <h2 className="text-sm font-bold text-slate-100">
              Export Mission Scenario & Provenance
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="flex flex-col gap-3 text-xs">
          <div className="flex flex-col gap-1">
            <label className="text-slate-300 font-medium">Scenario Title</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-slate-200 font-mono focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-slate-300 font-medium">Mission Notes / Assumptions</label>
            <textarea
              rows={2}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-slate-200 focus:outline-none focus:border-cyan-500"
            />
          </div>
        </div>

        {!savedId ? (
          <button
            onClick={handleSaveAndPrepareExport}
            disabled={isSaving}
            className="w-full py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-semibold text-xs flex items-center justify-center gap-2 shadow-lg transition-all cursor-pointer"
          >
            {isSaving ? (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <Sparkles className="w-4 h-4" />
            )}
            <span>Generate Scenario Export Bundle</span>
          </button>
        ) : (
          <div className="flex flex-col gap-3 pt-2 border-t border-slate-800">
            <div className="flex items-center gap-2 text-emerald-400 text-xs font-mono">
              <Check className="w-4 h-4" />
              <span>Immutable Scenario ID: {savedId.slice(0, 8)}...</span>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <a
                href={getExportUrl(savedId, 'json')}
                download
                className="p-3 bg-slate-900 hover:bg-slate-800 border border-slate-700 hover:border-cyan-500/50 rounded-xl flex items-center justify-center gap-2 text-xs font-semibold text-cyan-300 transition-all"
              >
                <FileJson className="w-4 h-4 text-cyan-400" />
                <span>Download JSON</span>
              </a>

              <a
                href={getExportUrl(savedId, 'csv')}
                download
                className="p-3 bg-slate-900 hover:bg-slate-800 border border-slate-700 hover:border-emerald-500/50 rounded-xl flex items-center justify-center gap-2 text-xs font-semibold text-emerald-300 transition-all"
              >
                <FileSpreadsheet className="w-4 h-4 text-emerald-400" />
                <span>Download CSV</span>
              </a>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
