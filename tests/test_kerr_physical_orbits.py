"""Scientific validation test suite for Kerr equatorial circular timelike orbits and ISCO (Stage 3B).

This module rigorously validates that the canonical Hamiltonian framework and numerical
integrator reproduce the classic analytic and physical properties of equatorial circular timelike
geodesics in Kerr spacetime:
1. VAL-KERR-CIRC-01: Analytic formula verification (energies, angular momenta, orbital frequencies,
   ISCO radii, photon orbit radii, Schwarzschild limit a -> 0, spin-reversal symmetry a -> -a, and M-scaling).
2. VAL-KERR-CIRC-02: Input validation and rejection of unphysical configurations (extremal/super-extremal
   spins |a| >= M, radii inside equatorial photon orbit r <= r_ph, invalid orientations).
3. VAL-KERR-CIRC-03: Mass-shell constraint preservation H = -0.5 for unperturbed and perturbed initial states.
4. VAL-KERR-CIRC-04: Multi-period numerical trajectory integration of prograde and retrograde circular orbits.
5. VAL-KERR-CIRC-05: Radial stability analysis distinguishing stable epicyclic motion outside ISCO
   from plunge inside ISCO.
6. VAL-KERR-CIRC-06: Tolerance refinement robustness across rtol=atol in [1e-8, 1e-10, 1e-12].
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
from geodesics.events import horizon_cutoff_event
from geodesics.hamiltonian import (
    hamiltonian_rhs,
    hamiltonian_value,
)
from geodesics.initial_conditions import (
    kerr_circular_orbital_frequency,
    kerr_circular_timelike_angular_momentum,
    kerr_circular_timelike_energy,
    kerr_circular_timelike_initial_state,
    kerr_equatorial_photon_orbit_radius,
    kerr_isco_radius,
    kerr_perturbed_circular_timelike_initial_state,
    kerr_proper_radial_distance_horizon_to_isco,
    kerr_radial_epicyclic_frequency,
    schwarzschild_circular_orbital_frequency,
    schwarzschild_circular_timelike_angular_momentum,
    schwarzschild_circular_timelike_energy,
)
from geodesics.integrator import integrate_geodesic
from geodesics.metrics.kerr import KerrMetric


# =============================================================================
# 1. Analytic Formula Verification & Limiting Cases
# =============================================================================


class TestKerrAnalyticFormulas:
    """Verifies analytic expressions for Kerr equatorial circular orbits, photon orbits, and ISCO."""

    @pytest.mark.parametrize(
        ("spin", "expected_pro", "expected_retro"),
        [
            (0.0, 6.0, 6.0),
            (0.5, 4.233003, 7.554585),
            (0.9, 2.320883, 8.717352),
            (0.99, 1.454498, 8.971861),
        ],
    )
    def test_kerr_isco_radius_benchmark_values(
        self, spin: float, expected_pro: float, expected_retro: float
    ) -> None:
        """Verifies ISCO radius for prograde and retrograde orbits against reference values."""
        mass = 1.0
        metric = KerrMetric(mass=mass, spin=spin)

        r_pro = kerr_isco_radius(metric, prograde=True)
        r_retro = kerr_isco_radius(metric, prograde=False)

        assert np.isclose(r_pro, expected_pro, atol=1e-5)
        assert np.isclose(r_retro, expected_retro, atol=1e-5)

        # Check metric convenience methods/properties
        assert np.isclose(metric.isco_radius(prograde=True), expected_pro, atol=1e-5)
        assert np.isclose(metric.isco_radius(prograde=False), expected_retro, atol=1e-5)
        assert np.isclose(metric.isco_radius_prograde, expected_pro, atol=1e-5)
        assert np.isclose(metric.isco_radius_retrograde, expected_retro, atol=1e-5)

    @pytest.mark.parametrize("spin", [0.0, 0.3, 0.5, 0.7, 0.9, 0.99, -0.5, -0.9])
    def test_isco_polynomial_equation_residual(self, spin: float) -> None:
        """Verifies that r_ISCO satisfies the exact polynomial equation:

        r^2 - 6*M*r + 8*s*a*sqrt(M*r) - 3*a^2 == 0.
        """
        mass = 1.0
        metric = KerrMetric(mass=mass, spin=spin)

        for prograde in [True, False]:
            r_isco = kerr_isco_radius(metric, prograde=prograde)
            # Determine s: for a >= 0, prograde is s=+1; for a < 0, prograde is s=-1
            if spin >= 0.0:
                s = 1 if prograde else -1
            else:
                s = -1 if prograde else 1

            residual = (
                r_isco ** 2
                - 6.0 * mass * r_isco
                + 8.0 * s * spin * np.sqrt(mass * r_isco)
                - 3.0 * (spin ** 2)
            )
            # Normalized residual relative to characteristic scale r_ISCO^2
            norm_res = abs(residual) / (r_isco ** 2)
            assert norm_res < 1e-12, f"ISCO residual {norm_res:.2e} too large for a={spin}, pro={prograde}"

    @pytest.mark.parametrize("r", [6.0, 7.0, 8.0, 10.0, 15.0])
    def test_schwarzschild_limit_reduction_at_zero_spin(self, r: float) -> None:
        """Verifies that Kerr formulas reduce identically to Schwarzschild formulas when a = 0."""
        mass = 1.0
        kerr = KerrMetric(mass=mass, spin=0.0)

        # 1. ISCO and photon orbit radii
        assert np.isclose(kerr_isco_radius(kerr, prograde=True), 6.0 * mass, atol=1e-15)
        assert np.isclose(kerr_isco_radius(kerr, prograde=False), 6.0 * mass, atol=1e-15)
        assert np.isclose(kerr_equatorial_photon_orbit_radius(kerr, prograde=True), 3.0 * mass, atol=1e-15)
        assert np.isclose(kerr_equatorial_photon_orbit_radius(kerr, prograde=False), 3.0 * mass, atol=1e-15)

        # 2. Orbital frequency
        w_kerr_pro = kerr_circular_orbital_frequency(kerr, r=r, prograde=True)
        w_kerr_retro = kerr_circular_orbital_frequency(kerr, r=r, prograde=False)
        w_schw_pro = schwarzschild_circular_orbital_frequency(r, mass=mass)
        assert np.isclose(w_kerr_pro, w_schw_pro, atol=1e-15)
        assert np.isclose(w_kerr_retro, -w_schw_pro, atol=1e-15)

        # 3. Conserved specific energy
        e_kerr_pro = kerr_circular_timelike_energy(kerr, r=r, prograde=True)
        e_kerr_retro = kerr_circular_timelike_energy(kerr, r=r, prograde=False)
        e_schw = schwarzschild_circular_timelike_energy(r, mass=mass)
        assert np.isclose(e_kerr_pro, e_schw, atol=1e-15)
        assert np.isclose(e_kerr_retro, e_schw, atol=1e-15)

        # 4. Conserved axial angular momentum
        l_kerr_pro = kerr_circular_timelike_angular_momentum(kerr, r=r, prograde=True)
        l_kerr_retro = kerr_circular_timelike_angular_momentum(kerr, r=r, prograde=False)
        l_schw_pro = schwarzschild_circular_timelike_angular_momentum(r, mass=mass, prograde=True)
        l_schw_retro = schwarzschild_circular_timelike_angular_momentum(r, mass=mass, prograde=False)
        assert np.isclose(l_kerr_pro, l_schw_pro, atol=1e-15)
        assert np.isclose(l_kerr_retro, l_schw_retro, atol=1e-15)

    @pytest.mark.parametrize("spin_mag", [0.2, 0.5, 0.8, 0.95])
    def test_spin_reversal_symmetry(self, spin_mag: float) -> None:
        """Verifies exact physical equivalence under simultaneous reversal of spin and coordinate direction."""
        mass = 1.0
        kerr_pos = KerrMetric(mass=mass, spin=+spin_mag)
        kerr_neg = KerrMetric(mass=mass, spin=-spin_mag)

        # Prograde relative to +spin has s=+1; prograde relative to -spin has s=-1
        # In both cases s*a = +spin_mag > 0
        r_isco_pro_pos = kerr_isco_radius(kerr_pos, prograde=True)
        r_isco_pro_neg = kerr_isco_radius(kerr_neg, prograde=True)
        assert np.isclose(r_isco_pro_pos, r_isco_pro_neg, atol=1e-15)

        r_isco_retro_pos = kerr_isco_radius(kerr_pos, prograde=False)
        r_isco_retro_neg = kerr_isco_radius(kerr_neg, prograde=False)
        assert np.isclose(r_isco_retro_pos, r_isco_retro_neg, atol=1e-15)

        # Photon orbit radii
        r_ph_pro_pos = kerr_equatorial_photon_orbit_radius(kerr_pos, prograde=True)
        r_ph_pro_neg = kerr_equatorial_photon_orbit_radius(kerr_neg, prograde=True)
        assert np.isclose(r_ph_pro_pos, r_ph_pro_neg, atol=1e-15)

        # Conserved energy and momentum at r = 10M
        r = 10.0 * mass
        e_pos = kerr_circular_timelike_energy(kerr_pos, r=r, prograde=True)
        e_neg = kerr_circular_timelike_energy(kerr_neg, r=r, prograde=True)
        assert np.isclose(e_pos, e_neg, atol=1e-15)

        l_pos = kerr_circular_timelike_angular_momentum(kerr_pos, r=r, prograde=True)
        l_neg = kerr_circular_timelike_angular_momentum(kerr_neg, r=r, prograde=True)
        assert np.isclose(l_pos, -l_neg, atol=1e-15)

        w_pos = kerr_circular_orbital_frequency(kerr_pos, r=r, prograde=True)
        w_neg = kerr_circular_orbital_frequency(kerr_neg, r=r, prograde=True)
        assert np.isclose(w_pos, -w_neg, atol=1e-15)

    @pytest.mark.parametrize("scale", [0.5, 2.0, 5.0])
    def test_mass_scaling_invariance(self, scale: float) -> None:
        """Verifies linear scaling of radii and appropriate dimensional scaling with black hole mass M."""
        m1 = 1.0
        a1 = 0.6
        m2 = scale * m1
        a2 = scale * a1

        # ISCO and photon radii scale linearly with M
        r_isco1 = kerr_isco_radius(m1, spin=a1, prograde=True)
        r_isco2 = kerr_isco_radius(m2, spin=a2, prograde=True)
        assert np.isclose(r_isco2, scale * r_isco1, atol=1e-14)

        r_ph1 = kerr_equatorial_photon_orbit_radius(m1, spin=a1, prograde=True)
        r_ph2 = kerr_equatorial_photon_orbit_radius(m2, spin=a2, prograde=True)
        assert np.isclose(r_ph2, scale * r_ph1, atol=1e-14)

        # Dimensionless energy is scale invariant
        r1 = 8.0 * m1
        r2 = scale * r1
        e1 = kerr_circular_timelike_energy(m1, r=r1, spin=a1, prograde=True)
        e2 = kerr_circular_timelike_energy(m2, r=r2, spin=a2, prograde=True)
        assert np.isclose(e1, e2, atol=1e-14)

        # Angular momentum scales as M (dimension of length)
        l1 = kerr_circular_timelike_angular_momentum(m1, r=r1, spin=a1, prograde=True)
        l2 = kerr_circular_timelike_angular_momentum(m2, r=r2, spin=a2, prograde=True)
        assert np.isclose(l2, scale * l1, atol=1e-14)

        # Frequency scales as 1/M (dimension of 1/length)
        w1 = kerr_circular_orbital_frequency(m1, r=r1, spin=a1, prograde=True)
        w2 = kerr_circular_orbital_frequency(m2, r=r2, spin=a2, prograde=True)
        assert np.isclose(w2, w1 / scale, atol=1e-14)

    @pytest.mark.parametrize("spin", [0.2, 0.6, 0.9, -0.6])
    @pytest.mark.parametrize("prograde", [True, False])
    def test_radial_potential_circularity_conditions(self, spin: float, prograde: bool) -> None:
        """Verifies R(r_c) == 0 and R'(r_c) == 0 identically for circular orbits."""
        mass = 1.0
        metric = KerrMetric(mass=mass, spin=spin)
        r_c = kerr_isco_radius(metric, prograde=prograde) + 2.0 * mass

        energy = kerr_circular_timelike_energy(metric, r=r_c, prograde=prograde)
        lz = kerr_circular_timelike_angular_momentum(metric, r=r_c, prograde=prograde)

        def r_potential(x: float) -> float:
            delta = x * x - 2.0 * mass * x + spin * spin
            term1 = energy * (x * x + spin * spin) - spin * lz
            term2 = x * x + (lz - spin * energy) ** 2
            return float(term1 * term1 - delta * term2)

        # 1. R(r_c) == 0 to machine precision
        r_val = r_potential(r_c)
        assert abs(r_val) <= 1e-11, f"R(r_c) = {r_val:.2e} not zero"

        # 2. Central difference of R(r) at r_c == 0
        h = 1e-5
        rp_val = (r_potential(r_c + h) - r_potential(r_c - h)) / (2.0 * h)
        assert abs(rp_val) <= 1e-7, f"R'(r_c) = {rp_val:.2e} not zero"

    @pytest.mark.parametrize("spin", [0.2, 0.5, 0.8, 0.95])
    def test_marginal_stability_condition_at_isco(self, spin: float) -> None:
        """Verifies R''(r_ISCO) == 0 holding conserved quantities E, Lz fixed."""
        mass = 1.0
        metric = KerrMetric(mass=mass, spin=spin)

        for prograde in [True, False]:
            r_isco = kerr_isco_radius(metric, prograde=prograde)
            energy = kerr_circular_timelike_energy(metric, r=r_isco, prograde=prograde)
            lz = kerr_circular_timelike_angular_momentum(metric, r=r_isco, prograde=prograde)

            def r_potential(x: float) -> float:
                delta = x * x - 2.0 * mass * x + spin * spin
                term1 = energy * (x * x + spin * spin) - spin * lz
                term2 = x * x + (lz - spin * energy) ** 2
                return float(term1 * term1 - delta * term2)

            h = 1e-4
            r_double_prime = (
                r_potential(r_isco + h) - 2.0 * r_potential(r_isco) + r_potential(r_isco - h)
            ) / (h * h)
            norm_r_double_prime = abs(r_double_prime) / (r_isco ** 2)
            assert norm_r_double_prime <= 1e-4, f"R''(r_ISCO) = {norm_r_double_prime:.2e} not zero"

    @pytest.mark.parametrize("spin", [0.0, 0.2, 0.5, 0.8, 0.95, -0.6])
    def test_marginal_stability_condition_exact_analytic_derivative(self, spin: float) -> None:
        """Verifies (d^2 R / dr^2)_{E, Lz} == 0 at r_ISCO using the exact algebraic derivative formula."""
        mass = 1.0
        metric = KerrMetric(mass=mass, spin=spin)

        for prograde in [True, False]:
            r_isco = kerr_isco_radius(metric, prograde=prograde)
            E = kerr_circular_timelike_energy(metric, r=r_isco, prograde=prograde)
            Lz = kerr_circular_timelike_angular_momentum(metric, r=r_isco, prograde=prograde)

            # Exact analytical derivatives holding E, Lz fixed:
            # P = E*(r^2 + a^2) - a*Lz => P' = 2*r*E, P'' = 2*E
            # Delta = r^2 - 2Mr + a^2 => Delta' = 2(r - M), Delta'' = 2
            # K = r^2 + (Lz - aE)^2 => K' = 2r, K'' = 2
            # R''(r) = 8*(r*E)^2 + 4*E*P - 2*K - 8*r*(r - M) - 2*Delta
            P = E * (r_isco ** 2 + spin ** 2) - spin * Lz
            K = r_isco ** 2 + (Lz - spin * E) ** 2
            delta = r_isco ** 2 - 2.0 * mass * r_isco + spin ** 2
            R_pp = 8.0 * (r_isco * E) ** 2 + 4.0 * E * P - 2.0 * K - 8.0 * r_isco * (r_isco - mass) - 2.0 * delta

            assert abs(R_pp) <= 1e-12, f"Exact R''(r_ISCO) = {R_pp:.2e} not zero for a={spin}, pro={prograde}"

    @pytest.mark.parametrize("spin", [0.0, 0.5, 0.9, -0.6])
    def test_radial_epicyclic_frequency_analytical_properties(self, spin: float) -> None:
        """Verifies analytical properties of radial epicyclic frequency in Kerr spacetime."""
        mass = 1.0
        metric = KerrMetric(mass=mass, spin=spin)

        for prograde in [True, False]:
            r_isco = kerr_isco_radius(metric, prograde=prograde)
            r_c = r_isco + 2.0 * mass

            # 1. Epicyclic frequency in coordinate time and proper time
            omega_coord = kerr_radial_epicyclic_frequency(
                metric, r=r_c, prograde=prograde, time_parameter="coordinate"
            )
            omega_prop = kerr_radial_epicyclic_frequency(
                metric, r=r_c, prograde=prograde, time_parameter="proper"
            )

            # 2. Conversion identity: omega_prop == u^t * omega_coord
            E = kerr_circular_timelike_energy(metric, r=r_c, prograde=prograde)
            Lz = kerr_circular_timelike_angular_momentum(metric, r=r_c, prograde=prograde)
            ginv = metric.g_contra(r_c, 0.5 * np.pi)
            u_t = -ginv[0, 0] * E + ginv[0, 3] * Lz
            assert np.isclose(omega_prop, u_t * omega_coord, rtol=1e-14)

            # 3. Direct equivalence to -R''(r_c) / (2 * r_c^4)
            P = E * (r_c ** 2 + spin ** 2) - spin * Lz
            K = r_c ** 2 + (Lz - spin * E) ** 2
            delta = r_c ** 2 - 2.0 * mass * r_c + spin ** 2
            R_pp = 8.0 * (r_c * E) ** 2 + 4.0 * E * P - 2.0 * K - 8.0 * r_c * (r_c - mass) - 2.0 * delta
            omega_from_R = np.sqrt(-R_pp / (2.0 * r_c ** 4))
            assert np.isclose(omega_prop, omega_from_R, rtol=1e-13)

            # 4. Limit at ISCO: frequency approaches zero
            with pytest.raises(ValueError):
                kerr_radial_epicyclic_frequency(metric, r=r_isco, prograde=prograde)

    def test_radial_epicyclic_frequency_trajectory_measurement(self) -> None:
        """Measures the epicyclic frequency from an integrated perturbed orbit and verifies agreement with analytical value."""
        mass = 1.0
        spin = 0.5
        metric = KerrMetric(mass=mass, spin=spin)
        r_c = metric.isco_radius(prograde=True) + 2.0 * mass  # ~6.233M

        omega_analytical = kerr_radial_epicyclic_frequency(
            metric, r=r_c, prograde=True, time_parameter="proper"
        )
        T_expected = 2.0 * np.pi / omega_analytical

        # Perturb with small delta_pr = 1e-4 and integrate for 5 periods
        y0 = kerr_perturbed_circular_timelike_initial_state(
            metric, r=r_c, delta_pr=1e-4, prograde=True
        )
        tau_span = (0.0, 5.0 * T_expected)
        t_eval = np.linspace(0.0, 5.0 * T_expected, 10000)
        res = integrate_geodesic(y0, metric, tau_span, t_eval=t_eval, rtol=1e-11, atol=1e-11)
        assert res.success is True

        # Detect radial turning points (peaks of r(tau))
        peaks = [i for i in range(1, len(res.r) - 1) if res.r[i] > res.r[i-1] and res.r[i] > res.r[i+1]]
        peak_times = res.lambdas[peaks]
        measured_periods = np.diff(peak_times)
        measured_T = float(np.mean(measured_periods))
        measured_omega = 2.0 * np.pi / measured_T

        rel_err = abs(measured_omega - omega_analytical) / omega_analytical
        assert rel_err < 1e-4, f"Measured omega = {measured_omega}, analytical = {omega_analytical}, rel_err = {rel_err}"

    def test_proper_radial_distance_horizon_to_isco_quadrature_and_asymptotics(self) -> None:
        """Verifies proper radial distance integral via regularized quadrature, analytic antiderivative, and logarithmic divergence."""
        from scipy.integrate import quad

        mass = 1.0
        spins = [0.0, 0.5, 0.9, 0.99, 0.999, 0.9999, 0.99999, 0.999999]

        for a in spins:
            metric = KerrMetric(mass=mass, spin=a)
            val_analytic = metric.proper_radial_distance_horizon_to_isco(prograde=True)

            # Numerical quadrature with endpoint-regularizing substitution: r - r_+ = u^2 => dr = 2u du
            r_plus = metric.horizon_radius
            r_minus = metric.inner_horizon_radius
            r_isco = metric.isco_radius(prograde=True)
            diff = r_plus - r_minus
            u_max = np.sqrt(r_isco - r_plus)

            def regularized_integrand(u: float) -> float:
                return float(2.0 * (r_plus + u * u) / np.sqrt(u * u + diff))

            val_quad, err_quad = quad(regularized_integrand, 0.0, u_max, epsabs=1e-13, epsrel=1e-13)

            # Verify analytical formula agrees with quadrature to <= 1e-12
            assert abs(val_analytic - val_quad) <= 1e-12

            # Check Schwarzschild exact limit at a=0: 2*sqrt(6) + ln(5 + 2*sqrt(6))
            if a == 0.0:
                expected_schw = 2.0 * np.sqrt(24.0) / 2.0 + np.log(5.0 + np.sqrt(24.0))
                assert np.isclose(val_analytic, expected_schw, atol=1e-14)

        # Verify logarithmic divergence towards extremality:
        # As 1 - a -> 0, Delta_ell diverges as M * (4/3 ln 2 + 1/6 ln(1 / (1 - a^2)))
        dists = [
            KerrMetric(mass=mass, spin=1.0 - 10.0**(-p)).proper_radial_distance_horizon_to_isco(prograde=True)
            for p in [4, 6, 8, 10]
        ]
        # Distances must monotonically increase towards extremality
        assert dists[0] < dists[1] < dists[2] < dists[3]
        # At 1 - a = 1e-10, distance exceeds 4.6M
        assert dists[3] > 4.6 * mass


