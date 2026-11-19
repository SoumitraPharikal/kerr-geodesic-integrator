"""Pydantic v2 schemas for Kerr Geodesics Lab Stateless Scientific API.

Strict typed schemas for:
- Health check
- Simulation preset metadata and catalogue
- Seven simulation preset parameter definitions with physical domain validation
- Simulation request and response containers
- Shadow request and response containers
- Structured error representations
"""

import math
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, model_validator

from geodesics.initial_conditions import (
    kerr_isco_radius,
    schwarzschild_circular_timelike_energy,
)
from geodesics.metrics.kerr import KerrMetric


# -----------------------------------------------------------------------------
# Base Presets and Validation Models
# -----------------------------------------------------------------------------

class SchwarzschildIscoParams(BaseModel):
    """Parameters for the Schwarzschild ISCO circular timelike orbit preset."""

    mass: float = Field(default=1.0, gt=0, description="Central black hole mass M > 0")
    affine_span: float = Field(default=50.0, gt=0, description="Integration affine parameter span")

    model_config = ConfigDict(extra="forbid")


class SchwarzschildPrecessionParams(BaseModel):
    """Parameters for the Schwarzschild relativistic precession preset.

    Enforces r > 6M and the physical bound-orbit condition E_pert < 1.0.
    """

    mass: float = Field(default=1.0, gt=0, description="Central black hole mass M > 0")
    radius: float = Field(default=8.0, gt=0, description="Initial orbital coordinate radius r > 6M")
    delta_pr: float = Field(default=0.001, description="Radial momentum perturbation delta_pr")
    affine_span: float = Field(default=100.0, gt=0, description="Integration affine parameter span")

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_orbit_bound(self) -> "SchwarzschildPrecessionParams":
        if self.radius <= 6.0 * self.mass:
            raise ValueError(
                f"Orbital radius r must be strictly greater than ISCO radius 6M ({6.0 * self.mass:.4f}), got r = {self.radius}"
            )

        # Evaluate exact perturbed energy: E_pert = sqrt(E_circ^2 + (f * delta_pr)^2)
        f_r = 1.0 - (2.0 * self.mass / self.radius)
        e_circ = schwarzschild_circular_timelike_energy(self.radius, self.mass)
        e_pert = float(np.sqrt(e_circ**2 + (f_r * self.delta_pr) ** 2))

        if e_pert >= 1.0:
            raise ValueError(
                f"Orbit is unbound with specific energy E_pert = {e_pert:.6f} >= 1.0. "
                "For a bound precessing orbit, parameters must satisfy E_pert < 1.0."
            )
        return self


class SchwarzschildPhotonSphereParams(BaseModel):
    """Parameters for the Schwarzschild circular photon sphere preset (exact null fixed point)."""

    mass: float = Field(default=1.0, gt=0, description="Central black hole mass M > 0")
    energy: float = Field(default=1.0, gt=0, description="Conserved photon energy E > 0")
    affine_span: float = Field(default=12.0, gt=0, description="Integration affine parameter span")

    model_config = ConfigDict(extra="forbid")


class KerrProgradePhotonParams(BaseModel):
    """Parameters for the Kerr equatorial prograde circular photon orbit preset."""

    mass: float = Field(default=1.0, gt=0, description="Central black hole mass M > 0")
    spin: float = Field(default=0.9, ge=0.0, description="Spacetime spin parameter 0 <= a < M")
    energy: float = Field(default=1.0, gt=0, description="Conserved photon energy E > 0")
    affine_span: float = Field(default=20.0, gt=0, description="Integration affine parameter span")

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_subextremal(self) -> "KerrProgradePhotonParams":
        if self.spin >= self.mass:
            raise ValueError(
                f"Prograde circular photon orbit requires sub-extremal spin a < M ({self.mass}), got spin = {self.spin}"
            )
        return self


class KerrRetrogradePhotonParams(BaseModel):
    """Parameters for the Kerr equatorial retrograde circular photon orbit preset."""

    mass: float = Field(default=1.0, gt=0, description="Central black hole mass M > 0")
    spin: float = Field(default=0.9, ge=0.0, description="Spacetime spin parameter 0 <= a <= M")
    energy: float = Field(default=1.0, gt=0, description="Conserved photon energy E > 0")
    affine_span: float = Field(default=30.0, gt=0, description="Integration affine parameter span")

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_spin(self) -> "KerrRetrogradePhotonParams":
        if self.spin > self.mass:
            raise ValueError(
                f"Retrograde circular photon orbit requires spin a <= M ({self.mass}), got spin = {self.spin}"
            )
        return self


