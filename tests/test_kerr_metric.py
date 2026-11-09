"""Automated verification suite for Kerr spacetime metric core (Stage 2A).

Implements Stage 2A validation tests:
- KERR-01: Parameter validation (mass > 0, spin |a| <= M, rejection of super-extremal |a| > M and non-finite).
- KERR-02: Coordinate-domain validation (exterior r > r_+, regular theta in (0, pi), rejection of r <= r_+ and axis).
- KERR-03: Metric symmetry and structure (g_{mu nu} = g_{nu mu}, off-diagonal zeros, nonzero t-phi cross term).
- KERR-04: Inverse identity (g_{mu alpha} g^{alpha nu} = delta_mu^nu to double precision).
- KERR-05: Independent numerical inverse comparison against numpy.linalg.inv.
- KERR-06: Determinant identity det(g_{mu nu}) = -Sigma^2 sin^2(theta) against numpy.linalg.det.
- KERR-07: Analytic inverse derivatives against 4th-order central finite differences across (r, theta).
- KERR-08: Schwarzschild limit (a = 0 reduces exactly to SchwarzschildMetric).
- KERR-09: Signed spin behavior (a -> -a preserves diagonals and reverses sign of cross-terms and their derivatives).
- KERR-10: Horizon radius and extremal black hole behavior (|a| = M).
"""

from decimal import Decimal, getcontext
from typing import Callable
import numpy as np
import pytest

from geodesics.constants import (
    IDX_PHI,
    IDX_R,
    IDX_THETA,
    IDX_X0,
)
from geodesics.metrics.kerr import KerrMetric
from geodesics.metrics.schwarzschild import SchwarzschildMetric


# =============================================================================
# Helper: Fourth-Order Central Finite Difference
# =============================================================================

def finite_difference_4th_order(func: Callable[[float], np.ndarray], x0: float, h: float = 1e-5) -> np.ndarray:
    """Computes the 4th-order central finite difference of a matrix-valued function.

    Formula:
        f'(x) = (-f(x + 2h) + 8f(x + h) - 8f(x - h) + f(x - 2h)) / (12h) + O(h^4)

    For h = 1e-5 in double precision, truncation error O(h^4) ~ 1e-20, while
    roundoff error eps_mach / h ~ 2e-11, yielding optimal ~1e-10 accuracy.
    """
    f_p2 = func(x0 + 2.0 * h)
    f_p1 = func(x0 + h)
    f_m1 = func(x0 - h)
    f_m2 = func(x0 - 2.0 * h)
    return (-f_p2 + 8.0 * f_p1 - 8.0 * f_m1 + f_m2) / (12.0 * h)


# =============================================================================
# Test Suite: KERR-01 (Parameter Validation)
# =============================================================================

class TestKerrParameterValidation:
    """KERR-01: Verification of Kerr parameter validation (mass M and spin a)."""

    def test_valid_parameters(self) -> None:
        """Valid positive mass and sub-extremal/extremal spins are accepted."""
        # Positive mass, zero spin
        m1 = KerrMetric(mass=1.0, spin=0.0)
        assert m1.mass == 1.0
        assert m1.spin == 0.0
        assert m1.is_extremal is False

        # Positive spin
        m2 = KerrMetric(mass=2.5, spin=1.5)
        assert m2.mass == 2.5
        assert m2.spin == 1.5
        assert m2.is_extremal is False

        # Negative spin (retrograde)
        m3 = KerrMetric(mass=1.0, spin=-0.7)
        assert m3.mass == 1.0
        assert m3.spin == -0.7
        assert m3.is_extremal is False

        # Extremal positive spin a = M
        m4 = KerrMetric(mass=1.2, spin=1.2)
        assert m4.is_extremal is True

        # Extremal negative spin a = -M
        m5 = KerrMetric(mass=1.2, spin=-1.2)
        assert m5.is_extremal is True

    @pytest.mark.parametrize("invalid_mass", [0.0, -1.0, -1e-6, np.nan, np.inf, -np.inf])
    def test_rejection_of_invalid_mass(self, invalid_mass: float) -> None:
        """Rejects non-positive or non-finite mass values."""
        with pytest.raises(ValueError, match="mass M must be positive and finite"):
            KerrMetric(mass=invalid_mass, spin=0.0)

    @pytest.mark.parametrize("invalid_spin", [np.nan, np.inf, -np.inf])
    def test_rejection_of_non_finite_spin(self, invalid_spin: float) -> None:
        """Rejects non-finite spin parameter values."""
        with pytest.raises(ValueError, match="spin parameter a must be finite"):
            KerrMetric(mass=1.0, spin=invalid_spin)

    @pytest.mark.parametrize("super_extremal_a", [1.0001, 1.5, 2.0, 10.0, -1.0001, -1.5, -5.0])
    def test_rejection_of_super_extremal_spin(self, super_extremal_a: float) -> None:
        """Rejects super-extremal spin |a| > M (naked singularity prevention)."""
        with pytest.raises(ValueError, match="Super-extremal spin"):
            KerrMetric(mass=1.0, spin=super_extremal_a)


# =============================================================================
# Test Suite: KERR-02 (Coordinate-Domain Validation)
# =============================================================================

class TestKerrCoordinateDomainValidation:
    """KERR-02: Verification of coordinate-domain restrictions (r > r_+, 0 < theta < pi)."""

    def test_valid_exterior_coordinates(self) -> None:
        """Valid exterior coordinates evaluate cleanly without error."""
        metric = KerrMetric(mass=1.0, spin=0.8)
        # r_+ = 1.0 + sqrt(1 - 0.64) = 1.6
        g = metric.g_cov(r=2.0, theta=np.pi / 2.0)
        assert isinstance(g, np.ndarray)
        assert g.shape == (4, 4)

    @pytest.mark.parametrize("spin", [0.0, 0.6, -0.6, 1.0, -1.0])
    def test_rejection_of_horizon_and_interior_radii(self, spin: float) -> None:
        """Rejects r <= r_+ (at or inside outer event horizon)."""
        metric = KerrMetric(mass=1.0, spin=spin)
        r_plus = metric.horizon_radius

        # Exactly at horizon
        with pytest.raises(ValueError, match="strictly outside the outer event horizon"):
            metric.g_cov(r=r_plus, theta=np.pi / 2.0)

        # Inside horizon
        with pytest.raises(ValueError, match="strictly outside the outer event horizon"):
            metric.g_cov(r=r_plus - 0.1, theta=np.pi / 2.0)

        with pytest.raises(ValueError, match="strictly outside the outer event horizon"):
            metric.g_contra(r=r_plus, theta=np.pi / 2.0)

    @pytest.mark.parametrize("invalid_theta", [0.0, np.pi, -0.1, np.pi + 0.1, np.nan, np.inf])
    def test_rejection_of_invalid_polar_angles(self, invalid_theta: float) -> None:
        """Rejects polar angles at or beyond coordinate boundaries (theta <= 0 or theta >= pi)."""
        metric = KerrMetric(mass=1.0, spin=0.5)
        r = 3.0

        with pytest.raises(ValueError, match="Polar angle theta must be"):
            metric.g_cov(r=r, theta=invalid_theta)

        with pytest.raises(ValueError, match="Polar angle theta must be"):
            metric.g_contra(r=r, theta=invalid_theta)

    @pytest.mark.parametrize("invalid_r", [np.nan, np.inf, -np.inf])
    def test_rejection_of_non_finite_radius(self, invalid_r: float) -> None:
        """Rejects non-finite radial coordinates."""
        metric = KerrMetric(mass=1.0, spin=0.5)
        with pytest.raises(ValueError, match="Radial coordinate r must be finite"):
            metric.g_cov(r=invalid_r, theta=np.pi / 2.0)