# =============================================================================
# 2. Input Validation and Domain Enforcement
# =============================================================================


class TestKerrInputValidation:
    """Verifies strict error handling for unphysical parameters and coordinates."""

    def test_rejection_of_extremal_and_superextremal_spins(self) -> None:
        """Rejects spins |a| >= M with descriptive ValueError."""
        mass = 1.0
        with pytest.raises(ValueError, match="sub-extremal Kerr metric"):
            kerr_isco_radius(mass, spin=1.0)
        with pytest.raises(ValueError, match="sub-extremal Kerr metric"):
            kerr_circular_orbital_frequency(mass, r=6.0, spin=1.2)
        with pytest.raises(ValueError, match="sub-extremal Kerr metric"):
            kerr_circular_timelike_energy(mass, r=6.0, spin=-1.0)

    def test_rejection_of_radii_inside_photon_orbit(self) -> None:
        """Rejects radii r <= r_ph for timelike circular orbits."""
        mass = 1.0
        kerr = KerrMetric(mass=mass, spin=0.5)
        r_ph_pro = kerr.photon_orbit_radius_prograde  # ~2.347M

        with pytest.raises(ValueError, match="require r > r_ph"):
            kerr_circular_timelike_energy(kerr, r=r_ph_pro, prograde=True)
        with pytest.raises(ValueError, match="require r > r_ph"):
            kerr_circular_timelike_energy(kerr, r=2.0 * mass, prograde=True)
        with pytest.raises(ValueError, match="require r > r_ph"):
            kerr_circular_timelike_angular_momentum(kerr, r=r_ph_pro, prograde=True)
        with pytest.raises(ValueError, match="require r > r_ph"):
            kerr_circular_orbital_frequency(kerr, r=r_ph_pro, prograde=True)

    def test_rejection_of_invalid_direction_parameter(self) -> None:
        """Rejects s values other than +1 or -1."""
        mass = 1.0
        with pytest.raises(ValueError, match="must be \\+1 or -1"):
            kerr_isco_radius(mass, spin=0.5, s=0)
        with pytest.raises(ValueError, match="must be \\+1 or -1"):
            kerr_circular_timelike_energy(mass, r=8.0, spin=0.5, s=2)


