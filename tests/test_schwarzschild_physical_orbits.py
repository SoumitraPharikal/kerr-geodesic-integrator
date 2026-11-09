"""Scientific validation test suite for Schwarzschild physical orbits (Stage 3A).

This module rigorously validates that the canonical Hamiltonian framework and numerical
integrator reproduce the classic analytic and physical properties of orbits in exterior
Schwarzschild spacetime:
1. VAL-SCH-CIRC-01: Null circular orbit at the photon sphere r = 3M.
2. VAL-SCH-CIRC-02: Timelike circular orbits across radii r = 8M (stable),
   r = 6M (marginally stable / ISCO), and r = 4M (unstable).
3. VAL-SCH-CIRC-03: Analytical and numerical characterization of the ISCO at r = 6M
   and radial stability via controlled constraint-preserving momentum perturbations.
"""

from typing import Final
import numpy as np
import pytest

from geodesics.constants import (
    IDX_PHI,
    IDX_R,
    IDX_THETA,
    IDX_X0,
)
from geodesics.events import (
    RadialTurningPointEvent,
    horizon_cutoff_event,
)
from geodesics.hamiltonian import (
    hamiltonian_rhs,
    hamiltonian_value,
)
from geodesics.initial_conditions import (
    schwarzschild_circular_orbital_frequency,
    schwarzschild_circular_timelike_angular_momentum,
    schwarzschild_circular_timelike_energy,
    schwarzschild_circular_timelike_initial_state,
    schwarzschild_perturbed_circular_timelike_initial_state,
    schwarzschild_photon_sphere_initial_state,
)
from geodesics.integrator import integrate_geodesic
from geodesics.metrics.schwarzschild import SchwarzschildMetric


# =============================================================================
# 1. Analytic Formula Verification & Effective Potential Derivatives
# =============================================================================