# =============================================================================
# Test Suite: KERR-03 (Metric Symmetry and Structure)
# =============================================================================

class TestKerrMetricSymmetryAndStructure:
    """KERR-03: Verification of metric symmetry and nonzero tensor components."""

    @pytest.mark.parametrize("spin", [-0.8, -0.3, 0.0, 0.5, 0.95])
    @pytest.mark.parametrize("theta", [0.2, np.pi / 4.0, np.pi / 2.0, 2.5])
    def test_metric_symmetry(self, spin: float, theta: float) -> None:
        """Verifies that both g_{mu nu} and g^{mu nu} are strictly symmetric matrices."""
        metric = KerrMetric(mass=1.0, spin=spin)
        r = 3.5

        g_cov = metric.g_cov(r, theta)
        g_contra = metric.g_contra(r, theta)

        np.testing.assert_array_equal(g_cov, g_cov.T)
        np.testing.assert_array_equal(g_contra, g_contra.T)

    @pytest.mark.parametrize("spin", [0.5, -0.7])
    def test_expected_zero_and_nonzero_components(self, spin: float) -> None:
        """Verifies off-diagonal zeros and nonzero t-phi cross terms for non-zero spin."""
        metric = KerrMetric(mass=1.0, spin=spin)
        r = 4.0
        theta = np.pi / 3.0

        g = metric.g_cov(r, theta)

        # Diagonals must be non-zero
        assert g[IDX_X0, IDX_X0] != 0.0
        assert g[IDX_R, IDX_R] != 0.0
        assert g[IDX_THETA, IDX_THETA] != 0.0
        assert g[IDX_PHI, IDX_PHI] != 0.0

        # t-phi cross term is nonzero for spin != 0 and theta != 0, pi
        assert g[IDX_X0, IDX_PHI] != 0.0
        assert g[IDX_PHI, IDX_X0] != 0.0
        assert g[IDX_X0, IDX_PHI] == g[IDX_PHI, IDX_X0]

        # All other off-diagonal components must be identically zero
        assert g[IDX_X0, IDX_R] == 0.0
        assert g[IDX_X0, IDX_THETA] == 0.0
        assert g[IDX_R, IDX_X0] == 0.0
        assert g[IDX_R, IDX_THETA] == 0.0
        assert g[IDX_R, IDX_PHI] == 0.0
        assert g[IDX_THETA, IDX_X0] == 0.0
        assert g[IDX_THETA, IDX_R] == 0.0
        assert g[IDX_THETA, IDX_PHI] == 0.0
        assert g[IDX_PHI, IDX_R] == 0.0
        assert g[IDX_PHI, IDX_THETA] == 0.0


# =============================================================================
# Test Suite: KERR-04 & KERR-05 (Inverse Identity and Numerical Inversion)
# =============================================================================

class TestKerrInverseMetric:
    """KERR-04 & KERR-05: Verification of analytic contravariant inverse metric."""

    @pytest.mark.parametrize("mass", [0.5, 1.0, 2.0])
    @pytest.mark.parametrize("spin_frac", [-0.95, -0.5, 0.0, 0.5, 0.95, 1.0])
    @pytest.mark.parametrize("r_factor", [1.5, 2.5, 5.0, 20.0])
    @pytest.mark.parametrize("theta", [0.15 * np.pi, 0.3 * np.pi, 0.5 * np.pi, 0.85 * np.pi])
    def test_kerr_04_analytic_inverse_identity(
        self, mass: float, spin_frac: float, r_factor: float, theta: float
    ) -> None:
        """KERR-04: Verifies g^{mu alpha} g_{alpha nu} = delta_mu^nu across parameter space."""
        spin = spin_frac * mass
        metric = KerrMetric(mass=mass, spin=spin)
        r = r_factor * metric.horizon_radius

        g_cov = metric.g_cov(r, theta)
        g_contra = metric.g_contra(r, theta)

        product = g_contra @ g_cov
        identity = np.eye(4, dtype=np.float64)

        max_err = float(np.max(np.abs(product - identity)))
        assert max_err <= 1e-13, (
            f"KERR-04 inverse identity failed: max_err = {max_err:.2e} at M={mass}, a={spin}, r={r}, theta={theta}"
        )

    @pytest.mark.parametrize("spin", [-0.9, -0.4, 0.0, 0.4, 0.9])
    @pytest.mark.parametrize("theta", [np.pi / 6.0, np.pi / 2.0, 2.0])
    def test_kerr_05_independent_numerical_inverse(self, spin: float, theta: float) -> None:
        """KERR-05: Compares analytic g^{mu nu} against numpy.linalg.inv(g_cov)."""
        mass = 1.0
        metric = KerrMetric(mass=mass, spin=spin)
        r = 3.5

        g_cov = metric.g_cov(r, theta)
        g_contra_analytic = metric.g_contra(r, theta)
        g_contra_numerical = np.linalg.inv(g_cov)

        max_diff = float(np.max(np.abs(g_contra_analytic - g_contra_numerical)))
        assert max_diff <= 1e-13, f"KERR-05 numerical inversion discrepancy {max_diff:.2e} > 1e-13"


# =============================================================================
# Test Suite: KERR-06 (Metric Determinant Identity)
# =============================================================================

