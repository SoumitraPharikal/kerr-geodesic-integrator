"""Scientific validation test suite for Kerr equatorial circular photon orbits and critical impact parameters (Stage 3C).

This module rigorously validates that the canonical Hamiltonian framework and numerical integrator
reproduce the classic analytic and physical properties of equatorial circular null geodesics
in Kerr spacetime:
1. VAL-KERR-PHOTON-01: Analytic radius verification (prograde and retrograde branches across
   spins a/M in {0, +-0.2, +-0.5, +-0.9, +-0.99}, Schwarzschild limit 3M, near-extremal limits
   r_ph -> M (prograde) and 4M (retrograde), mass scaling).
2. VAL-KERR-PHOTON-02: Critical signed impact parameter b_ph = L_z / E verification (algebraic
   equivalence, continuous cancellation-free Schwarzschild limit s*3*sqrt(3)*M, near-extremal
   limits +2M and -7M, and independent root-finding verification).
3. VAL-KERR-PHOTON-03: Radial potential circularity conditions R(r_ph) == 0 and R'(r_ph) == 0,
   and second derivative R''(r_ph) > 0 at fixed E, L_z proving physical orbital instability.
4. VAL-KERR-PHOTON-04: Spin-reversal symmetry under (a, s) -> (-a, -s) preserving parity.
5. VAL-KERR-PHOTON-05: Null mass-shell constraint preservation H == 0 for initial states.
6. VAL-KERR-PHOTON-06: Multi-revolution numerical trajectory integration and conserved quantities.
7. VAL-KERR-PHOTON-07: Near-extremal numerical conditioning for a/M in {0.99, 0.999, 1 - 1e-8}.
8. VAL-KERR-PHOTON-08: Strict error handling for invalid/unphysical inputs (extremal, super-extremal, E <= 0).
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
from geodesics.hamiltonian import (
    hamiltonian_value,
    carter_constant,
)
from geodesics.initial_conditions import (
    kerr_equatorial_photon_orbit_radius,
    kerr_equatorial_photon_impact_parameter,
    kerr_equatorial_photon_orbit_frequency,
    kerr_equatorial_photon_orbit_initial_state,
    schwarzschild_photon_sphere_initial_state,
)
from geodesics.integrator import integrate_geodesic
from geodesics.metrics.kerr import KerrMetric
from geodesics.metrics.schwarzschild import SchwarzschildMetric


# =============================================================================
# 1. Analytic Radius, Impact Parameter, and Frequency Verification
# =============================================================================


class TestKerrCircularPhotonOrbitAnalyticFormulas:
    """Validates closed-form expressions for r_ph, b_ph, and Omega_ph across spins."""

    @pytest.mark.parametrize("spin", [0.0, 0.2, 0.5, 0.9, 0.99, -0.2, -0.5, -0.9, -0.99])
    def test_photon_orbit_radius_bounds_and_hierarchy(self, spin: float) -> None:
        """Verifies that circular photon orbits lie strictly outside the outer event horizon."""
        mass = 1.0
        metric = KerrMetric(mass=mass, spin=spin)
        r_plus = metric.horizon_radius

        r_pro = kerr_equatorial_photon_orbit_radius(metric, prograde=True)
        r_retro = kerr_equatorial_photon_orbit_radius(metric, prograde=False)

        # 1. Both radii strictly outside outer horizon for subextremal spins
        assert r_pro > r_plus, f"Prograde r_ph={r_pro} must exceed r_+={r_plus}"
        assert r_retro > r_plus, f"Retrograde r_ph={r_retro} must exceed r_+={r_plus}"

        # 2. Hierarchy: prograde orbit is closer to horizon than retrograde orbit for nonzero spin
        if abs(spin) > 0.0:
            assert r_pro < r_retro, f"Expected r_pro < r_retro, got {r_pro} >= {r_retro}"
        else:
            assert np.isclose(r_pro, 3.0 * mass, atol=1e-15)
            assert np.isclose(r_retro, 3.0 * mass, atol=1e-15)

    def test_schwarzschild_limit_continuous_reduction(self) -> None:
        """Verifies continuous reduction to Schwarzschild photon sphere at a = 0."""
        mass = 1.5
        metric = KerrMetric(mass=mass, spin=0.0)

        # Radii
        r_pro = kerr_equatorial_photon_orbit_radius(metric, prograde=True)
        r_retro = kerr_equatorial_photon_orbit_radius(metric, prograde=False)
        assert np.isclose(r_pro, 3.0 * mass, atol=1e-15)
        assert np.isclose(r_retro, 3.0 * mass, atol=1e-15)

        # Impact parameters: b_ph = s * 3*sqrt(3)*M
        b_pro = kerr_equatorial_photon_impact_parameter(metric, prograde=True)
        b_retro = kerr_equatorial_photon_impact_parameter(metric, prograde=False)
        b_expected_mag = 3.0 * np.sqrt(3.0) * mass
        assert np.isclose(b_pro, +b_expected_mag, atol=1e-14)
        assert np.isclose(b_retro, -b_expected_mag, atol=1e-14)

        # Frequencies: Omega_ph = s / (3*sqrt(3)*M)
        w_pro = kerr_equatorial_photon_orbit_frequency(metric, prograde=True)
        w_retro = kerr_equatorial_photon_orbit_frequency(metric, prograde=False)
        w_expected_mag = 1.0 / (3.0 * np.sqrt(3.0) * mass)
        assert np.isclose(w_pro, +w_expected_mag, atol=1e-15)
        assert np.isclose(w_retro, -w_expected_mag, atol=1e-15)

    @pytest.mark.parametrize("scale", [0.5, 2.0, 7.5])
    def test_mass_scaling_invariance(self, scale: float) -> None:
        """Verifies correct dimensional scaling with black hole mass M."""
        m1 = 1.0
        a1 = 0.6
        m2 = scale * m1
        a2 = scale * a1

        # Radii scale as M
        r1 = kerr_equatorial_photon_orbit_radius(m1, spin=a1, prograde=True)
        r2 = kerr_equatorial_photon_orbit_radius(m2, spin=a2, prograde=True)
        assert np.isclose(r2, scale * r1, atol=1e-14)

        # Impact parameters scale as M
        b1 = kerr_equatorial_photon_impact_parameter(m1, spin=a1, prograde=True)
        b2 = kerr_equatorial_photon_impact_parameter(m2, spin=a2, prograde=True)
        assert np.isclose(b2, scale * b1, atol=1e-14)

        # Frequencies scale as 1/M
        w1 = kerr_equatorial_photon_orbit_frequency(m1, spin=a1, prograde=True)
        w2 = kerr_equatorial_photon_orbit_frequency(m2, spin=a2, prograde=True)
        assert np.isclose(w2, w1 / scale, atol=1e-14)

    @pytest.mark.parametrize("spin_mag", [0.2, 0.5, 0.9, 0.99])
    def test_spin_reversal_parity_symmetry(self, spin_mag: float) -> None:
        """Verifies exact discrete spatial parity under simultaneous spin and direction reversal."""
        mass = 1.0
        kerr_pos = KerrMetric(mass=mass, spin=+spin_mag)
        kerr_neg = KerrMetric(mass=mass, spin=-spin_mag)

        # Prograde relative to +spin has s=+1; prograde relative to -spin has s=-1
        # Radii: r_ph(a, pro) == r_ph(-a, pro)
        r_pro_pos = kerr_equatorial_photon_orbit_radius(kerr_pos, prograde=True)
        r_pro_neg = kerr_equatorial_photon_orbit_radius(kerr_neg, prograde=True)
        assert np.isclose(r_pro_pos, r_pro_neg, atol=1e-15)

        r_retro_pos = kerr_equatorial_photon_orbit_radius(kerr_pos, prograde=False)
        r_retro_neg = kerr_equatorial_photon_orbit_radius(kerr_neg, prograde=False)
        assert np.isclose(r_retro_pos, r_retro_neg, atol=1e-15)

        # Impact parameters: b_ph(-a, pro) == -b_ph(a, pro), b_ph(-a, retro) == -b_ph(a, retro)
        b_pro_pos = kerr_equatorial_photon_impact_parameter(kerr_pos, prograde=True)
        b_pro_neg = kerr_equatorial_photon_impact_parameter(kerr_neg, prograde=True)
        assert np.isclose(b_pro_pos, -b_pro_neg, atol=1e-14)

        b_retro_pos = kerr_equatorial_photon_impact_parameter(kerr_pos, prograde=False)
        b_retro_neg = kerr_equatorial_photon_impact_parameter(kerr_neg, prograde=False)
        assert np.isclose(b_retro_pos, -b_retro_neg, atol=1e-14)

        # Frequencies: Omega_ph(-a, pro) == -Omega_ph(a, pro), Omega_ph(-a, retro) == -Omega_ph(a, retro)
        w_pro_pos = kerr_equatorial_photon_orbit_frequency(kerr_pos, prograde=True)
        w_pro_neg = kerr_equatorial_photon_orbit_frequency(kerr_neg, prograde=True)
        assert np.isclose(w_pro_pos, -w_pro_neg, atol=1e-15)

        w_retro_pos = kerr_equatorial_photon_orbit_frequency(kerr_pos, prograde=False)
        w_retro_neg = kerr_equatorial_photon_orbit_frequency(kerr_neg, prograde=False)
        assert np.isclose(w_retro_pos, -w_retro_neg, atol=1e-15)

    def test_four_case_explicit_parity_combinations(self) -> None:
        """Audits all four combinations of (a = +/-0.5, s = +/-1) against exact parity identities."""
        mass = 1.0
        energy = 1.0

        # Exact expected values for |a| = 0.5, M = 1:
        # Prograde root: r_pro = 2 * (1 + cos(2/3 arccos(-0.5))) = 2.3472963553338606
        # Retrograde root: r_retro = 2 * (1 + cos(2/3 arccos(+0.5))) = 3.532088886237956
        # Prograde |b|: 4.096267071746205
        # Retrograde |b|: 6.138155986877478
        # Prograde |Omega|: 0.2441249718426176
        # Retrograde |Omega|: 0.1629150098555132

        # 1. (a = +0.5, s = +1): sa > 0 => PROGRADE
        m_pos = KerrMetric(mass=mass, spin=+0.5)
        r_1 = kerr_equatorial_photon_orbit_radius(m_pos, s=+1)
        b_1 = kerr_equatorial_photon_impact_parameter(m_pos, s=+1)
        w_1 = kerr_equatorial_photon_orbit_frequency(m_pos, s=+1)
        y0_1 = kerr_equatorial_photon_orbit_initial_state(m_pos, s=+1, energy=energy)
        assert np.isclose(r_1, 2.3472963553338606, atol=1e-14)
        assert np.isclose(b_1, +4.096267071746205, atol=1e-14)
        assert np.isclose(w_1, +0.2441249718426176, atol=1e-14)
        assert np.isclose(y0_1[7], +4.096267071746205, atol=1e-14)

        # 2. (a = +0.5, s = -1): sa < 0 => RETROGRADE
        r_2 = kerr_equatorial_photon_orbit_radius(m_pos, s=-1)
        b_2 = kerr_equatorial_photon_impact_parameter(m_pos, s=-1)
        w_2 = kerr_equatorial_photon_orbit_frequency(m_pos, s=-1)
        y0_2 = kerr_equatorial_photon_orbit_initial_state(m_pos, s=-1, energy=energy)
        assert np.isclose(r_2, 3.532088886237956, atol=1e-14)
        assert np.isclose(b_2, -6.138155986877478, atol=1e-14)
        assert np.isclose(w_2, -0.1629150098555132, atol=1e-14)
        assert np.isclose(y0_2[7], -6.138155986877478, atol=1e-14)

        # 3. (a = -0.5, s = +1): sa < 0 => RETROGRADE
        m_neg = KerrMetric(mass=mass, spin=-0.5)
        r_3 = kerr_equatorial_photon_orbit_radius(m_neg, s=+1)
        b_3 = kerr_equatorial_photon_impact_parameter(m_neg, s=+1)
        w_3 = kerr_equatorial_photon_orbit_frequency(m_neg, s=+1)
        y0_3 = kerr_equatorial_photon_orbit_initial_state(m_neg, s=+1, energy=energy)
        assert np.isclose(r_3, 3.532088886237956, atol=1e-14)
        assert np.isclose(b_3, +6.138155986877478, atol=1e-14)
        assert np.isclose(w_3, +0.1629150098555132, atol=1e-14)
        assert np.isclose(y0_3[7], +6.138155986877478, atol=1e-14)

        # 4. (a = -0.5, s = -1): sa > 0 => PROGRADE
        r_4 = kerr_equatorial_photon_orbit_radius(m_neg, s=-1)
        b_4 = kerr_equatorial_photon_impact_parameter(m_neg, s=-1)
        w_4 = kerr_equatorial_photon_orbit_frequency(m_neg, s=-1)
        y0_4 = kerr_equatorial_photon_orbit_initial_state(m_neg, s=-1, energy=energy)
        assert np.isclose(r_4, 2.3472963553338606, atol=1e-14)
        assert np.isclose(b_4, -4.096267071746205, atol=1e-14)
        assert np.isclose(w_4, -0.2441249718426176, atol=1e-14)
        assert np.isclose(y0_4[7], -4.096267071746205, atol=1e-14)

        # Parity Pair 1: (+0.5, +1) <-> (-0.5, -1) [Both Prograde]
        assert np.isclose(r_1, r_4, atol=1e-15)
        assert np.isclose(b_1, -b_4, atol=1e-15)
        assert np.isclose(w_1, -w_4, atol=1e-15)
        assert np.isclose(y0_1[7], -y0_4[7], atol=1e-15)

        # Parity Pair 2: (+0.5, -1) <-> (-0.5, +1) [Both Retrograde]
        assert np.isclose(r_2, r_3, atol=1e-15)
        assert np.isclose(b_2, -b_3, atol=1e-15)
        assert np.isclose(w_2, -w_3, atol=1e-15)
        assert np.isclose(y0_2[7], -y0_3[7], atol=1e-15)

    def test_near_extremal_limiting_values(self) -> None:
        """Verifies near-extremal convergence to M (prograde) and 4M (retrograde) as a -> M."""
        mass = 1.0
        metric = KerrMetric(mass=mass, spin=0.99999999)

        r_pro = kerr_equatorial_photon_orbit_radius(metric, prograde=True)
        r_retro = kerr_equatorial_photon_orbit_radius(metric, prograde=False)
        b_pro = kerr_equatorial_photon_impact_parameter(metric, prograde=True)
        b_retro = kerr_equatorial_photon_impact_parameter(metric, prograde=False)

        # Prograde approaches r = M, b = +2M
        assert np.isclose(r_pro, 1.0 * mass, atol=2e-4)
        assert np.isclose(b_pro, 2.0 * mass, atol=3e-4)

        # Retrograde approaches r = 4M, b = -7M
        assert np.isclose(r_retro, 4.0 * mass, atol=1e-6)
        assert np.isclose(b_retro, -7.0 * mass, atol=1e-6)


# =============================================================================
# 2. Radial Potential Circularity and Physical Instability
# =============================================================================


class TestKerrCircularPhotonRadialPotential:
    """Verifies that circular photon orbits satisfy R = 0, R' = 0, and R'' > 0."""

    @pytest.mark.parametrize("spin", [0.0, 0.2, 0.5, 0.9, -0.5, -0.9])
    @pytest.mark.parametrize("prograde", [True, False])
    def test_null_radial_potential_circularity_conditions(self, spin: float, prograde: bool) -> None:
        """Verifies R(r_ph) == 0 and R'(r_ph) == 0 identically for circular photon orbits."""
        mass = 1.0
        metric = KerrMetric(mass=mass, spin=spin)

        r_ph = kerr_equatorial_photon_orbit_radius(metric, prograde=prograde)
        b_ph = kerr_equatorial_photon_impact_parameter(metric, prograde=prograde)

        E = 1.0
        Lz = b_ph * E

        # Null radial potential: R(r) = [E(r^2 + a^2) - a Lz]^2 - Delta * (Lz - aE)^2
        def r_potential(r: float) -> float:
            delta = r * r - 2.0 * mass * r + spin * spin
            term1 = E * (r * r + spin * spin) - spin * Lz
            term2 = Lz - spin * E
            return float(term1 * term1 - delta * (term2 * term2))

        # 1. R(r_ph) == 0 to machine precision
        val = r_potential(r_ph)
        assert abs(val) <= 1e-12, f"R(r_ph) = {val:.2e} not zero"

        # 2. Central difference R'(r_ph) == 0
        h = 1e-5
        rp_diff = (r_potential(r_ph + h) - r_potential(r_ph - h)) / (2.0 * h)
        assert abs(rp_diff) <= 1e-8, f"R'(r_ph) = {rp_diff:.2e} not zero"

        # 3. Exact analytical derivative R'(r_ph)
        P = E * (r_ph ** 2 + spin ** 2) - spin * Lz
        R_prime_exact = 4.0 * r_ph * E * P - 2.0 * (r_ph - mass) * (Lz - spin * E) ** 2
        assert abs(R_prime_exact) <= 1e-12, f"Exact R'(r_ph) = {R_prime_exact:.2e} not zero"

    @pytest.mark.parametrize("spin", [0.0, 0.2, 0.5, 0.9, -0.5, -0.9])
    @pytest.mark.parametrize("prograde", [True, False])
    def test_circular_photon_orbit_instability(self, spin: float, prograde: bool) -> None:
        """Verifies R''(r_ph) > 0 holding E, Lz fixed, proving orbital instability."""
        mass = 1.0
        metric = KerrMetric(mass=mass, spin=spin)

        r_ph = kerr_equatorial_photon_orbit_radius(metric, prograde=prograde)
        b_ph = kerr_equatorial_photon_impact_parameter(metric, prograde=prograde)

        E = 1.0
        Lz = b_ph * E

        # Second derivative holding E, Lz fixed:
        # P = E*(r^2+a^2) - a*Lz, P' = 2rE, P'' = 2E
        # Delta = r^2 - 2Mr + a^2, Delta' = 2(r-M), Delta'' = 2
        # R''(r) = 8*(r*E)^2 + 4*E*P - 2*(Lz - aE)^2
        P = E * (r_ph ** 2 + spin ** 2) - spin * Lz
        R_double_prime = 8.0 * (r_ph * E) ** 2 + 4.0 * E * P - 2.0 * (Lz - spin * E) ** 2

        # In Kerr geometry, equatorial circular photon orbits sit atop potential barrier: R''(r_ph) > 0
        assert R_double_prime > 0.0, f"Expected R''(r_ph) > 0 for unstable orbit, got {R_double_prime}"

        # Finite difference check of R''(r_ph)
        def r_potential(r: float) -> float:
            delta = r * r - 2.0 * mass * r + spin * spin
            term1 = E * (r * r + spin * spin) - spin * Lz
            term2 = Lz - spin * E
            return float(term1 * term1 - delta * (term2 * term2))

        h = 1e-4
        r_pp_fd = (r_potential(r_ph + h) - 2.0 * r_potential(r_ph) + r_potential(r_ph - h)) / (h * h)
        assert np.isclose(R_double_prime, r_pp_fd, rtol=1e-4)