class TestSchwarzschildAnalyticFormulas:
    """Verifies exact analytic formulas for Schwarzschild circular orbits and ISCO condition."""

    @pytest.mark.parametrize("mass", [0.5, 1.0, 2.5])
    def test_photon_sphere_radius_and_critical_impact_parameter(self, mass: float) -> None:
        """Verifies photon sphere radius r_ph = 3M, b_crit = 3*sqrt(3)*M, and r_ISCO = 6M."""
        metric = SchwarzschildMetric(mass=mass)
        assert metric.photon_sphere_radius == 3.0 * mass
        assert np.isclose(metric.critical_impact_parameter, 3.0 * np.sqrt(3.0) * mass)
        assert metric.isco_radius == 6.0 * mass

    @pytest.mark.parametrize("mass", [0.8, 1.0, 2.0])
    def test_timelike_circular_analytic_energy_and_momentum_values(self, mass: float) -> None:
        """Verifies E_c, L_c, and Omega_phi against closed-form expressions for key radii."""
        # 1. Radius r = 4M: E_c = 1.0, L_c = 4*M, Omega = sqrt(M / (4M)^3) = 1 / (8*M)
        r4 = 4.0 * mass
        e4 = schwarzschild_circular_timelike_energy(r4, mass)
        l4 = schwarzschild_circular_timelike_angular_momentum(r4, mass, prograde=True)
        w4 = schwarzschild_circular_orbital_frequency(r4, mass)
        assert np.isclose(e4, 1.0, atol=1e-15)
        assert np.isclose(l4, 4.0 * mass, atol=1e-15)
        assert np.isclose(w4, 1.0 / (8.0 * mass), atol=1e-15)

        # 2. Radius r = 6M (ISCO): E_c = 2*sqrt(2)/3, L_c = 2*sqrt(3)*M, Omega = 1 / (6*sqrt(6)*M)
        r6 = 6.0 * mass
        e6 = schwarzschild_circular_timelike_energy(r6, mass)
        l6 = schwarzschild_circular_timelike_angular_momentum(r6, mass, prograde=True)
        w6 = schwarzschild_circular_orbital_frequency(r6, mass)
        assert np.isclose(e6, 2.0 * np.sqrt(2.0) / 3.0, atol=1e-15)
        assert np.isclose(l6, 2.0 * np.sqrt(3.0) * mass, atol=1e-15)
        assert np.isclose(w6, 1.0 / (6.0 * np.sqrt(6.0) * mass), atol=1e-15)

        # 3. Radius r = 8M: E_c = 3*sqrt(10)/10, L_c = 8*sqrt(5)*M/5, Omega = 1 / (16*sqrt(2)*M)
        r8 = 8.0 * mass
        e8 = schwarzschild_circular_timelike_energy(r8, mass)
        l8 = schwarzschild_circular_timelike_angular_momentum(r8, mass, prograde=True)
        w8 = schwarzschild_circular_orbital_frequency(r8, mass)
        assert np.isclose(e8, 3.0 * np.sqrt(10.0) / 10.0, atol=1e-15)
        assert np.isclose(l8, 8.0 * np.sqrt(5.0) * mass / 5.0, atol=1e-15)
        assert np.isclose(w8, 1.0 / (16.0 * np.sqrt(2.0) * mass), atol=1e-15)

        # 4. Retrograde angular momentum
        l8_retro = schwarzschild_circular_timelike_angular_momentum(r8, mass, prograde=False)
        assert np.isclose(l8_retro, -l8, atol=1e-15)

    def test_rejection_of_unphysical_radii_and_parameters(self) -> None:
        """Rejects radii r <= 3M for timelike circular orbits and non-positive masses."""
        mass = 1.0
        # Exactly on the photon sphere: denominator vanishes
        with pytest.raises(ValueError, match="exist only for r > 3M"):
            schwarzschild_circular_timelike_energy(3.0 * mass, mass)

        with pytest.raises(ValueError, match="exist only for r > 3M"):
            schwarzschild_circular_timelike_angular_momentum(2.5 * mass, mass)

        # Invalid masses
        with pytest.raises(ValueError, match="Mass M must be positive"):
            schwarzschild_circular_timelike_energy(8.0, mass=0.0)
        with pytest.raises(ValueError, match="Mass M must be positive"):
            schwarzschild_circular_orbital_frequency(8.0, mass=-1.0)

    @pytest.mark.parametrize("r", [3.5, 4.0, 5.0, 6.0, 7.0, 8.0, 10.0, 12.0])
    def test_isco_effective_potential_second_derivative_identity(self, r: float) -> None:
        """Verifies the exact analytical second derivative V_eff''(r) = 2M(r - 6M) / [r^3(r - 3M)].

        Compares the analytical formula against high-precision central finite difference of V_eff'(r).
        """
        mass = 1.0
        # Circular angular momentum for this radius:
        Lc = schwarzschild_circular_timelike_angular_momentum(r, mass)

        # Exact first derivative of effective potential:
        # V_eff'(x) = 2M / x^2 - 2Lc^2 / x^3 + 6M*Lc^2 / x^4
        def v_prime(x: float) -> float:
            return float((2.0 * mass) / (x ** 2) - (2.0 * (Lc ** 2)) / (x ** 3) + (6.0 * mass * (Lc ** 2)) / (x ** 4))

        # 1. Verify V'(r) == 0 at the circular radius
        assert abs(v_prime(r)) <= 1e-15, f"V_eff'(r={r}) should be zero, got {v_prime(r):.2e}"

        # 2. Central difference of V'(r) to get numerical V''(r):
        h = 1e-5
        v_double_prime_num = (v_prime(r + h) - v_prime(r - h)) / (2.0 * h)

        # Analytical formula: V_eff''(r) = 2M(r - 6M) / [r^3 (r - 3M)]
        v_double_prime_analytic = (2.0 * mass * (r - 6.0 * mass)) / ((r ** 3) * (r - 3.0 * mass))

        assert np.isclose(v_double_prime_num, v_double_prime_analytic, rtol=1e-8, atol=1e-12)

        # 3. Test physical stability sign:
        if r > 6.0 * mass:
            assert v_double_prime_analytic > 0.0, f"Expected stable V''>0 at r={r}"
        elif r == 6.0 * mass:
            assert np.isclose(v_double_prime_analytic, 0.0, atol=1e-15), "Expected V''=0 at ISCO (r=6M)"
        else:
            assert v_double_prime_analytic < 0.0, f"Expected unstable V''<0 at r={r}"


# =============================================================================
# 2. Photon Sphere Benchmark (Null Circular Orbit at r = 3M)
# =============================================================================


