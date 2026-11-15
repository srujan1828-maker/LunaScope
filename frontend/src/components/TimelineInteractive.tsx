import React, { useState, useRef, useMemo, useEffect, useCallback } from 'react';
import {
  CalendarDays,
  Calendar,
  Sun,
  Radio,
  Layers,
  BatteryCharging,
  BarChart3,
  Zap,
  Crosshair,
  Mountain,
  Compass,
  Database,
  Info,
  ChevronDown
} from 'lucide-react';
import { MissionState,missionStart } from '../mission';
import { LandingSite } from '../types';
import { Page } from '../pages';

interface TimelineInteractiveProps {
  state: MissionState;
  navigate?: (p: Page) => void;
  onContingency?: () => void;
}

// Operational State definitions
export type OperationalStateKey = 'nominal' | 'autonomous' | 'eclipse' | 'blackout' | 'unknown';

interface OperationalStateDef {
  key: OperationalStateKey;
  label: string;
  sublabel: string;
  color: string;
  badgeBg: string;
  badgeBorder: string;
}

const OP_STATES: Record<OperationalStateKey, OperationalStateDef> = {
  unknown:{key:'unknown',label:'Unknown',sublabel:'Insufficient terrain or visibility coverage',color:'#64748b',badgeBg:'#1e293b',badgeBorder:'#64748b'},
  nominal: {
    key: 'nominal',
    label: 'Nominal Science',
    sublabel: 'Sun and Earth geometrically visible',
    color: '#2a9d8f',
    badgeBg: 'rgba(42, 157, 143, 0.2)',
    badgeBorder: '#2a9d8f'
  },
  autonomous: {
    key: 'autonomous',
    label: 'Autonomous Day',
    sublabel: 'Sun visible; Earth blocked',
    color: '#dfa76a',
    badgeBg: 'rgba(223, 167, 106, 0.2)',
    badgeBorder: '#dfa76a'
  },
  eclipse: {
    key: 'eclipse',
    label: 'Tethered Eclipse',
    sublabel: 'Sun below threshold; Earth visible',
    color: '#7c3aed',
    badgeBg: 'rgba(124, 58, 237, 0.2)',
    badgeBorder: '#7c3aed'
  },
  blackout: {
    key: 'blackout',
    label: 'Total Blackout',
    sublabel: 'Sun below threshold; Earth blocked',
    color: '#334155',
    badgeBg: 'rgba(51, 65, 85, 0.3)',
    badgeBorder: '#475569'
  }
};

