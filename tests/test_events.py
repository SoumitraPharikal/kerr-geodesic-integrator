"""Verification test suite for geodesic termination events (Stage 1E).

Implements rigorous scientific verification for event detection in Schwarzschild spacetime:
- VAL-EVT-01: Exterior horizon-cutoff event for inward radial null ray.
- VAL-EVT-02: Horizon-cutoff event non-triggering for outward radial ray.
- VAL-EVT-03: Escape-radius event detection for outward radial null ray.
- VAL-EVT-04: Escape-radius event non-triggering for inward radial ray.
- VAL-EVT-05: Radial turning-point detection for physical Schwarzschild null geodesic (r_peri = 6M).
- VAL-EVT-06: Non-terminal event detection allowing integration through the affine span.
- VAL-EVT-07: Terminal event halting integration at exact root lambda_event.
- VAL-EVT-08: Direction filtering (-1 inward, +1 outward, 0 bidirectional).
- VAL-EVT-09: Multiple simultaneous events (horizon, escape, turning point).
- VAL-EVT-10: Event metadata and event state preservation in triggered_events.
- VAL-EVT-11: Clean handling of events that never trigger.
- VAL-EVT-12: Robust input validation and fail-fast behavior for event classes and factories.
- VAL-EVT-13: Backward compatibility when events=None.
- VAL-EVT-14: Immutability and caller input preservation.
"""

from typing import Final, Tuple
import numpy as np
import pytest
import scipy.integrate

from geodesics.constants import (
    DEFAULT_HORIZON_BUFFER,
    DEFAULT_MASS,
    IDX_PHI,
    IDX_R,
    IDX_THETA,
    IDX_X0,
)
from geodesics.events import (
    EscapeRadiusEvent,
    GeodesicEvent,
    HorizonCutoffEvent,
    RadialTurningPointEvent,
    escape_radius_event,
    horizon_cutoff_event,
    radial_turning_point_event,
)
from geodesics.hamiltonian import STATE_DIMENSION, hamiltonian_rhs, hamiltonian_value
from geodesics.initial_conditions import null_geodesic_initial_state
from geodesics.integrator import (
    EventTriggerRecord,
    GeodesicIntegrationResult,
    integrate_geodesic,
)
from geodesics.metrics.schwarzschild import SchwarzschildMetric# =============================================================================
# Test Suite: VAL-EVT-01 (Horizon Cutoff Detection for Inward Null Ray)
# =============================================================================

class TestHorizonCutoffDetection:
    """VAL-EVT-01: Exterior horizon-cutoff event detection for inward radial null rays.

    Analytical benchmark:
    For Schwarzschild spacetime with mass M and an inward radial null ray (Lz = 0, ptheta = 0):
        dr / dlambda = -E
    With r(0) = r0 and lambda_0 = 0:
        r(lambda) = r0 - E * lambda
    The horizon cutoff surface is defined at:
        r_cut = 2M * (1 + epsilon)
    The exact affine parameter where r(lambda) = r_cut is:
        lambda_cut = (r0 - r_cut) / E = (r0 - 2M(1 + epsilon)) / E
    """

    @pytest.mark.parametrize(
        "mass,r0,energy,epsilon",
        [
            (1.0, 10.0, 1.0, 0.01),   # r_cut = 2.02, lambda_cut = (10 - 2.02)/1 = 7.98
            (1.0, 8.0, 1.5, 0.005),   # r_cut = 2.01, lambda_cut = (8 - 2.01)/1.5 = 3.993333...
            (2.0, 15.0, 0.8, 0.02),   # r_cut = 4.08, lambda_cut = (15 - 4.08)/0.8 = 13.65
        ],
    )
    def test_val_evt_01_horizon_cutoff_inward_radial_ray(
        self, mass: float, r0: float, energy: float, epsilon: float
    ) -> None:
        metric = SchwarzschildMetric(mass=mass)
        x0 = np.array([0.0, r0, np.pi / 2.0, 0.0])
        y0 = null_geodesic_initial_state(
            metric=metric,
            x=x0,
            energy=energy,
            Lz=0.0,
            radial_direction="inward",
        )

        r_cut_exact = 2.0 * mass * (1.0 + epsilon)
        lambda_cut_exact = (r0 - r_cut_exact) / energy

        ev = horizon_cutoff_event(
            mass_or_metric=metric,
            epsilon=epsilon,
            terminal=True,
            direction=-1,
        )

        result = integrate_geodesic(
            initial_state=y0,
            metric=metric,
            affine_span=(0.0, lambda_cut_exact + 5.0),
            events=[ev],
            rtol=1e-10,
            atol=1e-10,
        )

        # Solver must terminate via event
        assert result.success is True
        assert result.status == 1
        assert result.terminal_event_occurred is True
        assert result.terminal_event_name == "horizon_cutoff"
        assert result.terminal_event_index == 0
        assert result.has_events is True
        assert len(result.triggered_events) == 1

        # Check termination affine parameter and radius match analytical prediction
        lambda_term = result.lambdas[-1]
        r_term = result.r[-1]
        assert np.isclose(lambda_term, lambda_cut_exact, rtol=1e-7, atol=1e-7)
        assert np.isclose(r_term, r_cut_exact, rtol=1e-7, atol=1e-7)

        # Verify event function value at root is near machine precision
        ev_val_at_term = ev(lambda_term, result.states[-1, :])
        assert abs(ev_val_at_term) < 1e-9

        # Verify triggered record contents
        rec = result.triggered_events[0]
        assert rec.name == "horizon_cutoff"
        assert rec.event_index == 0
        assert rec.terminal is True
        assert rec.direction == -1
        assert len(rec.lambdas) == 1
        assert np.isclose(rec.lambdas[0], lambda_cut_exact, rtol=1e-7, atol=1e-7)
        assert rec.states.shape == (1, STATE_DIMENSION)
        assert np.isclose(rec.states[0, IDX_R], r_cut_exact, rtol=1e-7, atol=1e-7)# =============================================================================
# Test Suite: VAL-EVT-02 (Horizon Cutoff Non-Triggering for Outward Ray)
# =============================================================================

class TestHorizonCutoffNonTriggering:
    """VAL-EVT-02: Horizon cutoff event must not trigger for outward rays."""

    def test_val_evt_02_horizon_cutoff_outward_ray(self) -> None:
        metric = SchwarzschildMetric(mass=1.0)
        x0 = np.array([0.0, 4.0, np.pi / 2.0, 0.0])
        y0 = null_geodesic_initial_state(
            metric=metric,
            x=x0,
            energy=1.0,
            Lz=0.0,
            radial_direction="outward",
        )

        ev = horizon_cutoff_event(
            mass_or_metric=metric,
            epsilon=0.01,
            terminal=True,
            direction=-1,
        )

        result = integrate_geodesic(
            initial_state=y0,
            metric=metric,
            affine_span=(0.0, 5.0),
            events=[ev],
        )

        assert result.success is True
        assert result.status == 0
        assert result.terminal_event_occurred is False
        assert result.terminal_event_name is None
        assert result.terminal_event_index is None
        assert result.has_events is False
        assert len(result.triggered_events) == 0
        assert result.t_events is not None
        assert len(result.t_events[0]) == 0
        assert result.y_events is not None
        assert result.y_events[0].shape == (0, STATE_DIMENSION)# =============================================================================
# Test Suite: VAL-EVT-03 (Escape Radius Detection for Outward Null Ray)
# =============================================================================

class TestEscapeRadiusDetection:
    """VAL-EVT-03: Escape-radius event detection for outward radial null rays.

    Analytical benchmark:
    For an outward radial null ray with dr/dlambda = +E:
        r(lambda) = r0 + E * lambda
    Exact affine parameter where r(lambda) = r_esc:
        lambda_esc = (r_esc - r0) / E
    """

    @pytest.mark.parametrize(
        "mass,r0,energy,r_esc",
        [
            (1.0, 4.0, 1.0, 15.0),   # lambda_esc = (15 - 4)/1 = 11.0
            (1.0, 6.0, 2.0, 20.0),   # lambda_esc = (20 - 6)/2 = 7.0
            (0.5, 3.0, 0.5, 10.0),   # lambda_esc = (10 - 3)/0.5 = 14.0
        ],
    )
    def test_val_evt_03_escape_radius_outward_radial_ray(
        self, mass: float, r0: float, energy: float, r_esc: float
    ) -> None:
        metric = SchwarzschildMetric(mass=mass)
        x0 = np.array([0.0, r0, np.pi / 2.0, 0.0])
        y0 = null_geodesic_initial_state(
            metric=metric,
            x=x0,
            energy=energy,
            Lz=0.0,
            radial_direction="outward",
        )

        lambda_esc_exact = (r_esc - r0) / energy

        ev = escape_radius_event(
            r_escape=r_esc,
            terminal=True,
            direction=1,
        )

        result = integrate_geodesic(
            initial_state=y0,
            metric=metric,
            affine_span=(0.0, lambda_esc_exact + 5.0),
            events=[ev],
            rtol=1e-10,
            atol=1e-10,
        )

        assert result.success is True
        assert result.status == 1
        assert result.terminal_event_occurred is True
        assert result.terminal_event_name == "escape_radius"
        assert result.terminal_event_index == 0
        assert result.has_events is True
        assert len(result.triggered_events) == 1

        lambda_term = result.lambdas[-1]
        r_term = result.r[-1]
        assert np.isclose(lambda_term, lambda_esc_exact, rtol=1e-7, atol=1e-7)
        assert np.isclose(r_term, r_esc, rtol=1e-7, atol=1e-7)

        rec = result.triggered_events[0]
        assert rec.name == "escape_radius"
        assert rec.terminal is True
        assert rec.direction == 1
        assert len(rec.lambdas) == 1
        assert np.isclose(rec.lambdas[0], lambda_esc_exact, rtol=1e-7, atol=1e-7)
        assert rec.states.shape == (1, STATE_DIMENSION)
        assert np.isclose(rec.states[0, IDX_R], r_esc, rtol=1e-7, atol=1e-7)# =============================================================================
# Test Suite: VAL-EVT-04 (Escape Radius Non-Triggering for Inward Ray)
# =============================================================================

class TestEscapeRadiusNonTriggering:
    """VAL-EVT-04: Escape-radius event must not trigger for inward rays."""

    def test_val_evt_04_escape_radius_inward_ray(self) -> None:
        metric = SchwarzschildMetric(mass=1.0)
        x0 = np.array([0.0, 10.0, np.pi / 2.0, 0.0])
        y0 = null_geodesic_initial_state(
            metric=metric,
            x=x0,
            energy=1.0,
            Lz=0.0,
            radial_direction="inward",
        )

        ev = escape_radius_event(
            r_escape=15.0,
            terminal=True,
            direction=1,
        )

        result = integrate_geodesic(
            initial_state=y0,
            metric=metric,
            affine_span=(0.0, 4.0),
            events=[ev],
        )

        assert result.success is True
        assert result.status == 0
        assert result.terminal_event_occurred is False
        assert result.has_events is False
        assert len(result.triggered_events) == 0
        assert len(result.t_events[0]) == 0
        assert result.y_events[0].shape == (0, STATE_DIMENSION)# =============================================================================
# Test Suite: VAL-EVT-05 (Radial Turning-Point Detection)
# =============================================================================

class TestRadialTurningPointDetection:
    """VAL-EVT-05: Radial turning-point detection for physical Schwarzschild null geodesic.

    Physics of Schwarzschild null geodesic reflection:
    In the equatorial plane (theta = pi/2), the null radial equation is:
        (dr/dlambda)^2 = E^2 - V_eff(r)
    where:
        V_eff(r) = (1 - 2M/r) * (L_z^2 / r^2)
    At a radial turning point (periapsis), dr/dlambda = 0, so:
        E^2 = (1 - 2M / r_peri) * (L_z^2 / r_peri^2)
        => L_z = r_peri * E / sqrt(1 - 2M / r_peri)

    For M = 1.0, E = 1.0, and r_peri = 6.0:
        f(6.0) = 1 - 2/6 = 4/6 = 2/3
        L_z = 6.0 * 1.0 / sqrt(2/3) = 6.0 * sqrt(3/2) = sqrt(54) ~ 7.3484692283495345

    Since r_peri = 6.0 > 3.0 (photon sphere), the effective potential has negative slope:
        dV_eff/dr(6) < 0 => d^2r/dlambda^2 = -1/2 dV_eff/dr > 0
    An infalling ray starting at r0 = 10.0 reaches periapsis at r = 6.0, where dr/dlambda
    smoothly crosses zero from negative to positive. This transversal sign change is detected
    by `radial_turning_point_event` with direction=1 (or direction=0).
    """

    def test_val_evt_05_periapsis_turning_point_detection(self) -> None:
        mass = 1.0
        energy = 1.0
        r_peri_target = 6.0
        Lz = r_peri_target * energy / np.sqrt(1.0 - 2.0 * mass / r_peri_target)  # sqrt(54)

        metric = SchwarzschildMetric(mass=mass)
        x0 = np.array([0.0, 10.0, np.pi / 2.0, 0.0])
        y0 = null_geodesic_initial_state(
            metric=metric,
            x=x0,
            energy=energy,
            Lz=Lz,
            radial_direction="inward",
        )

        ev_turn = radial_turning_point_event(
            metric=metric,
            terminal=True,
            direction=1,  # Inward to outward transition (dr/dlambda crossing - to +)
        )

        result = integrate_geodesic(
            initial_state=y0,
            metric=metric,
            affine_span=(0.0, 30.0),
            events=[ev_turn],
            rtol=1e-10,
            atol=1e-10,
        )

        assert result.success is True
        assert result.status == 1
        assert result.terminal_event_occurred is True
        assert result.terminal_event_name == "radial_turning_point"
        assert result.terminal_event_index == 0
        assert result.has_events is True
        assert len(result.triggered_events) == 1

        # Check termination radius matches target periapsis r_peri = 6.0
        r_term = result.r[-1]
        assert np.isclose(r_term, r_peri_target, rtol=1e-7, atol=1e-7)

        # Check conjugate radial momentum vanishes at periapsis
        pr_term = result.pr[-1]
        assert abs(pr_term) < 1e-7

        # Check vector field component dr/dlambda = [hamiltonian_rhs]_r vanishes
        rhs = hamiltonian_rhs(result.states[-1, :], metric)
        dr_dlambda_term = rhs[IDX_R]
        assert abs(dr_dlambda_term) < 1e-7# =============================================================================
