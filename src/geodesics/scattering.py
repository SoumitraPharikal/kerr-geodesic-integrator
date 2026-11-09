"""Equatorial Kerr photon capture, scattering, and critical-boundary analysis.

This module provides analytical and numerical tools for non-circular equatorial null
geodesics in Kerr and Schwarzschild spacetimes, including:
- Equatorial null radial potential R(r) and depressed cubic C(r).
- High-precision analytical radial turning-point (periapsis) solver using Brent's method.
- Analytical classification of incoming photons (SCATTERED, CAPTURED, CRITICAL).
- Dedicated geodesic trajectory integration and event monitoring.
- Trajectory classification state machine (SCATTERED, CAPTURED, CRITICAL, UNRESOLVED).

Mathematical Conventions:
-------------------------
Units: Geometrized units G = c = 1, black hole mass M > 0.
Metric signature: (-, +, +, +) with coordinates x^mu = (x0, r, theta, phi), x0 = ct.
Equatorial plane: theta = pi / 2, p_theta = 0, Carter constant Q = 0.
Null geodesic: mu = 0, canonical Hamiltonian H = (1/2) g^{mu nu} p_mu p_nu = 0.
Conserved quantities: Energy E = -p_0 > 0, axial angular momentum L_z = p_phi.
Signed impact parameter: b = L_z / E.

Radial Separation Equation:
---------------------------
In Boyer-Lindquist coordinates, the radial equation for equatorial null geodesics reduces to:
    r^4 (dr/dlambda)^2 = R(r)
where the radial potential R(r) is:
    R(r) = [E(r^2 + a^2) - a L_z]^2 - Delta (L_z - a E)^2
with Delta(r) = r^2 - 2Mr + a^2.
Factoring out E^2 and r > 0:
    R(r) / E^2 = r * C(r)
where C(r) is the depressed cubic polynomial:
    C(r) = r^3 - (b^2 - a^2) r + 2M (b - a)^2.

Roots and Turning Points:
-------------------------
The local minimum of C(r) for r > 0 occurs at:
    r_min = sqrt((b^2 - a^2) / 3)   (for b^2 > a^2).
At this minimum:
    C(r_min) = 2 * [ M(b - a)^2 - ((b^2 - a^2) / 3)^(3/2) ].
- C(r_min) < 0: Supercritical (|b| > |b_ph|). Unique turning point r_turn > r_min >= r_ph
  bracketed in [r_min, r_max], solvable to machine precision via Brent's method. (SCATTERING)
- C(r_min) = 0: Critical separatrix (|b| = |b_ph|). Double root at r_turn = r_ph = r_min. (CRITICAL)
- C(r_min) > 0 or b^2 <= a^2: Subcritical (|b| < |b_ph|). No turning point outside horizon;
  photon plunges across r_+. (CAPTURE)
"""

import math
from dataclasses import dataclass
from typing import Final, Literal, Optional, Tuple, Union
import numpy as np
from scipy.optimize import brentq

from geodesics.constants import (
    DEFAULT_ATOL,
    DEFAULT_HORIZON_BUFFER,
    DEFAULT_MASS,
    DEFAULT_RTOL,
    IDX_PHI,
    IDX_R,
    IDX_THETA,
    IDX_X0,
)
from geodesics.events import (
    EscapeRadiusEvent,
    GeodesicEvent,
    HorizonCutoffEvent,
    RadialTurningPointEvent,
)
from geodesics.hamiltonian import (
    carter_constant,
    conserved_angular_momentum,
    conserved_energy,
    hamiltonian_rhs,
    hamiltonian_value,
)
from geodesics.initial_conditions import (
    kerr_equatorial_photon_impact_parameter,
    kerr_equatorial_photon_orbit_radius,
    kerr_geodesic_initial_state,
)
from geodesics.integrator import GeodesicIntegrationResult, integrate_geodesic
from geodesics.metrics.base import SpacetimeMetric
from geodesics.metrics.kerr import KerrMetric
from geodesics.metrics.schwarzschild import SchwarzschildMetric

ClassificationOutcome = Literal[
    "SCATTERED",
    "CAPTURED",
    "CRITICAL",
    "NEAR_CRITICAL",
    "HORIZON_CUTOFF",
    "DWELLING",
    "UNRESOLVED",
]


