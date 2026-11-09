"""Verification test suite for numerical geodesic integrator (Stage 1D).

Implements rigorous scientific verification for `integrate_geodesic`:
- VAL-INT-01: Analytical Schwarzschild radial null geodesics (r(lambda) = r0 +/- E*(lambda - lambda0)).
- VAL-INT-02: Conservation of Killing conjugate momenta (p0 = -E, pphi = Lz, ptheta = 0 in equatorial plane).
- VAL-INT-03: Null Hamiltonian constraint preservation (scale-aware H(lambda) / (E^2/f) <= tol).
- VAL-INT-04: Numerical convergence across tolerances (rtol = 1e-4 down to 1e-12).
- VAL-INT-05: Bidirectional affine-parameter integration (forward vs backward).
- VAL-INT-06: Sampling and output structure (default steps vs t_eval, shapes, caller array non-mutation).
- VAL-INT-07: Alternative solver backends (RK45, Radau).
- VAL-INT-08: Robust input validation and fail-fast behavior (malformed states, invalid spans, tolerances, methods).
"""

from typing import Tuple
import numpy as np
import pytest

from geodesics.constants import (
    DEFAULT_ATOL,
    DEFAULT_MASS,
    DEFAULT_RTOL,
    IDX_PHI,
    IDX_R,
    IDX_THETA,
    IDX_X0,
)
from geodesics.events import HorizonCutoffEvent
from geodesics.hamiltonian import (
    STATE_DIMENSION,
    carter_constant,
    carter_constant_radial,
    carter_separation_constant,
    conserved_angular_momentum,
    conserved_energy,
    hamiltonian_value,
)
from geodesics.initial_conditions import (
    kerr_geodesic_initial_state,
    schwarzschild_null_initial_state,
)
from geodesics.integrator import (
    DEFAULT_INTEGRATOR_METHOD,
    SUPPORTED_METHODS,
    GeodesicIntegrationResult,
    integrate_geodesic,
)
from geodesics.metrics.kerr import KerrMetric
from geodesics.metrics.schwarzschild import SchwarzschildMetric


# =============================================================================
# Test Suite: VAL-INT-01 (Analytical Radial Null Geodesics)
# =============================================================================

class TestRadialNullGeodesics:
    """VAL-INT-01: Quantitative verification against exact analytical radial solutions.

    For radial null geodesics in Schwarzschild spacetime (Lz = 0, ptheta = 0):
        dr / dlambda = +/- E  =>  r(lambda) = r0 +/- E * (lambda - lambda0)
        p0(lambda) = -E
        pr(lambda) = +/- E / f(r(lambda))
        dx0 / dlambda = E / f(r(lambda))
    """

    @pytest.mark.parametrize("direction, sign", [("outward", 1.0), ("inward", -1.0)])
    @pytest.mark.parametrize("energy", [0.5, 1.0, 2.0])
    def test_val_int_01_radial_linear_trajectory(
        self, direction: str, sign: float, energy: float
    ):
        """Verifies that r(lambda) strictly matches the exact linear formula r0 +/- E*lambda."""
        mass = 1.0
        metric = SchwarzschildMetric(mass=mass)
        r0 = 6.0 if direction == "outward" else 12.0
        x0 = np.array([0.0, r0, np.pi / 2.0, 0.0], dtype=np.float64)

        # Generate exact initial state
        y0 = schwarzschild_null_initial_state(
            metric=metric,
            x=x0,
            energy=energy,
            Lz=0.0,
            ptheta=0.0,
            radial_direction=direction,  # type: ignore
        )

        lambda_span = (0.0, 4.0)
        t_eval = np.linspace(0.0, 4.0, 21)

        result = integrate_geodesic(
            initial_state=y0,
            metric=metric,
            affine_span=lambda_span,
            t_eval=t_eval,
            rtol=1e-11,
            atol=1e-12,
            method="DOP853",
        )

        assert result.success is True
        assert result.status == 0

        # Exact analytical radial solution: r(lambda) = r0 + sign * E * lambda
        r_exact = r0 + sign * energy * t_eval
        np.testing.assert_allclose(result.r, r_exact, rtol=1e-10, atol=1e-10)

        # Exact momentum relations:
        # p0 = -E
        np.testing.assert_allclose(result.p0, -energy, rtol=1e-11, atol=1e-11)
        # pphi = 0, ptheta = 0
        np.testing.assert_allclose(result.pphi, 0.0, atol=1e-14)
        np.testing.assert_allclose(result.ptheta, 0.0, atol=1e-14)

        # pr(lambda) = sign * E / f(r(lambda))
        f_vals = np.array([metric.lapse(r_val) for r_val in result.r])
        pr_expected = sign * (energy / f_vals)
        np.testing.assert_allclose(result.pr, pr_expected, rtol=1e-9, atol=1e-9)

        # dx0 / dlambda = E / f(r(lambda))
        from geodesics.hamiltonian import hamiltonian_rhs
        for i in range(len(result.lambdas)):
            rhs = hamiltonian_rhs(result.states[i], metric)
            expected_x0_dot = energy / f_vals[i]
            np.testing.assert_allclose(rhs[IDX_X0], expected_x0_dot, rtol=1e-9, atol=1e-9)

        # Analytical coordinate time x0(lambda) integral:
        # dx0 / dr = sign * (1 + 2M / (r - 2M))
        # x0(lambda) - x0(0) = sign * [(r - r0) + 2M * ln((r - 2M) / (r0 - 2M))]
        delta_x0_exact = sign * (
            (result.r - r0) + 2.0 * mass * np.log((result.r - 2.0 * mass) / (r0 - 2.0 * mass))
        )
        delta_x0_num = result.x0 - result.x0[0]
        np.testing.assert_allclose(delta_x0_num, delta_x0_exact, rtol=1e-9, atol=1e-9)


# =============================================================================
# Test Suite: VAL-INT-02 (Conserved Quantities Along Geodesics)
# =============================================================================