# Test Suite: VAL-EVT-06 (Non-Terminal Event Execution)
# =============================================================================

class TestNonTerminalEvent:
    """VAL-EVT-06: Non-terminal events log triggers without halting integration."""

    def test_val_evt_06_non_terminal_event_continues_to_span_end(self) -> None:
        metric = SchwarzschildMetric(mass=1.0)
        x0 = np.array([0.0, 10.0, np.pi / 2.0, 0.0])
        y0 = null_geodesic_initial_state(
            metric=metric,
            x=x0,
            energy=1.0,
            Lz=0.0,
            radial_direction="inward",
        )

        # Non-terminal event at r = 6.0: should trigger at lambda = 10 - 6 = 4.0
        ev_intermediate = EscapeRadiusEvent(
            r_escape=6.0,
            terminal=False,
            direction=-1,
            name="crossing_r6",
        )

        lambda_end = 6.0  # At lambda = 6.0, r = 10 - 6 = 4.0 > 2M
        result = integrate_geodesic(
            initial_state=y0,
            metric=metric,
            affine_span=(0.0, lambda_end),
            events=[ev_intermediate],
            rtol=1e-10,
            atol=1e-10,
        )

        # Solver must complete full span (status == 0)
        assert result.success is True
        assert result.status == 0
        assert result.terminal_event_occurred is False
        assert result.terminal_event_name is None
        assert np.isclose(result.lambdas[-1], lambda_end, atol=1e-7)
        assert np.isclose(result.r[-1], 10.0 - lambda_end, atol=1e-7)

        # But the non-terminal trigger was captured!
        assert result.has_events is True
        assert len(result.triggered_events) == 1
        rec = result.triggered_events[0]
        assert rec.name == "crossing_r6"
        assert rec.terminal is False
        assert rec.direction == -1
        assert len(rec.lambdas) == 1
        assert np.isclose(rec.lambdas[0], 4.0, rtol=1e-7, atol=1e-7)
        assert np.isclose(rec.states[0, IDX_R], 6.0, rtol=1e-7, atol=1e-7)# =============================================================================
# Test Suite: VAL-EVT-07 (Terminal vs Non-Terminal Event Comparison)
# =============================================================================

class TestTerminalEventStopping:
    """VAL-EVT-07: Terminal event halts integration at the exact root."""

    def test_val_evt_07_terminal_stops_early_comparison(self) -> None:
        metric = SchwarzschildMetric(mass=1.0)
        x0 = np.array([0.0, 10.0, np.pi / 2.0, 0.0])
        y0 = null_geodesic_initial_state(
            metric=metric,
            x=x0,
            energy=1.0,
            Lz=0.0,
            radial_direction="inward",
        )

        ev_terminal = EscapeRadiusEvent(
            r_escape=6.0,
            terminal=True,
            direction=-1,
            name="crossing_r6_terminal",
        )

        result_term = integrate_geodesic(
            initial_state=y0,
            metric=metric,
            affine_span=(0.0, 7.0),
            events=[ev_terminal],
            rtol=1e-10,
            atol=1e-10,
        )

        # Terminal event stopped at lambda = 4.0
        assert result_term.status == 1
        assert result_term.terminal_event_occurred is True
        assert result_term.terminal_event_name == "crossing_r6_terminal"
        assert np.isclose(result_term.lambdas[-1], 4.0, atol=1e-7)
        assert np.isclose(result_term.r[-1], 6.0, atol=1e-7)
        assert result_term.lambdas[-1] < 7.0# =============================================================================
# Test Suite: VAL-EVT-08 (Direction Filtering)
# =============================================================================

class TestDirectionFiltering:
    """VAL-EVT-08: Direction filtering (-1 inward, +1 outward, 0 bidirectional).

    Using the turning-point orbit (r0 = 10 -> r_peri = 6 -> r = 10):
    A radius-crossing event at r = 8.0 occurs twice:
    1. Inward leg: dr/dlambda < 0 (matches direction = -1 or direction = 0)
    2. Outward leg: dr/dlambda > 0 (matches direction = +1 or direction = 0)
    """

    def test_val_evt_08_direction_filtering_on_bouncing_orbit(self) -> None:
        mass = 1.0
        energy = 1.0
        r_peri = 6.0
        Lz = r_peri * energy / np.sqrt(1.0 - 2.0 * mass / r_peri)

        metric = SchwarzschildMetric(mass=mass)
        x0 = np.array([0.0, 10.0, np.pi / 2.0, 0.0])
        y0 = null_geodesic_initial_state(
            metric=metric,
            x=x0,
            energy=energy,
            Lz=Lz,
            radial_direction="inward",
        )

        # Span sufficient to bounce at r=6 (lambda ~ 8.9) and return past r=8
        span = (0.0, 20.0)

        # 1. Inward-only crossing (direction = -1, terminal = False)
        ev_inward = EscapeRadiusEvent(r_escape=8.0, terminal=False, direction=-1, name="cross_inward")
        res_inward = integrate_geodesic(y0, metric, span, events=[ev_inward], rtol=1e-10, atol=1e-10)
        assert len(res_inward.triggered_events) == 1
        assert len(res_inward.triggered_events[0].lambdas) == 1
        lambda_inward = res_inward.triggered_events[0].lambdas[0]
        # Inward crossing must occur BEFORE turning point (~8.88)
        assert lambda_inward < 8.88

        # 2. Outward-only crossing (direction = +1, terminal = False)
        ev_outward = EscapeRadiusEvent(r_escape=8.0, terminal=False, direction=1, name="cross_outward")
        res_outward = integrate_geodesic(y0, metric, span, events=[ev_outward], rtol=1e-10, atol=1e-10)
        assert len(res_outward.triggered_events) == 1
        assert len(res_outward.triggered_events[0].lambdas) == 1
        lambda_outward = res_outward.triggered_events[0].lambdas[0]
        # Outward crossing must occur AFTER turning point (~8.88)
        assert lambda_outward > 8.88

        # 3. Bidirectional crossing (direction = 0, terminal = False)
        ev_both = EscapeRadiusEvent(r_escape=8.0, terminal=False, direction=0, name="cross_both")
        res_both = integrate_geodesic(y0, metric, span, events=[ev_both], rtol=1e-10, atol=1e-10)
        assert len(res_both.triggered_events) == 1
        assert len(res_both.triggered_events[0].lambdas) == 2
        # Triggers must match the inward and outward crossing times
        assert np.isclose(res_both.triggered_events[0].lambdas[0], lambda_inward, atol=1e-7)
        assert np.isclose(res_both.triggered_events[0].lambdas[1], lambda_outward, atol=1e-7)# =============================================================================
# Test Suite: VAL-EVT-09 (Multiple Simultaneous Events)
# =============================================================================

class TestMultipleSimultaneousEvents:
    """VAL-EVT-09: Multiple events passed simultaneously to integrate_geodesic."""

    def test_val_evt_09_multiple_events_selective_triggering(self) -> None:
        metric = SchwarzschildMetric(mass=1.0)
        x0 = np.array([0.0, 10.0, np.pi / 2.0, 0.0])
        y0_inward = null_geodesic_initial_state(
            metric=metric,
            x=x0,
            energy=1.0,
            Lz=0.0,
            radial_direction="inward",
        )

        ev_horizon = horizon_cutoff_event(metric=metric, epsilon=0.01, terminal=True, direction=-1)
        ev_escape = escape_radius_event(r_escape=25.0, terminal=True, direction=1)
        ev_turn = radial_turning_point_event(metric=metric, terminal=True, direction=0)

        # For purely inward radial ray, only horizon cutoff should trigger
        events_all = [ev_horizon, ev_escape, ev_turn]
        result = integrate_geodesic(
            initial_state=y0_inward,
            metric=metric,
            affine_span=(0.0, 15.0),
            events=events_all,
            rtol=1e-10,
            atol=1e-10,
        )

        assert result.status == 1
        assert result.terminal_event_occurred is True
        # Under the conservative terminal identity contract with multiple registered terminal events,
        # omitted events (ev_escape, ev_turn) cannot be certified non-coincident on a scale-invariant basis.
        # Thus unique attribution is suppressed and completeness is False:
        assert result.terminal_event_identity_complete is False
        assert result.terminal_event_index is None
        assert result.terminal_event_name is None
        assert result.terminal_event_indices == (0,)
        assert result.scipy_recorded_terminal_event_indices == (0,)
        assert result.unresolved_terminal_indices == (1, 2)
        assert len(result.triggered_events) == 1
        assert result.triggered_events[0].name == "horizon_cutoff"

        # Check t_events and y_events preserve shape for all 3 events
        assert result.t_events is not None
        assert len(result.t_events) == 3
        assert len(result.t_events[0]) == 1  # Horizon cutoff triggered
        assert len(result.t_events[1]) == 0  # Escape radius did not trigger
        assert len(result.t_events[2]) == 0  # Turning point did not trigger

        # When escape and turning point are registered as non-terminal monitoring events,
        # exactly one terminal event is registered, proving unique identity completeness:
        ev_escape_nt = escape_radius_event(r_escape=25.0, terminal=False, direction=1)
        ev_turn_nt = radial_turning_point_event(metric=metric, terminal=False, direction=0)
        res_mon = integrate_geodesic(
            initial_state=y0_inward,
            metric=metric,
            affine_span=(0.0, 15.0),
            events=[ev_horizon, ev_escape_nt, ev_turn_nt],
            rtol=1e-10,
            atol=1e-10,
        )
        assert res_mon.status == 1
        assert res_mon.terminal_event_occurred is True
        assert res_mon.terminal_event_identity_complete is True
        assert res_mon.terminal_event_index == 0
        assert res_mon.terminal_event_name == "horizon_cutoff"
        assert res_mon.unresolved_terminal_indices == ()

        assert result.y_events is not None
        assert len(result.y_events) == 3
        assert result.y_events[0].shape == (1, STATE_DIMENSION)
        assert result.y_events[1].shape == (0, STATE_DIMENSION)
        assert result.y_events[2].shape == (0, STATE_DIMENSION)# =============================================================================
# Test Suite: VAL-EVT-10 (Event Metadata and State Preservation)
# =============================================================================

class TestEventMetadataAndStatePreservation:
    """VAL-EVT-10: Event metadata and event states preservation in triggered_events."""

    def test_val_evt_10_metadata_and_state_integrity(self) -> None:
        metric = SchwarzschildMetric(mass=1.0)
        x0 = np.array([0.0, 5.0, np.pi / 2.0, 0.0])
        y0 = null_geodesic_initial_state(
            metric=metric,
            x=x0,
            energy=1.0,
            Lz=0.0,
            radial_direction="outward",
        )

        custom_name = "boundary_sphere_12"
        ev = escape_radius_event(r_escape=12.0, terminal=True, direction=1, name=custom_name)

        result = integrate_geodesic(
            initial_state=y0,
            metric=metric,
            affine_span=(0.0, 10.0),
            events=[ev],
        )

        assert result.has_events is True
        rec = result.triggered_events[0]
        assert isinstance(rec, EventTriggerRecord)
        assert rec.name == custom_name
        assert rec.event_index == 0
        assert rec.terminal is True
        assert rec.direction == 1
        assert rec.lambdas.ndim == 1
        assert rec.states.ndim == 2
        assert rec.states.shape == (1, 8)

        # Verify the recorded state satisfies the null constraint
        H_val = hamiltonian_value(rec.states[0, :4], rec.states[0, 4:], metric)
        assert abs(H_val) < 1e-10# =============================================================================
# Test Suite: VAL-EVT-11 (No-Event Trigger Handling)
# =============================================================================

