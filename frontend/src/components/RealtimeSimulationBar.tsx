import { PowerConfig } from '../types';
import React, { useState, useEffect, useRef } from 'react';
import {
  Activity,
  Radio,
  Sun,
  Globe2,
  BatteryCharging,
  Zap,
  AlertTriangle,
  Clock,
  Play,
  Pause,
  SkipForward,
} from 'lucide-react';

interface RealtimeSimulationBarProps {
  selectedSiteIds: string[];
  currentUnix: number;
  mastHeightM: number;
  antennaMarginDeg: number;
  powerConfig: PowerConfig;
  onTimeUpdate: (newUnix: number) => void;
}

export const RealtimeSimulationBar: React.FC<RealtimeSimulationBarProps> = ({
  selectedSiteIds,
  currentUnix,
  mastHeightM,
  antennaMarginDeg,
  powerConfig,
  onTimeUpdate,
}) => {
  const [isConnected, setIsConnected] = useState(false);
  const [isLiveRunning, setIsLiveRunning] = useState(false);
  const [speedMultiplier, setSpeedMultiplier] = useState(60.0);
  const [telemetry, setTelemetry] = useState<any>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const onTimeRef = useRef(onTimeUpdate);
  onTimeRef.current = onTimeUpdate;

  useEffect(() => {
    // Construct WebSocket URL
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host || '127.0.0.1:8000';
    const wsUrl = `${protocol}//${host}/api/ws/simulation`;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      ws.send(JSON.stringify({command: "configure", antenna_margin_deg: antennaMarginDeg, power_config: powerConfig}));
      setIsConnected(true);
      // Sync sites & mast height
      ws.send(JSON.stringify({ command: 'select_sites', site_ids: selectedSiteIds }));
      ws.send(JSON.stringify({ command: 'set_mast', mast_height_m: mastHeightM }));
      ws.send(JSON.stringify({ command: 'seek', timestamp_unix: currentUnix }));
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'telemetry_frame') {
          setTelemetry(data);
          onTimeRef.current(data.timestamp_unix);
        } else if (data.type === 'session_init') {
          setTelemetry(data.frame);
        } else if (data.type === 'status' && 'is_running' in data) {
          setIsLiveRunning(data.is_running);
        }
      } catch (e) {
        console.error('WS parse error:', e);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      setIsLiveRunning(false);
    };

    return () => {
      ws.close();
    };
  }, []);

  // Update server when sites or mast height change
  useEffect(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ command: 'select_sites', site_ids: selectedSiteIds }));
      wsRef.current.send(JSON.stringify({ command: 'set_mast', mast_height_m: mastHeightM }));
    }
    if (wsRef.current?.readyState === WebSocket.OPEN) wsRef.current.send(JSON.stringify({command: "configure", antenna_margin_deg: antennaMarginDeg, power_config: powerConfig}));
  }, [selectedSiteIds, mastHeightM, antennaMarginDeg, powerConfig]);

  useEffect(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) wsRef.current.send(JSON.stringify({command: "seek", timestamp_unix: currentUnix}));
  }, [currentUnix]);

  const toggleLiveStreaming = () => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    if (isLiveRunning) {
      wsRef.current.send(JSON.stringify({ command: 'pause' }));
      setIsLiveRunning(false);
    } else {
      wsRef.current.send(JSON.stringify({ command: 'start', speed: speedMultiplier }));
      setIsLiveRunning(true);
    }
  };

  const handleSpeedChange = (spd: number) => {
    setSpeedMultiplier(spd);
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ command: 'set_speed', speed: spd }));
    }
  };

  const handleStep = (dtSeconds: number) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ command: 'step', dt_seconds: dtSeconds }));
    }
  };

  // Primary site telemetry
  const primaryId = selectedSiteIds[0];
  const primaryTel = telemetry?.sites?.[primaryId];

  return (
    <div className="glass-panel rounded-2xl p-4 flex flex-col gap-3 border border-cyan-500/30">
      {/* Top Controls Row */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span
              className={`w-2.5 h-2.5 rounded-full ${
                isConnected ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'
              }`}
            />
            <span className="text-xs font-bold uppercase tracking-wider text-slate-200 flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5 text-cyan-400" />
              NASA-data streamed simulation
            </span>
          </div>

          <button
            onClick={toggleLiveStreaming}
            disabled={!isConnected}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all shadow-md cursor-pointer disabled:opacity-50 ${
              isLiveRunning
                ? 'bg-amber-600 hover:bg-amber-500 text-white animate-pulse'
                : 'bg-gradient-to-r from-cyan-600 to-sky-600 hover:from-cyan-500 hover:to-sky-500 text-white'
            }`}
          >
            {isLiveRunning ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
            <span>{isLiveRunning ? 'Pause Live Stream' : 'Start Live Sim'}</span>
          </button>

          <button
            onClick={() => handleStep(3600.0)}
            disabled={!isConnected || isLiveRunning}
            className="px-2.5 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 text-xs flex items-center gap-1 transition-all disabled:opacity-50"
            title="Step forward 1 hour"
          >
            <SkipForward className="w-3.5 h-3.5" />
            <span>+1h Step</span>
          </button>

          {/* Speed Presets */}
          <div className="flex items-center bg-slate-900 border border-slate-800 rounded-lg p-0.5 text-xs font-mono">
            {[10, 60, 300, 3600].map((spd) => (
              <button
                key={spd}
                onClick={() => handleSpeedChange(spd)}
                className={`px-2 py-0.5 rounded ${
                  speedMultiplier === spd
                    ? 'bg-cyan-600 text-white font-bold'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {spd === 3600 ? '1h/s' : `${spd}x`}
              </button>
            ))}
          </div>
        </div>

        {/* Live Simulation Timestamp */}
        <div className="flex items-center gap-2 text-xs font-mono bg-slate-900/90 px-3 py-1 rounded-lg border border-cyan-800/40 text-cyan-300">
          <Clock className="w-3.5 h-3.5 text-cyan-400" />
          <span>{telemetry?.timestamp_iso?.slice(0, 19).replace('T', ' ') || 'Syncing...'} UTC</span>
        </div>
      </div>

      {/* Live Telemetry KPI Cards */}
      {primaryTel ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5 pt-1">
          {/* 1. Solar Exposure */}
          <div className="bg-slate-900/80 border border-slate-800/80 rounded-xl p-2.5 flex flex-col gap-1">
            <span className="text-[10px] text-amber-400 flex items-center gap-1 font-medium">
              <Sun className="w-3 h-3" /> Sun Elevation
            </span>
            <span className="text-sm font-bold font-mono text-slate-100">
              {primaryTel.sun.elevation_deg > 0 ? `+${primaryTel.sun.elevation_deg}°` : `${primaryTel.sun.elevation_deg}°`}
            </span>
            <span className="text-[10px] text-amber-300/80 font-mono">
              {(primaryTel.sun.visible_fraction * 100).toFixed(0)}% Disk Visible
            </span>
          </div>

          {/* 2. Earth Line of Sight */}
          <div className="bg-slate-900/80 border border-slate-800/80 rounded-xl p-2.5 flex flex-col gap-1">
            <span className="text-[10px] text-cyan-400 flex items-center gap-1 font-medium">
              <Radio className="w-3 h-3" /> Earth DTE Margin
            </span>
            <span
              className={`text-sm font-bold font-mono ${
                primaryTel.earth.visible ? 'text-emerald-400' : 'text-rose-400'
              }`}
            >
              {primaryTel.earth.clearance_margin_deg > 0
                ? `+${primaryTel.earth.clearance_margin_deg}°`
                : `${primaryTel.earth.clearance_margin_deg}°`}
            </span>
            <span className="text-[10px] font-mono text-slate-400">
              {primaryTel.earth.visible ? 'LOS Active' : 'Occulted by Ridge'}
            </span>
          </div>

          {/* 3. Operational State */}
          <div className="bg-slate-900/80 border border-slate-800/80 rounded-xl p-2.5 flex flex-col gap-1">
            <span className="text-[10px] text-slate-400 flex items-center gap-1 font-medium">
              <Activity className="w-3 h-3 text-purple-400" /> Operational Regime
            </span>
            <span className="text-xs font-bold text-slate-100 truncate">
              {primaryTel.regime.name}
            </span>
            <span
              className={`text-[9px] px-1.5 py-0.5 rounded font-mono font-semibold w-fit border ${
                primaryTel.regime.state === 1
                  ? 'bg-emerald-950 border-emerald-500/40 text-emerald-300'
                  : (primaryTel.regime.state === 2
                      ? 'bg-amber-950 border-amber-500/40 text-amber-300'
                      : (primaryTel.regime.state === 3
                          ? 'bg-purple-950 border-purple-500/40 text-purple-300'
                          : 'bg-rose-950 border-rose-500/40 text-rose-300'))
              }`}
            >
              {primaryTel.regime.badge}
            </span>
          </div>

          {/* 4. Instantaneous Power */}
          <div className="bg-slate-900/80 border border-slate-800/80 rounded-xl p-2.5 flex flex-col gap-1">
            <span className="text-[10px] text-yellow-400 flex items-center gap-1 font-medium">
              <Zap className="w-3 h-3" /> Power Gen / Load
            </span>
            <span className="text-sm font-bold font-mono text-slate-100">
              {primaryTel.power.generated_w.toFixed(0)} W
            </span>
            <span
              className={`text-[10px] font-mono ${
                primaryTel.power.net_w >= 0 ? 'text-emerald-400' : 'text-rose-400'
              }`}
            >
              Net: {primaryTel.power.net_w > 0 ? `+${primaryTel.power.net_w.toFixed(0)}` : primaryTel.power.net_w.toFixed(0)} W
            </span>
          </div>

          {/* 5. Battery State of Charge */}
          <div className="bg-slate-900/80 border border-slate-800/80 rounded-xl p-2.5 flex flex-col gap-1">
            <span className="text-[10px] text-emerald-400 flex items-center gap-1 font-medium">
              <BatteryCharging className="w-3 h-3" /> Battery SoC
            </span>
            <span
              className={`text-sm font-bold font-mono ${
                primaryTel.power.battery_soc_pct < 25 ? 'text-rose-400' : 'text-emerald-400'
              }`}
            >
              {primaryTel.power.battery_soc_pct.toFixed(1)}%
            </span>
            <div className="w-full bg-slate-950 h-1.5 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${
                  primaryTel.power.battery_soc_pct < 25 ? 'bg-rose-500' : 'bg-emerald-500'
                }`}
                style={{ width: `${Math.max(0, Math.min(100, primaryTel.power.battery_soc_pct))}%` }}
              />
            </div>
          </div>

          {/* 6. Event Horizon Lookahead */}
          <div className="bg-slate-900/80 border border-slate-800/80 rounded-xl p-2.5 flex flex-col gap-1">
            <span className="text-[10px] text-indigo-400 flex items-center gap-1 font-medium">
              <AlertTriangle className="w-3 h-3" /> Event Horizon
            </span>
            {primaryTel.upcoming_events?.length > 0 ? (
              <span className="text-[11px] font-medium text-amber-300 leading-tight">
                {primaryTel.upcoming_events[0].description}
              </span>
            ) : (
              <span className="text-[11px] text-slate-400">
                No transition detected in sampled 48h forecast
              </span>
            )}
          </div>
        </div>
      ) : (
        <div className="py-2 text-center text-xs text-slate-400 font-mono">
          Connecting to real-time simulation WebSocket...
        </div>
      )}
    </div>
  );
};
