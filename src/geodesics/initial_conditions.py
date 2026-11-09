"""Initial condition generators for null geodesics in Schwarzschild spacetime.

This module provides mathematically rigorous, scale-invariant initial condition
generators for photon trajectories (null geodesics) in exterior Schwarzschild spacetime,
enforcing the exact canonical Hamiltonian constraint H(x, p) = 0.

Mathematical Derivation:
------------------------
For Schwarzschild spacetime in standard coordinates x^mu = (x0, r, theta, phi) with x0 = c*t,
the contravariant metric is:
    g^{mu nu} = diag(-1/f, f, 1/r^2, 1/(r^2 * sin^2(theta)))
where:
    f(r) = 1 - 2M / r > 0  (for r > 2M).

The canonical Hamiltonian is:
    2*H = -p_0^2 / f + f * p_r^2 + p_theta^2 / r^2 + p_phi^2 / (r^2 * sin^2(theta))

Given conserved energy E = -p_0 > 0 and axial angular momentum L_z = p_phi:
    2*H = -E^2 / f + f * p_r^2 + (1 / r^2) * (p_theta^2 + L_z^2 / sin^2(theta)) = 0

Solving for p_r^2:
    p_r^2 = (E^2 - V_eff(r, theta)) / f(r)^2
where the effective potential barrier is:
    V_eff(r, theta) = (f(r) / r^2) * (p_theta^2 + L_z^2 / sin^2(theta)) >= 0

Defining numerator N = E^2 - V_eff(r, theta) and radicand R = N / f^2:
    p_r = s * sqrt(N) / f(r)
where s in {-1, +1} determines the radial branch:
    - s = -1 ("inward"): p_r <= 0, so dr/dlambda = f * p_r <= 0 (decreasing radius)
    - s = +1 ("outward"): p_r >= 0, so dr/dlambda = f * p_r >= 0 (increasing radius)

Scale-Invariant Turning-Point Policy:
-------------------------------------
The canonical momenta of null geodesics are homogeneous under positive affine rescaling
p_mu -> kappa * p_mu (kappa > 0). Consequently, E^2, V_eff, N, and p_r^2 all scale as kappa^2.
To maintain scale invariance, turning points (|N| -> 0) are identified via a relative tolerance
scaled by the characteristic momentum scale of the trajectory:
    scale = E^2 + |V_eff|
    N_tol = radicand_rtol * scale + f^2 * radicand_atol

1. Forbidden barrier (N < -N_tol):
   Classically forbidden region (E^2 < V_eff); raises ValueError. Negative radicands
   are never silently clipped to zero.
2. Numerical turning point (|N| <= N_tol):
   Identified as an instantaneous turning point; returns p_r = 0.0. Clamping avoids
   spurious nonzero velocities sqrt(eps_mach * scale) ~ 1e-8 * E and classifies states
   within |p_r| <= sqrt(N_tol) / f ~ 1e-6 * E / f. The choice radicand_rtol = 1e-12 is
   an engineering choice providing a conservative safety margin (~4500 * eps_mach)
   over IEEE 754 float64 machine precision (eps_mach ~ 2.22e-16).
3. Propagating ray (N > N_tol):
   Evaluates p_r = s * sqrt(N) / f.

Rescaling Scope:
----------------
The turning-point formulation is algebraically scale-invariant under positive affine
rescaling p_mu -> kappa * p_mu (kappa > 0), tested numerically across representable
float64 scales (e.g. 10^-8 to 10^8). Floating-point underflow or overflow may occur
outside that representable range.

State Vector Ordering Convention:
---------------------------------
    y = (x0, r, theta, phi, p0, pr, ptheta, pphi)
    - y[0:4] = (x0, r, theta, phi): contravariant coordinates with x0 = ct
    - y[4:8] = (p0, pr, ptheta, pphi): covariant canonical conjugate momenta

Units: Geometrized units G = c = 1.
"""

from typing import Final, Literal, Optional, Tuple, Union
import numpy as np

from geodesics.constants import (
    IDX_X0,
    IDX_R,
    IDX_THETA,
    IDX_PHI,
)
from geodesics.hamiltonian import STATE_DIMENSION
from geodesics.metrics.kerr import KerrMetric
from geodesics.metrics.schwarzschild import SchwarzschildMetric

DEFAULT_RADICAND_RTOL: Final[float] = 1e-12
DEFAULT_RADICAND_ATOL: Final[float] = 0.0
RadialDirection = Literal["inward", "outward"]


