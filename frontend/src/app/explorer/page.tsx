"use client";

import React, { useState, useEffect, useCallback, useMemo, useRef, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import ScientificPlot from "@/components/ScientificPlot";
import ReadoutList, { ReadoutItem } from "@/components/ReadoutList";
import MarginNote from "@/components/MarginNote";
import DerivationToggle from "@/components/DerivationToggle";
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
  Link2,
  Check,
} from "lucide-react";

function ExplorerContent() {
  const searchParams = useSearchParams();
  const presetParam = searchParams.get("preset");

  const [presets, setPresets] = useState<PresetMetadata[]>([]);
  const [selectedPresetId, setSelectedPresetId] = useState<string>(
    presetParam || "schwarzschild_precession"
  );
  const [presetLoading, setPresetLoading] = useState<boolean>(true);

  const [simulationData, setSimulationData] = useState<SimulationResponse | null>(null);
  const [isSimulating, setIsSimulating] = useState<boolean>(false);
  const [simError, setSimError] = useState<string | null>(null);

  const [params, setParams] = useState<Record<string, number>>({
    mass: 1.0,
    radius: 8.0,
    delta_pr: 0.001,
    affine_span: 100.0,
  });

  const [projection, setProjection] = useState<"equatorial" | "meridional">("equatorial");
  const [expandedEventIdx, setExpandedEventIdx] = useState<number | null>(null);
  const [copiedLink, setCopiedLink] = useState<boolean>(false);

  const abortControllerRef = useRef<AbortController | null>(null);
  const initialRunStartedRef = useRef<boolean>(false);

  const runSimulation = useCallback(
    async (overrideParams?: Record<string, number>, targetPresetId?: string) => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      const controller = new AbortController();
      abortControllerRef.current = controller;

      setIsSimulating(true);
      setSimError(null);
      setExpandedEventIdx(null);

      const activePresetId = targetPresetId || selectedPresetId;
      const activeParams = overrideParams || params;

      try {
        const res = await postSimulation(
          {
            preset_id: activePresetId,
            parameters: activeParams,
          },
          { signal: controller.signal }
        );
        if (!controller.signal.aborted) {
          setSimulationData(res);
        }
      } catch (err: unknown) {
        if (err instanceof ApiError) {
          if (!err.isAborted) {
            setSimError(err.message);
          }
        } else {
          setSimError("Failed to communicate with the simulation engine.");
        }
      } finally {
        if (abortControllerRef.current === controller) {
          setIsSimulating(false);
          abortControllerRef.current = null;
        }
      }
    },
    [selectedPresetId, params]
  );

  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function loadPresets() {
      try {
        const cat = await fetchPresetCatalogue();
        if (cancelled) return;
        setPresets(cat.presets);
        setPresetLoading(false);

        const targetId =
          presetParam && cat.presets.some((p) => p.id === presetParam)
            ? presetParam
            : "schwarzschild_precession";
        const target = cat.presets.find((p) => p.id === targetId);
        if (target && !initialRunStartedRef.current) {
          initialRunStartedRef.current = true;
          const targetParams = { ...target.default_parameters } as Record<string, number>;
          setSelectedPresetId(targetId);
          setParams(targetParams);
          runSimulation(targetParams, targetId);
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [presetParam]);

  const currentPreset: PresetMetadata = useMemo(() => {
    return (
      presets.find((p) => p.id === selectedPresetId) || {
        id: "schwarzschild_precession",
        name: "Schwarzschild Relativistic Periastron Precession",
        description:
          "Bound eccentric timelike orbit exhibiting relativistic periastron precession outside ISCO (r > 6M, E < 1) in Schwarzschild spacetime.",
        spacetime: "Schwarzschild",
        geodesic_type: "timelike",
        default_parameters: { mass: 1.0, radius: 8.0, delta_pr: 0.001, affine_span: 100.0 },
        parameter_schema: {},
      }
    );
  }, [presets, selectedPresetId]);

  const handlePresetChange = (newPresetId: string) => {
    setSelectedPresetId(newPresetId);
    const target = presets.find((p) => p.id === newPresetId);
    const newDefaults = (target ? { ...target.default_parameters } : {}) as Record<string, number>;
    setParams(newDefaults);
    if (typeof window !== "undefined") {
      window.history.replaceState(null, "", `/explorer?preset=${encodeURIComponent(newPresetId)}`);
    }
    runSimulation(newDefaults, newPresetId);
  };

  const handleResetDefaults = () => {
    const defaultParams = { ...currentPreset.default_parameters } as Record<string, number>;
    setParams(defaultParams);
    runSimulation(defaultParams, selectedPresetId);
  };

  const updateParam = (key: string, value: number) => {
    setParams((prev) => ({
      ...prev,
      [key]: Number.isFinite(value) ? value : 0,
    }));
  };

  const handleCopyShareLink = () => {
    if (typeof window === "undefined") return;
    const url = `${window.location.origin}/explorer?preset=${encodeURIComponent(selectedPresetId)}`;
    navigator.clipboard.writeText(url);
    setCopiedLink(true);
    setTimeout(() => setCopiedLink(false), 1800);
  };

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
      rows.push([lam, t, r, th, ph, pt, pr, pth, pph, x, y].join(","));
    }
    const blob = new Blob([rows.join("\n")], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${selectedPresetId}_trajectory_${simulationData.config_hash.slice(0, 8)}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleExportJSON = () => {
    if (!simulationData) return;
    const blob = new Blob([JSON.stringify(simulationData, null, 2)], {
      type: "application/json;charset=utf-8;",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${selectedPresetId}_simulation_${simulationData.config_hash.slice(0, 8)}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  // Parameter validation checks matching backend schema bounds
  const mVal = params.mass ?? 1.0;
  const isMassInvalid = params.mass !== undefined && params.mass <= 0;
  const iscoRadius = 6.0 * mVal;

  const isRadiusInvalid = useMemo(() => {
    if (selectedPresetId === "schwarzschild_precession" && params.radius !== undefined) {
      return params.radius <= iscoRadius;
    }
    if (selectedPresetId === "kerr_circular_timelike" && params.radius !== undefined) {
      return params.radius <= 0;
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
        return params.spin < 0 || params.spin > mVal;
      }
      if (selectedPresetId === "kerr_equatorial_scattering") {
        return Math.abs(params.spin) >= mVal;
      }
      return params.spin < 0 || params.spin >= mVal;
    }
    return false;
  }, [selectedPresetId, params.spin, mVal]);

  const isR0Invalid = useMemo(() => {
    if (params.r0 !== undefined) {
      return params.r0 < 10.0 * mVal;
    }
    return false;
  }, [params.r0, mVal]);

  const maxAffineSpan =
    selectedPresetId.includes("photon") ? 100.0 : 500.0;
  const isAffineSpanInvalid =
    params.affine_span !== undefined &&
    (params.affine_span <= 0 || params.affine_span > maxAffineSpan);

  const hasValidationError =
    isMassInvalid ||
    isRadiusInvalid ||
    isPerturbationInvalid ||
    isSpinInvalid ||
    isR0Invalid ||
    isAffineSpanInvalid;

  // Derived readout items
  const isKerr = currentPreset.spacetime.toLowerCase() === "kerr";
  const isRetrograde =
    simulationData !== null && simulationData.conserved_quantities.angular_momentum < 0;
  const directionTone: "default" | "prograde" | "retrograde" = !isKerr
    ? "default"
    : isRetrograde
    ? "retrograde"
    : "prograde";

  const conservedReadouts: ReadoutItem[] = [
    {
      label: "Conserved energy (E)",
      value: simulationData ? formatFloat(simulationData.conserved_quantities.energy, 6) : "—",
    },
    {
      label: "Axial angular momentum (L_z)",
      value: simulationData
        ? formatFloat(simulationData.conserved_quantities.angular_momentum, 6)
        : "—",
      unit: simulationData ? "M" : undefined,
      tone: directionTone,
    },
    {
      label: "Carter constant (Q)",
      value:
        simulationData && simulationData.conserved_quantities.carter_constant !== null
          ? formatFloat(simulationData.conserved_quantities.carter_constant, 6)
          : simulationData
          ? "0.000000"
          : "—",
    },
    {
      label: "Run Hamiltonian drift (|ΔH|)",
      value: simulationData
        ? formatDrift(simulationData.conserved_quantities.hamiltonian_drift_max)
        : "—",
    },
  ];

  const provenanceReadouts: ReadoutItem[] = [
    {
      label: "Spacetime",
      value: `${currentPreset.spacetime} (${
        params.spin !== undefined ? `a = ${formatFloat(params.spin, 2)} M` : "a = 0"
      })`,
    },
    {
      label: "Geodesic type",
      value: currentPreset.geodesic_type,
    },
    {
      label: "Outer horizon (analytical ref.)",
      value: !isKerr ? formatWithUnit(2.0 * mVal, "M", 2) : "Not in API schema",
    },
    ...(simulationData
      ? [
          {
            label: "Integrator",
            value: simulationData.solver_diagnostics.method,
          },
          {
            label: "Function evaluations",
            value: simulationData.solver_diagnostics.nfev,
          },
          {
            label: "Trajectory samples",
            value: simulationData.trajectory.lambdas.length,
          },
          {
            label: "Tolerances (rtol, atol)",
            value: `${formatScientific(simulationData.solver_diagnostics.rtol, { sigFigs: 1 })}, ${formatScientific(
              simulationData.solver_diagnostics.atol,
              { sigFigs: 1 }
            )}`,
          },
          {
            label: "Engine",
            value: `${simulationData.provenance.engine} v${simulationData.provenance.version}`,
          },
          {
            label: "Commit",
            value: simulationData.provenance.commit_hash.slice(0, 10),
          },
          {
            label: "Configuration hash",
            value: `${simulationData.config_hash.slice(0, 10)}…`,
            copyValue: simulationData.config_hash,
          },
        ]
      : []),
  ];

  const hasSpacetimeGroup = "mass" in params || "spin" in params;
  const hasInitialStateGroup =
    "radius" in params ||
    "r0" in params ||
    "impact_parameter" in params ||
    "delta_pr" in params ||
    "energy" in params;

  return (
    <div className="flex flex-col flex-1 pb-20">
      {/* Header */}
      <header className="border-b border-[var(--border)] bg-[var(--surface)] py-5 px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-7xl flex flex-col sm:flex-row sm:items-baseline justify-between gap-2">
          <div>
            <h1 className="font-serif text-2xl sm:text-3xl font-normal text-[var(--foreground)] tracking-tight">
              Geodesic Explorer
            </h1>
            <p className="text-xs sm:text-sm text-[var(--muted)] font-sans mt-0.5">
              Live trajectory integration via the Python FastAPI backend (adaptive non-symplectic DOP853).
            </p>
          </div>
          <div className="text-xs font-sans text-[var(--muted)]">
            Source: <span className="font-mono text-[var(--foreground)]">POST /api/v1/simulations</span>
          </div>
        </div>
      </header>

      {/* 3-Column Instrument Workbench */}
      <div className="mx-auto max-w-7xl w-full px-4 sm:px-6 lg:px-8 mt-6 grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* LEFT RAIL (3 cols): Parameters grouped by Spacetime / Initial state / Integration */}
        <aside className="lg:col-span-3 space-y-5">
          <div className="border border-[var(--border)] bg-[var(--surface)] rounded-[2px] p-4 space-y-4">
            <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-2.5">
              <h2 className="font-serif text-base font-normal text-[var(--foreground)]">
                Configuration
              </h2>
              <button
                type="button"
                onClick={handleResetDefaults}
                disabled={isSimulating || presetLoading}
                className="inline-flex items-center gap-1 text-xs font-sans text-[var(--muted)] hover:text-[var(--foreground)] hover:underline cursor-pointer disabled:opacity-40"
              >
                <RotateCcw className="h-3 w-3" />
                <span>Defaults</span>
              </button>
            </div>

            {/* Preset Selector */}
            <div className="space-y-1.5">
              <label
                htmlFor="preset-select"
                className="block text-xs font-sans font-medium text-[var(--foreground)]"
              >
                Preset
              </label>
              <select
                id="preset-select"
                value={selectedPresetId}
                onChange={(e) => handlePresetChange(e.target.value)}
                disabled={presetLoading || isSimulating}
                className="w-full rounded-[2px] border border-[var(--border)] bg-[var(--background)] px-2.5 py-1.5 text-xs font-sans text-[var(--foreground)] focus:border-[var(--accent)] focus:outline-none"
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
              <p className="text-xs text-[var(--muted)] font-sans leading-relaxed">
                {presetLoading
                  ? "Waking the Python backend... On Render Free, initial startup can take 30–60s."
                  : currentPreset.description}
              </p>
            </div>

            {/* Group 1: Spacetime */}
            {hasSpacetimeGroup && (
              <fieldset className="border-t border-[var(--border-subtle)] pt-3.5 space-y-3">
                <legend className="text-[11px] font-sans font-medium uppercase tracking-wider text-[var(--muted)]">
                  Spacetime
                </legend>

                {"mass" in params && (
                  <div className="space-y-1">
                    <div className="flex items-center justify-between">
                      <label htmlFor="param-mass" className="text-xs font-sans text-[var(--foreground)]">
                        Mass (M)
                      </label>
                      <span className="text-[11px] font-sans text-[var(--muted)] tabular-nums">
                        Default {String(currentPreset.default_parameters.mass ?? 1.0)}
                      </span>
                    </div>
                    <div
                      className={`flex items-center rounded-[2px] border bg-[var(--background)] ${
                        isMassInvalid ? "border-[var(--status-error)]" : "border-[var(--border)]"
                      }`}
                    >
                      <input
                        id="param-mass"
                        type="number"
                        step="0.1"
                        min="0.1"
                        max="10.0"
                        value={params.mass ?? 1.0}
                        onChange={(e) => updateParam("mass", parseFloat(e.target.value))}
                        disabled={isSimulating}
                        className="w-full bg-transparent px-2.5 py-1.5 text-xs font-sans text-right text-[var(--foreground)] focus:outline-none tabular-nums"
                      />
                      <span className="px-2 py-1.5 text-xs font-sans text-[var(--muted)] border-l border-[var(--border-subtle)] bg-[var(--surface-subtle)] select-none">
                        M
                      </span>
                    </div>
                    {isMassInvalid && (
                      <p className="text-[11px] font-sans text-[var(--status-error)]">
                        Mass must be strictly positive (M &gt; 0).
                      </p>
                    )}
                  </div>
                )}

                {"spin" in params && (
                  <div className="space-y-1">
                    <div className="flex items-center justify-between">
                      <label htmlFor="param-spin" className="text-xs font-sans text-[var(--foreground)]">
                        Spin (a)
                      </label>
                      <span className="text-[11px] font-sans text-[var(--muted)] tabular-nums">
                        Default {String(currentPreset.default_parameters.spin ?? 0.9)}
                      </span>
                    </div>
                    <div
                      className={`flex items-center rounded-[2px] border bg-[var(--background)] ${
                        isSpinInvalid ? "border-[var(--status-error)]" : "border-[var(--border)]"
                      }`}
                    >
                      <input
                        id="param-spin"
                        type="number"
                        step="0.05"
                        min={selectedPresetId === "kerr_equatorial_scattering" ? -mVal + 0.001 : 0}
                        max={
                          selectedPresetId === "kerr_equatorial_retrograde_photon"
                            ? mVal
                            : mVal - 0.001
                        }
                        value={params.spin ?? 0.9}
                        onChange={(e) => updateParam("spin", parseFloat(e.target.value))}
                        disabled={isSimulating}
                        className="w-full bg-transparent px-2.5 py-1.5 text-xs font-sans text-right text-[var(--foreground)] focus:outline-none tabular-nums"
                      />
                      <span className="px-2 py-1.5 text-xs font-sans text-[var(--muted)] border-l border-[var(--border-subtle)] bg-[var(--surface-subtle)] select-none">
                        M
                      </span>
                    </div>
                    {isSpinInvalid ? (
                      <p className="text-[11px] font-sans text-[var(--status-error)]">
                        {selectedPresetId === "kerr_equatorial_retrograde_photon"
                          ? `Spin must satisfy 0 ≤ a ≤ ${formatWithUnit(mVal, "M", 2)}.`
                          : selectedPresetId === "kerr_equatorial_scattering"
                          ? `Spin must satisfy |a| < ${formatWithUnit(mVal, "M", 2)}.`
                          : `Spin must satisfy 0 ≤ a < ${formatWithUnit(mVal, "M", 2)}.`}
                      </p>
                    ) : (
                      <p className="text-[11px] font-sans text-[var(--muted)]">
                        Specific angular momentum J/M.
                      </p>
                    )}
                  </div>
                )}
              </fieldset>
            )}

            {/* Group 2: Initial State */}
            {hasInitialStateGroup && (
              <fieldset className="border-t border-[var(--border-subtle)] pt-3.5 space-y-3">
                <legend className="text-[11px] font-sans font-medium uppercase tracking-wider text-[var(--muted)]">
                  Initial state
                </legend>

                {"radius" in params && (
                  <div className="space-y-1">
                    <div className="flex items-center justify-between">
                      <label htmlFor="param-radius" className="text-xs font-sans text-[var(--foreground)]">
                        Orbital radius (r)
                      </label>
                      <span className="text-[11px] font-sans text-[var(--muted)] tabular-nums">
                        Default {String(currentPreset.default_parameters.radius ?? 8.0)}
                      </span>
                    </div>
                    <div
                      className={`flex items-center rounded-[2px] border bg-[var(--background)] ${
                        isRadiusInvalid ? "border-[var(--status-error)]" : "border-[var(--border)]"
                      }`}
                    >
                      <input
                        id="param-radius"
                        type="number"
                        step="0.5"
                        min="0.1"
                        max="50.0"
                        value={params.radius ?? 8.0}
                        onChange={(e) => updateParam("radius", parseFloat(e.target.value))}
                        disabled={isSimulating}
                        className="w-full bg-transparent px-2.5 py-1.5 text-xs font-sans text-right text-[var(--foreground)] focus:outline-none tabular-nums"
                      />
                      <span className="px-2 py-1.5 text-xs font-sans text-[var(--muted)] border-l border-[var(--border-subtle)] bg-[var(--surface-subtle)] select-none">
                        M
                      </span>
                    </div>
                    {isRadiusInvalid && (
                      <p className="text-[11px] font-sans text-[var(--status-error)]">
                        Radius must exceed Schwarzschild ISCO ({formatWithUnit(iscoRadius, "M", 1)}).
                      </p>
                    )}
                  </div>
                )}

                {"r0" in params && (
                  <div className="space-y-1">
                    <div className="flex items-center justify-between">
                      <label htmlFor="param-r0" className="text-xs font-sans text-[var(--foreground)]">
                        Initial radius (r₀)
                      </label>
                      <span className="text-[11px] font-sans text-[var(--muted)] tabular-nums">
                        Default {String(currentPreset.default_parameters.r0 ?? 50.0)}
                      </span>
                    </div>
                    <div
                      className={`flex items-center rounded-[2px] border bg-[var(--background)] ${
                        isR0Invalid ? "border-[var(--status-error)]" : "border-[var(--border)]"
                      }`}
                    >
                      <input
                        id="param-r0"
                        type="number"
                        step="5.0"
                        min="10.0"
                        max="200.0"
                        value={params.r0 ?? 50.0}
                        onChange={(e) => updateParam("r0", parseFloat(e.target.value))}
                        disabled={isSimulating}
                        className="w-full bg-transparent px-2.5 py-1.5 text-xs font-sans text-right text-[var(--foreground)] focus:outline-none tabular-nums"
                      />
                      <span className="px-2 py-1.5 text-xs font-sans text-[var(--muted)] border-l border-[var(--border-subtle)] bg-[var(--surface-subtle)] select-none">
                        M
                      </span>
                    </div>
                    {isR0Invalid && (
                      <p className="text-[11px] font-sans text-[var(--status-error)]">
                        Initial radius must satisfy r₀ ≥ {formatWithUnit(10.0 * mVal, "M", 1)}.
                      </p>
                    )}
                  </div>
                )}

                {"impact_parameter" in params && (
                  <div className="space-y-1">
                    <div className="flex items-center justify-between">
                      <label htmlFor="param-b" className="text-xs font-sans text-[var(--foreground)]">
                        Impact parameter (b = L_z / E)
                      </label>
                      <span className="text-[11px] font-sans text-[var(--muted)] tabular-nums">
                        Default {String(currentPreset.default_parameters.impact_parameter ?? 4.5)}
                      </span>
                    </div>
                    <div className="flex items-center rounded-[2px] border border-[var(--border)] bg-[var(--background)]">
                      <input
                        id="param-b"
                        type="number"
                        step="0.1"
                        min="-20.0"
                        max="20.0"
                        value={params.impact_parameter ?? 4.5}
                        onChange={(e) =>
                          updateParam("impact_parameter", parseFloat(e.target.value))
                        }
                        disabled={isSimulating}
                        className="w-full bg-transparent px-2.5 py-1.5 text-xs font-sans text-right text-[var(--foreground)] focus:outline-none tabular-nums"
                      />
                      <span className="px-2 py-1.5 text-xs font-sans text-[var(--muted)] border-l border-[var(--border-subtle)] bg-[var(--surface-subtle)] select-none">
                        M
                      </span>
                    </div>
                  </div>
                )}

                {"delta_pr" in params && (
                  <div className="space-y-1">
                    <div className="flex items-center justify-between">
                      <label htmlFor="param-dpr" className="text-xs font-sans text-[var(--foreground)]">
                        Radial perturbation (δp_r)
                      </label>
                      <span className="text-[11px] font-sans text-[var(--muted)] tabular-nums">
                        Default {String(currentPreset.default_parameters.delta_pr ?? 0.001)}
                      </span>
                    </div>
                    <div
                      className={`flex items-center rounded-[2px] border bg-[var(--background)] ${
                        isPerturbationInvalid
                          ? "border-[var(--status-error)]"
                          : "border-[var(--border)]"
                      }`}
                    >
                      <input
                        id="param-dpr"
                        type="number"
                        step="0.0005"
                        min="0.0001"
                        max="0.02"
                        value={params.delta_pr ?? 0.001}
                        onChange={(e) => updateParam("delta_pr", parseFloat(e.target.value))}
                        disabled={isSimulating}
                        className="w-full bg-transparent px-2.5 py-1.5 text-xs font-sans text-right text-[var(--foreground)] focus:outline-none tabular-nums"
                      />
                    </div>
                    {isPerturbationInvalid && (
                      <p className="text-[11px] font-sans text-[var(--status-error)]">
                        Perturbation must satisfy 0.0001 ≤ δp_r ≤ 0.02.
                      </p>
                    )}
                  </div>
                )}

                {"energy" in params && (
                  <div className="space-y-1">
                    <div className="flex items-center justify-between">
                      <label htmlFor="param-energy" className="text-xs font-sans text-[var(--foreground)]">
                        Photon energy (E)
                      </label>
                      <span className="text-[11px] font-sans text-[var(--muted)] tabular-nums">
                        Default {String(currentPreset.default_parameters.energy ?? 1.0)}
                      </span>
                    </div>
                    <div className="flex items-center rounded-[2px] border border-[var(--border)] bg-[var(--background)]">
                      <input
                        id="param-energy"
                        type="number"
                        step="0.1"
                        min="0.1"
                        max="10.0"
                        value={params.energy ?? 1.0}
                        onChange={(e) => updateParam("energy", parseFloat(e.target.value))}
                        disabled={isSimulating}
                        className="w-full bg-transparent px-2.5 py-1.5 text-xs font-sans text-right text-[var(--foreground)] focus:outline-none tabular-nums"
                      />
                    </div>
                  </div>
                )}
              </fieldset>
            )}

            {/* Group 3: Integration */}
            {"affine_span" in params && (
              <fieldset className="border-t border-[var(--border-subtle)] pt-3.5 space-y-3">
                <legend className="text-[11px] font-sans font-medium uppercase tracking-wider text-[var(--muted)]">
                  Integration
                </legend>
                <div className="space-y-1">
                  <div className="flex items-center justify-between">
                    <label htmlFor="param-span" className="text-xs font-sans text-[var(--foreground)]">
                      Affine span (λ_max)
                    </label>
                    <span className="text-[11px] font-sans text-[var(--muted)] tabular-nums">
                      Max {maxAffineSpan}
                    </span>
                  </div>
                  <div
                    className={`flex items-center rounded-[2px] border bg-[var(--background)] ${
                      isAffineSpanInvalid
                        ? "border-[var(--status-error)]"
                        : "border-[var(--border)]"
                    }`}
                  >
                    <input
                      id="param-span"
                      type="number"
                      step="10"
                      min="1"
                      max={maxAffineSpan}
                      value={params.affine_span ?? 100.0}
                      onChange={(e) => updateParam("affine_span", parseFloat(e.target.value))}
                      disabled={isSimulating}
                      className="w-full bg-transparent px-2.5 py-1.5 text-xs font-sans text-right text-[var(--foreground)] focus:outline-none tabular-nums"
                    />
                  </div>
                  {isAffineSpanInvalid && (
                    <p className="text-[11px] font-sans text-[var(--status-error)]">
                      Affine span must satisfy 0 &lt; λ_max ≤ {maxAffineSpan}.
                    </p>
                  )}
                </div>
              </fieldset>
            )}

            {/* Run Button */}
            <div className="pt-2 space-y-2">
              <button
                type="button"
                onClick={() => runSimulation()}
                disabled={isSimulating || hasValidationError || presetLoading}
                className="w-full flex items-center justify-center gap-2 rounded-[2px] bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white py-2 px-4 text-xs font-sans font-medium disabled:opacity-45 cursor-pointer"
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
              <p className="text-[11px] text-[var(--muted)] font-sans text-center">
                Adaptive non-symplectic DOP853 via Python API.
              </p>
            </div>
          </div>
        </aside>

        {/* CENTER (6 cols): Dominant Trajectory Plot + Run Summary */}
        <section aria-label="Trajectory visualization" className="lg:col-span-6 space-y-3">
          {/* Toolbar */}
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div
              role="group"
              aria-label="Coordinate projection"
              className="inline-flex rounded-[2px] border border-[var(--border)] bg-[var(--surface)] p-0.5"
            >
              <button
                type="button"
                onClick={() => setProjection("equatorial")}
                aria-pressed={projection === "equatorial"}
                className={`px-3 py-1 text-xs font-sans rounded-[2px] cursor-pointer ${
                  projection === "equatorial"
                    ? "bg-[var(--foreground)] text-[var(--background)] font-medium"
                    : "text-[var(--foreground-secondary)] hover:text-[var(--foreground)]"
                }`}
              >
                Equatorial (x–y)
              </button>
              <button
                type="button"
                onClick={() => setProjection("meridional")}
                aria-pressed={projection === "meridional"}
                className={`px-3 py-1 text-xs font-sans rounded-[2px] cursor-pointer ${
                  projection === "meridional"
                    ? "bg-[var(--foreground)] text-[var(--background)] font-medium"
                    : "text-[var(--foreground-secondary)] hover:text-[var(--foreground)]"
                }`}
              >
                Meridional (x–z)
              </button>
            </div>

            <div className="flex flex-wrap items-center gap-1.5">
              <button
                type="button"
                onClick={handleCopyShareLink}
                className="inline-flex items-center gap-1.5 rounded-[2px] border border-[var(--border)] bg-[var(--surface)] px-2.5 py-1 text-xs font-sans text-[var(--foreground)] hover:bg-[var(--surface-hover)] cursor-pointer"
              >
                {copiedLink ? (
                  <Check className="h-3.5 w-3.5 text-[var(--status-ok)]" />
                ) : (
                  <Link2 className="h-3.5 w-3.5 text-[var(--muted)]" />
                )}
                <span>{copiedLink ? "Copied link" : "Share URL"}</span>
              </button>
              <button
                type="button"
                onClick={handleExportCSV}
                disabled={!simulationData}
                className="inline-flex items-center gap-1.5 rounded-[2px] border border-[var(--border)] bg-[var(--surface)] px-2.5 py-1 text-xs font-sans text-[var(--foreground)] hover:bg-[var(--surface-hover)] disabled:opacity-40 cursor-pointer"
              >
                <FileSpreadsheet className="h-3.5 w-3.5 text-[var(--muted)]" />
                <span>CSV</span>
              </button>
              <button
                type="button"
                onClick={handleExportJSON}
                disabled={!simulationData}
                className="inline-flex items-center gap-1.5 rounded-[2px] border border-[var(--border)] bg-[var(--surface)] px-2.5 py-1 text-xs font-sans text-[var(--foreground)] hover:bg-[var(--surface-hover)] disabled:opacity-40 cursor-pointer"
              >
                <FileJson className="h-3.5 w-3.5 text-[var(--muted)]" />
                <span>JSON</span>
              </button>
            </div>
          </div>

          {/* Plot */}
          <div className="border border-[var(--border)] bg-[var(--background)] rounded-[2px] overflow-hidden">
            <ScientificPlot
              simulationData={simulationData}
              presetId={selectedPresetId}
              spacetime={currentPreset.spacetime}
              geodesicType={currentPreset.geodesic_type}
              mass={params.mass ?? 1.0}
              spin={params.spin ?? 0.0}
              initialRadius={params.radius ?? params.r0 ?? 8.0}
              projection={projection}
              title={currentPreset.name}
              isLoading={isSimulating}
              error={simError}
              className="border-0 rounded-none"
            />
          </div>

          {/* Run Summary Footer */}
          <div className="border border-[var(--border)] bg-[var(--surface)] rounded-[2px] px-4 py-2.5 flex flex-wrap items-center justify-between gap-x-4 gap-y-2 text-xs font-sans text-[var(--foreground-secondary)] tabular-nums">
            <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
              <span>
                Samples:{" "}
                <strong className="text-[var(--foreground)] font-medium">
                  {simulationData ? simulationData.trajectory.lambdas.length : "—"}
                </strong>
              </span>
              <span>
                Integrator:{" "}
                <strong className="text-[var(--foreground)] font-medium">
                  {simulationData ? simulationData.solver_diagnostics.method : "DOP853"}
                </strong>
              </span>
              <span>
                Function evals:{" "}
                <strong className="text-[var(--foreground)] font-medium">
                  {simulationData ? simulationData.solver_diagnostics.nfev : "—"}
                </strong>
              </span>
            </div>
            <div className="flex flex-wrap items-center gap-x-2 gap-y-1 min-w-0 max-w-full">
              <span className="whitespace-nowrap">
                Status:{" "}
                <span
                  className={`font-medium ${
                    simError ? "text-[var(--status-error)]" : "text-[var(--status-ok)]"
                  }`}
                >
                  {simError ? "error" : simulationData?.status || "ready"}
                </span>
              </span>
              <span className="text-[var(--border)]" aria-hidden="true">
                |
              </span>
              <span className="text-[var(--muted)] break-words min-w-0">
                {simError
                  ? simError
                  : simulationData?.termination_reason || "Ready for execution"}
              </span>
            </div>
          </div>

          <MarginNote label="Live output vs. analytical reference">
            The trajectory, conserved quantities, and event roots are returned live by the Python
            engine. Schwarzschild reference rings (r+, r_ph, r_ISCO) are analytical overlays; Kerr
            reference rings are omitted because the v1.0.0 API does not return Kerr characteristic
            radii.
          </MarginNote>
        </section>

        {/* RIGHT RAIL (3 cols): Readouts, Triggered Events, Provenance */}
        <aside className="lg:col-span-3 space-y-6">
          {/* Conserved Quantities */}
          <section className="space-y-2">
            <h2 className="text-xs font-sans font-medium uppercase tracking-wider text-[var(--muted)]">
              Conserved quantities &amp; drift
            </h2>
            <ReadoutList items={conservedReadouts} />
            <p className="text-[11px] font-sans text-[var(--muted)] leading-relaxed">
              Measured drift is specific to this run; DOP853 keeps drift small via adaptive error
              control rather than symplectic structure.
            </p>
          </section>

          {/* Triggered Events */}
          <section className="border-t border-[var(--border)] pt-4 space-y-2.5">
            <div className="flex items-baseline justify-between gap-2">
              <h2 className="text-xs font-sans font-medium uppercase tracking-wider text-[var(--muted)]">
                Triggered events ({simulationData?.triggered_events.length ?? 0})
              </h2>
            </div>
            <p className="text-[11px] font-sans text-[var(--muted)] leading-relaxed">
              Refined with <span className="font-mono text-[var(--foreground)]">brentq</span> on
              SciPy&apos;s dense-output interpolant.
            </p>

            {simulationData && simulationData.triggered_events.length > 0 ? (
              <ul className="divide-y divide-[var(--border-subtle)] border-y border-[var(--border)]">
                {simulationData.triggered_events.map((ev, idx) => {
                  const isExpanded = expandedEventIdx === idx;
                  return (
                    <li key={`ev-${idx}`} className="py-2.5 space-y-1.5 text-xs font-sans">
                      <div className="flex items-baseline justify-between gap-2">
                        <span className="font-medium text-[var(--foreground)]">
                          #{idx + 1}{" "}
                          {ev.name === "radial_turning_point" ? "Radial turning point" : ev.name}
                        </span>
                        <span className="text-[11px] font-mono text-[var(--muted)] tabular-nums">
                          λ = {formatFloat(ev.lambda, 4)}
                        </span>
                      </div>
                      <div className="grid grid-cols-2 gap-x-3 gap-y-0.5 text-[11px] tabular-nums text-[var(--foreground-secondary)]">
                        <div>r = {formatWithUnit(ev.r, "M", 4)}</div>
                        <div>φ = {formatFloat(ev.phi, 4)} rad</div>
                        <div>t = {formatFloat(ev.t, 4)}</div>
                        <div>p_r = {formatScientific(ev.p_r, { sigFigs: 2 })}</div>
                      </div>
                      <button
                        type="button"
                        onClick={() => setExpandedEventIdx(isExpanded ? null : idx)}
                        className="text-[11px] text-[var(--accent)] hover:underline cursor-pointer"
                      >
                        {isExpanded ? "Hide 8D state vector" : "Inspect 8D state vector"}
                      </button>
                      {isExpanded && (
                        <pre className="mt-1 p-2 rounded-[2px] border border-[var(--border-subtle)] bg-[var(--surface)] text-[10px] font-mono text-[var(--foreground)] overflow-x-auto tabular-nums">
                          {JSON.stringify(ev.state, null, 2)}
                        </pre>
                      )}
                    </li>
                  );
                })}
              </ul>
            ) : (
              <p className="text-xs font-sans text-[var(--muted)]">
                No discrete events triggered during this integration span.
              </p>
            )}
          </section>

          {/* Provenance */}
          <section className="border-t border-[var(--border)] pt-4">
            <DerivationToggle summary="Solver & API provenance" defaultOpen={false}>
              <ReadoutList items={provenanceReadouts} />
            </DerivationToggle>
          </section>
        </aside>
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