def _field_exact_equal(a: object, b: object) -> bool:
    """Exact equality comparison for result fields preserving reflexivity for NaNs.

    Semantics:
    - If both are None: returns True.
    - If one is None and the other not None: returns False.
    - If both are float or np.floating and both are NaN: returns True (ensures reflexivity A == A).
    - If one is NaN and the other not: returns False.
    - Otherwise: returns standard Python exact equality (a == b).
      Note that in Python:
      - +0.0 == -0.0 is True.
      - float('inf') == float('inf') is True.
      - float('-inf') == float('-inf') is True.
      - float('inf') == float('-inf') is False.
    """
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    if isinstance(a, (float, np.floating)) and isinstance(b, (float, np.floating)):
        if np.isnan(a) and np.isnan(b):
            return True
        if np.isnan(a) or np.isnan(b):
            return False
    return a == b


@dataclass(frozen=True, eq=False)
class EquatorialPhotonClassificationResult:
    """Structured result decoupling analytical separatrix classification from numerical trajectory fate.

    This container resolves the conflation between analytical classification of initial conditions
    (|b| == |b_ph|) and the empirical dynamical fate of a numerical integration over a finite affine
    parameter span in double-precision floating-point arithmetic.

    Attributes
    ----------
    analytical_classification : str
        Analytical potential-based classification: 'CRITICAL', 'NEAR_CRITICAL', 'SCATTERED', or 'CAPTURED'.
    numerical_outcome : str
        Empirical dynamical trajectory fate over the integrated affine span:
        'HORIZON_CUTOFF' (terminated at artificial cutoff surface r_cut = r_+(1 + epsilon)),
        'SCATTERED' (radial turning point outside horizon followed by outward motion/escape),
        'DWELLING' (sustained orbit near r_ph without resolving within affine span),
        or 'UNRESOLVED'.
    impact_parameter : float
        Signed impact parameter b = L_z / E.
    critical_impact_parameter : float
        Signed critical impact parameter b_ph matching ray orientation.
    criticality_measure : float
        Relative difference (|b| - |b_ph|) / |b_ph|.
    criticality_tolerance : float
        Numerical tolerance used to identify the analytical separatrix.
    event_history : Tuple[str, ...]
        Chronological sequence of all triggered event names during numerical integration.
    r_turn_analytical : Optional[float]
        Analytical periapsis root of C(r) = 0 outside horizon (or None if subcritical).
    r_turn_numerical : Optional[float]
        Numerical periapsis radius from RadialTurningPointEvent (or None if not triggered).
    dwell_fraction : float
        Fraction of trajectory sample points located within [r_ph - 0.5M, r_ph + 0.5M].
    final_affine_parameter : float
        Final affine parameter lambda reached by the numerical integrator.
    final_radius : float
        Final radial coordinate r at termination.
    """

    analytical_classification: str
    numerical_outcome: str
    impact_parameter: float
    critical_impact_parameter: float
    criticality_measure: float
    criticality_tolerance: float
    event_history: Tuple[str, ...]
    r_turn_analytical: Optional[float]
    r_turn_numerical: Optional[float]
    dwell_fraction: float
    final_affine_parameter: float
    final_radius: float

    __hash__ = None  # Explicitly unhashable due to custom polymorphic string comparison

    @property
    def is_critical(self) -> bool:
        """Whether the initial impact parameter is analytically on the critical separatrix."""
        return self.analytical_classification == "CRITICAL"

    @property
    def is_scattered(self) -> bool:
        """Whether the numerical trajectory exhibited an outer turning point and scattered."""
        return self.numerical_outcome == "SCATTERED"

    @property
    def is_captured(self) -> bool:
        """Whether the trajectory belongs analytically to the subcritical capture basin."""
        return self.analytical_classification == "CAPTURED"

    @property
    def is_horizon_cutoff(self) -> bool:
        """Whether the numerical trajectory terminated at the exterior horizon cutoff surface."""
        return self.numerical_outcome == "HORIZON_CUTOFF"

    @property
    def is_dwelling(self) -> bool:
        """Whether the trajectory hovered near the photon sphere throughout the integration."""
        return self.numerical_outcome == "DWELLING"

    @property
    def primary_classification(self) -> str:
        """Primary summary classification for backward compatibility.

        Semantics:
        - If analytical_classification is 'CRITICAL' or 'NEAR_CRITICAL', returns that analytical status.
        - Otherwise, if numerical_outcome is 'SCATTERED', returns 'SCATTERED'.
        - Otherwise, if numerical_outcome is 'HORIZON_CUTOFF' and analytical_classification is 'CAPTURED',
          returns 'CAPTURED'.
        - Otherwise, returns the numerical_outcome ('HORIZON_CUTOFF', 'DWELLING', or 'UNRESOLVED').
        """
        if self.analytical_classification in ("CRITICAL", "NEAR_CRITICAL"):
            return self.analytical_classification
        if self.numerical_outcome == "SCATTERED":
            return "SCATTERED"
        if self.numerical_outcome == "HORIZON_CUTOFF" and self.analytical_classification == "CAPTURED":
            return "CAPTURED"
        return self.numerical_outcome

    def __str__(self) -> str:
        if self.primary_classification == self.numerical_outcome:
            return self.numerical_outcome
        return f"{self.analytical_classification} (numerical: {self.numerical_outcome})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, str):
            if other == "CRITICAL":
                return self.analytical_classification == "CRITICAL"
            if other == "CAPTURED":
                return self.analytical_classification == "CAPTURED"
            if other == "HORIZON_CUTOFF":
                return self.numerical_outcome == "HORIZON_CUTOFF"
            if other == "SCATTERED":
                return (
                    self.numerical_outcome == "SCATTERED"
                    or self.analytical_classification == "SCATTERED"
                )
            if other == "DWELLING":
                return self.numerical_outcome == "DWELLING"
            if other == "NEAR_CRITICAL":
                return self.analytical_classification == "NEAR_CRITICAL"
            if other == "UNRESOLVED":
                return self.numerical_outcome == "UNRESOLVED"
            return False
        if isinstance(other, EquatorialPhotonClassificationResult):
            # Exact field-by-field equality across all 12 fields (preserves reflexivity, symmetry, transitivity)
            return (
                self.analytical_classification == other.analytical_classification
                and self.numerical_outcome == other.numerical_outcome
                and _field_exact_equal(self.impact_parameter, other.impact_parameter)
                and _field_exact_equal(self.critical_impact_parameter, other.critical_impact_parameter)
                and _field_exact_equal(self.criticality_measure, other.criticality_measure)
                and _field_exact_equal(self.criticality_tolerance, other.criticality_tolerance)
                and self.event_history == other.event_history
                and _field_exact_equal(self.r_turn_analytical, other.r_turn_analytical)
                and _field_exact_equal(self.r_turn_numerical, other.r_turn_numerical)
                and _field_exact_equal(self.dwell_fraction, other.dwell_fraction)
                and _field_exact_equal(self.final_affine_parameter, other.final_affine_parameter)
                and _field_exact_equal(self.final_radius, other.final_radius)
            )
        return NotImplemented

    def is_close(
        self,
        other: object,
        rtol: float = 1e-14,
        atol: float = 1e-15,
        equal_nan: bool = True,
    ) -> bool:
        """Tolerance-based approximate comparison of two result instances.

        Parameters
        ----------
        other : object
            Another EquatorialPhotonClassificationResult instance to compare.
        rtol : float, optional
            Relative tolerance for continuous float fields, by default 1e-14.
        atol : float, optional
            Absolute tolerance for continuous float fields, by default 1e-15.
        equal_nan : bool, optional
            Whether to consider corresponding NaN values as equal, by default True.

        Returns
        -------
        bool
            True if all discrete fields match exactly and continuous fields agree within tolerances.

        Notes
        -----
        Unlike __eq__, approximate comparison via is_close is explicitly non-transitive:
        A.is_close(B) and B.is_close(C) does not necessarily imply A.is_close(C).
        """
        if not isinstance(other, EquatorialPhotonClassificationResult):
            return False
        if (
            self.analytical_classification != other.analytical_classification
            or self.numerical_outcome != other.numerical_outcome
            or self.event_history != other.event_history
        ):
            return False

        float_pairs = [
            (self.impact_parameter, other.impact_parameter),
            (self.critical_impact_parameter, other.critical_impact_parameter),
            (self.criticality_measure, other.criticality_measure),
            (self.criticality_tolerance, other.criticality_tolerance),
            (self.dwell_fraction, other.dwell_fraction),
            (self.final_affine_parameter, other.final_affine_parameter),
            (self.final_radius, other.final_radius),
        ]
        for val_a, val_b in float_pairs:
            if not np.isclose(val_a, val_b, atol=atol, rtol=rtol, equal_nan=equal_nan):
                return False

        for tp_a, tp_b in [
            (self.r_turn_analytical, other.r_turn_analytical),
            (self.r_turn_numerical, other.r_turn_numerical),
        ]:
            if (tp_a is None) != (tp_b is None):
                return False
            if tp_a is not None and tp_b is not None:
                if not np.isclose(tp_a, tp_b, atol=atol, rtol=rtol, equal_nan=equal_nan):
                    return False
        return True