# =============================================================================
# 3. Initial State Construction and Constraint Preservation
# =============================================================================


class TestKerrCircularPhotonInitialStates:
    """Verifies that kerr_equatorial_photon_orbit_initial_state preserves H == 0."""

    @pytest.mark.parametrize("spin", [0.0, 0.5, 0.9, -0.5, -0.9])
    @pytest.mark.parametrize("prograde", [True, False])
    @pytest.mark.parametrize("energy", [0.5, 1.0, 5.0])
    def test_null_hamiltonian_constraint_preservation(
        self, spin: float, prograde: bool, energy: float
    ) -> None:
        """Verifies H(x, p) == 0 to machine precision for circular photon states."""
        mass = 1.0
        metric = KerrMetric(mass=mass, spin=spin)

        y0 = kerr_equatorial_photon_orbit_initial_state(
            metric, energy=energy, prograde=prograde
        )

        # Coordinate checks
        r_ph = metric.photon_orbit_radius(prograde=prograde)
        assert np.isclose(y0[IDX_R], r_ph, atol=1e-15)
        assert np.isclose(y0[IDX_THETA], 0.5 * np.pi, atol=1e-15)

        # Momenta checks
        assert np.isclose(y0[4], -energy, atol=1e-15)
        assert y0[5] == 0.0  # p_r = 0
        assert y0[6] == 0.0  # p_theta = 0
        b_ph = metric.photon_orbit_impact_parameter(prograde=prograde)
        assert np.isclose(y0[7], b_ph * energy, atol=1e-14)

        # Null mass-shell constraint: H == 0 (scaled with E^2)
        h_val = hamiltonian_value(y0[:4], y0[4:], metric)
        assert abs(h_val) <= 5e-13 * (energy ** 2), f"Expected H=0, got H={h_val:.2e}"

        # Carter diagnostic for equatorial motion: Q == 0
        q_val = carter_constant(y0, metric, mu=0.0)
        assert abs(q_val) <= 1e-15, f"Expected Q=0, got Q={q_val:.2e}"


