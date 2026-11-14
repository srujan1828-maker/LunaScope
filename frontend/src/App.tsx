import React, { useState, useEffect, useCallback, useRef } from 'react';
import { LandingSite, ScenarioEvaluationResult, PowerConfig } from './types';
import { fetchSites, evaluateScenario } from './api/client';
import { Header } from './components/Header';
import { PolarMap } from './components/PolarMap';
import { SiteComparisonTray } from './components/SiteComparisonTray';
import { HorizonViewer360 } from './components/HorizonViewer360';
import { SynchronizedTimeline } from './components/SynchronizedTimeline';
import { InsightPanel } from './components/InsightPanel';
import { WindowFinderModal } from './components/WindowFinderModal';
import { ContingencyModal } from './components/ContingencyModal';
import { PowerSimulationDrawer } from './components/PowerSimulationDrawer';
import { ProvenanceDrawer } from './components/ProvenanceDrawer';
import { ScenarioExportModal } from './components/ScenarioExportModal';
import { RealtimeSimulationBar } from './components/RealtimeSimulationBar';
import { DispersionModal } from './components/DispersionModal';
import { MastSensitivityModal } from './components/MastSensitivityModal';
import { LiveMatchingPanel } from './components/LiveMatchingPanel';
import { Loader2, AlertCircle } from 'lucide-react';