class KerrCircularTimelikeParams(BaseModel):
    """Parameters for the Kerr equatorial circular timelike orbit preset."""

    mass: float = Field(default=1.0, gt=0, description="Central black hole mass M > 0")
    spin: float = Field(default=0.9, ge=0.0, description="Spacetime spin parameter 0 <= a < M")
    radius: Optional[float] = Field(default=None, description="Orbital coordinate radius r > r_ISCO. If None, defaults to 6.0*M or r_ISCO + 1.0*M")
    affine_span: float = Field(default=100.0, gt=0, description="Integration affine parameter span")

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_orbit(self) -> "KerrCircularTimelikeParams":
        if self.spin >= self.mass:
            raise ValueError(
                f"Kerr circular timelike orbit requires sub-extremal spin a < M ({self.mass}), got spin = {self.spin}"
            )
        kerr = KerrMetric(mass=self.mass, spin=self.spin)
        r_isco = kerr_isco_radius(kerr, prograde=True)

        if self.radius is None:
            # Default to r_ISCO + 1.0 * M or 6.0 * M (whichever is dynamically stable)
            self.radius = max(float(r_isco + 1.0 * self.mass), 6.0 * self.mass)
        elif self.radius <= r_isco:
            raise ValueError(
                f"Orbital radius r must be strictly greater than ISCO radius r_ISCO = {r_isco:.4f}, got r = {self.radius}"
            )
        return self


class KerrEquatorialScatteringParams(BaseModel):
    """Parameters for the Kerr equatorial photon scattering preset."""

    mass: float = Field(default=1.0, gt=0, description="Central black hole mass M > 0")
    spin: float = Field(default=0.5, description="Signed spin parameter |a| < M")
    impact_parameter: float = Field(default=4.5, description="Signed impact parameter b = L_z / E")
    r0: float = Field(default=50.0, gt=0, description="Initial emission radius r0 >= 10M")
    energy: float = Field(default=1.0, gt=0, description="Conserved photon energy E > 0")
    affine_span: float = Field(default=200.0, gt=0, description="Integration affine parameter span")

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_scattering(self) -> "KerrEquatorialScatteringParams":
        if abs(self.spin) >= self.mass:
            raise ValueError(
                f"Scattering simulation requires sub-extremal spin |a| < M ({self.mass}), got spin = {self.spin}"
            )
        if self.r0 < 10.0 * self.mass:
            raise ValueError(
                f"Emission radius r0 must be in asymptotic domain (r0 >= 10M = {10.0 * self.mass:.4f}), got r0 = {self.r0}"
            )
        return self


# Mapping of preset_id to parameter schema model
PRESET_PARAM_MODELS: Dict[str, Any] = {
    "schwarzschild_isco_circular": SchwarzschildIscoParams,
    "schwarzschild_precession": SchwarzschildPrecessionParams,
    "schwarzschild_photon_sphere": SchwarzschildPhotonSphereParams,
    "kerr_equatorial_prograde_photon": KerrProgradePhotonParams,
    "kerr_equatorial_retrograde_photon": KerrRetrogradePhotonParams,
    "kerr_circular_timelike": KerrCircularTimelikeParams,
    "kerr_equatorial_scattering": KerrEquatorialScatteringParams,
}


# -----------------------------------------------------------------------------
# Request Schemas
# -----------------------------------------------------------------------------

class SimulationRequest(BaseModel):
    """Stateless simulation execution request."""

    preset_id: str = Field(description="Unique identifier of the simulation preset")
    parameters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Preset-specific parameters. If omitted, preset defaults are used.",
    )

    model_config = ConfigDict(extra="forbid")


