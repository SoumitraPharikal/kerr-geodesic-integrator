"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import MathBlock from "@/components/MathBlock";
import MarginNote from "@/components/MarginNote";
import DerivationToggle from "@/components/DerivationToggle";
import { calculateKerrRadii } from "@/lib/kerrGeometry";

interface SectionLink {
  id: string;
  title: string;
  short: string;
}

const SECTIONS: SectionLink[] = [
  { id: "notation", title: "Notation & conventions", short: "Notation" },
  { id: "geometry", title: "1. Kerr geometry", short: "1. Geometry" },
  { id: "conserved", title: "2. Conserved quantities", short: "2. Invariants" },
  { id: "hamiltonian", title: "3. Canonical Hamiltonian", short: "3. Hamiltonian" },
  { id: "orbits", title: "4. Characteristic orbits", short: "4. Orbits" },
  { id: "numerics", title: "5. Numerical integration", short: "5. Numerics" },
  { id: "presets", title: "6. Registered presets", short: "6. Presets" },
];

function SpacetimeDiagram() {
  const [spin, setSpin] = useState(0.9);
  const [thetaDeg, setThetaDeg] = useState(60);
  const [mass, setMass] = useState(1.0);

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

  const cx = 280;
  const cy = 200;
  const scale = 55;

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

  const rayRNorm = rErgo / mass + 0.4;
  const rayX = cx + rayRNorm * sinTheta * scale;
  const rayY = cy - rayRNorm * cosTheta * scale;

  return (
    <figure className="border border-[var(--border)] bg-[var(--surface)] rounded-[2px] p-4 sm:p-5 space-y-4 my-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[var(--border-subtle)] pb-3">
        <div>
          <div className="text-xs font-sans font-medium uppercase tracking-wider text-[var(--muted)]">
            Figure 1 · Analytical reference geometry (not API output)
          </div>
          <div className="text-sm text-[var(--foreground-secondary)] mt-0.5 font-sans">
            Boyer–Lindquist meridional slice: event horizon <MathBlock math="r_+" display={false} />{" "}
            and static limit <MathBlock math="r_{\rm ergo}(\theta)" display={false} />
          </div>
        </div>
        <div className="flex items-center gap-4 text-xs font-sans">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-[var(--plot-horizon)] inline-block" />
            <span className="text-[var(--muted)]">
              Horizon (<MathBlock math="r_+" display={false} />)
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full border border-[var(--prograde)] bg-[var(--prograde)]/20 inline-block" />
            <span className="text-[var(--prograde)]">Ergosphere</span>
          </div>
        </div>
      </div>

      {/* SVG Canvas */}
      <div className="relative w-full overflow-hidden bg-[var(--plot-bg)] rounded-[2px] border border-[var(--border-subtle)] flex justify-center py-4">
        <svg
          viewBox="0 0 560 400"
          className="w-full max-w-[560px] h-auto select-none"
          role="img"
          aria-label="Kerr spacetime Boyer-Lindquist meridional geometry reference diagram"
        >
          <defs>
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
              id="progradeArrow"
              viewBox="0 0 10 10"
              refX="6"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 1 L 8 5 L 0 9 z" fill="var(--prograde)" />
            </marker>
          </defs>

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

          <text
            x="510"
            y={cy - 6}
            fill="var(--muted)"
            fontSize="10"
            fontFamily="var(--font-mono)"
            textAnchor="end"
          >
            Equatorial plane (θ = π/2)
          </text>

          <text
            x={cx + 10}
            y="45"
            fill="var(--foreground)"
            fontSize="11"
            fontFamily="var(--font-mono)"
          >
            Spin axis J = aM ẑ
          </text>

          {/* Ergosphere */}
          <path
            d={ergoPathD}
            fill="var(--prograde)"
            fillOpacity="0.1"
            stroke="var(--prograde)"
            strokeWidth="1.5"
            strokeDasharray="4 2"
          />

          {/* Outer Horizon r+ */}
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

          {/* Ring singularity marker */}
          <circle cx={cx} cy={cy} r="3" fill="var(--prograde)" />
          <text
            x={cx + 8}
            y={cy + 14}
            fill="var(--prograde)"
            fontSize="9"
            fontFamily="var(--font-mono)"
          >
            r = 0
          </text>

          {/* Polar angle ray */}
          <line x1={cx} y1={cy} x2={rayX} y2={rayY} stroke="var(--prograde)" strokeWidth="1.2" />
          <circle cx={rayX} cy={rayY} r="3.5" fill="var(--prograde)" />

          {thetaDeg > 0 && (
            <path
              d={`M ${cx} ${cy - 40} A 40 40 0 0 1 ${(cx + 40 * sinTheta).toFixed(1)} ${(
                cy -
                40 * cosTheta
              ).toFixed(1)}`}
              fill="none"
              stroke="var(--foreground)"
              strokeWidth="1"
            />
          )}
          <text x={cx + 18} y={cy - 22} fill="var(--foreground)" fontSize="10" fontFamily="var(--font-mono)">
            θ = {thetaDeg}°
          </text>

          {/* Horizon arrow */}
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
            fontFamily="var(--font-mono)"
            textAnchor="middle"
          >
            r+ = {rPlus.toFixed(2)}
            {mass === 1 ? "M" : ` (${rPlusNorm.toFixed(2)}M)`}
          </text>

          {/* Ergosphere equator arrow */}
          <line
            x1={cx}
            y1={cy + 80}
            x2={cx + 2 * scale}
            y2={cy + 80}
            stroke="var(--prograde)"
            strokeWidth="1"
            markerEnd="url(#progradeArrow)"
          />
          <text
            x={cx + scale}
            y={cy + 75}
            fill="var(--prograde)"
            fontSize="9"
            fontFamily="var(--font-mono)"
            textAnchor="middle"
          >
            r_ergo(π/2) = {(2 * mass).toFixed(2)}M
          </text>

          {/* Frame dragging arc */}
          <path
            d={`M ${cx + 1.2 * scale} ${cy - 0.7 * scale} A ${1.4 * scale} ${0.6 * scale} 0 0 1 ${
              cx + 1.2 * scale
            } ${cy + 0.7 * scale}`}
            fill="none"
            stroke="var(--prograde)"
            strokeWidth="1.25"
            strokeDasharray="3 3"
            markerEnd="url(#progradeArrow)"
          />
          <text x={cx + 1.5 * scale} y={cy} fill="var(--prograde)" fontSize="9" fontFamily="var(--font-mono)">
            dϕ/dλ &gt; 0
          </text>
        </svg>
      </div>

      {/* Controls */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="space-y-1">
          <div className="flex justify-between text-xs font-sans tabular-nums">
            <label htmlFor="math-spin" className="text-[var(--foreground)] font-medium">
              Dimensionless spin (χ = a/M)
            </label>
            <span className="text-[var(--prograde)] font-medium">{spin.toFixed(3)}</span>
          </div>
          <input
            id="math-spin"
            type="range"
            min="0"
            max="0.999"
            step="0.005"
            value={spin}
            onChange={(e) => setSpin(parseFloat(e.target.value))}
            className="w-full accent-[var(--accent)] cursor-pointer"
          />
        </div>

        <div className="space-y-1">
          <div className="flex justify-between text-xs font-sans tabular-nums">
            <label htmlFor="math-theta" className="text-[var(--foreground)] font-medium">
              Polar angle (θ)
            </label>
            <span className="text-[var(--prograde)] font-medium">{thetaDeg}°</span>
          </div>
          <input
            id="math-theta"
            type="range"
            min="0"
            max="90"
            step="1"
            value={thetaDeg}
            onChange={(e) => setThetaDeg(parseInt(e.target.value, 10))}
            className="w-full accent-[var(--accent)] cursor-pointer"
          />
        </div>

        <div className="space-y-1">
          <div className="flex justify-between text-xs font-sans tabular-nums">
            <label htmlFor="math-mass" className="text-[var(--foreground)] font-medium">
              Mass (M)
            </label>
            <span className="text-[var(--prograde)] font-medium">{mass.toFixed(1)} M</span>
          </div>
          <input
            id="math-mass"
            type="range"
            min="0.5"
            max="5.0"
            step="0.1"
            value={mass}
            onChange={(e) => setMass(parseFloat(e.target.value))}
            className="w-full accent-[var(--accent)] cursor-pointer"
          />
        </div>
      </div>

      {/* Radii Readout Table */}
      <div className="overflow-x-auto border-y border-[var(--border)]">
        <table className="w-full text-left text-xs font-sans tabular-nums">
          <thead className="border-b border-[var(--border)] text-[var(--muted)]">
            <tr>
              <th className="py-2 pr-3 font-medium">Horizon r+</th>
              <th className="py-2 px-3 font-medium">Inner r−</th>
              <th className="py-2 px-3 font-medium text-[var(--prograde)]">Ergosphere r_ergo(θ)</th>
              <th className="py-2 px-3 font-medium text-[var(--prograde)]">Prograde photon r_ph+</th>
              <th className="py-2 px-3 font-medium text-[var(--retrograde)]">Retrograde photon r_ph−</th>
              <th className="py-2 px-3 font-medium text-[var(--prograde)]">Prograde ISCO</th>
              <th className="py-2 pl-3 font-medium text-[var(--retrograde)]">Retrograde ISCO</th>
            </tr>
          </thead>
          <tbody className="text-[var(--foreground)]">
            <tr>
              <td className="py-2 pr-3 font-medium">{rPlus.toFixed(4)} M</td>
              <td className="py-2 px-3">{rMinus.toFixed(4)} M</td>
              <td className="py-2 px-3 font-medium text-[var(--prograde)]">{rErgo.toFixed(4)} M</td>
              <td className="py-2 px-3 text-[var(--prograde)]">{rPhPro.toFixed(4)} M</td>
              <td className="py-2 px-3 text-[var(--retrograde)]">{rPhRetro.toFixed(4)} M</td>
              <td className="py-2 px-3 text-[var(--prograde)]">{rIscoPro.toFixed(4)} M</td>
              <td className="py-2 pl-3 text-[var(--retrograde)]">{rIscoRetro.toFixed(4)} M</td>
            </tr>
          </tbody>
        </table>
      </div>
    </figure>
  );
}

export default function MathematicsPage() {
  const [activeSection, setActiveSection] = useState("notation");

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            setActiveSection(entry.target.id);
          }
        }
      },
      { rootMargin: "-20% 0px -65% 0px" }
    );

    for (const sec of SECTIONS) {
      const el = document.getElementById(sec.id);
      if (el) observer.observe(el);
    }

    return () => observer.disconnect();
  }, []);

  return (
    <div className="flex flex-col flex-1 pb-24">
      {/* Header */}
      <header className="border-b border-[var(--border)] bg-[var(--surface)] py-8 sm:py-10 px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-7xl space-y-3">
          <h1 className="font-serif text-3xl sm:text-4xl font-normal text-[var(--foreground)] tracking-tight">
            Mathematical formulation
          </h1>
          <p className="prose-notebook text-[var(--foreground-secondary)]">
            Boyer–Lindquist geometry, canonical 8D Hamiltonian equations, conserved quantities,
            and adaptive numerical integration used in the Python engine.
          </p>
        </div>
      </header>

      {/* Mobile / Tablet Jump Links (wrapping, no horizontal overflow) */}
      <nav
        aria-label="Section index"
        className="lg:hidden border-b border-[var(--border)] bg-[var(--background)] px-4 sm:px-6 py-3"
      >
        <div className="flex flex-wrap gap-x-4 gap-y-1.5 text-xs font-sans">
          {SECTIONS.map((sec) => (
            <a
              key={sec.id}
              href={`#${sec.id}`}
              onClick={() => setActiveSection(sec.id)}
              className={
                activeSection === sec.id
                  ? "text-[var(--foreground)] font-medium underline underline-offset-4"
                  : "text-[var(--muted)] hover:text-[var(--foreground)]"
              }
            >
              {sec.short}
            </a>
          ))}
        </div>
      </nav>

      {/* Main 2-Column Paper Layout: Sticky TOC + Prose */}
      <div className="mx-auto max-w-7xl w-full px-4 sm:px-6 lg:px-8 mt-10 grid grid-cols-1 lg:grid-cols-12 gap-10 items-start">
        {/* Desktop Sticky TOC */}
        <aside className="hidden lg:block lg:col-span-3 sticky top-20 space-y-6">
          <nav aria-label="Table of contents" className="space-y-1.5 border-l border-[var(--border)] pl-4">
            <div className="text-[11px] font-sans font-medium uppercase tracking-wider text-[var(--muted)] mb-2">
              Contents
            </div>
            {SECTIONS.map((sec) => {
              const active = activeSection === sec.id;
              return (
                <a
                  key={sec.id}
                  href={`#${sec.id}`}
                  onClick={() => setActiveSection(sec.id)}
                  className={`block py-1 text-[13px] font-sans ${
                    active
                      ? "text-[var(--foreground)] font-medium underline underline-offset-4"
                      : "text-[var(--muted)] hover:text-[var(--foreground)]"
                  }`}
                >
                  {sec.title}
                </a>
              );
            })}
          </nav>

          <div className="pt-2">
            <Link
              href="/explorer"
              className="inline-flex items-center gap-1.5 text-xs font-sans font-medium text-[var(--accent)] hover:underline underline-offset-4"
            >
              <span>Open Explorer</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        </aside>

        {/* Paper Content */}
        <article className="lg:col-span-9 space-y-14 min-w-0">
          {/* NOTATION */}
          <section id="notation" className="scroll-mt-20 space-y-4">
            <h2 className="font-serif text-2xl font-normal text-[var(--foreground)] border-b border-[var(--border)] pb-2">
              Notation and conventions
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-start">
              <div className="md:col-span-8 space-y-3 prose-notebook text-[var(--foreground-secondary)]">
                <p>
                  All equations follow geometrized units <MathBlock math="G = c = 1" display={false} />{" "}
                  and metric signature <MathBlock math="(-, +, +, +)" display={false} /> in
                  Boyer–Lindquist coordinates <MathBlock math="x^\mu = (t, r, \theta, \phi)" display={false} />.
                </p>
                <ul className="list-disc pl-5 space-y-1.5 text-base font-serif">
                  <li>
                    <MathBlock math="M > 0" display={false} />: ADM mass;{" "}
                    <MathBlock math="a \equiv J/M" display={false} />: signed specific angular momentum.
                  </li>
                  <li>
                    <MathBlock math="\lambda" display={false} />: affine parameter (proper time{" "}
                    <MathBlock math="\tau" display={false} /> for timelike particles with{" "}
                    <MathBlock math="\mu = 1" display={false} />; affine parameter for null rays with{" "}
                    <MathBlock math="\mu = 0" display={false} />).
                  </li>
                  <li>
                    <MathBlock math="E = -p_t" display={false} />,{" "}
                    <MathBlock math="L_z = p_\phi" display={false} />, and{" "}
                    <MathBlock math="\mathcal{Q} = \mathcal{K} - (L_z - aE)^2" display={false} />:
                    conserved energy, axial angular momentum, and Carter constant.
                  </li>
                </ul>
              </div>
              <div className="md:col-span-4">
                <MarginNote label="Spin bounds">
                  <code>KerrMetric</code> in Python permits{" "}
                  <MathBlock math="|a| \le M" display={false} />. The interactive Explorer and API
                  presets enforce sub-extremal <MathBlock math="|a| < M" display={false} /> (with{" "}
                  <MathBlock math="0 \le a \le M" display={false} /> allowed on the retrograde photon
                  preset).
                </MarginNote>
              </div>
            </div>
          </section>

          {/* 1. GEOMETRY */}
          <section id="geometry" className="scroll-mt-20 space-y-5 border-t border-[var(--border)] pt-8">
            <h2 className="font-serif text-2xl font-normal text-[var(--foreground)]">
              1. Kerr geometry in Boyer–Lindquist coordinates
            </h2>
            <div className="prose-notebook text-[var(--foreground-secondary)] space-y-4">
              <p>
                With auxiliary functions{" "}
                <MathBlock math="\Sigma(r,\theta) = r^2 + a^2\cos^2\theta" display={false} />,{" "}
                <MathBlock math="\Delta(r) = r^2 - 2Mr + a^2" display={false} />, and{" "}
                <MathBlock math="A(r,\theta) = (r^2 + a^2)^2 - a^2\Delta\sin^2\theta" display={false} />,
                the Kerr line element is:
              </p>
            </div>

            <MathBlock
              id="eq-1"
              number="1"
              math="ds^2 = -\left(1 - \frac{2Mr}{\Sigma}\right) dt^2 - \frac{4Mar\sin^2\theta}{\Sigma}\,dt\,d\phi + \frac{\Sigma}{\Delta}\,dr^2 + \Sigma\,d\theta^2 + \frac{A\sin^2\theta}{\Sigma}\,d\phi^2"
            />

            <DerivationToggle summary="Show 4D metric determinant identity">
              <p className="text-sm font-sans leading-relaxed">
                Factoring the <MathBlock math="2 \times 2" display={false} />{" "}
                <MathBlock math="(t,\phi)" display={false} /> block gives a volume element
                independent of <MathBlock math="\Delta(r)" display={false} />:
              </p>
              <MathBlock
                id="eq-det"
                math="\det(g_{\mu\nu}) = (g_{tt} g_{\phi\phi} - g_{t\phi}^2)\,g_{rr}\,g_{\theta\theta} = -\Sigma^2 \sin^2\theta \implies \sqrt{-g} = \Sigma \sin\theta"
              />
            </DerivationToggle>

            <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-start">
              <div className="md:col-span-8 space-y-4 prose-notebook text-[var(--foreground-secondary)]">
                <p>
                  The roots of <MathBlock math="\Delta(r) = 0" display={false} /> define the outer
                  event horizon <MathBlock math="r_+" display={false} /> and inner Cauchy horizon{" "}
                  <MathBlock math="r_-" display={false} />, while <MathBlock math="g_{tt}(r,\theta) = 0" display={false} />{" "}
                  defines the static limit (ergosphere boundary):
                </p>
                <MathBlock
                  id="eq-2"
                  number="2"
                  math="r_\pm = M \pm \sqrt{M^2 - a^2}, \qquad r_{\rm ergo}(\theta) = M + \sqrt{M^2 - a^2 \cos^2\theta}"
                />
                <p>
                  Between <MathBlock math="r_+" display={false} /> and{" "}
                  <MathBlock math="r_{\rm ergo}(\theta)" display={false} />,{" "}
                  <MathBlock math="g_{tt} > 0" display={false} />, so no physical observer can remain
                  stationary relative to infinity. In the Schwarzschild limit{" "}
                  <MathBlock math="a \to 0" display={false} />,{" "}
                  <MathBlock math="r_{\rm ergo}(\theta) = r_+ = 2M" display={false} /> and{" "}
                  <MathBlock math="r_- = 0" display={false} />.
                </p>
              </div>
              <div className="md:col-span-4">
                <MarginNote label="Coordinate singularity">
                  At <MathBlock math="r = r_+" display={false} />,{" "}
                  <MathBlock math="g_{rr} \to \infty" display={false} /> in Boyer–Lindquist
                  coordinates. Integration halts cleanly at a horizon buffer{" "}
                  <MathBlock math="r_+ + \epsilon" display={false} />.
                </MarginNote>
              </div>
            </div>

            <SpacetimeDiagram />
          </section>

          {/* 2. CONSERVED QUANTITIES */}
          <section id="conserved" className="scroll-mt-20 space-y-5 border-t border-[var(--border)] pt-8">
            <h2 className="font-serif text-2xl font-normal text-[var(--foreground)]">
              2. Symmetries and conserved quantities
            </h2>
            <div className="prose-notebook text-[var(--foreground-secondary)] space-y-4">
              <p>
                Stationarity (<MathBlock math="\partial_t g_{\mu\nu} = 0" display={false} />) and
                axisymmetry (<MathBlock math="\partial_\phi g_{\mu\nu} = 0" display={false} />) yield
                two first integrals directly from the conjugate momenta:
              </p>
              <MathBlock
                id="eq-3"
                number="3"
                math="E \equiv -p_t, \qquad L_z \equiv p_\phi"
              />
              <p>
                Separability of the Hamilton–Jacobi equation (Carter 1968) yields a fourth constant
                of motion. Using the project&apos;s primary convention{" "}
                <MathBlock math="\mathcal{Q} \equiv \mathcal{K} - (L_z - aE)^2" display={false} />:
              </p>
              <MathBlock
                id="eq-4"
                number="4"
                math="\mathcal{Q} = p_\theta^2 + \cos^2\theta\left[a^2(\mu^2 - E^2) + \frac{L_z^2}{\sin^2\theta}\right]"
              />
              <p>
                For all equatorial trajectories (<MathBlock math="\theta = \pi/2" display={false} />,{" "}
                <MathBlock math="p_\theta = 0" display={false} />),{" "}
                <MathBlock math="\cos(\pi/2) = 0" display={false} />, so{" "}
                <MathBlock math="\mathcal{Q} = 0" display={false} /> identically. In the
                Schwarzschild limit (<MathBlock math="a \to 0" display={false} />),{" "}
                <MathBlock math="\mathcal{Q} \to L^2 - L_z^2" display={false} />.
              </p>
            </div>

            <DerivationToggle summary="Show radial representation of the Carter constant">
              <p className="text-sm font-sans leading-relaxed">
                Equivalently, <MathBlock math="\mathcal{Q}" display={false} /> can be evaluated from
                the radial sector and cross-checked against the polar formula in tests:
              </p>
              <MathBlock
                id="eq-q-rad"
                math="\mathcal{Q}_{\rm radial} = \frac{\left[(r^2 + a^2)E - a L_z\right]^2}{\Delta(r)} - \Delta(r) p_r^2 - \mu^2 r^2 - (L_z - aE)^2"
              />
            </DerivationToggle>
          </section>

          {/* 3. CANONICAL HAMILTONIAN */}
          <section id="hamiltonian" className="scroll-mt-20 space-y-5 border-t border-[var(--border)] pt-8">
            <h2 className="font-serif text-2xl font-normal text-[var(--foreground)]">
              3. Canonical Hamiltonian and equations of motion
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-start">
              <div className="md:col-span-8 space-y-4 prose-notebook text-[var(--foreground-secondary)]">
                <p>
                  The solver integrates the 8-dimensional phase-space vector{" "}
                  <MathBlock math="y = (t, r, \theta, \phi, p_t, p_r, p_\theta, p_\phi) \in \mathbb{R}^8" display={false} />{" "}
                  using the super-Hamiltonian:
                </p>
                <MathBlock
                  id="eq-5"
                  number="5"
                  math="\mathcal{H}(x^\mu, p_\mu) = \frac{1}{2}\, g^{\mu\nu}(x)\, p_\mu p_\nu = -\frac{1}{2}\mu^2"
                />
                <p>
                  Hamilton&apos;s canonical equations propagate the state smoothly without Christoffel
                  symbols or radial turning-point square-root branch cuts:
                </p>
                <MathBlock
                  id="eq-6"
                  number="6"
                  math="\frac{dx^\mu}{d\lambda} = g^{\mu\nu}(x)\,p_\nu, \qquad \frac{dp_\mu}{d\lambda} = -\frac{1}{2}\left(\frac{\partial g^{\alpha\beta}}{\partial x^\mu}\right) p_\alpha p_\beta"
                />
              </div>
              <div className="md:col-span-4">
                <MarginNote label="Why 8D Hamiltonian ODEs">
                  In first-order separated equations, <MathBlock math="\dot{r} = \pm\sqrt{R(r)}/\Sigma" display={false} />{" "}
                  has a diverging derivative at <MathBlock math="R(r) = 0" display={false} />. In
                  canonical variables, turning points are smooth zero-crossings of{" "}
                  <MathBlock math="p_r = 0" display={false} />.
                </MarginNote>
              </div>
            </div>

            <DerivationToggle summary="Show contravariant inverse metric components g^{μν}">
              <MathBlock
                id="eq-inv-metric"
                math="\begin{aligned}
g^{tt} &= -\frac{A(r,\theta)}{\Sigma\Delta}, & g^{t\phi} &= g^{\phi t} = -\frac{2Mar}{\Sigma\Delta}, \\
g^{rr} &= \frac{\Delta}{\Sigma}, & g^{\theta\theta} &= \frac{1}{\Sigma}, & g^{\phi\phi} &= \frac{\Delta - a^2\sin^2\theta}{\Sigma\Delta\sin^2\theta}
\end{aligned}"
              />
            </DerivationToggle>
          </section>

          {/* 4. CHARACTERISTIC ORBITS */}
          <section id="orbits" className="scroll-mt-20 space-y-5 border-t border-[var(--border)] pt-8">
            <h2 className="font-serif text-2xl font-normal text-[var(--foreground)]">
              4. Separated potentials and characteristic orbits
            </h2>
            <div className="prose-notebook text-[var(--foreground-secondary)] space-y-4">
              <p>
                For analytical classification, radial and polar motion decouple through the Carter
                potentials <MathBlock math="R(r) \ge 0" display={false} /> and{" "}
                <MathBlock math="\Theta(\theta) \ge 0" display={false} />:
              </p>
              <MathBlock
                id="eq-7"
                number="7"
                math="R(r) = \left[E(r^2 + a^2) - aL_z\right]^2 - \Delta(r)\left[\mu^2 r^2 + (L_z - aE)^2 + \mathcal{Q}\right]"
              />
              <p>
                In Schwarzschild spacetime (<MathBlock math="a = 0" display={false} />), the
                innermost stable circular timelike orbit lies at{" "}
                <MathBlock math="r_{\rm ISCO} = 6M" display={false} /> and the unstable circular
                photon sphere lies at <MathBlock math="r_{\rm ph} = 3M" display={false} />{" "}
                (critical impact parameter <MathBlock math="b_c = 3\sqrt{3}M \approx 5.196M" display={false} />).
              </p>
              <p>
                For nonzero spin (<MathBlock math="a > 0" display={false} />), frame-dragging splits
                the equatorial circular photon orbit into{" "}
                <span className="text-[var(--prograde)] font-medium">prograde</span> (<MathBlock math="+" display={false} />)
                and <span className="text-[var(--retrograde)] font-medium">retrograde</span> (<MathBlock math="-" display={false} />)
                radii:
              </p>
              <MathBlock
                id="eq-8"
                number="8"
                math="r_{\rm ph}^\pm = 2M\left\{1 + \cos\left[\frac{2}{3}\arccos\left(\mp \frac{a}{M}\right)\right]\right\}"
              />
              <p>
                Equatorial photons fired from asymptotic infinity with impact parameter{" "}
                <MathBlock math="b = L_z / E" display={false} /> near the critical threshold{" "}
                <MathBlock math="b_{\rm crit}" display={false} /> deflect around the{" "}
                <strong>unstable photon orbit</strong> before either escaping or crossing the horizon.
              </p>
            </div>

            <DerivationToggle summary="Show Bardeen–Press–Teukolsky Kerr ISCO formula">
              <MathBlock
                id="eq-isco"
                math="\begin{aligned}
r_{\rm ISCO}^\pm &= M\left\{3 + Z_2 \mp \sqrt{(3 - Z_1)(3 + Z_1 + 2Z_2)}\right\}, \\
Z_1 &\equiv 1 + \left(1 - \frac{a^2}{M^2}\right)^{1/3}\left[\left(1 + \frac{a}{M}\right)^{1/3} + \left(1 - \frac{a}{M}\right)^{1/3}\right], \quad Z_2 \equiv \sqrt{3\frac{a^2}{M^2} + Z_1^2}
\end{aligned}"
              />
            </DerivationToggle>
          </section>

          {/* 5. NUMERICAL INTEGRATION */}
          <section id="numerics" className="scroll-mt-20 space-y-5 border-t border-[var(--border)] pt-8">
            <h2 className="font-serif text-2xl font-normal text-[var(--foreground)]">
              5. Numerical integration, event detection, and limitations
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-start">
              <div className="md:col-span-8 space-y-4 prose-notebook text-[var(--foreground-secondary)]">
                <p>
                  The Python engine integrates the 8D Hamiltonian system with{" "}
                  <span className="font-mono text-sm text-[var(--foreground)]">
                    scipy.integrate.solve_ivp
                  </span>
                  , defaulting to the 8th-order Dormand–Prince method{" "}
                  <span className="font-mono text-sm text-[var(--foreground)]">DOP853</span>{" "}
                  (<MathBlock math="\text{rtol} = \text{atol} = 10^{-10}" display={false} />). Other
                  supported SciPy solvers include <span className="font-mono text-sm">RK45</span>{" "}
                  (Dormand–Prince 5(4)), <span className="font-mono text-sm">RK23</span>,{" "}
                  <span className="font-mono text-sm">Radau</span>,{" "}
                  <span className="font-mono text-sm">BDF</span>, and{" "}
                  <span className="font-mono text-sm">LSODA</span>.
                </p>
                <p>
                  Event boundaries—horizon cutoff (<MathBlock math="r = r_+ + \epsilon" display={false} />),
                  escape radius, radial turning points (<MathBlock math="p_r = 0" display={false} />),
                  and ergosphere crossings—are refined with{" "}
                  <span className="font-mono text-sm text-[var(--foreground)]">scipy.optimize.brentq</span>{" "}
                  evaluated on the solver&apos;s continuous dense-output interpolant.
                </p>
                <p>
                  Because explicit Runge–Kutta methods are <strong>non-symplectic</strong>,
                  conserved-quantity drift is kept small by adaptive local error control rather than
                  forbidden by construction. Across the seven recorded preset runs, measured
                  Hamiltonian drift <MathBlock math="|\Delta\mathcal{H}|" display={false} /> ranges
                  from <MathBlock math="< 10^{-16}" display={false} /> up to{" "}
                  <MathBlock math="3.88 \times 10^{-13}" display={false} /> (at most approximately{" "}
                  <MathBlock math="4 \times 10^{-13}" display={false} />).
                </p>
              </div>
              <div className="md:col-span-4">
                <MarginNote label="Scope & limitations">
                  Recorded drifts apply to the seven tested preset spans. Over very long
                  integrations or near-horizon plunges, secular error can accumulate. The interactive
                  UI exposes equatorial presets only.
                </MarginNote>
              </div>
            </div>
          </section>

          {/* 6. REGISTERED PRESETS */}
          <section id="presets" className="scroll-mt-20 space-y-5 border-t border-[var(--border)] pt-8">
            <h2 className="font-serif text-2xl font-normal text-[var(--foreground)]">
              6. Registered presets in the lab
            </h2>
            <p className="text-sm font-sans text-[var(--foreground-secondary)] leading-relaxed max-w-2xl">
              Every preset below uses the exact default parameters served by{" "}
              <span className="font-mono text-xs text-[var(--foreground)]">GET /api/v1/presets</span>{" "}
              and opens directly in Explorer.
            </p>

            <div className="overflow-x-auto border-y border-[var(--border)]">
              <table className="w-full text-left text-sm font-sans">
                <thead>
                  <tr className="border-b border-[var(--border)] text-xs font-medium text-[var(--muted)]">
                    <th className="py-2.5 pr-4">Preset</th>
                    <th className="py-2.5 px-4">Type</th>
                    <th className="py-2.5 px-4">Default parameters</th>
                    <th className="py-2.5 pl-4 text-right">Explorer</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--border-subtle)] tabular-nums">
                  <tr>
                    <td className="py-2.5 pr-4 font-medium text-[var(--foreground)]">
                      Schwarzschild ISCO circular orbit
                    </td>
                    <td className="py-2.5 px-4 text-[var(--foreground-secondary)]">Timelike</td>
                    <td className="py-2.5 px-4 font-mono text-xs">M = 1.0, r = 6.0 M, λ = 50.0</td>
                    <td className="py-2.5 pl-4 text-right">
                      <Link href="/explorer?preset=schwarzschild_isco_circular" className="text-xs text-[var(--accent)] hover:underline">
                        Open
                      </Link>
                    </td>
                  </tr>
                  <tr>
                    <td className="py-2.5 pr-4 font-medium text-[var(--foreground)]">
                      Schwarzschild relativistic precession
                    </td>
                    <td className="py-2.5 px-4 text-[var(--foreground-secondary)]">Timelike</td>
                    <td className="py-2.5 px-4 font-mono text-xs">
                      M = 1.0, r₀ = 8.0 M, δp_r = 0.001, λ = 100.0
                    </td>
                    <td className="py-2.5 pl-4 text-right">
                      <Link href="/explorer?preset=schwarzschild_precession" className="text-xs text-[var(--accent)] hover:underline">
                        Open
                      </Link>
                    </td>
                  </tr>
                  <tr>
                    <td className="py-2.5 pr-4 font-medium text-[var(--foreground)]">
                      Schwarzschild photon sphere
                    </td>
                    <td className="py-2.5 px-4 text-[var(--foreground-secondary)]">Null</td>
                    <td className="py-2.5 px-4 font-mono text-xs">M = 1.0, r = 3.0 M, E = 1.0, λ = 12.0</td>
                    <td className="py-2.5 pl-4 text-right">
                      <Link href="/explorer?preset=schwarzschild_photon_sphere" className="text-xs text-[var(--accent)] hover:underline">
                        Open
                      </Link>
                    </td>
                  </tr>
                  <tr>
                    <td className="py-2.5 pr-4 font-medium text-[var(--foreground)]">
                      Kerr prograde circular photon orbit
                    </td>
                    <td className="py-2.5 px-4 text-[var(--prograde)]">Null (prograde)</td>
                    <td className="py-2.5 px-4 font-mono text-xs">
                      M = 1.0, a = 0.9 M, E = 1.0, λ = 20.0
                    </td>
                    <td className="py-2.5 pl-4 text-right">
                      <Link href="/explorer?preset=kerr_equatorial_prograde_photon" className="text-xs text-[var(--accent)] hover:underline">
                        Open
                      </Link>
                    </td>
                  </tr>
                  <tr>
                    <td className="py-2.5 pr-4 font-medium text-[var(--foreground)]">
                      Kerr retrograde circular photon orbit
                    </td>
                    <td className="py-2.5 px-4 text-[var(--retrograde)]">Null (retrograde)</td>
                    <td className="py-2.5 px-4 font-mono text-xs">
                      M = 1.0, a = 0.9 M, E = 1.0, λ = 30.0
                    </td>
                    <td className="py-2.5 pl-4 text-right">
                      <Link href="/explorer?preset=kerr_equatorial_retrograde_photon" className="text-xs text-[var(--accent)] hover:underline">
                        Open
                      </Link>
                    </td>
                  </tr>
                  <tr>
                    <td className="py-2.5 pr-4 font-medium text-[var(--foreground)]">
                      Kerr circular timelike orbit
                    </td>
                    <td className="py-2.5 px-4 text-[var(--prograde)]">Timelike (prograde)</td>
                    <td className="py-2.5 px-4 font-mono text-xs">
                      M = 1.0, a = 0.9 M, r = 6.0 M, λ = 100.0
                    </td>
                    <td className="py-2.5 pl-4 text-right">
                      <Link href="/explorer?preset=kerr_circular_timelike" className="text-xs text-[var(--accent)] hover:underline">
                        Open
                      </Link>
                    </td>
                  </tr>
                  <tr>
                    <td className="py-2.5 pr-4 font-medium text-[var(--foreground)]">
                      Kerr equatorial photon scattering
                    </td>
                    <td className="py-2.5 px-4 text-[var(--prograde)]">Null (scattering)</td>
                    <td className="py-2.5 px-4 font-mono text-xs">
                      M = 1.0, a = 0.5 M, b = 4.5 M, r₀ = 50.0 M, λ = 200.0
                    </td>
                    <td className="py-2.5 pl-4 text-right">
                      <Link href="/explorer?preset=kerr_equatorial_scattering" className="text-xs text-[var(--accent)] hover:underline">
                        Open
                      </Link>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>
        </article>
      </div>
    </div>
  );
}
