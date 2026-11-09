"""Verification test suite for Schwarzschild null-geodesic initial conditions generator.

Implements Stage 1C verification:
- VAL-IC-01: Radial null geodesics (L_z = 0, p_theta = 0 => p_r = +/- E/f).
- VAL-IC-02: Equatorial null geodesics (theta = pi/2, p_theta = 0, L_z != 0).
- VAL-IC-03: Non-equatorial null geodesics (theta != pi/2, p_theta != 0, L_z != 0).
- VAL-IC-04: Turning points (E^2 = V_eff => p_r = 0, inward/outward degeneracy).
- VAL-IC-05: Forbidden initial data (E^2 < V_eff => ValueError, no clipping/complex values).
- VAL-IC-06: Robust input validation (mass, energy, coordinates, shapes, direction, non-finite values).
- VAL-IC-07: State integrity and non-mutation of caller arrays.
- VAL-IC-08: Hamiltonian consistency (H(x, p) = 0 within float64 precision and dot{r} = f*p_r sign consistency).
"""

from typing import Tuple
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
    hamiltonian_rhs,
    hamiltonian_value,
)
from geodesics.initial_conditions import (
    DEFAULT_RADICAND_ATOL,
    kerr_geodesic_initial_state,
    schwarzschild_circular_timelike_initial_state,
    schwarzschild_null_initial_state,
    schwarzschild_perturbed_circular_timelike_initial_state,
    schwarzschild_photon_sphere_initial_state,
)
from geodesics.metrics.kerr import KerrMetric
from geodesics.metrics.schwarzschild import SchwarzschildMetric


# =============================================================================
# Test Suite: VAL-IC-01 (Radial Null Geodesics)
# =============================================================================

class TestRadialNullGeodesics:
    """VAL-IC-01: Verifies radial null trajectories (L_z = 0, p_theta = 0)."""

    @pytest.mark.parametrize("mass", [0.5, 1.0, 2.5])
    @pytest.mark.parametrize("r_over_m", [2.5, 4.0, 10.0, 50.0])
    @pytest.mark.parametrize("energy", [0.5, 1.0, 3.2])
    def test_val_ic_01_radial_inward_and_outward(
        self, mass: float, r_over_m: float, energy: float
    ):
        """Verifies p_r = +/- E / f(r) for radial rays on both inward and outward branches."""
        metric = SchwarzschildMetric(mass=mass)
        r = r_over_m * mass
        theta = np.pi / 2.0
        x = np.array([0.0, r, theta, 0.0], dtype=np.float64)

        f = 1.0 - (2.0 * mass / r)
        expected_pr_magnitude = energy / f

        # Inward branch (s = -1)
        state_in = schwarzschild_null_initial_state(
            metric=metric,
            x=x,
            energy=energy,
            Lz=0.0,
            ptheta=0.0,
            radial_direction="inward",
        )
        assert state_in[4] == -energy
        assert state_in[6] == 0.0
        assert state_in[7] == 0.0
        np.testing.assert_allclose(state_in[5], -expected_pr_magnitude, rtol=1e-14, atol=1e-14)

        # Outward branch (s = +1)
        state_out = schwarzschild_null_initial_state(
            metric=metric,
            x=x,
            energy=energy,
            Lz=0.0,
            ptheta=0.0,
            radial_direction="outward",
        )
        assert state_out[4] == -energy
        assert state_out[6] == 0.0
        assert state_out[7] == 0.0
        np.testing.assert_allclose(state_out[5], +expected_pr_magnitude, rtol=1e-14, atol=1e-14)


# =============================================================================
# Test Suite: VAL-IC-02 (Equatorial Null Geodesics)
# =============================================================================

class TestEquatorialNullGeodesics:
    """VAL-IC-02: Verifies equatorial null trajectories (theta = pi/2, p_theta = 0, L_z != 0)."""

    @pytest.mark.parametrize("mass", [0.8, 1.0, 2.0])
    @pytest.mark.parametrize("r_over_m", [4.0, 8.0, 25.0])
    @pytest.mark.parametrize("impact_param", [2.0, 3.5, 5.0])
    def test_val_ic_02_equatorial_trajectories(
        self, mass: float, r_over_m: float, impact_param: float
    ):
        """Verifies p_r against independent explicit formula for equatorial null geodesics."""
        metric = SchwarzschildMetric(mass=mass)
        r = r_over_m * mass
        theta = np.pi / 2.0
        x = np.array([0.0, r, theta, 0.0], dtype=np.float64)

        energy = 1.5
        Lz = impact_param * energy * mass  # L_z = b * E

        f = 1.0 - (2.0 * mass / r)
        radicand = (energy**2 / f**2) - (Lz**2 / (f * r**2))
        assert radicand > 0.0, "Test configuration must be in classically allowed region"
        expected_pr = np.sqrt(radicand)

        state_in = schwarzschild_null_initial_state(
            metric=metric,
            x=x,
            energy=energy,
            Lz=Lz,
            ptheta=0.0,
            radial_direction="inward",
        )
        np.testing.assert_allclose(state_in[5], -expected_pr, rtol=1e-14, atol=1e-14)

        state_out = schwarzschild_null_initial_state(
            metric=metric,
            x=x,
            energy=energy,
            Lz=Lz,
            ptheta=0.0,
            radial_direction="outward",
        )
        np.testing.assert_allclose(state_out[5], +expected_pr, rtol=1e-14, atol=1e-14)

    @pytest.mark.parametrize("r_over_m", [20.0, 100.0])
    @pytest.mark.parametrize("impact_param", [6.0, 10.0, 15.0])
    def test_val_ic_02_equatorial_distant_trajectories(
        self, r_over_m: float, impact_param: float
    ):
        """Verifies equatorial null geodesics for large impact parameters at distant radii."""
        mass = 1.0
        metric = SchwarzschildMetric(mass=mass)
        r = r_over_m * mass
        theta = np.pi / 2.0
        x = np.array([0.0, r, theta, 0.0], dtype=np.float64)

        energy = 1.0
        Lz = impact_param * energy * mass

        f = 1.0 - (2.0 * mass / r)
        radicand = (energy**2 / f**2) - (Lz**2 / (f * r**2))
        assert radicand > 0.0
        expected_pr = np.sqrt(radicand)

        state_in = schwarzschild_null_initial_state(
            metric=metric,
            x=x,
            energy=energy,
            Lz=Lz,
            ptheta=0.0,
            radial_direction="inward",
        )
        np.testing.assert_allclose(state_in[5], -expected_pr, rtol=1e-14, atol=1e-14)