def schwarzschild_null_initial_state(
    metric: Union[SchwarzschildMetric, float],
    x: np.ndarray,
    energy: float,
    Lz: float,
    ptheta: float = 0.0,
    radial_direction: RadialDirection = "inward",
    radicand_rtol: float = DEFAULT_RADICAND_RTOL,
    radicand_atol: float = DEFAULT_RADICAND_ATOL,
) -> np.ndarray:
    """Constructs a validated 8-component canonical initial state for a null geodesic in Schwarzschild spacetime.

    Solves the null constraint H(x, p) = 0 for the radial canonical momentum p_r
    given coordinates x, conserved energy E > 0, angular momentum components (L_z, p_theta),
    and initial radial branch s in {-1, +1}. Employs a scale-invariant turning-point
    criterion to preserve validity under arbitrary positive momentum rescalings.

    Parameters
    ----------
    metric : SchwarzschildMetric or float
        An instance of SchwarzschildMetric, or a positive float mass M.
    x : np.ndarray or sequence of float
        Initial 4-coordinates of shape (4,), ordered (x0, r, theta, phi).
        Must lie strictly outside the event horizon (r > 2M) and off the coordinate
        axes (0 < theta < pi).
    energy : float
        Conserved energy E = -p_0. Must be strictly positive (E > 0) to ensure
        future-directed motion (dx0/dlambda = E/f > 0).
    Lz : float
        Conserved axial angular momentum L_z = p_phi.
    ptheta : float, optional
        Initial polar canonical conjugate momentum p_theta, by default 0.0.
    radial_direction : {"inward", "outward"}, optional
        Initial radial direction branch, by default "inward".
        - "inward": p_r <= 0, corresponding to dr/dlambda <= 0.
        - "outward": p_r >= 0, corresponding to dr/dlambda >= 0.
    radicand_rtol : float, optional
        Dimensionless relative tolerance for scale-aware turning-point detection,
        scaled by (E^2 + |V_eff|). Default is 1e-12, an engineering choice providing
        a safety margin (~4500 * eps_mach) over IEEE 754 float64 machine precision
        (eps_mach ~ 2.22e-16), corresponding to a radial momentum classification
        threshold |p_r| ~ 1e-6 * E / f.
    radicand_atol : float, optional
        Optional absolute tolerance on the radicand p_r^2. Default is 0.0
        to ensure strict scale-invariance under momentum rescaling.

    Returns
    -------
    np.ndarray
        Canonical 8-component state vector y = (x0, r, theta, phi, p0, pr, ptheta, pphi)
        of shape (8,) with dtype float64, satisfying H(x, p) = 0.

    Raises
    ------
    TypeError
        If metric is neither a SchwarzschildMetric instance nor a numeric mass,
        or if radial_direction is not a string.
    ValueError
        If inputs are non-finite, coordinates are outside the physical domain (r <= 2M or
        theta not in (0, pi)), energy is non-positive (E <= 0), radial_direction is
        not in {"inward", "outward"}, or the state is in a classically forbidden
        barrier (E^2 - V_eff < -N_tol).
    """
    # 1. Validate and resolve metric
    if isinstance(metric, (int, float)) and not isinstance(metric, bool):
        metric = SchwarzschildMetric(mass=float(metric))
    elif not isinstance(metric, SchwarzschildMetric):
        raise TypeError(
            f"metric must be an instance of SchwarzschildMetric or a positive float mass, "
            f"got {type(metric).__name__}"
        )

    # 2. Validate coordinates x
    if not isinstance(x, np.ndarray):
        x = np.asarray(x, dtype=np.float64)
    if x.shape != (4,):
        raise ValueError(f"Coordinate array x must have shape (4,), got {x.shape}")
    if not np.all(np.isfinite(x)):
        raise ValueError("Coordinate array x contains non-finite values (NaN or Inf)")

    r = float(x[IDX_R])
    theta = float(x[IDX_THETA])

    # Domain validation using public metric properties and coordinate geometry
    if r <= metric.horizon_radius:
        raise ValueError(
            f"Radial coordinate r must be strictly outside the event horizon "
            f"r_H = 2M = {metric.horizon_radius}, got r = {r}"
        )
    if theta <= 0.0 or theta >= np.pi:
        raise ValueError(
            f"Polar angle theta must be strictly in the domain (0, pi), got theta = {theta}"
        )

    # 3. Validate conserved energy E
    if isinstance(energy, bool) or not np.isfinite(energy) or energy <= 0.0:
        raise ValueError(
            f"Conserved energy E must be strictly positive and finite, got E = {energy}"
        )
    energy = float(energy)

    # 4. Validate angular momentum parameters
    if isinstance(Lz, bool) or not np.isfinite(Lz):
        raise ValueError(f"Axial angular momentum Lz must be finite, got Lz = {Lz}")
    if isinstance(ptheta, bool) or not np.isfinite(ptheta):
        raise ValueError(f"Polar momentum ptheta must be finite, got ptheta = {ptheta}")
    Lz = float(Lz)
    ptheta = float(ptheta)

    # 5. Validate radial direction branch
    if not isinstance(radial_direction, str):
        raise TypeError(
            f"radial_direction must be a string ('inward' or 'outward'), "
            f"got {type(radial_direction).__name__}"
        )
    direction_normalized = radial_direction.strip().lower()
    if direction_normalized == "inward":
        sign = -1.0
    elif direction_normalized == "outward":
        sign = 1.0
    else:
        raise ValueError(
            f"radial_direction must be 'inward' or 'outward', got {radial_direction!r}"
        )

    # 6. Validate tolerances
    if (
        isinstance(radicand_rtol, bool)
        or not np.isfinite(radicand_rtol)
        or radicand_rtol < 0.0
    ):
        raise ValueError(
            f"radicand_rtol must be non-negative and finite, got {radicand_rtol}"
        )
    if (
        isinstance(radicand_atol, bool)
        or not np.isfinite(radicand_atol)
        or radicand_atol < 0.0
    ):
        raise ValueError(
            f"radicand_atol must be non-negative and finite, got {radicand_atol}"
        )
    radicand_rtol = float(radicand_rtol)
    radicand_atol = float(radicand_atol)

    # 7. Evaluate Schwarzschild lapse f(r) and angular momentum square L^2
    f = metric.lapse(r)  # f(r) = 1 - 2M / r > 0
    sin_theta = np.sin(theta)
    l_squared = (ptheta ** 2) + (Lz ** 2) / (sin_theta ** 2)
    v_eff = (f / (r * r)) * l_squared

    # 8. Compute numerator N = E^2 - V_eff and scale = E^2 + |V_eff|
    num = (energy ** 2) - v_eff
    scale = (energy ** 2) + abs(v_eff)

    # Scale-aware tolerance threshold on N:
    num_tol = (radicand_rtol * scale) + (f * f * radicand_atol)

    # 9. Radicand evaluation and turning-point detection
    # If N is physically negative beyond the scale-aware roundoff tolerance,
    # the requested state is in the classically forbidden barrier (E^2 < V_eff).
    if num < -num_tol:
        radicand = num / (f * f)
        raise ValueError(
            f"Initial conditions are physically forbidden for a null geodesic: "
            f"radicand p_r^2 = {radicand:.8e} < 0. "
            f"Conserved energy E = {energy:.6e} (E^2 = {energy**2:.6e}) is insufficient "
            f"to overcome the effective potential barrier V_eff = {v_eff:.6f} at "
            f"r = {r:.4f}, theta = {theta:.4f}."
        )

    # At or within scale-aware tolerance of a turning point (|N| <= num_tol),
    # the radial momentum is identically zero. Clamping avoids spurious velocities
    # and sets pr = 0 for states with |pr| <= sqrt(num_tol) / f ~ 1e-6 * E / f.
    if abs(num) <= num_tol:
        pr = 0.0
    else:
        pr = sign * (np.sqrt(num) / f)

    # 10. Assemble canonical state vector
    state = np.empty(STATE_DIMENSION, dtype=np.float64)
    state[0:4] = x
    state[4] = -energy
    state[5] = pr
    state[6] = ptheta
    state[7] = Lz

    return state


# Convenient alias
null_geodesic_initial_state = schwarzschild_null_initial_state


def kerr_geodesic_initial_state(
    metric: KerrMetric,
    x: np.ndarray,
    energy: float,
    Lz: float,
    ptheta: float = 0.0,
    mu: float = 0.0,
    radial_direction: RadialDirection = "inward",
    radicand_rtol: float = DEFAULT_RADICAND_RTOL,
    radicand_atol: float = DEFAULT_RADICAND_ATOL,
) -> np.ndarray:
    """Constructs a validated 8-component canonical initial state for a geodesic in Kerr spacetime.

    Solves the general canonical Hamiltonian constraint:
        H(x, p) = 1/2 * g^{mu nu}(x) * p_mu * p_nu = -1/2 * mu^2
    for the radial canonical conjugate momentum p_r in Boyer-Lindquist coordinates,
    given spacetime coordinates x, conserved energy E = -p_0 > 0, axial angular momentum
    L_z = p_phi, polar momentum p_theta, rest mass parameter mu (0.0 for null, 1.0 for timelike),
    and radial direction branch.

    Parameters
    ----------
    metric : KerrMetric
        An instance of KerrMetric with mass M > 0 and spin |a| <= M.
    x : np.ndarray or sequence of float
        Initial 4-coordinates of shape (4,), ordered (x0, r, theta, phi).
        Must lie strictly outside the outer event horizon (r > r_+) and off the coordinate
        axes (0 < theta < pi).
    energy : float
        Conserved energy E = -p_0. Must be strictly positive (E > 0).
    Lz : float
        Conserved axial angular momentum L_z = p_phi.
    ptheta : float, optional
        Initial polar canonical conjugate momentum p_theta, by default 0.0.
    mu : float, optional
        Rest mass parameter: mu = 0.0 for null geodesics (H = 0), mu = 1.0 for timelike
        geodesics (H = -0.5). Must be non-negative and finite. Default is 0.0.
    radial_direction : {"inward", "outward"}, optional
        Initial radial direction branch, by default "inward".
        - "inward": p_r <= 0, corresponding to dr/dlambda <= 0.
        - "outward": p_r >= 0, corresponding to dr/dlambda >= 0.
    radicand_rtol : float, optional
        Dimensionless relative tolerance for scale-aware turning-point detection. Default 1e-12.
    radicand_atol : float, optional
        Absolute tolerance on the radicand. Default 0.0.

    Returns
    -------
    np.ndarray
        Canonical 8-component state vector y = (x0, r, theta, phi, p0, pr, ptheta, pphi)
        of shape (8,) with dtype float64, satisfying H(x, p) = -1/2 * mu^2.

    Raises
    ------
    TypeError
        If metric is not a KerrMetric instance or radial_direction is not a string.
    ValueError
        If inputs are non-finite, coordinates are outside physical domain (r <= r_+ or
        theta not in (0, pi)), energy is non-positive (E <= 0), mu is negative,
        radial_direction is invalid, or the state is in a classically forbidden barrier.
    """
    # 1. Validate metric
    if not isinstance(metric, KerrMetric):
        raise TypeError(
            f"metric must be an instance of KerrMetric, got {type(metric).__name__}"
        )

    # 2. Validate coordinates x
    if not isinstance(x, np.ndarray):
        x = np.asarray(x, dtype=np.float64)
    if x.shape != (4,):
        raise ValueError(f"Coordinate array x must have shape (4,), got {x.shape}")
    if not np.all(np.isfinite(x)):
        raise ValueError("Coordinate array x contains non-finite values (NaN or Inf)")

    r = float(x[IDX_R])
    theta = float(x[IDX_THETA])

    if r <= metric.horizon_radius:
        raise ValueError(
            f"Radial coordinate r must be strictly outside the event horizon "
            f"r_+ = {metric.horizon_radius}, got r = {r}"
        )
    if theta <= 0.0 or theta >= np.pi:
        raise ValueError(
            f"Polar angle theta must be strictly in the domain (0, pi), got theta = {theta}"
        )

    # 3. Validate conserved energy E
    if isinstance(energy, bool) or not np.isfinite(energy) or energy <= 0.0:
        raise ValueError(
            f"Conserved energy E must be strictly positive and finite, got E = {energy}"
        )
    energy = float(energy)

    # 4. Validate angular momentum parameters
    if isinstance(Lz, bool) or not np.isfinite(Lz):
        raise ValueError(f"Axial angular momentum Lz must be finite, got Lz = {Lz}")
    if isinstance(ptheta, bool) or not np.isfinite(ptheta):
        raise ValueError(f"Polar momentum ptheta must be finite, got ptheta = {ptheta}")
    Lz = float(Lz)
    ptheta = float(ptheta)

    # 5. Validate rest mass parameter mu
    if isinstance(mu, bool) or not np.isfinite(mu) or mu < 0.0:
        raise ValueError(f"Rest mass parameter mu must be non-negative and finite, got {mu}")
    mu = float(mu)

    # 6. Validate radial direction branch
    if not isinstance(radial_direction, str):
        raise TypeError(
            f"radial_direction must be a string ('inward' or 'outward'), "
            f"got {type(radial_direction).__name__}"
        )
    direction_normalized = radial_direction.strip().lower()
    if direction_normalized == "inward":
        sign = -1.0
    elif direction_normalized == "outward":
        sign = 1.0
    else:
        raise ValueError(
            f"radial_direction must be 'inward' or 'outward', got {radial_direction!r}"
        )

    # 7. Validate tolerances
    if (
        isinstance(radicand_rtol, bool)
        or not np.isfinite(radicand_rtol)
        or radicand_rtol < 0.0
    ):
        raise ValueError(
            f"radicand_rtol must be non-negative and finite, got {radicand_rtol}"
        )
    if (
        isinstance(radicand_atol, bool)
        or not np.isfinite(radicand_atol)
        or radicand_atol < 0.0
    ):
        raise ValueError(
            f"radicand_atol must be non-negative and finite, got {radicand_atol}"
        )
    radicand_rtol = float(radicand_rtol)
    radicand_atol = float(radicand_atol)

    # 8. Evaluate inverse metric components
    g_inv = metric.g_contra(r, theta)
    g_rr = float(g_inv[IDX_R, IDX_R])  # Delta / Sigma > 0 for r > r_+
    pt = -energy
    pphi = Lz

    # Canonical kinetic/potential contraction of non-radial momentum components:
    # 2*H = g^{rr} p_r^2 + V = -mu^2
    V = (
        float(g_inv[IDX_X0, IDX_X0]) * (pt ** 2)
        + 2.0 * float(g_inv[IDX_X0, IDX_PHI]) * pt * pphi
        + float(g_inv[IDX_PHI, IDX_PHI]) * (pphi ** 2)
        + float(g_inv[IDX_THETA, IDX_THETA]) * (ptheta ** 2)
    )

    num = -(mu ** 2) - V
    scale = (mu ** 2) + (energy ** 2) + abs(V)
    num_tol = (radicand_rtol * scale) + (g_rr * radicand_atol)

    # 9. Radicand evaluation and turning-point detection
    if num < -num_tol:
        radicand = num / g_rr
        raise ValueError(
            f"Initial conditions are physically forbidden for geodesic (mu={mu}): "
            f"radicand p_r^2 = {radicand:.8e} < 0. "
            f"Conserved energy E = {energy:.6e} is insufficient to overcome "
            f"effective potential barrier V = {V:.6f} at r = {r:.4f}, theta = {theta:.4f}."
        )

    if abs(num) <= num_tol:
        pr = 0.0
    else:
        pr = sign * np.sqrt(num / g_rr)

    # 10. Assemble canonical state vector
    state = np.empty(STATE_DIMENSION, dtype=np.float64)
    state[0:4] = x
    state[4] = pt
    state[5] = pr
    state[6] = ptheta
    state[7] = pphi

    return state


