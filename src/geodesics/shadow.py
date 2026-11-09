"""Kerr black hole shadow boundary construction and analysis.

This module provides mathematically rigorous, scale-invariant computation of Kerr black
hole shadow boundaries as seen by distant observers in celestial Bardeen coordinates
(alpha, beta).

Theoretical Foundations:
------------------------
For a Kerr black hole of mass M and spin parameter a in Boyer-Lindquist coordinates,
null geodesics decouple via Carter's constant Q (or eta = Q / E^2) and axial angular
momentum L_z (or xi = L_z / E).

Spherical photon orbits (unstable photon orbits at constant coordinate radius r) satisfy
the simultaneous conditions:
    R(r) = 0,    R'(r) = 0.

Eliminating Carter constants yields the unique parameterization for exterior spherical
photon orbits r in [r_ph_pro, r_ph_retro]:
    xi(r) = [ M*(r^2 - a^2) - r*Delta ] / [ a * (r - M) ]
    eta(r) = r^3 * [ 4*M*a^2 - r*(r - 3*M)^2 ] / [ a^2 * (r - M)^2 ]
where Delta = r^2 - 2*M*r + a^2.

For an asymptotic observer at inclination theta_o, celestial Bardeen screen coordinates
(alpha, beta) correspond to conserved impact parameters:
    alpha = - xi / sin(theta_o)
    beta = +- sqrt( eta + a^2*cos^2(theta_o) - xi^2*cot^2(theta_o) )

For exact extremality (|a| = M), exterior spherical photon orbits are supplemented by
the Near-Horizon Extreme Kerr (NHEK) vertical line segment spanning:
    alpha = - 2*a / sin(theta_o)
    beta in [-beta_max, +beta_max]
where beta_max = M * sqrt(max(0, 3 - C(theta_o))) and:
    C(theta_o) = cos^2(theta_o) * (3 + cos^2(theta_o)) / (1 - cos^2(theta_o)) >= 0.
The critical observer inclination below which the NHEK segment is completely shielded is:
    theta_crit = arccos(sqrt(2*sqrt(3) - 3)) approx 47.058597135 degrees.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, Tuple, Union

import numpy as np
from scipy.optimize import brentq

from geodesics.constants import DEFAULT_MASS
from geodesics.metrics.base import SpacetimeMetric
from geodesics.metrics.kerr import KerrMetric
from geodesics.metrics.schwarzschild import SchwarzschildMetric

__all__ = [
    "SphericalPhotonOrbit",
    "KerrShadowCurve",
    "polar_motion_u_domain",
    "spherical_orbit_polar_turning_point",
    "kerr_spherical_orbit_offsets",
    "kerr_spherical_orbit_radius_range",
    "kerr_spherical_photon_orbit_parameters",
    "kerr_admissible_shadow_offset_range",
    "kerr_admissible_shadow_radius_range",
    "kerr_shadow_boundary",
    "shadow_contour_normals",
    "shadow_edge_normals",
    "CRITICAL_INCLINATION_COS2",
    "CRITICAL_INCLINATION_RAD",
    "MIN_SUPPORTED_NONZERO_SPIN",
    "NEAR_POLAR_INCLINATION_THRESHOLD",
]

# Critical inclination for extremal Kerr NHEK shadow visibility: cos^2(theta_crit) = 2*sqrt(3) - 3
CRITICAL_INCLINATION_COS2: float = 2.0 * math.sqrt(3.0) - 3.0
CRITICAL_INCLINATION_RAD: float = math.acos(math.sqrt(CRITICAL_INCLINATION_COS2))

# Small-spin policy threshold: empirically validated down to 1e-8; for a = 0 use SchwarzschildMetric directly
MIN_SUPPORTED_NONZERO_SPIN: float = 1e-8

# Near-polar inclination threshold below which general non-polar solver experiences cot^2(th) cancellation
# and is replaced by the regular translated-circle perturbation expansion:
#   alpha = delta_0(a)*sin(theta_o) + R_pole*cos(psi),  beta = R_pole*sin(psi)
# For all spins |a| <= M, the maximum radial shape deformation is bounded by:
#   Delta R_trans <= 0.5 * M * sin^2(theta_o) <= 5.0e-11 M (for theta_o <= 1e-5 rad).
NEAR_POLAR_INCLINATION_THRESHOLD: float = 1e-5



@dataclass(frozen=True)
class SphericalPhotonOrbit:
    """Conserved parameters and turning points of a Kerr spherical photon orbit.

    Parameters
    ----------
    radius : float
        Coordinate radius r of the spherical orbit in Boyer-Lindquist coordinates [M].
    xi : float
        Normalized axial angular momentum xi = L_z / E [M].
    eta : float
        Normalized Carter constant eta = Q / E^2 [M^2].
    theta_min : float
        Minimum polar inclination angle theta_min reached by the orbit [radians].
    theta_max : float
        Maximum polar inclination angle theta_max = pi - theta_min [radians].
    """

    radius: float
    xi: float
    eta: float
    theta_min: float
    theta_max: float

    @property
    def is_equatorial(self) -> bool:
        """Whether the spherical photon orbit is equatorial (theta = pi/2)."""
        return abs(self.eta) < 1e-12 or abs(self.theta_min - 0.5 * math.pi) < 1e-12

    @property
    def inclination_bound(self) -> float:
        """Minimum polar inclination angle reached by the orbit (same as theta_min)."""
        return self.theta_min


@dataclass(frozen=True)
class KerrShadowCurve:
    """Closed, counter-clockwise parameterization of a Kerr black hole shadow boundary.

    The boundary curve is stored as an open array of M_pts distinct vertices
    (alpha_i, beta_i) for i = 0, ..., M_pts - 1 without repeating the initial
    vertex at the end. The closing edge from vertex M_pts - 1 back to vertex 0
    is implicit.

    All array fields are backed by immutable, contiguous float64 bytes buffers.
    Tampering with array writeable flags will raise an explicit ValueError.

    Parameters
    ----------
    alpha : np.ndarray
        Horizontal celestial Bardeen screen coordinates [M], shape (M_pts,).
    beta : np.ndarray
        Vertical celestial Bardeen screen coordinates [M], shape (M_pts,).
    radius : np.ndarray
        Generating spherical orbit radii r [M], shape (M_pts,).
    xi : np.ndarray
        Generating normalized angular momenta xi = L_z / E [M], shape (M_pts,).
    eta : np.ndarray
        Generating normalized Carter constants eta = Q / E^2 [M^2], shape (M_pts,).
    dalpha_dlambda : np.ndarray
        Tangent derivative dalpha/dlambda along normalized curve parameter lambda, shape (M_pts,).
    dbeta_dlambda : np.ndarray
        Tangent derivative dbeta/dlambda along normalized curve parameter lambda, shape (M_pts,).
    observer_inclination : float
        Observer polar inclination angle theta_o [radians].
    spin : float
        Spacetime spin parameter a [M].
    mass : float
        Spacetime mass M [M].
    """

    alpha: np.ndarray
    beta: np.ndarray
    radius: np.ndarray
    xi: np.ndarray
    eta: np.ndarray
    dalpha_dlambda: np.ndarray
    dbeta_dlambda: np.ndarray
    observer_inclination: float
    spin: float
    mass: float

    def __post_init__(self) -> None:
        """Validate shapes, finiteness, non-degeneracy, CCW orientation, and enforce immutability."""
        array_names = (
            "alpha",
            "beta",
            "radius",
            "xi",
            "eta",
            "dalpha_dlambda",
            "dbeta_dlambda",
        )
        first_len: Optional[int] = None

        for name in array_names:
            arr = getattr(self, name)
            if not isinstance(arr, np.ndarray):
                arr = np.asarray(arr, dtype=np.float64)
            if arr.ndim != 1:
                raise ValueError(
                    f"Array '{name}' must be 1-dimensional, got ndim={arr.ndim} with shape {arr.shape}."
                )
            if first_len is None:
                first_len = len(arr)
                if first_len < 3:
                    raise ValueError(
                        f"KerrShadowCurve requires at least 3 vertices, got {first_len}."
                    )
            elif len(arr) != first_len:
                raise ValueError(
                    f"Length mismatch: array '{name}' has length {len(arr)}, expected {first_len}."
                )
            if not np.all(np.isfinite(arr)):
                raise ValueError(
                    f"Array '{name}' contains non-finite entries (NaN or Inf)."
                )

            # Defensive copy backed by immutable bytes buffer to prevent tampering
            immutable_copy = np.frombuffer(
                np.ascontiguousarray(arr, dtype=np.float64).tobytes(),
                dtype=np.float64,
            )
            object.__setattr__(self, name, immutable_copy)

        # Validate scalars
        if not (math.isfinite(self.observer_inclination) and 0.0 <= self.observer_inclination <= math.pi):
            raise ValueError(
                f"observer_inclination must be in [0, pi], got {self.observer_inclination}."
            )
        if not (math.isfinite(self.mass) and self.mass > 0.0):
            raise ValueError(f"mass must be strictly positive, got {self.mass}.")
        if not (math.isfinite(self.spin) and abs(self.spin) <= self.mass):
            raise ValueError(
                f"spin magnitude |a| must not exceed mass M, got spin={self.spin}, mass={self.mass}."
            )

        # Check consecutive vertex uniqueness (open array convention)
        alpha_arr = self.alpha
        beta_arr = self.beta
        d_alpha = np.diff(alpha_arr)
        d_beta = np.diff(beta_arr)
        edge_lens = np.hypot(d_alpha, d_beta)
        if np.any(edge_lens < 1e-13):
            raise ValueError("KerrShadowCurve contains consecutive duplicate vertices.")

        closing_len = math.hypot(alpha_arr[0] - alpha_arr[-1], beta_arr[0] - beta_arr[-1])
        if closing_len < 1e-13:
            raise ValueError(
                "KerrShadowCurve initial and terminal vertices are duplicate; open array polygon required."
            )

        # Verify positive CCW signed area under implicit closure
        signed_area = self._compute_signed_area()
        if signed_area <= 0.0:
            raise ValueError(
                f"KerrShadowCurve polygon must have strictly positive CCW area, got {signed_area}."
            )

    def _compute_signed_area(self) -> float:
        """Compute the signed polygon area under counter-clockwise traversal."""
        alpha = self.alpha
        beta = self.beta
        # Implicit closing edge: (i + 1) % N
        return 0.5 * float(np.sum(alpha * np.roll(beta, -1) - np.roll(alpha, -1) * beta))

    @property
    def area(self) -> float:
        """Total celestial screen area enclosed by the discrete shadow boundary polygon [M^2].

        Computed via the discrete Shoelace formula (Green's theorem for polygons)
        under implicit cyclic closure. For an N-vertex regular polygon sampling of a
        circular contour of radius R, this discrete area is A_N = 0.5 * N * R^2 * sin(2*pi/N),
        which differs from the continuous circular area pi * R^2 by a relative discretization
        factor of 1 - 2*pi^2 / (3*N^2) + O(N^-4) (~2.63e-5 for N = 500).
        """
        return self._compute_signed_area()

    @property
    def centroid(self) -> Tuple[float, float]:
        """Centroid (alpha_c, beta_c) of the shadow boundary on the celestial screen [M]."""
        alpha = self.alpha
        beta = self.beta
        cross = alpha * np.roll(beta, -1) - np.roll(alpha, -1) * beta
        a_val = self.area
        c_alpha = float(np.sum((alpha + np.roll(alpha, -1)) * cross) / (6.0 * a_val))
        c_beta = float(np.sum((beta + np.roll(beta, -1)) * cross) / (6.0 * a_val))
        return (c_alpha, c_beta)

    @property
    def width(self) -> float:
        """Horizontal extent max(alpha) - min(alpha) of the shadow boundary [M]."""
        return float(np.max(self.alpha) - np.min(self.alpha))

    @property
    def height(self) -> float:
        """Vertical extent max(beta) - min(beta) of the shadow boundary [M]."""
        return float(np.max(self.beta) - np.min(self.beta))

    @property
    def is_closed(self) -> bool:
        """Whether the curve forms a topologically closed polygon."""
        return True


def polar_motion_u_domain(
    metric: SpacetimeMetric, xi: float, eta: float
) -> Optional[Tuple[float, float]]:
    """Calculates the allowed physical range of u = cos^2(theta) in [0, 1] for null geodesics.

    In Boyer-Lindquist coordinates, the polar geodesic potential Theta(theta) satisfies:
        Theta(theta) / E^2 = eta + a^2*cos^2(theta) - xi^2*cot^2(theta) >= 0.
    Setting u = cos^2(theta) in [0, 1] and multiplying by sin^2(theta) = 1 - u yields:
        P(u) = a^2*u^2 + (xi^2 + eta - a^2)*u - eta <= 0.

    Dimensional units:
        xi has units of length [M].
        eta has units of length squared [M^2].
    Internally, parameters are scaled to dimensionless quantities:
        chi = a / M,    bar_xi = xi / M,    bar_eta = eta / M^2.

    Parameters
    ----------
    metric : SpacetimeMetric
        Spacetime metric providing mass M and spin a.
    xi : float
        Conserved axial impact parameter xi = L_z / E [M].
    eta : float
        Conserved Carter constant eta = Q / E^2 [M^2].

    Returns
    -------
    Optional[Tuple[float, float]]
        Tuple (u_min, u_max) defining the connected physical domain in [0, 1],
        or None if no real physical polar motion is possible.
    """
    m_val = float(metric.mass)
    if m_val <= 0.0:
        raise ValueError(f"Metric mass must be strictly positive, got {m_val}.")

    a_val = float(getattr(metric, "spin", 0.0))
    chi = a_val / m_val
    if abs(chi) > 1.0:
        raise ValueError(f"Spin parameter |a/M| must not exceed 1.0, got {chi}.")

    bar_xi = float(xi) / m_val
    bar_eta = float(eta) / (m_val * m_val)

    # Schwarzschild branch: chi == 0
    if abs(chi) == 0.0:
        if bar_eta < 0.0:
            return None
        if bar_eta == 0.0:
            if abs(bar_xi) == 0.0:
                # Radial ray: passes through poles and equator freely
                return (0.0, 1.0)
            # Equatorial motion only: u = 0
            return (0.0, 0.0)
        # bar_eta > 0: B = bar_xi^2 + bar_eta > 0
        b_val = bar_xi * bar_xi + bar_eta
        u_max = min(1.0, max(0.0, bar_eta / b_val))
        return (0.0, u_max)

    # Kerr branch: chi != 0
    # Quadratic: P(u) = chi^2 * u^2 + B * u - bar_eta <= 0
    chi2 = chi * chi
    b_val = bar_xi * bar_xi + bar_eta - chi2

    # Sign-preserving scaled discriminant:
    # D = B^2 + 4 * chi^2 * bar_eta
    # Let q = 2 * |chi| * sqrt(|bar_eta|), S = max(|B|, q)
    abs_eta = abs(bar_eta)
    q_val = 2.0 * abs(chi) * math.sqrt(abs_eta)
    s_scale = max(abs(b_val), q_val)

    if s_scale == 0.0:
        d_scaled = 0.0
        sqrt_d = 0.0
    else:
        sgn_eta = 1.0 if bar_eta > 0.0 else (-1.0 if bar_eta < 0.0 else 0.0)
        d_scaled = (b_val / s_scale) ** 2 + sgn_eta * (q_val / s_scale) ** 2
        if d_scaled < 0.0:
            return None
        sqrt_d = s_scale * math.sqrt(max(0.0, d_scaled))

    if bar_eta > 0.0:
        # P(0) = -bar_eta < 0, P(1) = bar_xi^2 >= 0
        # Exactly one positive root u_max in (0, 1]
        u_max = (2.0 * bar_eta) / (sqrt_d + b_val)
        u_max = min(1.0, max(0.0, u_max))
        return (0.0, u_max)

    if bar_eta == 0.0:
        # P(u) = u * (chi^2 * u + B)
        # Root 1: u = 0; Root 2: u = -B / chi^2 = 1 - bar_xi^2 / chi^2
        if bar_xi * bar_xi < chi2:
            u_max = min(1.0, max(0.0, 1.0 - (bar_xi * bar_xi) / chi2))
            return (0.0, u_max)
        return (0.0, 0.0)

    # bar_eta < 0:
    # P(0) = -bar_eta > 0. Motion requires real roots (d_scaled >= 0) and B < 0
    if b_val >= 0.0:
        return None

    # If bar_xi == 0, polar axis accessibility requires bar_eta + chi^2 >= 0
    if abs(bar_xi) == 0.0 and (bar_eta + chi2) < 0.0:
        return None

    # Two positive roots of P(u) = 0
    u_min = (2.0 * (-bar_eta)) / (-b_val + sqrt_d)
    u_max = (-b_val + sqrt_d) / (2.0 * chi2)

    if u_min > u_max or u_min > 1.0 or u_max < 0.0:
        return None

    u_lo = max(0.0, u_min)
    u_hi = min(1.0, u_max)
    if u_lo > u_hi:
        return None
    return (u_lo, u_hi)


def spherical_orbit_polar_turning_point(
    metric: SpacetimeMetric, xi: float, eta: float
) -> float:
    """Calculates the maximum value of u = cos^2(theta) accessible to the orbit.

    Parameters
    ----------
    metric : SpacetimeMetric
        Spacetime metric instance.
    xi : float
        Conserved axial impact parameter xi = L_z / E [M].
    eta : float
        Conserved Carter constant eta = Q / E^2 [M^2].

    Returns
    -------
    float
        Maximum accessible value u_max in [0, 1].

    Raises
    ------
    ValueError
        If no physical polar motion exists for the given (xi, eta).
    """
    domain = polar_motion_u_domain(metric, xi, eta)
    if domain is None:
        raise ValueError(
            f"No physical polar motion exists for metric spin={getattr(metric, 'spin', 0.0)}, "
            f"mass={metric.mass}, xi={xi}, eta={eta}."
        )
    return domain[1]


def kerr_spherical_orbit_offsets(metric: SpacetimeMetric) -> Tuple[float, float]:
    """Calculates dimensionless coordinate radius offsets (u = r - 3M) for equatorial photon orbits.

    Parameters
    ----------
    metric : SpacetimeMetric
        Spacetime metric (SchwarzschildMetric or KerrMetric).

    Returns
    -------
    Tuple[float, float]
        Tuple (u_min, u_max) of radial offsets u = r - 3M in [M].
    """
    m_val = float(metric.mass)
    a_val = float(metric.spin)
    chi = abs(a_val) / m_val

    if chi > 1.0:
        raise ValueError(f"Spin parameter |a/M| must not exceed 1.0, got {chi}.")

    if chi == 0.0:
        return (0.0, 0.0)

    if 0.0 < chi < MIN_SUPPORTED_NONZERO_SPIN:
        raise ValueError(
            f"Spin parameter 0 < |a/M| < {MIN_SUPPORTED_NONZERO_SPIN} is not supported; "
            f"use a=0 exactly or |a/M| >= {MIN_SUPPORTED_NONZERO_SPIN}."
        )

    # Numerically stable offset formulation: delta = (2/3) * asin(chi)
    # Avoids catastrophic cancellation from subtracting 3M at small spin:
    # r_pro/M - 3 = -sqrt(3)*sin(delta) - 2*sin^2(delta/2)
    # r_retro/M - 3 = +sqrt(3)*sin(delta) - 2*sin^2(delta/2)
    delta = (2.0 / 3.0) * math.asin(chi)
    sin_delta = math.sin(delta)
    sin_half_delta = math.sin(0.5 * delta)
    u_pro = m_val * (-math.sqrt(3.0) * sin_delta - 2.0 * (sin_half_delta ** 2))
    u_retro = m_val * (math.sqrt(3.0) * sin_delta - 2.0 * (sin_half_delta ** 2))
    return (min(u_pro, u_retro), max(u_pro, u_retro))


def kerr_spherical_orbit_radius_range(metric: SpacetimeMetric) -> Tuple[float, float]:
    """Calculates the physical radius range [r_ph_pro, r_ph_retro] of spherical photon orbits.

    Parameters
    ----------
    metric : SpacetimeMetric
        Kerr spacetime metric.

    Returns
    -------
    Tuple[float, float]
        Tuple (r_min, r_max) of equatorial circular photon orbit radii in [M].
    """
    m_val = float(metric.mass)
    u_min, u_max = kerr_spherical_orbit_offsets(metric)
    return (3.0 * m_val + u_min, 3.0 * m_val + u_max)


def kerr_spherical_photon_orbit_parameters(
    metric: KerrMetric, r: float
) -> SphericalPhotonOrbit:
    """Calculates conserved parameters and turning points for a spherical photon orbit at radius r.

    Parameters
    ----------
    metric : KerrMetric
        Kerr spacetime metric.
    r : float
        Coordinate radius r in Boyer-Lindquist coordinates [M].

    Returns
    -------
    SphericalPhotonOrbit
        Dataclass containing radius, xi, eta, theta_min, and theta_max.
    """
    m_val = float(metric.mass)
    a_val = float(metric.spin)
    chi = a_val / m_val

    if chi == 0.0:
        if abs(r - 3.0 * m_val) > 1e-12:
            raise ValueError(f"In Schwarzschild spacetime, photon sphere is only at r = 3M, got r = {r}.")
        return SphericalPhotonOrbit(
            radius=r,
            xi=0.0,
            eta=27.0 * m_val * m_val,
            theta_min=0.0,
            theta_max=math.pi,
        )

    if 0.0 < abs(chi) < MIN_SUPPORTED_NONZERO_SPIN:
        raise ValueError(
            f"Spin parameter 0 < |a/M| < {MIN_SUPPORTED_NONZERO_SPIN} is not supported; "
            f"use a=0 exactly or |a/M| >= {MIN_SUPPORTED_NONZERO_SPIN}."
        )

    # For exact extremality (|chi| == 1.0), evaluate removable singularity analytically
    if abs(abs(chi) - 1.0) < 1e-15:
        # Stable polynomial representations eliminating (r - M) denominator:
        # xi(r) = sgn(a) * (M + 2*r - r^2 / M)
        # eta(r) = r^3 * (4*M - r) / M^2
        sgn_a = 1.0 if a_val > 0.0 else -1.0
        xi_val = sgn_a * (m_val + 2.0 * r - (r * r) / m_val)
        eta_val = (r ** 3) * (4.0 * m_val - r) / (m_val * m_val)
    else:
        u = r - 3.0 * m_val
        num_xi = -u * (9.0 * m_val * m_val + 6.0 * m_val * u + u * u) - (a_val * a_val) * (4.0 * m_val + u)
        denom_xi = a_val * (2.0 * m_val + u)
        xi_val = num_xi / denom_xi
        u_min_c, u_max_c = kerr_spherical_orbit_offsets(metric)
        r_pro_c = 3.0 * m_val + u_min_c
        r_retro_c = 3.0 * m_val + u_max_c
        r1 = 4.0 * m_val * (a_val * a_val) / (r_pro_c * r_retro_c)
        u1 = r1 - 3.0 * m_val
        num_eta = (u - u1) * (u_max_c - u) * (u - u_min_c)
        eta_val = (r ** 3) * num_eta / (a_val * a_val * ((2.0 * m_val + u) ** 2))

    # Analytical spherical orbits have eta >= 0 on [r_pro, r_retro]; clamp negative round-off
    if eta_val < 0.0 and eta_val > -1e-12:
        eta_val = 0.0

    u_max = spherical_orbit_polar_turning_point(metric, xi_val, eta_val)
    cos_theta_min = math.sqrt(max(0.0, min(1.0, u_max)))
    theta_min = math.acos(cos_theta_min)
    theta_max = math.pi - theta_min

    return SphericalPhotonOrbit(
        radius=r,
        xi=xi_val,
        eta=eta_val,
        theta_min=theta_min,
        theta_max=theta_max,
    )


def _kerr_polar_shadow_parameters(
    m_val: float, a_val: float
) -> Tuple[float, float, float, float, float]:
    """Computes exact-polar orbital and screen parameters and translation rate Delta_0.

    Parameters
    ----------
    m_val : float
        Black hole mass M > 0.
    a_val : float
        Black hole spin parameter a with |a| <= M.

    Returns
    -------
    Tuple[float, float, float, float, float]
        Tuple (r_pole, r_circle, eta_pole, delta_0, xi_prime) where:
        r_pole: physical Boyer-Lindquist coordinate radius of the polar photon orbit
        r_circle: exact polar shadow screen radius R_pole
        eta_pole: Carter constant eta at r_pole
        delta_0: first-order horizontal center translation rate d(alpha_center)/d(sin theta_o)
        xi_prime: radial derivative d(xi)/dr at r_pole
    """
    chi = a_val / m_val
    sgn_a = 1.0 if a_val > 0.0 else (-1.0 if a_val < 0.0 else 0.0)
    a_abs = abs(a_val)

    if abs(chi) == 0.0:
        return (
            3.0 * m_val,
            3.0 * math.sqrt(3.0) * m_val,
            27.0 * m_val * m_val,
            0.0,
            -3.0 * math.sqrt(3.0),
        )

    if abs(abs(chi) - 1.0) < 1e-15:
        r_pole = (1.0 + math.sqrt(2.0)) * m_val
        r_circle = 2.0 * (1.0 + math.sqrt(2.0)) * m_val
        eta_pole = r_circle * r_circle - a_val * a_val
        delta_0 = sgn_a * (1.0 + math.sqrt(2.0)) * m_val
        xi_prime = -sgn_a * 2.0 * math.sqrt(2.0)
        return (r_pole, r_circle, eta_pole, delta_0, xi_prime)

    f_p = lambda x: x * x * (3.0 - x) - (chi * chi) * (x + 1.0)
    x_pole = float(brentq(f_p, 1.5, 3.0, xtol=1e-15 * m_val, rtol=1e-15))
    r_pole = x_pole * m_val

    num_eta = (r_pole ** 3) * (4.0 * m_val * a_abs * a_abs - r_pole * ((r_pole - 3.0 * m_val) ** 2))
    denom_eta = a_abs * a_abs * ((r_pole - m_val) ** 2)
    eta_pole = num_eta / denom_eta
    r_circle = math.sqrt(eta_pole + a_abs * a_abs)

    d_num_xi = 6.0 * m_val * r_pole - 3.0 * r_pole * r_pole - a_abs * a_abs
    xi_prime_mag = d_num_xi / (a_abs * (r_pole - m_val))
    xi_prime = sgn_a * xi_prime_mag

    N = -r_pole**6 + 6.0 * m_val * r_pole**5 - 9.0 * m_val**2 * r_pole**4 + 4.0 * m_val * a_abs**2 * r_pole**3
    dN = -6.0 * r_pole**5 + 30.0 * m_val * r_pole**4 - 36.0 * m_val**2 * r_pole**3 + 12.0 * m_val * a_abs**2 * r_pole**2
    eta_prime = (dN * (r_pole - m_val) - 2.0 * N) / (a_abs**2 * (r_pole - m_val)**3)

    delta_0 = sgn_a * (-eta_prime / (2.0 * xi_prime_mag))
    return (r_pole, r_circle, eta_pole, delta_0, xi_prime)


def kerr_admissible_shadow_offset_range(
    metric: SpacetimeMetric, observer_inclination: float
) -> Tuple[float, float]:
    """Calculates admissible radial offset interval [u_minus, u_plus] (where u = r - 3M).

    For general inclinations (theta_o > NEAR_POLAR_INCLINATION_THRESHOLD), this finds the
    exact roots of B(u; theta_o) = 0 via root-finding.
    For near-polar inclinations (theta_o <= NEAR_POLAR_INCLINATION_THRESHOLD or >= pi - 1e-5),
    where cot^2(theta_o) division suffers numerical loss of precision, this evaluates the
    regular first-order asymptotic expansion interval:
        u = u_pole +/- (R_pole / |xi'(r_pole)|) * sin(theta_o) + O(sin^2 theta_o),
    which defines the physical range of spherical photon orbit radii visible on the screen.

    Parameters
    ----------
    metric : SpacetimeMetric
        Spacetime metric (SchwarzschildMetric or KerrMetric).
    observer_inclination : float
        Observer polar inclination angle theta_o [radians].

    Returns
    -------
    Tuple[float, float]
        Tuple (u_minus, u_plus) defining the admissible radial offset interval in [M].
    """
    if not (0.0 <= observer_inclination <= math.pi):
        raise ValueError(
            f"observer_inclination must be in [0, pi], got {observer_inclination}."
        )

    m_val = float(metric.mass)
    a_val = float(metric.spin)
    chi = a_val / m_val

    if chi == 0.0:
        return (0.0, 0.0)

    if 0.0 < abs(chi) < MIN_SUPPORTED_NONZERO_SPIN:
        raise ValueError(
            f"Spin parameter 0 < |a/M| < {MIN_SUPPORTED_NONZERO_SPIN} is not supported."
        )

    # Symmetry across the equatorial plane: theta_o and pi - theta_o are identical
    th = observer_inclination
    if th > 0.5 * math.pi:
        th = math.pi - th

    # Near-polar observer: regular expansion around r_pole avoiding cot^2(th) cancellation
    if th <= NEAR_POLAR_INCLINATION_THRESHOLD:
        r_pole, r_circle, eta_pole, delta_0, xi_prime = _kerr_polar_shadow_parameters(m_val, a_val)
        u_pole = r_pole - 3.0 * m_val
        if abs(xi_prime) > 0.0 and th > 0.0:
            delta_u = (r_circle / abs(xi_prime)) * math.sin(th)
            return (u_pole - delta_u, u_pole + delta_u)
        return (u_pole, u_pole)

    cos_th = math.cos(th)
    sin_th = math.sin(th)
    cos2 = cos_th * cos_th
    sin2 = sin_th * sin_th
    cot2 = cos2 / sin2

    u_min_orb, u_max_orb = kerr_spherical_orbit_offsets(metric)

    # Equatorial observer: B(u; pi/2) = eta(u), whose roots are analytically u_min_orb and u_max_orb
    if abs(cos_th) < 1e-14 or cos2 == 0.0:
        return (u_min_orb, u_max_orb)

    r_pro = 3.0 * m_val + u_min_orb
    r_retro = 3.0 * m_val + u_max_orb
    r1 = 4.0 * m_val * (a_val * a_val) / (r_pro * r_retro)
    u1 = r1 - 3.0 * m_val

    def xi_u(u: float) -> float:
        num = -u * (9.0 * m_val * m_val + 6.0 * m_val * u + u * u) - (a_val * a_val) * (4.0 * m_val + u)
        den = a_val * (2.0 * m_val + u)
        return num / den

    def eta_u(u: float) -> float:
        r = 3.0 * m_val + u
        num_eta = (u - u1) * (u_max_orb - u) * (u - u_min_orb)
        den_eta = (a_val * a_val) * ((2.0 * m_val + u) ** 2)
        return (r ** 3) * num_eta / den_eta

    def b_u(u: float) -> float:
        if abs(abs(chi) - 1.0) < 1e-15:
            r = 3.0 * m_val + u
            sgn_a = 1.0 if a_val > 0.0 else -1.0
            xi_v = sgn_a * (m_val + 2.0 * r - (r * r) / m_val)
            eta_v = (r ** 3) * (4.0 * m_val - r) / (m_val * m_val)
        else:
            xi_v = xi_u(u)
            eta_v = eta_u(u)
        return eta_v + (a_val * a_val) * cos2 - (xi_v * xi_v) * cot2

    # Root of G(u; theta_o) = -(3M + u)^2 * u - a^2*cos^2(theta_o)*(4M + u) = 0
    g_u = lambda u: -(3.0 * m_val + u) ** 2 * u - (a_val * a_val) * cos2 * (4.0 * m_val + u)
    u_crit = float(brentq(g_u, u_min_orb, 0.0, xtol=1e-15 * m_val, rtol=1e-15))

    # Upper root u_plus in [u_crit, u_max_orb]
    b_retro = b_u(u_max_orb)
    if abs(b_retro) < 1e-14:
        u_plus = u_max_orb
    else:
        u_plus = float(brentq(b_u, u_crit, u_max_orb, xtol=1e-15 * m_val, rtol=1e-15))

    # Lower root u_minus in [u_min_orb, u_crit]
    if abs(abs(chi) - 1.0) < 1e-15:
        c_val = cos2 * (3.0 + cos2) / sin2
        if c_val <= 3.0:
            # Supercritical/critical: admissible exterior range extends to horizon r = M (u = -2M)
            u_minus = -2.0 * m_val
        else:
            # Subcritical: exterior root exists in (-2M, u_crit)
            u_minus = float(brentq(b_u, -2.0 * m_val, u_crit, xtol=1e-15 * m_val, rtol=1e-15))
    else:
        b_pro = b_u(u_min_orb)
        if abs(b_pro) < 1e-14:
            u_minus = u_min_orb
        else:
            u_minus = float(brentq(b_u, u_min_orb, u_crit, xtol=1e-15 * m_val, rtol=1e-15))

    return (u_minus, u_plus)


def kerr_admissible_shadow_radius_range(
    metric: SpacetimeMetric, observer_inclination: float
) -> Tuple[float, float]:
    """Calculates the physical coordinate radius range [r_minus, r_plus] of spherical orbits visible on the screen.

    Parameters
    ----------
    metric : SpacetimeMetric
        Kerr spacetime metric.
    observer_inclination : float
        Observer polar inclination angle theta_o [radians].

    Returns
    -------
    Tuple[float, float]
        Tuple (r_minus, r_plus) defining the admissible radial interval.
    """
    m_val = float(metric.mass)
    u_minus, u_plus = kerr_admissible_shadow_offset_range(metric, observer_inclination)
    return (3.0 * m_val + u_minus, 3.0 * m_val + u_plus)


def kerr_shadow_boundary(
    metric: SpacetimeMetric, observer_inclination: float, n_points: int = 500
) -> KerrShadowCurve:
    """Constructs the closed counter-clockwise Kerr shadow boundary curve.

    Parameters
    ----------
    metric : SpacetimeMetric
        Spacetime metric (SchwarzschildMetric or KerrMetric).
    observer_inclination : float
        Observer polar inclination angle theta_o [radians].
    n_points : int, optional
        Target number of vertices in the open-array polygon, by default 500.

    Returns
    -------
    KerrShadowCurve
        Frozen dataclass containing immutable arrays and geometric properties.
    """
    if n_points < 10:
        raise ValueError(f"n_points must be at least 10, got {n_points}.")
    if not (0.0 <= observer_inclination <= math.pi):
        raise ValueError(
            f"observer_inclination must be in [0, pi], got {observer_inclination}."
        )

    m_val = float(metric.mass)
    a_val = float(getattr(metric, "spin", 0.0))
    chi = a_val / m_val

    if abs(chi) > 1.0:
        raise ValueError(f"Spin parameter |a/M| must not exceed 1.0, got {chi}.")

    if 0.0 < abs(chi) < MIN_SUPPORTED_NONZERO_SPIN:
        raise ValueError(
            f"Spin parameter 0 < |a/M| < {MIN_SUPPORTED_NONZERO_SPIN} is not supported; "
            f"use a=0 exactly or |a/M| >= {MIN_SUPPORTED_NONZERO_SPIN}."
        )

    th = observer_inclination
    sin_th = math.sin(th)
    is_near_polar = (th <= NEAR_POLAR_INCLINATION_THRESHOLD) or (abs(th - math.pi) <= NEAR_POLAR_INCLINATION_THRESHOLD)

    # 1. Near-polar observer (theta_o <= NEAR_POLAR_INCLINATION_THRESHOLD or >= pi - NEAR_POLAR_INCLINATION_THRESHOLD)
    if is_near_polar:
        r_pole, r_circle, eta_pole, delta_0, xi_prime = _kerr_polar_shadow_parameters(m_val, a_val)

        psi = np.linspace(0.0, 2.0 * math.pi, n_points, endpoint=False)
        alpha = delta_0 * sin_th + r_circle * np.cos(psi)
        beta = r_circle * np.sin(psi)

        if abs(xi_prime) > 0.0 and sin_th > 0.0:
            radius = r_pole - (r_circle / xi_prime) * np.cos(psi) * sin_th
        else:
            radius = np.full(n_points, r_pole, dtype=np.float64)

        xi_arr = -alpha * sin_th
        eta_arr = np.full(n_points, eta_pole, dtype=np.float64)

        dalpha = -2.0 * math.pi * r_circle * np.sin(psi)
        dbeta = 2.0 * math.pi * r_circle * np.cos(psi)

        return KerrShadowCurve(
            alpha=alpha,
            beta=beta,
            radius=radius,
            xi=xi_arr,
            eta=eta_arr,
            dalpha_dlambda=dalpha,
            dbeta_dlambda=dbeta,
            observer_inclination=observer_inclination,
            spin=a_val,
            mass=m_val,
        )

    # 2. Schwarzschild observer (a = 0, non-polar)
    if abs(chi) == 0.0:
        r_circle = 3.0 * math.sqrt(3.0) * m_val
        psi = np.linspace(0.0, 2.0 * math.pi, n_points, endpoint=False)
        alpha = r_circle * np.cos(psi)
        beta = r_circle * np.sin(psi)
        radius = np.full(n_points, 3.0 * m_val, dtype=np.float64)
        # alpha = -xi / sin(theta_o) => xi = -alpha * sin(theta_o)
        sin_th = math.sin(th)
        cos_th = math.cos(th)
        xi_arr = -alpha * sin_th
        cot_th = cos_th / sin_th
        eta_arr = beta * beta + xi_arr * xi_arr * (cot_th * cot_th)

        dalpha = -2.0 * math.pi * r_circle * np.sin(psi)
        dbeta = 2.0 * math.pi * r_circle * np.cos(psi)

        return KerrShadowCurve(
            alpha=alpha,
            beta=beta,
            radius=radius,
            xi=xi_arr,
            eta=eta_arr,
            dalpha_dlambda=dalpha,
            dbeta_dlambda=dbeta,
            observer_inclination=observer_inclination,
            spin=0.0,
            mass=m_val,
        )

    # 3. Kerr observer (a != 0, 0 < theta_o < pi)
    sin_th = math.sin(th)
    cos_th = math.cos(th)
    cos2 = cos_th * cos_th
    sin2 = sin_th * sin_th
    cot2 = cos2 / sin2

    u_minus, u_plus = kerr_admissible_shadow_offset_range(metric, observer_inclination)
    r_minus = 3.0 * m_val + u_minus
    r_plus = 3.0 * m_val + u_plus

    is_extremal = abs(abs(chi) - 1.0) < 1e-15
    c_val = cos2 * (3.0 + cos2) / sin2 if sin2 > 0.0 else math.inf
    has_nhek = is_extremal and (c_val < 3.0)

    u_min_c, u_max_c = kerr_spherical_orbit_offsets(metric)
    r_pro_c = 3.0 * m_val + u_min_c
    r_retro_c = 3.0 * m_val + u_max_c
    r1_c = 4.0 * m_val * (a_val * a_val) / (r_pro_c * r_retro_c)
    u1_c = r1_c - 3.0 * m_val

    def eval_params(u_arr: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Compute xi, eta, alpha, beta for exterior spherical orbits using offset u = r - 3M."""
        r_arr = 3.0 * m_val + u_arr
        if is_extremal:
            sgn_a = 1.0 if a_val > 0.0 else -1.0
            xi_v = sgn_a * (m_val + 2.0 * r_arr - (r_arr * r_arr) / m_val)
            eta_v = (r_arr ** 3) * (4.0 * m_val - r_arr) / (m_val * m_val)
        else:
            num_xi = -u_arr * (9.0 * m_val * m_val + 6.0 * m_val * u_arr + u_arr * u_arr) - (a_val * a_val) * (4.0 * m_val + u_arr)
            denom_xi = a_val * (2.0 * m_val + u_arr)
            xi_v = num_xi / denom_xi
            num_eta = (u_arr - u1_c) * (u_max_c - u_arr) * (u_arr - u_min_c)
            eta_v = (r_arr ** 3) * num_eta / (a_val * a_val * ((2.0 * m_val + u_arr) ** 2))

        alpha_v = -xi_v / sin_th
        radicand = eta_v + (a_val * a_val) * cos2 - (xi_v * xi_v) * cot2
        beta_pos = np.sqrt(np.maximum(0.0, radicand))
        return xi_v, eta_v, alpha_v, beta_pos

    if not has_nhek:
        # Smooth closed contour or single cusp at critical inclination
        n_half = n_points // 2
        # Cosine clustering near turning points: phi in [0, pi]
        # At phi = 0: u = u_plus; At phi = pi: u = u_minus
        phi_half = np.linspace(0.0, math.pi, n_half + 1)
        u_half = 0.5 * (u_plus + u_minus) + 0.5 * (u_plus - u_minus) * np.cos(phi_half)
        r_half = 3.0 * m_val + u_half

        xi_half, eta_half, alpha_half, beta_half = eval_params(u_half)
        # Enforce exact zero vertical coordinate at turning points
        beta_half[0] = 0.0
        beta_half[-1] = 0.0

        # Upper branch: k = 0, ..., n_half
        # Lower branch: k = n_half - 1, ..., 1 (excluding duplicate turning point endpoints)
        alpha_upper = alpha_half
        beta_upper = beta_half
        r_upper = r_half
        xi_upper = xi_half
        eta_upper = eta_half

        alpha_lower = alpha_half[::-1][1:-1]
        beta_lower = -beta_half[::-1][1:-1]
        r_lower = r_half[::-1][1:-1]
        xi_lower = xi_half[::-1][1:-1]
        eta_lower = eta_half[::-1][1:-1]

        alpha_full = np.concatenate([alpha_upper, alpha_lower])
        beta_full = np.concatenate([beta_upper, beta_lower])
        r_full = np.concatenate([r_upper, r_lower])
        xi_full = np.concatenate([xi_upper, xi_lower])
        eta_full = np.concatenate([eta_upper, eta_lower])
    else:
        # Exact-extremal supercritical: includes vertical NHEK segment at alpha = alpha_pro
        alpha_pro = -2.0 * a_val / sin_th
        beta_max = m_val * math.sqrt(max(0.0, 3.0 - c_val))

        n_nhek = max(5, n_points // 4)
        n_ext = (n_points - n_nhek) // 2

        # Upper exterior branch: phi in [0, pi/2], r from r_plus down to M
        phi_ext = np.linspace(0.0, 0.5 * math.pi, n_ext)
        u_upper = -2.0 * m_val + (u_plus - (-2.0 * m_val)) * np.cos(phi_ext)
        r_upper = 3.0 * m_val + u_upper
        xi_u, eta_u, alpha_u, beta_u = eval_params(u_upper)
        beta_u[0] = 0.0
        beta_u[-1] = beta_max
        alpha_u[-1] = alpha_pro

        # NHEK segment: strictly interior points from +beta_max down to -beta_max
        beta_nhek = np.linspace(beta_max, -beta_max, n_nhek + 2)[1:-1]
        alpha_nhek = np.full_like(beta_nhek, alpha_pro)
        r_nhek = np.full_like(beta_nhek, m_val)
        xi_nhek = np.full_like(beta_nhek, 2.0 * a_val)
        eta_nhek = beta_nhek * beta_nhek + (m_val * m_val) * c_val

        # Lower exterior branch: r from M back to r_plus (excluding M and r_plus)
        u_lower = u_upper[::-1][1:-1]
        r_lower = 3.0 * m_val + u_lower
        xi_l, eta_l, alpha_l, beta_pos_l = eval_params(u_lower)
        beta_l = -beta_pos_l

        # Assemble CCW contour:
        # Upper exterior -> NHEK segment -> bottom corner -> Lower exterior
        alpha_full = np.concatenate([alpha_u, alpha_nhek, [alpha_pro], alpha_l])
        beta_full = np.concatenate([beta_u, beta_nhek, [-beta_max], beta_l])
        r_full = np.concatenate([r_upper, r_nhek, [m_val], r_lower])
        xi_full = np.concatenate([xi_u, xi_nhek, [2.0 * a_val], xi_l])
        eta_full = np.concatenate([eta_u, eta_nhek, [3.0 * m_val * m_val], eta_l])

    # Ensure strictly counter-clockwise (CCW) traversal with positive signed area
    raw_area = 0.5 * float(np.sum(alpha_full * np.roll(beta_full, -1) - np.roll(alpha_full, -1) * beta_full))
    if raw_area < 0.0:
        alpha_full = alpha_full[::-1]
        beta_full = beta_full[::-1]
        r_full = r_full[::-1]
        xi_full = xi_full[::-1]
        eta_full = eta_full[::-1]

    # Compute periodic central differences along closed curve
    m_pts = len(alpha_full)
    dalpha_dlambda = 0.5 * m_pts * (np.roll(alpha_full, -1) - np.roll(alpha_full, 1))
    dbeta_dlambda = 0.5 * m_pts * (np.roll(beta_full, -1) - np.roll(beta_full, 1))

    return KerrShadowCurve(
        alpha=alpha_full,
        beta=beta_full,
        radius=r_full,
        xi=xi_full,
        eta=eta_full,
        dalpha_dlambda=dalpha_dlambda,
        dbeta_dlambda=dbeta_dlambda,
        observer_inclination=observer_inclination,
        spin=a_val,
        mass=m_val,
    )


def shadow_edge_normals(curve: KerrShadowCurve) -> Tuple[np.ndarray, np.ndarray]:
    """Calculates the outward unit normal vectors for each edge of the shadow polygon.

    For each edge e_i = (alpha_{i+1} - alpha_i, beta_{i+1} - beta_i) in counter-clockwise
    traversal, the outward unit normal is formed by a 90-degree clockwise rotation:
        n_out = (e_{y, i}, -e_{x, i}) / ||e_i||.

    Parameters
    ----------
    curve : KerrShadowCurve
        Kerr shadow boundary curve instance.

    Returns
    -------
    Tuple[np.ndarray, np.ndarray]
        Tuple (n_alpha, n_beta) of unit outward normal vector components for each edge i -> i+1.
    """
    alpha = curve.alpha
    beta = curve.beta
    dx = np.roll(alpha, -1) - alpha
    dy = np.roll(beta, -1) - beta
    length = np.hypot(dx, dy)
    if np.any(length < 1e-14):
        length = np.where(length < 1e-14, 1.0, length)
    nx = dy / length
    ny = -dx / length
    return (
        np.frombuffer(nx.tobytes(), dtype=np.float64),
        np.frombuffer(ny.tobytes(), dtype=np.float64),
    )


def shadow_contour_normals(
    curve: KerrShadowCurve, convention: str = "angle_bisector"
) -> Tuple[np.ndarray, np.ndarray]:
    """Calculates outward unit normal vectors at every vertex of the shadow contour.

    Mathematical Conventions:
    -------------------------
    1. 'angle_bisector' (default):
       The vertex normal is the exact geometric angle bisector of the adjacent incoming
       and outgoing edges. The incoming and outgoing edge direction vectors are normalized
       individually to unit vectors before summing:
           u_b = (x_i - x_{i-1}) / ||x_i - x_{i-1}||
           u_f = (x_{i+1} - x_i) / ||x_{i+1} - x_i||
           n_sum = (u_{b, y} + u_{f, y}, -(u_{b, x} + u_{f, x}))
           n_out = n_sum / ||n_sum||
       This convention is strictly invariant under nonuniform mesh spacing (such as
       cosine-clustered parameterizations).

    2. 'central_difference':
       Length-weighted central difference normal:
           t = x_{i+1} - x_{i-1} = e_b + e_f
           n_out = (t_y, -t_x) / ||t||
       On nonuniform polygons, this vector is biased toward the longer adjacent edge.

    3. 'forward_edge':
       One-sided outward unit normal of the forward edge (i -> i+1).

    4. 'backward_edge':
       One-sided outward unit normal of the backward edge (i-1 -> i).

    Behavior at Corners, Cusps, and NHEK Joins:
    -------------------------------------------
    At smooth points on the shadow boundary, both 'angle_bisector' and 'central_difference'
    converge to the unique continuous geometric normal as mesh resolution increases.

    At corners (such as the upper and lower NHEK joins where the smooth exterior branch
    meets the vertical NHEK line segment), no classical differentiable normal exists.
    The normal cone (subdifferential) is bounded by the backward and forward edge normals;
    'angle_bisector' returns the central ray bisecting this corner angle.

    At degenerate critical endpoints or sharp cusps where adjacent edges are anti-parallel
    (||u_b + u_f|| < 1e-12), the angle bisector degenerates; the implementation falls
    back to the forward edge normal. Callers must note that this numerical vector does not
    represent a unique classical geometric normal.

    Parameters
    ----------
    curve : KerrShadowCurve
        Kerr shadow boundary curve instance.
    convention : str, optional
        Normal vector convention: 'angle_bisector' (default), 'central_difference',
        'forward_edge', or 'backward_edge'.

    Returns
    -------
    Tuple[np.ndarray, np.ndarray]
        Tuple (n_alpha, n_beta) of unit outward normal vector components at each vertex.
    """
    alpha = curve.alpha
    beta = curve.beta

    if convention == "forward_edge":
        return shadow_edge_normals(curve)

    if convention == "backward_edge":
        nx_fwd, ny_fwd = shadow_edge_normals(curve)
        return (np.roll(nx_fwd, 1), np.roll(ny_fwd, 1))

    if convention == "central_difference":
        t_alpha = np.roll(alpha, -1) - np.roll(alpha, 1)
        t_beta = np.roll(beta, -1) - np.roll(beta, 1)
        norm = np.hypot(t_beta, -t_alpha)
        if np.any(norm < 1e-14):
            t_alpha_fwd = np.roll(alpha, -1) - alpha
            t_beta_fwd = np.roll(beta, -1) - beta
            norm_fwd = np.hypot(t_beta_fwd, -t_alpha_fwd)
            t_beta = np.where(norm < 1e-14, t_beta_fwd, t_beta)
            t_alpha = np.where(norm < 1e-14, t_alpha_fwd, t_alpha)
            norm = np.where(norm < 1e-14, norm_fwd, norm)
        return (
            np.frombuffer((t_beta / norm).tobytes(), dtype=np.float64),
            np.frombuffer((-t_alpha / norm).tobytes(), dtype=np.float64),
        )

    if convention == "angle_bisector":
        # Backward edge (i-1 -> i)
        dx_b = alpha - np.roll(alpha, 1)
        dy_b = beta - np.roll(beta, 1)
        len_b = np.hypot(dx_b, dy_b)
        len_b = np.where(len_b < 1e-14, 1.0, len_b)
        ub_x = dx_b / len_b
        ub_y = dy_b / len_b

        # Forward edge (i -> i+1)
        dx_f = np.roll(alpha, -1) - alpha
        dy_f = np.roll(beta, -1) - beta
        len_f = np.hypot(dx_f, dy_f)
        len_f = np.where(len_f < 1e-14, 1.0, len_f)
        uf_x = dx_f / len_f
        uf_y = dy_f / len_f

        # Outward unit normals for each edge: (dy, -dx)
        nb_x = ub_y
        nb_y = -ub_x
        nf_x = uf_y
        nf_y = -uf_x

        # Exact angle bisector sum
        n_sum_x = nb_x + nf_x
        n_sum_y = nb_y + nf_y
        norm_sum = np.hypot(n_sum_x, n_sum_y)

        # Degenerate case (cusp/anti-parallel edges): fall back to forward edge normal
        deg_mask = norm_sum < 1e-12
        nx = np.where(deg_mask, nf_x, n_sum_x / np.where(deg_mask, 1.0, norm_sum))
        ny = np.where(deg_mask, nf_y, n_sum_y / np.where(deg_mask, 1.0, norm_sum))

        return (
            np.frombuffer(nx.tobytes(), dtype=np.float64),
            np.frombuffer(ny.tobytes(), dtype=np.float64),
        )

    raise ValueError(
        f"Unknown normal convention '{convention}'. "
        f"Supported conventions are: 'angle_bisector', 'central_difference', 'forward_edge', 'backward_edge'."
    )