# =============================================================================
# Test Suite: VAL-IC-03 (Non-Equatorial Null Geodesics)
# =============================================================================

class TestNonEquatorialNullGeodesics:
    """VAL-IC-03: Verifies 3D spherical null trajectories (theta != pi/2, p_theta != 0, L_z != 0)."""

    @pytest.mark.parametrize("theta", [0.2 * np.pi, 0.35 * np.pi, 0.65 * np.pi, 0.8 * np.pi])
    @pytest.mark.parametrize("ptheta", [-1.5, 0.8, 2.2])
    @pytest.mark.parametrize("Lz", [-3.0, 2.5, 4.0])
    def test_val_ic_03_non_equatorial(self, theta: float, ptheta: float, Lz: float):
        """Verifies p_r against independent analytical expression for arbitrary 3D angles."""
        mass = 1.0
        metric = SchwarzschildMetric(mass=mass)
        r = 12.0
        x = np.array([0.0, r, theta, 0.5], dtype=np.float64)

        energy = 2.0
        f = 1.0 - (2.0 * mass / r)
        sin_th = np.sin(theta)
        l_sq = ptheta**2 + (Lz**2 / (sin_th**2))
        radicand = (energy**2 / f**2) - (l_sq / (f * r**2))
        assert radicand > 0.0

        expected_pr_in = -np.sqrt(radicand)
        expected_pr_out = np.sqrt(radicand)

        state_in = schwarzschild_null_initial_state(
            metric=metric,
            x=x,
            energy=energy,
            Lz=Lz,
            ptheta=ptheta,
            radial_direction="inward",
        )
        np.testing.assert_allclose(state_in[5], expected_pr_in, rtol=1e-14, atol=1e-14)

        state_out = schwarzschild_null_initial_state(
            metric=metric,
            x=x,
            energy=energy,
            Lz=Lz,
            ptheta=ptheta,
            radial_direction="outward",
        )
        np.testing.assert_allclose(state_out[5], expected_pr_out, rtol=1e-14, atol=1e-14)


# =============================================================================
# Test Suite: VAL-IC-04 (Radial Turning Points)
# =============================================================================

class TestTurningPoints:
    """VAL-IC-04: Verifies turning points (p_r = 0) where inward/outward branches are degenerate."""

    @pytest.mark.parametrize("r_turn", [4.0, 6.0, 10.0, 20.0])
    @pytest.mark.parametrize("theta", [0.25 * np.pi, 0.5 * np.pi, 0.75 * np.pi])
    def test_val_ic_04_exact_turning_point(self, r_turn: float, theta: float):
        """Analytically constructs E = sqrt(V_eff) so p_r = 0, verifying inward/outward degeneracy."""
        mass = 1.0
        metric = SchwarzschildMetric(mass=mass)
        f = 1.0 - (2.0 * mass / r_turn)
        Lz = 3.5
        ptheta = 1.2
        sin_th = np.sin(theta)

        l_sq = ptheta**2 + (Lz**2 / (sin_th**2))
        v_eff = (f / (r_turn**2)) * l_sq
        energy = np.sqrt(v_eff)

        x = np.array([0.0, r_turn, theta, 0.0], dtype=np.float64)

        state_in = schwarzschild_null_initial_state(
            metric=metric,
            x=x,
            energy=energy,
            Lz=Lz,
            ptheta=ptheta,
            radial_direction="inward",
        )
        state_out = schwarzschild_null_initial_state(
            metric=metric,
            x=x,
            energy=energy,
            Lz=Lz,
            ptheta=ptheta,
            radial_direction="outward",
        )

        assert state_in[5] == 0.0
        assert state_out[5] == 0.0
        # Inward and outward states are identical at an instantaneous radial turning point
        np.testing.assert_array_equal(state_in, state_out)


# =============================================================================
# Test Suite: VAL-IC-05 (Physically Forbidden Initial Data)
# =============================================================================

class TestForbiddenInitialData:
    """VAL-IC-05: Verifies rejection of classically forbidden initial data (E^2 < V_eff)."""

    def test_val_ic_05_rejection_of_negative_radicand(self):
        """Rejects states with E^2 < V_eff, ensuring no silent clipping or complex returns."""
        metric = SchwarzschildMetric(mass=1.0)
        r = 6.0
        theta = np.pi / 2.0
        x = np.array([0.0, r, theta, 0.0], dtype=np.float64)

        # Huge angular momentum and tiny energy => heavily negative radicand
        Lz = 50.0
        energy = 0.1

        with pytest.raises(
            ValueError, match="Initial conditions are physically forbidden for a null geodesic"
        ):
            schwarzschild_null_initial_state(
                metric=metric,
                x=x,
                energy=energy,
                Lz=Lz,
                ptheta=0.0,
                radial_direction="inward",
            )

    def test_val_ic_05_zero_tolerance_strict_rejection(self):
        """With radicand_atol=0.0, even a microscopic negative value raises ValueError."""
        metric = SchwarzschildMetric(mass=1.0)
        r = 8.0
        theta = np.pi / 2.0
        f = 1.0 - (2.0 / r)
        Lz = 4.0
        v_eff = (f / (r**2)) * (Lz**2)
        # Choose energy slightly below sqrt(V_eff)
        energy = np.sqrt(v_eff) - 1e-12
        x = np.array([0.0, r, theta, 0.0], dtype=np.float64)

        with pytest.raises(ValueError, match="physically forbidden"):
            schwarzschild_null_initial_state(
                metric=metric,
                x=x,
                energy=energy,
                Lz=Lz,
                ptheta=0.0,
                radial_direction="inward",
                radicand_atol=0.0,
            )


# =============================================================================
# Test Suite: VAL-IC-06 (Input Validation)
# =============================================================================

