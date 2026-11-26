"use client";

import React, { useMemo, useState, useRef, useCallback } from "react";
import { EventTriggerItem, SimulationResponse } from "@/lib/api";
import { formatFloat, formatWithUnit, formatCoordinate } from "@/lib/format";
import { ZoomIn, ZoomOut, RotateCcw } from "lucide-react";

export interface PlotPoint {
  x: number;
  y: number;
}

export interface ScientificPlotProps {
  simulationData?: SimulationResponse | null;
  presetId?: string;
  spacetime?: string;
  geodesicType?: string;
  title?: string;
  mass?: number;
  spin?: number;
  initialRadius?: number;
  domainRadius?: number;
  projection?: "equatorial" | "meridional";
  className?: string;
  isLoading?: boolean;
  error?: string | null;
  showIllustrativeBanner?: boolean;
}

export function ScientificPlot({
  simulationData,
  presetId,
  spacetime,
  geodesicType,
  mass = 1.0,
  spin = 0.0,
  initialRadius = 8.0,
  projection = "equatorial",
  className = "",
  isLoading = false,
  error = null,
}: ScientificPlotProps) {
  const svgRef = useRef<SVGSVGElement | null>(null);

  // Hover coordinate state
  const [hoverCoords, setHoverCoords] = useState<{
    x: number;
    y: number;
    r: number;
    phi: number;
  } | null>(null);

  // Determine whether this configuration is Schwarzschild or Kerr
  const isSchwarzschild = useMemo(() => {
    if (spacetime) return spacetime.toLowerCase() === "schwarzschild";
    if (presetId) return presetId.startsWith("schwarzschild_");
    return (spin ?? 0) === 0;
  }, [spacetime, presetId, spin]);

  // Compute reference radii strictly in accordance with physics engine rules:
  // - For Schwarzschild: exact analytical horizon r+=2M, photon sphere r_ph=3M, and ISCO r_ISCO=6M (if timelike)
  // - For Kerr: reference radii are NOT exposed by API schema; never compute in TypeScript or assume Schwarzschild values!
  const { rPlus, rPhoton, rIsco } = useMemo(() => {
    if (isSchwarzschild) {
      const rp = 2.0 * mass;
      const rph = 3.0 * mass;
      // ISCO is only physically defined for timelike orbits, not null orbits
      const isTimelike = geodesicType ? geodesicType === "timelike" : !presetId?.includes("photon");
      const risco = isTimelike ? 6.0 * mass : NaN;
      return { rPlus: rp, rPhoton: rph, rIsco: risco };
    }

    // For Kerr: Per Rule 3 & Rule 4, do NOT derive Kerr photon-orbit or ISCO in TypeScript,
    // and do NOT assume r+=2M. Omit reference rings when not supplied by API schema.
    return { rPlus: NaN, rPhoton: NaN, rIsco: NaN };
  }, [isSchwarzschild, mass, geodesicType, presetId]);

  // Extract trajectory points from live simulationData
  const { points, events, dataMaxR } = useMemo(() => {
    if (!simulationData?.trajectory?.coordinates) {
      return { points: [], events: [], dataMaxR: initialRadius };
    }

    const coords = simulationData.trajectory.coordinates;
    const pts: PlotPoint[] = [];
    let maxR = initialRadius;

    for (let i = 0; i < coords.r.length; i++) {
      const r = coords.r[i];
      const theta = coords.theta[i];
      const phi = coords.phi[i];

      if (r > maxR) maxR = r;

      if (projection === "meridional") {
        const x = r * Math.sin(theta);
        const z = r * Math.cos(theta);
        pts.push({ x, y: z });
      } else {
        const x = r * Math.sin(theta) * Math.cos(phi);
        const y = r * Math.sin(theta) * Math.sin(phi);
        pts.push({ x, y });
      }
    }

    const evs = (simulationData.triggered_events || []).map((ev: EventTriggerItem) => {
      let evX: number;
      let evY: number;
      if (projection === "meridional") {
        evX = ev.r * Math.sin(ev.theta);
        evY = ev.r * Math.cos(ev.theta);
      } else {
        evX = ev.r * Math.sin(ev.theta) * Math.cos(ev.phi);
        evY = ev.r * Math.sin(ev.theta) * Math.sin(ev.phi);
      }
      return { ...ev, x: evX, y: evY };
    });

    return { points: pts, events: evs, dataMaxR: maxR };
  }, [simulationData, projection, initialRadius]);

  // Domain scaling & interactive zoom
  const [zoom, setZoom] = useState<number>(1.0);
  const baseDomainRadius = Math.max(10.0, Math.ceil(dataMaxR * 1.25));
  const domainRadius = Math.max(4.0, baseDomainRadius / zoom);

  const handleZoomIn = () => setZoom((z) => Math.min(4.0, z * 1.25));
  const handleZoomOut = () => setZoom((z) => Math.max(0.4, z / 1.25));
  const handleResetZoom = () => setZoom(1.0);

  // SVG dimensions: equal aspect ratio
  const size = 600;
  const center = size / 2;
  const scale = (size * 0.44) / domainRadius; // Margin ~6%

  const toSvgX = useCallback((x: number) => center + x * scale, [center, scale]);
  const toSvgY = useCallback((y: number) => center - y * scale, [center, scale]);

  // Build SVG path string
  const pathD = useMemo(() => {
    if (!points || points.length === 0) return "";
    return points.reduce((acc, pt, idx) => {
      const sx = center + pt.x * scale;
      const sy = center - pt.y * scale;
      return idx === 0 ? `M ${sx.toFixed(2)} ${sy.toFixed(2)}` : `${acc} L ${sx.toFixed(2)} ${sy.toFixed(2)}`;
    }, "");
  }, [points, scale, center]);

  // Hairline concentric coordinate rings
  const gridRadii = useMemo(() => {
    const list: number[] = [];
    const step = domainRadius > 20 ? 8 : domainRadius > 10 ? 4 : 2;
    for (let r = step; r < domainRadius; r += step) {
      list.push(r);
    }
    return list;
  }, [domainRadius]);

  // Mouse hover coordinate tracking
  const handleMouseMove = (e: React.MouseEvent<SVGSVGElement>) => {
    if (!svgRef.current) return;
    const rect = svgRef.current.getBoundingClientRect();
    const clientX = e.clientX - rect.left;
    const clientY = e.clientY - rect.top;

    const svgX = (clientX / rect.width) * size;
    const svgY = (clientY / rect.height) * size;

    const physX = (svgX - center) / scale;
    const physY = (center - svgY) / scale;

    const r = Math.sqrt(physX * physX + physY * physY);
    let phi = Math.atan2(physY, physX);
    if (phi < 0) phi += 2 * Math.PI;

    setHoverCoords({ x: physX, y: physY, r, phi });
  };

  const handleMouseLeave = () => setHoverCoords(null);

  const startPt = points && points.length > 0 ? points[0] : null;
  const endPt = points && points.length > 0 ? points[points.length - 1] : null;

  return (
    <div
      className={`relative flex flex-col bg-[var(--surface)] text-[var(--foreground)] transition-colors overflow-hidden ${
        className.includes("border-0") ? "" : "border border-[var(--border)]"
      } ${className.includes("rounded-none") ? "" : "rounded-[4px]"} ${className}`}
    >
      {/* Top Plot Header: Axis Mode & View Controls */}
      <div className="flex items-center justify-between border-b border-[var(--border)] bg-[var(--surface-subtle)] px-4 py-2 text-xs font-sans">
        <div className="flex items-center gap-3">
          <span className="font-serif text-[13px] text-[var(--foreground)] font-normal">
            {projection === "equatorial" ? "Equatorial plane (x, y)" : "Meridional plane (x, z)"}
          </span>
          <span className="text-[var(--border)]" aria-hidden="true">|</span>
          <span className="font-mono text-[11px] text-[var(--foreground-secondary)]">
            Span: [&plusmn;{formatWithUnit(domainRadius, "M", 1)}]
          </span>
        </div>

        {/* Zoom controls */}
        <div className="flex items-center gap-1 font-sans">
          <button
            type="button"
            onClick={handleZoomIn}
            className="flex h-6 w-6 items-center justify-center rounded-[3px] border border-[var(--border)] bg-[var(--surface)] text-[var(--foreground)] hover:bg-[var(--surface-hover)] transition-colors"
            title="Zoom in"
            aria-label="Zoom in"
          >
            <ZoomIn className="h-3.5 w-3.5" />
          </button>
          <button
            type="button"
            onClick={handleZoomOut}
            className="flex h-6 w-6 items-center justify-center rounded-[3px] border border-[var(--border)] bg-[var(--surface)] text-[var(--foreground)] hover:bg-[var(--surface-hover)] transition-colors"
            title="Zoom out"
            aria-label="Zoom out"
          >
            <ZoomOut className="h-3.5 w-3.5" />
          </button>
          <button
            type="button"
            onClick={handleResetZoom}
            className="flex h-6 px-2 items-center justify-center rounded-[3px] border border-[var(--border)] bg-[var(--surface)] text-[var(--muted)] hover:text-[var(--foreground)] hover:bg-[var(--surface-hover)] transition-colors text-[11px]"
            title="Reset zoom"
          >
            <RotateCcw className="h-3 w-3 mr-1" />
            <span>Reset</span>
          </button>
        </div>
      </div>

      {/* Main SVG Plot Canvas Area */}
      <div className="relative flex-1 p-2 flex items-center justify-center bg-[var(--plot-bg)] min-h-[460px] select-none">
        {/* Loading overlay */}
        {isLoading && (
          <div className="absolute inset-0 z-20 flex flex-col items-center justify-center bg-[var(--surface)]/75 backdrop-blur-[1px] text-[var(--foreground)] p-4 text-center">
            <span className="font-serif text-sm">Computing trajectory...</span>
            <span className="font-mono text-xs text-[var(--muted)] mt-1">Adaptive DOP853 integrator</span>
            <span className="font-sans text-[11px] text-[var(--muted)] mt-2 max-w-xs">
              First request may take up to ~60s if the free-tier backend is waking from idle.
            </span>
          </div>
        )}

        {/* Error overlay */}
        {error && !isLoading && (
          <div className="absolute inset-0 z-20 flex flex-col items-center justify-center bg-[var(--surface)]/90 p-6 text-center">
            <p className="font-serif text-sm font-medium text-[var(--status-error)]">
              {error.toLowerCase().includes("wake") || error.toLowerCase().includes("readiness")
                ? "Backend Wake-Up Timed Out"
                : "Simulation unavailable"}
            </p>
            <p className="font-mono text-xs text-[var(--muted)] mt-1 max-w-md">
              {error}
            </p>
          </div>
        )}

        <svg
          ref={svgRef}
          viewBox={`0 0 ${size} ${size}`}
          className="w-full h-auto max-h-[520px] cursor-crosshair"
          role="img"
          aria-label="Relativistic geodesic coordinate trajectory plot"
          onMouseMove={handleMouseMove}
          onMouseLeave={handleMouseLeave}
        >
          {/* Coordinate grid */}
          <g className="grid-layer">
            {/* Primary axes */}
            <line
              x1={center}
              y1={20}
              x2={center}
              y2={size - 20}
              stroke="var(--border)"
              strokeWidth="1"
            />
            <line
              x1={20}
              y1={center}
              x2={size - 20}
              y2={center}
              stroke="var(--border)"
              strokeWidth="1"
            />

            {/* Hairline concentric coordinate rings */}
            {gridRadii.map((r) => (
              <circle
                key={`grid-r-${r}`}
                cx={center}
                cy={center}
                r={r * scale}
                fill="none"
                stroke="var(--plot-grid)"
                strokeWidth="1"
                strokeDasharray="2 3"
              />
            ))}

            {/* Coordinate grid labels */}
            {gridRadii.map((r) => (
              <text
                key={`label-r-${r}`}
                x={center + r * scale + 3}
                y={center - 4}
                fill="var(--foreground-secondary)"
                fontSize="12"
                fontFamily="var(--font-ibm-plex-mono), monospace"
              >
                {r}&thinsp;M
              </text>
            ))}

            {/* Axis direction indicators */}
            <text
              x={size - 28}
              y={center - 6}
              fill="var(--foreground-secondary)"
              fontSize="12"
              fontFamily="var(--font-ibm-plex-sans), sans-serif"
              textAnchor="end"
            >
              {projection === "equatorial" ? "+x / M" : "+x / M"}
            </text>
            <text
              x={center + 6}
              y={32}
              fill="var(--foreground-secondary)"
              fontSize="12"
              fontFamily="var(--font-ibm-plex-sans), sans-serif"
            >
              {projection === "equatorial" ? "+y / M" : "+z / M"}
            </text>
          </g>

          {/* Physical Reference Circles */}
          {/* ISCO Ring: r = 6M for Schwarzschild timelike configurations only */}
          {!isNaN(rIsco) && (
            <g className="isco-layer">
              <circle
                cx={center}
                cy={center}
                r={rIsco * scale}
                fill="none"
                stroke="var(--plot-isco)"
                strokeWidth="1"
                strokeDasharray="3 3"
              />
              <text
                x={center}
                y={center - rIsco * scale - 4}
                fill="var(--plot-isco)"
                fontSize="12"
                fontFamily="var(--font-ibm-plex-mono), monospace"
                textAnchor="middle"
              >
                r_ISCO = 6 M (Schw)
              </text>
            </g>
          )}

          {/* Photon Sphere Ring: r = 3M for Schwarzschild configurations only */}
          {!isNaN(rPhoton) && (
            <g className="photon-layer">
              <circle
                cx={center}
                cy={center}
                r={rPhoton * scale}
                fill="none"
                stroke="var(--plot-photon)"
                strokeWidth="1"
                strokeDasharray="2 2"
              />
              <text
                x={center}
                y={center - rPhoton * scale - 4}
                fill="var(--plot-photon)"
                fontSize="12"
                fontFamily="var(--font-ibm-plex-mono), monospace"
                textAnchor="middle"
              >
                r_ph = 3 M (Schw)
              </text>
            </g>
          )}

          {/* Event Horizon: For Schwarzschild only (r+ = 2M solid disc). Omitted for Kerr per physical rules */}
          {!isNaN(rPlus) ? (
            <g className="horizon-layer">
              <circle
                cx={center}
                cy={center}
                r={rPlus * scale}
                fill="var(--plot-horizon)"
                stroke="var(--border)"
                strokeWidth="1"
              />
              {/* Center point */}
              <circle cx={center} cy={center} r={1.5} fill="var(--muted)" />
              <text
                x={center}
                y={center + 4}
                fill="#FFFFFF"
                fontSize="12"
                fontFamily="var(--font-ibm-plex-mono), monospace"
                textAnchor="middle"
              >
                r+ (Schw)
              </text>
            </g>
          ) : null}

          {/* Trajectory Path */}
          {pathD && (
            <path
              d={pathD}
              fill="none"
              stroke="var(--plot-trajectory)"
              strokeWidth="1.75"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="animate-draw-in"
            />
          )}

          {/* Triggered Event Roots */}
          {events.map((ev, i) => (
            <g key={`event-${i}`} transform={`translate(${toSvgX(ev.x)}, ${toSvgY(ev.y)})`}>
              <circle r="4" fill="none" stroke="var(--status-error)" strokeWidth="1.25" />
              <circle r="2" fill="var(--status-error)" />
              <text
                x="6"
                y="-4"
                fill="var(--status-error)"
                fontSize="12"
                fontFamily="var(--font-ibm-plex-mono), monospace"
              >
                {ev.name === "radial_turning_point" ? "Turning pt" : ev.name}
              </text>
            </g>
          ))}

          {/* Initial Condition Marker lambda_0 */}
          {startPt && (
            <g transform={`translate(${toSvgX(startPt.x)}, ${toSvgY(startPt.y)})`}>
              <circle r="4" fill="var(--status-ok)" stroke="var(--surface)" strokeWidth="1" />
              <text
                x="6"
                y="-4"
                fill="var(--status-ok)"
                fontSize="12"
                fontFamily="var(--font-ibm-plex-mono), monospace"
                fontWeight="600"
              >
                λ₀
              </text>
            </g>
          )}

          {/* Terminal Condition Marker lambda_end */}
          {endPt && (
            <g transform={`translate(${toSvgX(endPt.x)}, ${toSvgY(endPt.y)})`}>
              <circle r="4" fill="var(--status-error)" stroke="var(--surface)" strokeWidth="1" />
              <text
                x="6"
                y="12"
                fill="var(--status-error)"
                fontSize="12"
                fontFamily="var(--font-ibm-plex-mono), monospace"
                fontWeight="600"
              >
                λ_end
              </text>
            </g>
          )}

          {/* Interactive cursor tracking indicator */}
          {hoverCoords && (
            <g transform={`translate(${toSvgX(hoverCoords.x)}, ${toSvgY(hoverCoords.y)})`}>
              <circle r="3" fill="none" stroke="var(--foreground)" strokeWidth="1" strokeDasharray="1 1" />
            </g>
          )}
        </svg>
      </div>

      {/* Hover Readout Bar */}
      <div className="flex items-center justify-between border-t border-[var(--border)] bg-[var(--surface-subtle)] px-4 py-2 font-mono text-xs text-[var(--foreground-secondary)]">
        <div>
          {hoverCoords ? (
            <span>
              Cursor:&thinsp;x = {formatCoordinate(hoverCoords.x)}&thinsp;M, y = {formatCoordinate(hoverCoords.y)}&thinsp;M
              <span className="mx-2 text-[var(--border)]">|</span>
              r = {formatCoordinate(hoverCoords.r)}&thinsp;M, &phi; = {formatFloat(hoverCoords.phi, 2)} rad
            </span>
          ) : (
            <span className="text-[var(--muted)]">Hover over plot to inspect coordinates</span>
          )}
        </div>
        <div className="text-[11px] text-[var(--muted)] font-sans hidden sm:inline">
          Coordinate representation (Boyer-Lindquist), not an isometric embedding.
        </div>
      </div>

      {/* Plot Legend */}
      <div className="flex flex-wrap items-center gap-x-5 gap-y-1.5 border-t border-[var(--border)] bg-[var(--surface)] px-4 py-2.5 font-mono text-xs text-[var(--foreground-secondary)]">
        {!isNaN(rPlus) && (
          <span className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-[var(--plot-horizon)] border border-[var(--border)]" />
            <span>Horizon r₊ ({formatWithUnit(rPlus, "M", 2)}, Schw)</span>
          </span>
        )}
        {!isNaN(rPhoton) && (
          <span className="flex items-center gap-1.5">
            <span className="h-0.5 w-3 border-t border-dashed border-[var(--plot-photon)]" />
            <span>Photon sphere ({formatWithUnit(rPhoton, "M", 0)}, Schw)</span>
          </span>
        )}
        {!isNaN(rIsco) && (
          <span className="flex items-center gap-1.5">
            <span className="h-0.5 w-3 border-t border-dashed border-[var(--plot-isco)]" />
            <span>ISCO ({formatWithUnit(rIsco, "M", 0)}, Schw)</span>
          </span>
        )}
        {isNaN(rPlus) && (
          <span className="text-xs text-[var(--muted)] font-sans italic">
            Kerr reference surfaces (horizon, photon orbit, ISCO) omitted (not exposed by API schema)
          </span>
        )}
        <span className="flex items-center gap-1.5">
          <span className="h-0.5 w-3 bg-[var(--plot-trajectory)]" />
          <span>Trajectory {isSchwarzschild ? "(Schwarzschild)" : "(Kerr)"}</span>
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full bg-[var(--status-ok)]" />
          <span>λ₀</span>
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full bg-[var(--status-error)]" />
          <span>λ_end</span>
        </span>
      </div>
    </div>
  );
}

export default ScientificPlot;
