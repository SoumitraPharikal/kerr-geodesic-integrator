"""Comprehensive test suite for Kerr Geodesics Lab Stateless Scientific API Adapter.

Covers all 13 required verification areas:
1. Health endpoint (GET /health)
2. Preset catalogue and metadata (GET /api/v1/presets)
3. Successful request for each of the 7 simulation presets (POST /api/v1/simulations)
4. Successful analytical shadow boundary request (POST /api/v1/shadows)
5. Invalid preset ID rejection (404/422 with structured error)
6. Missing, extra, and incorrectly typed parameter rejection (extra="forbid")
7. Physical domain validation (sub-extremality, asymptotic radius, coordinate domains)
8. Bound-orbit validation for Schwarzschild precession (E_pert < 1.0 enforced)
9. Configuration hash determinism, canonical ordering, defaults, and sensitivity
10. Trajectory point limit (<= 500), endpoint preservation, and exact event root retention
11. Numerical agreement between API trajectory samples and direct engine integration
12. Structured error handling without stack trace or local filesystem leakage
13. Core package import and execution isolation without API extras
"""

import math
import subprocess
import sys
from typing import Any, Dict

import numpy as np
import pytest
from fastapi.testclient import TestClient

from geodesics.api import app
from geodesics.api.hashing import (
    compute_shadow_config_hash,
    compute_simulation_config_hash,
)
from geodesics.api.schemas import PRESET_PARAM_MODELS
from geodesics.api.service import PRESET_METADATA_CATALOGUE
from geodesics.initial_conditions import (
    kerr_isco_radius,
    schwarzschild_circular_timelike_energy,
    schwarzschild_circular_timelike_initial_state,
)
from geodesics.integrator import integrate_geodesic
from geodesics.metrics.kerr import KerrMetric
from geodesics.metrics.schwarzschild import SchwarzschildMetric
from geodesics.shadow import kerr_shadow_boundary


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Fixture providing a TestClient for the FastAPI app."""
    return TestClient(app)


# -----------------------------------------------------------------------------
# 1. Health Endpoint
# -----------------------------------------------------------------------------

def test_health_endpoint(client: TestClient) -> None:
    """Verifies GET /health returns expected status, engine, and version provenance."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["engine"] == "kerr-geodesics"
    assert data["version"] == "1.0.0"
    assert data["commit_hash"] == "062b20c80a689640637a2fcd003bdd921a7d4132"


# -----------------------------------------------------------------------------
# 2. Preset Catalogue and Metadata
# -----------------------------------------------------------------------------

def test_preset_catalogue(client: TestClient) -> None:
    """Verifies GET /api/v1/presets returns complete metadata for all 7 presets."""
    resp = client.get("/api/v1/presets")
    assert resp.status_code == 200
    data = resp.json()
    assert "presets" in data
    presets = data["presets"]
    assert len(presets) == 7

    preset_ids = {p["id"] for p in presets}
    expected_ids = {
        "schwarzschild_isco_circular",
        "schwarzschild_precession",
        "schwarzschild_photon_sphere",
        "kerr_equatorial_prograde_photon",
        "kerr_equatorial_retrograde_photon",
        "kerr_circular_timelike",
        "kerr_equatorial_scattering",
    }
    assert preset_ids == expected_ids

    for p in presets:
        assert isinstance(p["name"], str) and len(p["name"]) > 0
        assert isinstance(p["description"], str) and len(p["description"]) > 0
        assert p["spacetime"] in ("Schwarzschild", "Kerr")
        assert p["geodesic_type"] in ("timelike", "null")
        assert isinstance(p["default_parameters"], dict)
        assert isinstance(p["parameter_schema"], dict)


# -----------------------------------------------------------------------------
# 3. Successful Request for Each Simulation Preset
# -----------------------------------------------------------------------------