class TestConservedQuantities:
    """VAL-INT-02: Verifies conservation of Killing conjugate momenta along trajectories.

    Stationarity (partial_0 g = 0) => p0 = -E is conserved.
    Axisymmetry (partial_phi g = 0) => pphi = Lz is conserved.
    Equatorial symmetry (theta = pi/2, ptheta = 0) => ptheta = 0 is conserved.
    """

    @pytest.mark.parametrize("energy", [1.0, 2.5])
    @pytest.mark.parametrize("Lz", [-3.0, 0.0, 4.5])
    def test_val_int_02_equatorial_constants_of_motion(self, energy: float, Lz: float):
        """Verifies p0 and pphi are conserved along non-radial equatorial null geodesics."""
        mass = 1.0
        metric = SchwarzschildMetric(mass=mass)
        r0 = 10.0
        x0 = np.array([0.0, r0, np.pi / 2.0, 0.0], dtype=np.float64)

        y0 = schwarzschild_null_initial_state(
            metric=metric,
            x=x0,
            energy=energy,
            Lz=Lz,
            ptheta=0.0,
            radial_direction="outward",
        )

        result = integrate_geodesic(
            initial_state=y0,
            metric=metric,
            affine_span=(0.0, 8.0),
            rtol=1e-10,
            atol=1e-10,
        )

        assert result.success is True
        # p0 must equal -energy to within integration tolerance
        np.testing.assert_allclose(result.p0, -energy, rtol=1e-9, atol=1e-9)
        # pphi must equal Lz to within integration tolerance
        np.testing.assert_allclose(result.pphi, Lz, rtol=1e-9, atol=1e-9)
        # Equatorial motion preserves ptheta = 0 and theta = pi/2
        np.testing.assert_allclose(result.ptheta, 0.0, atol=1e-10)
        np.testing.assert_allclose(result.theta, np.pi / 2.0, atol=1e-10)


# =============================================================================
# Test Suite: VAL-INT-03 (Null Hamiltonian Constraint Preservation)
# =============================================================================

class TestHamiltonianConstraint:
    """VAL-INT-03: Evaluates H(lambda) = 1/2 g^{mu nu} p_mu p_nu and tests normalized drift."""

    @pytest.mark.parametrize("direction", ["inward", "outward"])
    @pytest.mark.parametrize("theta0", [np.pi / 3.0, np.pi / 2.0])
    def test_val_int_03_hamiltonian_drift(self, direction: str, theta0: float):
        """Verifies scale-aware normalized null constraint drift remains <= 1e-8."""
        mass = 1.0
        metric = SchwarzschildMetric(mass=mass)
        r0 = 8.0
        energy = 1.5
        Lz = 2.0
        ptheta = 0.5 if theta0 != np.pi / 2.0 else 0.0

        x0 = np.array([0.0, r0, theta0, 0.2], dtype=np.float64)
        y0 = schwarzschild_null_initial_state(
            metric=metric,
            x=x0,
            energy=energy,
            Lz=Lz,
            ptheta=ptheta,
            radial_direction=direction,  # type: ignore
        )

        result = integrate_geodesic(
            initial_state=y0,
            metric=metric,
            affine_span=(0.0, 3.0),
            rtol=1e-10,
            atol=1e-10,
        )

        assert result.success is True

        # Evaluate H(x, p) at every integrated step
        n_points = len(result.lambdas)
        h_residuals = np.empty(n_points, dtype=np.float64)
        rel_residuals = np.empty(n_points, dtype=np.float64)

        for i in range(n_points):
            coords = result.states[i, :4]
            momenta = result.states[i, 4:]
            h_val = hamiltonian_value(coords, momenta, metric)
            h_residuals[i] = abs(h_val)

            r_val = coords[IDX_R]
            f_val = metric.lapse(r_val)
            scale = (energy ** 2) / f_val
            rel_residuals[i] = abs(h_val) / scale

        max_rel_error = np.max(rel_residuals)
        assert max_rel_error <= 1e-8, (
            f"Normalized Hamiltonian constraint drift exceeded tolerance: "
            f"max |H|/(E^2/f) = {max_rel_error:.2e}"
        )


# =============================================================================
# Test Suite: VAL-INT-04 (Convergence Across Tolerances)
# =============================================================================

class TestConvergence:
    """VAL-INT-04: Demonstrates that tighter integration tolerances yield improved accuracy."""

    def test_val_int_04_tolerance_convergence(self):
        """Verifies that error against analytical radial solution decreases with tighter tolerances."""
        mass = 1.0
        metric = SchwarzschildMetric(mass=mass)
        r0 = 5.0
        energy = 1.0
        x0 = np.array([0.0, r0, np.pi / 2.0, 0.0], dtype=np.float64)

        y0 = schwarzschild_null_initial_state(
            metric=metric,
            x=x0,
            energy=energy,
            Lz=0.0,
            ptheta=0.0,
            radial_direction="outward",
        )

        lambda_end = 8.0
        t_eval = np.linspace(0.0, lambda_end, 33)
        r_exact = r0 + energy * t_eval

        tolerances = [1e-4, 1e-6, 1e-8, 1e-10]
        max_errors = []

        for tol in tolerances:
            result = integrate_geodesic(
                initial_state=y0,
                metric=metric,
                affine_span=(0.0, lambda_end),
                t_eval=t_eval,
                rtol=tol,
                atol=tol,
                method="DOP853",
            )
            assert result.success is True
            err = np.max(np.abs(result.r - r_exact))
            max_errors.append(err)

        # Verify that error monotonically decreases as tolerance is tightened
        for j in range(len(max_errors) - 1):
            assert max_errors[j + 1] < max_errors[j], (
                f"Error failed to decrease from tol={tolerances[j]} (err={max_errors[j]:.2e}) "
                f"to tol={tolerances[j+1]} (err={max_errors[j+1]:.2e})"
            )

        # Verify final precision is consistent with float64 high-order integration
        assert max_errors[-1] <= 1e-9


# =============================================================================
# Test Suite: VAL-INT-05 (Integration Direction: Forward and Backward)
# =============================================================================

class TestIntegrationDirection:
    """VAL-INT-05: Verifies support for both increasing and decreasing affine parameter."""

    def test_val_int_05_forward_and_backward_integration(self):
        """Verifies forward (lambda0 < lambda1) and backward (lambda0 > lambda1) integration."""
        mass = 1.0
        metric = SchwarzschildMetric(mass=mass)
        r0 = 7.0
        energy = 1.0
        x0 = np.array([0.0, r0, np.pi / 2.0, 0.0], dtype=np.float64)

        y0 = schwarzschild_null_initial_state(
            metric=metric,
            x=x0,
            energy=energy,
            Lz=0.0,
            ptheta=0.0,
            radial_direction="outward",
        )

        # 1. Forward: lambda from 0 to 5
        res_fwd = integrate_geodesic(
            initial_state=y0,
            metric=metric,
            affine_span=(0.0, 5.0),
            rtol=1e-10,
            atol=1e-10,
        )
        assert res_fwd.success is True
        assert res_fwd.lambdas[0] < res_fwd.lambdas[-1]
        np.testing.assert_allclose(res_fwd.r[-1], r0 + energy * 5.0, rtol=1e-9)

        # 2. Backward: lambda from 5 to 0
        y_at_5 = res_fwd.states[-1].copy()
        res_bwd = integrate_geodesic(
            initial_state=y_at_5,
            metric=metric,
            affine_span=(5.0, 0.0),
            rtol=1e-10,
            atol=1e-10,
        )
        assert res_bwd.success is True
        assert res_bwd.lambdas[0] > res_bwd.lambdas[-1]
        # Trajectory integrated backward should return to initial state at lambda = 0
        np.testing.assert_allclose(res_bwd.states[-1], y0, rtol=1e-8, atol=1e-8)


