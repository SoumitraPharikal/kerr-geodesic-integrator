"""Automated verification suite for Schwarzschild spacetime metric core.

Implements Stage 1A tests:
- VAL-MET-01: Metric inversion identity g^{mu alpha} g_{alpha nu} = delta^mu_nu.
- VAL-MET-02: 4th-order central finite-difference verification of contravariant derivatives.
- VAL-MET-02-REG: Explicit regression test verifying positive sign of partial_r g^{00}.
- Input validation and boundary tests for mass, radius, and polar angle.
"""

import numpy as np
import pytest

from geodesics.constants import IDX_X0, IDX_R, IDX_THETA, IDX_PHI
from geodesics.metrics.schwarzschild import SchwarzschildMetric


# =============================================================================
# Helper: Fourth-Order Central Finite Difference
# =============================================================================

def finite_difference_4th_order(func, x0: float, h: float = 1e-4) -> np.ndarray:
    """Computes the 4th-order central finite difference of a matrix-valued function.

    Formula:
        f'(x) = (-f(x + 2h) + 8f(x + h) - 8f(x - h) + f(x - 2h)) / (12h) + O(h^4)

    Parameters
    ----------
    func : callable
        Function returning a 2D NumPy array.
    x0 : float
        Evaluation point.
    h : float, optional
        Finite-difference step size (default is 1e-4).

    Returns
    -------
    np.ndarray
        Numerical derivative of func evaluated at x0.
    """
    f_p2 = func(x0 + 2.0 * h)
    f_p1 = func(x0 + h)
    f_m1 = func(x0 - h)
    f_m2 = func(x0 - 2.0 * h)
    return (-f_p2 + 8.0 * f_p1 - 8.0 * f_m1 + f_m2) / (12.0 * h)


# =============================================================================
# Test Suite: VAL-MET-01 (Metric Inversion Identity)
# =============================================================================

class TestMetricInversion:
    """Tests the metric inversion identity g^{mu alpha} g_{alpha nu} = delta^mu_nu."""

    @pytest.mark.parametrize("mass", [0.5, 1.0, 2.5, 10.0])
    @pytest.mark.parametrize("r", [2.5, 3.0, 5.0, 10.0, 100.0, 1000.0])
    @pytest.mark.parametrize("theta", [0.1 * np.pi, 0.25 * np.pi, 0.5 * np.pi, 0.75 * np.pi, 0.9 * np.pi])
    def test_val_met_01_inversion_identity(self, mass: float, r: float, theta: float):
        """VAL-MET-01: Verifies g^{mu alpha} g_{alpha nu} = delta^mu_nu to double precision.

        Tests across multiple masses, radii, and polar inclinations.
        Acceptance criterion: max absolute difference <= 1e-14.
        """
        # Ensure r is scaled appropriately if mass is large
        test_r = r * mass
        metric = SchwarzschildMetric(mass=mass)

        g_cov = metric.g_cov(test_r, theta)
        g_contra = metric.g_contra(test_r, theta)

        # Compute matrix product G_contra @ G_cov
        identity_test = g_contra @ g_cov
        expected_identity = np.eye(4, dtype=np.float64)

        max_err = np.max(np.abs(identity_test - expected_identity))
        assert max_err <= 1e-14, (
            f"VAL-MET-01 failed at M={mass}, r={test_r}, theta={theta}: "
            f"max error = {max_err:.2e} > 1e-14"
        )

    def test_metric_symmetry(self):
        """Verifies that both g_{mu nu} and g^{mu nu} are strictly symmetric matrices."""
        metric = SchwarzschildMetric(mass=1.0)
        r = 6.0
        theta = np.pi / 3.0

        g_cov = metric.g_cov(r, theta)
        g_contra = metric.g_contra(r, theta)

        np.testing.assert_array_equal(g_cov, g_cov.T)
        np.testing.assert_array_equal(g_contra, g_contra.T)


# =============================================================================
# Test Suite: VAL-MET-02 (Analytical Derivatives vs Finite Differences)
# =============================================================================

