"""Stateless scientific execution service for Kerr Geodesics Lab.

Dispatches simulation requests to the validated v1.0.0 Kerr Geodesic Integrator
engine without reimplementing equations of motion, metrics, conserved quantities,
or shadow boundary algorithms.
"""

from typing import Any, Dict, List, Tuple

import numpy as np

from geodesics.api.hashing import (
    compute_shadow_config_hash,
    compute_simulation_config_hash,
)
from geodesics.api.sampling import decimate_trajectory
from geodesics.api.schemas import (
    ConservedQuantities,
    EventTriggerItem,
    PRESET_PARAM_MODELS,
    PresetMetadata,
    Provenance,
    ShadowObservables,
    ShadowRequest,
    ShadowResponse,
    SimulationRequest,
    SimulationResponse,
    SolverDiagnostics,
    TrajectoryCoordinates,
    TrajectoryData,
    TrajectoryMomenta,
)
from geodesics.events import (
    escape_radius_event,
    horizon_cutoff_event,
    radial_turning_point_event,
)
from geodesics.hamiltonian import (
    carter_constant,
    hamiltonian_value,
)
from geodesics.initial_conditions import (
    kerr_circular_timelike_initial_state,
    kerr_equatorial_photon_orbit_initial_state,
    kerr_isco_radius,
    schwarzschild_circular_timelike_initial_state,
    schwarzschild_perturbed_circular_timelike_initial_state,
    schwarzschild_photon_sphere_initial_state,
)
from geodesics.integrator import integrate_geodesic
from geodesics.metrics.kerr import KerrMetric
from geodesics.metrics.schwarzschild import SchwarzschildMetric
from geodesics.scattering import (
    classify_equatorial_photon_trajectory,
    integrate_equatorial_photon,
)
from geodesics.shadow import kerr_shadow_boundary


# -----------------------------------------------------------------------------
# Preset Registry and Catalogue Definition
# -----------------------------------------------------------------------------

