"use client";

import React from "react";
import { ExternalLink, Copy, Check } from "lucide-react";

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

export default function AboutPage() {
  const [copied, setCopied] = React.useState(false);

  const bibtex = `@software{pharikal2026kerr,
  author       = {Pharikal, Soumitra},
  title        = {Kerr Geodesics Lab: Numerical Integration of Curved Spacetime Geodesics},
  year         = {2026},
  version      = {v1.0.0},
  publisher    = {GitHub},
  url          = {https://github.com/SoumitraPharikal/kerr-geodesic-integrator}
}`;

  const handleCopyBibtex = () => {
    navigator.clipboard.writeText(bibtex);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex flex-col flex-1 pb-20">
      {/* Page Header */}
      <div className="border-b border-[var(--border)] py-8 px-4 sm:px-6 lg:px-8 bg-[var(--surface)]">
        <div className="mx-auto max-w-4xl">
          <h1 className="font-serif text-2xl sm:text-3xl lg:text-4xl font-normal text-[var(--foreground)] tracking-tight">
            About the Project
          </h1>
          <p className="text-xs sm:text-sm text-[var(--foreground-secondary)] font-sans mt-1.5 max-w-2xl leading-relaxed">
            Motivation, computational physics principles, and personal research background behind Kerr Geodesics Lab.
          </p>
        </div>
      </div>

      <div className="mx-auto max-w-4xl w-full px-4 sm:px-6 lg:px-8 mt-8 space-y-10">
        {/* Author Block */}
        <div className="rounded-[4px] border border-[var(--border)] bg-[var(--surface)] p-5 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="text-[10px] font-mono uppercase tracking-wider text-[var(--foreground-secondary)]">
              Author &amp; Maintainer
            </div>
            <div className="font-serif text-lg font-medium text-[var(--foreground)]">
              Soumitra Pharikal
            </div>
            <div className="text-xs font-sans text-[var(--foreground-secondary)]">
              BS-MS Physics, IISER Berhampur
            </div>
          </div>

          <div className="flex items-center gap-3">
            <a
              href="https://github.com/SoumitraPharikal/kerr-geodesic-integrator"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 rounded-[3px] border border-[var(--border)] bg-[var(--surface-subtle)] hover:bg-[var(--surface-hover)] px-3 py-1.5 text-xs font-sans text-[var(--foreground)] transition-colors cursor-pointer"
            >
              <GithubIcon className="h-3.5 w-3.5 text-[var(--muted)]" />
              <span>GitHub</span>
              <ExternalLink className="h-3 w-3 text-[var(--muted)]" />
            </a>
          </div>
        </div>

        {/* Essay Section 1: Why I Built This Project */}
        <section className="space-y-3 font-sans text-xs sm:text-sm text-[var(--foreground-secondary)] leading-relaxed">
          <h2 className="font-serif text-lg font-normal text-[var(--foreground)] tracking-tight">
            Why I Built This Project
          </h2>
          <p>
            I built Kerr Geodesics Lab to explore the mathematical structure and observational signatures of rotating black holes through exact, high-order numerical mechanics. While studying General Relativity, I found that many accessible educational tools either rely on post-Newtonian approximations or use low-order integration routines that fail to preserve non-trivial first integrals over extended dynamical timescales.
          </p>
          <p>
            I wanted to create an instrument where numerical trajectories respect the underlying Killing symmetries of curved spacetime to machine precision. By casting the geodesic equations into canonical Hamiltonian form and using embedded 8th-order Runge-Kutta steppers with rigorous local error control, the integrator preserves energy, angular momentum, and the Carter constant across thousands of orbital revolutions without unphysical secular drift.
          </p>
        </section>

        {/* Essay Section 2: Physical & Numerical Questions */}
        <section className="space-y-3 font-sans text-xs sm:text-sm text-[var(--foreground-secondary)] leading-relaxed">
          <h2 className="font-serif text-lg font-normal text-[var(--foreground)] tracking-tight">
            Physical &amp; Numerical Questions Explored
          </h2>
          <ul className="list-disc pl-5 space-y-2 text-xs sm:text-sm text-[var(--muted)]">
            <li>
              <strong className="text-[var(--foreground)]">Frame-Dragging and Photon Orbits:</strong> How does black hole spin <span className="font-mono text-[var(--foreground)]">a</span> split the degenerate Schwarzschild photon sphere into distinct prograde (<span className="font-mono text-[var(--foreground)]">r_ph⁺</span>) and retrograde (<span className="font-mono text-[var(--foreground)]">r_ph⁻</span>) circular null orbits?
            </li>
            <li>
              <strong className="text-[var(--foreground)]">Relativistic Periastron Precession:</strong> How does spacetime curvature outside the innermost stable circular orbit (ISCO) advance the periapsis of eccentric timelike orbits, producing rosette trajectories in Boyer-Lindquist coordinates?
            </li>
            <li>
              <strong className="text-[var(--foreground)]">Critical Photon Scattering:</strong> How does the asymptotic impact parameter <span className="font-mono text-[var(--foreground)]">b = L_z / E</span> govern the knife-edge boundary between horizon capture and escape back to spatial infinity?
            </li>
            <li>
              <strong className="text-[var(--foreground)]">Phase-Space Event Roots:</strong> How accurately can bracketed zero-finders isolate discrete physical transitions (radial turning points and horizon crossings) without interpolating from nearby steps?
            </li>
          </ul>
        </section>

        {/* Essay Section 3: Single-Source-of-Physics Architecture */}
        <section className="space-y-3 font-sans text-xs sm:text-sm text-[var(--foreground-secondary)] leading-relaxed">
          <h2 className="font-serif text-lg font-normal text-[var(--foreground)] tracking-tight">
            Role of the Validated Python Engine
          </h2>
          <p>
            A core principle of this project is strict separation of concerns: <strong className="text-[var(--foreground)]">the browser never computes physics</strong>. The Next.js frontend acts solely as an interactive scientific interface. Every trajectory point, four-momentum coordinate, conserved quantity, and event root is computed by the validated Python package (<span className="font-mono text-[var(--foreground)]">src/geodesics/</span>) and served via FastAPI.
          </p>
          <p>
            When a physical quantity (such as Kerr ISCO or horizon radii) is not supplied by the backend API schema, the frontend strictly omits those visual markers rather than attempting analytical derivations in TypeScript. This guarantees that every visual element displayed in the application reflects genuine physics engine output.
          </p>
        </section>

        {/* Essay Section 4: Current Status & Future Roadmap */}
        <section className="space-y-3 font-sans text-xs sm:text-sm text-[var(--foreground-secondary)] leading-relaxed">
          <h2 className="font-serif text-lg font-normal text-[var(--foreground)] tracking-tight">
            Implementation Scope &amp; Future Work
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
            <div className="rounded-[3px] border border-[var(--border)] bg-[var(--surface)] p-4 space-y-2">
              <div className="text-xs font-mono font-medium uppercase tracking-wider text-[var(--status-ok)]">
                Implemented (Release v1.0.0)
              </div>
              <ul className="text-xs text-[var(--muted)] space-y-1 list-disc pl-4 font-sans">
                <li>7 registered presets for Schwarzschild and Kerr metrics</li>
                <li>8th-order DOP853 and 5th-order RKCK45 adaptive steppers</li>
                <li>Exact event root-finding with 8D phase-space vectors</li>
                <li>Machine-precision Hamiltonian drift (|ΔH| ≤ 10⁻¹⁵)</li>
                <li>Raw CSV trajectory and JSON metadata export</li>
              </ul>
            </div>

            <div className="rounded-[3px] border border-[var(--border)] bg-[var(--surface)] p-4 space-y-2">
              <div className="text-xs font-mono font-medium uppercase tracking-wider text-[var(--accent)]">
                Future Extensions
              </div>
              <ul className="text-xs text-[var(--muted)] space-y-1 list-disc pl-4 font-sans">
                <li>Interactive Bardeen celestial shadow boundary contours</li>
                <li>Off-equatorial spherical photon orbits with Carter constant</li>
                <li>Gravitational-wave inspiral approximations (EMRI kludges)</li>
                <li>Kruskal-Szekeres and Kerr-Schild coordinate visualizers</li>
              </ul>
            </div>
          </div>
        </section>

        {/* Essay Section 5: Acknowledgements */}
        <section className="space-y-3 font-sans text-xs sm:text-sm text-[var(--foreground-secondary)] leading-relaxed">
          <h2 className="font-serif text-lg font-normal text-[var(--foreground)] tracking-tight">
            Acknowledgements &amp; References
          </h2>
          <p className="text-xs text-[var(--muted)] leading-relaxed">
            This work builds upon foundational research in relativistic mechanics and numerical astrophysics:
          </p>
          <ul className="list-disc pl-5 space-y-1.5 text-xs text-[var(--muted)]">
            <li>S. Chandrasekhar, <em>The Mathematical Theory of Black Holes</em>, Oxford University Press (1983).</li>
            <li>B. Carter, <em>Global structure of the Kerr family of gravitational fields</em>, Phys. Rev. 174, 1559 (1968).</li>
            <li>J. M. Bardeen, <em>Timelike and null geodesics in the Kerr metric</em>, Black Holes (Les Houches), 215–239 (1973).</li>
            <li>E. Hairer, S. P. Nørsett, and G. Wanner, <em>Solving Ordinary Differential Equations I: Nonstiff Problems</em>, Springer (1993).</li>
          </ul>
          <p className="text-xs text-[var(--muted)] pt-1">
            Built using Python, NumPy, SciPy, FastAPI, Pydantic, Next.js, React, Tailwind CSS, and KaTeX.
          </p>
        </section>

        {/* Section 6: Citation */}
        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="font-serif text-lg font-normal text-[var(--foreground)] tracking-tight">
              Citation
            </h2>
            <button
              type="button"
              onClick={handleCopyBibtex}
              className="inline-flex items-center gap-1 text-xs font-sans text-[var(--muted)] hover:text-[var(--foreground)] transition-colors cursor-pointer"
            >
              {copied ? <Check className="h-3.5 w-3.5 text-[var(--status-ok)]" /> : <Copy className="h-3.5 w-3.5" />}
              <span>{copied ? "Copied" : "Copy BibTeX"}</span>
            </button>
          </div>

          <div className="rounded-[3px] border border-[var(--border)] bg-[var(--surface-subtle)] p-4 overflow-x-auto">
            <pre className="text-xs font-mono text-[var(--foreground)] whitespace-pre tabular-nums">
              {bibtex}
            </pre>
          </div>
        </section>

        {/* Section 7: License */}
        <section className="border-t border-[var(--border)] pt-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="font-serif text-sm font-normal text-[var(--foreground)]">
              Open Source License
            </div>
            <p className="text-xs font-sans text-[var(--muted)]">
              Released under the permissive MIT License for academic, educational, and research use.
            </p>
          </div>

          <a
            href="https://github.com/SoumitraPharikal/kerr-geodesic-integrator/blob/master/LICENSE"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 rounded-[3px] border border-[var(--border)] bg-[var(--surface)] hover:bg-[var(--surface-hover)] px-3 py-1.5 text-xs font-sans text-[var(--foreground)] transition-colors cursor-pointer"
          >
            <span>MIT License</span>
            <ExternalLink className="h-3 w-3 text-[var(--muted)]" />
          </a>
        </section>
      </div>
    </div>
  );
}
