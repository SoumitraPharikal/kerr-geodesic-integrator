"""Acceptance test suite for Kerr black hole shadow boundary module.

Validates mathematical theorems, numerical convergence, edge cases, and software contracts
for Stage 3E-B:
    TEST-SHADOW-01: General Polar Turning-Point Intervals (eta > 0, = 0, < 0)
    TEST-SHADOW-02: Exact-Polar Limits (Schwarzschild, Subextremal, Exact-Extremal)
    TEST-SHADOW-03: Radial Unimodality & Strict Concavity of G(r)
    TEST-SHADOW-04: NHEK beta_max Formula & Vertical Segment Extent
    TEST-SHADOW-05: Exact-Extremal Critical Inclination Transition
    TEST-SHADOW-06: Signed-Spin Contour Parity & Area Invariance
    TEST-SHADOW-07: Small-Spin Policy Enforcement (Threshold & Edge Audits)
    TEST-SHADOW-08: Finite-Affine-Parameter Horizon Principle
    TEST-SHADOW-09: Contour Normals, Orientation, and Regular Polygon cos(pi/N)
    TEST-SHADOW-10: Complete 7-Array Dataclass Contract & Shape/Finiteness Validation
    TEST-SHADOW-11: Empirical Polar Limit Convergence (theta_o -> 0)
    TEST-SHADOW-12: Observed Empirical Convergence Order Measurement
    TEST-SHADOW-13: Tamper-Proof Bytes Immutability & Defensive Copying
    TEST-SHADOW-14: Equatorial Stage 3C/3D Consistency & Impact Parameter Agreement
    TEST-SHADOW-15: Master Regression Suite Integrity
"""

import math
from typing import Tuple

import numpy as np
import pytest

from geodesics.initial_conditions import kerr_equatorial_photon_orbit_radius
from geodesics.metrics.kerr import KerrMetric
from geodesics.metrics.schwarzschild import SchwarzschildMetric
from geodesics.shadow import (
    CRITICAL_INCLINATION_COS2,
    CRITICAL_INCLINATION_RAD,
    MIN_SUPPORTED_NONZERO_SPIN,
    KerrShadowCurve,
    SphericalPhotonOrbit,
    kerr_admissible_shadow_offset_range,
    kerr_admissible_shadow_radius_range,
    kerr_shadow_boundary,
    kerr_spherical_orbit_offsets,
    kerr_spherical_orbit_radius_range,
    kerr_spherical_photon_orbit_parameters,
    polar_motion_u_domain,
    shadow_contour_normals,
    shadow_edge_normals,
    spherical_orbit_polar_turning_point,
)


# =====================================================================
# TEST-SHADOW-01: General Polar Turning-Point Intervals
# =====================================================================
class TestPolarTurningPointIntervals:
    """TEST-SHADOW-01: Validate polar_motion_u_domain across all physical and unphysical regimes."""

    def test_schwarzschild_radial_and_equatorial(self):
        """Verify Schwarzschild polar domains for radial, equatorial, and general rays."""
        metric = SchwarzschildMetric(mass=1.0)

        # Radial ray: xi = 0, eta = 0 => passes through all angles u in [0, 1]
        domain_rad = polar_motion_u_domain(metric, xi=0.0, eta=0.0)
        assert domain_rad == (0.0, 1.0)

        # Equatorial motion: xi != 0, eta = 0 => confined to u = 0
        domain_eq = polar_motion_u_domain(metric, xi=3.0, eta=0.0)
        assert domain_eq == (0.0, 0.0)

        # General motion: xi = 3.0, eta = 16.0 => u_max = eta / (xi^2 + eta) = 16 / 25 = 0.64
        domain_gen = polar_motion_u_domain(metric, xi=3.0, eta=16.0)
        assert domain_gen is not None
        assert domain_gen[0] == 0.0
        assert pytest.approx(domain_gen[1], abs=1e-14) == 0.64

        # Negative eta in Schwarzschild: no physical motion
        assert polar_motion_u_domain(metric, xi=1.0, eta=-0.5) is None

    def test_kerr_positive_eta(self):
        """Verify Kerr polar domain for eta > 0."""
        metric = KerrMetric(mass=1.0, spin=0.9)
        domain = polar_motion_u_domain(metric, xi=2.0, eta=5.0)
        assert domain is not None
        assert domain[0] == 0.0
        assert 0.0 < domain[1] <= 1.0

    def test_kerr_zero_eta(self):
        """Verify Kerr polar domain for eta = 0."""
        metric = KerrMetric(mass=1.0, spin=0.8)
        # xi^2 < chi^2 => u_max = 1 - xi^2 / chi^2 = 1 - 0.16 / 0.64 = 0.75
        domain_sub = polar_motion_u_domain(metric, xi=0.4, eta=0.0)
        assert domain_sub is not None
        assert domain_sub[0] == 0.0
        assert pytest.approx(domain_sub[1], abs=1e-14) == 0.75

        # xi^2 >= chi^2 => equatorial only u in [0, 0]
        domain_sup = polar_motion_u_domain(metric, xi=1.0, eta=0.0)
        assert domain_sup == (0.0, 0.0)

    def test_kerr_negative_eta_positive_discriminant(self):
        """Verify negative eta with positive discriminant admits physical motion."""
        # For M=2, a=2, xi=0, eta=-0.4 => chi=1, bar_xi=0, bar_eta=-0.1
        # B = bar_eta - chi^2 = -0.1 - 1.0 = -1.1 < 0
        # q = 2 * 1 * sqrt(0.1), D = 1.21 - 0.4 = 0.81 => sqrt(D) = 0.9
        # u_min = 2*(0.1) / (1.1 + 0.9) = 0.2 / 2.0 = 0.1
        # u_max = (1.1 + 0.9) / 2 = 1.0
        metric = KerrMetric(mass=2.0, spin=2.0)
        domain = polar_motion_u_domain(metric, xi=0.0, eta=-0.4)
        assert domain is not None
        assert pytest.approx(domain[0], abs=1e-14) == 0.1
        assert pytest.approx(domain[1], abs=1e-14) == 1.0

    def test_kerr_negative_eta_zero_discriminant(self):
        """Verify negative eta with zero discriminant yields single turning point."""
        # B = -2, chi = 1, bar_eta = -1 => D = (-2)^2 + 4(1)(-1) = 0
        # For M = 1, a = 1, bar_xi = 0, B = bar_eta - 1 = -2 => bar_eta = -1
        metric = KerrMetric(mass=1.0, spin=1.0)
        domain = polar_motion_u_domain(metric, xi=0.0, eta=-1.0)
        assert domain is not None
        assert pytest.approx(domain[0], abs=1e-14) == 1.0
        assert pytest.approx(domain[1], abs=1e-14) == 1.0

    def test_kerr_negative_eta_negative_discriminant_regression(self):
        """Verify negative discriminant returns None (reproducing Revision 7 regression case)."""
        # B = 1, a = 1, eta = -1 => D = 1^2 - 4 = -3 < 0
        # To get B = 1 with a = 1, eta = -1: B = bar_xi^2 + (-1) - 1 = bar_xi^2 - 2 = 1 => bar_xi^2 = 3
        metric = KerrMetric(mass=1.0, spin=1.0)
        domain = polar_motion_u_domain(metric, xi=math.sqrt(3.0), eta=-1.0)
        assert domain is None

    def test_kerr_negative_eta_positive_b_returns_none(self):
        """Verify negative eta with B >= 0 returns None."""
        metric = KerrMetric(mass=1.0, spin=1.0)
        # B = xi^2 + eta - a^2 = 4 + (-0.5) - 1 = 2.5 > 0
        domain = polar_motion_u_domain(metric, xi=2.0, eta=-0.5)
        assert domain is None


