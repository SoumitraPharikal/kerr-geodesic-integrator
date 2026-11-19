# Kerr Geodesics Lab — Architecture Feasibility & Scientific API Audit
**Document ID:** KGL-ARCH-M0 / KGL-ARCH-M0B
**Baseline Release:** v1.0.0 (`062b20c80a689640637a2fcd003bdd921a7d4132`)
**Branch:** `feat/kerr-geodesics-lab`
**Date:** November 19, 2026
**Status:** Approved Architectural Reconnaissance & Milestone 0B Corrections

---

## 1. Executive Summary

This document establishes the architectural foundation and scientific API boundaries for **Kerr Geodesics Lab**, an interactive, extensible computational general relativity laboratory designed to simulate, visualize, and explore relativistic trajectories in curved spacetime.

The authoritative numerical physics engine is the released and verified `kerr-geodesics` package (v1.0.0), which integrates canonical Hamiltonian dynamics using an 8th-order adaptive Dormand–Prince (DOP853) solver with exact constraint tracking, high-order event root-finding, and scale-invariant Bardeen shadow construction.

All 4,412 automated tests in the regression suite pass with 100% success rate on the v1.0.0 release. Milestone 0B incorporates targeted corrections to initial-condition preset contracts, polar coordinate limitations, performance qualifications, hosting realities, and plotting architecture without altering any core physics code.

---

## 2. Release Verification & Git State

| Check | Specification | Verified Status | Evidence |
|---|---|---|---|
| Working Directory | `Kerr-Geodesic-Integrator` | Verified | Repository root (`Kerr-Geodesic-Integrator`) |
| Local HEAD Commit | `062b20c80a689640637a2fcd003bdd921a7d4132` | Verified | `git rev-parse HEAD` |
| Remote Master | `062b20c80a689640637a2fcd003bdd921a7d4132` | Verified | `git ls-remote origin refs/heads/master` |
| Release Tag | `v1.0.0` (Annotated) | Created Locally | Points to `062b20c8...`; not pushed |
| Development Branch | `feat/kerr-geodesics-lab` | Active | Branched directly from `062b20c8...` |
| Working Tree | Untracked Report Present | Verified | Core package files clean; `docs/lab/` is untracked |

### Git State Diagnostics & Anomaly Resolution
1. **Initial Tag-Creation Exit Code 1:**
   - In the earlier session, the command string:
     `git tag -a v1.0.0 <commit> -m "..."; git show v1.0.0 --no-patch; git rev-parse v1.0.0^{commit}`
     exited with code 1.
   - **Root Cause Established:** In PowerShell, unquoted `{commit}` was parsed as a script block, and PowerShell passed the base64-encoded command `YwBvAG0AbQBpAHQA` to Git, yielding `fatal: ambiguous argument 'YwBvAG0AbQBpAHQA'`. The tag itself was successfully created by the first command. Quoting the argument as `'v1.0.0^{commit}'` confirmed that the tag object points directly to `062b20c80a689640637a2fcd003bdd921a7d4132`.
2. **Working Tree Status Discrepancy:**
   - The initial report stated "Working Tree: Clean, 0 unstaged/untracked changes".
   - **Resolution:** The working tree was strictly clean prior to writing this audit document. The report file itself (`docs/lab/architecture_audit_milestone_0.md`) is untracked (`?? docs/lab/`) and is not ignored by `.gitignore` (`git check-ignore` returns code 1). Core source files in `src/geodesics/`, `tests/`, and `docs/report/` remain unmodified.

---

## 3. Existing Engine API Inventory