class TestInputValidation:
    """VAL-IC-06: Verifies comprehensive input error checking."""

    @pytest.mark.parametrize("invalid_mass", [0.0, -1.0, np.nan, np.inf])
    def test_rejection_of_invalid_mass(self, invalid_mass: float):
        """Rejects non-positive or non-finite mass."""
        x = np.array([0.0, 10.0, np.pi / 2.0, 0.0])
        with pytest.raises(ValueError):
            schwarzschild_null_initial_state(
                metric=invalid_mass,
                x=x,
                energy=1.0,
                Lz=2.0,
            )

    @pytest.mark.parametrize("invalid_energy", [0.0, -0.5, -10.0, np.nan, np.inf, -np.inf])
    def test_rejection_of_invalid_energy(self, invalid_energy: float):
        """Rejects non-positive or non-finite conserved energy."""
        metric = SchwarzschildMetric(mass=1.0)
        x = np.array([0.0, 10.0, np.pi / 2.0, 0.0])
        with pytest.raises(ValueError, match="Conserved energy E must be strictly positive"):
            schwarzschild_null_initial_state(
                metric=metric,
                x=x,
                energy=invalid_energy,
                Lz=2.0,
            )

    @pytest.mark.parametrize("invalid_r", [2.0, 1.9, 0.5, 0.0, -5.0])
    def test_rejection_of_horizon_and_interior_radii(self, invalid_r: float):
        """Rejects radii on or within the Schwarzschild event horizon r <= 2M."""
        metric = SchwarzschildMetric(mass=1.0)
        x = np.array([0.0, invalid_r, np.pi / 2.0, 0.0])
        with pytest.raises(ValueError, match="Radial coordinate r"):
            schwarzschild_null_initial_state(
                metric=metric,
                x=x,
                energy=1.0,
                Lz=2.0,
            )

    @pytest.mark.parametrize("non_finite_r", [np.nan, np.inf, -np.inf])
    def test_rejection_of_non_finite_radius(self, non_finite_r: float):
        """Rejects non-finite radial coordinate."""
        metric = SchwarzschildMetric(mass=1.0)
        x = np.array([0.0, non_finite_r, np.pi / 2.0, 0.0])
        with pytest.raises(ValueError, match="contains non-finite values"):
            schwarzschild_null_initial_state(
                metric=metric,
                x=x,
                energy=1.0,
                Lz=2.0,
            )

    @pytest.mark.parametrize("invalid_theta", [0.0, np.pi, -0.1, np.pi + 0.1])
    def test_rejection_of_invalid_polar_angle(self, invalid_theta: float):
        """Rejects polar angles outside (0, pi)."""
        metric = SchwarzschildMetric(mass=1.0)
        x = np.array([0.0, 10.0, invalid_theta, 0.0])
        with pytest.raises(ValueError, match="Polar angle theta"):
            schwarzschild_null_initial_state(
                metric=metric,
                x=x,
                energy=1.0,
                Lz=2.0,
            )

    @pytest.mark.parametrize("non_finite_theta", [np.nan, np.inf, -np.inf])
    def test_rejection_of_non_finite_polar_angle(self, non_finite_theta: float):
        """Rejects non-finite polar angle."""
        metric = SchwarzschildMetric(mass=1.0)
        x = np.array([0.0, 10.0, non_finite_theta, 0.0])
        with pytest.raises(ValueError, match="contains non-finite values"):
            schwarzschild_null_initial_state(
                metric=metric,
                x=x,
                energy=1.0,
                Lz=2.0,
            )

    @pytest.mark.parametrize("invalid_shape", [np.zeros(3), np.zeros(5), np.zeros((2, 2))])
    def test_rejection_of_invalid_coordinate_shape(self, invalid_shape: np.ndarray):
        """Rejects coordinate array whose shape is not (4,)."""
        metric = SchwarzschildMetric(mass=1.0)
        with pytest.raises(ValueError, match="Coordinate array x must have shape \\(4,\\)"):
            schwarzschild_null_initial_state(
                metric=metric,
                x=invalid_shape,
                energy=1.0,
                Lz=2.0,
            )

    @pytest.mark.parametrize("invalid_direction", ["sideways", "in", "out", "INWARDS", "up"])
    def test_rejection_of_invalid_radial_direction(self, invalid_direction: str):
        """Rejects radial direction strings that are not exactly 'inward' or 'outward'."""
        metric = SchwarzschildMetric(mass=1.0)
        x = np.array([0.0, 10.0, np.pi / 2.0, 0.0])
        with pytest.raises(ValueError, match="radial_direction must be 'inward' or 'outward'"):
            schwarzschild_null_initial_state(
                metric=metric,
                x=x,
                energy=1.0,
                Lz=2.0,
                radial_direction=invalid_direction,  # type: ignore
            )

    def test_rejection_of_invalid_metric_type(self):
        """Rejects metric arguments of invalid type."""
        x = np.array([0.0, 10.0, np.pi / 2.0, 0.0])
        with pytest.raises(TypeError, match="metric must be an instance of SchwarzschildMetric"):
            schwarzschild_null_initial_state(
                metric="invalid_metric",  # type: ignore
                x=x,
                energy=1.0,
                Lz=2.0,
            )

    @pytest.mark.parametrize("coord_idx", [0, 1, 2, 3])
    @pytest.mark.parametrize("bad_val", [np.nan, np.inf, -np.inf])
    def test_rejection_of_non_finite_coordinates(self, coord_idx: int, bad_val: float):
        """Rejects coordinate array if any component is NaN or Inf."""
        metric = SchwarzschildMetric(mass=1.0)
        x = np.array([0.0, 10.0, np.pi / 2.0, 0.0])
        x[coord_idx] = bad_val
        with pytest.raises(ValueError, match="contains non-finite values"):
            schwarzschild_null_initial_state(
                metric=metric,
                x=x,
                energy=1.0,
                Lz=2.0,
            )

    @pytest.mark.parametrize("bad_lz", [np.nan, np.inf, -np.inf, True])
    def test_rejection_of_invalid_lz(self, bad_lz):
        """Rejects non-finite or boolean Lz."""
        metric = SchwarzschildMetric(mass=1.0)
        x = np.array([0.0, 10.0, np.pi / 2.0, 0.0])
        with pytest.raises(ValueError, match="Axial angular momentum Lz must be finite"):
            schwarzschild_null_initial_state(
                metric=metric,
                x=x,
                energy=1.0,
                Lz=bad_lz,
            )

    @pytest.mark.parametrize("bad_ptheta", [np.nan, np.inf, -np.inf, True])
    def test_rejection_of_invalid_ptheta(self, bad_ptheta):
        """Rejects non-finite or boolean ptheta."""
        metric = SchwarzschildMetric(mass=1.0)
        x = np.array([0.0, 10.0, np.pi / 2.0, 0.0])
        with pytest.raises(ValueError, match="Polar momentum ptheta must be finite"):
            schwarzschild_null_initial_state(
                metric=metric,
                x=x,
                energy=1.0,
                Lz=2.0,
                ptheta=bad_ptheta,
            )

    @pytest.mark.parametrize("invalid_rtol", [-1e-12, -1.0, -100.0, np.nan, np.inf, -np.inf, True])
    def test_rejection_of_invalid_radicand_rtol(self, invalid_rtol):
        """Rejects negative, non-finite, or boolean radicand_rtol."""
        metric = SchwarzschildMetric(mass=1.0)
        x = np.array([0.0, 10.0, np.pi / 2.0, 0.0])
        with pytest.raises(ValueError, match="radicand_rtol must be non-negative and finite"):
            schwarzschild_null_initial_state(
                metric=metric,
                x=x,
                energy=1.0,
                Lz=2.0,
                radicand_rtol=invalid_rtol,
            )

    @pytest.mark.parametrize("invalid_atol", [-1e-14, -1.0, -100.0, np.nan, np.inf, -np.inf, True])
    def test_rejection_of_invalid_radicand_atol(self, invalid_atol):
        """Rejects negative, non-finite, or boolean radicand_atol."""
        metric = SchwarzschildMetric(mass=1.0)
        x = np.array([0.0, 10.0, np.pi / 2.0, 0.0])
        with pytest.raises(ValueError, match="radicand_atol must be non-negative and finite"):
            schwarzschild_null_initial_state(
                metric=metric,
                x=x,
                energy=1.0,
                Lz=2.0,
                radicand_atol=invalid_atol,
            )