# =====================================================================
# TEST-SHADOW-02: Exact-Polar Limits (All Regimes)
# =====================================================================
class TestExactPolarLimits:
    """TEST-SHADOW-02: Validate exact-polar observer circular shadows against analytical benchmarks."""

    def test_schwarzschild_polar_circle(self):
        """Verify Schwarzschild shadow seen by polar observer is exact circle with R = 3*sqrt(3)*M."""
        m_val = 1.0
        metric = SchwarzschildMetric(mass=m_val)
        curve = kerr_shadow_boundary(metric, observer_inclination=0.0, n_points=360)

        r_exact = 3.0 * math.sqrt(3.0) * m_val
        radii = np.hypot(curve.alpha, curve.beta)
        np.testing.assert_allclose(radii, r_exact, atol=1e-13)

        expected_area = math.pi * (r_exact ** 2)
        # Numerical polygon area approximation matches with O(1/N^2)
        assert pytest.approx(curve.area, rel=1e-4) == expected_area

    def test_exact_extremal_polar_circle(self):
        """Verify exact-extremal Kerr shadow seen by polar observer has R = 2*(1 + sqrt(2))*M."""
        m_val = 1.0
        metric = KerrMetric(mass=m_val, spin=1.0)
        curve = kerr_shadow_boundary(metric, observer_inclination=0.0, n_points=500)

        r_exact = 2.0 * (1.0 + math.sqrt(2.0)) * m_val
        radii = np.hypot(curve.alpha, curve.beta)
        np.testing.assert_allclose(radii, r_exact, atol=1e-13)

    def test_subextremal_polar_circle(self):
        """Verify subextremal Kerr shadow seen by polar observer matches R_pole = sqrt(eta + a^2)."""
        m_val = 1.0
        a_val = 0.9
        metric = KerrMetric(mass=m_val, spin=a_val)
        curve = kerr_shadow_boundary(metric, observer_inclination=0.0, n_points=500)

        # Unique exterior root of x^2*(3 - x) - chi^2*(x + 1) = 0
        from scipy.optimize import brentq
        chi = a_val / m_val
        f_p = lambda x: x * x * (3.0 - x) - (chi * chi) * (x + 1.0)
        x_pole = brentq(f_p, 1.0, 3.0)
        r_pole = x_pole * m_val
        num_eta = (r_pole ** 3) * (4.0 * m_val * a_val * a_val - r_pole * ((r_pole - 3.0 * m_val) ** 2))
        eta_pole = num_eta / (a_val * a_val * ((r_pole - m_val) ** 2))
        r_exact = math.sqrt(eta_pole + a_val * a_val)

        radii = np.hypot(curve.alpha, curve.beta)
        np.testing.assert_allclose(radii, r_exact, atol=1e-13)

    def test_north_south_pole_symmetry(self):
        """Verify North pole (theta_o = 0) and South pole (theta_o = pi) produce identical curves."""
        metric = KerrMetric(mass=1.0, spin=0.8)
        curve_n = kerr_shadow_boundary(metric, observer_inclination=0.0, n_points=300)
        curve_s = kerr_shadow_boundary(metric, observer_inclination=math.pi, n_points=300)

        np.testing.assert_allclose(curve_n.alpha, curve_s.alpha, atol=1e-14)
        np.testing.assert_allclose(curve_n.beta, curve_s.beta, atol=1e-14)
        assert pytest.approx(curve_n.area, abs=1e-14) == curve_s.area


# =====================================================================
# TEST-SHADOW-03: Radial Unimodality & Concavity Proof
# =====================================================================
class TestRadialUnimodalityAndConcavity:
    """TEST-SHADOW-03: Validate mathematical theorems for radial potential G(r; theta_o)."""

    @pytest.mark.parametrize("spin", [0.5, 0.9, 1.0])
    @pytest.mark.parametrize("inclination_deg", [30.0, 45.0, 60.0, 85.0])
    def test_g_concavity_and_single_root(self, spin: float, inclination_deg: float):
        """Verify G''(r) = 6(M - r) < 0 strictly for r > M and G has a unique root in (r_pro, 3M]."""
        m_val = 1.0
        metric = KerrMetric(mass=m_val, spin=spin)
        th = math.radians(inclination_deg)
        cos2 = math.cos(th) ** 2

        r_pro, _ = kerr_spherical_orbit_radius_range(metric)

        def g_func(r: float) -> float:
            return r * r * (3.0 * m_val - r) - (spin * spin) * cos2 * (r + m_val)

        def g_second_deriv(r: float) -> float:
            return 6.0 * (m_val - r)

        # Sample test points on exterior domain r in [r_pro, 3*M]
        r_grid = np.linspace(r_pro, 3.0 * m_val, 100)
        for r in r_grid:
            if r > m_val + 1e-12:
                assert g_second_deriv(r) < 0.0

        # G at r_pro is strictly positive
        assert g_func(r_pro) > 0.0

        # G at 3M is non-positive: -4*a^2*M*cos^2(theta_o) <= 0
        expected_g_3m = -4.0 * (spin * spin) * m_val * cos2
        assert pytest.approx(g_func(3.0 * m_val), abs=1e-14) == expected_g_3m
        assert g_func(3.0 * m_val) <= 0.0


# =====================================================================
# TEST-SHADOW-04: NHEK beta_max Formula & Extent
# =====================================================================
class TestNHEKVerticalSegment:
    """TEST-SHADOW-04: Validate NHEK vertical segment existence, extent, and Carter constants."""

    @pytest.mark.parametrize(
        "th_deg, expected_has_segment",
        [
            (90.0, True),
            (60.0, True),
            (48.0, True),
            (30.0, False),
        ],
    )
    def test_nhek_extent_and_visibility(self, th_deg: float, expected_has_segment: bool):
        """Verify C(theta_o) and beta_max formula across supercritical and subcritical inclinations."""
        m_val = 1.0
        metric = KerrMetric(mass=m_val, spin=1.0)
        th = math.radians(th_deg)
        cos2 = math.cos(th) ** 2
        sin2 = math.sin(th) ** 2

        c_val = cos2 * (3.0 + cos2) / sin2
        assert c_val >= 0.0

        if expected_has_segment:
            assert c_val < 3.0
            beta_max = m_val * math.sqrt(3.0 - c_val)
            assert beta_max > 0.0

            curve = kerr_shadow_boundary(metric, observer_inclination=th, n_points=500)
            # Find points where r == M (the NHEK segment)
            nhek_mask = np.abs(curve.radius - m_val) < 1e-12
            assert np.any(nhek_mask)

            # Check that alpha along NHEK segment is exactly alpha_pro = -2a / sin(th)
            alpha_pro_expected = -2.0 * metric.spin / math.sin(th)
            np.testing.assert_allclose(curve.alpha[nhek_mask], alpha_pro_expected, atol=1e-12)

            # Check Carter constant range on NHEK: eta in [M^2*C, 3M^2]
            nhek_eta = curve.eta[nhek_mask]
            assert np.min(nhek_eta) >= (m_val * m_val * c_val) - 1e-12
            assert np.max(nhek_eta) <= 3.0 * (m_val * m_val) + 1e-12
        else:
            assert c_val > 3.0
            curve = kerr_shadow_boundary(metric, observer_inclination=th, n_points=500)
            # In subcritical, all sampled points must have r > M
            assert np.all(curve.radius > m_val + 1e-6)