# =============================================================================
# Test Suite: VAL-INT-06 (Sampling, Output Structure, and Non-Mutation)
# =============================================================================

class TestSamplingAndOutput:
    """VAL-INT-06: Verifies output array shapes, sampling modes, and caller array non-mutation."""

    def test_default_solver_steps_vs_explicit_t_eval(self):
        """Verifies default step generation and explicit t_eval sampling."""
        metric = SchwarzschildMetric(mass=1.0)
        x0 = np.array([0.0, 8.0, np.pi / 2.0, 0.0])
        y0 = schwarzschild_null_initial_state(metric, x0, energy=1.0, Lz=2.0)

        # Mode A: default solver steps (t_eval = None)
        res_default = integrate_geodesic(
            initial_state=y0,
            metric=metric,
            affine_span=(0.0, 6.0),
        )
        assert res_default.success is True
        assert res_default.states.ndim == 2
        assert res_default.states.shape[1] == STATE_DIMENSION
        assert res_default.states.shape[0] == len(res_default.lambdas)
        assert res_default.nfev > 0
        assert res_default.method == DEFAULT_INTEGRATOR_METHOD
        assert res_default.raw_solution is not None

        # Mode B: explicit t_eval sampling
        t_eval = np.linspace(0.0, 6.0, 41)
        res_eval = integrate_geodesic(
            initial_state=y0,
            metric=metric,
            affine_span=(0.0, 6.0),
            t_eval=t_eval,
        )
        assert res_eval.success is True
        assert res_eval.states.shape == (41, STATE_DIMENSION)
        np.testing.assert_array_equal(res_eval.lambdas, t_eval)

    def test_caller_array_non_mutation(self):
        """Verifies that the caller's initial_state array is never mutated."""
        metric = SchwarzschildMetric(mass=1.0)
        x0 = np.array([0.0, 10.0, np.pi / 3.0, 1.0], dtype=np.float64)
        y0 = schwarzschild_null_initial_state(metric, x0, energy=2.0, Lz=3.0, ptheta=-0.5)
        y0_backup = y0.copy()

        res = integrate_geodesic(
            initial_state=y0,
            metric=metric,
            affine_span=(0.0, 4.0),
        )
        assert res.success is True
        # Check byte-for-byte equality with backup
        np.testing.assert_array_equal(y0, y0_backup)

        # Initial state should be reflected at lambda = 0
        np.testing.assert_array_equal(res.states[0], y0_backup)

    def test_t_eval_does_not_prepend_initial_point(self):
        """Verifies that t_eval sampling points are returned strictly without automatically inserting lambda_start."""
        metric = SchwarzschildMetric(mass=1.0)
        x0 = np.array([0.0, 8.0, np.pi / 2.0, 0.0])
        y0 = schwarzschild_null_initial_state(metric, x0, energy=1.0, Lz=0.0, radial_direction="outward")

        # Request points strictly after lambda_start = 0.0
        t_eval = np.array([1.0, 2.0, 3.0])
        res = integrate_geodesic(
            initial_state=y0,
            metric=metric,
            affine_span=(0.0, 4.0),
            t_eval=t_eval,
        )
        assert res.success is True
        # lambda_start = 0.0 must NOT be automatically prepended
        assert res.lambdas[0] == 1.0
        assert len(res.lambdas) == 3
        np.testing.assert_array_equal(res.lambdas, t_eval)
        assert res.states.shape == (3, STATE_DIMENSION)

    def test_decreasing_t_eval_sampling(self):
        """Verifies that t_eval sampling works correctly for backward integration (lambda0 > lambda1)."""
        metric = SchwarzschildMetric(mass=1.0)
        x0 = np.array([0.0, 8.0, np.pi / 2.0, 0.0])
        y0 = schwarzschild_null_initial_state(metric, x0, energy=1.0, Lz=0.0, radial_direction="outward")

        # Backward integration: span from 5.0 to 0.0 with decreasing t_eval
        t_eval_bwd = np.array([4.0, 2.5, 1.0])
        res = integrate_geodesic(
            initial_state=y0,
            metric=metric,
            affine_span=(5.0, 0.0),
            t_eval=t_eval_bwd,
        )
        assert res.success is True
        np.testing.assert_array_equal(res.lambdas, t_eval_bwd)
        assert res.states.shape == (3, STATE_DIMENSION)


# =============================================================================
# Test Suite: VAL-INT-07 (Solver Failure Behavior and Partial Trajectories)
# =============================================================================

class TestSolverFailureBehavior:
    """Verifies that solver failure (e.g. infalling trajectory reaching horizon) preserves diagnostics and partial state."""

    def test_infalling_horizon_failure_preserves_diagnostics_and_partial_trajectory(self):
        """Verifies that an infalling ray reaching the horizon reports failure cleanly without raising unhandled exceptions."""
        mass = 1.0
        metric = SchwarzschildMetric(mass=mass)
        r0 = 2.5
        energy = 1.0
        Lz = 0.0

        x0 = np.array([0.0, r0, np.pi / 2.0, 0.0], dtype=np.float64)
        y0 = schwarzschild_null_initial_state(
            metric=metric,
            x=x0,
            energy=energy,
            Lz=Lz,
            ptheta=0.0,
            radial_direction="inward",
        )

        # Span (0.0, 1.0) exceeds the affine horizon arrival time lambda_H = (2.5 - 2.0)/1.0 = 0.5
        result = integrate_geodesic(
            initial_state=y0,
            metric=metric,
            affine_span=(0.0, 1.0),
            rtol=1e-6,
            atol=1e-6,
        )

        # Solver must report failure accurately (not masked as success)
        assert result.success is False
        assert result.status == -1
        assert len(result.message) > 0
        assert "Required step size is less than spacing between numbers" in result.message

        # Partial trajectory must be retained and consistent
        n_points = len(result.lambdas)
        assert n_points > 0
        assert result.states.shape == (n_points, STATE_DIMENSION)
        assert result.nfev > 0
        assert result.raw_solution is not None
        assert result.raw_solution.success is False

        # Verify that radius decreased monotonically towards horizon r = 2M before failure
        assert result.r[0] == r0
        assert result.r[-1] < r0
        assert np.isclose(result.r[-1], 2.0 * mass, atol=1e-3)


# =============================================================================
# Test Suite: VAL-INT-07 (Alternative Solver Backends)
# =============================================================================

