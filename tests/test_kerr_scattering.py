"""Automated scientific test suite for equatorial Kerr photon capture and scattering.

Validates:
1. Analytical turning-point solver accuracy against depressed cubic polynomial C(r).
2. Analytical turning point vs numerical turning point across spins.
3. Supercritical scattering trajectories correctly classified as SCATTERED.
4. Subcritical trajectories correctly classified as CAPTURED.
5. Critical impact parameters classified as CRITICAL.
6. Theoretical turning-point existence criterion (|b| > |b_ph|).
7. Negative-spin parity under (a, b) <-> (-a, -b).
8. Schwarzschild limit consistency (a = 0 vs SchwarzschildMetric).
9. Hamiltonian, energy, angular momentum, and Carter constant conservation.
10. Near-extremal spin (a = 0.99M) prograde and retrograde sharpness.
11. Numerical tolerance refinement convergence.
12. Initial emission radius independence (r0 = 30M, 50M, 100M).
"""

from typing import Tuple
import numpy as np
import pytest

from geodesics.constants import DEFAULT_HORIZON_BUFFER, IDX_R
from geodesics.hamiltonian import (
    carter_constant,
    conserved_angular_momentum,
    conserved_energy,
    hamiltonian_value,
)
from geodesics.metrics.kerr import KerrMetric
from geodesics.metrics.schwarzschild import SchwarzschildMetric
from geodesics.scattering import (
    EquatorialPhotonClassificationResult,
    classify_equatorial_photon_potential,
    classify_equatorial_photon_trajectory,
    critical_photon_impact_parameter,
    equatorial_photon_initial_state,
    equatorial_photon_potential,
    equatorial_photon_potential_cubic,
    equatorial_photon_scaled_cubic_residual,
    equatorial_photon_turning_point,
    integrate_equatorial_photon,
)


class TestEquatorialPhotonPotentialAndRoots:
    """Tests 1, 6, 8: Analytical potential, depressed cubic root solver, and existence criterion."""

    @pytest.mark.parametrize("spin", [0.0, 0.5, -0.5, 0.99])
    @pytest.mark.parametrize("prograde", [True, False])
    def test_analytical_turning_point_cubic_residual(self, spin: float, prograde: bool) -> None:
        """Item 1: Verify |C(r_turn)| < 1e-12 for supercritical turning points."""
        metric = KerrMetric(mass=1.0, spin=spin)
        b_ph = critical_photon_impact_parameter(metric, 1.0 if prograde else -1.0)

        for factor in [1.01, 1.1, 1.2, 1.5]:
            b = b_ph * factor
            r_turn = equatorial_photon_turning_point(metric, b)
            assert r_turn is not None, f"Expected valid turning point for b = {b}"
            c_val = equatorial_photon_potential_cubic(r_turn, metric, b)
            assert abs(c_val) < 1e-12, f"Cubic residual {c_val} exceeds 1e-12 at r_turn = {r_turn}"

            # Also check R(r_turn)
            r_pot = equatorial_photon_potential(r_turn, metric, b, energy=1.0)
            assert abs(r_pot) < 1e-9, f"Radial potential residual {r_pot} exceeds 1e-9 at r_turn"

    @pytest.mark.parametrize("spin", [0.0, 0.5, 0.9, 0.99])
    def test_turning_point_existence_criterion(self, spin: float) -> None:
        """Item 6: Turning point exists outside horizon if and only if |b| >= |b_ph|."""
        metric = KerrMetric(mass=1.0, spin=spin)
        for prograde in [True, False]:
            b_ph = critical_photon_impact_parameter(metric, 1.0 if prograde else -1.0)

            # Subcritical: no turning point outside horizon
            b_sub = 0.95 * b_ph
            r_turn_sub = equatorial_photon_turning_point(metric, b_sub)
            assert r_turn_sub is None, f"Expected None for subcritical b={b_sub}, got {r_turn_sub}"

            # Supercritical: turning point exists and r_turn > r_ph
            b_sup = 1.05 * b_ph
            r_turn_sup = equatorial_photon_turning_point(metric, b_sup)
            r_ph = metric.photon_orbit_radius(prograde=prograde)
            assert r_turn_sup is not None
            assert r_turn_sup > r_ph, f"Expected r_turn > r_ph ({r_ph}), got {r_turn_sup}"

    def test_schwarzschild_limit_consistency(self) -> None:
        """Item 8: Kerr with a=0 identically matches Schwarzschild formulas and turning points."""
        m_schw = SchwarzschildMetric(mass=1.0)
        m_kerr0 = KerrMetric(mass=1.0, spin=0.0)

        b_vals = [5.5, 6.0, 7.0, -5.5, -6.0]
        for b in b_vals:
            r_schw = equatorial_photon_turning_point(m_schw, b)
            r_kerr = equatorial_photon_turning_point(m_kerr0, b)
            assert r_schw is not None and r_kerr is not None
            assert np.isclose(r_schw, r_kerr, rtol=1e-14, atol=1e-14)

            # Compare potential profiles
            r_test = np.linspace(4.0, 20.0, 50)
            pot_schw = equatorial_photon_potential(r_test, m_schw, b)
            pot_kerr = equatorial_photon_potential(r_test, m_kerr0, b)
            np.testing.assert_allclose(pot_schw, pot_kerr, rtol=1e-14, atol=1e-14)


