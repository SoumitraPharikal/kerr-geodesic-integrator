"""Canonical Hamiltonian formulation for geodesic motion in curved spacetime.

Implements the canonical equations of motion for test particles (including photons)
in stationary, axisymmetric spacetimes represented by SpacetimeMetric instances:

    H(x, p) = 1/2 * g^{mu nu}(x) * p_mu * p_nu
    dx^mu / dlambda =  dH / dp_mu = g^{mu nu} * p_nu
    dp_mu / dlambda = -dH / dx^mu = -1/2 * (partial_mu g^{alpha beta}) * p_alpha * p_beta

State vector ordering convention:
    y = (x0, r, theta, phi, p0, pr, ptheta, pphi)
    - y[0:4] = (x0, r, theta, phi): contravariant coordinates with x0 = c*t
    - y[4:8] = (p0, pr, ptheta, pphi): covariant canonical conjugate momenta

Units: Geometrized units G = c = 1.
"""

from typing import Final, Tuple, Union
import numpy as np

from geodesics.constants import (
    IDX_PHI,
    IDX_R,
    IDX_THETA,
    IDX_X0,
)
from geodesics.metrics.base import SpacetimeMetric
from geodesics.metrics.kerr import KerrMetric

STATE_DIMENSION: Final[int] = 8
STATE_NAMES: Final[Tuple[str, ...]] = (
    "x0", "r", "theta", "phi",
    "p0", "pr", "ptheta", "pphi"
)

__all__ = [
    "STATE_DIMENSION",
    "STATE_NAMES",
    "carter_constant",
    "carter_constant_radial",
    "carter_separation_constant",
    "carter_separation_constant_radial",
    "conserved_angular_momentum",
    "conserved_energy",
    "hamiltonian_rhs",
    "hamiltonian_value",
]


def hamiltonian_value(
    x: np.ndarray,
    p: np.ndarray,
    metric: SpacetimeMetric
) -> float:
    """Calculates the canonical Hamiltonian H(x, p) = 1/2 * g^{mu nu}(x) * p_mu * p_nu.

    Parameters
    ----------
    x : np.ndarray
        Coordinate 1D array of shape (4,), ordered (x0, r, theta, phi).
    p : np.ndarray
        Canonical momentum 1D array of shape (4,), ordered (p0, pr, ptheta, pphi).
    metric : SpacetimeMetric
        An instance implementing the SpacetimeMetric abstract interface.

    Returns
    -------
    float
        The scalar Hamiltonian value H(x, p).

    Raises
    ------
    TypeError
        If metric is not an instance of SpacetimeMetric.
    ValueError
        If x or p does not have shape (4,), or contains non-finite values (NaN/Inf).
    """
    if not isinstance(metric, SpacetimeMetric):
        raise TypeError(
            f"metric must be an instance of SpacetimeMetric, got {type(metric).__name__}"
        )

    if not isinstance(x, np.ndarray):
        x = np.asarray(x, dtype=np.float64)
    if x.shape != (4,):
        raise ValueError(f"Coordinate array x must have shape (4,), got {x.shape}")
    if not np.all(np.isfinite(x)):
        raise ValueError("Coordinate array x contains non-finite values (NaN or Inf)")

    if not isinstance(p, np.ndarray):
        p = np.asarray(p, dtype=np.float64)
    if p.shape != (4,):
        raise ValueError(f"Momentum array p must have shape (4,), got {p.shape}")
    if not np.all(np.isfinite(p)):
        raise ValueError("Momentum array p contains non-finite values (NaN or Inf)")

    r = float(x[IDX_R])
    theta = float(x[IDX_THETA])

    g_contra = metric.g_contra(r, theta)
    h_val = 0.5 * np.einsum("ij,i,j->", g_contra, p, p)
    return float(h_val)


