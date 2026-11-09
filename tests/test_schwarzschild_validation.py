"""Scientific validation test suite for Schwarzschild null geodesics (Stage 1F).

Implements rigorous scientific verification against exact analytic results and
known physical properties for null geodesics in Schwarzschild spacetime:
- VAL-SCH-01: Inward and outward radial null geodesics:
    - Linear affine parameter radial motion: r(lambda) = r0 +/- E * (lambda - lambda0).
    - Analytic radial momentum: p_r(lambda) = +/- E / f(r(lambda)).
    - Exact coordinate time integral t(lambda) for both radial directions.
- VAL-SCH-02: Conservation of Killing conjugate momenta along trajectories:
    - Conserved energy E = -p_0.
    - Conserved axial angular momentum L_z = p_phi.
    - Equatorial and non-equatorial (3D polar momentum) trajectories.
- VAL-SCH-03: Null Hamiltonian constraint preservation:
    - Absolute residual |H(lambda)| = |1/2 g^{mu nu} p_mu p_nu|.
    - Normalized scale-invariant residual |H| / (E^2 / f(r)).
- VAL-SCH-04: Schwarzschild photon sphere circular null orbit at r = 3M:
    - Critical impact parameter b_crit = L_z / E = 3*sqrt(3)*M.
    - Initial Hamiltonian constraint H(y0) = 0.
    - Vanishing phase-space radial flow: dr/dlambda = 0, dp_r/dlambda = 0.
    - Orbit preservation over finite affine parameter intervals.
    - Physical characterization of orbital instability (V_eff''(3M) < 0).
- VAL-SCH-05: Numerical convergence under tightening integration tolerances:
    - Error metric epsilon_r = max_i |r_num(lambda_i) - r_analytic(lambda_i)|.
    - Comparison across loose (1e-6), intermediate (1e-9), and tight (1e-12) tolerances.
"""

from typing import Final, Tuple
import numpy as np
import pytest

from geodesics.constants import (
    DEFAULT_MASS,
    IDX_PHI,
    IDX_R,
    IDX_THETA,
    IDX_X0,
)
from geodesics.hamiltonian import (
    STATE_DIMENSION,
    hamiltonian_rhs,
    hamiltonian_value,
)
from geodesics.initial_conditions import (
    null_geodesic_initial_state,
    schwarzschild_null_initial_state,
)
from geodesics.integrator import (
    GeodesicIntegrationResult,
    integrate_geodesic,
)
from geodesics.metrics.schwarzschild import SchwarzschildMetric


# =============================================================================
# Test Suite: VAL-SCH-01 (Analytic Radial Null Geodesics)
# =============================================================================

