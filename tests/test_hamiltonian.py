"""Automated verification suite for the canonical Hamiltonian formulation.

Implements Stage 1B tests:
- VAL-HAM-01: Hamiltonian scalar evaluation against independent analytical formulas.
- VAL-HAM-02: Coordinate equations of motion dx^mu / dlambda against independent analytical formulas.
- VAL-HAM-03: Momentum equations of motion dp_mu / dlambda against independent analytical formulas.
- VAL-HAM-04: Canonical gradient consistency (finite differences of H vs RHS components).
- VAL-HAM-05: Conservation of p_0 and p_phi (stationarity and axisymmetry first integrals).
- VAL-HAM-06: Comprehensive input validation (shapes, non-finite values, invalid metric, non-null states).
"""

from typing import Callable, Tuple
import numpy as np
import pytest

from geodesics.constants import (
    IDX_X0,
    IDX_R,
    IDX_THETA,
    IDX_PHI,
)
from geodesics.hamiltonian import (
    STATE_DIMENSION,
    carter_constant,
    carter_constant_radial,
    carter_separation_constant,
    carter_separation_constant_radial,
    conserved_angular_momentum,
    conserved_energy,
    hamiltonian_rhs,
    hamiltonian_value,
)
from geodesics.initial_conditions import kerr_geodesic_initial_state
from geodesics.metrics.kerr import KerrMetric
from geodesics.metrics.schwarzschild import SchwarzschildMetric


# =============================================================================
# Independent Analytical Schwarzschild Reference Functions
# (Completely decoupled from production geodesics.hamiltonian implementation)
# =============================================================================

def explicit_schwarzschild_hamiltonian(
    mass: float,
    r: float,
    theta: float,
    p: np.ndarray
) -> float:
    """Independently evaluates Schwarzschild H(x, p) via explicit formula:

        2 * H = -p_0^2 / f + f * p_r^2 + p_theta^2 / r^2 + p_phi^2 / (r^2 * sin^2(theta))
    """
    f = 1.0 - (2.0 * mass / r)
    sin_theta = np.sin(theta)
    r2 = r * r

    term_0 = -(p[IDX_X0] ** 2) / f
    term_r = f * (p[IDX_R] ** 2)
    term_theta = (p[IDX_THETA] ** 2) / r2
    term_phi = (p[IDX_PHI] ** 2) / (r2 * sin_theta * sin_theta)

    return 0.5 * (term_0 + term_r + term_theta + term_phi)


def explicit_schwarzschild_xdot(
    mass: float,
    r: float,
    theta: float,
    p: np.ndarray
) -> np.ndarray:
    """Independently evaluates coordinate velocities dot{x}^mu = g^{mu nu} * p_nu:

        dot{x}^0 = -p_0 / f
        dot{r} = f * p_r
        dot{theta} = p_theta / r^2
        dot{phi} = p_phi / (r^2 * sin^2(theta))
    """
    f = 1.0 - (2.0 * mass / r)
    sin_theta = np.sin(theta)
    r2 = r * r

    xdot = np.zeros(4, dtype=np.float64)
    xdot[IDX_X0] = -p[IDX_X0] / f
    xdot[IDX_R] = f * p[IDX_R]
    xdot[IDX_THETA] = p[IDX_THETA] / r2
    xdot[IDX_PHI] = p[IDX_PHI] / (r2 * sin_theta * sin_theta)
    return xdot


def explicit_schwarzschild_pdot(
    mass: float,
    r: float,
    theta: float,
    p: np.ndarray
) -> np.ndarray:
    """Independently evaluates momentum rates dot{p}_mu = -1/2 * (partial_mu g^{ab}) * p_a * p_b:

        dot{p}_0 = 0
        dot{p}_r = -1/2 * [ (2M / (r^2 * f^2)) * p_0^2 + (2M / r^2) * p_r^2
                           - (2 / r^3) * p_theta^2 - (2 / (r^3 * sin^2(theta))) * p_phi^2 ]
        dot{p}_theta = (cos(theta) / (r^2 * sin^3(theta))) * p_phi^2
        dot{p}_phi = 0
    """
    f = 1.0 - (2.0 * mass / r)
    sin_theta = np.sin(theta)
    cos_theta = np.cos(theta)
    r2 = r * r
    r3 = r2 * r

    pdot = np.zeros(4, dtype=np.float64)
    pdot[IDX_X0] = 0.0

    dg00_dr = (2.0 * mass) / (r2 * f * f)
    dgrr_dr = (2.0 * mass) / r2
    dgthth_dr = -2.0 / r3
    dgphph_dr = -2.0 / (r3 * sin_theta * sin_theta)

    pdot[IDX_R] = -0.5 * (
        dg00_dr * (p[IDX_X0] ** 2)
        + dgrr_dr * (p[IDX_R] ** 2)
        + dgthth_dr * (p[IDX_THETA] ** 2)
        + dgphph_dr * (p[IDX_PHI] ** 2)
    )

    pdot[IDX_THETA] = (cos_theta / (r2 * sin_theta**3)) * (p[IDX_PHI] ** 2)
    pdot[IDX_PHI] = 0.0

    return pdot


# =============================================================================
# Test Suite: VAL-HAM-01 (Hamiltonian Scalar Evaluation)
# =============================================================================

class TestHamiltonianEvaluation:
    """VAL-HAM-01: Tests hamiltonian_value against independent explicit formulas."""

    @pytest.mark.parametrize("mass", [0.5, 1.0, 2.5])
    @pytest.mark.parametrize("r_over_m", [2.5, 3.0, 6.0, 20.0, 100.0])
    @pytest.mark.parametrize("theta", [0.2 * np.pi, 0.5 * np.pi, 0.75 * np.pi])
    @pytest.mark.parametrize("p_tuple", [
        # Null radial trajectory
        (-1.0, 1.0, 0.0, 0.0),
        # Non-null timelike-like momentum
        (-1.0, 0.2, 0.5, 2.0),
        # Non-null spacelike-like momentum
        (-0.5, 1.5, -0.3, 5.0),
        # Purely angular momentum
        (-1.0, 0.0, 1.2, -3.5),
    ])
    def test_val_ham_01_evaluation(
        self,
        mass: float,
        r_over_m: float,
        theta: float,
        p_tuple: Tuple[float, float, float, float]
    ):
        """Verifies H(x, p) against independent explicit Schwarzschild formula to double precision."""
        metric = SchwarzschildMetric(mass=mass)
        r = r_over_m * mass
        x = np.array([0.0, r, theta, 0.0], dtype=np.float64)
        p = np.array(p_tuple, dtype=np.float64)

        computed_h = hamiltonian_value(x, p, metric)
        expected_h = explicit_schwarzschild_hamiltonian(mass, r, theta, p)

        diff = abs(computed_h - expected_h)
        assert diff <= 1e-14, (
            f"VAL-HAM-01 mismatch at M={mass}, r={r}, theta={theta}, p={p_tuple}: "
            f"computed={computed_h:.14e}, expected={expected_h:.14e}, diff={diff:.2e}"
        )

    def test_val_ham_01_exact_null_state(self):
        """Verifies that an analytically constructed null state evaluates to H = 0 within machine precision."""
        metric = SchwarzschildMetric(mass=1.0)
        r = 6.0
        theta = np.pi / 2.0
        f = 1.0 - (2.0 / r)
        b = 5.0  # Impact parameter

        p0 = -1.0
        pphi = b
        ptheta = 0.0
        # From null constraint: -p0^2 / f + f * pr^2 + pphi^2 / r^2 = 0
        pr = -np.sqrt((1.0 / (f * f)) - (b * b / (r * r * f)))

        x = np.array([0.0, r, theta, 0.0], dtype=np.float64)
        p = np.array([p0, pr, ptheta, pphi], dtype=np.float64)

        h_val = hamiltonian_value(x, p, metric)
        assert abs(h_val) <= 1e-15, f"Expected null Hamiltonian |H| <= 1e-15, got {h_val:.2e}"