# =============================================================================
# Test Suite: VAL-IC-07 (State Integrity and Caller Non-Mutation)
# =============================================================================

class TestStateIntegrity:
    """VAL-IC-07: Verifies output vector structure, dtype, and caller non-mutation."""

    def test_state_shape_dtype_and_non_mutation(self):
        """Verifies state shape (8,), float64 dtype, and non-mutation of caller array."""
        metric = SchwarzschildMetric(mass=1.0)
        x_caller = np.array([5.0, 12.0, np.pi / 3.0, 1.2], dtype=np.float64)
        x_backup = x_caller.copy()

        state = schwarzschild_null_initial_state(
            metric=metric,
            x=x_caller,
            energy=1.8,
            Lz=3.0,
            ptheta=-0.5,
            radial_direction="inward",
        )

        assert state.shape == (STATE_DIMENSION,)
        assert state.dtype == np.float64
        # Caller array is completely unchanged
        np.testing.assert_array_equal(x_caller, x_backup)

        # Coordinate elements copied correctly
        np.testing.assert_array_equal(state[:4], x_backup)
        assert state[4] == -1.8
        assert state[6] == -0.5
        assert state[7] == 3.0


# =============================================================================
# Test Suite: VAL-IC-08 (Hamiltonian Constraint & Velocity Consistency)
# =============================================================================

class TestHamiltonianConsistency:
    """VAL-IC-08: Verifies H(x, p) = 0 and dot{r} = f*p_r sign consistency."""

    @pytest.mark.parametrize("r", [3.5, 6.0, 15.0, 50.0])
    @pytest.mark.parametrize("theta", [0.2 * np.pi, 0.5 * np.pi, 0.8 * np.pi])
    @pytest.mark.parametrize("ptheta", [-0.8, 0.0, 1.4])
    @pytest.mark.parametrize("direction", ["inward", "outward"])
    def test_val_ic_08_hamiltonian_and_velocity_consistency(
        self, r: float, theta: float, ptheta: float, direction: str
    ):
        """Verifies H(x, p) == 0 within machine precision and sgn(dot{r}) == sgn(p_r)."""
        mass = 1.0
        metric = SchwarzschildMetric(mass=mass)
        energy = 2.0
        Lz = 2.5
        x = np.array([0.0, r, theta, 0.0], dtype=np.float64)

        state = schwarzschild_null_initial_state(
            metric=metric,
            x=x,
            energy=energy,
            Lz=Lz,
            ptheta=ptheta,
            radial_direction=direction,  # type: ignore
        )

        # 1. Scale-aware Hamiltonian null constraint |H| / (E^2 / f) <= 1e-13
        h_val = hamiltonian_value(state[:4], state[4:], metric)
        f = metric.lapse(r)
        scale_hamiltonian = (energy ** 2) / f
        rel_h_error = abs(h_val) / scale_hamiltonian
        assert rel_h_error <= 1e-13, (
            f"Scale-aware null constraint violated: |H|/(E^2/f) = {rel_h_error:.2e} "
            f"for r={r}, theta={theta}, dir={direction}, E={energy}"
        )

        # 2. Velocity dot{r} = f * p_r sign consistency
        rhs = hamiltonian_rhs(state, metric)
        r_dot = rhs[IDX_R]
        pr = state[5]

        np.testing.assert_allclose(r_dot, f * pr, rtol=1e-14, atol=1e-14)
        if direction == "inward":
            assert r_dot <= 0.0, f"Expected inward velocity dr/dlambda <= 0, got {r_dot}"
            assert pr <= 0.0
        else:
            assert r_dot >= 0.0, f"Expected outward velocity dr/dlambda >= 0, got {r_dot}"
            assert pr >= 0.0


# =============================================================================
# Test Suite: VAL-IC-09 (Scale Invariance & Small-Energy Regression)
# =============================================================================

