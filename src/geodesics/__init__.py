"""Kerr Geodesic Integrator package."""

from geodesics.constants import (
    DEFAULT_MASS,
    DEFAULT_RTOL,
    DEFAULT_ATOL,
    DEFAULT_MOMENTUM_ATOL,
    IDX_X0,
    IDX_R,
    IDX_THETA,
    IDX_PHI,
)
from geodesics.hamiltonian import (
    STATE_DIMENSION,
    STATE_NAMES,
    hamiltonian_rhs,
    hamiltonian_value,
)
from geodesics.metrics.base import SpacetimeMetric
from geodesics.metrics.schwarzschild import SchwarzschildMetric

__all__ = [
    "DEFAULT_MASS",
    "DEFAULT_RTOL",
    "DEFAULT_ATOL",
    "DEFAULT_MOMENTUM_ATOL",
    "IDX_X0",
    "IDX_R",
    "IDX_THETA",
    "IDX_PHI",
    "STATE_DIMENSION",
    "STATE_NAMES",
    "SpacetimeMetric",
    "SchwarzschildMetric",
    "hamiltonian_value",
    "hamiltonian_rhs",
]

__version__ = "0.1.0"