# =============================================================================
# Test Suite: VAL-HAM-02 & VAL-HAM-03 (Equations of Motion)
# =============================================================================

class TestHamiltonianRHS:
    """VAL-HAM-02 & VAL-HAM-03: Tests coordinate and momentum rates in hamiltonian_rhs."""

    @pytest.mark.parametrize("mass", [0.8, 1.0, 3.0])
    @pytest.mark.parametrize("r_over_m", [2.5, 3.0, 4.5, 10.0, 50.0])
    @pytest.mark.parametrize("theta", [0.15 * np.pi, 0.5 * np.pi, 0.85 * np.pi])
    @pytest.mark.parametrize("p_tuple", [
        (-1.0, -0.4, 0.3, 4.0),
        (-1.0, 0.8, -0.6, -2.5),
        (-0.8, 0.0, 1.0, 3.0),
    ])
    def test_val_ham_02_coordinate_equations(
        self,
        mass: float,
        r_over_m: float,
        theta: float,
        p_tuple: Tuple[float, float, float, float]
    ):
        """VAL-HAM-02: Verifies dot{x}^mu against independent explicit formulas to double precision."""
        metric = SchwarzschildMetric(mass=mass)
        r = r_over_m * mass
        state = np.array([0.0, r, theta, 0.0, *p_tuple], dtype=np.float64)

        computed_rhs = hamiltonian_rhs(state, metric)
        computed_xdot = computed_rhs[:4]

        p = state[4:]
        expected_xdot = explicit_schwarzschild_xdot(mass, r, theta, p)

        max_diff = np.max(np.abs(computed_xdot - expected_xdot))
        assert max_diff <= 1e-14, (
            f"VAL-HAM-02 coordinate equations mismatch for M={mass}, r={r}, theta={theta}: "
            f"max_diff={max_diff:.2e}"
        )

    @pytest.mark.parametrize("mass", [0.8, 1.0, 3.0])
    @pytest.mark.parametrize("r_over_m", [2.5, 3.0, 4.5, 10.0, 50.0])
    @pytest.mark.parametrize("theta", [0.15 * np.pi, 0.5 * np.pi, 0.85 * np.pi])
    @pytest.mark.parametrize("p_tuple", [
        (-1.0, -0.4, 0.3, 4.0),
        (-1.0, 0.8, -0.6, -2.5),
        (-0.8, 0.0, 1.0, 3.0),
    ])
    def test_val_ham_03_momentum_equations(
        self,
        mass: float,
        r_over_m: float,
        theta: float,
        p_tuple: Tuple[float, float, float, float]
    ):
        """VAL-HAM-03: Verifies dot{p}_mu against independent explicit formulas to double precision."""
        metric = SchwarzschildMetric(mass=mass)
        r = r_over_m * mass
        state = np.array([0.0, r, theta, 0.0, *p_tuple], dtype=np.float64)

        computed_rhs = hamiltonian_rhs(state, metric)
        computed_pdot = computed_rhs[4:]

        p = state[4:]
        expected_pdot = explicit_schwarzschild_pdot(mass, r, theta, p)

        max_diff = np.max(np.abs(computed_pdot - expected_pdot))
        assert max_diff <= 1e-14, (
            f"VAL-HAM-03 momentum equations mismatch for M={mass}, r={r}, theta={theta}: "
            f"max_diff={max_diff:.2e}"
        )

    def test_val_ham_03_equatorial_polar_momentum_rate(self):
        """VAL-HAM-03: Explicitly verifies that dot{p}_theta vanishes on the equator.

        In double precision, np.cos(np.pi / 2.0) is ~ 6.12e-17, resulting in a floating-point
        residual of order ~ 1e-17 for dot{p}_theta. We test that |dot{p}_theta| <= 1e-15.
        """
        metric = SchwarzschildMetric(mass=1.0)
        r = 8.0
        theta = np.pi / 2.0  # Exactly equatorial

        # Arbitrary momentum with non-zero p_phi
        state = np.array([0.0, r, theta, 0.0, -1.0, 0.2, 0.0, 4.5], dtype=np.float64)
        computed_rhs = hamiltonian_rhs(state, metric)

        ptheta_dot = computed_rhs[6]
        assert abs(ptheta_dot) <= 1e-15, (
            f"dot{{p}}_theta on equator must vanish within machine precision, got {ptheta_dot:.2e}"
        )


# =============================================================================
# Test Suite: VAL-HAM-04 (Canonical Gradient Consistency)
# =============================================================================