# =============================================================================
# 3. Initial State Construction & Mass-Shell Preservation
# =============================================================================


class TestKerrCircularInitialStates:
    """Verifies canonical 8-component initial state generation and exact constraint preservation."""

    @pytest.mark.parametrize("spin", [0.0, 0.5, 0.9, -0.5, -0.9])
    @pytest.mark.parametrize("prograde", [True, False])
    def test_exact_circular_initial_state_mass_shell_and_flow(
        self, spin: float, prograde: bool
    ) -> None:
        """Verifies mass-shell constraint H = -0.5 and vanishing radial/polar phase-space velocity."""
        mass = 1.0
        metric = KerrMetric(mass=mass, spin=spin)
        r_c = metric.isco_radius(prograde=prograde) + 2.0 * mass

        y0 = kerr_circular_timelike_initial_state(metric, r=r_c, prograde=prograde)

        # Coordinates
        assert y0[IDX_R] == r_c
        assert y0[IDX_THETA] == 0.5 * np.pi
        assert y0[5] == 0.0  # p_r == 0
        assert y0[6] == 0.0  # p_theta == 0

        # Mass-shell constraint: H(y0) == -0.5 to machine precision
        h0 = hamiltonian_value(y0[:4], y0[4:], metric)
        assert abs(h0 - (-0.5)) <= 5e-16

        # Phase-space flow vanishing
        rhs = hamiltonian_rhs(y0, metric)
        assert abs(rhs[IDX_R]) <= 1e-15, f"dr/dtau should be 0, got {rhs[IDX_R]}"
        assert abs(rhs[5]) <= 1e-14, f"dp_r/dtau should be 0, got {rhs[5]}"
        assert abs(rhs[IDX_THETA]) <= 1e-15, f"dtheta/dtau should be 0, got {rhs[IDX_THETA]}"
        assert abs(rhs[6]) <= 1e-14, f"dp_theta/dtau should be 0, got {rhs[6]}"

        # Coordinate-time frequency: (dphi/dtau) / (dt/dtau) == Omega_phi
        omega_num = rhs[IDX_PHI] / rhs[IDX_X0]
        omega_analytic = kerr_circular_orbital_frequency(metric, r=r_c, prograde=prograde)
        assert np.isclose(omega_num, omega_analytic, atol=1e-14)

    @pytest.mark.parametrize("spin", [0.0, 0.5, 0.9, -0.5, -0.9])
    @pytest.mark.parametrize("delta_pr", [-1e-3, 1e-4, 1e-3, 5e-3])
    def test_perturbed_initial_state_preserves_mass_shell(
        self, spin: float, delta_pr: float
    ) -> None:
        """Verifies that recomputing energy E_pert strictly preserves H = -0.5 to machine precision."""
        mass = 1.0
        metric = KerrMetric(mass=mass, spin=spin)
        r_c = metric.isco_radius_prograde + 2.0 * mass

        y0_pert = kerr_perturbed_circular_timelike_initial_state(
            metric, r=r_c, delta_pr=delta_pr, prograde=True
        )
        assert y0_pert[5] == delta_pr

        h_pert = hamiltonian_value(y0_pert[:4], y0_pert[4:], metric)
        assert abs(h_pert - (-0.5)) <= 5e-16


