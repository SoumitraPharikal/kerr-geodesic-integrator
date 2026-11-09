"""Geodesic termination and monitoring events for numerical trajectory integration.

This module provides an event-detection framework compatible with `scipy.integrate.solve_ivp`,
enabling the detection of geometric and physical boundaries along geodesic paths in curved
spacetime. Supported events include:
- Exterior horizon-cutoff events (r = r_cut = 2M(1 + epsilon)).
- Escape-radius events (r = r_esc).
- Radial turning-point events (dr/dlambda = 0).

Design Architecture & Compatibility with Future Stages:
-------------------------------------------------------
Events are implemented as callable objects inheriting from `GeodesicEvent`.
Each event instance implements:
    __call__(lambda, y) -> float
and exposes two attributes inspected by `solve_ivp`:
    terminal: bool (whether to stop integration upon triggering)
    direction: int (-1: positive to negative crossing; +1: negative to positive; 0: all)
as well as a human-readable `name` attribute.

This design cleanly decouples event geometry from the ODE solver and extends seamlessly
to Kerr spacetime (Stage 2), where:
- Horizon cutoff events adapt to Kerr outer horizon r_+ = M + sqrt(M^2 - a^2).
- Radial turning-point events evaluate dr/dlambda = [hamiltonian_rhs(y, metric)]_r,
  which automatically accounts for Kerr frame dragging and Boyer-Lindquist metric terms.
- Polar turning points (dtheta/dlambda = 0) and Carter constant bounds can be added
  as subclasses without modifying the integrator core.

State Vector Ordering:
    y = (x0, r, theta, phi, p0, pr, ptheta, pphi)
    - y[1] is the radial coordinate r.

Units: Geometrized units G = c = 1.
"""

from abc import ABC, abstractmethod
from typing import Final, Literal, Optional, Union
import numpy as np

from geodesics.constants import DEFAULT_HORIZON_BUFFER, IDX_R
from geodesics.hamiltonian import hamiltonian_rhs
from geodesics.metrics.base import SpacetimeMetric

EventDirection = Literal[-1, 0, 1]


class GeodesicEvent(ABC):
    """Abstract base class for geodesic event functions compatible with scipy.integrate.solve_ivp.

    Attributes
    ----------
    name : str
        Human-readable identifier for the event.
    terminal : bool
        Whether reaching the event surface terminates numerical integration.
    direction : int
        Direction of zero crossing to detect:
        -1: Transition from positive to negative values (e.g. decreasing coordinate).
        +1: Transition from negative to positive values (e.g. increasing coordinate).
         0: All zero-crossing transitions.
    """

    def __init__(
        self,
        name: str,
        terminal: bool = True,
        direction: EventDirection = 0,
    ) -> None:
        if not isinstance(name, str) or not name.strip():
            raise TypeError(f"name must be a non-empty string, got {name!r}")
        if not isinstance(terminal, bool):
            raise TypeError(f"terminal must be a boolean, got {type(terminal).__name__}")
        if direction not in (-1, 0, 1):
            raise ValueError(f"direction must be in {{-1, 0, 1}}, got {direction}")

        self._name: Final[str] = name.strip()
        self.terminal: bool = terminal
        self.direction: int = direction

    @property
    def name(self) -> str:
        """Human-readable identifier of the event."""
        return self._name

    @abstractmethod
    def __call__(self, _lambda: float, y: np.ndarray) -> float:
        """Evaluates the scalar event function g(lambda, y).

        A zero crossing g(lambda, y) = 0 defines an event occurrence.

        Parameters
        ----------
        _lambda : float
            Current affine parameter value.
        y : np.ndarray
            Current 8-component canonical state vector (x0, r, theta, phi, p0, pr, ptheta, pphi).
            Must not be mutated.

        Returns
        -------
        float
            Scalar value whose sign change triggers the event detector.
        """
        pass

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(name={self.name!r}, "
            f"terminal={self.terminal}, direction={self.direction})"
        )