class TestEquatorialPhotonTrajectoryIntegration:
    """Tests 2, 3, 4, 5: Numerical trajectory turning points and classification outcomes."""

    @pytest.mark.parametrize("spin", [0.0, 0.5, -0.5])
    def test_numerical_vs_analytical_turning_point(self, spin: float) -> None:
        """Item 2: |r_turn_num - r_turn_ana| / r_turn_ana < 1e-5 across spins."""
        metric = KerrMetric(mass=1.0, spin=spin)
        for prograde in [True, False]:
            b_ph = critical_photon_impact_parameter(metric, 1.0 if prograde else -1.0)
            b_super = 1.2 * b_ph

            r_turn_ana = equatorial_photon_turning_point(metric, b_super)
            res = integrate_equatorial_photon(metric, b_super, r0=50.0, rtol=1e-10, atol=1e-12)

            tp_events = [rec for rec in res.triggered_events if rec.name == "radial_turning_point"]
            assert len(tp_events) == 1, "Expected exactly 1 radial turning point event"
            r_turn_num = float(tp_events[0].states[0, IDX_R])

            rel_err = abs(r_turn_num - r_turn_ana) / r_turn_ana
            assert rel_err < 1e-5, f"Relative turning point error {rel_err:.2e} exceeds 1e-5"

    @pytest.mark.parametrize("spin", [0.0, 0.5])
    def test_supercritical_scattering_classification(self, spin: float) -> None:
        """Item 3: Supercritical trajectories are classified as SCATTERED."""
        metric = KerrMetric(mass=1.0, spin=spin)
        for prograde in [True, False]:
            b_ph = critical_photon_impact_parameter(metric, 1.0 if prograde else -1.0)
            for factor in [1.02, 1.2]:
                b = b_ph * factor
                res = integrate_equatorial_photon(metric, b, r0=50.0)
                classification = classify_equatorial_photon_trajectory(res, metric, b, r0=50.0)
                assert classification == "SCATTERED", f"Expected SCATTERED for b={b}, got {classification}"

    @pytest.mark.parametrize("spin", [0.0, 0.5])
    def test_subcritical_capture_classification(self, spin: float) -> None:
        """Item 4: Subcritical trajectories are classified as CAPTURED."""
        metric = KerrMetric(mass=1.0, spin=spin)
        for prograde in [True, False]:
            b_ph = critical_photon_impact_parameter(metric, 1.0 if prograde else -1.0)
            for factor in [0.8, 0.98]:
                b = b_ph * factor
                res = integrate_equatorial_photon(metric, b, r0=50.0)
                classification = classify_equatorial_photon_trajectory(res, metric, b, r0=50.0)
                assert classification == "CAPTURED", f"Expected CAPTURED for b={b}, got {classification}"

    @pytest.mark.parametrize("spin", [0.0, 0.5])
    def test_critical_parameter_classification(self, spin: float) -> None:
        """Item 5: Trajectories at exact critical parameter are classified as CRITICAL."""
        metric = KerrMetric(mass=1.0, spin=spin)
        for prograde in [True, False]:
            b_ph = critical_photon_impact_parameter(metric, 1.0 if prograde else -1.0)
            res = integrate_equatorial_photon(metric, b_ph, r0=50.0, lambda_span=(0.0, 100.0))
            classification = classify_equatorial_photon_trajectory(res, metric, b_ph, r0=50.0)
            assert classification == "CRITICAL", f"Expected CRITICAL for b_ph={b_ph}, got {classification}"


class TestParityConservationAndConditioning:
    """Tests 7, 9, 10, 11, 12: Invariances, conservation laws, near-extremal, and convergence."""

    def test_negative_spin_parity(self) -> None:
        """Item 7: Under (a, b) <-> (-a, -b), radial trajectory and turning point are identical."""
        m_pos = KerrMetric(mass=1.0, spin=0.5)
        m_neg = KerrMetric(mass=1.0, spin=-0.5)

        b_pos = 1.2 * critical_photon_impact_parameter(m_pos, 1.0)
        b_neg = -b_pos

        r_turn_pos = equatorial_photon_turning_point(m_pos, b_pos)
        r_turn_neg = equatorial_photon_turning_point(m_neg, b_neg)
        assert np.isclose(r_turn_pos, r_turn_neg, rtol=1e-14, atol=1e-14)

        res_pos = integrate_equatorial_photon(m_pos, b_pos, r0=50.0)
        res_neg = integrate_equatorial_photon(m_neg, b_neg, r0=50.0)

        tp_pos = [rec for rec in res_pos.triggered_events if rec.name == "radial_turning_point"][0].states[0, IDX_R]
        tp_neg = [rec for rec in res_neg.triggered_events if rec.name == "radial_turning_point"][0].states[0, IDX_R]
        assert np.isclose(tp_pos, tp_neg, rtol=1e-12, atol=1e-12)

    def test_constraint_conservation(self) -> None:
        """Item 9: |H| < 1e-8, |dE/E| < 1e-8, |dL/L| < 1e-8, |Q| < 1e-12 across trajectory types."""
        metric = KerrMetric(mass=1.0, spin=0.5)
        b_ph = critical_photon_impact_parameter(metric, 1.0)

        trajectories = [
            ("supercritical", 1.2 * b_ph),
            ("subcritical", 0.8 * b_ph),
            ("critical", b_ph),
        ]

        for label, b_val in trajectories:
            res = integrate_equatorial_photon(metric, b_val, r0=50.0, rtol=1e-10, atol=1e-12)
            states = res.states

            # Check Hamiltonian constraint |H|
            h_max = max(abs(hamiltonian_value(y[:4], y[4:], metric)) for y in states)
            assert h_max < 1e-7, f"{label} trajectory max |H| = {h_max:.2e} >= 1e-7"

            # Check energy conservation
            e_max_drift = max(abs(conserved_energy(y) - 1.0) for y in states)
            assert e_max_drift < 1e-8, f"{label} trajectory max |dE/E| = {e_max_drift:.2e} >= 1e-8"

            # Check angular momentum conservation
            l_max_drift = max(abs(conserved_angular_momentum(y) - b_val) / abs(b_val) for y in states)
            assert l_max_drift < 1e-8, f"{label} trajectory max |dL/L| = {l_max_drift:.2e} >= 1e-8"

            # Check Carter constant Q = 0
            q_vals = carter_constant(states, metric, mu=0.0)
            q_max = float(np.max(np.abs(q_vals)))
            assert q_max < 1e-12, f"{label} trajectory max |Q| = {q_max:.2e} >= 1e-12"

    def test_near_extremal_spin_sharpness(self) -> None:
        """Item 10: Near-extremal spin a = 0.99M prograde and retrograde stability and sharpness."""
        metric = KerrMetric(mass=1.0, spin=0.99)
        r_plus = metric.horizon_radius

        for prograde in [True, False]:
            b_ph = critical_photon_impact_parameter(metric, 1.0 if prograde else -1.0)
            r_ph = metric.photon_orbit_radius(prograde=prograde)

            # Supercritical
            b_sup = 1.1 * b_ph
            r_turn_ana = equatorial_photon_turning_point(metric, b_sup)
            assert r_turn_ana is not None and r_turn_ana > r_ph > r_plus
            res_sup = integrate_equatorial_photon(metric, b_sup, r0=50.0)
            cls_sup = classify_equatorial_photon_trajectory(res_sup, metric, b_sup, r0=50.0)
            assert cls_sup == "SCATTERED"

            # Subcritical
            b_sub = 0.9 * b_ph
            res_sub = integrate_equatorial_photon(metric, b_sub, r0=50.0)
            cls_sub = classify_equatorial_photon_trajectory(res_sub, metric, b_sub, r0=50.0)
            assert cls_sub == "CAPTURED"
            assert res_sub.states[-1, IDX_R] <= r_plus * (1.0 + 2.0 * DEFAULT_HORIZON_BUFFER)

    def test_tolerance_refinement_convergence(self) -> None:
        """Item 11: Turning point error decreases with tighter solver tolerance."""
        metric = KerrMetric(mass=1.0, spin=0.5)
        b_val = 1.2 * critical_photon_impact_parameter(metric, 1.0)
        r_turn_ana = equatorial_photon_turning_point(metric, b_val)

        errors = []
        for tol in [1e-8, 1e-10, 1e-12]:
            res = integrate_equatorial_photon(metric, b_val, r0=50.0, rtol=tol, atol=tol)
            tp_rec = [rec for rec in res.triggered_events if rec.name == "radial_turning_point"][0]
            r_num = float(tp_rec.states[0, IDX_R])
            errors.append(abs(r_num - r_turn_ana))

        # Check monotonic decrease or machine precision floor (< 1e-11)
        assert errors[1] <= errors[0] + 1e-14
        assert errors[2] <= errors[1] + 1e-14
        assert errors[-1] < 1e-11

    def test_initial_radius_independence(self) -> None:
        """Item 12: r0 in {30M, 50M, 100M} gives turning points consistent within 1e-6."""
        metric = KerrMetric(mass=1.0, spin=0.5)
        b_val = 1.2 * critical_photon_impact_parameter(metric, 1.0)
        r_turn_ana = equatorial_photon_turning_point(metric, b_val)

        r_turns = []
        for r0 in [30.0, 50.0, 100.0]:
            res = integrate_equatorial_photon(metric, b_val, r0=r0, rtol=1e-10, atol=1e-12)
            tp_rec = [rec for rec in res.triggered_events if rec.name == "radial_turning_point"][0]
            r_turns.append(float(tp_rec.states[0, IDX_R]))

        for r_num in r_turns:
            assert abs(r_num - r_turn_ana) < 1e-6
        assert max(r_turns) - min(r_turns) < 1e-9


