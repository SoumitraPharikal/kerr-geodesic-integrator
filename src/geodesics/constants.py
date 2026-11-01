"""Physical and numerical constants for the geodesic integrator.

Defines coordinate indices, default parameters, and default tolerances
consistent with Stage 0 v1.2 specification.
"""

from typing import Final, Tuple

# Coordinate index mappings for x^mu = (x0, r, theta, phi)
IDX_X0: Final[int] = 0
IDX_R: Final[int] = 1
IDX_THETA: Final[int] = 2
IDX_PHI: Final[int] = 3

COORDINATE_NAMES: Final[Tuple[str, ...]] = ("x0", "r", "theta", "phi")
SPACETIME_DIMENSION: Final[int] = 4

# Default physical mass in geometrized units (G = c = M = 1)
DEFAULT_MASS: Final[float] = 1.0

# Numerical tolerances and defaults
DEFAULT_RTOL: Final[float] = 1e-10
DEFAULT_ATOL: Final[float] = 1e-10
DEFAULT_MOMENTUM_ATOL: Final[float] = 1e-12

# Horizon buffer fraction: r_cut = 2M * (1 + HORIZON_BUFFER)
DEFAULT_HORIZON_BUFFER: Final[float] = 1e-3