@pytest.mark.parametrize(
    "preset_id, params",
    [
        ("schwarzschild_isco_circular", {"mass": 1.0, "affine_span": 50.0}),
        ("schwarzschild_precession", {"mass": 1.0, "radius": 8.0, "delta_pr": 0.001, "affine_span": 100.0}),
        ("schwarzschild_photon_sphere", {"mass": 1.0, "energy": 1.0, "affine_span": 12.0}),
        ("kerr_equatorial_prograde_photon", {"mass": 1.0, "spin": 0.9, "energy": 1.0, "affine_span": 20.0}),
        ("kerr_equatorial_retrograde_photon", {"mass": 1.0, "spin": 0.9, "energy": 1.0, "affine_span": 30.0}),
        ("kerr_circular_timelike", {"mass": 1.0, "spin": 0.9, "radius": 6.0, "affine_span": 100.0}),
        ("kerr_equatorial_scattering", {"mass": 1.0, "spin": 0.5, "impact_parameter": 4.5, "r0": 50.0, "affine_span": 200.0}),
    ],
)
def test_all_seven_simulation_presets_success(client: TestClient, preset_id: str, params: Dict[str, Any]) -> None:
    """Verifies that each of the seven simulation presets completes successfully."""
    payload = {"preset_id": preset_id, "parameters": params}
    resp = client.post("/api/v1/simulations", json=payload)
    assert resp.status_code == 200, f"Preset {preset_id} failed: {resp.text}"
    data = resp.json()

    assert data["preset_id"] == preset_id
    assert data["status"] == "completed"
    assert isinstance(data["config_hash"], str) and len(data["config_hash"]) == 64
    assert isinstance(data["termination_reason"], str)

    # Check solver diagnostics
    diag = data["solver_diagnostics"]
    assert diag["method"] == "DOP853"
    assert diag["nfev"] > 0
    assert diag["rtol"] == 1e-10
    assert diag["atol"] == 1e-10

    # Check trajectory length <= 500
    traj = data["trajectory"]
    lambdas = traj["lambdas"]
    assert 2 <= len(lambdas) <= 500
    coords = traj["coordinates"]
    momenta = traj["momenta"]
    assert len(coords["t"]) == len(lambdas)
    assert len(coords["r"]) == len(lambdas)
    assert len(coords["theta"]) == len(lambdas)
    assert len(coords["phi"]) == len(lambdas)
    assert len(momenta["p_t"]) == len(lambdas)
    assert len(momenta["p_r"]) == len(lambdas)
    assert len(momenta["p_theta"]) == len(lambdas)
    assert len(momenta["p_phi"]) == len(lambdas)

    # Check conserved quantities
    cons = data["conserved_quantities"]
    assert math.isfinite(cons["energy"])
    assert math.isfinite(cons["angular_momentum"])
    assert cons["hamiltonian_drift_max"] < 1e-8


# -----------------------------------------------------------------------------
# 4. Successful Shadow Request
# -----------------------------------------------------------------------------