class TestSchwarzschildRadialNullGeodesics:
    """VAL-SCH-01: Verification against exact analytic radial null geodesic motion.

    In exterior Schwarzschild spacetime (f(r) = 1 - 2M/r > 0), radial null motion
    (L_z = 0, p_theta = 0) satisfies:
        p_r(lambda) = +/- E / f(r(lambda))
        dr / dlambda = +/- E
        dt / dlambda = E / f(r(lambda))

    Yielding the exact linear trajectory:
        r(lambda) = r0 +/- E * (lambda - lambda0)
    """

    @pytest.mark.parametrize("direction, sign", [("outward", 1.0), ("inward", -1.0)])
    @pytest.mark.parametrize("energy", [0.5, 1.0, 2.0])
    @pytest.mark.parametrize("mass", [0.5, 1.0, 2.5])
    def test_val_sch_01_radial_linear_position_and_momentum(
        self, direction: str, sign: float, energy: float, mass: float
    ) -> None:
        """Verifies that numerical r(lambda) and pr(lambda) match exact analytic formulas."""
        metric = SchwarzschildMetric(mass=mass)
        # Choose r0 and span scaled by mass/energy so trajectory stays strictly
        # in the regular exterior region r >= 4M > 2M for any (mass, energy) combination.
        r0 = 4.0 * mass if direction == "outward" else 8.0 * mass
        x0 = np.array([0.0, r0, np.pi / 2.0, 0.0], dtype=np.float64)

        y0 = null_geodesic_initial_state(
            metric=metric,
            x=x0,
            energy=energy,
            Lz=0.0,
            ptheta=0.0,
            radial_direction=direction,  # type: ignore
        )

        lambda_end = 3.0 * mass / energy
        n_samples = 31
        t_eval = np.linspace(0.0, lambda_end, n_samples)

        res = integrate_geodesic(
            initial_state=y0,
            metric=metric,
            affine_span=(0.0, lambda_end),
            t_eval=t_eval,
            rtol=1e-11,
            atol=1e-12,
            method="DOP853",
        )

        assert res.success is True
        assert res.status == 0

        # 1. Exact radial position: r(lambda) = r0 + sign * E * lambda
        r_analytic = r0 + sign * energy * t_eval
        np.testing.assert_allclose(res.r, r_analytic, rtol=1e-10, atol=1e-10)

        # 2. Exact radial canonical momentum: p_r(lambda) = sign * E / f(r(lambda))
        f_vals = np.array([metric.lapse(r_val) for r_val in res.r])
        pr_analytic = sign * (energy / f_vals)
        np.testing.assert_allclose(res.pr, pr_analytic, rtol=1e-9, atol=1e-9)

        # 3. Exact energy: p_0(lambda) = -E
        np.testing.assert_allclose(res.p0, -energy, rtol=1e-11, atol=1e-11)

        # 4. Zero angular momenta
        np.testing.assert_allclose(res.pphi, 0.0, atol=1e-14)
        np.testing.assert_allclose(res.ptheta, 0.0, atol=1e-14)

        # 5. Null Hamiltonian constraint preservation throughout trajectory
        for i in range(len(res.lambdas)):
            h_val = hamiltonian_value(res.states[i, :4], res.states[i, 4:], metric)
            norm_scale = (energy ** 2) / f_vals[i]
            assert abs(h_val) <= 1e-10
            assert abs(h_val) / norm_scale <= 1e-9

    @pytest.mark.parametrize("direction, sign", [("outward", 1.0), ("inward", -1.0)])
    def test_val_sch_01_coordinate_time_exact_integral(
        self, direction: str, sign: float
    ) -> None:
        """Verifies numerical coordinate time t(lambda) against direction-derived exact integrals.

        Derivation:
            dt / dr = +/- 1 / f(r) = +/- (1 + 2M / (r - 2M))
            Outward (+): t(r) - t0 = +( (r - r0) + 2M * ln((r - 2M) / (r0 - 2M)) )
            Inward  (-): t(r) - t0 = -( (r - r0) + 2M * ln((r - 2M) / (r0 - 2M)) )
                                  = (r0 - r) + 2M * ln((r0 - 2M) / (r - 2M))
        Both are strictly positive for lambda > lambda0 (future-directed).
        """
        mass = 1.0
        metric = SchwarzschildMetric(mass=mass)
        energy = 1.0
        r0 = 4.0 if direction == "outward" else 8.0
        x0 = np.array([0.0, r0, np.pi / 2.0, 0.0], dtype=np.float64)

        y0 = null_geodesic_initial_state(
            metric=metric,
            x=x0,
            energy=energy,
            Lz=0.0,
            ptheta=0.0,
            radial_direction=direction,  # type: ignore
        )

        lambda_end = 3.0
        t_eval = np.linspace(0.0, lambda_end, 31)

        res = integrate_geodesic(
            initial_state=y0,
            metric=metric,
            affine_span=(0.0, lambda_end),
            t_eval=t_eval,
            rtol=1e-11,
            atol=1e-12,
        )

        assert res.success is True

        r_num = res.r
        r_H = metric.horizon_radius  # 2M

        if direction == "outward":
            delta_t_analytic = (r_num - r0) + r_H * np.log((r_num - r_H) / (r0 - r_H))
        else:
            delta_t_analytic = (r0 - r_num) + r_H * np.log((r0 - r_H) / (r_num - r_H))

        delta_t_num = res.x0 - res.x0[0]

        # Verify future-directed propagation: dt > 0 along increasing lambda
        assert np.all(delta_t_num[1:] > 0.0)
        assert np.all(delta_t_analytic[1:] > 0.0)

        # Quantitative agreement against exact coordinate time integral
        np.testing.assert_allclose(delta_t_num, delta_t_analytic, rtol=1e-9, atol=1e-9)