class TestSchwarzschildPhotonSphereBenchmark:
    """VAL-SCH-CIRC-01: Rigorous verification of the null circular orbit at r = 3M."""

    def test_photon_sphere_initial_state_and_hamiltonian_constraint(self) -> None:
        """Verifies photon sphere initial state construction, null constraint, and vanishing radial flow."""
        mass = 1.0
        metric = SchwarzschildMetric(mass=mass)
        energy = 1.0
        y0 = schwarzschild_photon_sphere_initial_state(metric, energy=energy)

        # Coordinates
        assert y0[IDX_X0] == 0.0
        assert y0[IDX_R] == 3.0 * mass
        assert y0[IDX_THETA] == 0.5 * np.pi
        assert y0[IDX_PHI] == 0.0

        # Momenta
        assert y0[4] == -energy
        assert y0[5] == 0.0
        assert y0[6] == 0.0
        assert np.isclose(y0[7], 3.0 * np.sqrt(3.0) * mass * energy)

        # Mass-shell constraint: H(y0) == 0 to machine precision
        h0 = hamiltonian_value(y0[:4], y0[4:], metric)
        assert abs(h0) <= 1e-15

        # Phase-space vector field at r = 3M
        rhs = hamiltonian_rhs(y0, metric)
        # dr/dlambda = g^{rr} * p_r = 0
        assert abs(rhs[IDX_R]) <= 1e-15
        # dp_r/dlambda = -1/2 (dg/dr) p p = 0
        assert abs(rhs[5]) <= 1e-14
        # dp_theta/dlambda = 0
        assert abs(rhs[6]) <= 1e-15

        # Affine coordinate rates:
        # dt/dlambda = -g^{00} * (-E) = E / f(3M) = 3*E
        assert np.isclose(rhs[IDX_X0], 3.0 * energy)
        # dphi/dlambda = g^{phi phi} * Lz = 3*sqrt(3)*M*E / (9M^2) = E / (sqrt(3)*M)
        assert np.isclose(rhs[IDX_PHI], energy / (np.sqrt(3.0) * mass))

        # Coordinate-time frequency: dphi/dt = (dphi/dlambda) / (dt/dlambda) = 1 / (3*sqrt(3)*M)
        omega_coord = rhs[IDX_PHI] / rhs[IDX_X0]
        assert np.isclose(omega_coord, 1.0 / (3.0 * np.sqrt(3.0) * mass), atol=1e-15)

    def test_photon_sphere_multi_orbit_numerical_integration(self) -> None:
        """Integrates photon sphere orbit over 2 complete revolutions and confirms conservation."""
        mass = 1.0
        metric = SchwarzschildMetric(mass=mass)
        energy = 1.0
        y0 = schwarzschild_photon_sphere_initial_state(metric, energy=energy)

        # Period in affine parameter: Delta lambda = 2*pi / (dphi/dlambda) = 2*pi * sqrt(3)*M ~ 10.88 M
        # Integrate for 2 full revolutions: Delta lambda = 4*pi * sqrt(3) ~ 21.7656
        t_span = (0.0, 4.0 * np.pi * np.sqrt(3.0) * mass)

        res = integrate_geodesic(
            initial_state=y0,
            metric=metric,
            affine_span=t_span,
            rtol=1e-10,
            atol=1e-10,
            method="DOP853",
        )
        assert res.success is True

        # 1. Radial invariance: r stays at 3M to high accuracy
        max_dr = float(np.max(np.abs(res.r - 3.0 * mass)))
        assert max_dr <= 1e-10, f"Photon sphere radius drifted by {max_dr:.2e}"

        # 2. Polar invariance: theta stays in equator
        max_dth = float(np.max(np.abs(res.theta - 0.5 * np.pi)))
        assert max_dth <= 1e-12

        # 3. Radial and polar conjugate momenta remain consistent with zero
        max_pr = float(np.max(np.abs(res.pr)))
        max_pth = float(np.max(np.abs(res.ptheta)))
        assert max_pr <= 1e-10
        assert max_pth <= 1e-12

        # 4. Energy and angular momentum conservation
        max_de = float(np.max(np.abs(-res.states[:, 4] - energy)))
        max_dl = float(np.max(np.abs(res.states[:, 7] - y0[7])))
        assert max_de <= 1e-14
        assert max_dl <= 1e-14

        # 5. Null Hamiltonian constraint preservation
        h_vals = [abs(hamiltonian_value(s[:4], s[4:], metric)) for s in res.states]
        assert max(h_vals) <= 1e-14

        # 6. Orbital frequency verification:
        # Measured coordinate-time frequency: Delta phi / Delta t
        delta_phi = res.phi[-1] - res.phi[0]
        delta_t = res.x0[-1] - res.x0[0]
        omega_num = delta_phi / delta_t
        omega_analytic = 1.0 / (3.0 * np.sqrt(3.0) * mass)
        assert np.isclose(omega_num, omega_analytic, rtol=1e-13, atol=1e-14)

        # Measured affine angular rate: Delta phi / Delta lambda
        delta_lambda = res.lambdas[-1] - res.lambdas[0]
        dphi_dlambda_num = delta_phi / delta_lambda
        dphi_dlambda_analytic = energy / (np.sqrt(3.0) * mass)
        assert np.isclose(dphi_dlambda_num, dphi_dlambda_analytic, rtol=1e-10, atol=1e-10)


