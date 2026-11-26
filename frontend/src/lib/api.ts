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
  | "readiness_timeout"
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
    return (
      this.errorType === "timeout_error" ||
      this.errorType === "readiness_timeout" ||
      this.statusCode === 408
    );
  }

  get isReadinessTimeout(): boolean {
    return this.errorType === "readiness_timeout";
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
  baseUrl?: string;
  fastProbeTimeoutMs?: number;
  pollIntervalMs?: number;
}

export const COLD_START_TIMEOUT_MS = 90000;         // 90s bounded timeout for backend wake-up / cold start
export const DEFAULT_SIMULATION_TIMEOUT_MS = 25000; // 25s bounded timeout for ODE integration on awake backend
export const DEFAULT_METADATA_TIMEOUT_MS = 10000;   // 10s bounded timeout for routine metadata requests on awake backend
export const FAST_PROBE_TIMEOUT_MS = 2500;          // 2.5s bounded lightweight probe timeout
export const IDLE_FRESHNESS_WINDOW_MS = 60000;      // 60s freshness window: active communication within 60s guarantees awake

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/+$/, "") || "http://127.0.0.1:8000";

// Use performance.now() for monotonic freshness elapsed-time (immune to wall-clock adjustments).
// Falls back to Date.now() in environments where performance is unavailable (e.g., older test runners).
function monotonicNow(): number {
  return typeof performance !== "undefined" ? performance.now() : Date.now();
}

// Internal backend awake state, monotonic timestamp of last successful communication,
// and shared in-flight readiness promise.
let backendIsAwake = false;
let lastBackendContactMono = 0; // performance.now() timestamp
let pendingReadinessPromise: Promise<HealthResponse> | null = null;

export function isBackendAwake(): boolean {
  return backendIsAwake && !isBackendStale();
}

export function isBackendStale(): boolean {
  if (!backendIsAwake) return true;
  return monotonicNow() - lastBackendContactMono >= IDLE_FRESHNESS_WINDOW_MS;
}

export function resetBackendReadiness(): void {
  backendIsAwake = false;
  lastBackendContactMono = 0;
  pendingReadinessPromise = null;
}

export function markBackendAwake(): void {
  backendIsAwake = true;
  lastBackendContactMono = monotonicNow();
}

export function markBackendStale(): void {
  // Set to a sufficiently negative value so that monotonicNow() - lastBackendContactMono
  // is always >= IDLE_FRESHNESS_WINDOW_MS regardless of process uptime.
  lastBackendContactMono = -IDLE_FRESHNESS_WINDOW_MS;
}

function sleepWithSignal(ms: number, signal?: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    if (signal?.aborted) {
      return reject(new ApiError("Request was cancelled.", "abort_error", 499));
    }
    let timer: NodeJS.Timeout | null = null;
    const onAbort = () => {
      if (timer) clearTimeout(timer);
      reject(new ApiError("Request was cancelled.", "abort_error", 499));
    };
    if (signal) {
      signal.addEventListener("abort", onAbort, { once: true });
    }
    timer = setTimeout(() => {
      if (signal) {
        signal.removeEventListener("abort", onAbort);
      }
      resolve();
    }, ms);
  });
}

/**
 * Ensures the backend is awake before submitting calculations.
 * If backend is currently awake and fresh (<60s since last contact), returns immediately.
 * When stale or cold, performs a lightweight /health probe with a short timeout (2.5s).
 * If the probe succeeds quickly, returns immediately.
 * If the probe times out or indicates a sleeping container, continues with a bounded
 * readiness wait (up to 90s total), deduplicating concurrent probes.
 */
