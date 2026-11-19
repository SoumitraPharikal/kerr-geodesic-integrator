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

export class ApiError extends Error {
  errorType: string;
  details?: unknown;
  statusCode?: number;

  constructor(
    message: string,
    errorType: string = "connection_error",
    statusCode?: number,
    details?: unknown
  ) {
    super(message);
    this.name = "ApiError";
    this.errorType = errorType;
    this.statusCode = statusCode;
    this.details = details;
  }
}

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/+$/, "") || "http://127.0.0.1:8000";

/**
 * Fetch health status and engine provenance from GET /health.
 */
export async function fetchHealth(): Promise<HealthResponse> {
  try {
    const res = await fetch(`${API_BASE_URL}/health`, {
      method: "GET",
      headers: { Accept: "application/json" },
      cache: "no-store",
    });

    if (!res.ok) {
      let errData: ApiErrorResponse | null = null;
      try {
        errData = await res.json();
      } catch {
        // Non-JSON response
      }
      throw new ApiError(
        errData?.message || `Backend returned HTTP status ${res.status} (${res.statusText})`,
        errData?.error_type || "http_error",
        res.status,
        errData?.details
      );
    }

    const data: HealthResponse = await res.json();
    return data;
  } catch (err: unknown) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(
      `The scientific computation engine is currently offline or unreachable at ${API_BASE_URL}. Please ensure the FastAPI backend is running (uvicorn geodesics.api.app:app --port 8000).`,
      "network_unreachable"
    );
  }
}

/**
 * Fetch the registered simulation preset catalogue from GET /api/v1/presets.
 */
export async function fetchPresetCatalogue(): Promise<PresetCatalogueResponse> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/presets`, {
      method: "GET",
      headers: { Accept: "application/json" },
      cache: "no-store",
    });

    if (!res.ok) {
      let errData: ApiErrorResponse | null = null;
      try {
        errData = await res.json();
      } catch {
        // Non-JSON response
      }
      throw new ApiError(
        errData?.message || `Failed to fetch presets: HTTP ${res.status}`,
        errData?.error_type || "http_error",
        res.status,
        errData?.details
      );
    }

    const data: PresetCatalogueResponse = await res.json();
    return data;
  } catch (err: unknown) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(
      `Could not retrieve simulation presets from ${API_BASE_URL}/api/v1/presets. The backend server appears offline.`,
      "network_unreachable"
    );
  }
}

/**
 * Submit a simulation execution request to POST /api/v1/simulations.
 */
export async function postSimulation(
  request: SimulationRequest
): Promise<SimulationResponse> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/simulations`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!res.ok) {
      let errData: ApiErrorResponse | null = null;
      try {
        errData = await res.json();
      } catch {
        // Non-JSON response
      }
      throw new ApiError(
        errData?.message || `Simulation failed: HTTP ${res.status} (${res.statusText})`,
        errData?.error_type || "simulation_error",
        res.status,
        errData?.details
      );
    }

    const data: SimulationResponse = await res.json();
    return data;
  } catch (err: unknown) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(
      `Failed to communicate with simulation engine at ${API_BASE_URL}/api/v1/simulations: ${
        err instanceof Error ? err.message : String(err)
      }`,
      "simulation_network_error"
    );
  }
}

/**
 * Submit an analytical shadow boundary request to POST /api/v1/shadows.
 */
export async function postShadow(request: ShadowRequest): Promise<ShadowResponse> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/shadows`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!res.ok) {
      let errData: ApiErrorResponse | null = null;
      try {
        errData = await res.json();
      } catch {
        // Non-JSON response
      }
      throw new ApiError(
        errData?.message || `Shadow calculation failed: HTTP ${res.status}`,
        errData?.error_type || "shadow_error",
        res.status,
        errData?.details
      );
    }

    const data: ShadowResponse = await res.json();
    return data;
  } catch (err: unknown) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(
      `Failed to communicate with shadow engine at ${API_BASE_URL}/api/v1/shadows: ${
        err instanceof Error ? err.message : String(err)
      }`,
      "shadow_network_error"
    );
  }
}