# =============================================================================
# Test Suite: VAL-SCH-02 (Conserved Killing Quantities)
# =============================================================================

class TestSchwarzschildConservedQuantities:
    """VAL-SCH-02: Quantification of energy and axial angular momentum conservation.

    Stationarity (partial_t g = 0) => p_0 = -E is conserved.
    Axisymmetry (partial_phi g = 0) => p_phi = L_z is conserved.
    Tests across equatorial and fully 3D non-equatorial null geodesics.
    """

    def test_val_sch_02_equatorial_trajectory_conservation(self) -> None:
        """Verifies E and Lz conservation along equatorial orbiting/scattering null ray."""
        mass = 1.0
        metric = SchwarzschildMetric(mass=mass)
        energy = 1.0
        Lz = 7.0  # Scattering orbit: b = 7.0 > 3*sqrt(3) ~ 5.196
        r0 = 10.0
        x0 = np.array([0.0, r0, np.pi / 2.0, 0.0], dtype=np.float64)

        y0 = null_geodesic_initial_state(
            metric=metric,
            x=x0,
            energy=energy,
            Lz=Lz,
            ptheta=0.0,
            radial_direction="inward",
        )

        res = integrate_geodesic(
            initial_state=y0,
            metric=metric,
            affine_span=(0.0, 20.0),
            rtol=1e-10,
            atol=1e-10,
        )

        assert res.success is True
        assert len(res.lambdas) >= 20

        # Maximum absolute and relative energy drift
        e_vals = -res.p0
        delta_E_abs = float(np.max(np.abs(e_vals - energy)))
        delta_E_rel = delta_E_abs / energy

        # Maximum absolute and relative angular momentum drift
        lz_vals = res.pphi
        delta_Lz_abs = float(np.max(np.abs(lz_vals - Lz)))
        delta_Lz_rel = delta_Lz_abs / abs(Lz)

        # Planar preservation: theta == pi/2, p_theta == 0
        max_theta_drift = float(np.max(np.abs(res.theta - np.pi / 2.0)))
        max_ptheta_drift = float(np.max(np.abs(res.ptheta)))

        assert delta_E_rel <= 1e-9, f"Energy drift {delta_E_rel:.2e} exceeded tolerance"
        assert delta_Lz_rel <= 1e-9, f"Lz drift {delta_Lz_rel:.2e} exceeded tolerance"
        assert max_theta_drift <= 1e-10
        assert max_ptheta_drift <= 1e-10

    def test_val_sch_02_non_equatorial_3d_trajectory_conservation(self) -> None:
        """Verifies E and Lz conservation on inclined 3D trajectory (theta0 != pi/2, ptheta != 0)."""
        mass = 1.0
        metric = SchwarzschildMetric(mass=mass)
        energy = 1.0
        Lz = 5.0
        ptheta_0 = 3.0
        theta_0 = np.pi / 3.0  # 60 degrees inclination; total L^2 = 5^2/(3/4) + 3^2 = 42.33 > 27
        r0 = 10.0
        x0 = np.array([0.0, r0, theta_0, 0.5], dtype=np.float64)

        y0 = null_geodesic_initial_state(
            metric=metric,
            x=x0,
            energy=energy,
            Lz=Lz,
            ptheta=ptheta_0,
            radial_direction="inward",
        )

        res = integrate_geodesic(
            initial_state=y0,
            metric=metric,
            affine_span=(0.0, 20.0),
            rtol=1e-10,
            atol=1e-10,
        )

        assert res.success is True

        # Verify that motion is genuinely 3D (theta and ptheta actively vary along trajectory)
        theta_range = float(np.ptp(res.theta))
        ptheta_range = float(np.ptp(res.ptheta))
        assert theta_range > 0.1, "Trajectory failed to explore polar angle domain"
        assert ptheta_range > 0.1, "Trajectory failed to exhibit dynamic polar momentum"

        # Energy conservation
        delta_E_abs = float(np.max(np.abs(-res.p0 - energy)))
        delta_E_rel = delta_E_abs / energy
        assert delta_E_rel <= 1e-9

        # Axial angular momentum conservation
        delta_Lz_abs = float(np.max(np.abs(res.pphi - Lz)))
        delta_Lz_rel = delta_Lz_abs / abs(Lz)
        assert delta_Lz_rel <= 1e-9