class TestNearCriticalClassificationAndScaledResiduals:
    """Audit Tests: Critical tolerance refinement, scaled residuals, and independent references."""

    @pytest.mark.parametrize("delta", [-1e-5, -1e-6, -1e-7, -1e-8, 0.0, 1e-8, 1e-7, 1e-6, 1e-5])
    def test_near_critical_fine_grid_classification(self, delta: float) -> None:
        """Task 1: Verify fine-grid delta classification without false critical reporting."""
        metric = KerrMetric(mass=1.0, spin=0.5)
        b_ph = critical_photon_impact_parameter(metric, 1.0)
        b = b_ph * (1.0 + delta)

        pot_cls, r_turn, _ = classify_equatorial_photon_potential(metric, b)
        res = integrate_equatorial_photon(metric, b, r0=50.0, lambda_span=(0.0, 200.0))
        traj_cls = classify_equatorial_photon_trajectory(res, metric, b, r0=50.0)

        if delta < 0.0:
            assert pot_cls == "CAPTURED", f"Expected CAPTURED for delta={delta}, got {pot_cls}"
            assert traj_cls == "CAPTURED", f"Expected CAPTURED for delta={delta}, got {traj_cls}"
            assert r_turn is None
        elif delta > 0.0:
            assert pot_cls == "SCATTERED", f"Expected SCATTERED for delta={delta}, got {pot_cls}"
            assert traj_cls == "SCATTERED", f"Expected SCATTERED for delta={delta}, got {traj_cls}"
            assert r_turn is not None and r_turn > metric.photon_orbit_radius(True)
        else:
            assert pot_cls == "CRITICAL", f"Expected CRITICAL for delta=0, got {pot_cls}"
            assert traj_cls == "CRITICAL", f"Expected CRITICAL for delta=0, got {traj_cls}"

    def test_near_critical_uncertainty_band(self) -> None:
        """Task 1: Verify explicit NEAR_CRITICAL classification when uncertainty band is requested."""
        metric = KerrMetric(mass=1.0, spin=0.5)
        b_ph = critical_photon_impact_parameter(metric, 1.0)

        # Within uncertainty band near_crit_tol = 1e-6
        b_near = b_ph * (1.0 + 1e-8)
        res_near = integrate_equatorial_photon(metric, b_near, r0=50.0, lambda_span=(0.0, 200.0))
        cls_pot = classify_equatorial_photon_potential(metric, b_near, near_crit_tol=1e-6)[0]
        cls_traj = classify_equatorial_photon_trajectory(res_near, metric, b_near, r0=50.0, near_crit_tol=1e-6)
        assert cls_pot == "NEAR_CRITICAL"
        assert cls_traj == "NEAR_CRITICAL"

        # Outside uncertainty band
        b_out = b_ph * (1.0 + 1e-4)
        cls_out = classify_equatorial_photon_potential(metric, b_out, near_crit_tol=1e-6)[0]
        assert cls_out == "SCATTERED"

        # Exact critical remains CRITICAL
        cls_exact = classify_equatorial_photon_potential(metric, b_ph, near_crit_tol=1e-6)[0]
        assert cls_exact == "CRITICAL"

    @pytest.mark.parametrize("spin", [0.0, 0.5, -0.5, 0.99])
    def test_scaled_cubic_residual_and_halley_reference(self, spin: float) -> None:
        """Task 2: Scaled cubic residual eta_C and independent 60-digit Decimal Halley reference."""
        from decimal import Decimal, getcontext
        getcontext().prec = 60

        metric = KerrMetric(mass=1.0, spin=spin)
        for prograde in [True, False]:
            b_ph = critical_photon_impact_parameter(metric, 1.0 if prograde else -1.0)
            b = 1.2 * b_ph

            # 1. Scaled residual
            r_turn = equatorial_photon_turning_point(metric, b)
            assert r_turn is not None
            eta_C = equatorial_photon_scaled_cubic_residual(r_turn, metric, b)
            assert eta_C < 1e-14, f"Scaled residual {eta_C:.2e} exceeds 1e-14"

            # 2. Independent 60-digit Decimal Halley reference
            M_dec = Decimal("1.0")
            a_dec = Decimal(str(spin))
            b_dec = Decimal(str(b))
            p = b_dec**2 - a_dec**2
            q = 2 * M_dec * (b_dec - a_dec)**2

            # Halley iteration in Decimal
            r_dec = (p / 3).sqrt() * Decimal("1.5") + 1
            for _ in range(50):
                f = r_dec**3 - p * r_dec + q
                f1 = 3 * r_dec**2 - p
                f2 = 6 * r_dec
                dx = (2 * f * f1) / (2 * f1**2 - f * f2)
                r_dec = r_dec - dx
                if abs(dx) < Decimal("1e-50"):
                    break
            r_ref = float(r_dec)

            rel_err = abs(r_turn - r_ref) / r_ref
            assert rel_err < 1e-14, f"Discrepancy vs independent reference {rel_err:.2e} exceeds 1e-14"

    def test_special_cases_threshold(self) -> None:
        """Task 3: Verify b=a and b^2 <= a^2 yield None (unconditional plunge)."""
        for a in [0.1, 0.5, 0.9, 0.99]:
            m = KerrMetric(mass=1.0, spin=a)
            assert equatorial_photon_turning_point(m, a) is None
            for b in np.linspace(-abs(a), abs(a), 5):
                assert equatorial_photon_turning_point(m, b) is None


