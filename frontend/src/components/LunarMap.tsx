import React, { useState } from 'react';
import { Plus, Minus, RotateCcw } from 'lucide-react';
import { MissionState } from '../mission';
import { LandingSite } from '../types';

interface LunarMapProps {
  state: MissionState;
}

export function LunarMap({ state }: LunarMapProps) {
  const [zoom, setZoom] = useState(2);
  const [hoveredSite, setHoveredSite] = useState<LandingSite | null>(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });

  const cx = 270;
  const cy = 240;
  const mapRadius = 175;

  // Same south-polar projection and 608 km footprint as the official hillshade.
  const project=(lat:number,lon:number)=>{const r=2*Math.tan(Math.PI/4+lat*Math.PI/360)*1737400;const scale=mapRadius*2*zoom/608000;return {x:cx+r*Math.sin(lon*Math.PI/180)*scale,y:cy-r*Math.cos(lon*Math.PI/180)*scale};};
  const getSunDays=(s:LandingSite)=>{const r=state.rank(s.site_id);return r?(r.metrics.longest_sun_window_hours/24).toFixed(2):'Pending';};
  const getJointDays=(s:LandingSite)=>{const r=state.rank(s.site_id);return r?(r.metrics.joint_availability_pct/100*state.mission.days).toFixed(2):'Pending';};
  const craters = [
    { name: 'SHACKLETON', lat: -89.67, lon: 129.78 },
    { name: 'DE GERLACHE', lat: -88.5, lon: 271.0 },
    { name: 'HAWORTH', lat: -87.4, lon: 354.5 },
    { name: 'SHOEMAKER', lat: -88.1, lon: 45.0 },
    { name: 'FAUSTINI', lat: -87.1, lon: 84.3 },
    { name: 'NOBILE', lat: -85.2, lon: 35.8 },
  ];

  return (
    <div className="circular-polar-map-container" style={{ position: 'relative', width: '100%', height: '100%', minHeight: '380px' }}>
      {/* Top Right Legend */}
      <div className="map-legend-overlay">
        <div className="legend-row">
          <svg width="14" height="17" viewBox="0 0 24 24" fill="#dfa76a">
            <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" />
          </svg>
          <span>Selected Site (Primary)</span>
        </div>
        <div className="legend-row">
          <svg width="14" height="17" viewBox="0 0 24 24" fill="#63c9c0">
            <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" />
          </svg>
          <span>Candidate Site</span>
        </div>
        <div className="legend-row">
          <svg width="14" height="17" viewBox="0 0 24 24" fill="#7293a0">
            <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" />
          </svg>
          <span>Backup (Passing)</span>
        </div>
        <div className="legend-row">
          <svg width="14" height="17" viewBox="0 0 24 24" fill="#e06c68">
            <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" />
          </svg>
          <span>Backup (Fail)</span>
        </div>
      </div>

      {/* Bottom Left Scale */}
      <div className="map-scale-overlay">NASA LOLA · 80 m source<br/>400 m hillshade overview</div>

      {/* Zoom controls */}
      <div className="map-zoom-overlay">
        <button className="zoom-btn" onClick={() => setZoom(z => Math.min(2.5, z + 0.25))} title="Zoom In" aria-label="Zoom in">
          <Plus size={14} />
        </button>
        <button className="zoom-btn" onClick={() => setZoom(z => Math.max(0.8, z - 0.25))} title="Zoom Out" aria-label="Zoom out">
          <Minus size={14} />
        </button>
        <button className="zoom-btn" onClick={() => setZoom(2)} title="Reset Map" aria-label="Reset map">
          <RotateCcw size={13} />
        </button>
      </div>

      {/* Main SVG Polar Map */}
      <svg
        viewBox="0 0 540 480"
        className="polar-svg-map"
        style={{ width: '100%', height: '100%', display: 'block', maxHeight: '420px' }}
      >
        <defs>
          <clipPath id="circular-polar-clip">
            <circle cx={cx} cy={cy} r={mapRadius} />
          </clipPath>
          <radialGradient id="polar-vignette" cx="50%" cy="50%" r="50%">
            <stop offset="60%" stopColor="#000000" stopOpacity="0" />
            <stop offset="90%" stopColor="#000000" stopOpacity="0.45" />
            <stop offset="100%" stopColor="#051019" stopOpacity="0.85" />
          </radialGradient>
          <filter id="pin-glow">
            <feDropShadow dx="0" dy="2" stdDeviation="3" floodColor="#000000" floodOpacity="0.8" />
          </filter>
        </defs>

        {/* Circular Lunar Surface Texture */}
        <g clipPath="url(#circular-polar-clip)">
          {/* Photographic terrain relief */}
          <image
            href="/assets/nasa-lola-hillshade.png"
            x={cx - mapRadius * zoom}
            y={cy - mapRadius * zoom}
            width={mapRadius * 2 * zoom}
            height={mapRadius * 2 * zoom}
            preserveAspectRatio="xMidYMid slice"
            opacity="0.88"
          />

          {/* Vignette gradient overlay */}
          <circle cx={cx} cy={cy} r={mapRadius} fill="url(#polar-vignette)" />

          {/* Concentric Range Rings */}
          <circle cx={cx} cy={cy} r={45 * zoom} fill="none" stroke="rgba(255, 255, 255, 0.12)" strokeWidth="0.8" strokeDasharray="3 3" />
          <circle cx={cx} cy={cy} r={90 * zoom} fill="none" stroke="rgba(255, 255, 255, 0.12)" strokeWidth="0.8" strokeDasharray="3 3" />
          <circle cx={cx} cy={cy} r={135 * zoom} fill="none" stroke="rgba(255, 255, 255, 0.12)" strokeWidth="0.8" strokeDasharray="3 3" />
          <circle cx={cx} cy={cy} r={mapRadius} fill="none" stroke="rgba(255, 255, 255, 0.25)" strokeWidth="1" />

          {/* Polar Grid Axis Lines */}
          <line x1={cx} y1={cy - mapRadius} x2={cx} y2={cy + mapRadius} stroke="rgba(255, 255, 255, 0.12)" strokeWidth="0.8" strokeDasharray="3 3" />
          <line x1={cx - mapRadius} y1={cy} x2={cx + mapRadius} y2={cy} stroke="rgba(255, 255, 255, 0.12)" strokeWidth="0.8" strokeDasharray="3 3" />

          {/* Crater Labels */}
          {craters.map(c => {
            const p = project(c.lat, c.lon);
            return (
              <text
                key={c.name}
                x={p.x}
                y={p.y}
                textAnchor="middle"
                fill="#cbd5e1"
                fontSize="7.5"
                letterSpacing="1.2"
                opacity="0.55"
                fontWeight="500"
                style={{ pointerEvents: 'none', userSelect: 'none' }}
              >
                {c.name}
              </text>
            );
          })}

          {/* Center Crosshair and Pole Label */}
          <g>
            <line x1={cx - 7} y1={cy} x2={cx + 7} y2={cy} stroke="#ffffff" strokeWidth="1" opacity="0.6" />
            <line x1={cx} y1={cy - 7} x2={cx + 7} y2={cy} stroke="#ffffff" strokeWidth="1" opacity="0.6" />
            <text x={cx} y={cy - 12} textAnchor="middle" fill="#f1f5f9" fontSize="9.5" fontWeight="600" opacity="0.9">
              South Pole
            </text>
            <text x={cx} y={cy + 18} textAnchor="middle" fill="#94a3b8" fontSize="8.5" opacity="0.8">
              (90° S)
            </text>
          </g>

          {/* Site Pins */}
          {state.sites.map(s => {
            const pos = project(s.lat_deg, s.lon_deg);
            const isPrimary = s.site_id === state.primary;
            const ranking = state.rank(s.site_id);
            const isPassingBackup = state.backups.includes(s.site_id) && ranking?.passed;
            const isFailingBackup = state.backups.includes(s.site_id) && ranking && !ranking.passed;

            const pinColor = isPrimary
              ? '#dfa76a'
              : isPassingBackup
              ? '#84c99d'
              : isFailingBackup
              ? '#e06c68'
              : '#63c9c0';

            return (
              <g
                key={s.site_id}
                role="button" tabIndex={0} aria-label={`Select ${s.name}`} onKeyDown={e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();state.setAsPrimary(s.site_id);}}}
                style={{ cursor: 'pointer' }}
                onClick={() => {
                  state.setAsPrimary(s.site_id);
                  state.setSelected(s.site_id);
                }}
                onMouseEnter={e => {
                  setHoveredSite(s);
                  const rect = e.currentTarget.getBoundingClientRect();
                  const container = e.currentTarget.closest('.circular-polar-map-container')?.getBoundingClientRect();
                  if (container) {
                    setTooltipPos({
                      x: rect.left - container.left + rect.width / 2,
                      y: rect.top - container.top - 10,
                    });
                  }
                }}
                onMouseLeave={() => setHoveredSite(null)}
              >
                {/* Primary Radar Pulse Ring */}
                {isPrimary && (
                  <>
                    <circle cx={pos.x} cy={pos.y} r="7" fill="none" stroke="#dfa76a" strokeWidth="2" className="radar-pulse-ring" />
                    <circle cx={pos.x} cy={pos.y} r="7" fill="none" stroke="#dfa76a" strokeWidth="1.5" className="radar-pulse-ring-delayed" />
                    <circle cx={pos.x} cy={pos.y} r="18" fill="rgba(223, 167, 106, 0.16)" />
                  </>
                )}

                {/* Pin Head */}
                <g transform={`translate(${pos.x - 9}, ${pos.y - 20}) scale(0.75)`} filter="url(#pin-glow)">
                  <path
                    d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"
                    fill={pinColor}
                    stroke="#051019"
                    strokeWidth="1"
                  />
                </g>
              </g>
            );
          })}
        </g>

        {/* Outer Circle Ring */}
        <circle cx={cx} cy={cy} r={mapRadius} fill="none" stroke="rgba(255, 255, 255, 0.28)" strokeWidth="1.2" />

        {/* Cardinal Markers on Border */}
        {/* Top: 0° */}
        <line x1={cx} y1={cy - mapRadius - 4} x2={cx} y2={cy - mapRadius} stroke="#cbd5e1" strokeWidth="1" />
        <text x={cx} y={cy - mapRadius - 9} textAnchor="middle" fill="#cbd5e1" fontSize="10" fontWeight="600">
          0°
        </text>

        {/* Right: 90° E */}
        <line x1={cx + mapRadius} y1={cy} x2={cx + mapRadius + 4} y2={cy} stroke="#cbd5e1" strokeWidth="1" />
        <text x={cx + mapRadius + 9} y={cy + 3.5} textAnchor="start" fill="#cbd5e1" fontSize="10" fontWeight="600">
          90° E
        </text>

        {/* Bottom: 180° */}
        <line x1={cx} y1={cy + mapRadius} x2={cx} y2={cy + mapRadius + 4} stroke="#cbd5e1" strokeWidth="1" />
        <text x={cx} y={cy + mapRadius + 15} textAnchor="middle" fill="#cbd5e1" fontSize="10" fontWeight="600">
          180°
        </text>

        {/* Left: 90° W */}
        <line x1={cx - mapRadius - 4} y1={cy} x2={cx - mapRadius} y2={cy} stroke="#cbd5e1" strokeWidth="1" />
        <text x={cx - mapRadius - 9} y={cy + 3.5} textAnchor="end" fill="#cbd5e1" fontSize="10" fontWeight="600">
          90° W
        </text>
      </svg>

      {/* Floating Pin Tooltip */}
      {hoveredSite && (
        <div
          className="map-tooltip-card"
          style={{
            position: 'absolute',
            left: `${tooltipPos.x}px`,
            top: `${tooltipPos.y}px`,
            transform: 'translate(-50%, -100%)',
            pointerEvents: 'none',
            zIndex: 30,
          }}
        >
          <div className="tooltip-title">{hoveredSite.name}</div>
          <div className="tooltip-coords">
            {Math.abs(hoveredSite.lat_deg).toFixed(1)}° S, {hoveredSite.lon_deg >= 0 ? hoveredSite.lon_deg.toFixed(1) : (360 + hoveredSite.lon_deg).toFixed(1)}° E
          </div>
          <div className="tooltip-stats">
            <div>
              <span>Sunlight:</span> <strong>{getSunDays(hoveredSite)} days</strong>
            </div>
            <div>
              <span>Sun + Earth:</span> <strong>{getJointDays(hoveredSite)} days</strong>
            </div>
          </div>
          <div className="tooltip-tag">
            {hoveredSite.site_id === state.primary ? 'Primary Site' : 'Click to select as Primary'}
          </div>
        </div>
      )}
    </div>
  );
}