def _extract_metric_parameters(metric: SpacetimeMetric) -> Tuple[float, float, float]:
    """Extracts physical mass M, signed spin a, and outer horizon radius r_+ from a metric.

    Parameters
    ----------
    metric : SpacetimeMetric
        Spacetime metric instance (KerrMetric or SchwarzschildMetric).

    Returns
    -------
    Tuple[float, float, float]
        (mass, spin, r_plus).
    """
    if not isinstance(metric, SpacetimeMetric):
        raise TypeError(f"metric must be an instance of SpacetimeMetric, got {type(metric).__name__}")
    mass = float(metric.mass)
    spin = float(getattr(metric, "spin", 0.0))
    if isinstance(metric, KerrMetric):
        r_plus = float(metric.horizon_radius)
    elif isinstance(metric, SchwarzschildMetric):
        r_plus = float(metric.horizon_radius)
    else:
        r_plus = float(getattr(metric, "horizon_radius", mass + np.sqrt(max(0.0, mass**2 - spin**2))))
    return mass, spin, r_plus


def critical_photon_impact_parameter(metric: SpacetimeMetric, b: float) -> float:
    """Returns the signed critical circular photon orbit impact parameter b_ph matching ray orientation.

    Parameters
    ----------
    metric : SpacetimeMetric
        KerrMetric or SchwarzschildMetric instance.
    b : float
        Signed impact parameter of the ray, b = L_z / E.

    Returns
    -------
    float
        Signed critical impact parameter b_ph.
    """
    mass, a, _ = _extract_metric_parameters(metric)
    if a == 0.0:
        sign = 1.0 if b >= 0.0 else -1.0
        return float(sign * 3.0 * np.sqrt(3.0) * mass)

    if abs(a) == mass:
        # Exact-extremal limiting values:
        # Prograde (b * a > 0): b_ph = 2 * a
        # Retrograde (b * a < 0): b_ph = -7 * a
        # b == 0: default to prograde branch reference
        if b * a > 0.0 or b == 0.0:
            return float(2.0 * a)
        else:
            return float(-7.0 * a)

    # For Kerr spacetime:
    # Prograde motion has sign(L_z) == sign(a), i.e., b * a > 0.
    # Retrograde motion has sign(L_z) != sign(a), i.e., b * a < 0.
    if b * a > 0.0:
        # Ray is prograde
        return float(kerr_equatorial_photon_impact_parameter(metric, prograde=True))
    elif b * a < 0.0:
        # Ray is retrograde
        return float(kerr_equatorial_photon_impact_parameter(metric, prograde=False))
    else:
        # b == 0: default to prograde branch for threshold reference
        return float(kerr_equatorial_photon_impact_parameter(metric, prograde=True))