# =============================================================================
# Schwarzschild Physical Circular Orbit Generators (Stage 3A)
# =============================================================================


def schwarzschild_circular_timelike_energy(r: float, mass: float = 1.0) -> float:
    """Calculates the specific conserved energy E_c for an equatorial circular timelike orbit.

    The analytical expression derived from effective potential extremization V_eff'(r) = 0 is:
        E_c = (1 - 2M / r) / sqrt(1 - 3M / r)

    Parameters
    ----------
    r : float
        Orbital coordinate radius. Must satisfy r > 3M.
    mass : float, optional
        Schwarzschild black hole mass M > 0. Default is 1.0.

    Returns
    -------
    float
        Specific conserved energy E_c = -p_t.

    Raises
    ------
    ValueError
        If mass <= 0 or r <= 3M.
    """
    if not np.isfinite(mass) or mass <= 0.0:
        raise ValueError(f"Mass M must be positive and finite, got M = {mass}")
    if not np.isfinite(r):
        raise ValueError(f"Orbital radius r must be finite, got r = {r}")
    if r <= 3.0 * mass:
        raise ValueError(
            f"Timelike circular orbits exist only for r > 3M = {3.0 * mass}, got r = {r}"
        )
    return float((1.0 - 2.0 * mass / r) / np.sqrt(1.0 - 3.0 * mass / r))


def schwarzschild_circular_timelike_angular_momentum(
    r: float, mass: float = 1.0, prograde: bool = True
) -> float:
    """Calculates the specific axial angular momentum L_c for an equatorial circular timelike orbit.

    The analytical expression derived from effective potential extremization V_eff'(r) = 0 is:
        L_c = +/- sqrt(M * r) / sqrt(1 - 3M / r)

    Parameters
    ----------
    r : float
        Orbital coordinate radius. Must satisfy r > 3M.
    mass : float, optional
        Schwarzschild black hole mass M > 0. Default is 1.0.
    prograde : bool, optional
        Whether orbital angular momentum is aligned (+, prograde) or anti-aligned (-, retrograde).
        Default is True.

    Returns
    -------
    float
        Specific conserved angular momentum L_c = p_phi.

    Raises
    ------
    ValueError
        If mass <= 0 or r <= 3M.
    """
    if not np.isfinite(mass) or mass <= 0.0:
        raise ValueError(f"Mass M must be positive and finite, got M = {mass}")
    if not np.isfinite(r):
        raise ValueError(f"Orbital radius r must be finite, got r = {r}")
    if r <= 3.0 * mass:
        raise ValueError(
            f"Timelike circular orbits exist only for r > 3M = {3.0 * mass}, got r = {r}"
        )
    sign = 1.0 if prograde else -1.0
    return float(sign * np.sqrt(mass * r) / np.sqrt(1.0 - 3.0 * mass / r))


def schwarzschild_circular_orbital_frequency(r: float, mass: float = 1.0) -> float:
    """Calculates the coordinate-time orbital angular frequency Omega_phi = dphi / dt.

    In Schwarzschild coordinates, all equatorial circular geodesics satisfy Kepler's third law:
        Omega_phi = sqrt(M / r^3)

    Parameters
    ----------
    r : float
        Orbital coordinate radius r > 0.
    mass : float, optional
        Schwarzschild black hole mass M > 0. Default is 1.0.

    Returns
    -------
    float
        Orbital frequency Omega_phi = dphi / dt in rad / (geometrized time).

    Raises
    ------
    ValueError
        If mass <= 0 or r <= 0.
    """
    if not np.isfinite(mass) or mass <= 0.0:
        raise ValueError(f"Mass M must be positive and finite, got M = {mass}")
    if not np.isfinite(r) or r <= 0.0:
        raise ValueError(f"Orbital radius r must be positive and finite, got r = {r}")
    return float(np.sqrt(mass / (r ** 3)))