# =============================================================================
# Test Suite: VAL-SCH-03 (Null Hamiltonian Constraint Preservation)
# =============================================================================

class TestSchwarzschildHamiltonianConstraint:
    """VAL-SCH-03: Verification of the null Hamiltonian constraint H(x, p) = 0.

    Evaluates both absolute residual |H| and normalized residual |H| / (E^2 / f(r)).
    Confirms scale-invariance and non-vanishing normalization denominator.
    """

    @pytest.mark.parametrize("energy", [0.1, 1.0, 10.0])
    @pytest.mark.parametrize("direction", ["inward", "outward"])
    def test_val_sch_03_absolute_and_normalized_hamiltonian_residuals(
        self, energy: float, direction: str
    ) -> None:
        """Verifies absolute and normalized Hamiltonian residuals across energy scales."""
        mass = 1.0
        metric = SchwarzschildMetric(mass=mass)
        r0 = 10.0
        Lz = 7.0 * energy  # Scattering orbit: b = 7.0 > 3*sqrt(3) ~ 5.196
        x0 = np.array([0.0, r0, np.pi / 2.0, 0.0], dtype=np.float64)

        y0 = null_geodesic_initial_state(
            metric=metric,
            x=x0,
            energy=energy,
            Lz=Lz,
            ptheta=0.0,
            radial_direction=direction,  # type: ignore
        )

        # Scale affine span inversely with energy (dlambda ~ dt/E) for consistent spatial extent
        affine_span = (0.0, 4.0 / energy)
        res = integrate_geodesic(
            initial_state=y0,
            metric=metric,
            affine_span=affine_span,
            rtol=1e-10,
            atol=1e-10,
        )

        assert res.success is True

        n_pts = len(res.lambdas)
        h_abs = np.empty(n_pts, dtype=np.float64)
        h_norm = np.empty(n_pts, dtype=np.float64)

        for i in range(n_pts):
            coords = res.states[i, :4]
            momenta = res.states[i, 4:]
            val = hamiltonian_value(coords, momenta, metric)
            h_abs[i] = abs(val)

            # Normalization scale: E^2 / f(r).
            # Because r > 2M and E > 0, scale >= E^2 > 0 is strictly non-vanishing.
            f_r = metric.lapse(coords[IDX_R])
            scale = (energy ** 2) / f_r
            h_norm[i] = abs(val) / scale

        max_abs = float(np.max(h_abs))
        max_norm = float(np.max(h_norm))

        # Normalized residual must be scale-invariant and within solver tolerance
        assert max_norm <= 1e-8, f"Normalized residual {max_norm:.2e} exceeded tolerance"
        # Absolute residual scales as energy^2
        assert max_abs <= 1e-8 * (energy ** 2)

    @pytest.mark.parametrize("kappa", [0.01, 0.1, 1.0, 10.0, 100.0])
    def test_val_sch_03_algebraic_and_pointwise_scale_invariance(self, kappa: float) -> None:
        """Confirms that scaling momenta p_mu -> kappa * p_mu produces quadratic H scaling and invariant normalized residual."""
        metric = SchwarzschildMetric(mass=1.0)
        coords = np.array([0.0, 6.0, np.pi / 2.0, 0.0])
        base_energy = 1.0
        y0 = null_geodesic_initial_state(
            metric=metric, x=coords, energy=base_energy, Lz=4.0, radial_direction="inward"
        )
        base_p = y0[4:]
        base_h = hamiltonian_value(coords, base_p, metric)

        scaled_p = kappa * base_p
        scaled_h = hamiltonian_value(coords, scaled_p, metric)

        # 1. Quadratic scaling of absolute residual: |H(x, kappa * p)| <= C * eps_mach * (kappa * E)^2
        f_r = metric.lapse(coords[IDX_R])
        scale_scaled = ((kappa * base_energy) ** 2) / f_r
        assert abs(scaled_h) <= 1e-12 * (kappa ** 2)

        # 2. Pointwise normalized residual: |H| / ((kappa * E)^2 / f(r)) is scale-invariant and <= 1e-12
        norm_scaled = abs(scaled_h) / scale_scaled
        assert norm_scaled <= 1e-12

    def test_val_sch_03_integrated_trajectory_scale_invariance_and_quadratic_scaling(self) -> None:
        """Verifies that across integrated trajectories with energy varying over 2 decades,
        the maximum normalized residual is invariant and maximum absolute residual scales quadratically."""
        metric = SchwarzschildMetric(mass=1.0)
        r0 = 10.0
        x0 = np.array([0.0, r0, np.pi / 2.0, 0.0], dtype=np.float64)

        energies = [0.1, 1.0, 10.0]
        max_abs_list = []
        max_norm_list = []

        for E in energies:
            y0 = null_geodesic_initial_state(
                metric=metric, x=x0, energy=E, Lz=7.0 * E, ptheta=0.0, radial_direction="outward"
            )
            res = integrate_geodesic(
                initial_state=y0,
                metric=metric,
                affine_span=(0.0, 4.0 / E),
                rtol=1e-10,
                atol=1e-10,
            )
            assert res.success is True
            h_abs = [
                abs(hamiltonian_value(res.states[i, :4], res.states[i, 4:], metric))
                for i in range(len(res.lambdas))
            ]
            h_norm = [
                h_abs[i] / ((E ** 2) / metric.lapse(res.states[i, 1]))
                for i in range(len(res.lambdas))
            ]
            max_abs_list.append(max(h_abs))
            max_norm_list.append(max(h_norm))

        # Normalized residuals are invariant within a factor of 2 across 100x energy span
        assert max_norm_list[0] <= 1e-8
        assert max_norm_list[1] <= 1e-8
        assert max_norm_list[2] <= 1e-8
        np.testing.assert_allclose(max_norm_list, max_norm_list[1], rtol=0.5)

        # Absolute residuals scale quadratically: E=1 vs E=0.1 has ratio ~100; E=10 vs E=1 has ratio ~100
        ratio_1_to_01 = max_abs_list[1] / max_abs_list[0]
        ratio_10_to_1 = max_abs_list[2] / max_abs_list[1]
        assert 50.0 <= ratio_1_to_01 <= 200.0, f"Expected ~100, got {ratio_1_to_01}"
        assert 50.0 <= ratio_10_to_1 <= 200.0, f"Expected ~100, got {ratio_10_to_1}"


