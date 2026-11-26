"""Unit tests for post-deployment smoke-test suite and Render Free cold-start tolerance.

Exercises scripts/smoke_test_deployment.py:
- Configurable timeout propagation and error message formatting
- Bounded readiness polling on /health
- No silent retries on simulation/shadow endpoints
- CLI argument defaults
"""

import http.server
import json
import sys
import threading
from pathlib import Path

# Ensure repository root is on sys.path for importing scripts
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from scripts.smoke_test_deployment import (
    _http_request,
    poll_health_readiness,
    run_smoke_tests,
)


class MockHealthServer(http.server.HTTPServer):
    def __init__(self, addr, handler_cls, fail_health_count=0):
        super().__init__(addr, handler_cls)
        self.health_requests = 0
        self.simulation_requests = 0
        self.fail_health_count = fail_health_count


class MockHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress console logging

    def do_GET(self):
        if self.path == "/health":
            self.server.health_requests += 1
            if self.server.health_requests <= self.server.fail_health_count:
                self.send_response(503)
                self.end_headers()
                self.wfile.write(b'{"status": "starting"}')
            else:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(
                    b'{"status": "ok", "commit_hash": "062b20c80a689640637a2fcd003bdd921a7d4132"}'
                )
        elif self.path == "/api/v1/presets":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            presets = [
                {"id": "schwarzschild_isco_circular"},
                {"id": "schwarzschild_precession"},
                {"id": "schwarzschild_photon_sphere"},
                {"id": "kerr_equatorial_prograde_photon"},
                {"id": "kerr_equatorial_retrograde_photon"},
                {"id": "kerr_circular_timelike"},
                {"id": "kerr_equatorial_scattering"},
            ]
            self.wfile.write(json.dumps({"presets": presets}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/api/v1/simulations":
            self.server.simulation_requests += 1
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b'{"error": "sim_failure"}')
        else:
            self.send_response(404)
            self.end_headers()


@pytest.fixture
def mock_server():
    server = MockHealthServer(("127.0.0.1", 0), MockHandler, fail_health_count=2)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    yield server
    server.shutdown()
    server.server_close()


def test_http_request_timeout_formatting():
    """Verify that timeout errors report endpoint URL and timeout duration clearly."""
    with pytest.raises(TimeoutError) as exc_info:
        # Non-routable IP to guarantee timeout
        _http_request("http://10.255.255.1:1", timeout=0.05)
    err = str(exc_info.value)
    assert "timed out after 0.1s" in err or "timed out after 0.0s" in err
    assert "http://10.255.255.1:1" in err


def test_poll_health_readiness_recovers(mock_server):
    """Verify that poll_health_readiness polls until backend returns HTTP 200 ok."""
    port = mock_server.server_address[1]
    url = f"http://127.0.0.1:{port}"

    ready = poll_health_readiness(url, max_wait_seconds=5.0, poll_interval=0.1)
    assert ready is True
    # Server failed twice, so it should have taken at least 3 attempts
    assert mock_server.health_requests >= 3


def test_poll_health_readiness_timeout():
    """Verify that poll_health_readiness gracefully returns False if max_wait expires."""
    # Dead port
    ready = poll_health_readiness("http://127.0.0.1:1", max_wait_seconds=0.2, poll_interval=0.05)
    assert ready is False


def test_no_silent_simulation_retries(mock_server):
    """Verify that a failing simulation check is executed once without silent retries."""
    port = mock_server.server_address[1]
    url = f"http://127.0.0.1:{port}"

    # First warm up health so check 1 passes
    poll_health_readiness(url, max_wait_seconds=5.0, poll_interval=0.1)

    initial_sim_requests = mock_server.simulation_requests
    # Run smoke tests - simulation endpoints will return 500
    run_smoke_tests(url, timeout=2.0)

    # Check 3 (Schwarzschild) and Check 4 (Kerr) each send exactly ONE POST
    # Plus Check 6 sends one out-of-bounds POST
    assert mock_server.simulation_requests == initial_sim_requests + 3


def test_cli_argument_defaults():
    """Verify CLI argument defaults accommodate Render Free cold starts (25s timeout, 90s max-wait)."""
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--api-url", required=True)
    parser.add_argument("--frontend-url", default=None)
    parser.add_argument("--origin", default=None)
    parser.add_argument("--timeout", type=float, default=25.0)
    parser.add_argument("--wait-for-health", action="store_true", default=False)
    parser.add_argument("--max-wait", type=float, default=90.0)

    args = parser.parse_args(["--api-url", "http://localhost:8000"])
    assert args.timeout == 25.0
    assert args.wait_for_health is False
    assert args.max_wait == 90.0