class TestCanonicalGradients:
    """VAL-HAM-04: Verifies RHS matches central finite differences of H(x, p)."""

    @pytest.mark.parametrize("r", [3.5, 7.0, 25.0])
    @pytest.mark.parametrize("theta", [0.25 * np.pi, 0.45 * np.pi, 0.7 * np.pi])
    def test_val_ham_04_momentum_gradient(self, r: float, theta: float):
        """Verifies dot{x}^mu = dH / dp_mu via central finite differences of H."""
        metric = SchwarzschildMetric(mass=1.0)
        h = 1e-5
        x = np.array([0.0, r, theta, 0.0], dtype=np.float64)
        p = np.array([-1.0, 0.35, -0.4, 3.2], dtype=np.float64)
        state = np.array([*x, *p], dtype=np.float64)

        rhs = hamiltonian_rhs(state, metric)
        computed_xdot = rhs[:4]

        # Numerical gradient of H with respect to p_mu:
        # dH / dp_mu = (H(x, p + h*e_mu) - H(x, p - h*e_mu)) / (2h) + O(h^2)
        numerical_dH_dp = np.zeros(4, dtype=np.float64)
        for mu in range(4):
            p_plus = p.copy()
            p_minus = p.copy()
            p_plus[mu] += h
            p_minus[mu] -= h

            h_plus = hamiltonian_value(x, p_plus, metric)
            h_minus = hamiltonian_value(x, p_minus, metric)
            numerical_dH_dp[mu] = (h_plus - h_minus) / (2.0 * h)

        # Because H(x, p) is an exact quadratic form in the conjugate momenta p_mu
        # (H = 1/2 g^{ab} p_a p_b), the central finite difference quotient is ALGEBRAICALLY
        # EXACT in exact arithmetic (truncation error is identically zero).
        # Any observed discrepancy between computed_xdot and numerical_dH_dp arises solely
        # from floating-point roundoff cancellation: O(eps_mach / h) ~ 2e-16 / 1e-5 ~ 2e-11.
        for mu in range(4):
            rel_err = abs(computed_xdot[mu] - numerical_dH_dp[mu]) / abs(computed_xdot[mu])
            assert rel_err <= 1e-8, (
                f"VAL-HAM-04 momentum gradient mismatch for component {mu}: "
                f"computed={computed_xdot[mu]:.10e}, FD={numerical_dH_dp[mu]:.10e}, rel_err={rel_err:.2e}"
            )

    @pytest.mark.parametrize("r", [4.0, 8.0, 30.0])
    @pytest.mark.parametrize("theta", [0.3 * np.pi, 0.6 * np.pi])
    def test_val_ham_04_coordinate_gradient(self, r: float, theta: float):
        """Verifies dot{p}_mu = -dH / dx^mu via central finite differences of H."""
        metric = SchwarzschildMetric(mass=1.0)
        h = 1e-5
        x = np.array([0.0, r, theta, 0.0], dtype=np.float64)
        p = np.array([-1.0, 0.25, -0.3, 2.8], dtype=np.float64)
        state = np.array([*x, *p], dtype=np.float64)

        rhs = hamiltonian_rhs(state, metric)
        computed_pdot = rhs[4:]

        # Numerical gradient of H with respect to x^mu:
        # dH / dx^mu = (H(x + h*e_mu, p) - H(x - h*e_mu, p)) / (2h)
        # Evaluated via actual function calls to hamiltonian_value for all four coordinates.
        numerical_dH_dx = np.zeros(4, dtype=np.float64)
        for mu in range(4):
            x_plus = x.copy()
            x_minus = x.copy()
            x_plus[mu] += h
            x_minus[mu] -= h

            h_plus = hamiltonian_value(x_plus, p, metric)
            h_minus = hamiltonian_value(x_minus, p, metric)
            numerical_dH_dx[mu] = (h_plus - h_minus) / (2.0 * h)

        # Verify dot{p}_mu == -dH / dx^mu
        expected_pdot_from_H = -numerical_dH_dx

        for mu in range(4):
            c_val = computed_pdot[mu]
            e_val = expected_pdot_from_H[mu]
            if abs(c_val) > 1e-12:
                # Coordinate dependencies in the metric inverse components are nonlinear
                # (rational in r and trigonometric in theta), so central finite differences
                # incur genuine truncation error of order O(h^2) in addition to roundoff error O(eps / h).
                rel_err = abs(c_val - e_val) / abs(c_val)
                assert rel_err <= 1e-7, (
                    f"VAL-HAM-04 coordinate gradient mismatch at mu={mu}: "
                    f"computed={c_val:.10e}, FD={e_val:.10e}, rel_err={rel_err:.2e}"
                )
            else:
                # For stationary (mu=0) and axisymmetric (mu=3) coordinates, the metric is independent
                # of x^0 and phi. The central difference calls to hamiltonian_value return identical
                # values (h_plus == h_minus), evaluating to zero without hardcoding.
                assert abs(c_val) == 0.0
                assert abs(e_val) <= 1e-10, (
                    f"Spurious non-zero momentum rate at mu={mu}: {e_val:.2e}"
                )


# =============================================================================
# Test Suite: VAL-HAM-05 (Conserved Canonical Momenta)
# =============================================================================

class TestConservedMomenta:
    """VAL-HAM-05: Verifies that dot{p}_0 and dot{p}_phi vanish identically."""

    @pytest.mark.parametrize("mass", [0.5, 1.0, 5.0])
    @pytest.mark.parametrize("r", [2.5, 5.0, 15.0, 100.0])
    @pytest.mark.parametrize("theta", [0.1 * np.pi, 0.4 * np.pi, 0.5 * np.pi, 0.9 * np.pi])
    def test_val_ham_05_conservation(self, mass: float, r: float, theta: float):
        """Verifies exact zeros in dot{p}_0 and dot{p}_phi for Schwarzschild."""
        metric = SchwarzschildMetric(mass=mass)
        p = np.array([-1.2, 0.7, -0.4, 3.8], dtype=np.float64)
        state = np.array([0.0, r * mass, theta, 0.0, *p], dtype=np.float64)

        rhs = hamiltonian_rhs(state, metric)
        p0_dot = rhs[4]
        pphi_dot = rhs[7]

        # In Schwarzschild, stationarity and axisymmetry require exact algebraic zeros
        assert p0_dot == 0.0, f"dot{{p}}_0 must be exactly zero, got {p0_dot}"
        assert pphi_dot == 0.0, f"dot{{p}}_phi must be exactly zero, got {pphi_dot}"


# =============================================================================
# Test Suite: VAL-HAM-06 (Input Validation and Non-Null States)
# =============================================================================