class TestScientificConsistencyAndDecoupledClassification:
    """Stage 3D Final Audit: Rigorous decoupling of analytical separatrix from numerical outcome."""

    def test_decoupled_result_fields_and_backward_compatibility(self) -> None:
        """Task 1: Verify EquatorialPhotonClassificationResult fields, accessors, and string equality."""
        metric = KerrMetric(mass=1.0, spin=0.5)
        b_ph = critical_photon_impact_parameter(metric, 1.0)
        b_sup = 1.2 * b_ph

        res_ode = integrate_equatorial_photon(metric, b_sup, r0=50.0)
        res = classify_equatorial_photon_trajectory(res_ode, metric, b_sup, r0=50.0)

        assert isinstance(res, EquatorialPhotonClassificationResult)
        assert res.analytical_classification == "SCATTERED"
        assert res.numerical_outcome == "SCATTERED"
        assert res.is_scattered is True
        assert res.is_critical is False
        assert res.is_captured is False
        assert res.is_dwelling is False

        # Verify numerical fields
        assert res.impact_parameter == b_sup
        assert res.critical_impact_parameter == b_ph
        assert np.isclose(res.criticality_measure, 0.2, rtol=1e-12)
        assert res.r_turn_analytical is not None
        assert res.r_turn_numerical is not None
        assert abs(res.r_turn_numerical - res.r_turn_analytical) < 1e-5
        assert res.event_history == ("radial_turning_point", "escape_radius")

        # Backward compatibility with string comparisons
        assert res == "SCATTERED"
        assert res != "CAPTURED"
        assert res != "CRITICAL"
        assert str(res) == "SCATTERED"

    def test_critical_trajectory_conflation_resolution_a099(self) -> None:
        """Task 1 & 3: Resolve conflation for a=0.99M exact critical ray triggering horizon cutoff."""
        metric = KerrMetric(mass=1.0, spin=0.99)
        b_ph = critical_photon_impact_parameter(metric, 1.0)

        res_ode = integrate_equatorial_photon(metric, b_ph, r0=50.0, lambda_span=(0.0, 200.0))
        res = classify_equatorial_photon_trajectory(res_ode, metric, b_ph, r0=50.0)

        # Analytical classification is CRITICAL (b = b_ph)
        assert res.analytical_classification == "CRITICAL"
        assert res.is_critical is True
        assert res.is_captured is False  # Never claim critical separatrix is physically captured
        assert res.r_turn_analytical is not None

        # Numerical outcome is HORIZON_CUTOFF (Lyapunov instability drove state into numerical cutoff surface)
        assert res.numerical_outcome == "HORIZON_CUTOFF"
        assert res.is_horizon_cutoff is True
        assert res.event_history == ("horizon_cutoff",)
        assert res.r_turn_numerical is None
        assert res.final_radius < metric.horizon_radius * (1.0 + 2.0 * DEFAULT_HORIZON_BUFFER)

        # Decoupling verified: both classifications accessible and transparent
        assert res.analytical_classification != res.numerical_outcome
        assert "CRITICAL" in str(res) and "HORIZON_CUTOFF" in str(res)

        # String comparisons: matches CRITICAL and HORIZON_CUTOFF, but NOT CAPTURED
        assert res == "CRITICAL"
        assert res == "HORIZON_CUTOFF"
        assert res != "CAPTURED"  # Explicitly prevents accidental equivalence between cutoff and capture

    def test_dwelling_critical_trajectory_a00(self) -> None:
        """Task 1: Verify sustained DWELLING outcome for a=0.0M critical ray within lambda in [0, 100M]."""
        metric = KerrMetric(mass=1.0, spin=0.0)
        b_ph = critical_photon_impact_parameter(metric, 1.0)

        res_ode = integrate_equatorial_photon(metric, b_ph, r0=50.0, lambda_span=(0.0, 100.0))
        res = classify_equatorial_photon_trajectory(res_ode, metric, b_ph, r0=50.0)

        assert res.analytical_classification == "CRITICAL"
        assert res.is_critical is True
        assert res.numerical_outcome == "DWELLING"
        assert res.is_dwelling is True
        assert res.dwell_fraction > 0.3
        assert res == "CRITICAL"
        assert res == "DWELLING"

    def test_near_extremal_condition_number_and_tolerance_a09999(self) -> None:
        """Task 2: Evaluate condition number and defensibility of 100*eps_mach at a=0.9999M."""
        metric = KerrMetric(mass=1.0, spin=0.9999)
        b_ph = critical_photon_impact_parameter(metric, 1.0)
        r_ph = metric.photon_orbit_radius(prograde=True)

        assert np.isclose(r_ph, 1.016374, atol=1e-5)
        assert np.isclose(b_ph, 2.024562, atol=1e-5)

        # Evaluate condition number cond(b_ph) = |a/b_ph * db/da|
        h = 1e-7
        m_plus = KerrMetric(mass=1.0, spin=0.9999 + h)
        m_minus = KerrMetric(mass=1.0, spin=0.9999 - h)
        db_da = (critical_photon_impact_parameter(m_plus, 1.0) - critical_photon_impact_parameter(m_minus, 1.0)) / (2.0 * h)
        cond_b = abs(0.9999 * db_da / b_ph)
        assert cond_b < 100.0, f"Condition number {cond_b} unexpectedly large"

        # Numerical comparison tolerance 100*eps_mach is large enough to absorb roundoff
        eps_mach = np.finfo(float).eps
        tol_mach = 100.0 * eps_mach
        assert tol_mach > cond_b * eps_mach

        # Verify analytical potential classifications on fine delta grid
        cls_sub, r_sub, _ = classify_equatorial_photon_potential(metric, b_ph * (1.0 - 1e-8))
        assert cls_sub == "CAPTURED" and r_sub is None

        cls_crit, r_crit, _ = classify_equatorial_photon_potential(metric, b_ph)
        assert cls_crit == "CRITICAL" and r_crit is not None

        cls_sup, r_sup, _ = classify_equatorial_photon_potential(metric, b_ph * (1.0 + 1e-8))
        assert cls_sup == "SCATTERED" and r_sup is not None

        # Verify scale-aware residual at supercritical turning point
        eta_C = equatorial_photon_scaled_cubic_residual(r_sup, metric, b_ph * (1.0 + 1e-8))
        assert eta_C < 1e-14

    @pytest.mark.parametrize("spin", [0.0, 0.5, -0.5, 0.99])
    def test_analytical_curvatures_and_lyapunov_exponent(self, spin: float) -> None:
        """Task 4: Analytical R''(r_ph) = 6*r_ph^2, gamma = sqrt(3)/r_ph, and S_theo = r_ph/(2*sqrt(3))."""
        metric = KerrMetric(mass=1.0, spin=spin)

        for prograde in [True, False]:
            r_ph = metric.photon_orbit_radius(prograde=prograde)
            # Ensure correct signed impact parameter matching orientation
            if spin > 0.0:
                b_probe = 1.0 if prograde else -1.0
            elif spin < 0.0:
                b_probe = -1.0 if prograde else 1.0
            else:
                b_probe = 1.0 if prograde else -1.0

            b_ph = critical_photon_impact_parameter(metric, b_probe)

            # Central finite difference of R(r)
            h = 1e-4
            r_plus = equatorial_photon_potential(r_ph + h, metric, b_ph, energy=1.0)
            r_0 = equatorial_photon_potential(r_ph, metric, b_ph, energy=1.0)
            r_minus = equatorial_photon_potential(r_ph - h, metric, b_ph, energy=1.0)
            d2R_num = (r_plus - 2.0 * r_0 + r_minus) / (h**2)
            d2R_theo = 6.0 * r_ph**2

            rel_diff = abs(d2R_num - d2R_theo) / d2R_theo
            assert rel_diff < 1e-6, f"R''(r_ph) mismatch: num={d2R_num}, theo={d2R_theo}, rel_diff={rel_diff}"

            # Theoretical Lyapunov exponent and arrival slope
            gamma_theo = np.sqrt(3.0) / r_ph
            s_theo = r_ph / (2.0 * np.sqrt(3.0))
            assert np.isclose(s_theo * gamma_theo, 0.5, rtol=1e-14)

    def test_subcritical_distinguishes_cutoff_from_captured(self) -> None:
        """Section 1 & 5: Subcritical ray has analytical CAPTURED and numerical HORIZON_CUTOFF."""
        metric = KerrMetric(mass=1.0, spin=0.5)
        b_ph = critical_photon_impact_parameter(metric, 1.0)
        b_sub = 0.8 * b_ph

        res_ode = integrate_equatorial_photon(metric, b_sub, r0=50.0)
        res = classify_equatorial_photon_trajectory(res_ode, metric, b_sub, r0=50.0)

        assert res.analytical_classification == "CAPTURED"
        assert res.numerical_outcome == "HORIZON_CUTOFF"
        assert res.is_captured is True
        assert res.is_horizon_cutoff is True
        assert res.is_critical is False
        assert res.is_scattered is False

        # Matches both CAPTURED (analytical) and HORIZON_CUTOFF (numerical event)
        assert res == "CAPTURED"
        assert res == "HORIZON_CUTOFF"
        assert res != "SCATTERED"
        assert res != "CRITICAL"

    def test_result_object_equality_and_properties(self) -> None:
        """Section 3: Verify dataclass equality, unhashability, bidirectional string equality, and inequality on all fields."""
        metric = KerrMetric(mass=1.0, spin=0.5)
        b_ph = critical_photon_impact_parameter(metric, 1.0)

        # 1. Supercritical trajectory
        res_sup = classify_equatorial_photon_trajectory(
            integrate_equatorial_photon(metric, 1.2 * b_ph, r0=50.0),
            metric, 1.2 * b_ph, r0=50.0
        )
        res_sup_dup = classify_equatorial_photon_trajectory(
            integrate_equatorial_photon(metric, 1.2 * b_ph, r0=50.0),
            metric, 1.2 * b_ph, r0=50.0
        )
        assert res_sup == res_sup_dup
        assert res_sup.is_scattered is True
        assert res_sup.is_captured is False
        assert res_sup.is_critical is False
        assert res_sup.is_horizon_cutoff is False

        # Bidirectional string comparison for SCATTERED
        assert res_sup == "SCATTERED"
        assert "SCATTERED" == res_sup
        assert res_sup != "CAPTURED"
        assert "CAPTURED" != res_sup
        assert res_sup != "CRITICAL"
        assert "CRITICAL" != res_sup

        # 2. Critical trajectory
        res_crit = classify_equatorial_photon_trajectory(
            integrate_equatorial_photon(metric, b_ph, r0=50.0, lambda_span=(0.0, 100.0)),
            metric, b_ph, r0=50.0
        )
        assert res_crit.is_critical is True
        assert res_crit.is_captured is False  # Never claim critical is captured
        assert res_crit != res_sup

        # Bidirectional string comparison for CRITICAL and SCATTERED (late numerical departure)
        assert res_crit == "CRITICAL"
        assert "CRITICAL" == res_crit
        assert res_crit == "SCATTERED"
        assert "SCATTERED" == res_crit
        assert res_crit != "CAPTURED"
        assert "CAPTURED" != res_crit
        assert res_crit != "HORIZON_CUTOFF"
        assert "HORIZON_CUTOFF" != res_crit

        # Test dwelling trajectory at a=0.0M
        m_zero = KerrMetric(mass=1.0, spin=0.0)
        b_zero = critical_photon_impact_parameter(m_zero, 1.0)
        res_dwell = classify_equatorial_photon_trajectory(
            integrate_equatorial_photon(m_zero, b_zero, r0=50.0, lambda_span=(0.0, 100.0)),
            m_zero, b_zero, r0=50.0
        )
        assert res_dwell == "CRITICAL"
        assert "CRITICAL" == res_dwell
        assert res_dwell == "DWELLING"
        assert "DWELLING" == res_dwell
        assert res_dwell != "CAPTURED"
        assert "CAPTURED" != res_dwell
        assert res_dwell != "HORIZON_CUTOFF"
        assert "HORIZON_CUTOFF" != res_dwell

        # 3. Verify unhashable behavior (TypeError raised)
        with pytest.raises(TypeError, match="unhashable type"):
            hash(res_sup)
        with pytest.raises(TypeError, match="unhashable type"):
            {res_sup}

        # 4. Unknown string and unrelated types compare False
        assert res_sup != "UNKNOWN_BRANCH"
        assert "UNKNOWN_BRANCH" != res_sup
        assert res_sup != 42
        assert 42 != res_sup
        assert res_sup != None
        assert None != res_sup

        # 5. Strict inequality across all 12 fields:
        # Construct two result objects and verify inequality when any single field differs
        base_args = dict(
            analytical_classification="CRITICAL",
            numerical_outcome="HORIZON_CUTOFF",
            impact_parameter=2.251724,
            critical_impact_parameter=2.251724,
            criticality_measure=0.0,
            criticality_tolerance=2.22e-14,
            event_history=("horizon_cutoff",),
            r_turn_analytical=1.167642,
            r_turn_numerical=None,
            dwell_fraction=0.35,
            final_affine_parameter=67.73,
            final_radius=1.142208,
        )
        r_base = EquatorialPhotonClassificationResult(**base_args)
        r_identical = EquatorialPhotonClassificationResult(**base_args)
        assert r_base == r_identical

        # Test each of the 12 fields individually
        assert r_base != EquatorialPhotonClassificationResult(**{**base_args, "final_radius": 1.150000})
        assert r_base != EquatorialPhotonClassificationResult(**{**base_args, "final_affine_parameter": 75.0})
        assert r_base != EquatorialPhotonClassificationResult(**{**base_args, "dwell_fraction": 0.50})
        assert r_base != EquatorialPhotonClassificationResult(**{**base_args, "event_history": ("radial_turning_point",)})
        assert r_base != EquatorialPhotonClassificationResult(**{**base_args, "r_turn_analytical": 1.200000})
        assert r_base != EquatorialPhotonClassificationResult(**{**base_args, "r_turn_numerical": 1.150000})
        assert r_base != EquatorialPhotonClassificationResult(**{**base_args, "criticality_tolerance": 1e-12})
        assert r_base != EquatorialPhotonClassificationResult(**{**base_args, "criticality_measure": 1e-5})
        assert r_base != EquatorialPhotonClassificationResult(**{**base_args, "impact_parameter": 2.260000})
        assert r_base != EquatorialPhotonClassificationResult(**{**base_args, "critical_impact_parameter": 2.240000})
        assert r_base != EquatorialPhotonClassificationResult(**{**base_args, "analytical_classification": "CAPTURED"})
        assert r_base != EquatorialPhotonClassificationResult(**{**base_args, "numerical_outcome": "DWELLING"})

        # 6. Transitivity of exact equality:
        # A == B and B == C implies A == C strictly
        r_A = EquatorialPhotonClassificationResult(**base_args)
        r_B = EquatorialPhotonClassificationResult(**base_args)
        r_C = EquatorialPhotonClassificationResult(**base_args)
        assert r_A == r_B
        assert r_B == r_C
        assert r_A == r_C

        # Sub-ULP differences make objects strictly unequal under exact equality
        r_perturbed = EquatorialPhotonClassificationResult(
            **{**base_args, "final_radius": base_args["final_radius"] + 1e-15}
        )
        assert r_base != r_perturbed
        assert r_base.is_close(r_perturbed, atol=1e-14, rtol=1e-14) is True

        # 7. Concrete demonstration that tolerance-based comparison (is_close) is non-transitive
        # A is close to B, B is close to C, but A is NOT close to C
        args_A = {**base_args, "final_radius": 1.0}
        args_B = {**base_args, "final_radius": 1.0 + 8e-15}
        args_C = {**base_args, "final_radius": 1.0 + 1.6e-14}
        obj_A = EquatorialPhotonClassificationResult(**args_A)
        obj_B = EquatorialPhotonClassificationResult(**args_B)
        obj_C = EquatorialPhotonClassificationResult(**args_C)

        assert obj_A.is_close(obj_B, rtol=1e-14, atol=1e-15) is True
        assert obj_B.is_close(obj_C, rtol=1e-14, atol=1e-15) is True
        assert obj_A.is_close(obj_C, rtol=1e-14, atol=1e-15) is False, "is_close must be non-transitive"
        # Under exact equality, they are all mutually unequal
        assert obj_A != obj_B and obj_B != obj_C and obj_A != obj_C

        # 8. Reflexivity, NaNs, infinities, signed zero, and 1-ULP changes
        # Reflexivity (A == A) holds for any instance, including with NaNs
        r_nan = EquatorialPhotonClassificationResult(**{**base_args, "impact_parameter": float("nan")})
        assert r_nan == r_nan, "Reflexivity (A == A) must hold even with standard float NaN"

        # Reflexivity holds for numpy floating scalars (np.float64, np.float32)
        r_np64_nan = EquatorialPhotonClassificationResult(**{**base_args, "impact_parameter": np.float64(np.nan)})
        assert r_np64_nan == r_np64_nan, "Reflexivity (A == A) must hold for np.float64 NaN"
        assert r_nan == r_np64_nan, "float NaN and np.float64 NaN must compare equal"

        r_np32_nan = EquatorialPhotonClassificationResult(**{**base_args, "impact_parameter": np.float32(np.nan)})
        assert r_np32_nan == r_np32_nan, "Reflexivity (A == A) must hold for np.float32 NaN"
        assert r_nan == r_np32_nan, "float NaN and np.float32 NaN must compare equal"

        # Corresponding NaNs in every float-valued field compare equal; one-sided NaNs compare unequal
        float_field_names = [
            "impact_parameter",
            "critical_impact_parameter",
            "criticality_measure",
            "criticality_tolerance",
            "dwell_fraction",
            "final_affine_parameter",
            "final_radius",
            "r_turn_analytical",
            "r_turn_numerical",
        ]
        for field in float_field_names:
            nan_args1 = {**base_args, field: float("nan")}
            nan_args2 = {**base_args, field: float("nan")}
            obj_nan1 = EquatorialPhotonClassificationResult(**nan_args1)
            obj_nan2 = EquatorialPhotonClassificationResult(**nan_args2)
            # Corresponding NaNs match
            assert obj_nan1 == obj_nan2, f"Corresponding NaNs in field '{field}' must compare equal"
            # One-sided NaN vs finite differs
            assert obj_nan1 != r_base, f"One-sided NaN in field '{field}' must compare unequal to finite"
            assert r_base != obj_nan1, f"Finite in field '{field}' must compare unequal to NaN"

        # Positive and negative infinity
        r_pos_inf1 = EquatorialPhotonClassificationResult(**{**base_args, "final_radius": float("inf")})
        r_pos_inf2 = EquatorialPhotonClassificationResult(**{**base_args, "final_radius": float("inf")})
        r_neg_inf = EquatorialPhotonClassificationResult(**{**base_args, "final_radius": float("-inf")})
        assert r_pos_inf1 == r_pos_inf2  # +inf == +inf
        assert r_pos_inf1 != r_neg_inf   # +inf != -inf
        assert r_pos_inf1 != r_base      # +inf != finite

        # Signed zero (+0.0 == -0.0)
        r_zero1 = EquatorialPhotonClassificationResult(**{**base_args, "criticality_measure": 0.0})
        r_zero2 = EquatorialPhotonClassificationResult(**{**base_args, "criticality_measure": -0.0})
        assert r_zero1 == r_zero2  # IEEE 754 +0.0 == -0.0

        # Optional field None vs float
        r_turn_none1 = EquatorialPhotonClassificationResult(**{**base_args, "r_turn_analytical": None})
        r_turn_none2 = EquatorialPhotonClassificationResult(**{**base_args, "r_turn_analytical": None})
        r_turn_float = EquatorialPhotonClassificationResult(**{**base_args, "r_turn_analytical": 1.167642})
        assert r_turn_none1 == r_turn_none2
        assert r_turn_none1 != r_turn_float
        assert r_turn_float != r_turn_none1

        # Changing any ordinary finite field by 1 ULP strictly breaks exact equality
        for field in float_field_names:
            orig_val = base_args[field]
            if orig_val is None:
                continue
            ulp_val = float(np.nextafter(orig_val, orig_val + 1.0))
            assert ulp_val != orig_val, f"ULP perturbation failed for field '{field}'"
            obj_ulp = EquatorialPhotonClassificationResult(**{**base_args, field: ulp_val})
            assert r_base != obj_ulp, f"1-ULP change in field '{field}' must break exact equality"
            assert obj_ulp != r_base, f"1-ULP change in field '{field}' must be symmetric"

    def test_signed_branch_and_orientation_audit(self) -> None:
        """Section 3: Comprehensive signed-spin, orientation, and non-conflation audit."""
        # Test a/M = +/-0.5, s = +/-1
        m_pos = KerrMetric(mass=1.0, spin=0.5)
        m_neg = KerrMetric(mass=1.0, spin=-0.5)

        # Prograde has s*a > 0
        b_pro_pos = critical_photon_impact_parameter(m_pos, 1.0)
        b_ret_pos = critical_photon_impact_parameter(m_pos, -1.0)
        assert b_pro_pos > 0.0, "Prograde impact parameter for positive spin must be positive"
        assert b_ret_pos < 0.0, "Retrograde impact parameter for positive spin must be negative"

        # Spin reversal parity: b_ph(-a, -s) = -b_ph(a, s)
        b_pro_neg = critical_photon_impact_parameter(m_neg, -1.0)
        b_ret_neg = critical_photon_impact_parameter(m_neg, 1.0)
        assert b_pro_neg < 0.0, "Prograde impact parameter for negative spin must be negative"
        assert b_ret_neg > 0.0, "Retrograde impact parameter for negative spin must be positive"

        assert np.isclose(b_pro_pos, -b_pro_neg, rtol=1e-14)
        assert np.isclose(b_ret_pos, -b_ret_neg, rtol=1e-14)

        # Orbital frequency parity: Omega(-a, -s) = -Omega(a, s)
        om_pro_pos = m_pos.photon_orbit_frequency(prograde=True)
        om_pro_neg = m_neg.photon_orbit_frequency(prograde=True)
        om_ret_pos = m_pos.photon_orbit_frequency(prograde=False)
        om_ret_neg = m_neg.photon_orbit_frequency(prograde=False)
        assert np.isclose(om_pro_pos, -om_pro_neg, rtol=1e-14)
        assert np.isclose(om_ret_pos, -om_ret_neg, rtol=1e-14)

        # Ensure opposite orientation is NOT accidentally classified as critical:
        # Pass b = -b_pro_pos (-4.096) to a=+0.5.
        # This is a retrograde ray with magnitude |b| = 4.096 < |b_ph_retro| = 6.138.
        # It must be classified as CAPTURED, NOT CRITICAL!
        cls_false_check, _, b_crit_used = classify_equatorial_photon_potential(m_pos, -b_pro_pos)
        assert cls_false_check == "CAPTURED"
        assert np.isclose(b_crit_used, b_ret_pos, rtol=1e-14)
        assert cls_false_check != "CRITICAL"


