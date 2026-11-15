import React, { useState, useRef, useEffect, useMemo } from 'react';
import {
  BookOpen,
  Home,
  Moon,
  Orbit,
  Zap,
  Radio,
  Clock,
  Compass,
  FileText,
  CheckCircle2,
  Layers,
  ArrowRight,
  Play,
  Pause,
  RotateCcw,
  Sun,
  Mountain,
  ShieldCheck,
  ChevronRight,
  Info,
  FlaskConical,
  Snowflake,
  Thermometer,
  Telescope,
  ArrowLeftRight,
  Target,
  Calendar,
  Search,
  MapPin
} from 'lucide-react';
import { Page } from '../pages';

interface LearnInteractiveProps {
  navigate?: (p: Page) => void;
}

export type LearnTabKey =
  | 'big-picture'
  | 'south-pole'
  | 'sun-earth-motion'
  | 'power-illumination'
  | 'communication'
  | 'mission-challenges'
  | 'key-terms';

interface TabItem {
  key: LearnTabKey;
  label: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
}

const TABS: TabItem[] = [
  { key: 'big-picture', label: 'The Big Picture', icon: Home },
  { key: 'south-pole', label: 'Lunar South Pole', icon: Moon },
  { key: 'sun-earth-motion', label: 'Sun & Earth Motion', icon: Orbit },
  { key: 'power-illumination', label: 'Power & Illumination', icon: Zap },
  { key: 'communication', label: 'Communication (DTE)', icon: Radio },
  { key: 'mission-challenges', label: 'Mission Challenges', icon: Clock },
  { key: 'key-terms', label: 'Key Terms', icon: FileText }
];