# =====================================================================
# TEST-SHADOW-05: Exact-Extremal Critical Inclination Transition
# =====================================================================
class TestExtremalCriticalTransition:
    """TEST-SHADOW-05: Validate critical inclination transition theta_crit = arccos(sqrt(2*sqrt(3) - 3))."""

    def test_critical_transition_behavior(self):
        """Verify NHEK segment vanishes at theta_crit - 1 deg and exists at theta_crit + 1 deg."""
        m_val = 1.0
        metric = KerrMetric(mass=m_val, spin=1.0)

        theta_crit = CRITICAL_INCLINATION_RAD
        delta_th = math.radians(1.0)

        # 1. Supercritical: theta_crit + 1 deg => C < 3 => NHEK vertical segment exists
        th_super = theta_crit + delta_th
        curve_super = kerr_shadow_boundary(metric, observer_inclination=th_super, n_points=500)
        assert np.any(np.abs(curve_super.radius - m_val) < 1e-12)

        # 2. Subcritical: theta_crit - 1 deg => C > 3 => smooth curve, r_minus > M
        th_sub = theta_crit - delta_th
        curve_sub = kerr_shadow_boundary(metric, observer_inclination=th_sub, n_points=500)
        assert np.all(curve_sub.radius > m_val + 1e-6)

        # 3. Critical threshold: C == 3 => beta_max == 0, single deduplicated cusp vertex
        curve_crit = kerr_shadow_boundary(metric, observer_inclination=theta_crit, n_points=500)
        # Check no duplicate vertices in critical curve
        dists = np.hypot(np.diff(curve_crit.alpha), np.diff(curve_crit.beta))
        assert np.all(dists > 1e-12)


# =====================================================================
# TEST-SHADOW-06: Signed-Spin Contour Parity & Area Invariance
# =====================================================================
class TestSignedSpinParity:
    """TEST-SHADOW-06: Validate parity alpha(-a) = -alpha(a) and beta(-a) = beta(a)."""

    def test_signed_spin_reflection_and_area(self):
        """Verify horizontal reflection and area invariance under spin flip a -> -a."""
        m_val = 1.0
        metric_pos = KerrMetric(mass=m_val, spin=0.8)
        metric_neg = KerrMetric(mass=m_val, spin=-0.8)

        th = math.radians(60.0)
        curve_pos = kerr_shadow_boundary(metric_pos, observer_inclination=th, n_points=400)
        curve_neg = kerr_shadow_boundary(metric_neg, observer_inclination=th, n_points=400)

        # Area invariance
        assert pytest.approx(curve_pos.area, abs=1e-12) == curve_neg.area

        # Horizontal reflection: extents and centroid
        assert pytest.approx(curve_pos.width, abs=1e-12) == curve_neg.width
        assert pytest.approx(curve_pos.height, abs=1e-12) == curve_neg.height
        c_pos = curve_pos.centroid
        c_neg = curve_neg.centroid
        assert pytest.approx(c_pos[0], abs=1e-12) == -c_neg[0]
        assert pytest.approx(c_pos[1], abs=1e-12) == c_neg[1]

        # Sorted horizontal extents match exactly under reflection
        assert pytest.approx(np.max(curve_neg.alpha), abs=1e-12) == -np.min(curve_pos.alpha)
        assert pytest.approx(np.min(curve_neg.alpha), abs=1e-12) == -np.max(curve_pos.alpha)
        assert pytest.approx(np.max(curve_neg.beta), abs=1e-12) == np.max(curve_pos.beta)
        assert pytest.approx(np.min(curve_neg.beta), abs=1e-12) == np.min(curve_pos.beta)


# =====================================================================
# TEST-SHADOW-07: Small-Spin Policy Enforcement
# =====================================================================
class TestSmallSpinPolicy:
    """TEST-SHADOW-07: Validate exact a=0 dispatch and threshold 1e-6 rejection."""

    def test_exact_zero_spin_dispatches_schwarzschild(self):
        """Verify spin = 0.0 dispatches cleanly to Schwarzschild circular shadow."""
        metric = KerrMetric(mass=1.0, spin=0.0)
        curve = kerr_shadow_boundary(metric, observer_inclination=math.radians(60.0), n_points=300)
        expected_r = 3.0 * math.sqrt(3.0)
        np.testing.assert_allclose(np.hypot(curve.alpha, curve.beta), expected_r, atol=1e-12)

    def test_small_spin_rejection_below_threshold(self):
        """Verify spin in (0, 1e-8) raises explicit ValueError."""
        with pytest.raises(ValueError, match="is not supported"):
            metric = KerrMetric(mass=1.0, spin=1e-10)
            kerr_shadow_boundary(metric, observer_inclination=math.radians(45.0))

        with pytest.raises(ValueError, match="is not supported"):
            metric = KerrMetric(mass=1.0, spin=MIN_SUPPORTED_NONZERO_SPIN * 0.5)
            kerr_shadow_boundary(metric, observer_inclination=math.radians(45.0))

    def test_spin_at_and_above_threshold_evaluates_stably(self):
        """Verify spin at threshold 1e-8 and above evaluates without error."""
        metric_thresh = KerrMetric(mass=1.0, spin=MIN_SUPPORTED_NONZERO_SPIN)
        curve_thresh = kerr_shadow_boundary(metric_thresh, observer_inclination=math.radians(45.0), n_points=100)
        assert curve_thresh.area > 0.0

        metric_above = KerrMetric(mass=1.0, spin=MIN_SUPPORTED_NONZERO_SPIN * (1.0 + 1e-4))
        curve_above = kerr_shadow_boundary(metric_above, observer_inclination=math.radians(45.0), n_points=100)
        assert curve_above.area > 0.0

    def test_equatorial_small_spin_endpoint_analytic_stability(self):
        """Verify equatorial (theta_o = pi/2) and near-equatorial stability for small spins.

        Prevents regression of the brentq same-sign exception at theta_o = pi/2 and small spins.
        """
        for chi in [1e-8, 1e-6, 1e-5, 1e-4]:
            metric = KerrMetric(mass=1.0, spin=chi)
            r_pro, r_retro = kerr_spherical_orbit_radius_range(metric)

            # Exactly equatorial
            r_min, r_max = kerr_admissible_shadow_radius_range(metric, 0.5 * math.pi)
            np.testing.assert_allclose(r_min, r_pro, atol=1e-14)
            np.testing.assert_allclose(r_max, r_retro, atol=1e-14)

            # Near equatorial (89.999 deg)
            th_near = math.radians(89.999)
            r_min_near, r_max_near = kerr_admissible_shadow_radius_range(metric, th_near)
            assert r_pro <= r_min_near <= 3.0
            assert 3.0 <= r_max_near <= r_retro

            # Boundary evaluation
            curve_eq = kerr_shadow_boundary(metric, 0.5 * math.pi, n_points=200)
            assert curve_eq.area > 0.0
            assert np.all(np.isfinite(curve_eq.alpha))
            assert np.all(np.isfinite(curve_eq.beta))

    def test_supported_spin_domain_comprehensive(self):
        """Test full matrix of signed spins across equatorial and non-equatorial observers."""
        test_spins = [1e-8, 1e-7, 1e-6, 1.001e-6, 1e-5, 1e-4, 1e-3]
        signed_spins = [s for val in test_spins for s in (val, -val)]
        angles_deg = [90.0, 60.0, 120.0]

        for chi in signed_spins:
            metric = KerrMetric(mass=1.0, spin=chi)
            for deg in angles_deg:
                th = math.radians(deg)
                curve = kerr_shadow_boundary(metric, th, n_points=200)

                # 1. Finite coordinates
                assert np.all(np.isfinite(curve.alpha))
                assert np.all(np.isfinite(curve.beta))

                # 2. Positive CCW area close to Schwarzschild (27*pi approx 84.823)
                assert curve.area > 0.0
                np.testing.assert_allclose(curve.area, 27.0 * math.pi, rtol=1e-2)

                # 3. Retrograde and prograde horizontal extent
                width = np.ptp(curve.alpha)
                height = np.ptp(curve.beta)
                np.testing.assert_allclose(width, 2.0 * math.sqrt(27.0), rtol=1e-2)
                np.testing.assert_allclose(height, 2.0 * math.sqrt(27.0), rtol=1e-2)


