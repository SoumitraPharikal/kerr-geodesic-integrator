/**
 * Frontend API client for Kerr Geodesics Lab.
 *
 * Connects to the FastAPI backend adapter (default: http://127.0.0.1:8000).
 * Implements strictly typed interfaces matching the Pydantic v2 schemas in src/geodesics/api/schemas.py.
 */

export interface HealthResponse {
  status: string;
  engine: string;
  version: string;
  commit_hash: string;
}

export interface PresetMetadata {
  id: string;
  name: string;
  description: string;
  spacetime: "Schwarzschild" | "Kerr" | string;
  geodesic_type: "timelike" | "null" | string;
  default_parameters: Record<string, unknown>;
  parameter_schema: Record<string, unknown>;
}

export interface PresetCatalogueResponse {
  presets: PresetMetadata[];
}

export interface SimulationRequest {
  preset_id: string;
  parameters?: Record<string, unknown>;
}

export interface TrajectoryCoordinates {
  t: number[];
  r: number[];
  theta: number[];
  phi: number[];
}

export interface TrajectoryMomenta {
  p_t: number[];
  p_r: number[];
  p_theta: number[];
  p_phi: number[];
}

export interface TrajectoryData {
  lambdas: number[];
  coordinates: TrajectoryCoordinates;
  momenta: TrajectoryMomenta;
}

export interface SolverDiagnostics {
  method: string;
  nfev: number;
  rtol: number;
  atol: number;
}

export interface ConservedQuantities {
  energy: number;
  angular_momentum: number;
  carter_constant: number | null;
  hamiltonian_drift_max: number;
}

export interface EventTriggerItem {
  name: string;
  lambda: number;
  t: number;
  r: number;
  theta: number;
  phi: number;
  p_t: number;
  p_r: number;
  p_theta: number;
  p_phi: number;
  state: number[]; // 8 components: [t, r, theta, phi, p_t, p_r, p_theta, p_phi]
  terminal: boolean;
}

export interface Provenance {
  engine: string;
  version: string;
  commit_hash: string;
}

export interface SimulationResponse {
  preset_id: string;
  config_hash: string;
  status: string;
  termination_reason: string;
  solver_diagnostics: SolverDiagnostics;
  trajectory: TrajectoryData;
  conserved_quantities: ConservedQuantities;
  triggered_events: EventTriggerItem[];
  provenance: Provenance;
}

export interface ShadowRequest {
  mass: number;
  spin: number;
  observer_inclination: number;
  num_points: number;
}

export interface ShadowObservables {
  area: number;
  centroid: [number, number];
  width: number;
  height: number;
}

export interface ShadowResponse {
  alpha: number[];
  beta: number[];
  observables: ShadowObservables;
  provenance: Provenance;
  config_hash: string;
}

export interface ApiErrorDetail {
  loc: (string | number)[];
  message: string;
  type: string;
}

export interface ApiErrorResponse {
  error_type: string;
  message: string;
  details?: ApiErrorDetail[] | unknown;
}

export type ApiErrorType =
  | "timeout_error"
  | "network_unreachable"
  | "abort_error"
  | "invalid_request_parameters"
  | "unphysical_configuration"
  | "unsupported_preset"
  | "numerical_integration_failure"
  | "internal_error"
  | "http_error"
  | string;

export class ApiError extends Error {
  errorType: ApiErrorType;
  details?: unknown;
  statusCode?: number;

  constructor(
    message: string,
    errorType: ApiErrorType = "network_unreachable",
    statusCode?: number,
    details?: unknown
  ) {
    super(message);
    this.name = "ApiError";
    this.errorType = errorType;
    this.statusCode = statusCode;
    this.details = details;
  }

  get isTimeout(): boolean {
    return this.errorType === "timeout_error" || this.statusCode === 408;
  }

  get isNetworkError(): boolean {
    return this.errorType === "network_unreachable" || this.errorType === "connection_error";
  }

  get isValidationError(): boolean {
    return (
      this.statusCode === 422 ||
      this.errorType === "invalid_request_parameters" ||
      this.errorType === "unphysical_configuration"
    );
  }

  get isServerError(): boolean {
    return (
      (this.statusCode !== undefined && this.statusCode >= 500) ||
      this.errorType === "internal_error" ||
      this.errorType === "numerical_integration_failure"
    );
  }

  get isAborted(): boolean {
    return this.errorType === "abort_error";
  }
}

export interface RequestOptions {
  timeoutMs?: number;
  signal?: AbortSignal;
}

export const DEFAULT_SIMULATION_TIMEOUT_MS = 25000; // 25s for ODE integration
export const DEFAULT_METADATA_TIMEOUT_MS = 10000;   // 10s for health & catalogue checks

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/+$/, "") || "http://127.0.0.1:8000";

/**
 * Execute an HTTP request with explicit timeout bounding and AbortSignal support.
 */