export const LearnInteractive: React.FC<LearnInteractiveProps> = ({ navigate }) => {
  const [activeTab, setActiveTab] = useState<LearnTabKey>('big-picture');

  // Animation states for the Hero Moon-Sun-Earth simulation
  const heroVideoRef = useRef<HTMLVideoElement>(null);
  const [isPlaying, setIsPlaying] = useState<boolean>(true);
  const [orbitAngle, setOrbitAngle] = useState<number>(35); // 0 to 360 degrees
  const [highlightTarget, setHighlightTarget] = useState<'sun' | 'earth' | 'moon' | null>(null);

  // Handlers for Hero Video Playback & Scrubbing
  const toggleHeroPlay = () => {
    if (heroVideoRef.current) {
      if (isPlaying) {
        heroVideoRef.current.pause();
      } else {
        heroVideoRef.current.play().catch(() => {});
      }
    }
    setIsPlaying(p => !p);
  };

  const handleHeroReset = () => {
    if (heroVideoRef.current) {
      heroVideoRef.current.currentTime = 0;
      heroVideoRef.current.pause();
    }
    setIsPlaying(false);
    setOrbitAngle(0);
  };

  const handleHeroSliderChange = (deg: number) => {
    setOrbitAngle(deg);
    if (heroVideoRef.current && heroVideoRef.current.duration) {
      heroVideoRef.current.pause();
      heroVideoRef.current.currentTime = (deg / 360) * heroVideoRef.current.duration;
    }
    setIsPlaying(false);
  };

  // Interactive controls for sub-tabs
  const [mastHeight, setMastHeight] = useState<number>(2.0);
  const [sunElevationDeg, setSunElevationDeg] = useState<number>(1.2);
  const [earthLibrationPhase, setEarthLibrationPhase] = useState<number>(14); // 0 to 27.3 days
  const [craterDepthRatio, setCraterDepthRatio] = useState<number>(0.2); // depth-to-diameter
  const [commElevationMask, setCommElevationMask] = useState<number>(0.0); // minimum elevation mask deg
  const [glossarySearch, setGlossarySearch] = useState<string>('');
  const [glossaryCategory, setGlossaryCategory] = useState<string>('All Terms');
  const [isPlayingLibration, setIsPlayingLibration] = useState<boolean>(false);

  // Auto-play loop for Earth optical libration simulator
  useEffect(() => {
    if (!isPlayingLibration) return;
    const interval = setInterval(() => {
      setEarthLibrationPhase(prev => {
        const next = prev + 0.1;
        return next > 27.3 ? 0 : Number(next.toFixed(1));
      });
    }, 50);
    return () => clearInterval(interval);
  }, [isPlayingLibration]);

  // Optical libration physics calculations (anomalistic / draconic month)
  // At Day 14.0 (halfway through the 27.3-day anomalistic month), Earth crosses the sky origin (0°, 0°)
  const phaseRad = useMemo(() => {
    return ((earthLibrationPhase - 14.0) / 27.3) * 2 * Math.PI;
  }, [earthLibrationPhase]);

  const currentLon = useMemo(() => {
    return 7.9 * Math.sin(phaseRad);
  }, [phaseRad]);

  const currentLat = useMemo(() => {
    return 6.68 * Math.sin(phaseRad * 2);
  }, [phaseRad]);

  // Visual SVG coordinates
  const librationCX = 512;
  const librationCY = 215;
  const librationRX = 237;
  const librationRY = 110;

  const librationEarthX = useMemo(() => {
    return librationCX + (currentLon / 7.9) * librationRX;
  }, [currentLon]);

  const librationEarthY = useMemo(() => {
    return librationCY - (currentLat / 6.68) * librationRY;
  }, [currentLat]);

  // Synchronize 60fps orbit angle with video playback
  useEffect(() => {
    let animFrame: number;
    if (isPlaying) {
      const step = () => {
        if (heroVideoRef.current && heroVideoRef.current.duration) {
          const deg = (heroVideoRef.current.currentTime / heroVideoRef.current.duration) * 360;
          setOrbitAngle(deg);
        }
        animFrame = requestAnimationFrame(step);
      };
      animFrame = requestAnimationFrame(step);
    }
    return () => cancelAnimationFrame(animFrame);
  }, [isPlaying]);

  // Derived positions for Sun & Earth in Hero SVG (viewBox 0 0 760 360)
  const heroPositions = useMemo(() => {
    const cx = 380;
    const cy = 210;
    const rx = 240;
    const ry = 58;

    const rad = (orbitAngle * Math.PI) / 180;
    // Sun position on elliptical grazing ecliptic path
    const sunX = cx - rx * Math.cos(rad);
    const sunY = cy - 25 - ry * Math.sin(rad);

    // Current Sun topocentric elevation near South Pole: oscillates between -1.54 and +1.54
    const sunElev = (Math.sin(rad) * 1.54).toFixed(2);

    // Earth position with optical libration wobble (27.3 days period)
    const earthBaseX = cx + 220;
    const earthBaseY = cy - 65;
    const libRad = ((earthLibrationPhase / 27.3) * 2 * Math.PI) + (rad * 0.1);
    const earthX = earthBaseX + 12 * Math.cos(libRad);
    const earthY = earthBaseY + 8 * Math.sin(libRad * 2);

    return {
      cx,
      cy,
      rx,
      ry,
      sunX,
      sunY,
      sunElev,
      earthX,
      earthY
    };
  }, [orbitAngle, earthLibrationPhase]);

  return (
    <div className="learn-page-layout">
      {/* Background Floating Earth Orb (Top Right) */}
      <div className="learn-space-earth-wrap">
        <img
          src="/assets/earth-floating.png"
          alt="Earth viewed from Moon"
          className="learn-floating-earth"
        />
      </div>

      {/* Left Navigation Sidebar */}
      <aside className="learn-nav-sidebar">
        <div className="sidebar-header-title">
          <BookOpen size={20} className="gold-icon" />
          <span>Learn</span>
        </div>

        <nav className="learn-sidebar-nav">
          {TABS.map(tab => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.key;
            return (
              <button
                key={tab.key}
                className={`learn-sidebar-pill ${isActive ? 'active' : ''}`}
                onClick={() => setActiveTab(tab.key)}
              >
                <Icon size={18} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </aside>

      {/* Main Content Area */}
      <div className="learn-main-column"><p className="learning-scope">Concept illustrations and teaching controls, not measured terrain or live mission predictions. Use the planner and horizon simulator for NASA-data calculations.</p>
        {/* Page Title & Intro */}
        <header className="learn-header-bar">
          <div className="learn-header-row">
            <div className="learn-title-group">
              <span className="eyebrow">LEARN</span>
              <h1>The Big Picture</h1>
              <p>
                Understand the lunar environment, the key orbital dynamics and why landing site and
                timing matter for a successful Moon mission.
              </p>
            </div>
          </div>
        </header>

        {/* Tab 1: The Big Picture (Mockup Match) */}
        {activeTab === 'big-picture' && (
          <>
            {/* Middle Hero Section: Two Columns */}
            <div className="learn-hero-grid">
              {/* Left Hero Card: The Moon-Sun-Earth System Simulation */}
              <div className="learn-hero-card">
                <div className="hero-card-header">
                  <h2>The Moon–Sun–Earth System</h2>
                  <p>
                    The Moon&apos;s rotation axis is tilted by only <strong>1.54°</strong> to the ecliptic,
                    so near the south pole the Sun skims the horizon all year. Earth also stays near a
                    fixed direction, wobbling slightly due to optical libration.
                  </p>
                  <div className="hero-action-row">
                    <button
                      className="button gold-action-btn"
                      onClick={toggleHeroPlay}
                    >
                      {isPlaying ? (
                        <>
                          <Pause size={15} /> Pause Motion
                        </>
                      ) : (
                        <>
                          <Play size={15} /> See It in Motion ▶
                        </>
                      )}
                    </button>
                    <button
                      className="button subtle-reset-btn"
                      onClick={handleHeroReset}
                      title="Reset orbit angle"
                    >
                      <RotateCcw size={14} /> Reset
                    </button>
                    <span className="telemetry-badge">
                      Sun Elev: <strong>{heroPositions.sunElev}°</strong> | Libration: <strong>±6.7°</strong>
                    </span>
                  </div>
                </div>

                {/* Interactive Orbital Video Player */}
                <div className="hero-svg-container">
                  <video
                    ref={heroVideoRef}
                    src="/assets/learn-orbit-sim.mp4"
                    className="hero-orbit-video"
                    autoPlay
                    muted
                    loop
                    playsInline
                    onClick={toggleHeroPlay}
                    onPlay={() => setIsPlaying(true)}
                    onPause={() => setIsPlaying(false)}
                  />
                  <div className="hero-video-overlay-badge">
                    <span>Moon (1.54° tilt) • South Pole Diurnal Orbit</span>
                  </div>
                </div>

                {/* Interactive Slider to scrub Sun position manually */}
                <div className="hero-slider-bar">
                  <span className="slider-label">Orbit Angle (Diurnal Cycle):</span>
                  <input
                    type="range"
                    min="0"
                    max="360"
                    value={orbitAngle}
                    onChange={e => handleHeroSliderChange(Number(e.target.value))}
                    className="orbit-slider"
                  />
                  <span className="slider-value">{Math.round(orbitAngle)}°</span>
                </div>
              </div>

              {/* Right Hero Card: Key Takeaways */}
              <div className="learn-takeaways-card">
                <div className="takeaways-header">
                  <Zap size={18} className="gold-icon" />
                  <h2>Key Takeaways</h2>
                </div>

                <div className="takeaways-list">
                  <div
                    className="takeaway-item"
                    onMouseEnter={() => setHighlightTarget('sun')}
                    onMouseLeave={() => setHighlightTarget(null)}
                  >
                    <CheckCircle2 size={18} className="takeaway-check-icon" />
                    <p>
                      <strong>Sun elevation stays between ±1.54°</strong> near the south pole.
                    </p>
                  </div>

                  <div
                    className="takeaway-item"
                    onMouseEnter={() => setHighlightTarget('earth')}
                    onMouseLeave={() => setHighlightTarget(null)}
                  >
                    <CheckCircle2 size={18} className="takeaway-check-icon" />
                    <p>
                      <strong>Earth shifts by about ±6.68°</strong> (latitude) and <strong>±7.9°</strong> (longitude)
                      over 27.3 days (optical libration).
                    </p>
                  </div>

                  <div
                    className="takeaway-item"
                    onMouseEnter={() => setHighlightTarget('moon')}
                    onMouseLeave={() => setHighlightTarget(null)}
                  >
                    <CheckCircle2 size={18} className="takeaway-check-icon" />
                    <p>
                      <strong>Terrain (craters and ridges)</strong> can block sunlight and Earth&apos;s
                      line-of-sight.
                    </p>
                  </div>

                  <div className="takeaway-item">
                    <CheckCircle2 size={18} className="takeaway-check-icon" />
                    <p>
                      <strong>Choosing the right site and date</strong> helps evaluate power and communication opportunities.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Bottom Section: Explore the Concepts Grid */}
            <section className="explore-concepts-section">
              <div className="concepts-header">
                <div className="concepts-title-row">
                  <Layers size={20} className="gold-icon" />
                  <h3>Explore the Concepts</h3>
                </div>
                <p>Dive into the key ideas that power LunaScope.</p>
              </div>

              <div className="concepts-card-grid">
                {/* Concept Card 1: Lunar South Pole */}
                <article
                  className="concept-card"
                  onClick={() => setActiveTab('south-pole')}
                >
                  <div className="card-thumb-wrap">
                    <img
                      src="/assets/learn-lunar-south-pole.png"
                      alt="Lunar South Pole crater"
                      className="card-thumb-img"
                    />
                  </div>
                  <div className="card-body">
                    <div className="card-text">
                      <h4>Lunar South Pole</h4>
                      <p>Why it&apos;s unique and important for future missions.</p>
                    </div>
                    <button className="card-arrow-btn" aria-label="Explore Lunar South Pole">
                      <ArrowRight size={15} />
                    </button>
                  </div>
                </article>

                {/* Concept Card 2: Sun & Earth Motion */}
                <article
                  className="concept-card"
                  onClick={() => setActiveTab('sun-earth-motion')}
                >
                  <div className="card-thumb-wrap">
                    <img
                      src="/assets/learn-orbit-motion.png"
                      alt="Sun & Earth Motion"
                      className="card-thumb-img"
                    />
                  </div>
                  <div className="card-body">
                    <div className="card-text">
                      <h4>Sun & Earth Motion</h4>
                      <p>How the Sun and Earth move in the lunar sky.</p>
                    </div>
                    <button className="card-arrow-btn" aria-label="Explore Sun & Earth Motion">
                      <ArrowRight size={15} />
                    </button>
                  </div>
                </article>

                {/* Concept Card 3: Power & Illumination */}
                <article
                  className="concept-card"
                  onClick={() => setActiveTab('power-illumination')}
                >
                  <div className="card-thumb-wrap">
                    <img
                      src="/assets/learn-solar-array.png"
                      alt="Power & Illumination"
                      className="card-thumb-img"
                    />
                  </div>
                  <div className="card-body">
                    <div className="card-text">
                      <h4>Power & Illumination</h4>
                      <p>Estimating sunlight, shadows and energy generation.</p>
                    </div>
                    <button className="card-arrow-btn" aria-label="Explore Power & Illumination">
                      <ArrowRight size={15} />
                    </button>
                  </div>
                </article>

                {/* Concept Card 4: Communication (DTE) */}
                <article
                  className="concept-card"
                  onClick={() => setActiveTab('communication')}
                >
                  <div className="card-thumb-wrap">
                    <img
                      src="/assets/learn-dte-antenna.png"
                      alt="Communication DTE"
                      className="card-thumb-img"
                    />
                  </div>
                  <div className="card-body">
                    <div className="card-text">
                      <h4>Communication (DTE)</h4>
                      <p>When Earth is visible and how communication windows work.</p>
                    </div>
                    <button className="card-arrow-btn" aria-label="Explore Communication DTE">
                      <ArrowRight size={15} />
                    </button>
                  </div>
                </article>
              </div>
            </section>
          </>
        )}

        {/* Tab 2: Lunar South Pole (Mockup Match) */}
        {activeTab === 'south-pole' && (
          <div className="learn-south-pole-view">
            {/* Top Banner Card */}
            <div className="south-pole-banner-card">
              <div className="banner-thumb-wrap">
                <img
                  src="/assets/learn-lunar-south-pole.png"
                  alt="Lunar South Pole Crater"
                  className="banner-thumb-img"
                />
              </div>
              <div className="banner-content">
                <h2>Lunar South Pole: Peaks of Eternal Light &amp; Shadowed Craters</h2>
                <p>
                  Because the Moon has almost no axial tilt (only 1.54°), sunlight strikes polar topography at very shallow grazing angles. High elevated crater rims can remain illuminated for over 100 consecutive days, while deep crater depressions are permanently shrouded in darkness (PSRs), preserving ancient volatile water ice at cryogenic temperatures of ~40 K.
                </p>
              </div>
            </div>

            {/* Middle Section: Interactive Crater Shadow & PSR Lab */}
            <div className="crater-lab-container">
              {/* Left Column: Controls & Telemetry */}
              <div className="crater-lab-controls-col">
                <div className="lab-controls-header">
                  <div className="lab-title-row">
                    <FlaskConical size={20} className="gold-icon" />
                    <h3>Interactive Crater Shadow &amp; PSR Lab</h3>
                  </div>
                  <p>Adjust the parameters to see how sunlight and crater geometry create permanently shadowed regions.</p>
                </div>

                <div className="lab-sliders-list">
                  {/* Sun Elevation Angle Slider */}
                  <div className="lab-slider-group">
                    <div className="slider-label-row">
                      <div className="label-with-icon">
                        <Sun size={16} className="control-icon" />
                        <span>Sun Elevation Angle</span>
                        <span className="info-badge-dot" title="Topocentric solar elevation above local terrain horizon">
                          <Info size={13} />
                        </span>
                      </div>
                      <span className="slider-val-badge">{sunElevationDeg.toFixed(1)}°</span>
                    </div>
                    <input
                      type="range"
                      min="0.0"
                      max="5.0"
                      step="0.1"
                      value={sunElevationDeg}
                      onChange={e => setSunElevationDeg(Number(e.target.value))}
                      className="gold-range-slider"
                    />
                  </div>

                  {/* Crater Depth-to-Diameter Ratio Slider */}
                  <div className="lab-slider-group">
                    <div className="slider-label-row">
                      <div className="label-with-icon">
                        <Mountain size={16} className="control-icon" />
                        <span>Crater Depth-to-Diameter Ratio</span>
                        <span className="info-badge-dot" title="Ratio of crater bowl depth (d) to rim crest diameter (D)">
                          <Info size={13} />
                        </span>
                      </div>
                      <span className="slider-val-badge">{Math.round(craterDepthRatio * 100)}%</span>
                    </div>
                    <input
                      type="range"
                      min="0.10"
                      max="0.40"
                      step="0.01"
                      value={craterDepthRatio}
                      onChange={e => setCraterDepthRatio(Number(e.target.value))}
                      className="gold-range-slider"
                    />
                  </div>
                </div>

                {/* Status Indicator Card */}
                <div className="lab-status-card">
                  <div className="status-label-col">
                    <div className="status-title-row">
                      <Snowflake size={15} className="cyan-icon" />
                      <span>Illumination Status</span>
                    </div>
                    <strong className="status-val-text">
                      {sunElevationDeg <= 2.8 && craterDepthRatio >= 0.14
                        ? 'Permanently Shadowed Region (PSR)'
                        : 'Partially Illuminated Basin'}
                    </strong>
                  </div>
                  <div className="temp-val-badge">
                    {sunElevationDeg <= 2.8 && craterDepthRatio >= 0.14 ? '~ 40 K' : '~ 115 K'}
                  </div>
                </div>

                {/* Reset Simulation Button */}
                <button
                  className="reset-sim-btn"
                  onClick={() => {
                    setSunElevationDeg(1.2);
                    setCraterDepthRatio(0.20);
                  }}
                >
                  <RotateCcw size={14} />
                  <span>Reset Simulation</span>
                </button>
              </div>

              {/* Right Column: Visual Simulation Canvas */}
              <div className="crater-lab-canvas-col">
                {(() => {
                  // Geometry definitions for 720 x 320 SVG
                  const SVG_W = 720;
                  const SVG_H = 320;

                  // Crater Rim Positions
                  const XL = 175;
                  const Y_RIM = 160;
                  const XR = 595;
                  const D = XR - XL; // 420 px
                  const d_px = D * craterDepthRatio;
                  const Y_FLOOR = Y_RIM + d_px;

                  // Sun Position
                  const X_SUN = 50;
                  const Y_SUN = Y_RIM - 85 - sunElevationDeg * 16;

                  // Ray Tracing
                  // Ray 1 passes through left rim
                  const m1 = (Y_RIM - Y_SUN) / (XL - X_SUN);
                  // Ray 2 passing across
                  const Y_RAY_CENTER = Y_RIM + m1 * (385 - XL);
                  const Y_RAY_RIGHT = Y_RIM + m1 * (XR - XL);

                  // Floor shadow depth clearance
                  const isShadowed = Y_FLOOR > Y_RAY_CENTER;

                  return (
                    <svg
                      viewBox={`0 0 ${SVG_W} ${SVG_H}`}
                      className="crater-cross-section-svg"
                      preserveAspectRatio="xMidYMid meet"
                    >
                      <defs>
                        {/* Sun Radial Glow */}
                        <radialGradient id="craterSunGlow" cx="50%" cy="50%" r="50%">
                          <stop offset="0%" stopColor="#fffae0" stopOpacity="1" />
                          <stop offset="30%" stopColor="#f59e0b" stopOpacity="0.9" />
                          <stop offset="65%" stopColor="#dfa76a" stopOpacity="0.4" />
                          <stop offset="100%" stopColor="#dfa76a" stopOpacity="0" />
                        </radialGradient>

                        {/* Terrain Dark Shading */}
                        <linearGradient id="craterTerrainGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#1e2836" />
                          <stop offset="25%" stopColor="#141c26" />
                          <stop offset="70%" stopColor="#0a0f16" />
                          <stop offset="100%" stopColor="#03060a" />
                        </linearGradient>

                        {/* Sunlight Ray Beam Gradient */}
                        <linearGradient id="rayBeamGrad" x1="0" y1="0" x2="1" y2="0">
                          <stop offset="0%" stopColor="#dfa76a" stopOpacity="0.8" />
                          <stop offset="60%" stopColor="#dfa76a" stopOpacity="0.35" />
                          <stop offset="100%" stopColor="#dfa76a" stopOpacity="0.05" />
                        </linearGradient>
                      </defs>

                      {/* Deep Space Background */}
                      <rect width={SVG_W} height={SVG_H} fill="#03080e" />

                      {/* Top Right Mini-Widget: d / D ratio badge */}
                      <g transform="translate(615, 18)">
                        <rect x="0" y="0" width="88" height="42" rx="8" fill="#051019" stroke="#1e293b" />
                        {/* Crescent crater silhouette curve */}
                        <path d="M 12 24 Q 22 32, 32 24 Q 22 27, 12 24 Z" fill="#38bdf8" />
                        <text x="42" y="20" fill="#f3f1ea" fontSize="11" fontWeight="600" fontFamily="monospace">
                          d / D = {craterDepthRatio.toFixed(2)}
                        </text>
                        <text x="42" y="33" fill="#94a3b8" fontSize="10.5" fontFamily="monospace">
                          ({Math.round(craterDepthRatio * 100)}%)
                        </text>
                      </g>

                      {/* --- SUNLIGHT RAYS (RAY TRACING) --- */}
                      {/* Tangent rays emitted from Sun */}
                      <g>
                        {/* Ray 1: Grazing left rim */}
                        <line
                          x1={X_SUN}
                          y1={Y_SUN}
                          x2={XL}
                          y2={Y_RIM}
                          stroke="#dfa76a"
                          strokeWidth="1.6"
                        />
                        {/* Ray 2: Extending over crater basin */}
                        <line
                          x1={XL}
                          y1={Y_RIM}
                          x2={XR + 30}
                          y2={Y_RAY_RIGHT + 8}
                          stroke="#dfa76a"
                          strokeWidth="1.4"
                          strokeDasharray="4 3"
                        />
                        {/* Ray 3: Grazing toward right rim */}
                        <line
                          x1={X_SUN}
                          y1={Y_SUN}
                          x2={XR}
                          y2={Y_RIM}
                          stroke="#dfa76a"
                          strokeWidth="1.2"
                          strokeDasharray="4 3"
                          opacity="0.8"
                        />
                        {/* Secondary ray */}
                        <line
                          x1={X_SUN}
                          y1={Y_SUN}
                          x2={XL + 60}
                          y2={Y_RIM + 20}
                          stroke="#dfa76a"
                          strokeWidth="1"
                          strokeDasharray="4 3"
                          opacity="0.5"
                        />
                      </g>

                      {/* Sun Elevation Angle Arc & Annotation */}
                      <g>
                        {/* Horizontal reference dashed line from Sun */}
                        <line
                          x1={X_SUN}
                          y1={Y_SUN}
                          x2={X_SUN + 120}
                          y2={Y_SUN}
                          stroke="#64748b"
                          strokeWidth="1"
                          strokeDasharray="3 3"
                        />
                        {/* Arrow arc */}
                        <path
                          d={`M ${X_SUN + 60} ${Y_SUN} A 60 60 0 0 1 ${X_SUN + 58} ${Y_SUN + 15}`}
                          fill="none"
                          stroke="#dfa76a"
                          strokeWidth="1.2"
                        />
                        <text
                          x={X_SUN + 130}
                          y={Y_SUN - 4}
                          fill="#dfa76a"
                          fontSize="11.5"
                          fontWeight="600"
                          fontFamily="system-ui, -apple-system, sans-serif"
                        >
                          Sun Elevation Angle: {sunElevationDeg.toFixed(1)}°
                        </text>
                      </g>

                      {/* --- CRATER TOPOGRAPHY CROSS-SECTION --- */}
                      {/* Lunar terrain body */}
                      <path
                        d={`M 0 220 
                            L 110 210 
                            Q 145 160, ${XL} ${Y_RIM} 
                            Q 265 190, 315 ${Y_RIM + d_px * 0.75} 
                            Q 385 ${Y_FLOOR}, 455 ${Y_RIM + d_px * 0.75} 
                            Q 515 190, ${XR} ${Y_RIM} 
                            Q 630 160, 665 210 
                            L ${SVG_W} 220 
                            V ${SVG_H} H 0 Z`}
                        fill="url(#craterTerrainGrad)"
                        stroke="#334155"
                        strokeWidth="1.5"
                      />

                      {/* Illuminated Left Rim Peak & Indicator */}
                      <circle cx={XL} cy={Y_RIM} r="4.5" fill="#f59e0b" filter="drop-shadow(0 0 6px #f59e0b)" />
                      <g transform={`translate(${XL - 35}, ${Y_RIM - 36})`}>
                        <rect x="0" y="0" width="86" height="22" rx="4" fill="#051019" stroke="#dfa76a" strokeWidth="1" />
                        <text x="43" y="15" fill="#f3f1ea" fontSize="10.5" fontWeight="600" textAnchor="middle">
                          Illuminated Rim
                        </text>
                        {/* Pointer line to rim */}
                        <line x1="43" y1="22" x2="35" y2="34" stroke="#dfa76a" strokeWidth="1" />
                      </g>

                      {/* Right Rim Crest Golden Sunlight Flare */}
                      <circle cx={XR} cy={Y_RIM} r="5" fill="#fbbf24" filter="drop-shadow(0 0 10px #f59e0b)" />
                      <path
                        d={`M ${XR - 25} ${Y_RIM + 8} Q ${XR} ${Y_RIM}, ${XR + 25} ${Y_RIM + 8}`}
                        stroke="#dfa76a"
                        strokeWidth="2.5"
                        fill="none"
                        filter="drop-shadow(0 0 8px #dfa76a)"
                      />

                      {/* --- PERMANENTLY SHADOWED REGION (PSR) GLOW ON FLOOR --- */}
                      {isShadowed && (
                        <g>
                          {/* Cyan glowing outline along crater floor */}
                          <path
                            d={`M 290 ${Y_RIM + d_px * 0.65} 
                                Q 385 ${Y_FLOOR}, 480 ${Y_RIM + d_px * 0.65}`}
                            fill="none"
                            stroke="#38bdf8"
                            strokeWidth="2.5"
                            filter="drop-shadow(0 0 10px #38bdf8)"
                          />
                          {/* Center pointer dot */}
                          <circle cx="385" cy={Y_FLOOR - 4} r="4" fill="#38bdf8" filter="drop-shadow(0 0 6px #38bdf8)" />

                          {/* PSR Label Badge */}
                          <g transform="translate(330, 185)">
                            <rect x="0" y="0" width="180" height="28" rx="6" fill="#051019" stroke="#38bdf8" strokeWidth="1.2" />
                            <text x="90" y="18" fill="#38bdf8" fontSize="11" fontWeight="600" textAnchor="middle">
                              Permanently Shadowed
                            </text>
                            <text x="90" y="32" fill="#38bdf8" fontSize="10.5" fontWeight="600" textAnchor="middle">
                              Region (PSR) ~ 40 K
                            </text>
                            {/* Pointer down to dot */}
                            <line x1="55" y1="28" x2="55" y2={Y_FLOOR - 189} stroke="#38bdf8" strokeWidth="1" strokeDasharray="2 2" />
                          </g>
                        </g>
                      )}

                      {/* --- DIMENSIONAL ANNOTATIONS --- */}
                      {/* Horizontal Dimension: Crater Diameter (D) */}
                      <g transform="translate(0, 245)">
                        <line x1={XL} y1="0" x2={XR} y2="0" stroke="#64748b" strokeWidth="1.2" />
                        <line x1={XL} y1="-5" x2={XL} y2="5" stroke="#64748b" strokeWidth="1.2" />
                        <line x1={XR} y1="-5" x2={XR} y2="5" stroke="#64748b" strokeWidth="1.2" />
                        <text x="385" y="16" fill="#94a3b8" fontSize="11" textAnchor="middle" fontFamily="system-ui, sans-serif">
                          Crater Diameter (D)
                        </text>
                      </g>

                      {/* Vertical Dimension: Depth (d) */}
                      <g transform="translate(635, 0)">
                        <line x1="0" y1={Y_RIM} x2="0" y2={Y_FLOOR} stroke="#64748b" strokeWidth="1.2" />
                        <line x1="-5" y1={Y_RIM} x2="5" y2={Y_RIM} stroke="#64748b" strokeWidth="1.2" />
                        <line x1="-5" y1={Y_FLOOR} x2="5" y2={Y_FLOOR} stroke="#64748b" strokeWidth="1.2" />
                        <text x="12" y={Y_RIM + d_px * 0.5 - 2} fill="#94a3b8" fontSize="11" fontWeight="500">
                          Depth
                        </text>
                        <text x="12" y={Y_RIM + d_px * 0.5 + 11} fill="#94a3b8" fontSize="10.5" fontFamily="monospace">
                          (d)
                        </text>
                      </g>

                      {/* Glowing Sun Orb at (X_SUN, Y_SUN) */}
                      <g transform={`translate(${X_SUN}, ${Y_SUN})`}>
                        <circle cx="0" cy="0" r="30" fill="url(#craterSunGlow)" />
                        <circle cx="0" cy="0" r="13" fill="#fffae0" stroke="#f59e0b" strokeWidth="2" />
                      </g>
                    </svg>
                  );
                })()}
              </div>
            </div>

            {/* Bottom Section: Key Insights */}
            <div className="south-pole-insights-section">
              <div className="insights-header">
                <Layers size={20} className="gold-icon" />
                <h3>Key Insights</h3>
              </div>

              <div className="insights-cards-grid">
                {/* Insight Card 1 */}
                <div className="insight-card">
                  <div className="insight-icon-wrap">
                    <Sun size={24} className="gold-icon" />
                  </div>
                  <h4>Illuminated Terrain</h4>
                  <p>Elevated crater rims can receive prolonged sunlight, making them ideal for power generation.</p>
                </div>

                {/* Insight Card 2 */}
                <div className="insight-card">
                  <div className="insight-icon-wrap">
                    <Moon size={24} className="cyan-icon" />
                  </div>
                  <h4>Shadowed Terrain (PSR)</h4>
                  <p>Deep crater interiors may never receive direct sunlight, forming permanently shadowed regions.</p>
                </div>

                {/* Insight Card 3 */}
                <div className="insight-card">
                  <div className="insight-icon-wrap">
                    <Thermometer size={24} className="gold-icon" />
                  </div>
                  <h4>Temperature</h4>
                  <p>PSRs can reach extremely low temperatures of around 40 K, allowing volatile ices to remain stable.</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tab 3: Sun & Earth Motion (Mockup Match) */}
        {activeTab === 'sun-earth-motion' && (
          <div className="learn-sun-motion-view">
            {/* Top Banner Card */}
            <div className="south-pole-banner-card">
              <div className="banner-thumb-wrap">
                <img
                  src="/assets/learn-sun-earth-motion.png"
                  alt="Sun & Earth Motion Orbit"
                  className="banner-thumb-img"
                />
              </div>
              <div className="banner-content">
                <h2>Sun &amp; Earth Motion: 360° Horizontal Sweeps &amp; Optical Libration</h2>
                <p>
                  Unlike Earth where the Sun rises in the east and sets in the west, at the lunar south pole the Sun moves entirely horizontally around the horizon, taking 29.5 Earth days to complete one full 360° circle. Concurrently, Earth stays locked near a fixed azimuth but oscillates by ±6.68° in latitude and ±7.9° in longitude due to the Moon&apos;s eccentric orbit.
                </p>
              </div>
            </div>

            {/* Middle Section: Earth Optical Libration Simulator */}
            <div className="libration-lab-container">
              {/* Left Column: Controls & Telemetry */}
              <div className="libration-lab-controls-col">
                <div className="lab-controls-header">
                  <div className="lab-title-row">
                    <Telescope size={20} className="gold-icon" />
                    <h3>Earth Optical Libration Simulator</h3>
                  </div>
                  <p>Scrub the 27.3-day anomalistic month to watch Earth&apos;s libration ellipse in the lunar sky.</p>
                </div>

                <div className="lab-sliders-list">
                  {/* Libration Phase Slider */}
                  <div className="lab-slider-group">
                    <div className="slider-label-row">
                      <div className="label-with-icon">
                        <Calendar size={16} className="control-icon" />
                        <span>Libration Phase</span>
                        <span className="info-badge-dot" title="Phase of the 27.3-day anomalistic/draconic orbital cycle">
                          <Info size={13} />
                        </span>
                      </div>
                      <span className="slider-val-badge">Day {earthLibrationPhase.toFixed(1)} / 27.3</span>
                    </div>
                    <input
                      type="range"
                      min="0.0"
                      max="27.3"
                      step="0.1"
                      value={earthLibrationPhase}
                      onChange={e => setEarthLibrationPhase(Number(e.target.value))}
                      className="gold-range-slider"
                    />

                    {/* Simulation Playback Actions */}
                    <div className="libration-action-row">
                      <button
                        className="libration-action-btn"
                        onClick={() => setIsPlayingLibration(p => !p)}
                        title={isPlayingLibration ? "Pause Libration Animation" : "Play Continuous Libration Cycle"}
                      >
                        {isPlayingLibration ? <Pause size={13} /> : <Play size={13} />}
                        <span>{isPlayingLibration ? "Pause" : "Play Cycle"}</span>
                      </button>
                      <button
                        className="libration-action-btn"
                        onClick={() => {
                          setEarthLibrationPhase(14.0);
                          setIsPlayingLibration(false);
                        }}
                        title="Reset to Day 14.0 (Mean Sub-Earth Node)"
                      >
                        <RotateCcw size={13} />
                        <span>Reset (Day 14.0)</span>
                      </button>
                    </div>
                  </div>
                </div>

                {/* Libration Status & Range Card */}
                <div className="libration-status-card">
                  <div className="status-label-col">
                    <div className="status-title-row">
                      <Info size={16} className="text-[#38bdf8]" />
                      <span className="status-title-text">Libration Range</span>
                    </div>
                    <div className="libration-range-value">Lat ±6.68° × Lon ±7.9°</div>
                  </div>

                  <div className="libration-live-coords">
                    <span>Current Sky Position:</span>
                    <strong>
                      Lat {(currentLat >= 0 ? '+' : '') + currentLat.toFixed(2)}° × Lon {(currentLon >= 0 ? '+' : '') + currentLon.toFixed(2)}°
                    </strong>
                  </div>
                </div>
              </div>

              {/* Right Column: Visual Sky Cross-Section Canvas */}
              <div className="libration-lab-canvas-col" style={{ position: 'relative', minHeight: '280px' }}>
                {/* Full Photorealistic Artwork from Figma (Image 2) */}
                <img
                  src={earthLibrationPhase === 14.0 ? "/assets/learn-sun-earth-canvas.png" : "/assets/learn-sun-earth-canvas-bg.png"}
                  alt="Earth Optical Libration Simulator"
                  style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    width: '100%',
                    height: '100%',
                    objectFit: 'cover',
                    pointerEvents: 'none'
                  }}
                />

                <svg
                  viewBox="0 0 1024 512"
                  className="libration-canvas-svg"
                  preserveAspectRatio="xMidYMid meet"
                  style={{ position: 'relative', width: '100%', height: '100%', display: 'block', zIndex: 2 }}
                >
                  <defs>
                    {/* Earth Atmosphere Radial Halo Glow */}
                    <radialGradient id="earthAtmosphereGlow" cx="50%" cy="50%" r="50%">
                      <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.8" />
                      <stop offset="45%" stopColor="#0284c7" stopOpacity="0.35" />
                      <stop offset="80%" stopColor="#0369a1" stopOpacity="0.1" />
                      <stop offset="100%" stopColor="#38bdf8" stopOpacity="0" />
                    </radialGradient>
                  </defs>

                  {/* Dynamic interactive elements only when Earth moves away from rest state (Day 14.0) */}
                  {earthLibrationPhase !== 14.0 && (
                    <g>
                      {/* Connecting displacement vector from origin (512, 215) to Earth */}
                      {(Math.abs(currentLon) > 0.1 || Math.abs(currentLat) > 0.1) && (
                        <line
                          x1={librationCX}
                          y1={librationCY}
                          x2={librationEarthX}
                          y2={librationEarthY}
                          stroke="rgba(56, 189, 248, 0.6)"
                          strokeWidth="2"
                          strokeDasharray="4 4"
                        />
                      )}

                      {/* Moving Earth Orb */}
                      <g transform={`translate(${librationEarthX}, ${librationEarthY})`}>
                        {/* Atmosphere Radial Glow */}
                        <circle cx="0" cy="0" r="48" fill="url(#earthAtmosphereGlow)" />
                        <circle cx="0" cy="0" r="38" fill="none" stroke="rgba(56, 189, 248, 0.45)" strokeWidth="1.5" />

                        {/* High-res Earth Image */}
                        <image
                          href="/assets/earth-floating.png"
                          x="-32"
                          y="-32"
                          width="64"
                          height="64"
                          preserveAspectRatio="xMidYMid meet"
                        />

                        {/* Coordinates Indicator on Earth */}
                        <g transform="translate(0, -42)">
                          <rect
                            x="-65"
                            y="-18"
                            width="130"
                            height="22"
                            rx="4"
                            fill="#051019"
                            stroke="#38bdf8"
                            strokeWidth="1.2"
                            opacity="0.95"
                          />
                          <text
                            x="0"
                            y="-3"
                            fill="#38bdf8"
                            fontSize="11.5"
                            fontWeight="600"
                            textAnchor="middle"
                            fontFamily="system-ui, -apple-system, sans-serif"
                          >
                            {(currentLat >= 0 ? '+' : '') + currentLat.toFixed(1)}° / {(currentLon >= 0 ? '+' : '') + currentLon.toFixed(1)}°
                          </text>
                        </g>
                      </g>
                    </g>
                  )}
                </svg>
              </div>
            </div>

            {/* Bottom Section: Key Takeaways */}
            <div className="south-pole-insights-section">
              <div className="insights-header">
                <Layers size={18} className="gold-icon" />
                <h3>Key Takeaways</h3>
              </div>

              <div className="insights-cards-grid">
                {/* Takeaway 1: Horizontal Sun Motion */}
                <div className="insight-card">
                  <div className="insight-card-icon gold">
                    <svg
                      width="22"
                      height="22"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.85.99 6.57 2.57L21 8" />
                      <path d="M21 3v5h-5" />
                      <text x="12" y="13.5" fill="currentColor" stroke="none" fontSize="6.5" fontWeight="700" textAnchor="middle">
                        360°
                      </text>
                    </svg>
                  </div>
                  <div className="insight-card-content">
                    <h4>Horizontal Sun Motion</h4>
                    <p>At the lunar south pole, the Sun moves around the horizon, completing 360° in ~29.5 Earth days.</p>
                  </div>
                </div>

                {/* Takeaway 2: Earth's Libration */}
                <div className="insight-card">
                  <div className="insight-card-icon cyan">
                    <ArrowLeftRight size={20} />
                  </div>
                  <div className="insight-card-content">
                    <h4>Earth&apos;s Libration</h4>
                    <p>Earth appears to wobble within ±6.68° in latitude and ±7.9° in longitude, forming a small ellipse in the lunar sky.</p>
                  </div>
                </div>

                {/* Takeaway 3: Mission Relevance */}
                <div className="insight-card">
                  <div className="insight-card-icon gold">
                    <Target size={20} />
                  </div>
                  <div className="insight-card-content">
                    <h4>Mission Relevance</h4>
                    <p>This motion affects visibility, communication windows and the best timing for sustained operations.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tab 4: Power & Illumination (Mockup Match) */}
        {activeTab === 'power-illumination' && (
          <div className="learn-south-pole-view">
            {/* Top Banner Card */}
            <div className="south-pole-banner-card">
              <div className="banner-thumb-wrap">
                <img
                  src="/assets/learn-power-illumination.png"
                  alt="Solar Mast on Lunar Surface"
                  className="banner-thumb-img"
                />
              </div>
              <div className="banner-content">
                <h2>Power &amp; Illumination: Mast Height &amp; Solar Energy Availability</h2>
                <p>
                  Solar panels on a lander or rover depend heavily on elevation above ground level. A 2.0-meter mast can elevate solar cells above immediate boulder and ridge obstacles, transforming an otherwise shadowed site into one with over 120 days of continuous sunlight.
                </p>
              </div>
            </div>

            {/* Middle Section: Solar Panel Mast Sensitivity Lab */}
            <div className="crater-lab-container">
              {/* Left Column: Controls & Telemetry */}
              <div className="crater-lab-controls-col">
                <div className="lab-controls-header">
                  <div className="lab-title-row">
                    <Sun size={20} className="gold-icon" />
                    <h3>Solar Panel Mast Sensitivity Lab</h3>
                  </div>
                  <p>Adjust the mast height to see how terrain affects solar illumination and continuous sunlight.</p>
                </div>

                <div className="lab-sliders-list">
                  {/* Mast Height Slider */}
                  <div className="lab-slider-group">
                    <div className="slider-label-row">
                      <div className="label-with-icon">
                        <span>Lander Solar Mast Height</span>
                        <span className="info-badge-dot" title="Elevation of solar cells above lunar ground level atop lander mast">
                          <Info size={13} />
                        </span>
                      </div>
                      <span className="slider-val-badge">{mastHeight.toFixed(1)} m</span>
                    </div>
                    <input
                      type="range"
                      min="0.5"
                      max="4.0"
                      step="0.1"
                      value={mastHeight}
                      onChange={e => setMastHeight(Number(e.target.value))}
                      className="gold-range-slider"
                    />
                  </div>
                </div>

                {/* Status Indicator Card */}
                <div className="lab-status-card">
                  <div className="status-label-col">
                    <div className="status-title-row">
                      <Calendar size={16} className="text-[#38bdf8]" />
                      <span className="status-title-text">Continuous Sunlight (Estimated)</span>
                    </div>
                    <div className="status-value-badge" style={{
                      color: mastHeight >= 1.8 ? '#38bdf8' : mastHeight >= 1.2 ? '#dfa76a' : '#ef4444'
                    }}>
                      {mastHeight >= 1.8 ? '> 120 days' : mastHeight >= 1.2 ? '~ 72 days' : '< 25 days (Shadowed)'}
                    </div>
                  </div>
                </div>

                {/* Reset Simulation Button */}
                <button
                  className="reset-sim-btn"
                  onClick={() => setMastHeight(2.0)}
                >
                  <RotateCcw size={14} />
                  <span>Reset Simulation</span>
                </button>
              </div>

              {/* Right Column: Interactive 2D Cross-Section Canvas */}
              <div className="crater-lab-canvas-col" style={{ minHeight: '260px', position: 'relative' }}>
                {/* Background Landscape Artwork */}
                <img
                  src={mastHeight === 2.0 ? "/assets/learn-power-canvas.png" : "/assets/learn-power-canvas-bg.png"}
                  alt="Lunar Polar Mast Simulation"
                  style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    width: '100%',
                    height: '100%',
                    objectFit: 'cover',
                    pointerEvents: 'none'
                  }}
                />

                {/* Dynamic SVG Overlay for Interactive Mast and Terrain Rays */}
                <svg
                  viewBox="0 0 1024 512"
                  style={{
                    position: 'relative',
                    width: '100%',
                    height: '100%',
                    display: 'block',
                    zIndex: 2
                  }}
                  preserveAspectRatio="xMidYMid meet"
                >
                  <defs>
                    <radialGradient id="sunFlareGlow" cx="50%" cy="50%" r="50%">
                      <stop offset="0%" stopColor="#fff" stopOpacity="1" />
                      <stop offset="35%" stopColor="#f59e0b" stopOpacity="0.8" />
                      <stop offset="100%" stopColor="#f59e0b" stopOpacity="0" />
                    </radialGradient>
                  </defs>

                  {/* Render dynamic lander, mast and rays only when mastHeight is adjusted away from default 2.0 */}
                  {mastHeight !== 2.0 && (() => {
                    const landerX = 260;
                    const groundY = 405;
                    const bodyH = 65;
                    const bodyTopY = groundY - bodyH; // 340
                    // Height in pixels proportional to mastHeight (2.0m = 110px)
                    const mastPx = (mastHeight / 2.0) * 110;
                    const panelY = bodyTopY - mastPx;
                    const isIlluminated = mastHeight >= 1.8;

                    return (
                      <g>
                        {/* Golden Sunlight Rays Streaming from Sun (x=61, y=44) */}
                        <line
                          x1="61"
                          y1="44"
                          x2={landerX}
                          y2={panelY}
                          stroke={isIlluminated ? "#dfa76a" : "rgba(223, 167, 106, 0.3)"}
                          strokeWidth="2.5"
                          strokeDasharray="6 6"
                        />
                        <line
                          x1="61"
                          y1="44"
                          x2={landerX - 30}
                          y2={panelY + 8}
                          stroke={isIlluminated ? "rgba(223, 167, 106, 0.6)" : "rgba(223, 167, 106, 0.2)"}
                          strokeWidth="2"
                          strokeDasharray="5 5"
                        />
                        <line
                          x1="61"
                          y1="44"
                          x2={landerX + 30}
                          y2={panelY - 8}
                          stroke={isIlluminated ? "rgba(223, 167, 106, 0.6)" : "rgba(223, 167, 106, 0.2)"}
                          strokeWidth="2"
                          strokeDasharray="5 5"
                        />

                        {/* Lander Base on Ground */}
                        <g transform={`translate(${landerX - 42}, ${bodyTopY})`}>
                          {/* Landing legs */}
                          <line x1="10" y1="50" x2="-14" y2="65" stroke="#94a3b8" strokeWidth="4" />
                          <line x1="74" y1="50" x2="98" y2="65" stroke="#94a3b8" strokeWidth="4" />
                          {/* Main payload body with gold foil shading */}
                          <rect x="0" y="0" width="84" height="56" rx="4" fill="#d4af37" stroke="#b4941f" strokeWidth="2" />
                          <rect x="12" y="8" width="60" height="38" fill="#1e293b" rx="3" />
                        </g>

                        {/* Mast Column */}
                        <line
                          x1={landerX}
                          y1={bodyTopY}
                          x2={landerX}
                          y2={panelY}
                          stroke="#dfa76a"
                          strokeWidth="6"
                          strokeLinecap="round"
                        />

                        {/* Solar Panel Array atop mast */}
                        <g transform={`translate(${landerX}, ${panelY}) rotate(-18)`}>
                          <rect
                            x="-38"
                            y="-10"
                            width="76"
                            height="20"
                            rx="3"
                            fill={isIlluminated ? "#0284c7" : "#1e293b"}
                            stroke={isIlluminated ? "#38bdf8" : "#475569"}
                            strokeWidth="2"
                            filter={isIlluminated ? "drop-shadow(0 0 10px #38bdf8)" : undefined}
                          />
                          {/* Solar cells pattern */}
                          <line x1="-19" y1="-10" x2="-19" y2="10" stroke="rgba(255,255,255,0.4)" strokeWidth="1.5" />
                          <line x1="0" y1="-10" x2="0" y2="10" stroke="rgba(255,255,255,0.4)" strokeWidth="1.5" />
                          <line x1="19" y1="-10" x2="19" y2="10" stroke="rgba(255,255,255,0.4)" strokeWidth="1.5" />
                        </g>

                        {/* Measurement Bracket */}
                        <g transform={`translate(${landerX + 46}, 0)`}>
                          <line x1="0" y1={panelY} x2="12" y2={panelY} stroke="#38bdf8" strokeWidth="2" />
                          <line x1="6" y1={panelY} x2="6" y2={bodyTopY} stroke="#38bdf8" strokeWidth="2" />
                          <line x1="0" y1={bodyTopY} x2="12" y2={bodyTopY} stroke="#38bdf8" strokeWidth="2" />
                          <text
                            x="18"
                            y={(panelY + bodyTopY) / 2 + 6}
                            fill="#f3f1ea"
                            fontSize="17"
                            fontWeight="600"
                            fontFamily="system-ui, -apple-system, sans-serif"
                          >
                            {mastHeight.toFixed(1)} m
                          </text>
                        </g>

                        {/* Ridge Horizon Shadow Line when in shadow */}
                        {!isIlluminated && (
                          <g>
                            <line
                              x1="120"
                              y1="224"
                              x2="846"
                              y2="224"
                              stroke="#ef4444"
                              strokeWidth="2.5"
                              strokeDasharray="8 5"
                            />
                            {/* Marker dot on ridge horizon */}
                            <circle cx="846" cy="224" r="6" fill="#ef4444" />
                            <line x1="846" y1="224" x2="825" y2="185" stroke="#ef4444" strokeWidth="1.6" />
                            <g transform="translate(714, 138)">
                              <rect x="0" y="0" width="240" height="42" rx="8" fill="#051019" stroke="#ef4444" strokeWidth="1.6" />
                              <text x="120" y="27" fill="#ef4444" fontSize="16" fontWeight="600" textAnchor="middle">
                                Blocked by Ridge Horizon
                              </text>
                            </g>
                          </g>
                        )}
                      </g>
                    );
                  })()}
                </svg>              </div>
            </div>

            {/* Bottom Section: Key Insights */}
            <div className="south-pole-insights-section">
              <div className="insights-header">
                <Layers size={20} className="gold-icon" />
                <h3>Key Insights</h3>
              </div>

              <div className="insights-cards-grid">
                {/* Insight Card 1 */}
                <div className="insight-card">
                  <div className="insight-icon-wrap">
                    <Sun size={24} className="gold-icon" />
                  </div>
                  <h4>Illuminated Terrain</h4>
                  <p>Elevated crater rims can receive prolonged sunlight, making them ideal for power generation.</p>
                </div>

                {/* Insight Card 2 */}
                <div className="insight-card">
                  <div className="insight-icon-wrap">
                    <Moon size={24} className="cyan-icon" />
                  </div>
                  <h4>Shadowed Terrain (PSR)</h4>
                  <p>Deep crater interiors may never receive direct sunlight, forming permanently shadowed regions.</p>
                </div>

                {/* Insight Card 3 */}
                <div className="insight-card">
                  <div className="insight-icon-wrap">
                    <Thermometer size={24} className="gold-icon" />
                  </div>
                  <h4>Temperature</h4>
                  <p>PSRs can reach extremely low temperatures of around 40 K, allowing volatile ices to remain stable.</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tab 3: Sun & Earth Motion (Mockup Match) */}
        {activeTab === 'sun-earth-motion' && (
          <div className="learn-sun-motion-view">
            {/* Top Banner Card */}
            <div className="south-pole-banner-card">
              <div className="banner-thumb-wrap">
                <img
                  src="/assets/learn-sun-earth-motion.png"
                  alt="Sun & Earth Motion Orbit"
                  className="banner-thumb-img"
                />
              </div>
              <div className="banner-content">
                <h2>Sun &amp; Earth Motion: 360° Horizontal Sweeps &amp; Optical Libration</h2>
                <p>
                  Unlike Earth where the Sun rises in the east and sets in the west, at the lunar south pole the Sun moves entirely horizontally around the horizon, taking 29.5 Earth days to complete one full 360° circle. Concurrently, Earth stays locked near a fixed azimuth but oscillates by ±6.68° in latitude and ±7.9° in longitude due to the Moon&apos;s eccentric orbit.
                </p>
              </div>
            </div>

            {/* Middle Section: Earth Optical Libration Simulator */}
            <div className="libration-lab-container">
              {/* Left Column: Controls & Telemetry */}
              <div className="libration-lab-controls-col">
                <div className="lab-controls-header">
                  <div className="lab-title-row">
                    <Telescope size={20} className="gold-icon" />
                    <h3>Earth Optical Libration Simulator</h3>
                  </div>
                  <p>Scrub the 27.3-day anomalistic month to watch Earth&apos;s libration ellipse in the lunar sky.</p>
                </div>

                <div className="lab-sliders-list">
                  {/* Libration Phase Slider */}
                  <div className="lab-slider-group">
                    <div className="slider-label-row">
                      <div className="label-with-icon">
                        <Calendar size={16} className="control-icon" />
                        <span>Libration Phase</span>
                        <span className="info-badge-dot" title="Phase of the 27.3-day anomalistic/draconic orbital cycle">
                          <Info size={13} />
                        </span>
                      </div>
                      <span className="slider-val-badge">Day {earthLibrationPhase.toFixed(1)} / 27.3</span>
                    </div>
                    <input
                      type="range"
                      min="0.0"
                      max="27.3"
                      step="0.1"
                      value={earthLibrationPhase}
                      onChange={e => setEarthLibrationPhase(Number(e.target.value))}
                      className="gold-range-slider"
                    />

                    {/* Simulation Playback Actions */}
                    <div className="libration-action-row">
                      <button
                        className="libration-action-btn"
                        onClick={() => setIsPlayingLibration(p => !p)}
                        title={isPlayingLibration ? "Pause Libration Animation" : "Play Continuous Libration Cycle"}
                      >
                        {isPlayingLibration ? <Pause size={13} /> : <Play size={13} />}
                        <span>{isPlayingLibration ? "Pause" : "Play Cycle"}</span>
                      </button>
                      <button
                        className="libration-action-btn"
                        onClick={() => {
                          setEarthLibrationPhase(14.0);
                          setIsPlayingLibration(false);
                        }}
                        title="Reset to Day 14.0 (Mean Sub-Earth Node)"
                      >
                        <RotateCcw size={13} />
                        <span>Reset (Day 14.0)</span>
                      </button>
                    </div>
                  </div>
                </div>

                {/* Libration Status & Range Card */}
                <div className="libration-status-card">
                  <div className="status-label-col">
                    <div className="status-title-row">
                      <Info size={16} className="text-[#38bdf8]" />
                      <span className="status-title-text">Libration Range</span>
                    </div>
                    <div className="libration-range-value">Lat ±6.68° × Lon ±7.9°</div>
                  </div>

                  <div className="libration-live-coords">
                    <span>Current Sky Position:</span>
                    <strong>
                      Lat {(currentLat >= 0 ? '+' : '') + currentLat.toFixed(2)}° × Lon {(currentLon >= 0 ? '+' : '') + currentLon.toFixed(2)}°
                    </strong>
                  </div>
                </div>
              </div>

              {/* Right Column: Visual Sky Cross-Section Canvas */}
              <div className="libration-lab-canvas-col" style={{ position: 'relative', minHeight: '280px' }}>
                {/* Full Photorealistic Artwork from Figma (Image 2) */}
                <img
                  src={earthLibrationPhase === 14.0 ? "/assets/learn-sun-earth-canvas.png" : "/assets/learn-sun-earth-canvas-bg.png"}
                  alt="Earth Optical Libration Simulator"
                  style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    width: '100%',
                    height: '100%',
                    objectFit: 'cover',
                    pointerEvents: 'none'
                  }}
                />

                <svg
                  viewBox="0 0 1024 512"
                  className="libration-canvas-svg"
                  preserveAspectRatio="xMidYMid meet"
                  style={{ position: 'relative', width: '100%', height: '100%', display: 'block', zIndex: 2 }}
                >
                  <defs>
                    {/* Earth Atmosphere Radial Halo Glow */}
                    <radialGradient id="earthAtmosphereGlow" cx="50%" cy="50%" r="50%">
                      <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.8" />
                      <stop offset="45%" stopColor="#0284c7" stopOpacity="0.35" />
                      <stop offset="80%" stopColor="#0369a1" stopOpacity="0.1" />
                      <stop offset="100%" stopColor="#38bdf8" stopOpacity="0" />
                    </radialGradient>
                  </defs>

                  {/* Dynamic interactive elements only when Earth moves away from rest state (Day 14.0) */}
                  {earthLibrationPhase !== 14.0 && (
                    <g>
                      {/* Connecting displacement vector from origin (512, 215) to Earth */}
                      {(Math.abs(currentLon) > 0.1 || Math.abs(currentLat) > 0.1) && (
                        <line
                          x1={librationCX}
                          y1={librationCY}
                          x2={librationEarthX}
                          y2={librationEarthY}
                          stroke="rgba(56, 189, 248, 0.6)"
                          strokeWidth="2"
                          strokeDasharray="4 4"
                        />
                      )}

                      {/* Moving Earth Orb */}
                      <g transform={`translate(${librationEarthX}, ${librationEarthY})`}>
                        {/* Atmosphere Radial Glow */}
                        <circle cx="0" cy="0" r="48" fill="url(#earthAtmosphereGlow)" />
                        <circle cx="0" cy="0" r="38" fill="none" stroke="rgba(56, 189, 248, 0.45)" strokeWidth="1.5" />

                        {/* High-res Earth Image */}
                        <image
                          href="/assets/earth-floating.png"
                          x="-32"
                          y="-32"
                          width="64"
                          height="64"
                          preserveAspectRatio="xMidYMid meet"
                        />

                        {/* Coordinates Indicator on Earth */}
                        <g transform="translate(0, -42)">
                          <rect
                            x="-65"
                            y="-18"
                            width="130"
                            height="22"
                            rx="4"
                            fill="#051019"
                            stroke="#38bdf8"
                            strokeWidth="1.2"
                            opacity="0.95"
                          />
                          <text
                            x="0"
                            y="-3"
                            fill="#38bdf8"
                            fontSize="11.5"
                            fontWeight="600"
                            textAnchor="middle"
                            fontFamily="system-ui, -apple-system, sans-serif"
                          >
                            {(currentLat >= 0 ? '+' : '') + currentLat.toFixed(1)}° / {(currentLon >= 0 ? '+' : '') + currentLon.toFixed(1)}°
                          </text>
                        </g>
                      </g>
                    </g>
                  )}
                </svg>
              </div>
            </div>

            {/* Bottom Section: Key Takeaways */}
            <div className="south-pole-insights-section">
              <div className="insights-header">
                <Layers size={18} className="gold-icon" />
                <h3>Key Takeaways</h3>
              </div>

              <div className="insights-cards-grid">
                {/* Takeaway 1: Horizontal Sun Motion */}
                <div className="insight-card">
                  <div className="insight-card-icon gold">
                    <svg
                      width="22"
                      height="22"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.85.99 6.57 2.57L21 8" />
                      <path d="M21 3v5h-5" />
                      <text x="12" y="13.5" fill="currentColor" stroke="none" fontSize="6.5" fontWeight="700" textAnchor="middle">
                        360°
                      </text>
                    </svg>
                  </div>
                  <div className="insight-card-content">
                    <h4>Horizontal Sun Motion</h4>
                    <p>At the lunar south pole, the Sun moves around the horizon, completing 360° in ~29.5 Earth days.</p>
                  </div>
                </div>

                {/* Takeaway 2: Earth's Libration */}
                <div className="insight-card">
                  <div className="insight-card-icon cyan">
                    <ArrowLeftRight size={20} />
                  </div>
                  <div className="insight-card-content">
                    <h4>Earth&apos;s Libration</h4>
                    <p>Earth appears to wobble within ±6.68° in latitude and ±7.9° in longitude, forming a small ellipse in the lunar sky.</p>
                  </div>
                </div>

                {/* Takeaway 3: Mission Relevance */}
                <div className="insight-card">
                  <div className="insight-card-icon gold">
                    <Target size={20} />
                  </div>
                  <div className="insight-card-content">
                    <h4>Mission Relevance</h4>
                    <p>This motion affects visibility, communication windows and the best timing for sustained operations.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tab 4: Power & Illumination (Mockup Match) */}
        {activeTab === 'power-illumination' && (
          <div className="learn-south-pole-view">
            {/* Top Banner Card */}
            <div className="south-pole-banner-card">
              <div className="banner-thumb-wrap">
                <img
                  src="/assets/learn-power-illumination.png"
                  alt="Solar Mast on Lunar Surface"
                  className="banner-thumb-img"
                />
              </div>
              <div className="banner-content">
                <h2>Power &amp; Illumination: Mast Height &amp; Solar Energy Availability</h2>
                <p>
                  Solar panels on a lander or rover depend heavily on elevation above ground level. A 2.0-meter mast can elevate solar cells above immediate boulder and ridge obstacles, transforming an otherwise shadowed site into one with over 120 days of continuous sunlight.
                </p>
              </div>
            </div>

            {/* Middle Section: Solar Panel Mast Sensitivity Lab */}
            <div className="crater-lab-container">
              {/* Left Column: Controls & Telemetry */}
              <div className="crater-lab-controls-col">
                <div className="lab-controls-header">
                  <div className="lab-title-row">
                    <Sun size={20} className="gold-icon" />
                    <h3>Solar Panel Mast Sensitivity Lab</h3>
                  </div>
                  <p>Adjust the mast height to see how terrain affects solar illumination and continuous sunlight.</p>
                </div>

                <div className="lab-sliders-list">
                  {/* Mast Height Slider */}
                  <div className="lab-slider-group">
                    <div className="slider-label-row">
                      <div className="label-with-icon">
                        <span>Lander Solar Mast Height</span>
                        <span className="info-badge-dot" title="Elevation of solar cells above lunar ground level atop lander mast">
                          <Info size={13} />
                        </span>
                      </div>
                      <span className="slider-val-badge">{mastHeight.toFixed(1)} m</span>
                    </div>
                    <input
                      type="range"
                      min="0.5"
                      max="4.0"
                      step="0.1"
                      value={mastHeight}
                      onChange={e => setMastHeight(Number(e.target.value))}
                      className="gold-range-slider"
                    />
                  </div>
                </div>

                {/* Status Indicator Card */}
                <div className="lab-status-card">
                  <div className="status-label-col">
                    <div className="status-title-row">
                      <Calendar size={16} className="text-[#38bdf8]" />
                      <span className="status-title-text">Continuous Sunlight (Estimated)</span>
                    </div>
                    <div className="status-value-badge" style={{
                      color: mastHeight >= 1.8 ? '#38bdf8' : mastHeight >= 1.2 ? '#dfa76a' : '#ef4444'
                    }}>
                      {mastHeight >= 1.8 ? '> 120 days' : mastHeight >= 1.2 ? '~ 72 days' : '< 25 days (Shadowed)'}
                    </div>
                  </div>
                </div>

                {/* Reset Simulation Button */}
                <button
                  className="reset-sim-btn"
                  onClick={() => setMastHeight(2.0)}
                >
                  <RotateCcw size={14} />
                  <span>Reset Simulation</span>
                </button>
              </div>

              {/* Right Column: Interactive 2D Cross-Section Canvas */}
              <div className="crater-lab-canvas-col" style={{ minHeight: '260px', position: 'relative' }}>
                {/* Background Landscape Artwork */}
                <img
                  src={mastHeight === 2.0 ? "/assets/learn-power-canvas.png" : "/assets/learn-power-canvas-bg.png"}
                  alt="Lunar Polar Mast Simulation"
                  style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    width: '100%',
                    height: '100%',
                    objectFit: 'cover',
                    pointerEvents: 'none'
                  }}
                />

                {/* Dynamic SVG Overlay for Interactive Mast and Terrain Rays */}
                <svg
                  viewBox="0 0 755 323"
                  style={{
                    position: 'relative',
                    width: '100%',
                    height: '100%',
                    display: 'block',
                    zIndex: 2
                  }}
                  preserveAspectRatio="xMidYMid meet"
                >
                  <defs>
                    <radialGradient id="sunFlareGlow" cx="50%" cy="50%" r="50%">
                      <stop offset="0%" stopColor="#fff" stopOpacity="1" />
                      <stop offset="35%" stopColor="#f59e0b" stopOpacity="0.8" />
                      <stop offset="100%" stopColor="#f59e0b" stopOpacity="0" />
                    </radialGradient>
                  </defs>

                  {/* Render dynamic lander, mast and rays only when mastHeight is adjusted away from default 2.0 */}
                  {mastHeight !== 2.0 && (() => {
                    const landerX = 198;
                    const groundY = 248;
                    const bodyH = 36;
                    const bodyTopY = groundY - bodyH; // 212
                    // Height in pixels proportional to mastHeight (2.0m = 55px)
                    const mastPx = (mastHeight / 2.0) * 55;
                    const panelY = bodyTopY - mastPx;
                    const isIlluminated = mastHeight >= 1.8;

                    return (
                      <g>
                        {/* Golden Sunlight Rays Streaming from Sun (x=38, y=36) */}
                        <line
                          x1="38"
                          y1="36"
                          x2={landerX}
                          y2={panelY}
                          stroke={isIlluminated ? "#dfa76a" : "rgba(223, 167, 106, 0.3)"}
                          strokeWidth="2"
                          strokeDasharray="5 5"
                        />
                        <line
                          x1="38"
                          y1="36"
                          x2={landerX - 22}
                          y2={panelY + 6}
                          stroke={isIlluminated ? "rgba(223, 167, 106, 0.6)" : "rgba(223, 167, 106, 0.2)"}
                          strokeWidth="1.5"
                          strokeDasharray="4 4"
                        />
                        <line
                          x1="38"
                          y1="36"
                          x2={landerX + 22}
                          y2={panelY - 6}
                          stroke={isIlluminated ? "rgba(223, 167, 106, 0.6)" : "rgba(223, 167, 106, 0.2)"}
                          strokeWidth="1.5"
                          strokeDasharray="4 4"
                        />

                        {/* Lander Base on Ground */}
                        <g transform={`translate(${landerX - 26}, ${bodyTopY})`}>
                          {/* Landing legs */}
                          <line x1="6" y1="28" x2="-8" y2="36" stroke="#94a3b8" strokeWidth="2.5" />
                          <line x1="46" y1="28" x2="60" y2="36" stroke="#94a3b8" strokeWidth="2.5" />
                          {/* Main payload body with gold foil shading */}
                          <rect x="0" y="0" width="52" height="34" rx="3" fill="#d4af37" stroke="#b4941f" strokeWidth="1.2" />
                          <rect x="8" y="6" width="36" height="22" fill="#1e293b" rx="2" />
                        </g>

                        {/* Mast Column */}
                        <line
                          x1={landerX}
                          y1={bodyTopY}
                          x2={landerX}
                          y2={panelY}
                          stroke="#dfa76a"
                          strokeWidth="4"
                          strokeLinecap="round"
                        />

                        {/* Solar Panel Array atop mast */}
                        <g transform={`translate(${landerX}, ${panelY}) rotate(-18)`}>
                          <rect
                            x="-24"
                            y="-6"
                            width="48"
                            height="12"
                            rx="2"
                            fill={isIlluminated ? "#0284c7" : "#1e293b"}
                            stroke={isIlluminated ? "#38bdf8" : "#475569"}
                            strokeWidth="1.5"
                            filter={isIlluminated ? "drop-shadow(0 0 8px #38bdf8)" : undefined}
                          />
                          {/* Solar cells pattern */}
                          <line x1="-12" y1="-6" x2="-12" y2="6" stroke="rgba(255,255,255,0.4)" strokeWidth="1" />
                          <line x1="0" y1="-6" x2="0" y2="6" stroke="rgba(255,255,255,0.4)" strokeWidth="1" />
                          <line x1="12" y1="-6" x2="12" y2="6" stroke="rgba(255,255,255,0.4)" strokeWidth="1" />
                        </g>

                        {/* Measurement Bracket */}
                        <g transform={`translate(${landerX + 26}, 0)`}>
                          <line x1="0" y1={panelY} x2="8" y2={panelY} stroke="#38bdf8" strokeWidth="1.5" />
                          <line x1="4" y1={panelY} x2="4" y2={bodyTopY} stroke="#38bdf8" strokeWidth="1.5" />
                          <line x1="0" y1={bodyTopY} x2="8" y2={bodyTopY} stroke="#38bdf8" strokeWidth="1.5" />
                          <text
                            x="14"
                            y={(panelY + bodyTopY) / 2 + 5}
                            fill="#f3f1ea"
                            fontSize="13"
                            fontWeight="600"
                            fontFamily="system-ui, -apple-system, sans-serif"
                          >
                            {mastHeight.toFixed(1)} m
                          </text>
                        </g>

                        {/* Ridge Horizon Shadow Line when in shadow */}
                        {!isIlluminated && (
                          <g>
                            <line
                              x1="90"
                              y1="168"
                              x2="610"
                              y2="168"
                              stroke="#ef4444"
                              strokeWidth="2"
                              strokeDasharray="6 4"
                            />
                            {/* Marker dot on ridge horizon */}
                            <circle cx="610" cy="168" r="4.5" fill="#ef4444" />
                            <line x1="610" y1="168" x2="590" y2="135" stroke="#ef4444" strokeWidth="1.2" />
                            <g transform="translate(510, 95)">
                              <rect x="0" y="0" width="168" height="28" rx="6" fill="#051019" stroke="#ef4444" strokeWidth="1.2" />
                              <text x="84" y="19" fill="#ef4444" fontSize="12" fontWeight="600" textAnchor="middle">
                                Blocked by Ridge Horizon
                              </text>
                            </g>
                          </g>
                        )}
                      </g>
                    );
                  })()}
                </svg>
              </div>
            </div>

            {/* Bottom Section: Key Insights */}
            <div className="south-pole-insights-section">
              <div className="insights-header">
                <Layers size={18} className="gold-icon" />
                <h3>Key Insights</h3>
              </div>

              <div className="insights-cards-grid">
                {/* Insight 1: Elevation Matters */}
                <div className="insight-card">
                  <div className="insight-card-icon gold">
                    <Sun size={20} />
                  </div>
                  <div className="insight-card-content">
                    <h4>Elevation Matters</h4>
                    <p>Raising the solar panel above local obstacles can significantly increase sunlight availability.</p>
                  </div>
                </div>

                {/* Insight 2: Illumination Windows */}
                <div className="insight-card">
                  <div className="insight-card-icon cyan">
                    <Calendar size={20} />
                  </div>
                  <div className="insight-card-content">
                    <h4>Illumination Windows</h4>
                    <p>At favorable sites, elevated masts can enable over 120 days of continuous sunlight.</p>
                  </div>
                </div>

                {/* Insight 3: Terrain Influence */}
                <div className="insight-card">
                  <div className="insight-card-icon gold">
                    <Mountain size={20} />
                  </div>
                  <div className="insight-card-content">
                    <h4>Terrain Influence</h4>
                    <p>Ridges and boulders create shadow zones that can block sunlight, even at high-sun conditions.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tab 5: Communication (DTE) (Mockup Match) */}
        {activeTab === 'communication' && (
          <div className="learn-south-pole-view">
            {/* Top Banner Card: Direct-to-Earth Geometric Links */}
            <div className="dte-hero-banner-card">
              <div className="dte-hero-text-col">
                <div className="dte-hero-title-row">
                  <Radio size={22} className="gold-icon" />
                  <h2>Communication (DTE): Direct-to-Earth Geometric Links</h2>
                </div>
                <div className="dte-hero-desc-wrap">
                  <div className="dte-hero-gold-bar" />
                  <p>
                    Direct-to-Earth (DTE) radio links require uninterrupted line of sight from the lunar landing site to Earth. Signals are received by NASA&apos;s Deep Space Network (DSN) complexes in Goldstone (California), Madrid (Spain) and Canberra (Australia), at different longitudes. Earth rotation changes which station can see a target; schedules and link budgets still need separate verification.
                  </p>
                </div>
              </div>
              <div className="dte-hero-canvas-col">
                <img
                  src="/assets/learn-dte-link-canvas.png"
                  alt="Direct-to-Earth Geometric Links"
                />
              </div>
            </div>

            {/* Middle Section: NASA Deep Space Network (DSN) Ground Station Tracking */}
            <div className="dsn-tracking-section">
              <div className="dsn-tracking-header">
                <div className="dsn-tracking-title-row">
                  <Radio size={20} className="gold-icon" />
                  <h3>NASA Deep Space Network (DSN) Ground Station Tracking</h3>
                </div>
                <p>Ground stations support deep-space communication. Live tracking status and availability are not connected in LunaScope.</p>
              </div>

              <div className="dsn-stations-grid">
                {/* Station 1: Goldstone Complex */}
                <div className="dsn-card">
                  <div className="dsn-thumb-wrap">
                    <img
                      src="/assets/dsn-goldstone.jpg"
                      alt="Goldstone Complex Antenna"
                    />
                  </div>
                  <div className="dsn-info">
                    <h4>Goldstone Complex</h4>
                    <span className="dsn-loc">
                      <MapPin size={13} className="text-[#94a3b8]" />
                      Mojave Desert, USA (35.4° N)
                    </span>
                    <span className="dsn-status online">
                      <span className="status-dot green" />
                      Status not connected
                    </span>
                  </div>
                </div>

                {/* Station 2: Madrid Complex */}
                <div className="dsn-card">
                  <div className="dsn-thumb-wrap">
                    <img
                      src="/assets/dsn-madrid.jpg"
                      alt="Madrid Complex Antenna"
                    />
                  </div>
                  <div className="dsn-info">
                    <h4>Madrid Complex</h4>
                    <span className="dsn-loc">
                      <MapPin size={13} className="text-[#94a3b8]" />
                      Robledo de Chavela, Spain (40.4° N)
                    </span>
                    <span className="dsn-status standby">
                      <span className="status-dot amber" />
                      Status not connected
                    </span>
                  </div>
                </div>

                {/* Station 3: Canberra Complex */}
                <div className="dsn-card">
                  <div className="dsn-thumb-wrap">
                    <img
                      src="/assets/dsn-canberra.jpg"
                      alt="Canberra Complex Antenna"
                    />
                  </div>
                  <div className="dsn-info">
                    <h4>Canberra Complex</h4>
                    <span className="dsn-loc">
                      <MapPin size={13} className="text-[#94a3b8]" />
                      Tidbinbilla, Australia (35.4° S)
                    </span>
                    <span className="dsn-status online">
                      <span className="status-dot green" />
                      Status not connected
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Bottom Section: Key Takeaways */}
            <div className="south-pole-insights-section">
              <div className="insights-header">
                <Layers size={18} className="gold-icon" />
                <h3>Key Takeaways</h3>
              </div>

              <div className="insights-cards-grid">
                {/* Takeaway 1: Line of Sight */}
                <div className="insight-card">
                  <div className="insight-card-icon gold">
                    <Radio size={20} />
                  </div>
                  <div className="insight-card-content">
                    <h4>Line of Sight</h4>
                    <p>A clear, uninterrupted view between the lunar lander and Earth is essential.</p>
                  </div>
                </div>

                {/* Takeaway 2: Continuous Coverage */}
                <div className="insight-card">
                  <div className="insight-card-icon gold">
                    <Clock size={20} />
                  </div>
                  <div className="insight-card-content">
                    <h4>Continuous Coverage</h4>
                    <p>Earth rotation changes station visibility. Geometric line of sight does not guarantee antenna availability or an operational link.</p>
                  </div>
                </div>

                {/* Takeaway 3: Mission Impact */}
                <div className="insight-card">
                  <div className="insight-card-icon gold">
                    <Compass size={20} />
                  </div>
                  <div className="insight-card-content">
                    <h4>Mission Impact</h4>
                    <p>Reliable DTE links enable real-time data, operations and mission safety.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tab 6: Mission Challenges (Mockup Match) */}
        {activeTab === 'mission-challenges' && (
          <div className="learn-south-pole-view">
            {/* Top Banner Card */}
            <div className="challenges-banner-card">
              <div className="challenges-thumb-wrap">
                <img
                  src="/assets/learn-challenges-banner.png"
                  alt="Lunar Polar Lander Mission Challenges"
                  className="banner-thumb-img"
                />
              </div>
              <div className="banner-gold-bar" />
              <div className="banner-content">
                <h2>Mission Challenges: Surviving the Harsh Lunar Polar Environment</h2>
                <p>
                  Operating at the Moon&apos;s south pole is unlike anywhere on Earth. Extreme cold, steep and rugged terrain, and the abrasive lunar dust all pose significant challenges to spacecraft, instruments and long-duration missions.
                </p>
              </div>
            </div>

            {/* Middle Section: 3 Deep-Dive Challenge Cards Grid */}
            <div className="challenges-cards-grid">
              {/* Challenge 1: Extreme Cryogenic Temperatures */}
              <div className="mission-challenge-card">
                <div className="challenge-photo-wrap">
                  <img
                    src="/assets/learn-challenge-cold.png"
                    alt="Extreme Cryogenic Temperatures in PSR"
                    className="challenge-photo-img"
                  />
                </div>
                <div className="challenge-card-body">
                  <h4>Extreme Cryogenic Temperatures</h4>
                  <p>
                    PSRs drop to around 40 K (-233°C). Electronics and lubricants can freeze, requiring Radioisotope Heater Units (RHUs) or specialized survival heating.
                  </p>
                </div>
                <div className="challenge-metric-badge">
                  <Snowflake size={18} className="text-[#38bdf8]" />
                  <div className="challenge-metric-content">
                    <span className="challenge-metric-label">Minimum Temperature</span>
                    <span className="challenge-metric-value cyan">~ 40 K (-233°C)</span>
                  </div>
                </div>
              </div>

              {/* Challenge 2: Steep Crater Slopes */}
              <div className="mission-challenge-card">
                <div className="challenge-photo-wrap">
                  <img
                    src="/assets/learn-challenge-slope.png"
                    alt="Steep Lunar Crater Wall Incline"
                    className="challenge-photo-img"
                  />
                </div>
                <div className="challenge-card-body">
                  <h4>Steep Crater Slopes</h4>
                  <p>
                    Crater walls often exceed 25° to 35° incline, creating severe slippage risks for autonomous wheeled rovers and lander touchdown gear.
                  </p>
                </div>
                <div className="challenge-metric-badge">
                  <Mountain size={18} className="text-[#38bdf8]" />
                  <div className="challenge-metric-content">
                    <span className="challenge-metric-label">Typical Slope Range</span>
                    <span className="challenge-metric-value gold">25° – 35°</span>
                  </div>
                </div>
              </div>

              {/* Challenge 3: Abrasive Electrostatic Regolith */}
              <div className="mission-challenge-card">
                <div className="challenge-photo-wrap">
                  <img
                    src="/assets/learn-challenge-dust.png"
                    alt="Abrasive Lunar Regolith Dust"
                    className="challenge-photo-img"
                  />
                </div>
                <div className="challenge-card-body">
                  <h4>Abrasive Electrostatic Regolith</h4>
                  <p>
                    Lunar dust is razor-sharp due to lack of atmospheric weathering and carries an electrostatic charge, adhering tenaciously to solar panels and optical radiators.
                  </p>
                </div>
                <div className="challenge-metric-badge">
                  <Sun size={18} className="text-[#38bdf8]" />
                  <div className="challenge-metric-content">
                    <span className="challenge-metric-label">Particle Size (Regolith)</span>
                    <span className="challenge-metric-value gold">~ 10 – 100 µm</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Bottom Section: Key Takeaways */}
            <div className="south-pole-insights-section">
              <div className="insights-header">
                <Layers size={18} className="gold-icon" />
                <h3>Key Takeaways</h3>
              </div>

              <div className="insights-cards-grid">
                {/* Takeaway 1: Cold & Dark */}
                <div className="insight-card">
                  <div className="insight-card-icon gold">
                    <Thermometer size={20} />
                  </div>
                  <div className="insight-card-content">
                    <h4>Cold &amp; Dark</h4>
                    <p>Temperatures can fall to ~40 K in permanently shadowed regions.</p>
                  </div>
                </div>

                {/* Takeaway 2: Rugged Terrain */}
                <div className="insight-card">
                  <div className="insight-card-icon gold">
                    <Mountain size={20} />
                  </div>
                  <div className="insight-card-content">
                    <h4>Rugged Terrain</h4>
                    <p>Slopes up to 35° demand careful site selection.</p>
                  </div>
                </div>

                {/* Takeaway 3: Dust Hazard */}
                <div className="insight-card">
                  <div className="insight-card-icon gold">
                    <Sun size={20} />
                  </div>
                  <div className="insight-card-content">
                    <h4>Dust Hazard</h4>
                    <p>Abrasive, electrostatically charged dust affects mobility, power and optics.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tab 7: Key Terms (Mockup Match) */}
        {activeTab === 'key-terms' && (() => {
          const GLOSSARY_CATEGORIES = ['All Terms', 'Orbital Motion', 'Lunar Environment', 'Missions', 'Communication'];
          const GLOSSARY_TERMS = [
            {
              id: 'optical-libration',
              title: 'Optical Libration',
              category: 'Orbital Motion',
              tagColor: 'blue',
              thumb: '/assets/glossary-optical-libration.png',
              description:
                'Apparent nodding and wobbling of the Moon caused by its orbital eccentricity and axial inclination, causing Earth to shift by ±6.68° (latitude) and ±7.9° (longitude) in the lunar sky.'
            },
            {
              id: 'psr',
              title: 'Permanently Shadowed Region (PSR)',
              category: 'Lunar Environment',
              tagColor: 'teal',
              thumb: '/assets/glossary-psr.png',
              description:
                'Topographical depressions near lunar poles where the rim permanently blocks direct sunlight, allowing water ice and volatiles to remain stable over billions of years.'
            },
            {
              id: 'topocentric-frame',
              title: 'Topocentric Frame',
              category: 'Reference Systems',
              tagColor: 'purple',
              thumb: '/assets/glossary-topocentric.png',
              description:
                'A local coordinate frame centered directly on the observer\'s surface position on the Moon, defining azimuth (0° to 360°) and elevation above local terrain.'
            },
            {
              id: 'dte',
              title: 'Direct-to-Earth (DTE)',
              category: 'Communication',
              tagColor: 'gold',
              thumb: '/assets/glossary-dte.png',
              description:
                'Direct microwave radio frequency communications from the lunar surface to Earth\'s Deep Space Network without requiring orbital relay satellites.'
            }
          ];

          const filteredTerms = GLOSSARY_TERMS.filter(term => {
            const matchesCategory =
              glossaryCategory === 'All Terms' ||
              term.category.toLowerCase() === glossaryCategory.toLowerCase() ||
              (glossaryCategory === 'Missions' && term.category === 'Reference Systems');
            const matchesSearch =
              term.title.toLowerCase().includes(glossarySearch.toLowerCase()) ||
              term.description.toLowerCase().includes(glossarySearch.toLowerCase()) ||
              term.category.toLowerCase().includes(glossarySearch.toLowerCase());
            return matchesCategory && matchesSearch;
          });

          return (
            <div className="learn-south-pole-view">
              {/* Top Banner Card */}
              <div className="south-pole-banner-card">
                <div className="banner-thumb-wrap">
                  <img
                    src="/assets/learn-glossary-banner.png"
                    alt="Key Terms & Lunar Science Glossary"
                    className="banner-thumb-img"
                  />
                </div>
                <div className="banner-content">
                  <h2>Key Terms &amp; Lunar Science Glossary</h2>
                  <p>
                    A concise guide to the essential terms, concepts and measurements used in lunar mission planning and analysis.
                  </p>
                </div>
              </div>

              {/* Search and Category Filter Bar */}
              <div className="glossary-filter-bar">
                <div className="glossary-search-wrap">
                  <Search size={15} className="glossary-search-icon" />
                  <input
                    type="text"
                    placeholder="Search a term..."
                    value={glossarySearch}
                    onChange={e => setGlossarySearch(e.target.value)}
                    className="glossary-search-input"
                  />
                </div>

                <div className="glossary-pills-row">
                  {GLOSSARY_CATEGORIES.map(cat => {
                    const isActive = glossaryCategory === cat;
                    return (
                      <button
                        key={cat}
                        className={`glossary-pill-btn ${isActive ? 'active' : ''}`}
                        onClick={() => setGlossaryCategory(cat)}
                      >
                        {cat}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Key Terms 2-Column Grid */}
              <div className="glossary-cards-grid">
                {filteredTerms.map(term => (
                  <article key={term.id} className="glossary-term-card">
                    <div className="term-thumb-wrap">
                      <img
                        src={term.thumb}
                        alt={term.title}
                        className="term-thumb-img"
                      />
                    </div>
                    <div className="term-content-col">
                      <h3 className="term-title">{term.title}</h3>
                      <div className="term-tag-wrap">
                        <span className={`term-tag-badge ${term.tagColor}`}>
                          {term.category}
                        </span>
                      </div>
                      <p className="term-desc">{term.description}</p>
                    </div>
                  </article>
                ))}
              </div>
            </div>
          );
        })()}
              </div>
    </div>
  );
};