class TestKerrMetricDeterminant:
    """KERR-06: Verification of metric determinant det(g) = -Sigma^2 sin^2(theta)."""

    @pytest.mark.parametrize("mass", [0.5, 1.0, 2.5])
    @pytest.mark.parametrize("spin", [-0.8, -0.2, 0.0, 0.4, 0.9])
    @pytest.mark.parametrize("r", [2.5, 5.0, 12.0])
    @pytest.mark.parametrize("theta", [0.2, np.pi / 4.0, np.pi / 2.0, 2.6])
    def test_kerr_06_determinant_identity(self, mass: float, spin: float, r: float, theta: float) -> None:
        """Verifies det(g) = -Sigma^2 sin^2(theta) against both analytic method and numpy.linalg.det."""
        metric = KerrMetric(mass=mass, spin=spin * mass)
        test_r = r * mass

        # Numerical determinant from covariant matrix
        g_cov = metric.g_cov(test_r, theta)
        num_det = float(np.linalg.det(g_cov))

        # Analytic formula
        sigma_val = metric.sigma(test_r, theta)
        sin_theta = np.sin(theta)
        analytic_det = -((sigma_val * sin_theta) ** 2)

        # Method evaluation
        method_det = metric.det_cov(test_r, theta)

        # 1. Method matches analytic formula exactly
        assert method_det == analytic_det

        # 2. Matrix determinant matches analytic formula to high relative precision
        rel_err = abs(num_det - analytic_det) / abs(analytic_det)
        assert rel_err <= 1e-12, f"KERR-06 determinant error {rel_err:.2e} > 1e-12 at r={test_r}, theta={theta}"


# =============================================================================
# Test Suite: KERR-07 (Analytic Inverse Derivatives vs Finite Differences)
# =============================================================================

class TestKerrInverseDerivatives:
    """KERR-07: Verification of partial_r g^{alpha beta} and partial_theta g^{alpha beta}
    against independent 4th-order central finite differences.
    """

    @pytest.mark.parametrize("mass", [0.5, 1.0, 2.0])
    @pytest.mark.parametrize("spin", [-0.85, -0.4, 0.0, 0.4, 0.85])
    @pytest.mark.parametrize("theta", [0.25, np.pi / 4.0, np.pi / 2.0, 2.4])
    def test_kerr_07_radial_derivatives(self, mass: float, spin: float, theta: float) -> None:
        """Verifies partial_r g^{alpha beta} across full 4x4 tensor against 4th-order central FD."""
        actual_spin = spin * mass
        metric = KerrMetric(mass=mass, spin=actual_spin)
        r = 3.5 * mass

        analytic_dg_dr = metric.dg_contra_dr(r, theta)
        fd_dg_dr = finite_difference_4th_order(
            lambda r_val: metric.g_contra(r_val, theta),
            x0=r,
            h=1e-5,
        )

        max_err = float(np.max(np.abs(analytic_dg_dr - fd_dg_dr)))
        assert max_err <= 1e-8, (
            f"KERR-07 radial derivative failed: max_err={max_err:.2e} at M={mass}, a={actual_spin}, theta={theta}"
        )

    @pytest.mark.parametrize("mass", [0.5, 1.0, 2.0])
    @pytest.mark.parametrize("spin", [-0.85, -0.4, 0.0, 0.4, 0.85])
    @pytest.mark.parametrize("r_factor", [2.5, 4.0, 8.0])
    @pytest.mark.parametrize("theta", [0.3, np.pi / 4.0, np.pi / 2.0, 2.3])
    def test_kerr_07_polar_derivatives(self, mass: float, spin: float, r_factor: float, theta: float) -> None:
        """Verifies partial_theta g^{alpha beta} across full 4x4 tensor against 4th-order central FD."""
        actual_spin = spin * mass
        metric = KerrMetric(mass=mass, spin=actual_spin)
        r = r_factor * mass

        analytic_dg_dtheta = metric.dg_contra_dtheta(r, theta)
        fd_dg_dtheta = finite_difference_4th_order(
            lambda th_val: metric.g_contra(r, th_val),
            x0=theta,
            h=1e-5,
        )

        max_err = float(np.max(np.abs(analytic_dg_dtheta - fd_dg_dtheta)))
        assert max_err <= 1e-8, (
            f"KERR-07 polar derivative failed: max_err={max_err:.2e} at M={mass}, a={actual_spin}, r={r}, theta={theta}"
        )

    def test_kerr_07_full_dg_contra_all_tensor(self) -> None:
        """Verifies dg_contra_all 3D tensor shape and exact stationarity/axisymmetry zeros."""
        metric = KerrMetric(mass=1.0, spin=0.7)
        r = 4.0
        theta = np.pi / 3.0

        dg_all = metric.dg_contra_all(r, theta)
        assert dg_all.shape == (4, 4, 4)

        # Stationarity: partial_0 g^{alpha beta} == 0
        np.testing.assert_array_equal(dg_all[0, :, :], 0.0)

        # Axisymmetry: partial_3 g^{alpha beta} == 0
        np.testing.assert_array_equal(dg_all[3, :, :], 0.0)

        # Radial slice matches dg_contra_dr
        np.testing.assert_array_equal(dg_all[1, :, :], metric.dg_contra_dr(r, theta))

        # Polar slice matches dg_contra_dtheta
        np.testing.assert_array_equal(dg_all[2, :, :], metric.dg_contra_dtheta(r, theta))

    @pytest.mark.parametrize("mass", [0.8, 1.0, 2.5])
    @pytest.mark.parametrize("spin_ratio", [-0.85, -0.4, 0.4, 0.85])
    @pytest.mark.parametrize("r_factor", [2.5, 4.0, 10.0])
    @pytest.mark.parametrize("theta", [np.pi / 6.0, np.pi / 4.0, 2.3])
    def test_kerr_07_polar_derivative_g_tt_exact_and_regression(
        self, mass: float, spin_ratio: float, r_factor: float, theta: float
    ) -> None:
        """KERR-07 Regression: Validates partial_theta g^{tt} against both exact formula and 5-pt FD,
        and confirms explicit rejection of the erroneous formula reported in prior documentation:
            erroneous = 2 a^2 cos(theta) sin(theta) [ Delta^2 sin^2(theta) - (r^2+a^2)^2 ] / (Sigma^2 Delta)
        """
        spin = spin_ratio * mass
        metric = KerrMetric(mass=mass, spin=spin)
        r = r_factor * mass

        prod_val = metric.dg_contra_dtheta(r, theta)[IDX_X0, IDX_X0]
        sigma_val = metric.sigma(r, theta)
        delta_val = metric.delta(r)
        a2 = spin * spin
        r2_plus_a2 = r * r + a2

        # Mathematically exact formula
        exact_formula = -(4.0 * mass * a2 * r * r2_plus_a2 * np.sin(theta) * np.cos(theta)) / (
            sigma_val * sigma_val * delta_val
        )
        assert abs(prod_val - exact_formula) <= 1e-15

        # Independent scale-aware 4th-order central finite difference
        h = 1e-5 * max(theta, 1.0)
        fd_val = finite_difference_4th_order(
            lambda th: metric.g_contra(r, th)[IDX_X0, IDX_X0],
            x0=theta,
            h=h,
        )
        abs_err = abs(prod_val - fd_val)
        assert abs_err <= 1e-8

        # Explicit rejection of erroneous formula (which differs by >= 24% across domain)
        sin_th = np.sin(theta)
        cos_th = np.cos(theta)
        erroneous_formula = (
            2.0 * a2 * cos_th * sin_th * (delta_val * delta_val * sin_th * sin_th - r2_plus_a2 * r2_plus_a2)
        ) / (sigma_val * sigma_val * delta_val)
        diff_from_erroneous = abs(prod_val - erroneous_formula)
        rel_diff_from_erroneous = diff_from_erroneous / max(abs(prod_val), 1e-15)
        assert rel_diff_from_erroneous > 0.15, (
            f"Regression failed: production derivative matched erroneous formula! rel_diff={rel_diff_from_erroneous:.2e}"
        )

    @pytest.mark.parametrize("mass", [0.5, 1.0, 2.0])
    @pytest.mark.parametrize("spin_ratio", [-0.9, -0.4, 0.0, 0.5, 0.9])
    @pytest.mark.parametrize("r_factor", [2.5, 5.0, 12.0])
    @pytest.mark.parametrize("theta", [0.25, np.pi / 4.0, np.pi / 2.0, 2.4])
    def test_kerr_07_scale_aware_finite_difference_all_components(
        self, mass: float, spin_ratio: float, r_factor: float, theta: float
    ) -> None:
        """KERR-07: Component-by-component validation of all non-zero derivatives with scale-aware FD."""
        spin = spin_ratio * mass
        metric = KerrMetric(mass=mass, spin=spin)
        r = r_factor * mass

        hr = 1e-5 * max(r, 1.0)
        hth = 1e-5 * max(theta, 1.0)

        analytic_dr = metric.dg_contra_dr(r, theta)
        analytic_dth = metric.dg_contra_dtheta(r, theta)

        fd_dr = finite_difference_4th_order(lambda r_val: metric.g_contra(r_val, theta), x0=r, h=hr)
        fd_dth = finite_difference_4th_order(lambda th_val: metric.g_contra(r, th_val), x0=theta, h=hth)

        for mu, nu in [(IDX_X0, IDX_X0), (IDX_X0, IDX_PHI), (IDX_R, IDX_R), (IDX_THETA, IDX_THETA), (IDX_PHI, IDX_PHI)]:
            # Radial derivative
            abs_err_r = abs(analytic_dr[mu, nu] - fd_dr[mu, nu])
            scale_r = max(abs(analytic_dr[mu, nu]), abs(fd_dr[mu, nu]), 1.0 / mass)
            rel_err_r = abs_err_r / scale_r
            assert rel_err_r <= 1e-8, (
                f"Radial rel_err too large at ({mu},{nu}): {rel_err_r:.2e} (abs={abs_err_r:.2e})"
            )

            # Polar derivative
            abs_err_th = abs(analytic_dth[mu, nu] - fd_dth[mu, nu])
            scale_th = max(abs(analytic_dth[mu, nu]), abs(fd_dth[mu, nu]), 1.0)
            rel_err_th = abs_err_th / scale_th
            assert rel_err_th <= 1e-8, (
                f"Polar rel_err too large at ({mu},{nu}): {rel_err_th:.2e} (abs={abs_err_th:.2e})"
            )