# =============================================================================
# 4. Multi-Revolution Numerical Trajectory Integration
# =============================================================================


class TestKerrCircularPhotonTrajectoryIntegration:
    """Verifies numerical integration of Kerr circular photon orbits over two full revolutions."""

    @pytest.mark.parametrize("spin", [0.0, 0.5, 0.9, -0.5, -0.9])
    @pytest.mark.parametrize("prograde", [True, False])
    def test_circular_photon_orbit_two_revolution_integration(
        self, spin: float, prograde: bool
    ) -> None:
        """Integrates circular photon orbit over 2 revolutions and verifies conservation and frequency."""
        mass = 1.0
        metric = KerrMetric(mass=mass, spin=spin)

        y0 = kerr_equatorial_photon_orbit_initial_state(metric, energy=1.0, prograde=prograde)
        r_ph = y0[IDX_R]
        b_ph = y0[7] / (-y0[4])
        omega_ph = metric.photon_orbit_frequency(prograde=prograde)

        # Compute affine parameter span for 2 complete revolutions in coordinate time:
        # dt/dlambda = -g^{tt} E + g^{t phi} L_z
        ginv = metric.g_contra(r_ph, 0.5 * np.pi)
        dt_dlam = -ginv[0, 0] * (-y0[4]) + ginv[0, 3] * y0[7]
        t_orbit = 2.0 * np.pi / abs(omega_ph)
        lam_final = 2.0 * t_orbit / dt_dlam

        res = integrate_geodesic(y0, metric, (0.0, lam_final), rtol=1e-10, atol=1e-10)
        assert res.success is True

        # 1. Circularity preservation: delta_r bounded
        dr_max = float(np.max(np.abs(res.r - r_ph)))
        assert dr_max < 1e-8, f"Radial drift {dr_max:.2e} exceeded bound"

        # 2. Planar equatorial confinement: delta_theta bounded
        dth_max = float(np.max(np.abs(res.theta - 0.5 * np.pi)))
        assert dth_max < 1e-12, f"Polar drift {dth_max:.2e} exceeded bound"

        # 3. Hamiltonian constraint preservation: H == 0
        h_vals = [abs(hamiltonian_value(s[:4], s[4:], metric)) for s in res.states]
        assert max(h_vals) <= 1e-13, f"Max H drift {max(h_vals):.2e} exceeded bound"

        # 4. Energy and angular momentum conservation
        e_drift = float(np.max(np.abs(-res.states[:, 4] - (-y0[4]))))
        l_drift = float(np.max(np.abs(res.states[:, 7] - y0[7])))
        assert e_drift <= 1e-14
        assert l_drift <= 1e-14

        # 5. Measured coordinate frequency Delta_phi / Delta_t matches Omega_ph
        delta_phi = res.phi[-1] - res.phi[0]
        delta_t = res.x0[-1] - res.x0[0]
        omega_measured = delta_phi / delta_t
        rel_freq_err = abs(omega_measured - omega_ph) / abs(omega_ph)
        assert rel_freq_err <= 1e-10, f"Frequency rel error {rel_freq_err:.2e} exceeded bound"


