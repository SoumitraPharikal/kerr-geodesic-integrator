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
    "SpacetimeMetric",
    "SchwarzschildMetric",
]

__version__ = "0.1.0"
