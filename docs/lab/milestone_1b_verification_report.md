# Kerr Geodesics Lab — Milestone 1B: Targeted Scientific Verification Report

**Author:** Scientific Verification Agent
**Date:** November 19, 2026
**Repository:** Kerr Geodesic Integrator
**Branch:** `feat/kerr-geodesics-lab`
**HEAD Commit:** `062b20c80a689640637a2fcd003bdd921a7d4132`
**Immutable Release Tag:** `v1.0.0` (points to `062b20c80a689640637a2fcd003bdd921a7d4132`)
**Baseline Test Count:** 4,412 passing tests
**New API Test Count:** 27 passing tests
**Total Test Count:** 4,439 passing tests (100% pass rate)
**Overall Decision:** **PASS**

---

## 1. Executive Summary

This report performs a narrow, evidence-based scientific verification of the Kerr Geodesics Lab Milestone 1 stateless API adapter. Four specific technical concerns raised in independent review were investigated:
1. Physical values and Hamiltonian constraints for the Schwarzschild precession preset.
2. The exact serialization contract and float sensitivity of the configuration hashing scheme.
3. The event preservation contract in relation to the strict 500-point trajectory limit.
4. The exact origin, severity, and resolution policy for the single external pytest deprecation warning.

Every investigation was grounded directly in source code inspection, exact mathematical derivations, and automated regression tests. Genuine defects and discrepancies have been resolved without altering the immutable v1.0.0 physics engine, release metadata, or git history.

---

## 2. Investigation 1: Schwarzschild Precession Physical Values

### Finding
The numerical discrepancy reported in Milestone 1 Report Section 11.1 ($E = 0.957427, L_z = 3.651484$) was a **documentation transcription artifact** copied from an early synthetic outline in `docs/lab/architecture_audit_milestone_0.md`.

The underlying physics engine (`src/geodesics/initial_conditions.py`) and API service dispatcher (`src/geodesics/api/service.py`) **already compute the exact physical values to machine precision**. The API adapter's execution and outputs are mathematically correct; only the illustrative JSON text in the Markdown report was inaccurate.

### Exact Source Files & Functions
- `src/geodesics/initial_conditions.py`:
  - `schwarzschild_circular_timelike_energy(r, mass)`
  - `schwarzschild_circular_timelike_angular_momentum(r, mass, prograde=True)`
  - `schwarzschild_perturbed_circular_timelike_initial_state(metric, r, delta_pr, prograde=True)`
- `src/geodesics/api/service.py`: `run_simulation(request)`
- `tests/test_api.py`: `test_schwarzschild_precession_exact_physical_values`

### Mathematical & Physical Derivation
For an unperturbed circular timelike geodesic in Schwarzschild spacetime with $M = 1.0$ at coordinate radius $r = 8.0$:
$$E_{\rm circ} = \frac{1 - 2M/r}{\sqrt{1 - 3M/r}} = \frac{1 - 2/8}{\sqrt{1 - 3/8}} = \frac{3/4}{\sqrt{5/8}} = \frac{3}{\sqrt{10}} \approx 0.9486832980505138$$
$$L_{\rm circ} = \frac{\sqrt{Mr}}{\sqrt{1 - 3M/r}} = \frac{\sqrt{8}}{\sqrt{5/8}} = \frac{8}{\sqrt{5}} \approx 3.5777087639996634$$

For a radial kick $\delta p_r = 0.001$, the metric coefficient is $f(r) = 1 - 2M/r = 0.75$. The exact perturbed energy derived from the timelike mass-shell Hamiltonian constraint $2H = -f^{-1} E_{\rm pert}^2 + f (\delta p_r)^2 + r^{-2} L_{\rm circ}^2 = -1$ (with particle rest mass $\mu = 1$) is:
$$E_{\rm pert} = \sqrt{E_{\rm circ}^2 + [f(r)\,\delta p_r]^2} = \sqrt{\frac{9}{10} + (0.75 \times 0.001)^2} = \sqrt{0.9000005625} \approx 0.9486835945139981$$

Evaluating the initial Hamiltonian invariant:
$$2H = -\frac{4}{3} \times 0.9000005625 + 0.75 \times 10^{-6} + \frac{1}{64} \times \frac{64}{5} = -1.20000075 + 0.00000075 + 0.20000000 = -1.0000000000000000$$
$$H(y_0) = -0.5 = -\frac{\mu^2}{2} \quad (\text{exact to machine precision } < 10^{-16})$$

### Empirical Engine and API Reproduction
Direct evaluation in Python 3.13 confirms:
- Initial state: $y_0 = (0.0, 8.0, \pi/2, 0.0, -0.948683594514, 0.001, 0.0, 3.577708764)$
- Hamiltonian value at $y_0$: $H(y_0) = -0.5000000000000000$
- API `conserved_quantities.energy`: $0.9486835945139981$
- API `conserved_quantities.angular_momentum`: $3.5777087639996634$
- API `conserved_quantities.hamiltonian_drift_max`: $2.22 \times 10^{-16}$

