"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Compass, ExternalLink, Copy, Check } from "lucide-react";

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

function CodeBlock({ code, title }: { code: string; title?: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="rounded-[3px] border border-[var(--border)] bg-[var(--surface-subtle)] overflow-hidden my-3">
      {title && (
        <div className="flex items-center justify-between border-b border-[var(--border)] px-3.5 py-1.5 bg-[var(--surface)] text-[11px] font-mono text-[var(--foreground-secondary)]">
          <span>{title}</span>
          <button
            type="button"
            onClick={handleCopy}
            className="flex items-center gap-1 text-[var(--muted)] hover:text-[var(--foreground)] transition-colors cursor-pointer"
            title="Copy to clipboard"
          >
            {copied ? (
              <>
                <Check className="h-3 w-3 text-[var(--status-ok)]" />
                <span className="text-[10px]">Copied</span>
              </>
            ) : (
              <>
                <Copy className="h-3 w-3" />
                <span className="text-[10px]">Copy</span>
              </>
            )}
          </button>
        </div>
      )}
      <pre className="p-3.5 overflow-x-auto font-mono text-xs leading-relaxed text-[var(--foreground)]">
        <code>{code}</code>
      </pre>
    </div>
  );
}

export default function DocsPage() {
  return (
    <div className="flex flex-col flex-1 pb-20">
      {/* Editorial Header */}
      <div className="border-b border-[var(--border)] py-8 px-4 sm:px-6 lg:px-8 bg-[var(--surface)]">
        <div className="mx-auto max-w-5xl">
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-[3px] border border-[var(--border)] bg-[var(--surface-subtle)] text-xs font-mono text-[var(--foreground-secondary)] mb-3">
            <span>FastAPI 0.115+</span>
            <span className="text-[var(--border)]">·</span>
            <span>Python 3.10+</span>
            <span className="text-[var(--border)]">·</span>
            <span>Release v1.0.0</span>
          </div>

          <h1 className="font-serif text-3xl sm:text-4xl font-normal text-[var(--foreground)] tracking-tight">
            API &amp; Technical Reference
          </h1>
          <p className="text-sm sm:text-base text-[var(--foreground-secondary)] font-sans mt-2 max-w-3xl leading-relaxed">
            Stateless computational REST interface, schemas, and CLI operations for the Kerr Geodesic Integrator. All physical quantities are evaluated directly by the validated Python Hamiltonian engine.
          </p>
        </div>
      </div>

      <div className="mx-auto max-w-5xl w-full px-4 sm:px-6 lg:px-8 mt-10 space-y-12">
        {/* Section 1: Architecture Overview */}
        <section className="space-y-4">
          <h2 className="font-serif text-2xl font-normal text-[var(--foreground)] border-b border-[var(--border)] pb-2">
            1. System Architecture &amp; Separation of Concerns
          </h2>
          <p className="text-sm text-[var(--foreground-secondary)] leading-relaxed">
            Kerr Geodesics Lab enforces a strict three-tier separation of concerns. Physics calculations, numerical integration, Carter constant evaluations, and shadow boundaries are exclusively implemented in Python. The web client performs zero numerical physics.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
            <div className="rounded-[3px] border border-[var(--border)] bg-[var(--surface)] p-4 space-y-2">
              <div className="font-mono text-xs font-medium uppercase tracking-wider text-[var(--accent)]">
                Tier 1: Core Engine
              </div>
              <p className="text-xs text-[var(--foreground-secondary)] leading-relaxed">
                Python package (<code className="font-mono text-[11px] bg-[var(--surface-subtle)] px-1 rounded">geodesics</code>). First-order canonical Hamiltonian ODEs in Boyer-Lindquist coordinates with adaptive Dormand-Prince (DOP853) stepper.
              </p>
            </div>

            <div className="rounded-[3px] border border-[var(--border)] bg-[var(--surface)] p-4 space-y-2">
              <div className="font-mono text-xs font-medium uppercase tracking-wider text-[var(--accent)]">
                Tier 2: API Adapter
              </div>
              <p className="text-xs text-[var(--foreground-secondary)] leading-relaxed">
                FastAPI service (<code className="font-mono text-[11px] bg-[var(--surface-subtle)] px-1 rounded">geodesics.api</code>). Stateless serialization, schema validation with unphysical parameter rejection, and structured JSON responses.
              </p>
            </div>

            <div className="rounded-[3px] border border-[var(--border)] bg-[var(--surface)] p-4 space-y-2">
              <div className="font-mono text-xs font-medium uppercase tracking-wider text-[var(--accent)]">
                Tier 3: Research UI
              </div>
              <p className="text-xs text-[var(--foreground-secondary)] leading-relaxed">
                Next.js / React / TypeScript frontend. Form collection, SVG orbit projection, conserved quantity tables, and interactive parameter exploration.
              </p>
            </div>
          </div>
        </section>

        {/* Section 2: REST API Reference */}
        <section className="space-y-8">
          <div>
            <h2 className="font-serif text-2xl font-normal text-[var(--foreground)] border-b border-[var(--border)] pb-2">
              2. REST Endpoints
            </h2>
            <p className="text-sm text-[var(--foreground-secondary)] mt-2 leading-relaxed">
              Base URL: <code className="font-mono text-xs bg-[var(--surface-subtle)] px-1.5 py-0.5 rounded border border-[var(--border)]">http://127.0.0.1:8000</code>
            </p>
          </div>

          {/* Endpoint 1: GET /health */}
          <div className="rounded-[4px] border border-[var(--border)] bg-[var(--surface)] overflow-hidden">
            <div className="flex items-center gap-3 border-b border-[var(--border)] bg-[var(--surface-subtle)] px-4 py-3">
              <span className="font-mono text-xs font-semibold px-2 py-0.5 rounded-[2px] border border-[var(--border)] bg-[var(--surface)] text-[var(--foreground)]">
                GET
              </span>
              <span className="font-mono text-xs font-medium text-[var(--foreground)]">
                /health
              </span>
              <span className="text-xs text-[var(--muted)] font-sans ml-auto hidden sm:inline">
                Health &amp; Provenance
              </span>
            </div>

            <div className="p-5 space-y-3">
              <p className="text-xs text-[var(--foreground-secondary)] leading-relaxed">
                Returns runtime operational status, engine package name, software version, release git commit hash, and supported capabilities.
              </p>

              <CodeBlock
                title="Example Response (200 OK)"
                code={`{
  "status": "healthy",
  "engine": "kerr-geodesic-integrator",
  "version": "1.0.0",
  "commit_hash": "062b20c80a689640637a2fcd003bdd921a7d4132",
  "capabilities": {
    "schwarzschild": true,
    "kerr": true,
    "timelike": true,
    "null": true,
    "shadows": true
  }
}`}
              />
            </div>
          </div>

          {/* Endpoint 2: GET /api/v1/presets */}
          <div className="rounded-[4px] border border-[var(--border)] bg-[var(--surface)] overflow-hidden">
            <div className="flex items-center gap-3 border-b border-[var(--border)] bg-[var(--surface-subtle)] px-4 py-3">
              <span className="font-mono text-xs font-semibold px-2 py-0.5 rounded-[2px] border border-[var(--border)] bg-[var(--surface)] text-[var(--foreground)]">
                GET
              </span>
              <span className="font-mono text-xs font-medium text-[var(--foreground)]">
                /api/v1/presets
              </span>
              <span className="text-xs text-[var(--muted)] font-sans ml-auto hidden sm:inline">
                Preset Catalogue
              </span>
            </div>

            <div className="p-5 space-y-3">
              <p className="text-xs text-[var(--foreground-secondary)] leading-relaxed">
                Retrieves the catalogue of all 7 registered scientific presets with default physical parameters, descriptions, and spacetime classifications.
              </p>

              <CodeBlock
                title="Example Response (200 OK)"
                code={`{
  "presets": [
    {
      "id": "schwarzschild_precession",
      "name": "Schwarzschild Relativistic Periastron Precession",
      "spacetime": "Schwarzschild",
      "geodesic_type": "timelike",
      "description": "Bound eccentric orbit exhibiting advance of periastron (Mercury-like).",
      "default_parameters": {
        "mass": 1.0,
        "radius": 8.0,
        "delta_pr": 0.001,
        "affine_span": 100.0
      }
    },
    {
      "id": "kerr_prograde_equatorial",
      "name": "Kerr Prograde Equatorial Orbit",
      "spacetime": "Kerr",
      "geodesic_type": "timelike",
      "description": "Frame-dragging enhanced prograde timelike orbit around spinning black hole.",
      "default_parameters": {
        "mass": 1.0,
        "spin": 0.9,
        "radius": 6.0,
        "affine_span": 80.0
      }
    }
  ],
  "total_count": 7
}`}
              />
            </div>
          </div>

          {/* Endpoint 3: POST /api/v1/simulations */}
          <div className="rounded-[4px] border border-[var(--border)] bg-[var(--surface)] overflow-hidden">
            <div className="flex items-center gap-3 border-b border-[var(--border)] bg-[var(--surface-subtle)] px-4 py-3">
              <span className="font-mono text-xs font-semibold px-2 py-0.5 rounded-[2px] border border-[var(--border)] bg-[var(--surface)] text-[var(--foreground)]">
                POST
              </span>
              <span className="font-mono text-xs font-medium text-[var(--foreground)]">
                /api/v1/simulations
              </span>
              <span className="text-xs text-[var(--muted)] font-sans ml-auto hidden sm:inline">
                Geodesic Integration
              </span>
            </div>

            <div className="p-5 space-y-3">
              <p className="text-xs text-[var(--foreground-secondary)] leading-relaxed">
                Integrates canonical geodesic equations from initial coordinates and momenta. Accepts either a <code className="font-mono text-[11px] bg-[var(--surface-subtle)] px-1 rounded">preset_id</code> with optional parameter overrides, or explicit initial phase space coordinates. Returns sampled coordinate trajectories, conserved Killing quantities, Hamiltonian drift metrics, and root-evaluated termination events.
              </p>

              <CodeBlock
                title="Example Request Payload"
                code={`{
  "preset_id": "schwarzschild_precession",
  "parameters": {
    "mass": 1.0,
    "radius": 8.0,
    "delta_pr": 0.001,
    "affine_span": 100.0
  }
}`}
              />

              <CodeBlock
                title="Example Response Schema"
                code={`{
  "trajectory": {
    "lambdas": [0.0, 0.05, 0.1, ...],
    "coordinates": {
      "t": [0.0, 0.057, 0.115, ...],
      "r": [8.0, 7.999, 7.996, ...],
      "theta": [1.570796, 1.570796, ...],
      "phi": [0.0, 0.0078, 0.0156, ...]
    }
  },
  "conserved_quantities": {
    "energy": 0.957427,
    "angular_momentum": 3.464102,
    "carter_constant": 0.0,
    "hamiltonian_drift_max": 2.14e-11
  },
  "solver_diagnostics": {
    "method": "DOP853",
    "nfev": 1432,
    "rtol": 1e-10,
    "atol": 1e-10
  },
  "triggered_events": [
    {
      "name": "radial_turning_point",
      "lambda_val": 34.215,
      "r": 5.421,
      "theta": 1.570796,
      "phi": 3.842
    }
  ],
  "provenance": {
    "engine": "kerr-geodesic-integrator",
    "version": "1.0.0",
    "commit_hash": "062b20c80a689640637a2fcd003bdd921a7d4132"
  },
  "config_hash": "8f4e2b17a94d8c6..."
}`}
              />
            </div>
          </div>

          {/* Endpoint 4: POST /api/v1/shadows */}
          <div className="rounded-[4px] border border-[var(--border)] bg-[var(--surface)] overflow-hidden">
            <div className="flex items-center gap-3 border-b border-[var(--border)] bg-[var(--surface-subtle)] px-4 py-3">
              <span className="font-mono text-xs font-semibold px-2 py-0.5 rounded-[2px] border border-[var(--border)] bg-[var(--surface)] text-[var(--foreground)]">
                POST
              </span>
              <span className="font-mono text-xs font-medium text-[var(--foreground)]">
                /api/v1/shadows
              </span>
              <span className="text-xs text-[var(--muted)] font-sans ml-auto hidden sm:inline">
                Kerr Shadow Calculation
              </span>
            </div>

            <div className="p-5 space-y-3">
              <p className="text-xs text-[var(--foreground-secondary)] leading-relaxed">
                Computes the exact analytical Bardeen Kerr shadow boundary coordinates <span className="font-serif italic">(α, β)</span> in the celestial observer plane for given black hole spin <span className="font-serif italic">a</span> and observer inclination angle <span className="font-serif italic">θ_obs</span>.
              </p>

              <CodeBlock
                title="Example Request Payload"
                code={`{
  "mass": 1.0,
  "spin": 0.9,
  "inclination_deg": 90.0,
  "n_points": 200
}`}
              />

              <CodeBlock
                title="Example Response Schema"
                code={`{
  "alpha": [-5.12, -5.08, -4.92, ...],
  "beta": [0.0, 0.42, 0.85, ...],
  "mass": 1.0,
  "spin": 0.9,
  "inclination_deg": 90.0,
  "horizon_r_plus": 1.435889,
  "shadow_width": 9.874,
  "shadow_height": 9.542
}`}
              />
            </div>
          </div>
        </section>

        {/* Section 3: CLI Commands & Local Development */}
        <section className="space-y-4">
          <h2 className="font-serif text-2xl font-normal text-[var(--foreground)] border-b border-[var(--border)] pb-2">
            3. Local Commands &amp; Verification Suite
          </h2>
          <p className="text-sm text-[var(--foreground-secondary)] leading-relaxed">
            The Python engine and frontend interface include reproducible test harnesses and local development servers:
          </p>

          <div className="space-y-3 pt-1">
            <div>
              <div className="text-xs font-medium font-sans text-[var(--foreground)] mb-1">
                Run Engine &amp; API Regression Test Suite:
              </div>
              <CodeBlock code="pytest tests/" />
            </div>

            <div>
              <div className="text-xs font-medium font-sans text-[var(--foreground)] mb-1">
                Launch FastAPI Backend Server:
              </div>
              <CodeBlock code="uvicorn geodesics.api.app:app --host 127.0.0.1 --port 8000" />
            </div>

            <div>
              <div className="text-xs font-medium font-sans text-[var(--foreground)] mb-1">
                Build &amp; Run Next.js Production Client:
              </div>
              <CodeBlock code="cd frontend && npm run build && npx next start -p 3000" />
            </div>
          </div>
        </section>

        {/* Section 4: Repository Links */}
        <section className="border-t border-[var(--border)] pt-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="space-y-0.5 text-center sm:text-left">
            <div className="font-serif text-base text-[var(--foreground)]">
              Kerr Geodesics Lab Open Science Repository
            </div>
            <p className="text-xs text-[var(--muted)] font-sans">
              Source code, mathematical derivation notes, and test suites are open access under the MIT License.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Link
              href="/explorer"
              className="inline-flex items-center gap-1.5 rounded-[3px] bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white px-3.5 py-2 text-xs font-sans font-medium transition-colors cursor-pointer shadow-xs"
            >
              <Compass className="h-3.5 w-3.5" />
              <span>Launch Explorer</span>
            </Link>

            <a
              href="https://github.com/SoumitraPharikal/kerr-geodesic-integrator"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 rounded-[3px] border border-[var(--border)] bg-[var(--surface)] hover:bg-[var(--surface-hover)] px-3.5 py-2 text-xs font-sans text-[var(--foreground)] transition-colors cursor-pointer"
            >
              <GithubIcon className="h-3.5 w-3.5 text-[var(--foreground-secondary)]" />
              <span>GitHub</span>
              <ExternalLink className="h-3 w-3 text-[var(--muted)]" />
            </a>
          </div>
        </section>
      </div>
    </div>
  );
}
