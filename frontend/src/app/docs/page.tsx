"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Check, Copy, ExternalLink } from "lucide-react";
import MarginNote from "@/components/MarginNote";

const NAV_SECTIONS = [
  { id: "quickstart", label: "Quickstart" },
  { id: "base-url", label: "Base URL & OpenAPI" },
  { id: "health", label: "GET /health" },
  { id: "presets", label: "GET /api/v1/presets" },
  { id: "simulations", label: "POST /api/v1/simulations" },
  { id: "shadows", label: "POST /api/v1/shadows" },
  { id: "exports", label: "Exports & deployment" },
];

function CodeBlock({ code, title }: { code: string; title?: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  };

  return (
    <div className="rounded-[2px] border border-[var(--border)] bg-[var(--surface)] overflow-hidden my-3">
      <div className="flex items-center justify-between border-b border-[var(--border-subtle)] px-3.5 py-1.5 bg-[var(--surface-subtle)] text-[11px] font-sans text-[var(--foreground-secondary)]">
        <span>{title || "Snippet"}</span>
        <button
          type="button"
          onClick={handleCopy}
          aria-label={`Copy ${title || "code"}`}
          className="inline-flex items-center gap-1 text-[var(--muted)] hover:text-[var(--foreground)] cursor-pointer"
        >
          {copied ? (
            <>
              <Check className="h-3 w-3 text-[var(--status-ok)]" />
              <span>Copied</span>
            </>
          ) : (
            <>
              <Copy className="h-3 w-3" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>
      <pre className="p-3.5 overflow-x-auto font-mono text-xs leading-relaxed text-[var(--foreground)] tabular-nums">
        <code>{code}</code>
      </pre>
    </div>
  );
}

function RequestTabs({
  curlCode,
  pythonCode,
}: {
  curlCode: string;
  pythonCode: string;
}) {
  const [tab, setTab] = useState<"curl" | "python">("curl");

  return (
    <div className="space-y-2 my-3">
      <div className="flex items-center gap-2 border-b border-[var(--border-subtle)] text-xs font-sans">
        <button
          type="button"
          onClick={() => setTab("curl")}
          aria-pressed={tab === "curl"}
          className={`pb-1.5 px-1 border-b-2 cursor-pointer ${
            tab === "curl"
              ? "border-[var(--foreground)] text-[var(--foreground)] font-medium"
              : "border-transparent text-[var(--muted)] hover:text-[var(--foreground)]"
          }`}
        >
          curl
        </button>
        <button
          type="button"
          onClick={() => setTab("python")}
          aria-pressed={tab === "python"}
          className={`pb-1.5 px-1 border-b-2 cursor-pointer ${
            tab === "python"
              ? "border-[var(--foreground)] text-[var(--foreground)] font-medium"
              : "border-transparent text-[var(--muted)] hover:text-[var(--foreground)]"
          }`}
        >
          Python
        </button>
      </div>
      <CodeBlock
        title={tab === "curl" ? "curl request" : "Python (urllib) request"}
        code={tab === "curl" ? curlCode : pythonCode}
      />
    </div>
  );
}

export default function DocsPage() {
  return (
    <div className="flex flex-col flex-1 pb-24">
      {/* Header */}
      <header className="border-b border-[var(--border)] bg-[var(--surface)] py-8 sm:py-10 px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-7xl space-y-3">
          <h1 className="font-serif text-3xl sm:text-4xl font-normal text-[var(--foreground)] tracking-tight">
            API and developer reference
          </h1>
          <p className="prose-notebook text-[var(--foreground-secondary)]">
            Installation, FastAPI HTTP endpoints, request and response schemas, captured outputs,
            and local development commands for Kerr Geodesics Lab.
          </p>
        </div>
      </header>

      {/* Mobile Jump Links */}
      <nav
        aria-label="Documentation sections"
        className="lg:hidden border-b border-[var(--border)] bg-[var(--background)] px-4 sm:px-6 py-3"
      >
        <div className="flex flex-wrap gap-x-4 gap-y-1.5 text-xs font-sans">
          {NAV_SECTIONS.map((s) => (
            <a
              key={s.id}
              href={`#${s.id}`}
              className="text-[var(--foreground-secondary)] hover:text-[var(--foreground)] underline-offset-4 hover:underline"
            >
              {s.label}
            </a>
          ))}
        </div>
      </nav>

      {/* Main Layout: Sticky Endpoint List + Reference Body */}
      <div className="mx-auto max-w-7xl w-full px-4 sm:px-6 lg:px-8 mt-10 grid grid-cols-1 lg:grid-cols-12 gap-10 items-start">
        <aside className="hidden lg:block lg:col-span-3 sticky top-20 space-y-6">
          <nav aria-label="Endpoint list" className="space-y-1.5 border-l border-[var(--border)] pl-4">
            <div className="text-[11px] font-sans font-medium uppercase tracking-wider text-[var(--muted)] mb-2">
              Reference
            </div>
            {NAV_SECTIONS.map((s) => (
              <a
                key={s.id}
                href={`#${s.id}`}
                className="block py-1 text-[13px] font-sans text-[var(--foreground-secondary)] hover:text-[var(--foreground)]"
              >
                {s.label}
              </a>
            ))}
          </nav>

          <MarginNote label="Architecture">
            Python computes all trajectories and invariants; Next.js renders Explorer (live API) and
            Gallery (saved commit <span className="font-mono">062b20c</span> snapshots).
          </MarginNote>
        </aside>

        <article className="lg:col-span-9 space-y-14 min-w-0">
          {/* 1. Quickstart */}
          <section id="quickstart" className="scroll-mt-20 space-y-4">
            <h2 className="font-serif text-2xl font-normal text-[var(--foreground)] border-b border-[var(--border)] pb-2">
              Quickstart
            </h2>
            <p className="text-sm font-sans text-[var(--foreground-secondary)] leading-relaxed max-w-2xl">
              Requires Python <span className="font-mono text-xs text-[var(--foreground)]">&gt;= 3.11</span>{" "}
              (with <span className="font-mono text-xs">numpy&gt;=2.0.0</span>,{" "}
              <span className="font-mono text-xs">scipy&gt;=1.11.0</span>,{" "}
              <span className="font-mono text-xs">fastapi&gt;=0.115.0</span>) and Node.js 22 for
              the Next.js frontend.
            </p>
            <CodeBlock
              title="Three-command local setup"
              code={`# 1. Install the Python package with API and test dependencies
pip install -e ".[api,dev]"

# 2. Start the FastAPI backend (port 8000)
uvicorn geodesics.api.app:app --host 127.0.0.1 --port 8000

# 3. Start the Next.js frontend in another terminal (port 3000)
cd frontend && npm install && npm run dev`}
            />
          </section>

          {/* 2. Base URL & OpenAPI */}
          <section id="base-url" className="scroll-mt-20 space-y-3 border-t border-[var(--border)] pt-8">
            <h2 className="font-serif text-2xl font-normal text-[var(--foreground)]">
              Base URL and OpenAPI schema
            </h2>
            <div className="text-sm font-sans text-[var(--foreground-secondary)] space-y-2 leading-relaxed">
              <p>
                Local development defaults to{" "}
                <code className="font-mono text-xs text-[var(--foreground)]">http://127.0.0.1:8000</code>.
                The hosted Render Free backend runs at{" "}
                <code className="font-mono text-xs text-[var(--foreground)]">
                  https://kerr-geodesics-api.onrender.com
                </code>{" "}
                (containers spin down after 15 minutes of inactivity, causing a ~30–60s cold start
                on first contact).
              </p>
              <p className="flex flex-wrap items-center gap-x-4 gap-y-1">
                <a
                  href="http://127.0.0.1:8000/docs"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-[var(--accent)] hover:underline"
                >
                  <span>Local OpenAPI (/docs)</span>
                  <ExternalLink className="h-3 w-3" />
                </a>
                <a
                  href="https://kerr-geodesics-api.onrender.com/docs"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-[var(--accent)] hover:underline"
                >
                  <span>Hosted OpenAPI (/docs)</span>
                  <ExternalLink className="h-3 w-3" />
                </a>
              </p>
            </div>
          </section>

          {/* 3. GET /health */}
          <section id="health" className="scroll-mt-20 space-y-3 border-t border-[var(--border)] pt-8">
            <h2 className="font-serif text-2xl font-normal text-[var(--foreground)] font-mono text-xl">
              GET /health
            </h2>
            <p className="text-sm font-sans text-[var(--foreground-secondary)]">
              Returns service health, engine package identifier, version, and pinned release commit hash.
            </p>
            <CodeBlock
              title="Captured response (200 OK)"
              code={`{
  "status": "ok",
  "engine": "kerr-geodesics",
  "version": "1.0.0",
  "commit_hash": "062b20c80a689640637a2fcd003bdd921a7d4132"
}`}
            />
          </section>

          {/* 4. GET /api/v1/presets */}
          <section id="presets" className="scroll-mt-20 space-y-3 border-t border-[var(--border)] pt-8">
            <h2 className="font-serif text-2xl font-normal text-[var(--foreground)] font-mono text-xl">
              GET /api/v1/presets
            </h2>
            <p className="text-sm font-sans text-[var(--foreground-secondary)]">
              Returns the 7 registered Schwarzschild and Kerr presets with default parameters and
              Pydantic JSON schemas.
            </p>
            <CodeBlock
              title="Captured response excerpt (200 OK, 7 presets)"
              code={`{
  "presets": [
    {
      "id": "schwarzschild_precession",
      "name": "Schwarzschild Relativistic Periastron Precession",
      "description": "Bound eccentric timelike orbit exhibiting relativistic periastron precession outside ISCO (r > 6M, E < 1) in Schwarzschild spacetime.",
      "spacetime": "Schwarzschild",
      "geodesic_type": "timelike",
      "default_parameters": {
        "mass": 1.0,
        "radius": 8.0,
        "delta_pr": 0.001,
        "affine_span": 100.0
      }
    }
  ]
}`}
            />
          </section>

          {/* 5. POST /api/v1/simulations */}
          <section id="simulations" className="scroll-mt-20 space-y-4 border-t border-[var(--border)] pt-8">
            <h2 className="font-serif text-2xl font-normal text-[var(--foreground)] font-mono text-xl">
              POST /api/v1/simulations
            </h2>
            <p className="text-sm font-sans text-[var(--foreground-secondary)] leading-relaxed">
              Executes a stateless 8D Hamiltonian integration via{" "}
              <span className="font-mono text-xs text-[var(--foreground)]">DOP853</span> (adaptive,
              non-symplectic) and refines event roots with{" "}
              <span className="font-mono text-xs text-[var(--foreground)]">brentq</span> on SciPy&apos;s
              dense-output interpolant.
            </p>

            <div className="overflow-x-auto border-y border-[var(--border)]">
              <table className="w-full text-left text-xs sm:text-[13px] font-sans tabular-nums">
                <thead>
                  <tr className="border-b border-[var(--border)] text-xs font-medium text-[var(--muted)]">
                    <th className="py-2 pr-4">Field</th>
                    <th className="py-2 px-4">Type</th>
                    <th className="py-2 px-4">Units</th>
                    <th className="py-2 px-4">Default</th>
                    <th className="py-2 pl-4">Constraint</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--border-subtle)]">
                  <tr>
                    <td className="py-2 pr-4 font-mono text-xs">preset_id</td>
                    <td className="py-2 px-4">string</td>
                    <td className="py-2 px-4">—</td>
                    <td className="py-2 px-4">Required</td>
                    <td className="py-2 pl-4">One of the 7 registered preset IDs</td>
                  </tr>
                  <tr>
                    <td className="py-2 pr-4 font-mono text-xs">parameters.mass</td>
                    <td className="py-2 px-4">number</td>
                    <td className="py-2 px-4">M</td>
                    <td className="py-2 px-4">1.0</td>
                    <td className="py-2 pl-4">M &gt; 0</td>
                  </tr>
                  <tr>
                    <td className="py-2 pr-4 font-mono text-xs">parameters.spin</td>
                    <td className="py-2 px-4">number</td>
                    <td className="py-2 px-4">M</td>
                    <td className="py-2 px-4">0.9 / 0.5</td>
                    <td className="py-2 pl-4">|a| &lt; M (0 ≤ a ≤ M on retrograde photon)</td>
                  </tr>
                  <tr>
                    <td className="py-2 pr-4 font-mono text-xs">parameters.affine_span</td>
                    <td className="py-2 px-4">number</td>
                    <td className="py-2 px-4">λ</td>
                    <td className="py-2 px-4">Preset-specific</td>
                    <td className="py-2 pl-4">0 &lt; λ ≤ 100 (photon) or ≤ 500 (timelike/scattering)</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <RequestTabs
              curlCode={`curl -s -X POST http://127.0.0.1:8000/api/v1/simulations \\
  -H "Content-Type: application/json" \\
  -d '{"preset_id":"schwarzschild_precession","parameters":{"mass":1.0,"radius":8.0,"delta_pr":0.001,"affine_span":100.0}}'`}
              pythonCode={`import json, urllib.request
req = urllib.request.Request(
    "http://127.0.0.1:8000/api/v1/simulations",
    data=json.dumps({"preset_id": "schwarzschild_precession"}).encode(),
    headers={"Content-Type": "application/json"},
)
res = json.loads(urllib.request.urlopen(req, timeout=25).read())`}
            />

            <CodeBlock
              title="Captured response (200 OK, schwarzschild_precession)"
              code={`{
  "preset_id": "schwarzschild_precession",
  "config_hash": "30d74cea08590904e2301e4368518fa678a70d955c43f816c2542d475942b26f",
  "status": "completed",
  "termination_reason": "The solver successfully reached the end of the integration interval.",
  "solver_diagnostics": {
    "method": "DOP853",
    "nfev": 3032,
    "rtol": 1e-10,
    "atol": 1e-10
  },
  "conserved_quantities": {
    "energy": 0.9486835945139981,
    "angular_momentum": 3.5777087639996634,
    "carter_constant": 0.0,
    "hamiltonian_drift_max": 2.220446049250313e-16
  },
  "triggered_events": [
    {
      "name": "radial_turning_point",
      "lambda": 56.31911057776004,
      "t": 71.18806887886007,
      "r": 8.026878004400958,
      "theta": 1.5707963267948966,
      "phi": 3.1349173837326214,
      "terminal": false
    }
  ],
  "provenance": {
    "engine": "kerr-geodesics",
    "version": "1.0.0",
    "commit_hash": "062b20c80a689640637a2fcd003bdd921a7d4132"
  }
}`}
            />

            <CodeBlock
              title="Captured error response (HTTP 422, spin = 1.0 >= mass = 1.0)"
              code={`{
  "error_type": "unphysical_configuration",
  "message": "Kerr circular timelike orbit requires sub-extremal spin a < M (1.0), got spin = 1.0",
  "details": [
    {
      "loc": [],
      "message": "Kerr circular timelike orbit requires sub-extremal spin a < M (1.0), got spin = 1.0",
      "type": "value_error"
    }
  ]
}`}
            />
          </section>

          {/* 6. POST /api/v1/shadows */}
          <section id="shadows" className="scroll-mt-20 space-y-4 border-t border-[var(--border)] pt-8">
            <h2 className="font-serif text-2xl font-normal text-[var(--foreground)] font-mono text-xl">
              POST /api/v1/shadows
            </h2>
            <p className="text-sm font-sans text-[var(--foreground-secondary)] leading-relaxed">
              Computes the analytical Bardeen shadow boundary <span className="font-serif italic">(α, β)</span>{" "}
              for a distant observer. The backend endpoint is active; the{" "}
              <Link href="/shadows" className="underline underline-offset-2 hover:text-[var(--foreground)]">
                Shadow Lab
              </Link>{" "}
              frontend page remains a planned extension.
            </p>

            <div className="overflow-x-auto border-y border-[var(--border)]">
              <table className="w-full text-left text-xs sm:text-[13px] font-sans tabular-nums">
                <thead>
                  <tr className="border-b border-[var(--border)] text-xs font-medium text-[var(--muted)]">
                    <th className="py-2 pr-4">Field</th>
                    <th className="py-2 px-4">Type</th>
                    <th className="py-2 px-4">Units</th>
                    <th className="py-2 px-4">Default</th>
                    <th className="py-2 pl-4">Constraint</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--border-subtle)]">
                  <tr>
                    <td className="py-2 pr-4 font-mono text-xs">mass</td>
                    <td className="py-2 px-4">number</td>
                    <td className="py-2 px-4">M</td>
                    <td className="py-2 px-4">1.0</td>
                    <td className="py-2 pl-4">M &gt; 0</td>
                  </tr>
                  <tr>
                    <td className="py-2 pr-4 font-mono text-xs">spin</td>
                    <td className="py-2 px-4">number</td>
                    <td className="py-2 px-4">M</td>
                    <td className="py-2 px-4">0.9</td>
                    <td className="py-2 pl-4">|a| &lt; M</td>
                  </tr>
                  <tr>
                    <td className="py-2 pr-4 font-mono text-xs">observer_inclination</td>
                    <td className="py-2 px-4">number</td>
                    <td className="py-2 px-4">rad</td>
                    <td className="py-2 px-4">1.5708 (π/2)</td>
                    <td className="py-2 pl-4">0 &lt; θ_obs &lt; π</td>
                  </tr>
                  <tr>
                    <td className="py-2 pr-4 font-mono text-xs">num_points</td>
                    <td className="py-2 px-4">integer</td>
                    <td className="py-2 px-4">—</td>
                    <td className="py-2 px-4">500</td>
                    <td className="py-2 pl-4">10 ≤ num_points ≤ 2000</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <CodeBlock
              title="Captured response excerpt (200 OK, mass=1.0, spin=0.9, num_points=200)"
              code={`{
  "alpha": [6.832319, 6.828537, 6.817199, "..."],
  "beta": [0.0, 0.200449, 0.400569, "..."],
  "observables": {
    "area": 79.57286118261203,
    "centroid": [1.9327597720554517, 0.0],
    "width": 9.676740633922833,
    "height": 10.391923002286456
  },
  "provenance": {
    "engine": "kerr-geodesics",
    "version": "1.0.0",
    "commit_hash": "062b20c80a689640637a2fcd003bdd921a7d4132"
  },
  "config_hash": "28becc41071f08aca8b2f8a049282d672dc0ddabef3dd4e5e137f9c92dcd6983"
}`}
            />
          </section>

          {/* 7. Exports, Verification & Hosting */}
          <section id="exports" className="scroll-mt-20 space-y-4 border-t border-[var(--border)] pt-8">
            <h2 className="font-serif text-2xl font-normal text-[var(--foreground)]">
              Exports, verification commands, and hosting
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 text-sm font-sans text-[var(--foreground-secondary)] leading-relaxed">
              <div className="space-y-2">
                <h3 className="font-serif text-lg text-[var(--foreground)]">
                  Explorer CSV &amp; JSON exports
                </h3>
                <p>
                  CSV exports contain unrounded samples with columns{" "}
                  <span className="font-mono text-xs text-[var(--foreground)]">
                    lambda, t, r, theta, phi, p_t, p_r, p_theta, p_phi, x_equatorial, y_equatorial
                  </span>
                  . JSON exports contain the full <span className="font-mono text-xs">SimulationResponse</span>{" "}
                  including solver diagnostics, events, and provenance.
                </p>
              </div>
              <div className="space-y-2">
                <h3 className="font-serif text-lg text-[var(--foreground)]">
                  Free-tier deployment configuration
                </h3>
                <p>
                  The backend deploys on Render Free (<span className="font-mono text-xs">render.yaml</span>,{" "}
                  <span className="font-mono text-xs">branch: master</span>,{" "}
                  <span className="font-mono text-xs">autoDeployTrigger: off</span>, fail-closed{" "}
                  <span className="font-mono text-xs">CORS_ALLOWED_ORIGINS</span> in production). The
                  frontend deploys on Vercel Hobby from <span className="font-mono text-xs">frontend/</span>{" "}
                  with <span className="font-mono text-xs">NEXT_PUBLIC_API_BASE_URL</span> inlined at
                  build time.
                </p>
              </div>
            </div>

            <CodeBlock
              title="Local verification commands"
              code={`# Python test suite
python -m pytest tests/

# Frontend typecheck, lint, tests, and build
cd frontend && npx tsc --noEmit && npm run lint && npm test && npm run build`}
            />

            <p className="text-sm font-sans text-[var(--foreground-secondary)]">
              For equations and solver details, see{" "}
              <Link href="/mathematics" className="text-[var(--accent)] hover:underline">
                Mathematics
              </Link>{" "}
              and{" "}
              <Link href="/validation" className="text-[var(--accent)] hover:underline">
                Validation
              </Link>
              .
            </p>
          </section>
        </article>
      </div>
    </div>
  );
}