# =============================================================================
# 4. Multi-Period Numerical Trajectory Integration
# =============================================================================


class TestKerrCircularOrbitIntegration:
    """Verifies that numerical evolution preserves circular orbits over 2 complete revolutions."""

    @pytest.mark.parametrize("spin", [0.5, 0.9, -0.5, -0.9])
    @pytest.mark.parametrize("prograde", [True, False])
    def test_circular_orbit_two_period_integration(self, spin: float, prograde: bool) -> None:
        """Integrates representative prograde and retrograde circular orbits for 2 orbital periods."""
        mass = 1.0
        metric = KerrMetric(mass=mass, spin=spin)
        r_c = metric.isco_radius(prograde=prograde) + 2.0 * mass

        Ec = kerr_circular_timelike_energy(metric, r=r_c, prograde=prograde)
        Lc = kerr_circular_timelike_angular_momentum(metric, r=r_c, prograde=prograde)
        Omega_analytic = kerr_circular_orbital_frequency(metric, r=r_c, prograde=prograde)

        # Coordinate-time period: T = 2*pi / |Omega_phi|
        T_coord = 2.0 * np.pi / abs(Omega_analytic)

        # Rate of coordinate time with proper time: dt/dtau = -g^{tt} E + g^{t phi} L_z
        g_contra = metric.g_contra(r_c, 0.5 * np.pi)
        dt_dtau = -g_contra[0, 0] * Ec + g_contra[0, 3] * Lc

        # Proper time duration for 2 full revolutions:
        tau_span = (0.0, 2.0 * T_coord / dt_dtau)

        y0 = kerr_circular_timelike_initial_state(metric, r=r_c, prograde=prograde)
        h0 = hamiltonian_value(y0[:4], y0[4:], metric)

        res = integrate_geodesic(
            initial_state=y0,
            metric=metric,
            affine_span=tau_span,
            rtol=1e-10,
            atol=1e-10,
            method="DOP853",
        )
        assert res.success is True

        # 1. Radial constancy
        max_dr = float(np.max(np.abs(res.r - r_c)))
        assert max_dr <= 1e-11, f"Radius drifted by {max_dr:.2e} at r={r_c}"

        # 2. Polar constancy (stays in equatorial plane)
        max_dth = float(np.max(np.abs(res.theta - 0.5 * np.pi)))
        assert max_dth <= 1e-12

        # 3. Conjugate momenta remain approximately zero
        max_pr = float(np.max(np.abs(res.pr)))
        max_pth = float(np.max(np.abs(res.ptheta)))
        assert max_pr <= 1e-11
        assert max_pth <= 1e-12

        # 4. Energy and angular momentum conservation
        max_de = float(np.max(np.abs(-res.states[:, 4] - Ec)))
        max_dl = float(np.max(np.abs(res.states[:, 7] - Lc)))
        assert max_de <= 1e-14
        assert max_dl <= 1e-14

        # 5. Mass-shell constraint preservation
        h_err = [abs(hamiltonian_value(s[:4], s[4:], metric) - h0) for s in res.states]
        assert max(h_err) <= 1e-13

        # 6. Measured coordinate orbital frequency
        delta_phi = res.phi[-1] - res.phi[0]
        delta_t = res.x0[-1] - res.x0[0]
        omega_num = delta_phi / delta_t
        omega_rel_err = abs(omega_num - Omega_analytic) / abs(Omega_analytic)
        assert omega_rel_err <= 1e-11