export const App: React.FC = () => {
  const [mode, setMode] = useState<'explore' | 'plan'>('explore');
  const [sites, setSites] = useState<LandingSite[]>([]);
  const [selectedSiteIds, setSelectedSiteIds] = useState<string[]>([
    'shackleton-connecting-ridge',
    'malapert-mountain',
  ]);

  // Mission parameters
  const [startDateIso, setStartDateIso] = useState<string>('2027-01-01T00:00:00Z');
  const [durationDays, setDurationDays] = useState<number>(14);
  const [mastHeightM, setMastHeightM] = useState<number>(2.0);
  const [antennaMarginDeg, setAntennaMarginDeg] = useState<number>(0.0);
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(0);

  // Power model settings
  const [powerConfig, setPowerConfig] = useState<PowerConfig>({
    enabled: true,
    panel_area_m2: 3.5,
    panel_efficiency: 0.28,
    panel_orientation: 'tracking',
    spacecraft_load_w: 120.0,
    battery_capacity_wh: 2400.0,
    initial_soc_pct: 100.0,
    reserve_margin_pct: 20.0,
  });

  // Scenario evaluation state
  const [evaluation, setEvaluation] = useState<ScenarioEvaluationResult | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Modal visibility states
  const [isWindowFinderOpen, setIsWindowFinderOpen] = useState<boolean>(false);
  const [isContingencyOpen, setIsContingencyOpen] = useState<boolean>(false);
  const [isPowerOpen, setIsPowerOpen] = useState<boolean>(false);
  const [isProvenanceOpen, setIsProvenanceOpen] = useState<boolean>(false);
  const [isExportOpen, setIsExportOpen] = useState<boolean>(false);
  const [isDispersionOpen, setIsDispersionOpen] = useState<boolean>(false);
  const [isMastSensitivityOpen, setIsMastSensitivityOpen] = useState<boolean>(false);

  // Load sites catalog on mount
  useEffect(() => {
    fetchSites()
      .then((data) => setSites(data))
      .catch((err) => setError(`Failed to load sites: ${err.message}`));
  }, []);

  // Compute end time from start date and duration
  const getEndTimeIso = useCallback((startIso: string, days: number) => {
    const startDt = new Date(startIso);
    const endDt = new Date(startDt.getTime() + days * 86400 * 1000);
    return endDt.toISOString();
  }, []);

  const evaluationRevision = useRef(0);

  // Run scenario evaluation
  const runEvaluation = useCallback(async () => {
    if (selectedSiteIds.length === 0) return;
    const requestRevision = ++evaluationRevision.current;
    setIsLoading(true);
    setError(null);
    try {
      const endIso = getEndTimeIso(startDateIso, durationDays);
      const res = await evaluateScenario({
        site_ids: selectedSiteIds,
        start_time_iso: startDateIso,
        end_time_iso: endIso,
        mast_height_m: mastHeightM,
        antenna_margin_deg: antennaMarginDeg,
        sun_threshold: 0.10,
        power_config: powerConfig,
      });
      if (requestRevision === evaluationRevision.current) {setEvaluation(res); setCurrentStepIndex(0);}
    } catch (err: any) {
      if (requestRevision === evaluationRevision.current) setError(err.message || 'Evaluation failed');
    } finally {
      if (requestRevision === evaluationRevision.current) setIsLoading(false);
    }
  }, [selectedSiteIds, startDateIso, durationDays, mastHeightM, antennaMarginDeg, powerConfig, getEndTimeIso]);

  useEffect(() => {
    const timer = setTimeout(runEvaluation, 350);
    return () => {clearTimeout(timer); ++evaluationRevision.current;};
  }, [runEvaluation]);

  // Handle site toggle
  const handleToggleSite = (siteId: string) => {
    setSelectedSiteIds((prev) => {
      if (prev.includes(siteId)) {
        if (prev.length === 1) return prev; // Keep at least one site
        return prev.filter((id) => id !== siteId);
      } else {
        if (prev.length >= 3) {
          return [prev[1], prev[2], siteId]; // Replace oldest if tray full
        }
        return [...prev, siteId];
      }
    });
  };

  const handleRemoveSite = (siteId: string) => {
    if (selectedSiteIds.length > 1) {
      setSelectedSiteIds((prev) => prev.filter((id) => id !== siteId));
    }
  };

  const handleApplyWindow = (startIso: string, duration: number) => {
    setStartDateIso(startIso);
    setDurationDays(duration);
    setCurrentStepIndex(0);
  };

  const selectedSites = sites.filter((s) => selectedSiteIds.includes(s.site_id));

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col selection:bg-cyan-500/30 selection:text-cyan-200">
      <div className="fixed inset-0 pointer-events-none" style={{zIndex:0, background:'#080B12'}}>
        <video autoPlay muted loop playsInline aria-hidden="true" src="/assets/lunar-background.mp4" style={{width:'100%',height:'100%',objectFit:'cover',opacity:.17}} />
      </div>
      {/* App Header */}
      <Header
        mode={mode}
        onToggleMode={setMode}
        onOpenWindowFinder={() => setIsWindowFinderOpen(true)}
        onOpenContingency={() => setIsContingencyOpen(true)}
        onOpenPower={() => setIsPowerOpen(true)}
        onOpenDispersion={() => setIsDispersionOpen(true)}
        onOpenMastSensitivity={() => setIsMastSensitivityOpen(true)}
        onOpenProvenance={() => setIsProvenanceOpen(true)}
        onOpenExport={() => setIsExportOpen(true)}
      />

      {/* Main Workspace Layout */}
      <main className="flex-1 p-4 lg:p-6 max-w-[1600px] w-full mx-auto relative flex flex-col gap-5">
        {error && (
          <div className="p-3 bg-red-950/70 border border-red-500/40 rounded-xl text-red-200 text-xs flex items-center gap-2.5">
            <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <div className="p-3 border border-amber-500/30 rounded-xl text-xs text-amber-200">Demonstration workspace. Site metrics and terrain are illustrative; ephemeris is approximate. Live means streamed simulation, not NASA telemetry.</div>
        <LiveMatchingPanel startDateIso={startDateIso} durationDays={durationDays} mastHeightM={mastHeightM}
          antennaMarginDeg={antennaMarginDeg} primaryId={selectedSiteIds[0]} powerConfig={powerConfig}
          onSelect={id => {setSelectedSiteIds(prev => [id, ...prev.filter(s=>s!==id)].slice(0,3)); setCurrentStepIndex(0);}} />

        {/* Real-Time Simulation Status Bar */}
        <RealtimeSimulationBar
          selectedSiteIds={selectedSiteIds}
          antennaMarginDeg={antennaMarginDeg}
          powerConfig={powerConfig}
          currentUnix={new Date(startDateIso).getTime() / 1000}
          mastHeightM={mastHeightM}
          onTimeUpdate={(newUnix) => {
            const primaryId = selectedSiteIds[0];
            const pData = evaluation?.evaluated_sites?.[primaryId];
            if (pData?.timestamps?.length) {
              // Find closest step index
              const tsArr = pData.timestamps;
              let bestIdx = 0;
              let minDiff = Infinity;
              for (let i = 0; i < tsArr.length; i++) {
                const diff = Math.abs(tsArr[i] - newUnix);
                if (diff < minDiff) {
                  minDiff = diff;
                  bestIdx = i;
                }
              }
              setCurrentStepIndex(bestIdx);
            }
          }}
        />

        {/* Top Control Bar: Comparison Tray & Mission Parameters */}
        <SiteComparisonTray
          selectedSites={selectedSites}
          onRemoveSite={handleRemoveSite}
          startDateIso={startDateIso}
          onStartDateChange={setStartDateIso}
          durationDays={durationDays}
          onDurationChange={setDurationDays}
          mastHeightM={mastHeightM}
          onMastHeightChange={setMastHeightM}
          antennaMarginDeg={antennaMarginDeg}
          onAntennaMarginChange={setAntennaMarginDeg}
          mode={mode}
        />

        {/* 2-Column Responsive Workspace */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
          {/* Left Column (5 cols): Polar Map */}
          <div className="lg:col-span-5 flex flex-col gap-5">
            <PolarMap
              sites={sites}
              selectedSiteIds={selectedSiteIds}
              onToggleSite={handleToggleSite}
            />
          </div>

          {/* Right Column (7 cols): Horizon & Timelines & Insights */}
          <div className="lg:col-span-7 flex flex-col gap-5">
            {isLoading && !evaluation ? (
              <div className="glass-panel rounded-2xl p-12 flex flex-col items-center justify-center gap-3 text-slate-400">
                <Loader2 className="w-8 h-8 text-cyan-400 animate-spin" />
                <span className="text-xs font-mono">Computing raycasted horizons & ephemerides...</span>
              </div>
            ) : (
              evaluation && (
                <>
                  {/* 360 Panoramic Horizon */}
                  <HorizonViewer360
                    evaluatedSites={evaluation.evaluated_sites}
                    selectedSiteIds={selectedSiteIds}
                    currentStepIndex={currentStepIndex}
                  />

                  {/* Synchronized Timeline & Scrubber */}
                  <SynchronizedTimeline
                    evaluatedSites={evaluation.evaluated_sites}
                    selectedSiteIds={selectedSiteIds}
                    currentStepIndex={currentStepIndex}
                    onStepChange={setCurrentStepIndex}
                  />

                  {/* Insight & Comparative Metrics Table */}
                  <InsightPanel
                    evaluatedSites={evaluation.evaluated_sites}
                    selectedSiteIds={selectedSiteIds}
                    comparativeInsights={evaluation.comparative_insights}
                  />
                </>
              )
            )}
          </div>
        </div>
      </main>

      {/* Signature Modals & Drawers */}
      <WindowFinderModal
        isOpen={isWindowFinderOpen}
        onClose={() => setIsWindowFinderOpen(false)}
        selectedSites={selectedSites}
        mastHeightM={mastHeightM}
        onApplyWindow={handleApplyWindow}
      />

      <ContingencyModal
        isOpen={isContingencyOpen}
        onClose={() => setIsContingencyOpen(false)}
        sites={sites}
        currentPrimarySiteId={selectedSiteIds[0] || 'shackleton-connecting-ridge'}
        onSelectBackup={(backupId) => {
          if (!selectedSiteIds.includes(backupId)) {
            setSelectedSiteIds([selectedSiteIds[0], backupId]);
          }
        }}
      />

      <PowerSimulationDrawer
        isOpen={isPowerOpen}
        onClose={() => setIsPowerOpen(false)}
        evaluatedSites={evaluation?.evaluated_sites || {}}
        selectedSiteIds={selectedSiteIds}
        powerConfig={powerConfig}
        onUpdatePowerConfig={setPowerConfig}
      />

      <ProvenanceDrawer
        isOpen={isProvenanceOpen}
        onClose={() => setIsProvenanceOpen(false)}
      />

      <ScenarioExportModal
        isOpen={isExportOpen}
        onClose={() => setIsExportOpen(false)}
        scenarioPayload={evaluation || {}}
      />

      <DispersionModal
        isOpen={isDispersionOpen}
        onClose={() => setIsDispersionOpen(false)}
        site={selectedSites[0] || null}
        startDateIso={startDateIso}
        durationDays={durationDays}
        mastHeightM={mastHeightM}
      />

      <MastSensitivityModal
        isOpen={isMastSensitivityOpen}
        onClose={() => setIsMastSensitivityOpen(false)}
        site={selectedSites[0] || null}
        startDateIso={startDateIso}
        durationDays={durationDays}
        currentMastHeightM={mastHeightM}
        onApplyMastHeight={setMastHeightM}
      />
    </div>
  );
};