class TestNoEventTriggerHandling:
    """VAL-EVT-11: Clean handling of events when none trigger."""

    def test_val_evt_11_clean_empty_event_structures(self) -> None:
        metric = SchwarzschildMetric(mass=1.0)
        x0 = np.array([0.0, 5.0, np.pi / 2.0, 0.0])
        y0 = null_geodesic_initial_state(
            metric=metric,
            x=x0,
            energy=1.0,
            Lz=0.0,
            radial_direction="outward",
        )

        # Event at r = 100.0, not reached within lambda in [0, 2]
        ev = escape_radius_event(r_escape=100.0, terminal=True, direction=1)

        result = integrate_geodesic(
            initial_state=y0,
            metric=metric,
            affine_span=(0.0, 2.0),
            events=[ev],
        )

        assert result.success is True
        assert result.status == 0
        assert result.terminal_event_occurred is False
        assert result.terminal_event_name is None
        assert result.terminal_event_index is None
        assert result.has_events is False
        assert result.triggered_events == ()
        assert result.event_names == ("escape_radius",)
        assert len(result.t_events) == 1
        assert result.t_events[0].shape == (0,)
        assert len(result.y_events) == 1
        assert result.y_events[0].shape == (0, STATE_DIMENSION)# =============================================================================
# Test Suite: VAL-EVT-12 (Input Validation & Fail-Fast Behavior)
# =============================================================================

class TestEventInputValidation:
    """VAL-EVT-12: Robust input validation for event classes and factory functions."""

    def test_val_evt_12_horizon_cutoff_invalid_parameters(self) -> None:
        metric = SchwarzschildMetric(mass=1.0)

        # Invalid epsilon
        with pytest.raises(ValueError, match="epsilon must be strictly positive"):
            horizon_cutoff_event(mass_or_metric=metric, epsilon=0.0)
        with pytest.raises(ValueError, match="epsilon must be strictly positive"):
            horizon_cutoff_event(mass_or_metric=metric, epsilon=-0.01)
        with pytest.raises(ValueError, match="epsilon must be strictly positive"):
            horizon_cutoff_event(mass_or_metric=metric, epsilon=float("nan"))
        with pytest.raises(ValueError, match="epsilon must be strictly positive"):
            horizon_cutoff_event(mass_or_metric=metric, epsilon=True)  # type: ignore

        # Invalid mass
        with pytest.raises(ValueError, match="mass must be strictly positive"):
            HorizonCutoffEvent(mass_or_metric=0.0)
        with pytest.raises(ValueError, match="mass must be strictly positive"):
            HorizonCutoffEvent(mass_or_metric=-1.0)
        with pytest.raises(TypeError, match="mass_or_metric must be a positive float"):
            HorizonCutoffEvent(mass_or_metric="not_a_metric")  # type: ignore

    def test_val_evt_12_escape_radius_invalid_parameters(self) -> None:
        with pytest.raises(ValueError, match="r_escape must be strictly positive"):
            escape_radius_event(r_escape=0.0)
        with pytest.raises(ValueError, match="r_escape must be strictly positive"):
            escape_radius_event(r_escape=-5.0)
        with pytest.raises(ValueError, match="r_escape must be strictly positive"):
            escape_radius_event(r_escape=float("nan"))
        with pytest.raises(ValueError, match="r_escape must be strictly positive"):
            escape_radius_event(r_escape=True)  # type: ignore

    def test_val_evt_12_radial_turning_point_invalid_parameters(self) -> None:
        with pytest.raises(TypeError, match="metric must be an instance of SpacetimeMetric"):
            radial_turning_point_event(metric="invalid")  # type: ignore

    def test_val_evt_12_base_event_invalid_parameters(self) -> None:
        # Invalid name
        with pytest.raises(TypeError, match="name must be a non-empty string"):
            HorizonCutoffEvent(mass_or_metric=1.0, name="")
        with pytest.raises(TypeError, match="name must be a non-empty string"):
            HorizonCutoffEvent(mass_or_metric=1.0, name="   ")

        # Invalid terminal
        with pytest.raises(TypeError, match="terminal must be a boolean"):
            HorizonCutoffEvent(mass_or_metric=1.0, terminal="true")  # type: ignore

        # Invalid direction
        with pytest.raises(ValueError, match="direction must be in"):
            HorizonCutoffEvent(mass_or_metric=1.0, direction=2)  # type: ignore
        with pytest.raises(ValueError, match="direction must be in"):
            HorizonCutoffEvent(mass_or_metric=1.0, direction=-2)  # type: ignore

    def test_val_evt_12_integrator_events_rejection(self) -> None:
        metric = SchwarzschildMetric(mass=1.0)
        x0 = np.array([0.0, 5.0, np.pi / 2.0, 0.0])
        y0 = null_geodesic_initial_state(metric=metric, x=x0, energy=1.0, Lz=0.0)

        # Non-callable event
        with pytest.raises(TypeError, match="events must be a callable or sequence of callables"):
            integrate_geodesic(y0, metric, (0.0, 1.0), events="not_a_callable")  # type: ignore

        # Sequence containing a non-callable item
        ev_valid = escape_radius_event(10.0)
        with pytest.raises(TypeError, match="Each event must be callable"):
            integrate_geodesic(y0, metric, (0.0, 1.0), events=[ev_valid, 12345])  # type: ignore# =============================================================================
# Test Suite: VAL-EVT-13 (Backward Compatibility when events=None)
# =============================================================================

class TestBackwardCompatibility:
    """VAL-EVT-13: Backward compatibility when events=None."""

    def test_val_evt_13_events_none_preserves_stage_1d_behavior(self) -> None:
        metric = SchwarzschildMetric(mass=1.0)
        x0 = np.array([0.0, 6.0, np.pi / 2.0, 0.0])
        y0 = null_geodesic_initial_state(
            metric=metric,
            x=x0,
            energy=1.0,
            Lz=0.0,
            radial_direction="outward",
        )

        result = integrate_geodesic(
            initial_state=y0,
            metric=metric,
            affine_span=(0.0, 2.0),
            events=None,
        )

        assert result.success is True
        assert result.status == 0
        assert result.t_events is None
        assert result.y_events is None
        assert result.event_names is None
        assert result.triggered_events == ()
        assert result.has_events is False
        assert result.terminal_event_occurred is False
        assert result.terminal_event_name is None
        assert result.terminal_event_index is None

        # Verify trajectory matches analytical outward null geodesic: r(lambda) = r0 + E * lambda
        r_exact = 6.0 + 1.0 * result.lambdas
        assert np.allclose(result.r, r_exact, atol=1e-8)# =============================================================================
# Test Suite: VAL-EVT-14 (Immutability & Caller State Non-Mutation)
# =============================================================================

class TestImmutabilityAndNonMutation:
    """VAL-EVT-14: Event evaluation must not mutate caller input arrays."""

    def test_val_evt_14_event_and_state_immutability(self) -> None:
        metric = SchwarzschildMetric(mass=1.0)
        x0 = np.array([0.0, 8.0, np.pi / 2.0, 0.0])
        y0 = null_geodesic_initial_state(
            metric=metric,
            x=x0,
            energy=1.0,
            Lz=0.0,
            radial_direction="inward",
        )
        y0_copy = y0.copy()

        ev = horizon_cutoff_event(metric=metric, epsilon=0.01)

        # Directly call event function
        val = ev(0.0, y0)
        assert np.array_equal(y0, y0_copy)

        # Integrate with event
        result = integrate_geodesic(
            initial_state=y0,
            metric=metric,
            affine_span=(0.0, 7.0),
            events=[ev],
        )
        assert np.array_equal(y0, y0_copy)

        # Check immutability of returned result fields
        assert isinstance(result.triggered_events, tuple)
        assert isinstance(result.t_events, tuple)
        assert isinstance(result.y_events, tuple)# =============================================================================
# Test Suite: VAL-EVT-15 (Terminal Event Ambiguity and Coincident Roots)
# =============================================================================