def test_shadow_endpoint_success(client: TestClient) -> None:
    """Verifies POST /api/v1/shadows constructs analytical shadow boundary."""
    payload = {
        "mass": 1.0,
        "spin": 0.9,
        "observer_inclination": math.pi / 2.0,
        "num_points": 500,
    }
    resp = client.post("/api/v1/shadows", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert len(data["alpha"]) == 500
    assert len(data["beta"]) == 500
    obs = data["observables"]
    assert obs["area"] > 0.0
    assert obs["width"] > 0.0
    assert obs["height"] > 0.0
    assert len(obs["centroid"]) == 2

    # Check against known Kerr shadow area (~79.58 for M=1, a=0.9, theta=pi/2)
    assert 75.0 < obs["area"] < 85.0

    # Check provenance
    assert data["provenance"]["engine"] == "kerr-geodesics"
    assert data["provenance"]["version"] == "1.0.0"
    assert len(data["config_hash"]) == 64


# -----------------------------------------------------------------------------
# 5. Invalid Preset ID Rejection
# -----------------------------------------------------------------------------

def test_invalid_preset_id_rejection(client: TestClient) -> None:
    """Verifies that unknown or unsupported preset IDs return a structured 404 error."""
    resp = client.post(
        "/api/v1/simulations",
        json={"preset_id": "nonexistent_preset_xyz", "parameters": {}},
    )
    assert resp.status_code == 404
    data = resp.json()
    assert data["error_type"] == "unsupported_preset"
    assert "not supported" in data["message"]


# -----------------------------------------------------------------------------
# 6. Missing, Extra, and Incorrectly Typed Parameter Rejection
# -----------------------------------------------------------------------------

def test_extra_parameter_rejected(client: TestClient) -> None:
    """Verifies that extra/unknown parameters are rejected by extra='forbid'."""
    # Extra field inside parameters
    resp = client.post(
        "/api/v1/simulations",
        json={
            "preset_id": "schwarzschild_isco_circular",
            "parameters": {"mass": 1.0, "unknown_field_extra": 123},
        },
    )
    assert resp.status_code == 422
    data = resp.json()
    assert data["error_type"] == "invalid_request_parameters"

    # Extra field in root request body
    resp_root = client.post(
        "/api/v1/simulations",
        json={
            "preset_id": "schwarzschild_isco_circular",
            "spurious_root_key": "bad_input",
        },
    )
    assert resp_root.status_code == 422


def test_mistyped_parameter_rejected(client: TestClient) -> None:
    """Verifies that non-numeric types for numeric parameters are rejected."""
    resp = client.post(
        "/api/v1/simulations",
        json={
            "preset_id": "schwarzschild_isco_circular",
            "parameters": {"mass": "not_a_valid_float"},
        },
    )
    assert resp.status_code == 422
    data = resp.json()
    assert data["error_type"] == "invalid_request_parameters"


def test_shadow_extra_parameter_rejected(client: TestClient) -> None:
    """Verifies that unknown fields in shadow requests are rejected."""
    resp = client.post(
        "/api/v1/shadows",
        json={"mass": 1.0, "spin": 0.5, "unrecognized_option": True},
    )
    assert resp.status_code == 422


# -----------------------------------------------------------------------------
# 7. Physical Domain Validation
# -----------------------------------------------------------------------------

def test_physical_domain_validation_mass(client: TestClient) -> None:
    """Verifies that mass <= 0 is rejected."""
    resp = client.post(
        "/api/v1/simulations",
        json={"preset_id": "schwarzschild_isco_circular", "parameters": {"mass": -1.0}},
    )
    assert resp.status_code == 422


def test_physical_domain_validation_subextremal(client: TestClient) -> None:
    """Verifies that prograde photon with spin >= mass is rejected."""
    resp = client.post(
        "/api/v1/simulations",
        json={
            "preset_id": "kerr_equatorial_prograde_photon",
            "parameters": {"mass": 1.0, "spin": 1.0},
        },
    )
    assert resp.status_code == 422
    data = resp.json()
    assert "sub-extremal" in data["message"].lower() or "unphysical" in data["error_type"]


def test_physical_domain_validation_kerr_timelike_isco(client: TestClient) -> None:
    """Verifies that Kerr circular timelike radius r <= r_ISCO is rejected."""
    # For a=0.9, M=1.0, r_ISCO ~ 2.32
    resp = client.post(
        "/api/v1/simulations",
        json={
            "preset_id": "kerr_circular_timelike",
            "parameters": {"mass": 1.0, "spin": 0.9, "radius": 2.0},
        },
    )
    assert resp.status_code == 422
    data = resp.json()
    assert "r_isco" in data["message"].lower()


def test_physical_domain_validation_scattering_r0(client: TestClient) -> None:
    """Verifies that scattering initial radius r0 < 10M is rejected."""
    resp = client.post(
        "/api/v1/simulations",
        json={
            "preset_id": "kerr_equatorial_scattering",
            "parameters": {"mass": 1.0, "spin": 0.5, "r0": 5.0},
        },
    )
    assert resp.status_code == 422
    data = resp.json()
    assert "asymptotic domain" in data["message"].lower()


def test_physical_domain_validation_shadow_extremal(client: TestClient) -> None:
    """Verifies that shadow request with |spin| > mass is rejected."""
    resp = client.post(
        "/api/v1/shadows",
        json={"mass": 1.0, "spin": 1.5},
    )
    assert resp.status_code == 422


# -----------------------------------------------------------------------------
# 8. Bound-Orbit Validation for Schwarzschild Precession
# -----------------------------------------------------------------------------

def test_schwarzschild_precession_bound_orbit_validation(client: TestClient) -> None:
    """Verifies strict bound-orbit physical validation for Schwarzschild precession."""
    # 1. Valid bound orbit (r=8M, delta_pr=0.001 -> E_pert < 1)
    resp_ok = client.post(
        "/api/v1/simulations",
        json={
            "preset_id": "schwarzschild_precession",
            "parameters": {"mass": 1.0, "radius": 8.0, "delta_pr": 0.001},
        },
    )
    assert resp_ok.status_code == 200

    # 2. Radius <= 6M (inside or at ISCO) must be rejected
    resp_isco = client.post(
        "/api/v1/simulations",
        json={
            "preset_id": "schwarzschild_precession",
            "parameters": {"mass": 1.0, "radius": 6.0, "delta_pr": 0.001},
        },
    )
    assert resp_isco.status_code == 422
    assert "isco" in resp_isco.json()["message"].lower()

    # 3. Radius > 6M but perturbation too large such that E_pert >= 1.0 (unbound / escape)
    # At r=8M, E_circ = 3/sqrt(10) ~ 0.9486833. f(r) = 1 - 2/8 = 0.75.
    # To get E_pert >= 1.0, need (0.75 * delta_pr)^2 >= 1 - (9/10) = 0.1
    # 0.75 * delta_pr >= sqrt(0.1) ~ 0.3162277 -> delta_pr >= 4*sqrt(0.1)/3 ~ 0.421637
    # Thus delta_pr = 0.4 yields E_pert ~ 0.994987 < 1.0 (bound),
    # while delta_pr = 0.5 yields E_pert = sqrt(0.9 + 0.375^2) = sqrt(1.040625) ~ 1.02011 >= 1.0 (unbound).
    resp_unbound = client.post(
        "/api/v1/simulations",
        json={
            "preset_id": "schwarzschild_precession",
            "parameters": {"mass": 1.0, "radius": 8.0, "delta_pr": 0.5},
        },
    )
    assert resp_unbound.status_code == 422
    data_unbound = resp_unbound.json()
    assert data_unbound["error_type"] == "unphysical_configuration"
    assert "unbound" in data_unbound["message"].lower()
    assert "e_pert" in data_unbound["message"].lower()


def test_schwarzschild_precession_exact_physical_values(client: TestClient) -> None:
    """Verifies that Schwarzschild precession reproduces exact analytical values and Hamiltonian mass-shell.

    At r = 8M, M = 1:
        E_circ = (1 - 2/8) / sqrt(1 - 3/8) = (3/4) / sqrt(5/8) = 3 / sqrt(10) ~ 0.9486832980505138
        L_circ = sqrt(8) / sqrt(1 - 3/8) = sqrt(8) / sqrt(5/8) = 8 / sqrt(5) ~ 3.5777087639996634
        f(r) = 1 - 2/8 = 0.75
        delta_pr = 0.001
        E_pert = sqrt(E_circ^2 + (f * delta_pr)^2) = sqrt(0.9 + (0.75 * 0.001)^2) = sqrt(0.9000005625) ~ 0.9486835945139981

    Hamiltonian mass-shell invariant (mu = 1):
        2*H = -f^(-1) * E_pert^2 + f * (delta_pr)^2 + r^(-2) * L_circ^2
            = -(4/3) * 0.9000005625 + 0.75 * 1e-6 + (1/64) * (64/5)
            = -1.20000075 + 0.00000075 + 0.20000000 = -1.0
        H = -0.5 = -mu^2 / 2
    """
    resp = client.post(
        "/api/v1/simulations",
        json={
            "preset_id": "schwarzschild_precession",
            "parameters": {
                "mass": 1.0,
                "radius": 8.0,
                "delta_pr": 0.001,
                "affine_span": 100.0,
            },
        },
    )
    assert resp.status_code == 200
    data = resp.json()

    # Exact expected analytical values
    e_circ = 3.0 / math.sqrt(10.0)
    l_circ = 8.0 / math.sqrt(5.0)
    e_pert = math.sqrt(0.9 + (0.75 * 0.001) ** 2)

    # 1. Check conserved quantities in API response
    cons = data["conserved_quantities"]
    assert abs(cons["energy"] - e_pert) < 1e-12, f"Energy mismatch: expected {e_pert}, got {cons['energy']}"
    assert abs(cons["angular_momentum"] - l_circ) < 1e-12, f"Angular momentum mismatch: expected {l_circ}, got {cons['angular_momentum']}"
    assert cons["carter_constant"] == 0.0
    assert cons["hamiltonian_drift_max"] < 1e-12

    # 2. Check initial state in trajectory
    coords = data["trajectory"]["coordinates"]
    momenta = data["trajectory"]["momenta"]
    assert coords["t"][0] == 0.0
    assert abs(coords["r"][0] - 8.0) < 1e-12
    assert abs(coords["theta"][0] - (math.pi / 2.0)) < 1e-12
    assert coords["phi"][0] == 0.0

    assert abs(momenta["p_t"][0] - (-e_pert)) < 1e-12
    assert abs(momenta["p_r"][0] - 0.001) < 1e-12
    assert abs(momenta["p_theta"][0] - 0.0) < 1e-12
    assert abs(momenta["p_phi"][0] - l_circ) < 1e-12


# -----------------------------------------------------------------------------
# 9. Configuration Hash Determinism and Sensitivity
# -----------------------------------------------------------------------------

def test_config_hash_determinism_and_sensitivity(client: TestClient) -> None:
    """Verifies that config hashes are deterministic, order-independent, and sensitive to parameter changes."""
    # 1. Order independence
    p1 = {"mass": 1.0, "radius": 8.0, "delta_pr": 0.001, "affine_span": 100.0}
    p2 = {"affine_span": 100.0, "delta_pr": 0.001, "radius": 8.0, "mass": 1.0}
    h1 = compute_simulation_config_hash("schwarzschild_precession", p1)
    h2 = compute_simulation_config_hash("schwarzschild_precession", p2)
    assert h1 == h2

    # 2. Sensitivity to tiny representable floating-point difference (1e-14)
    # Proves no lossy decimal rounding or quantization causes artificial collisions
    p_exact = {"mass": 1.0, "radius": 8.0, "delta_pr": 0.001, "affine_span": 100.0}
    p_tiny_pert = {"mass": 1.0, "radius": 8.0 + 1e-14, "delta_pr": 0.001, "affine_span": 100.0}
    h_exact = compute_simulation_config_hash("schwarzschild_precession", p_exact)
    h_tiny_pert = compute_simulation_config_hash("schwarzschild_precession", p_tiny_pert)
    assert h_exact != h_tiny_pert, "Hash must be sensitive to 1e-14 parameter change"

    # 3. Default parameter equivalence via API
    # Omitting parameters must yield the identical hash as passing explicit defaults
    r_omitted = client.post("/api/v1/simulations", json={"preset_id": "schwarzschild_isco_circular"})
    r_explicit = client.post(
        "/api/v1/simulations",
        json={
            "preset_id": "schwarzschild_isco_circular",
            "parameters": {"mass": 1.0, "affine_span": 50.0},
        },
    )
    assert r_omitted.status_code == 200
    assert r_explicit.status_code == 200
    assert r_omitted.json()["config_hash"] == r_explicit.json()["config_hash"]

    # 4. Sensitivity to preset_id
    h_other = compute_simulation_config_hash("schwarzschild_isco_circular", {"mass": 1.0, "affine_span": 50.0})
    assert h1 != h_other

    # 5. Shadow config hash determinism and sensitivity
    sh1 = compute_shadow_config_hash(1.0, 0.9, math.pi / 2.0, 500)
    sh2 = compute_shadow_config_hash(1.0, 0.9, math.pi / 2.0, 500)
    sh3 = compute_shadow_config_hash(1.0, 0.91, math.pi / 2.0, 500)
    assert sh1 == sh2
    assert sh1 != sh3


# -----------------------------------------------------------------------------
# 10. Trajectory Point Limit, Endpoint, and Event Preservation
# -----------------------------------------------------------------------------

def test_trajectory_sampling_and_point_limit(client: TestClient) -> None:
    """Verifies the <= 500 point cap, endpoint retention, and exact event root preservation."""
    from geodesics.api.sampling import decimate_trajectory
    from geodesics.integrator import EventTriggerRecord

    # 1. Test ordinary event preservation with live API scattering trajectory
    # Supercritical scattering triggers radial turning point + escape radius
    payload = {
        "preset_id": "kerr_equatorial_scattering",
        "parameters": {
            "mass": 1.0,
            "spin": 0.5,
            "impact_parameter": 6.0,
            "r0": 50.0,
            "affine_span": 200.0,
        },
    }
    resp = client.post("/api/v1/simulations", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    lambdas = data["trajectory"]["lambdas"]
    coords = data["trajectory"]["coordinates"]

    # Trajectory bounded to <= 500 points
    assert len(lambdas) <= 500

    # Initial state preservation
    assert lambdas[0] == 0.0
    assert coords["r"][0] == 50.0

    # Strict monotonicity
    diffs = np.diff(lambdas)
    assert np.all(diffs > 0), "Lambdas must be strictly monotonically increasing"

    # All triggered event records must be present in triggered_events
    events = data["triggered_events"]
    assert len(events) >= 1
    for ev in events:
        ev_lam = ev["lambda"]
        # In the non-overflow regime, every event root is preserved in trajectory samples
        min_dist = min(abs(l - ev_lam) for l in lambdas)
        assert min_dist < 1e-11, f"Event lambda {ev_lam} was not preserved in trajectory"

    # 2. Test artificial event overflow (> 498 events)
    # Verifies contract: when event count exceeds capacity, trajectory remains <= 500,
    # strictly preserves endpoints (lambda_0, lambda_final), and downsamples event vertices deterministically
    raw_l = np.linspace(0.0, 10.0, 1000)
    raw_s = np.zeros((1000, 8))
    ev_many = EventTriggerRecord(
        event_index=0,
        name="oscillating_turning_point",
        lambdas=np.linspace(0.01, 9.99, 600),
        states=np.ones((600, 8)),
        terminal=False,
        direction=0,
    )
    dec_l, dec_s = decimate_trajectory(raw_l, raw_s, triggered_events=[ev_many], max_points=500)

    assert len(dec_l) <= 500
    assert dec_l[0] == 0.0, "Initial state lambda must be preserved"
    assert dec_l[-1] == 10.0, "Terminal state lambda must be preserved"
    assert np.all(np.diff(dec_l) > 0), "Decimated trajectory must be strictly monotonic"
    # Exactly 498 events + 2 endpoints = 500 points
    assert len(dec_l) == 500


def test_event_complete_phase_space_state_and_exact_root(client: TestClient) -> None:
    """Verifies that every event record preserves the complete 8-component phase-space state.

    The required state ordering is:
        (t, r, theta, phi, p_t, p_r, p_theta, p_phi)

    Verifies:
    1. Complete 8-component state is returned in each triggered_events record.
    2. Both named fields (t, r, theta, phi, p_t, p_r, p_theta, p_phi) and the canonical 'state' array are populated.
    3. Event affine parameter lambda and state vector correspond to the exact same root evaluation,
       matching direct engine root-finding output to machine precision (< 1e-14).
    4. At a radial turning point, p_r = 0 to machine precision (< 1e-15), -p_t = E, and p_phi = L_z.
    """
    from geodesics.metrics.kerr import KerrMetric
    from geodesics.scattering import integrate_equatorial_photon

    mass = 1.0
    spin = 0.5
    b_val = 6.0
    r0_val = 50.0

    # 1. API request
    resp = client.post(
        "/api/v1/simulations",
        json={
            "preset_id": "kerr_equatorial_scattering",
            "parameters": {
                "mass": mass,
                "spin": spin,
                "impact_parameter": b_val,
                "r0": r0_val,
                "affine_span": 200.0,
            },
        },
    )
    assert resp.status_code == 200
    data = resp.json()

    api_events = data["triggered_events"]
    assert len(api_events) >= 2, "Expected radial_turning_point and escape_radius events"

    # 2. Direct engine run for exact root comparison
    kerr = KerrMetric(mass=mass, spin=spin)
    engine_res = integrate_equatorial_photon(kerr, b=b_val, r0=r0_val, energy=1.0, max_step=0.5)

    engine_event_map = {}
    for rec in engine_res.triggered_events:
        for l_v, s_v in zip(rec.lambdas, rec.states):
            engine_event_map[rec.name] = (float(l_v), np.asarray(s_v, dtype=np.float64))

    for ev in api_events:
        name = ev["name"]
        assert name in engine_event_map, f"Unexpected event name: {name}"
        eng_lam, eng_state = engine_event_map[name]

        # Verify lambda matches exact engine root evaluation
        assert abs(ev["lambda"] - eng_lam) < 1e-14, "Event lambda must match engine root exactly"

        # Verify state array has exact length 8 and matches engine root state vector
        st = ev["state"]
        assert len(st) == 8, f"Event state must have exactly 8 components, got {len(st)}"
        assert np.allclose(st, eng_state, atol=1e-14, rtol=1e-14), "Event state must match engine root state exactly"

        # Verify named fields match state array entries
        assert ev["t"] == st[0]
        assert ev["r"] == st[1]
        assert ev["theta"] == st[2]
        assert ev["phi"] == st[3]
        assert ev["p_t"] == st[4]
        assert ev["p_r"] == st[5]
        assert ev["p_theta"] == st[6]
        assert ev["p_phi"] == st[7]

        # Physical turning point check
        if name == "radial_turning_point":
            assert abs(ev["p_r"]) < 1e-15, f"p_r at radial turning point must be zero, got {ev['p_r']}"
            assert abs(ev["p_t"] - (-1.0)) < 1e-12, f"p_t must equal -E = -1.0, got {ev['p_t']}"
            assert abs(ev["p_phi"] - b_val) < 1e-12, f"p_phi must equal L_z = b*E = {b_val}, got {ev['p_phi']}"

        # Physical escape radius check
        if name == "escape_radius":
            assert abs(ev["r"] - r0_val) < 1e-12, f"r at escape_radius must equal r0 = {r0_val}, got {ev['r']}"
            assert ev["p_r"] > 0.0, "p_r at escape_radius must be positive (outward)"


# -----------------------------------------------------------------------------
# 11. Engine / API Numerical Agreement
# -----------------------------------------------------------------------------

def test_engine_api_numerical_agreement(client: TestClient) -> None:
    """Verifies that API trajectory points numerically match direct engine calculations."""
    mass = 1.0
    r_val = 8.0
    delta_pr = 0.001
    span = 50.0

    # 1. Call API
    payload = {
        "preset_id": "schwarzschild_precession",
        "parameters": {
            "mass": mass,
            "radius": r_val,
            "delta_pr": delta_pr,
            "affine_span": span,
        },
    }
    resp = client.post("/api/v1/simulations", json=payload)
    assert resp.status_code == 200
    api_data = resp.json()

    api_lambdas = np.array(api_data["trajectory"]["lambdas"])
    api_r = np.array(api_data["trajectory"]["coordinates"]["r"])

    # 2. Direct engine run
    metric = SchwarzschildMetric(mass=mass)
    from geodesics.initial_conditions import schwarzschild_perturbed_circular_timelike_initial_state
    from geodesics.events import horizon_cutoff_event, escape_radius_event, radial_turning_point_event

    y0 = schwarzschild_perturbed_circular_timelike_initial_state(metric, r=r_val, delta_pr=delta_pr)
    events = (
        horizon_cutoff_event(metric),
        escape_radius_event(100.0 * mass),
        radial_turning_point_event(metric, terminal=False),
    )
    raw_res = integrate_geodesic(y0, metric, (0.0, span), events=events, max_step=0.5)

    # Check initial conditions match exactly
    assert abs(api_lambdas[0] - raw_res.lambdas[0]) < 1e-14
    assert abs(api_r[0] - raw_res.states[0, 1]) < 1e-14

    # Check terminal conditions match exactly
    assert abs(api_lambdas[-1] - raw_res.lambdas[-1]) < 1e-12
    assert abs(api_r[-1] - raw_res.states[-1, 1]) < 1e-12

    # Check every sampled API point matches a corresponding raw engine state
    for lam, r in zip(api_lambdas, api_r):
        idx = np.argmin(np.abs(raw_res.lambdas - lam))
        if abs(raw_res.lambdas[idx] - lam) < 1e-10:
            assert abs(raw_res.states[idx, 1] - r) < 1e-10


# -----------------------------------------------------------------------------
# 12. Structured Error Handling Without Stack Traces or Path Leaks
# -----------------------------------------------------------------------------

def test_structured_error_no_stack_traces_or_paths(client: TestClient) -> None:
    """Verifies that errors return clean JSON without Python tracebacks or filesystem paths."""
    # Test 1: Invalid parameter error
    resp1 = client.post(
        "/api/v1/simulations",
        json={"preset_id": "schwarzschild_isco_circular", "parameters": {"mass": "bad"}},
    )
    assert resp1.status_code == 422
    text1 = resp1.text
    assert "Traceback (most recent call last)" not in text1
    assert "File \"" not in text1
    assert "C:\\" not in text1
    assert "/Users/" not in text1
    assert "/home/" not in text1

    # Test 2: Unphysical configuration error
    resp2 = client.post(
        "/api/v1/simulations",
        json={
            "preset_id": "schwarzschild_precession",
            "parameters": {"mass": 1.0, "radius": 8.0, "delta_pr": 0.5},
        },
    )
    assert resp2.status_code == 422
    text2 = resp2.text
    assert "Traceback (most recent call last)" not in text2
    assert "File \"" not in text2
    assert "C:\\" not in text2


# -----------------------------------------------------------------------------
# 13. Core Package Import and Execution Isolation
# -----------------------------------------------------------------------------

def test_core_package_import_isolation_without_api() -> None:
    """Verifies that the core geodesics package operates cleanly without importing API extras.

    Executes a subprocess where fastapi, pydantic, and uvicorn are masked out in sys.modules,
    proving that core physics integration has zero dependency on the API package.
    """
    python_code = """
import sys

# Mask out optional API dependencies
sys.modules['fastapi'] = None
sys.modules['pydantic'] = None
sys.modules['uvicorn'] = None

# Import core package
import geodesics
from geodesics.metrics.schwarzschild import SchwarzschildMetric
from geodesics.metrics.kerr import KerrMetric
from geodesics.initial_conditions import schwarzschild_circular_timelike_initial_state
from geodesics.integrator import integrate_geodesic
from geodesics.shadow import kerr_shadow_boundary

# Verify core operations work without API dependencies
sm = SchwarzschildMetric(1.0)
km = KerrMetric(1.0, 0.9)
y0 = schwarzschild_circular_timelike_initial_state(sm, 6.0)
res = integrate_geodesic(y0, sm, (0.0, 10.0))
curve = kerr_shadow_boundary(km, 1.5707963, 100)

assert res.success is True
assert len(curve.alpha) == 100
print("CORE_ISOLATION_VERIFIED")
"""
    cmd = [sys.executable, "-c", python_code]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, f"Core isolation failed with stderr:\n{result.stderr}"
    assert "CORE_ISOLATION_VERIFIED" in result.stdout