# =============================================================================
# Test Suite: VAL-SCH-04 (Schwarzschild Photon Sphere Validation)
# =============================================================================

class TestSchwarzschildPhotonSphere:
    """VAL-SCH-04: Scientific validation of the Schwarzschild photon sphere at r = 3M.

    Validates:
    1. Critical impact parameter b_crit = L_z / E = 3*sqrt(3)*M.
    2. Initial state satisfies exact null constraint H(y0) = 0.
    3. Hamiltonian phase-space flow vanishes identically at r = 3M:
           dr / dlambda = 0,  dp_r / dlambda = 0.
    4. Orbit remains on circular track over finite affine parameter intervals.
    5. Conservation of E and L_z on the circular orbit.
    6. Physical instability characterization: V_eff''(3M) < 0.
    """

    def test_val_sch_04_photon_sphere_phase_space_fixed_point(self) -> None:
        """Verifies vanishing radial Hamiltonian vector field at r = 3M, b = 3*sqrt(3)*M."""
        mass = 1.0
        metric = SchwarzschildMetric(mass=mass)
        energy = 1.0
        r_ph = metric.photon_sphere_radius  # 3M = 3.0
        b_crit = metric.critical_impact_parameter  # 3*sqrt(3)*M ~ 5.196152422706632
        Lz_ph = energy * b_crit

        x0 = np.array([0.0, r_ph, np.pi / 2.0, 0.0], dtype=np.float64)

        y0 = null_geodesic_initial_state(
            metric=metric,
            x=x0,
            energy=energy,
            Lz=Lz_ph,
            ptheta=0.0,
            radial_direction="inward",  # At turning point pr = 0 identically
        )

        # 1. State properties at photon sphere
        assert np.isclose(y0[IDX_R], 3.0 * mass)
        assert np.isclose(y0[5], 0.0, atol=1e-14)  # pr == 0.0

        # 2. Hamiltonian value is zero to machine precision
        h_val = hamiltonian_value(y0[:4], y0[4:], metric)
        assert abs(h_val) <= 1e-15

        # 3. Hamiltonian right-hand side vector field evaluation:
        # dx^mu / dlambda and dp_mu / dlambda
        rhs = hamiltonian_rhs(y0, metric)

        # dr / dlambda = g^{rr} * pr = f(3M) * 0 = 0
        dr_dlambda = rhs[IDX_R]
        assert abs(dr_dlambda) <= 1e-15, f"Expected dr/dlambda == 0, got {dr_dlambda}"

        # dp_r / dlambda = -1/2 [ f'/(f^2) * E^2 - 2/r^3 * Lz^2 ]
        # At r = 3M: f' = 2/(9M), f = 1/3 => f'/f^2 = 2/M
        # 2/r^3 * Lz^2 = 2/(27M^3) * 27M^2 E^2 = 2/M E^2
        # Exact cancellation: dp_r / dlambda == 0
        dpr_dlambda = rhs[5]
        assert abs(dpr_dlambda) <= 1e-14, f"Expected dpr/dlambda == 0, got {dpr_dlambda}"

        # Non-radial velocities:
        # dt / dlambda = E / f(3M) = 3*E
        assert np.isclose(rhs[IDX_X0], 3.0 * energy)
        # dphi / dlambda = Lz / r^2 = 3*sqrt(3)*M*E / (9M^2) = E * sqrt(3) / (3M)
        expected_omega = energy * np.sqrt(3.0) / (3.0 * mass)
        assert np.isclose(rhs[IDX_PHI], expected_omega)

    def test_val_sch_04_finite_affine_orbit_propagation(self) -> None:
        """Integrates circular photon orbit over finite interval and confirms radius preservation.

        A complete 2*pi revolution requires Delta lambda = 2*pi / omega = 2*pi * sqrt(3) * M ~ 10.88 M.
        We integrate over Delta lambda = 12.0 M (~1.1 revolutions) under tight DOP853 tolerances.
        """
        mass = 1.0
        metric = SchwarzschildMetric(mass=mass)
        energy = 1.0
        r_ph = 3.0 * mass
        Lz_ph = energy * 3.0 * np.sqrt(3.0) * mass
        x0 = np.array([0.0, r_ph, np.pi / 2.0, 0.0], dtype=np.float64)

        y0 = null_geodesic_initial_state(
            metric=metric,
            x=x0,
            energy=energy,
            Lz=Lz_ph,
            ptheta=0.0,
            radial_direction="inward",
        )

        lambda_span = (0.0, 12.0)
        res = integrate_geodesic(
            initial_state=y0,
            metric=metric,
            affine_span=lambda_span,
            rtol=1e-11,
            atol=1e-12,
            method="DOP853",
        )

        assert res.success is True

        # Radius stays at 3M to high precision over this finite interval
        max_r_err = float(np.max(np.abs(res.r - r_ph)))
        assert max_r_err <= 1e-7, (
            f"Photon sphere radius drifted by {max_r_err:.2e} > 1e-7 over lambda={lambda_span[1]}"
        )

        # pr stays approximately zero
        max_pr = float(np.max(np.abs(res.pr)))
        assert max_pr <= 1e-7

        # Conserved quantities preserved
        np.testing.assert_allclose(res.p0, -energy, rtol=1e-10)
        np.testing.assert_allclose(res.pphi, Lz_ph, rtol=1e-10)

        # Planar preservation
        np.testing.assert_allclose(res.theta, np.pi / 2.0, atol=1e-10)
        np.testing.assert_allclose(res.ptheta, 0.0, atol=1e-10)

        # Completed azimuthal angle should be approx omega * lambda_end ~ 0.57735 * 12 ~ 6.93 rad
        omega = energy * np.sqrt(3.0) / (3.0 * mass)
        np.testing.assert_allclose(res.phi[-1], omega * lambda_span[1], rtol=1e-4)

    def test_val_sch_04_effective_potential_instability(self) -> None:
        """Validates that r = 3M is an unstable maximum of V_eff: V_eff''(3M) < 0."""
        mass = 1.0
        metric = SchwarzschildMetric(mass=mass)
        energy = 1.0
        Lz = energy * 3.0 * np.sqrt(3.0) * mass

        r_ph = 3.0 * mass
        dr = 1e-4

        def v_eff(r: float) -> float:
            return float((1.0 - 2.0 * mass / r) * (Lz ** 2) / (r ** 2))

        # First derivative via central difference
        dv_dr = (v_eff(r_ph + dr) - v_eff(r_ph - dr)) / (2.0 * dr)
        assert abs(dv_dr) <= 1e-7, f"dV_eff/dr at r=3M was {dv_dr}, expected 0"

        # Second derivative via central difference
        d2v_dr2 = (v_eff(r_ph + dr) - 2.0 * v_eff(r_ph) + v_eff(r_ph - dr)) / (dr ** 2)
        expected_d2v_dr2 = -6.0 * (Lz ** 2) / (243.0 * (mass ** 4))
        np.testing.assert_allclose(d2v_dr2, expected_d2v_dr2, rtol=1e-4)
        assert d2v_dr2 < 0.0, "Photon sphere is not a local maximum of V_eff"