class TestMetricDerivatives:
    """Tests analytical contravariant metric derivatives against 4th-order finite differences."""

    @pytest.mark.parametrize("mass", [0.8, 1.0, 2.0])
    @pytest.mark.parametrize("r_over_m", [2.5, 3.5, 6.0, 15.0, 50.0])
    @pytest.mark.parametrize("theta", [0.2 * np.pi, 0.5 * np.pi, 0.8 * np.pi])
    def test_val_met_02_radial_derivative(self, mass: float, r_over_m: float, theta: float):
        """VAL-MET-02 (Radial): Compares partial_r g^{alpha beta} against finite differences.

        Acceptance criterion: relative error <= 1e-7 for non-zero components,
        absolute error <= 1e-14 for zero components.
        """
        metric = SchwarzschildMetric(mass=mass)
        r = r_over_m * mass
        h = 1e-4

        analytical = metric.dg_contra_dr(r, theta)
        numerical = finite_difference_4th_order(lambda r_: metric.g_contra(r_, theta), r, h=h)

        # Check all components
        for mu in range(4):
            for nu in range(4):
                a_val = analytical[mu, nu]
                n_val = numerical[mu, nu]

                if abs(a_val) > 1e-12:
                    rel_err = abs(a_val - n_val) / abs(a_val)
                    assert rel_err <= 1e-7, (
                        f"VAL-MET-02 radial derivative mismatch at ({mu}, {nu}) "
                        f"for M={mass}, r={r}, theta={theta}: "
                        f"analytical={a_val:.10e}, numerical={n_val:.10e}, rel_err={rel_err:.2e}"
                    )
                else:
                    assert abs(a_val) == 0.0
                    assert abs(n_val) <= 1e-10, (
                        f"Spurious non-zero radial derivative at ({mu}, {nu}): {n_val:.2e}"
                    )

    @pytest.mark.parametrize("mass", [1.0, 3.0])
    @pytest.mark.parametrize("r_over_m", [2.5, 4.0, 10.0, 25.0])
    @pytest.mark.parametrize("theta", [0.15 * np.pi, 0.35 * np.pi, 0.65 * np.pi, 0.85 * np.pi])
    def test_val_met_02_polar_derivative(self, mass: float, r_over_m: float, theta: float):
        """VAL-MET-02 (Polar): Compares partial_theta g^{alpha beta} against finite differences.

        Acceptance criterion: relative error <= 1e-7 for non-zero components,
        absolute error <= 1e-14 for zero components.
        """
        metric = SchwarzschildMetric(mass=mass)
        r = r_over_m * mass
        h = 1e-4

        analytical = metric.dg_contra_dtheta(r, theta)
        numerical = finite_difference_4th_order(lambda th_: metric.g_contra(r, th_), theta, h=h)

        for mu in range(4):
            for nu in range(4):
                a_val = analytical[mu, nu]
                n_val = numerical[mu, nu]

                if abs(a_val) > 1e-12:
                    rel_err = abs(a_val - n_val) / abs(a_val)
                    assert rel_err <= 1e-7, (
                        f"VAL-MET-02 polar derivative mismatch at ({mu}, {nu}) "
                        f"for M={mass}, r={r}, theta={theta}: "
                        f"analytical={a_val:.10e}, numerical={n_val:.10e}, rel_err={rel_err:.2e}"
                    )
                else:
                    assert abs(a_val) == 0.0
                    assert abs(n_val) <= 1e-10, (
                        f"Spurious non-zero polar derivative at ({mu}, {nu}): {n_val:.2e}"
                    )

    def test_val_met_02_positive_sign_regression(self):
        """VAL-MET-02-REG: Explicit regression test verifying positive sign of partial_r g^{00}.

        The analytical derivative is:
            partial_r g^{00} = +2M / (r^2 * f(r)^2) > 0.
        A negative sign would create a repulsive gravitational acceleration in
        the radial Hamiltonian equation dp_r/dlambda = -1/2 (partial_r g^{00}) p_0^2.
        """
        metric = SchwarzschildMetric(mass=1.0)
        radii = [2.01, 2.5, 3.0, 5.0, 10.0, 100.0]

        for r in radii:
            dg_dr = metric.dg_contra_dr(r, theta=np.pi / 2.0)
            dg00_dr = dg_dr[IDX_X0, IDX_X0]

            # Verify strictly positive
            assert dg00_dr > 0.0, f"partial_r g^{{00}} must be strictly positive, got {dg00_dr} at r={r}"

            # Verify exact analytical formula value
            f = 1.0 - (2.0 / r)
            expected = 2.0 / (r * r * f * f)
            assert np.isclose(dg00_dr, expected, rtol=1e-14, atol=1e-15)

    def test_dg_contra_all_structure(self):
        """Verifies dg_contra_all returns shape (4, 4, 4) with zero stationary and azimuthal slices."""
        metric = SchwarzschildMetric(mass=1.0)
        r = 5.0
        theta = np.pi / 4.0

        dg_all = metric.dg_contra_all(r, theta)
        assert dg_all.shape == (4, 4, 4)

        # Stationarity: partial_0 g^{alpha beta} == 0
        np.testing.assert_array_equal(dg_all[IDX_X0, :, :], np.zeros((4, 4)))

        # Axisymmetry: partial_phi g^{alpha beta} == 0
        np.testing.assert_array_equal(dg_all[IDX_PHI, :, :], np.zeros((4, 4)))

        # Slices 1 and 2 match individual methods
        np.testing.assert_array_equal(dg_all[IDX_R, :, :], metric.dg_contra_dr(r, theta))
        np.testing.assert_array_equal(dg_all[IDX_THETA, :, :], metric.dg_contra_dtheta(r, theta))