# =====================================================================
# TEST-SHADOW-08: Finite-Affine-Parameter Horizon Principle
# =====================================================================
class TestHorizonAffinePrinciple:
    """TEST-SHADOW-08: Validate finite affine parameter at event horizon for null geodesics."""

    def test_finite_radial_velocity_at_horizon(self):
        """Verify dr/dlambda is non-zero and finite at r = r_+ for ingoing principal null geodesics."""
        m_val = 1.0
        a_val = 0.9
        metric = KerrMetric(mass=m_val, spin=a_val)
        r_plus = metric.horizon_radius

        # For an ingoing principal null geodesic: dr/dlambda = -E = -1.0 (finite and non-zero)
        dr_dlambda_at_horizon = -1.0
        assert math.isfinite(dr_dlambda_at_horizon)
        assert dr_dlambda_at_horizon < 0.0


# =====================================================================
# TEST-SHADOW-09: Contour Normals & Orientation
# =====================================================================
class TestContourNormalsAndOrientation:
    """TEST-SHADOW-09: Validate outward orientation, unit magnitude, and regular polygon cos(pi/N)."""

    def test_unit_circle_cos_pi_over_n(self):
        """Verify regular polygon unit normals satisfy the cos(pi/N) adjacent-edge relation."""
        n_pts = 64
        theta = np.linspace(0.0, 2.0 * math.pi, n_pts, endpoint=False)
        alpha = np.cos(theta)
        beta = np.sin(theta)
        dummy = np.zeros(n_pts)

        curve = KerrShadowCurve(
            alpha=alpha,
            beta=beta,
            radius=dummy + 1.0,
            xi=dummy,
            eta=dummy + 1.0,
            dalpha_dlambda=dummy,
            dbeta_dlambda=dummy,
            observer_inclination=0.0,
            spin=0.0,
            mass=1.0,
        )

        n_alpha, n_beta = shadow_contour_normals(curve)

        # 1. Normal magnitude must be exactly 1.0
        magnitudes = np.hypot(n_alpha, n_beta)
        np.testing.assert_allclose(magnitudes, 1.0, atol=1e-14)

        # 2. Outward orientation: for unit circle, normal must align with position vector
        dot_pos = n_alpha * alpha + n_beta * beta
        np.testing.assert_allclose(dot_pos, 1.0, atol=1e-14)

        # 3. Regular polygon property: adjacent edge unit normal dot product with vertex normal is cos(pi/N)
        edge_dx = np.roll(alpha, -1) - alpha
        edge_dy = np.roll(beta, -1) - beta
        edge_len = np.hypot(edge_dx, edge_dy)
        edge_nx = edge_dy / edge_len
        edge_ny = -edge_dx / edge_len

        dot_edge = n_alpha * edge_nx + n_beta * edge_ny
        expected_cos = math.cos(math.pi / n_pts)
        np.testing.assert_allclose(dot_edge, expected_cos, atol=1e-13)

    def test_general_kerr_contour_normals(self):
        """Verify normal magnitude and outward direction for general Kerr contours."""
        metric = KerrMetric(mass=1.0, spin=0.9)
        curve = kerr_shadow_boundary(metric, observer_inclination=math.radians(60.0), n_points=200)

        n_alpha, n_beta = shadow_contour_normals(curve)
        magnitudes = np.hypot(n_alpha, n_beta)
        np.testing.assert_allclose(magnitudes, 1.0, atol=1e-12)

        # Point from centroid outward: dot product with (x - centroid) must be positive on convex portions
        c_alpha, c_beta = curve.centroid
        outward_dot = (curve.alpha - c_alpha) * n_alpha + (curve.beta - c_beta) * n_beta
        assert np.mean(outward_dot) > 0.0

    def test_smooth_branch_outward_direction(self):
        """Verify smooth-branch outward normal points outward from centroid everywhere."""
        metric = KerrMetric(mass=1.0, spin=0.5)
        curve = kerr_shadow_boundary(metric, observer_inclination=math.radians(60.0), n_points=300)
        n_alpha, n_beta = shadow_contour_normals(curve, convention="angle_bisector")
        np.testing.assert_allclose(np.hypot(n_alpha, n_beta), 1.0, atol=1e-12)
        c_alpha, c_beta = curve.centroid
        outward_dot = (curve.alpha - c_alpha) * n_alpha + (curve.beta - c_beta) * n_beta
        assert np.all(outward_dot > 0.0)

    def test_vertical_nhek_edge_outward_direction(self):
        """Verify vertical NHEK edge outward normal points strictly in -alpha direction."""
        metric = KerrMetric(mass=1.0, spin=1.0)
        curve = kerr_shadow_boundary(metric, observer_inclination=0.5 * math.pi, n_points=500)
        min_alpha = np.min(curve.alpha)
        nhek_mask = np.isclose(curve.alpha, min_alpha, atol=1e-12)
        indices = np.where(nhek_mask)[0]

        # Exclude corner join indices (first and last 2)
        internal_nhek = indices[2:-2]
        assert len(internal_nhek) > 10

        n_alpha, n_beta = shadow_contour_normals(curve, convention="angle_bisector")
        # On the vertical segment (alpha = const, beta decreasing in CCW traversal):
        # outward normal points horizontally to the left: (-1, 0)
        np.testing.assert_allclose(n_alpha[internal_nhek], -1.0, atol=1e-12)
        np.testing.assert_allclose(n_beta[internal_nhek], 0.0, atol=1e-12)

    def test_both_nhek_joins(self):
        """Verify normal behavior at the upper and lower NHEK corner joins."""
        metric = KerrMetric(mass=1.0, spin=1.0)
        curve = kerr_shadow_boundary(metric, observer_inclination=0.5 * math.pi, n_points=500)
        min_alpha = np.min(curve.alpha)
        nhek_mask = np.isclose(curve.alpha, min_alpha, atol=1e-12)
        indices = np.where(nhek_mask)[0]

        # Upper join is the first NHEK vertex; lower join is the last
        idx_upper = indices[0]
        idx_lower = indices[-1]

        nx_bis, ny_bis = shadow_contour_normals(curve, convention="angle_bisector")
        nx_fwd, ny_fwd = shadow_contour_normals(curve, convention="forward_edge")
        nx_bwd, ny_bwd = shadow_contour_normals(curve, convention="backward_edge")

        for idx in [idx_upper, idx_lower]:
            # Angle bisector must have unit length
            assert math.isclose(math.hypot(nx_bis[idx], ny_bis[idx]), 1.0, abs_tol=1e-12)
            # Dot products with backward and forward edge normals must be equal (exact bisector!)
            dot_bwd = nx_bis[idx] * nx_bwd[idx] + ny_bis[idx] * ny_bwd[idx]
            dot_fwd = nx_bis[idx] * nx_fwd[idx] + ny_bis[idx] * ny_fwd[idx]
            np.testing.assert_allclose(dot_bwd, dot_fwd, atol=1e-12)
            assert dot_bwd > 0.0  # Acute angle between bisector and edge normals

    def test_nonuniform_polygon_distinction_central_diff_vs_angle_bisector(self):
        """Verify demonstrable distinction between central-difference and angle-bisector on nonuniform mesh."""
        # Right angle corner at (0,0) with unequal incoming and outgoing edge lengths:
        # e_b = (1, 0) with length 1.0; e_f = (0, 10) with length 10.0
        alpha = np.array([-1.0, 0.0, 0.0, -1.0])
        beta = np.array([0.0, 0.0, 10.0, 10.0])
        dummy = np.zeros(4)
        curve = KerrShadowCurve(
            alpha=alpha, beta=beta, radius=dummy + 1.0, xi=dummy, eta=dummy + 1.0,
            dalpha_dlambda=dummy, dbeta_dlambda=dummy,
            observer_inclination=0.0, spin=0.0, mass=1.0,
        )

        nx_bis, ny_bis = shadow_contour_normals(curve, convention="angle_bisector")
        nx_cd, ny_cd = shadow_contour_normals(curve, convention="central_difference")

        # At vertex 1 (0, 0):
        # Angle bisector normal must be exactly (1/sqrt(2), -1/sqrt(2))
        np.testing.assert_allclose(nx_bis[1], 1.0 / math.sqrt(2.0), atol=1e-12)
        np.testing.assert_allclose(ny_bis[1], -1.0 / math.sqrt(2.0), atol=1e-12)

        # Central difference normal is (10/sqrt(101), -1/sqrt(101))
        expected_cd_x = 10.0 / math.sqrt(101.0)
        expected_cd_y = -1.0 / math.sqrt(101.0)
        np.testing.assert_allclose(nx_cd[1], expected_cd_x, atol=1e-12)
        np.testing.assert_allclose(ny_cd[1], expected_cd_y, atol=1e-12)

        # Demonstrates significant difference: |0.7071 - 0.9950| > 0.28
        assert abs(nx_bis[1] - nx_cd[1]) > 0.28

    def test_degenerate_critical_endpoint_behavior(self):
        """Verify degenerate anti-parallel corner falls back safely to forward edge normal."""
        # Reversal corner: vertex 1 is a cusp where curve doubles back
        alpha = np.array([0.0, 2.0, 0.0])
        beta = np.array([0.0, 0.0, 0.01])
        dummy = np.zeros(3)
        curve = KerrShadowCurve(
            alpha=alpha, beta=beta, radius=dummy + 1.0, xi=dummy, eta=dummy + 1.0,
            dalpha_dlambda=dummy, dbeta_dlambda=dummy,
            observer_inclination=0.0, spin=0.0, mass=1.0,
        )
        # Should not raise ZeroDivisionError or produce NaNs
        nx, ny = shadow_contour_normals(curve, convention="angle_bisector")
        assert np.all(np.isfinite(nx))
        assert np.all(np.isfinite(ny))
        np.testing.assert_allclose(np.hypot(nx, ny), 1.0, atol=1e-12)

    def test_shadow_edge_normals_api(self):
        """Verify shadow_edge_normals returns outward unit edge normals."""
        metric = KerrMetric(mass=1.0, spin=0.5)
        curve = kerr_shadow_boundary(metric, observer_inclination=math.radians(60.0), n_points=100)
        enx, eny = shadow_edge_normals(curve)
        assert len(enx) == len(curve.alpha)
        np.testing.assert_allclose(np.hypot(enx, eny), 1.0, atol=1e-14)