### Implemented Corrections
1. Added dedicated regression test `test_schwarzschild_precession_exact_physical_values` to `tests/test_api.py` asserting analytical agreement with $E_{\rm pert}$, $L_{\rm circ}$, and trajectory initial momenta within $10^{-12}$.
2. Corrected the sample response in `docs/lab/milestone_1_report.md` Section 11.1 to display the true numerical values computed by the engine.

---

## 3. Investigation 2: Configuration Hash Serialization Contract

### Finding
The Milestone 1 report claimed compliance with RFC 8785 while simultaneously applying an arbitrary 12-decimal place float rounding (`round(item, 12)`). This introduced two deficiencies:
1. **Mislabeling:** The scheme was not strictly RFC 8785 because Python's float serializer outputs integer-valued floats with `.0` (e.g. `1.0`), whereas RFC 8785 specifies ECMAScript Number syntax (e.g. `1`).
2. **Artificial Quantization:** Truncating floats at 12 decimal places discarded representable precision and created artificial collisions for parameter differences smaller than $10^{-12}$.

### Exact Source Files & Functions
- `src/geodesics/api/hashing.py`: `canonical_json_bytes()`, `compute_simulation_config_hash()`, `compute_shadow_config_hash()`
- `tests/test_api.py`: `test_config_hash_determinism_and_sensitivity()`

### Technical Resolution & Implementation
1. **Removed Arbitrary Quantization:** `round(item, 12)` was eliminated. All floating-point numbers are now preserved at full IEEE 754 64-bit double precision. Python's built-in float JSON serializer (using David Gay's dtoa shortest round-tripping decimal algorithm) guarantees exact, reproducible string representations without precision loss.
2. **Documented True Contract:** The hashing specification was updated to honestly describe its approach: **Deterministic Canonical JSON Serialization** (lexicographically sorted keys, minimal separators `','` and `':'`, exact IEEE 754 float representation, UTF-8 encoded, SHA-256 digested).
3. **Default Normalization Verified:** Pydantic schemas normalize defaults prior to serialization. It was verified that omitting default parameters (`{"preset_id": "schwarzschild_isco_circular"}`) and providing them explicitly (`{"preset_id": "schwarzschild_isco_circular", "parameters": {"mass": 1.0, "affine_span": 50.0}}`) produce identical hashes:
   `a0b3031849e2fb5058501e4247316f0790ad66d92bc2514a28548c6af2fefc8f`
4. **Machine-Precision Sensitivity:** It was verified that a parameter variation of only $10^{-14}$ ($r = 8.0$ vs $r = 8.0 + 10^{-14}$) produces distinct hashes:
   - Base ($r=8.0$): `30d74cea08590904e2301e4368518fa678a70d955c43f816c2542d475942b26f`
   - Perturbed ($r=8.0 + 10^{-14}$): `a9afc28de6ffc68946dcba834ef83734691faea9ca1048e777418ed7c459054e`

---

## 4. Investigation 3: Event Preservation and the 500-Point Limit

### Finding
The contract governing event retention across the `triggered_events` response container versus the decimated `trajectory` coordinate/momentum arrays needed formal clarification.

### Contract Specification
The API distinguishes between **event diagnostic records** and **trajectory visualization vertices**:

1. **`triggered_events: List[EventTriggerItem]` (Lossless Record):**
   - Retains **100% of all event triggers** detected during numerical integration by SciPy's root solver.
   - No event records are ever discarded, downsampled, or omitted from this list, regardless of whether $N_{\rm events}$ is 2 or 600.
   - Each item preserves the exact event name, root affine parameter $\lambda_{\rm ev}$, and exact spatial coordinates $(r, \theta, \phi)$.

2. **`trajectory: TrajectoryData` (Bounded Visualization Buffer):**
   - Strictly bounded to $N \le 500$ points to guarantee fast network transport and responsive frontend SVG vector rendering.
   - **Initial State ($\lambda_0$):** Unconditionally preserved at index 0.
   - **Terminal State ($\lambda_{\rm final}$):** Unconditionally preserved at index $-1$.
   - **Normal Regime ($N_{\rm events} \le 498$):** All exact event root vertices $(\lambda_{\rm ev}, y_{\rm ev})$ are injected directly into the trajectory array. If an event root coincides with an ODE step, the root evaluation takes precedence. Remaining slots are populated by uniformly spaced accepted solver steps.
   - **Event Overflow Regime ($N_{\rm events} > 498$):** When an extreme physical oscillation generates $> 498$ events within the affine span, all events remain intact in `triggered_events`. For the 500-point trajectory array, initial and final endpoints are preserved, and exactly 498 event vertices are sampled deterministically via uniform index spacing (`np.round(np.linspace(0, N_events - 1, 498)).astype(int)`).

### Tests Executed
1. **Normal Regime:** Live scattering test verifying that both the radial turning point and the escape radius event are present in both `triggered_events` and `trajectory.lambdas` with $|\Delta\lambda| < 10^{-11}$.
2. **Overflow Regime:** Artificial trajectory with 600 event triggers passed to `decimate_trajectory`. Verified that:
   - Output trajectory length is strictly equal to 500.
   - Initial state $\lambda = 0.0$ is preserved.
   - Final state $\lambda = 10.0$ is preserved.
   - Trajectory is strictly monotonic ($\Delta\lambda > 0$).
   - Exactly 498 event samples were selected deterministically.