# =============================================================================
# 5. Radial Stability Validation (Outside vs. Inside ISCO)
# =============================================================================


class TestKerrPhysicalOrbitStability:
    """Verifies physical radial stability: bounded epicyclic libration outside ISCO vs. plunge inside ISCO."""

    @pytest.mark.parametrize("spin", [0.5, 0.9, -0.5, -0.9])
    @pytest.mark.parametrize("prograde", [True, False])
    def test_stable_orbit_bounded_epicyclic_motion_outside_isco(
        self, spin: float, prograde: bool
    ) -> None:
        """Applies radial perturbation delta_pr to an orbit outside ISCO and confirms bounded motion."""
        mass = 1.0
        metric = KerrMetric(mass=mass, spin=spin)
        r_c = metric.isco_radius(prograde=prograde) + 2.0 * mass
        dp = 1e-3

        y0_pert = kerr_perturbed_circular_timelike_initial_state(
            metric, r=r_c, delta_pr=dp, prograde=prograde
        )
        res = integrate_geodesic(y0_pert, metric, (0.0, 300.0), rtol=1e-10, atol=1e-10)
        assert res.success is True

        r_min = float(np.min(res.r))
        r_max = float(np.max(res.r))
        amp = r_max - r_min

        # Motion is strictly bounded near r_c
        assert amp < 0.2 * r_c
        assert abs(0.5 * (r_min + r_max) - r_c) < 0.05 * r_c

        # Conserved quantities preserved
        e0 = -y0_pert[4]
        l0 = y0_pert[7]
        assert float(np.max(np.abs(-res.states[:, 4] - e0))) <= 1e-14
        assert float(np.max(np.abs(res.states[:, 7] - l0))) <= 1e-14

    @pytest.mark.parametrize("spin", [0.5, 0.9, -0.5, -0.9])
    @pytest.mark.parametrize("prograde", [True, False])
    def test_unstable_orbit_inward_plunge_inside_isco(
        self, spin: float, prograde: bool
    ) -> None:
        """Selects a circular orbit inside ISCO (r_ph < r < r_ISCO) and confirms inward plunge."""
        mass = 1.0
        metric = KerrMetric(mass=mass, spin=spin)
        r_isco = metric.isco_radius(prograde=prograde)
        r_ph = metric.photon_orbit_radius(prograde=prograde)

        # Radius midway between photon orbit and ISCO (admits valid timelike circular orbit)
        r_u = 0.5 * (r_ph + r_isco)

        # Apply small inward kick delta_pr = -1e-3
        y0_in = kerr_perturbed_circular_timelike_initial_state(
            metric, r=r_u, delta_pr=-1e-3, prograde=prograde
        )

        cutoff = horizon_cutoff_event(metric, epsilon=0.05)
        res = integrate_geodesic(
            y0_in, metric, (0.0, 200.0), events=[cutoff], rtol=1e-10, atol=1e-10
        )

        # Unstable inward trajectory plunges into event horizon cutoff surface
        assert res.terminal_event_occurred is True
        assert res.terminal_event_name == "horizon_cutoff"
        assert res.r[-1] <= metric.horizon_radius * 1.051


# =============================================================================
# 6. Tolerance Refinement Suite
# =============================================================================


class TestKerrStabilityToleranceRobustness:
    """Verifies that Kerr stability conclusions are robust against numerical tolerances."""

    @pytest.mark.parametrize("tol", [1e-8, 1e-10, 1e-12])
    def test_kerr_prograde_stability_across_tolerances(self, tol: float) -> None:
        """Verifies bounded motion for prograde orbit at a=0.9M across tolerances."""
        mass = 1.0
        metric = KerrMetric(mass=mass, spin=0.9)
        r_c = metric.isco_radius_prograde + 2.0 * mass  # ~4.321M
        dp = 1e-3

        y0 = kerr_perturbed_circular_timelike_initial_state(
            metric, r=r_c, delta_pr=dp, prograde=True
        )
        res = integrate_geodesic(y0, metric, (0.0, 200.0), rtol=tol, atol=tol)
        assert res.success is True

        amp = float(np.max(res.r) - np.min(res.r))
        assert 0.01 < amp < 0.05
        h_err = [abs(hamiltonian_value(s[:4], s[4:], metric) - (-0.5)) for s in res.states]
        expected_bound = 1e-11 if tol >= 1e-8 else 2e-12
        assert max(h_err) <= expected_bound