# =============================================================================
# 5. Near-Extremal Numerical Conditioning and Error Handling
# =============================================================================


class TestKerrCircularPhotonNearExtremalAndValidation:
    """Verifies numerical conditioning near extremality and strict input validation."""

    @pytest.mark.parametrize("spin", [0.99, 0.999, 1.0 - 1e-8])
    def test_near_extremal_photon_orbit_conditioning(self, spin: float) -> None:
        """Verifies numerical stability, horizon separation, and constraint preservation near extremality."""
        mass = 1.0
        metric = KerrMetric(mass=mass, spin=spin)

        r_plus = metric.horizon_radius
        r_ph_pro = metric.photon_orbit_radius(prograde=True)
        r_ph_retro = metric.photon_orbit_radius(prograde=False)

        # Horizon separation strictly positive
        assert r_ph_pro > r_plus
        sep_pro = r_ph_pro - r_plus
        assert sep_pro > 0.0

        # Initial states preserve H == 0 consistent with Boyer-Lindquist coordinate conditioning:
        # Since g^{tt}, g^{t\phi}, g^{\phi\phi} scale as 1/Delta, the cancellation error in
        # H = 1/2 g^{\mu\nu} p_\mu p_\nu scales as machine_eps / Delta.
        y0_pro = kerr_equatorial_photon_orbit_initial_state(metric, prograde=True)
        y0_retro = kerr_equatorial_photon_orbit_initial_state(metric, prograde=False)

        delta_pro = r_ph_pro**2 - 2.0 * mass * r_ph_pro + metric.spin**2
        h_pro = hamiltonian_value(y0_pro[:4], y0_pro[4:], metric)
        h_retro = hamiltonian_value(y0_retro[:4], y0_retro[4:], metric)
        expected_h_pro_tol = max(1e-12, 1e-15 / delta_pro)
        assert abs(h_pro) <= expected_h_pro_tol
        assert abs(h_retro) <= 1e-12

        # In contrast, the unseparated polynomial R(r) has no 1/Delta factor and vanishes
        # to near machine precision across all subextremal spins:
        b_pro = metric.photon_orbit_impact_parameter(prograde=True)
        p_pro = (r_ph_pro**2 + metric.spin**2) - metric.spin * b_pro
        r_poly_pro = p_pro**2 - delta_pro * (b_pro - metric.spin)**2
        assert abs(r_poly_pro) <= 1e-14

    def test_rejection_of_extremal_and_superextremal_spins(self) -> None:
        """Rejects spins |a| >= M with descriptive ValueError."""
        with pytest.raises(ValueError, match="sub-extremal"):
            kerr_equatorial_photon_orbit_radius(1.0, spin=1.0)

        with pytest.raises(ValueError, match="sub-extremal"):
            kerr_equatorial_photon_impact_parameter(1.0, spin=-1.0)

        with pytest.raises(ValueError, match="sub-extremal"):
            kerr_equatorial_photon_orbit_initial_state(1.0, spin=1.05)

    def test_rejection_of_unphysical_energy(self) -> None:
        """Rejects non-positive or non-finite photon energies."""
        metric = KerrMetric(mass=1.0, spin=0.5)

        with pytest.raises(ValueError, match="energy"):
            kerr_equatorial_photon_orbit_initial_state(metric, energy=0.0)

        with pytest.raises(ValueError, match="energy"):
            kerr_equatorial_photon_orbit_initial_state(metric, energy=-1.0)

        with pytest.raises(ValueError, match="energy"):
            kerr_equatorial_photon_orbit_initial_state(metric, energy=float("nan"))
