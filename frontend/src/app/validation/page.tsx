"use client";

import React from "react";
import Link from "next/link";
import MarginNote from "@/components/MarginNote";

const REPO_BASE = "https://github.com/SoumitraPharikal/kerr-geodesic-integrator/blob/062b20c80a689640637a2fcd003bdd921a7d4132";

interface AuditRow {
  category: "Analytical" | "Numerical";
  claim: string;
  measured: string;
  conditions: string;
  sourceLabel: string;
  sourceUrl: string;
}

const AUDIT_LEDGER: AuditRow[] = [
  {
    category: "Analytical",
    claim: "Pointwise null Hamiltonian constraint",
    measured: "|H| ≤ 10⁻¹⁵",
    conditions: "Single phase-space point at exact null initial condition (no stepping)",
    sourceLabel: "tests/test_hamiltonian.py#L191",
    sourceUrl: `${REPO_BASE}/tests/test_hamiltonian.py#L191`,
  },
  {
    category: "Analytical",
    claim: "Metric inverse closure ‖g · g⁻¹ − I‖",
    measured: "≤ 10⁻¹⁴",
    conditions: "Boyer–Lindquist metric vs. analytic contravariant inverse at test points",
    sourceLabel: "tests/test_hamiltonian.py#L735",
    sourceUrl: `${REPO_BASE}/tests/test_hamiltonian.py#L735`,
  },
  {
    category: "Analytical",
    claim: "Polar vs. explicit Carter constant Q",
    measured: "|ΔQ| ≤ 10⁻¹³",
    conditions: "Algebraic evaluation of Q = K − (L_z − aE)² at fixed state",
    sourceLabel: "tests/test_hamiltonian.py#L869",
    sourceUrl: `${REPO_BASE}/tests/test_hamiltonian.py#L869`,
  },
  {
    category: "Analytical",
    claim: "Radial vs. polar separation constant K",
    measured: "|ΔK| ≤ 10⁻¹²",
    conditions: "Independent radial and polar evaluations at constraint-satisfying states",
    sourceLabel: "tests/test_hamiltonian.py#L878-L899",
    sourceUrl: `${REPO_BASE}/tests/test_hamiltonian.py#L878-L899`,
  },
  {
    category: "Numerical",
    claim: "Event root localization (brentq)",
    measured: "xtol = rtol = 4ε",
    conditions: "Refined via scipy.optimize.brentq on SciPy dense-output interpolant",
    sourceLabel: "src/geodesics/integrator.py#L743",
    sourceUrl: `${REPO_BASE}/src/geodesics/integrator.py#L743`,
  },
  {
    category: "Numerical",
    claim: "Seven recorded preset Hamiltonian drifts",
    measured: "0 to 3.88 × 10⁻¹³",
    conditions: "DOP853, rtol = atol = 10⁻¹⁰, recorded at commit 062b20c (λ ≤ 200)",
    sourceLabel: "frontend/src/data/gallery_trajectories.json",
    sourceUrl: `${REPO_BASE}/frontend/src/data/gallery_trajectories.json`,
  },
];

interface DriftPoint {
  id: string;
  label: string;
  params: string;
  driftValue: number;
  driftText: string;
  tone: "default" | "prograde" | "retrograde";
}

const RECORDED_DRIFTS: DriftPoint[] = [
  {
    id: "schwarzschild_isco_circular",
    label: "Schwarzschild ISCO circular",
    params: "M = 1, r = 6 M, λ = 50",
    driftValue: 1e-16,
    driftText: "< 10⁻¹⁶ (0.00)",
    tone: "default",
  },
  {
    id: "schwarzschild_precession",
    label: "Schwarzschild precession",
    params: "M = 1, r₀ = 8 M, δp_r = 0.001, λ = 100",
    driftValue: 2.22e-16,
    driftText: "2.22 × 10⁻¹⁶",
    tone: "default",
  },
  {
    id: "schwarzschild_photon_sphere",
    label: "Schwarzschild photon sphere",
    params: "M = 1, r = 3 M, E = 1, λ = 12",
    driftValue: 4.44e-16,
    driftText: "4.44 × 10⁻¹⁶",
    tone: "default",
  },
  {
    id: "kerr_equatorial_prograde_photon",
    label: "Kerr prograde photon",
    params: "M = 1, a = 0.9 M, E = 1, λ = 20",
    driftValue: 1.07e-14,
    driftText: "1.07 × 10⁻¹⁴",
    tone: "prograde",
  },
  {
    id: "kerr_equatorial_retrograde_photon",
    label: "Kerr retrograde photon",
    params: "M = 1, a = 0.9 M, E = 1, λ = 30",
    driftValue: 6.66e-16,
    driftText: "6.66 × 10⁻¹⁶",
    tone: "retrograde",
  },
  {
    id: "kerr_circular_timelike",
    label: "Kerr circular timelike",
    params: "M = 1, a = 0.9 M, r = 6 M, λ = 100",
    driftValue: 3.33e-16,
    driftText: "3.33 × 10⁻¹⁶",
    tone: "prograde",
  },
  {
    id: "kerr_equatorial_scattering",
    label: "Kerr equatorial scattering",
    params: "M = 1, a = 0.5 M, b = 4.5 M, r₀ = 50 M, λ = 200",
    driftValue: 3.88e-13,
    driftText: "3.88 × 10⁻¹³",
    tone: "prograde",
  },
];

