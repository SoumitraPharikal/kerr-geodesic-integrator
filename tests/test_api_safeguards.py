"""Safeguard verification tests for Kerr Geodesics Lab.

Tests:
1. CORS fail-closed behavior:
   - Development mode with no explicit origins (falls back to localhost).
   - Production mode with valid explicit origins.
   - Production mode startup failure when origins are missing.
   - Production mode startup failure when origins are empty or whitespace-only.
   - Wildcard origin strictly prohibited with ValueError.
   - Allowed and disallowed preflight OPTIONS requests.
2. Workload bounding via affine_span upper bounds on all 7 presets.
3. Acceptance at exact upper boundary.
4. Fast rejection (HTTP 422) above boundary before integration begins.
5. Non-positive and invalid span rejection.
6. Preservation of preset defaults.
"""

import time
import pytest
from fastapi.testclient import TestClient

from geodesics.api.app import DEFAULT_DEV_ORIGINS, create_app, parse_cors_origins
from geodesics.api.schemas import (
    MAX_SCATTERING_AFFINE_SPAN,
    MAX_TIMELIKE_AFFINE_SPAN,
    MAX_UNSTABLE_PHOTON_AFFINE_SPAN,
    PRESET_PARAM_MODELS,
)


@pytest.fixture
def client() -> TestClient:
    """Default client with development origins."""
    app = create_app()
    return TestClient(app)


# -----------------------------------------------------------------------------
# 1. CORS Origin Parsing & Environment Mode Tests
# -----------------------------------------------------------------------------

def test_cors_development_no_explicit_origins() -> None:
    """1. Development with no explicit origins falls back to DEFAULT_DEV_ORIGINS."""
    assert parse_cors_origins(None, environment="development") == DEFAULT_DEV_ORIGINS
    assert parse_cors_origins("", environment="development") == DEFAULT_DEV_ORIGINS
    assert parse_cors_origins("   ", environment="development") == DEFAULT_DEV_ORIGINS
    assert parse_cors_origins(" , , , ", environment="development") == DEFAULT_DEV_ORIGINS

    # Default create_app() in dev mode functions with dev origins
    app = create_app(environment="development")
    client = TestClient(app)
    resp = client.options(
        "/api/v1/simulations",
        headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "POST"},
    )
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_cors_production_valid_explicit_origins(monkeypatch: pytest.MonkeyPatch) -> None:
    """2. Production mode accepts valid explicit origins and trims whitespace."""
    raw = "  https://kerr-geodesics.vercel.app , https://kerr-lab.org   "
    expected = ["https://kerr-geodesics.vercel.app", "https://kerr-lab.org"]
    assert parse_cors_origins(raw, environment="production") == expected

    # Verify create_app in production mode with CORS_ALLOWED_ORIGINS env var
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", raw)
    prod_app = create_app()
    prod_client = TestClient(prod_app)
    resp = prod_client.options(
        "/api/v1/simulations",
        headers={"Origin": "https://kerr-geodesics.vercel.app", "Access-Control-Request-Method": "POST"},
    )
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "https://kerr-geodesics.vercel.app"


