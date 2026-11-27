"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import ScientificPlot from "@/components/ScientificPlot";
import ReadoutList, { ReadoutItem } from "@/components/ReadoutList";
import MarginNote from "@/components/MarginNote";
import galleryData from "@/data/gallery_trajectories.json";
import { formatDrift, formatFloat, formatScientific } from "@/lib/format";
import { SimulationResponse } from "@/lib/api";

type FilterType = "all" | "schwarzschild" | "kerr" | "timelike" | "null";

const OBSERVATION_NOTES: Record<string, string> = {
  schwarzschild_isco_circular:
    "Marginally stable circular timelike orbit at r = 6.0 M; the recorded span (λ = 50.0) covers 0.766 of a revolution.",
  schwarzschild_precession:
    "Small-perturbation bound orbit (δp_r = 0.001) spanning r ∈ [8.000, 8.027] M over 0.886 of a revolution; a subtle departure from circularity rather than a multi-lap rosette.",
  schwarzschild_photon_sphere:
    "Unperturbed unstable circular null orbit at r = 3.0 M over 1.103 revolutions.",
  kerr_equatorial_prograde_photon:
    "Co-rotating unstable circular null orbit at r ≈ 1.558 M around a spinning black hole (a = 0.9 M), completing 9.143 revolutions.",
  kerr_equatorial_retrograde_photon:
    "Counter-rotating unstable circular null orbit at r ≈ 3.910 M (a = 0.9 M, L_z < 0), pushed outward relative to the prograde photon orbit.",
  kerr_circular_timelike:
    "Stable prograde circular timelike orbit at r = 6.0 M outside the Kerr ISCO (a = 0.9 M), covering 1.373 revolutions.",
  kerr_equatorial_scattering:
    "Equatorial photon launched inward from r₀ = 50.0 M with b = 4.5 M (a = 0.5 M); it reaches closest approach r ≈ 3.123 M near the prograde photon orbit before escaping back to 50.0 M.",
};

const PARAM_LABELS: Record<string, { label: string; unit?: string }> = {
  mass: { label: "Mass", unit: "M" },
  spin: { label: "Spin", unit: "M" },
  radius: { label: "Orbital radius", unit: "M" },
  r0: { label: "Initial radius", unit: "M" },
  delta_pr: { label: "Radial perturbation" },
  impact_parameter: { label: "Impact parameter", unit: "M" },
  energy: { label: "Photon energy" },
  affine_span: { label: "Affine span" },
};