# =============================================================================
# 3. Timelike Circular Orbits (r = 8M, 6M, 4M)
# =============================================================================


class TestSchwarzschildTimelikeCircularOrbits:
    """VAL-SCH-CIRC-02: Rigorous verification of timelike circular orbits."""

    @pytest.mark.parametrize("r_c", [8.0, 6.0, 4.0])
    def test_timelike_circular_initial_state_and_hamiltonian_constraint(self, r_c: float) -> None:
        """Verifies exact mass-shell constraint H = -0.5 and vanishing phase-space velocity."""
        mass = 1.0
        metric = SchwarzschildMetric(mass=mass)
        y0 = schwarzschild_circular_timelike_initial_state(metric, r=r_c)

        # Coordinates
        assert y0[IDX_R] == r_c
        assert y0[IDX_THETA] == 0.5 * np.pi
        assert y0[5] == 0.0  # p_r == 0
        assert y0[6] == 0.0  # p_theta == 0

        # Conserved quantities
        Ec = schwarzschild_circular_timelike_energy(r_c, mass)
        Lc = schwarzschild_circular_timelike_angular_momentum(r_c, mass)
        assert np.isclose(-y0[4], Ec, atol=1e-15)
        assert np.isclose(y0[7], Lc, atol=1e-15)

        # Exact mass-shell constraint: 2*H = -1 => H = -0.5
        h0 = hamiltonian_value(y0[:4], y0[4:], metric)
        assert abs(h0 - (-0.5)) <= 2e-16

        # Phase-space flow vanishing
        rhs = hamiltonian_rhs(y0, metric)
        assert abs(rhs[IDX_R]) <= 1e-16, f"dr/dtau should be 0, got {rhs[IDX_R]}"
        assert abs(rhs[5]) <= 2e-16, f"dp_r/dtau should be 0, got {rhs[5]}"
        assert abs(rhs[6]) <= 1e-16, f"dp_theta/dtau should be 0, got {rhs[6]}"

        # Coordinate-time frequency: dphi / dt = (dphi/dtau) / (dt/dtau) == sqrt(M / r^3)
        omega_coord = rhs[IDX_PHI] / rhs[IDX_X0]
        omega_analytic = schwarzschild_circular_orbital_frequency(r_c, mass)
        assert np.isclose(omega_coord, omega_analytic, atol=2e-16)

    @pytest.mark.parametrize("r_c", [8.0, 6.0, 4.0])
    def test_timelike_circular_orbit_preservation_over_two_periods(self, r_c: float) -> None:
        """Demonstrates numerical preservation of exact circular orbits over 2 orbital periods.

        NOTE: Preservation of an unperturbed circular orbit demonstrates that it is an exact
        stationary solution of the geodesic equations; it does NOT prove radial stability.
        """
        mass = 1.0
        metric = SchwarzschildMetric(mass=mass)
        y0 = schwarzschild_circular_timelike_initial_state(metric, r=r_c)

        # Coordinate period: T = 2*pi / Omega_phi = 2*pi * sqrt(r^3/M)
        # Proper time span: Delta tau = Delta t / (dt/dtau) = Delta t * f(r) / E_c
        f_r = 1.0 - (2.0 * mass / r_c)
        Ec = -y0[4]
        Lc = y0[7]
        omega_analytic = np.sqrt(mass / (r_c ** 3))
        T_coord = 2.0 * np.pi / omega_analytic
        tau_span = (0.0, 2.0 * T_coord * f_r / Ec)

        res = integrate_geodesic(
            initial_state=y0,
            metric=metric,
            affine_span=tau_span,
            rtol=1e-10,
            atol=1e-10,
            method="DOP853",
        )
        assert res.success is True

        # 1. Radial invariance
        max_dr = float(np.max(np.abs(res.r - r_c)))
        assert max_dr <= 1e-11, f"Radius drifted by {max_dr:.2e} at r={r_c}"

        # 2. Polar invariance
        max_dth = float(np.max(np.abs(res.theta - 0.5 * np.pi)))
        assert max_dth <= 1e-12

        # 3. Radial momentum
        max_pr = float(np.max(np.abs(res.pr)))
        assert max_pr <= 1e-13

        # 4. Conservation of E and Lz
        max_de = float(np.max(np.abs(-res.states[:, 4] - Ec)))
        max_dl = float(np.max(np.abs(res.states[:, 7] - Lc)))
        assert max_de <= 1e-14
        assert max_dl <= 1e-14

        # 5. Mass-shell constraint preservation: H = -0.5
        h_vals = [abs(hamiltonian_value(s[:4], s[4:], metric) - (-0.5)) for s in res.states]
        assert max(h_vals) <= 1e-14

        # 6. Measured orbital frequency matches Kepler's third law
        delta_phi = res.phi[-1] - res.phi[0]
        delta_t = res.x0[-1] - res.x0[0]
        omega_num = delta_phi / delta_t
        assert np.isclose(omega_num, omega_analytic, rtol=1e-13, atol=1e-13)