def hamiltonian_rhs(
    state: np.ndarray,
    metric: SpacetimeMetric
) -> np.ndarray:
    """Calculates the canonical Hamiltonian right-hand side vector field dy/dlambda.

    Evaluates the 8-component system of first-order differential equations:
        dx^mu / dlambda =  g^{mu nu} * p_nu
        dp_mu / dlambda = -1/2 * (partial_mu g^{alpha beta}) * p_alpha * p_beta

    Parameters
    ----------
    state : np.ndarray
        1D array of shape (8,), ordered (x0, r, theta, phi, p0, pr, ptheta, pphi).
    metric : SpacetimeMetric
        An instance implementing the SpacetimeMetric abstract interface.

    Returns
    -------
    np.ndarray
        1D array of shape (8,) containing dy/dlambda in the exact same ordering.

    Raises
    ------
    TypeError
        If metric is not an instance of SpacetimeMetric.
    ValueError
        If state does not have shape (8,), or contains non-finite values (NaN/Inf).
    """
    if not isinstance(metric, SpacetimeMetric):
        raise TypeError(
            f"metric must be an instance of SpacetimeMetric, got {type(metric).__name__}"
        )

    if not isinstance(state, np.ndarray):
        state = np.asarray(state, dtype=np.float64)
    if state.shape != (8,):
        raise ValueError(f"State array must have shape (8,), got {state.shape}")
    if not np.all(np.isfinite(state)):
        raise ValueError("State array contains non-finite values (NaN or Inf)")

    x = state[:4]
    p = state[4:]

    r = float(x[IDX_R])
    theta = float(x[IDX_THETA])

    g_contra = metric.g_contra(r, theta)
    dg_all = metric.dg_contra_all(r, theta)

    # dx^mu / dlambda = g^{mu nu} * p_nu
    x_dot = np.einsum("ij,j->i", g_contra, p)

    # dp_mu / dlambda = -1/2 * (partial_mu g^{alpha beta}) * p_alpha * p_beta
    p_dot = -0.5 * np.einsum("uab,a,b->u", dg_all, p, p)

    rhs = np.empty(8, dtype=np.float64)
    rhs[:4] = x_dot
    rhs[4:] = p_dot
    return rhs


def conserved_energy(p_or_state: np.ndarray) -> float:
    """Extracts conserved energy E = -p_0 = -p_t from covariant momentum or phase-space state.

    For stationary spacetimes admitting a timelike Killing vector field xi^mu = delta^mu_0,
    the inner product E = -xi^mu p_mu = -p_0 is a rigorous first integral of geodesic motion:
        dp_0 / dlambda = -1/2 * (partial_0 g^{alpha beta}) * p_alpha * p_beta = 0.

    Parameters
    ----------
    p_or_state : np.ndarray
        Either a 4-component canonical covariant momentum array p = (p0, pr, ptheta, pphi)
        or an 8-component phase-space state array y = (x0, r, theta, phi, p0, pr, ptheta, pphi).

    Returns
    -------
    float
        The scalar conserved energy E = -p_0.

    Raises
    ------
    ValueError
        If p_or_state does not have shape (4,) or (8,), or contains non-finite values (NaN/Inf).
    """
    if not isinstance(p_or_state, np.ndarray):
        p_or_state = np.asarray(p_or_state, dtype=np.float64)
    if p_or_state.shape == (8,):
        p0 = float(p_or_state[4])
    elif p_or_state.shape == (4,):
        p0 = float(p_or_state[IDX_X0])
    else:
        raise ValueError(
            f"Input array must have shape (4,) or (8,), got {p_or_state.shape}"
        )
    if not np.isfinite(p0):
        raise ValueError("Momentum p_0 contains non-finite values (NaN or Inf)")
    return -p0


def conserved_angular_momentum(p_or_state: np.ndarray) -> float:
    """Extracts conserved axial angular momentum L_z = p_phi from covariant momentum or phase-space state.

    For axisymmetric spacetimes admitting an axial Killing vector field eta^mu = delta^mu_3,
    the inner product L_z = eta^mu p_mu = p_phi is a rigorous first integral of geodesic motion:
        dp_phi / dlambda = -1/2 * (partial_phi g^{alpha beta}) * p_alpha * p_beta = 0.

    Parameters
    ----------
    p_or_state : np.ndarray
        Either a 4-component canonical covariant momentum array p = (p0, pr, ptheta, pphi)
        or an 8-component phase-space state array y = (x0, r, theta, phi, p0, pr, ptheta, pphi).

    Returns
    -------
    float
        The scalar conserved axial angular momentum L_z = p_phi.

    Raises
    ------
    ValueError
        If p_or_state does not have shape (4,) or (8,), or contains non-finite values (NaN/Inf).
    """
    if not isinstance(p_or_state, np.ndarray):
        p_or_state = np.asarray(p_or_state, dtype=np.float64)
    if p_or_state.shape == (8,):
        pphi = float(p_or_state[7])
    elif p_or_state.shape == (4,):
        pphi = float(p_or_state[IDX_PHI])
    else:
        raise ValueError(
            f"Input array must have shape (4,) or (8,), got {p_or_state.shape}"
        )
    if not np.isfinite(pphi):
        raise ValueError("Momentum p_phi contains non-finite values (NaN or Inf)")
    return pphi