class TestTerminalEventAmbiguityAndSimultaneity:
    """Scientific audit: Terminal event disambiguation and coincident root semantics."""

    def test_two_terminal_events_at_identical_root_flags_ambiguity(self) -> None:
        """Two terminal events with identical roots must NOT report a false unique terminal identity."""
        metric = SchwarzschildMetric(mass=1.0)
        x0 = np.array([0.0, 4.0, np.pi / 2.0, 0.0])
        y0 = null_geodesic_initial_state(
            metric=metric, x=x0, energy=1.0, Lz=0.0, radial_direction="outward"
        )

        # Both terminal events trigger at r = 10.0 (lambda = 6.0)
        ev1 = escape_radius_event(r_escape=10.0, terminal=True, direction=1, name="escape_A")
        ev2 = escape_radius_event(r_escape=10.0, terminal=True, direction=1, name="escape_B")

        result = integrate_geodesic(y0, metric, (0.0, 15.0), events=[ev1, ev2])

        assert result.status == 1
        assert result.terminal_event_occurred is True
        # Both events coincided at lambda = 6.0; neither is uniquely the terminator!
        assert result.terminal_event_index is None
        assert result.terminal_event_name is None
        assert result.terminal_event_indices == (0, 1)
        assert result.terminal_event_names == ("escape_A", "escape_B")

    def test_two_terminal_events_at_distinct_roots_identifies_earlier(self) -> None:
        """Two terminal events at distinct roots: unrecovered candidate marked unresolved."""
        metric = SchwarzschildMetric(mass=1.0)
        x0 = np.array([0.0, 4.0, np.pi / 2.0, 0.0])
        y0 = null_geodesic_initial_state(
            metric=metric, x=x0, energy=1.0, Lz=0.0, radial_direction="outward"
        )

        # ev1 triggers at r = 8.0 (lambda = 4.0), ev2 triggers at r = 10.0 (lambda = 6.0)
        ev1 = escape_radius_event(r_escape=8.0, terminal=True, direction=1, name="escape_earlier")
        ev2 = escape_radius_event(r_escape=10.0, terminal=True, direction=1, name="escape_later")

        result = integrate_geodesic(y0, metric, (0.0, 15.0), events=[ev1, ev2])

        assert result.status == 1
        assert result.terminal_event_occurred is True
        assert np.isclose(result.lambdas[-1], 4.0, atol=1e-7)
        # ev1 is recorded by SciPy at lambda = 4.0
        assert result.scipy_recorded_terminal_event_indices == (0,)
        assert result.scipy_recorded_terminal_event_names == ("escape_earlier",)
        assert result.terminal_event_indices == (0,)
        assert result.inferred_coincident_terminal_indices == ()
        # ev2 was omitted; without an ungrounded heuristic, it is conservatively unresolved
        assert result.unresolved_terminal_indices == (1,)
        assert result.unresolved_terminal_names == ("escape_later",)
        assert result.terminal_event_identity_complete is False
        assert result.terminal_event_index is None
        assert result.terminal_event_name is None

        # When later event is non-terminal, identity completeness holds with unique index
        ev2_nt = escape_radius_event(r_escape=10.0, terminal=False, direction=1, name="escape_later")
        res_unique = integrate_geodesic(y0, metric, (0.0, 15.0), events=[ev1, ev2_nt])
        assert res_unique.status == 1
        assert res_unique.terminal_event_identity_complete is True
        assert res_unique.terminal_event_index == 0
        assert res_unique.terminal_event_name == "escape_earlier"
        assert res_unique.unresolved_terminal_indices == ()

    def test_terminal_and_non_terminal_coincident_roots(self) -> None:
        """Coincident roots between terminal and non-terminal events must identify terminal uniquely."""
        metric = SchwarzschildMetric(mass=1.0)
        x0 = np.array([0.0, 4.0, np.pi / 2.0, 0.0])
        y0 = null_geodesic_initial_state(
            metric=metric, x=x0, energy=1.0, Lz=0.0, radial_direction="outward"
        )

        # Ordering A: Non-terminal first, terminal second
        ev_nt = escape_radius_event(r_escape=8.0, terminal=False, direction=1, name="cross_monitor")
        ev_term = escape_radius_event(r_escape=8.0, terminal=True, direction=1, name="escape_halt")

        res_A = integrate_geodesic(y0, metric, (0.0, 15.0), events=[ev_nt, ev_term])
        assert res_A.status == 1
        assert res_A.terminal_event_occurred is True
        assert res_A.terminal_event_index == 1
        assert res_A.terminal_event_name == "escape_halt"
        assert res_A.terminal_event_indices == (1,)

        # Ordering B: Terminal first, non-terminal second
        res_B = integrate_geodesic(y0, metric, (0.0, 15.0), events=[ev_term, ev_nt])
        assert res_B.status == 1
        assert res_B.terminal_event_occurred is True
        assert res_B.terminal_event_index == 0
        assert res_B.terminal_event_name == "escape_halt"
        assert res_B.terminal_event_indices == (0,)

    def test_adversarial_01_coincident_terminal_events_with_vastly_different_scales(self) -> None:
        """Adversarial 1: Multiple terminal events at same root with scales differing by 18 orders of magnitude."""
        metric = SchwarzschildMetric(mass=1.0)
        x0 = np.array([0.0, 4.0, np.pi / 2.0, 0.0])
        y0 = null_geodesic_initial_state(metric, x0, energy=1.0, Lz=0.0, radial_direction="outward")

        # Three terminal events with identical root r = 8.0 (lambda = 4.0), scales 1, 1e8, 1e-10
        def ev_unit(t: float, y: np.ndarray) -> float:
            return float(y[1] - 8.0)
        ev_unit.terminal = True; ev_unit.name = "scale_unit"; ev_unit.direction = 1

        def ev_huge(t: float, y: np.ndarray) -> float:
            return float((y[1] - 8.0) * 1e8)
        ev_huge.terminal = True; ev_huge.name = "scale_huge"; ev_huge.direction = 1

        def ev_tiny(t: float, y: np.ndarray) -> float:
            return float((y[1] - 8.0) * 1e-10)
        ev_tiny.terminal = True; ev_tiny.name = "scale_tiny"; ev_tiny.direction = 1

        res = integrate_geodesic(y0, metric, (0.0, 10.0), events=[ev_unit, ev_huge, ev_tiny])
        assert res.status == 1
        assert res.terminal_event_occurred is True
        # Scale-independent root solving must identify all three without false unique attribution
        assert res.terminal_event_index is None
        assert res.terminal_event_name is None
        assert res.terminal_event_indices == (0, 1, 2)
        assert res.terminal_event_names == ("scale_unit", "scale_huge", "scale_tiny")
        # SciPy only recorded index 0; wrapper independently inferred indices 1 and 2 via dense root solving
        assert res.inferred_coincident_terminal_indices == (1, 2)
        assert np.isclose(res.lambdas[-1], 4.0, atol=1e-7)

    def test_adversarial_02_distinct_terminal_roots_close_in_parameter(self) -> None:
        """Adversarial 2: Two distinct terminal roots close in parameter are NOT marked coincident."""
        metric = SchwarzschildMetric(mass=1.0)
        x0 = np.array([0.0, 4.0, np.pi / 2.0, 0.0])
        y0 = null_geodesic_initial_state(metric, x0, energy=1.0, Lz=0.0, radial_direction="outward")

        # Root 1 at r = 8.0000 (lambda = 4.0000)
        ev1 = escape_radius_event(r_escape=8.0, terminal=True, direction=1, name="first_halt")
        # Root 2 at r = 8.0001 (lambda = 4.0001) - distinct root!
        ev2 = escape_radius_event(r_escape=8.0001, terminal=True, direction=1, name="second_halt")

        res = integrate_geodesic(y0, metric, (0.0, 10.0), events=[ev1, ev2])
        assert res.status == 1
        assert res.terminal_event_occurred is True
        # Only the first event was reached; the second was 1e-4 away and must NOT be marked coincident
        assert res.scipy_recorded_terminal_event_indices == (0,)
        assert res.terminal_event_indices == (0,)
        assert res.inferred_coincident_terminal_indices == ()
        assert res.unresolved_terminal_indices == (1,)
        assert res.terminal_event_identity_complete is False
        assert res.terminal_event_index is None



        assert res.terminal_event_name is None
        assert np.isclose(res.lambdas[-1], 4.0, atol=1e-7)

    def test_adversarial_03_scale_invariance_under_extreme_multiplication(self) -> None:
        """Adversarial 3: Single event multiplied by 1e-15 or 1e15 preserves unique identity."""
        metric = SchwarzschildMetric(mass=1.0)
        x0 = np.array([0.0, 4.0, np.pi / 2.0, 0.0])
        y0 = null_geodesic_initial_state(metric, x0, energy=1.0, Lz=0.0, radial_direction="outward")

        def ev_extreme_small(t: float, y: np.ndarray) -> float:
            return float((y[1] - 8.0) * 1e-15)
        ev_extreme_small.terminal = True; ev_extreme_small.name = "small_scale"; ev_extreme_small.direction = 1

        def ev_extreme_large(t: float, y: np.ndarray) -> float:
            return float((y[1] - 8.0) * 1e15)
        ev_extreme_large.terminal = True; ev_extreme_large.name = "large_scale"; ev_extreme_large.direction = 1

        # Single extreme small
        res_small = integrate_geodesic(y0, metric, (0.0, 10.0), events=[ev_extreme_small])
        assert res_small.status == 1
        assert res_small.terminal_event_index == 0
        assert res_small.terminal_event_name == "small_scale"

        # Single extreme large
        res_large = integrate_geodesic(y0, metric, (0.0, 10.0), events=[ev_extreme_large])
        assert res_large.status == 1
        assert res_large.terminal_event_index == 0
        assert res_large.terminal_event_name == "large_scale"

        # Both together: coincident across 30 orders of magnitude
        res_both = integrate_geodesic(y0, metric, (0.0, 10.0), events=[ev_extreme_small, ev_extreme_large])
        assert res_both.status == 1
        assert res_both.terminal_event_index is None
        assert res_both.terminal_event_indices == (0, 1)

    def test_adversarial_04_backward_integration_with_different_scales(self) -> None:
        """Adversarial 4: Scale-independent coincidence detection operates symmetrically in backward integration."""
        metric = SchwarzschildMetric(mass=1.0)
        # Outward null ray integrated backward from lambda = 5.0 to 0.0
        # For outward null ray: r(lambda) = r0 + E*lambda.
        # At lambda = 5.0, r = 9.0 (with r0 = 4.0, E = 1.0).
        x0_bwd = np.array([0.0, 9.0, np.pi / 2.0, 0.0])
        y0_bwd = null_geodesic_initial_state(metric, x0_bwd, energy=1.0, Lz=0.0, radial_direction="outward")

        # Along backward integration (5.0 -> 0.0), r decreases from 9.0 to 4.0.
        # Root at r = 6.0 occurs at lambda = 2.0.
        # Along progression of integration, r is decreasing, so direction along progression is -1!
        def ev_bwd_unit(t: float, y: np.ndarray) -> float:
            return float(y[1] - 6.0)
        ev_bwd_unit.terminal = True; ev_bwd_unit.direction = -1; ev_bwd_unit.name = "bwd_unit"

        def ev_bwd_scaled(t: float, y: np.ndarray) -> float:
            return float((y[1] - 6.0) * 1e7)
        ev_bwd_scaled.terminal = True; ev_bwd_scaled.direction = -1; ev_bwd_scaled.name = "bwd_scaled"

        res = integrate_geodesic(y0_bwd, metric, (5.0, 0.0), events=[ev_bwd_unit, ev_bwd_scaled])
        assert res.status == 1
        assert res.terminal_event_occurred is True
        assert np.isclose(res.lambdas[-1], 2.0, atol=1e-7)
        # Symmetrically identified in backward integration
        assert res.terminal_event_index is None
        assert res.terminal_event_indices == (0, 1)
        assert res.terminal_event_names == ("bwd_unit", "bwd_scaled")

    def test_adversarial_05_no_dense_extrapolation_beyond_accepted_step(self) -> None:
        """Adversarial 5: Verify dense interpolant is NEVER evaluated outside original accepted step."""
        from scipy.integrate._ivp.base import DenseOutput

        extrapolations = []
        orig_call = DenseOutput.__call__

        def guarded_call(self_interp: DenseOutput, t):
            t_arr = np.asarray(t)
            for ti in t_arr.flat:
                if hasattr(self_interp, "t_min") and hasattr(self_interp, "t_max"):
                    if ti < self_interp.t_min - 1e-12 or ti > self_interp.t_max + 1e-12:
                        extrapolations.append((float(ti), float(self_interp.t_min), float(self_interp.t_max)))
            return orig_call(self_interp, t)

        DenseOutput.__call__ = guarded_call
        try:
            metric = SchwarzschildMetric(mass=1.0)
            x0 = np.array([0.0, 10.0, np.pi / 2.0, 0.0])
            y0 = null_geodesic_initial_state(metric, x0, energy=1.0, Lz=0.0, radial_direction="inward")

            def ev1(t: float, y: np.ndarray) -> float:
                return float(y[1] - 5.0)
            ev1.terminal = True; ev1.direction = -1; ev1.name = "term_at_5"

            def ev2(t: float, y: np.ndarray) -> float:
                return float((y[1] - 5.0) * 1e-8)
            ev2.terminal = True; ev2.direction = -1; ev2.name = "coincident_tracker"

            res = integrate_geodesic(y0, metric, (0.0, 10.0), events=[ev1, ev2])
            assert res.terminal_event_occurred is True
            assert len(extrapolations) == 0, f"DenseOutput extrapolation detected: {extrapolations}"
            assert res.terminal_event_index is None
            assert res.terminal_event_indices == (0, 1)
        finally:
            DenseOutput.__call__ = orig_call

    def test_adversarial_06_multiple_roots_distinct_root_not_coincident(self) -> None:
        """Adversarial 6: Event with multiple roots including one close to (1e-3) but distinct from terminal."""
        metric = SchwarzschildMetric(mass=1.0)
        x0 = np.array([0.0, 10.0, np.pi / 2.0, 0.0])
        y0 = null_geodesic_initial_state(metric, x0, energy=1.0, Lz=0.0, radial_direction="inward")

        # ev1 halts at r = 6.0 (lambda = 4.0)
        def ev1(t: float, y: np.ndarray) -> float:
            return float(y[1] - 6.0)
        ev1.terminal = True
        ev1.direction = -1
        ev1.name = "ev1_term_at_6"

        # ev2 has roots at r = 5.999 (lambda = 4.001) and r = 5.5 (lambda = 4.5)
        # Root at 5.999 is separated by |delta lambda| ~ 0.001 from lambda_term=4.0
        def ev2_multi_distinct(t: float, y: np.ndarray) -> float:
            return float((y[1] - 5.999) * (y[1] - 5.5))
        ev2_multi_distinct.terminal = True
        ev2_multi_distinct.name = "ev2_distinct_multi"

        res = integrate_geodesic(y0, metric, (0.0, 10.0), events=[ev1, ev2_multi_distinct])
        assert res.terminal_event_occurred is True
        # ev2_multi_distinct is an arbitrary callable with roots near the terminal root.
        # Under conservative identity-confidence semantics, completeness cannot be established.
        assert res.terminal_event_identity_complete is False
        assert res.terminal_event_index is None



        assert res.terminal_event_name is None
        assert res.terminal_event_indices == (0,)
        # Distinct root was NEVER labeled coincident
        assert res.inferred_coincident_terminal_indices == ()
        assert res.unresolved_terminal_indices == (1,)

    def test_adversarial_07_multiple_roots_coincident_and_interior_root(self) -> None:
        """Adversarial 7: Event with multiple roots where one is genuinely coincident with terminal root."""
        metric = SchwarzschildMetric(mass=1.0)
        x0 = np.array([0.0, 10.0, np.pi / 2.0, 0.0])
        y0 = null_geodesic_initial_state(metric, x0, energy=1.0, Lz=0.0, radial_direction="inward")

        # ev1 halts at r = 6.0 (lambda = 4.0)
        def ev1(t: float, y: np.ndarray) -> float:
            return float(y[1] - 6.0)
        ev1.terminal = True
        ev1.direction = -1
        ev1.name = "ev1_term_at_6"

        # ev2 has roots at r = 6.0 (coincident) and r = 5.5 (interior)
        def ev2_multi_coincident(t: float, y: np.ndarray) -> float:
            return float((y[1] - 6.0) * (y[1] - 5.5))
        ev2_multi_coincident.terminal = True
        ev2_multi_coincident.name = "ev2_coincident_multi"

        res = integrate_geodesic(y0, metric, (0.0, 10.0), events=[ev1, ev2_multi_coincident])
        assert res.terminal_event_occurred is True
        # Coincidence is correctly detected despite multiple roots
        assert res.terminal_event_index is None
        assert res.terminal_event_indices == (0, 1)
        assert res.terminal_event_names == ("ev1_term_at_6", "ev2_coincident_multi")
        assert res.inferred_coincident_terminal_indices == (1,)

    def test_adversarial_08_sub_tolerance_near_coincident_roots_indistinguishable(self) -> None:
        """Adversarial 8: Roots separated by less than root_time_atol are numerically indistinguishable."""
        metric = SchwarzschildMetric(mass=1.0)
        x0 = np.array([0.0, 4.0, np.pi / 2.0, 0.0])
        y0 = null_geodesic_initial_state(metric, x0, energy=1.0, Lz=0.0, radial_direction="outward")

        eps = np.finfo(np.float64).eps
        # At lambda ~ 4.0: root_time_atol = 100 * eps * 4.0 ~ 8.88e-14
        delta_sub_tol = 10.0 * eps  # ~ 2.22e-15, strictly < root_time_atol

        # Root 1 at r = 8.0 (lambda = 4.0)
        def ev1(t: float, y: np.ndarray) -> float:
            return float(y[1] - 8.0)
        ev1.terminal = True; ev1.name = "ev1_exact_8"; ev1.direction = 1

        # Root 2 mathematically distinct but separated by delta_sub_tol < root_time_atol
        def ev2_sub(t: float, y: np.ndarray) -> float:
            return float(y[1] - (8.0 + delta_sub_tol))
        ev2_sub.terminal = True; ev2_sub.name = "ev2_sub_tol"; ev2_sub.direction = 1

        res_sub = integrate_geodesic(y0, metric, (0.0, 10.0), events=[ev1, ev2_sub])
        assert res_sub.status == 1
        assert res_sub.terminal_event_occurred is True

        # Numerical Coincidence Behavior:
        # The two roots differ by 10 * eps_mach, which is less than the comparison tolerance
        # root_time_atol = 100 * eps_mach * max(1, |lambda_term|). In double-precision floating point,
        # such close roots cannot be distinguished from exact coincidence.
        # Under the documented numerical identification policy:
        # - Both events are classified as coincident within tolerance (indices 0 and 1)
        # - Unique attribution is suppressed (terminal_event_index is None)
        # - Identity completeness is True under the numerical policy because all registered
        #   terminal events are accounted for within tolerance.
        assert res_sub.scipy_recorded_terminal_event_indices == (0,)
        assert res_sub.inferred_coincident_terminal_indices == (1,)
        assert res_sub.terminal_event_indices == (0, 1)
        assert res_sub.unresolved_terminal_indices == ()
        assert res_sub.terminal_event_identity_complete is True
        assert res_sub.terminal_event_index is None
        assert res_sub.terminal_event_name is None

        # Nearby Case: Distinct root separated comfortably beyond tolerance (delta = 1e-4 >> root_time_atol)
        def ev3_beyond(t: float, y: np.ndarray) -> float:
            return float(y[1] - (8.0 + 1e-4))
        ev3_beyond.terminal = True; ev3_beyond.name = "ev3_beyond_tol"; ev3_beyond.direction = 1

        res_beyond = integrate_geodesic(y0, metric, (0.0, 10.0), events=[ev1, ev3_beyond])
        assert res_beyond.status == 1
        assert res_beyond.terminal_event_occurred is True
        # ev3 is well beyond tolerance: it is NOT identified as coincident
        assert res_beyond.scipy_recorded_terminal_event_indices == (0,)
        assert res_beyond.terminal_event_indices == (0,)
        assert res_beyond.inferred_coincident_terminal_indices == ()
        # Because ev3 was omitted by SciPy and cannot be certified non-coincident on a rigorous basis,
        # it is conservatively placed in unresolved_terminal_indices, setting completeness to False:
        assert res_beyond.unresolved_terminal_indices == (1,)
        assert res_beyond.terminal_event_identity_complete is False
        assert res_beyond.terminal_event_index is None
        assert res_beyond.terminal_event_name is None# =============================================================================