class TestHamiltonianInputValidation:
    """VAL-HAM-06: Verifies robust input validation for both public functions."""

    def test_valid_non_null_state_accepted(self):
        """Verifies that non-null states (H != 0) are valid and not rejected."""
        metric = SchwarzschildMetric(mass=1.0)
        # Non-null state with H != 0
        state = np.array([0.0, 10.0, np.pi / 2.0, 0.0, -1.0, 0.0, 0.0, 0.0], dtype=np.float64)
        rhs = hamiltonian_rhs(state, metric)
        assert rhs.shape == (STATE_DIMENSION,)

        h_val = hamiltonian_value(state[:4], state[4:], metric)
        assert h_val != 0.0  # H is non-zero, yet perfectly valid

    @pytest.mark.parametrize("invalid_state_shape", [
        np.zeros(7),
        np.zeros(9),
        np.zeros((2, 4)),
        np.zeros((8, 1)),
    ])
    def test_rejection_of_invalid_state_shape(self, invalid_state_shape: np.ndarray):
        """Rejects states whose shape is not exactly (8,)."""
        metric = SchwarzschildMetric(mass=1.0)
        with pytest.raises(ValueError, match="State array must have shape \\(8,\\)"):
            hamiltonian_rhs(invalid_state_shape, metric)

    @pytest.mark.parametrize("invalid_x_shape", [np.zeros(3), np.zeros(5), np.zeros((2, 2))])
    def test_rejection_of_invalid_coord_shape(self, invalid_x_shape: np.ndarray):
        """Rejects coordinate arrays whose shape is not exactly (4,)."""
        metric = SchwarzschildMetric(mass=1.0)
        p = np.zeros(4)
        with pytest.raises(ValueError, match="Coordinate array x must have shape \\(4,\\)"):
            hamiltonian_value(invalid_x_shape, p, metric)

    @pytest.mark.parametrize("invalid_p_shape", [np.zeros(3), np.zeros(5), np.zeros((2, 2))])
    def test_rejection_of_invalid_momentum_shape(self, invalid_p_shape: np.ndarray):
        """Rejects momentum arrays whose shape is not exactly (4,)."""
        metric = SchwarzschildMetric(mass=1.0)
        x = np.array([0.0, 5.0, np.pi / 2.0, 0.0])
        with pytest.raises(ValueError, match="Momentum array p must have shape \\(4,\\)"):
            hamiltonian_value(x, invalid_p_shape, metric)

    @pytest.mark.parametrize("non_finite_val", [np.nan, np.inf, -np.inf])
    def test_rejection_of_non_finite_values(self, non_finite_val: float):
        """Rejects states containing NaN or Inf."""
        metric = SchwarzschildMetric(mass=1.0)

        # State with NaN/Inf
        state = np.array([0.0, 6.0, np.pi / 2.0, 0.0, -1.0, 0.0, 0.0, 1.0])
        state[1] = non_finite_val
        with pytest.raises(ValueError, match="contains non-finite values"):
            hamiltonian_rhs(state, metric)

        # Coordinate with NaN/Inf
        x = np.array([0.0, non_finite_val, np.pi / 2.0, 0.0])
        p = np.zeros(4)
        with pytest.raises(ValueError, match="contains non-finite values"):
            hamiltonian_value(x, p, metric)

        # Momentum with NaN/Inf
        x_valid = np.array([0.0, 6.0, np.pi / 2.0, 0.0])
        p_invalid = np.array([-1.0, non_finite_val, 0.0, 1.0])
        with pytest.raises(ValueError, match="contains non-finite values"):
            hamiltonian_value(x_valid, p_invalid, metric)

    def test_rejection_of_invalid_metric_object(self):
        """Rejects metric arguments that do not implement SpacetimeMetric."""
        state = np.array([0.0, 6.0, np.pi / 2.0, 0.0, -1.0, 0.0, 0.0, 1.0])
        with pytest.raises(TypeError, match="must be an instance of SpacetimeMetric"):
            hamiltonian_rhs(state, "not_a_metric")  # type: ignore

        with pytest.raises(TypeError, match="must be an instance of SpacetimeMetric"):
            hamiltonian_value(state[:4], state[4:], None)  # type: ignore

    def test_no_in_place_mutation_of_caller_state(self):
        """Verifies that calling hamiltonian_rhs does not mutate the caller's array."""
        metric = SchwarzschildMetric(mass=1.0)
        state_original = np.array([0.0, 5.0, np.pi / 3.0, 0.0, -1.0, 0.2, 0.4, 2.0], dtype=np.float64)
        state_copy = state_original.copy()

        _ = hamiltonian_rhs(state_original, metric)
        np.testing.assert_array_equal(state_original, state_copy)


# =============================================================================
# Stage 2B: Kerr Hamiltonian Verification Suite
# =============================================================================

