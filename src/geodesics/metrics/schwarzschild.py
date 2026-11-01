"""Schwarzschild spacetime metric implementation.

Defines the SchwarzschildMetric class representing the exterior spacetime of a
static, spherically symmetric black hole in Schwarzschild coordinates:
x^mu = (x0, r, theta, phi) with x0 = ct.

Follows Stage 0 v1.2 specification.
"""

from typing import Optional
import numpy as np

from geodesics.constants import (
    DEFAULT_MASS,
    IDX_X0,
    IDX_R,
    IDX_THETA,
    IDX_PHI,
)
from geodesics.metrics.base import SpacetimeMetric


class SchwarzschildMetric(SpacetimeMetric):
    """Schwarzschild metric in standard Schwarzschild coordinates (x0, r, theta, phi).

    The line element is:
        ds^2 = -f(r)(dx0)^2 + f(r)^{-1} dr^2 + r^2 dtheta^2 + r^2 sin^2(theta) dphi^2
    where:
        f(r) = 1 - 2M / r
        x0 = c * t

    All calculations use geometrized units: G = c = 1.
    """

    def __init__(self, mass: float = DEFAULT_MASS) -> None:
        """Initializes the Schwarzschild metric with mass M.

        Parameters
        ----------
        mass : float, optional
            Physical black hole mass M in geometrized units. Must be positive.
            Default is 1.0.

        Raises
        ------
        ValueError
            If mass is less than or equal to zero, or non-finite.
        """
        if not np.isfinite(mass) or mass <= 0.0:
            raise ValueError(f"Black hole mass M must be positive and finite, got M = {mass}")
        self._mass = float(mass)

    @property
    def mass(self) -> float:
        """Physical mass M of the Schwarzschild black hole."""
        return self._mass

    @property
    def horizon_radius(self) -> float:
        """Event horizon coordinate radius r_H = 2M."""
        return 2.0 * self._mass

    @property
    def photon_sphere_radius(self) -> float:
        """Unstable circular photon orbit radius r_ph = 3M."""
        return 3.0 * self._mass

    @property
    def critical_impact_parameter(self) -> float:
        """Critical impact parameter separating capture from scattering: b_crit = 3*sqrt(3)*M."""
        return 3.0 * np.sqrt(3.0) * self._mass

    def lapse(self, r: float) -> float:
        """Evaluates the Schwarzschild lapse function f(r) = 1 - 2M / r.

        Parameters
        ----------
        r : float
            Radial coordinate (r > 2M).

        Returns
        -------
        float
            f(r) = 1 - 2M / r.

        Raises
        ------
        ValueError
            If r <= 2M or non-finite.
        """
        self._validate_radius(r)
        return 1.0 - (2.0 * self._mass / r)

    def _validate_radius(self, r: float) -> None:
        """Validates that r is in the exterior Schwarzschild vacuum domain (r > 2M)."""
        if not np.isfinite(r):
            raise ValueError(f"Radial coordinate r must be finite, got r = {r}")
        if r <= self.horizon_radius:
            raise ValueError(
                f"Radial coordinate r must be strictly outside the event horizon "
                f"r_H = 2M = {self.horizon_radius}, got r = {r}"
            )

    def _validate_theta(self, theta: float) -> None:
        """Validates that theta is in the standard coordinate domain (0 < theta < pi)."""
        if not np.isfinite(theta):
            raise ValueError(f"Polar angle theta must be finite, got theta = {theta}")
        if theta <= 0.0 or theta >= np.pi:
            raise ValueError(
                f"Polar angle theta must be strictly in the domain (0, pi), got theta = {theta}"
            )

    def _validate_coordinates(self, r: float, theta: float) -> None:
        """Validates both radial and polar coordinates."""
        self._validate_radius(r)
        self._validate_theta(theta)

    def g_cov(self, r: float, theta: float = np.pi / 2.0) -> np.ndarray:
        """Calculates the covariant metric tensor g_{mu nu}.

        Coordinate basis: x^mu = (x0, r, theta, phi).

        Parameters
        ----------
        r : float
            Radial coordinate (r > 2M).
        theta : float, optional
            Polar coordinate in radians (0 < theta < pi). Default is pi/2.

        Returns
        -------
        np.ndarray
            4x4 diagonal array representing g_{mu nu}.
        """
        self._validate_coordinates(r, theta)
        f = 1.0 - (2.0 * self._mass / r)
        sin_theta = np.sin(theta)

        g = np.zeros((4, 4), dtype=np.float64)
        g[IDX_X0, IDX_X0] = -f
        g[IDX_R, IDX_R] = 1.0 / f
        g[IDX_THETA, IDX_THETA] = r * r
        g[IDX_PHI, IDX_PHI] = (r * sin_theta) ** 2
        return g

    def g_contra(self, r: float, theta: float = np.pi / 2.0) -> np.ndarray:
        """Calculates the contravariant (inverse) metric tensor g^{mu nu}.

        Coordinate basis: x^mu = (x0, r, theta, phi).

        Parameters
        ----------
        r : float
            Radial coordinate (r > 2M).
        theta : float, optional
            Polar coordinate in radians (0 < theta < pi). Default is pi/2.

        Returns
        -------
        np.ndarray
            4x4 diagonal array representing g^{mu nu}.
        """
        self._validate_coordinates(r, theta)
        f = 1.0 - (2.0 * self._mass / r)
        sin_theta = np.sin(theta)
        r2 = r * r

        g_inv = np.zeros((4, 4), dtype=np.float64)
        g_inv[IDX_X0, IDX_X0] = -1.0 / f
        g_inv[IDX_R, IDX_R] = f
        g_inv[IDX_THETA, IDX_THETA] = 1.0 / r2
        g_inv[IDX_PHI, IDX_PHI] = 1.0 / (r2 * sin_theta * sin_theta)
        return g_inv

    def dg_contra_dr(self, r: float, theta: float = np.pi / 2.0) -> np.ndarray:
        """Calculates partial_r g^{alpha beta}.

        The non-zero components are:
            partial_r g^{00} = +2M / (r^2 * f^2)
            partial_r g^{rr} = +2M / r^2
            partial_r g^{theta theta} = -2 / r^3
            partial_r g^{phi phi} = -2 / (r^3 * sin^2(theta))

        Parameters
        ----------
        r : float
            Radial coordinate (r > 2M).
        theta : float, optional
            Polar coordinate in radians (0 < theta < pi). Default is pi/2.

        Returns
        -------
        np.ndarray
            4x4 array of partial_r g^{alpha beta}.
        """
        self._validate_coordinates(r, theta)
        f = 1.0 - (2.0 * self._mass / r)
        sin_theta = np.sin(theta)
        r2 = r * r
        r3 = r2 * r

        dg_dr = np.zeros((4, 4), dtype=np.float64)
        # CRITICAL: partial_r g^{00} is strictly positive: +2M / (r^2 * f^2)
        dg_dr[IDX_X0, IDX_X0] = (2.0 * self._mass) / (r2 * f * f)
        dg_dr[IDX_R, IDX_R] = (2.0 * self._mass) / r2
        dg_dr[IDX_THETA, IDX_THETA] = -2.0 / r3
        dg_dr[IDX_PHI, IDX_PHI] = -2.0 / (r3 * sin_theta * sin_theta)
        return dg_dr

    def dg_contra_dtheta(self, r: float, theta: float = np.pi / 2.0) -> np.ndarray:
        """Calculates partial_theta g^{alpha beta}.

        The only non-zero component is:
            partial_theta g^{phi phi} = -2 * cos(theta) / (r^2 * sin^3(theta))

        Parameters
        ----------
        r : float
            Radial coordinate (r > 2M).
        theta : float, optional
            Polar coordinate in radians (0 < theta < pi). Default is pi/2.

        Returns
        -------
        np.ndarray
            4x4 array of partial_theta g^{alpha beta}.
        """
        self._validate_coordinates(r, theta)
        sin_theta = np.sin(theta)
        cos_theta = np.cos(theta)
        r2 = r * r

        dg_dtheta = np.zeros((4, 4), dtype=np.float64)
        dg_dtheta[IDX_PHI, IDX_PHI] = (-2.0 * cos_theta) / (r2 * sin_theta**3)
        return dg_dtheta