# Test Suite: VAL-EVT-18 (Terminal Event Identity Completeness Semantics)
# =============================================================================

class TestTerminalEventIdentityCompleteness:
    """Scientific audit: Identity completeness, poorly conditioned, flat, scale-invariance, and callables."""

    def test_01_single_registered_terminal_event_complete_identity(self) -> None:
        """Scenario 1: One registered terminal event, successfully recorded by SciPy: complete identity."""
        metric = SchwarzschildMetric(mass=1.0)
        x0 = np.array([0.0, 10.0, np.pi / 2.0, 0.0])
        y0 = null_geodesic_initial_state(metric, x0, energy=1.0, Lz=0.0, radial_direction="inward")

        ev_horizon = horizon_cutoff_event(metric=metric, epsilon=0.01, terminal=True, direction=-1)

        res = integrate_geodesic(y0, metric, (0.0, 10.0), events=[ev_horizon])
        assert res.terminal_event_occurred is True
        assert res.terminal_event_identity_complete is True
        assert res.terminal_event_index == 0
        assert res.terminal_event_name == "horizon_cutoff"
        assert res.terminal_event_indices == (0,)
        assert res.terminal_event_names == ("horizon_cutoff",)
        assert res.scipy_recorded_terminal_event_indices == (0,)
        assert res.scipy_recorded_terminal_event_names == ("horizon_cutoff",)
        assert res.inferred_coincident_terminal_indices == ()
        assert res.unresolved_terminal_indices == ()
        assert res.unresolved_terminal_names == ()

    def test_02_two_well_conditioned_coincident_events(self) -> None:
        """Scenario 2: Two well-conditioned coincident events: both identified, unique attribution suppressed."""
        metric = SchwarzschildMetric(mass=1.0)
        x0 = np.array([0.0, 10.0, np.pi / 2.0, 0.0])
        y0 = null_geodesic_initial_state(metric, x0, energy=1.0, Lz=0.0, radial_direction="inward")

        ev1 = EscapeRadiusEvent(r_escape=6.0, terminal=True, direction=-1, name="escape_A")
        ev2 = EscapeRadiusEvent(r_escape=6.0, terminal=True, direction=-1, name="escape_B")

        res = integrate_geodesic(y0, metric, (0.0, 10.0), events=[ev1, ev2])
        assert res.terminal_event_occurred is True
        # Both registered events are accounted for as coincident; no omitted candidate remains unresolved
        assert res.terminal_event_identity_complete is True
        assert res.terminal_event_index is None
        assert res.terminal_event_name is None
        assert res.terminal_event_indices == (0, 1)
        assert res.terminal_event_names == ("escape_A", "escape_B")
        assert res.scipy_recorded_terminal_event_indices == (0,)
        assert res.inferred_coincident_terminal_indices == (1,)
        assert res.unresolved_terminal_indices == ()

    def test_03_two_registered_events_one_recorded_one_unresolved(self) -> None:
        """Scenario 3: Two registered events where one is recorded and the other cannot be ruled out."""
        metric = SchwarzschildMetric(mass=1.0)
        x0 = np.array([0.0, 10.0, np.pi / 2.0, 0.0])
        y0 = null_geodesic_initial_state(metric, x0, energy=1.0, Lz=0.0, radial_direction="inward")

        ev_horizon = horizon_cutoff_event(metric=metric, epsilon=0.01, terminal=True, direction=-1)
        ev_escape = escape_radius_event(r_escape=25.0, terminal=True, direction=1)

        res = integrate_geodesic(y0, metric, (0.0, 10.0), events=[ev_horizon, ev_escape])
        assert res.terminal_event_occurred is True
        # Under conservative contract, ev_escape is omitted and unrecovered, so completeness is False
        assert res.terminal_event_identity_complete is False
        assert res.terminal_event_index is None



        assert res.terminal_event_name is None
        assert res.terminal_event_indices == (0,)
        assert res.scipy_recorded_terminal_event_indices == (0,)
        assert res.inferred_coincident_terminal_indices == ()
        assert res.unresolved_terminal_indices == (1,)
        assert res.unresolved_terminal_names == ("escape_radius",)

    def test_04_poorly_conditioned_cubic_contact_candidate(self) -> None:
        """Scenario 4: A poorly conditioned cubic-contact candidate (g' = 0)."""
        metric = SchwarzschildMetric(mass=1.0)
        x0 = np.array([0.0, 10.0, np.pi / 2.0, 0.0])
        y0 = null_geodesic_initial_state(metric, x0, energy=1.0, Lz=0.0, radial_direction="inward")

        ev1 = EscapeRadiusEvent(r_escape=6.0, terminal=True, direction=-1, name="ev1_clean")

        # Ill-conditioned cubic contact: g(r) = -(r - 6.0)^3
        def ev_cubic(t: float, y: np.ndarray) -> float:
            return float(-((y[1] - 6.0) ** 3))
        ev_cubic.terminal = True
        ev_cubic.direction = -1
        ev_cubic.name = "ev_cubic_ill_conditioned"

        res = integrate_geodesic(y0, metric, (0.0, 10.0), events=[ev1, ev_cubic])
        assert res.terminal_event_occurred is True
        assert res.terminal_event_identity_complete is False
        assert res.terminal_event_index is None



        assert res.terminal_event_name is None
        assert 0 in res.terminal_event_indices
        assert 1 in res.unresolved_terminal_indices

    def test_05_very_flat_even_multiplicity_candidate(self) -> None:
        """Scenario 5: A very flat/even-multiplicity candidate."""
        metric = SchwarzschildMetric(mass=1.0)
        x0 = np.array([0.0, 10.0, np.pi / 2.0, 0.0])
        y0 = null_geodesic_initial_state(metric, x0, energy=1.0, Lz=0.0, radial_direction="inward")

        ev1 = EscapeRadiusEvent(r_escape=6.0, terminal=True, direction=-1, name="ev1_clean")

        # High-order flat contact: -(r - 6.0)^4 with vanishing derivatives g' = g'' = g''' = 0
        def ev_flat(t: float, y: np.ndarray) -> float:
            return float(-((y[1] - 6.0) ** 4))
        ev_flat.terminal = True
        ev_flat.name = "ev_flat_contact"

        res = integrate_geodesic(y0, metric, (0.0, 10.0), events=[ev1, ev_flat])
        assert res.terminal_event_occurred is True
        assert res.terminal_event_identity_complete is False
        assert res.terminal_event_index is None



        assert res.unresolved_terminal_indices == (1,)

    def test_06_radial_turning_point_candidate_incomplete_identity(self) -> None:
        """Scenario 6: Built-in RadialTurningPointEvent case challenging completeness logic."""
        metric = SchwarzschildMetric(mass=1.0)
        # Inward ray with angular momentum that encounters a periapsis turning point around r ~ 4.45
        x0 = np.array([0.0, 8.0, np.pi / 2.0, 0.0])
        y0 = null_geodesic_initial_state(metric, x0, energy=1.0, Lz=6.0, radial_direction="inward")

        ev_turn = radial_turning_point_event(metric=metric, terminal=True, direction=0)
        ev_horizon = horizon_cutoff_event(metric=metric, epsilon=0.01, terminal=True, direction=-1)

        res = integrate_geodesic(y0, metric, (0.0, 10.0), events=[ev_turn, ev_horizon])
        assert res.status == 1
        assert res.terminal_event_occurred is True
        # ev_turn triggers at periapsis; ev_horizon is omitted and cannot be certified ruled out
        assert res.scipy_recorded_terminal_event_indices == (0,)
        assert res.unresolved_terminal_indices == (1,)
        assert res.terminal_event_identity_complete is False
        assert res.terminal_event_index is None


    def test_07_momentum_rescaling_scale_invariant_identity_semantics(self) -> None:
        """Scenario 7: Momentum rescaling of radial-turning event: no dependence on fixed event-value threshold."""
        metric = SchwarzschildMetric(mass=1.0)
        x0 = np.array([0.0, 10.0, np.pi / 2.0, 0.0])

        ev_horizon = horizon_cutoff_event(metric=metric, epsilon=0.01, terminal=True, direction=-1)
        ev_turn = radial_turning_point_event(metric=metric, terminal=True, direction=0)

        # Scale A: Enormous momentum E = 1e8 -> p_r ~ 1e8
        y0_huge = null_geodesic_initial_state(metric, x0, energy=1e8, Lz=0.0, radial_direction="inward")
        res_huge = integrate_geodesic(y0_huge, metric, (0.0, 1e-7), events=[ev_horizon, ev_turn])
        assert res_huge.status == 1
        assert res_huge.scipy_recorded_terminal_event_indices == (0,)
        assert res_huge.unresolved_terminal_indices == (1,)
        assert res_huge.terminal_event_identity_complete is False
        assert res_huge.terminal_event_index is None

        # Scale B: Tiny momentum E = 1e-8 -> p_r ~ 1e-8
        # Under the old fixed 1e-5 threshold, |pr| ~ 1e-8 would have triggered false coincidence/ruled-out logic!
        # Under scale-invariant conservative semantics, identity completeness is robustly False.
        y0_tiny = null_geodesic_initial_state(metric, x0, energy=1e-8, Lz=0.0, radial_direction="inward")
        res_tiny = integrate_geodesic(y0_tiny, metric, (0.0, 1e9), events=[ev_horizon, ev_turn])
        assert res_tiny.status == 1
        assert res_tiny.scipy_recorded_terminal_event_indices == (0,)
        assert res_tiny.unresolved_terminal_indices == (1,)
        assert res_tiny.terminal_event_identity_complete is False
        assert res_tiny.terminal_event_index is None

    def test_08_arbitrary_user_callable_unresolved(self) -> None:
        """Scenario 8: Arbitrary user callable whose coincidence cannot be established or excluded."""
        metric = SchwarzschildMetric(mass=1.0)
        x0 = np.array([0.0, 10.0, np.pi / 2.0, 0.0])
        y0 = null_geodesic_initial_state(metric, x0, energy=1.0, Lz=0.0, radial_direction="inward")

        ev1 = EscapeRadiusEvent(r_escape=6.0, terminal=True, direction=-1, name="ev1_clean")

        def custom_user_callable(t: float, y: np.ndarray) -> float:
            return float(y[1] - 20.0)
        custom_user_callable.terminal = True
        custom_user_callable.name = "user_black_box"

        res = integrate_geodesic(y0, metric, (0.0, 10.0), events=[ev1, custom_user_callable])
        assert res.terminal_event_occurred is True
        assert res.terminal_event_identity_complete is False
        assert res.terminal_event_index is None



        assert res.unresolved_terminal_indices == (1,)

    def test_09_well_separated_omitted_event_unresolved(self) -> None:
        """Scenario 9: Well-separated omitted event: unresolved unless defensible basis, complete if non-terminal."""
        metric = SchwarzschildMetric(mass=1.0)
        x0 = np.array([0.0, 10.0, np.pi / 2.0, 0.0])
        y0 = null_geodesic_initial_state(metric, x0, energy=1.0, Lz=0.0, radial_direction="inward")

        ev_horizon = horizon_cutoff_event(metric=metric, epsilon=0.01, terminal=True, direction=-1)
        ev_escape = escape_radius_event(r_escape=25.0, terminal=True, direction=1)

        # Both terminal: ev_escape omitted and unresolved
        res = integrate_geodesic(y0, metric, (0.0, 10.0), events=[ev_horizon, ev_escape])
        assert res.terminal_event_occurred is True
        assert res.terminal_event_identity_complete is False
        assert res.terminal_event_index is None



        assert res.unresolved_terminal_indices == (1,)

        # Alternative: ev_escape configured as non-terminal monitoring event
        ev_escape_nt = escape_radius_event(r_escape=25.0, terminal=False, direction=1)
        res_nt = integrate_geodesic(y0, metric, (0.0, 10.0), events=[ev_horizon, ev_escape_nt])
        assert res_nt.terminal_event_occurred is True
        assert res_nt.terminal_event_identity_complete is True
        assert res_nt.terminal_event_index == 0
        assert res_nt.terminal_event_name == "horizon_cutoff"
        assert res_nt.unresolved_terminal_indices == ()

    def test_10_backward_integration_and_multiple_terminal_ordering(self) -> None:
        """Scenario 10: Backward integration and multiple terminal-event ordering."""
        metric = SchwarzschildMetric(mass=1.0)
        x0_bwd = np.array([0.0, 9.0, np.pi / 2.0, 0.0])
        y0_bwd = null_geodesic_initial_state(metric, x0_bwd, energy=1.0, Lz=0.0, radial_direction="outward")

        # Two coincident events at r = 6.0 (lambda = 2.0)
        def ev_bwd_unit(t: float, y: np.ndarray) -> float:
            return float(y[1] - 6.0)
        ev_bwd_unit.terminal = True; ev_bwd_unit.direction = -1; ev_bwd_unit.name = "bwd_unit"

        def ev_bwd_scaled(t: float, y: np.ndarray) -> float:
            return float((y[1] - 6.0) * 1e7)
        ev_bwd_scaled.terminal = True; ev_bwd_scaled.direction = -1; ev_bwd_scaled.name = "bwd_scaled"

        # Third omitted event at r = 15.0 (never reached during backward integration from 9.0 to 4.0)
        def ev_bwd_omitted(t: float, y: np.ndarray) -> float:
            return float(y[1] - 15.0)
        ev_bwd_omitted.terminal = True; ev_bwd_omitted.direction = -1; ev_bwd_omitted.name = "bwd_omitted"

        res = integrate_geodesic(y0_bwd, metric, (5.0, 0.0), events=[ev_bwd_unit, ev_bwd_scaled, ev_bwd_omitted])
        assert res.status == 1
        assert res.terminal_event_occurred is True
        assert np.isclose(res.lambdas[-1], 2.0, atol=1e-7)
        assert res.scipy_recorded_terminal_event_indices == (0,)
        assert res.scipy_recorded_terminal_event_names == ("bwd_unit",)
        assert res.inferred_coincident_terminal_indices == (1,)
        assert res.unresolved_terminal_indices == (2,)
        assert res.unresolved_terminal_names == ("bwd_omitted",)
        assert res.terminal_event_indices == (0, 1)
        assert res.terminal_event_names == ("bwd_unit", "bwd_scaled")
        assert res.terminal_event_identity_complete is False
        assert res.terminal_event_index is None



        assert res.terminal_event_name is None

    def test_11_dense_output_unavailable_marks_omitted_events_unresolved(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Dense output unavailable during multi-step integration conservatively marks omitted events unresolved."""
        import geodesics.integrator

        orig_solve_ivp = geodesics.integrator.solve_ivp

        def solve_ivp_without_dense_output(*args, **kwargs):
            sol = orig_solve_ivp(*args, **kwargs)
            sol.sol = None
            return sol

        monkeypatch.setattr(geodesics.integrator, "solve_ivp", solve_ivp_without_dense_output)

        metric = SchwarzschildMetric(mass=1.0)
        x0 = np.array([0.0, 10.0, np.pi / 2.0, 0.0])
        y0 = null_geodesic_initial_state(metric, x0, energy=1.0, Lz=0.0, radial_direction="inward")

        # Three events:
        # Event 0: Terminal event at r = 6.0
        # Event 1: Coincident terminal event at r = 6.0 (omitted by SciPy due to active_events[:t+1] slice)
        # Event 2: Non-terminal monitoring event at r = 8.0 (triggers along the trajectory)
        def ev0_term(t: float, y: np.ndarray) -> float:
            return float(y[1] - 6.0)
        ev0_term.terminal = True
        ev0_term.direction = -1
        ev0_term.name = "term_at_6"

        def ev1_coincident(t: float, y: np.ndarray) -> float:
            return float(y[1] - 6.0)
        ev1_coincident.terminal = True
        ev1_coincident.direction = -1
        ev1_coincident.name = "coincident_at_6"

        def ev2_monitoring(t: float, y: np.ndarray) -> float:
            return float(y[1] - 8.0)
        ev2_monitoring.terminal = False
        ev2_monitoring.direction = -1
        ev2_monitoring.name = "monitor_at_8"

        res = integrate_geodesic(
            y0,
            metric,
            (0.0, 10.0),
            events=[ev0_term, ev1_coincident, ev2_monitoring],
        )

        # 1. Integration succeeded and terminated on the terminal event
        assert res.status == 1
        assert res.terminal_event_occurred is True
        assert len(res.lambdas) >= 2  # Multi-step trajectory
        assert res.raw_solution.sol is None  # Dense output was unavailable

        # 2. SciPy-recorded terminal event identities remain intact
        assert res.scipy_recorded_terminal_event_indices == (0,)
        assert res.scipy_recorded_terminal_event_names == ("term_at_6",)

        # 3. Dense output was unavailable, so omitted event could not be recovered
        assert res.inferred_coincident_terminal_indices == ()

        # 4. Omitted terminal candidates become unresolved
        assert res.unresolved_terminal_indices == (1,)
        assert res.unresolved_terminal_names == ("coincident_at_6",)

        # 5. Non-terminal monitoring event must NOT be marked unresolved
        assert 2 not in res.unresolved_terminal_indices
        assert "monitor_at_8" not in res.unresolved_terminal_names
        # But the monitoring trigger record was preserved
        assert any(rec.name == "monitor_at_8" for rec in res.triggered_events)

        # 6. terminal_event_identity_complete is False
        assert res.terminal_event_identity_complete is False

        # 7. Unique terminal attribution is strictly None
        assert res.terminal_event_index is None
        assert res.terminal_event_name is None
        assert res.terminal_event_indices == (0,)

        # 8. Single terminal event with sol.sol = None: complete identity because no omitted candidates exist
        res_single = integrate_geodesic(
            y0,
            metric,
            (0.0, 10.0),
            events=[ev0_term, ev2_monitoring],
        )
        assert res_single.status == 1
        assert res_single.terminal_event_occurred is True
        assert res_single.scipy_recorded_terminal_event_indices == (0,)
        assert res_single.unresolved_terminal_indices == ()
        assert res_single.terminal_event_identity_complete is True
        assert res_single.terminal_event_index == 0
        assert res_single.terminal_event_name == "term_at_6"# =============================================================================
# Test Suite: VAL-EVT-16 (Circular Orbit and Initial Zero Root Semantics)
# =============================================================================

class TestCircularOrbitAndInitialRootBehavior:
    """Scientific audit: Circular photon orbit and initial-root solver semantics."""

    def test_circular_orbit_turning_point_event_halts_at_initial_step(self) -> None:
        """On an exact circular orbit (r=3M, pr=0), turning-point event halts immediately at lambda=0."""
        metric = SchwarzschildMetric(mass=1.0)
        r_circ = 3.0
        energy = 1.0
        Lz = 3.0 * np.sqrt(3.0) * energy  # Critical angular momentum for circular null orbit
        x0 = np.array([0.0, r_circ, np.pi / 2.0, 0.0])
        y0 = null_geodesic_initial_state(
            metric=metric, x=x0, energy=energy, Lz=Lz, radial_direction="inward"
        )
        assert np.isclose(y0[5], 0.0, atol=1e-14)  # pr is zero initially

        ev_turn = radial_turning_point_event(metric=metric, terminal=True, direction=0)
        result = integrate_geodesic(y0, metric, (0.0, 10.0), events=[ev_turn])

        assert result.status == 1
        assert result.terminal_event_occurred is True
        assert result.terminal_event_name == "radial_turning_point"
        assert np.isclose(result.lambdas[-1], 0.0, atol=1e-12)
        assert len(result.lambdas) == 2  # [0.0, 0.0]

    def test_initial_point_zero_terminal_vs_non_terminal(self) -> None:
        """Event zero at initial point: terminal halts at lambda=0, non-terminal logs lambda=0 and continues."""
        metric = SchwarzschildMetric(mass=1.0)
        x0 = np.array([0.0, 6.0, np.pi / 2.0, 0.0])
        y0 = null_geodesic_initial_state(
            metric=metric, x=x0, energy=1.0, Lz=0.0, radial_direction="outward"
        )

        # Event at r = 6.0 (exactly initial radius)
        ev_term = escape_radius_event(r_escape=6.0, terminal=True, direction=1)
        res_term = integrate_geodesic(y0, metric, (0.0, 5.0), events=[ev_term])
        assert res_term.status == 1
        assert np.isclose(res_term.lambdas[-1], 0.0, atol=1e-12)

        ev_nonterm = escape_radius_event(r_escape=6.0, terminal=False, direction=1)
        res_nonterm = integrate_geodesic(y0, metric, (0.0, 5.0), events=[ev_nonterm])
        assert res_nonterm.status == 0
        assert np.isclose(res_nonterm.lambdas[-1], 5.0, atol=1e-7)
        assert len(res_nonterm.triggered_events) == 1
        assert np.isclose(res_nonterm.triggered_events[0].lambdas[0], 0.0, atol=1e-12)# =============================================================================
# Test Suite: VAL-EVT-17 (Public Event API Edge Cases and Callables)
# =============================================================================

class TestPublicEventAPIEdgeCases:
    """Scientific audit: Public event API robustness, empty sequences, and arbitrary callables."""

    def test_empty_events_sequence(self) -> None:
        """Empty list events=[] executes cleanly without error."""
        metric = SchwarzschildMetric(mass=1.0)
        x0 = np.array([0.0, 5.0, np.pi / 2.0, 0.0])
        y0 = null_geodesic_initial_state(metric, x0, 1.0, 0.0)

        result = integrate_geodesic(y0, metric, (0.0, 2.0), events=[])
        assert result.success is True
        assert result.status == 0
        assert result.t_events == ()
        assert result.y_events == ()
        assert result.event_names == ()
        assert result.triggered_events == ()
        assert result.has_events is False
        assert result.terminal_event_occurred is False

    def test_arbitrary_callable_fallback_metadata(self) -> None:
        """Arbitrary callable without name, terminal, or direction uses sensible defaults."""
        metric = SchwarzschildMetric(mass=1.0)
        x0 = np.array([0.0, 5.0, np.pi / 2.0, 0.0])
        y0 = null_geodesic_initial_state(metric, x0, 1.0, 0.0, radial_direction="outward")

        def my_custom_trigger(_lambda: float, y: np.ndarray) -> float:
            return float(y[1] - 8.0)

        result = integrate_geodesic(y0, metric, (0.0, 5.0), events=my_custom_trigger)
        assert result.success is True
        assert result.status == 0  # terminal defaults to False
        assert result.event_names == ("my_custom_trigger",)
        assert result.has_events is True
        rec = result.triggered_events[0]
        assert rec.name == "my_custom_trigger"
        assert rec.terminal is False
        assert rec.direction == 0
        assert np.isclose(rec.lambdas[0], 3.0, atol=1e-7)

    def test_arbitrary_callable_invalid_direction_rejected(self) -> None:
        """Arbitrary callable with invalid direction raises ValueError."""
        metric = SchwarzschildMetric(mass=1.0)
        x0 = np.array([0.0, 5.0, np.pi / 2.0, 0.0])
        y0 = null_geodesic_initial_state(metric, x0, 1.0, 0.0)

        def bad_direction_event(_lambda: float, y: np.ndarray) -> float:
            return float(y[1] - 8.0)

        bad_direction_event.direction = 5  # Invalid direction

        with pytest.raises(ValueError, match="invalid direction"):
            integrate_geodesic(y0, metric, (0.0, 1.0), events=[bad_direction_event])# =============================================================================
# Test Suite: VAL-EVT-19 (Terminal Events When t_eval Is Supplied)
# =============================================================================class TestTerminalEventsWithTEval:
    """Audit suite: Terminal-event identity and coincidence semantics when t_eval is supplied."""

    def test_teval_terminal_event_between_requested_samples(self) -> None:
        """Case A: Terminal event occurs between requested samples.

        Verifies that the true event root (not the last requested sample) is used
        for terminal-event identity and coincidence resolution.
        """
        metric = SchwarzschildMetric(mass=1.0)
        x0 = np.array([0.0, 10.0, np.pi / 2.0, 0.0])
        y0 = null_geodesic_initial_state(metric, x0, energy=1.0, Lz=0.0, radial_direction="inward")

        # Inward ray reaches r = 4.0 at affine parameter lambda = 6.0
        ev = horizon_cutoff_event(metric=metric, epsilon=1.0, terminal=True, direction=-1)

        # t_eval samples do not include lambda = 6.0; last sample before event is 5.0
        t_eval = np.array([0.0, 2.0, 4.0, 5.0, 8.0])
        res = integrate_geodesic(y0, metric, (0.0, 10.0), events=[ev], t_eval=t_eval)

        assert res.status == 1
        assert res.terminal_event_occurred is True

        # Returned trajectory strictly follows t_eval up to termination
        np.testing.assert_allclose(res.lambdas, [0.0, 2.0, 4.0, 5.0])
        assert res.lambdas[-1] == 5.0

        # Event root is correctly recorded at lambda = 6.0, not confused with lambdas[-1] == 5.0
        assert res.t_events is not None
        assert len(res.t_events[0]) == 1
        assert np.isclose(res.t_events[0][0], 6.0, atol=1e-6)

        # Terminal event identity correctly established at the true event root
        assert res.scipy_recorded_terminal_event_indices == (0,)
        assert res.scipy_recorded_terminal_event_names == ("horizon_cutoff",)
        assert res.terminal_event_indices == (0,)
        assert res.unresolved_terminal_indices == ()
        assert res.terminal_event_identity_complete is True
        assert res.terminal_event_index == 0
        assert res.terminal_event_name == "horizon_cutoff"

    def test_teval_produces_only_one_returned_sample(self) -> None:
        """Case B: t_eval produces only one returned sample before termination.

        Verifies that a multi-step integration is not falsely classified as an
        initial-point event merely because len(sol.t) == 1.
        """
        metric = SchwarzschildMetric(mass=1.0)
        x0 = np.array([0.0, 10.0, np.pi / 2.0, 0.0])
        y0 = null_geodesic_initial_state(metric, x0, energy=1.0, Lz=0.0, radial_direction="inward")

        # Inward ray reaches r = 4.0 at lambda = 6.0
        ev = horizon_cutoff_event(metric=metric, epsilon=1.0, terminal=True, direction=-1)

        # Only lambda = 0.0 is before the event; next point is 8.0
        t_eval = np.array([0.0, 8.0])
        res = integrate_geodesic(y0, metric, (0.0, 10.0), events=[ev], t_eval=t_eval)

        assert res.status == 1
        assert res.terminal_event_occurred is True
        assert len(res.lambdas) == 1
        assert res.lambdas[0] == 0.0

        # Solver took multiple internal steps before reaching the event
        assert res.nfev > 10
        assert len(res.raw_solution.sol.interpolants) > 1

        # Event root is at lambda = 6.0, NOT at the initial point
        assert res.t_events is not None
        assert np.isclose(res.t_events[0][0], 6.0, atol=1e-6)

        # Correctly recognized as a multi-step terminal event, not initial-point root
        assert res.scipy_recorded_terminal_event_indices == (0,)
        assert res.terminal_event_indices == (0,)
        assert res.unresolved_terminal_indices == ()
        assert res.terminal_event_identity_complete is True
        assert res.terminal_event_index == 0
        assert res.terminal_event_name == "horizon_cutoff"

    def test_teval_produces_no_returned_samples_before_termination(self) -> None:
        """Case C: t_eval produces no returned samples before termination.

        Verifies that when all requested samples lie after the event root,
        sol.t/sol.y lists do not trigger AttributeError or IndexError, and
        the terminal event identity is still correctly resolved from event records.
        """
        metric = SchwarzschildMetric(mass=1.0)
        x0 = np.array([0.0, 10.0, np.pi / 2.0, 0.0])
        y0 = null_geodesic_initial_state(metric, x0, energy=1.0, Lz=0.0, radial_direction="inward")

        # Inward ray reaches r = 4.0 at lambda = 6.0
        ev = horizon_cutoff_event(metric=metric, epsilon=1.0, terminal=True, direction=-1)

        # All requested samples are after termination at lambda = 6.0
        t_eval = np.array([7.0, 8.0, 9.0])
        res = integrate_geodesic(y0, metric, (0.0, 10.0), events=[ev], t_eval=t_eval)

        assert res.status == 1
        assert res.terminal_event_occurred is True

        # Returned arrays are valid empty NumPy arrays preserving shapes
        assert isinstance(res.lambdas, np.ndarray)
        assert res.lambdas.shape == (0,)
        assert isinstance(res.states, np.ndarray)
        assert res.states.shape == (0, 8)

        # Event root is still recorded and identified
        assert res.t_events is not None
        assert np.isclose(res.t_events[0][0], 6.0, atol=1e-6)
        assert res.scipy_recorded_terminal_event_indices == (0,)
        assert res.terminal_event_indices == (0,)
        assert res.unresolved_terminal_indices == ()
        assert res.terminal_event_identity_complete is True
        assert res.terminal_event_index == 0
        assert res.terminal_event_name == "horizon_cutoff"

    def test_teval_coincident_terminal_events_recovery_and_unresolved(self) -> None:
        """Case D: Multiple terminal events (coincident + unreached) with t_eval.

        Verifies that an omitted coincident terminal event is recovered via dense
        output around the true root, while an unreached candidate is marked unresolved.
        """
        metric = SchwarzschildMetric(mass=1.0)
        x0 = np.array([0.0, 10.0, np.pi / 2.0, 0.0])
        y0 = null_geodesic_initial_state(metric, x0, energy=1.0, Lz=0.0, radial_direction="inward")

        # Two coincident terminal events at r = 4.0 (lambda = 6.0)
        ev1 = horizon_cutoff_event(metric=metric, epsilon=1.0, terminal=True, direction=-1)
        ev2 = escape_radius_event(r_escape=4.0, terminal=True, direction=-1, name="coincident_radius_4")

        # A third terminal event that is never reached (r = 25.0 in the escape direction)
        ev3 = escape_radius_event(r_escape=25.0, terminal=True, direction=1, name="unreached_escape")

        t_eval = np.array([0.0, 2.0, 4.0, 5.0, 8.0])
        res = integrate_geodesic(y0, metric, (0.0, 10.0), events=[ev1, ev2, ev3], t_eval=t_eval)

        assert res.status == 1
        assert res.terminal_event_occurred is True

        # SciPy only recorded ev1; ev2 was omitted by SciPy's active_events truncation
        assert res.scipy_recorded_terminal_event_indices == (0,)
        assert res.scipy_recorded_terminal_event_names == ("horizon_cutoff",)

        # ev2 is numerically recovered as coincident at lambda = 6.0 despite t_eval
        assert res.inferred_coincident_terminal_indices == (1,)
        assert res.terminal_event_indices == (0, 1)

        # ev3 was omitted and cannot be certified non-coincident on a scale-invariant basis
        assert res.unresolved_terminal_indices == (2,)
        assert res.unresolved_terminal_names == ("unreached_escape",)

        # Because an unresolved candidate exists, completeness is False and unique attribution is suppressed
        assert res.terminal_event_identity_complete is False
        assert res.terminal_event_index is None



        assert res.terminal_event_name is None

        # Control subcase: only coincident events registered (no unreached candidate)
        res_coinc = integrate_geodesic(y0, metric, (0.0, 10.0), events=[ev1, ev2], t_eval=t_eval)
        assert res_coinc.status == 1
        assert res_coinc.scipy_recorded_terminal_event_indices == (0,)
        assert res_coinc.inferred_coincident_terminal_indices == (1,)
        assert res_coinc.unresolved_terminal_indices == ()
        assert res_coinc.terminal_event_identity_complete is True
        assert res_coinc.terminal_event_indices == (0, 1)
        # Multiplicity suppresses unique attribution
        assert res_coinc.terminal_event_index is None
        assert res_coinc.terminal_event_name is None

    def test_teval_backward_integration_with_terminal_event(self) -> None:
        """Case E: Backward integration with t_eval and a terminal event.

        Verifies that root-time comparisons, step direction, and dense-output
        bounds remain correct in backward parameter integration when t_eval is supplied.
        """
        metric = SchwarzschildMetric(mass=1.0)
        x0_bwd = np.array([0.0, 9.0, np.pi / 2.0, 0.0])
        y0_bwd = null_geodesic_initial_state(metric, x0_bwd, energy=1.0, Lz=0.0, radial_direction="outward")

        # Inward-moving along decreasing affine parameter:
        # Integrated from lambda = 5.0 down to 0.0.
        # r(lambda) = 9.0 - (5.0 - lambda). Reaches r = 6.0 at lambda = 2.0.
        def ev_bwd(t: float, y: np.ndarray) -> float:
            return float(y[1] - 6.0)
        ev_bwd.terminal = True
        ev_bwd.direction = -1
        ev_bwd.name = "bwd_term_at_6"

        # t_eval descending from 5.0 to 0.0, skipping 2.0
        t_eval = np.array([4.5, 3.5, 2.5, 1.5, 0.5])
        res = integrate_geodesic(y0_bwd, metric, (5.0, 0.0), events=[ev_bwd], t_eval=t_eval)

        assert res.status == 1
        assert res.terminal_event_occurred is True

        # Returned trajectory follows t_eval down to 2.5 (last sample before termination at 2.0)
        np.testing.assert_allclose(res.lambdas, [4.5, 3.5, 2.5])

        # Event root is at lambda = 2.0
        assert res.t_events is not None
        assert np.isclose(res.t_events[0][0], 2.0, atol=1e-6)

        assert res.scipy_recorded_terminal_event_indices == (0,)
        assert res.scipy_recorded_terminal_event_names == ("bwd_term_at_6",)
        assert res.terminal_event_indices == (0,)
        assert res.unresolved_terminal_indices == ()
        assert res.terminal_event_identity_complete is True
        assert res.terminal_event_index == 0
        assert res.terminal_event_name == "bwd_term_at_6"# =============================================================================
# Test Suite: Dense Output Fallback Step Bounds Verification
# =============================================================================

class TestDenseOutputFallbackStepBounds:
    """Verifies defensive handling when dense output callable exists but lacks
    trustworthy final accepted-step bounds (lacks interpolants and lacks ts).

    Confirms that:
    1. Grid output samples (lambdas[-2:]) are NEVER substituted for solver step bounds.
    2. Whole-span intervals ([lambda_start, final_lambda]) are NEVER substituted for solver step bounds.
    3. SciPy-recorded terminal events are preserved intact.
    4. Omitted registered terminal events are conservatively marked unresolved.
    5. Terminal event identity completeness is False, and unique attribution is suppressed (None).
    """

    def test_dense_output_without_bounds_multi_sample_teval(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Case 1: Bare callable sol.sol (no .interpolants, no .ts) with len(lambdas) >= 2.

        In the pre-fix code, this branch would use lambdas[-2:] as step bounds,
        evaluating candidate brackets over grid output samples that do not contain
        the terminal root (since the terminal root occurs after lambdas[-1]).

        With the defensive fix, step_bounds_available is False, coincidence recovery
        is not attempted on bogus brackets, event 1 is marked unresolved, completeness
        is False, and unique attribution is suppressed.
        """
        metric = SchwarzschildMetric(mass=1.0)
        x0 = np.array([0.0, 10.0, np.pi / 2.0, 0.0])
        y0 = null_geodesic_initial_state(metric, x0, energy=1.0, Lz=0.0, radial_direction="inward")

        # Two coincident terminal events at r = 4.0 (lambda = 6.0)
        ev1 = horizon_cutoff_event(metric=metric, epsilon=1.0, terminal=True, direction=-1)
        ev2 = escape_radius_event(r_escape=4.0, terminal=True, direction=-1, name="coincident_radius_4")

        # t_eval grid with samples well before termination at lambda = 6.0
        # lambdas will contain [0.0, 2.0, 4.0, 5.0] (len >= 2)
        t_eval = np.array([0.0, 2.0, 4.0, 5.0, 8.0])

        real_solve_ivp = scipy.integrate.solve_ivp

        def mock_solve_ivp(*args, **kwargs):
            sol = real_solve_ivp(*args, **kwargs)
            # Replace sol.sol with a bare callable that has no .interpolants and no .ts attributes
            if hasattr(sol, "sol") and sol.sol is not None:
                orig_sol = sol.sol
                bare_callable = lambda t: orig_sol(t)
                sol.sol = bare_callable
            return sol

        monkeypatch.setattr("geodesics.integrator.solve_ivp", mock_solve_ivp)

        res = integrate_geodesic(y0, metric, (0.0, 10.0), events=[ev1, ev2], t_eval=t_eval)

        assert res.status == 1
        assert res.terminal_event_occurred is True

        # SciPy recorded ev1 directly
        assert res.scipy_recorded_terminal_event_indices == (0,)
        assert res.scipy_recorded_terminal_event_names == ("horizon_cutoff",)

        # Because dense output lacks trustworthy step bounds, coincidence recovery is not attempted:
        # ev2 must NOT be recovered using lambdas[-2:], but marked unresolved
        assert res.inferred_coincident_terminal_indices == ()
        assert res.terminal_event_indices == (0,)
        assert res.unresolved_terminal_indices == (1,)
        assert res.unresolved_terminal_names == ("coincident_radius_4",)

        # Completeness is False, and unique attribution is suppressed
        assert res.terminal_event_identity_complete is False
        assert res.terminal_event_index is None



        assert res.terminal_event_name is None

    def test_dense_output_without_bounds_few_samples_teval(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Case 2: Bare callable sol.sol (no .interpolants, no .ts) with len(lambdas) < 2.

        In the pre-fix code, this branch would fall back to [lambda_start, final_lambda]
        (the entire integration span from 0.0 to 6.0) as the step interval, violating
        the principle of strictly local root finding over the final accepted step.

        With the defensive fix, the integrator never substitutes the whole span for
        a final step; it marks event 1 as unresolved.
        """
        metric = SchwarzschildMetric(mass=1.0)
        x0 = np.array([0.0, 10.0, np.pi / 2.0, 0.0])
        y0 = null_geodesic_initial_state(metric, x0, energy=1.0, Lz=0.0, radial_direction="inward")

        # Two coincident terminal events at r = 4.0 (lambda = 6.0)
        ev1 = horizon_cutoff_event(metric=metric, epsilon=1.0, terminal=True, direction=-1)
        ev2 = escape_radius_event(r_escape=4.0, terminal=True, direction=-1, name="coincident_radius_4")

        # t_eval grid with only 1 sample before termination at lambda = 6.0
        # lambdas will contain [5.5] (len < 2)
        t_eval = np.array([5.5, 8.0])

        real_solve_ivp = scipy.integrate.solve_ivp

        def mock_solve_ivp(*args, **kwargs):
            sol = real_solve_ivp(*args, **kwargs)
            if hasattr(sol, "sol") and sol.sol is not None:
                orig_sol = sol.sol
                bare_callable = lambda t: orig_sol(t)
                sol.sol = bare_callable
            return sol

        monkeypatch.setattr("geodesics.integrator.solve_ivp", mock_solve_ivp)

        res = integrate_geodesic(y0, metric, (0.0, 10.0), events=[ev1, ev2], t_eval=t_eval)

        assert res.status == 1
        assert res.terminal_event_occurred is True

        # SciPy recorded ev1 directly
        assert res.scipy_recorded_terminal_event_indices == (0,)
        assert res.scipy_recorded_terminal_event_names == ("horizon_cutoff",)

        # Whole-span [0.0, 6.0] must NOT be used for root finding; ev2 must be marked unresolved
        assert res.inferred_coincident_terminal_indices == ()
        assert res.terminal_event_indices == (0,)
        assert res.unresolved_terminal_indices == (1,)
        assert res.unresolved_terminal_names == ("coincident_radius_4",)

        # Completeness is False, and unique attribution is suppressed
        assert res.terminal_event_identity_complete is False
        assert res.terminal_event_index is None



        assert res.terminal_event_name is None

    def test_dense_output_secondary_ts_fallback_valid(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Case 3: sol.sol lacks interpolants, but has valid sol.sol.ts containing final_lambda.

        Verifies that secondary fallback to sol.sol.ts[-2:] succeeds in recovering
        coincident events when the timestamps reliably describe the final step.
        """
        metric = SchwarzschildMetric(mass=1.0)
        x0 = np.array([0.0, 10.0, np.pi / 2.0, 0.0])
        y0 = null_geodesic_initial_state(metric, x0, energy=1.0, Lz=0.0, radial_direction="inward")

        ev1 = horizon_cutoff_event(metric=metric, epsilon=1.0, terminal=True, direction=-1)
        ev2 = escape_radius_event(r_escape=4.0, terminal=True, direction=-1, name="coincident_radius_4")

        real_solve_ivp = scipy.integrate.solve_ivp

        def mock_solve_ivp(*args, **kwargs):
            sol = real_solve_ivp(*args, **kwargs)
            if hasattr(sol, "sol") and sol.sol is not None:
                orig_sol = sol.sol
                # Construct a callable with ts but NO interpolants
                class CallableWithTs:
                    def __init__(self, fn, ts):
                        self.fn = fn
                        self.ts = ts
                    def __call__(self, t):
                        return self.fn(t)

                sol.sol = CallableWithTs(orig_sol, orig_sol.ts)
            return sol

        monkeypatch.setattr("geodesics.integrator.solve_ivp", mock_solve_ivp)

        res = integrate_geodesic(y0, metric, (0.0, 10.0), events=[ev1, ev2])

        assert res.status == 1
        assert res.terminal_event_occurred is True
        assert res.scipy_recorded_terminal_event_indices == (0,)
        # ev2 is recovered via secondary ts bounds
        assert res.inferred_coincident_terminal_indices == (1,)
        assert res.terminal_event_indices == (0, 1)
        assert res.unresolved_terminal_indices == ()
        assert res.terminal_event_identity_complete is True
        # Multiplicity suppresses unique attribution
        assert res.terminal_event_index is None
        assert res.terminal_event_name is None

    def test_dense_output_secondary_ts_fallback_rejected_if_root_not_contained(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Case 4: sol.sol has sol.sol.ts, but final_lambda is outside sol.sol.ts[-2:].

        Verifies that if the timestamps in sol.sol.ts[-2:] do NOT contain final_lambda,
        they are defensively rejected, no coincidence search occurs on invalid intervals,
        and omitted terminal events are marked unresolved.
        """
        metric = SchwarzschildMetric(mass=1.0)
        x0 = np.array([0.0, 10.0, np.pi / 2.0, 0.0])
        y0 = null_geodesic_initial_state(metric, x0, energy=1.0, Lz=0.0, radial_direction="inward")

        ev1 = horizon_cutoff_event(metric=metric, epsilon=1.0, terminal=True, direction=-1)
        ev2 = escape_radius_event(r_escape=4.0, terminal=True, direction=-1, name="coincident_radius_4")

        real_solve_ivp = scipy.integrate.solve_ivp

        def mock_solve_ivp(*args, **kwargs):
            sol = real_solve_ivp(*args, **kwargs)
            if hasattr(sol, "sol") and sol.sol is not None:
                orig_sol = sol.sol
                class CallableWithStaleTs:
                    def __init__(self, fn):
                        self.fn = fn
                        # Timestamps that do not contain final_lambda (e.g. [0.0, 1.0])
                        self.ts = np.array([0.0, 1.0])
                    def __call__(self, t):
                        return self.fn(t)

                sol.sol = CallableWithStaleTs(orig_sol)
            return sol

        monkeypatch.setattr("geodesics.integrator.solve_ivp", mock_solve_ivp)

        res = integrate_geodesic(y0, metric, (0.0, 10.0), events=[ev1, ev2])

        assert res.status == 1
        assert res.terminal_event_occurred is True
        assert res.scipy_recorded_terminal_event_indices == (0,)
        # ev2 cannot be recovered with stale ts bounds that don't contain 6.0; marked unresolved
        assert res.inferred_coincident_terminal_indices == ()
        assert res.terminal_event_indices == (0,)
        assert res.unresolved_terminal_indices == (1,)
        assert res.terminal_event_identity_complete is False
        assert res.terminal_event_index is None


# =============================================================================
# Test Suite: Missing Terminal Root Records Defensive Handling
# =============================================================================

class TestMissingTerminalRootRecords:
    """Verifies defensive handling when solver reports status == 1 (terminal event)
    but provides no recorded terminal event roots in sol.t_events / sol.y_events.

    Ensures that:
    1. Grid output samples (lambdas[-1]) are NEVER inferred as terminal root locations.
    2. Initial affine parameter (lambda_start) is NEVER inferred as terminal root location.
    3. No unique terminal identity is claimed (terminal_event_index/name are None).
    4. No omitted event is falsely inferred as coincident.
    5. All registered terminal candidates are marked unresolved.
    6. Terminal event identity completeness is False.
    7. Valid returned trajectory samples are preserved and not mutated with fabricated points.
    8. A control case with no registered terminal events also behaves consistently.
    """

    def test_missing_terminal_root_records_with_registered_terminal_events_and_teval(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Inconsistent solver output: status == 1, no t_events roots, registered terminal events, t_eval grid.

        Tests that an inconsistent solver result (status=1 but empty t_events)
        never falls back to requested grid samples (t_eval[-1]) or lambda_start,
        marks all registered terminal events unresolved, and sets completeness to False.
        """
        metric = SchwarzschildMetric(mass=1.0)
        x0 = np.array([0.0, 10.0, np.pi / 2.0, 0.0])
        y0 = null_geodesic_initial_state(metric, x0, energy=1.0, Lz=0.0, radial_direction="inward")

        ev1 = horizon_cutoff_event(metric=metric, epsilon=1.0, terminal=True, direction=-1)
        ev2 = escape_radius_event(r_escape=4.0, terminal=True, direction=-1, name="ev_escape_4")

        # Requested output grid
        t_eval = np.array([0.0, 1.0, 2.0, 3.0, 4.0, 5.0])

        real_solve_ivp = scipy.integrate.solve_ivp

        def mock_solve_ivp(*args, **kwargs):
            sol = real_solve_ivp(*args, **kwargs)
            # Forge inconsistent solver output: status=1, but completely empty t_events/y_events
            sol.status = 1
            sol.t_events = [np.empty(0, dtype=np.float64), np.empty(0, dtype=np.float64)]
            sol.y_events = [
                np.empty((0, STATE_DIMENSION), dtype=np.float64),
                np.empty((0, STATE_DIMENSION), dtype=np.float64),
            ]
            return sol

        monkeypatch.setattr("geodesics.integrator.solve_ivp", mock_solve_ivp)

        res = integrate_geodesic(y0, metric, (0.0, 10.0), events=[ev1, ev2], t_eval=t_eval)

        # 1. SciPy reported status == 1, so terminal_event_occurred is True
        assert res.status == 1
        assert res.terminal_event_occurred is True

        # 2. No verified terminal roots were recorded by SciPy
        assert res.scipy_recorded_terminal_event_indices == ()
        assert res.scipy_recorded_terminal_event_names == ()

        # 3. No unique terminal identity is claimed
        assert res.terminal_event_index is None
        assert res.terminal_event_name is None
        assert res.terminal_event_indices == ()
        assert res.terminal_event_names == ()

        # 4. No omitted event is falsely inferred as coincident
        assert res.inferred_coincident_terminal_indices == ()

        # 5. All registered terminal candidates are unresolved
        assert res.unresolved_terminal_indices == (0, 1)
        assert res.unresolved_terminal_names == ("horizon_cutoff", "ev_escape_4")

        # 6. Terminal event identity completeness is False
        assert res.terminal_event_identity_complete is False

        # 7. No requested output sample (such as t_eval[-1] == 5.0) is represented as a verified terminal root
        assert res.t_events is not None
        assert len(res.t_events[0]) == 0
        assert len(res.t_events[1]) == 0
        assert len(res.triggered_events) == 0

        # Trajectory data reflects solver grid output without fabrication
        np.testing.assert_allclose(res.lambdas, t_eval)

    def test_missing_terminal_root_records_control_no_registered_terminal_events(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Control case: solver reports status == 1, but NO terminal events were registered.

        Tests that even when only non-terminal events (or no events) are registered,
        the inconsistent solver status=1 cannot claim terminal identity completeness.
        """
        metric = SchwarzschildMetric(mass=1.0)
        x0 = np.array([0.0, 10.0, np.pi / 2.0, 0.0])
        y0 = null_geodesic_initial_state(metric, x0, energy=1.0, Lz=0.0, radial_direction="inward")

        # Only a non-terminal monitoring event
        ev_mon = escape_radius_event(r_escape=25.0, terminal=False, direction=1, name="non_terminal_mon")

        real_solve_ivp = scipy.integrate.solve_ivp

        def mock_solve_ivp(*args, **kwargs):
            sol = real_solve_ivp(*args, **kwargs)
            sol.status = 1
            sol.t_events = [np.empty(0, dtype=np.float64)]
            sol.y_events = [np.empty((0, STATE_DIMENSION), dtype=np.float64)]
            return sol

        monkeypatch.setattr("geodesics.integrator.solve_ivp", mock_solve_ivp)

        res = integrate_geodesic(y0, metric, (0.0, 10.0), events=[ev_mon])

        assert res.status == 1
        assert res.terminal_event_occurred is True
        assert res.scipy_recorded_terminal_event_indices == ()
        assert res.terminal_event_indices == ()
        assert res.terminal_event_index is None
        assert res.terminal_event_name is None
        assert res.inferred_coincident_terminal_indices == ()
        # No terminal events were registered, so none are in unresolved_terminal_indices
        assert res.unresolved_terminal_indices == ()
        # BUT because status == 1 occurred and zero terminal events were identified, completeness is False
        assert res.terminal_event_identity_complete is False
