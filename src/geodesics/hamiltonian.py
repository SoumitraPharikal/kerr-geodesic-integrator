"""Canonical Hamiltonian formulation for geodesic motion in curved spacetime.

Implements the general canonical equations of motion for test particles (including
photons) in curved spacetimes represented by SpacetimeMetric instances:

    H(x, p) = 1/2 * g^{mu nu}(x) * p_mu * p_nu
    dx^mu / dlambda =  dH / dp_mu = g^{mu nu} * p_nu
    dp_mu / dlambda = -dH / dx^mu = -1/2 * (partial_mu g^{alpha beta}) * p_alpha * p_beta

State vector ordering convention:
    y = (x0, r, theta, phi, p0, pr, ptheta, pphi)
    - y[0:4] = (x0, r, theta, phi): contravariant coordinates with x0 = c*t
    - y[4:8] = (p0, pr, ptheta, pphi): covariant canonical conjugate momenta

Units: Geometrized units G = c = 1.
"""

from typing import Final, Tuple
import numpy as np

from geodesics.constants import IDX_R, IDX_THETA
from geodesics.metrics.base import SpacetimeMetric

STATE_DIMENSION: Final[int] = 8
STATE_NAMES: Final[Tuple[str, ...]] = (
    "x0", "r", "theta", "phi",
    "p0", "pr", "ptheta", "pphi"
)


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