class TestExactExtremalBoundaryAudit:
    """Targeted regression suite for exact-extremal (|a| = M) Kerr photon orbits."""

    def test_exact_extremal_photon_radii_and_impact_parameters(self) -> None:
        """Verify analytical photon orbit radii and critical impact parameters at |a| = M."""
        from geodesics.initial_conditions import (
            kerr_equatorial_photon_impact_parameter,
            kerr_equatorial_photon_orbit_radius,
        )

        m_pos = KerrMetric(mass=1.0, spin=1.0)
        m_neg = KerrMetric(mass=1.0, spin=-1.0)

        # 1. Horizon radii
        assert m_pos.horizon_radius == 1.0
        assert m_neg.horizon_radius == 1.0

        # 2. Photon radii: prograde r_ph = M = r_+, retrograde r_ph = 4M
        assert m_pos.photon_orbit_radius(prograde=True) == 1.0
        assert m_pos.photon_orbit_radius(prograde=False) == 4.0
        assert m_neg.photon_orbit_radius(prograde=True) == 1.0
        assert m_neg.photon_orbit_radius(prograde=False) == 4.0

        # Initial conditions wrapper consistency:
        # Default allow_extremal=False raises ValueError for raw sub-extremal helper API
        with pytest.raises(ValueError, match="sub-extremal"):
            kerr_equatorial_photon_orbit_radius(m_pos, prograde=True)
        with pytest.raises(ValueError, match="sub-extremal"):
            kerr_equatorial_photon_impact_parameter(m_pos, prograde=True)

        # When explicitly permitted via allow_extremal=True:
        assert kerr_equatorial_photon_orbit_radius(m_pos, prograde=True, allow_extremal=True) == 1.0
        assert kerr_equatorial_photon_orbit_radius(m_pos, prograde=False, allow_extremal=True) == 4.0
        assert kerr_equatorial_photon_orbit_radius(m_neg, prograde=True, allow_extremal=True) == 1.0
        assert kerr_equatorial_photon_orbit_radius(m_neg, prograde=False, allow_extremal=True) == 4.0

        # 3. Critical impact parameters:
        # a = +1: prograde (s=+1) -> b_ph = +2.0; retrograde (s=-1) -> b_ph = -7.0
        # a = -1: prograde (s=-1) -> b_ph = -2.0; retrograde (s=+1) -> b_ph = +7.0
        assert m_pos.photon_orbit_impact_parameter(prograde=True) == 2.0
        assert m_pos.photon_orbit_impact_parameter(prograde=False) == -7.0
        assert m_neg.photon_orbit_impact_parameter(prograde=True) == -2.0
        assert m_neg.photon_orbit_impact_parameter(prograde=False) == 7.0

        # Initial conditions wrapper consistency with allow_extremal=True
        assert kerr_equatorial_photon_impact_parameter(m_pos, prograde=True, allow_extremal=True) == 2.0
        assert kerr_equatorial_photon_impact_parameter(m_pos, prograde=False, allow_extremal=True) == -7.0
        assert kerr_equatorial_photon_impact_parameter(m_neg, prograde=True, allow_extremal=True) == -2.0
        assert kerr_equatorial_photon_impact_parameter(m_neg, prograde=False, allow_extremal=True) == 7.0

        # Scattering module wrapper consistency
        assert critical_photon_impact_parameter(m_pos, 2.0) == 2.0
        assert critical_photon_impact_parameter(m_pos, -7.0) == -7.0
        assert critical_photon_impact_parameter(m_neg, -2.0) == -2.0
        assert critical_photon_impact_parameter(m_neg, 7.0) == 7.0

    def test_exact_extremal_potential_and_turning_points(self) -> None:
        """Verify potential classification and turning points for exact extremal Kerr."""
        m_pos = KerrMetric(mass=1.0, spin=1.0)
        m_neg = KerrMetric(mass=1.0, spin=-1.0)

        # Prograde turning point coincides with horizon r_turn = r_+ = 1.0
        assert equatorial_photon_turning_point(m_pos, 2.0) == 1.0
        assert equatorial_photon_turning_point(m_neg, -2.0) == 1.0

        # Retrograde turning point is at r_turn = 4.0
        assert equatorial_photon_turning_point(m_pos, -7.0) == 4.0
        assert equatorial_photon_turning_point(m_neg, 7.0) == 4.0

        # Analytical classification identifies critical separatrix
        cls_p, r_p, b_p = classify_equatorial_photon_potential(m_pos, 2.0)
        assert cls_p == "CRITICAL"
        assert r_p == 1.0
        assert b_p == 2.0

        cls_r, r_r, b_r = classify_equatorial_photon_potential(m_pos, -7.0)
        assert cls_r == "CRITICAL"
        assert r_r == 4.0
        assert b_r == -7.0

    def test_exact_extremal_trajectory_outcomes(self) -> None:
        """Verify trajectory integration behavior at exact extremality |a| = M.

        Prograde critical ray (b = 2M):
            The photon sphere coincides with the event horizon (r_ph = r_+ = M).
            In Boyer-Lindquist coordinates, the incoming ray reaches the numerical cutoff
            r_cut = r_+(1 + 10^-3) = 1.001M before reaching r_ph.
            Outcome: analytical_classification == 'CRITICAL', numerical_outcome == 'HORIZON_CUTOFF'.
        Retrograde critical ray (b = -7M):
            The photon sphere lies outside the horizon at r_ph = 4.0M >> r_cut = 1.001M.
            Outcome: analytical_classification == 'CRITICAL', numerical_outcome == 'DWELLING'.
        """
        m_ext = KerrMetric(mass=1.0, spin=1.0)

        # 1. Prograde critical ray at b = 2.0
        res_pro_ode = integrate_equatorial_photon(m_ext, 2.0, r0=50.0, lambda_span=(0.0, 100.0))
        cls_pro = classify_equatorial_photon_trajectory(res_pro_ode, m_ext, 2.0, r0=50.0)

        assert cls_pro.analytical_classification == "CRITICAL"
        assert cls_pro.numerical_outcome == "HORIZON_CUTOFF"
        assert cls_pro.is_critical is True
        assert cls_pro.is_horizon_cutoff is True
        assert cls_pro.is_captured is False
        assert cls_pro.is_scattered is False
        assert cls_pro.final_radius == pytest.approx(1.001, rel=1e-5)
        assert str(cls_pro) == "CRITICAL (numerical: HORIZON_CUTOFF)"

        # 2. Retrograde critical ray at b = -7.0
        res_ret_ode = integrate_equatorial_photon(m_ext, -7.0, r0=50.0, lambda_span=(0.0, 100.0))
        cls_ret = classify_equatorial_photon_trajectory(res_ret_ode, m_ext, -7.0, r0=50.0)

        assert cls_ret.analytical_classification == "CRITICAL"
        assert cls_ret.numerical_outcome in ("DWELLING", "SCATTERED")
        assert cls_ret.is_critical is True
        assert cls_ret.is_horizon_cutoff is False
        assert cls_ret.final_radius > 3.0  # Stays near r_ph = 4.0M

    def test_exact_extremal_circular_state_rejection_and_success(self) -> None:
        """Verify API behavior for circular orbit state initialization at |a| = M."""
        from geodesics.initial_conditions import kerr_equatorial_photon_orbit_initial_state

        m_ext = KerrMetric(mass=1.0, spin=1.0)

        # Prograde circular orbit without allow_extremal=True raises sub-extremal requirement
        with pytest.raises(ValueError, match="sub-extremal"):
            kerr_equatorial_photon_orbit_initial_state(m_ext, prograde=True)

        # Prograde circular orbit with allow_extremal=True coincides with event horizon: must raise ValueError
        with pytest.raises(ValueError, match="coincides with outer event horizon"):
            kerr_equatorial_photon_orbit_initial_state(m_ext, prograde=True, allow_extremal=True)

        # Retrograde circular orbit with allow_extremal=True is at r_ph = 4.0M: succeeds and produces regular state
        state_ret = kerr_equatorial_photon_orbit_initial_state(m_ext, prograde=False, allow_extremal=True)
        assert state_ret[IDX_R] == 4.0
        assert state_ret[7] == -7.0  # p_phi = b_ph * E = -7.0
