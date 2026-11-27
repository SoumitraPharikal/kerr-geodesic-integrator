"use client";

import React from "react";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import ScientificPlot from "@/components/ScientificPlot";
import ReadoutList from "@/components/ReadoutList";
import MarginNote from "@/components/MarginNote";
import galleryData from "@/data/gallery_trajectories.json";
import { formatDrift, formatFloat } from "@/lib/format";
import { SimulationResponse } from "@/lib/api";

const RECORDED_PRESET_DRIFTS = [
  {
    id: "schwarzschild_isco_circular",
    name: "Schwarzschild ISCO circular orbit",
    spacetime: "Schwarzschild",
    drift: "< 1e-16",
    tone: "default" as const,
  },
  {
    id: "schwarzschild_precession",
    name: "Schwarzschild precession",
    spacetime: "Schwarzschild",
    drift: "2.22e-16",
    tone: "default" as const,
  },
  {
    id: "schwarzschild_photon_sphere",
    name: "Schwarzschild photon sphere",
    spacetime: "Schwarzschild",
    drift: "4.44e-16",
    tone: "default" as const,
  },
  {
    id: "kerr_equatorial_prograde_photon",
    name: "Kerr prograde photon orbit",
    spacetime: "Kerr (a = 0.9 M)",
    drift: "1.07e-14",
    tone: "prograde" as const,
  },
  {
    id: "kerr_equatorial_retrograde_photon",
    name: "Kerr retrograde photon orbit",
    spacetime: "Kerr (a = 0.9 M)",
    drift: "6.66e-16",
    tone: "retrograde" as const,
  },
  {
    id: "kerr_circular_timelike",
    name: "Kerr circular timelike orbit",
    spacetime: "Kerr (a = 0.9 M)",
    drift: "3.33e-16",
    tone: "prograde" as const,
  },
  {
    id: "kerr_equatorial_scattering",
    name: "Kerr equatorial scattering",
    spacetime: "Kerr (a = 0.5 M)",
    drift: "3.88e-13",
    tone: "prograde" as const,
  },
];