# =============================================================================
# Test Suite: KERR-08 (Schwarzschild Limit a = 0)
# =============================================================================

class TestKerrSchwarzschildLimit:
    """KERR-08: Verification that KerrMetric(mass=M, spin=0) reduces identically to SchwarzschildMetric(mass=M)."""

    @pytest.mark.parametrize("mass", [0.5, 1.0, 2.5])
    @pytest.mark.parametrize("r", [2.5, 4.0, 8.0, 25.0])
    @pytest.mark.parametrize("theta", [0.2, np.pi / 4.0, np.pi / 2.0, 2.5])
    def test_kerr_08_schwarzschild_reduction(self, mass: float, r: float, theta: float) -> None:
        """KerrMetric with a = 0 reproduces SchwarzschildMetric covariant, contravariant, and derivative tensors."""
        test_r = r * mass
        kerr_zero = KerrMetric(mass=mass, spin=0.0)
        schw = SchwarzschildMetric(mass=mass)

        # 1. Horizon radius
        assert kerr_zero.horizon_radius == schw.horizon_radius

        # 2. Covariant metric tensor: double-precision equality to machine epsilon
        g_kerr = kerr_zero.g_cov(test_r, theta)
        g_schw = schw.g_cov(test_r, theta)
        np.testing.assert_allclose(g_kerr, g_schw, rtol=1e-15, atol=1e-15)

        # Cross terms are identically zero
        assert g_kerr[IDX_X0, IDX_PHI] == 0.0
        assert g_kerr[IDX_PHI, IDX_X0] == 0.0

        # 3. Contravariant metric tensor: double-precision equality to machine epsilon
        g_inv_kerr = kerr_zero.g_contra(test_r, theta)
        g_inv_schw = schw.g_contra(test_r, theta)
        np.testing.assert_allclose(g_inv_kerr, g_inv_schw, rtol=1e-15, atol=1e-15)

        # 4. Radial derivatives: double-precision equality
        dg_dr_kerr = kerr_zero.dg_contra_dr(test_r, theta)
        dg_dr_schw = schw.dg_contra_dr(test_r, theta)
        np.testing.assert_allclose(dg_dr_kerr, dg_dr_schw, rtol=1e-14, atol=1e-14)

        # 5. Polar derivatives: double-precision equality
        dg_dth_kerr = kerr_zero.dg_contra_dtheta(test_r, theta)
        dg_dth_schw = schw.dg_contra_dtheta(test_r, theta)
        np.testing.assert_allclose(dg_dth_kerr, dg_dth_schw, rtol=1e-14, atol=1e-14)


# =============================================================================
# Test Suite: KERR-09 (Spin-Sign Behavior a -> -a)
# =============================================================================