class TestScaleInvariance:
    """VAL-IC-09: Verifies scale-invariance under arbitrary momentum rescaling."""

    @pytest.mark.parametrize("direction", ["inward", "outward"])
    def test_val_ic_09_small_energy_radial_ray(self, direction: str):
        """Regression test: M=1, r=10, E=1e-8 must NOT be misclassified as a turning point."""
        mass = 1.0
        metric = SchwarzschildMetric(mass=mass)
        r = 10.0
        theta = np.pi / 2.0
        x = np.array([0.0, r, theta, 0.0], dtype=np.float64)

        energy = 1e-8
        f = 1.0 - (2.0 * mass / r)  # f = 0.8
        expected_pr_magnitude = energy / f  # 1.25e-8

        state = schwarzschild_null_initial_state(
            metric=metric,
            x=x,
            energy=energy,
            Lz=0.0,
            ptheta=0.0,
            radial_direction=direction,  # type: ignore
        )

        expected_sign = -1.0 if direction == "inward" else +1.0
        expected_pr = expected_sign * expected_pr_magnitude

        # Under the old absolute tolerance policy (radicand_atol = 1e-14),
        # p_r^2 = 1.5625e-16 <= 1e-14 was clamped to 0.0. Here we verify it is non-zero:
        assert state[5] != 0.0, "Small-energy radial ray must NOT be classified as turning point!"
        np.testing.assert_allclose(state[5], expected_pr, rtol=1e-14, atol=1e-22)

        # Scale-aware Hamiltonian assertion
        h_val = hamiltonian_value(state[:4], state[4:], metric)
        scale = (energy ** 2) / f
        rel_h_error = abs(h_val) / scale
        assert rel_h_error <= 1e-14, f"Scale-aware |H|/(E^2/f) failed: {rel_h_error:.2e}"

    @pytest.mark.parametrize("kappa", [1e-8, 1e-5, 1e-2, 1.0, 1e2, 1e5, 1e8])
    def test_val_ic_09_momentum_rescaling_invariance(self, kappa: float):
        """Verifies exact linear scaling of canonical momenta under (E, Lz, ptheta) -> kappa*(E, Lz, ptheta)."""
        mass = 1.0
        metric = SchwarzschildMetric(mass=mass)
        r = 8.0
        theta = np.pi / 3.0
        x = np.array([0.0, r, theta, 0.0], dtype=np.float64)

        # Baseline momenta (kappa = 1.0)
        e0 = 1.5
        lz0 = 2.0
        pth0 = -0.7

        state_base = schwarzschild_null_initial_state(
            metric=metric,
            x=x,
            energy=e0,
            Lz=lz0,
            ptheta=pth0,
            radial_direction="inward",
        )
        assert state_base[5] != 0.0  # Non-turning

        # Rescaled momenta
        state_scaled = schwarzschild_null_initial_state(
            metric=metric,
            x=x,
            energy=kappa * e0,
            Lz=kappa * lz0,
            ptheta=kappa * pth0,
            radial_direction="inward",
        )

        # Verify that all 4 conjugate momenta scale strictly by kappa
        np.testing.assert_allclose(
            state_scaled[4:], kappa * state_base[4:], rtol=1e-14, atol=1e-25
        )
        # Verify radial branch is unchanged and not converted to turning point
        assert state_scaled[5] < 0.0

        # Scale-aware Hamiltonian consistency across 16 orders of magnitude
        h_val = hamiltonian_value(state_scaled[:4], state_scaled[4:], metric)
        f = metric.lapse(r)
        scale = ((kappa * e0) ** 2) / f
        rel_h_error = abs(h_val) / scale
        assert rel_h_error <= 1e-13, f"Scale-aware null constraint failed at kappa={kappa}: {rel_h_error:.2e}"

    @pytest.mark.parametrize("kappa", [1e-6, 1e-2, 1.0, 1e3, 1e6])
    def test_val_ic_09_turning_point_rescaling_invariance(self, kappa: float):
        """Verifies turning points p_r = 0 are preserved across arbitrary positive momentum scales."""
        mass = 1.0
        metric = SchwarzschildMetric(mass=mass)
        r = 6.0
        theta = np.pi / 2.0
        f = 1.0 - (2.0 * mass / r)
        lz0 = 3.0
        pth0 = 0.0
        v_eff0 = (f / (r * r)) * (lz0 ** 2)
        e0 = np.sqrt(v_eff0)

        x = np.array([0.0, r, theta, 0.0], dtype=np.float64)

        state = schwarzschild_null_initial_state(
            metric=metric,
            x=x,
            energy=kappa * e0,
            Lz=kappa * lz0,
            ptheta=kappa * pth0,
            radial_direction="inward",
        )
        assert state[5] == 0.0, f"Turning point failed to evaluate to exactly 0.0 at scale {kappa}"


# =============================================================================
# Test Suite: Stage 2C (Kerr Geodesic Initial Conditions)
# =============================================================================