export default function HomePage() {
  const heroPreset = galleryData["kerr_equatorial_scattering"];
  const heroSimulation = heroPreset.simulation as unknown as SimulationResponse;

  const rValues = heroSimulation.trajectory.coordinates.r;
  const rMin = Math.min(...rValues);
  const rMax = Math.max(...rValues);

  return (
    <div className="flex flex-col flex-1 pb-24">
      {/* Asymmetric Instrument + Notebook Hero */}
      <section className="border-b border-[var(--border)] bg-[var(--surface)] py-12 sm:py-16 px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-7xl grid grid-cols-1 lg:grid-cols-12 gap-10 items-start">
          <div className="lg:col-span-5 space-y-6">
            <h1 className="font-serif text-3xl sm:text-4xl lg:text-[42px] font-normal text-[var(--foreground)] tracking-tight leading-[1.14]">
              A spinning black hole drags space around with it. This lab follows what happens next.
            </h1>

            <p className="prose-notebook text-[var(--foreground-secondary)]">
              I built Kerr Geodesics Lab to test how spacetime curvature and frame-dragging shape the
              motion of particles and light. You can inspect seven recorded Schwarzschild and Kerr
              presets, vary physical parameters against the Python integrator, and check conserved
              quantities along each orbit.
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
                href="/validation"
                className="inline-flex items-center gap-2 rounded-[2px] border border-[var(--border)] bg-[var(--background)] hover:bg-[var(--surface-hover)] text-[var(--foreground)] px-4 py-2 text-sm font-medium"
              >
                <span>Read the validation</span>
              </Link>
            </div>

            <nav aria-label="Quick links" className="pt-4 border-t border-[var(--border-subtle)] flex flex-wrap gap-x-6 gap-y-2 text-sm font-sans">
              <Link href="/gallery" className="text-[var(--foreground-secondary)] hover:text-[var(--foreground)] underline underline-offset-4">
                Orbit gallery
              </Link>
              <Link href="/mathematics" className="text-[var(--foreground-secondary)] hover:text-[var(--foreground)] underline underline-offset-4">
                Mathematical formulation
              </Link>
              <Link href="/docs" className="text-[var(--foreground-secondary)] hover:text-[var(--foreground)] underline underline-offset-4">
                API reference
              </Link>
              <Link href="/about" className="text-[var(--foreground-secondary)] hover:text-[var(--foreground)] underline underline-offset-4">
                About the project
              </Link>
            </nav>
          </div>

          {/* Dominant Trajectory Figure */}
          <div className="lg:col-span-7 space-y-3">
            <div className="border border-[var(--border)] bg-[var(--background)] rounded-[2px] overflow-hidden">
              <ScientificPlot
                simulationData={heroSimulation}
                presetId="kerr_equatorial_scattering"
                spacetime="Kerr"
                geodesicType="null"
                mass={1.0}
                spin={0.5}
                initialRadius={50.0}
                projection="equatorial"
                title="Kerr equatorial photon scattering"
                className="border-0 rounded-none"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-12 gap-6 pt-1">
              <p className="md:col-span-7 text-xs sm:text-[13px] text-[var(--foreground-secondary)] font-sans leading-relaxed">
                <strong className="font-medium text-[var(--foreground)]">Recorded output (commit 062b20c):</strong>{" "}
                An equatorial null ray enters from <span className="tabular-nums">r₀ = 50.0 M</span> with
                impact parameter <span className="tabular-nums">b = L_z / E = 4.5 M</span> around a Kerr
                black hole (<span className="tabular-nums">a = 0.5 M</span>), bends around closest
                approach <span className="tabular-nums">r_min = {formatFloat(rMin, 3)} M</span> near the
                prograde photon orbit, and escapes back to <span className="tabular-nums">{formatFloat(rMax, 1)} M</span>.
              </p>

              <div className="md:col-span-5">
                <ReadoutList
                  items={[
                    {
                      label: "Conserved energy",
                      value: formatFloat(heroSimulation.conserved_quantities.energy, 6),
                    },
                    {
                      label: "Axial angular momentum",
                      value: formatFloat(heroSimulation.conserved_quantities.angular_momentum, 6),
                      unit: "M",
                      tone: "prograde",
                    },
                    {
                      label: "Hamiltonian drift",
                      value: formatDrift(heroSimulation.conserved_quantities.hamiltonian_drift_max),
                    },
                    {
                      label: "Integrator, samples",
                      value: `${heroSimulation.solver_diagnostics.method}, ${heroSimulation.trajectory.lambdas.length}`,
                    },
                  ]}
                />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Main Editorial Sections */}
      <div className="mx-auto max-w-7xl w-full px-4 sm:px-6 lg:px-8 mt-14 space-y-16">
        {/* Seven Orbits, Checked */}
        <section className="grid grid-cols-1 lg:grid-cols-12 gap-8 border-t border-[var(--border)] pt-10">
          <div className="lg:col-span-4 space-y-3">
            <h2 className="font-serif text-2xl font-normal text-[var(--foreground)] tracking-tight">
              Seven orbits, checked
            </h2>
            <p className="text-sm font-sans text-[var(--foreground-secondary)] leading-relaxed">
              Maximum observed Hamiltonian drift: approximately{" "}
              <span className="tabular-nums font-medium text-[var(--foreground)]">4 × 10⁻¹³</span>{" "}
              across the seven recorded preset runs.
            </p>
            <MarginNote label="Recorded result">
              This bound summarizes the seven default preset snapshots recorded at commit{" "}
              <span className="font-mono text-[var(--foreground)]">062b20c</span>. It is not a
              universal guarantee for arbitrary initial conditions or integration spans.
            </MarginNote>
          </div>

          <div className="lg:col-span-8">
            <div className="overflow-x-auto border-y border-[var(--border)]">
              <table className="w-full text-left text-sm font-sans">
                <thead>
                  <tr className="border-b border-[var(--border)] text-xs font-medium text-[var(--muted)]">
                    <th className="py-2.5 pr-4">Preset</th>
                    <th className="py-2.5 px-4">Spacetime</th>
                    <th className="py-2.5 px-4 text-right">Recorded |ΔH|</th>
                    <th className="py-2.5 pl-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--border-subtle)] tabular-nums">
                  {RECORDED_PRESET_DRIFTS.map((row) => (
                    <tr key={row.id}>
                      <td className="py-2.5 pr-4 font-medium text-[var(--foreground)]">
                        {row.name}
                      </td>
                      <td
                        className={`py-2.5 px-4 ${
                          row.tone === "prograde"
                            ? "text-[var(--prograde)]"
                            : row.tone === "retrograde"
                            ? "text-[var(--retrograde)]"
                            : "text-[var(--foreground-secondary)]"
                        }`}
                      >
                        {row.spacetime}
                      </td>
                      <td className="py-2.5 px-4 text-right font-mono text-xs text-[var(--foreground)]">
                        {row.drift}
                      </td>
                      <td className="py-2.5 pl-4 text-right">
                        <Link
                          href={`/explorer?preset=${row.id}`}
                          className="text-xs text-[var(--accent)] hover:underline underline-offset-2"
                        >
                          Open Explorer
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>

        {/* How It Is Built & Methods / Limitations */}
        <section className="grid grid-cols-1 lg:grid-cols-12 gap-8 border-t border-[var(--border)] pt-10">
          <div className="lg:col-span-4 space-y-2">
            <h2 className="font-serif text-2xl font-normal text-[var(--foreground)] tracking-tight">
              How it is built, and what it does not do
            </h2>
          </div>

          <div className="lg:col-span-8 grid grid-cols-1 md:grid-cols-2 gap-8 text-sm font-sans text-[var(--foreground-secondary)] leading-relaxed">
            <div className="space-y-3">
              <h3 className="font-serif text-lg text-[var(--foreground)]">
                Python engine, FastAPI, interface
              </h3>
              <p>
                The Python engine computes the trajectories and physical quantities. The interface
                presents those results.
              </p>
              <p>
                Geodesics are integrated in 8D Boyer–Lindquist phase space using SciPy&apos;s{" "}
                <span className="font-mono text-[var(--foreground)]">solve_ivp</span> with the
                adaptive 8th-order <span className="font-mono text-[var(--foreground)]">DOP853</span>{" "}
                method by default. Because <span className="font-mono text-[var(--foreground)]">DOP853</span>{" "}
                is non-symplectic, drift is kept small by adaptive error control rather than forbidden
                by construction.
              </p>
            </div>

            <div className="space-y-3">
              <h3 className="font-serif text-lg text-[var(--foreground)]">
                Scope and limitations
              </h3>
              <ul className="space-y-2 list-disc pl-4">
                <li>
                  The seven interactive presets cover equatorial Schwarzschild and sub-extremal Kerr
                  orbits; off-equatorial trajectories are not exposed in the lab UI.
                </li>
                <li>
                  No general relativistic ray tracing, accretion-flow modeling, or external peer
                  review is claimed.
                </li>
                <li>
                  The <Link href="/shadows" className="underline underline-offset-2 hover:text-[var(--foreground)]">Shadow Lab</Link>{" "}
                  frontend remains a planned extension; its interface is not yet active.
                </li>
              </ul>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