export default function GalleryPage() {
  const presetList = Object.values(galleryData);
  const [filter, setFilter] = useState<FilterType>("all");
  const [selectedId, setSelectedId] = useState<string>(presetList[0].metadata.id);

  useEffect(() => {
    const syncFromHash = () => {
      const hash = window.location.hash.replace(/^#/, "");
      if (hash && presetList.some((p) => p.metadata.id === hash)) {
        setSelectedId(hash);
      }
    };
    queueMicrotask(syncFromHash);
    window.addEventListener("hashchange", syncFromHash);
    return () => window.removeEventListener("hashchange", syncFromHash);
  }, [presetList]);

  const filteredPresets = presetList.filter((item) => {
    if (filter === "schwarzschild") return item.metadata.spacetime.toLowerCase() === "schwarzschild";
    if (filter === "kerr") return item.metadata.spacetime.toLowerCase() === "kerr";
    if (filter === "timelike") return item.metadata.geodesic_type.toLowerCase() === "timelike";
    if (filter === "null") return item.metadata.geodesic_type.toLowerCase() === "null";
    return true;
  });

  const activeItem =
    filteredPresets.find((p) => p.metadata.id === selectedId) || filteredPresets[0] || presetList[0];

  const meta = activeItem.metadata;
  const sim = activeItem.simulation as unknown as SimulationResponse;
  const params = meta.default_parameters as Record<string, unknown>;
  const mass = (params.mass as number) ?? 1.0;
  const spin = (params.spin as number) ?? 0.0;
  const initR =
    (params.radius as number) ??
    (params.r0 as number) ??
    (params.impact_parameter as number) ??
    8.0;

  const isRetrograde = sim.conserved_quantities.angular_momentum < 0;
  const isKerr = meta.spacetime.toLowerCase() === "kerr";
  const directionTone: "default" | "prograde" | "retrograde" = !isKerr
    ? "default"
    : isRetrograde
    ? "retrograde"
    : "prograde";

  const paramReadouts: ReadoutItem[] = Object.entries(meta.default_parameters).map(
    ([key, val]) => {
      const mapping = PARAM_LABELS[key] ?? { label: key };
      return {
        label: mapping.label,
        value: typeof val === "number" ? String(val) : String(val),
        unit: mapping.unit,
      };
    }
  );

  const diagnosticReadouts: ReadoutItem[] = [
    {
      label: "Conserved energy",
      value: formatFloat(sim.conserved_quantities.energy, 6),
    },
    {
      label: "Axial angular momentum",
      value: formatFloat(sim.conserved_quantities.angular_momentum, 6),
      unit: "M",
      tone: directionTone,
    },
    {
      label: "Carter constant",
      value:
        sim.conserved_quantities.carter_constant !== null
          ? formatFloat(sim.conserved_quantities.carter_constant, 6)
          : "0.000000",
    },
    {
      label: "Measured Hamiltonian drift",
      value: formatDrift(sim.conserved_quantities.hamiltonian_drift_max),
    },
    {
      label: "Integrator",
      value: sim.solver_diagnostics.method,
    },
    {
      label: "Function evaluations",
      value: sim.solver_diagnostics.nfev,
    },
    {
      label: "Trajectory samples",
      value: sim.trajectory.lambdas.length,
    },
    {
      label: "Tolerances (rtol, atol)",
      value: `${formatScientific(sim.solver_diagnostics.rtol, { sigFigs: 1 })}, ${formatScientific(
        sim.solver_diagnostics.atol,
        { sigFigs: 1 }
      )}`,
    },
    {
      label: "Configuration hash",
      value: `${sim.config_hash.slice(0, 12)}…`,
      copyValue: sim.config_hash,
    },
  ];

  const handleSelectPreset = (id: string) => {
    setSelectedId(id);
    if (typeof window !== "undefined") {
      window.history.replaceState(null, "", `#${id}`);
    }
  };

  return (
    <div className="flex flex-col flex-1 pb-24">
      {/* Header */}
      <header className="border-b border-[var(--border)] bg-[var(--surface)] py-8 px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-7xl flex flex-col lg:flex-row lg:items-end justify-between gap-6">
          <div className="space-y-2 max-w-2xl">
            <h1 className="font-serif text-3xl sm:text-4xl font-normal text-[var(--foreground)] tracking-tight">
              Orbit gallery
            </h1>
            <p className="text-sm sm:text-base text-[var(--foreground-secondary)] font-sans leading-relaxed">
              Seven recorded trajectory snapshots from the{" "}
              <span className="font-mono text-xs text-[var(--foreground)]">v1.0.0</span> Python
              engine (commit{" "}
              <span className="font-mono text-xs text-[var(--foreground)]">062b20c</span>). This
              page shows saved outputs only; open Explorer to run live integrations.
            </p>
          </div>

          {/* Wrapping Filter Controls */}
          <div
            role="group"
            aria-label="Filter recorded presets"
            className="flex flex-wrap items-center gap-1.5"
          >
            {(
              [
                { id: "all", label: "All (7)" },
                { id: "schwarzschild", label: "Schwarzschild (3)" },
                { id: "kerr", label: "Kerr (4)" },
                { id: "timelike", label: "Timelike" },
                { id: "null", label: "Null" },
              ] as { id: FilterType; label: string }[]
            ).map((btn) => {
              const active = filter === btn.id;
              return (
                <button
                  key={btn.id}
                  type="button"
                  onClick={() => setFilter(btn.id)}
                  aria-pressed={active}
                  className={`px-3 py-1.5 text-xs font-sans rounded-[2px] border cursor-pointer ${
                    active
                      ? "border-[var(--foreground)] bg-[var(--foreground)] text-[var(--background)] font-medium"
                      : "border-[var(--border)] bg-[var(--background)] text-[var(--foreground-secondary)] hover:text-[var(--foreground)] hover:bg-[var(--surface-hover)]"
                  }`}
                >
                  {btn.label}
                </button>
              );
            })}
          </div>
        </div>
      </header>

      {/* Main Master-Detail Gallery Layout */}
      <div className="mx-auto max-w-7xl w-full px-4 sm:px-6 lg:px-8 mt-8 grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left: Compact Preset Index */}
        <aside className="lg:col-span-4 space-y-4">
          <div className="text-xs font-sans font-medium uppercase tracking-wider text-[var(--muted)]">
            Recorded presets ({filteredPresets.length})
          </div>

          <ul className="divide-y divide-[var(--border-subtle)] border-y border-[var(--border)]">
            {filteredPresets.map((item) => {
              const itemMeta = item.metadata;
              const itemSim = item.simulation as unknown as SimulationResponse;
              const selected = itemMeta.id === activeItem.metadata.id;
              const itemKerr = itemMeta.spacetime.toLowerCase() === "kerr";
              const itemRetro = itemSim.conserved_quantities.angular_momentum < 0;

              return (
                <li key={itemMeta.id} id={itemMeta.id}>
                  <button
                    type="button"
                    onClick={() => handleSelectPreset(itemMeta.id)}
                    aria-current={selected ? "true" : undefined}
                    className={`w-full text-left py-3 px-3 flex items-start justify-between gap-3 cursor-pointer border-l-2 ${
                      selected
                        ? "border-l-[var(--foreground)] bg-[var(--surface)]"
                        : "border-l-transparent hover:bg-[var(--surface)]/60"
                    }`}
                  >
                    <div className="space-y-0.5 min-w-0">
                      <div className="font-serif text-[15px] text-[var(--foreground)] leading-snug">
                        {itemMeta.name}
                      </div>
                      <div className="text-xs font-sans text-[var(--muted)] flex flex-wrap items-center gap-x-2">
                        <span
                          className={
                            !itemKerr
                              ? ""
                              : itemRetro
                              ? "text-[var(--retrograde)]"
                              : "text-[var(--prograde)]"
                          }
                        >
                          {itemMeta.spacetime}
                          {itemKerr ? (itemRetro ? " retrograde" : " prograde") : ""}
                        </span>
                        <span aria-hidden="true">/</span>
                        <span>{itemMeta.geodesic_type}</span>
                      </div>
                    </div>
                    <span className="text-xs font-mono text-[var(--muted)] tabular-nums shrink-0 pt-0.5">
                      {formatDrift(itemSim.conserved_quantities.hamiltonian_drift_max)}
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>

          <MarginNote label="Reference surfaces">
            Schwarzschild plots show analytical reference circles (horizon, photon sphere, and
            ISCO for timelike orbits). Kerr plots omit these circles because the v1.0.0 API does not
            return Kerr characteristic radii.
          </MarginNote>
        </aside>

        {/* Right: Selected Trajectory & Readouts */}
        <section
          aria-label={meta.name}
          className="lg:col-span-8 space-y-6"
        >
          <div className="space-y-2">
            <div className="flex flex-wrap items-baseline justify-between gap-3">
              <h2 className="font-serif text-2xl font-normal text-[var(--foreground)] tracking-tight">
                {meta.name}
              </h2>
              <Link
                href={`/explorer?preset=${meta.id}`}
                className="inline-flex items-center gap-1.5 text-sm font-sans font-medium text-[var(--accent)] hover:underline underline-offset-4"
              >
                <span>Open in Explorer</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>
            <p className="text-sm font-sans text-[var(--foreground-secondary)] leading-relaxed max-w-2xl">
              {OBSERVATION_NOTES[meta.id] ?? meta.description}
            </p>
          </div>

          <div className="border border-[var(--border)] bg-[var(--background)] rounded-[2px] overflow-hidden">
            <ScientificPlot
              simulationData={sim}
              presetId={meta.id}
              spacetime={meta.spacetime}
              geodesicType={meta.geodesic_type}
              mass={mass}
              spin={spin}
              initialRadius={initR}
              projection="equatorial"
              title={meta.name}
              className="border-0 rounded-none"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 pt-2">
            <div className="space-y-2">
              <h3 className="text-xs font-sans font-medium uppercase tracking-wider text-[var(--muted)]">
                Input configuration
              </h3>
              <ReadoutList items={paramReadouts} />
            </div>

            <div className="space-y-2">
              <h3 className="text-xs font-sans font-medium uppercase tracking-wider text-[var(--muted)]">
                Recorded output (commit 062b20c)
              </h3>
              <ReadoutList items={diagnosticReadouts} />
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
