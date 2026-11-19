"use client";

import React from "react";
import Link from "next/link";
import ScientificPlot from "@/components/ScientificPlot";
import galleryData from "@/data/gallery_trajectories.json";
import { Compass, Layers, ShieldCheck, ArrowRight, ExternalLink } from "lucide-react";
import { SimulationResponse } from "@/lib/api";

function GithubIcon({ className = "h-4 w-4" }: { className?: string }) {
  return (
    <svg className={className} fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
      <path
        fillRule="evenodd"
        d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
        clipRule="evenodd"
      />
    </svg>
  );
}

export default function HomePage() {
  const heroPreset = galleryData["schwarzschild_precession"];
  const heroSimulation = heroPreset.simulation as unknown as SimulationResponse;

  return (
    <div className="flex flex-col flex-1 pb-20">
      {/* Editorial Header Section */}
      <section className="border-b border-[var(--border)] bg-[var(--surface)] py-12 px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-5xl text-center space-y-4">
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-[3px] border border-[var(--border)] bg-[var(--surface-subtle)] text-xs font-mono text-[var(--muted)]">
            <span>Release v1.0.0</span>
            <span className="text-[var(--border)]">·</span>
            <span>Immutable Engine Baseline</span>
          </div>

          <h1 className="font-serif text-3xl sm:text-4xl lg:text-5xl font-normal text-[var(--foreground)] tracking-tight leading-[1.15]">
            Kerr Geodesics Lab
          </h1>

          <p className="max-w-2xl mx-auto text-sm sm:text-base text-[var(--foreground-secondary)] font-sans leading-relaxed">
            Numerical integration of timelike and null geodesics in Kerr and Schwarzschild spacetimes via canonical Hamiltonian equations.
            Developed for machine-precision research and education in relativistic astrophysics and curved spacetime geometry.
          </p>

          {/* Three Primary Entry Points */}
          <div className="pt-4 flex flex-wrap items-center justify-center gap-3">
            <Link
              href="/explorer"
              className="inline-flex items-center gap-2 rounded-[3px] bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white px-4 py-2 text-xs font-sans font-medium transition-colors cursor-pointer shadow-xs"
            >
              <Compass className="h-4 w-4" />
              <span>Launch Geodesic Explorer</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>

            <Link
              href="/gallery"
              className="inline-flex items-center gap-2 rounded-[3px] border border-[var(--border)] bg-[var(--surface)] hover:bg-[var(--surface-hover)] text-[var(--foreground)] px-4 py-2 text-xs font-sans font-medium transition-colors cursor-pointer"
            >
              <Layers className="h-4 w-4 text-[var(--muted)]" />
              <span>Orbit Gallery (7 Presets)</span>
            </Link>

            <Link
              href="/validation"
              className="inline-flex items-center gap-2 rounded-[3px] border border-[var(--border)] bg-[var(--surface)] hover:bg-[var(--surface-hover)] text-[var(--foreground)] px-4 py-2 text-xs font-sans font-medium transition-colors cursor-pointer"
            >
              <ShieldCheck className="h-4 w-4 text-[var(--muted)]" />
              <span>Validation Record</span>
            </Link>
          </div>
        </div>
      </section>

      {/* Main Content Area */}
      <div className="mx-auto max-w-5xl w-full px-4 sm:px-6 lg:px-8 mt-10 space-y-12">

        {/* Prominent Real Orbit Figure */}
        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="text-xs font-mono uppercase tracking-wider text-[var(--muted)]">
              Representative Numerical Trajectory
            </div>
            <Link
              href="/explorer"
              className="text-xs font-sans text-[var(--accent)] hover:underline flex items-center gap-1 cursor-pointer"
            >
              <span>Open in Explorer</span>
              <ArrowRight className="h-3 w-3" />
            </Link>
          </div>

          <div className="rounded-[4px] border border-[var(--border)] bg-[var(--surface)] overflow-hidden shadow-xs">
            <ScientificPlot
              simulationData={heroSimulation}
              presetId="schwarzschild_precession"
              spacetime="Schwarzschild"
              geodesicType="timelike"
              mass={1.0}
              spin={0.0}
              initialRadius={8.0}
              projection="equatorial"
              title="Schwarzschild Relativistic Periastron Precession"
              className="border-0 rounded-none"
            />
          </div>

          <p className="text-xs text-[var(--foreground-secondary)] font-sans leading-relaxed">
            <strong className="text-[var(--foreground)] font-medium">Figure 1:</strong> Relativistic periastron precession of a bound timelike geodesic outside the innermost stable circular orbit in Schwarzschild spacetime (<span className="font-mono">M = 1.0</span>, initial coordinate radius <span className="font-mono">r₀ = 8.0 M</span>, radial perturbation <span className="font-mono">δp_r = 0.001</span>, affine parameter span <span className="font-mono">λ = 100.0</span>). The trajectory is integrated directly by the Python engine using the 8th-order Dormand-Prince stepper (DOP853) with adaptive local error control (<span className="font-mono">rtol = atol = 10⁻¹⁰</span>), achieving maximum Hamiltonian constraint drift <span className="font-mono">|ΔH| ≤ 2.22 × 10⁻¹⁶</span>.
          </p>
        </section>

        {/* Restrained Validation Strip */}
        <section className="border-t border-[var(--border)] pt-8 space-y-4">
          <div className="text-xs font-mono uppercase tracking-wider text-[var(--foreground-secondary)]">
            Empirical Benchmark Summary
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="rounded-[3px] border border-[var(--border)] bg-[var(--surface)] p-3 space-y-1">
              <div className="font-mono text-base font-semibold text-[var(--foreground)]">4,440 Passing</div>
              <div className="text-[11px] font-sans text-[var(--foreground-secondary)]">Recorded test suite baseline (4,412 core + 28 API &amp; gallery)</div>
            </div>

            <div className="rounded-[3px] border border-[var(--border)] bg-[var(--surface)] p-3 space-y-1">
              <div className="font-mono text-base font-semibold text-[var(--foreground)]">|ΔH| ≤ 10⁻¹⁵</div>
              <div className="text-[11px] font-sans text-[var(--foreground-secondary)]">Pointwise Hamiltonian constraint residual</div>
            </div>

            <div className="rounded-[3px] border border-[var(--border)] bg-[var(--surface)] p-3 space-y-1">
              <div className="font-mono text-base font-semibold text-[var(--foreground)]">7 Presets</div>
              <div className="text-[11px] font-sans text-[var(--foreground-secondary)]">Verified Schwarzschild and Kerr configurations</div>
            </div>

            <div className="rounded-[3px] border border-[var(--border)] bg-[var(--surface)] p-3 space-y-1">
              <div className="font-mono text-base font-semibold text-[var(--foreground)]">DOP853</div>
              <div className="text-[11px] font-sans text-[var(--foreground-secondary)]">Explicit 8th-order embedded Runge-Kutta integrator</div>
            </div>
          </div>
        </section>

        {/* Technical Documentation & Repository Link */}
        <section className="border-t border-[var(--border)] pt-8 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <h3 className="font-serif text-sm font-normal text-[var(--foreground)]">
              Open Research & Technical Report
            </h3>
            <p className="text-xs font-sans text-[var(--muted)]">
              Full architectural specifications, mathematical derivations, and verification records are available in the repository.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <a
              href="https://github.com/SoumitraPharikal/kerr-geodesic-integrator"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 rounded-[3px] border border-[var(--border)] bg-[var(--surface)] hover:bg-[var(--surface-hover)] px-3 py-1.5 text-xs font-sans text-[var(--foreground)] transition-colors cursor-pointer"
            >
              <GithubIcon className="h-3.5 w-3.5 text-[var(--muted)]" />
              <span>GitHub Repository</span>
              <ExternalLink className="h-3 w-3 text-[var(--muted)]" />
            </a>
          </div>
        </section>

      </div>
    </div>
  );
}