class TestKerrSpinSignBehavior:
    """KERR-09: Verification of metric transformation under spin parity reversal a -> -a."""

    @pytest.mark.parametrize("spin_mag", [0.2, 0.5, 0.9, 1.0])
    @pytest.mark.parametrize("theta", [np.pi / 4.0, np.pi / 3.0, 2.2])
    def test_kerr_09_spin_sign_parity(self, spin_mag: float, theta: float) -> None:
        """Verifies that changing a -> -a preserves diagonal components and reverses cross terms and their derivatives."""
        mass = 1.0
        r = 3.5

        kerr_pos = KerrMetric(mass=mass, spin=+spin_mag)
        kerr_neg = KerrMetric(mass=mass, spin=-spin_mag)

        # 1. Horizon radius is even in spin
        assert kerr_pos.horizon_radius == kerr_neg.horizon_radius
        assert kerr_pos.inner_horizon_radius == kerr_neg.inner_horizon_radius

        # 2. Covariant metric components
        g_pos = kerr_pos.g_cov(r, theta)
        g_neg = kerr_neg.g_cov(r, theta)

        # Diagonals are strictly even functions of a: g_{mu mu}(-a) == g_{mu mu}(a)
        for i in range(4):
            assert g_pos[i, i] == g_neg[i, i]

        # Off-diagonal t-phi is strictly odd function of a: g_{t phi}(-a) == -g_{t phi}(a)
        assert g_neg[IDX_X0, IDX_PHI] == -g_pos[IDX_X0, IDX_PHI]
        assert g_neg[IDX_PHI, IDX_X0] == -g_pos[IDX_PHI, IDX_X0]

        # 3. Contravariant metric components
        g_inv_pos = kerr_pos.g_contra(r, theta)
        g_inv_neg = kerr_neg.g_contra(r, theta)

        for i in range(4):
            assert g_inv_pos[i, i] == g_inv_neg[i, i]

        assert g_inv_neg[IDX_X0, IDX_PHI] == -g_inv_pos[IDX_X0, IDX_PHI]
        assert g_inv_neg[IDX_PHI, IDX_X0] == -g_inv_pos[IDX_PHI, IDX_X0]

        # 4. Derivative components
        # Radial derivatives
        dg_dr_pos = kerr_pos.dg_contra_dr(r, theta)
        dg_dr_neg = kerr_neg.dg_contra_dr(r, theta)

        for i in range(4):
            assert dg_dr_pos[i, i] == dg_dr_neg[i, i]

        assert dg_dr_neg[IDX_X0, IDX_PHI] == -dg_dr_pos[IDX_X0, IDX_PHI]
        assert dg_dr_neg[IDX_PHI, IDX_X0] == -dg_dr_pos[IDX_PHI, IDX_X0]

        # Polar derivatives
        dg_dth_pos = kerr_pos.dg_contra_dtheta(r, theta)
        dg_dth_neg = kerr_neg.dg_contra_dtheta(r, theta)

        for i in range(4):
            assert dg_dth_pos[i, i] == dg_dth_neg[i, i]

        assert dg_dth_neg[IDX_X0, IDX_PHI] == -dg_dth_pos[IDX_X0, IDX_PHI]
        assert dg_dth_neg[IDX_PHI, IDX_X0] == -dg_dth_pos[IDX_PHI, IDX_X0]


# =============================================================================
# Test Suite: KERR-10 (Horizon and Extremal Behavior)
# =============================================================================

class TestKerrHorizonAndExtremalBehavior:
    """KERR-10: Verification of event horizons and extremal black hole behavior (|a| = M)."""

    def test_horizon_radii_formulas(self) -> None:
        """Verifies exact analytic horizon radii across spin regimes."""
        mass = 1.0

        # a = 0 (Schwarzschild): r_+ = 2M, r_- = 0
        k0 = KerrMetric(mass=mass, spin=0.0)
        assert k0.horizon_radius == 2.0
        assert k0.inner_horizon_radius == 0.0

        # a = 0.6: r_+ = 1 + sqrt(1 - 0.36) = 1.8, r_- = 1 - 0.8 = 0.2
        k_sub = KerrMetric(mass=mass, spin=0.6)
        assert np.isclose(k_sub.horizon_radius, 1.8)
        assert np.isclose(k_sub.inner_horizon_radius, 0.2)

        # a = -0.8: r_+ = 1 + sqrt(1 - 0.64) = 1.6, r_- = 1 - 0.6 = 0.4
        k_neg = KerrMetric(mass=mass, spin=-0.8)
        assert np.isclose(k_neg.horizon_radius, 1.6)
        assert np.isclose(k_neg.inner_horizon_radius, 0.4)

        # Extremal a = +M: r_+ = r_- = M
        k_ext_pos = KerrMetric(mass=mass, spin=+1.0)
        assert k_ext_pos.is_extremal is True
        assert np.isclose(k_ext_pos.horizon_radius, 1.0)
        assert np.isclose(k_ext_pos.inner_horizon_radius, 1.0)

        # Extremal a = -M: r_+ = r_- = M
        k_ext_neg = KerrMetric(mass=mass, spin=-1.0)
        assert k_ext_neg.is_extremal is True
        assert np.isclose(k_ext_neg.horizon_radius, 1.0)
        assert np.isclose(k_ext_neg.inner_horizon_radius, 1.0)

    @pytest.mark.parametrize("spin", [-1.0, -0.6, 0.0, 0.6, 1.0])
    def test_valid_evaluation_near_horizon(self, spin: float) -> None:
        """Confirms that valid exterior evaluations near horizon (r = r_+ + eps) succeed cleanly."""
        metric = KerrMetric(mass=1.0, spin=spin)
        r_plus = metric.horizon_radius
        r_test = r_plus + 0.05

        g_cov = metric.g_cov(r_test, np.pi / 2.0)
        g_contra = metric.g_contra(r_test, np.pi / 2.0)

        assert np.all(np.isfinite(g_cov))
        assert np.all(np.isfinite(g_contra))

        # Inversion identity holds near horizon (with conditioning margin)
        prod = g_contra @ g_cov
        np.testing.assert_allclose(prod, np.eye(4), atol=1e-10)

    @pytest.mark.parametrize(
        "spin_val, expected_extremal",
        [
            (1.0, True),
            (-1.0, True),
            (0.0, False),
            (0.99, False),
            (1.0 - 1e-14, False),
            (-1.0 + 1e-14, False),
        ],
    )
    def test_exact_extremality_classification(self, spin_val: float, expected_extremal: bool) -> None:
        """Verifies exact extremality classification |a| == M without approximate conflation."""
        mass = 1.0
        if not expected_extremal:
            assert abs(spin_val) != mass, f"Spin {spin_val} is not representably distinct from mass {mass}"
        metric = KerrMetric(mass=mass, spin=spin_val)
        assert metric.is_extremal is expected_extremal


# =============================================================================
# Test Suite: KERR-11 (Near-Horizon Stability and Factorized Delta)
# =============================================================================