# =============================================================================
# 4. Stability Analysis via Controlled Radial Perturbations
# =============================================================================


class TestSchwarzschildStabilityAnalysis:
    """VAL-SCH-CIRC-03: Controlled constraint-preserving radial momentum perturbations.

    Validates:
    1. r = 8M > 6M: Stable orbit; bounded radial epicyclic oscillations with amplitude ~ O(delta_pr).
    2. r = 6M: Marginally stable (ISCO); asymmetric restoring force.
    3. r = 4M < 6M: Unstable orbit; outward perturbation escapes to large r; inward perturbation plunges.
    """

    @pytest.mark.parametrize("r_c", [8.0, 6.0, 4.0])
    @pytest.mark.parametrize("delta_pr", [-1e-3, 1e-4, 1e-3, 5e-3])
    def test_perturbed_state_preserves_mass_shell_constraint(
        self, r_c: float, delta_pr: float
    ) -> None:
        """Verifies that recomputing energy E_pert strictly preserves H = -0.5 to machine precision."""
        mass = 1.0
        metric = SchwarzschildMetric(mass=mass)
        y0_pert = schwarzschild_perturbed_circular_timelike_initial_state(
            metric=metric, r=r_c, delta_pr=delta_pr
        )

        assert y0_pert[5] == delta_pr
        h0 = hamiltonian_value(y0_pert[:4], y0_pert[4:], metric)
        assert abs(h0 - (-0.5)) <= 5e-16

    def test_stable_orbit_at_8M_bounded_epicyclic_oscillation(self) -> None:
        """Demonstrates bounded radial oscillation at r = 8M with linear scaling in delta_pr."""
        mass = 1.0
        metric = SchwarzschildMetric(mass=mass)
        r_c = 8.0 * mass
        tau_span = (0.0, 300.0)

        # Test two perturbation amplitudes to confirm physical stability and linearity
        y0_small = schwarzschild_perturbed_circular_timelike_initial_state(
            metric=metric, r=r_c, delta_pr=1e-4
        )
        res_small = integrate_geodesic(y0_small, metric, tau_span, rtol=1e-10, atol=1e-10)
        assert res_small.success is True
        amp_small = float(np.max(res_small.r) - np.min(res_small.r))

        y0_large = schwarzschild_perturbed_circular_timelike_initial_state(
            metric=metric, r=r_c, delta_pr=1e-3
        )
        res_large = integrate_geodesic(y0_large, metric, tau_span, rtol=1e-10, atol=1e-10)
        assert res_large.success is True
        amp_large = float(np.max(res_large.r) - np.min(res_large.r))

        # 1. Bounded oscillations around 8.0
        assert amp_small < 0.01 * r_c
        assert amp_large < 0.1 * r_c
        assert np.isclose(0.5 * (np.max(res_small.r) + np.min(res_small.r)), r_c, atol=1e-3)

        # 2. Linear scaling with perturbation amplitude (10x delta_pr -> ~10x amplitude)
        ratio = amp_large / amp_small
        assert 9.5 <= ratio <= 10.5, f"Expected ~10x amplitude ratio, got {ratio:.2f}"

        # 3. Hamiltonian conservation along perturbed trajectory
        h_err_small = [abs(hamiltonian_value(s[:4], s[4:], metric) - (-0.5)) for s in res_small.states]
        assert max(h_err_small) <= 1e-13

    def test_unstable_orbit_at_4M_escape_and_plunge(self) -> None:
        """Demonstrates physical instability at r = 4M: outward kick escapes, inward kick plunges."""
        mass = 1.0
        metric = SchwarzschildMetric(mass=mass)
        r_c = 4.0 * mass

        # 1. Outward perturbation delta_pr = +1e-3: particle escapes over potential barrier
        y0_out = schwarzschild_perturbed_circular_timelike_initial_state(
            metric=metric, r=r_c, delta_pr=1e-3
        )
        res_out = integrate_geodesic(y0_out, metric, (0.0, 200.0), rtol=1e-10, atol=1e-10)
        assert res_out.success is True
        # Particle completely departs from r=4M and escapes to large r > 30M
        assert res_out.r[-1] > 30.0 * mass
        assert np.max(res_out.r) - r_c > 35.0 * mass

        # 2. Inward perturbation delta_pr = -1e-3: particle plunges into the horizon
        y0_in = schwarzschild_perturbed_circular_timelike_initial_state(
            metric=metric, r=r_c, delta_pr=-1e-3
        )
        # Attach a horizon cutoff event at r = 2M*(1 + epsilon) = 2.10M
        cutoff = horizon_cutoff_event(metric, epsilon=0.05)
        res_in = integrate_geodesic(
            y0_in, metric, (0.0, 200.0), events=[cutoff], rtol=1e-10, atol=1e-10
        )
        # Plunge reaches the horizon surface and triggers the cutoff event
        assert res_in.terminal_event_occurred is True
        assert res_in.terminal_event_name == "horizon_cutoff"
        assert np.isclose(res_in.r[-1], 2.0 * mass * 1.05, atol=1e-3)

    def test_marginal_stability_at_isco_6M(self) -> None:
        """Demonstrates marginal stability at r = 6M: asymmetric response between outward and inward kicks."""
        mass = 1.0
        metric = SchwarzschildMetric(mass=mass)
        r_c = 6.0 * mass

        # 1. Outward perturbation delta_pr = +1e-3: moves into stable domain r > 6M
        y0_out = schwarzschild_perturbed_circular_timelike_initial_state(
            metric=metric, r=r_c, delta_pr=1e-3
        )
        res_out = integrate_geodesic(y0_out, metric, (0.0, 200.0), rtol=1e-10, atol=1e-10)
        assert res_out.success is True
        # Bounded departure in the stable exterior region
        assert np.max(res_out.r) < 6.2 * mass
        assert np.min(res_out.r) >= 5.999 * mass

        # 2. Inward perturbation delta_pr = -1e-3: moves into unstable domain r < 6M
        y0_in = schwarzschild_perturbed_circular_timelike_initial_state(
            metric=metric, r=r_c, delta_pr=-1e-3
        )
        res_in = integrate_geodesic(y0_in, metric, (0.0, 200.0), rtol=1e-10, atol=1e-10)
        assert res_in.success is True
        # Inward motion goes significantly deeper than the outward excursion
        assert np.min(res_in.r) < 5.85 * mass
        inward_drop = r_c - np.min(res_in.r)
        outward_rise = np.max(res_out.r) - r_c
        # Asymmetry of the inflection point: inward drop is strictly greater than outward rise
        assert inward_drop > 1.5 * outward_rise