| Capability | Module & Function / Class | Tested? | Application Ready? | Limitations & API Constraints |
|---|---|---|---|---|
| **Schwarzschild Metric** | `geodesics.metrics.schwarzschild.SchwarzschildMetric` | Yes (100+ tests) | **Yes** | Domain $r > 2M, 0 < \theta < \pi$. Analytical $g_{\mu\nu}, g^{\mu\nu}, \partial_r g^{\mu\nu}, \partial_\theta g^{\mu\nu}$. Geometrized units ($G=c=1$). |
| **Kerr Metric** | `geodesics.metrics.kerr.KerrMetric` | Yes (250+ tests) | **Yes** | Domain $r > r_+, 0 < \theta < \pi, \|a\| \le M$. Analytical contravariant derivatives, $r_\pm, r_{\rm ISCO}^\pm, r_{\rm ph}^\pm, b_{\rm ph}^\pm, \Omega_{\rm ph}^\pm$. |
| **Metric Protocol** | `geodesics.metrics.base.SpacetimeMetric` | Yes | **Yes** | ABC requiring coordinate ordering $(x^0, r, \theta, \phi)$ with $x^0 = t$, signature $(-,+,+,+)$, and stationary/axial symmetries $\partial_0 g = \partial_\phi g = 0$. |
| **Null ICs (Schwarzschild)** | `geodesics.initial_conditions.schwarzschild_null_initial_state` | Yes | **Yes** | Solves $H(x, p) = 0$ for $p_r$ given $E > 0, L_z, p_\theta$. Scale-invariant turning point policy (`radicand_rtol=1e-12`). |
| **Geodesic ICs (Kerr)** | `geodesics.initial_conditions.kerr_geodesic_initial_state` | Yes | **Conditional** | Solves $H = -\mu^2/2$ for $p_r$ given $E, L_z, \mathcal{Q}, \mu$. Non-equatorial trajectories ($\mathcal{Q} > 0$) risk hitting polar singularity. |
| **Circular Orbit Presets** | `geodesics.initial_conditions.schwarzschild_circular_timelike_initial_state` | Yes | **Yes** | Timelike circular orbits $r > 6M$, exact $E(r), L(r), \Omega_\phi$. |
| **Photon Sphere Preset** | `geodesics.initial_conditions.schwarzschild_photon_sphere_initial_state` | Yes | **Yes** | Unperturbed circular null fixed point at $r = 3M, b = 3\sqrt{3}M, p_r = 0$. |
| **Perturbed Orbits** | `geodesics.initial_conditions.schwarzschild_perturbed_circular_timelike_initial_state` | Yes | **Yes** | Applies radial momentum kick $\delta p_r$ to circular orbit to induce epicyclic oscillations. |
| **Kerr Circular Presets** | `geodesics.initial_conditions.kerr_circular_timelike_initial_state` | Yes | **Yes** | Exact Boyer–Lindquist circular timelike orbit $r > r_{\rm ISCO}$. |
| **Kerr Photon Orbits** | `geodesics.initial_conditions.kerr_equatorial_photon_orbit_initial_state` | Yes | **Yes** | Equatorial prograde/retrograde photon orbits ($r_{\rm ph}^\pm, b_{\rm ph}^\pm$). |
| **Canonical Vector Field** | `geodesics.hamiltonian.hamiltonian_rhs` | Yes (50+ tests) | **Yes** | Evaluates $\dot{x}^\mu = g^{\mu\nu} p_\nu, \dot{p}_\mu = -\frac{1}{2} (\partial_\mu g^{\alpha\beta}) p_\alpha p_\beta$. State shape: (8,). |
| **Hamiltonian Value** | `geodesics.hamiltonian.hamiltonian_value` | Yes | **Yes** | Evaluates scalar $H(x, p) = \frac{1}{2} g^{\mu\nu} p_\mu p_\nu$. Preserved to $< 10^{-11}$. |
| **Conserved Quantities** | `geodesics.hamiltonian.conserved_energy`, `conserved_angular_momentum` | Yes | **Yes** | Extracts $E = -p_0, L_z = p_\phi$ from 4-momentum or 8-state vector. |
| **Carter Constant** | `geodesics.hamiltonian.carter_constant`, `carter_separation_constant` | Yes | **Yes** | Evaluates $\mathcal{Q}$ and $K$ using polar formula. Supports 1D state and 2D trajectory arrays. |
| **Carter Radial Check** | `geodesics.hamiltonian.carter_constant_radial`, `carter_separation_constant_radial` | Yes | **Yes** | Independent radial evaluation of $\mathcal{Q}$ without referencing $\theta$. Cross-verification diagnostic. |
| **ODE Integrator** | `geodesics.integrator.integrate_geodesic` | Yes (300+ tests) | **Yes** | DOP853 solver, adaptive step size, returns `GeodesicIntegrationResult`. Dense step storage or `t_eval`. |
| **Event Detection** | `geodesics.events.HorizonCutoffEvent`, `EscapeRadiusEvent`, `RadialTurningPointEvent` | Yes (120+ tests) | **Yes** | Decoupled event classes for `scipy.integrate.solve_ivp`. Terminal stopping and non-terminal monitoring. |
| **Scattering Analysis** | `geodesics.scattering.integrate_equatorial_photon`, `classify_equatorial_photon_trajectory` | Yes (100+ tests) | **Yes** | Inward propagation from $r_0 \gg M$, automated capture vs escape event handling. |
| **Shadow Boundary** | `geodesics.shadow.kerr_shadow_boundary` | Yes (80+ tests) | **Yes** | Analytical parameterization $(\xi(r), \eta(r))$, Brent root solver, cosine clustering. Returns `KerrShadowCurve`. |
| **Shadow Observables** | `geodesics.shadow.KerrShadowCurve.area`, `.centroid`, `.width`, `.height` | Yes | **Yes** | Discrete Shoelace formula with cyclic closure. Exact aspect ratios and retrograde shift. |