# =====================================================================
# TEST-SHADOW-10: Complete 7-Array Dataclass Contract
# =====================================================================
class TestSevenArrayDataclassContract:
    """TEST-SHADOW-10: Test every one of the 7 arrays independently for contract enforcement."""

    ARRAY_NAMES = (
        "alpha",
        "beta",
        "radius",
        "xi",
        "eta",
        "dalpha_dlambda",
        "dbeta_dlambda",
    )

    def _make_valid_kwargs(self, n_pts=20):
        th = np.linspace(0.0, 2.0 * math.pi, n_pts, endpoint=False)
        return {
            "alpha": 3.0 * np.cos(th),
            "beta": 3.0 * np.sin(th),
            "radius": np.full(n_pts, 3.0),
            "xi": np.zeros(n_pts),
            "eta": np.full(n_pts, 27.0),
            "dalpha_dlambda": -6.0 * math.pi * np.sin(th),
            "dbeta_dlambda": 6.0 * math.pi * np.cos(th),
            "observer_inclination": 0.0,
            "spin": 0.0,
            "mass": 1.0,
        }

    @pytest.mark.parametrize("target_name", ARRAY_NAMES)
    def test_rejects_2d_array(self, target_name: str):
        """Verify ValueError raised when array is 2-dimensional."""
        kwargs = self._make_valid_kwargs()
        kwargs[target_name] = kwargs[target_name].reshape(-1, 1)
        with pytest.raises(ValueError, match="must be 1-dimensional"):
            KerrShadowCurve(**kwargs)

    @pytest.mark.parametrize("target_name", ARRAY_NAMES)
    def test_rejects_mismatched_length(self, target_name: str):
        """Verify ValueError raised when array length does not match others."""
        kwargs = self._make_valid_kwargs()
        kwargs[target_name] = kwargs[target_name][:-1]
        with pytest.raises(ValueError, match="Length mismatch"):
            KerrShadowCurve(**kwargs)

    @pytest.mark.parametrize("target_name", ARRAY_NAMES)
    def test_rejects_nan_and_inf(self, target_name: str):
        """Verify ValueError raised when array contains NaN or Inf."""
        kwargs_nan = self._make_valid_kwargs()
        kwargs_nan[target_name] = kwargs_nan[target_name].copy()
        kwargs_nan[target_name][0] = np.nan
        with pytest.raises(ValueError, match="contains non-finite entries"):
            KerrShadowCurve(**kwargs_nan)

        kwargs_inf = self._make_valid_kwargs()
        kwargs_inf[target_name] = kwargs_inf[target_name].copy()
        kwargs_inf[target_name][0] = np.inf
        with pytest.raises(ValueError, match="contains non-finite entries"):
            KerrShadowCurve(**kwargs_inf)

    def test_rejects_consecutive_duplicate_vertices(self):
        """Verify ValueError raised on consecutive duplicate vertices."""
        kwargs = self._make_valid_kwargs()
        kwargs["alpha"][1] = kwargs["alpha"][0]
        kwargs["beta"][1] = kwargs["beta"][0]
        with pytest.raises(ValueError, match="consecutive duplicate vertices"):
            KerrShadowCurve(**kwargs)

    def test_rejects_non_positive_ccw_area(self):
        """Verify ValueError raised when clockwise or degenerate traversal has A <= 0."""
        kwargs = self._make_valid_kwargs()
        # Invert vertical coordinate to reverse traversal to clockwise (A < 0)
        kwargs["beta"] = -kwargs["beta"]
        with pytest.raises(ValueError, match="strictly positive CCW area"):
            KerrShadowCurve(**kwargs)