def equatorial_photon_potential(
    r: Union[float, np.ndarray],
    metric: SpacetimeMetric,
    b: float,
    energy: float = 1.0,
) -> Union[float, np.ndarray]:
    """Calculates the equatorial null radial potential R(r) for Kerr spacetime.

    Evaluates:
        R(r) = [E(r^2 + a^2) - a L_z]^2 - Delta (L_z - a E)^2
    where Delta = r^2 - 2Mr + a^2, L_z = b * E.

    Parameters
    ----------
    r : float or np.ndarray
        Radial coordinate r (or array of radii).
    metric : SpacetimeMetric
        KerrMetric or SchwarzschildMetric instance.
    b : float
        Signed impact parameter b = L_z / E.
    energy : float, optional
        Conserved photon energy E > 0, by default 1.0.

    Returns
    -------
    float or np.ndarray
        Value of R(r).
    """
    mass, a, _ = _extract_metric_parameters(metric)
    if energy <= 0.0:
        raise ValueError(f"Photon energy must be strictly positive, got energy = {energy}")

    r_arr = np.asarray(r, dtype=float)
    delta = r_arr**2 - 2.0 * mass * r_arr + a**2
    term1 = energy * (r_arr**2 + a**2) - a * (b * energy)
    term2 = b * energy - a * energy
    r_val = term1**2 - delta * term2**2

    if np.isscalar(r):
        return float(r_val)
    return r_val


def equatorial_photon_potential_cubic(
    r: Union[float, np.ndarray],
    metric: SpacetimeMetric,
    b: float,
) -> Union[float, np.ndarray]:
    """Calculates the depressed cubic polynomial C(r) = R(r) / (r * E^2).

    Evaluates:
        C(r) = r^3 - (b^2 - a^2) r + 2M (b - a)^2.

    Parameters
    ----------
    r : float or np.ndarray
        Radial coordinate r (or array of radii).
    metric : SpacetimeMetric
        KerrMetric or SchwarzschildMetric instance.
    b : float
        Signed impact parameter b = L_z / E.

    Returns
    -------
    float or np.ndarray
        Value of C(r).
    """
    mass, a, _ = _extract_metric_parameters(metric)
    r_arr = np.asarray(r, dtype=float)
    c_val = r_arr**3 - (b**2 - a**2) * r_arr + 2.0 * mass * (b - a)**2
    if np.isscalar(r):
        return float(c_val)
    return c_val


