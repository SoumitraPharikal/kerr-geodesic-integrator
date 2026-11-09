"""Base interface for curved spacetime metrics.

Defines the SpacetimeMetric abstract base class specifying the protocol for
covariant metric components, contravariant components, and contravariant spatial
derivatives in accordance with Stage 0 v1.2 specification.
"""

from abc import ABC, abstractmethod
from typing import Tuple
import numpy as np

from geodesics.constants import COORDINATE_NAMES, SPACETIME_DIMENSION


class SpacetimeMetric(ABC):
    """Abstract base class defining the interface for stationary, axisymmetric spacetime metrics.

    The protocol assumes 4D spacetimes admitting a stationary Killing vector
    xi = partial_{x^0} and an axial Killing vector psi = partial_phi, such that
    metric components and their contravariant derivatives depend only on the
    coordinates (r, theta) in coordinates adapted to these symmetries.

    All metric implementations must adhere to:
    - Coordinate ordering: x^mu = (x0, r, theta, phi) where x0 = ct.
    - Symmetries: Stationary (partial_0 g = 0) and axisymmetric (partial_phi g = 0).
    - Geometrized units: G = c = 1.
    - Metric signature: (-, +, +, +).
    - Array dimensions: (4, 4) for rank-2 tensors, (4, 4, 4) for derivatives.
    """

    @property
    def coordinate_names(self) -> Tuple[str, ...]:
        """Returns the canonical coordinate names in index order (0, 1, 2, 3)."""
        return COORDINATE_NAMES

    @property
    def dimension(self) -> int:
        """Spacetime manifold dimension (always 4)."""
        return SPACETIME_DIMENSION

    @property
    @abstractmethod
    def mass(self) -> float:
        """Physical mass M of the central gravitating source."""
        pass

    @abstractmethod
    def g_cov(self, r: float, theta: float = np.pi / 2.0) -> np.ndarray:
        """Calculates the 4x4 covariant metric tensor g_{mu nu}.

        Parameters
        ----------
        r : float
            Radial coordinate (must be in exterior domain).
        theta : float, optional
            Polar coordinate in radians, by default np.pi / 2.0.

        Returns
        -------
        np.ndarray
            A 2D array of shape (4, 4) representing g_{mu nu}.
        """
        pass

    @abstractmethod
    def g_contra(self, r: float, theta: float = np.pi / 2.0) -> np.ndarray:
        """Calculates the 4x4 contravariant (inverse) metric tensor g^{mu nu}.

        Parameters
        ----------
        r : float
            Radial coordinate (must be in exterior domain).
        theta : float, optional
            Polar coordinate in radians, by default np.pi / 2.0.

        Returns
        -------
        np.ndarray
            A 2D array of shape (4, 4) representing g^{mu nu}.
        """
        pass

    @abstractmethod
    def dg_contra_dr(self, r: float, theta: float = np.pi / 2.0) -> np.ndarray:
        """Calculates partial_r g^{alpha beta}.

        Parameters
        ----------
        r : float
            Radial coordinate.
        theta : float, optional
            Polar coordinate in radians.

        Returns
        -------
        np.ndarray
            A 2D array of shape (4, 4) containing partial_r g^{alpha beta}.
        """
        pass

    @abstractmethod
    def dg_contra_dtheta(self, r: float, theta: float = np.pi / 2.0) -> np.ndarray:
        """Calculates partial_theta g^{alpha beta}.

        Parameters
        ----------
        r : float
            Radial coordinate.
        theta : float, optional
            Polar coordinate in radians.

        Returns
        -------
        np.ndarray
            A 2D array of shape (4, 4) containing partial_theta g^{alpha beta}.
        """
        pass

    def dg_contra_all(self, r: float, theta: float = np.pi / 2.0) -> np.ndarray:
        """Returns all coordinate derivatives of the contravariant metric.

        Returns a 3D array of shape (4, 4, 4) where the first index corresponds
        to the coordinate derivative index mu in (x0, r, theta, phi):
        out[mu, alpha, beta] = partial_mu g^{alpha beta}.

        Because stationary and axisymmetric metrics satisfy partial_0 g = 0
        and partial_phi g = 0, slices 0 and 3 are identically zero.

        Parameters
        ----------
        r : float
            Radial coordinate.
        theta : float, optional
            Polar coordinate in radians.

        Returns
        -------
        np.ndarray
            3D array of shape (4, 4, 4) with dtype float64.
        """
        dg = np.zeros((4, 4, 4), dtype=np.float64)
        dg[1, :, :] = self.dg_contra_dr(r, theta)
        dg[2, :, :] = self.dg_contra_dtheta(r, theta)
        return dg