---

## 5. Investigation 4: Pytest Warning Analysis

### Finding
The test run output showed:
```
====================== 4437 passed, 1 warning in 47.86s =======================
```

The single warning is:
```
<python-env>/Lib/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
  from starlette.testclient import TestClient as TestClient
```

### Origin & Severity Analysis
- **Origin:** Upstream third-party interaction between `starlette==1.10.0` and `fastapi==0.165.0`.
- **Mechanism:** In Starlette 1.10.0, `starlette/testclient.py` attempts to import `httpx2`. When `httpx2` is absent, it falls back to standard `httpx` (0.27.2) and emits `StarletteDeprecationWarning`.
- **Severity:** Completely harmless. All HTTP endpoints, request serialization, and response deserialization function with 100% reliability under `httpx`.
- **Resolution Policy:** As directed by the working rules, **broad warning suppression has not been applied**. The warning originates outside the project's codebase. When the FastAPI/Starlette ecosystem stabilizes its transition to `httpx2`, the project's optional `api` dependencies can be updated accordingly.

---

## 6. Investigation 5 (Milestone 1C): Event-State Completeness and Root Fidelity

### Finding
Inspection of the underlying physics engine confirmed that SciPy's event root-solver in `integrate_geodesic` (`src/geodesics/integrator.py`) evaluates and records the exact 8-dimensional phase-space state vector at each root:
$$y(\lambda_{\rm ev}) = (t, r, \theta, \phi, p_t, p_r, p_\theta, p_\phi)$$
In the previous API iteration, `EventTriggerItem` only serialized coordinate components $(r, \theta, \phi)$, omitting coordinate time $t$ and all four canonical momenta $(p_t, p_r, p_\theta, p_\phi)$.

### Completeness Across Supported Event Types
All three engine-supported event types produce exact 8-component state vectors at root crossings:
1. `HorizonCutoffEvent`: Evaluates $(t, r_+, \theta, \phi, p_t, p_r, p_\theta, p_\phi)$ at the cutoff boundary $r_{\rm cut} = r_+(1 + \epsilon)$.
2. `EscapeRadiusEvent`: Evaluates $(t, r_{\rm esc}, \theta, \phi, p_t, p_r, p_\theta, p_\phi)$ at the asymptotic escape boundary.
3. `RadialTurningPointEvent`: Evaluates $(t, r_{\rm turn}, \theta, \phi, p_t, 0, p_\theta, p_\phi)$ where radial momentum vanishes ($p_r = 0$).

### Implemented Serialization
`EventTriggerItem` in `src/geodesics/api/schemas.py` and `run_simulation` in `src/geodesics/api/service.py` were updated to serialize the complete state in dual form:
1. **Explicit Named Fields:** `t`, `r`, `theta`, `phi`, `p_t`, `p_r`, `p_theta`, `p_phi`.
2. **Canonical State Vector:** `state: List[float]` containing the exact 8-element float list in canonical ordering `[t, r, theta, phi, p_t, p_r, p_theta, p_phi]`.

### Root Evaluation Fidelity
Event affine locations $\lambda_{\rm ev}$ and event states $y(\lambda_{\rm ev})$ originate directly from the same SciPy root evaluation tuple `(t_ev, y_ev)` in `EventTriggerRecord`. No event states are interpolated, approximated, or reconstructed from nearby accepted integration steps.

### Verification Test
The dedicated test `test_event_complete_phase_space_state_and_exact_root` in `tests/test_api.py` verified:
- Exact agreement between API event states and direct engine root states to $< 10^{-14}$.
- Physical consistency: $p_r = 0$ ($< 10^{-15}$) at radial turning points, $p_t = -E = -1.0$, $p_\phi = L_z = 6.0$, $\theta = \pi/2$, and $p_\theta \approx 0$.
- Escape radius: $r = 50.0$, outward radial velocity ($p_r > 0$).

---

## 7. Comprehensive Verification Summary

### Regression Test Suite Results
```
====================== 4439 passed, 1 warning in 47.02s =======================
```
- **Pre-existing core tests:** 4,412 passed (100%).
- **API test suite (`tests/test_api.py`):** 27 passed (100%).
- **Total:** 4,439 passed, 0 failures, 0 errors.

### Git State Verification
- **Branch:** `feat/kerr-geodesics-lab`
- **HEAD Commit:** `062b20c80a689640637a2fcd003bdd921a7d4132`
- **Release Tag:** `v1.0.0` points to `062b20c80a689640637a2fcd003bdd921a7d4132` (untouched).
- **Staged Git Modifications:** None (`git diff --cached` is empty).

---

## 8. Decision

**PASS: Milestone 1 scientifically verified.**

All five verification areas (Schwarzschild precession exact physical values, machine-precision configuration hashing, event preservation and trajectory capping, harmless external warning identification, and complete event-state phase-space fidelity) have been verified with complete mathematical rigor and automated regression tests. The API adapter is production-ready for subsequent milestones.