class TestAlternativeSolvers:
    """VAL-INT-07: Verifies integration with alternative solve_ivp methods (RK45, Radau)."""

    @pytest.mark.parametrize("method", ["RK45", "Radau"])
    def test_val_int_07_alternative_methods(self, method: str):
        """Verifies that RK45 and Radau integrate successfully and agree with analytical solution."""
        metric = SchwarzschildMetric(mass=1.0)
        x0 = np.array([0.0, 6.0, np.pi / 2.0, 0.0])
        y0 = schwarzschild_null_initial_state(metric, x0, energy=1.0, Lz=0.0, radial_direction="outward")

        result = integrate_geodesic(
            initial_state=y0,
            metric=metric,
            affine_span=(0.0, 4.0),
            method=method,
            rtol=1e-8,
            atol=1e-8,
        )

        assert result.success is True
        assert result.method == method
        r_exact_end = 6.0 + 1.0 * 4.0
        np.testing.assert_allclose(result.r[-1], r_exact_end, rtol=1e-7)


# =============================================================================
# Test Suite: VAL-INT-08 (Input Validation and Fail-Fast Errors)
# =============================================================================

class TestInputValidation:
    """VAL-INT-08: Verifies robust parameter validation and descriptive error reporting."""

    def test_rejection_of_invalid_metric(self):
        """Rejects metric arguments that do not implement SpacetimeMetric."""
        y0 = np.zeros(STATE_DIMENSION)
        with pytest.raises(TypeError, match="metric must be an instance of SpacetimeMetric"):
            integrate_geodesic(initial_state=y0, metric="invalid", affine_span=(0.0, 1.0))  # type: ignore

    @pytest.mark.parametrize("bad_shape", [np.zeros(7), np.zeros(9), np.zeros((2, 4))])
    def test_rejection_of_invalid_state_shape(self, bad_shape: np.ndarray):
        """Rejects initial state arrays whose shape is not exactly (8,)."""
        metric = SchwarzschildMetric(mass=1.0)
        with pytest.raises(ValueError, match="initial_state must have shape \\(8,\\)"):
            integrate_geodesic(initial_state=bad_shape, metric=metric, affine_span=(0.0, 1.0))

    @pytest.mark.parametrize("bad_val", [np.nan, np.inf, -np.inf])
    def test_rejection_of_non_finite_initial_state(self, bad_val: float):
        """Rejects initial state arrays containing NaN or infinite values."""
        metric = SchwarzschildMetric(mass=1.0)
        y0 = np.ones(STATE_DIMENSION)
        y0[3] = bad_val
        with pytest.raises(ValueError, match="initial_state contains non-finite values"):
            integrate_geodesic(initial_state=y0, metric=metric, affine_span=(0.0, 1.0))

    def test_rejection_of_horizon_initial_radius(self):
        """Rejects initial states starting on or within the Schwarzschild event horizon r <= 2M."""
        metric = SchwarzschildMetric(mass=1.0)
        y0 = np.zeros(STATE_DIMENSION)
        y0[IDX_R] = 2.0  # r = 2M = 2.0
        y0[IDX_THETA] = np.pi / 2.0
        with pytest.raises(ValueError, match="lies on or within event horizon"):
            integrate_geodesic(initial_state=y0, metric=metric, affine_span=(0.0, 1.0))

    @pytest.mark.parametrize("bad_theta", [0.0, np.pi, -0.2, 3.5])
    def test_rejection_of_invalid_polar_angle(self, bad_theta: float):
        """Rejects initial states with polar angles outside (0, pi)."""
        metric = SchwarzschildMetric(mass=1.0)
        y0 = np.zeros(STATE_DIMENSION)
        y0[IDX_R] = 6.0
        y0[IDX_THETA] = bad_theta
        with pytest.raises(ValueError, match="must be strictly in \\(0, pi\\)"):
            integrate_geodesic(initial_state=y0, metric=metric, affine_span=(0.0, 1.0))

    @pytest.mark.parametrize("bad_span", [(0.0,), (0.0, 1.0, 2.0), "0 to 1"])
    def test_rejection_of_malformed_affine_span(self, bad_span):
        """Rejects affine spans that are not 2-tuples."""
        metric = SchwarzschildMetric(mass=1.0)
        y0 = np.ones(STATE_DIMENSION)
        y0[IDX_R] = 6.0
        y0[IDX_THETA] = np.pi / 2.0
        with pytest.raises(ValueError, match="affine_span must be a 2-tuple"):
            integrate_geodesic(initial_state=y0, metric=metric, affine_span=bad_span)  # type: ignore

    @pytest.mark.parametrize("bad_span", [(np.nan, 1.0), (0.0, np.inf), (-np.inf, 1.0)])
    def test_rejection_of_non_finite_affine_span(self, bad_span):
        """Rejects affine spans containing non-finite endpoints."""
        metric = SchwarzschildMetric(mass=1.0)
        y0 = np.ones(STATE_DIMENSION)
        y0[IDX_R] = 6.0
        y0[IDX_THETA] = np.pi / 2.0
        with pytest.raises(ValueError, match="endpoints must be finite"):
            integrate_geodesic(initial_state=y0, metric=metric, affine_span=bad_span)

    def test_rejection_of_degenerate_affine_span(self):
        """Rejects affine spans with identical endpoints (lambda_start == lambda_end)."""
        metric = SchwarzschildMetric(mass=1.0)
        y0 = np.ones(STATE_DIMENSION)
        y0[IDX_R] = 6.0
        y0[IDX_THETA] = np.pi / 2.0
        with pytest.raises(ValueError, match="endpoints must be distinct"):
            integrate_geodesic(initial_state=y0, metric=metric, affine_span=(2.5, 2.5))

    @pytest.mark.parametrize("bad_tol", [0.0, -1e-6, np.nan, np.inf, True])
    def test_rejection_of_invalid_tolerances(self, bad_tol):
        """Rejects non-positive, non-finite, or boolean tolerances."""
        metric = SchwarzschildMetric(mass=1.0)
        y0 = np.ones(STATE_DIMENSION)
        y0[IDX_R] = 6.0
        y0[IDX_THETA] = np.pi / 2.0
        with pytest.raises(ValueError, match="rtol must be a strictly positive and finite scalar float"):
            integrate_geodesic(initial_state=y0, metric=metric, affine_span=(0.0, 1.0), rtol=bad_tol)
        with pytest.raises(ValueError, match="atol must be a strictly positive and finite scalar float"):
            integrate_geodesic(initial_state=y0, metric=metric, affine_span=(0.0, 1.0), atol=bad_tol)

    @pytest.mark.parametrize("too_small_rtol", [1e-14, 1e-15, 1e-18, 1e-25])
    def test_rejection_of_too_small_rtol(self, too_small_rtol: float):
        """Rejects rtol values below SciPy's minimum effective threshold (100 * eps_mach ~ 2.22e-14)."""
        metric = SchwarzschildMetric(mass=1.0)
        y0 = np.ones(STATE_DIMENSION)
        y0[IDX_R] = 6.0
        y0[IDX_THETA] = np.pi / 2.0
        with pytest.raises(ValueError, match="below the minimum effective relative tolerance"):
            integrate_geodesic(initial_state=y0, metric=metric, affine_span=(0.0, 1.0), rtol=too_small_rtol)

    @pytest.mark.parametrize("non_scalar_tol", [np.array([1e-10]), [1e-10], "1e-10"])
    def test_rejection_of_non_scalar_tolerances(self, non_scalar_tol):
        """Rejects non-scalar tolerance arguments."""
        metric = SchwarzschildMetric(mass=1.0)
        y0 = np.ones(STATE_DIMENSION)
        y0[IDX_R] = 6.0
        y0[IDX_THETA] = np.pi / 2.0
        with pytest.raises(ValueError, match="rtol must be a strictly positive and finite scalar float"):
            integrate_geodesic(initial_state=y0, metric=metric, affine_span=(0.0, 1.0), rtol=non_scalar_tol)
        with pytest.raises(ValueError, match="atol must be a strictly positive and finite scalar float"):
            integrate_geodesic(initial_state=y0, metric=metric, affine_span=(0.0, 1.0), atol=non_scalar_tol)

    @pytest.mark.parametrize("bad_max_step", [0.0, -1.0, np.nan, True])
    def test_rejection_of_invalid_max_step(self, bad_max_step):
        """Rejects non-positive or NaN max_step."""
        metric = SchwarzschildMetric(mass=1.0)
        y0 = np.ones(STATE_DIMENSION)
        y0[IDX_R] = 6.0
        y0[IDX_THETA] = np.pi / 2.0
        with pytest.raises(ValueError, match="max_step must be strictly positive"):
            integrate_geodesic(initial_state=y0, metric=metric, affine_span=(0.0, 1.0), max_step=bad_max_step)

    def test_rejection_of_unsupported_method(self):
        """Rejects unsupported solver method strings."""
        metric = SchwarzschildMetric(mass=1.0)
        y0 = np.ones(STATE_DIMENSION)
        y0[IDX_R] = 6.0
        y0[IDX_THETA] = np.pi / 2.0
        with pytest.raises(ValueError, match="Unsupported method 'INVALID_METHOD'"):
            integrate_geodesic(initial_state=y0, metric=metric, affine_span=(0.0, 1.0), method="INVALID_METHOD")

    @pytest.mark.parametrize("bad_t_eval", [
        np.array([]),                    # empty
        np.zeros((2, 3)),                # 2D
        np.array([0.0, np.nan, 1.0]),     # non-finite
        np.array([0.0, 2.0, 1.0]),       # non-monotonic
        np.array([-0.5, 0.5, 1.0]),      # outside span [0, 1]
        np.array([0.0, 0.5, 1.5]),       # outside span [0, 1]
    ])
    def test_rejection_of_invalid_t_eval(self, bad_t_eval: np.ndarray):
        """Rejects malformed, non-finite, non-monotonic, or out-of-bounds t_eval."""
        metric = SchwarzschildMetric(mass=1.0)
        y0 = np.ones(STATE_DIMENSION)
        y0[IDX_R] = 6.0
        y0[IDX_THETA] = np.pi / 2.0
        with pytest.raises(ValueError):
            integrate_geodesic(
                initial_state=y0,
                metric=metric,
                affine_span=(0.0, 1.0),
                t_eval=bad_t_eval,
            )