# =============================================================================
# Test Suite: Input Validation and Coordinate Domain Checks
# =============================================================================

class TestInputValidation:
    """Verifies that invalid parameters and coordinates raise informative exceptions."""

    def test_default_mass(self):
        """Checks default mass parameter M = 1.0."""
        metric = SchwarzschildMetric()
        assert metric.mass == 1.0
        assert metric.horizon_radius == 2.0
        assert metric.photon_sphere_radius == 3.0
        assert np.isclose(metric.critical_impact_parameter, 3.0 * np.sqrt(3.0))

    def test_custom_positive_mass(self):
        """Checks initialization with custom positive mass."""
        metric = SchwarzschildMetric(mass=4.5)
        assert metric.mass == 4.5
        assert metric.horizon_radius == 9.0
        assert metric.photon_sphere_radius == 13.5
        assert np.isclose(metric.critical_impact_parameter, 13.5 * np.sqrt(3.0))

    @pytest.mark.parametrize("invalid_mass", [0.0, -1.0, -1e-6, np.nan, np.inf, -np.inf])
    def test_rejection_of_invalid_mass(self, invalid_mass: float):
        """Rejects zero, negative, and non-finite mass values with ValueError."""
        with pytest.raises(ValueError, match="mass M must be positive and finite"):
            SchwarzschildMetric(mass=invalid_mass)

    @pytest.mark.parametrize("invalid_r", [2.0, 1.99, 1.0, 0.0, -5.0, np.nan, np.inf, -np.inf])
    def test_rejection_of_horizon_and_interior_radius(self, invalid_r: float):
        """Rejects evaluations on or inside the event horizon r <= 2M."""
        metric = SchwarzschildMetric(mass=1.0)
        with pytest.raises(ValueError):
            metric.g_cov(invalid_r)
        with pytest.raises(ValueError):
            metric.g_contra(invalid_r)
        with pytest.raises(ValueError):
            metric.dg_contra_dr(invalid_r)
        with pytest.raises(ValueError):
            metric.dg_contra_dtheta(invalid_r)
        with pytest.raises(ValueError):
            metric.lapse(invalid_r)

    @pytest.mark.parametrize("invalid_theta", [0.0, np.pi, -0.1, np.pi + 0.1, np.nan, np.inf])
    def test_rejection_of_invalid_polar_angle(self, invalid_theta: float):
        """Rejects evaluations on or outside the polar coordinate domain theta in (0, pi)."""
        metric = SchwarzschildMetric(mass=1.0)
        r = 10.0
        with pytest.raises(ValueError):
            metric.g_cov(r, theta=invalid_theta)
        with pytest.raises(ValueError):
            metric.g_contra(r, theta=invalid_theta)
        with pytest.raises(ValueError):
            metric.dg_contra_dr(r, theta=invalid_theta)
        with pytest.raises(ValueError):
            metric.dg_contra_dtheta(r, theta=invalid_theta)

    def test_coordinate_names_and_dimension(self):
        """Verifies coordinate naming metadata and dimension properties."""
        metric = SchwarzschildMetric()
        assert metric.coordinate_names == ("x0", "r", "theta", "phi")
        assert metric.dimension == 4