class TestKerrNearHorizonStability:
    """KERR-11: Numerical stability of KerrMetric evaluations near event horizons."""

    @pytest.mark.parametrize("spin_ratio", [0.0, 0.5, -0.5, 0.9, -0.9, 0.99, -0.99, 1.0, -1.0])
    @pytest.mark.parametrize("dr", [1e-2, 1e-4, 1e-6, 1e-8])
    @pytest.mark.parametrize("theta", [np.pi / 2.0, np.pi / 4.0])
    def test_near_horizon_multiscale_evaluation(
        self, spin_ratio: float, dr: float, theta: float
    ) -> None:
        """Verifies tensor finiteness and condition-governed accuracy across multiscale near-horizon offsets.

        Distinguishes strictly between:
        1. Tensor component finiteness (holds everywhere on the open domain r > r_+).
        2. Accurate numerical inversion (holds when cond(g) < 1/eps_mach).
        3. Condition-driven accuracy loss (when cond(g) >= 1/eps_mach, inversion product
           loses significance in float64 without indicating an implementation defect).
        """
        mass = 1.0
        a = spin_ratio * mass
        metric = KerrMetric(mass=mass, spin=a)
        r_plus = metric.horizon_radius
        r = r_plus + dr

        # 1. Coordinate must be strictly exterior and representably distinct from r_+
        assert r > r_plus, f"r = {r:.16e} is not representably distinct from r_+ = {r_plus:.16e} at dr = {dr}"

        # 2. Delta(r) must be strictly positive
        delta_val = metric.delta(r)
        assert delta_val > 0.0, f"Delta(r) must be strictly positive, got {delta_val} at a={a}, dr={dr}"

        # 3-5. Tensor and derivative evaluations must be finite everywhere
        g_cov = metric.g_cov(r, theta)
        g_contra = metric.g_contra(r, theta)
        dg_dr = metric.dg_contra_dr(r, theta)
        dg_dth = metric.dg_contra_dtheta(r, theta)

        assert np.all(np.isfinite(g_cov)), "All components of g_cov must be finite"
        assert np.all(np.isfinite(g_contra)), "All components of g_contra must be finite"
        assert np.all(np.isfinite(dg_dr)), "All components of dg_contra_dr must be finite"
        assert np.all(np.isfinite(dg_dth)), "All components of dg_contra_dtheta must be finite"

        # 6. Inversion identity and condition number
        prod = g_contra @ g_cov
        inv_err = float(np.max(np.abs(prod - np.eye(4))))
        cond_est = float(np.linalg.cond(g_cov))
        inv_eps = 1.0 / np.finfo(np.float64).eps  # ~ 4.5e15

        # Rigorous condition-based verification:
        # Well-conditioned regime (cond < 1e10): high accuracy (inv_err <= 1e-8)
        # Moderate conditioning (1e10 <= cond < 1e14): moderate accuracy (inv_err <= 1e-4)
        # Severely ill-conditioned (cond >= inv_eps):
        #   Floating-point arithmetic loses all significant figures due to condition number.
        #   Finiteness is verified, but false claims of accurate inversion are avoided.
        if cond_est < 1e10:
            assert inv_err <= 1e-8, f"Inversion error {inv_err:.2e} exceeded tolerance at cond = {cond_est:.2e}"
        elif cond_est < 1e14:
            assert inv_err <= 1e-4, f"Inversion error {inv_err:.2e} exceeded tolerance at cond = {cond_est:.2e}"
        else:
            # Condition number exceeds 1/eps_mach (~4.5e15) - accuracy loss is mathematically unavoidable
            assert np.isfinite(inv_err), f"Inversion error must be finite, got {inv_err}"

        # 7. Determinant identity against numpy.linalg.det
        det_anal = metric.det_cov(r, theta)
        assert det_anal < 0.0, f"Analytic determinant must be strictly negative, got {det_anal}"
        det_num = float(np.linalg.det(g_cov))
        rel_det_err = abs(det_num - det_anal) / abs(det_anal)

        # Numerical determinant via LU decomposition is reliable only when cond(g) < 1e14
        if cond_est < 1e14:
            assert rel_det_err <= 1e-6, (
                f"Determinant error {rel_det_err:.2e} exceeded tolerance at cond = {cond_est:.2e}"
            )
        else:
            assert np.isfinite(rel_det_err), f"Relative determinant error must be finite, got {rel_det_err}"

    @pytest.mark.parametrize("spin_ratio", [0.0, 0.5, -0.5, 0.9, -0.9, 0.99, -0.99, 1.0, -1.0])
    @pytest.mark.parametrize("dr", [1e-2, 1e-4, 1e-6, 1e-8])
    def test_factorized_delta_benchmark_a_represented_inputs(self, spin_ratio: float, dr: float) -> None:
        """Benchmark A: Exact represented-input reference.

        Converts the actual binary64 values passed to the production implementation
        into 60-digit Decimal without losing their exact represented values (using
        Decimal.from_float). Verifies that factorized evaluation in float64 achieves
        near-exact bitwise agreement (<= 1e-15 relative error) with the exact represented
        algebraic factorization.
        """
        getcontext().prec = 60
        mass = 1.0
        a = spin_ratio * mass
        metric = KerrMetric(mass=mass, spin=a)
        r_plus = metric.horizon_radius
        r_minus = metric.inner_horizon_radius
        r = r_plus + dr

        assert r > r_plus, f"r={r} not representably distinct from r_+={r_plus}"

        # Exact represented inputs converted to Decimal
        r_dec = Decimal.from_float(r)
        r_plus_dec = Decimal.from_float(r_plus)
        r_minus_dec = Decimal.from_float(r_minus)

        # High-precision reference evaluation on exact represented inputs
        delta_rep_dec = (r_dec - r_plus_dec) * (r_dec - r_minus_dec)
        delta_rep_float = float(delta_rep_dec)

        # Production float64 factorized evaluation
        delta_prod = metric.delta(r)
        rel_err = abs(delta_prod - delta_rep_float) / delta_rep_float

        assert rel_err <= 1e-15, (
            f"Benchmark A failed: production Delta {delta_prod:.16e} differed from exact "
            f"represented reference {delta_rep_float:.16e} with rel_err = {rel_err:.2e}"
        )

    @pytest.mark.parametrize("spin_ratio", [0.0, 0.5, -0.5, 0.9, -0.9, 0.99, -0.99, 1.0, -1.0])
    @pytest.mark.parametrize("dr", [1e-2, 1e-4, 1e-6, 1e-8])
    def test_factorized_delta_benchmark_b_mathematical_inputs(self, spin_ratio: float, dr: float) -> None:
        """Benchmark B: High-precision mathematical-input reference.

        Constructs M, a, and dr directly from their intended decimal values as pure 60-digit
        Decimals. Computes horizon radii and Delta entirely in Decimal at high precision:
            Delta_math = (r_math - r_{+, math}) * (r_math - r_{-, math})
        Compares production float64 Delta against float(Delta_math).

        Note on Limitation:
        The relative difference between production Delta and float(Delta_math) is bounded by
        the 1-ULP binary64 representation roundoff of r = r_+ + dr (which introduces a relative
        offset perturbation ~ eps_mach / dr). At dr = 1e-8, this representation discrepancy is
        ~ 1e-8. For extremal black holes, naive polynomial evaluation yields 0.0 (100% loss of
        significance), whereas factorized Delta matches the mathematical reference to 8 digits.
        """
        getcontext().prec = 60
        mass = 1.0
        a = spin_ratio * mass
        metric = KerrMetric(mass=mass, spin=a)
        r_plus = metric.horizon_radius
        r_prod = r_plus + dr

        assert r_prod > r_plus, f"r={r_prod} not representably distinct from r_+={r_plus}"

        # Pure mathematical inputs in 60-digit Decimal
        M_dec = Decimal(str(mass))
        a_dec = Decimal(str(a))
        dr_dec = Decimal(str(dr))
        disc_dec = M_dec * M_dec - a_dec * a_dec
        if disc_dec < Decimal(0):
            disc_dec = Decimal(0)
        sqrt_disc = disc_dec.sqrt()
        r_plus_math = M_dec + sqrt_disc
        r_minus_math = M_dec - sqrt_disc
        r_math = r_plus_math + dr_dec

        # Mathematical high-precision reference Delta
        delta_math_dec = (r_math - r_plus_math) * (r_math - r_minus_math)
        delta_math_float = float(delta_math_dec)

        # Production float64 result
        delta_prod = metric.delta(r_prod)
        rel_err = abs(delta_prod - delta_math_float) / delta_math_float

        assert rel_err <= 1e-7, (
            f"Benchmark B failed: factorized delta {delta_prod:.16e} differed from mathematical "
            f"reference {delta_math_float:.16e} with rel_err = {rel_err:.2e} at a={a}, dr={dr}"
        )

        # For extremal black hole at dr = 1e-8, confirm naive polynomial fails while factorized Delta succeeds
        if abs(spin_ratio) == 1.0 and dr == 1e-8:
            naive_poly = r_prod * r_prod - 2.0 * mass * r_prod + a * a
            assert naive_poly == 0.0, "Expected naive polynomial Delta to catastrophically cancel to zero in float64"
            assert delta_prod > 0.0, "Factorized Delta must remain strictly positive"

    @pytest.mark.parametrize("spin_ratio", [0.0, 0.9, 0.99, 1.0, -1.0])
    @pytest.mark.parametrize("theta", [np.pi / 2.0, np.pi / 4.0])
    def test_closest_representable_exterior_radius_nextafter(
        self, spin_ratio: float, theta: float
    ) -> None:
        """Verifies evaluation at the single closest representable exterior radius: r_next = nextafter(r_+, inf).

        Validates:
        1. r_next > r_+ strictly.
        2. Domain validator accepts r_next.
        3. Factorized Delta(r_next) > 0 strictly.
        4. Metric, inverse metric, and derivatives are strictly finite.
        5. Explains that for Kerr (a != 0), condition number cond(g) >> 1/eps_mach causes
           loss of inversion accuracy in float64 matrix multiplication, which is an unavoidable
           property of the Boyer-Lindquist coordinate horizon, not an implementation defect.
        """
        mass = 1.0
        a = spin_ratio * mass
        metric = KerrMetric(mass=mass, spin=a)
        r_plus = metric.horizon_radius
        r_next = np.nextafter(r_plus, np.inf)

        # 1. r_next is strictly greater than r_+
        assert r_next > r_plus, f"nextafter failed to produce distinct radius from r_+ = {r_plus}"

        # 2. Domain validator accepts r_next without exception
        metric._validate_coordinates(r_next, theta)

        # 3. Factorized Delta is strictly positive
        delta_val = metric.delta(r_next)
        assert delta_val > 0.0, f"Delta(r_next) must be positive, got {delta_val}"

        # 4. All tensor and derivative components are strictly finite
        g_cov = metric.g_cov(r_next, theta)
        g_contra = metric.g_contra(r_next, theta)
        dg_dr = metric.dg_contra_dr(r_next, theta)
        dg_dth = metric.dg_contra_dtheta(r_next, theta)

        assert np.all(np.isfinite(g_cov)), "g_cov must be finite at nextafter"
        assert np.all(np.isfinite(g_contra)), "g_contra must be finite at nextafter"
        assert np.all(np.isfinite(dg_dr)), "dg_contra_dr must be finite at nextafter"
        assert np.all(np.isfinite(dg_dth)), "dg_contra_dtheta must be finite at nextafter"

        # 5. Measure and record inversion error and determinant error
        prod = g_contra @ g_cov
        inv_err = float(np.max(np.abs(prod - np.eye(4))))
        assert np.isfinite(inv_err), f"Inversion error must be finite, got {inv_err}"

        # For diagonal Schwarzschild metric (a = 0), inversion is exact to machine epsilon
        if spin_ratio == 0.0:
            assert inv_err <= 1e-14, f"Schwarzschild inversion at nextafter failed: {inv_err:.2e}"

    @pytest.mark.parametrize(
        "mass,spin,expected_extremal",
        [
            (1.0, 1.0, True),
            (1.0, -1.0, True),
            (1.0, np.nextafter(1.0, 0.0), False),
            (1.0, -np.nextafter(1.0, 0.0), False),
            (1.0, 1.0 - 1e-15, False),
            (1.0, -(1.0 - 1e-15), False),
            (1.0, 1.0 - 1e-14, False),
            (1.0, -(1.0 - 1e-14), False),
            (1.0, 1.0 - 1e-12, False),
            (1.0, -(1.0 - 1e-12), False),
            (1.0, 0.99, False),
            (1.0, -0.99, False),
            (2.5, 2.5, True),
            (2.5, np.nextafter(2.5, 0.0), False),
            (2.5, -np.nextafter(2.5, 0.0), False),
            (2.5, 2.5 * (1.0 - 1e-12), False),
        ],
    )
    def test_near_extremal_horizon_radii_and_exterior_delta(
        self, mass: float, spin: float, expected_extremal: bool
    ) -> None:
        """Verifies horizon radii and exterior Delta accuracy near extremality.

        Validates:
        1. Exact extremality classification (|a| == M vs |a| < M).
        2. Positive horizon separation (r_+ - r_- > 0 and r_+ > r_-) for all sub-extremal spins,
           distinguishing sub-extremal horizons from unphysical degenerate collapse.
        3. Finiteness of r_+ and r_-.
        4. Strict positivity and finiteness of exterior Delta(r_next) where r_next = nextafter(r_+, inf).
        5. Agreement of r_+ and r_- with 60-digit Decimal references computed from exact represented
           float inputs (Decimal.from_float) to <= 1e-15 relative tolerance.
        """
        getcontext().prec = 60
        metric = KerrMetric(mass=mass, spin=spin)

        # 1. Exact extremality classification
        assert metric.is_extremal is expected_extremal

        r_plus = metric.horizon_radius
        r_minus = metric.inner_horizon_radius

        # 2. Finiteness of radii
        assert np.isfinite(r_plus), f"r_+ must be finite, got {r_plus}"
        assert np.isfinite(r_minus), f"r_- must be finite, got {r_minus}"

        # 3. Horizon separation and ordering
        separation = r_plus - r_minus
        if expected_extremal:
            assert r_plus == mass
            assert r_minus == mass
            assert separation == 0.0
        else:
            assert r_plus > r_minus, (
                f"Outer horizon must strictly exceed inner horizon for sub-extremal spin: "
                f"r_+ = {r_plus}, r_- = {r_minus}, a = {spin}"
            )
            assert separation > 0.0, (
                f"Horizon separation must be strictly positive for sub-extremal spin, got {separation}"
            )

        # 4. Strict positivity and finiteness of exterior Delta at adjacent float
        r_next = np.nextafter(r_plus, np.inf)
        assert r_next > r_plus
        delta_next = metric.delta(r_next)
        assert np.isfinite(delta_next), f"Delta(r_next) must be finite, got {delta_next}"
        assert delta_next > 0.0, f"Delta(r_next) must be strictly positive, got {delta_next}"

        # 5. Agreement with high-precision Decimal reference from represented float inputs
        mass_dec = Decimal.from_float(mass)
        spin_dec = Decimal.from_float(spin)
        disc_ref = (mass_dec - abs(spin_dec)) * (mass_dec + abs(spin_dec))
        sqrt_disc_ref = disc_ref.sqrt()
        r_plus_ref = mass_dec + sqrt_disc_ref
        r_minus_ref = mass_dec - sqrt_disc_ref

        err_r_plus = abs(Decimal.from_float(r_plus) - r_plus_ref) / r_plus_ref
        err_r_minus = abs(Decimal.from_float(r_minus) - r_minus_ref) / r_minus_ref

        assert float(err_r_plus) <= 1e-15, (
            f"r_+ relative error vs Decimal reference exceeded tolerance: {err_r_plus}"
        )
        assert float(err_r_minus) <= 1e-15, (
            f"r_- relative error vs Decimal reference exceeded tolerance: {err_r_minus}"
        )

    @pytest.mark.parametrize(
        "mass,spin",
        [
            # M = 1.0 series
            (1.0, 0.0),
            (1.0, 1e-16),
            (1.0, -1e-16),
            (1.0, 1e-12),
            (1.0, -1e-12),
            (1.0, 1e-8),
            (1.0, -1e-8),
            (1.0, 1e-4),
            (1.0, -1e-4),
            (1.0, 0.1),
            (1.0, -0.1),
            (1.0, 0.5),
            (1.0, -0.5),
            (1.0, 0.9),
            (1.0, -0.9),
            (1.0, 1.0 - 1e-12),
            (1.0, -(1.0 - 1e-12)),
            (1.0, 1.0),
            (1.0, -1.0),
            # M = 2.5 series
            (2.5, 0.0),
            (2.5, 2.5 * 1e-16),
            (2.5, -2.5 * 1e-16),
            (2.5, 2.5 * 1e-12),
            (2.5, -2.5 * 1e-12),
            (2.5, 2.5 * 1e-8),
            (2.5, -2.5 * 1e-8),
            (2.5, 2.5 * 1e-4),
            (2.5, -2.5 * 1e-4),
            (2.5, 2.5 * 0.1),
            (2.5, -2.5 * 0.1),
            (2.5, 2.5 * 0.5),
            (2.5, -2.5 * 0.5),
            (2.5, 2.5 * 0.9),
            (2.5, -2.5 * 0.9),
            (2.5, 2.5 * (1.0 - 1e-12)),
            (2.5, -2.5 * (1.0 - 1e-12)),
            (2.5, 2.5),
            (2.5, -2.5),
            # Large finite spin (verifying overflow-safe evaluation)
            (1.0e154, 1.0e154),
            (1.0e154, 0.5e154),
        ],
    )
    def test_inner_horizon_radius_stability_small_and_large_spins(
        self, mass: float, spin: float
    ) -> None:
        """Verifies inner horizon stability across small, intermediate, near-extremal, and large spins.

        Validates:
        1. Exact zero spin: r_- == 0.0 exactly and r_+ == 2M.
        2. Non-zero sub-extremal spins: r_- > 0.0 strictly (no collapse to zero due to catastrophic cancellation)
           and r_+ > r_- strictly.
        3. Extremal spins (|a| == M): r_+ == r_- == M exactly.
        4. Parity invariance: positive and negative spins yield identical horizon radii.
        5. Finiteness and non-negativity across all parameter regimes, including overflow-safe evaluation
           for large inputs (e.g. mass ~ 1e154).
        6. Sub-ulp agreement with high-precision 80-digit Decimal references (relerr <= 1e-15).
        """
        getcontext().prec = 80
        metric = KerrMetric(mass=mass, spin=spin)

        r_minus = metric.inner_horizon_radius
        r_plus = metric.horizon_radius

        # 1. Finiteness and nonnegativity
        assert np.isfinite(r_plus), f"r_+ must be finite, got {r_plus}"
        assert np.isfinite(r_minus), f"r_- must be finite, got {r_minus}"
        assert r_minus >= 0.0, f"r_- must be non-negative, got {r_minus}"

        # 2. Spin sign parity
        metric_neg = KerrMetric(mass=mass, spin=-spin)
        assert metric.horizon_radius == metric_neg.horizon_radius
        assert metric.inner_horizon_radius == metric_neg.inner_horizon_radius

        # 3. Exact zero, sub-extremal, and extremal behavior
        if spin == 0.0:
            assert r_minus == 0.0, f"r_- must be exactly 0 for a=0, got {r_minus}"
            assert r_plus == 2.0 * mass
            assert not metric.is_extremal
        elif abs(spin) == mass:
            assert r_minus == mass
            assert r_plus == mass
            assert metric.is_extremal
        else:
            assert r_minus > 0.0, f"r_- collapsed to zero for nonzero spin a={spin}"
            assert r_plus > r_minus, f"r_+ <= r_- for sub-extremal spin a={spin}: r_+={r_plus}, r_-={r_minus}"
            assert not metric.is_extremal

        # 4. High-precision Decimal benchmark comparison (standard masses)
        if mass <= 2.5:
            mass_dec = Decimal.from_float(mass)
            spin_dec = Decimal.from_float(spin)
            disc_ref = (mass_dec - abs(spin_dec)) * (mass_dec + abs(spin_dec))
            sqrt_disc_ref = disc_ref.sqrt()
            r_plus_ref = mass_dec + sqrt_disc_ref
            r_minus_ref = mass_dec - sqrt_disc_ref

            err_r_plus = abs(Decimal.from_float(r_plus) - r_plus_ref) / r_plus_ref
            assert float(err_r_plus) <= 1e-15, f"r_+ error vs Decimal reference exceeded tolerance: {err_r_plus}"

            if spin == 0.0:
                assert r_minus_ref == 0
                assert r_minus == 0.0
            else:
                err_r_minus = abs(Decimal.from_float(r_minus) - r_minus_ref) / r_minus_ref
                assert float(err_r_minus) <= 1e-15, (
                    f"r_- error vs Decimal reference exceeded tolerance: {err_r_minus} for a={spin}"
                )