class HorizonCutoffEvent(GeodesicEvent):
    """Detects when a geodesic crosses an exterior cutoff surface outside the event horizon.

    In standard Schwarzschild coordinates, the event horizon r_H = 2M is a coordinate
    singularity where coordinate time t -> infinity and radial momentum p_r -> infinity,
    even though affine parameter lambda remains finite. Integrating directly into r = 2M
    causes numerical step-size underflow.

    This event stops integration at a configurable exterior buffer:
        r_cut = r_H * (1 + epsilon) = 2M * (1 + epsilon),   epsilon > 0
    such that:
        g_horizon(y) = r - r_cut = 0

    IMPORTANT SCIENTIFIC NOTE:
    Reaching r = r_cut is an exterior numerical cutoff in coordinate space; it does NOT
    represent traversing the physical event horizon into the black hole interior.

    Parameters
    ----------
    mass_or_metric : float or SpacetimeMetric
        Physical mass M (positive float) or an instance of SpacetimeMetric (e.g. SchwarzschildMetric).
    epsilon : float, optional
        Fractional exterior buffer fraction, by default DEFAULT_HORIZON_BUFFER (1e-3).
        Must be strictly positive and finite.
    terminal : bool, optional
        Whether triggering terminates integration, by default True.
    direction : {-1, 0, 1}, optional
        Zero-crossing direction, by default -1 (detects decreasing radius / inward motion).
    name : str, optional
        Event identifier, by default "horizon_cutoff".
    """

    def __init__(
        self,
        mass_or_metric: Optional[Union[float, SpacetimeMetric]] = None,
        epsilon: float = DEFAULT_HORIZON_BUFFER,
        terminal: bool = True,
        direction: EventDirection = -1,
        name: str = "horizon_cutoff",
        *,
        mass: Optional[float] = None,
        metric: Optional[SpacetimeMetric] = None,
    ) -> None:
        super().__init__(name=name, terminal=terminal, direction=direction)

        if mass_or_metric is None:
            if metric is not None:
                mass_or_metric = metric
            elif mass is not None:
                mass_or_metric = mass
            else:
                raise TypeError(
                    "HorizonCutoffEvent requires mass_or_metric, mass, or metric to be specified."
                )

        if isinstance(mass_or_metric, SpacetimeMetric):
            if hasattr(mass_or_metric, "horizon_radius"):
                r_horizon = float(mass_or_metric.horizon_radius)
            else:
                r_horizon = 2.0 * float(mass_or_metric.mass)
            mass = float(mass_or_metric.mass)
        elif isinstance(mass_or_metric, (int, float)) and not isinstance(mass_or_metric, bool):
            mass = float(mass_or_metric)
            if not np.isfinite(mass) or mass <= 0.0:
                raise ValueError(f"mass must be strictly positive and finite, got {mass}")
            r_horizon = 2.0 * mass
        else:
            raise TypeError(
                f"mass_or_metric must be a positive float mass or SpacetimeMetric instance, "
                f"got {type(mass_or_metric).__name__}"
            )

        if isinstance(epsilon, bool) or not np.isfinite(epsilon) or epsilon <= 0.0:
            raise ValueError(f"epsilon must be strictly positive and finite, got {epsilon}")

        self._mass: Final[float] = mass
        self._epsilon: Final[float] = float(epsilon)
        self._r_horizon: Final[float] = r_horizon
        self._r_cut: Final[float] = r_horizon * (1.0 + self._epsilon)

    @property
    def mass(self) -> float:
        """Physical mass M used for the cutoff calculation."""
        return self._mass

    @property
    def epsilon(self) -> float:
        """Fractional exterior buffer epsilon."""
        return self._epsilon

    @property
    def horizon_radius(self) -> float:
        """Underlying horizon radius r_H."""
        return self._r_horizon

    @property
    def r_cut(self) -> float:
        """Exterior cutoff radius r_cut = r_H * (1 + epsilon)."""
        return self._r_cut

    def __call__(self, _lambda: float, y: np.ndarray) -> float:
        """Evaluates g(y) = r - r_cut."""
        return float(y[IDX_R] - self._r_cut)


class EscapeRadiusEvent(GeodesicEvent):
    """Detects when a geodesic reaches a specified exterior escape sphere r = r_esc.

    Evaluates:
        g_escape(y) = r - r_esc = 0

    IMPORTANT SCIENTIFIC NOTE:
    Reaching a finite escape radius r_esc confirms only that the trajectory has crossed
    the chosen coordinate sphere. It does NOT prove that a photon is gravitationally unbound
    unless accompanied by an asymptotic kinetic condition (e.g. outward branch with
    positive asymptotic velocity). Depending on the geodesic and the sphere's position relative
    to the effective-potential barrier, a trajectory may still encounter a later turning point.
    Crossing a finite coordinate sphere does not, by itself, establish asymptotic escape to infinity.

    Parameters
    ----------
    r_escape : float
        Radius of the escape boundary sphere. Must be strictly positive and finite.
    terminal : bool, optional
        Whether triggering terminates integration, by default True.
    direction : {-1, 0, 1}, optional
        Zero-crossing direction, by default +1 (detects increasing radius / outward motion).
    name : str, optional
        Event identifier, by default "escape_radius".
    """

    def __init__(
        self,
        r_escape: float,
        terminal: bool = True,
        direction: EventDirection = 1,
        name: str = "escape_radius",
    ) -> None:
        super().__init__(name=name, terminal=terminal, direction=direction)

        if isinstance(r_escape, bool) or not np.isfinite(r_escape) or r_escape <= 0.0:
            raise ValueError(f"r_escape must be strictly positive and finite, got {r_escape}")

        self._r_escape: Final[float] = float(r_escape)

    @property
    def r_escape(self) -> float:
        """Escape boundary radius r_esc."""
        return self._r_escape

    def __call__(self, _lambda: float, y: np.ndarray) -> float:
        """Evaluates g(y) = r - r_esc."""
        return float(y[IDX_R] - self._r_escape)