PRESET_METADATA_CATALOGUE: List[PresetMetadata] = [
    PresetMetadata(
        id="schwarzschild_isco_circular",
        name="Schwarzschild ISCO Circular Orbit",
        description=(
            "Marginally stable equatorial circular timelike orbit at the innermost "
            "stable circular orbit (r = 6M) in Schwarzschild spacetime."
        ),
        spacetime="Schwarzschild",
        geodesic_type="timelike",
        default_parameters={"mass": 1.0, "affine_span": 50.0},
        parameter_schema=PRESET_PARAM_MODELS["schwarzschild_isco_circular"].model_json_schema(),
    ),
    PresetMetadata(
        id="schwarzschild_precession",
        name="Schwarzschild Relativistic Periastron Precession",
        description=(
            "Bound eccentric timelike orbit exhibiting relativistic periastron precession "
            "outside ISCO (r > 6M, E < 1) in Schwarzschild spacetime."
        ),
        spacetime="Schwarzschild",
        geodesic_type="timelike",
        default_parameters={"mass": 1.0, "radius": 8.0, "delta_pr": 0.001, "affine_span": 100.0},
        parameter_schema=PRESET_PARAM_MODELS["schwarzschild_precession"].model_json_schema(),
    ),
    PresetMetadata(
        id="schwarzschild_photon_sphere",
        name="Schwarzschild Circular Photon Sphere Orbit",
        description=(
            "Exact unperturbed unstable circular null orbit at the photon sphere (r = 3M) "
            "in Schwarzschild spacetime."
        ),
        spacetime="Schwarzschild",
        geodesic_type="null",
        default_parameters={"mass": 1.0, "energy": 1.0, "affine_span": 12.0},
        parameter_schema=PRESET_PARAM_MODELS["schwarzschild_photon_sphere"].model_json_schema(),
    ),
    PresetMetadata(
        id="kerr_equatorial_prograde_photon",
        name="Kerr Equatorial Prograde Photon Orbit",
        description=(
            "Unstable co-rotating circular null geodesic at the prograde photon orbit "
            "radius r_ph^+ in Kerr spacetime."
        ),
        spacetime="Kerr",
        geodesic_type="null",
        default_parameters={"mass": 1.0, "spin": 0.9, "energy": 1.0, "affine_span": 20.0},
        parameter_schema=PRESET_PARAM_MODELS["kerr_equatorial_prograde_photon"].model_json_schema(),
    ),
    PresetMetadata(
        id="kerr_equatorial_retrograde_photon",
        name="Kerr Equatorial Retrograde Photon Orbit",
        description=(
            "Unstable counter-rotating circular null geodesic at the retrograde photon orbit "
            "radius r_ph^- in Kerr spacetime."
        ),
        spacetime="Kerr",
        geodesic_type="null",
        default_parameters={"mass": 1.0, "spin": 0.9, "energy": 1.0, "affine_span": 30.0},
        parameter_schema=PRESET_PARAM_MODELS["kerr_equatorial_retrograde_photon"].model_json_schema(),
    ),
    PresetMetadata(
        id="kerr_circular_timelike",
        name="Kerr Equatorial Circular Timelike Orbit",
        description=(
            "Stable equatorial circular timelike orbit outside the Kerr ISCO (r > r_ISCO) "
            "in Kerr spacetime."
        ),
        spacetime="Kerr",
        geodesic_type="timelike",
        default_parameters={"mass": 1.0, "spin": 0.9, "radius": 6.0, "affine_span": 100.0},
        parameter_schema=PRESET_PARAM_MODELS["kerr_circular_timelike"].model_json_schema(),
    ),
    PresetMetadata(
        id="kerr_equatorial_scattering",
        name="Kerr Equatorial Photon Scattering",
        description=(
            "Equatorial null geodesic launched from asymptotic infinity (r0 >= 10M) testing "
            "capture versus escape across the critical impact parameter b_crit in Kerr spacetime."
        ),
        spacetime="Kerr",
        geodesic_type="null",
        default_parameters={
            "mass": 1.0,
            "spin": 0.5,
            "impact_parameter": 4.5,
            "r0": 50.0,
            "energy": 1.0,
            "affine_span": 200.0,
        },
        parameter_schema=PRESET_PARAM_MODELS["kerr_equatorial_scattering"].model_json_schema(),
    ),
]


# -----------------------------------------------------------------------------
# Simulation Execution Service
# -----------------------------------------------------------------------------