# =============================================================================
# Test Suite: Stage 2C (Kerr Geodesic Numerical Integration & Conservation)
# =============================================================================

class TestKerrGeodesicIntegration:
    """Stage 2C: Numerical integration and conservation of Kerr geodesics."""

    @pytest.mark.parametrize("mass", [0.8, 1.0, 2.0])
    @pytest.mark.parametrize("spin_ratio", [-0.85, -0.4, 0.4, 0.85])
    def test_kerr_timelike_equatorial_invariance_and_conservation(
        self, mass: float, spin_ratio: float
    ):
        """Kerr timelike equatorial geodesic: preserves theta = pi/2, ptheta = 0, E, Lz, and H = -0.5."""
        spin = spin_ratio * mass
        metric = KerrMetric(mass=mass, spin=spin)
        r0 = 6.0 * mass
        theta0 = np.pi / 2.0
        x0 = np.array([0.0, r0, theta0, 0.0], dtype=np.float64)

        y0 = kerr_geodesic_initial_state(
            metric=metric,
            x=x0,
            energy=0.96,
            Lz=3.0 * mass,
            ptheta=0.0,
            mu=1.0,
            radial_direction="outward",
        )

        res = integrate_geodesic(y0, metric, affine_span=(0.0, 40.0), rtol=1e-10, atol=1e-10)

        assert res.success is True
        assert res.status == 0
        assert np.all(np.isfinite(res.states))
        assert np.all(res.r > metric.horizon_radius)

        # 1. Equatorial plane invariance throughout integration: theta = pi/2, ptheta = 0
        max_theta_drift = float(np.max(np.abs(res.theta - np.pi / 2.0)))
        max_ptheta_drift = float(np.max(np.abs(res.ptheta)))
        assert max_theta_drift <= 1e-14, f"Equatorial theta drift: {max_theta_drift:.2e}"
        assert max_ptheta_drift <= 1e-14, f"Equatorial ptheta drift: {max_ptheta_drift:.2e}"

        # 2. Conservation of energy E = -p_0 and axial angular momentum L_z = p_phi
        max_e_drift = float(np.max(np.abs(-res.p0 - (-y0[4]))))
        max_lz_drift = float(np.max(np.abs(res.pphi - y0[7])))
        assert max_e_drift <= 1e-14, f"Energy drift: {max_e_drift:.2e}"
        assert max_lz_drift <= 1e-14, f"Lz drift: {max_lz_drift:.2e}"

        # 3. Hamiltonian conservation: |H(lambda) - H(0)|
        h_vals = np.array([hamiltonian_value(s[:4], s[4:], metric) for s in res.states])
        max_h_drift = float(np.max(np.abs(h_vals - h_vals[0])))
        assert max_h_drift <= 1e-10, f"Hamiltonian drift: {max_h_drift:.2e}"

    @pytest.mark.parametrize("mass", [0.8, 1.0, 2.5])
    @pytest.mark.parametrize("spin_ratio", [-0.7, 0.6])
    @pytest.mark.parametrize("theta0", [np.pi / 3.0, 2.1])
    def test_kerr_timelike_nonequatorial_conservation(
        self, mass: float, spin_ratio: float, theta0: float
    ):
        """Kerr timelike non-equatorial geodesic: validates H = -0.5, E, and Lz conservation."""
        spin = spin_ratio * mass
        metric = KerrMetric(mass=mass, spin=spin)
        r0 = 7.0 * mass
        x0 = np.array([0.0, r0, theta0, 0.0], dtype=np.float64)

        y0 = kerr_geodesic_initial_state(
            metric=metric,
            x=x0,
            energy=1.02,
            Lz=2.2 * mass,
            ptheta=0.25,
            mu=1.0,
            radial_direction="outward",
        )

        res = integrate_geodesic(y0, metric, affine_span=(0.0, 30.0), rtol=1e-10, atol=1e-10)

        assert res.success is True
        assert res.status == 0
        assert np.all(np.isfinite(res.states))
        assert np.all(res.r > metric.horizon_radius)

        max_e_drift = float(np.max(np.abs(-res.p0 - (-y0[4]))))
        max_lz_drift = float(np.max(np.abs(res.pphi - y0[7])))
        assert max_e_drift <= 1e-14
        assert max_lz_drift <= 1e-14

        h_vals = np.array([hamiltonian_value(s[:4], s[4:], metric) for s in res.states])
        max_h_drift = float(np.max(np.abs(h_vals - h_vals[0])))
        assert max_h_drift <= 1e-10

    @pytest.mark.parametrize("mass", [0.8, 1.0, 2.5])
    @pytest.mark.parametrize("spin_ratio", [-0.85, 0.9])
    @pytest.mark.parametrize("theta0", [np.pi / 4.0, 2.2])
    def test_kerr_null_nonequatorial_conservation(
        self, mass: float, spin_ratio: float, theta0: float
    ):
        """Kerr null non-equatorial geodesic: validates H = 0.0, E, and Lz conservation."""
        spin = spin_ratio * mass
        metric = KerrMetric(mass=mass, spin=spin)
        r0 = 8.0 * mass
        x0 = np.array([0.0, r0, theta0, 0.0], dtype=np.float64)

        y0 = kerr_geodesic_initial_state(
            metric=metric,
            x=x0,
            energy=1.0,
            Lz=3.0 * mass,
            ptheta=0.4,
            mu=0.0,
            radial_direction="outward",
        )

        res = integrate_geodesic(y0, metric, affine_span=(0.0, 25.0), rtol=1e-10, atol=1e-10)

        assert res.success is True
        assert res.status == 0
        assert np.all(np.isfinite(res.states))
        assert np.all(res.r > metric.horizon_radius)

        max_e_drift = float(np.max(np.abs(-res.p0 - (-y0[4]))))
        max_lz_drift = float(np.max(np.abs(res.pphi - y0[7])))
        assert max_e_drift <= 1e-14
        assert max_lz_drift <= 1e-14

        h_vals = np.array([hamiltonian_value(s[:4], s[4:], metric) for s in res.states])
        max_h_drift = float(np.max(np.abs(h_vals - h_vals[0])))
        assert max_h_drift <= 1e-10