def schwarzschild_circular_timelike_initial_state(
    metric: Union[SchwarzschildMetric, float],
    r: float,
    phi: float = 0.0,
    prograde: bool = True,
) -> np.ndarray:
    """Constructs a canonical 8-component initial state for an equatorial circular timelike orbit.

    The state is constructed in the equatorial plane (theta = pi/2, p_r = 0, p_theta = 0) with
    conserved energy E_c and axial angular momentum L_c satisfying the exact circular condition
    and mass-shell invariant H = -1/2 * mu^2 = -0.5:
        y = (t=0, r, theta=pi/2, phi, p_t=-E_c, p_r=0, p_theta=0, p_phi=L_c)

    Parameters
    ----------
    metric : SchwarzschildMetric or float
        An instance of SchwarzschildMetric or a positive float mass M.
    r : float
        Orbital coordinate radius. Must satisfy r > 3M.
    phi : float, optional
        Initial azimuthal angle phi, by default 0.0.
    prograde : bool, optional
        Whether orbital motion is in the +phi direction, by default True.

    Returns
    -------
    np.ndarray
        Canonical 8-component state vector of shape (8,) and dtype float64.

    Raises
    ------
    TypeError
        If metric is neither a SchwarzschildMetric instance nor a numeric mass.
    ValueError
        If r <= 3M or inputs are non-finite.
    """
    if isinstance(metric, (int, float)) and not isinstance(metric, bool):
        metric = SchwarzschildMetric(mass=float(metric))
    elif not isinstance(metric, SchwarzschildMetric):
        raise TypeError(
            f"metric must be an instance of SchwarzschildMetric or positive float mass, "
            f"got {type(metric).__name__}"
        )

    if not np.isfinite(r):
        raise ValueError(f"Orbital radius r must be finite, got r = {r}")
    if r <= 3.0 * metric.mass:
        raise ValueError(
            f"Equatorial timelike circular orbits require r > 3M = {3.0 * metric.mass}, got r = {r}"
        )
    if not np.isfinite(phi):
        raise ValueError(f"Initial azimuth phi must be finite, got phi = {phi}")

    energy = schwarzschild_circular_timelike_energy(r, metric.mass)
    lz = schwarzschild_circular_timelike_angular_momentum(r, metric.mass, prograde=prograde)

    state = np.zeros(STATE_DIMENSION, dtype=np.float64)
    state[IDX_X0] = 0.0
    state[IDX_R] = float(r)
    state[IDX_THETA] = 0.5 * np.pi
    state[IDX_PHI] = float(phi)
    state[4] = -energy
    state[5] = 0.0
    state[6] = 0.0
    state[7] = lz

    return state


def schwarzschild_photon_sphere_initial_state(
    metric: Union[SchwarzschildMetric, float],
    energy: float = 1.0,
    phi: float = 0.0,
    prograde: bool = True,
) -> np.ndarray:
    """Constructs a canonical 8-component initial state for the null circular orbit at the photon sphere (r = 3M).

    The photon sphere orbit satisfies:
        r = 3M
        theta = pi/2
        p_r = 0, p_theta = 0
        p_t = -E
        p_phi = +/- 3*sqrt(3)*M*E
    satisfying the exact null Hamiltonian constraint H = 0.

    Parameters
    ----------
    metric : SchwarzschildMetric or float
        An instance of SchwarzschildMetric or a positive float mass M.
    energy : float, optional
        Conserved energy E > 0 of the photon, by default 1.0.
    phi : float, optional
        Initial azimuthal angle phi, by default 0.0.
    prograde : bool, optional
        Whether orbital motion is in the +phi direction, by default True.

    Returns
    -------
    np.ndarray
        Canonical 8-component state vector of shape (8,) and dtype float64.

    Raises
    ------
    TypeError
        If metric is neither a SchwarzschildMetric instance nor a numeric mass.
    ValueError
        If energy <= 0 or inputs are non-finite.
    """
    if isinstance(metric, (int, float)) and not isinstance(metric, bool):
        metric = SchwarzschildMetric(mass=float(metric))
    elif not isinstance(metric, SchwarzschildMetric):
        raise TypeError(
            f"metric must be an instance of SchwarzschildMetric or positive float mass, "
            f"got {type(metric).__name__}"
        )

    if isinstance(energy, bool) or not np.isfinite(energy) or energy <= 0.0:
        raise ValueError(f"Photon energy E must be strictly positive and finite, got E = {energy}")
    if not np.isfinite(phi):
        raise ValueError(f"Initial azimuth phi must be finite, got phi = {phi}")

    mass = metric.mass
    r_ph = 3.0 * mass
    sign = 1.0 if prograde else -1.0
    lz = sign * 3.0 * np.sqrt(3.0) * mass * energy

    state = np.zeros(STATE_DIMENSION, dtype=np.float64)
    state[IDX_X0] = 0.0
    state[IDX_R] = r_ph
    state[IDX_THETA] = 0.5 * np.pi
    state[IDX_PHI] = float(phi)
    state[4] = -float(energy)
    state[5] = 0.0
    state[6] = 0.0
    state[7] = lz

    return state


def schwarzschild_perturbed_circular_timelike_initial_state(
    metric: Union[SchwarzschildMetric, float],
    r: float,
    delta_pr: float,
    phi: float = 0.0,
    prograde: bool = True,
) -> np.ndarray:
    """Constructs a radially perturbed circular timelike initial state preserving the mass-shell constraint.

    To perturb the circular orbit at radius r while preserving the exact timelike mass-shell invariant
    2*H = -f(r)^(-1) E^2 + f(r) p_r^2 + L_c^2 / r^2 = -1 (where mu = 1), a nonzero radial momentum
    p_r = delta_pr is introduced and the conserved energy is recomputed as:
        E_pert = sqrt( E_c^2 + f(r)^2 * delta_pr^2 )
    where f(r) = 1 - 2M/r and E_c = (1 - 2M/r) / sqrt(1 - 3M/r).

    This ensures H(y0) = -0.5 to machine precision without violating phase space or metric constraints.

    Parameters
    ----------
    metric : SchwarzschildMetric or float
        An instance of SchwarzschildMetric or a positive float mass M.
    r : float
        Orbital coordinate radius. Must satisfy r > 3M.
    delta_pr : float
        Initial radial momentum perturbation delta_pr.
        - delta_pr > 0: outward perturbation (increasing radius initially).
        - delta_pr < 0: inward perturbation (decreasing radius initially).
    phi : float, optional
        Initial azimuthal angle phi, by default 0.0.
    prograde : bool, optional
        Whether orbital motion is in the +phi direction, by default True.

    Returns
    -------
    np.ndarray
        Canonical 8-component state vector of shape (8,) and dtype float64.

    Raises
    ------
    TypeError
        If metric is neither a SchwarzschildMetric instance nor a numeric mass.
    ValueError
        If r <= 3M or inputs are non-finite.
    """
    if isinstance(metric, (int, float)) and not isinstance(metric, bool):
        metric = SchwarzschildMetric(mass=float(metric))
    elif not isinstance(metric, SchwarzschildMetric):
        raise TypeError(
            f"metric must be an instance of SchwarzschildMetric or positive float mass, "
            f"got {type(metric).__name__}"
        )

    if not np.isfinite(r):
        raise ValueError(f"Orbital radius r must be finite, got r = {r}")
    if r <= 3.0 * metric.mass:
        raise ValueError(
            f"Equatorial timelike circular orbits require r > 3M = {3.0 * metric.mass}, got r = {r}"
        )
    if not np.isfinite(delta_pr):
        raise ValueError(f"Radial perturbation delta_pr must be finite, got delta_pr = {delta_pr}")
    if not np.isfinite(phi):
        raise ValueError(f"Initial azimuth phi must be finite, got phi = {phi}")

    energy_circ = schwarzschild_circular_timelike_energy(r, metric.mass)
    lz = schwarzschild_circular_timelike_angular_momentum(r, metric.mass, prograde=prograde)

    f = 1.0 - (2.0 * metric.mass / r)
    energy_pert = float(np.sqrt(energy_circ ** 2 + (f * delta_pr) ** 2))

    state = np.zeros(STATE_DIMENSION, dtype=np.float64)
    state[IDX_X0] = 0.0
    state[IDX_R] = float(r)
    state[IDX_THETA] = 0.5 * np.pi
    state[IDX_PHI] = float(phi)
    state[4] = -energy_pert
    state[5] = float(delta_pr)
    state[6] = 0.0
    state[7] = lz

    return state


# =============================================================================
# Kerr Equatorial Circular Timelike Orbit Initial Conditions (Stage 3B)
# =============================================================================