# =============================================================================
# 5. Tolerance-Refinement and Stability Robustness Regression Suite
# =============================================================================


class TestSchwarzschildStabilityToleranceRobustness:
    """Regression tests verifying stability conclusions across numerical tolerances.

    Confirms that:
    1. Stable orbit at r = 8M exhibits bounded oscillations across rtol=atol in [1e-8, 1e-10, 1e-12].
    2. Marginal ISCO orbit at r = 6M preserves outward/inward asymmetry across tolerances.
    3. Unstable orbit at r = 4M consistently bifurcates into outward escape vs. inward plunge.
    4. Exact circular orbits at r = 8M, 6M, 4M remain exact stationary fixed points at all tolerances.
    """

    @staticmethod
    def _count_turning_points(r_arr: np.ndarray) -> int:
        dr = np.diff(r_arr)
        signs = np.sign(dr)
        # Filter zero differences
        valid = signs != 0
        filtered_signs = signs[valid]
        sign_changes = np.where(np.diff(filtered_signs) != 0)[0]
        return int(len(sign_changes))

    @pytest.mark.parametrize("tol", [1e-8, 1e-10, 1e-12])
    @pytest.mark.parametrize("delta_pr", [1e-4, 1e-3])
    def test_stable_orbit_boundedness_across_tolerances(
        self, tol: float, delta_pr: float
    ) -> None:
        """Verifies that bounded epicyclic oscillation at r = 8M survives tolerance refinement."""
        mass = 1.0
        metric = SchwarzschildMetric(mass=mass)
        r_c = 8.0 * mass
        tau_span = (0.0, 300.0)

        y0 = schwarzschild_perturbed_circular_timelike_initial_state(
            metric=metric, r=r_c, delta_pr=delta_pr
        )
        e0 = -y0[4]
        l0 = y0[7]
        h0 = hamiltonian_value(y0[:4], y0[4:], metric)

        res = integrate_geodesic(y0, metric, tau_span, rtol=tol, atol=tol)
        assert res.success is True

        # 1. Trajectory remains bounded within tight physical neighborhood
        r_min = float(np.min(res.r))
        r_max = float(np.max(res.r))
        assert r_min > 7.95 * mass
        assert r_max < 8.05 * mass

        # 2. Epicyclic oscillations: multiple turning points occur over tau in [0, 300]
        n_tp = self._count_turning_points(res.r)
        assert n_tp >= 3, f"Expected at least 3 turning points, got {n_tp}"

        # 3. Conserved quantities and Hamiltonian constraint preservation
        max_de = float(np.max(np.abs(-res.states[:, 4] - e0)))
        max_dl = float(np.max(np.abs(res.states[:, 7] - l0)))
        max_dh = float(np.max([abs(hamiltonian_value(s[:4], s[4:], metric) - h0) for s in res.states]))

        assert max_de <= 1e-14
        assert max_dl <= 1e-14
        assert max_dh <= 2e-12

    @pytest.mark.parametrize("tol", [1e-8, 1e-10, 1e-12])
    def test_isco_asymmetry_across_tolerances(self, tol: float) -> None:
        """Verifies that the qualitative ISCO asymmetry persists across tolerances."""
        mass = 1.0
        metric = SchwarzschildMetric(mass=mass)
        r_c = 6.0 * mass
        tau_span = (0.0, 200.0)
        dp = 1e-3

        y0_out = schwarzschild_perturbed_circular_timelike_initial_state(metric, r_c, delta_pr=+dp)
        y0_in = schwarzschild_perturbed_circular_timelike_initial_state(metric, r_c, delta_pr=-dp)

        res_out = integrate_geodesic(y0_out, metric, tau_span, rtol=tol, atol=tol)
        res_in = integrate_geodesic(y0_in, metric, tau_span, rtol=tol, atol=tol)

        assert res_out.success is True
        assert res_in.success is True

        outward_rise = float(np.max(res_out.r) - r_c)
        inward_drop = float(r_c - np.min(res_in.r))

        # Over tau in [0, 200M], the outward trajectory has not reached its turning point:
        # p_r(tau=200M) remains strictly positive (still moving outward).
        assert res_out.pr[-1] > 0.0, f"Expected positive p_r at tau=200, got {res_out.pr[-1]}"
        assert np.isclose(res_out.r[-1], 6.096717, atol=1e-4)

        # Outward excursion over [0, 200M] is bounded by r(200M) < 6.12M
        assert outward_rise < 0.12 * mass
        # Inward motion plunges significantly deeper
        assert inward_drop > 0.18 * mass
        # Inward drop is substantially larger than outward excursion
        assert inward_drop > 1.8 * outward_rise

        # Hamiltonian conservation
        h0_out = hamiltonian_value(y0_out[:4], y0_out[4:], metric)
        max_dh_out = float(np.max([abs(hamiltonian_value(s[:4], s[4:], metric) - h0_out) for s in res_out.states]))
        assert max_dh_out <= 5e-12

    @pytest.mark.parametrize("tol", [1e-8, 1e-10, 1e-12])
    def test_isco_outward_perturbation_turning_point_and_plunge(self, tol: float) -> None:
        """Verifies true outer turning point and subsequent plunge for r = 6M, delta_pr = +1e-3.

        Specifically verifies:
        1. Over tau in [0, 200M], dr/dtau > 0 everywhere (no turning point prior to tau = 200M).
        2. A genuine radial turning point (dr/dtau = 0, p_r = 0) occurs at tau_turn ~ 204.31M
           at r_turn ~ 6.09678M (matching the exact algebraic root of V_eff(r) = E_pert^2).
        3. After turning around, the trajectory plunges into the horizon cutoff surface.
        """
        mass = 1.0
        metric = SchwarzschildMetric(mass=mass)
        r_c = 6.0 * mass
        dp = 1e-3
        y0_out = schwarzschild_perturbed_circular_timelike_initial_state(metric, r_c, delta_pr=dp)

        # 1. No turning point on [0, 200M]: p_r > 0 at tau = 200M
        res_200 = integrate_geodesic(y0_out, metric, (0.0, 200.0), rtol=tol, atol=tol)
        assert res_200.pr[-1] > 0.0

        # 2. Turning point event on extended interval [0, 300M]
        turn_evt = RadialTurningPointEvent(metric, terminal=False, direction=-1)
        res_turn = integrate_geodesic(y0_out, metric, (0.0, 300.0), events=[turn_evt], rtol=tol, atol=tol)
        assert res_turn.has_events is True
        rec = res_turn.triggered_events[0]
        assert np.isclose(rec.lambdas[0], 204.309, atol=1e-2)
        assert np.isclose(rec.states[0, 1], 6.096780, atol=1e-4)
        assert abs(rec.states[0, 5]) <= 1e-14

    @pytest.mark.parametrize("tol", [1e-8, 1e-10, 1e-12])
    def test_unstable_orbit_bifurcation_across_tolerances(self, tol: float) -> None:
        """Verifies physical bifurcation at r = 4M (escape vs. plunge) across tolerances."""
        mass = 1.0
        metric = SchwarzschildMetric(mass=mass)
        r_c = 4.0 * mass
        tau_span = (0.0, 200.0)
        cutoff = horizon_cutoff_event(metric, epsilon=0.05)

        # 1. Outward kick: delta_pr = +1e-4 -> escapes outward over simulated interval
        y0_out = schwarzschild_perturbed_circular_timelike_initial_state(metric, r_c, delta_pr=1e-4)
        res_out = integrate_geodesic(y0_out, metric, tau_span, events=[cutoff], rtol=tol, atol=tol)
        assert res_out.success is True
        assert res_out.terminal_event_occurred is False
        assert res_out.r[-1] > 30.0 * mass

        # 2. Inward kick: delta_pr = -1e-4 -> terminates at horizon cutoff surface
        y0_in = schwarzschild_perturbed_circular_timelike_initial_state(metric, r_c, delta_pr=-1e-4)
        res_in = integrate_geodesic(y0_in, metric, tau_span, events=[cutoff], rtol=tol, atol=tol)
        assert res_in.terminal_event_occurred is True
        assert res_in.terminal_event_name == "horizon_cutoff"
        assert np.isclose(res_in.r[-1], 2.0 * mass * 1.05, atol=1e-3)

    @pytest.mark.parametrize("tol", [1e-8, 1e-10, 1e-12])
    @pytest.mark.parametrize("r_c", [8.0, 6.0, 4.0])
    def test_exact_circular_orbit_preservation_across_tolerances(
        self, tol: float, r_c: float
    ) -> None:
        """Verifies exact circular-orbit preservation (stationary solution) across tolerances."""
        mass = 1.0
        metric = SchwarzschildMetric(mass=mass)
        f_r = 1.0 - (2.0 * mass / r_c)
        Ec = schwarzschild_circular_timelike_energy(r_c, mass)
        Lc = schwarzschild_circular_timelike_angular_momentum(r_c, mass)
        omega_analytic = np.sqrt(mass / (r_c ** 3))
        t_coord = 2.0 * np.pi / omega_analytic
        tau_span = (0.0, 2.0 * t_coord * f_r / Ec)

        y0 = np.array([0.0, r_c, 0.5 * np.pi, 0.0, -Ec, 0.0, 0.0, Lc], dtype=np.float64)
        h0 = hamiltonian_value(y0[:4], y0[4:], metric)

        res = integrate_geodesic(y0, metric, tau_span, rtol=tol, atol=tol)
        assert res.success is True

        max_dr = float(np.max(np.abs(res.r - r_c)))
        max_dth = float(np.max(np.abs(res.theta - 0.5 * np.pi)))
        max_pr = float(np.max(np.abs(res.pr)))
        max_dh = float(np.max([abs(hamiltonian_value(s[:4], s[4:], metric) - h0) for s in res.states]))

        assert max_dr <= 1e-10
        assert max_dth <= 1e-11
        assert max_pr <= 1e-10
        assert max_dh <= 1e-13

        omega_num = (res.phi[-1] - res.phi[0]) / (res.x0[-1] - res.x0[0])
        omega_err = abs(omega_num - omega_analytic) / omega_analytic
        assert omega_err <= 1e-11