class TestKerrGeodesicInitialState:
    """Stage 2C: Verification of kerr_geodesic_initial_state across timelike and null regimes."""

    @pytest.mark.parametrize("spin_ratio", [-0.8, -0.4, 0.4, 0.8])
    @pytest.mark.parametrize("direction", ["inward", "outward"])
    def test_kerr_ic_timelike_equatorial(self, spin_ratio: float, direction: str):
        """Verifies H = -0.5 for equatorial timelike Kerr geodesics with positive and negative spin."""
        mass = 1.0
        spin = spin_ratio * mass
        metric = KerrMetric(mass=mass, spin=spin)
        r = 6.0 * mass
        theta = np.pi / 2.0
        x = np.array([0.0, r, theta, 0.0], dtype=np.float64)

        state = kerr_geodesic_initial_state(
            metric=metric,
            x=x,
            energy=0.96,
            Lz=3.0,
            ptheta=0.0,
            mu=1.0,
            radial_direction=direction,
        )

        h_val = hamiltonian_value(state[:4], state[4:], metric)
        assert abs(h_val - (-0.5)) <= 1e-14
        assert state[6] == 0.0  # ptheta == 0
        if direction == "inward":
            assert state[5] <= 0.0
        else:
            assert state[5] >= 0.0

    @pytest.mark.parametrize("spin_ratio", [-0.6, 0.7])
    @pytest.mark.parametrize("theta", [np.pi / 3.0, 2.2])
    def test_kerr_ic_timelike_nonequatorial(self, spin_ratio: float, theta: float):
        """Verifies H = -0.5 for non-equatorial timelike Kerr geodesics."""
        mass = 1.0
        spin = spin_ratio * mass
        metric = KerrMetric(mass=mass, spin=spin)
        r = 7.0 * mass
        x = np.array([0.0, r, theta, 0.0], dtype=np.float64)

        state = kerr_geodesic_initial_state(
            metric=metric,
            x=x,
            energy=1.02,
            Lz=2.2,
            ptheta=0.25,
            mu=1.0,
            radial_direction="outward",
        )

        h_val = hamiltonian_value(state[:4], state[4:], metric)
        assert abs(h_val - (-0.5)) <= 1e-14
        assert state[5] > 0.0

    @pytest.mark.parametrize("spin_ratio", [-0.7, 0.9])
    @pytest.mark.parametrize("theta", [np.pi / 4.0, 2.0])
    def test_kerr_ic_null_nonequatorial(self, spin_ratio: float, theta: float):
        """Verifies H = 0.0 for non-equatorial null Kerr geodesics."""
        mass = 1.0
        spin = spin_ratio * mass
        metric = KerrMetric(mass=mass, spin=spin)
        r = 8.0 * mass
        x = np.array([0.0, r, theta, 0.0], dtype=np.float64)

        state = kerr_geodesic_initial_state(
            metric=metric,
            x=x,
            energy=1.0,
            Lz=3.0,
            ptheta=0.4,
            mu=0.0,
            radial_direction="outward",
        )

        h_val = hamiltonian_value(state[:4], state[4:], metric)
        assert abs(h_val) <= 1e-14

    def test_kerr_ic_schwarzschild_reduction(self):
        """Verifies that kerr_geodesic_initial_state with a=0, mu=0 matches schwarzschild_null_initial_state."""
        mass = 1.0
        kerr_zero = KerrMetric(mass=mass, spin=0.0)
        schw = SchwarzschildMetric(mass=mass)
        x = np.array([0.0, 8.0, np.pi / 3.0, 0.0], dtype=np.float64)

        state_kerr = kerr_geodesic_initial_state(
            metric=kerr_zero,
            x=x,
            energy=1.5,
            Lz=2.5,
            ptheta=0.3,
            mu=0.0,
            radial_direction="inward",
        )

        state_schw = schwarzschild_null_initial_state(
            metric=schw,
            x=x,
            energy=1.5,
            Lz=2.5,
            ptheta=0.3,
            radial_direction="inward",
        )

        np.testing.assert_allclose(state_kerr, state_schw, rtol=1e-15, atol=1e-15)

    def test_kerr_ic_forbidden_barrier_rejection(self):
        """Verifies rejection of classically forbidden initial conditions (insufficient energy)."""
        metric = KerrMetric(mass=1.0, spin=0.5)
        x = np.array([0.0, 6.0, np.pi / 2.0, 0.0], dtype=np.float64)
        with pytest.raises(ValueError, match="physically forbidden"):
            kerr_geodesic_initial_state(
                metric=metric,
                x=x,
                energy=0.1,  # Insufficient energy
                Lz=5.0,
                ptheta=0.0,
                mu=1.0,
            )

    def test_kerr_ic_validation_errors(self):
        """Verifies validation checks for coordinates, types, and parameter bounds."""
        metric = KerrMetric(mass=1.0, spin=0.5)
        r_plus = metric.horizon_radius
        x_inside = np.array([0.0, r_plus - 0.1, np.pi / 2.0, 0.0])
        with pytest.raises(ValueError, match="strictly outside the event horizon"):
            kerr_geodesic_initial_state(metric, x_inside, energy=1.0, Lz=2.0)

        x_axis = np.array([0.0, 5.0, 0.0, 0.0])
        with pytest.raises(ValueError, match="strictly in the domain"):
            kerr_geodesic_initial_state(metric, x_axis, energy=1.0, Lz=2.0)

        x_valid = np.array([0.0, 5.0, np.pi / 2.0, 0.0])
        with pytest.raises(ValueError, match="energy E must be strictly positive"):
            kerr_geodesic_initial_state(metric, x_valid, energy=-1.0, Lz=2.0)

        with pytest.raises(ValueError, match="mu must be non-negative"):
            kerr_geodesic_initial_state(metric, x_valid, energy=1.0, Lz=2.0, mu=-0.5)


# =============================================================================
# Test Suite: Stage 2D-Audit (Positive vs Negative Spin Radial Momentum and Benchmarks)
# =============================================================================