def equatorial_photon_scaled_cubic_residual(
    r: Union[float, np.ndarray],
    metric: SpacetimeMetric,
    b: float,
) -> Union[float, np.ndarray]:
    """Calculates the dimensionless scale-aware residual eta_C of the depressed cubic.

    Evaluates:
        eta_C = |C(r)| / (|r|^3 + |b^2 - a^2| * |r| + 2M(b - a)^2)
    where C(r) = r^3 - (b^2 - a^2)r + 2M(b - a)^2.
    A safe floor of 1e-30 is applied to the denominator to prevent division by zero.

    Parameters
    ----------
    r : float or np.ndarray
        Radial coordinate r.
    metric : SpacetimeMetric
        KerrMetric or SchwarzschildMetric instance.
    b : float
        Signed impact parameter b = L_z / E.

    Returns
    -------
    float or np.ndarray
        Dimensionless scaled residual eta_C.
    """
    mass, a, _ = _extract_metric_parameters(metric)
    r_arr = np.asarray(r, dtype=float)
    c_val = r_arr**3 - (b**2 - a**2) * r_arr + 2.0 * mass * (b - a)**2
    denom = np.abs(r_arr)**3 + np.abs(b**2 - a**2) * np.abs(r_arr) + 2.0 * mass * (b - a)**2
    denom_safe = np.maximum(denom, 1e-30)
    eta = np.abs(c_val) / denom_safe
    if np.isscalar(r):
        return float(eta)
    return eta


def equatorial_photon_turning_point(
    metric: SpacetimeMetric,
    b: float,
    energy: float = 1.0,
    tol: float = 1e-14,
) -> Optional[float]:
    """Solves for the outer radial turning point r_turn (periapsis) of an equatorial null geodesic.

    Finds the root of C(r) = 0 lying in r >= r_ph > r_+ using bracketed Brent's root-finding.

    Parameters
    ----------
    metric : SpacetimeMetric
        KerrMetric or SchwarzschildMetric instance.
    b : float
        Signed impact parameter b = L_z / E.
    energy : float, optional
        Photon energy E > 0, by default 1.0.
    tol : float, optional
        Absolute and relative root-finding tolerance, by default 1e-12.

    Returns
    -------
    Optional[float]
        Radial turning point r_turn if a turning point exists outside the horizon (supercritical
        or critical ray). Returns None if the photon is captured with no turning point (subcritical).
    """
    mass, a, r_plus = _extract_metric_parameters(metric)
    if energy <= 0.0:
        raise ValueError(f"Photon energy must be strictly positive, got energy = {energy}")

    diff_sq = b**2 - a**2
    if diff_sq <= 0.0:
        # If b^2 <= a^2, C'(r) = 3r^2 - diff_sq >= 0 for all r >= 0.
        # Since C(0) = 2M(b-a)^2 >= 0, C(r) > 0 for all r > 0. No root exists.
        return None

    r_min = float(np.sqrt(diff_sq / 3.0))
    c_min = float(2.0 * (mass * (b - a)**2 - r_min**3))

    # Threshold for critical double root
    scale = max(1.0, abs(2.0 * mass * (b - a)**2))
    if abs(c_min) <= tol * scale:
        # Critical double root at r_ph = r_min
        return r_min

    if c_min > 0.0:
        # Local minimum is strictly positive; C(r) > 0 for all r > 0. Captured.
        return None

    # Supercritical: C(r_min) < 0 and C(r) -> +inf as r -> +inf.
    # Root is uniquely bracketed in [r_min, r_hi].
    r_hi = max(r_min + 1.0, abs(b) + 2.0 * mass)
    c_hi = float(r_hi**3 - diff_sq * r_hi + 2.0 * mass * (b - a)**2)
    while c_hi <= 0.0:
        r_hi *= 2.0
        c_hi = float(r_hi**3 - diff_sq * r_hi + 2.0 * mass * (b - a)**2)

    def cubic_func(r_val: float) -> float:
        return float(r_val**3 - diff_sq * r_val + 2.0 * mass * (b - a)**2)

    root = float(brentq(cubic_func, r_min, r_hi, xtol=tol, rtol=tol))
    return root