def _resolve_kerr_parameters(
    metric: Union[KerrMetric, float],
    spin: Optional[float] = None,
    prograde: bool = True,
    s: Optional[int] = None,
    orientation: Optional[str] = None,
    allow_extremal: bool = False,
) -> Tuple[float, float, int]:
    """Resolves mass, signed Kerr spin a, and orbital direction parameter s in {-1, +1}.

    Parameters
    ----------
    metric : KerrMetric or float
        An instance of KerrMetric or a positive float mass M.
    spin : float, optional
        Signed spin parameter a = J/M when metric is passed as a float mass.
        If metric is a KerrMetric instance, spin must either be None or match metric.spin.
    prograde : bool, optional
        Whether orbital motion is prograde relative to the spin direction (sa > 0).
        Ignored if coordinate direction s is explicitly provided. Default is True.
    s : {-1, 1}, optional
        Coordinate azimuthal direction parameter (s = +1 for dphi/dt > 0, s = -1 for dphi/dt < 0).
        If provided, takes precedence over the prograde flag.
    orientation : {'prograde', 'retrograde'}, optional
        Alternative string orientation specification. If provided, sets prograde flag.
    allow_extremal : bool, optional
        Whether to permit exact extremal spin |a| == M, by default False.

    Returns
    -------
    Tuple[float, float, int]
        Tuple (mass, spin, s_val) where s_val in {-1, +1}.

    Raises
    ------
    TypeError
        If metric is not a KerrMetric or numeric mass, or prograde is not a bool.
    ValueError
        If mass <= 0, |a| > M, |a| >= M (when allow_extremal=False), or s not in {-1, 1}.
    """
    if orientation is not None:
        if not isinstance(orientation, str):
            raise TypeError(f"orientation must be a string, got {type(orientation).__name__}")
        orient_clean = orientation.strip().lower()
        if orient_clean in ("prograde", "co-rotating", "corotating", "+", "+1"):
            prograde = True
        elif orient_clean in ("retrograde", "counter-rotating", "counterrotating", "-", "-1"):
            prograde = False
        else:
            raise ValueError(
                f"orientation must be 'prograde' or 'retrograde', got {orientation!r}"
            )

    if isinstance(metric, KerrMetric):
        mass = metric.mass
        a = metric.spin
        if spin is not None and not np.isclose(float(spin), a, atol=1e-14):
            raise ValueError(f"Conflicting spin parameter provided: metric.spin={a} vs spin={spin}")
    elif isinstance(metric, (int, float)) and not isinstance(metric, bool):
        mass = float(metric)
        if not np.isfinite(mass) or mass <= 0.0:
            raise ValueError(f"Black hole mass M must be positive and finite, got M = {mass}")
        if spin is None:
            a = 0.0
        else:
            if not np.isfinite(spin):
                raise ValueError(f"Black hole spin a must be finite, got a = {spin}")
            a = float(spin)
    else:
        raise TypeError(
            f"metric must be an instance of KerrMetric or positive float mass, got {type(metric).__name__}"
        )

    if allow_extremal:
        if abs(a) > mass:
            raise ValueError(
                f"Super-extremal spin |a| = {abs(a)} > M = {mass} is not a valid black hole "
                f"(naked singularity rejected)."
            )
    else:
        if abs(a) >= mass:
            raise ValueError(
                f"Equatorial circular orbit formulas require sub-extremal Kerr metric (|a| < M), "
                f"got a = {a}, M = {mass}"
            )

    if s is not None:
        if s not in (-1, 1):
            raise ValueError(f"Orbital direction parameter s must be +1 or -1, got {s}")
        s_val = int(s)
    else:
        if not isinstance(prograde, bool):
            raise TypeError(f"prograde must be a boolean, got {type(prograde).__name__}")
        if a >= 0.0:
            s_val = 1 if prograde else -1
        else:
            s_val = -1 if prograde else 1

    return mass, a, s_val


def kerr_equatorial_photon_orbit_radius(
    metric: Union[KerrMetric, float],
    spin: Optional[float] = None,
    prograde: bool = True,
    s: Optional[int] = None,
    orientation: Optional[str] = None,
    allow_extremal: bool = False,
) -> float:
    """Calculates the coordinate radius of the equatorial circular photon orbit r_ph.

    The equatorial circular photon orbit satisfies:
        r_ph = 2M * [1 + cos( 2/3 * arccos(-s*a / M) )]
    where s*a > 0 for prograde and s*a < 0 for retrograde.

    Parameters
    ----------
    metric : KerrMetric or float
        An instance of KerrMetric or a positive float mass M.
    spin : float, optional
        Signed spin parameter a when metric is a float mass.
    prograde : bool, optional
        Whether orbital motion is prograde relative to spin. Default is True.
    s : {-1, 1}, optional
        Coordinate azimuthal direction parameter.
    orientation : {'prograde', 'retrograde'}, optional
        Alternative string orientation specification.
    allow_extremal : bool, optional
        Whether to permit exact extremal spin |a| == M, by default False.

    Returns
    -------
    float
        Equatorial photon orbit radius in Boyer-Lindquist coordinates.
    """
    mass, a, s_val = _resolve_kerr_parameters(
        metric, spin, prograde=prograde, s=s, orientation=orientation, allow_extremal=allow_extremal
    )
    chi = abs(a) / mass
    if chi == 0.0:
        return 3.0 * mass
    is_pro = (s_val * a > 0.0) if s is not None else (orientation.lower() == "prograde" if orientation is not None else prograde)
    if chi == 1.0:
        return float(mass if is_pro else 4.0 * mass)
    sign = 1.0 if is_pro else -1.0
    cos_arg = max(-1.0, min(1.0, -sign * chi))
    return float(2.0 * mass * (1.0 + np.cos((2.0 / 3.0) * np.arccos(cos_arg))))


def kerr_equatorial_photon_impact_parameter(
    metric: Union[KerrMetric, float],
    spin: Optional[float] = None,
    prograde: bool = True,
    s: Optional[int] = None,
    orientation: Optional[str] = None,
    allow_extremal: bool = False,
) -> float:
    """Calculates the critical signed impact parameter b_ph = L_z / E for equatorial circular photon orbits.

    Evaluates:
        b_ph = [ 2 * s * r_ph * sqrt(M * r_ph) - a * (r_ph + M) ] / (r_ph - M)
    which is cancellation-free across all subextremal spins, reduces to s * 3 * sqrt(3) * M
    in the Schwarzschild limit (a -> 0), and approaches the exact limits b_ph = 2*a (prograde)
    and b_ph = -7*a (retrograde) in the exact extremal limit (|a| = M).

    Parameters
    ----------
    metric : KerrMetric or float
        An instance of KerrMetric or a positive float mass M.
    spin : float, optional
        Signed spin parameter a when metric is a float mass.
    prograde : bool, optional
        Whether orbital motion is prograde relative to spin. Default is True.
    s : {-1, 1}, optional
        Coordinate azimuthal direction parameter.
    orientation : {'prograde', 'retrograde'}, optional
        Alternative string orientation specification.
    allow_extremal : bool, optional
        Whether to permit exact extremal spin |a| == M, by default False.

    Returns
    -------
    float
        Signed critical impact parameter b_ph in geometrized units of M.
    """
    mass, a, s_val = _resolve_kerr_parameters(
        metric, spin, prograde=prograde, s=s, orientation=orientation, allow_extremal=allow_extremal
    )
    is_pro = (s_val * a > 0.0) if s is not None else (orientation.lower() == "prograde" if orientation is not None else prograde)
    if isinstance(metric, KerrMetric):
        return metric.photon_orbit_impact_parameter(prograde=is_pro)
    return KerrMetric(mass=mass, spin=a).photon_orbit_impact_parameter(prograde=is_pro)


def kerr_equatorial_photon_orbit_frequency(
    metric: Union[KerrMetric, float],
    spin: Optional[float] = None,
    prograde: bool = True,
    s: Optional[int] = None,
    orientation: Optional[str] = None,
) -> float:
    """Calculates the coordinate angular frequency Omega_ph = dphi / dt for equatorial circular photon orbits.

    Evaluates:
        Omega_ph = s * sqrt(M) / (r_ph^(3/2) + s * a * sqrt(M))
    which reduces to s / (3 * sqrt(3) * M) in the Schwarzschild limit (a -> 0).

    Parameters
    ----------
    metric : KerrMetric or float
        An instance of KerrMetric or a positive float mass M.
    spin : float, optional
        Signed spin parameter a when metric is a float mass.
    prograde : bool, optional
        Whether orbital motion is prograde relative to spin. Default is True.
    s : {-1, 1}, optional
        Coordinate azimuthal direction parameter.
    orientation : {'prograde', 'retrograde'}, optional
        Alternative string orientation specification.

    Returns
    -------
    float
        Signed orbital frequency Omega_ph in rad / (geometrized time).
    """
    mass, a, s_val = _resolve_kerr_parameters(
        metric, spin, prograde=prograde, s=s, orientation=orientation, allow_extremal=True
    )
    is_pro = (s_val * a > 0.0) if s is not None else (orientation.lower() == "prograde" if orientation is not None else prograde)
    if isinstance(metric, KerrMetric):
        return metric.photon_orbit_frequency(prograde=is_pro)
    return KerrMetric(mass=mass, spin=a).photon_orbit_frequency(prograde=is_pro)