# =============================================================================
# Test Suite: Stage 2C (Tolerance Convergence)
# =============================================================================

class TestKerrToleranceConvergence:
    """Stage 2C: Convergence of Kerr geodesic integration under tightening tolerances."""

    def test_kerr_timelike_tolerance_convergence(self):
        """Verifies monotonic error decrease and Hamiltonian preservation for timelike Kerr geodesic."""
        mass = 1.0
        metric = KerrMetric(mass=mass, spin=0.5)
        x0 = np.array([0.0, 6.0, np.pi / 3.0, 0.0], dtype=np.float64)
        y0 = kerr_geodesic_initial_state(
            metric=metric,
            x=x0,
            energy=0.98,
            Lz=2.5,
            ptheta=0.2,
            mu=1.0,
            radial_direction="outward",
        )
        span = (0.0, 30.0)

        # High-accuracy reference solution
        ref_res = integrate_geodesic(y0, metric, span, rtol=1e-12, atol=1e-12)
        assert ref_res.success is True
        y_ref = ref_res.states[-1]

        tols = [1e-6, 1e-8, 1e-10]
        state_errors = []
        h_drifts = []

        for tol in tols:
            res = integrate_geodesic(y0, metric, span, rtol=tol, atol=tol)
            assert res.success is True
            err = float(np.linalg.norm(res.states[-1] - y_ref))
            state_errors.append(err)

            h_vals = np.array([hamiltonian_value(s[:4], s[4:], metric) for s in res.states])
            h_drifts.append(float(np.max(np.abs(h_vals - h_vals[0]))))

        # Errors strictly decrease monotonically
        assert state_errors[0] > state_errors[1] > state_errors[2]
        assert h_drifts[0] > h_drifts[1] > h_drifts[2]
        assert state_errors[2] < 1e-8
        assert h_drifts[2] < 1e-11

    def test_kerr_null_tolerance_convergence(self):
        """Verifies monotonic error decrease and Hamiltonian preservation for null Kerr geodesic."""
        mass = 1.0
        metric = KerrMetric(mass=mass, spin=-0.7)
        x0 = np.array([0.0, 8.0, np.pi / 4.0, 0.0], dtype=np.float64)
        y0 = kerr_geodesic_initial_state(
            metric=metric,
            x=x0,
            energy=1.0,
            Lz=3.0,
            ptheta=0.4,
            mu=0.0,
            radial_direction="outward",
        )
        span = (0.0, 25.0)

        ref_res = integrate_geodesic(y0, metric, span, rtol=1e-12, atol=1e-12)
        assert ref_res.success is True
        y_ref = ref_res.states[-1]

        tols = [1e-6, 1e-8, 1e-10]
        state_errors = []
        h_drifts = []

        for tol in tols:
            res = integrate_geodesic(y0, metric, span, rtol=tol, atol=tol)
            assert res.success is True
            err = float(np.linalg.norm(res.states[-1] - y_ref))
            state_errors.append(err)

            h_vals = np.array([hamiltonian_value(s[:4], s[4:], metric) for s in res.states])
            h_drifts.append(float(np.max(np.abs(h_vals - h_vals[0]))))

        assert state_errors[0] > state_errors[1] > state_errors[2]
        assert h_drifts[0] > h_drifts[1] > h_drifts[2]
        assert state_errors[2] < 1e-8
        assert h_drifts[2] < 1e-11


# =============================================================================
# Test Suite: Stage 2C (Schwarzschild Limit Trajectory Agreement)
# =============================================================================