def classify_equatorial_photon_potential(
    metric: SpacetimeMetric,
    b: float,
    energy: float = 1.0,
    tol: Optional[float] = None,
    near_crit_tol: Optional[float] = None,
) -> Tuple[ClassificationOutcome, Optional[float], float]:
    """Analytically classifies an equatorial null geodesic based on its radial potential.

    Three-tier analytical classification policy:
    1. Exact critical separatrix: |b - b_ph| / |b_ph| <= tol (where tol defaults to machine
       representation precision 100 * eps_mach ~ 2.22e-14). Returns 'CRITICAL'.
    2. Finite uncertainty band: If near_crit_tol is provided and tol < |rel_diff| <= near_crit_tol,
       returns 'NEAR_CRITICAL'.
    3. Basin of attraction:
       - rel_diff > tol: Supercritical basin. Returns 'SCATTERED' and periapsis root r_turn > r_ph.
       - rel_diff < -tol: Subcritical basin. Returns 'CAPTURED' and None.

    Parameters
    ----------
    metric : SpacetimeMetric
        KerrMetric or SchwarzschildMetric instance.
    b : float
        Signed impact parameter b = L_z / E.
    energy : float, optional
        Photon energy E > 0, by default 1.0.
    tol : float, optional
        Relative tolerance for identifying the exact critical separatrix (|b| == |b_ph|).
        Defaults to 100 * np.finfo(float).eps (~2.22e-14).
    near_crit_tol : float, optional
        Optional uncertainty band width. If provided, trajectories with
        tol < |rel_diff| <= near_crit_tol are classified as 'NEAR_CRITICAL'.

    Returns
    -------
    Tuple[ClassificationOutcome, Optional[float], float]
        (classification, r_turn, b_ph)
    """
    b_ph = critical_photon_impact_parameter(metric, b)
    rel_diff = (abs(b) - abs(b_ph)) / abs(b_ph)

    tol_mach = 100.0 * np.finfo(float).eps if tol is None else float(tol)

    if abs(rel_diff) <= tol_mach:
        r_turn = equatorial_photon_turning_point(metric, b, energy=energy, tol=1e-14)
        return "CRITICAL", r_turn, b_ph

    if near_crit_tol is not None and abs(rel_diff) <= near_crit_tol:
        r_turn = equatorial_photon_turning_point(metric, b, energy=energy, tol=1e-14) if rel_diff > 0.0 else None
        return "NEAR_CRITICAL", r_turn, b_ph

    if rel_diff > 0.0:
        r_turn = equatorial_photon_turning_point(metric, b, energy=energy, tol=1e-14)
        return "SCATTERED", r_turn, b_ph
    else:
        return "CAPTURED", None, b_ph


def equatorial_photon_initial_state(
    metric: SpacetimeMetric,
    b: float,
    r0: float = 50.0,
    energy: float = 1.0,
    radial_direction: str = "inward",
    t0: float = 0.0,
    phi0: float = 0.0,
) -> np.ndarray:
    """Constructs a valid 8-component canonical initial state for an equatorial null geodesic.

    The state vector has ordering (x0, r, theta, phi, p0, pr, ptheta, pphi) and satisfies:
        x0 = t0
        r = r0
        theta = pi / 2
        phi = phi0
        p0 = -energy (E > 0)
        pphi = b * energy
        ptheta = 0.0
        pr = inward/outward root of canonical Hamiltonian constraint H = 0.

    Parameters
    ----------
    metric : SpacetimeMetric
        KerrMetric or SchwarzschildMetric instance.
    b : float
        Signed impact parameter b = L_z / E.
    r0 : float, optional
        Initial radial coordinate r0, by default 50.0. Must be strictly outside the event horizon.
    energy : float, optional
        Conserved photon energy E > 0, by default 1.0.
    radial_direction : {'inward', 'outward'}, optional
        Initial radial direction, by default 'inward'.
    t0 : float, optional
        Initial coordinate time t0, by default 0.0.
    phi0 : float, optional
        Initial azimuthal angle phi0, by default 0.0.

    Returns
    -------
    np.ndarray
        8-component canonical state vector.
    """
    mass, a, r_plus = _extract_metric_parameters(metric)
    if r0 <= r_plus:
        raise ValueError(f"r0 = {r0} must be strictly outside the horizon r_+ = {r_plus}")
    if energy <= 0.0:
        raise ValueError(f"energy must be strictly positive, got energy = {energy}")

    x0_pos = np.array([t0, r0, np.pi / 2.0, phi0], dtype=float)
    kerr_m = KerrMetric(mass=mass, spin=a) if not isinstance(metric, KerrMetric) else metric
    return kerr_geodesic_initial_state(
        metric=kerr_m,
        x=x0_pos,
        energy=energy,
        Lz=b * energy,
        mu=0.0,
        radial_direction=radial_direction,
    )


