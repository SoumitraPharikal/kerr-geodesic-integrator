"use client";

import React, { useState, useEffect, useCallback, useMemo, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import ScientificPlot from "@/components/ScientificPlot";
import {
  fetchPresetCatalogue,
  postSimulation,
  PresetMetadata,
  SimulationResponse,
  ApiError,
} from "@/lib/api";
import {
  formatFloat,
  formatWithUnit,
  formatScientific,
  formatDrift,
} from "@/lib/format";
import {
  Play,
  RotateCcw,
  FileJson,
  FileSpreadsheet,
  ChevronDown,
  ChevronUp,
} from "lucide-react";

function ExplorerContent() {
  const searchParams = useSearchParams();
  const presetParam = searchParams.get("preset");

  // Preset catalogue state from GET /api/v1/presets
  const [presets, setPresets] = useState<PresetMetadata[]>([]);
  const [selectedPresetId, setSelectedPresetId] = useState<string>(presetParam || "schwarzschild_precession");
  const [presetLoading, setPresetLoading] = useState<boolean>(true);

  // Simulation execution state
  const [simulationData, setSimulationData] = useState<SimulationResponse | null>(null);
  const [isSimulating, setIsSimulating] = useState<boolean>(false);
  const [simError, setSimError] = useState<string | null>(null);

  // Dynamic parameters dictionary matching current preset default_parameters schema
  const [params, setParams] = useState<Record<string, number>>({
    mass: 1.0,
    radius: 8.0,
    delta_pr: 0.001,
    affine_span: 100.0,
  });

  // View state
  const [projection, setProjection] = useState<"equatorial" | "meridional">("equatorial");
  const [showEventJson, setShowEventJson] = useState<boolean>(false);
  const [showProvenanceDrawer, setShowProvenanceDrawer] = useState<boolean>(false);

  // Execute simulation against POST /api/v1/simulations
  const runSimulation = useCallback(
    async (overrideParams?: Record<string, number>, targetPresetId?: string) => {
      setIsSimulating(true);
      setSimError(null);

      const activePresetId = targetPresetId || selectedPresetId;
      const activeParams = overrideParams || params;

      try {
        const res = await postSimulation({
          preset_id: activePresetId,
          parameters: activeParams,
        });
        setSimulationData(res);
      } catch (err: unknown) {
        if (err instanceof ApiError) {
          setSimError(err.message);
        } else {
          setSimError("Failed to communicate with the simulation engine.");
        }
      } finally {
        setIsSimulating(false);
      }
    },
    [selectedPresetId, params]
  );

  // Load preset catalogue on mount
  useEffect(() => {
    let cancelled = false;
    async function loadPresets() {
      try {
        const cat = await fetchPresetCatalogue();
        if (!cancelled) {
          setPresets(cat.presets);
          setPresetLoading(false);
          if (presetParam && cat.presets.some((p) => p.id === presetParam)) {
            setSelectedPresetId(presetParam);
            const target = cat.presets.find((p) => p.id === presetParam);
            if (target) {
              const targetParams = { ...target.default_parameters } as Record<string, number>;
              setParams(targetParams);
              runSimulation(targetParams, presetParam);
            }
          }
        }
      } catch (err: unknown) {
        if (!cancelled) {
          setPresetLoading(false);
          if (err instanceof ApiError) {
            setSimError(err.message);
          }
        }
      }
    }
    loadPresets();
    return () => {
      cancelled = true;
    };
  }, [presetParam, runSimulation]);

  // Current active preset metadata
  const currentPreset: PresetMetadata = useMemo(() => {
    return (
      presets.find((p) => p.id === selectedPresetId) || {
        id: "schwarzschild_precession",
        name: "Schwarzschild Relativistic Periastron Precession",
        description:
          "Bound eccentric timelike orbit exhibiting relativistic periastron precession outside ISCO.",
        spacetime: "Schwarzschild",
        geodesic_type: "timelike",
        default_parameters: { mass: 1.0, radius: 8.0, delta_pr: 0.001, affine_span: 100.0 },
        parameter_schema: {},
      }
    );
  }, [presets, selectedPresetId]);

  // Auto-run simulation on initial load for default preset
  useEffect(() => {
    let active = true;
    async function autoRunInitial() {
      if (active && !simulationData && !isSimulating) {
        await runSimulation();
      }
    }
    autoRunInitial();
    return () => {
      active = false;
    };
  }, [runSimulation, simulationData, isSimulating]);

  // Handle switching preset from dropdown
  const handlePresetChange = (newPresetId: string) => {
    setSelectedPresetId(newPresetId);
    const target = presets.find((p) => p.id === newPresetId);
    const newDefaults = (target ? { ...target.default_parameters } : {}) as Record<string, number>;
    setParams(newDefaults);
    runSimulation(newDefaults, newPresetId);
  };

  // Reset parameters to active preset defaults
  const handleResetDefaults = () => {
    const defaultParams = { ...currentPreset.default_parameters } as Record<string, number>;
    setParams(defaultParams);
    runSimulation(defaultParams, selectedPresetId);
  };

  // Update a single parameter in the state dictionary
  const updateParam = (key: string, value: number) => {
    setParams((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  // Export trajectory samples as CSV (raw precision)
  const handleExportCSV = () => {
    if (!simulationData?.trajectory) return;
    const traj = simulationData.trajectory;
    const n = traj.lambdas.length;

    const headers = [
      "lambda",
      "t",
      "r",
      "theta",
      "phi",
      "p_t",
      "p_r",
      "p_theta",
      "p_phi",
      "x_equatorial",
      "y_equatorial",
    ];

    const rows = [headers.join(",")];

    for (let i = 0; i < n; i++) {
      const lam = traj.lambdas[i];
      const t = traj.coordinates.t[i];
      const r = traj.coordinates.r[i];
      const th = traj.coordinates.theta[i];
      const ph = traj.coordinates.phi[i];
      const pt = traj.momenta.p_t[i];
      const pr = traj.momenta.p_r[i];
      const pth = traj.momenta.p_theta[i];
      const pph = traj.momenta.p_phi[i];
      const x = r * Math.sin(th) * Math.cos(ph);
      const y = r * Math.sin(th) * Math.sin(ph);

      rows.push(
        [lam, t, r, th, ph, pt, pr, pth, pph, x, y].join(",")
      );
    }

    const csvContent = "data:text/csv;charset=utf-8," + rows.join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute(
      "download",
      `${selectedPresetId}_trajectory_${simulationData.config_hash.slice(0, 8)}.csv`
    );
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Export simulation JSON metadata & full provenance (raw precision)
  const handleExportJSON = () => {
    if (!simulationData) return;
    const jsonStr =
      "data:text/json;charset=utf-8," +
      encodeURIComponent(JSON.stringify(simulationData, null, 2));
    const link = document.createElement("a");
    link.setAttribute("href", jsonStr);
    link.setAttribute(
      "download",
      `${selectedPresetId}_simulation_${simulationData.config_hash.slice(0, 8)}.json`
    );
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Parameter validation checks
  const mVal = params.mass ?? 1.0;
  const iscoRadius = 6.0 * mVal;

  const isRadiusInvalid = useMemo(() => {
    if (selectedPresetId === "schwarzschild_precession" && params.radius !== undefined) {
      return params.radius <= iscoRadius;
    }
    return false;
  }, [selectedPresetId, params.radius, iscoRadius]);

  const isPerturbationInvalid = useMemo(() => {
    if (selectedPresetId === "schwarzschild_precession" && params.delta_pr !== undefined) {
      return params.delta_pr > 0.02 || params.delta_pr < 0.0001;
    }
    return false;
  }, [selectedPresetId, params.delta_pr]);

  const isSpinInvalid = useMemo(() => {
    if (params.spin !== undefined) {
      if (selectedPresetId === "kerr_equatorial_retrograde_photon") {
        return Math.abs(params.spin) > mVal;
      }
      return Math.abs(params.spin) >= mVal;
    }
    return false;
  }, [selectedPresetId, params.spin, mVal]);

  const isR0Invalid = useMemo(() => {
    if (params.r0 !== undefined) {
      return params.r0 < 10.0 * mVal;
    }
    return false;
  }, [params.r0, mVal]);

  const hasValidationError = isRadiusInvalid || isPerturbationInvalid || isSpinInvalid || isR0Invalid;

  return (
    <div className="flex flex-col flex-1 pb-16">
      {/* Compact Page Header: Single Plain Sentence */}
      <div className="border-b border-[var(--border)] py-3 px-4 sm:px-6 lg:px-8 bg-[var(--surface)]">
        <div className="mx-auto max-w-7xl">
          <h1 className="font-serif text-xl sm:text-2xl font-normal text-[var(--foreground)] tracking-tight">
            Geodesic Explorer
          </h1>
          <p className="text-xs sm:text-sm text-[var(--muted)] font-sans mt-0.5">
            Numerical integration of timelike and null geodesics in Kerr and Schwarzschild spacetimes via canonical Hamiltonian equations.
          </p>
        </div>
      </div>

      <div className="mx-auto max-w-7xl w-full px-4 sm:px-6 lg:px-8 mt-5">
        {/* 2-Column Laboratory Workspace Layout: Left Rail 4 cols (33.3%), Right Area 8 cols (66.7%) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">

          {/* Left Control Rail (col-span-4) */}
          <div className="lg:col-span-4 space-y-4">

            {/* Simulation Controls Panel */}
            <div className="rounded-[4px] border border-[var(--border)] bg-[var(--surface)] overflow-hidden">
              <div className="border-b border-[var(--border)] bg-[var(--surface-subtle)] px-4 py-2.5 flex items-center justify-between">
                <h2 className="font-serif text-sm font-normal text-[var(--foreground)]">
                  Orbital Configuration
                </h2>
                <button
                  type="button"
                  onClick={handleResetDefaults}
                  className="inline-flex items-center gap-1 text-xs font-sans text-[var(--muted)] hover:text-[var(--foreground)] hover:underline cursor-pointer"
                  title="Reset all parameters to default"
                >
                  <RotateCcw className="h-3 w-3" />
                  <span>Defaults</span>
                </button>
              </div>

              <div className="p-4 space-y-4">
                {/* Preset Selector */}
                <div>
                  <label className="block text-xs font-sans font-medium text-[var(--foreground)] mb-1">
                    Preset
                  </label>
                  <select
                    value={selectedPresetId}
                    onChange={(e) => handlePresetChange(e.target.value)}
                    disabled={presetLoading || isSimulating}
                    className="w-full rounded-[3px] border border-[var(--border)] bg-[var(--surface-subtle)] px-2.5 py-1.5 text-xs font-sans text-[var(--foreground)] focus:border-[var(--accent)] focus:outline-none transition-colors"
                  >
                    {presets.length > 0 ? (
                      presets.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.name}
                        </option>
                      ))
                    ) : (
                      <option value="schwarzschild_precession">
                        Schwarzschild Relativistic Periastron Precession
                      </option>
                    )}
                  </select>
                  <p className="mt-1 text-xs text-[var(--muted)] font-sans leading-tight">
                    {currentPreset.description}
                  </p>
                </div>

                {/* Dynamic Parameters Section */}
                <div className="border-t border-[var(--border)] pt-3.5 space-y-3.5">
                  <div className="text-xs font-sans font-medium text-[var(--foreground-secondary)]">
                    Parameters
                  </div>

                  {/* Mass M */}
                  {"mass" in params && (
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <label className="text-xs font-sans text-[var(--foreground)]">
                          Mass (<span className="font-serif italic">M</span>)
                        </label>
                        <span className="text-[11px] font-mono text-[var(--foreground-secondary)]">
                          Default: {String(currentPreset.default_parameters.mass ?? 1.0)}
                        </span>
                      </div>
                      <div className="flex items-center rounded-[3px] border border-[var(--border)] bg-[var(--surface-subtle)] focus-within:border-[var(--accent)] overflow-hidden">
                        <input
                          type="number"
                          step="0.1"
                          min="0.1"
                          max="10.0"
                          value={params.mass ?? 1.0}
                          onChange={(e) => updateParam("mass", parseFloat(e.target.value) || 1.0)}
                          disabled={isSimulating}
                          className="w-full bg-transparent px-2.5 py-1.5 text-xs font-mono text-right text-[var(--foreground)] focus:outline-none tabular-nums"
                        />
                        <span className="px-2.5 py-1.5 text-xs font-mono text-[var(--foreground-secondary)] border-l border-[var(--border)] bg-[var(--surface)] select-none">
                          M
                        </span>
                      </div>
                      <p className="mt-1 text-[11px] font-sans text-[var(--foreground-secondary)]">
                        Geometrized black hole mass scale.
                      </p>
                    </div>
                  )}

                  {/* Spin Parameter a */}
                  {"spin" in params && (
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <label className="text-xs font-sans text-[var(--foreground)]">
                          Spin Parameter (<span className="font-serif italic">a</span>)
                        </label>
                        <span className="text-[11px] font-mono text-[var(--foreground-secondary)]">
                          Default: {String(currentPreset.default_parameters.spin ?? 0.9)}
                        </span>
                      </div>
                      <div className={`flex items-center rounded-[3px] border bg-[var(--surface-subtle)] focus-within:border-[var(--accent)] overflow-hidden ${
                        isSpinInvalid ? "border-[var(--status-error)]" : "border-[var(--border)]"
                      }`}>
                        <input
                          type="number"
                          step="0.05"
                          min="0.0"
                          max={mVal ? mVal - 0.001 : 0.999}
                          value={params.spin ?? 0.9}
                          onChange={(e) => updateParam("spin", parseFloat(e.target.value) || 0.0)}
                          disabled={isSimulating}
                          className="w-full bg-transparent px-2.5 py-1.5 text-xs font-mono text-right text-[var(--foreground)] focus:outline-none tabular-nums"
                        />
                        <span className="px-2.5 py-1.5 text-xs font-mono text-[var(--foreground-secondary)] border-l border-[var(--border)] bg-[var(--surface)] select-none">
                          M
                        </span>
                      </div>
                      {isSpinInvalid ? (
                        <p className="mt-1 text-[11px] font-sans text-[var(--status-error)]">
                          Spin must satisfy |a| &lt; M ({formatWithUnit(mVal, "M", 2)}) for regular Kerr spacetime.
                        </p>
                      ) : (
                        <p className="mt-1 text-[11px] font-sans text-[var(--foreground-secondary)]">
                          Kerr angular momentum per unit mass (J/M).
                        </p>
                      )}
                    </div>
                  )}

                  {/* Coordinate Radius r */}
                  {"radius" in params && (
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <label className="text-xs font-sans text-[var(--foreground)]">
                          Orbital Radius (<span className="font-serif italic">r</span>)
                        </label>
                        <span className="text-[11px] font-mono text-[var(--muted)]">
                          Default: {String(currentPreset.default_parameters.radius ?? 8.0)}
                        </span>
                      </div>
                      <div className={`flex items-center rounded-[3px] border bg-[var(--surface-subtle)] focus-within:border-[var(--accent)] overflow-hidden ${
                        isRadiusInvalid ? "border-[var(--status-error)]" : "border-[var(--border)]"
                      }`}>
                        <input
                          type="number"
                          step="0.5"
                          min="0.1"
                          max="50.0"
                          value={params.radius ?? 8.0}
                          onChange={(e) => updateParam("radius", parseFloat(e.target.value) || 8.0)}
                          disabled={isSimulating}
                          className="w-full bg-transparent px-2.5 py-1.5 text-xs font-mono text-right text-[var(--foreground)] focus:outline-none tabular-nums"
                        />
                        <span className="px-2.5 py-1.5 text-xs font-mono text-[var(--muted)] border-l border-[var(--border)] bg-[var(--surface)] select-none">
                          M
                        </span>
                      </div>
                      {isRadiusInvalid ? (
                        <p className="mt-1 text-[11px] font-sans text-[var(--status-error)]">
                          Must exceed Schwarzschild ISCO ({formatWithUnit(iscoRadius, "M", 1)}).
                        </p>
                      ) : (
                        <p className="mt-1 text-[11px] font-sans text-[var(--muted)]">
                          Initial coordinate radius in Boyer-Lindquist / Schwarzschild units.
                        </p>
                      )}
                    </div>
                  )}

                  {/* Emission Radius r0 (Scattering) */}
                  {"r0" in params && (
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <label className="text-xs font-sans text-[var(--foreground)]">
                          Emission Radius (<span className="font-serif italic">r₀</span>)
                        </label>
                        <span className="text-[11px] font-mono text-[var(--muted)]">
                          Default: {String(currentPreset.default_parameters.r0 ?? 50.0)}
                        </span>
                      </div>
                      <div className={`flex items-center rounded-[3px] border bg-[var(--surface-subtle)] focus-within:border-[var(--accent)] overflow-hidden ${
                        isR0Invalid ? "border-[var(--status-error)]" : "border-[var(--border)]"
                      }`}>
                        <input
                          type="number"
                          step="5.0"
                          min="10.0"
                          max="200.0"
                          value={params.r0 ?? 50.0}
                          onChange={(e) => updateParam("r0", parseFloat(e.target.value) || 50.0)}
                          disabled={isSimulating}
                          className="w-full bg-transparent px-2.5 py-1.5 text-xs font-mono text-right text-[var(--foreground)] focus:outline-none tabular-nums"
                        />
                        <span className="px-2.5 py-1.5 text-xs font-mono text-[var(--muted)] border-l border-[var(--border)] bg-[var(--surface)] select-none">
                          M
                        </span>
                      </div>
                      {isR0Invalid ? (
                        <p className="mt-1 text-[11px] font-sans text-[var(--status-error)]">
                          Emission radius must be in the asymptotic domain (r₀ ≥ 10M).
                        </p>
                      ) : (
                        <p className="mt-1 text-[11px] font-sans text-[var(--muted)]">
                          Asymptotic launch radius for photon scattering.
                        </p>
                      )}
                    </div>
                  )}

                  {/* Impact Parameter b (Scattering) */}
                  {"impact_parameter" in params && (
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <label className="text-xs font-sans text-[var(--foreground)]">
                          Impact Parameter (<span className="font-serif italic">b = L_z/E</span>)
                        </label>
                        <span className="text-[11px] font-mono text-[var(--muted)]">
                          Default: {String(currentPreset.default_parameters.impact_parameter ?? 4.5)}
                        </span>
                      </div>
                      <div className="flex items-center rounded-[3px] border border-[var(--border)] bg-[var(--surface-subtle)] focus-within:border-[var(--accent)] overflow-hidden">
                        <input
                          type="number"
                          step="0.1"
                          min="-20.0"
                          max="20.0"
                          value={params.impact_parameter ?? 4.5}
                          onChange={(e) => updateParam("impact_parameter", parseFloat(e.target.value) || 4.5)}
                          disabled={isSimulating}
                          className="w-full bg-transparent px-2.5 py-1.5 text-xs font-mono text-right text-[var(--foreground)] focus:outline-none tabular-nums"
                        />
                        <span className="px-2.5 py-1.5 text-xs font-mono text-[var(--muted)] border-l border-[var(--border)] bg-[var(--surface)] select-none">
                          M
                        </span>
                      </div>
                      <p className="mt-1 text-[11px] font-sans text-[var(--muted)]">
                        Asymptotic photon impact parameter governing capture vs. escape.
                      </p>
                    </div>
                  )}

                  {/* Radial Perturbation delta_pr */}
                  {"delta_pr" in params && (
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <label className="text-xs font-sans text-[var(--foreground)]">
                          Radial Perturbation (<span className="font-serif italic">δp_r</span>)
                        </label>
                        <span className="text-[11px] font-mono text-[var(--muted)]">
                          Default: {String(currentPreset.default_parameters.delta_pr ?? 0.001)}
                        </span>
                      </div>
                      <div className={`flex items-center rounded-[3px] border bg-[var(--surface-subtle)] focus-within:border-[var(--accent)] overflow-hidden ${
                        isPerturbationInvalid ? "border-[var(--status-error)]" : "border-[var(--border)]"
                      }`}>
                        <input
                          type="number"
                          step="0.0005"
                          min="0.0001"
                          max="0.02"
                          value={params.delta_pr ?? 0.001}
                          onChange={(e) => updateParam("delta_pr", parseFloat(e.target.value) || 0.001)}
                          disabled={isSimulating}
                          className="w-full bg-transparent px-2.5 py-1.5 text-xs font-mono text-right text-[var(--foreground)] focus:outline-none tabular-nums"
                        />
                      </div>
                      {isPerturbationInvalid ? (
                        <p className="mt-1 text-[11px] font-sans text-[var(--status-error)]">
                          Perturbation must satisfy 0.0001 ≤ δp_r ≤ 0.02 to ensure E &lt; 1.0.
                        </p>
                      ) : (
                        <p className="mt-1 text-[11px] font-sans text-[var(--muted)]">
                          Bound condition E &lt; 1.0. Induces periastron advance.
                        </p>
                      )}
                    </div>
                  )}

                  {/* Photon Energy E */}
                  {"energy" in params && (
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <label className="text-xs font-sans text-[var(--foreground)]">
                          Photon Energy (<span className="font-serif italic">E</span>)
                        </label>
                        <span className="text-[11px] font-mono text-[var(--muted)]">
                          Default: {String(currentPreset.default_parameters.energy ?? 1.0)}
                        </span>
                      </div>
                      <div className="flex items-center rounded-[3px] border border-[var(--border)] bg-[var(--surface-subtle)] focus-within:border-[var(--accent)] overflow-hidden">
                        <input
                          type="number"
                          step="0.1"
                          min="0.1"
                          max="10.0"
                          value={params.energy ?? 1.0}
                          onChange={(e) => updateParam("energy", parseFloat(e.target.value) || 1.0)}
                          disabled={isSimulating}
                          className="w-full bg-transparent px-2.5 py-1.5 text-xs font-mono text-right text-[var(--foreground)] focus:outline-none tabular-nums"
                        />
                      </div>
                      <p className="mt-1 text-[11px] font-sans text-[var(--muted)]">
                        Conserved null geodesic energy E = −p_t.
                      </p>
                    </div>
                  )}

                  {/* Affine Span */}
                  {"affine_span" in params && (
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <label className="text-xs font-sans text-[var(--foreground)]">
                          Affine Span (<span className="font-serif italic">λ_max</span>)
                        </label>
                        <span className="text-[11px] font-mono text-[var(--muted)]">
                          Default: {String(currentPreset.default_parameters.affine_span ?? 100.0)}
                        </span>
                      </div>
                      <div className="flex items-center rounded-[3px] border border-[var(--border)] bg-[var(--surface-subtle)] focus-within:border-[var(--accent)] overflow-hidden">
                        <input
                          type="number"
                          step="20"
                          min="1"
                          max="1000"
                          value={params.affine_span ?? 100.0}
                          onChange={(e) => updateParam("affine_span", parseFloat(e.target.value) || 100.0)}
                          disabled={isSimulating}
                          className="w-full bg-transparent px-2.5 py-1.5 text-xs font-mono text-right text-[var(--foreground)] focus:outline-none tabular-nums"
                        />
                      </div>
                      <p className="mt-1 text-[11px] font-sans text-[var(--muted)]">
                        Integration span in dimensionless affine parameter units.
                      </p>
                    </div>
                  )}
                </div>

                {/* Primary Action Button */}
                <div className="pt-2">
                  <button
                    type="button"
                    onClick={() => runSimulation()}
                    disabled={isSimulating || hasValidationError}
                    className="w-full flex items-center justify-center gap-2 rounded-[3px] bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white py-2 px-4 text-xs font-sans font-medium transition-colors disabled:opacity-50 cursor-pointer"
                  >
                    {isSimulating ? (
                      <>
                        <span className="inline-block h-3.5 w-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        <span>Integrating equations...</span>
                      </>
                    ) : (
                      <>
                        <Play className="h-3.5 w-3.5 fill-current" />
                        <span>Run integration</span>
                      </>
                    )}
                  </button>
                  <p className="mt-1.5 text-center text-[11px] text-[var(--muted)] font-sans">
                    Stateless execution via Python adaptive DOP853 solver.
                  </p>
                </div>
              </div>
            </div>

            {/* Simulation Provenance Drawer */}
            <div className="rounded-[4px] border border-[var(--border)] bg-[var(--surface)] overflow-hidden">
              <button
                type="button"
                onClick={() => setShowProvenanceDrawer(!showProvenanceDrawer)}
                className="w-full border-b border-[var(--border)] bg-[var(--surface-subtle)] px-4 py-2 flex items-center justify-between text-xs font-sans text-left cursor-pointer hover:bg-[var(--surface-hover)] transition-colors"
              >
                <span className="font-serif text-sm font-normal text-[var(--foreground)]">
                  Simulation Provenance
                </span>
                <span className="flex items-center gap-1 font-mono text-xs text-[var(--muted)]">
                  <span>{showProvenanceDrawer ? "Collapse" : "Expand"}</span>
                  {showProvenanceDrawer ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
                </span>
              </button>

              <div className="p-3 space-y-2 text-xs font-mono">
                <div className="flex justify-between items-center py-0.5 border-b border-[var(--border)]">
                  <span className="text-[var(--muted)] font-sans">Spacetime:</span>
                  <span className="font-medium text-[var(--foreground)]">
                    {currentPreset.spacetime} {params.spin !== undefined ? `(a = ${formatFloat(params.spin, 2)})` : "(a = 0)"}
                  </span>
                </div>
                <div className="flex justify-between items-center py-0.5 border-b border-[var(--border)]">
                  <span className="text-[var(--muted)] font-sans">Geodesic Type:</span>
                  <span className="font-medium text-[var(--foreground)] capitalize">
                    {currentPreset.geodesic_type}
                  </span>
                </div>
                <div className="flex justify-between items-center py-0.5 border-b border-[var(--border)]">
                  <span className="text-[var(--muted)] font-sans">Outer Horizon (r₊):</span>
                  <span className="tabular-nums text-[var(--foreground)]">
                    {currentPreset.spacetime.toLowerCase() === "schwarzschild"
                      ? formatWithUnit(2.0 * mVal, "M", 2)
                      : "Omitted (not in API schema)"}
                  </span>
                </div>
                <div className="flex justify-between items-center py-0.5 border-b border-[var(--border)]">
                  <span className="text-[var(--muted)] font-sans">Config Hash:</span>
                  <span className="text-[10px] text-[var(--muted)] truncate max-w-[140px]">
                    {simulationData ? simulationData.config_hash.slice(0, 16) + "…" : "Pending"}
                  </span>
                </div>

                {showProvenanceDrawer && simulationData && (
                  <div className="pt-2 space-y-1.5 border-t border-[var(--border)] text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-[var(--muted)] font-sans">Engine Package:</span>
                      <span className="text-[var(--foreground)]">{simulationData.provenance.engine}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[var(--muted)] font-sans">Engine Version:</span>
                      <span className="text-[var(--foreground)]">v{simulationData.provenance.version}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[var(--muted)] font-sans">Release Commit:</span>
                      <span className="text-[var(--foreground)]">{simulationData.provenance.commit_hash.slice(0, 10)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[var(--muted)] font-sans">Relative Tol (rtol):</span>
                      <span className="text-[var(--foreground)] tabular-nums">{formatScientific(simulationData.solver_diagnostics.rtol, { sigFigs: 1 })}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[var(--muted)] font-sans">Absolute Tol (atol):</span>
                      <span className="text-[var(--foreground)] tabular-nums">{formatScientific(simulationData.solver_diagnostics.atol, { sigFigs: 1 })}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[var(--muted)] font-sans">Termination:</span>
                      <span className="text-[var(--status-ok)] font-medium">{simulationData.status}</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right Main Column (col-span-8): Plot & Results */}
          <div className="lg:col-span-8 space-y-4">

            {/* Viewport Toolbar: Projection & Export */}
            <div className="flex flex-wrap items-center justify-between gap-2">
              {/* Projection Segmented Control */}
              <div className="inline-flex rounded-[3px] border border-[var(--border)] bg-[var(--surface-subtle)] p-0.5">
                <button
                  type="button"
                  onClick={() => setProjection("equatorial")}
                  className={`px-3 py-1 text-xs font-sans rounded-[2px] transition-colors cursor-pointer ${
                    projection === "equatorial"
                      ? "bg-[var(--surface)] text-[var(--foreground)] font-medium border border-[var(--border)] shadow-xs"
                      : "text-[var(--muted)] hover:text-[var(--foreground)]"
                  }`}
                >
                  Equatorial (x–y)
                </button>
                <button
                  type="button"
                  onClick={() => setProjection("meridional")}
                  className={`px-3 py-1 text-xs font-sans rounded-[2px] transition-colors cursor-pointer ${
                    projection === "meridional"
                      ? "bg-[var(--surface)] text-[var(--foreground)] font-medium border border-[var(--border)] shadow-xs"
                      : "text-[var(--muted)] hover:text-[var(--foreground)]"
                  }`}
                >
                  Meridional (x–z)
                </button>
              </div>

              {/* Data Export Actions */}
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={handleExportCSV}
                  disabled={!simulationData}
                  className="inline-flex items-center gap-1.5 rounded-[3px] border border-[var(--border)] bg-[var(--surface)] px-2.5 py-1 text-xs font-sans text-[var(--foreground)] hover:bg-[var(--surface-hover)] disabled:opacity-40 transition-colors cursor-pointer"
                  title="Export unrounded trajectory CSV"
                >
                  <FileSpreadsheet className="h-3.5 w-3.5 text-[var(--muted)]" />
                  <span>Export CSV</span>
                </button>
                <button
                  type="button"
                  onClick={handleExportJSON}
                  disabled={!simulationData}
                  className="inline-flex items-center gap-1.5 rounded-[3px] border border-[var(--border)] bg-[var(--surface)] px-2.5 py-1 text-xs font-sans text-[var(--foreground)] hover:bg-[var(--surface-hover)] disabled:opacity-40 transition-colors cursor-pointer"
                  title="Export full response JSON"
                >
                  <FileJson className="h-3.5 w-3.5 text-[var(--muted)]" />
                  <span>Export JSON</span>
                </button>
              </div>
            </div>

            {/* Central Plot (occupies 100% of the 8-col width = 66.7% of total layout) */}
            <ScientificPlot
              simulationData={simulationData}
              presetId={selectedPresetId}
              spacetime={currentPreset.spacetime}
              geodesicType={currentPreset.geodesic_type}
              mass={params.mass ?? 1.0}
              spin={params.spin ?? 0.0}
              initialRadius={params.radius ?? params.r0 ?? 8.0}
              projection={projection}
              title={`${currentPreset.name} Trajectory`}
              isLoading={isSimulating}
              error={simError}
            />

            {/* Results & Diagnostics Table: | Quantity | Symbol | Value | Drift | */}
            <div className="rounded-[4px] border border-[var(--border)] bg-[var(--surface)] overflow-hidden">
              <div className="border-b border-[var(--border)] bg-[var(--surface-subtle)] px-4 py-2 flex items-center justify-between">
                <h3 className="font-serif text-sm font-normal text-[var(--foreground)]">
                  Conserved Quantities & Diagnostics
                </h3>
                <span className="font-mono text-xs text-[var(--muted)]">
                  Killing Symmetries & Hamiltonian Constraint
                </span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs font-sans">
                  <thead>
                    <tr className="border-b border-[var(--border)] bg-[var(--surface)] text-[var(--foreground-secondary)] font-mono text-xs">
                      <th className="py-2.5 px-4 font-medium">Quantity</th>
                      <th className="py-2.5 px-4 font-medium">Symbol</th>
                      <th className="py-2.5 px-4 font-medium text-right">Value</th>
                      <th className="py-2.5 px-4 font-medium text-right">Drift</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[var(--border)] font-mono text-xs tabular-nums text-[var(--foreground)]">
                    <tr>
                      <td className="py-2.5 px-4 font-sans font-medium text-[var(--foreground)]">Energy</td>
                      <td className="py-2.5 px-4 text-[var(--foreground-secondary)] font-serif italic">E = −pₜ</td>
                      <td className="py-2.5 px-4 text-right">
                        {simulationData ? formatFloat(simulationData.conserved_quantities.energy, 6) : "—"}
                      </td>
                      <td className="py-2.5 px-4 text-right text-[var(--muted)]">&minus;</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-4 font-sans font-medium text-[var(--foreground)]">Axial Angular Momentum</td>
                      <td className="py-2.5 px-4 text-[var(--foreground-secondary)] font-serif italic">L_z = p_φ</td>
                      <td className="py-2.5 px-4 text-right">
                        {simulationData ? formatFloat(simulationData.conserved_quantities.angular_momentum, 6) : "—"}
                      </td>
                      <td className="py-2.5 px-4 text-right text-[var(--muted)]">&minus;</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-4 font-sans font-medium text-[var(--foreground)]">Carter Constant</td>
                      <td className="py-2.5 px-4 text-[var(--foreground-secondary)] font-serif italic">Q</td>
                      <td className="py-2.5 px-4 text-right">
                        {simulationData && simulationData.conserved_quantities.carter_constant !== null
                          ? formatFloat(simulationData.conserved_quantities.carter_constant, 6)
                          : simulationData ? "0.000000" : "—"}
                      </td>
                      <td className="py-2.5 px-4 text-right text-[var(--muted)]">&minus;</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-4 font-sans font-medium text-[var(--foreground)]">Hamiltonian Constraint</td>
                      <td className="py-2.5 px-4 text-[var(--foreground-secondary)] font-serif italic">|ΔH|</td>
                      <td className="py-2.5 px-4 text-right">0</td>
                      <td className="py-2.5 px-4 text-right text-[var(--accent)] font-medium">
                        {simulationData ? formatDrift(simulationData.conserved_quantities.hamiltonian_drift_max) : "—"}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              {/* Quiet Run Summary */}
              <div className="border-t border-[var(--border)] bg-[var(--surface-subtle)] px-4 py-2.5 flex flex-wrap items-center justify-between gap-3 text-xs font-mono text-[var(--foreground-secondary)]">
                <div className="flex items-center gap-4">
                  <span>Samples:&thinsp;<strong className="text-[var(--foreground)] font-normal tabular-nums">{simulationData ? simulationData.trajectory.lambdas.length : "—"}</strong></span>
                  <span>Integrator:&thinsp;<strong className="text-[var(--foreground)] font-normal">{simulationData ? simulationData.solver_diagnostics.method : "DOP853"}</strong></span>
                  <span>Evals (nfev):&thinsp;<strong className="text-[var(--foreground)] font-normal tabular-nums">{simulationData ? simulationData.solver_diagnostics.nfev : "—"}</strong></span>
                </div>
                <div className="flex items-center gap-2">
                  <span>Status:&thinsp;<span className="text-[var(--status-ok)] font-medium">{simulationData?.status || "Ready"}</span></span>
                  <span className="text-[var(--border)]">|</span>
                  <span className="text-[11px] text-[var(--muted-light)] truncate max-w-xs">{simulationData?.termination_reason || "Ready for execution"}</span>
                </div>
              </div>
            </div>

            {/* Expandable Event Records Inspector */}
            <div className="rounded-[4px] border border-[var(--border)] bg-[var(--surface)] overflow-hidden">
              <div className="border-b border-[var(--border)] bg-[var(--surface-subtle)] px-4 py-2 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <h3 className="font-serif text-sm font-normal text-[var(--foreground)]">
                    Triggered Event Records
                  </h3>
                  <span className="font-mono text-xs text-[var(--muted)]">
                    ({simulationData?.triggered_events.length || 0} events)
                  </span>
                </div>
                <span className="text-[11px] font-sans text-[var(--muted)] hidden sm:inline">
                  Phase-space roots evaluated by SciPy Brentq
                </span>
              </div>

              {simulationData && simulationData.triggered_events.length > 0 ? (
                <div className="p-4 space-y-3">
                  {simulationData.triggered_events.map((ev, idx) => (
                    <div
                      key={`ev-${idx}`}
                      className="rounded-[3px] border border-[var(--border)] bg-[var(--surface-subtle)] p-3 space-y-2 text-xs font-mono"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-sans font-medium text-[var(--foreground)]">
                          #{idx + 1}: {ev.name === "radial_turning_point" ? "Radial Turning Point (dr/dλ = 0)" : ev.name}
                        </span>
                        <span className="text-[var(--muted)] tabular-nums">
                          λ = {formatFloat(ev.lambda, 6)}
                        </span>
                      </div>

                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px] tabular-nums text-[var(--foreground)]">
                        <div><span className="text-[var(--muted)] font-sans">t:</span> {formatFloat(ev.t, 4)}</div>
                        <div><span className="text-[var(--muted)] font-sans">r:</span> {formatWithUnit(ev.r, "M", 4)}</div>
                        <div><span className="text-[var(--muted)] font-sans">θ:</span> {formatFloat(ev.theta, 4)} rad</div>
                        <div><span className="text-[var(--muted)] font-sans">φ:</span> {formatFloat(ev.phi, 4)} rad</div>
                      </div>

                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px] tabular-nums text-[var(--foreground)] border-t border-[var(--border)] pt-1.5">
                        <div><span className="text-[var(--muted)] font-sans">p_t:</span> {formatFloat(ev.p_t, 4)}</div>
                        <div><span className="text-[var(--muted)] font-sans">p_r:</span> {formatScientific(ev.p_r, { sigFigs: 3 })}</div>
                        <div><span className="text-[var(--muted)] font-sans">p_θ:</span> {formatScientific(ev.p_theta, { sigFigs: 3 })}</div>
                        <div><span className="text-[var(--muted)] font-sans">p_φ:</span> {formatFloat(ev.p_phi, 4)}</div>
                      </div>

                      {/* Expandable Complete 8D Phase-Space State Vector */}
                      <div className="pt-1">
                        <button
                          type="button"
                          onClick={() => setShowEventJson(!showEventJson)}
                          className="text-[11px] text-[var(--accent)] hover:underline flex items-center gap-1 font-sans cursor-pointer"
                        >
                          <span>{showEventJson ? "Hide 8D state vector" : "Inspect complete 8D phase-space state vector"}</span>
                        </button>

                        {showEventJson && (
                          <div className="mt-2 rounded-[3px] bg-[var(--surface)] p-2.5 border border-[var(--border)] overflow-x-auto">
                            <div className="text-[10px] text-[var(--muted)] mb-1 font-sans">
                              Canonical ordering: [t, r, θ, φ, p_t, p_r, p_θ, p_φ]
                            </div>
                            <pre className="text-[11px] text-[var(--foreground)] font-mono tabular-nums">
                              {JSON.stringify(ev.state, null, 2)}
                            </pre>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-4 text-xs font-sans text-[var(--muted)]">
                  No discrete events triggered during integration span.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ExplorerPage() {
  return (
    <Suspense
      fallback={
        <div className="flex-1 p-8 text-xs font-sans text-[var(--muted)] flex items-center justify-center min-h-[400px]">
          <span>Loading Geodesic Explorer...</span>
        </div>
      }
    >
      <ExplorerContent />
    </Suspense>
  );
}