export async function fetchWithTimeout(
  url: string,
  init: RequestInit,
  timeoutMs: number,
  externalSignal?: AbortSignal
): Promise<Response> {
  const controller = new AbortController();
  let timedOut = false;

  const onExternalAbort = () => {
    controller.abort();
  };

  if (externalSignal) {
    if (externalSignal.aborted) {
      throw new ApiError("Request was cancelled.", "abort_error", 499);
    }
    externalSignal.addEventListener("abort", onExternalAbort);
  }

  const timer = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, timeoutMs);

  try {
    const res = await fetch(url, {
      ...init,
      signal: controller.signal,
    });
    return res;
  } catch (err: unknown) {
    if (err instanceof ApiError) throw err;

    if (timedOut) {
      throw new ApiError(
        `Request timed out after ${timeoutMs / 1000}s. The scientific engine took too long to complete the calculation.`,
        "timeout_error",
        408
      );
    }
    if (externalSignal?.aborted) {
      throw new ApiError("Request was cancelled.", "abort_error", 499);
    }
    const message = err instanceof Error ? err.message : String(err);
    throw new ApiError(
      `Failed to communicate with engine at ${url}: ${message}. The backend server may be offline or unreachable.`,
      "network_unreachable"
    );
  } finally {
    clearTimeout(timer);
    if (externalSignal) {
      externalSignal.removeEventListener("abort", onExternalAbort);
    }
  }
}

/**
 * Fetch health status and engine provenance from GET /health.
 */
export async function fetchHealth(options?: RequestOptions): Promise<HealthResponse> {
  const timeoutMs = options?.timeoutMs ?? DEFAULT_METADATA_TIMEOUT_MS;
  const res = await fetchWithTimeout(
    `${API_BASE_URL}/health`,
    {
      method: "GET",
      headers: { Accept: "application/json" },
      cache: "no-store",
    },
    timeoutMs,
    options?.signal
  );

  if (!res.ok) {
    let errData: ApiErrorResponse | null = null;
    try {
      errData = await res.json();
    } catch {
      // Non-JSON response
    }
    throw new ApiError(
      errData?.message || `Backend returned HTTP status ${res.status} (${res.statusText})`,
      errData?.error_type || (res.status >= 500 ? "internal_error" : "http_error"),
      res.status,
      errData?.details
    );
  }

  const data: HealthResponse = await res.json();
  return data;
}

/**
 * Fetch the registered simulation preset catalogue from GET /api/v1/presets.
 */
export async function fetchPresetCatalogue(
  options?: RequestOptions
): Promise<PresetCatalogueResponse> {
  const timeoutMs = options?.timeoutMs ?? DEFAULT_METADATA_TIMEOUT_MS;
  const res = await fetchWithTimeout(
    `${API_BASE_URL}/api/v1/presets`,
    {
      method: "GET",
      headers: { Accept: "application/json" },
      cache: "no-store",
    },
    timeoutMs,
    options?.signal
  );

  if (!res.ok) {
    let errData: ApiErrorResponse | null = null;
    try {
      errData = await res.json();
    } catch {
      // Non-JSON response
    }
    throw new ApiError(
      errData?.message || `Failed to fetch presets: HTTP ${res.status}`,
      errData?.error_type || (res.status >= 500 ? "internal_error" : "http_error"),
      res.status,
      errData?.details
    );
  }

  const data: PresetCatalogueResponse = await res.json();
  return data;
}

/**
 * Submit a simulation execution request to POST /api/v1/simulations.
 */
export async function postSimulation(
  request: SimulationRequest,
  options?: RequestOptions
): Promise<SimulationResponse> {
  const timeoutMs = options?.timeoutMs ?? DEFAULT_SIMULATION_TIMEOUT_MS;
  const res = await fetchWithTimeout(
    `${API_BASE_URL}/api/v1/simulations`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify(request),
    },
    timeoutMs,
    options?.signal
  );

  if (!res.ok) {
    let errData: ApiErrorResponse | null = null;
    try {
      errData = await res.json();
    } catch {
      // Non-JSON response
    }
    const defaultType =
      res.status === 422
        ? "invalid_request_parameters"
        : res.status >= 500
        ? "internal_error"
        : "simulation_error";
    throw new ApiError(
      errData?.message || `Simulation failed: HTTP ${res.status} (${res.statusText})`,
      errData?.error_type || defaultType,
      res.status,
      errData?.details
    );
  }

  const data: SimulationResponse = await res.json();
  return data;
}

/**
 * Submit an analytical shadow boundary request to POST /api/v1/shadows.
 */
export async function postShadow(
  request: ShadowRequest,
  options?: RequestOptions
): Promise<ShadowResponse> {
  const timeoutMs = options?.timeoutMs ?? DEFAULT_METADATA_TIMEOUT_MS;
  const res = await fetchWithTimeout(
    `${API_BASE_URL}/api/v1/shadows`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify(request),
    },
    timeoutMs,
    options?.signal
  );

  if (!res.ok) {
    let errData: ApiErrorResponse | null = null;
    try {
      errData = await res.json();
    } catch {
      // Non-JSON response
    }
    const defaultType =
      res.status === 422
        ? "invalid_request_parameters"
        : res.status >= 500
        ? "internal_error"
        : "shadow_error";
    throw new ApiError(
      errData?.message || `Shadow calculation failed: HTTP ${res.status}`,
      errData?.error_type || defaultType,
      res.status,
      errData?.details
    );
  }

  const data: ShadowResponse = await res.json();
  return data;
}