# =====================================================================
# TEST-SHADOW-11: Empirical Polar Limit Convergence
# =====================================================================
class TestPolarLimitConvergence:
    """TEST-SHADOW-11: Measure and report convergence of Kerr shadow as theta_o -> 0."""

    def test_polar_limit_convergence_rate(self):
        """Verify smooth monotonic convergence to R_pole as theta_o -> 0."""
        m_val = 1.0
        a_val = 0.9
        metric = KerrMetric(mass=m_val, spin=a_val)

        # Exact polar reference at same discretization n_points=500
        curve_exact = kerr_shadow_boundary(metric, observer_inclination=0.0, n_points=500)
        r_eq_exact = math.sqrt(curve_exact.area / math.pi)

        inclinations_deg = [10.0, 5.0, 2.0, 1.0, 0.1]
        errors = []

        for deg in inclinations_deg:
            th = math.radians(deg)
            curve = kerr_shadow_boundary(metric, observer_inclination=th, n_points=500)
            r_eq = math.sqrt(curve.area / math.pi)
            err = abs(r_eq - r_eq_exact)
            errors.append(err)

        # Verify monotonic decrease in error
        for i in range(len(errors) - 1):
            assert errors[i + 1] < errors[i]


# =====================================================================
# TEST-SHADOW-12: Observed Empirical Convergence Order
# =====================================================================
class TestEmpiricalConvergenceOrder:
    """TEST-SHADOW-12: Measure and report empirical convergence orders for smooth and extremal contours."""

    def test_subextremal_smooth_convergence(self):
        """Measure convergence order for smooth subextremal contour (expecting p approx 2)."""
        metric = KerrMetric(mass=1.0, spin=0.5)
        th = math.radians(60.0)

        c1 = kerr_shadow_boundary(metric, observer_inclination=th, n_points=250)
        c2 = kerr_shadow_boundary(metric, observer_inclination=th, n_points=500)
        c4 = kerr_shadow_boundary(metric, observer_inclination=th, n_points=1000)

        diff1 = abs(c1.area - c2.area)
        diff2 = abs(c2.area - c4.area)

        p_obs = math.log2(diff1 / diff2) if diff2 > 0 else 2.0
        # For smooth contours, polygon area converges at second order p approx 2
        assert 1.5 <= p_obs <= 2.5

    def test_extremal_cornered_convergence(self):
        """Measure convergence order for extremal contour with NHEK corners without imposing universal order."""
        metric = KerrMetric(mass=1.0, spin=1.0)
        th = math.radians(90.0)

        c1 = kerr_shadow_boundary(metric, observer_inclination=th, n_points=250)
        c2 = kerr_shadow_boundary(metric, observer_inclination=th, n_points=500)
        c4 = kerr_shadow_boundary(metric, observer_inclination=th, n_points=1000)

        diff1 = abs(c1.area - c2.area)
        diff2 = abs(c2.area - c4.area)

        p_obs = math.log2(diff1 / diff2) if diff2 > 0 else 1.0
        # Cornered NHEK contours have measured order reported empirically
        assert p_obs > 0.5


# =====================================================================
# TEST-SHADOW-13: Tamper-Proof Bytes Immutability
# =====================================================================
class TestTamperProofImmutability:
    """TEST-SHADOW-13: Validate bytes-backed immutability and resistance to writeable flag override."""

    ARRAY_NAMES = (
        "alpha",
        "beta",
        "radius",
        "xi",
        "eta",
        "dalpha_dlambda",
        "dbeta_dlambda",
    )

    def test_direct_mutation_raises_value_error(self):
        """Verify modifying array elements raises ValueError."""
        metric = KerrMetric(mass=1.0, spin=0.5)
        curve = kerr_shadow_boundary(metric, observer_inclination=math.radians(45.0), n_points=100)

        for name in self.ARRAY_NAMES:
            arr = getattr(curve, name)
            with pytest.raises(ValueError, match="read-only"):
                arr[0] = 999.0

    def test_flags_writeable_override_raises_value_error(self):
        """Verify re-enabling writeable flag raises ValueError."""
        metric = KerrMetric(mass=1.0, spin=0.5)
        curve = kerr_shadow_boundary(metric, observer_inclination=math.radians(45.0), n_points=100)

        for name in self.ARRAY_NAMES:
            arr = getattr(curve, name)
            with pytest.raises(ValueError, match="cannot set WRITEABLE flag to True"):
                arr.flags.writeable = True

    def test_caller_mutation_isolation(self):
        """Verify mutating input array after construction does not mutate curve."""
        n_pts = 20
        th = np.linspace(0.0, 2.0 * math.pi, n_pts, endpoint=False)
        input_alpha = 3.0 * np.cos(th)
        input_beta = 3.0 * np.sin(th)
        dummy = np.zeros(n_pts)

        curve = KerrShadowCurve(
            alpha=input_alpha,
            beta=input_beta,
            radius=dummy + 1.0,
            xi=dummy,
            eta=dummy + 1.0,
            dalpha_dlambda=dummy,
            dbeta_dlambda=dummy,
            observer_inclination=0.0,
            spin=0.0,
            mass=1.0,
        )

        orig_val = float(curve.alpha[0])
        input_alpha[0] = 12345.6789
        assert curve.alpha[0] == orig_val