def integrate_equatorial_photon(
    metric: SpacetimeMetric,
    b: float,
    r0: float = 50.0,
    energy: float = 1.0,
    lambda_span: Tuple[float, float] = (0.0, 200.0),
    r_escape: Optional[float] = None,
    horizon_epsilon: float = DEFAULT_HORIZON_BUFFER,
    rtol: float = DEFAULT_RTOL,
    atol: float = DEFAULT_ATOL,
    method: str = "DOP853",
    max_step: float = 0.5,
    terminal_turning_point: bool = False,
) -> GeodesicIntegrationResult:
    """Integrates an incoming equatorial null geodesic from r0 with automated event monitoring.

    Configures:
    1. HorizonCutoffEvent: r = r_+(1 + horizon_epsilon), terminal=True, direction=-1.
    2. RadialTurningPointEvent: dr/dlambda = 0, terminal=terminal_turning_point, direction=+1.
    3. EscapeRadiusEvent: r = r_esc (default r0), terminal=True, direction=+1.

    Parameters
    ----------
    metric : SpacetimeMetric
        KerrMetric or SchwarzschildMetric instance.
    b : float
        Signed impact parameter b = L_z / E.
    r0 : float, optional
        Initial emission radius, by default 50.0.
    energy : float, optional
        Conserved energy E > 0, by default 1.0.
    lambda_span : Tuple[float, float], optional
        Integration affine parameter span (lambda_start, lambda_end), by default (0.0, 200.0).
    r_escape : float, optional
        Escape boundary radius, by default equal to r0.
    horizon_epsilon : float, optional
        Fractional exterior buffer above outer horizon r_+, by default DEFAULT_HORIZON_BUFFER.
    rtol : float, optional
        Relative integration tolerance, by default DEFAULT_RTOL (1e-10).
    atol : float, optional
        Absolute integration tolerance, by default DEFAULT_ATOL (1e-12).
    method : str, optional
        ODE solver method, by default 'DOP853'.
    max_step : float, optional
        Maximum integration step size, by default 0.5.
    terminal_turning_point : bool, optional
        Whether the radial turning point terminates integration, by default False.
        When False, the trajectory passes periapsis and integrates out to r_escape.

    Returns
    -------
    GeodesicIntegrationResult
        Integrated trajectory result with triggered events.
    """
    y0 = equatorial_photon_initial_state(
        metric=metric,
        b=b,
        r0=r0,
        energy=energy,
        radial_direction="inward",
    )
    r_esc_val = float(r_escape if r_escape is not None else r0)

    events = [
        HorizonCutoffEvent(
            metric=metric,
            epsilon=horizon_epsilon,
            terminal=True,
            direction=-1,
            name="horizon_cutoff",
        ),
        RadialTurningPointEvent(
            metric=metric,
            terminal=terminal_turning_point,
            direction=1,
            name="radial_turning_point",
        ),
        EscapeRadiusEvent(
            r_escape=r_esc_val,
            terminal=True,
            direction=1,
            name="escape_radius",
        ),
    ]

    return integrate_geodesic(
        initial_state=y0,
        metric=metric,
        affine_span=lambda_span,
        events=events,
        rtol=rtol,
        atol=atol,
        method=method,
        max_step=max_step,
    )


