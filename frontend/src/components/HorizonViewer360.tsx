import React from 'react';
import { EvaluatedSiteData } from '../types';
import { Sun, Globe2, Eye } from 'lucide-react';

interface HorizonViewer360Props {
  evaluatedSites: Record<string, EvaluatedSiteData>;
  selectedSiteIds: string[];
  currentStepIndex: number;
}

export const HorizonViewer360: React.FC<HorizonViewer360Props> = ({
  evaluatedSites,
  selectedSiteIds,
  currentStepIndex,
}) => {
  const siteColors = ['#38bdf8', '#fbbf24', '#c084fc'];

  // Plot coordinate mappings
  // Viewbox: 0 to 720 wide, 0 to 260 high
  const width = 720;
  const height = 260;
  const padLeft = 45;
  const padRight = 20;
  const padTop = 25;
  const padBottom = 35;

  const plotW = width - padLeft - padRight;
  const plotH = height - padTop - padBottom;

  // Elevation range: -6° to +18°
  const minEl = -6.0;
  const maxEl = 18.0;

  const azToX = (azDeg: number) => {
    const norm = (azDeg % 360.0) / 360.0;
    return padLeft + norm * plotW;
  };

  const elToY = (elDeg: number) => {
    const clamped = Math.max(minEl, Math.min(maxEl, elDeg));
    const norm = (clamped - minEl) / (maxEl - minEl);
    return padTop + (1.0 - norm) * plotH;
  };

  const zeroElY = elToY(0.0);

  // Compass ticks
  const compassTicks = [
    { az: 0, label: '0° N' },
    { az: 45, label: '45° NE' },
    { az: 90, label: '90° E' },
    { az: 135, label: '135° SE' },
    { az: 180, label: '180° S' },
    { az: 225, label: '225° SW' },
    { az: 270, label: '270° W' },
    { az: 315, label: '315° NW' },
    { az: 360, label: '360° N' },
  ];

  // Elevation ticks
  const elTicks = [-5, 0, 5, 10, 15];

  return (
    <div className="glass-panel rounded-2xl p-4 flex flex-col h-full">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Eye className="w-4 h-4 text-amber-400" />
          <h2 className="text-sm font-semibold text-slate-200">
            360° Panoramic Horizon & Skyline Viewer
          </h2>
        </div>
        <div className="flex items-center gap-3 text-xs font-mono">
          <span className="flex items-center gap-1 text-amber-300">
            <Sun className="w-3.5 h-3.5 text-amber-400 animate-pulse" />
            Solar Disk (0.53°)
          </span>
          <span className="flex items-center gap-1 text-cyan-300">
            <Globe2 className="w-3.5 h-3.5 text-cyan-400" />
            Earth Center (DTE)
          </span>
        </div>
      </div>

      <div className="relative flex-1 min-h-[260px] bg-slate-950/80 rounded-xl border border-slate-800/80 p-2 overflow-hidden flex items-center justify-center">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="w-full h-full select-none"
        >
          <defs>
            {/* Shaded horizon gradients */}
            {selectedSiteIds.map((sid, index) => {
              const color = siteColors[index % siteColors.length];
              return (
                <linearGradient
                  key={sid}
                  id={`horizonGrad-${sid}`}
                  x1="0"
                  y1="0"
                  x2="0"
                  y2="1"
                >
                  <stop offset="0%" stopColor={color} stopOpacity="0.35" />
                  <stop offset="100%" stopColor={color} stopOpacity="0.05" />
                </linearGradient>
              );
            })}
            <filter id="glowSun" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
            <filter id="glowEarth" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="2.5" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {/* Grid lines: Elevation */}
          {elTicks.map((el) => {
            const y = elToY(el);
            const isZero = el === 0;
            return (
              <g key={el}>
                <line
                  x1={padLeft}
                  y1={y}
                  x2={width - padRight}
                  y2={y}
                  stroke={isZero ? '#475569' : '#1e293b'}
                  strokeWidth={isZero ? 1.2 : 0.8}
                  strokeDasharray={isZero ? 'none' : '3 3'}
                />
                <text
                  x={padLeft - 6}
                  y={y + 3}
                  textAnchor="end"
                  fill={isZero ? '#94a3b8' : '#475569'}
                  fontSize="9"
                  fontFamily="monospace"
                >
                  {el > 0 ? `+${el}°` : `${el}°`}
                </text>
              </g>
            );
          })}

          {/* Grid lines: Azimuth */}
          {compassTicks.map((tick) => {
            const x = azToX(tick.az);
            return (
              <g key={tick.az}>
                <line
                  x1={x}
                  y1={padTop}
                  x2={x}
                  y2={height - padBottom}
                  stroke="#1e293b"
                  strokeWidth="0.8"
                />
                <text
                  x={x}
                  y={height - padBottom + 16}
                  textAnchor="middle"
                  fill="#64748b"
                  fontSize="9"
                  fontFamily="monospace"
                >
                  {tick.label}
                </text>
              </g>
            );
          })}

          {/* Terrain silhouettes for each site */}
          {selectedSiteIds.map((sid, index) => {
            const sdata = evaluatedSites[sid];
            if (!sdata || !sdata.horizon_360) return null;
            const color = siteColors[index % siteColors.length];

            // Build polygon path
            let d = `M ${azToX(0)} ${elToY(sdata.horizon_360[0])} `;
            for (let az = 1; az < 360; az++) {
              d += `L ${azToX(az)} ${elToY(sdata.horizon_360[az])} `;
            }
            // Close at 360 deg using first point
            d += `L ${azToX(360)} ${elToY(sdata.horizon_360[0])} `;
            // Drop down to bottom
            d += `L ${azToX(360)} ${height - padBottom} L ${azToX(0)} ${height - padBottom} Z`;

            // Stroke line path only
            let strokeD = `M ${azToX(0)} ${elToY(sdata.horizon_360[0])} `;
            for (let az = 1; az < 360; az++) {
              strokeD += `L ${azToX(az)} ${elToY(sdata.horizon_360[az])} `;
            }
            strokeD += `L ${azToX(360)} ${elToY(sdata.horizon_360[0])}`;

            return (
              <g key={sid}>
                {/* Shaded area */}
                <path d={d} fill={`url(#horizonGrad-${sid})`} />
                {/* Silhouette line */}
                <path
                  d={strokeD}
                  fill="none"
                  stroke={color}
                  strokeWidth={index === 0 ? 2.0 : 1.5}
                  strokeDasharray={index === 1 ? '4 2' : (index === 2 ? '2 2' : 'none')}
                  opacity="0.9"
                />
              </g>
            );
          })}

          {/* Sun & Earth markers at current timestep */}
          {selectedSiteIds.map((sid, index) => {
            const sdata = evaluatedSites[sid];
            if (!sdata || !sdata.ephemeris) return null;
            const eph = sdata.ephemeris;
            const tIdx = Math.min(currentStepIndex, (eph.sun_azimuth?.length || 1) - 1);

            const sunAz = eph.sun_azimuth[tIdx] ?? 0;
            const sunEl = eph.sun_elevation[tIdx] ?? 0;
            const earthAz = eph.earth_azimuth[tIdx] ?? 0;
            const earthEl = eph.earth_elevation[tIdx] ?? 0;

            const sunX = azToX(sunAz);
            const sunY = elToY(sunEl);
            const earthX = azToX(earthAz);
            const earthY = elToY(earthEl);

            const isPrimary = index === 0;

            return (
              <g key={`markers-${sid}`}>
                {/* Render Sun for primary site prominently, other sites subtly */}
                {isPrimary ? (
                  <g filter="url(#glowSun)">
                    <circle cx={sunX} cy={sunY} r={7} fill="#f59e0b" stroke="#fef08a" strokeWidth="1.5" />
                    <circle cx={sunX} cy={sunY} r={14} fill="#f59e0b" opacity="0.2" />
                    <text
                      x={sunX}
                      y={sunY - 11}
                      textAnchor="middle"
                      fill="#fde047"
                      fontSize="9"
                      fontWeight="bold"
                      fontFamily="monospace"
                    >
                      Sun {sunEl > 0 ? `+${sunEl.toFixed(1)}°` : `${sunEl.toFixed(1)}°`}
                    </text>
                  </g>
                ) : (
                  <circle
                    cx={sunX}
                    cy={sunY}
                    r={4}
                    fill="#f59e0b"
                    stroke="#ffffff"
                    strokeWidth="0.8"
                    opacity="0.75"
                  />
                )}

                {/* Render Earth */}
                {isPrimary ? (
                  <g filter="url(#glowEarth)">
                    <circle cx={earthX} cy={earthY} r={6} fill="#06b6d4" stroke="#e0f2fe" strokeWidth="1.5" />
                    <circle cx={earthX} cy={earthY} r={12} fill="#06b6d4" opacity="0.2" />
                    <text
                      x={earthX}
                      y={earthY - 10}
                      textAnchor="middle"
                      fill="#38bdf8"
                      fontSize="9"
                      fontWeight="bold"
                      fontFamily="monospace"
                    >
                      Earth {earthEl > 0 ? `+${earthEl.toFixed(1)}°` : `${earthEl.toFixed(1)}°`}
                    </text>
                  </g>
                ) : (
                  <circle
                    cx={earthX}
                    cy={earthY}
                    r={3.5}
                    fill="#06b6d4"
                    stroke="#ffffff"
                    strokeWidth="0.8"
                    opacity="0.75"
                  />
                )}
              </g>
            );
          })}
        </svg>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap items-center justify-between gap-2 mt-2 pt-2 border-t border-slate-800 text-[11px] text-slate-400">
        <div className="flex items-center gap-3">
          {selectedSiteIds.map((sid, idx) => {
            const sdata = evaluatedSites[sid];
            const name = sdata?.site_info?.name || sid;
            const color = siteColors[idx % siteColors.length];
            return (
              <div key={sid} className="flex items-center gap-1.5">
                <span className="w-3 h-1 rounded" style={{ backgroundColor: color }} />
                <span className="text-slate-300 font-medium">{name}</span>
              </div>
            );
          })}
        </div>
        <span className="font-mono text-slate-400">
          Horizon elevation calculated with spherical curvature drop-off (d² / 2R)
        </span>
      </div>
    </div>
  );
};
