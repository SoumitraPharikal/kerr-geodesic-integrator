"use client";

import React, { useState } from "react";
import Link from "next/link";
import ScientificPlot from "@/components/ScientificPlot";
import galleryData from "@/data/gallery_trajectories.json";
import { formatFloat, formatDrift, formatScientific } from "@/lib/format";
import { Compass, Filter } from "lucide-react";
import { SimulationResponse } from "@/lib/api";

type FilterType = "all" | "schwarzschild" | "kerr" | "timelike" | "null";

export default function GalleryPage() {
  const [filter, setFilter] = useState<FilterType>("all");

  const presetList = Object.values(galleryData);

  const filteredPresets = presetList.filter((item) => {
    if (filter === "schwarzschild") return item.metadata.spacetime.toLowerCase() === "schwarzschild";
    if (filter === "kerr") return item.metadata.spacetime.toLowerCase() === "kerr";
    if (filter === "timelike") return item.metadata.geodesic_type.toLowerCase() === "timelike";
    if (filter === "null") return item.metadata.geodesic_type.toLowerCase() === "null";
    return true;
  });

  return (
    <div className="flex flex-col flex-1 pb-20">
      {/* Page Header */}
      <div className="border-b border-[var(--border)] py-6 px-4 sm:px-6 lg:px-8 bg-[var(--surface)]">
        <div className="mx-auto max-w-7xl">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <h1 className="font-serif text-2xl sm:text-3xl font-normal text-[var(--foreground)] tracking-tight">
                Orbit Gallery
              </h1>
              <p className="text-xs sm:text-sm text-[var(--muted)] font-sans mt-1">
                Authentic numerical trajectories computed by the validated v1.0.0 Python engine across all 7 registered presets.
              </p>
            </div>

            {/* Filter controls */}
            <div className="flex items-center gap-1.5 p-1 rounded-[3px] border border-[var(--border)] bg-[var(--surface-subtle)] self-start md:self-auto overflow-x-auto max-w-full">
              <Filter className="h-3 w-3 text-[var(--muted)] ml-1 mr-0.5 shrink-0" />
              <button
                type="button"
                onClick={() => setFilter("all")}
                className={`px-2.5 py-1 text-xs font-sans rounded-[2px] transition-colors cursor-pointer shrink-0 ${
                  filter === "all"
                    ? "bg-[var(--surface)] text-[var(--foreground)] font-medium border border-[var(--border)] shadow-xs"
                    : "text-[var(--muted)] hover:text-[var(--foreground)]"
                }`}
              >
                All (7)
              </button>
              <button
                type="button"
                onClick={() => setFilter("schwarzschild")}
                className={`px-2.5 py-1 text-xs font-sans rounded-[2px] transition-colors cursor-pointer shrink-0 ${
                  filter === "schwarzschild"
                    ? "bg-[var(--surface)] text-[var(--foreground)] font-medium border border-[var(--border)] shadow-xs"
                    : "text-[var(--muted)] hover:text-[var(--foreground)]"
                }`}
              >
                Schwarzschild (3)
              </button>
              <button
                type="button"
                onClick={() => setFilter("kerr")}
                className={`px-2.5 py-1 text-xs font-sans rounded-[2px] transition-colors cursor-pointer shrink-0 ${
                  filter === "kerr"
                    ? "bg-[var(--surface)] text-[var(--foreground)] font-medium border border-[var(--border)] shadow-xs"
                    : "text-[var(--muted)] hover:text-[var(--foreground)]"
                }`}
              >
                Kerr (4)
              </button>
              <button
                type="button"
                onClick={() => setFilter("timelike")}
                className={`px-2.5 py-1 text-xs font-sans rounded-[2px] transition-colors cursor-pointer shrink-0 ${
                  filter === "timelike"
                    ? "bg-[var(--surface)] text-[var(--foreground)] font-medium border border-[var(--border)] shadow-xs"
                    : "text-[var(--muted)] hover:text-[var(--foreground)]"
                }`}
              >
                Timelike
              </button>
              <button
                type="button"
                onClick={() => setFilter("null")}
                className={`px-2.5 py-1 text-xs font-sans rounded-[2px] transition-colors cursor-pointer shrink-0 ${
                  filter === "null"
                    ? "bg-[var(--surface)] text-[var(--foreground)] font-medium border border-[var(--border)] shadow-xs"
                    : "text-[var(--muted)] hover:text-[var(--foreground)]"
                }`}
              >
                Null
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Gallery List */}
      <div className="mx-auto max-w-7xl w-full px-4 sm:px-6 lg:px-8 mt-8 space-y-10">
        <div className="space-y-10">
          {filteredPresets.map((item) => {
            const meta = item.metadata;
            const sim = item.simulation as unknown as SimulationResponse;
            const params = meta.default_parameters as Record<string, unknown>;
            const mass = (params.mass as number) ?? 1.0;
            const spin = (params.spin as number) ?? 0.0;
            const initR =
              (params.radius as number) ??
              (params.r0 as number) ??
              (params.impact_parameter as number) ??
              8.0;

            return (
              <div
                key={meta.id}
                id={meta.id}
                className="rounded-[4px] border border-[var(--border)] bg-[var(--surface)] overflow-hidden shadow-xs grid grid-cols-1 lg:grid-cols-12 items-stretch"
              >
                {/* Left Area: Plot (lg:col-span-7) */}
                <div className="lg:col-span-7 border-b lg:border-b-0 lg:border-r border-[var(--border)] flex flex-col justify-between bg-[var(--surface)]">
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
                    className="border-0 rounded-none h-full"
                  />
                </div>

                {/* Right Area: Metadata & Diagnostics (lg:col-span-5) */}
                <div className="lg:col-span-5 p-6 flex flex-col justify-between space-y-5 bg-[var(--surface)]">
                  <div className="space-y-4">
                    {/* Header info */}
                    <div>
                      <div className="flex items-center gap-2 font-mono text-xs text-[var(--foreground-secondary)] mb-1.5">
                        <span className="capitalize">{meta.spacetime}</span>
                        <span>·</span>
                        <span className="capitalize">{meta.geodesic_type}</span>
                        <span>·</span>
                        <span>a = {formatFloat(spin, 2)}</span>
                      </div>
                      <h2 className="font-serif text-xl font-normal text-[var(--foreground)] leading-snug">
                        {meta.name}
                      </h2>
                      <p className="text-xs text-[var(--foreground-secondary)] font-sans mt-2 leading-relaxed">
                        {meta.description}
                      </p>
                    </div>

                    {/* Physical Parameters Table */}
                    <div className="border border-[var(--border)] rounded-[3px] bg-[var(--surface-subtle)] p-3.5 space-y-2 font-mono text-xs">
                      <div className="text-[11px] font-sans font-medium uppercase tracking-wider text-[var(--foreground-secondary)] mb-1">
                        Physical Configuration
                      </div>
                      <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-xs">
                        {Object.entries(meta.default_parameters).map(([key, val]) => (
                          <div key={key} className="flex justify-between">
                            <span className="text-[var(--foreground-secondary)] font-sans">{key}:</span>
                            <span className="text-[var(--foreground)] font-mono tabular-nums">{String(val)}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Conserved Quantities & Diagnostics */}
                    <div className="border border-[var(--border)] rounded-[3px] bg-[var(--surface-subtle)] p-3.5 space-y-2 font-mono text-xs">
                      <div className="text-[11px] font-sans font-medium uppercase tracking-wider text-[var(--foreground-secondary)] mb-1">
                        Conserved Quantities &amp; Solver
                      </div>
                      <div className="space-y-1.5 text-xs">
                        <div className="flex justify-between">
                          <span className="text-[var(--foreground-secondary)] font-sans">Energy (E = −p_t):</span>
                          <span className="text-[var(--foreground)] font-mono tabular-nums">{formatFloat(sim.conserved_quantities.energy, 6)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-[var(--foreground-secondary)] font-sans">Angular Mom (L_z = p_φ):</span>
                          <span className="text-[var(--foreground)] font-mono tabular-nums">{formatFloat(sim.conserved_quantities.angular_momentum, 6)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-[var(--foreground-secondary)] font-sans">Carter Constant (Q):</span>
                          <span className="text-[var(--foreground)] font-mono tabular-nums">
                            {sim.conserved_quantities.carter_constant !== null
                              ? formatFloat(sim.conserved_quantities.carter_constant, 6)
                              : "0.000000"}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-[var(--foreground-secondary)] font-sans">Max Drift (|ΔH|):</span>
                          <span className="text-[var(--accent)] font-medium font-mono tabular-nums">
                            {formatDrift(sim.conserved_quantities.hamiltonian_drift_max)}
                          </span>
                        </div>
                        <div className="flex justify-between pt-1.5 border-t border-[var(--border)]">
                          <span className="text-[var(--foreground-secondary)] font-sans">Solver / Steps:</span>
                          <span className="text-[var(--foreground)] font-mono text-[11px]">
                            {sim.solver_diagnostics.method} ({sim.solver_diagnostics.nfev} evals, {sim.trajectory.lambdas.length} samples)
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-[var(--foreground-secondary)] font-sans">Tolerances:</span>
                          <span className="text-[var(--foreground)] font-mono tabular-nums">
                            rtol = {formatScientific(sim.solver_diagnostics.rtol, { sigFigs: 1 })}, atol = {formatScientific(sim.solver_diagnostics.atol, { sigFigs: 1 })}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-[var(--foreground-secondary)] font-sans">Config Hash:</span>
                          <span className="text-[11px] text-[var(--muted)] truncate max-w-[140px]" title={sim.config_hash}>
                            {sim.config_hash.slice(0, 16)}…
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="pt-3 border-t border-[var(--border)] flex items-center justify-between">
                    <span className="text-xs font-mono text-[var(--muted)]">
                      Provenance: {sim.provenance.engine} v{sim.provenance.version}
                    </span>
                    <Link
                      href={`/explorer?preset=${meta.id}`}
                      className="inline-flex items-center gap-1.5 rounded-[3px] bg-[var(--surface-subtle)] hover:bg-[var(--surface-hover)] border border-[var(--border)] px-3 py-1.5 text-xs font-sans text-[var(--foreground)] transition-colors cursor-pointer"
                    >
                      <Compass className="h-3.5 w-3.5 text-[var(--accent)]" />
                      <span>Open in Explorer</span>
                    </Link>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