class ShadowRequest(BaseModel):
    """Analytical Kerr black hole shadow boundary construction request."""

    mass: float = Field(default=1.0, gt=0, description="Central black hole mass M > 0")
    spin: float = Field(default=0.9, description="Signed spin parameter |a| <= M")
    observer_inclination: float = Field(
        default=math.pi / 2.0,
        ge=0.0,
        le=math.pi,
        description="Observer polar inclination theta_o in radians [0, pi]",
    )
    num_points: int = Field(
        default=500,
        ge=3,
        le=2000,
        description="Number of boundary vertices to compute",
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_spin(self) -> "ShadowRequest":
        if abs(self.spin) > self.mass:
            raise ValueError(
                f"Spin magnitude |a| must not exceed mass M ({self.mass}), got spin = {self.spin}"
            )
        return self


# -----------------------------------------------------------------------------
# Response Components
# -----------------------------------------------------------------------------

class TrajectoryCoordinates(BaseModel):
    """Boyer-Lindquist / Schwarzschild trajectory coordinates."""

    t: List[float]
    r: List[float]
    theta: List[float]
    phi: List[float]


class TrajectoryMomenta(BaseModel):
    """Canonical covariant momentum components along the trajectory."""

    p_t: List[float]
    p_r: List[float]
    p_theta: List[float]
    p_phi: List[float]


class TrajectoryData(BaseModel):
    """Decimated trajectory data containing affine parameters, coordinates, and momenta."""

    lambdas: List[float]
    coordinates: TrajectoryCoordinates
    momenta: TrajectoryMomenta


class SolverDiagnostics(BaseModel):
    """Numerical ODE solver diagnostics from the integration engine."""

    method: str
    nfev: int
    rtol: float
    atol: float


class ConservedQuantities(BaseModel):
    """Physical conserved quantities and numerical constraint drift."""

    energy: float
    angular_momentum: float
    carter_constant: Optional[float] = None
    hamiltonian_drift_max: float


class EventTriggerItem(BaseModel):
    """Record of a triggered physical or geometric event.

    Preserves the exact root affine parameter lambda and the complete 8-component
    phase-space state evaluated at the event root: (t, r, theta, phi, p_t, p_r, p_theta, p_phi).
    """

    name: str
    lambda_: float = Field(..., alias="lambda")
    t: float = Field(description="Coordinate time t at event root")
    r: float = Field(description="Radial coordinate r at event root")
    theta: float = Field(description="Polar angle theta at event root")
    phi: float = Field(description="Azimuthal angle phi at event root")
    p_t: float = Field(description="Canonical momentum p_t at event root")
    p_r: float = Field(description="Canonical momentum p_r at event root")
    p_theta: float = Field(description="Canonical momentum p_theta at event root")
    p_phi: float = Field(description="Canonical momentum p_phi at event root")
    state: List[float] = Field(
        description="Complete canonical 8-component state vector: [t, r, theta, phi, p_t, p_r, p_theta, p_phi]"
    )
    terminal: bool

    model_config = ConfigDict(populate_by_name=True)


class Provenance(BaseModel):
    """Scientific software version and origin metadata."""

    engine: str = "kerr-geodesics"
    version: str = "1.0.0"
    commit_hash: str = "062b20c80a689640637a2fcd003bdd921a7d4132"


class SimulationResponse(BaseModel):
    """Complete simulation response container."""

    preset_id: str
    config_hash: str
    status: str
    termination_reason: str
    solver_diagnostics: SolverDiagnostics
    trajectory: TrajectoryData
    conserved_quantities: ConservedQuantities
    triggered_events: List[EventTriggerItem]
    provenance: Provenance


class ShadowObservables(BaseModel):
    """Geometric observables derived from the analytical shadow boundary."""

    area: float
    centroid: Tuple[float, float]
    width: float
    height: float


class ShadowResponse(BaseModel):
    """Complete analytical shadow boundary response container."""

    alpha: List[float]
    beta: List[float]
    observables: ShadowObservables
    provenance: Provenance
    config_hash: str


class HealthResponse(BaseModel):
    """Service health and engine version status."""

    status: str = "ok"
    engine: str = "kerr-geodesics"
    version: str = "1.0.0"
    commit_hash: str = "062b20c80a689640637a2fcd003bdd921a7d4132"


class PresetMetadata(BaseModel):
    """Metadata describing an available simulation preset."""

    id: str
    name: str
    description: str
    spacetime: str
    geodesic_type: str
    default_parameters: Dict[str, Any]
    parameter_schema: Dict[str, Any]


class PresetCatalogueResponse(BaseModel):
    """Catalogue of all registered simulation presets."""

    presets: List[PresetMetadata]


class ErrorResponse(BaseModel):
    """Structured error response."""

    error_type: str
    message: str
    details: Optional[Any] = None