export async function ensureBackendReady(options?: RequestOptions): Promise<HealthResponse> {
  if (backendIsAwake && !isBackendStale()) {
    return {
      status: "ok",
      engine: "kerr-geodesics",
      version: "1.0.0",
      commit_hash: "062b20c80a689640637a2fcd003bdd921a7d4132",
    };
  }

  if (pendingReadinessPromise) {
    return pendingReadinessPromise;
  }

  const baseUrl = options?.baseUrl ?? API_BASE_URL;
  const totalTimeoutMs = options?.timeoutMs ?? COLD_START_TIMEOUT_MS;
  const fastProbeTimeoutMs = options?.fastProbeTimeoutMs ?? FAST_PROBE_TIMEOUT_MS;
  const pollIntervalMs = options?.pollIntervalMs ?? 2000;

  const promise = (async () => {
    // Single absolute deadline covering fast probe + all polling + all sleep intervals.
    // fastProbeTimeoutMs is capped to remain within the global deadline so the total
    // readiness wait never exceeds totalTimeoutMs (plus unavoidable JS scheduling jitter).
    const deadline = Date.now() + totalTimeoutMs;

    // 1. Lightweight fast probe to /health, capped to remaining time
    const fastProbeMs = Math.min(fastProbeTimeoutMs, Math.max(1, deadline - Date.now()));
    let probeOk = false;
    let probeData: HealthResponse | null = null;
    try {
      const probeRes = await fetchWithTimeout(
        `${baseUrl}/health`,
        {
          method: "GET",
          headers: { Accept: "application/json" },
          cache: "no-store",
        },
        fastProbeMs,
        options?.signal
      );
      if (probeRes.ok) {
        probeData = await probeRes.json();
        probeOk = true;
      }
    } catch (err: unknown) {
      if (err instanceof ApiError && err.isAborted) {
        throw err;
      }
      // Fast probe timed out or failed; container is sleeping / spinning up
    }

    // 2. If fast probe succeeded quickly, backend is warm
    if (probeOk && probeData) {
      markBackendAwake();
      return probeData;
    }

    // 3. Backend may have gone idle or is cold.
    // Invalidate stale awake flag so UI/components know container is waking.
    backendIsAwake = false;

    // Continue with bounded readiness polling; all timeouts are capped to remaining deadline.
    while (Date.now() < deadline) {
      if (options?.signal?.aborted) {
        throw new ApiError("Request was cancelled.", "abort_error", 499);
      }

      const remainingMs = deadline - Date.now();
      if (remainingMs <= 0) break;

      const requestTimeout = Math.max(1, Math.min(pollIntervalMs, remainingMs));
      try {
        const res = await fetchWithTimeout(
          `${baseUrl}/health`,
          {
            method: "GET",
            headers: { Accept: "application/json" },
            cache: "no-store",
          },
          requestTimeout,
          options?.signal
        );
        if (res.ok) {
          const data: HealthResponse = await res.json();
          markBackendAwake();
          return data;
        }
      } catch (err: unknown) {
        if (err instanceof ApiError && err.isAborted) {
          throw err;
        }
        // Container still waking up
      }

      const sleepMs = Math.min(pollIntervalMs, Math.max(0, deadline - Date.now()));
      if (sleepMs > 0) {
        await sleepWithSignal(sleepMs, options?.signal);
      }
    }

    // 4. Exhausted bounded readiness window
    throw new ApiError(
      `Backend wake-up timed out after ${totalTimeoutMs / 1000}s. On Render Free tier, the container did not finish spinning up from idle in time. Please retry.`,
      "readiness_timeout",
      408
    );
  })().finally(() => {
    pendingReadinessPromise = null;
  });

  pendingReadinessPromise = promise;
  return promise;
}

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
      `Failed to communicate with engine at ${url}: ${message}. The backend server may be spinning up from idle or unreachable.`,
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
  const baseUrl = options?.baseUrl ?? API_BASE_URL;
  const timeoutMs =
    options?.timeoutMs ??
    (backendIsAwake && !isBackendStale() ? DEFAULT_METADATA_TIMEOUT_MS : COLD_START_TIMEOUT_MS);
  try {
    const res = await fetchWithTimeout(
      `${baseUrl}/health`,
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
    markBackendAwake();
    return data;
  } catch (err: unknown) {
    if (err instanceof ApiError && (err.isNetworkError || err.isTimeout)) {
      backendIsAwake = false;
      lastBackendContactMono = -IDLE_FRESHNESS_WINDOW_MS;
    }
    throw err;
  }
}