---

## 4. Reusable Simulation Presets & Catalogue Contract

The initial application must expose only physically valid, engine-constructible configurations via stable preset identifiers. It must not accept arbitrary raw 8D phase-space states.

### Preset Categorization & Contract Table

| Preset ID | Metric & Geodesic Type | Constructor Function | User-Adjustable Parameters | Fixed & Derived Parameters | Physical & Domain Restrictions | Test Evidence Reference | Catalogue Readiness |
|---|---|---|---|---|---|---|---|
| `schwarzschild_isco_circular` | `SchwarzschildMetric`, Timelike ($\mu=1$) | `schwarzschild_circular_timelike_initial_state` | `mass` ($M > 0$) | $r=6M, \theta=\pi/2, \phi_0=0, p_r=0, p_\theta=0$. Derived: $E=\sqrt{8/9}, L=2\sqrt{3}M$. | Fixed to equator; marginally stable ISCO orbit. | `test_schwarzschild_physical_orbits.py::TestSchwarzschildTimelikeCircularOrbits::test_timelike_circular_orbit_preservation_over_two_periods` | **Ready** |
| `schwarzschild_precession` | `SchwarzschildMetric`, Timelike ($\mu=1$) | `schwarzschild_perturbed_circular_timelike_initial_state` | `mass` ($M > 0$), `radius` ($r > 6M$), `delta_pr` ($|\delta p_r| < 0.1$) | $\theta=\pi/2, \phi_0=0, p_\theta=0$. Derived: circular $E(r), L(r)$ with kick $p_r = \delta p_r$. | $r > 6M$; bound state requires $E < 1$. | `test_schwarzschild_physical_orbits.py::TestSchwarzschildStabilityAnalysis::test_stable_orbit_at_8M_bounded_epicyclic_oscillation` | **Ready** |
| `schwarzschild_photon_sphere` | `SchwarzschildMetric`, Null ($\mu=0$) | `schwarzschild_photon_sphere_initial_state` | `mass` ($M > 0$), `energy` ($E > 0$) | $r=3M, \theta=\pi/2, \phi_0=0, p_r=0, p_\theta=0$. Derived: $L_z = \pm 3\sqrt{3}ME$. | Exact circular null fixed point. Demonstrates unperturbed circular orbit. | `test_schwarzschild_validation.py::TestSchwarzschildPhotonSphere::test_val_sch_04_photon_sphere_phase_space_fixed_point` | **Ready** |
| `kerr_equatorial_prograde_photon` | `KerrMetric`, Null ($\mu=0$) | `kerr_equatorial_photon_orbit_initial_state` | `mass` ($M > 0$), `spin` ($0 \le a < M$) | $\theta=\pi/2, \phi_0=0, p_r=0, p_\theta=0, \mathcal{Q}=0$. Derived: $r = r_{\rm ph}^+, b = b_{\rm ph}^+$. | Sub-extremal $a < M$. Co-rotating circular photon orbit. | `test_kerr_circular_photon_orbits.py::TestKerrCircularPhotonTrajectoryIntegration::test_circular_photon_orbit_two_revolution_integration` | **Ready** |
| `kerr_equatorial_retrograde_photon` | `KerrMetric`, Null ($\mu=0$) | `kerr_equatorial_photon_orbit_initial_state` | `mass` ($M > 0$), `spin` ($0 \le a \le M$) | $\theta=\pi/2, \phi_0=0, p_r=0, p_\theta=0, \mathcal{Q}=0$. Derived: $r = r_{\rm ph}^-, b = b_{\rm ph}^-$. | Exterior counter-rotating photon orbit ($r_{\rm ph}^- \in [3M, 4M]$). | `test_kerr_circular_photon_orbits.py::TestKerrCircularPhotonOrbitAnalyticFormulas::test_four_case_explicit_parity_combinations` | **Ready** |
| `kerr_circular_timelike` | `KerrMetric`, Timelike ($\mu=1$) | `kerr_circular_timelike_initial_state` | `mass` ($M > 0$), `spin` ($0 \le a < M$), `radius` ($r > r_{\rm ISCO}$) | $\theta=\pi/2, \phi_0=0, p_r=0, p_\theta=0, \mathcal{Q}=0$. Derived: $E(r), L_z(r)$. | $r > r_{\rm ISCO}(M, a)$ for orbital stability. | `test_kerr_physical_orbits.py::TestKerrCircularOrbitIntegration::test_circular_orbit_two_period_integration` | **Ready** |
| `kerr_equatorial_scattering` | `KerrMetric`, Null ($\mu=0$) | `equatorial_photon_initial_state` | `mass` ($M > 0$), `spin` ($|a| \le M$), `impact_parameter` ($b$), `r0` ($r_0 \gg M$) | $\theta=\pi/2, \phi_0=0, p_\theta=0, \mathcal{Q}=0$. Derived: $p_r$ from $H=0$, direction="inward". | Capture vs escape determined by $b \lessgtr b_{\rm crit}$. | `test_kerr_scattering.py::TestEquatorialPhotonTrajectoryIntegration::test_supercritical_scattering_classification` | **Ready** |
| `kerr_shadow_boundary` | `KerrMetric`, Null Envelope | `kerr_shadow_boundary` | `mass` ($M > 0$), `spin` ($|a| \le M$), `observer_inclination` ($\theta_o$) | Closed Bardeen polygon $(\alpha, \beta)$, $N=500$. Derived: $A, P, D_H, D_V$, centroid. | Analytical root-finding (Brent), not ODE integration. | `test_kerr_shadow.py::TestContourNormalsAndOrientation::test_general_kerr_contour_normals` | **Ready** (Separate endpoint) |
| `kerr_non_equatorial_orbit` | `KerrMetric`, Timelike/Null | `kerr_geodesic_initial_state` | `spin`, $\mathcal{Q} > 0$, $E, L_z$, $\theta_0$ | $p_r$ from $H = -\mu^2/2$. | Polar turning points near $\theta \to 0, \pi$ trigger coordinate singularities. | N/A (General constructor tested, but polar safety unguaranteed) | **Conditional** (Excluded from v1.0.0 GUI) |

