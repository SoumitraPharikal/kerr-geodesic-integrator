# Kerr Geodesic Integrator

A rigorously validated numerical framework for null geodesic integration in Schwarzschild and Kerr spacetimes.

## Scientific Objective

Develop an independently verified numerical integrator for photon trajectories in curved spacetime, beginning with static spherically symmetric black holes (Schwarzschild) and extending to stationary axisymmetric rotating black holes (Kerr). The project prioritizes mathematical transparency, numerical reliability, reproducible benchmarks, and defensible results.

## Current Project Status: Stage 1A

- **Scope:** Repository foundation and Schwarzschild metric core.
- **Implemented:**
  - Standard `src/` layout package structure.
  - Abstract spacetime metric protocol (`SpacetimeMetric`).
  - Analytical Schwarzschild metric tensor and exact spatial contravariant derivatives.
  - Level-1 automated unit test suite (`VAL-MET-01`, `VAL-MET-02`, and input validation).
- **Deferred:** Hamiltonian dynamical equations, geodesic ODE integrators, event handling, Kerr metric, and ray-tracing modules belong to subsequent stages.

## Mathematical Conventions

- **Units:** Geometrized units $G = c = M = 1$ internally.
- **Metric Signature:** $(-, +, +, +)$.
- **Coordinate Basis:** $x^\mu = (x^0, r, \theta, \phi)$ where $x^0 = ct$.
- **Coordinate Dimensions:** Length dimensions $[x^0] = [r] = [L]$ and dimensionless angles $[\theta] = [\phi] = 1$.
- **Affine Parameter Scaling:** $\tilde{\lambda} = \lambda \frac{E_0 c}{GM}$.

## Installation & Testing

Requirements: Python $\ge 3.11$, NumPy $\ge 2.0.0$, pytest $\ge 8.0.0$.

To install test dependencies and run the automated test suite:

```powershell
python -m pip install -e ".[dev]"
pytest
```

## Repository Structure

```text
kerr-geodesics/
├── README.md
├── LICENSE
├── CITATION.cff
├── pyproject.toml
├── .gitignore
│
├── docs/
│   ├── mathematical_foundations.md
│   └── numerical_methods.md
│
├── src/
│   └── geodesics/
│       ├── __init__.py
│       ├── constants.py
│       └── metrics/
│           ├── __init__.py
│           ├── base.py
│           └── schwarzschild.py
│
├── tests/
│   └── test_metrics.py
│
├── examples/
└── results/
```