def _validate_carter_state_and_metric(
    state: np.ndarray,
    metric: KerrMetric,
    mu: float,
) -> Tuple[np.ndarray, KerrMetric, float, bool]:
    """Validates inputs for Carter constant and separation constant diagnostics."""
    if not isinstance(metric, KerrMetric):
        raise TypeError(
            f"metric must be an instance of KerrMetric, got {type(metric).__name__}"
        )
    if isinstance(mu, bool) or not np.isfinite(mu) or mu < 0.0:
        raise ValueError(
            f"Rest mass parameter mu must be a non-negative finite float, got {mu}"
        )
    mu_val = float(mu)

    if not isinstance(state, np.ndarray):
        state = np.asarray(state, dtype=np.float64)
    if not np.all(np.isfinite(state)):
        raise ValueError("State array contains non-finite values (NaN or Inf)")

    if state.ndim == 1:
        if state.shape != (8,):
            raise ValueError(f"1D state array must have shape (8,), got {state.shape}")
        return state, metric, mu_val, False
    elif state.ndim == 2:
        if state.shape[1] != 8:
            raise ValueError(f"2D state array must have shape (N, 8), got {state.shape}")
        return state, metric, mu_val, True
    else:
        raise ValueError(
            f"State array must be 1D with shape (8,) or 2D with shape (N, 8), got {state.shape}"
        )


def carter_separation_constant(
    state: np.ndarray,
    metric: KerrMetric,
    mu: float = 0.0,
) -> Union[float, np.ndarray]:
    """Evaluates the polar separation constant K from Kerr geodesic phase-space state(s).

    In Boyer-Lindquist coordinates, the polar separation constant K arises from the
    separability of the Hamilton-Jacobi equation in Kerr spacetime:
        K = p_theta^2 + (L_z / sin(theta) - a * E * sin(theta))^2 + a^2 * mu^2 * cos^2(theta)
    where:
        E = -p_0 = -p_t (conserved specific energy)
        L_z = p_phi (conserved axial angular momentum)
        a = metric.spin (signed spin parameter)
        mu = rest mass parameter (mu = 1.0 for timelike, mu = 0.0 for null geodesics)

    Parameters
    ----------
    state : np.ndarray
        Either a 1D array of shape (8,) representing a single phase-space state
        y = (x0, r, theta, phi, p0, pr, ptheta, pphi), or a 2D array of shape (N, 8)
        representing a sequence of N states along a geodesic trajectory.
    metric : KerrMetric
        An instance of KerrMetric defining the mass M and spin a.
    mu : float, default 0.0
        Rest mass parameter (mu = 1.0 for timelike geodesics, mu = 0.0 for null geodesics).
        Must be a non-negative finite float.

    Returns
    -------
    Union[float, np.ndarray]
        Scalar float if input is a 1D state of shape (8,); 1D numpy array of shape (N,)
        if input is a 2D state array of shape (N, 8).

    Raises
    ------
    TypeError
        If metric is not an instance of KerrMetric.
    ValueError
        If state shape is not (8,) or (N, 8), contains non-finite values (NaN/Inf),
        mu is negative or non-finite, or theta is outside the coordinate domain (0, pi).
    """
    arr, kerr, mu_val, is_2d = _validate_carter_state_and_metric(state, metric, mu)

    theta = arr[..., IDX_THETA]
    if np.any(theta <= 0.0) or np.any(theta >= np.pi):
        raise ValueError(
            "Polar coordinate theta must lie strictly in (0, pi) to avoid coordinate singularities"
        )

    p0 = arr[..., 4]
    ptheta = arr[..., 6]
    pphi = arr[..., 7]

    E = -p0
    Lz = pphi
    a = float(kerr.spin)

    sin_theta = np.sin(theta)
    cos_theta = np.cos(theta)

    term_phi = (Lz / sin_theta) - (a * E * sin_theta)
    k_val = (ptheta ** 2) + (term_phi ** 2) + ((a * mu_val * cos_theta) ** 2)

    if is_2d:
        return np.asarray(k_val, dtype=np.float64)
    return float(k_val)


def carter_constant(
    state: np.ndarray,
    metric: KerrMetric,
    mu: float = 0.0,
) -> Union[float, np.ndarray]:
    """Evaluates the Carter constant Q from Kerr geodesic phase-space state(s).

    In the Kerr Geodesic Integrator project convention, the Carter constant Q is defined
    in terms of the polar separation constant K and conserved axial angular momentum L_z:
        Q = K - (L_z - a * E)^2
    which is algebraically identical to:
        Q = p_theta^2 + cos^2(theta) * [a^2 * (mu^2 - E^2) + L_z^2 / sin^2(theta)]
    For equatorial geodesics (theta = pi/2, p_theta = 0), Q vanishes identically (Q = 0).
    In the Schwarzschild limit (a = 0), Q reduces to the squared transverse angular
    momentum Q = p_theta^2 + L_z^2 * cot^2(theta) = L^2 - L_z^2.

    Parameters
    ----------
    state : np.ndarray
        Either a 1D array of shape (8,) representing a single phase-space state
        y = (x0, r, theta, phi, p0, pr, ptheta, pphi), or a 2D array of shape (N, 8)
        representing a sequence of N states along a geodesic trajectory.
    metric : KerrMetric
        An instance of KerrMetric defining the mass M and spin a.
    mu : float, default 0.0
        Rest mass parameter (mu = 1.0 for timelike geodesics, mu = 0.0 for null geodesics).
        Must be a non-negative finite float.

    Returns
    -------
    Union[float, np.ndarray]
        The Carter constant Q (scalar float or 1D array of length N).

    Raises
    ------
    TypeError
        If metric is not an instance of KerrMetric.
    ValueError
        If state shape is not (8,) or (N, 8), contains non-finite values (NaN/Inf),
        mu is negative or non-finite, or theta is outside the coordinate domain (0, pi).
    """
    arr, kerr, mu_val, is_2d = _validate_carter_state_and_metric(state, metric, mu)

    k_val = carter_separation_constant(arr, kerr, mu=mu_val)

    p0 = arr[..., 4]
    pphi = arr[..., 7]
    E = -p0
    Lz = pphi
    a = float(kerr.spin)

    shift = (Lz - (a * E)) ** 2
    q_val = k_val - shift

    if is_2d:
        return np.asarray(q_val, dtype=np.float64)
    return float(q_val)