---

## 5. Architecture Decision Record (ADR) — Corrected

### ADR-1: Backend Framework — FastAPI
- **Decision:** **Adopt** FastAPI as a thin, stateless application wrapper.
- **Performance Status Qualification:**
  - The previously cited 1–15 ms integration execution times are **unverified estimates**, not measured performance guarantees. No formal timing benchmark harness specifying hardware, CPU governor, operating system, repeated runs, mean, or percentiles is documented in the repository.
  - While single trajectory integrations over moderate affine intervals ($\Delta\lambda \le 50M$) are observed to be rapid in test runs, formal benchmarking remains an open task.
  - Declaring route handlers as synchronous `def` ensures Starlette dispatches them to an AnyIO worker threadpool, preventing event-loop stalling.

### ADR-2: Frontend Framework — Next.js (React + TypeScript)
- **Decision:** **Adopt** Next.js with App Router, configured for static HTML export capability (`output: 'export'`).
- **Rationale:** Decoupled static delivery of educational notes with zero JavaScript payload for static text, client-side hydration for simulation visualizers, and shareable URL query state.

### ADR-3: Scientific Data Visualization Strategy — Simplified
- **Decision:** **Adopt a Single 2D Vector Charting Layer (visx / SVG or D3-scale + SVG)** for the initial application release:
  - Because the API contract guarantees decimated output trajectories ($N \le 500$ points), rendering 2D trajectories and 1D diagnostic curves in SVG takes $< 1\text{ ms}$ on modern browsers with zero canvas blur, full responsive vector scaling, and direct Tailwind theme token integration.
  - Proposing three separate libraries (`visx`, `uPlot`, `Three.js`) introduces unnecessary dependency surface, maintenance overhead, and conflicting styling systems. `uPlot` is deferred (only justified for un-decimated streams $> 100{,}000$ points).
  - Three-dimensional WebGL rendering (Three.js / React Three Fiber) is **deferred to a future release**.
  - **Scientific Honesty Qualification:** When 3D visualizations are introduced, they must be explicitly labeled as **coordinate visualizations** (mapping coordinate $r, \theta, \phi$ to Euclidean Cartesian displays), **not** described as spatial embeddings or literal geometric representations of curved spacetime.