class RadialTurningPointEvent(GeodesicEvent):
    """Detects radial turning points where the radial velocity dr/dlambda vanishes.

    Evaluates the exact radial coordinate velocity directly from the canonical vector field:
        g_turn(y) = dr/dlambda = [hamiltonian_rhs(y, metric)]_r = 0

    For Schwarzschild spacetime, dr/dlambda = f(r)*p_r = (1 - 2M/r)*p_r.
    Evaluating the full vector field component guarantees mathematical consistency across
    both Schwarzschild and Kerr spacetimes (Stage 2) without relying on ad-hoc sign checks.

    Numerical & Physical Classification of Turning-Point Roots:
    ----------------------------------------------------------
    SciPy's event detection detects roots of g(lambda) = 0 by locating sign changes between
    ODE time steps (g(lambda_k) * g(lambda_{k+1}) <= 0) followed by Brent's root-finding.
    Consequently, four physically distinct cases arise:

    A. Ordinary Periapsis:
       dr/dlambda = 0 with d^2r/dlambda^2 > 0.
       The radial velocity dr/dlambda undergoes a genuine transversal sign change from
       negative to positive. Detected cleanly by root finding with direction=+1 or direction=0.

    B. Ordinary Apoapsis:
       dr/dlambda = 0 with d^2r/dlambda^2 < 0.
       The radial velocity dr/dlambda undergoes a genuine transversal sign change from
       positive to negative. Detected cleanly by root finding with direction=-1 or direction=0.

    C. Exact Circular Photon Orbit (r = 3M in Schwarzschild):
       dr/dlambda = 0 and d^2r/dlambda^2 = 0 throughout the orbit.
       Here, g(lambda) is identically zero everywhere along the trajectory rather than at an
       isolated zero crossing. Because g(lambda_0) = 0, SciPy detects g <= 0 and g >= 0 on the
       very first step, causing a terminal event to halt integration immediately at lambda = 0.
       Ordinary sign-change detection does NOT monitor or follow circular orbits.

    D. Critical Geodesic Asymptotic Approach:
       For critical trajectories asymptotically spiraling toward the photon sphere (r -> 3M as
       lambda -> infinity), dr/dlambda -> 0 only as affine parameter tends to infinity. At any
       finite lambda, dr/dlambda remains strictly negative. There is no isolated finite-parameter
       root, so standard bracketed sign-change detection cannot identify an asymptotic approach.

    Parameters
    ----------
    metric : SpacetimeMetric
        Spacetime metric instance used to evaluate the Hamiltonian vector field.
    terminal : bool, optional
        Whether triggering terminates integration, by default True.
    direction : {-1, 0, 1}, optional
        Zero-crossing direction, by default 0 (detects both periapsis +1 and apoapsis -1).
    name : str, optional
        Event identifier, by default "radial_turning_point".
    """

    def __init__(
        self,
        metric: SpacetimeMetric,
        terminal: bool = True,
        direction: EventDirection = 0,
        name: str = "radial_turning_point",
    ) -> None:
        super().__init__(name=name, terminal=terminal, direction=direction)

        if not isinstance(metric, SpacetimeMetric):
            raise TypeError(
                f"metric must be an instance of SpacetimeMetric, got {type(metric).__name__}"
            )

        self._metric: Final[SpacetimeMetric] = metric

    @property
    def metric(self) -> SpacetimeMetric:
        """Underlying spacetime metric."""
        return self._metric

    def __call__(self, _lambda: float, y: np.ndarray) -> float:
        """Evaluates g(y) = dr/dlambda = [hamiltonian_rhs(y, metric)]_r."""
        rhs = hamiltonian_rhs(y, self._metric)
        return float(rhs[IDX_R])


# Factory helper functions
def horizon_cutoff_event(
    mass_or_metric: Optional[Union[float, SpacetimeMetric]] = None,
    epsilon: float = DEFAULT_HORIZON_BUFFER,
    terminal: bool = True,
    direction: EventDirection = -1,
    name: str = "horizon_cutoff",
    *,
    mass: Optional[float] = None,
    metric: Optional[SpacetimeMetric] = None,
) -> HorizonCutoffEvent:
    """Creates a configured HorizonCutoffEvent."""
    return HorizonCutoffEvent(
        mass_or_metric=mass_or_metric,
        epsilon=epsilon,
        terminal=terminal,
        direction=direction,
        name=name,
        mass=mass,
        metric=metric,
    )


def escape_radius_event(
    r_escape: float,
    terminal: bool = True,
    direction: EventDirection = 1,
    name: str = "escape_radius",
) -> EscapeRadiusEvent:
    """Creates a configured EscapeRadiusEvent."""
    return EscapeRadiusEvent(
        r_escape=r_escape,
        terminal=terminal,
        direction=direction,
        name=name,
    )


def radial_turning_point_event(
    metric: SpacetimeMetric,
    terminal: bool = True,
    direction: EventDirection = 0,
    name: str = "radial_turning_point",
) -> RadialTurningPointEvent:
    """Creates a configured RadialTurningPointEvent."""
    return RadialTurningPointEvent(
        metric=metric,
        terminal=terminal,
        direction=direction,
        name=name,
    )