def test_cors_production_missing_origins_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    """3. Production startup must fail clearly (RuntimeError) if origins are missing."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("CORS_ALLOWED_ORIGINS", raising=False)

    with pytest.raises(RuntimeError, match="In production mode.*CORS_ALLOWED_ORIGINS must be set"):
        parse_cors_origins(None, environment="production")

    with pytest.raises(RuntimeError, match="In production mode.*CORS_ALLOWED_ORIGINS must be set"):
        create_app(environment="production")


def test_cors_production_empty_or_whitespace_origins_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    """4. Production startup must fail clearly if origins are empty or whitespace-only."""
    for bad_raw in ["", "   ", " , , , ", "\t\n"]:
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("CORS_ALLOWED_ORIGINS", bad_raw)

        with pytest.raises(RuntimeError, match="In production mode.*CORS_ALLOWED_ORIGINS must be set"):
            parse_cors_origins(bad_raw, environment="production")

        with pytest.raises(RuntimeError, match="In production mode.*CORS_ALLOWED_ORIGINS must be set"):
            create_app(environment="production")


def test_cors_wildcard_strictly_prohibited() -> None:
    """5. Wildcard origin '*' is strictly prohibited in both dev and prod modes."""
    with pytest.raises(ValueError, match="Wildcard CORS origin '\\*' is strictly prohibited"):
        parse_cors_origins("*", environment="development")

    with pytest.raises(ValueError, match="Wildcard CORS origin '\\*' is strictly prohibited"):
        parse_cors_origins("*", environment="production")

    with pytest.raises(ValueError, match="Wildcard CORS origin '\\*' is strictly prohibited"):
        parse_cors_origins("https://kerr.vercel.app, *, https://other.org", environment="production")


def test_cors_preflight_allowed_and_disallowed_requests() -> None:
    """6. Allowed and disallowed preflight requests verification."""
    prod_app = create_app(cors_origins=["https://kerr-geodesics.vercel.app"])
    client = TestClient(prod_app)

    # Allowed preflight request
    allowed_headers = {
        "Origin": "https://kerr-geodesics.vercel.app",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type",
    }
    resp_allowed = client.options("/api/v1/simulations", headers=allowed_headers)
    assert resp_allowed.status_code == 200
    assert resp_allowed.headers.get("access-control-allow-origin") == "https://kerr-geodesics.vercel.app"
    assert "POST" in resp_allowed.headers.get("access-control-allow-methods", "")
    assert resp_allowed.headers.get("access-control-allow-credentials") is None or resp_allowed.headers.get("access-control-allow-credentials") == "false"

    # Disallowed origin receives no access-control-allow-origin header
    disallowed_headers = {
        "Origin": "https://unauthorized-attacker.com",
        "Access-Control-Request-Method": "POST",
    }
    resp_disallowed = client.options("/api/v1/simulations", headers=disallowed_headers)
    assert resp_disallowed.headers.get("access-control-allow-origin") is None

    # Dev origin receives no access-control-allow-origin header when prod origin is configured
    dev_headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "POST",
    }
    resp_dev = client.options("/api/v1/simulations", headers=dev_headers)
    assert resp_dev.headers.get("access-control-allow-origin") is None


# -----------------------------------------------------------------------------
# 2. Workload Bounding: affine_span Upper Bound Tests
# -----------------------------------------------------------------------------

PRESET_LIMITS = [
    ("schwarzschild_isco_circular", MAX_TIMELIKE_AFFINE_SPAN),
    ("schwarzschild_precession", MAX_TIMELIKE_AFFINE_SPAN),
    ("schwarzschild_photon_sphere", MAX_UNSTABLE_PHOTON_AFFINE_SPAN),
    ("kerr_equatorial_prograde_photon", MAX_UNSTABLE_PHOTON_AFFINE_SPAN),
    ("kerr_equatorial_retrograde_photon", MAX_UNSTABLE_PHOTON_AFFINE_SPAN),
    ("kerr_circular_timelike", MAX_TIMELIKE_AFFINE_SPAN),
    ("kerr_equatorial_scattering", MAX_SCATTERING_AFFINE_SPAN),
]


@pytest.mark.parametrize("preset_id, max_span", PRESET_LIMITS)
def test_affine_span_exact_boundary_accepted(client: TestClient, preset_id: str, max_span: float) -> None:
    """Verifies that affine_span equal to the maximum permitted bound is accepted."""
    params = {"affine_span": max_span}
    if preset_id == "schwarzschild_precession":
        params.update({"mass": 1.0, "radius": 8.0, "delta_pr": 0.001})
    elif preset_id == "kerr_circular_timelike":
        params.update({"mass": 1.0, "spin": 0.5, "radius": 6.0})
    elif preset_id == "kerr_equatorial_scattering":
        params.update({"mass": 1.0, "spin": 0.5, "impact_parameter": 4.5, "r0": 50.0})

    # Validate directly via Pydantic model
    model_cls = PRESET_PARAM_MODELS[preset_id]
    validated = model_cls(**params)
    assert validated.affine_span == max_span


@pytest.mark.parametrize("preset_id, max_span", PRESET_LIMITS)
def test_affine_span_above_boundary_rejected(client: TestClient, preset_id: str, max_span: float) -> None:
    """Verifies that affine_span exceeding the maximum bound is immediately rejected with HTTP 422."""
    t0 = time.perf_counter()
    resp = client.post(
        "/api/v1/simulations",
        json={"preset_id": preset_id, "parameters": {"affine_span": max_span + 0.1}},
    )
    dt = time.perf_counter() - t0

    assert resp.status_code == 422, f"Preset {preset_id} did not reject above-bound span: {resp.text}"
    # Verification that rejection is instantaneous (schema-level) without running integration
    assert dt < 0.1, f"Rejection took too long ({dt:.3f}s), indicating integration may have run"

    data = resp.json()
    assert data["error_type"] == "invalid_request_parameters"
    assert any("less_than_equal" in err["type"] for err in data["details"])


@pytest.mark.parametrize("preset_id, _", PRESET_LIMITS)
def test_affine_span_non_positive_rejected(client: TestClient, preset_id: str, _: float) -> None:
    """Verifies that non-positive (0 or negative) affine_span is rejected with HTTP 422."""
    for bad_span in [0.0, -10.0]:
        resp = client.post(
            "/api/v1/simulations",
            json={"preset_id": preset_id, "parameters": {"affine_span": bad_span}},
        )
        assert resp.status_code == 422
        data = resp.json()
        assert data["error_type"] == "invalid_request_parameters"
        assert any("greater_than" in err["type"] for err in data["details"])


# -----------------------------------------------------------------------------
# 3. Preset Defaults Preservation
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("preset_id, max_span", PRESET_LIMITS)
def test_all_preset_defaults_strictly_within_bounds(preset_id: str, max_span: float) -> None:
    """Verifies that default parameters for every preset satisfy the workload bounds."""
    model_cls = PRESET_PARAM_MODELS[preset_id]
    instance = model_cls()
    assert instance.affine_span > 0
    assert instance.affine_span <= max_span


def test_simulation_with_empty_parameters_uses_defaults(client: TestClient) -> None:
    """Verifies that omitting parameters executes with default parameters successfully."""
    resp = client.post(
        "/api/v1/simulations",
        json={"preset_id": "schwarzschild_isco_circular", "parameters": {}},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert data["preset_id"] == "schwarzschild_isco_circular"