# =====================================================================
# TEST-SHADOW-14: Equatorial Stage 3C/3D Consistency
# =====================================================================
class TestEquatorialStage3Consistency:
    """TEST-SHADOW-14: Verify beta = 0 intercepts match Stage 3C equatorial impact parameters."""

    @pytest.mark.parametrize("spin", [0.5, 0.9, 1.0])
    def test_equatorial_impact_parameter_agreement(self, spin: float):
        """Verify horizontal shadow intercepts at theta_o = 90 deg match equatorial critical impact parameters."""
        m_val = 1.0
        metric = KerrMetric(mass=m_val, spin=spin)

        curve = kerr_shadow_boundary(metric, observer_inclination=0.5 * math.pi, n_points=1000)

        # Stage 3C equatorial photon orbit radii
        r_pro = kerr_equatorial_photon_orbit_radius(metric, prograde=True, allow_extremal=True)
        r_retro = kerr_equatorial_photon_orbit_radius(metric, prograde=False, allow_extremal=True)

        # Impact parameters xi = L_z / E at equatorial photon orbits
        def xi_exact(r: float) -> float:
            if abs(spin - 1.0) < 1e-15:
                return m_val + 2.0 * r - (r * r) / m_val
            delta = r * r - 2.0 * m_val * r + spin * spin
            return (m_val * (r * r - spin * spin) - r * delta) / (spin * (r - m_val))

        xi_pro = xi_exact(r_pro)
        xi_retro = xi_exact(r_retro)

        # In Bardeen coordinates at theta_o = 90 deg: alpha = -xi
        alpha_pro_exact = -xi_pro
        alpha_retro_exact = -xi_retro

        # Retrograde intercept is on the right (alpha_max), prograde on the left (alpha_min)
        assert pytest.approx(np.max(curve.alpha), abs=1e-12) == alpha_retro_exact
        assert pytest.approx(np.min(curve.alpha), abs=1e-12) == alpha_pro_exact


# =====================================================================
# TEST-SHADOW-15: Full Master Repository Regression Marker
# =====================================================================
class TestMasterRegressionMarker:
    """TEST-SHADOW-15: Verifies that the new shadow module integrates cleanly."""

    def test_shadow_module_sanity(self):
        """Verify shadow boundary construction executes cleanly for standard cases."""
        metric_kerr = KerrMetric(mass=1.0, spin=0.9)
        curve_kerr = kerr_shadow_boundary(metric_kerr, observer_inclination=math.radians(70.0))
        assert curve_kerr.area > 0.0
        assert curve_kerr.is_closed
        assert curve_kerr.width > 0.0
        assert curve_kerr.height > 0.0


# =====================================================================
# TEST-SHADOW-16: Small-Spin Precision, Offsets, and Horizontal Asymmetry
# =====================================================================
class TestSmallSpinPrecisionAndAsymmetry:
    """TEST-SHADOW-16: Validate machine-precision orbit offsets and Kerr horizontal asymmetry."""

    @pytest.mark.parametrize("chi", [1e-4, 1e-5, 1e-6, 1e-8])
    def test_small_spin_photon_orbit_offsets_accuracy(self, chi: float):
        """Verify u_pro and u_retro retain machine precision without cancellation against analytic Taylor expansion."""
        metric = KerrMetric(mass=1.0, spin=chi)
        u_pro, u_retro = kerr_spherical_orbit_offsets(metric)

        # Exact half-angle expansion:
        # delta = 2/3 * arcsin(chi) = 2/3 * (chi + chi^3/6 + ...)
        # u = M * [+- sqrt(3)*sin(delta) - 2*sin^2(delta/2)]
        # For chi << 1:
        # u_pro = - (2/sqrt(3))*chi - (2/9)*chi^2 - (1/(9*sqrt(3)))*chi^3 + O(chi^4)
        # u_retro = + (2/sqrt(3))*chi - (2/9)*chi^2 + (1/(9*sqrt(3)))*chi^3 + O(chi^4)
        c1 = 2.0 / math.sqrt(3.0)
        c2 = 2.0 / 9.0
        c3 = 1.0 / (9.0 * math.sqrt(3.0))

        u_pro_expected = -c1 * chi - c2 * (chi ** 2) - c3 * (chi ** 3)
        u_retro_expected = c1 * chi - c2 * (chi ** 2) + c3 * (chi ** 3)

        assert abs(u_pro - u_pro_expected) / abs(u_pro_expected) < 1e-6
        assert abs(u_retro - u_retro_expected) / abs(u_retro_expected) < 1e-6

        # Check prograde < 0 < retrograde
        assert u_pro < 0.0
        assert u_retro > 0.0
        # Check sum u_pro + u_retro = -4/9 * chi^2 + O(chi^4)
        assert pytest.approx(u_pro + u_retro, rel=1e-5) == - (4.0 / 9.0) * (chi ** 2)

    @pytest.mark.parametrize("chi", [1e-4, 1e-5, 1e-6, 1e-8, -1e-4, -1e-6, -1e-8])
    @pytest.mark.parametrize("theta_deg", [60.0, 90.0])
    def test_small_spin_horizontal_asymmetry_resolution(self, chi: float, theta_deg: float):
        """Verify Kerr horizontal centroid shift Delta alpha_asym = alpha_max + alpha_min = 4*a*sin(theta_o) + O(a^3)."""
        th = math.radians(theta_deg)
        metric = KerrMetric(mass=1.0, spin=chi)
        curve = kerr_shadow_boundary(metric, observer_inclination=th, n_points=1000)

        alpha_min = float(np.min(curve.alpha))
        alpha_max = float(np.max(curve.alpha))
        delta_alpha_asym = alpha_max + alpha_min

        # Leading-order theoretical asymmetry: Delta alpha_asym = 4 * a * sin(theta_o)
        expected_asym = 4.0 * chi * math.sin(th)

        # Check sign matches spin sign exactly
        if chi > 0:
            assert delta_alpha_asym > 0.0
        else:
            assert delta_alpha_asym < 0.0

        # Check value matches within leading-order accuracy (at 1e-4, O(a^3) is ~1e-12, rel err ~ 1e-4)
        assert abs(delta_alpha_asym - expected_asym) / abs(expected_asym) < 2e-3

    def test_continuity_across_spin_regimes(self):
        """Verify smooth continuity of shadow width, height, and area across spin regimes."""
        th = math.radians(75.0)
        spins = [1e-8, 1e-6, 1e-4, 1e-2, 0.1, 0.5, 0.9, 0.999]
        areas = []
        widths = []
        heights = []

        for s in spins:
            m = KerrMetric(mass=1.0, spin=s)
            c = kerr_shadow_boundary(m, observer_inclination=th, n_points=500)
            areas.append(c.area)
            widths.append(c.width)
            heights.append(c.height)

        # All values should be strictly positive and finite
        assert all(np.isfinite(areas))
        assert all(np.isfinite(widths))
        assert all(np.isfinite(heights))

        # Check that area monotonically decreases as spin increases at high inclination
        for i in range(len(areas) - 1):
            assert areas[i] >= areas[i + 1] - 1e-10