class TestStage2DAuditSpinSymmetryAndBenchmarks:
    """Stage 2D-Audit: Verification of spin-sign radial momentum asymmetry and exact benchmarks."""

    @pytest.mark.parametrize("spin_mag", [0.3, 0.5, 0.85, 0.95])
    @pytest.mark.parametrize("r_val", [5.0, 7.0, 10.0])
    @pytest.mark.parametrize("mu", [0.0, 1.0])
    def test_audit_spin_sign_radial_potential_and_pr_asymmetry(
        self, spin_mag: float, r_val: float, mu: float
    ) -> None:
        """Verifies exact R(-a) - R(+a) = 8*M*a*r*E*Lz identity and pr(+a) != pr(-a) asymmetry."""
        mass = 1.0
        energy = 1.15
        lz = 2.5
        ptheta = 0.3
        theta = np.pi / 3.0
        x = np.array([0.0, r_val, theta, 0.0], dtype=np.float64)

        m_pos = KerrMetric(mass=mass, spin=spin_mag)
        m_neg = KerrMetric(mass=mass, spin=-spin_mag)

        state_pos = kerr_geodesic_initial_state(
            m_pos, x, energy=energy, Lz=lz, ptheta=ptheta, mu=mu, radial_direction="outward"
        )
        state_neg = kerr_geodesic_initial_state(
            m_neg, x, energy=energy, Lz=lz, ptheta=ptheta, mu=mu, radial_direction="outward"
        )

        # 1. Mass shell condition H = -0.5 * mu^2 for both signs
        h_pos = hamiltonian_value(state_pos[:4], state_pos[4:], m_pos)
        h_neg = hamiltonian_value(state_neg[:4], state_neg[4:], m_neg)
        assert abs(h_pos - (-0.5 * mu ** 2)) <= 1e-14
        assert abs(h_neg - (-0.5 * mu ** 2)) <= 1e-14

        # 2. Carter constant equality at identical phase space Q(+a) == Q(-a)
        q_pos = carter_constant(state_pos, m_pos, mu=mu)
        q_neg = carter_constant(state_neg, m_neg, mu=mu)
        assert abs(q_pos - q_neg) <= 1e-14

        # 3. Separated radial potential R(r)
        delta_pos = m_pos.delta(r_val)
        delta_neg = m_neg.delta(r_val)
        assert abs(delta_pos - delta_neg) <= 1e-15

        r_pos = (energy * (r_val ** 2 + spin_mag ** 2) - spin_mag * lz) ** 2 - delta_pos * (
            mu ** 2 * r_val ** 2 + (lz - spin_mag * energy) ** 2 + q_pos
        )
        r_neg = (energy * (r_val ** 2 + spin_mag ** 2) + spin_mag * lz) ** 2 - delta_neg * (
            mu ** 2 * r_val ** 2 + (lz + spin_mag * energy) ** 2 + q_neg
        )

        expected_diff_r = 8.0 * mass * spin_mag * r_val * energy * lz
        assert abs((r_neg - r_pos) - expected_diff_r) <= 1e-10

        # 4. Canonical radial momentum pr = sqrt(R)/Delta
        expected_pr_pos = np.sqrt(r_pos) / delta_pos
        expected_pr_neg = np.sqrt(r_neg) / delta_neg
        assert abs(state_pos[5] - expected_pr_pos) <= 1e-14
        assert abs(state_neg[5] - expected_pr_neg) <= 1e-14

        # 5. Non-identity of radial momenta: pr(-a) > pr(+a) for positive energy and angular momentum
        assert state_neg[5] > state_pos[5]
        diff_pr = state_neg[5] - state_pos[5]
        assert diff_pr > 0.0

    def test_audit_all_eight_benchmark_initial_states(self) -> None:
        """Verifies exact properties, mass-shell residuals, and Carter agreement for all 8 benchmarks."""
        benchmarks = [
            ("BM-EQ", 1.0, 0.70, 1.0, 7.0, 0.5 * np.pi, 0.95, 2.8, 0.0, 0.3202973027),
            ("BM-T1", 1.0, 0.50, 1.0, 6.0, np.pi / 3.0, 0.98, 2.5, 0.2, 0.5088271267),
            ("BM-T2", 1.0, -0.50, 1.0, 6.0, np.pi / 3.0, 0.98, 2.5, 0.2, 0.5990779721),
            ("BM-T3", 1.0, 0.95, 1.0, 6.0, np.pi / 3.0, 0.98, 2.5, 0.2, 0.4593223345),
            ("BM-T4", 1.0, -0.95, 1.0, 6.0, np.pi / 3.0, 0.98, 2.5, 0.2, 0.6254050461),
            ("BM-N1", 1.0, 0.85, 0.0, 8.0, 0.25 * np.pi, 1.00, 3.0, 0.4, 1.1631201919),
            ("BM-N2", 1.0, -0.85, 0.0, 8.0, 0.25 * np.pi, 1.00, 3.0, 0.4, 1.1923073146),
            ("BM-N3", 1.0, 0.50, 0.0, 8.0, 0.25 * np.pi, 1.00, 3.0, 0.4, 1.1724162460),
        ]

        states = {}
        for name, M, a, mu, r, th, E, Lz, pth, expected_pr in benchmarks:
            m = KerrMetric(mass=M, spin=a)
            x0 = np.array([0.0, r, th, 0.0], dtype=np.float64)
            y = kerr_geodesic_initial_state(m, x0, energy=E, Lz=Lz, ptheta=pth, mu=mu, radial_direction="outward")
            states[name] = y

            # Check pr matches analytical value
            assert abs(y[5] - expected_pr) <= 1e-8, f"{name}: pr {y[5]} != expected {expected_pr}"

            # Check mass shell residual |H + 0.5*mu^2| <= 1e-14
            h = hamiltonian_value(y[:4], y[4:], m)
            assert abs(h - (-0.5 * mu ** 2)) <= 1e-14

            # Check polar and radial Carter constants agree
            q_pol = carter_constant(y, m, mu=mu)
            q_rad = carter_constant_radial(y, m, mu=mu)
            assert abs(q_pol - q_rad) <= 1e-13

            # Check polar and radial separation constants agree
            k_pol = carter_separation_constant(y, m, mu=mu)
            k_rad = carter_separation_constant_radial(y, m, mu=mu)
            assert abs(k_pol - k_rad) <= 1e-13

        # Explicitly verify that pr differs between positive and negative spins
        assert abs(states["BM-T1"][5] - states["BM-T2"][5]) > 0.08
        assert abs(states["BM-T3"][5] - states["BM-T4"][5]) > 0.15
        assert abs(states["BM-N1"][5] - states["BM-N2"][5]) > 0.02

    def test_null_convergence_benchmark_initial_state(self) -> None:
        """Verifies exact analytical and numerical properties of the null convergence benchmark state (a = -0.7)."""
        m = KerrMetric(mass=1.0, spin=-0.7)
        x0 = np.array([0.0, 8.0, 0.25 * np.pi, 0.0], dtype=np.float64)
        y0 = kerr_geodesic_initial_state(
            metric=m,
            x=x0,
            energy=1.0,
            Lz=3.0,
            ptheta=0.4,
            mu=0.0,
            radial_direction="outward",
        )

        # 1. State components
        t, r, theta, phi, pt, pr, ptheta, pphi = y0
        assert t == 0.0 and r == 8.0 and theta == 0.25 * np.pi and phi == 0.0
        assert pt == -1.0
        assert ptheta == 0.4
        assert pphi == 3.0
        # Expected pr analytical value
        # Delta = 8^2 - 2(1)(8) + (-0.7)^2 = 64 - 16 + 0.49 = 48.49
        # Sigma = 8^2 + (-0.7)^2 * cos^2(pi/4) = 64 + 0.49 * 0.5 = 64.245
        # R(r) = [(r^2 + a^2)*E - a*Lz]^2 - Delta * [mu^2*r^2 + (Lz - a*E)^2 + Q]
        # (r^2 + a^2)*E - a*Lz = (64 + 0.49)*1.0 - (-0.7)*3.0 = 64.49 + 2.1 = 66.59
        # (66.59)^2 = 4434.2281
        # Lz - a*E = 3.0 - (-0.7)*1.0 = 3.7 => (3.7)^2 = 13.69
        # Q = 8.915 => (Lz - a*E)^2 + Q = 13.69 + 8.915 = 22.605 (= K)
        # Delta * K = 48.49 * 22.605 = 1096.11645
        # R(r) = 4434.2281 - 1096.11645 = 3338.11165
        # pr = sqrt(R(r)) / Delta = sqrt(3338.11165) / 48.49 = 57.77639353577033 / 48.49 = 1.1915115185763778
        expected_pr = np.sqrt(3338.11165) / 48.49
        assert abs(pr - expected_pr) <= 1e-14
        assert abs(pr - 1.1915115185763778) <= 1e-14

        # 2. Conserved quantities
        assert -pt == 1.0  # E = -pt
        assert pphi == 3.0  # Lz = pphi
        h0 = hamiltonian_value(y0[:4], y0[4:], m)
        assert abs(h0) <= 1e-15  # Null mass-shell constraint

        # 3. Carter constant Q and Carter separation constant K
        # Polar definitions
        q_pol = carter_constant(y0, m, mu=0.0)
        k_pol = carter_separation_constant(y0, m, mu=0.0)
        # Radial definitions
        q_rad = carter_constant_radial(y0, m, mu=0.0)
        k_rad = carter_separation_constant_radial(y0, m, mu=0.0)

        # Exact analytic values:
        # Q = ptheta^2 + cos^2(theta) * [a^2*(mu^2 - E^2) + Lz^2/sin^2(theta)]
        #   = 0.4^2 + 0.5 * [0.49*(0 - 1) + 9 / 0.5] = 0.16 + 0.5 * 17.51 = 8.915
        # K = Q + (Lz - a*E)^2 = 8.915 + 3.7^2 = 8.915 + 13.69 = 22.605
        assert np.isclose(q_pol, 8.915, atol=1e-14, rtol=1e-14)
        assert np.isclose(q_rad, 8.915, atol=1e-14, rtol=1e-14)
        assert np.isclose(k_pol, 22.605, atol=1e-14, rtol=1e-14)
        assert np.isclose(k_rad, 22.605, atol=1e-14, rtol=1e-14)