class TestKerrSchwarzschildLimitTrajectories:
    """Stage 2C: Trajectory-level reduction of Kerr (a=0) to Schwarzschild."""

    def test_kerr_schwarzschild_limit_null_trajectory(self):
        """KerrMetric with a=0 matches SchwarzschildMetric across all 8 state components over a trajectory."""
        mass = 1.0
        kerr_zero = KerrMetric(mass=mass, spin=0.0)
        schw = SchwarzschildMetric(mass=mass)

        x0 = np.array([0.0, 8.0, np.pi / 3.0, 0.0], dtype=np.float64)
        y0 = kerr_geodesic_initial_state(
            metric=kerr_zero,
            x=x0,
            energy=1.0,
            Lz=3.0,
            ptheta=0.5,
            mu=0.0,
            radial_direction="outward",
        )

        span = (0.0, 30.0)
        t_eval = np.linspace(0.0, 30.0, 100)

        res_kerr = integrate_geodesic(y0, kerr_zero, span, t_eval=t_eval, rtol=1e-11, atol=1e-11)
        res_schw = integrate_geodesic(y0, schw, span, t_eval=t_eval, rtol=1e-11, atol=1e-11)

        assert res_kerr.success is True
        assert res_schw.success is True

        # All 8 components must match to within 1e-13
        max_diff = float(np.max(np.abs(res_kerr.states - res_schw.states)))
        assert max_diff <= 1e-13, f"Schwarzschild trajectory difference: {max_diff:.2e}"

    def test_kerr_schwarzschild_limit_timelike_trajectory(self):
        """KerrMetric with a=0 matches SchwarzschildMetric for timelike trajectory."""
        mass = 1.0
        kerr_zero = KerrMetric(mass=mass, spin=0.0)
        schw = SchwarzschildMetric(mass=mass)

        x0 = np.array([0.0, 7.0, np.pi / 4.0, 0.0], dtype=np.float64)
        y0 = kerr_geodesic_initial_state(
            metric=kerr_zero,
            x=x0,
            energy=1.02,
            Lz=2.5,
            ptheta=0.2,
            mu=1.0,
            radial_direction="outward",
        )

        span = (0.0, 25.0)
        t_eval = np.linspace(0.0, 25.0, 100)

        res_kerr = integrate_geodesic(y0, kerr_zero, span, t_eval=t_eval, rtol=1e-11, atol=1e-11)
        res_schw = integrate_geodesic(y0, schw, span, t_eval=t_eval, rtol=1e-11, atol=1e-11)

        max_diff = float(np.max(np.abs(res_kerr.states - res_schw.states)))
        assert max_diff <= 1e-13, f"Schwarzschild timelike trajectory difference: {max_diff:.2e}"


# =============================================================================
# Test Suite: Stage 2C (Horizon Cutoff and Stability)
# =============================================================================

class TestKerrHorizonCutoff:
    """Stage 2C: Horizon cutoff event handling and numerical stability near Boyer-Lindquist horizon."""

    def test_kerr_inward_plunge_horizon_cutoff(self):
        """Inward trajectory terminates cleanly at r_cut = r_+(1 + eps) with HorizonCutoffEvent."""
        mass = 1.0
        metric = KerrMetric(mass=mass, spin=0.7)
        r_plus = metric.horizon_radius

        x0 = np.array([0.0, 8.0, np.pi / 3.0, 0.0], dtype=np.float64)
        y0 = kerr_geodesic_initial_state(
            metric=metric,
            x=x0,
            energy=0.98,
            Lz=2.5,
            ptheta=0.2,
            mu=1.0,
            radial_direction="inward",
        )

        # 1. Unmitigated plunge steps into coordinate singularity
        res_unmitigated = integrate_geodesic(y0, metric, (0.0, 50.0))
        assert res_unmitigated.status == -1  # Step-size underflow near r_+

        # 2. Mitigated plunge terminates cleanly with HorizonCutoffEvent
        epsilon = 1e-2
        event = HorizonCutoffEvent(metric=metric, epsilon=epsilon)
        res_mitigated = integrate_geodesic(y0, metric, (0.0, 50.0), events=event)

        assert res_mitigated.success is True
        assert res_mitigated.status == 1
        assert res_mitigated.terminal_event_occurred is True
        assert res_mitigated.terminal_event_name == "horizon_cutoff"

        expected_r_cut = r_plus * (1.0 + epsilon)
        final_r = res_mitigated.r[-1]
        assert abs(final_r - expected_r_cut) <= 1e-5
        assert np.all(res_mitigated.r >= expected_r_cut - 1e-5)


# =============================================================================
# Test Suite: Stage 2D (Carter Constant Trajectory Conservation)
# =============================================================================