def carter_separation_constant_radial(
    state: np.ndarray,
    metric: KerrMetric,
    mu: float = 0.0,
) -> Union[float, np.ndarray]:
    """Evaluates the separation constant K from Kerr geodesic state(s) using the independent radial formula.

    Arising from the separated radial Hamilton-Jacobi equation in Boyer-Lindquist coordinates:
        K_radial = [(r^2 + a^2) * E - a * L_z]^2 / Delta(r) - Delta(r) * p_r^2 - mu^2 * r^2
    where:
        Delta(r) = r^2 - 2*M*r + a^2 = (r - r_+)*(r - r_-)
    This provides a genuinely independent mathematical evaluation of the exact same first integral
    of motion K without referencing the polar angle theta or polar momentum p_theta.

    Parameters
    ----------
    state : np.ndarray
        Either a 1D array of shape (8,) or a 2D array of shape (N, 8).
    metric : KerrMetric
        An instance of KerrMetric defining the mass M and spin a.
    mu : float, default 0.0
        Rest mass parameter (mu = 1.0 for timelike geodesics, mu = 0.0 for null geodesics).
        Must be a non-negative finite float.

    Returns
    -------
    Union[float, np.ndarray]
        Scalar float or 1D array of length N.

    Raises
    ------
    TypeError
        If metric is not an instance of KerrMetric.
    ValueError
        If state shape is not (8,) or (N, 8), contains non-finite values,
        mu is negative or non-finite, or r <= metric.horizon_radius.
    """
    arr, kerr, mu_val, is_2d = _validate_carter_state_and_metric(state, metric, mu)

    r = arr[..., IDX_R]
    r_plus = kerr.horizon_radius
    if np.any(r <= r_plus):
        raise ValueError(
            f"Radial coordinate r must be strictly outside the event horizon r_+ = {r_plus}"
        )

    p0 = arr[..., 4]
    pr = arr[..., 5]
    pphi = arr[..., 7]

    E = -p0
    Lz = pphi
    a = float(kerr.spin)
    r_minus = kerr.inner_horizon_radius

    # Delta = (r - r_+)*(r - r_-)
    delta = (r - r_plus) * (r - r_minus)

    num = ((r ** 2 + a ** 2) * E) - (a * Lz)
    k_rad = ((num ** 2) / delta) - (delta * (pr ** 2)) - ((mu_val * r) ** 2)

    if is_2d:
        return np.asarray(k_rad, dtype=np.float64)
    return float(k_rad)


def carter_constant_radial(
    state: np.ndarray,
    metric: KerrMetric,
    mu: float = 0.0,
) -> Union[float, np.ndarray]:
    """Evaluates Carter constant Q from Kerr geodesic state(s) using the independent radial formula:

        Q_radial = K_radial - (L_z - a * E)^2

    Parameters
    ----------
    state : np.ndarray
        Either a 1D array of shape (8,) or a 2D array of shape (N, 8).
    metric : KerrMetric
        An instance of KerrMetric defining the mass M and spin a.
    mu : float, default 0.0
        Rest mass parameter (mu = 1.0 for timelike geodesics, mu = 0.0 for null geodesics).
        Must be a non-negative finite float.

    Returns
    -------
    Union[float, np.ndarray]
        The Carter constant Q computed from radial components.
    """
    arr, kerr, mu_val, is_2d = _validate_carter_state_and_metric(state, metric, mu)

    k_rad = carter_separation_constant_radial(arr, kerr, mu=mu_val)

    p0 = arr[..., 4]
    pphi = arr[..., 7]
    E = -p0
    Lz = pphi
    a = float(kerr.spin)

    shift = (Lz - (a * E)) ** 2
    q_rad = k_rad - shift

    if is_2d:
        return np.asarray(q_rad, dtype=np.float64)
    return float(q_rad)