class TestSchwarzschildCircularOrbitInitialConditions:
    """Tests validation, type checking, and boundary errors for Schwarzschild circular orbit helpers."""

    def test_circular_timelike_type_and_domain_errors(self):
        """Verifies type checks and domain restrictions for circular timelike initial conditions."""
        m = SchwarzschildMetric(mass=1.0)

        # Invalid metric type
        with pytest.raises(TypeError, match="metric must be an instance of SchwarzschildMetric"):
            schwarzschild_circular_timelike_initial_state("invalid", 8.0)  # type: ignore

        # Float mass accepted
        y = schwarzschild_circular_timelike_initial_state(1.0, 8.0)
        assert y.shape == (8,)

        # Boundary r = 3M rejected
        with pytest.raises(ValueError, match="require r > 3M"):
            schwarzschild_circular_timelike_initial_state(m, 3.0)

        # Sub-photon-sphere r < 3M rejected
        with pytest.raises(ValueError, match="require r > 3M"):
            schwarzschild_circular_timelike_initial_state(m, 2.5)

        # Non-finite coordinates rejected
        with pytest.raises(ValueError, match="must be finite"):
            schwarzschild_circular_timelike_initial_state(m, np.nan)
        with pytest.raises(ValueError, match="must be finite"):
            schwarzschild_circular_timelike_initial_state(m, 8.0, phi=np.inf)

    def test_photon_sphere_type_and_energy_errors(self):
        """Verifies type checks and energy restrictions for photon sphere initial conditions."""
        m = SchwarzschildMetric(mass=1.0)

        # Invalid metric type
        with pytest.raises(TypeError, match="metric must be an instance of SchwarzschildMetric"):
            schwarzschild_photon_sphere_initial_state("invalid")  # type: ignore

        # Float mass accepted
        y = schwarzschild_photon_sphere_initial_state(1.0, energy=2.0)
        assert y.shape == (8,)
        assert y[4] == -2.0

        # Non-positive or non-finite energy rejected
        with pytest.raises(ValueError, match="strictly positive and finite"):
            schwarzschild_photon_sphere_initial_state(m, energy=0.0)
        with pytest.raises(ValueError, match="strictly positive and finite"):
            schwarzschild_photon_sphere_initial_state(m, energy=-1.0)
        with pytest.raises(ValueError, match="strictly positive and finite"):
            schwarzschild_photon_sphere_initial_state(m, energy=np.nan)

    def test_perturbed_circular_timelike_validation(self):
        """Verifies validation for perturbed circular timelike initial states."""
        m = SchwarzschildMetric(mass=1.0)

        # Invalid metric type
        with pytest.raises(TypeError, match="metric must be an instance of SchwarzschildMetric"):
            schwarzschild_perturbed_circular_timelike_initial_state("invalid", 8.0, 1e-4)  # type: ignore

        # Non-finite perturbation rejected
        with pytest.raises(ValueError, match="must be finite"):
            schwarzschild_perturbed_circular_timelike_initial_state(m, 8.0, delta_pr=np.nan)

        # Sub-photon-sphere radius rejected
        with pytest.raises(ValueError, match="require r > 3M"):
            schwarzschild_perturbed_circular_timelike_initial_state(m, 3.0, delta_pr=1e-4)