# =============================================================================
# Test Suite: VAL-SCH-05 (Numerical Convergence Across Tolerances)
# =============================================================================

class TestSchwarzschildConvergence:
    """VAL-SCH-05: Numerical convergence verification under tightening tolerances.

    Examines:
        epsilon_r = max_i |r_num(lambda_i) - r_analytic(lambda_i)|
    along with Hamiltonian constraint and energy drift errors across identical sample grids.
    """

    def test_val_sch_05_three_tier_convergence(self) -> None:
        """Evaluates convergence across loose (1e-6), intermediate (1e-9), and tight (1e-12) tolerances."""
        mass = 1.0
        metric = SchwarzschildMetric(mass=mass)
        r0 = 6.0
        energy = 1.0
        x0 = np.array([0.0, r0, np.pi / 2.0, 0.0], dtype=np.float64)

        y0 = null_geodesic_initial_state(
            metric=metric,
            x=x0,
            energy=energy,
            Lz=0.0,
            ptheta=0.0,
            radial_direction="outward",
        )

        lambda_end = 6.0
        # Common sample grid for all tolerance configurations
        t_eval = np.linspace(0.0, lambda_end, 31)
        r_exact = r0 + energy * t_eval

        tolerance_configs = [
            (1e-6, 1e-6, "loose"),
            (1e-9, 1e-9, "intermediate"),
            (1e-12, 1e-12, "tight"),
        ]

        results = []

        for rtol, atol, label in tolerance_configs:
            res = integrate_geodesic(
                initial_state=y0,
                metric=metric,
                affine_span=(0.0, lambda_end),
                t_eval=t_eval,
                rtol=rtol,
                atol=atol,
                method="DOP853",
            )
            assert res.success is True

            # Error metrics
            r_err = float(np.max(np.abs(res.r - r_exact)))
            e_err = float(np.max(np.abs(-res.p0 - energy)))

            # Hamiltonian residual
            h_res = float(np.max([
                abs(hamiltonian_value(res.states[i, :4], res.states[i, 4:], metric))
                for i in range(len(res.lambdas))
            ]))

            results.append({
                "label": label,
                "rtol": rtol,
                "atol": atol,
                "r_err": r_err,
                "e_err": e_err,
                "h_res": h_res,
                "nfev": res.nfev,
            })

        # Monotonic decrease of position error with tighter tolerance
        assert results[1]["r_err"] < results[0]["r_err"], "Intermediate tol did not improve on loose"
        assert results[2]["r_err"] < results[1]["r_err"], "Tight tol did not improve on intermediate"

        # Energy conservation is preserved to machine precision across all tiers
        for item in results:
            assert item["e_err"] <= 1e-12

        # Final tight configuration achieves precision near machine roundoff for radial motion
        assert results[2]["r_err"] <= 1e-10
        assert results[2]["e_err"] <= 1e-11
        assert results[2]["h_res"] <= 1e-11