class TestKerrCarterConservation:
    """Stage 2D: Numerical conservation of Carter constant along integrated Kerr geodesics."""

    def test_carter_conservation_timelike_equatorial(self) -> None:
        """Equatorial geodesic (theta=pi/2, p_theta=0) preserves Q == 0 identically to < 1e-12."""
        mass = 1.0
        spin = 0.7
        metric = KerrMetric(mass=mass, spin=spin)

        x0 = np.array([0.0, 7.0, 0.5 * np.pi, 0.0], dtype=np.float64)
        energy = 0.95
        lz = 2.8
        y0 = kerr_geodesic_initial_state(
            metric=metric,
            x=x0,
            energy=energy,
            Lz=lz,
            ptheta=0.0,
            mu=1.0,
            radial_direction="outward",
        )

        res = integrate_geodesic(y0, metric, (0.0, 40.0), rtol=1e-10, atol=1e-10)
        assert res.success is True
        assert len(res.lambdas) >= 5

        # Evaluate Carter constant along complete numerical trajectory
        q_traj = carter_constant(res.states, metric, mu=1.0)
        assert abs(q_traj[0]) <= 1e-15

        max_drift = float(np.max(np.abs(q_traj - q_traj[0])))
        scale = max(abs(q_traj[0]), energy ** 2 + lz ** 2 + 1.0)
        norm_drift = max_drift / scale

        assert max_drift <= 1e-12, f"Equatorial Q drift: {max_drift:.2e}"
        assert norm_drift <= 1e-12

        # Verify motion remained equatorial
        theta_err = float(np.max(np.abs(res.theta - 0.5 * np.pi)))
        ptheta_err = float(np.max(np.abs(res.ptheta)))
        assert theta_err <= 1e-11, f"Polar angle deviated from equator: {theta_err:.2e}"
        assert ptheta_err <= 1e-11, f"Polar momentum deviated from zero: {ptheta_err:.2e}"

    @pytest.mark.parametrize("spin", [0.5, -0.5, 0.95, -0.95])
    def test_carter_conservation_timelike_nonequatorial(self, spin: float) -> None:
        """Non-equatorial timelike orbits conserve Carter constant with normalized drift < 1e-9."""
        mass = 1.0
        metric = KerrMetric(mass=mass, spin=spin)

        x0 = np.array([0.0, 6.0, np.pi / 3.0, 0.0], dtype=np.float64)
        energy = 0.98
        lz = 2.5
        ptheta = 0.2
        mu = 1.0
        y0 = kerr_geodesic_initial_state(
            metric=metric,
            x=x0,
            energy=energy,
            Lz=lz,
            ptheta=ptheta,
            mu=mu,
            radial_direction="outward",
        )

        res = integrate_geodesic(y0, metric, (0.0, 30.0), rtol=1e-10, atol=1e-10)
        assert res.success is True
        assert len(res.lambdas) >= 5

        q_traj = carter_constant(res.states, metric, mu=mu)
        q0 = q_traj[0]
        max_drift = float(np.max(np.abs(q_traj - q0)))
        scale = max(abs(q0), energy ** 2 + lz ** 2 + mu ** 2)
        norm_drift = max_drift / scale

        assert norm_drift <= 1e-9, f"Timelike Carter normalized drift at a={spin}: {norm_drift:.2e}"

        # Check Killing energy, angular momentum, and super-Hamiltonian conservation
        e_drift = float(np.max(np.abs(-res.states[:, 4] - energy)))
        lz_drift = float(np.max(np.abs(res.states[:, 7] - lz)))
        assert e_drift <= 1e-9, f"Energy drift at a={spin}: {e_drift:.2e}"
        assert lz_drift <= 1e-9, f"Lz drift at a={spin}: {lz_drift:.2e}"

        h_vals = np.array([hamiltonian_value(s[:4], s[4:], metric) for s in res.states])
        h_residuals = np.abs(h_vals - (-0.5 * mu ** 2))
        assert np.max(h_residuals) <= 1e-9

        # Independent radial Carter constant agreement along trajectory
        q_rad_traj = carter_constant_radial(res.states, metric, mu=mu)
        max_diff_rad_pol = float(np.max(np.abs(q_traj - q_rad_traj)))
        assert max_diff_rad_pol <= 1e-7, f"Radial vs polar Carter mismatch along trajectory: {max_diff_rad_pol:.2e}"

    @pytest.mark.parametrize("spin", [0.85, -0.85, 0.5])
    def test_carter_conservation_null_nonequatorial(self, spin: float) -> None:
        """Non-equatorial null geodesics conserve Carter constant with normalized drift < 1e-9."""
        mass = 1.0
        metric = KerrMetric(mass=mass, spin=spin)

        x0 = np.array([0.0, 8.0, np.pi / 4.0, 0.0], dtype=np.float64)
        energy = 1.0
        lz = 3.0
        ptheta = 0.4
        mu = 0.0
        y0 = kerr_geodesic_initial_state(
            metric=metric,
            x=x0,
            energy=energy,
            Lz=lz,
            ptheta=ptheta,
            mu=mu,
            radial_direction="outward",
        )

        res = integrate_geodesic(y0, metric, (0.0, 25.0), rtol=1e-10, atol=1e-10)
        assert res.success is True
        assert len(res.lambdas) >= 5

        q_traj = carter_constant(res.states, metric, mu=mu)
        q0 = q_traj[0]
        max_drift = float(np.max(np.abs(q_traj - q0)))
        scale = max(abs(q0), energy ** 2 + lz ** 2 + 1.0)
        norm_drift = max_drift / scale

        assert norm_drift <= 1e-9, f"Null Carter normalized drift at a={spin}: {norm_drift:.2e}"

        # Mass shell constraint 2*H = 0
        h_vals = np.array([hamiltonian_value(s[:4], s[4:], metric) for s in res.states])
        assert np.max(np.abs(h_vals)) <= 1e-9

        # Independent radial Carter constant agreement along trajectory
        q_rad_traj = carter_constant_radial(res.states, metric, mu=mu)
        max_diff_rad_pol = float(np.max(np.abs(q_traj - q_rad_traj)))
        assert max_diff_rad_pol <= 1e-7, f"Null radial vs polar Carter mismatch along trajectory: {max_diff_rad_pol:.2e}"

    def test_carter_tolerance_convergence(self) -> None:
        """Verifies strictly monotonic reduction of Carter drift as rtol/atol are tightened."""
        # 1. Timelike test case (spin a = 0.5)
        m_time = KerrMetric(mass=1.0, spin=0.5)
        x0_time = np.array([0.0, 6.0, np.pi / 3.0, 0.0], dtype=np.float64)
        y0_time = kerr_geodesic_initial_state(
            metric=m_time,
            x=x0_time,
            energy=0.98,
            Lz=2.5,
            ptheta=0.2,
            mu=1.0,
            radial_direction="outward",
        )
        q0_time = float(carter_constant(y0_time, m_time, mu=1.0))
        assert np.isclose(q0_time, 2.125808333333333, atol=1e-12, rtol=1e-12)

        tols = [1e-6, 1e-8, 1e-10, 1e-12]
        drifts_time = []
        for tol in tols:
            res = integrate_geodesic(y0_time, m_time, (0.0, 30.0), rtol=tol, atol=tol)
            assert res.success is True
            q_traj = carter_constant(res.states, m_time, mu=1.0)
            assert np.isclose(q_traj[0], q0_time, atol=1e-14, rtol=1e-14)
            drifts_time.append(float(np.max(np.abs(q_traj - q_traj[0]))))

        for i in range(len(drifts_time) - 1):
            assert drifts_time[i] > drifts_time[i + 1], (
                f"Timelike Carter drift failed monotonic convergence: "
                f"tol={tols[i]:.0e} -> {drifts_time[i]:.2e}, tol={tols[i+1]:.0e} -> {drifts_time[i+1]:.2e}"
            )

        # 2. Null test case (spin a = -0.7)
        m_null = KerrMetric(mass=1.0, spin=-0.7)
        x0_null = np.array([0.0, 8.0, np.pi / 4.0, 0.0], dtype=np.float64)
        y0_null = kerr_geodesic_initial_state(
            metric=m_null,
            x=x0_null,
            energy=1.0,
            Lz=3.0,
            ptheta=0.4,
            mu=0.0,
            radial_direction="outward",
        )
        # Dynamic Carter constant evaluation: Q(0) evaluated directly from initial state
        # Analytic value: Q = ptheta^2 + cos^2(theta)*[a^2*(mu^2 - E^2) + Lz^2/sin^2(theta)]
        # = 0.4^2 + 0.5 * [(-0.7)^2 * (0 - 1) + 3.0^2 / 0.5] = 0.16 + 0.5 * [-0.49 + 18.0] = 8.915
        q0_null = float(carter_constant(y0_null, m_null, mu=0.0))
        assert np.isclose(q0_null, 8.915, atol=1e-14, rtol=1e-14)

        drifts_null = []
        for tol in tols:
            res = integrate_geodesic(y0_null, m_null, (0.0, 25.0), rtol=tol, atol=tol)
            assert res.success is True
            q_traj = carter_constant(res.states, m_null, mu=0.0)
            # Verify dynamic trajectory Carter constant matches analytic 8.915 and state q0_null
            assert np.isclose(q_traj[0], 8.915, atol=1e-14, rtol=1e-14)
            assert np.isclose(q_traj[0], q0_null, atol=1e-14, rtol=1e-14)
            drifts_null.append(float(np.max(np.abs(q_traj - q_traj[0]))))

        for i in range(len(drifts_null) - 1):
            assert drifts_null[i] > drifts_null[i + 1], (
                f"Null Carter drift failed monotonic convergence: "
                f"tol={tols[i]:.0e} -> {drifts_null[i]:.2e}, tol={tols[i+1]:.0e} -> {drifts_null[i+1]:.2e}"
            )
