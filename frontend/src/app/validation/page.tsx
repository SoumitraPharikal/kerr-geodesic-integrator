"use client";

import React from "react";
import { ShieldCheck, BookOpen, ExternalLink, Info, AlertTriangle } from "lucide-react";

export default function ValidationPage() {
  return (
    <div className="flex flex-col flex-1 pb-20">
      {/* Header */}
      <div className="border-b border-[var(--border)] py-8 px-4 sm:px-6 lg:px-8 bg-[var(--surface)]">
        <div className="mx-auto max-w-5xl">
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-[3px] border border-[var(--border)] bg-[var(--surface-subtle)] text-xs font-mono text-[var(--foreground-secondary)] mb-3">
            <span>Recorded Test Baseline</span>
            <span className="text-[var(--border)]">·</span>
            <span className="text-[var(--status-ok)] font-medium">4,440 / 4,440 Passing</span>
          </div>

          <h1 className="font-serif text-2xl sm:text-3xl lg:text-4xl font-normal text-[var(--foreground)] tracking-tight">
            Validation &amp; Verification Record
          </h1>
          <p className="text-xs sm:text-sm text-[var(--foreground-secondary)] font-sans mt-1.5 max-w-3xl leading-relaxed">
            Traceable numerical tolerances, Hamiltonian invariant bounds, and mathematical consistency audits established in the Kerr Geodesic Integrator test suite.
          </p>
        </div>
      </div>

      <div className="mx-auto max-w-5xl w-full px-4 sm:px-6 lg:px-8 mt-8 space-y-12">
        {/* Authoritative Recorded Baseline Notice */}
        <div className="rounded-[4px] border border-[var(--border)] bg-[var(--surface)] p-5 space-y-3 shadow-xs">
          <div className="flex items-center justify-between border-b border-[var(--border)] pb-3">
            <div className="flex items-center gap-2.5">
              <ShieldCheck className="h-5 w-5 text-[var(--status-ok)]" />
              <h2 className="font-serif text-base font-normal text-[var(--foreground)]">
                Recorded Regression Baseline (2026-11-19)
              </h2>
            </div>
            <span className="font-mono text-xs text-[var(--foreground-secondary)]">
              Tag: v1.0.0 (commit 062b20c8)
            </span>
          </div>

          <p className="text-xs text-[var(--foreground-secondary)] font-sans leading-relaxed">
            All figures below represent <strong className="text-[var(--foreground)] font-medium">recorded regression test results</strong> extracted directly from the Python test suite (<span className="font-mono text-[var(--foreground)]">tests/test_*.py</span>) and the accompanying 43-page architectural audit report. They are not client-side simulations.
          </p>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-1 font-mono text-xs">
            <div className="p-2.5 rounded-[3px] bg-[var(--surface-subtle)] border border-[var(--border)]">
              <div className="text-[10px] text-[var(--foreground-secondary)] font-sans uppercase">Core Engine Tests</div>
              <div className="font-semibold text-sm text-[var(--foreground)] mt-0.5">4,412 passed</div>
              <div className="text-[10px] text-[var(--muted)] mt-0.5 font-sans">0 failed, 0 skipped</div>
            </div>

            <div className="p-2.5 rounded-[3px] bg-[var(--surface-subtle)] border border-[var(--border)]">
              <div className="text-[10px] text-[var(--foreground-secondary)] font-sans uppercase">API &amp; Gallery Tests</div>
              <div className="font-semibold text-sm text-[var(--foreground)] mt-0.5">28 passed</div>
              <div className="text-[10px] text-[var(--muted)] mt-0.5 font-sans">100% endpoint coverage</div>
            </div>

            <div className="p-2.5 rounded-[3px] bg-[var(--surface-subtle)] border border-[var(--border)]">
              <div className="text-[10px] text-[var(--foreground-secondary)] font-sans uppercase">Total Suite</div>
              <div className="font-semibold text-sm text-[var(--status-ok)] mt-0.5">4,440 passing</div>
              <div className="text-[10px] text-[var(--muted)] mt-0.5 font-sans">pytest regression run</div>
            </div>

            <div className="p-2.5 rounded-[3px] bg-[var(--surface-subtle)] border border-[var(--border)]">
              <div className="text-[10px] text-[var(--foreground-secondary)] font-sans uppercase">Release Provenance</div>
              <div className="font-semibold text-sm text-[var(--foreground)] mt-0.5">v1.0.0</div>
              <div className="text-[10px] text-[var(--muted)] mt-0.5 font-sans">Annotated release tag</div>
            </div>
          </div>
        </div>

        {/* Section 1: Clear Separation of Pointwise Algebraic Checks vs. Trajectory Drift */}
        <section className="space-y-4">
          <div className="border-b border-[var(--border)] pb-2">
            <h3 className="font-serif text-lg font-normal text-[var(--foreground)]">
              1. Invariant Preservation: Algebraic Consistency vs. Trajectory Drift
            </h3>
            <p className="text-xs text-[var(--muted)] font-sans mt-0.5">
              Rigorous separation between instantaneous single-point identities and continuous numerical integration errors.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Subsection A: Pointwise Algebraic Invariants */}
            <div className="rounded-[4px] border border-[var(--border)] bg-[var(--surface)] p-4 space-y-3">
              <div className="text-xs font-mono font-medium uppercase tracking-wider text-[var(--foreground)]">
                A. Pointwise Algebraic Identities
              </div>
              <p className="text-xs text-[var(--muted)] font-sans leading-relaxed">
                Evaluated at discrete phase-space points without numerical stepping. Tests exact algebraic closure of the metric inverse, Christoffel symbols, and Hamiltonian constraint.
              </p>

              <div className="space-y-2.5 font-mono text-xs pt-1">
                <div className="p-2.5 rounded-[3px] bg-[var(--surface-subtle)] border border-[var(--border)] space-y-1">
                  <div className="flex justify-between items-center">
                    <span className="font-sans text-[var(--foreground)] font-medium">Pointwise Null Residual |H|:</span>
                    <span className="text-[var(--status-ok)] font-semibold">≤ 10⁻¹⁵</span>
                  </div>
                  <div className="text-[11px] text-[var(--muted)] font-sans">
                    Assertion in <code className="text-[var(--foreground)]">test_hamiltonian.py:191</code> (exact null fixed-point).
                  </div>
                </div>

                <div className="p-2.5 rounded-[3px] bg-[var(--surface-subtle)] border border-[var(--border)] space-y-1">
                  <div className="flex justify-between items-center">
                    <span className="font-sans text-[var(--foreground)] font-medium">Carter Algebraic Match |ΔQ|:</span>
                    <span className="text-[var(--status-ok)] font-semibold">≤ 10⁻¹³</span>
                  </div>
                  <div className="text-[11px] text-[var(--muted)] font-sans">
                    Assertion in <code className="text-[var(--foreground)]">test_hamiltonian.py:869</code> (Killing tensor vs explicit form).
                  </div>
                </div>

                <div className="p-2.5 rounded-[3px] bg-[var(--surface-subtle)] border border-[var(--border)] space-y-1">
                  <div className="flex justify-between items-center">
                    <span className="font-sans text-[var(--foreground)] font-medium">Metric Inverse Identity ‖g·g⁻¹ - I‖:</span>
                    <span className="text-[var(--status-ok)] font-semibold">&lt; 10⁻¹⁵</span>
                  </div>
                  <div className="text-[11px] text-[var(--muted)] font-sans">
                    Assertion in <code className="text-[var(--foreground)]">test_metric.py:64</code> (Boyer-Lindquist contravariant inverse).
                  </div>
                </div>
              </div>
            </div>

            {/* Subsection B: Trajectory-Integrated Drift */}
            <div className="rounded-[4px] border border-[var(--border)] bg-[var(--surface)] p-4 space-y-3">
              <div className="text-xs font-mono font-medium uppercase tracking-wider text-[var(--foreground)]">
                B. Trajectory-Integrated Conservation Drift
              </div>
              <p className="text-xs text-[var(--muted)] font-sans leading-relaxed">
                Evaluated along continuous numerical solutions over hundreds of affine parameter units. Measures accumulation of truncation and roundoff errors across thousands of integrator steps.
              </p>

              <div className="space-y-2.5 font-mono text-xs pt-1">
                <div className="p-2.5 rounded-[3px] bg-[var(--surface-subtle)] border border-[var(--border)] space-y-1">
                  <div className="flex justify-between items-center">
                    <span className="font-sans text-[var(--foreground)] font-medium">Schwarzschild Precession Drift:</span>
                    <span className="text-[var(--accent)] font-semibold">2.22 × 10⁻¹⁶</span>
                  </div>
                  <div className="text-[11px] text-[var(--muted)] font-sans">
                    Observed in <code className="text-[var(--foreground)]">test_api.py:412</code> over λ = 100 with DOP853.
                  </div>
                </div>

                <div className="p-2.5 rounded-[3px] bg-[var(--surface-subtle)] border border-[var(--border)] space-y-1">
                  <div className="flex justify-between items-center">
                    <span className="font-sans text-[var(--foreground)] font-medium">Kerr Prograde Photon Drift:</span>
                    <span className="text-[var(--accent)] font-semibold">1.07 × 10⁻¹⁴</span>
                  </div>
                  <div className="text-[11px] text-[var(--muted)] font-sans">
                    Observed in <code className="text-[var(--foreground)]">test_api.py:111</code> (circular null orbit at a = 0.9).
                  </div>
                </div>

                <div className="p-2.5 rounded-[3px] bg-[var(--surface-subtle)] border border-[var(--border)] space-y-1">
                  <div className="flex justify-between items-center">
                    <span className="font-sans text-[var(--foreground)] font-medium">Asymptotic Scattering Drift:</span>
                    <span className="text-[var(--accent)] font-semibold">3.88 × 10⁻¹³</span>
                  </div>
                  <div className="text-[11px] text-[var(--muted)] font-sans">
                    Observed in <code className="text-[var(--foreground)]">test_api.py:114</code> over λ = 200 with r₀ = 50 M.
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Section 2: Numerical Stepper Specifications */}
        <section className="space-y-4">
          <div className="border-b border-[var(--border)] pb-2">
            <h3 className="font-serif text-lg font-normal text-[var(--foreground)]">
              2. Numerical Steppers &amp; Error Control
            </h3>
            <p className="text-xs text-[var(--muted)] font-sans mt-0.5">
              Embedded explicit Runge-Kutta formulations implemented via SciPy integration routines.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="rounded-[4px] border border-[var(--border)] bg-[var(--surface)] p-4 space-y-3">
              <div className="flex items-center justify-between">
                <span className="font-serif text-base font-normal text-[var(--foreground)]">
                  DOP853: Dormand-Prince 8(5,3)
                </span>
                <span className="font-mono text-xs text-[var(--accent)]">8th Order</span>
              </div>
              <p className="text-xs text-[var(--muted)] font-sans leading-relaxed">
                An explicit 8th-order Runge-Kutta method featuring embedded 5th- and 3rd-order error estimators with 12 stages per step. Designed for high-precision bound orbits to suppress secular phase error.
              </p>
              <div className="pt-2 border-t border-[var(--border)] space-y-1 font-mono text-xs text-[11px]">
                <div className="flex justify-between"><span className="text-[var(--muted)] font-sans">Implementation:</span><span className="text-[var(--foreground)]">scipy.integrate.DOP853</span></div>
                <div className="flex justify-between"><span className="text-[var(--muted)] font-sans">Local Error Order:</span><span className="text-[var(--foreground)]">O(h⁸) truncation</span></div>
                <div className="flex justify-between"><span className="text-[var(--muted)] font-sans">Default Tolerances:</span><span className="text-[var(--foreground)]">rtol = 10⁻¹⁰, atol = 10⁻¹⁰</span></div>
              </div>
            </div>

            <div className="rounded-[4px] border border-[var(--border)] bg-[var(--surface)] p-4 space-y-3">
              <div className="flex items-center justify-between">
                <span className="font-serif text-base font-normal text-[var(--foreground)]">
                  RKCK45: Cash-Karp 5(4)
                </span>
                <span className="font-mono text-xs text-[var(--accent)]">5th Order</span>
              </div>
              <p className="text-xs text-[var(--muted)] font-sans leading-relaxed">
                A 6-stage Cash-Karp embedded Runge-Kutta formula with 5th-order step propagation and 4th-order error estimation. Ideal for rapid step adjustments in strong gravitational potential gradients.
              </p>
              <div className="pt-2 border-t border-[var(--border)] space-y-1 font-mono text-xs text-[11px]">
                <div className="flex justify-between"><span className="text-[var(--muted)] font-sans">Implementation:</span><span className="text-[var(--foreground)]">scipy.integrate.RK45 (Cash-Karp)</span></div>
                <div className="flex justify-between"><span className="text-[var(--muted)] font-sans">Local Error Order:</span><span className="text-[var(--foreground)]">O(h⁵) truncation</span></div>
                <div className="flex justify-between"><span className="text-[var(--muted)] font-sans">Default Tolerances:</span><span className="text-[var(--foreground)]">rtol = 10⁻⁸, atol = 10⁻¹⁰</span></div>
              </div>
            </div>
          </div>
        </section>

        {/* Section 3: Event Root-Finding Precision */}
        <section className="space-y-4">
          <div className="border-b border-[var(--border)] pb-2">
            <h3 className="font-serif text-lg font-normal text-[var(--foreground)]">
              3. Event Root-Finding &amp; Phase-Space State Preservation
            </h3>
            <p className="text-xs text-[var(--muted)] font-sans mt-0.5">
              Exact root isolation using bracketed Brent-Dekker zero finding.
            </p>
          </div>

          <div className="rounded-[4px] border border-[var(--border)] bg-[var(--surface)] p-5 space-y-3 text-xs font-sans">
            <p className="text-[var(--muted)] leading-relaxed">
              When a trajectory encounters a physical boundary (outer event horizon <span className="font-mono text-[var(--foreground)]">r = r₊</span>, escape sphere <span className="font-mono text-[var(--foreground)]">r = r_esc</span>, or radial turning point <span className="font-mono text-[var(--foreground)]">dr/dλ = 0</span>), the solver isolates the event root via Brentq zero-finding.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1 font-mono">
              <div className="p-3 rounded-[3px] bg-[var(--surface-subtle)] border border-[var(--border)]">
                <div className="text-[10px] text-[var(--muted)] font-sans uppercase">Root Tolerance</div>
                <div className="font-semibold text-sm text-[var(--foreground)] mt-0.5">&lt; 10⁻¹⁰</div>
                <div className="text-[10px] text-[var(--muted-light)] mt-0.5 font-sans">Verified in tests/test_events.py</div>
              </div>

              <div className="p-3 rounded-[3px] bg-[var(--surface-subtle)] border border-[var(--border)]">
                <div className="text-[10px] text-[var(--muted)] font-sans uppercase">Phase-Space State</div>
                <div className="font-semibold text-sm text-[var(--foreground)] mt-0.5">8 Components</div>
                <div className="text-[10px] text-[var(--muted-light)] mt-0.5 font-sans">[t, r, θ, φ, p_t, p_r, p_θ, p_φ]</div>
              </div>

              <div className="p-3 rounded-[3px] bg-[var(--surface-subtle)] border border-[var(--border)]">
                <div className="text-[10px] text-[var(--muted)] font-sans uppercase">Root Evaluation</div>
                <div className="font-semibold text-sm text-[var(--status-ok)] mt-0.5">Exact Evaluation</div>
                <div className="text-[10px] text-[var(--muted-light)] mt-0.5 font-sans">No step interpolation</div>
              </div>
            </div>
          </div>
        </section>

        {/* Section 4: Known Scope Boundaries & Physical Limitations */}
        <section className="space-y-4">
          <div className="border-b border-[var(--border)] pb-2">
            <h3 className="font-serif text-lg font-normal text-[var(--foreground)]">
              4. Known Scope Boundaries &amp; Methodological Limitations
            </h3>
            <p className="text-xs text-[var(--muted)] font-sans mt-0.5">
              Explicit physical and computational constraints governing this implementation.
            </p>
          </div>

          <div className="rounded-[4px] border border-[var(--border)] bg-[var(--surface)] p-5 space-y-4 text-xs font-sans">
            <div className="flex items-start gap-3">
              <AlertTriangle className="h-4 w-4 text-[var(--accent)] shrink-0 mt-0.5" />
              <div className="space-y-1">
                <h4 className="font-medium text-[var(--foreground)]">Coordinate Singularities in Boyer-Lindquist Coordinates</h4>
                <p className="text-[var(--muted)] leading-relaxed">
                  Boyer-Lindquist coordinates exhibit coordinate singularities at the outer event horizon <span className="font-mono text-[var(--foreground)]">r = r₊</span> (<span className="font-mono text-[var(--foreground)]">Δ = 0</span>, where <span className="font-mono text-[var(--foreground)]">g_rr → ∞</span>) and on the stationary limit surface (<span className="font-mono text-[var(--foreground)]">g_tt = 0</span>). The numerical integrator uses event detection to terminate integration as trajectories cross <span className="font-mono text-[var(--foreground)]">r₊ + ε</span>, preventing arithmetic overflow.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3 border-t border-[var(--border)] pt-3">
              <AlertTriangle className="h-4 w-4 text-[var(--accent)] shrink-0 mt-0.5" />
              <div className="space-y-1">
                <h4 className="font-medium text-[var(--foreground)]">Sub-Extremal Kerr Parameter Restriction</h4>
                <p className="text-[var(--muted)] leading-relaxed">
                  Simulations strictly enforce sub-extremal spin <span className="font-mono text-[var(--foreground)]">|a| &lt; M</span>. Configurations with <span className="font-mono text-[var(--foreground)]">|a| ≥ M</span> (extremal horizons or naked singularities) are rejected by parameter schema validators to preserve physical predictability.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3 border-t border-[var(--border)] pt-3">
              <AlertTriangle className="h-4 w-4 text-[var(--accent)] shrink-0 mt-0.5" />
              <div className="space-y-1">
                <h4 className="font-medium text-[var(--foreground)]">Coordinate Plots are Not Isometric Riemannian Embeddings</h4>
                <p className="text-[var(--muted)] leading-relaxed">
                  The equatorial 2D projections display coordinate values <span className="font-mono text-[var(--foreground)]">x = r sin(θ) cos(φ)</span> and <span className="font-mono text-[var(--foreground)]">y = r sin(θ) sin(φ)</span>. In curved spacetime, spatial geometry cannot be embedded isometrically into flat Euclidean planes without metric distortion.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3 border-t border-[var(--border)] pt-3">
              <Info className="h-4 w-4 text-[var(--muted)] shrink-0 mt-0.5" />
              <div className="space-y-1">
                <h4 className="font-medium text-[var(--foreground)]">No Claim of External Peer Review or Observational Data</h4>
                <p className="text-[var(--muted)] leading-relaxed">
                  This project models test-particle trajectories under classical vacuum General Relativity. It does not incorporate hydrodynamic accretion flows (GRMHD), radiation transport, or empirical telescope instrument responses.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Section 5: Technical Provenance & Report Link */}
        <section className="border-t border-[var(--border)] pt-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <h4 className="font-serif text-sm font-normal text-[var(--foreground)]">
              Full Mathematical Audit Report
            </h4>
            <p className="text-xs font-sans text-[var(--muted)]">
              Read the complete 43-page architectural audit report and equation derivations in the repository.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <a
              href="https://github.com/SoumitraPharikal/kerr-geodesic-integrator"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 rounded-[3px] border border-[var(--border)] bg-[var(--surface)] hover:bg-[var(--surface-hover)] px-3 py-1.5 text-xs font-sans text-[var(--foreground)] transition-colors cursor-pointer"
            >
              <BookOpen className="h-3.5 w-3.5 text-[var(--muted)]" />
              <span>Repository &amp; Audit Logs</span>
              <ExternalLink className="h-3 w-3 text-[var(--muted)]" />
            </a>
          </div>
        </section>
      </div>
    </div>
  );
}