def classify_equatorial_photon_trajectory(
    result: GeodesicIntegrationResult,
    metric: SpacetimeMetric,
    b: float,
    r0: float,
    r_escape: Optional[float] = None,
    delta_crit: Optional[float] = None,
    near_crit_tol: Optional[float] = None,
    energy: float = 1.0,
) -> EquatorialPhotonClassificationResult:
    """Classifies an integrated equatorial null geodesic trajectory into physical outcome states.

    Principled classification policy distinguishing physical event outcomes, exact analytical
    critical separatrix, and finite-precision uncertainty bands:
    - Decouples the analytical classification of initial conditions (|b| == |b_ph|) from the
      empirical dynamical outcome of numerical integration over a finite affine parameter span.
    - An exact critical trajectory (analytical 'CRITICAL') integrated in finite-precision ODE
      arithmetic will eventually depart along the unstable manifold due to Lyapunov instability
      (growth rate gamma = sqrt(3)*E/r_ph). If numerical roundoff drives it inward past the barrier crest,
      the trajectory approaches the horizon and triggers horizon_cutoff at r_cut = r_+(1 + epsilon),
      resulting in a numerical outcome of 'HORIZON_CUTOFF'.
    - Returns an EquatorialPhotonClassificationResult container that faithfully preserves both the
      analytical classification and the numerical trajectory fate, while supporting backward-compatible
      equality comparisons with classification strings.

    Parameters
    ----------
    result : GeodesicIntegrationResult
        Result container returned by integrate_geodesic.
    metric : SpacetimeMetric
        KerrMetric or SchwarzschildMetric instance.
    b : float
        Signed impact parameter b = L_z / E.
    r0 : float
        Initial radial coordinate.
    r_escape : float, optional
        Escape boundary radius, by default r0.
    delta_crit : float, optional
        Threshold for analytical exact critical identification. Defaults to
        100 * np.finfo(float).eps (~2.22e-14).
    near_crit_tol : float, optional
        Optional uncertainty band width. If provided and delta_crit < |rel_diff| <= near_crit_tol,
        the analytical classification is 'NEAR_CRITICAL'.
    energy : float, optional
        Conserved photon energy E > 0, by default 1.0.

    Returns
    -------
    EquatorialPhotonClassificationResult
        Structured classification result containing analytical classification, numerical outcome,
        criticality measures, turning points, and event history.
    """
    mass, a, r_plus = _extract_metric_parameters(metric)
    r_esc_val = float(r_escape if r_escape is not None else r0)

    b_ph = critical_photon_impact_parameter(metric, b)
    rel_diff = (abs(b) - abs(b_ph)) / abs(b_ph)
    tol_mach = 100.0 * np.finfo(float).eps if delta_crit is None else float(delta_crit)

    # 1. Analytical classification from potential
    analytical_cls, r_turn_ana, _ = classify_equatorial_photon_potential(
        metric=metric,
        b=b,
        energy=energy,
        tol=tol_mach,
        near_crit_tol=near_crit_tol,
    )

    # 2. Inspect event trigger records
    triggered_names = tuple(rec.name for rec in result.triggered_events)
    has_horizon_cutoff = "horizon_cutoff" in triggered_names
    has_turning_point = "radial_turning_point" in triggered_names
    has_escape = "escape_radius" in triggered_names

    # Extract numerical turning point radius if triggered
    r_turn_num: Optional[float] = None
    if has_turning_point:
        for rec in result.triggered_events:
            if rec.name == "radial_turning_point":
                r_turn_num = float(rec.states[0, IDX_R])
                break

    # Determine photon orbit radius for dwell diagnostics
    if a == 0.0:
        r_ph = 3.0 * mass
    elif abs(a) == mass:
        r_ph = mass if (b * a > 0.0 or b == 0.0) else 4.0 * mass
    elif b * a > 0.0:
        r_ph = float(kerr_equatorial_photon_orbit_radius(metric, prograde=True))
    else:
        r_ph = float(kerr_equatorial_photon_orbit_radius(metric, prograde=False))

    r_history = result.states[:, IDX_R]
    near_r_ph = np.abs(r_history - r_ph) < 0.5 * mass
    dwell_fraction = float(np.sum(near_r_ph)) / len(r_history)
    final_affine = float(result.lambdas[-1])
    final_r = float(r_history[-1])

    # 3. Determine empirical numerical trajectory outcome
    numerical_outcome: str = "UNRESOLVED"

    # A. Numerical HORIZON_CUTOFF outcome:
    # Trajectory triggered horizon_cutoff at r_cut = r_+(1 + epsilon) with inward velocity.
    # Distinguishes numerical boundary termination from demonstrated physical capture.
    if has_horizon_cutoff:
        numerical_outcome = "HORIZON_CUTOFF"

    # B. Physical SCATTERED outcome:
    # Trajectory exhibits an outer turning point (r_turn > r_plus) and subsequently moves outward
    elif has_turning_point and r_turn_num is not None and r_turn_num > r_plus:
        final_rhs = hamiltonian_rhs(result.states[-1], metric)
        tp_rec = [rec for rec in result.triggered_events if rec.name == "radial_turning_point"][0]
        is_scattering_branch = (
            has_escape
            or (tp_rec.terminal and result.terminal_event_occurred and rel_diff > 0.0)
            or (final_r > 2.0 * r_ph and final_rhs[IDX_R] > 0.0)
        )
        if is_scattering_branch:
            numerical_outcome = "SCATTERED"
        elif dwell_fraction > 0.3 or abs(final_r - r_ph) < 0.5 * mass:
            numerical_outcome = "DWELLING"
        else:
            numerical_outcome = "UNRESOLVED"

    # C. Sustained DWELLING near photon orbit without exit:
    elif dwell_fraction > 0.3 and final_affine >= 50.0 * mass:
        numerical_outcome = "DWELLING"

    else:
        numerical_outcome = "UNRESOLVED"

    return EquatorialPhotonClassificationResult(
        analytical_classification=analytical_cls,
        numerical_outcome=numerical_outcome,
        impact_parameter=float(b),
        critical_impact_parameter=float(b_ph),
        criticality_measure=float(rel_diff),
        criticality_tolerance=float(tol_mach),
        event_history=triggered_names,
        r_turn_analytical=r_turn_ana,
        r_turn_numerical=r_turn_num,
        dwell_fraction=dwell_fraction,
        final_affine_parameter=final_affine,
        final_radius=final_r,
    )