function LogDriftChart() {
  const width = 680;
  const rowHeight = 32;
  const topPad = 24;
  const bottomPad = 36;
  const leftPad = 210;
  const rightPad = 110;
  const plotWidth = width - leftPad - rightPad;
  const height = topPad + RECORDED_DRIFTS.length * rowHeight + bottomPad;

  const minLog = -16.5;
  const maxLog = -12;
  const ticks = [-16, -15, -14, -13, -12];

  const toX = (val: number) => {
    const logVal = Math.max(minLog, Math.min(maxLog, Math.log10(val)));
    return leftPad + ((logVal - minLog) / (maxLog - minLog)) * plotWidth;
  };

  return (
    <figure className="border border-[var(--border)] bg-[var(--plot-bg)] rounded-[2px] p-4 space-y-2">
      <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-[var(--border-subtle)] pb-2">
        <figcaption className="text-xs font-sans font-medium text-[var(--foreground)]">
          Recorded results: maximum Hamiltonian drift |ΔH| across the seven presets (log₁₀ scale)
        </figcaption>
        <span className="text-[11px] font-sans text-[var(--muted)]">
          DOP853, rtol = atol = 10⁻¹⁰, commit 062b20c
        </span>
      </div>

      <div className="overflow-x-auto">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="w-full min-w-[540px] h-auto select-none"
          role="img"
          aria-label="Logarithmic dot chart of recorded Hamiltonian drift across seven presets"
        >
          {/* Vertical log grid lines */}
          {ticks.map((exp) => {
            const x = toX(Math.pow(10, exp));
            return (
              <g key={`tick-${exp}`}>
                <line
                  x1={x}
                  y1={topPad - 6}
                  x2={x}
                  y2={height - bottomPad + 6}
                  stroke="var(--plot-grid)"
                  strokeWidth="1"
                  strokeDasharray="2 3"
                />
                <text
                  x={x}
                  y={height - 12}
                  textAnchor="middle"
                  fill="var(--muted)"
                  fontSize="10"
                  fontFamily="var(--font-mono)"
                >
                  10^{exp}
                </text>
              </g>
            );
          })}

          {/* Rows */}
          {RECORDED_DRIFTS.map((item, idx) => {
            const y = topPad + idx * rowHeight + rowHeight / 2;
            const x = toX(item.driftValue);
            const dotColor =
              item.tone === "prograde"
                ? "var(--prograde)"
                : item.tone === "retrograde"
                ? "var(--retrograde)"
                : "var(--foreground)";

            return (
              <g key={item.id}>
                <line
                  x1={leftPad}
                  y1={y}
                  x2={width - rightPad}
                  y2={y}
                  stroke="var(--border-subtle)"
                  strokeWidth="0.75"
                />
                <text
                  x={leftPad - 10}
                  y={y + 4}
                  textAnchor="end"
                  fill="var(--foreground)"
                  fontSize="11"
                  fontFamily="var(--font-sans)"
                >
                  {item.label}
                </text>
                <circle cx={x} cy={y} r={4.5} fill={dotColor} />
                <text
                  x={width - rightPad + 10}
                  y={y + 4}
                  textAnchor="start"
                  fill="var(--foreground-secondary)"
                  fontSize="10.5"
                  fontFamily="var(--font-mono)"
                >
                  {item.driftText}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
    </figure>
  );
}

export default function ValidationPage() {
  return (
    <div className="flex flex-col flex-1 pb-24">
      {/* Header */}
      <header className="border-b border-[var(--border)] bg-[var(--surface)] py-8 sm:py-10 px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-6xl space-y-3">
          <h1 className="font-serif text-3xl sm:text-4xl font-normal text-[var(--foreground)] tracking-tight">
            Validation and verification
          </h1>
          <p className="prose-notebook text-[var(--foreground-secondary)]">
            Audit ledger of analytical identities, numerical regression checks, recorded preset
            drifts, and the boundaries of what those checks establish.
          </p>
          <p className="text-xs font-sans text-[var(--muted)] tabular-nums pt-1">
            v1.0.0 baseline recorded 2026-11-19 (commit{" "}
            <span className="font-mono text-[var(--foreground)]">062b20c</span>): 4,440 tests
            passed (4,412 core + 28 API/gallery); 4,511 tests are currently collected in the
            repository after deployment safeguard additions.
          </p>
        </div>
      </header>

      <div className="mx-auto max-w-6xl w-full px-4 sm:px-6 lg:px-8 mt-10 space-y-14">
        {/* 1. Audit Ledger */}
        <section className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            <div className="lg:col-span-8 space-y-2">
              <h2 className="font-serif text-2xl font-normal text-[var(--foreground)]">
                1. Audit ledger: analytical checks vs. numerical tests
              </h2>
              <p className="text-sm font-sans text-[var(--foreground-secondary)] leading-relaxed">
                Analytical checks test exact algebraic identities at single points without stepping.
                Numerical regression checks test integrated trajectories and root-finding tolerances.
              </p>
            </div>
            <div className="lg:col-span-4">
              <MarginNote label="What tests establish">
                Passing regression tests verify internal algebraic consistency and solver
                tolerances against reference formulas. They do not constitute independent
                peer review or external astrophysical validation.
              </MarginNote>
            </div>
          </div>

          <div className="overflow-x-auto border-y border-[var(--border)]">
            <table className="w-full text-left text-xs sm:text-[13px] font-sans">
              <thead>
                <tr className="border-b border-[var(--border)] text-xs font-medium text-[var(--muted)]">
                  <th className="py-2.5 pr-4">Kind</th>
                  <th className="py-2.5 px-4">Claim</th>
                  <th className="py-2.5 px-4">Measured / bound</th>
                  <th className="py-2.5 px-4">Conditions</th>
                  <th className="py-2.5 pl-4">Source (commit 062b20c)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border-subtle)] tabular-nums">
                {AUDIT_LEDGER.map((row) => (
                  <tr key={row.claim}>
                    <td className="py-3 pr-4 font-medium text-[var(--foreground-secondary)] whitespace-nowrap">
                      {row.category}
                    </td>
                    <td className="py-3 px-4 font-medium text-[var(--foreground)]">{row.claim}</td>
                    <td className="py-3 px-4 font-mono text-xs text-[var(--foreground)] whitespace-nowrap">
                      {row.measured}
                    </td>
                    <td className="py-3 px-4 text-[var(--foreground-secondary)]">
                      {row.conditions}
                    </td>
                    <td className="py-3 pl-4 font-mono text-xs whitespace-nowrap">
                      <a
                        href={row.sourceUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-[var(--accent)] hover:underline underline-offset-2"
                      >
                        {row.sourceLabel}
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* 2. Per-Preset Recorded Drift */}
        <section className="space-y-5 border-t border-[var(--border)] pt-10">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            <div className="lg:col-span-8 space-y-2">
              <h2 className="font-serif text-2xl font-normal text-[var(--foreground)]">
                2. Per-preset recorded Hamiltonian drift
              </h2>
              <p className="text-sm font-sans text-[var(--foreground-secondary)] leading-relaxed">
                Across the seven recorded default preset runs, maximum observed Hamiltonian drift is
                approximately <span className="font-medium text-[var(--foreground)]">4 × 10⁻¹³</span>{" "}
                (highest on the unbound scattering run at{" "}
                <span className="font-mono text-xs">3.88 × 10⁻¹³</span>).
              </p>
            </div>
            <div className="lg:col-span-4">
              <MarginNote label="Run-specific bound">
                Explicit Runge–Kutta methods are non-symplectic. Drift is kept small by adaptive
                error control, not forbidden by construction, and depends on orbit geometry and
                span.
              </MarginNote>
            </div>
          </div>

          <LogDriftChart />

          <div className="overflow-x-auto border-y border-[var(--border)]">
            <table className="w-full text-left text-xs sm:text-[13px] font-sans tabular-nums">
              <thead>
                <tr className="border-b border-[var(--border)] text-xs font-medium text-[var(--muted)]">
                  <th className="py-2.5 pr-4">Preset</th>
                  <th className="py-2.5 px-4">Recorded parameters</th>
                  <th className="py-2.5 px-4 text-right">Measured |ΔH|</th>
                  <th className="py-2.5 pl-4 text-right">Explorer</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border-subtle)]">
                {RECORDED_DRIFTS.map((row) => (
                  <tr key={row.id}>
                    <td className="py-2.5 pr-4 font-medium text-[var(--foreground)]">{row.label}</td>
                    <td className="py-2.5 px-4 font-mono text-xs text-[var(--foreground-secondary)]">
                      {row.params}
                    </td>
                    <td
                      className={`py-2.5 px-4 text-right font-mono text-xs font-medium ${
                        row.tone === "prograde"
                          ? "text-[var(--prograde)]"
                          : row.tone === "retrograde"
                          ? "text-[var(--retrograde)]"
                          : "text-[var(--foreground)]"
                      }`}
                    >
                      {row.driftText}
                    </td>
                    <td className="py-2.5 pl-4 text-right">
                      <Link
                        href={`/explorer?preset=${row.id}`}
                        className="text-xs text-[var(--accent)] hover:underline underline-offset-2"
                      >
                        Open
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* 3. Numerical Method & Event Localization */}
        <section className="space-y-4 border-t border-[var(--border)] pt-10">
          <h2 className="font-serif text-2xl font-normal text-[var(--foreground)]">
            3. Numerical solvers and event root refinement
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 text-sm font-sans text-[var(--foreground-secondary)] leading-relaxed">
            <div className="space-y-2">
              <h3 className="font-serif text-lg text-[var(--foreground)]">
                Adaptive explicit Runge–Kutta solvers
              </h3>
              <p>
                The engine delegates ODE integration to{" "}
                <span className="font-mono text-xs text-[var(--foreground)]">
                  scipy.integrate.solve_ivp
                </span>
                . The default method is{" "}
                <span className="font-mono text-xs text-[var(--foreground)]">DOP853</span>{" "}
                (Dormand–Prince 8(5,3), 12 stages per step,{" "}
                <span className="font-mono text-xs">rtol = atol = 10⁻¹⁰</span>). Additional SciPy
                methods supported by the core engine are{" "}
                <span className="font-mono text-xs">RK45</span> (Dormand–Prince 5(4)),{" "}
                <span className="font-mono text-xs">RK23</span>,{" "}
                <span className="font-mono text-xs">Radau</span>,{" "}
                <span className="font-mono text-xs">BDF</span>, and{" "}
                <span className="font-mono text-xs">LSODA</span>.
              </p>
            </div>

            <div className="space-y-2">
              <h3 className="font-serif text-lg text-[var(--foreground)]">
                Dense-output event refinement
              </h3>
              <p>
                When an event function changes sign across an integration step,{" "}
                <span className="font-mono text-xs text-[var(--foreground)]">
                  scipy.optimize.brentq
                </span>{" "}
                refines the root to <span className="font-mono text-xs">xtol = rtol = 4ε</span> on
                SciPy&apos;s continuous dense-output polynomial interpolant, recording the full 8D
                phase-space vector <span className="font-mono text-xs">[t, r, θ, φ, p_t, p_r, p_θ, p_φ]</span>.
              </p>
            </div>
          </div>
        </section>

        {/* 4. What Is Not Claimed (Equal Weight) */}
        <section className="space-y-5 border-t border-[var(--border)] pt-10">
          <h2 className="font-serif text-2xl font-normal text-[var(--foreground)]">
            4. What is not claimed
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 text-sm font-sans text-[var(--foreground-secondary)] leading-relaxed">
            <div className="border-t border-[var(--border-subtle)] pt-3 space-y-1.5">
              <h3 className="font-serif text-base text-[var(--foreground)]">
                No external peer review or observational comparison
              </h3>
              <p>
                The solver models classical vacuum test-particle geodesics. It does not include
                magnetohydrodynamic accretion flows, radiative transfer, or telescope-calibrated
                observational comparisons.
              </p>
            </div>

            <div className="border-t border-[var(--border-subtle)] pt-3 space-y-1.5">
              <h3 className="font-serif text-base text-[var(--foreground)]">
                Coordinate projections are not isometric embeddings
              </h3>
              <p>
                2D coordinate plots (<span className="font-mono text-xs">x = r sinθ cosφ</span>,{" "}
                <span className="font-mono text-xs">y = r sinθ sinφ</span>) display Boyer–Lindquist
                coordinates rather than isometric Riemannian embeddings of curved space.
              </p>
            </div>

            <div className="border-t border-[var(--border-subtle)] pt-3 space-y-1.5">
              <h3 className="font-serif text-base text-[var(--foreground)]">
                Sub-extremal spin &amp; horizon coordinate boundary
              </h3>
              <p>
                Boyer–Lindquist coordinates are singular at{" "}
                <span className="font-mono text-xs">r = r_+</span>, so integration halts at{" "}
                <span className="font-mono text-xs">r_+ + ε</span>. API presets enforce{" "}
                <span className="font-mono text-xs">|a| &lt; M</span> (with{" "}
                <span className="font-mono text-xs">0 ≤ a ≤ M</span> on retrograde photon).
              </p>
            </div>

            <div className="border-t border-[var(--border-subtle)] pt-3 space-y-1.5">
              <h3 className="font-serif text-base text-[var(--foreground)]">
                Non-symplectic drift over unbounded spans
              </h3>
              <p>
                Because explicit Runge–Kutta integrators do not preserve a symplectic form, secular
                drift in conserved quantities will accumulate over sufficiently long integration
                spans or near-horizon plunges.
              </p>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
