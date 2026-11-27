"use client";

import React from "react";
import Link from "next/link";
import { ArrowRight, Check, Copy, ExternalLink } from "lucide-react";
import MathBlock from "@/components/MathBlock";
import MarginNote from "@/components/MarginNote";

const REPO_URL = "https://github.com/SoumitraPharikal/kerr-geodesic-integrator";

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
  url          = {${REPO_URL}}
}`;

  const handleCopyBibtex = () => {
    navigator.clipboard.writeText(bibtex);
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  };

  return (
    <div className="flex flex-col flex-1 pb-24">
      {/* Header */}
      <header className="border-b border-[var(--border)] bg-[var(--surface)] py-10 sm:py-12 px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-6xl space-y-4">
          <h1 className="font-serif text-3xl sm:text-4xl lg:text-[42px] font-normal text-[var(--foreground)] tracking-tight leading-[1.15]">
            A path through curved spacetime.
          </h1>
          <p className="prose-notebook text-[var(--foreground-secondary)]">
            I built Kerr Geodesics Lab while studying general relativity and numerical physics. I
            wanted to connect the equations of motion to something I could inspect: an orbit, its
            turning points, and the quantities that should remain conserved along it.
          </p>
          <div className="flex flex-wrap items-center gap-3 pt-1 font-sans">
            <Link
              href="/explorer"
              className="inline-flex items-center gap-2 rounded-[2px] bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white px-4 py-2 text-sm font-medium"
            >
              <span>Open Explorer</span>
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="/mathematics"
              className="inline-flex items-center gap-2 rounded-[2px] border border-[var(--border)] bg-[var(--background)] hover:bg-[var(--surface-hover)] text-[var(--foreground)] px-4 py-2 text-sm font-medium"
            >
              <span>Read the mathematics</span>
            </Link>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-6xl w-full px-4 sm:px-6 lg:px-8 mt-12 space-y-14">
        {/* 1. Four questions */}
        <section className="grid grid-cols-1 lg:grid-cols-12 gap-8 border-t border-[var(--border)] pt-8">
          <div className="lg:col-span-4 space-y-2">
            <h2 className="font-serif text-2xl font-normal text-[var(--foreground)]">
              Questions the lab explores
            </h2>
          </div>
          <div className="lg:col-span-8 space-y-4">
            <ul className="space-y-3 text-sm font-sans text-[var(--foreground-secondary)] leading-relaxed list-disc pl-5">
              <li>
                <strong className="text-[var(--foreground)] font-medium">
                  Spin-split photon orbits:
                </strong>{" "}
                How black hole spin <MathBlock math="a" display={false} /> splits the circular photon
                sphere into distinct{" "}
                <span className="text-[var(--prograde)] font-medium">prograde</span> (
                <MathBlock math="r_{\rm ph}^+" display={false} />) and{" "}
                <span className="text-[var(--retrograde)] font-medium">retrograde</span> (
                <MathBlock math="r_{\rm ph}^-" display={false} />) radii.
              </li>
              <li>
                <strong className="text-[var(--foreground)] font-medium">
                  Strong-field orbital precession:
                </strong>{" "}
                How bound timelike orbits outside the innermost stable circular orbit depart from
                closed Newtonian ellipses.
              </li>
              <li>
                <strong className="text-[var(--foreground)] font-medium">
                  Equatorial photon capture and scattering:
                </strong>{" "}
                Where the boundary between horizon capture and escape lies in terms of the impact
                parameter <MathBlock math="b = L_z / E" display={false} /> for equatorial photons.
              </li>
              <li>
                <strong className="text-[var(--foreground)] font-medium">
                  Numerical turning points and horizon cutoffs:
                </strong>{" "}
                Where an orbit reverses radial direction (<MathBlock math="p_r = 0" display={false} />)
                or approaches the coordinate horizon, and what its 8D phase-space state is there.
              </li>
            </ul>
          </div>
        </section>

        {/* 2. How it works & Architecture */}
        <section className="grid grid-cols-1 lg:grid-cols-12 gap-8 border-t border-[var(--border)] pt-8">
          <div className="lg:col-span-4 space-y-3">
            <h2 className="font-serif text-2xl font-normal text-[var(--foreground)]">
              How it is built
            </h2>
            <MarginNote label="Live vs. saved">
              Explorer runs live integrations against the Python API. Gallery displays saved
              snapshots recorded at commit <span className="font-mono">062b20c</span>.
            </MarginNote>
          </div>
          <div className="lg:col-span-8 space-y-4 prose-notebook text-[var(--foreground-secondary)]">
            <p>
              The Python engine formulates geodesic motion using Hamilton&apos;s equations in
              Boyer–Lindquist coordinates. It integrates the resulting 8D system with adaptive
              numerical methods (<span className="font-mono text-sm">DOP853</span> by default) and
              refines event roots with <span className="font-mono text-sm">brentq</span> on
              SciPy&apos;s dense-output interpolant.
            </p>
            <p>
              The numerical methods are <strong>non-symplectic</strong>, so conservation of{" "}
              <MathBlock math="E" display={false} />, <MathBlock math="L_z" display={false} />,{" "}
              <MathBlock math="\mathcal{Q}" display={false} />, and{" "}
              <MathBlock math="\mathcal{H}" display={false} /> is not exact by construction. Across
              the seven recorded preset runs, measured Hamiltonian drift is at most approximately{" "}
              <MathBlock math="4 \times 10^{-13}" display={false} /> (see{" "}
              <Link href="/validation" className="text-[var(--accent)] hover:underline">
                Validation
              </Link>{" "}
              for per-preset results and limits).
            </p>
            <div className="border-y border-[var(--border-subtle)] py-3 font-mono text-xs text-[var(--foreground)]">
              Python engine (src/geodesics) → FastAPI (geodesics.api) → Next.js interface
            </div>
            <p className="text-sm font-sans">
              The browser renders trajectories, readouts, and analytical reference surfaces without
              independently integrating orbits. For endpoints and deployment details, see{" "}
              <Link href="/docs" className="text-[var(--accent)] hover:underline">
                Docs
              </Link>
              .
            </p>
          </div>
        </section>

        {/* 3. Scope & Limitations */}
        <section className="grid grid-cols-1 lg:grid-cols-12 gap-8 border-t border-[var(--border)] pt-8">
          <div className="lg:col-span-4">
            <h2 className="font-serif text-2xl font-normal text-[var(--foreground)]">
              Scope and limitations
            </h2>
          </div>
          <div className="lg:col-span-8 grid grid-cols-1 sm:grid-cols-2 gap-8 text-sm font-sans text-[var(--foreground-secondary)] leading-relaxed">
            <div className="space-y-2">
              <h3 className="font-serif text-lg text-[var(--foreground)]">Implemented</h3>
              <ul className="list-disc pl-4 space-y-1.5">
                <li>Seven equatorial Schwarzschild and sub-extremal Kerr presets</li>
                <li>Live Explorer integration with CSV and JSON export</li>
                <li>Static Gallery snapshots with conserved-quantity readouts</li>
                <li>
                  Backend analytical shadow boundary endpoint (
                  <span className="font-mono text-xs">POST /api/v1/shadows</span>)
                </li>
              </ul>
            </div>
            <div className="space-y-2">
              <h3 className="font-serif text-lg text-[var(--foreground)]">
                Not implemented or claimed
              </h3>
              <ul className="list-disc pl-4 space-y-1.5">
                <li>
                  The{" "}
                  <Link href="/shadows" className="underline underline-offset-2 hover:text-[var(--foreground)]">
                    Shadow Lab
                  </Link>{" "}
                  frontend UI remains a planned placeholder
                </li>
                <li>No inclined (off-equatorial) presets in the current lab UI</li>
                <li>No full numerical relativity, ray tracing, or accretion-disk modeling</li>
                <li>No external peer review or observational fitting claimed</li>
              </ul>
            </div>
          </div>
        </section>

        {/* 4. Author */}
        <section className="grid grid-cols-1 lg:grid-cols-12 gap-8 border-t border-[var(--border)] pt-8">
          <div className="lg:col-span-4">
            <h2 className="font-serif text-2xl font-normal text-[var(--foreground)]">
              Author
            </h2>
          </div>
          <div className="lg:col-span-8 flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-y border-[var(--border)] py-5">
            <div className="space-y-1">
              <div className="font-serif text-lg text-[var(--foreground)]">Soumitra Pharikal</div>
              <div className="text-sm font-sans text-[var(--foreground-secondary)]">
                BS-MS Physics student at IISER Berhampur, interested in general relativity and
                computational physics.
              </div>
            </div>
            <a
              href={REPO_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 rounded-[2px] border border-[var(--border)] bg-[var(--surface)] hover:bg-[var(--surface-hover)] px-3 py-1.5 text-xs font-sans text-[var(--foreground)] shrink-0 self-start sm:self-auto"
            >
              <GithubIcon className="h-3.5 w-3.5 text-[var(--muted)]" />
              <span>GitHub</span>
              <ExternalLink className="h-3 w-3 text-[var(--muted)]" />
            </a>
          </div>
        </section>

        {/* 5. References, Citation & License */}
        <section className="grid grid-cols-1 lg:grid-cols-12 gap-8 border-t border-[var(--border)] pt-8">
          <div className="lg:col-span-4">
            <h2 className="font-serif text-2xl font-normal text-[var(--foreground)]">
              References and license
            </h2>
          </div>
          <div className="lg:col-span-8 space-y-8">
            <ul className="list-disc pl-5 space-y-1.5 text-xs sm:text-sm font-sans text-[var(--foreground-secondary)] leading-relaxed">
              <li>
                S. Chandrasekhar, <em>The Mathematical Theory of Black Holes</em>, Oxford University
                Press (1983).
              </li>
              <li>
                B. Carter, <em>Global structure of the Kerr family of gravitational fields</em>, Phys.
                Rev. 174, 1559 (1968).
              </li>
              <li>
                J. M. Bardeen, W. H. Press, and S. A. Teukolsky,{" "}
                <em>Rotating black holes: locally nonrotating frames, energy extraction, and scalar synchrotron radiation</em>,
                Astrophys. J. 178, 347 (1972).
              </li>
              <li>
                J. M. Bardeen, <em>Timelike and null geodesics in the Kerr metric</em>, Black Holes
                (Les Houches), 215–239 (1973).
              </li>
              <li>
                J. R. Dormand and P. J. Prince,{" "}
                <em>A family of embedded Runge-Kutta formulae</em>, J. Comput. Appl. Math. 6, 19–26
                (1980).
              </li>
              <li>
                E. Hairer, S. P. Nørsett, and G. Wanner,{" "}
                <em>Solving Ordinary Differential Equations I: Nonstiff Problems</em>, Springer (1993).
              </li>
            </ul>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-sans font-medium uppercase tracking-wider text-[var(--muted)]">
                  Citation (BibTeX)
                </span>
                <button
                  type="button"
                  onClick={handleCopyBibtex}
                  className="inline-flex items-center gap-1 text-xs font-sans text-[var(--muted)] hover:text-[var(--foreground)] cursor-pointer"
                >
                  {copied ? (
                    <Check className="h-3.5 w-3.5 text-[var(--status-ok)]" />
                  ) : (
                    <Copy className="h-3.5 w-3.5" />
                  )}
                  <span>{copied ? "Copied" : "Copy BibTeX"}</span>
                </button>
              </div>
              <pre className="rounded-[2px] border border-[var(--border)] bg-[var(--surface)] p-4 overflow-x-auto text-xs font-mono text-[var(--foreground)] tabular-nums">
                {bibtex}
              </pre>
            </div>

            <div className="border-t border-[var(--border-subtle)] pt-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs font-sans text-[var(--muted)]">
              <span>Released under the MIT License (release tag v1.0.0).</span>
              <a
                href={`${REPO_URL}/blob/master/LICENSE`}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-[var(--foreground)] hover:underline"
              >
                <span>MIT License</span>
                <ExternalLink className="h-3 w-3 text-[var(--muted)]" />
              </a>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
