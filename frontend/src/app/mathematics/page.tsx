"use client";

import React, { useState } from "react";
import Link from "next/link";
import MathBlock from "@/components/MathBlock";
import { calculateKerrRadii } from "@/lib/kerrGeometry";
import {
  Compass,
  ArrowRight,
  Copy,
  Check,
  BookOpen,
  Info,
} from "lucide-react";

interface SectionLink {
  id: string;
  title: string;
  short: string;
}

const SECTIONS: SectionLink[] = [
  { id: "foundations", title: "1. Geometric Foundations", short: "Foundations" },
  { id: "hamiltonian", title: "2. Hamiltonian Formulation", short: "Hamiltonian" },
  { id: "symmetries", title: "3. Symmetries & Conserved Quantities", short: "Symmetries" },
  { id: "separated", title: "4. Separated Geodesic Equations", short: "Potentials" },
  { id: "orbits", title: "5. Important Physical Orbits", short: "Orbits" },
  { id: "numerics", title: "6. Numerical Integration & Diagnostics", short: "Numerics" },
  { id: "explorer", title: "7. Connection to Geodesic Explorer", short: "Explorer" },
];

function CopyableEquation({ math, label }: { math: string; label?: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(math);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative group my-3 rounded-[3px] border border-[var(--border)] bg-[var(--surface-subtle)] p-3 pt-2">
      <div className="flex items-center justify-between text-[11px] font-mono text-[var(--muted)] border-b border-[var(--border)] pb-1 mb-2">
        <span>{label || "Equation"}</span>
        <button
          type="button"
          onClick={handleCopy}
          className="inline-flex items-center gap-1 text-[var(--muted)] hover:text-[var(--foreground)] transition-colors cursor-pointer"
          title="Copy LaTeX source"
        >
          {copied ? (
            <>
              <Check className="h-3 w-3 text-[var(--status-ok)]" />
              <span className="text-[10px]">Copied</span>
            </>
          ) : (
            <>
              <Copy className="h-3 w-3" />
              <span className="text-[10px]">Copy LaTeX</span>
            </>
          )}
        </button>
      </div>
      <MathBlock math={math} display={true} />
    </div>
  );
}

function SpacetimeDiagram() {
  const [spin, setSpin] = useState(0.9);
  const [thetaDeg, setThetaDeg] = useState(60);
  const [mass, setMass] = useState(1.0);

  // Evaluate characteristic Kerr radii via the pure geometry module
  const radii = calculateKerrRadii(spin, thetaDeg, mass);
  const {
    rPlus,
    rMinus,
    rErgo,
    rPhPro,
    rPhRetro,
    rIscoPro,
    rIscoRetro,
    rPlusNorm,
  } = radii;

  const clampedChi = Math.max(0, Math.min(0.999, spin));
  const thetaRad = (thetaDeg * Math.PI) / 180;
  const sinTheta = Math.sin(thetaRad);
  const cosTheta = Math.cos(thetaRad);

  // SVG scaling: 1 M = 55 px, center at (280, 200)
  const cx = 280;
  const cy = 200;
  const scale = 55;

  // Ergosphere outer profile points: parametric in theta from 0 to 2pi (in units of M)
  const ergoPathPoints: string[] = [];
  const steps = 72;
  for (let i = 0; i <= steps; i++) {
    const t = (i / steps) * 2 * Math.PI;
    const ct = Math.cos(t);
    const st = Math.sin(t);
    const rE = 1 + Math.sqrt(Math.max(0, 1 - clampedChi * clampedChi * ct * ct));
    const px = cx + rE * st * scale;
    const py = cy - rE * ct * scale;
    ergoPathPoints.push(`${i === 0 ? "M" : "L"} ${px.toFixed(1)} ${py.toFixed(1)}`);
  }
  const ergoPathD = ergoPathPoints.join(" ") + " Z";

  // Ray coordinate position (normalized in units of M)
  const rayRNorm = rErgo / mass + 0.4;
  const rayX = cx + rayRNorm * sinTheta * scale;
  const rayY = cy - rayRNorm * cosTheta * scale;

  return (
    <div className="rounded-[4px] border border-[var(--border)] bg-[var(--surface)] p-5 space-y-4 my-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[var(--border)] pb-3">
        <div>
          <div className="font-mono text-xs uppercase tracking-wider text-[var(--accent)] font-semibold">
            Figure 1.1 · Interactive Spacetime Slicing
          </div>
          <div className="text-xs text-[var(--foreground-secondary)] mt-0.5">
            Boyer-Lindquist geometry: Event Horizon $r_+$, Ergosphere $r_{'{'}\rm ergo{'}'}(\theta)$, and Frame-Dragging
          </div>
        </div>
        <div className="flex items-center gap-4 text-xs font-mono">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-[var(--foreground)] border border-[var(--border)] inline-block" />
            <span className="text-[var(--muted)]">Horizon ($r_+$)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-[var(--accent)]/30 border border-[var(--accent)] inline-block" />
            <span className="text-[var(--accent)]">Ergosphere</span>
          </div>
        </div>
      </div>

      {/* SVG Canvas */}
      <div className="relative w-full overflow-hidden bg-[var(--surface-subtle)] rounded-[3px] border border-[var(--border)] flex justify-center py-4">
        <svg
          viewBox="0 0 560 400"
          className="w-full max-w-[560px] h-auto select-none"
          aria-label="Kerr Spacetime Boyer-Lindquist Geometry Diagram"
        >
          <defs>
            {/* Ergoregion striped pattern or gradient */}
            <radialGradient id="ergoGlow" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="var(--accent)" stopOpacity="0.25" />
              <stop offset="100%" stopColor="var(--accent)" stopOpacity="0.05" />
            </radialGradient>
            <marker
              id="axisArrow"
              viewBox="0 0 10 10"
              refX="6"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 1 L 8 5 L 0 9 z" fill="var(--foreground)" />
            </marker>
            <marker
              id="accentArrow"
              viewBox="0 0 10 10"
              refX="6"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 1 L 8 5 L 0 9 z" fill="var(--accent)" />
            </marker>
          </defs>

          {/* Coordinate grid lines */}
          <line
            x1="40"
            y1={cy}
            x2="520"
            y2={cy}
            stroke="var(--border)"
            strokeDasharray="3 3"
            strokeWidth="1"
          />
          <line
            x1={cx}
            y1="30"
            x2={cx}
            y2="370"
            stroke="var(--foreground)"
            strokeWidth="1.25"
            markerEnd="url(#axisArrow)"
          />

          {/* Equatorial Plane Label */}
          <text
            x="510"
            y={cy - 6}
            fill="var(--muted)"
            fontSize="10"
            fontFamily="monospace"
            textAnchor="end"
          >
            Equatorial Plane (θ = π/2)
          </text>

          {/* Rotation Axis Label */}
          <text
            x={cx + 10}
            y="45"
            fill="var(--foreground)"
            fontSize="11"
            fontFamily="monospace"
            fontWeight="bold"
          >
            Spin Axis J = aM ẑ
          </text>

          {/* Ergosphere shape */}
          <path
            d={ergoPathD}
            fill="url(#ergoGlow)"
            stroke="var(--accent)"
            strokeWidth="1.5"
            strokeDasharray="4 2"
          />

          {/* Outer Horizon r+ (circle in Boyer-Lindquist coordinate representation) */}
          <circle
            cx={cx}
            cy={cy}
            r={rPlusNorm * scale}
            fill="var(--surface)"
            stroke="var(--foreground)"
            strokeWidth="2"
          />

          {/* Inner Cauchy Horizon r- */}
          {rMinus / mass > 0.05 && (
            <circle
              cx={cx}
              cy={cy}
              r={(rMinus / mass) * scale}
              fill="none"
              stroke="var(--muted)"
              strokeDasharray="2 2"
              strokeWidth="1"
            />
          )}

          {/* Ring singularity indicator at r = 0 in equatorial plane */}
          <circle
            cx={cx}
            cy={cy}
            r="3"
            fill="var(--accent)"
          />
          <text
            x={cx + 8}
            y={cy + 14}
            fill="var(--accent)"
            fontSize="9"
            fontFamily="monospace"
          >
            r = 0 (Ring Singularity)
          </text>

          {/* Sample test particle ray / angle */}
          <line
            x1={cx}
            y1={cy}
            x2={rayX}
            y2={rayY}
            stroke="var(--accent)"
            strokeWidth="1.2"
          />
          <circle cx={rayX} cy={rayY} r="3.5" fill="var(--accent)" />

          {/* Angle arc for theta (guarded when theta = 0) */}
          {thetaDeg > 0 && (
            <path
              d={`M ${cx} ${cy - 40} A 40 40 0 0 1 ${(cx + 40 * sinTheta).toFixed(1)} ${(cy - 40 * cosTheta).toFixed(1)}`}
              fill="none"
              stroke="var(--foreground)"
              strokeWidth="1"
            />
          )}
          <text
            x={cx + 18}
            y={cy - 22}
            fill="var(--foreground)"
            fontSize="10"
            fontFamily="monospace"
          >
            θ = {thetaDeg}°
          </text>

          {/* Dimension arrows for r+ and r_ergo on equator */}
          <line
            x1={cx}
            y1={cy + 55}
            x2={cx + rPlusNorm * scale}
            y2={cy + 55}
            stroke="var(--foreground)"
            strokeWidth="1"
            markerEnd="url(#axisArrow)"
          />
          <text
            x={cx + (rPlusNorm * scale) / 2}
            y={cy + 50}
            fill="var(--foreground)"
            fontSize="9"
            fontFamily="monospace"
            textAnchor="middle"
          >
            r+ = {rPlus.toFixed(2)}{mass === 1 ? "M" : ` (${rPlusNorm.toFixed(2)}M)`}
          </text>

          <line
            x1={cx}
            y1={cy + 80}
            x2={cx + 2 * scale}
            y2={cy + 80}
            stroke="var(--accent)"
            strokeWidth="1"
            markerEnd="url(#accentArrow)"
          />
          <text
            x={cx + scale}
            y={cy + 75}
            fill="var(--accent)"
            fontSize="9"
            fontFamily="monospace"
            textAnchor="middle"
          >
            r_ergo(π/2) = {(2 * mass).toFixed(2)}{mass === 1 ? "M" : ` (2.00M)`}
          </text>

          {/* Frame dragging rotational swirl indicator */}
          <path
            d={`M ${cx + 1.2 * scale} ${cy - 0.7 * scale} A ${1.4 * scale} ${0.6 * scale} 0 0 1 ${cx + 1.2 * scale} ${cy + 0.7 * scale}`}
            fill="none"
            stroke="var(--accent)"
            strokeWidth="1.25"
            strokeDasharray="3 3"
            markerEnd="url(#accentArrow)"
          />
          <text
            x={cx + 1.5 * scale}
            y={cy}
            fill="var(--accent)"
            fontSize="9"
            fontFamily="monospace"
          >
            Frame Dragging dϕ/dλ &gt; 0
          </text>
        </svg>
      </div>

      {/* Interactive Controls */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
        {/* Dimensionless Spin Slider */}
        <div className="space-y-1.5 bg-[var(--surface-subtle)] p-3 rounded-[3px] border border-[var(--border)]">
          <div className="flex justify-between text-xs font-mono">
            <span className="text-[var(--foreground)] font-medium">Spin (χ = a/M)</span>
            <span className="text-[var(--accent)] font-semibold">{spin.toFixed(3)}</span>
          </div>
          <input
            type="range"
            min="0"
            max="0.999"
            step="0.005"
            value={spin}
            onChange={(e) => setSpin(parseFloat(e.target.value))}
            className="w-full accent-[var(--accent)] cursor-pointer"
          />
          <div className="flex justify-between text-[10px] text-[var(--muted)] font-mono">
            <span>0.000</span>
            <span>0.900</span>
            <span>0.999</span>
          </div>
        </div>

        {/* Polar Angle Slider */}
        <div className="space-y-1.5 bg-[var(--surface-subtle)] p-3 rounded-[3px] border border-[var(--border)]">
          <div className="flex justify-between text-xs font-mono">
            <span className="text-[var(--foreground)] font-medium">Polar Angle (θ)</span>
            <span className="text-[var(--accent)] font-semibold">{thetaDeg}°</span>
          </div>
          <input
            type="range"
            min="0"
            max="90"
            step="1"
            value={thetaDeg}
            onChange={(e) => setThetaDeg(parseInt(e.target.value))}
            className="w-full accent-[var(--accent)] cursor-pointer"
          />
          <div className="flex justify-between text-[10px] text-[var(--muted)] font-mono">
            <span>0° (Pole)</span>
            <span>45°</span>
            <span>90° (Equator)</span>
          </div>
        </div>

        {/* Black Hole Mass Slider */}
        <div className="space-y-1.5 bg-[var(--surface-subtle)] p-3 rounded-[3px] border border-[var(--border)]">
          <div className="flex justify-between text-xs font-mono">
            <span className="text-[var(--foreground)] font-medium">Mass (M)</span>
            <span className="text-[var(--accent)] font-semibold">{mass.toFixed(1)}</span>
          </div>
          <input
            type="range"
            min="0.5"
            max="5.0"
            step="0.1"
            value={mass}
            onChange={(e) => setMass(parseFloat(e.target.value))}
            className="w-full accent-[var(--accent)] cursor-pointer"
          />
          <div className="flex justify-between text-[10px] text-[var(--muted)] font-mono">
            <span>0.5 M</span>
            <span>1.0 M</span>
            <span>5.0 M</span>
          </div>
        </div>
      </div>

      {/* Real-time Radii Readout Table (7 Columns: Horizons, Ergosphere, Photons, ISCOs) */}
      <div className="overflow-x-auto rounded-[3px] border border-[var(--border)]">
        <table className="w-full text-left text-xs font-mono">
          <thead className="bg-[var(--surface-subtle)] border-b border-[var(--border)] text-[var(--foreground)]">
            <tr>
              <th className="py-1.5 px-2.5">Horizon r+</th>
              <th className="py-1.5 px-2.5">Inner Cauchy r-</th>
              <th className="py-1.5 px-2.5 text-[var(--accent)]">Ergosphere r_ergo(θ)</th>
              <th className="py-1.5 px-2.5">Prograde Photon r_ph+</th>
              <th className="py-1.5 px-2.5">Retrograde Photon r_ph-</th>
              <th className="py-1.5 px-2.5">Prograde ISCO r_isco+</th>
              <th className="py-1.5 px-2.5">Retrograde ISCO r_isco-</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--border)] bg-[var(--surface)] text-[var(--foreground-secondary)]">
            <tr>
              <td className="py-1.5 px-2.5 font-semibold text-[var(--foreground)]">{mass === 1 ? `${rPlus.toFixed(4)} M` : `${rPlus.toFixed(3)} (${rPlusNorm.toFixed(3)}M)`}</td>
              <td className="py-1.5 px-2.5">{mass === 1 ? `${rMinus.toFixed(4)} M` : `${rMinus.toFixed(3)} (${(rMinus / mass).toFixed(3)}M)`}</td>
              <td className="py-1.5 px-2.5 font-semibold text-[var(--accent)]">{mass === 1 ? `${rErgo.toFixed(4)} M` : `${rErgo.toFixed(3)} (${(rErgo / mass).toFixed(3)}M)`}</td>
              <td className="py-1.5 px-2.5">{mass === 1 ? `${rPhPro.toFixed(4)} M` : `${rPhPro.toFixed(3)} (${(rPhPro / mass).toFixed(3)}M)`}</td>
              <td className="py-1.5 px-2.5">{mass === 1 ? `${rPhRetro.toFixed(4)} M` : `${rPhRetro.toFixed(3)} (${(rPhRetro / mass).toFixed(3)}M)`}</td>
              <td className="py-1.5 px-2.5">{mass === 1 ? `${rIscoPro.toFixed(4)} M` : `${rIscoPro.toFixed(3)} (${(rIscoPro / mass).toFixed(3)}M)`}</td>
              <td className="py-1.5 px-2.5">{mass === 1 ? `${rIscoRetro.toFixed(4)} M` : `${rIscoRetro.toFixed(3)} (${(rIscoRetro / mass).toFixed(3)}M)`}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p className="text-[11px] text-[var(--muted)] font-sans italic leading-tight">
        {"All characteristic radii scale strictly linearly with mass M (r(M) = M · r_1). At the non-rotating Schwarzschild endpoint (χ = 0), prograde and retrograde branches coalesce with exact equality: r_ph(pro) = r_ph(retro) = 3M, r_ISCO(pro) = r_ISCO(retro) = 6M, and r_+ = 2M, r_- = 0M. For non-zero subextremal spins (0 < χ < 1), frame dragging splits the branches into strict inequalities (r_+ < r_ph(pro) < 3M < r_ph(retro) and r_ph(pro) < r_ISCO(pro) < 6M < r_ISCO(retro)). At the polar axis (θ = 0°), r_ergo(0) ≡ r_+ = M(1 + √(1 - χ²)) identically for all spins, while at the equator (θ = 90°), r_ergo(π/2) ≡ 2M identically."}
      </p>
    </div>
  );
}