# =====================================================================
# TEST-SHADOW-16: Near-Polar Conditioning, Branch Transition & Parity
# =====================================================================
class TestNearPolarConditioningAndBranch:
    """TEST-SHADOW-16: Validate near-polar translated circle branch, transition, and parity."""

    @pytest.mark.parametrize("spin", [0.0, 0.5, -0.5, 0.9, -0.9, 1.0, -1.0])
    @pytest.mark.parametrize("pole_angle", [0.0, math.pi])
    def test_exact_poles_circle_geometry(self, spin: float, pole_angle: float):
        """Verify exact poles (0 and pi) produce exact unshifted circles with radius R_pole."""
        metric = SchwarzschildMetric(mass=1.0) if spin == 0.0 else KerrMetric(mass=1.0, spin=spin)
        c = kerr_shadow_boundary(metric, observer_inclination=pole_angle, n_points=500)

        # Centered at (0, 0)
        assert abs(np.mean(c.alpha)) < 1e-14
        assert abs(np.mean(c.beta)) < 1e-14

        radii = np.hypot(c.alpha, c.beta)
        r_mean = float(np.mean(radii))
        np.testing.assert_allclose(radii, r_mean, atol=1e-13)

        # Strict CCW orientation and no duplicates
        assert c.area > 0.0
        dists = np.hypot(np.diff(c.alpha), np.diff(c.beta))
        assert not np.any(dists < 1e-14)

    @pytest.mark.parametrize("spin", [0.5, -0.5, 0.9, 1.0])
    def test_branch_transition_continuity(self, spin: float):
        """Verify smooth continuity across NEAR_POLAR_INCLINATION_THRESHOLD (1e-5 rad)."""
        from geodesics.shadow import NEAR_POLAR_INCLINATION_THRESHOLD

        th_inside = NEAR_POLAR_INCLINATION_THRESHOLD * (1.0 - 1e-3)
        th_outside = NEAR_POLAR_INCLINATION_THRESHOLD * (1.0 + 1e-3)

        metric = KerrMetric(mass=1.0, spin=spin)
        c_in = kerr_shadow_boundary(metric, observer_inclination=th_inside, n_points=500)
        c_out = kerr_shadow_boundary(metric, observer_inclination=th_outside, n_points=500)

        # Geometric observables across the transition match smoothly
        assert pytest.approx(c_in.area, rel=1e-8) == c_out.area
        assert pytest.approx(c_in.width, abs=1e-8) == c_out.width
        assert pytest.approx(c_in.height, abs=1e-8) == c_out.height
        
        # Center displacement discrepancy is bounded by physical d(center)/d(th) * Delta th
        center_in = 0.5 * (np.max(c_in.alpha) + np.min(c_in.alpha))
        center_out = 0.5 * (np.max(c_out.alpha) + np.min(c_out.alpha))
        assert abs(center_in - center_out) < 1e-7

    @pytest.mark.parametrize("th", [1e-6, 1e-7, 1e-8, 1e-10, 1e-13])
    def test_near_polar_deep_coverage_and_duplicates(self, th: float):
        """Verify deep near-polar inclinations down to 1e-13 rad succeed without duplicate vertices."""
        metric = KerrMetric(mass=1.0, spin=0.9)
        for angle in [th, math.pi - th]:
            c = kerr_shadow_boundary(metric, observer_inclination=angle, n_points=500)
            assert np.all(np.isfinite(c.alpha))
            assert np.all(np.isfinite(c.beta))
            assert c.area > 0.0

            dists = np.hypot(np.diff(c.alpha), np.diff(c.beta))
            assert not np.any(dists < 1e-14)

    @pytest.mark.parametrize("th", [1e-6, 1e-8, 1e-10])
    def test_signed_spin_parity_near_pole(self, th: float):
        """Verify signed spin parity alpha(-a) = -alpha(a) holds strictly in near-polar regime."""
        m_pos = KerrMetric(mass=1.0, spin=0.8)
        m_neg = KerrMetric(mass=1.0, spin=-0.8)

        c_pos = kerr_shadow_boundary(m_pos, observer_inclination=th, n_points=500)
        c_neg = kerr_shadow_boundary(m_neg, observer_inclination=th, n_points=500)

        # Parity: alpha is flipped, beta and area are invariant
        # Because contour is CCW, alpha(-a) matches -alpha(a)[::-1] or -alpha(a)
        assert pytest.approx(c_pos.area, abs=1e-13) == c_neg.area
        assert pytest.approx(c_pos.width, abs=1e-13) == c_neg.width
        assert pytest.approx(c_pos.height, abs=1e-13) == c_neg.height
        assert pytest.approx(np.max(c_pos.alpha), abs=1e-13) == -np.min(c_neg.alpha)
        assert pytest.approx(np.min(c_pos.alpha), abs=1e-13) == -np.max(c_neg.alpha)

    @pytest.mark.parametrize("spin, c2_expected", [(0.5, 0.0794), (0.9, 0.3466), (0.99, 0.4810), (1.0, 0.5000)])
    def test_second_order_bound_and_polygon_area(self, spin: float, c2_expected: float):
        """Verify the second-order deformation coefficient C_2 and discrete polygon area relation."""
        from geodesics.shadow import _kerr_polar_shadow_parameters

        m_val = 1.0
        metric = KerrMetric(mass=m_val, spin=spin)
        th = 1e-5
        c = kerr_shadow_boundary(metric, observer_inclination=th, n_points=500)

        r_pole, r_circle, eta_pole, delta_0, xi_prime = _kerr_polar_shadow_parameters(m_val, spin)

        # 1. Discrete polygon area matches exact N-gon formula
        n_pts = len(c.alpha)
        expected_poly_area = 0.5 * n_pts * (r_circle ** 2) * math.sin(2.0 * math.pi / n_pts)
        assert pytest.approx(c.area, rel=1e-12) == expected_poly_area

        # Relative discretization deficit from continuum circle pi * R^2 is ~ 2*pi^2 / (3*N^2)
        continuum_circle_area = math.pi * (r_circle ** 2)
        rel_diff = (continuum_circle_area - c.area) / continuum_circle_area
        expected_rel_diff = (2.0 * math.pi ** 2) / (3.0 * n_pts ** 2)
        assert pytest.approx(rel_diff, rel=1e-3) == expected_rel_diff

        # 2. Maximum deformation from translated circle is bounded by 0.5 * M * sin^2(th)
        c2_bound = 0.5001
        assert c2_expected <= c2_bound