### ADR-4: Zero-Cost Sustainable Hosting Architecture — Corrected Reality Check
- **Provider Constraints (Verified November 2026):**
  - **Render Free Web Service** ([render.com/docs/free](https://render.com/docs/free)): 512 MB RAM, 0.1 shared vCPU, 750 free instance-hours/month. Spins down after 15 minutes of inactivity; waking introduces a $50\text{--}60\text{ second}$ cold start. Filesystem is strictly ephemeral.
  - **Hugging Face Spaces** ([huggingface.co/docs/hub/spaces-overview](https://huggingface.co/docs/hub/spaces-overview)): 2 vCPU, 16 GB RAM specs on `cpu-basic` must **not** be confused with an unconditional entitlement to deploy compute-backed Spaces freely under all personal accounts, as Hugging Face enforces account standing and resource limits.
  - **Static Hosting (Cloudflare Pages / Vercel Hobby):** Highly reliable, 0 cold starts, free global CDN for static frontend assets.
  - **Hosting Policy Warning:** All provider free-tier terms are subject to change and must be re-verified prior to deployment.
  - **Static Gallery Role:** The precomputed static gallery serves as a critical UX mitigation, allowing users to inspect curated benchmark orbits immediately without waiting for the backend to wake. However, **it does not make live custom-parameter simulations available while the backend is asleep**.

---

## 6. Proposed Scientific API Contract — Preset-Only v1.0.0

The initial public API restricts simulation execution to pre-validated, physically consistent presets. Arbitrary raw 8D phase-space states, arbitrary initial momenta, and custom solver tolerances (`rtol`, `atol`) are strictly excluded from the public request schema.

### Endpoints
1. `GET /health` — Service health, git commit hash, physics engine version (`1.0.0`).
2. `GET /api/v1/presets` — Catalog of available presets, metadata, and parameter schemas.
3. `POST /api/v1/simulations` — Stateless trajectory integration for a specified preset.
4. `POST /api/v1/shadows` — Analytical celestial shadow boundary construction.

### 1. Minimal Request Example (Tested Preset: `schwarzschild_precession`)
```json
POST /api/v1/simulations
Content-Type: application/json

{
  "preset_id": "schwarzschild_precession",
  "parameters": {
    "mass": 1.0,
    "radius": 8.0,
    "delta_pr": 0.001,
    "affine_span": 100.0
  }
}
```

### 2. Response Outline
```json
{
  "preset_id": "schwarzschild_precession",
  "config_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "status": "completed",
  "termination_reason": "End of affine parameter span",
  "solver_diagnostics": {
    "method": "DOP853",
    "nfev": 386,
    "rtol": 1e-10,
    "atol": 1e-10
  },
  "trajectory": {
    "lambdas": [0.0, 0.25, 0.5, "..."],
    "coordinates": {
      "t": [0.0, 0.78, "..."],
      "r": [8.0, 8.002, "..."],
      "theta": [1.5707963, 1.5707963, "..."],
      "phi": [0.0, 0.012, "..."]
    },
    "momenta": {
      "p_t": [-0.965, -0.965, "..."],
      "p_r": [0.001, 0.00098, "..."],
      "p_theta": [0.0, 0.0, "..."],
      "p_phi": [3.651, 3.651, "..."]
    }
  },
  "conserved_quantities": {
    "energy": 0.965,
    "angular_momentum": 3.651,
    "hamiltonian_drift_max": 2.1e-12
  },
  "triggered_events": [],
  "provenance": {
    "engine": "kerr-geodesics",
    "version": "1.0.0"
  }
}
```

### 3. Output Decimation & Sampling Architecture
To guarantee fast network serialization and responsive rendering while preserving physical fidelity, sampling is explicitly divided across three tiers:
1. **Engine Integration Output:** The adaptive DOP853 solver selects internal step sizes dynamically based on local spacetime curvature and tolerances, generating an arbitrary number of points (typically $300\text{--}2{,}000$).
2. **API Response Sampling:** The API decodes the engine result and produces a decimated array ($N \le 500$).
   - **Critical Feature Preservation:** Uniform subsampling alone does **not** guarantee preserving sharp turning points or boundary triggers. The API sampling logic must explicitly preserve:
     - The initial state ($\lambda_0$).
     - The exact terminal state ($\lambda_{\rm final}$).
     - All recorded event trigger coordinates (e.g. periapsis turning points from `RadialTurningPointEvent` or cutoff points from `HorizonCutoffEvent`).
     - Intermediate steps sampled uniformly across the remaining trajectory.
   - *Implementation Note:* Evaluating points via the engine's continuous dense polynomial output (`res.raw_solution.sol`) versus downsampling accepted steps is an architectural implementation decision requiring dedicated validation tests in Milestone 1.
3. **Frontend Display Sampling:** The browser receives the curated $N \le 500$ points and renders them directly as an SVG vector path. No secondary client-side decimation is required.

---

## 7. Design System Feasibility (Scientific Editorial)

The scientific-editorial design identity is preserved:
- **Palette:** Warm off-white paper (`#FBFBFA`), deep near-black text (`#18181B`), 1px hairline borders (`#E4E4E7`), and a restrained Oxford navy accent (`#1B365D`).
- **Typography:** Source Serif 4 for prose ($\approx 65\text{ch}$ measure), IBM Plex Sans for UI controls, JetBrains Mono with tabular numerals (`font-feature-settings: "tnum" 1`) for stable numerical coordinate tables.
- **Discipline:** Flat aesthetic, 2–4px corner radii, zero decorative gradients/neon, perceptually uniform colormaps (Viridis/Plasma), and full WCAG AA contrast compliance.

---

## 8. Known Engine Limitations & Polar Singularity Policy

### Analysis of the Boyer–Lindquist Polar Coordinate Singularity
1. **Mathematical Divergence:**
   In Boyer–Lindquist coordinates, contravariant metric components $g^{\phi\phi} \propto 1/\sin^2\theta$ and derivatives $\partial_\theta g^{\phi\phi} \propto \cos\theta/\sin^3\theta$ diverge at the coordinate poles $\theta = 0, \pi$.
2. **Engine Evaluation Path:**
   - Both `SchwarzschildMetric._validate_theta` and `KerrMetric._validate_theta` enforce:
     ```python
     if theta <= 0.0 or theta >= np.pi:
         raise ValueError(f"Polar angle theta must be strictly in the domain (0, pi), got theta = {theta}")
     ```
   - During numerical integration, `scipy.integrate.solve_ivp` evaluates the right-hand side vector field at 8 intermediate Runge–Kutta sub-stages per step.
   - If a trajectory approaches the axis, an intermediate trial step $y_n + c_i h$ can step into $\theta \le 0$ or $\theta \ge \pi$ **before** an accepted step is completed.
   - When this occurs, `_validate_theta` raises an unhandled `ValueError`, crashing the integration process. SciPy's event functions are only evaluated at the boundaries of accepted steps and **cannot prevent intermediate Runge–Kutta sub-stages from throwing exceptions**.
3. **Engine Capability Assessment:**
   The engine does **not** provide a coordinate regularization chart (e.g. Kerr–Schild coordinates) or a verified pole-crossing reflection mechanism.
4. **Conservative First-Version Policy:**
   - Restrict the initial application catalogue strictly to **equatorial orbits ($\theta \equiv \pi/2, p_\theta = 0$)** and **analytical shadow boundaries**.
   - By equatorial symmetry, trajectories initialized with $\theta = \pi/2$ and $p_\theta = 0$ have $\dot{\theta} \equiv 0$ and $\dot{p}_\theta \equiv 0$ identically for all $\lambda$, guaranteeing that the polar singularity is never approached.
   - **Explicitly exclude non-equatorial polar-crossing or high-inclination 3D trajectories** from the initial preset catalogue.

---

## 9. Test Verification Summary

- **Engine Code Integrity:** Zero modifications made to `src/geodesics/`, `tests/`, or `docs/report/`.
- **Regression Baseline:** The established v1.0.0 test suite passes **4,412 out of 4,412 tests** (0 failures, 0 skipped) under Python 3.13.5 and pytest 9.2.0. Because no engine or test source code was modified during this reconnaissance correction, a redundant test run was not executed.

---

## 10. Milestone 0B Corrections & Adjustments Summary

1. **Photon Sphere Fixed Point:** Corrected description of `schwarzschild_photon_sphere_initial_state` to reflect that it returns an exact unperturbed circular null fixed point. Clarified that Lyapunov instability governs perturbation growth, not spontaneous departure of unperturbed trajectories.
2. **Preset-Only Contract:** Replaced the open 8D phase-space simulation proposal with a strict preset-based catalog (7 Ready presets, 1 Ready shadow endpoint, 1 Conditional preset excluded).
3. **Polar Singularity Policy:** Established that intermediate solver sub-stages can trigger `ValueError` at $\theta \le 0, \ge \pi$, and restricted the initial GUI scope to equatorial trajectories.
4. **Performance Qualification:** Explicitly labeled the 1–15 ms integration claims as unverified estimates requiring formal benchmark instrumentation.
5. **Plotting Stack Simplification:** Replaced the 3-library stack with a single 2D vector charting layer (visx / SVG), deferring Three.js coordinate visualizations.
6. **Hosting Realities:** Documented Render 15-minute idle spin-down and Hugging Face compute policies; clarified the role of the precomputed static gallery.
7. **Git Audit State:** Documented the PowerShell argument-parsing cause of the initial tag exit code 1 and confirmed the untracked status of the audit report.

---

## 11. Next Milestone Recommendation (Milestone 1)

**Scope: Stateless Scientific API Adapter Layer (`src/geodesics/api/`)**
1. Define Pydantic v2 schemas for the 7 Ready presets.
2. Implement feature-preserving trajectory decimation (initial, final, event triggers).
3. Implement `GET /health`, `GET /api/v1/presets`, `POST /api/v1/simulations`, and `POST /api/v1/shadows` in a lightweight FastAPI service under optional dependencies `[project.optional-dependencies] api = [...]`.
4. Validate API endpoints using FastAPI `TestClient` against the underlying engine.