def run_simulation(request: SimulationRequest) -> SimulationResponse:
    """Executes a simulation request by dispatching to the underlying engine."""
    preset_id = request.preset_id
    if preset_id not in PRESET_PARAM_MODELS:
        raise KeyError(
            f"Preset '{preset_id}' is not supported. Supported presets: "
            f"{list(PRESET_PARAM_MODELS.keys())}"
        )

    # Validate parameters with strict schema
    param_cls = PRESET_PARAM_MODELS[preset_id]
    raw_params = request.parameters or {}
    validated_params = param_cls.model_validate(raw_params)
    param_dict = validated_params.model_dump()

    # Compute deterministic configuration hash
    config_hash = compute_simulation_config_hash(preset_id, param_dict)

    # Dispatch to specific preset runner
    if preset_id == "schwarzschild_isco_circular":
        mass = validated_params.mass
        span = validated_params.affine_span
        metric = SchwarzschildMetric(mass=mass)
        y0 = schwarzschild_circular_timelike_initial_state(metric, r=6.0 * mass, prograde=True)
        events = (
            horizon_cutoff_event(metric),
            escape_radius_event(r_escape=100.0 * mass),
            radial_turning_point_event(metric, terminal=False),
        )
        result = integrate_geodesic(y0, metric, (0.0, span), events=events, max_step=0.5)
        mu_val = 1.0

    elif preset_id == "schwarzschild_precession":
        mass = validated_params.mass
        r_val = validated_params.radius
        delta_pr = validated_params.delta_pr
        span = validated_params.affine_span
        metric = SchwarzschildMetric(mass=mass)
        y0 = schwarzschild_perturbed_circular_timelike_initial_state(
            metric, r=r_val, delta_pr=delta_pr, prograde=True
        )
        events = (
            horizon_cutoff_event(metric),
            escape_radius_event(r_escape=100.0 * mass),
            radial_turning_point_event(metric, terminal=False),
        )
        result = integrate_geodesic(y0, metric, (0.0, span), events=events, max_step=0.5)
        mu_val = 1.0

    elif preset_id == "schwarzschild_photon_sphere":
        mass = validated_params.mass
        energy = validated_params.energy
        span = validated_params.affine_span
        metric = SchwarzschildMetric(mass=mass)
        y0 = schwarzschild_photon_sphere_initial_state(metric, energy=energy, prograde=True)
        events = (
            horizon_cutoff_event(metric),
            escape_radius_event(r_escape=50.0 * mass),
            radial_turning_point_event(metric, terminal=False),
        )
        result = integrate_geodesic(y0, metric, (0.0, span), events=events, max_step=0.5)
        mu_val = 0.0

    elif preset_id == "kerr_equatorial_prograde_photon":
        mass = validated_params.mass
        spin = validated_params.spin
        energy = validated_params.energy
        span = validated_params.affine_span
        metric = KerrMetric(mass=mass, spin=spin)
        y0 = kerr_equatorial_photon_orbit_initial_state(
            metric, energy=energy, spin=spin, prograde=True, allow_extremal=False
        )
        events = (
            horizon_cutoff_event(metric),
            escape_radius_event(r_escape=50.0 * mass),
            radial_turning_point_event(metric, terminal=False),
        )
        result = integrate_geodesic(y0, metric, (0.0, span), events=events, max_step=0.5)
        mu_val = 0.0

    elif preset_id == "kerr_equatorial_retrograde_photon":
        mass = validated_params.mass
        spin = validated_params.spin
        energy = validated_params.energy
        span = validated_params.affine_span
        metric = KerrMetric(mass=mass, spin=spin)
        y0 = kerr_equatorial_photon_orbit_initial_state(
            metric, energy=energy, spin=spin, prograde=False, allow_extremal=True
        )
        events = (
            horizon_cutoff_event(metric),
            escape_radius_event(r_escape=50.0 * mass),
            radial_turning_point_event(metric, terminal=False),
        )
        result = integrate_geodesic(y0, metric, (0.0, span), events=events, max_step=0.5)
        mu_val = 0.0

    elif preset_id == "kerr_circular_timelike":
        mass = validated_params.mass
        spin = validated_params.spin
        r_val = validated_params.radius
        span = validated_params.affine_span
        metric = KerrMetric(mass=mass, spin=spin)
        y0 = kerr_circular_timelike_initial_state(metric, r=r_val, prograde=True)
        events = (
            horizon_cutoff_event(metric),
            escape_radius_event(r_escape=100.0 * mass),
            radial_turning_point_event(metric, terminal=False),
        )
        result = integrate_geodesic(y0, metric, (0.0, span), events=events, max_step=0.5)
        mu_val = 1.0

    elif preset_id == "kerr_equatorial_scattering":
        mass = validated_params.mass
        spin = validated_params.spin
        b_val = validated_params.impact_parameter
        r0_val = validated_params.r0
        energy = validated_params.energy
        span = validated_params.affine_span
        metric = KerrMetric(mass=mass, spin=spin)
        result = integrate_equatorial_photon(
            metric=metric,
            b=b_val,
            r0=r0_val,
            energy=energy,
            lambda_span=(0.0, span),
            max_step=0.5,
        )
        mu_val = 0.0

    else:
        raise KeyError(f"Unsupported preset '{preset_id}'")

    if not result.success:
        raise RuntimeError(
            f"Numerical integration failed: status={result.status}, message='{result.message}'"
        )

    # Trajectory decimation (guaranteed <= 500 points)
    dec_lambdas, dec_states = decimate_trajectory(
        lambdas=result.lambdas,
        states=result.states,
        triggered_events=result.triggered_events,
        max_points=500,
    )

    # Conserved quantities & Hamiltonian drift
    h0 = hamiltonian_value(result.states[0, :4], result.states[0, 4:], metric)
    h_drifts = [
        abs(hamiltonian_value(s[:4], s[4:], metric) - h0) for s in dec_states
    ]
    max_h_drift = float(np.max(h_drifts)) if h_drifts else 0.0

    energy_val = float(-result.states[0, 4])
    lz_val = float(result.states[0, 7])

    if isinstance(metric, KerrMetric):
        q_val = float(carter_constant(result.states[0], metric, mu=mu_val))
    else:
        # In Schwarzschild equatorial motion, Q vanishes identically
        q_val = 0.0

    # Format triggered events
    event_items: List[EventTriggerItem] = []
    if result.triggered_events:
        for rec in result.triggered_events:
            for l_v, s_v in zip(rec.lambdas, rec.states):
                s_list = [float(x) for x in s_v]
                event_items.append(
                    EventTriggerItem(
                        name=rec.name,
                        lambda_=float(l_v),
                        t=s_list[0],
                        r=s_list[1],
                        theta=s_list[2],
                        phi=s_list[3],
                        p_t=s_list[4],
                        p_r=s_list[5],
                        p_theta=s_list[6],
                        p_phi=s_list[7],
                        state=s_list,
                        terminal=rec.terminal,
                    )
                )

    # Status and termination
    if result.terminal_event_occurred:
        term_reason = f"Terminated by event '{result.terminal_event_name}'"
    else:
        term_reason = result.message

    status_str = "completed" if result.success else "failed"

    return SimulationResponse(
        preset_id=preset_id,
        config_hash=config_hash,
        status=status_str,
        termination_reason=term_reason,
        solver_diagnostics=SolverDiagnostics(
            method=result.method,
            nfev=result.nfev,
            rtol=result.rtol,
            atol=result.atol,
        ),
        trajectory=TrajectoryData(
            lambdas=[float(x) for x in dec_lambdas],
            coordinates=TrajectoryCoordinates(
                t=[float(s[0]) for s in dec_states],
                r=[float(s[1]) for s in dec_states],
                theta=[float(s[2]) for s in dec_states],
                phi=[float(s[3]) for s in dec_states],
            ),
            momenta=TrajectoryMomenta(
                p_t=[float(s[4]) for s in dec_states],
                p_r=[float(s[5]) for s in dec_states],
                p_theta=[float(s[6]) for s in dec_states],
                p_phi=[float(s[7]) for s in dec_states],
            ),
        ),
        conserved_quantities=ConservedQuantities(
            energy=energy_val,
            angular_momentum=lz_val,
            carter_constant=q_val,
            hamiltonian_drift_max=max_h_drift,
        ),
        triggered_events=event_items,
        provenance=Provenance(),
    )


# -----------------------------------------------------------------------------
# Shadow Execution Service
# -----------------------------------------------------------------------------

def run_shadow(request: ShadowRequest) -> ShadowResponse:
    """Executes an analytical Kerr black hole shadow boundary construction."""
    mass = request.mass
    spin = request.spin
    theta_o = request.observer_inclination
    n_pts = request.num_points

    if spin == 0.0:
        metric = SchwarzschildMetric(mass=mass)
    else:
        metric = KerrMetric(mass=mass, spin=spin)

    curve = kerr_shadow_boundary(
        metric=metric, observer_inclination=theta_o, n_points=n_pts
    )

    config_hash = compute_shadow_config_hash(
        mass=mass,
        spin=spin,
        observer_inclination=theta_o,
        num_points=n_pts,
    )

    return ShadowResponse(
        alpha=[float(x) for x in curve.alpha],
        beta=[float(y) for y in curve.beta],
        observables=ShadowObservables(
            area=float(curve.area),
            centroid=(float(curve.centroid[0]), float(curve.centroid[1])),
            width=float(curve.width),
            height=float(curve.height),
        ),
        provenance=Provenance(),
        config_hash=config_hash,
    )