def kerr_equatorial_photon_orbit_initial_state(
    metric: Union[KerrMetric, float],
    energy: float = 1.0,
    spin: Optional[float] = None,
    prograde: bool = True,
    s: Optional[int] = None,
    orientation: Optional[str] = None,
    t0: float = 0.0,
    phi0: float = 0.0,
    allow_extremal: bool = False,
) -> np.ndarray:
    """Constructs a valid 8-component canonical initial state for an equatorial circular null geodesic in Kerr spacetime.

    The constructed state vector has ordering (x0, r, theta, phi, p0, pr, ptheta, pphi) and satisfies:
        x0 = t0
        r = r_ph
        theta = pi / 2
        phi = phi0
        p0 = -energy (E > 0)
        pr = 0.0
        ptheta = 0.0
        pphi = b_ph * energy
    ensuring exact null Hamiltonian constraint H = 0 to machine precision.

    Parameters
    ----------
    metric : KerrMetric or float
        An instance of KerrMetric or a positive float mass M.
    energy : float, optional
        Conserved photon energy E = -p_0. Must be strictly positive and finite.
        Default is 1.0.
    spin : float, optional
        Signed spin parameter a when metric is a float mass.
    prograde : bool, optional
        Whether orbital motion is prograde relative to spin. Default is True.
    s : {-1, 1}, optional
        Coordinate azimuthal direction parameter.
    orientation : {'prograde', 'retrograde'}, optional
        Alternative string orientation specification.
    t0 : float, optional
        Initial coordinate time t0. Default is 0.0.
    phi0 : float, optional
        Initial azimuthal angle phi0. Default is 0.0.
    allow_extremal : bool, optional
        Whether to permit exact extremal spin |a| == M for regular retrograde orbits, by default False.

    Returns
    -------
    np.ndarray
        Canonical 8-component state vector of shape (8,) and dtype float64.

    Raises
    ------
    ValueError
        If energy <= 0 or non-finite, if t0, phi0 are non-finite, or if an extremal prograde orbit
        (r_ph = r_+ = M) is requested on the horizon coordinate singularity.
    """
    if not np.isfinite(energy) or energy <= 0.0:
        raise ValueError(f"Photon energy E must be positive and finite, got energy = {energy}")
    if not np.isfinite(t0):
        raise ValueError(f"Initial time t0 must be finite, got t0 = {t0}")
    if not np.isfinite(phi0):
        raise ValueError(f"Initial azimuth phi0 must be finite, got phi0 = {phi0}")

    mass, a, s_val = _resolve_kerr_parameters(
        metric, spin, prograde=prograde, s=s, orientation=orientation, allow_extremal=allow_extremal
    )
    is_pro = (s_val * a > 0.0) if s is not None else (orientation.lower() == "prograde" if orientation is not None else prograde)
    if abs(a) == mass and is_pro:
        raise ValueError(
            f"Prograde circular photon orbit coincides with outer event horizon (r_ph = r_+ = {mass}) "
            f"for extremal Kerr metric (|a| = M = {mass}); cannot initialize a regular circular orbit state "
            f"on a coordinate horizon in Boyer-Lindquist coordinates."
        )

    if isinstance(metric, KerrMetric):
        kerr = metric
    else:
        kerr = KerrMetric(mass=mass, spin=a)

    r_ph = kerr.photon_orbit_radius(prograde=is_pro)
    b_ph = kerr.photon_orbit_impact_parameter(prograde=is_pro)

    state = np.zeros(STATE_DIMENSION, dtype=np.float64)
    state[IDX_X0] = float(t0)
    state[IDX_R] = float(r_ph)
    state[IDX_THETA] = 0.5 * np.pi
    state[IDX_PHI] = float(phi0)
    state[4] = -float(energy)
    state[5] = 0.0
    state[6] = 0.0
    state[7] = float(b_ph * energy)

    return state


def kerr_isco_radius(
    metric: Union[KerrMetric, float],
    spin: Optional[float] = None,
    prograde: bool = True,
    s: Optional[int] = None,
) -> float:
    """Calculates the coordinate radius of the innermost stable circular orbit (ISCO) in Kerr spacetime.

    Uses the exact closed-form expression (Bardeen, Press, Teukolsky 1972):
        r_ISCO = M * [3 + Z2 +/- sqrt((3 - Z1)(3 + Z1 + 2*Z2))]
    where minus is prograde and plus is retrograde.

    Parameters
    ----------
    metric : KerrMetric or float
        An instance of KerrMetric or a positive float mass M.
    spin : float, optional
        Signed spin parameter a when metric is a float mass.
    prograde : bool, optional
        Whether orbital motion is prograde relative to spin. Default is True.
    s : {-1, 1}, optional
        Coordinate azimuthal direction parameter.

    Returns
    -------
    float
        ISCO coordinate radius in Boyer-Lindquist coordinates.
    """
    mass, a, s_val = _resolve_kerr_parameters(metric, spin, prograde=prograde, s=s)
    chi = abs(a) / mass
    if chi == 0.0:
        return 6.0 * mass
    is_pro = (s_val * a > 0.0) if s is not None else prograde
    z1 = 1.0 + ((1.0 - chi * chi) ** (1.0 / 3.0)) * (
        (1.0 + chi) ** (1.0 / 3.0) + (1.0 - chi) ** (1.0 / 3.0)
    )
    z2 = float(np.sqrt(3.0 * chi * chi + z1 * z1))
    term = max(0.0, (3.0 - z1) * (3.0 + z1 + 2.0 * z2))
    sqrt_term = float(np.sqrt(term))
    if is_pro:
        return float(mass * (3.0 + z2 - sqrt_term))
    return float(mass * (3.0 + z2 + sqrt_term))


def kerr_circular_orbital_frequency(
    metric: Union[KerrMetric, float],
    r: float,
    spin: Optional[float] = None,
    prograde: bool = True,
    s: Optional[int] = None,
) -> float:
    """Calculates the coordinate angular frequency Omega_phi = dphi/dt for an equatorial circular orbit.

    The signed orbital frequency is:
        Omega_phi = s * sqrt(M) / (r^(3/2) + s * a * sqrt(M))

    Parameters
    ----------
    metric : KerrMetric or float
        An instance of KerrMetric or a positive float mass M.
    r : float
        Orbital coordinate radius. Must be strictly outside the equatorial photon orbit r > r_ph.
    spin : float, optional
        Signed spin parameter a when metric is a float mass.
    prograde : bool, optional
        Whether orbital motion is prograde relative to spin. Default is True.
    s : {-1, 1}, optional
        Coordinate azimuthal direction parameter.

    Returns
    -------
    float
        Signed coordinate angular velocity dphi/dt in Boyer-Lindquist coordinates.

    Raises
    ------
    ValueError
        If r <= r_ph or inputs are non-finite.
    """
    mass, a, s_val = _resolve_kerr_parameters(metric, spin, prograde=prograde, s=s)
    if not np.isfinite(r):
        raise ValueError(f"Orbital radius r must be finite, got r = {r}")
    r_ph = kerr_equatorial_photon_orbit_radius(mass, a, s=s_val)
    if r <= r_ph:
        raise ValueError(
            f"Equatorial timelike circular orbits require r > r_ph = {r_ph:.6f}, got r = {r}"
        )
    denom = r ** 1.5 + s_val * a * np.sqrt(mass)
    return float(s_val * np.sqrt(mass) / denom)


