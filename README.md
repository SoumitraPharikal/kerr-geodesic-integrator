# Kerr Geodesic Integrator

A rigorously validated, high-precision numerical framework for relativistic null geodesic integration, Hamiltonian constraint preservation, and celestial shadow construction in Schwarzschild and Kerr spacetimes.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11+-brightgreen.svg)](pyproject.toml)
[![Tests: 4,412 Passed](https://img.shields.io/badge/Tests-4%2C412%20Passed%20(100%25)-success.svg)](tests/)
[![Technical Report: 43 Pages](https://img.shields.io/badge/Technical%20Report-43%20Pages%20PDF-purple.svg)](docs/report/Kerr_Geodesic_Integrator_Report.pdf)

---

## Technical Report & Publication Deliverables

A comprehensive, peer-review-structured 43-page LaTeX technical report documents the theoretical foundations, numerical architecture, mathematical derivations, convergence proofs, and astrophysical benchmark results:

- **[Kerr_Geodesic_Integrator_Report.pdf](docs/report/Kerr_Geodesic_Integrator_Report.pdf)** — Complete, publication-ready compiled PDF deliverable.
- **[docs/report/](docs/report/)** — Complete editable LaTeX source project (master document, 15 modular chapters, BibTeX references, publication figures, and analysis scripts).

---

## Scientific Scope & Capabilities

The Kerr Geodesic Integrator provides a mathematically transparent and computationally robust platform for null ray tracing and astrophysical black hole imaging:

1. **Analytical Spacetime Metrics:**
   - **Schwarzschild Spacetime:** Exact contravariant metric $g^{\mu\nu}$ and spatial derivatives $\partial_i g^{\mu\nu}$ in spherical coordinates $(t, r, \theta, \phi)$.
   - **Kerr Spacetime:** Exact Boyer--Lindquist metric tensor and derivatives across all valid spin parameters $|a| \le M$. Includes dedicated handling for small spins ($|a| \ge 10^{-8}M$) and exact extremality ($|a| = M$).

2. **Canonical Hamiltonian Dynamics:**
   - Evaluates geodesic motion in 8-dimensional phase space $(x^\mu, p_\mu)$ via canonical Hamiltonian equations:
     $$\frac{dx^\mu}{d\lambda} = \frac{\partial \mathcal{H}}{\partial p_\mu} = g^{\mu\nu} p_\nu, \qquad \frac{dp_\mu}{d\lambda} = -\frac{\partial \mathcal{H}}{\partial x^\mu} = -\frac{1}{2} \frac{\partial g^{\alpha\beta}}{\partial x^\mu} p_\alpha p_\beta.$$
   - Maintains the null dispersion constraint $\mathcal{H} = \frac{1}{2} g^{\mu\nu} p_\mu p_\nu = 0$ with scale-invariant residuals $|\hat{\mathcal{H}}| \le 10^{-12}$.
   - Preserves conserved Carter constants of motion: energy $E = -p_t$, axial angular momentum $L_z = p_\phi$, and Carter constant $\mathcal{Q} = p_\theta^2 + \cos^2\theta \left( a^2 (E^2 - \mu^2) + \frac{L_z^2}{\sin^2\theta} \right)$.

3. **High-Order Adaptive Integration (DOP853):**
   - Embedded 8(5,3) Runge--Kutta--Fehlberg / Dormand--Prince ODE integrator with continuous local dense output.
   - Scale-invariant error controller preserving trajectory phase-space geometry over long affine propagation distances.
   - High-order event root-finding:
     - **Horizon Cutoff:** Halts integration when trajectories cross $r \le r_+ + \epsilon$.
     - **Periapsis Turning Points:** Resolves radial and polar turning points $dr/d\lambda = 0, d\theta/d\lambda = 0$ to machine epsilon without overshoot.
     - **Asymptotic Escape:** Terminates outbound trajectories crossing boundary spheres $r \ge r_{\rm esc}$.

4. **Astrophysical Null Scattering & Cross Sections:**
   - Validated against exact Chandrasekhar large-impact parameter deflection angles $\Delta\phi = \frac{4M}{b} + \frac{15\pi M^2}{4b^2} + \dots$ across asymptotic distances up to $10^5 M$.
   - Captures frame-dragging asymmetry in prograde vs. retrograde photon deflection.

5. **Celestial Bardeen Shadow Boundary Construction:**
   - Scale-invariant root isolation in terms of offset variable $u \equiv r - 3M$ to eliminate catastrophic floating-point cancellation.
   - Smooth cosine-clustered contour parameterization $u(\phi)$ resolving turning-point boundary layers.
   - **Near-Horizon Extreme Kerr (NHEK) Segment:** Constructs the exact prograde vertical boundary $\alpha = -2M/\sin\theta_o, |\beta| \le M\sqrt{3 - C(\theta_o)}$ for extremal black holes observed at supercritical inclinations $\theta_o > \theta_{\rm crit} \approx 47.06^\circ$.
   - **Exact-Polar Shadows ($\theta_o = 0^\circ$):** Exact concentric shadow circles of radius $R_{\rm pole} = \sqrt{\eta(r_p) + a^2}$.

6. **Quantitative Shadow Observables & Discretization Convergence:**
   - Computes mass-normalized shadow area ($A/M^2$), perimeter ($P/M$), horizontal and vertical diameters ($D_{\mathrm{H}}/M, D_{\mathrm{V}}/M$), and planar area centroid $(\bar{\alpha}/M, \bar{\beta}/M)$ via Green's theorem / Shoelace moments.
   - Rigorous demonstration of quadratic $\mathcal{O}(N^{-2})$ convergence of polygonal area and perimeter toward continuous limits, verified against the Euler--Maclaurin chord formula $P_N - P_{\rm cont} = -\frac{\pi^2}{6N^2} \int \kappa^2 \sigma^3 d\phi + \mathcal{O}(N^{-4})$.

---

## Installation

Requirements: Python $\ge 3.11$, NumPy $\ge 2.0.0$, SciPy $\ge 1.11.0$, pytest $\ge 8.0.0$.

Clone the repository and install in editable development mode:

```bash
git clone https://github.com/SoumitraPharikal/kerr-geodesic-integrator.git
cd kerr-geodesic-integrator
python -m pip install -e ".[dev]"
```

---

## Verification & Testing

The framework includes a comprehensive automated test suite consisting of **4,412 unit and regression tests**, validating mathematical identities, Hamiltonian constraints, metric signatures, scale invariance, scattering limits, shadow boundaries, and deliverable reproducibility:

```bash
pytest
```

All 4,412 tests pass with 100% success rate in under 60 seconds.

---

## Repository Structure

```text
kerr-geodesic-integrator/
├── README.md                           # Main project documentation and overview
├── LICENSE                             # MIT License
├── CITATION.cff                        # Academic citation metadata
├── pyproject.toml                      # Package build specifications and test config
├── .gitignore                          # Exclusions for caches, OS files, and LaTeX temp files
│
├── docs/                               # Theoretical documentation and technical report
│   ├── mathematical_foundations.md     # Detailed differential geometry & Carter constants
│   ├── numerical_methods.md            # DOP853 integration & event root-finding algorithms
│   └── report/                         # Final 43-page technical report project
│       ├── Kerr_Geodesic_Integrator_Report.pdf   # Compiled PDF deliverable
│       ├── main.tex                    # Master LaTeX document
│       ├── references.bib              # Verified academic citations
│       ├── README.md                   # Instructions for Overleaf and Linux compilation
│       ├── sections/                   # 15 modular report chapters
│       ├── figures/                    # 7 vector PDF and 7 high-resolution PNG figures
│       └── scripts/                    # Analysis, observables, and compilation scripts
│
├── src/                                # Core scientific Python package
│   └── geodesics/
│       ├── __init__.py                 # Public API exports
│       ├── constants.py                # Physical constants and numerical tolerances
│       ├── events.py                   # Event detection protocol and concrete root handlers
│       ├── hamiltonian.py              # 8D canonical Hamiltonian vector field
│       ├── initial_conditions.py       # Phase-space state preparation and Carter mapping
│       ├── integrator.py               # DOP853 adaptive ODE integrator
│       ├── scattering.py               # Large-impact parameter null scattering
│       ├── shadow.py                   # Bardeen screen coordinates & NHEK shadow boundary
│       └── metrics/
│           ├── __init__.py             # Metric exports
│           ├── base.py                 # Abstract SpacetimeMetric protocol
│           ├── kerr.py                 # Kerr Boyer-Lindquist metric and derivatives
│           └── schwarzschild.py        # Schwarzschild spherical metric and derivatives
│
├── tests/                              # Automated test suite (4,412 tests)
│   ├── test_events.py                  # Event root-finding and horizon cutoff tests
│   ├── test_hamiltonian.py             # Phase-space equations and constraint preservation
│   ├── test_initial_conditions.py      # Null vector alignment and Carter constant setup
│   ├── test_integrator.py              # DOP853 step adaptation and dense output
│   ├── test_kerr_circular_photon_orbits.py  # Equatorial and spherical photon orbits
│   ├── test_kerr_metric.py             # Metric tensor, inverse, and contravariant derivatives
│   ├── test_kerr_physical_orbits.py    # Timelike and null bound orbit dynamics
│   ├── test_kerr_scattering.py         # Asymptotic deflection and Chandrasekhar limits
│   ├── test_kerr_shadow.py             # Shadow contours, NHEK segments, and polar circles
│   ├── test_metrics.py                 # Basic metric protocol validation
│   ├── test_schwarzschild_physical_orbits.py # Schwarzschild precession and circular orbits
│   └── test_schwarzschild_validation.py      # Schwarzschild validation suite
│
├── output/                             # Generated scientific deliverables
│   └── shadow/                         # Stage 3E-B approved shadow figures and CSV datasets
│       ├── schwarzschild_shadow.pdf / .png
│       ├── kerr_shadow_a05.pdf / .png
│       ├── kerr_shadow_a09.pdf / .png
│       ├── kerr_shadow_extremal.pdf / .png
│       ├── kerr_shadow_inclination_comparison.pdf / .png
│       ├── exact_polar_shadow.pdf / .png
│       ├── shadow_contour_data.csv
│       └── shadow_generating_data.csv
│
└── tools/                              # Verification, deliverable generation, and audit scripts
    ├── generate_shadow_deliverables.py
    ├── independent_high_precision_audit.py
    └── precision_audit/
```

---

## Citation

If you use this framework or technical report in your research or educational materials, please cite:

```bibtex
@software{pharikal2026kerr,
  author       = {Pharikal, Soumitra},
  title        = {{Kerr Geodesic Integrator: A Rigorous Numerical Framework for Relativistic Geodesic Dynamics and Black Hole Shadow Construction}},
  year         = {2026},
  publisher    = {GitHub},
  journal      = {GitHub repository},
  howpublished = {\url{https://github.com/SoumitraPharikal/kerr-geodesic-integrator}}
}
```

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
