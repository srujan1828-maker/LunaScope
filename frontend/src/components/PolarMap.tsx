import React, { useState } from 'react';
import { LandingSite } from '../types';
import { MapPin, Mountain, Sun, Sparkles } from 'lucide-react';

interface PolarMapProps {
  sites: LandingSite[];
  selectedSiteIds: string[];
  onToggleSite: (siteId: string) => void;
}

export const PolarMap: React.FC<PolarMapProps> = ({
  sites,
  selectedSiteIds,
  onToggleSite,
}) => {
  const [hoveredSite, setHoveredSite] = useState<LandingSite | null>(null);

  // SVG viewport dimensions
  const size = 440;
  const center = size / 2;
  const maxRadius = center - 35; // Map boundary corresponds to ~84°S (colatitude = 6°)

  // Map lat/lon to planar SVG coordinates
  // colatitude = 90 - abs(lat) in degrees [0 at pole, 6 at 84°S]
  const projectPoint = (lat: number, lon: number) => {
    const colat = 90.0 + lat; // positive degrees from pole
    const r = (colat / 6.5) * maxRadius;
    const rad = (lon * Math.PI) / 180.0;
    // lon 0° points UP (negative Y), lon 90° points RIGHT (positive X)
    const x = center + r * Math.sin(rad);
    const y = center - r * Math.cos(rad);
    return { x, y };
  };

  const rings = [
    { lat: -89.0, label: "89°S" },
    { lat: -88.0, label: "88°S" },
    { lat: -86.0, label: "86°S" },
    { lat: -84.0, label: "84°S" },
  ];

  const siteColors = ['#38bdf8', '#fbbf24', '#c084fc'];

  return (
    <div className="glass-panel rounded-2xl p-4 flex flex-col h-full relative overflow-hidden">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <MapPin className="w-4 h-4 text-cyan-400" />
          <h2 className="text-sm font-semibold text-slate-200">
            Lunar South Pole Stereographic Map
          </h2>
        </div>
        <span className="text-[11px] font-mono text-slate-400 bg-slate-900/80 px-2 py-0.5 rounded border border-slate-800">
          84°S – 90°S (DE421 / MOON_ME)
        </span>
      </div>

      <div className="relative flex-1 flex items-center justify-center min-h-[360px]">
        <svg
          viewBox={`0 0 ${size} ${size}`}
          className="w-full max-w-[400px] h-auto select-none"
        >
          <defs>
            {/* Crater gradients */}
            <radialGradient id="craterDark" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#020617" stopOpacity="0.9" />
              <stop offset="85%" stopColor="#0f172a" stopOpacity="0.4" />
              <stop offset="100%" stopColor="#1e293b" stopOpacity="0.1" />
            </radialGradient>
            <radialGradient id="poleGlow" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.15" />
              <stop offset="100%" stopColor="#020617" stopOpacity="0" />
            </radialGradient>
          </defs>

          {/* Background polar disc */}
          <circle cx={center} cy={center} r={maxRadius} fill="#090f24" stroke="#1e293b" strokeWidth="1.5" />
          <circle cx={center} cy={center} r={maxRadius} fill="url(#poleGlow)" />

          {/* Crater feature outlines */}
          {/* Shackleton crater at center */}
          <circle cx={center} cy={center} r={14} fill="url(#craterDark)" stroke="#334155" strokeWidth="1" strokeDasharray="2 2" />
          <text x={center + 16} y={center + 4} fill="#64748b" fontSize="8" fontFamily="monospace">Shackleton</text>

          {/* Haworth crater rim */}
          <ellipse cx={center - 12} cy={center - 110} rx={32} ry={24} fill="url(#craterDark)" stroke="#334155" strokeWidth="0.8" strokeDasharray="3 3" />
          <text x={center - 38} y={center - 112} fill="#64748b" fontSize="7" fontFamily="monospace">Haworth</text>

          {/* Faustini crater rim */}
          <ellipse cx={center + 120} cy={center - 30} rx={28} ry={22} fill="url(#craterDark)" stroke="#334155" strokeWidth="0.8" strokeDasharray="3 3" />
          <text x={center + 100} y={center - 32} fill="#64748b" fontSize="7" fontFamily="monospace">Faustini</text>

          {/* Nobile crater rim */}
          <ellipse cx={center + 130} cy={center + 110} rx={45} ry={35} fill="url(#craterDark)" stroke="#334155" strokeWidth="0.8" strokeDasharray="3 3" />
          <text x={center + 110} y={center + 112} fill="#64748b" fontSize="7" fontFamily="monospace">Nobile</text>

          {/* Concentric Latitude Rings */}
          {rings.map((ring) => {
            const colat = 90.0 + ring.lat;
            const r = (colat / 6.5) * maxRadius;
            return (
              <g key={ring.lat}>
                <circle
                  cx={center}
                  cy={center}
                  r={r}
                  fill="none"
                  stroke="#1e293b"
                  strokeWidth="0.8"
                  strokeDasharray="4 4"
                />
                <text
                  x={center + 4}
                  y={center - r + 9}
                  fill="#475569"
                  fontSize="8"
                  fontFamily="monospace"
                >
                  {ring.label}
                </text>
              </g>
            );
          })}

          {/* Radial Longitude Meridians */}
          {[0, 45, 90, 135, 180, 225, 270, 315].map((deg) => {
            const rad = (deg * Math.PI) / 180.0;
            const x2 = center + maxRadius * Math.sin(rad);
            const y2 = center - maxRadius * Math.cos(rad);
            return (
              <line
                key={deg}
                x1={center}
                y1={center}
                x2={x2}
                y2={y2}
                stroke="#1e293b"
                strokeWidth="0.7"
              />
            );
          })}

          {/* Meridian Labels */}
          <text x={center} y={center - maxRadius - 8} fill="#64748b" fontSize="9" textAnchor="middle" fontFamily="monospace">0° (Prime)</text>
          <text x={center + maxRadius + 14} y={center + 3} fill="#64748b" fontSize="9" textAnchor="middle" fontFamily="monospace">90°E</text>
          <text x={center} y={center + maxRadius + 14} fill="#64748b" fontSize="9" textAnchor="middle" fontFamily="monospace">180°</text>
          <text x={center - maxRadius - 14} y={center + 3} fill="#64748b" fontSize="9" textAnchor="middle" fontFamily="monospace">270°E</text>

          {/* Exact South Pole Marker */}
          <circle cx={center} cy={center} r={3} fill="#38bdf8" />
          <circle cx={center} cy={center} r={7} fill="none" stroke="#38bdf8" strokeWidth="0.8" opacity="0.6" />

          {/* Candidate Landing Site Markers */}
          {sites.map((site) => {
            const { x, y } = projectPoint(site.lat_deg, site.lon_deg);
            const isSelected = selectedSiteIds.includes(site.site_id);
            const selIndex = selectedSiteIds.indexOf(site.site_id);
            const color = isSelected ? siteColors[selIndex % siteColors.length] : '#94a3b8';
            const isHovered = hoveredSite?.site_id === site.site_id;

            return (
              <g
                key={site.site_id}
                className="cursor-pointer transition-transform hover:scale-125"
                onClick={() => onToggleSite(site.site_id)}
                onMouseEnter={() => setHoveredSite(site)}
                onMouseLeave={() => setHoveredSite(null)}
              >
                {/* Selection ring */}
                {isSelected && (
                  <circle
                    cx={x}
                    cy={y}
                    r={12}
                    fill="none"
                    stroke={color}
                    strokeWidth="1.5"
                    strokeDasharray="3 3"
                    className="animate-spin"
                    style={{ transformOrigin: `${x}px ${y}px`, animationDuration: '8s' }}
                  />
                )}

                {/* Outer halo */}
                <circle
                  cx={x}
                  cy={y}
                  r={isHovered ? 8 : (isSelected ? 6 : 4.5)}
                  fill={color}
                  fillOpacity={isSelected ? 0.3 : 0.15}
                />

                {/* Core dot */}
                <circle
                  cx={x}
                  cy={y}
                  r={isHovered ? 4.5 : (isSelected ? 4 : 3)}
                  fill={color}
                  stroke="#0f172a"
                  strokeWidth="1"
                />

                {/* Site label */}
                <text
                  x={x}
                  y={y - 8}
                  textAnchor="middle"
                  fill={isSelected ? '#f8fafc' : '#94a3b8'}
                  fontSize={isSelected ? "9" : "8"}
                  fontWeight={isSelected ? "600" : "400"}
                  className="pointer-events-none drop-shadow"
                >
                  {site.name.split(' ')[0]}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Hover Tooltip Popup */}
        {hoveredSite && (
          <div className="absolute bottom-2 left-2 right-2 bg-slate-900/95 border border-cyan-500/30 rounded-xl p-3 shadow-xl backdrop-blur-md pointer-events-none z-20">
            <div className="flex items-center justify-between mb-1">
              <span className="font-semibold text-xs text-cyan-300">{hoveredSite.name}</span>
              <span className="text-[10px] text-slate-400 font-mono">
                {hoveredSite.lat_deg.toFixed(2)}°, {hoveredSite.lon_deg.toFixed(2)}°
              </span>
            </div>
            <p className="text-[11px] text-slate-300 leading-snug line-clamp-2 mb-2">
              {hoveredSite.description}
            </p>
            <div className="grid grid-cols-3 gap-2 text-[10px] font-mono">
              <div className="bg-slate-950/80 px-2 py-1 rounded border border-slate-800 flex items-center gap-1">
                <Mountain className="w-3 h-3 text-slate-400" />
                <span>{hoveredSite.elevation_m > 0 ? `+${hoveredSite.elevation_m}` : hoveredSite.elevation_m} m</span>
              </div>
              <div className="bg-slate-950/80 px-2 py-1 rounded border border-slate-800 flex items-center gap-1">
                <Sun className="w-3 h-3 text-amber-400" />
                <span>{hoveredSite.annual_data["2027"]?.max_consec_sun_days || 0}d Sun</span>
              </div>
              <div className="bg-slate-950/80 px-2 py-1 rounded border border-slate-800 flex items-center gap-1">
                <Sparkles className="w-3 h-3 text-cyan-400" />
                <span>{hoveredSite.psr_distance_km}km PSR</span>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="mt-2 text-center text-[11px] text-slate-400">
        Click any site pin to toggle comparison tray (up to 3 sites)
      </div>
    </div>
  );
};