def kerr_circular_timelike_energy(
    metric: Union[KerrMetric, float],
    r: float,
    spin: Optional[float] = None,
    prograde: bool = True,
    s: Optional[int] = None,
) -> float:
    """Calculates conserved specific energy E = -p_t for an equatorial circular timelike orbit.

    The conserved specific energy per unit rest mass is:
        E = (r^(3/2) - 2M*sqrt(r) + s*a*sqrt(M)) / [r^(3/4) * sqrt(r^(3/2) - 3M*sqrt(r) + 2*s*a*sqrt(M))]

    Parameters
    ----------
    metric : KerrMetric or float
        An instance of KerrMetric or a positive float mass M.
    r : float
        Orbital coordinate radius. Must satisfy r > r_ph.
    spin : float, optional
        Signed spin parameter a when metric is a float mass.
    prograde : bool, optional
        Whether orbital motion is prograde relative to spin. Default is True.
    s : {-1, 1}, optional
        Coordinate azimuthal direction parameter.

    Returns
    -------
    float
        Conserved specific energy E > 0.

    Raises
    ------
    ValueError
        If r <= r_ph or inputs are non-finite.
    """
    mass, a, s_val = _resolve_kerr_parameters(metric, spin, prograde=prograde, s=s)
    if not np.isfinite(r):
        raise ValueError(f"Orbital radius r must be finite, got r = {r}")
    r_ph = kerr_equatorial_photon_orbit_radius(mass, a, s=s_val)
    if r <= r_ph:
        raise ValueError(
            f"Equatorial timelike circular orbits require r > r_ph = {r_ph:.6f}, got r = {r}"
        )
    num = r ** 1.5 - 2.0 * mass * np.sqrt(r) + s_val * a * np.sqrt(mass)
    radicand = r ** 1.5 - 3.0 * mass * np.sqrt(r) + 2.0 * s_val * a * np.sqrt(mass)
    if radicand <= 0.0:
        raise ValueError(f"Radicand non-positive for r = {r}: radicand = {radicand}")
    denom = (r ** 0.75) * np.sqrt(radicand)
    return float(num / denom)


def kerr_circular_timelike_angular_momentum(
    metric: Union[KerrMetric, float],
    r: float,
    spin: Optional[float] = None,
    prograde: bool = True,
    s: Optional[int] = None,
) -> float:
    """Calculates conserved axial angular momentum L_z = p_phi for an equatorial circular timelike orbit.

    The conserved axial angular momentum per unit rest mass is:
        L_z = s * sqrt(M) * (r^2 - 2*s*a*sqrt(M*r) + a^2) / [r^(3/4) * sqrt(r^(3/2) - 3M*sqrt(r) + 2*s*a*sqrt(M))]

    Parameters
    ----------
    metric : KerrMetric or float
        An instance of KerrMetric or a positive float mass M.
    r : float
        Orbital coordinate radius. Must satisfy r > r_ph.
    spin : float, optional
        Signed spin parameter a when metric is a float mass.
    prograde : bool, optional
        Whether orbital motion is prograde relative to spin. Default is True.
    s : {-1, 1}, optional
        Coordinate azimuthal direction parameter.

    Returns
    -------
    float
        Conserved axial angular momentum L_z.

    Raises
    ------
    ValueError
        If r <= r_ph or inputs are non-finite.
    """
    mass, a, s_val = _resolve_kerr_parameters(metric, spin, prograde=prograde, s=s)
    if not np.isfinite(r):
        raise ValueError(f"Orbital radius r must be finite, got r = {r}")
    r_ph = kerr_equatorial_photon_orbit_radius(mass, a, s=s_val)
    if r <= r_ph:
        raise ValueError(
            f"Equatorial timelike circular orbits require r > r_ph = {r_ph:.6f}, got r = {r}"
        )
    num = s_val * np.sqrt(mass) * (r * r - 2.0 * s_val * a * np.sqrt(mass * r) + a * a)
    radicand = r ** 1.5 - 3.0 * mass * np.sqrt(r) + 2.0 * s_val * a * np.sqrt(mass)
    if radicand <= 0.0:
        raise ValueError(f"Radicand non-positive for r = {r}: radicand = {radicand}")
    denom = (r ** 0.75) * np.sqrt(radicand)
    return float(num / denom)


def kerr_circular_timelike_initial_state(
    metric: Union[KerrMetric, float],
    r: float,
    phi: float = 0.0,
    spin: Optional[float] = None,
    prograde: bool = True,
    s: Optional[int] = None,
) -> np.ndarray:
    """Constructs a canonical 8-component initial state for an equatorial circular timelike orbit in Kerr spacetime.

    The state is represented as:
        y0 = (x0=0, r=r, theta=pi/2, phi=phi, p0=-E, pr=0, ptheta=0, pphi=L_z)
    satisfying the exact mass-shell condition H(x, p) = -1/2.

    Parameters
    ----------
    metric : KerrMetric or float
        An instance of KerrMetric or a positive float mass M.
    r : float
        Orbital coordinate radius (r > r_ph).
    phi : float, optional
        Initial azimuthal angle phi, by default 0.0.
    spin : float, optional
        Signed spin parameter a when metric is a float mass.
    prograde : bool, optional
        Whether orbital motion is prograde relative to spin. Default is True.
    s : {-1, 1}, optional
        Coordinate azimuthal direction parameter.

    Returns
    -------
    np.ndarray
        Canonical 8-component state vector of shape (8,) and dtype float64.

    Raises
    ------
    ValueError
        If r <= r_ph or inputs are non-finite.
    """
    mass, a, s_val = _resolve_kerr_parameters(metric, spin, prograde=prograde, s=s)
    if not isinstance(metric, KerrMetric):
        kerr_metric = KerrMetric(mass=mass, spin=a)
    else:
        kerr_metric = metric

    if not np.isfinite(phi):
        raise ValueError(f"Initial azimuth phi must be finite, got phi = {phi}")

    energy = kerr_circular_timelike_energy(kerr_metric, r, prograde=prograde, s=s)
    lz = kerr_circular_timelike_angular_momentum(kerr_metric, r, prograde=prograde, s=s)

    state = np.zeros(STATE_DIMENSION, dtype=np.float64)
    state[IDX_X0] = 0.0
    state[IDX_R] = float(r)
    state[IDX_THETA] = 0.5 * np.pi
    state[IDX_PHI] = float(phi)
    state[4] = -energy
    state[5] = 0.0
    state[6] = 0.0
    state[7] = lz

    return state


def kerr_perturbed_circular_timelike_initial_state(
    metric: Union[KerrMetric, float],
    r: float,
    delta_pr: float,
    phi: float = 0.0,
    spin: Optional[float] = None,
    prograde: bool = True,
    s: Optional[int] = None,
) -> np.ndarray:
    """Constructs a radially perturbed circular timelike initial state preserving the Kerr mass-shell constraint.

    To perturb the circular orbit at radius r with radial momentum p_r = delta_pr while preserving the
    exact timelike mass-shell invariant 2*H = g^{mu nu} p_mu p_nu = -1, the perturbed energy is recomputed
    by solving the exact quadratic constraint on the equator (theta = pi/2):
        g^{tt} E^2 - 2 g^{t phi} E L_z + g^{phi phi} L_z^2 + g^{rr} (delta_pr)^2 = -1
    yielding:
        E_pert = [ -g^{t phi} L_z + sqrt( (g^{t phi} L_z)^2 - g^{tt} (1 + g^{phi phi} L_z^2 + g^{rr} (delta_pr)^2) ) ] / (-g^{tt})

    This ensures H(y0) = -0.5 to machine precision without introducing spurious constraint violations.

    Parameters
    ----------
    metric : KerrMetric or float
        An instance of KerrMetric or a positive float mass M.
    r : float
        Orbital coordinate radius (r > r_ph).
    delta_pr : float
        Initial radial momentum perturbation delta_pr.
    phi : float, optional
        Initial azimuthal angle phi, by default 0.0.
    spin : float, optional
        Signed spin parameter a when metric is a float mass.
    prograde : bool, optional
        Whether orbital motion is prograde relative to spin. Default is True.
    s : {-1, 1}, optional
        Coordinate azimuthal direction parameter.

    Returns
    -------
    np.ndarray
        Canonical 8-component state vector of shape (8,) and dtype float64.

    Raises
    ------
    ValueError
        If r <= r_ph, delta_pr is non-finite, or inputs are non-finite.
    """
    mass, a, s_val = _resolve_kerr_parameters(metric, spin, prograde=prograde, s=s)
    if not isinstance(metric, KerrMetric):
        kerr_metric = KerrMetric(mass=mass, spin=a)
    else:
        kerr_metric = metric

    if not np.isfinite(delta_pr):
        raise ValueError(f"Radial perturbation delta_pr must be finite, got delta_pr = {delta_pr}")
    if not np.isfinite(phi):
        raise ValueError(f"Initial azimuth phi must be finite, got phi = {phi}")

    lz = kerr_circular_timelike_angular_momentum(kerr_metric, r, prograde=prograde, s=s)

    g_contra = kerr_metric.g_contra(r, 0.5 * np.pi)
    g_tt = g_contra[0, 0]
    g_tphi = g_contra[0, 3]
    g_phiphi = g_contra[3, 3]
    g_rr = g_contra[1, 1]

    A_tilde = -g_tt
    B_tilde = 2.0 * g_tphi * lz
    C_tilde = -(1.0 + g_phiphi * (lz ** 2) + g_rr * (delta_pr ** 2))
    disc = B_tilde * B_tilde - 4.0 * A_tilde * C_tilde
    if disc < 0.0:
        raise ValueError(f"Negative discriminant in perturbed energy calculation: {disc}")
    energy_pert = float((-B_tilde + np.sqrt(disc)) / (2.0 * A_tilde))

    state = np.zeros(STATE_DIMENSION, dtype=np.float64)
    state[IDX_X0] = 0.0
    state[IDX_R] = float(r)
    state[IDX_THETA] = 0.5 * np.pi
    state[IDX_PHI] = float(phi)
    state[4] = -energy_pert
    state[5] = float(delta_pr)
    state[6] = 0.0
    state[7] = lz

    return state