/**
 * Fetch the registered simulation preset catalogue from GET /api/v1/presets.
 */
export async function fetchPresetCatalogue(
  options?: RequestOptions
): Promise<PresetCatalogueResponse> {
  const baseUrl = options?.baseUrl ?? API_BASE_URL;
  if (!backendIsAwake || isBackendStale()) {
    await ensureBackendReady({
      signal: options?.signal,
      baseUrl,
      fastProbeTimeoutMs: options?.fastProbeTimeoutMs,
      pollIntervalMs: options?.pollIntervalMs,
    });
  }

  const timeoutMs = options?.timeoutMs ?? DEFAULT_METADATA_TIMEOUT_MS;
  try {
    const res = await fetchWithTimeout(
      `${baseUrl}/api/v1/presets`,
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
    markBackendAwake();
    return data;
  } catch (err: unknown) {
    if (err instanceof ApiError && (err.isNetworkError || err.isTimeout)) {
      backendIsAwake = false;
      lastBackendContactMono = -IDLE_FRESHNESS_WINDOW_MS;
    }
    throw err;
  }
}

/**
 * Submit a simulation execution request to POST /api/v1/simulations.
 */
export async function postSimulation(
  request: SimulationRequest,
  options?: RequestOptions
): Promise<SimulationResponse> {
  const baseUrl = options?.baseUrl ?? API_BASE_URL;
  // Await backend readiness before submitting calculation if backend is cold or stale (>60s since last contact)
  if (!backendIsAwake || isBackendStale()) {
    await ensureBackendReady({
      signal: options?.signal,
      baseUrl,
      fastProbeTimeoutMs: options?.fastProbeTimeoutMs,
      pollIntervalMs: options?.pollIntervalMs,
    });
  }

  const timeoutMs = options?.timeoutMs ?? DEFAULT_SIMULATION_TIMEOUT_MS;
  try {
    const res = await fetchWithTimeout(
      `${baseUrl}/api/v1/simulations`,
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
    markBackendAwake();
    return data;
  } catch (err: unknown) {
    if (err instanceof ApiError && (err.isNetworkError || err.isTimeout)) {
      backendIsAwake = false;
      lastBackendContactMono = -IDLE_FRESHNESS_WINDOW_MS;
    }
    throw err;
  }
}

/**
 * Submit an analytical shadow boundary request to POST /api/v1/shadows.
 */
export async function postShadow(
  request: ShadowRequest,
  options?: RequestOptions
): Promise<ShadowResponse> {
  const baseUrl = options?.baseUrl ?? API_BASE_URL;
  // Await backend readiness before submitting calculation if backend is cold or stale (>60s since last contact)
  if (!backendIsAwake || isBackendStale()) {
    await ensureBackendReady({
      signal: options?.signal,
      baseUrl,
      fastProbeTimeoutMs: options?.fastProbeTimeoutMs,
      pollIntervalMs: options?.pollIntervalMs,
    });
  }

  const timeoutMs = options?.timeoutMs ?? DEFAULT_METADATA_TIMEOUT_MS;
  try {
    const res = await fetchWithTimeout(
      `${baseUrl}/api/v1/shadows`,
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
    markBackendAwake();
    return data;
  } catch (err: unknown) {
    if (err instanceof ApiError && (err.isNetworkError || err.isTimeout)) {
      backendIsAwake = false;
      lastBackendContactMono = -IDLE_FRESHNESS_WINDOW_MS;
    }
    throw err;
  }
}