export default function MathematicsPage() {
  const [activeSection, setActiveSection] = useState("foundations");

  return (
    <div className="flex flex-col flex-1 pb-24">
      {/* Editorial Header */}
      <div className="border-b border-[var(--border)] py-8 px-4 sm:px-6 lg:px-8 bg-[var(--surface)]">
        <div className="mx-auto max-w-5xl">
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-[3px] border border-[var(--border)] bg-[var(--surface-subtle)] text-xs font-mono text-[var(--foreground-secondary)] mb-3">
            <span>Kerr Spacetime Family</span>
            <span className="text-[var(--border)]">·</span>
            <span>Boyer-Lindquist Chart</span>
            <span className="text-[var(--border)]">·</span>
            <span>Canonical Hamiltonian</span>
            <span className="text-[var(--border)]">·</span>
            <span>DOP853 Stepper</span>
          </div>

          <h1 className="font-serif text-3xl sm:text-4xl font-normal text-[var(--foreground)] tracking-tight">
            Mathematics Lab: Hamiltonian Geodesics in Kerr Spacetime
          </h1>
          <p className="text-sm sm:text-base text-[var(--foreground-secondary)] font-sans mt-2 max-w-3xl leading-relaxed">
            The rigorous mathematical framework of the Kerr Geodesic Integrator. Derivations of the 8D canonical Hamiltonian vector field, Boyer-Lindquist metric geometry, Carter constant invariance, separated effective potentials, and high-order numerical integration schemes.
          </p>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-6 pt-4 border-t border-[var(--border)]">
            <div className="space-y-0.5">
              <span className="text-[10px] font-mono uppercase tracking-wider text-[var(--muted)]">Spacetime Metric</span>
              <p className="text-xs font-mono font-medium text-[var(--foreground)]">Kerr (M, a) / Boyer-Lindquist</p>
            </div>
            <div className="space-y-0.5">
              <span className="text-[10px] font-mono uppercase tracking-wider text-[var(--muted)]">Phase Space</span>
              <p className="text-xs font-mono font-medium text-[var(--foreground)]">8D (t, r, θ, ϕ, p_t, p_r, p_θ, p_ϕ)</p>
            </div>
            <div className="space-y-0.5">
              <span className="text-[10px] font-mono uppercase tracking-wider text-[var(--muted)]">Conserved Invariants</span>
              <p className="text-xs font-mono font-medium text-[var(--foreground)]">E, L_z, Q, μ² = -2H</p>
            </div>
            <div className="space-y-0.5">
              <span className="text-[10px] font-mono uppercase tracking-wider text-[var(--muted)]">Numerical Engine</span>
              <p className="text-xs font-mono font-medium text-[var(--accent)]">DOP853 (8th-Order RK)</p>
            </div>
          </div>
        </div>
      </div>

      {/* Sticky Table of Contents Subnav */}
      <div className="sticky top-0 z-20 border-b border-[var(--border)] bg-[var(--surface)]/95 backdrop-blur-sm px-4 sm:px-6 lg:px-8 py-2.5">
        <div className="mx-auto max-w-5xl flex items-center justify-between gap-4">
          <div className="flex items-center gap-1 overflow-x-auto no-scrollbar py-0.5 text-xs font-sans">
            {SECTIONS.map((sec) => (
              <a
                key={sec.id}
                href={`#${sec.id}`}
                onClick={() => setActiveSection(sec.id)}
                className={`px-2.5 py-1 rounded-[2px] whitespace-nowrap transition-colors cursor-pointer ${
                  activeSection === sec.id
                    ? "bg-[var(--surface-subtle)] text-[var(--accent)] font-medium border border-[var(--border)]"
                    : "text-[var(--muted)] hover:text-[var(--foreground)]"
                }`}
              >
                {sec.short}
              </a>
            ))}
          </div>

          <Link
            href="/explorer"
            className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1 rounded-[3px] bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white text-xs font-sans font-medium transition-colors shrink-0 shadow-xs"
          >
            <Compass className="h-3.5 w-3.5" />
            <span>Launch Explorer</span>
          </Link>
        </div>
      </div>

      {/* Main Content Body */}
      <div className="mx-auto max-w-5xl w-full px-4 sm:px-6 lg:px-8 mt-10 space-y-16">
        {/* ========================================================================= */}
        {/* SECTION 1: GEOMETRIC FOUNDATIONS */}
        {/* ========================================================================= */}
        <section id="foundations" className="space-y-5 scroll-mt-20">
          <div className="border-b border-[var(--border)] pb-2 flex items-center justify-between">
            <h2 className="font-serif text-2xl font-normal text-[var(--foreground)] tracking-tight">
              1. Geometric Foundations &amp; Boyer-Lindquist Coordinates
            </h2>
            <span className="font-mono text-xs text-[var(--muted)]">Section 01</span>
          </div>

          <p className="text-sm text-[var(--foreground-secondary)] leading-relaxed">
            The Kerr solution to Einstein&apos;s vacuum field equations represents the exterior spacetime of an uncharged, stationary, axisymmetric rotating black hole. We formulate all geometric quantities in standard <strong>Boyer-Lindquist coordinates</strong> <MathBlock math="x^\mu = (t, r, \theta, \phi)" display={false} /> in geometrized units where <MathBlock math="G = c = 1" display={false} /> with metric signature <MathBlock math="(-, +, +, +)" display={false} />.
          </p>

          <p className="text-sm text-[var(--foreground-secondary)] leading-relaxed">
            The global spacetime geometry is parameterized by two fundamental physical constants: the ADM mass <MathBlock math="M > 0" display={false} /> and the signed specific angular momentum (spin parameter) <MathBlock math="a \equiv J/M \in [-M, M]" display={false} />. Positive <MathBlock math="a > 0" display={false} /> denotes prograde rotation relative to increasing azimuthal angle <MathBlock math="\phi" display={false} />, while <MathBlock math="a < 0" display={false} /> represents retrograde rotation.
          </p>

          <div className="space-y-3">
            <h3 className="font-serif text-lg text-[var(--foreground)]">Auxiliary Metric Functions</h3>
            <p className="text-sm text-[var(--foreground-secondary)]">
              To express the metric components compactly, we introduce four standard auxiliary functions:
            </p>

            <CopyableEquation
              label="Auxiliary Metric Functions"
              math="\begin{aligned}
\Sigma(r, \theta) &\equiv r^2 + a^2 \cos^2\theta \\
\Delta(r) &\equiv r^2 - 2Mr + a^2 = (r - r_+)(r - r_-) \\
A(r, \theta) &\equiv (r^2 + a^2)^2 - a^2 \Delta(r) \sin^2\theta \\
\Pi(r, \theta) &\equiv \Sigma(r, \theta)\,\Delta(r)
\end{aligned}"
            />
          </div>

          <div className="space-y-3">
            <h3 className="font-serif text-lg text-[var(--foreground)]">Metric Line Element</h3>
            <p className="text-sm text-[var(--foreground-secondary)]">
              The invariant spacetime interval <MathBlock math="ds^2 = g_{\mu\nu} dx^\mu dx^\nu" display={false} /> takes the form:
            </p>

            <CopyableEquation
              label="Boyer-Lindquist Line Element"
              math="ds^2 = -\left(1 - \frac{2Mr}{\Sigma}\right) dt^2 - \frac{4Mar\sin^2\theta}{\Sigma}\,dt\,d\phi + \frac{\Sigma}{\Delta}\,dr^2 + \Sigma\,d\theta^2 + \frac{A\sin^2\theta}{\Sigma}\,d\phi^2"
            />

            <p className="text-sm text-[var(--foreground-secondary)] leading-relaxed">
              The non-zero components of the symmetric covariant metric tensor <MathBlock math="g_{\mu\nu}" display={false} /> are:
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono">
              <div className="p-2.5 rounded-[3px] border border-[var(--border)] bg-[var(--surface-subtle)]">
                <span className="text-[var(--accent)] font-semibold">g_tt = -(1 - 2Mr/Σ)</span>
                <p className="text-[11px] text-[var(--muted)] font-sans mt-0.5">Stationary time lapse component</p>
              </div>
              <div className="p-2.5 rounded-[3px] border border-[var(--border)] bg-[var(--surface-subtle)]">
                <span className="text-[var(--accent)] font-semibold">g_tϕ = -2Mar sin²θ / Σ</span>
                <p className="text-[11px] text-[var(--muted)] font-sans mt-0.5">Off-diagonal frame-dragging cross term</p>
              </div>
              <div className="p-2.5 rounded-[3px] border border-[var(--border)] bg-[var(--surface-subtle)]">
                <span className="text-[var(--accent)] font-semibold">g_rr = Σ / Δ</span>
                <p className="text-[11px] text-[var(--muted)] font-sans mt-0.5">Radial scale factor; singular at Δ = 0</p>
              </div>
              <div className="p-2.5 rounded-[3px] border border-[var(--border)] bg-[var(--surface-subtle)]">
                <span className="text-[var(--accent)] font-semibold">g_θθ = Σ, g_ϕϕ = (A sin²θ) / Σ</span>
                <p className="text-[11px] text-[var(--muted)] font-sans mt-0.5">Polar and azimuthal angular components</p>
              </div>
            </div>
          </div>

          <div className="space-y-3">
            <h3 className="font-serif text-lg text-[var(--foreground)]">Metric Determinant Identity</h3>
            <p className="text-sm text-[var(--foreground-secondary)]">
              Because <MathBlock math="g_{\mu\nu}" display={false} /> blocks into a <MathBlock math="2\times 2" display={false} /> <MathBlock math="(t, \phi)" display={false} /> block and two diagonal terms <MathBlock math="g_{rr}, g_{\theta\theta}" display={false} />, the exact 4-volume metric determinant evaluates identically to:
            </p>

            <CopyableEquation
              label="Exact 4D Metric Determinant"
              math="\det(g_{\mu\nu}) = (g_{tt} g_{\phi\phi} - g_{t\phi}^2)\,g_{rr}\,g_{\theta\theta} = (-\Delta \sin^2\theta)\left(\frac{\Sigma}{\Delta}\right)\Sigma = -\Sigma^2 \sin^2\theta \implies \sqrt{-g} = \Sigma \sin\theta"
            />
            <p className="text-xs text-[var(--muted)] font-sans">
              This determinant identity is completely independent of <MathBlock math="\Delta(r)" display={false} /> and guarantees that the volume form remains regular everywhere outside coordinate poles.
            </p>
          </div>

          <div className="space-y-3">
            <h3 className="font-serif text-lg text-[var(--foreground)]">Horizons, Ergosphere, and Singularities</h3>
            <p className="text-sm text-[var(--foreground-secondary)] leading-relaxed">
              The roots of <MathBlock math="\Delta(r) = 0" display={false} /> locate the coordinate event horizons:
            </p>
            <MathBlock
              math="r_\pm = M \pm \sqrt{M^2 - a^2} \quad (|a| \le M)"
              display={true}
            />
            <p className="text-sm text-[var(--foreground-secondary)] leading-relaxed">
              where <MathBlock math="r_+" display={false} /> is the <strong>outer event horizon</strong> and <MathBlock math="r_-" display={false} /> is the <strong>inner Cauchy horizon</strong>. At <MathBlock math="r = r_+" display={false} />, <MathBlock math="g_{rr} \to \infty" display={false} />, which is a coordinate singularity of the Boyer-Lindquist chart, while the curvature invariants (such as the Kretschmann scalar <MathBlock math="K = R^{\alpha\beta\gamma\delta} R_{\alpha\beta\gamma\delta}" display={false} />) remain completely finite.
            </p>

            <p className="text-sm text-[var(--foreground-secondary)] leading-relaxed">
              The <strong>ergosphere boundary</strong> (the static limit surface) is defined by the condition <MathBlock math="g_{tt}(r, \theta) = 0" display={false} />:
            </p>
            <MathBlock
              math="r_{\rm ergo}(\theta) = M + \sqrt{M^2 - a^2 \cos^2\theta}"
              display={true}
            />
            <p className="text-sm text-[var(--foreground-secondary)] leading-relaxed">
              Between <MathBlock math="r_+" display={false} /> and <MathBlock math="r_{\rm ergo}(\theta)" display={false} /> lies the <strong>ergoregion</strong>. Inside this region, <MathBlock math="g_{tt} > 0" display={false} />, meaning that the asymptotic time-translation Killing vector <MathBlock math="\partial_t" display={false} /> becomes spacelike. Consequently, no physical observer can remain stationary with respect to asymptotic infinity: all physical matter and photons are forced to co-rotate with the black hole (<MathBlock math="d\phi/d\lambda > 0" display={false} />).
            </p>
          </div>

          {/* Interactive Spacetime Diagram Widget */}
          <SpacetimeDiagram />

          <div className="rounded-[3px] border border-[var(--border)] bg-[var(--surface-subtle)] p-4 text-xs font-sans space-y-2">
            <div className="font-mono text-xs font-semibold text-[var(--foreground)] uppercase tracking-wider flex items-center gap-1.5">
              <Info className="h-3.5 w-3.5 text-[var(--accent)]" />
              <span>Schwarzschild Limit (a → 0)</span>
            </div>
            <p className="text-[var(--foreground-secondary)] leading-relaxed">
              In the non-rotating limit <MathBlock math="a = 0" display={false} />, we have <MathBlock math="\Sigma = r^2" display={false} />, <MathBlock math="\Delta = r(r - 2M)" display={false} />, and <MathBlock math="g_{t\phi} \equiv 0" display={false} />. The ergosphere collapses into the event horizon <MathBlock math="r_{\rm ergo}(\theta) = r_+ = 2M" display={false} />, the inner horizon recedes to <MathBlock math="r_- = 0" display={false} />, and the line element reduces to standard Schwarzschild geometry:
            </p>
            <MathBlock
              math="ds^2 = -\left(1 - \frac{2M}{r}\right)dt^2 + \left(1 - \frac{2M}{r}\right)^{-1}dr^2 + r^2 d\theta^2 + r^2 \sin^2\theta\,d\phi^2"
              display={true}
            />
          </div>
        </section>

        {/* ========================================================================= */}
        {/* SECTION 2: HAMILTONIAN FORMULATION */}
        {/* ========================================================================= */}
        <section id="hamiltonian" className="space-y-5 scroll-mt-20">
          <div className="border-b border-[var(--border)] pb-2 flex items-center justify-between">
            <h2 className="font-serif text-2xl font-normal text-[var(--foreground)] tracking-tight">
              2. Canonical Hamiltonian Formulation in Phase Space
            </h2>
            <span className="font-mono text-xs text-[var(--muted)]">Section 02</span>
          </div>

          <p className="text-sm text-[var(--foreground-secondary)] leading-relaxed">
            Rather than integrating second-order geodesic equations with Christoffel symbols <MathBlock math="\ddot{x}^\mu + \Gamma^\mu_{\alpha\beta} \dot{x}^\alpha \dot{x}^\beta = 0" display={false} /> (which require 40 connection coefficients), the Kerr Geodesic Integrator formulates geodesic trajectories as an 8-dimensional first-order canonical Hamiltonian dynamical system.
          </p>

          <div className="space-y-3">
            <h3 className="font-serif text-lg text-[var(--foreground)]">Phase-Space State Ordering</h3>
            <p className="text-sm text-[var(--foreground-secondary)] leading-relaxed">
              The continuous phase space consists of four contravariant spacetime coordinates <MathBlock math="x^\mu = (t, r, \theta, \phi)" display={false} /> and four covariant canonical conjugate momenta <MathBlock math="p_\mu = (p_t, p_r, p_\theta, p_\phi)" display={false} />. The state vector <MathBlock math="y \in \mathbb{R}^8" display={false} /> is ordered strictly as:
            </p>

            <CopyableEquation
              label="Canonical 8D State Ordering"
              math="y = \begin{pmatrix} x^0 \\ x^1 \\ x^2 \\ x^3 \\ p_0 \\ p_1 \\ p_2 \\ p_3 \end{pmatrix} = \begin{pmatrix} t \\ r \\ \theta \\ \phi \\ p_t \\ p_r \\ p_\theta \\ p_\phi \end{pmatrix} \in \mathbb{R}^8"
            />
          </div>

          <div className="space-y-3">
            <h3 className="font-serif text-lg text-[var(--foreground)]">The Super-Hamiltonian &amp; Mass-Shell Constraint</h3>
            <p className="text-sm text-[var(--foreground-secondary)] leading-relaxed">
              The super-Hamiltonian governing test particle motion in curved spacetime is defined as:
            </p>

            <CopyableEquation
              label="Canonical Geodesic Super-Hamiltonian"
              math="\mathcal{H}(x^\mu, p_\mu) = \frac{1}{2} g^{\mu\nu}(x) p_\mu p_\nu"
            />

            <p className="text-sm text-[var(--foreground-secondary)] leading-relaxed">
              The value of <MathBlock math="\mathcal{H}" display={false} /> is governed by the invariant particle rest mass <MathBlock math="\mu \ge 0" display={false} /> via the mass-shell relation:
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono">
              <div className="p-3 rounded-[3px] border border-[var(--border)] bg-[var(--surface-subtle)] space-y-1">
                <span className="text-[var(--accent)] font-semibold">Timelike Particles (μ = 1)</span>
                <MathBlock math="\mathcal{H} = -\frac{1}{2}\mu^2 = -\frac{1}{2}" display={false} />
                <p className="text-[11px] text-[var(--muted)] font-sans">
                  Affine parameter <MathBlock math="\lambda = \tau" display={false} /> represents the proper time of the massive test particle.
                </p>
              </div>

              <div className="p-3 rounded-[3px] border border-[var(--border)] bg-[var(--surface-subtle)] space-y-1">
                <span className="text-[var(--accent)] font-semibold">Null Photons (μ = 0)</span>
                <MathBlock math="\mathcal{H} = 0 \quad (\text{Null Constraint})" display={false} />
                <p className="text-[11px] text-[var(--muted)] font-sans">
                  Trajectory lies strictly on the light cone. Monitored continuously during numerical integration.
                </p>
              </div>
            </div>
          </div>

          <div className="space-y-3">
            <h3 className="font-serif text-lg text-[var(--foreground)]">Contravariant Inverse Metric Tensor</h3>
            <p className="text-sm text-[var(--foreground-secondary)] leading-relaxed">
              The inverse metric <MathBlock math="g^{\mu\nu}" display={false} /> satisfies <MathBlock math="g^{\mu\alpha} g_{\alpha\nu} = \delta^\mu_{\ \nu}" display={false} />. Evaluating the <MathBlock math="2\times 2" display={false} /> block inverse in the <MathBlock math="(t, \phi)" display={false} /> sector yields:
            </p>

            <CopyableEquation
              label="Exact Inverse Metric Tensor Components"
              math="\begin{aligned}
g^{tt} &= -\frac{A(r, \theta)}{\Sigma(r, \theta)\,\Delta(r)} \\
g^{t\phi} &= g^{\phi t} = -\frac{2Mar}{\Sigma(r, \theta)\,\Delta(r)} \\
g^{rr} &= \frac{\Delta(r)}{\Sigma(r, \theta)} \\
g^{\theta\theta} &= \frac{1}{\Sigma(r, \theta)} \\
g^{\phi\phi} &= \frac{\Delta(r) - a^2\sin^2\theta}{\Sigma(r, \theta)\,\Delta(r)\sin^2\theta} = \frac{1}{\Sigma\sin^2\theta} - \frac{a^2}{\Sigma\Delta}
\end{aligned}"
            />
          </div>

          <div className="space-y-3">
            <h3 className="font-serif text-lg text-[var(--foreground)]">Hamilton&apos;s Canonical Equations of Motion</h3>
            <p className="text-sm text-[var(--foreground-secondary)] leading-relaxed">
              The continuous first-order Hamilton equations are:
            </p>

            <CopyableEquation
              label="Canonical Hamilton Equations"
              math="\begin{aligned}
\frac{dx^\mu}{d\lambda} &= \frac{\partial \mathcal{H}}{\partial p_\mu} = g^{\mu\nu}(x)\,p_\nu \\
\frac{dp_\mu}{d\lambda} &= -\frac{\partial \mathcal{H}}{\partial x^\mu} = -\frac{1}{2}\left(\frac{\partial g^{\alpha\beta}}{\partial x^\mu}\right) p_\alpha p_\beta
\end{aligned}"
            />

            <p className="text-sm text-[var(--foreground-secondary)] leading-relaxed">
              Notice that because <MathBlock math="\mathcal{H}" display={false} /> is strictly a homogeneous quadratic polynomial in momenta <MathBlock math="p_\mu" display={false} />, the velocity equations <MathBlock math="\dot{x}^\mu = g^{\mu\nu} p_\nu" display={false} /> are linear in momenta. Stationarity (<MathBlock math="\partial_t g^{\alpha\beta} = 0" display={false} />) and axisymmetry (<MathBlock math="\partial_\phi g^{\alpha\beta} = 0" display={false} />) immediately guarantee that <MathBlock math="\dot{p}_t = 0" display={false} /> and <MathBlock math="\dot{p}_\phi = 0" display={false} />, leaving only radial and polar derivatives to evaluate!
            </p>
          </div>
        </section>

        {/* ========================================================================= */}
        {/* SECTION 3: SYMMETRIES & CONSERVED QUANTITIES */}
        {/* ========================================================================= */}
        <section id="symmetries" className="space-y-5 scroll-mt-20">
          <div className="border-b border-[var(--border)] pb-2 flex items-center justify-between">
            <h2 className="font-serif text-2xl font-normal text-[var(--foreground)] tracking-tight">
              3. Symmetries, Killing Tensors, and Conserved Quantities
            </h2>
            <span className="font-mono text-xs text-[var(--muted)]">Section 03</span>
          </div>

          <p className="text-sm text-[var(--foreground-secondary)] leading-relaxed">
            By Noether&apos;s theorem, every continuous isometry of the metric generated by a Killing vector field <MathBlock math="\xi^\mu" display={false} /> (satisfying Killing&apos;s equation <MathBlock math="\nabla_{(\mu}\xi_{\nu)} = 0" display={false} />) generates a first integral of geodesic motion <MathBlock math="C = \xi^\mu p_\mu = \text{const}" display={false} />.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="rounded-[3px] border border-[var(--border)] bg-[var(--surface-subtle)] p-4 space-y-2">
              <span className="font-mono text-xs font-semibold text-[var(--accent)] uppercase tracking-wider">
                Stationarity Symmetry: Energy E
              </span>
              <p className="text-xs text-[var(--foreground-secondary)] leading-relaxed">
                The Kerr metric components are independent of coordinate time <MathBlock math="t" display={false} /> (<MathBlock math="\partial_t g_{\mu\nu} \equiv 0" display={false} />). The time-translation Killing vector is <MathBlock math="\xi_{(t)}^\mu = \delta^\mu_t" display={false} />, yielding conserved specific energy:
              </p>
              <MathBlock math="E \equiv -p_t = -p_0 = \text{constant}" display={true} />
            </div>

            <div className="rounded-[3px] border border-[var(--border)] bg-[var(--surface-subtle)] p-4 space-y-2">
              <span className="font-mono text-xs font-semibold text-[var(--accent)] uppercase tracking-wider">
                Axisymmetry: Axial Angular Momentum L_z
              </span>
              <p className="text-xs text-[var(--foreground-secondary)] leading-relaxed">
                The Kerr metric components are independent of azimuth <MathBlock math="\phi" display={false} /> (<MathBlock math="\partial_\phi g_{\mu\nu} \equiv 0" display={false} />). The rotational Killing vector is <MathBlock math="\xi_{(\phi)}^\mu = \delta^\mu_\phi" display={false} />, yielding conserved axial angular momentum:
              </p>
              <MathBlock math="L_z \equiv p_\phi = p_3 = \text{constant}" display={true} />
            </div>
          </div>

          <div className="space-y-3">
            <h3 className="font-serif text-lg text-[var(--foreground)]">Carter Constant (Q) &amp; The Second-Order Killing Tensor</h3>
            <p className="text-sm text-[var(--foreground-secondary)] leading-relaxed">
              Because Kerr spacetime is only axisymmetric (not spherically symmetric), total 3D angular momentum <MathBlock math="\mathbf{L}^2" display={false} /> is not conserved. In 1968, Brandon Carter discovered that the Hamilton-Jacobi equation in Kerr spacetime is completely separable, revealing a fourth hidden constant of motion associated with a symmetric rank-2 Killing tensor <MathBlock math="K_{\mu\nu}" display={false} /> satisfying <MathBlock math="\nabla_{(\sigma} K_{\mu\nu)} = 0" display={false} />.
            </p>

            <p className="text-sm text-[var(--foreground-secondary)] leading-relaxed">
              The separation constant <MathBlock math="\mathcal{K}" display={false} /> evaluates from the polar sector as:
            </p>
            <MathBlock
              math="\mathcal{K} \equiv p_\theta^2 + \left(\frac{L_z}{\sin\theta} - aE\sin\theta\right)^2 + a^2 \mu^2 \cos^2\theta"
              display={true}
            />

            <p className="text-sm text-[var(--foreground-secondary)] leading-relaxed">
              In the authoritative convention of this project, the <strong>Carter constant</strong> <MathBlock math="\mathcal{Q}" display={false} /> is defined by subtracting <MathBlock math="(L_z - aE)^2" display={false} /> from the separation constant:
            </p>

            <CopyableEquation
              label="Carter Constant Definition (Project Convention)"
              math="\boxed{\mathcal{Q} \equiv \mathcal{K} - (L_z - aE)^2 = p_\theta^2 + \cos^2\theta\left[a^2(\mu^2 - E^2) + \frac{L_z^2}{\sin^2\theta}\right]}"
            />

            <div className="rounded-[3px] border border-[var(--border)] bg-[var(--surface-subtle)] p-4 text-xs font-sans space-y-2">
              <span className="font-mono text-xs font-semibold text-[var(--foreground)] uppercase tracking-wider">
                Key Mathematical Properties of Q:
              </span>
              <ul className="list-disc list-inside space-y-1.5 text-[var(--foreground-secondary)]">
                <li>
                  <strong>Equatorial Motion Invariance:</strong> For motion confined to the equatorial plane (<MathBlock math="\theta = \pi/2, p_\theta = 0" display={false} />), we have <MathBlock math="\cos(\pi/2) = 0" display={false} />, which yields <MathBlock math="\mathcal{Q} \equiv 0" display={false} /> identically for all equatorial orbits regardless of mass, energy, or spin!
                </li>
                <li>
                  <strong>Schwarzschild Limit (a → 0):</strong> As <MathBlock math="a \to 0" display={false} />, <MathBlock math="\mathcal{Q}_{a=0} = p_\theta^2 + L_z^2 \cot^2\theta = L^2 - L_z^2 = L_x^2 + L_y^2" display={false} />. The Carter constant reduces to the squared magnitude of the transverse angular momentum orthogonal to the polar axis.
                </li>
                <li>
                  <strong>Spin-Reversal Parity:</strong> Because the spin parameter enters the polar expression exclusively as <MathBlock math="a^2" display={false} />, <MathBlock math="\mathcal{Q}(-a) = \mathcal{Q}(a)" display={false} />. The Carter constant is strictly even under spin reversal at fixed phase-space coordinates.
                </li>
                <li>
                  <strong>Independent Radial Representation:</strong> The Carter constant can also be computed entirely from the radial coordinates:
                  <MathBlock math="\mathcal{Q}_{\rm radial} = \frac{\left[(r^2 + a^2)E - a L_z\right]^2}{\Delta(r)} - \Delta(r) p_r^2 - \mu^2 r^2 - (L_z - aE)^2" display={true} />
                  Evaluating both channels provides a rigorous consistency check: for an exact constraint-satisfying state point, the polar and radial expressions agree algebraically to double-precision roundoff (<MathBlock math="|\mathcal{Q}_{\rm polar} - \mathcal{Q}_{\rm radial}| \le 10^{-12}" display={false} />). Along dynamically integrated numerical trajectories, accumulated floating-point roundoff across all 8 phase-space coordinates is verified in automated regression tests to satisfy <MathBlock math="\max |\mathcal{Q}_{\rm polar} - \mathcal{Q}_{\rm radial}| \le 10^{-7}" display={false} />.
                </li>
              </ul>
            </div>
          </div>
        </section>

        {/* ========================================================================= */}
        {/* SECTION 4: SEPARATED GEODESIC EQUATIONS */}
        {/* ========================================================================= */}
        <section id="separated" className="space-y-5 scroll-mt-20">
          <div className="border-b border-[var(--border)] pb-2 flex items-center justify-between">
            <h2 className="font-serif text-2xl font-normal text-[var(--foreground)] tracking-tight">
              4. Separated Geodesic Equations &amp; Effective Potentials
            </h2>
            <span className="font-mono text-xs text-[var(--muted)]">Section 04</span>
          </div>

          <p className="text-sm text-[var(--foreground-secondary)] leading-relaxed">
            By applying Carter&apos;s separability ansatz to the Hamilton-Jacobi action <MathBlock math="S = \frac{1}{2}\mu^2\lambda - Et + L_z\phi + S_r(r) + S_\theta(\theta)" display={false} />, the equations of motion decouple into four first-order quadratures:
          </p>

          <CopyableEquation
            label="Carter Separated First-Order Equations"
            math="\begin{aligned}
\Sigma \frac{dr}{d\lambda} &= \pm \sqrt{R(r)} \\
\Sigma \frac{d\theta}{d\lambda} &= \pm \sqrt{\Theta(\theta)} \\
\Sigma \frac{d\phi}{d\lambda} &= -\left(aE - \frac{L_z}{\sin^2\theta}\right) + \frac{a}{\Delta(r)}\left[E(r^2 + a^2) - aL_z\right] \\
\Sigma \frac{dt}{d\lambda} &= -a(aE\sin^2\theta - L_z) + \frac{r^2 + a^2}{\Delta(r)}\left[E(r^2 + a^2) - aL_z\right]
\end{aligned}"
          />

          <div className="space-y-3">
            <h3 className="font-serif text-lg text-[var(--foreground)]">Radial and Polar Effective Potentials</h3>
            <p className="text-sm text-[var(--foreground-secondary)] leading-relaxed">
              The functions <MathBlock math="R(r)" display={false} /> and <MathBlock math="\Theta(\theta)" display={false} /> govern the kinematically allowed regions of motion:
            </p>

            <CopyableEquation
              label="Radial Potential R(r) and Polar Potential Θ(θ)"
              math="\begin{aligned}
R(r) &= \left[E(r^2 + a^2) - aL_z\right]^2 - \Delta(r)\left[\mu^2 r^2 + (L_z - aE)^2 + \mathcal{Q}\right] \\
\Theta(\theta) &= \mathcal{Q} - \cos^2\theta\left[a^2(\mu^2 - E^2) + \frac{L_z^2}{\sin^2\theta}\right]
\end{aligned}"
            />

            <p className="text-sm text-[var(--foreground-secondary)] leading-relaxed">
              Physical geodesics are restricted to regions where <MathBlock math="R(r) \ge 0" display={false} /> and <MathBlock math="\Theta(\theta) \ge 0" display={false} />.
            </p>
          </div>

          <div className="space-y-3">
            <h3 className="font-serif text-lg text-[var(--foreground)]">Turning Points, Circular Orbits, and Stability</h3>
            <p className="text-sm text-[var(--foreground-secondary)] leading-relaxed">
              The roots of the radial potential <MathBlock math="R(r)" display={false} /> classify orbital morphology:
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs font-mono">
              <div className="p-3 rounded-[3px] border border-[var(--border)] bg-[var(--surface-subtle)] space-y-1">
                <span className="text-[var(--accent)] font-semibold">Radial Turning Point</span>
                <MathBlock math="R(r_t) = 0, \quad R'(r_t) \neq 0" display={false} />
                <p className="text-[11px] text-[var(--muted)] font-sans">
                  Radial velocity vanishes (<MathBlock math="dr/d\lambda = 0" display={false} />). The particle reverses radial direction between periapsis and apoapsis.
                </p>
              </div>

              <div className="p-3 rounded-[3px] border border-[var(--border)] bg-[var(--surface-subtle)] space-y-1">
                <span className="text-[var(--accent)] font-semibold">Circular Orbit</span>
                <MathBlock math="R(r_c) = 0, \quad \frac{dR}{dr}(r_c) = 0" display={false} />
                <p className="text-[11px] text-[var(--muted)] font-sans">
                  Particle remains at constant radius <MathBlock math="r_c" display={false} /> for all affine parameter <MathBlock math="\lambda" display={false} />.
                </p>
              </div>

              <div className="p-3 rounded-[3px] border border-[var(--border)] bg-[var(--surface-subtle)] space-y-1">
                <span className="text-[var(--accent)] font-semibold">Marginally Stable (ISCO)</span>
                <MathBlock math="R(r) = R'(r) = R''(r) = 0" display={false} />
                <p className="text-[11px] text-[var(--muted)] font-sans">
                  Inflection point marking the boundary between stable bound circular orbits and catastrophic plunge into the horizon.
                </p>
              </div>
            </div>
          </div>

          <div className="rounded-[4px] border border-[var(--border)] bg-[var(--surface)] p-4 space-y-2">
            <h4 className="font-serif text-base text-[var(--foreground)] flex items-center gap-2">
              <BookOpen className="h-4 w-4 text-[var(--accent)]" />
              <span>Architectural Rationale: Why Integrate the Canonical 8D System?</span>
            </h4>
            <p className="text-xs text-[var(--foreground-secondary)] leading-relaxed font-sans">
              While Carter&apos;s first-order equations are invaluable for analytical classification, turning points present a formidable numerical obstacle for direct integration of <MathBlock math="\dot{r} = \pm \sqrt{R(r)}/\Sigma" display={false} />. At a turning point, <MathBlock math="R(r) \to 0" display={false} />, causing the square root derivative <MathBlock math="d(\sqrt{R})/dr \to \infty" display={false} /> to diverge, requiring branch-tracking sign logic that frequently stalls numerical steppers.
            </p>
            <p className="text-xs text-[var(--foreground-secondary)] leading-relaxed font-sans">
              In contrast, the <strong>canonical 8D Hamiltonian ODE system</strong> <MathBlock math="\dot{y} = J \nabla \mathcal{H}" display={false} /> implemented in our Python engine is completely smooth, single-valued, and analytic everywhere on the manifold outside the horizon. Turning points correspond simply to smooth zero-crossings of <MathBlock math="p_r = 0" display={false} /> and are integrated cleanly with standard high-order Runge-Kutta steppers without heuristic branch cuts.
            </p>
          </div>
        </section>

        {/* ========================================================================= */}
        {/* SECTION 5: IMPORTANT PHYSICAL ORBITS */}
        {/* ========================================================================= */}
        <section id="orbits" className="space-y-5 scroll-mt-20">
          <div className="border-b border-[var(--border)] pb-2 flex items-center justify-between">
            <h2 className="font-serif text-2xl font-normal text-[var(--foreground)] tracking-tight">
              5. Important Physical Orbits in Black Hole Spacetimes
            </h2>
            <span className="font-mono text-xs text-[var(--muted)]">Section 05</span>
          </div>

          <div className="space-y-3">
            <h3 className="font-serif text-lg text-[var(--foreground)]">1. Schwarzschild Circular Orbits &amp; The ISCO (6M)</h3>
            <p className="text-sm text-[var(--foreground-secondary)] leading-relaxed">
              In non-rotating Schwarzschild spacetime, equatorial timelike motion (<MathBlock math="\mu = 1" display={false} />) reduces to the 1D radial effective potential:
            </p>
            <MathBlock
              math="V_{\rm eff}(r) = \left(1 - \frac{2M}{r}\right)\left(1 + \frac{L^2}{r^2}\right)"
              display={true}
            />
            <p className="text-sm text-[var(--foreground-secondary)] leading-relaxed">
              Setting <MathBlock math="V_{\rm eff}'(r) = 0" display={false} /> yields the radii of circular orbits:
            </p>
            <MathBlock
              math="r_{\rm circ} = \frac{L^2 \pm \sqrt{L^4 - 12M^2 L^2}}{2M}"
              display={true}
            />
            <p className="text-sm text-[var(--foreground-secondary)] leading-relaxed">
              Real solutions exist only when <MathBlock math="L^2 \ge 12M^2" display={false} />. The marginal case <MathBlock math="L^2 = 12M^2" display={false} /> defines the <strong>Innermost Stable Circular Orbit (ISCO)</strong>:
            </p>
            <MathBlock
              math="\boxed{r_{\rm ISCO} = 6M \quad (\text{Schwarzschild Timelike ISCO})}"
              display={true}
            />
            <p className="text-xs text-[var(--muted)] font-sans">
              For <MathBlock math="r < 6M" display={false} />, circular orbits are unstable; test particles plunge inward toward the event horizon.
            </p>
          </div>

          <div className="space-y-3">
            <h3 className="font-serif text-lg text-[var(--foreground)]">2. The Photon Sphere (3M) &amp; Kerr Photon Orbit Splitting</h3>
            <p className="text-sm text-[var(--foreground-secondary)] leading-relaxed">
              For massless null geodesics (<MathBlock math="\mu = 0" display={false} />) in Schwarzschild geometry, the circular photon orbit occurs at:
            </p>
            <MathBlock
              math="\boxed{r_{\rm ph} = 3M \quad (\text{Schwarzschild Photon Sphere})}"
              display={true}
            />
            <p className="text-sm text-[var(--foreground-secondary)] leading-relaxed">
              The corresponding critical impact parameter is <MathBlock math="b_c \equiv L_z / E = 3\sqrt{3}M \approx 5.196M" display={false} />. Any incoming photon with impact parameter <MathBlock math="b < b_c" display={false} /> crosses the photon sphere and is captured into the black hole horizon.
            </p>

            <p className="text-sm text-[var(--foreground-secondary)] leading-relaxed">
              In Kerr spacetime, frame dragging drags spacetime in the direction of black hole rotation, breaking spherical symmetry and splitting equatorial photon orbits into distinct prograde (<MathBlock math="+" display={false} />) and retrograde (<MathBlock math="-" display={false} />) branches:
            </p>

            <CopyableEquation
              label="Kerr Equatorial Circular Photon Orbits"
              math="r_{\rm ph}^\pm = 2M\left\{1 + \cos\left[\frac{2}{3}\arccos\left(\mp \frac{a}{M}\right)\right]\right\}"
            />

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono">
              <div className="p-3 rounded-[3px] border border-[var(--border)] bg-[var(--surface-subtle)] space-y-1">
                <span className="text-[var(--accent)] font-semibold">Prograde Photon Orbit (r_ph+)</span>
                <p className="text-[11px] text-[var(--foreground-secondary)] font-sans">
                  Co-rotates with spin. Sits closer to the horizon: as <MathBlock math="a \to M" display={false} />, <MathBlock math="r_{\rm ph}^+ \to M" display={false} /> (approaching the outer event horizon).
                </p>
              </div>
              <div className="p-3 rounded-[3px] border border-[var(--border)] bg-[var(--surface-subtle)] space-y-1">
                <span className="text-[var(--accent)] font-semibold">Retrograde Photon Orbit (r_ph-)</span>
                <p className="text-[11px] text-[var(--foreground-secondary)] font-sans">
                  Counter-rotates against spin. Pushed outward by repulsive frame-dragging momentum: as <MathBlock math="a \to M" display={false} />, <MathBlock math="r_{\rm ph}^- \to 4M" display={false} />.
                </p>
              </div>
            </div>
          </div>

          <div className="space-y-3">
            <h3 className="font-serif text-lg text-[var(--foreground)]">3. Kerr Timelike ISCO Formula</h3>
            <p className="text-sm text-[var(--foreground-secondary)] leading-relaxed">
              The Innermost Stable Circular Orbit for timelike particles in the Kerr equatorial plane is given by the Bardeen-Press-Teukolsky (1972) formula:
            </p>

            <CopyableEquation
              label="Kerr Equatorial ISCO Radius"
              math="\begin{aligned}
r_{\rm ISCO}^\pm &= M\left\{3 + Z_2 \mp \sqrt{(3 - Z_1)(3 + Z_1 + 2Z_2)}\right\} \\
Z_1 &\equiv 1 + \left(1 - \frac{a^2}{M^2}\right)^{1/3}\left[\left(1 + \frac{a}{M}\right)^{1/3} + \left(1 - \frac{a}{M}\right)^{1/3}\right] \\
Z_2 &\equiv \sqrt{3\frac{a^2}{M^2} + Z_1^2}
\end{aligned}"
            />
            <p className="text-xs text-[var(--muted)] font-sans">
              For an extremal prograde black hole (<MathBlock math="a = M" display={false} />), <MathBlock math="r_{\rm ISCO}^+ = M" display={false} />, while for retrograde motion, <MathBlock math="r_{\rm ISCO}^- = 9M" display={false} />.
            </p>
          </div>

          <div className="space-y-3">
            <h3 className="font-serif text-lg text-[var(--foreground)]">4. Relativistic Scattering &amp; Logarithmic Whirl Dynamics</h3>
            <p className="text-sm text-[var(--foreground-secondary)] leading-relaxed">
              When a photon approaches from infinity with impact parameter <MathBlock math="b = L_z / E" display={false} /> close to the critical value <MathBlock math="b_{\rm crit}" display={false} />, the trajectory approaches the unstable circular photon orbit and executes multiple &quot;whirl&quot; revolutions before escaping or plunging.
            </p>
            <p className="text-sm text-[var(--foreground-secondary)] leading-relaxed">
              Near the separatrix, the total deflection angle <MathBlock math="\Delta\phi" display={false} /> diverges logarithmically:
            </p>
            <MathBlock
              math="\Delta\phi \sim -\ln|b - b_{\rm crit}| + \text{const}"
              display={true}
            />
            <p className="text-sm text-[var(--foreground-secondary)] leading-relaxed">
              and the affine dwell time scales inversely with the Lyapunov exponent <MathBlock math="\lambda_L" display={false} /> of the unstable photon orbit:
            </p>
            <MathBlock
              math="\Delta\lambda \approx \frac{1}{\lambda_L} \ln\left(\frac{1}{|b - b_{\rm crit}|}\right)"
              display={true}
            />
          </div>
        </section>

        {/* ========================================================================= */}
        {/* SECTION 6: NUMERICAL INTEGRATION & DIAGNOSTICS */}
        {/* ========================================================================= */}
        <section id="numerics" className="space-y-5 scroll-mt-20">
          <div className="border-b border-[var(--border)] pb-2 flex items-center justify-between">
            <h2 className="font-serif text-2xl font-normal text-[var(--foreground)] tracking-tight">
              6. Numerical Integration Architecture &amp; Error Control
            </h2>
            <span className="font-mono text-xs text-[var(--muted)]">Section 06</span>
          </div>

          <p className="text-sm text-[var(--foreground-secondary)] leading-relaxed">
            Integrating geodesics around spinning black holes requires exceptional numerical precision to resolve rapid frame-dragging oscillations near the horizon while maintaining tight conservation of constants over hundreds of orbits.
          </p>

          <div className="space-y-3">
            <h3 className="font-serif text-lg text-[var(--foreground)]">Dormand-Prince 8th-Order Integrator (DOP853)</h3>
            <p className="text-sm text-[var(--foreground-secondary)] leading-relaxed">
              The core engine employs the <strong>DOP853</strong> explicit Runge-Kutta scheme (Hairer, Nørsett &amp; Wanner 1993). Key specifications:
            </p>
            <ul className="list-disc list-inside space-y-1.5 text-xs text-[var(--foreground-secondary)] font-sans">
              <li><strong>12 evaluation stages per step:</strong> constructs an 8th-order solution along with embedded 5th-order and 3rd-order error estimators.</li>
              <li><strong>Adaptive step size control:</strong> local truncation error <MathBlock math="E_n" display={false} /> is estimated at each step. If <MathBlock math="E_n > \text{tol}" display={false} />, the step is rejected and repeated with smaller <MathBlock math="h" display={false} />.</li>
              <li><strong>Default error tolerances:</strong> absolute tolerance <MathBlock math="atol = 10^{-10}" display={false} />, relative tolerance <MathBlock math="rtol = 10^{-10}" display={false} />.</li>
              <li><strong>Continuous dense output:</strong> a 7th-order polynomial interpolant provides dense trajectory reconstruction without compromising step size.</li>
            </ul>
          </div>

          <div className="space-y-3">
            <h3 className="font-serif text-lg text-[var(--foreground)]">Directional Event Detection &amp; Root Localization</h3>
            <p className="text-sm text-[var(--foreground-secondary)] leading-relaxed">
              During integration, four physical and geometric events are monitored continuously as zero-crossings of scalar functions <MathBlock math="g(\lambda, y(\lambda)) = 0" display={false} />:
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono">
              <div className="p-3 rounded-[3px] border border-[var(--border)] bg-[var(--surface-subtle)] space-y-1">
                <span className="text-[var(--accent)] font-semibold">Horizon Cutoff Event</span>
                <MathBlock math="g(y) = r(\lambda) - (r_+ + \epsilon) = 0" display={false} />
                <p className="text-[11px] text-[var(--muted)] font-sans">
                  Detects coordinate horizon approach with buffer <MathBlock math="\epsilon = 10^{-4}M" display={false} /> before coordinate singularity divergence.
                </p>
              </div>
              <div className="p-3 rounded-[3px] border border-[var(--border)] bg-[var(--surface-subtle)] space-y-1">
                <span className="text-[var(--accent)] font-semibold">Escape Radius Event</span>
                <MathBlock math="g(y) = r(\lambda) - r_{\rm esc} = 0" display={false} />
                <p className="text-[11px] text-[var(--muted)] font-sans">
                  Terminates unbound scattering trajectories when reaching asymptotic flat spacetime (<MathBlock math="r_{\rm esc} \sim 100 - 1000M" display={false} />).
                </p>
              </div>
              <div className="p-3 rounded-[3px] border border-[var(--border)] bg-[var(--surface-subtle)] space-y-1">
                <span className="text-[var(--accent)] font-semibold">Radial Turning Point</span>
                <MathBlock math="g(y) = p_r(\lambda) = 0" display={false} />
                <p className="text-[11px] text-[var(--muted)] font-sans">
                  Non-terminal diagnostic event recording periapsis and apoapsis passages with sign direction.
                </p>
              </div>
              <div className="p-3 rounded-[3px] border border-[var(--border)] bg-[var(--surface-subtle)] space-y-1">
                <span className="text-[var(--accent)] font-semibold">Ergosphere Crossing</span>
                <MathBlock math="g(y) = r(\lambda) - r_{\rm ergo}(\theta) = 0" display={false} />
                <p className="text-[11px] text-[var(--muted)] font-sans">
                  Non-terminal event recording transitions into and out of the co-rotating ergoregion.
                </p>
              </div>
            </div>

            <p className="text-xs text-[var(--foreground-secondary)] font-sans mt-2">
              When an event bracket <MathBlock math="[\lambda_n, \lambda_{n+1}]" display={false} /> is detected by sign change, the engine applies Brent&apos;s bracketed root-finding method to the dense polynomial interpolant to isolate the event boundary down to root tolerance <MathBlock math="< 10^{-10}" display={false} />.
            </p>
          </div>

          <div className="space-y-3">
            <h3 className="font-serif text-lg text-[var(--foreground)]">Constraint Conservation as Trajectory Diagnostics</h3>
            <p className="text-sm text-[var(--foreground-secondary)] leading-relaxed">
              Standard explicit Runge-Kutta schemes do not exactly preserve symplectic 2-forms, leading to slight numerical dissipation or growth in constants of motion over very long integration times. Rather than artificially projecting trajectories back onto constant surfaces, the engine tracks these residuals as rigorous diagnostic indicators of trajectory fidelity:
            </p>

            <CopyableEquation
              label="Diagnostic Conservation Residuals"
              math="\begin{aligned}
\Delta \mathcal{H} &\equiv |\mathcal{H}(\lambda) - \mathcal{H}_0| \quad (\text{Hamiltonian Mass-Shell Drift}) \\
\Delta \mathcal{Q} &\equiv |\mathcal{Q}(\lambda) - \mathcal{Q}_0| \quad (\text{Carter Constant Invariance Drift}) \\
\Delta E &\equiv |p_t(\lambda) - p_t(0)|, \quad \Delta L_z \equiv |p_\phi(\lambda) - p_\phi(0)|
\end{aligned}"
            />

            <div className="space-y-2 text-xs font-sans text-[var(--foreground-secondary)] leading-relaxed bg-[var(--surface-subtle)] p-3.5 rounded-[3px] border border-[var(--border)]">
              <div className="font-mono text-xs font-semibold text-[var(--foreground)] uppercase tracking-wider">
                Precision Hierarchy: Tolerances, Empirical Residuals &amp; Diagnostic Thresholds
              </div>
              <p>
                To avoid conflating numerical settings with observational guarantees, the project maintains a strict three-tier precision distinction:
              </p>
              <ul className="list-disc list-inside space-y-1.5 pl-1 text-[var(--foreground-secondary)]">
                <li>
                  <strong>Integrator Local Error Tolerances:</strong> The DOP853 adaptive stepper is supplied with explicit step-size control tolerances <MathBlock math="atol = 10^{-10}, rtol = 10^{-10}" display={false} /> to constrain estimated single-step truncation error <MathBlock math="\|E_n\|" display={false} />.
                </li>
                <li>
                  <strong>Empirical Trajectory Residuals:</strong> In specific validation runs over moderate affine spans (<MathBlock math="\lambda \sim 25 - 100M" display={false} />), observed residuals depend on orbital geometry. Equatorial planar presets maintain near machine-precision Hamiltonian conservation (<MathBlock math="|\Delta\mathcal{H}| \lesssim 10^{-15}" display={false} />), while representative 3D non-equatorial benchmark orbits typically exhibit empirical residuals of <MathBlock math="|\Delta \mathcal{H}| \lesssim 10^{-10}" display={false} /> and normalized Carter drift <MathBlock math="|\Delta \mathcal{Q}|/\mathcal{Q}_0 \lesssim 10^{-9}" display={false} />.
                </li>
                <li>
                  <strong>Automated Test Acceptance Thresholds:</strong> In the regression test suite (<code className="font-mono text-[11px] bg-[var(--surface)] px-1 rounded">tests/test_integrator.py</code>), the bound <MathBlock math="10^{-9}" display={false} /> serves as a project-specific assertion criterion (<code className="font-mono text-[11px] bg-[var(--surface)] px-1 rounded">assert norm_drift &lt;= 1e-9</code>) to detect unphysical drift without failing on benign floating-point accumulation.
                </li>
              </ul>
              <p className="text-[11px] text-[var(--muted)] italic pt-1 border-t border-[var(--border)]">
                Note: Because standard Runge-Kutta steppers are non-symplectic, these empirical values are representative benchmark observations and diagnostic thresholds, not universal mathematical bounds. Over unbounded affine spans (<MathBlock math="\lambda \to \infty" display={false} />) or in near-horizon coordinate plunges, secular phase and energy drift will inevitably accumulate.
              </p>
            </div>
          </div>
        </section>

        {/* ========================================================================= */}
        {/* SECTION 7: CONNECTION TO THE GEODESIC EXPLORER */}
        {/* ========================================================================= */}
        <section id="explorer" className="space-y-5 scroll-mt-20">
          <div className="border-b border-[var(--border)] pb-2 flex items-center justify-between">
            <h2 className="font-serif text-2xl font-normal text-[var(--foreground)] tracking-tight">
              7. Connection to the Geodesic Explorer &amp; Presets
            </h2>
            <span className="font-mono text-xs text-[var(--muted)]">Section 07</span>
          </div>

          <p className="text-sm text-[var(--foreground-secondary)] leading-relaxed">
            The Geodesic Explorer exposes the computational power of the validated Python engine directly in your browser. Every input parameter in the Explorer control panel corresponds directly to a physical quantity in the Hamiltonian vector field:
          </p>

          <div className="overflow-x-auto rounded-[3px] border border-[var(--border)]">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-[var(--surface-subtle)] border-b border-[var(--border)] text-[var(--foreground)]">
                <tr>
                  <th className="py-2 px-3">UI Parameter</th>
                  <th className="py-2 px-3">Mathematical Symbol</th>
                  <th className="py-2 px-3">Phase-Space State Mapping</th>
                  <th className="py-2 px-3">Physical Meaning</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border)] bg-[var(--surface)] text-[var(--foreground-secondary)]">
                <tr>
                  <td className="py-2 px-3 font-semibold text-[var(--foreground)]">Mass (M)</td>
                  <td className="py-2 px-3 text-[var(--accent)]">M &gt; 0</td>
                  <td className="py-2 px-3">Metric parameter</td>
                  <td className="py-2 px-3 font-sans">Spacetime gravitational scale; sets length unit (default 1.0 M)</td>
                </tr>
                <tr>
                  <td className="py-2 px-3 font-semibold text-[var(--foreground)]">Spin (a)</td>
                  <td className="py-2 px-3 text-[var(--accent)]">a \in [-M, M]</td>
                  <td className="py-2 px-3">Metric parameter</td>
                  <td className="py-2 px-3 font-sans">Specific angular momentum J/M; controls horizon and frame dragging</td>
                </tr>
                <tr>
                  <td className="py-2 px-3 font-semibold text-[var(--foreground)]">Initial Radius (r₀)</td>
                  <td className="py-2 px-3 text-[var(--accent)]">r(0)</td>
                  <td className="py-2 px-3">y[1] = r₀</td>
                  <td className="py-2 px-3 font-sans">Starting radial coordinate in units of M; must satisfy r₀ &gt; r+</td>
                </tr>
                <tr>
                  <td className="py-2 px-3 font-semibold text-[var(--foreground)]">Polar Angle (θ₀)</td>
                  <td className="py-2 px-3 text-[var(--accent)]">\theta(0)</td>
                  <td className="py-2 px-3">y[2] = \theta_0</td>
                  <td className="py-2 px-3 font-sans">Starting polar angle in radians; π/2 ≈ 1.5708 is equatorial</td>
                </tr>
                <tr>
                  <td className="py-2 px-3 font-semibold text-[var(--foreground)]">Radial Momentum Perturbation</td>
                  <td className="py-2 px-3 text-[var(--accent)]">\delta p_r</td>
                  <td className="py-2 px-3">y[5] = p_{'{'}\rm circ{'}'} + \delta p_r</td>
                  <td className="py-2 px-3 font-sans">Perturbation to circular radial momentum; induces eccentricity</td>
                </tr>
                <tr>
                  <td className="py-2 px-3 font-semibold text-[var(--foreground)]">Energy (E)</td>
                  <td className="py-2 px-3 text-[var(--accent)]">E = -p_t</td>
                  <td className="py-2 px-3">y[4] = -E</td>
                  <td className="py-2 px-3 font-sans">Conserved specific energy conjugate to coordinate time</td>
                </tr>
                <tr>
                  <td className="py-2 px-3 font-semibold text-[var(--foreground)]">Affine Span (λ_max)</td>
                  <td className="py-2 px-3 text-[var(--accent)]">\lambda_{'{'}\max{'}'}</td>
                  <td className="py-2 px-3">t_span = (0, \lambda_{'{'}\max{'}'})</td>
                  <td className="py-2 px-3 font-sans">Maximum integration affine parameter span</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div className="space-y-4 pt-4">
            <h3 className="font-serif text-lg text-[var(--foreground)]">Direct Deep Links to All 7 Registered Presets</h3>
            <p className="text-sm text-[var(--foreground-secondary)] leading-relaxed">
              Explore the exact physical trajectories discussed in this lab by launching the registered presets directly into the Geodesic Explorer:
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Preset 1 */}
              <div className="rounded-[4px] border border-[var(--border)] bg-[var(--surface)] p-4 flex flex-col justify-between space-y-3">
                <div className="space-y-1">
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-[var(--accent)] font-semibold">schwarzschild_isco_circular</span>
                    <span className="px-1.5 py-0.5 rounded bg-[var(--surface-subtle)] text-[var(--muted)]">Timelike · a = 0</span>
                  </div>
                  <h4 className="font-serif text-base text-[var(--foreground)]">Schwarzschild ISCO Circular Orbit</h4>
                  <p className="text-xs text-[var(--foreground-secondary)] leading-relaxed font-sans">
                    Marginally stable circular orbit at <MathBlock math="r = 6M" display={false} /> with <MathBlock math="L = 2\sqrt{3}M \approx 3.464M" display={false} /> and binding energy <MathBlock math="E = \sqrt{8/9} \approx 0.9428" display={false} />.
                  </p>
                </div>
                <Link
                  href="/explorer?preset=schwarzschild_isco_circular"
                  className="inline-flex items-center gap-1.5 text-xs font-mono text-[var(--accent)] hover:text-[var(--accent-hover)] font-medium"
                >
                  <span>Launch in Explorer</span>
                  <ArrowRight className="h-3 w-3" />
                </Link>
              </div>

              {/* Preset 2 */}
              <div className="rounded-[4px] border border-[var(--border)] bg-[var(--surface)] p-4 flex flex-col justify-between space-y-3">
                <div className="space-y-1">
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-[var(--accent)] font-semibold">schwarzschild_precession</span>
                    <span className="px-1.5 py-0.5 rounded bg-[var(--surface-subtle)] text-[var(--muted)]">Timelike · a = 0</span>
                  </div>
                  <h4 className="font-serif text-base text-[var(--foreground)]">Relativistic Periastron Precession</h4>
                  <p className="text-xs text-[var(--foreground-secondary)] leading-relaxed font-sans">
                    Eccentric bound orbit at <MathBlock math="r_0 = 8M" display={false} /> exhibiting general relativistic periastron advance, producing a characteristic rosette trajectory.
                  </p>
                </div>
                <Link
                  href="/explorer?preset=schwarzschild_precession"
                  className="inline-flex items-center gap-1.5 text-xs font-mono text-[var(--accent)] hover:text-[var(--accent-hover)] font-medium"
                >
                  <span>Launch in Explorer</span>
                  <ArrowRight className="h-3 w-3" />
                </Link>
              </div>

              {/* Preset 3 */}
              <div className="rounded-[4px] border border-[var(--border)] bg-[var(--surface)] p-4 flex flex-col justify-between space-y-3">
                <div className="space-y-1">
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-[var(--accent)] font-semibold">schwarzschild_photon_sphere</span>
                    <span className="px-1.5 py-0.5 rounded bg-[var(--surface-subtle)] text-[var(--muted)]">Null · a = 0</span>
                  </div>
                  <h4 className="font-serif text-base text-[var(--foreground)]">Schwarzschild Photon Sphere</h4>
                  <p className="text-xs text-[var(--foreground-secondary)] leading-relaxed font-sans">
                    Unstable circular null orbit at <MathBlock math="r = 3M" display={false} /> with critical impact parameter <MathBlock math="b_c = 3\sqrt{3}M \approx 5.196M" display={false} />.
                  </p>
                </div>
                <Link
                  href="/explorer?preset=schwarzschild_photon_sphere"
                  className="inline-flex items-center gap-1.5 text-xs font-mono text-[var(--accent)] hover:text-[var(--accent-hover)] font-medium"
                >
                  <span>Launch in Explorer</span>
                  <ArrowRight className="h-3 w-3" />
                </Link>
              </div>

              {/* Preset 4 */}
              <div className="rounded-[4px] border border-[var(--border)] bg-[var(--surface)] p-4 flex flex-col justify-between space-y-3">
                <div className="space-y-1">
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-[var(--accent)] font-semibold">kerr_equatorial_prograde_photon</span>
                    <span className="px-1.5 py-0.5 rounded bg-[var(--surface-subtle)] text-[var(--muted)]">Null · a = 0.9</span>
                  </div>
                  <h4 className="font-serif text-base text-[var(--foreground)]">Kerr Prograde Circular Photon Orbit</h4>
                  <p className="text-xs text-[var(--foreground-secondary)] leading-relaxed font-sans">
                    Equatorial photon orbit co-rotating with high spin <MathBlock math="a = 0.9M" display={false} />, pulled inward to <MathBlock math="r_{\rm ph}^+ \approx 1.558M" display={false} /> by frame dragging.
                  </p>
                </div>
                <Link
                  href="/explorer?preset=kerr_equatorial_prograde_photon"
                  className="inline-flex items-center gap-1.5 text-xs font-mono text-[var(--accent)] hover:text-[var(--accent-hover)] font-medium"
                >
                  <span>Launch in Explorer</span>
                  <ArrowRight className="h-3 w-3" />
                </Link>
              </div>

              {/* Preset 5 */}
              <div className="rounded-[4px] border border-[var(--border)] bg-[var(--surface)] p-4 flex flex-col justify-between space-y-3">
                <div className="space-y-1">
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-[var(--accent)] font-semibold">kerr_equatorial_retrograde_photon</span>
                    <span className="px-1.5 py-0.5 rounded bg-[var(--surface-subtle)] text-[var(--muted)]">Null · a = 0.9</span>
                  </div>
                  <h4 className="font-serif text-base text-[var(--foreground)]">Kerr Retrograde Circular Photon Orbit</h4>
                  <p className="text-xs text-[var(--foreground-secondary)] leading-relaxed font-sans">
                    Equatorial photon orbit counter-rotating against black hole spin <MathBlock math="a = 0.9M" display={false} />, pushed outward to <MathBlock math="r_{\rm ph}^- \approx 3.910M" display={false} />.
                  </p>
                </div>
                <Link
                  href="/explorer?preset=kerr_equatorial_retrograde_photon"
                  className="inline-flex items-center gap-1.5 text-xs font-mono text-[var(--accent)] hover:text-[var(--accent-hover)] font-medium"
                >
                  <span>Launch in Explorer</span>
                  <ArrowRight className="h-3 w-3" />
                </Link>
              </div>

              {/* Preset 6 */}
              <div className="rounded-[4px] border border-[var(--border)] bg-[var(--surface)] p-4 flex flex-col justify-between space-y-3">
                <div className="space-y-1">
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-[var(--accent)] font-semibold">kerr_circular_timelike</span>
                    <span className="px-1.5 py-0.5 rounded bg-[var(--surface-subtle)] text-[var(--muted)]">Timelike · a = 0.9</span>
                  </div>
                  <h4 className="font-serif text-base text-[var(--foreground)]">Kerr Stable Circular Timelike Orbit</h4>
                  <p className="text-xs text-[var(--foreground-secondary)] leading-relaxed font-sans">
                    Bound stable prograde circular orbit around a rapidly spinning Kerr hole at <MathBlock math="r = 4.0M" display={false} /> with exact azimuthal frequency <MathBlock math="\Omega_\phi" display={false} />.
                  </p>
                </div>
                <Link
                  href="/explorer?preset=kerr_circular_timelike"
                  className="inline-flex items-center gap-1.5 text-xs font-mono text-[var(--accent)] hover:text-[var(--accent-hover)] font-medium"
                >
                  <span>Launch in Explorer</span>
                  <ArrowRight className="h-3 w-3" />
                </Link>
              </div>

              {/* Preset 7 */}
              <div className="rounded-[4px] border border-[var(--border)] bg-[var(--surface)] p-4 flex flex-col justify-between space-y-3 md:col-span-2">
                <div className="space-y-1">
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-[var(--accent)] font-semibold">kerr_equatorial_scattering</span>
                    <span className="px-1.5 py-0.5 rounded bg-[var(--surface-subtle)] text-[var(--muted)]">Null · a = 0.9 · Scattering</span>
                  </div>
                  <h4 className="font-serif text-base text-[var(--foreground)]">Kerr Relativistic Deflection &amp; Critical Scattering</h4>
                  <p className="text-xs text-[var(--foreground-secondary)] leading-relaxed font-sans">
                    Unbound photon trajectory fired from <MathBlock math="r_0 = 30M" display={false} /> with near-critical impact parameter <MathBlock math="b \approx b_{\rm crit}" display={false} />, illustrating multiple whirl loops around the ergosphere before escaping to infinity.
                  </p>
                </div>
                <Link
                  href="/explorer?preset=kerr_equatorial_scattering"
                  className="inline-flex items-center gap-1.5 text-xs font-mono text-[var(--accent)] hover:text-[var(--accent-hover)] font-medium"
                >
                  <span>Launch in Explorer</span>
                  <ArrowRight className="h-3 w-3" />
                </Link>
              </div>
            </div>
          </div>

          <div className="rounded-[4px] border border-[var(--border)] bg-[var(--surface)] p-6 text-center space-y-3 mt-8">
            <h3 className="font-serif text-xl text-[var(--foreground)]">Ready to Experiment with Kerr Geodesics?</h3>
            <p className="text-xs sm:text-sm text-[var(--muted)] font-sans max-w-xl mx-auto leading-relaxed">
              Launch the interactive Geodesic Explorer to simulate custom orbits, test knife-edge scattering parameters, and inspect live numerical conservation readouts computed directly by the Python engine.
            </p>
            <div className="pt-2">
              <Link
                href="/explorer"
                className="inline-flex items-center gap-2 rounded-[3px] bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white px-5 py-2.5 text-xs font-sans font-medium transition-colors cursor-pointer shadow-xs"
              >
                <Compass className="h-4 w-4" />
                <span>Open Geodesic Explorer</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