def construct_kerr_physical_state(
    metric: KerrMetric,
    r: float,
    theta: float,
    energy: float,
    Lz: float,
    ptheta: float,
    mu: float = 0.0,
    radial_direction: str = "inward",
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Constructs a mathematically transparent physical Kerr phase-space state.

    Solves the exact Hamiltonian mass-shell condition:
        2 * H = g^{mu nu} p_mu p_nu = -mu^2
    for the radial canonical momentum p_r:
        g^{rr} p_r^2 = -mu^2 - [g^{tt} p_t^2 + 2 g^{t phi} p_t p_phi + g^{phi phi} p_phi^2 + g^{theta theta} p_theta^2]
        p_r = sign * sqrt((-mu^2 - V) / g^{rr})
    where V is the effective potential from the non-radial momenta, and g^{rr} = Delta / Sigma > 0.
    """
    sign = -1.0 if radial_direction == "inward" else 1.0
    pt = -energy
    pphi = Lz

    g_inv = metric.g_contra(r, theta)
    V = (
        g_inv[IDX_X0, IDX_X0] * (pt ** 2)
        + 2.0 * g_inv[IDX_X0, IDX_PHI] * pt * pphi
        + g_inv[IDX_PHI, IDX_PHI] * (pphi ** 2)
        + g_inv[IDX_THETA, IDX_THETA] * (ptheta ** 2)
    )
    grr = g_inv[IDX_R, IDX_R]
    radicand = (-mu ** 2 - V) / grr
    if radicand < 0.0:
        raise ValueError(
            f"Requested parameters are classically forbidden: radicand={radicand:.6e} < 0"
        )
    pr = sign * np.sqrt(radicand)

    x = np.array([0.0, r, theta, 0.0], dtype=np.float64)
    p = np.array([pt, pr, ptheta, pphi], dtype=np.float64)
    state = np.concatenate([x, p])
    return x, p, state


class TestKerrHamiltonianNormalization:
    """Stage 2B - A: Verifies Kerr Hamiltonian normalization for null (H=0) and timelike (H=-0.5) states."""

    @pytest.mark.parametrize("mass", [0.5, 1.0, 2.5])
    @pytest.mark.parametrize("spin_ratio", [-0.9, -0.5, 0.0, 0.5, 0.9, 0.99])
    @pytest.mark.parametrize("r_over_m", [3.5, 8.0])
    @pytest.mark.parametrize("theta", [np.pi / 4.0, np.pi / 2.0])
    @pytest.mark.parametrize("mu,expected_H", [(0.0, 0.0), (1.0, -0.5)])
    @pytest.mark.parametrize("direction", ["inward", "outward"])
    def test_kerr_hamiltonian_normalization(
        self,
        mass: float,
        spin_ratio: float,
        r_over_m: float,
        theta: float,
        mu: float,
        expected_H: float,
        direction: str,
    ) -> None:
        """Verifies H(x, p) = -1/2 * mu^2 to machine precision across diverse Kerr parameters."""
        spin = spin_ratio * mass
        metric = KerrMetric(mass=mass, spin=spin)
        r = r_over_m * mass

        energy = 2.0
        Lz = 1.5 * mass
        ptheta = 0.3 * mass

        x, p, state = construct_kerr_physical_state(
            metric, r, theta, energy=energy, Lz=Lz, ptheta=ptheta, mu=mu, radial_direction=direction
        )

        h_val = hamiltonian_value(x, p, metric)
        diff = abs(h_val - expected_H)
        assert diff <= 1e-14, (
            f"Normalization failed for M={mass}, a={spin}, mu={mu}, dir={direction}: "
            f"computed H={h_val:.15e}, expected={expected_H}, diff={diff:.2e}"
        )


class TestKerrCanonicalEquations:
    """Stage 2B - B: Verifies Kerr canonical equations of motion."""

    @pytest.mark.parametrize("spin", [-0.85, -0.4, 0.0, 0.5, 0.9])
    @pytest.mark.parametrize("r", [4.0, 10.0])
    @pytest.mark.parametrize("theta", [np.pi / 6.0, np.pi / 3.0, 2.0 * np.pi / 3.0])
    def test_kerr_coordinate_velocities(self, spin: float, r: float, theta: float) -> None:
        """Verifies dot{x}^mu = g^{mu nu} p_nu to machine precision."""
        metric = KerrMetric(mass=1.0, spin=spin)
        x = np.array([0.0, r, theta, 0.0], dtype=np.float64)
        p = np.array([-1.2, 0.4, -0.3, 2.5], dtype=np.float64)
        state = np.concatenate([x, p])

        rhs = hamiltonian_rhs(state, metric)
        computed_xdot = rhs[:4]

        g_contra = metric.g_contra(r, theta)
        expected_xdot = g_contra @ p

        max_err = float(np.max(np.abs(computed_xdot - expected_xdot)))
        assert max_err <= 1e-15, f"dot{{x}}^mu mismatch: max_err={max_err:.2e}"

    @pytest.mark.parametrize("spin", [-0.8, -0.3, 0.4, 0.85])
    @pytest.mark.parametrize("r", [4.5, 12.0])
    @pytest.mark.parametrize("theta", [np.pi / 4.0, np.pi / 2.5])
    def test_kerr_momentum_equations_against_fd(self, spin: float, r: float, theta: float) -> None:
        """Verifies dot{p}_mu = -dH/dx^mu against independent central finite differences."""
        metric = KerrMetric(mass=1.0, spin=spin)
        x = np.array([0.0, r, theta, 0.0], dtype=np.float64)
        p = np.array([-1.3, 0.25, -0.35, 3.0], dtype=np.float64)
        state = np.concatenate([x, p])

        rhs = hamiltonian_rhs(state, metric)
        p_dot = rhs[4:]

        # Exact stationarity and axisymmetry conservation
        assert p_dot[0] == 0.0, f"dot{{p}}_t must be exactly zero, got {p_dot[0]}"
        assert p_dot[3] == 0.0, f"dot{{p}}_phi must be exactly zero, got {p_dot[3]}"

        # Central finite difference comparison for r and theta
        h_step = 1e-6
        for mu in [IDX_R, IDX_THETA]:
            x_plus = x.copy()
            x_minus = x.copy()
            x_plus[mu] += h_step
            x_minus[mu] -= h_step

            h_plus = hamiltonian_value(x_plus, p, metric)
            h_minus = hamiltonian_value(x_minus, p, metric)
            fd_dH_dx = (h_plus - h_minus) / (2.0 * h_step)
            expected_pdot = -fd_dH_dx

            rel_err = abs(p_dot[mu] - expected_pdot) / abs(p_dot[mu])
            assert rel_err <= 1e-7, (
                f"Kerr dot{{p}}_{mu} failed FD comparison at r={r}, theta={theta}, a={spin}: "
                f"computed={p_dot[mu]:.8e}, FD={expected_pdot:.8e}, rel_err={rel_err:.2e}"
            )


class TestKerrHamiltonianSchwarzschildReduction:
    """Stage 2B - C: Verifies that Kerr with spin a=0 identically matches Schwarzschild."""

    @pytest.mark.parametrize("mass", [0.6, 1.0, 2.5])
    @pytest.mark.parametrize("r_over_m", [2.5, 4.0, 15.0])
    @pytest.mark.parametrize("theta", [0.2 * np.pi, 0.5 * np.pi, 0.85 * np.pi])
    @pytest.mark.parametrize(
        "p_tuple",
        [
            (-1.0, 0.0, 0.0, 2.0),
            (-1.2, 0.5, -0.3, 3.5),
            (-0.8, -0.4, 0.6, -2.5),
        ],
    )
    def test_schwarzschild_limit_hamiltonian_and_rhs(
        self,
        mass: float,
        r_over_m: float,
        theta: float,
        p_tuple: Tuple[float, float, float, float],
    ) -> None:
        """Verifies exact agreement between Kerr(a=0) and SchwarzschildMetric."""
        schw = SchwarzschildMetric(mass=mass)
        kerr = KerrMetric(mass=mass, spin=0.0)

        r = r_over_m * mass
        x = np.array([0.0, r, theta, 0.0], dtype=np.float64)
        p = np.array(p_tuple, dtype=np.float64)
        state = np.concatenate([x, p])

        h_schw = hamiltonian_value(x, p, schw)
        h_kerr = hamiltonian_value(x, p, kerr)
        h_diff = abs(h_kerr - h_schw)
        if abs(h_schw) > 1.0:
            assert h_diff / abs(h_schw) <= 1e-14, f"H relative mismatch: {h_diff / abs(h_schw):.2e}"
        else:
            assert h_diff <= 1e-14, f"H absolute mismatch: {h_diff:.2e}"

        rhs_schw = hamiltonian_rhs(state, schw)
        rhs_kerr = hamiltonian_rhs(state, kerr)

        for i in range(8):
            diff = abs(rhs_kerr[i] - rhs_schw[i])
            if abs(rhs_schw[i]) > 1e-12:
                rel_err = diff / abs(rhs_schw[i])
                assert rel_err <= 1e-13, f"RHS component {i} rel_err={rel_err:.2e}"
            else:
                assert diff <= 1e-13, f"RHS component {i} abs_diff={diff:.2e}"


class TestKerrEquatorialSymmetry:
    """Stage 2B - D: Verifies preservation of equatorial plane theta = pi/2, p_theta = 0."""

    @pytest.mark.parametrize("mass", [1.0, 2.0])
    @pytest.mark.parametrize("spin_ratio", [-0.95, -0.5, 0.3, 0.8, 0.99])
    @pytest.mark.parametrize("r_over_m", [2.5, 5.0, 15.0])
    @pytest.mark.parametrize("pphi", [-3.0, 0.0, 2.5, 4.0])
    def test_equatorial_plane_preservation(
        self, mass: float, spin_ratio: float, r_over_m: float, pphi: float
    ) -> None:
        """Verifies dot{theta} = 0 and dot{p}_theta = 0 on equatorial plane for all spins."""
        spin = spin_ratio * mass
        metric = KerrMetric(mass=mass, spin=spin)
        r = r_over_m * mass
        theta = np.pi / 2.0
        ptheta = 0.0
        state = np.array([0.0, r, theta, 0.0, -1.2, 0.3, ptheta, pphi], dtype=np.float64)

        rhs = hamiltonian_rhs(state, metric)
        theta_dot = rhs[IDX_THETA]
        ptheta_dot = rhs[4 + IDX_THETA]

        assert abs(theta_dot) <= 1e-15, f"dot{{theta}} on equator failed: {theta_dot:.2e}"
        assert abs(ptheta_dot) <= 1e-14, f"dot{{p}}_theta on equator failed: {ptheta_dot:.2e}"


class TestKerrMetricHamiltonianConsistency:
    """Stage 2B - E: Verifies inverse metric identity and quadratic momentum homogeneity."""

    @pytest.mark.parametrize("spin", [-0.7, 0.6])
    @pytest.mark.parametrize("r", [4.0, 10.0])
    @pytest.mark.parametrize("theta", [np.pi / 4.0, np.pi / 2.0])
    def test_inverse_identity_and_momentum_homogeneity(
        self, spin: float, r: float, theta: float
    ) -> None:
        """Verifies g^{mu alpha} g_{alpha nu} = delta^mu_nu and H(x, lambda p) = lambda^2 H(x, p)."""
        metric = KerrMetric(mass=1.0, spin=spin)

        # 1. Metric inverse identity
        g_cov = metric.g_cov(r, theta)
        g_contra = metric.g_contra(r, theta)
        prod = g_contra @ g_cov
        identity_err = float(np.max(np.abs(prod - np.eye(4))))
        assert identity_err <= 1e-14, f"Metric inverse identity error: {identity_err:.2e}"

        # 2. Quadratic momentum homogeneity
        x = np.array([0.0, r, theta, 0.0], dtype=np.float64)
        p = np.array([-1.0, 0.25, -0.3, 2.0], dtype=np.float64)
        base_h = hamiltonian_value(x, p, metric)

        for lam in [-2.5, 0.3, 1.7, 4.0]:
            scaled_h = hamiltonian_value(x, lam * p, metric)
            expected_scaled_h = (lam ** 2) * base_h
            rel_err = abs(scaled_h - expected_scaled_h) / abs(expected_scaled_h)
            assert rel_err <= 1e-14, f"Quadratic homogeneity failed for lambda={lam}: rel_err={rel_err:.2e}"


class TestKerrConservedQuantities:
    """Stage 2B - Conserved Quantities: Verifies E = -p_0 and L_z = p_phi helpers and conservation."""

    @pytest.mark.parametrize("p0,pphi", [(-1.5, 3.2), (-0.8, -2.1), (-2.0, 0.0)])
    def test_conserved_quantities_extraction(self, p0: float, pphi: float) -> None:
        """Verifies conserved_energy and conserved_angular_momentum for both 4-vector and 8-state."""
        p = np.array([p0, 0.2, 0.3, pphi], dtype=np.float64)
        state = np.array([0.0, 5.0, np.pi / 3.0, 0.0, *p], dtype=np.float64)

        # 4-vector
        assert conserved_energy(p) == -p0
        assert conserved_angular_momentum(p) == pphi

        # 8-state
        assert conserved_energy(state) == -p0
        assert conserved_angular_momentum(state) == pphi

    def test_conserved_quantities_input_validation(self) -> None:
        """Verifies rejection of invalid shapes and non-finite values."""
        with pytest.raises(ValueError, match="Input array must have shape"):
            conserved_energy(np.zeros(5))
        with pytest.raises(ValueError, match="Input array must have shape"):
            conserved_angular_momentum(np.zeros(7))
        with pytest.raises(ValueError, match="contains non-finite values"):
            conserved_energy(np.array([np.nan, 0.0, 0.0, 1.0]))
        with pytest.raises(ValueError, match="contains non-finite values"):
            conserved_angular_momentum(np.array([0.0, 5.0, 1.0, 0.0, -1.0, 0.0, 0.0, np.inf]))


class TestKerrFiniteDifferenceDerivativeValidation:
    """Stage 2B - F: High-accuracy finite-difference validation of analytic metric derivatives."""

    @staticmethod
    def _fd_4th_order(func: Callable[[float], np.ndarray], x0: float, h: float = 1e-5) -> np.ndarray:
        """Computes the 4th-order central finite difference of a matrix-valued function:

            f'(x) = (-f(x + 2h) + 8f(x + h) - 8f(x - h) + f(x - 2h)) / (12h) + O(h^4)
        """
        f_p2 = func(x0 + 2.0 * h)
        f_p1 = func(x0 + h)
        f_m1 = func(x0 - h)
        f_m2 = func(x0 - 2.0 * h)
        return (-f_p2 + 8.0 * f_p1 - 8.0 * f_m1 + f_m2) / (12.0 * h)

    @pytest.mark.parametrize("mass", [0.8, 1.0, 2.5])
    @pytest.mark.parametrize("spin_ratio", [-0.85, -0.4, 0.3, 0.9])
    @pytest.mark.parametrize("r_over_m", [3.5, 6.0, 15.0])
    @pytest.mark.parametrize("theta", [0.25 * np.pi, 0.5 * np.pi, 0.75 * np.pi])
    def test_analytic_radial_and_polar_derivatives_vs_4th_order_fd(
        self, mass: float, spin_ratio: float, r_over_m: float, theta: float
    ) -> None:
        """Verifies analytic partial_r g^{mu nu} and partial_theta g^{mu nu} against 4th-order FD to <= 1e-8."""
        spin = spin_ratio * mass
        metric = KerrMetric(mass=mass, spin=spin)
        r = r_over_m * mass

        # 1. Radial derivatives: partial_r g^{alpha beta}
        analytic_dg_dr = metric.dg_contra_dr(r, theta)
        fd_dg_dr = self._fd_4th_order(lambda r_val: metric.g_contra(r_val, theta), r, h=1e-5)
        max_err_dr = float(np.max(np.abs(analytic_dg_dr - fd_dg_dr)))
        assert max_err_dr <= 1e-8, (
            f"Radial derivative mismatch at M={mass}, a={spin}, r={r}, theta={theta}: {max_err_dr:.2e}"
        )

        # 2. Polar derivatives: partial_theta g^{alpha beta}
        analytic_dg_dth = metric.dg_contra_dtheta(r, theta)
        fd_dg_dth = self._fd_4th_order(lambda th_val: metric.g_contra(r, th_val), theta, h=1e-5)
        max_err_dth = float(np.max(np.abs(analytic_dg_dth - fd_dg_dth)))
        assert max_err_dth <= 1e-8, (
            f"Polar derivative mismatch at M={mass}, a={spin}, r={r}, theta={theta}: {max_err_dth:.2e}"
        )

        # 3. Momentum rate equation consistency:
        # dot{p}_r = -1/2 * (partial_r g^{alpha beta}) * p_alpha * p_beta
        # dot{p}_theta = -1/2 * (partial_theta g^{alpha beta}) * p_alpha * p_beta
        p = np.array([-1.2, 0.35, -0.4, 2.8], dtype=np.float64)
        state = np.array([0.0, r, theta, 0.0, *p], dtype=np.float64)
        rhs = hamiltonian_rhs(state, metric)

        expected_pr_dot = -0.5 * np.einsum("ab,a,b->", analytic_dg_dr, p, p)
        expected_ptheta_dot = -0.5 * np.einsum("ab,a,b->", analytic_dg_dth, p, p)

        assert abs(rhs[4 + IDX_R] - expected_pr_dot) <= 1e-15
        assert abs(rhs[4 + IDX_THETA] - expected_ptheta_dot) <= 1e-15


# =============================================================================
# Test Suite: Stage 2D (Carter Constant and Separation Constant Diagnostics)
# =============================================================================

class TestCarterConstant:
    """Stage 2D: Verification suite for Carter constant and separation constant diagnostics."""

    @pytest.mark.parametrize("spin", [-0.95, -0.5, 0.0, 0.6, 0.99])
    @pytest.mark.parametrize("theta", [0.1 * np.pi, 0.25 * np.pi, 0.45 * np.pi, 0.7 * np.pi, 0.85 * np.pi])
    @pytest.mark.parametrize("mu", [0.0, 1.0])
    @pytest.mark.parametrize("energy", [0.85, 1.05, 1.5])
    @pytest.mark.parametrize("lz", [-2.5, 0.0, 3.2])
    def test_carter_polar_algebraic_equivalence(
        self, spin: float, theta: float, mu: float, energy: float, lz: float
    ) -> None:
        """Verifies algebraic equivalence between Q = K - (Lz - a*E)^2 and the explicit theta formula."""
        metric = KerrMetric(mass=1.0, spin=spin)
        ptheta = 0.75
        state = np.array([0.0, 6.0, theta, 0.0, -energy, 0.1, ptheta, lz], dtype=np.float64)

        k_val = carter_separation_constant(state, metric, mu=mu)
        q_val = carter_constant(state, metric, mu=mu)

        # Expected Q from definition Q = K - (Lz - a*E)^2
        shift = (lz - (spin * energy)) ** 2
        assert abs(q_val - (k_val - shift)) <= 1e-14

        # Expected Q from second explicit formula:
        # Q = p_theta^2 + cos^2(theta) * [a^2 * (mu^2 - E^2) + L_z^2 / sin^2(theta)]
        sin_th = np.sin(theta)
        cos_th = np.cos(theta)
        q_explicit = (ptheta ** 2) + (cos_th ** 2) * (
            (spin ** 2) * (mu ** 2 - energy ** 2) + (lz ** 2) / (sin_th ** 2)
        )
        assert abs(q_val - q_explicit) <= 1e-13

    @pytest.mark.parametrize("spin", [-0.9, -0.5, 0.0, 0.5, 0.95])
    @pytest.mark.parametrize("r_val", [4.5, 7.0, 12.0])
    @pytest.mark.parametrize("theta", [0.2 * np.pi, 0.35 * np.pi, 0.65 * np.pi])
    @pytest.mark.parametrize("mu", [0.0, 1.0])
    def test_carter_independent_radial_vs_polar_agreement(
        self, spin: float, r_val: float, theta: float, mu: float
    ) -> None:
        """Verifies that independent radial and polar separation constants agree to < 1e-12."""
        metric = KerrMetric(mass=1.0, spin=spin)
        x = np.array([0.0, r_val, theta, 0.0], dtype=np.float64)
        energy = 1.15
        lz = 2.2
        ptheta = 0.45

        # Construct physical on-shell state satisfying H(x, p) = -0.5 * mu^2
        state = kerr_geodesic_initial_state(
            metric=metric,
            x=x,
            energy=energy,
            Lz=lz,
            ptheta=ptheta,
            mu=mu,
            radial_direction="inward",
        )

        k_polar = carter_separation_constant(state, metric, mu=mu)
        k_radial = carter_separation_constant_radial(state, metric, mu=mu)
        diff_k = abs(k_polar - k_radial)
        assert diff_k <= 1e-12, f"K mismatch at a={spin}, r={r_val}, theta={theta}, mu={mu}: {diff_k:.2e}"

        q_polar = carter_constant(state, metric, mu=mu)
        q_radial = carter_constant_radial(state, metric, mu=mu)
        diff_q = abs(q_polar - q_radial)
        assert diff_q <= 1e-12, f"Q mismatch at a={spin}, r={r_val}, theta={theta}, mu={mu}: {diff_q:.2e}"

    @pytest.mark.parametrize("spin", [-0.8, -0.2, 0.0, 0.4, 0.9])
    @pytest.mark.parametrize("mu", [0.0, 1.0])
    @pytest.mark.parametrize("energy", [0.9, 1.1])
    @pytest.mark.parametrize("lz", [-3.0, 1.5, 4.0])
    def test_carter_equatorial_zero(
        self, spin: float, mu: float, energy: float, lz: float
    ) -> None:
        """Verifies Q == 0 identically for equatorial motion (theta = pi/2, p_theta = 0)."""
        metric = KerrMetric(mass=1.0, spin=spin)
        state = np.array([0.0, 6.0, 0.5 * np.pi, 0.0, -energy, -0.2, 0.0, lz], dtype=np.float64)

        q_val = carter_constant(state, metric, mu=mu)
        assert abs(q_val) <= 1e-15, f"Equatorial Q is nonzero: {q_val:.2e}"

        k_val = carter_separation_constant(state, metric, mu=mu)
        expected_k = (lz - (spin * energy)) ** 2
        assert abs(k_val - expected_k) <= 1e-14

    @pytest.mark.parametrize("theta", [0.2 * np.pi, 0.35 * np.pi, 0.6 * np.pi, 0.8 * np.pi])
    @pytest.mark.parametrize("mu", [0.0, 1.0])
    @pytest.mark.parametrize("energy", [0.95, 1.2])
    @pytest.mark.parametrize("lz", [-2.0, 2.5])
    @pytest.mark.parametrize("ptheta", [-0.6, 0.8])
    def test_carter_schwarzschild_limit(
        self, theta: float, mu: float, energy: float, lz: float, ptheta: float
    ) -> None:
        """In the Schwarzschild limit (a = 0), Q = p_theta^2 + L_z^2 * cot^2(theta) = L^2 - L_z^2."""
        metric = KerrMetric(mass=1.0, spin=0.0)
        state = np.array([0.0, 8.0, theta, 0.0, -energy, 0.1, ptheta, lz], dtype=np.float64)

        q_val = carter_constant(state, metric, mu=mu)

        # In spherical symmetry: L^2 = p_theta^2 + L_z^2 / sin^2(theta)
        # Transverse angular momentum squared: L^2 - L_z^2 = p_theta^2 + L_z^2 * cot^2(theta)
        sin_th = np.sin(theta)
        cos_th = np.cos(theta)
        cot_th = cos_th / sin_th
        l_total_sq = (ptheta ** 2) + (lz / sin_th) ** 2
        expected_q = l_total_sq - (lz ** 2)
        expected_q_cot = (ptheta ** 2) + (lz * cot_th) ** 2

        assert abs(q_val - expected_q) <= 1e-14
        assert abs(q_val - expected_q_cot) <= 1e-14

    @pytest.mark.parametrize("spin_mag", [0.25, 0.65, 0.9])
    @pytest.mark.parametrize("mu", [0.0, 1.0])
    @pytest.mark.parametrize("theta", [0.3 * np.pi, 0.7 * np.pi])
    def test_carter_spin_sign_symmetry(
        self, spin_mag: float, mu: float, theta: float
    ) -> None:
        """At fixed phase space (x, p), Q(+a) == Q(-a) because a enters only as a^2 in the polar formula."""
        m_pos = KerrMetric(mass=1.0, spin=spin_mag)
        m_neg = KerrMetric(mass=1.0, spin=-spin_mag)
        state = np.array([0.0, 7.0, theta, 0.0, -1.1, 0.2, 0.5, 2.0], dtype=np.float64)

        q_pos = carter_constant(state, m_pos, mu=mu)
        q_neg = carter_constant(state, m_neg, mu=mu)
        assert abs(q_pos - q_neg) <= 1e-14

        # Note that K contains the linear cross-term -2*a*E*Lz, so K(+a) != K(-a) in general
        k_pos = carter_separation_constant(state, m_pos, mu=mu)
        k_neg = carter_separation_constant(state, m_neg, mu=mu)
        # Difference in K is (Lz - aE)^2 - (Lz + aE)^2 = -4*a*E*Lz
        expected_diff_k = -4.0 * spin_mag * 1.1 * 2.0
        assert abs((k_pos - k_neg) - expected_diff_k) <= 1e-14

    def test_carter_vectorized_2d_input(self) -> None:
        """Verifies that 2D state arrays (N, 8) evaluate consistently with row-by-row 1D evaluation."""
        metric = KerrMetric(mass=1.0, spin=0.7)
        states = []
        for i in range(5):
            th = 0.2 * np.pi + i * 0.1 * np.pi
            r = 6.0 + i * 1.5
            s = np.array([0.0, r, th, 0.0, -1.05, 0.1 * (i + 1), 0.3 * (i - 2), 2.1], dtype=np.float64)
            states.append(s)
        states_arr = np.array(states)

        q_1d = np.array([carter_constant(s, metric, mu=1.0) for s in states])
        q_2d = carter_constant(states_arr, metric, mu=1.0)
        assert isinstance(q_2d, np.ndarray)
        assert q_2d.shape == (5,)
        assert np.allclose(q_1d, q_2d, atol=1e-15, rtol=1e-15)

        k_1d = np.array([carter_separation_constant(s, metric, mu=1.0) for s in states])
        k_2d = carter_separation_constant(states_arr, metric, mu=1.0)
        assert np.allclose(k_1d, k_2d, atol=1e-15, rtol=1e-15)

        k_rad_1d = np.array([carter_separation_constant_radial(s, metric, mu=1.0) for s in states])
        k_rad_2d = carter_separation_constant_radial(states_arr, metric, mu=1.0)
        assert np.allclose(k_rad_1d, k_rad_2d, atol=1e-15, rtol=1e-15)

        q_rad_1d = np.array([carter_constant_radial(s, metric, mu=1.0) for s in states])
        q_rad_2d = carter_constant_radial(states_arr, metric, mu=1.0)
        assert np.allclose(q_rad_1d, q_rad_2d, atol=1e-15, rtol=1e-15)

    def test_carter_input_validation_and_singularities(self) -> None:
        """Verifies fail-fast error handling for invalid metric types, shapes, mu, and singular coordinates."""
        metric = KerrMetric(mass=1.0, spin=0.7)
        valid_state = np.array([0.0, 6.0, 0.3 * np.pi, 0.0, -1.0, 0.0, 0.5, 2.0], dtype=np.float64)

        # 1. Invalid metric type
        schwarz = SchwarzschildMetric(mass=1.0)
        with pytest.raises(TypeError, match="metric must be an instance of KerrMetric"):
            carter_constant(valid_state, schwarz)  # type: ignore

        # 2. Invalid mu parameter
        with pytest.raises(ValueError, match="Rest mass parameter mu must be a non-negative finite float"):
            carter_constant(valid_state, metric, mu=-0.5)
        with pytest.raises(ValueError, match="Rest mass parameter mu must be a non-negative finite float"):
            carter_constant(valid_state, metric, mu=np.nan)
        with pytest.raises(ValueError, match="Rest mass parameter mu must be a non-negative finite float"):
            carter_constant(valid_state, metric, mu=True)  # type: ignore

        # 3. Invalid state shapes
        with pytest.raises(ValueError, match="1D state array must have shape"):
            carter_constant(np.zeros(7), metric)
        with pytest.raises(ValueError, match="2D state array must have shape"):
            carter_constant(np.zeros((3, 7)), metric)
        with pytest.raises(ValueError, match="State array must be 1D"):
            carter_constant(np.zeros((2, 2, 8)), metric)

        # 4. Non-finite values
        state_nan = valid_state.copy()
        state_nan[4] = np.nan
        with pytest.raises(ValueError, match="contains non-finite values"):
            carter_constant(state_nan, metric)

        # 5. Polar coordinate singularities (theta <= 0 or theta >= pi)
        state_theta_zero = valid_state.copy()
        state_theta_zero[IDX_THETA] = 0.0
        with pytest.raises(ValueError, match="theta must lie strictly in"):
            carter_constant(state_theta_zero, metric)

        state_theta_pi = valid_state.copy()
        state_theta_pi[IDX_THETA] = np.pi
        with pytest.raises(ValueError, match="theta must lie strictly in"):
            carter_constant(state_theta_pi, metric)

        # 6. Radial coordinate singularity in radial evaluator (r <= r_+)
        state_horizon = valid_state.copy()
        state_horizon[IDX_R] = metric.horizon_radius
        with pytest.raises(ValueError, match="Radial coordinate r must be strictly outside"):
            carter_separation_constant_radial(state_horizon, metric)

        state_inside = valid_state.copy()
        state_inside[IDX_R] = metric.horizon_radius - 0.1
        with pytest.raises(ValueError, match="Radial coordinate r must be strictly outside"):
            carter_separation_constant_radial(state_inside, metric)