def kerr_radial_epicyclic_frequency(
    metric: Union[KerrMetric, float],
    r: float,
    spin: Optional[float] = None,
    prograde: bool = True,
    s: Optional[int] = None,
    time_parameter: str = "proper",
) -> float:
    """Calculates the radial epicyclic frequency for an equatorial circular timelike orbit in Kerr spacetime.

    In Boyer-Lindquist coordinates, small radial perturbations delta_r about an equatorial circular
    timelike orbit at radius r satisfy harmonic oscillation equations:
        d^2(delta_r) / dtau^2 + omega_r^2 delta_r = 0  (proper time tau)
        d^2(delta_r) / dt^2   + Omega_r^2 delta_r = 0  (coordinate time t)

    The coordinate-time frequency is given analytically by:
        Omega_r^2 = Omega_phi^2 * [ 1 - 6M/r + 8 s a sqrt(M)/r^(3/2) - 3 a^2 / r^2 ]
    where:
        Omega_phi = s * sqrt(M) / (r^(3/2) + s * a * sqrt(M))
    and s in {-1, +1} is the azimuthal circulation direction (sa > 0 for prograde, sa < 0 for retrograde).

    The proper-time frequency relates to coordinate-time frequency via:
        omega_r = u^t * Omega_r = dt/dtau * Omega_r
    which identically matches the second derivative of the Carter radial potential:
        omega_r = sqrt( -R''(r) / (2 * r^4) )
    evaluated with conserved specific energy E and axial angular momentum L_z held fixed during differentiation.

    Parameters
    ----------
    metric : KerrMetric or float
        An instance of KerrMetric or a positive float mass M.
    r : float
        Orbital coordinate radius. Must be strictly outside the ISCO (r > r_ISCO)
        for a stable orbit with real epicyclic frequency.
    spin : float, optional
        Signed spin parameter a when metric is a float mass.
    prograde : bool, optional
        Whether orbital motion is prograde relative to spin. Default is True.
    s : {-1, 1}, optional
        Coordinate azimuthal direction parameter.
    time_parameter : {'proper', 'coordinate'}, optional
        Time parameter with respect to which the frequency is evaluated:
        - 'proper': proper time tau along the geodesic (omega_r).
        - 'coordinate': Boyer-Lindquist coordinate time t (Omega_r).
        Default is 'proper'.

    Returns
    -------
    float
        Radial epicyclic frequency in radians per unit time.

    Raises
    ------
    ValueError
        If r <= r_ISCO (marginally stable or unstable orbit; frequency is non-positive or imaginary),
        r <= r_ph, or invalid time_parameter.
    """
    if time_parameter not in ("proper", "coordinate"):
        raise ValueError(
            f"time_parameter must be 'proper' or 'coordinate', got '{time_parameter}'"
        )
    mass, a, s_val = _resolve_kerr_parameters(metric, spin, prograde=prograde, s=s)
    if not isinstance(metric, KerrMetric):
        kerr_metric = KerrMetric(mass=mass, spin=a)
    else:
        kerr_metric = metric

    r_ph = kerr_equatorial_photon_orbit_radius(kerr_metric, prograde=prograde, s=s)
    if r <= r_ph:
        raise ValueError(
            f"Radius r = {r} is inside or on equatorial photon orbit r_ph = {r_ph}"
        )
    r_isco = kerr_isco_radius(kerr_metric, prograde=prograde, s=s)
    if r < r_isco or np.isclose(r, r_isco, atol=1e-12):
        raise ValueError(
            f"Radius r = {r} must be strictly outside ISCO r_ISCO = {r_isco} for stable real epicyclic frequency"
        )

    omega_phi = kerr_circular_orbital_frequency(kerr_metric, r, prograde=prograde, s=s)
    poly_bracket = 1.0 - 6.0 * mass / r + 8.0 * s_val * a * np.sqrt(mass) / (r ** 1.5) - 3.0 * (a ** 2) / (r ** 2)
    omega_r_sq_coord = max(0.0, (omega_phi ** 2) * poly_bracket)
    omega_r_coord = float(np.sqrt(omega_r_sq_coord))

    if time_parameter == "coordinate":
        return omega_r_coord

    # Proper time conversion: omega_r = u^t * Omega_r
    E = kerr_circular_timelike_energy(kerr_metric, r, prograde=prograde, s=s)
    Lz = kerr_circular_timelike_angular_momentum(kerr_metric, r, prograde=prograde, s=s)
    g_inv = kerr_metric.g_contra(r, 0.5 * np.pi)
    u_t = -g_inv[0, 0] * E + g_inv[0, 3] * Lz
    return float(u_t * omega_r_coord)


def kerr_proper_radial_distance_horizon_to_isco(
    metric: Union[KerrMetric, float],
    spin: Optional[float] = None,
    prograde: bool = True,
    s: Optional[int] = None,
) -> float:
    """Calculates the proper radial distance between outer horizon and ISCO on a Boyer-Lindquist spatial slice.

    Evaluates the integral:
        Delta_ell = int_{r_+}^{r_ISCO} sqrt(g_{rr}) dr = int_{r_+}^{r_ISCO} [ r / sqrt((r - r_+)(r - r_-)) ] dr
    on a constant-(t, phi) equatorial (theta = pi/2) spatial slice.

    Using the exact analytic antiderivative:
        F(r) = sqrt(Delta(r)) + M * ln( r - M + sqrt(Delta(r)) )
    the integral evaluates in closed form across all subextremal spins (|a| < M) to:
        Delta_ell = sqrt(Delta(r_ISCO)) + M * ln( [ r_ISCO - M + sqrt(Delta(r_ISCO)) ] / sqrt(M^2 - a^2) )

    Parameters
    ----------
    metric : KerrMetric or float
        An instance of KerrMetric or a positive float mass M.
    spin : float, optional
        Signed spin parameter a when metric is a float mass.
    prograde : bool, optional
        Whether the ISCO is prograde relative to spin. Default is True.
    s : {-1, 1}, optional
        Coordinate azimuthal direction parameter.

    Returns
    -------
    float
        Proper radial distance Delta_ell in units of length (geometrized M).

    Raises
    ------
    ValueError
        If |a| >= M (extremal or naked singularity).
    """
    mass, a, _ = _resolve_kerr_parameters(metric, spin, prograde=prograde, s=s)
    if not isinstance(metric, KerrMetric):
        kerr_metric = KerrMetric(mass=mass, spin=a)
    else:
        kerr_metric = metric

    if abs(a) >= mass:
        raise ValueError(
            f"Proper distance calculation requires subextremal spin |a| < M, got |a| = {abs(a)} and M = {mass}"
        )

    r_plus = kerr_metric.horizon_radius
    r_isco = kerr_isco_radius(kerr_metric, prograde=prograde, s=s)
    delta_isco = r_isco ** 2 - 2.0 * mass * r_isco + a ** 2
    sqrt_delta_isco = float(np.sqrt(max(0.0, delta_isco)))

    b_val = float(np.sqrt((mass - abs(a)) * (mass + abs(a))))
    numerator = (r_isco - mass) + sqrt_delta_isco
    term_log = float(mass * np.log(numerator / b_val))

    return float(sqrt_delta_isco + term_log)