export const TimelineInteractive: React.FC<TimelineInteractiveProps> = ({
  state,
  navigate,
  onContingency
}) => {
  const selectedSiteId=state.primary;
  const setSelectedSiteId=state.setAsPrimary;
  const startDateStr=state.mission.start,windowDays=state.mission.days;
  const setStartDateStr=(v:string)=>state.update('start',v),setWindowDays=(v:number)=>state.update('days',v);
  const data=state.chartBusy?undefined:state.evaluation?.evaluated_sites[selectedSiteId];
  // Scrubber cursor progress (0.0 to 1.0)
  const [cursorProgress, setCursorProgress] = useState<number>(0);
  useEffect(()=>setCursorProgress(0),[startDateStr,windowDays,selectedSiteId]);
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [highlightedState, setHighlightedState] = useState<OperationalStateKey | null>(null);

  const chartSvgRef = useRef<SVGSVGElement | null>(null);
  const batterySvgRef = useRef<SVGSVGElement | null>(null);

  const found=state.sites.find(s=>s.site_id===selectedSiteId),ranking=state.rank(selectedSiteId),summary=data?.power_simulation?.summary;
  const siteInfo={name:found?.name||'Loading location…',coords:found?`${found.lat_deg.toFixed(3)}°, ${found.lon_deg.toFixed(3)}°E`:'Unknown',sunDays:ranking?(ranking.metrics.longest_sun_window_hours/24).toFixed(2):'Pending',jointDays:data?(data.interval_metrics.joint_availability_pct/100*windowDays).toFixed(2):'Pending',minBattery:summary?.min_soc_pct.toFixed(1)??'Unknown',energyMargin:summary?(summary.min_soc_pct-state.power.reserve_margin_pct).toFixed(1)+' pp':'Unknown',thumb:'/assets/nasa-lola-hillshade.png'};
  // Generate Date points across the window
  const startUnix = useMemo(() => {
    return new Date(missionStart(state.mission)).getTime();
  }, [startDateStr,state.mission.utcTime]);

  const endUnix = useMemo(() => {
    return startUnix + windowDays * 86400000;
  }, [startUnix, windowDays]);

  // Current scrubbed timestamp
  const currentUnix = useMemo(() => {
    return startUnix + cursorProgress * (endUnix - startUnix);
  }, [startUnix, endUnix, cursorProgress]);

  // Formatted scrubbed date string
  const currentFormattedTime = useMemo(() => {
    const d = new Date(currentUnix);
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const m = months[d.getUTCMonth()];
    const day = String(d.getUTCDate()).padStart(2, '0');
    const yr = d.getUTCFullYear();
    const hr = String(d.getUTCHours()).padStart(2, '0');
    const min = String(d.getUTCMinutes()).padStart(2, '0');
    return `${m} ${day}, ${yr} | ${hr}:${min} UTC`;
  }, [currentUnix]);

  const seriesData=useMemo(()=>{
    const keys:OperationalStateKey[]=['unknown','nominal','autonomous','eclipse','blackout'];
    return data?.timestamps.map((stamp,i)=>({t:(stamp*1000-startUnix)/(endUnix-startUnix),stamp,sunFraction:data.solar_fractions[i],dte:data.dte_visibility[i]==null?null:data.dte_visibility[i]>0,state:keys[data.operational_states[i]]||'unknown',batterySoc:data.power_simulation?.time_series.battery_soc_pct[i]??null}))||[];
  },[data,startUnix,endUnix]);
  const currentStatus=useMemo(()=>{
    // Use the preceding real sample, not an index proportional to time: samples are adaptive.
    let index=0;for(let i=0;i<seriesData.length;i++){if(seriesData[i].t<=cursorProgress)index=i;else break;}
    const p=seriesData[index];
    return {sunFraction:p?.sunFraction??null,dte:p?.dte??null,state:OP_STATES[p?.state||'unknown'],batterySoc:p?.batterySoc??null,stamp:p?.stamp};
  },[cursorProgress,seriesData]);
  // X-axis date ticks (one for each day in window)
  const dateTicks = useMemo(() => {
    const ticks: Array<{ dayStr: string; progress: number }> = [];
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    for (let day = 0; day <= windowDays; day+=Math.max(1,Math.ceil(windowDays/7))) {
      const d = new Date(startUnix + day * 86400000);
      const m = months[d.getUTCMonth()];
      const dayNum = String(d.getUTCDate()).padStart(2, '0');
      ticks.push({
        dayStr: `${m} ${dayNum}`,
        progress: day / windowDays
      });
    }
    return ticks;
  }, [startUnix, windowDays]);

  // SVG Coordinates calculation for Multi-Track Chart
  // Total SVG viewBox: 0 0 1000 275
  const SVG_W = 1000;
  const TRACK1_TOP = 10;
  const TRACK1_H = 110;
  const TRACK1_BOTTOM = TRACK1_TOP + TRACK1_H;

  const TRACK2_TOP = 145;
  const TRACK2_H = 34;

  const TRACK3_TOP = 195;
  const TRACK3_H = 34;

  const X_AXIS_Y = 245;

  // Path generator for Sunlight Fraction curve
  const { sunCurvePath, sunAreaPath, cursorSunY } = useMemo(() => {
    if (seriesData.length === 0) return { sunCurvePath: '', sunAreaPath: '', cursorSunY: TRACK1_BOTTOM };

    let curveStr='',areaStr='',gap=true;
    for(const p of seriesData){if(p.sunFraction==null){gap=true;continue;}const px=p.t*SVG_W,py=TRACK1_BOTTOM-p.sunFraction*TRACK1_H;curveStr+=`${gap?'M':'L'}${px},${py} `;gap=false;}
    return {sunCurvePath:curveStr,sunAreaPath:areaStr,cursorSunY:currentStatus.sunFraction==null?TRACK1_BOTTOM:TRACK1_BOTTOM-currentStatus.sunFraction*TRACK1_H};
  },[seriesData,currentStatus.sunFraction]);

  const segments=useMemo(()=>{
    const blocks:{start:number;end:number;state:OperationalStateDef;dte:boolean|null}[]=[];
    for(let i=0;i<seriesData.length-1;i++){const p=seriesData[i],end=seriesData[i+1].t,prev=blocks[blocks.length-1];if(prev&&prev.state.key===p.state&&prev.dte===p.dte)prev.end=end;else blocks.push({start:p.t,end,state:OP_STATES[p.state],dte:p.dte});}
    return blocks;
  },[seriesData]);
  const dteBlocks=segments.filter(b=>b.dte===true),opStateBlocks=segments;
  const batteryPoints=seriesData.filter(p=>p.batterySoc!=null).map(p=>({label:new Date(p.stamp*1000).toISOString(),progress:p.t,soc:p.batterySoc!}));
  // Scrubber interactive event handlers
  const handlePointerSeek = useCallback(
    (clientX: number, targetSvg: SVGSVGElement | null) => {
      if (!targetSvg) return;
      const rect = targetSvg.getBoundingClientRect();
      const relX = clientX - rect.left;
      const progress = Math.max(0, Math.min(1, relX / rect.width));
      setCursorProgress(progress);
    },
    []
  );

  const handleMouseDown = (e: React.MouseEvent<SVGSVGElement>, svg: SVGSVGElement | null) => {
    setIsDragging(true);
    handlePointerSeek(e.clientX, svg);
  };

  const handleMouseMove = (e: React.MouseEvent<SVGSVGElement>, svg: SVGSVGElement | null) => {
    if (isDragging || e.buttons === 1) {
      handlePointerSeek(e.clientX, svg);
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  useEffect(() => {
    const globalMouseUp = () => setIsDragging(false);
    window.addEventListener('mouseup', globalMouseUp);
    return () => window.removeEventListener('mouseup', globalMouseUp);
  }, []);

  return (
    <div className="timeline-page-layout">

      {/* Main Content Area */}
      <div className="timeline-main-column">
        {/* Header & Filter Bar */}
        <div className="timeline-header-bar">
          <div className="header-title-group">
            <CalendarDays size={28} className="timeline-header-icon" />
            <div>
              <h1>Mission Timeline</h1>
              <p>Track sunlight, communication and operational state throughout the selected mission window.</p>
            </div>
          </div>

          {/* Top Filter Controls */}
          <div className="timeline-filter-group">
            <div className="filter-item">
              <label htmlFor="site-select">Site</label>
              <div className="select-wrapper">
                <select
                  id="site-select"
                  value={selectedSiteId}
                  onChange={e => setSelectedSiteId(e.target.value)}
                >
                  {state.sites
                    .map((s: LandingSite) => (
                      <option key={s.site_id} value={s.site_id}>
                        {s.name}
                      </option>
                    ))}
                </select>
                <ChevronDown size={14} className="select-arrow" />
              </div>
            </div>

            <div className="filter-item">
              <label htmlFor="start-date-input">Start Date</label>
              <div className="date-input-wrap">
                <input
                  id="start-date-input" min="2025-01-01" max="2032-12-31"
                  type="date"
                  value={startDateStr}
                  onChange={e => e.target.value && setStartDateStr(e.target.value)}
                />
                <Calendar size={14} className="date-icon" />
              </div>
            </div>

            <div className="filter-item">
              <label htmlFor="window-select">Window</label>
              <div className="select-wrapper">
                <select
                  id="window-select"
                  value={windowDays}
                  onChange={e => setWindowDays(Number(e.target.value))}
                >
                  {![7,14,30,60,90,180].includes(windowDays)&&<option value={windowDays}>{windowDays} days</option>}<option value={7}>7 days</option>
                  <option value={14}>14 days</option>
                  <option value={30}>30 days</option>
                  <option value={60}>60 days</option>
                  <option value={90}>90 days</option>
                  <option value={180}>180 days</option>
                </select>
                <ChevronDown size={14} className="select-arrow" />
              </div>
            </div>
          </div>
        </div>

        {(state.chartBusy||state.chartError)&&<p className="mission-feedback" role={state.chartError?'alert':'status'}>{state.chartError||'Calculating visibility and battery state for the selected mission…'}</p>}
        <p className="chart-caption">NASA terrain / SPICE geometry · {startDateStr} {state.mission.utcTime||'00:00'} UTC · {windowDays} days. Battery values use your configured hardware. No DSN schedule is implied.</p>
        <label className="timeline-accessible-seek">Mission time<input aria-label="Timeline time" type="range" min="0" max="1" step="0.001" value={cursorProgress} onChange={e=>setCursorProgress(Number(e.target.value))}/></label>
        {/* Middle Section: Multi-Track Timeline Chart (Left) + Site/States (Right) */}
        <div className="timeline-middle-grid">
          {/* Left Column: Interactive Multi-Track Timeline Chart */}
          <section className="timeline-multitrack-card">
            {/* Left labels column */}
            <div className="track-labels-col">
              {/* Track 1 Label & Y-Scale */}
              <div className="track-label-block track1">
                <div className="track-title-text">
                  <span>Sunlight</span>
                  <span>Fraction</span>
                  <span>f(t)</span>
                </div>
                <div className="track1-scale">
                  <span>1.0</span>
                  <span>0.75</span>
                  <span>0.50</span>
                  <span>0.25</span>
                  <span>0.0</span>
                </div>
              </div>

              {/* Track 2 Label */}
              <div className="track-label-block track2">
                <div className="track-title-text">
                  <span>DTE</span>
                  <span>Visibility</span>
                  <span>(Earth LOS)</span>
                </div>
              </div>

              {/* Track 3 Label */}
              <div className="track-label-block track3">
                <div className="track-title-text">
                  <span>Operational</span>
                  <span>State</span>
                </div>
              </div>
            </div>

            {/* Right SVG Tracks Area */}
            <div className="track-svg-container">
              <svg
                ref={chartSvgRef}
                viewBox={`0 0 ${SVG_W} 275`}
                className="multitrack-svg"
                preserveAspectRatio="none"
                onMouseDown={e => handleMouseDown(e, chartSvgRef.current)}
                onMouseMove={e => handleMouseMove(e, chartSvgRef.current)}
                onMouseUp={handleMouseUp}
                onClick={e => handlePointerSeek(e.clientX, chartSvgRef.current)}
              >
                <defs>
                  {/* Gold gradient for sunlight fraction fill */}
                  <linearGradient id="goldAreaGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#dfa76a" stopOpacity="0.45" />
                    <stop offset="60%" stopColor="#dfa76a" stopOpacity="0.15" />
                    <stop offset="100%" stopColor="#dfa76a" stopOpacity="0.01" />
                  </linearGradient>
                </defs>

                {/* --- TRACK 1: Sunlight Fraction f(t) --- */}
                {[0, 0.25, 0.5, 0.75, 1.0].map(val => {
                  const y = TRACK1_BOTTOM - val * TRACK1_H;
                  return (
                    <line
                      key={val}
                      x1="0"
                      y1={y}
                      x2={SVG_W}
                      y2={y}
                      stroke="rgba(255,255,255,0.07)"
                      strokeDasharray="3 3"
                    />
                  );
                })}

                {/* Filled gradient area under sunlight curve */}
                <path d={sunAreaPath} fill="url(#goldAreaGrad)" />

                {/* Golden curve line */}
                <path
                  d={sunCurvePath}
                  fill="none"
                  stroke="#dfa76a"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                />

                {/* --- TRACK 2: DTE Visibility (Earth LOS) --- */}
                <rect
                  x="0"
                  y={TRACK2_TOP}
                  width={SVG_W}
                  height={TRACK2_H}
                  rx="4"
                  fill="#030b12"
                  stroke="#122536"
                  strokeWidth="1"
                />
                {dteBlocks.map((blk, idx) => (
                  <rect
                    key={idx}
                    x={blk.start * SVG_W}
                    y={TRACK2_TOP + 2}
                    width={(blk.end - blk.start) * SVG_W}
                    height={TRACK2_H - 4}
                    rx="3"
                    fill="#2a9d8f"
                  />
                ))}

                {/* --- TRACK 3: Operational State --- */}
                <rect
                  x="0"
                  y={TRACK3_TOP}
                  width={SVG_W}
                  height={TRACK3_H}
                  rx="4"
                  fill="#030b12"
                  stroke="#122536"
                  strokeWidth="1"
                />
                {opStateBlocks.map((blk, idx) => {
                  const isHighlighted = !highlightedState || highlightedState === blk.state.key;
                  return (
                    <rect
                      key={idx}
                      x={blk.start * SVG_W}
                      y={TRACK3_TOP + 2}
                      width={(blk.end - blk.start) * SVG_W}
                      height={TRACK3_H - 4}
                      rx="3"
                      fill={blk.state.color}
                      opacity={isHighlighted ? 1 : 0.3}
                      style={{ transition: 'opacity 0.2s ease' }}
                    />
                  );
                })}

                {/* --- X-AXIS TICKS & DATES --- */}
                <line
                  x1="0"
                  y1={X_AXIS_Y}
                  x2={SVG_W}
                  y2={X_AXIS_Y}
                  stroke="#1e293b"
                  strokeWidth="1"
                />
                {dateTicks.map(tick => {
                  const x = tick.progress * SVG_W;
                  return (
                    <g key={tick.dayStr}>
                      <line
                        x1={x}
                        y1={X_AXIS_Y}
                        x2={x}
                        y2={X_AXIS_Y + 5}
                        stroke="#475569"
                        strokeWidth="1"
                      />
                      <text
                        x={x}
                        y={X_AXIS_Y + 18}
                        fill="#94a3b8"
                        fontSize="11"
                        textAnchor="middle"
                        fontFamily="system-ui, -apple-system, sans-serif"
                      >
                        {tick.dayStr}
                      </text>
                    </g>
                  );
                })}

                {/* --- SYNCHRONIZED INTERACTIVE SCRUBBER CURSOR --- */}
                <line
                  x1={cursorProgress * SVG_W}
                  y1={TRACK1_TOP}
                  x2={cursorProgress * SVG_W}
                  y2={X_AXIS_Y}
                  stroke="#ffffff"
                  strokeDasharray="4 3"
                  strokeWidth="1.5"
                  pointerEvents="none"
                />

                {/* White handle circle at intersection with sunlight curve */}
                <circle
                  opacity={currentStatus.sunFraction==null?0:1}
                  cx={cursorProgress * SVG_W}
                  cy={cursorSunY}
                  r="5.5"
                  fill="#ffffff"
                  stroke="#dfa76a"
                  strokeWidth="2.5"
                  filter="drop-shadow(0px 0px 4px rgba(223, 167, 106, 0.8))"
                  pointerEvents="none"
                />
              </svg>
            </div>
          </section>

          {/* Right Column: Selected Site & Operational States Cards */}
          <div className="timeline-sidebar-cards">
            {/* Card 1: Selected Site */}
            <div className="timeline-info-card site-card">
              <div className="card-header">
                <Crosshair size={18} className="gold-icon" />
                <h3>Selected Site</h3>
              </div>
              <div className="site-card-body">
                <div className="crater-thumb-wrap">
                  <img src={siteInfo.thumb} alt="Regional NASA LOLA hillshade, not a local site photograph" className="crater-thumb-img" />
                  
                </div>
                <div className="site-meta-details">
                  <h4>{siteInfo.name}</h4>
                  <p>{siteInfo.coords}</p>
                </div>
              </div>
            </div>

            {/* Card 2: Operational States (i) */}
            <div className="timeline-info-card states-card">
              <div className="card-header">
                <Compass size={18} className="gold-icon" />
                <h3>Operational States</h3>
                <span
                  className="info-icon"
                  title="Operational states determined by simultaneous sunlight and DTE visibility"
                >
                  <Info size={14} />
                </span>
              </div>
              <div className="states-list">
                {Object.values(OP_STATES).map(st => (
                  <div
                    key={st.key}
                    className="state-legend-row"
                    onMouseEnter={() => setHighlightedState(st.key)}
                    onMouseLeave={() => setHighlightedState(null)}
                    style={{ cursor: 'pointer' }}
                  >
                    <span className="state-swatch-box" style={{ background: st.color }} />
                    <div className="state-desc-group">
                      <strong>{st.label}</strong>
                      <span>{st.sublabel}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Section: Three Cards */}
        <div className="timeline-bottom-grid">
          {/* Card 1: Selected Time & State Status */}
          <div className="timeline-bottom-card status-card">
            <div className="bottom-card-header">
              <CalendarDays size={18} className="gold-icon" />
              <h3>Selected Time</h3>
            </div>
            <div className="primary-time-display">{currentFormattedTime}</div><small>{currentStatus.stamp?`Sample: ${new Date(currentStatus.stamp*1000).toISOString()}`:'No computed sample available'}</small>

            <div className="metric-status-rows">
              <div className="status-row">
                <div className="row-label">
                  <Sun size={16} className="metric-icon" />
                  <span>Sunlight Fraction</span>
                </div>
                <strong className="row-value">{currentStatus.sunFraction==null?'Unknown':currentStatus.sunFraction.toFixed(2)}</strong>
              </div>

              <div className="status-row">
                <div className="row-label">
                  <Radio size={16} className="metric-icon" />
                  <span>DTE Visibility</span>
                </div>
                <strong className="row-value">{currentStatus.dte==null?'Unknown':currentStatus.dte?'Yes':'No'}</strong>
              </div>

              <div className="status-row">
                <div className="row-label">
                  <Layers size={16} className="metric-icon" />
                  <span>Operational State</span>
                </div>
                <span
                  className="state-badge-pill"
                  style={{
                    backgroundColor: currentStatus.state.badgeBg,
                    borderColor: currentStatus.state.badgeBorder,
                    color: currentStatus.state.color === '#334155' ? '#94a3b8' : currentStatus.state.color
                  }}
                >
                  {currentStatus.state.label}
                </span>
              </div>
            </div>
          </div>

          {/* Card 2: Battery State of Charge (SoC) */}
          <div className="timeline-bottom-card battery-card">
            <div className="bottom-card-header">
              <BatteryCharging size={18} className="gold-icon" />
              <h3>Battery State of Charge (SoC)</h3>
            </div>

            <div className="battery-chart-wrap">
              {/* Mini Battery SVG Chart */}
              <div className="battery-svg-inner">
                {/* Y-axis Labels */}
                <div className="battery-y-labels">
                  <span>100%</span>
                  <span>75%</span>
                  <span>50%</span>
                  <span>25%</span>
                  <span>0%</span>
                </div>

                <div className="battery-svg-col">
                  <svg
                    ref={batterySvgRef}
                    viewBox="0 0 400 110"
                    className="battery-svg"
                    preserveAspectRatio="none"
                    onMouseDown={e => handleMouseDown(e, batterySvgRef.current)}
                    onMouseMove={e => handleMouseMove(e, batterySvgRef.current)}
                    onMouseUp={handleMouseUp}
                    onClick={e => handlePointerSeek(e.clientX, batterySvgRef.current)}
                    style={{ cursor: 'crosshair' }}
                  >
                    {/* Horizontal grid lines */}
                    {[0, 0.25, 0.5, 0.75, 1.0].map(v => (
                      <line
                        key={v}
                        x1="0"
                        y1={10 + (1 - v) * 80}
                        x2="400"
                        y2={10 + (1 - v) * 80}
                        stroke="rgba(255,255,255,0.06)"
                        strokeDasharray="2 2"
                      />
                    ))}

                    {/* Cyan line connecting battery SoC */}
                    {(() => {
                      const pts = batteryPoints.map(p => ({
                        x: p.progress * 400,
                        y: 10 + (1 - p.soc / 100) * 80
                      }));
                      if(!pts.length)return <text x="100" y="50" fill="#94a3b8">No battery data</text>;
                      const pathStr = `M ${pts[0].x} ${pts[0].y} ` + pts.slice(1).map(pt => `L ${pt.x} ${pt.y}`).join(' ');
                      return (
                        <>
                          <path
                            d={pathStr}
                            fill="none"
                            stroke="#38bdf8"
                            strokeWidth="2"
                            strokeLinecap="round"
                          />
                          {pts.map((pt, i) => (
                            <circle key={i} cx={pt.x} cy={pt.y} r="3" fill="#38bdf8" />
                          ))}
                        </>
                      );
                    })()}

                    {/* Synchronized Vertical Cursor line */}
                    <line
                      x1={cursorProgress * 400}
                      y1="5"
                      x2={cursorProgress * 400}
                      y2="95"
                      stroke="#ffffff"
                      strokeDasharray="3 3"
                      strokeWidth="1.2"
                    />

                    {/* Highlight Ring Circle at scrubbed battery SoC */}
                    <circle
                      opacity={currentStatus.batterySoc==null?0:1}
                      cx={cursorProgress * 400}
                      cy={10 + (1 - (currentStatus.batterySoc??0) / 100) * 80}
                      r="5"
                      fill="#051019"
                      stroke="#38bdf8"
                      strokeWidth="2.5"
                    />
                  </svg>

                  {/* X-axis date labels */}
                  <div className="battery-x-labels">
                    {dateTicks.map(p => (
                      <span key={p.dayStr}>{p.dayStr}</span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Card 3: Key Metrics (Window) */}
          <div className="timeline-bottom-card metrics-card">
            <div className="bottom-card-header">
              <BarChart3 size={18} className="gold-icon" />
              <h3>Key Metrics (Window)</h3>
            </div>

            <div className="key-metrics-list">
              <div className="metric-item-row">
                <div className="row-label">
                  <Sun size={16} className="metric-icon" />
                  <span>Consecutive Sunlight</span>
                </div>
                <strong className="row-value">{siteInfo.sunDays} days</strong>
              </div>

              <div className="metric-item-row">
                <div className="row-label">
                  <Radio size={16} className="metric-icon" />
                  <span>Sun + Earth Visibility</span>
                </div>
                <strong className="row-value">{siteInfo.jointDays} days</strong>
              </div>

              <div className="metric-item-row">
                <div className="row-label">
                  <Calendar size={16} className="metric-icon" />
                  <span>Min. Battery SoC</span>
                </div>
                <strong className="row-value">{siteInfo.minBattery}%</strong>
              </div>

              <div className="metric-item-row">
                <div className="row-label">
                  <Zap size={16} className="metric-icon gold-icon" />
                  <span>Minimum SoC above reserve</span>
                </div>
                <strong className="row-value highlight-gold">{siteInfo.energyMargin}</strong>
              </div>
            </div>
          </div>
        </div>

        {/* Footer Bar: Operational Timeline (Legend) */}
        <div className="operational-legend-footer">
          <div className="legend-title">
            <Layers size={18} className="gold-icon" />
            <span>Operational Timeline (Legend)</span>
          </div>

          <div className="legend-pills-row">
            {Object.values(OP_STATES).map(st => (
              <div
                key={st.key}
                className="legend-pill"
                onMouseEnter={() => setHighlightedState(st.key)}
                onMouseLeave={() => setHighlightedState(null)}
                style={{
                  cursor: 'pointer',
                  borderColor: highlightedState === st.key ? st.color : '#1e293b',
                  boxShadow: highlightedState === st.key ? `0 0 10px ${st.color}40` : 'none',
                  transition: 'all 0.2s ease'
                }}
              >
                <span className="pill-dot" style={{ backgroundColor: st.color }} />
                <span>{st.label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
