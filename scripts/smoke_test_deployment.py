#!/usr/bin/env python3
"""Post-deployment smoke-test suite for Kerr Geodesics Lab.

Implemented Checks:
1. Backend GET /health returns HTTP 200 and exact v1.0.0 engine provenance.
2. Backend GET /api/v1/presets returns all seven presets.
3. Valid Schwarzschild simulation (POST /api/v1/simulations) succeeds with bounded parameters.
4. Valid Kerr simulation (POST /api/v1/simulations) succeeds with bounded parameters.
5. Analytical Kerr shadow calculation (POST /api/v1/shadows) succeeds.
6. Parameter validation bounds reject out-of-bounds affine_span with HTTP 422.
7. Production CORS preflight OPTIONS allows approved origin with POST and content-type headers (when origin/frontend-url provided).
8. Production CORS preflight OPTIONS omits allow-origin for unapproved origin (when origin/frontend-url provided).
9-16. Frontend pages return HTTP 200 across all 8 primary routes (optional; run when --frontend-url provided, otherwise marked SKIP).

Render Free Cold-Start Tolerance:
- Configurable per-request timeout via `--timeout` (default: 25.0s, matching the 25s simulation timeout).
- Optional bounded readiness polling via `--wait-for-health` (default max-wait: 90.0s) to tolerate 30–60s Render Free container wake-up before running checks.
- Zero silent retries of expensive simulation or shadow calculations.

Zero third-party dependencies required (uses standard library urllib.request).
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Optional, Tuple


def _http_request(
    url: str,
    method: str = "GET",
    data: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 25.0,
) -> Tuple[int, Dict[str, str], bytes]:
    """Execute HTTP request and return (status_code, headers_dict, body_bytes)."""
    req_headers = {"User-Agent": "Kerr-Deployment-SmokeTest/1.0"}
    if headers:
        req_headers.update(headers)

    body_bytes = None
    if data is not None:
        body_bytes = json.dumps(data).encode("utf-8")
        req_headers["Content-Type"] = "application/json"
        req_headers["Accept"] = "application/json"

    req = urllib.request.Request(url, data=body_bytes, headers=req_headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            resp_headers = {k.lower(): v for k, v in response.getheaders()}
            return response.status, resp_headers, response.read()
    except urllib.error.HTTPError as e:
        resp_headers = {k.lower(): v for k, v in e.headers.items()} if e.headers else {}
        return e.code, resp_headers, e.read()
    except TimeoutError as e:
        raise TimeoutError(f"HTTP request to {url} timed out after {timeout:.1f}s") from e
    except urllib.error.URLError as e:
        if "timed out" in str(e).lower():
            raise TimeoutError(f"HTTP request to {url} timed out after {timeout:.1f}s: {e}") from e
        raise ConnectionError(f"Connection failure to {url} (timeout={timeout:.1f}s): {e}") from e
    except Exception as e:
        raise RuntimeError(f"Request error to {url} (timeout={timeout:.1f}s): {e}") from e


def poll_health_readiness(
    api_url: str,
    max_wait_seconds: float = 90.0,
    poll_interval: float = 3.0,
) -> bool:
    """Bounded readiness polling for /health to tolerate Render Free container spin-up (30-60s)."""
    print(f"Waiting for backend readiness at {api_url}/health (up to {max_wait_seconds:.0f}s)...")
    start = time.time()
    attempts = 0
    while time.time() - start < max_wait_seconds:
        attempts += 1
        elapsed = time.time() - start
        try:
            code, _, body = _http_request(f"{api_url}/health", timeout=min(10.0, max_wait_seconds))
            if code == 200:
                data = json.loads(body.decode("utf-8"))
                if data.get("status") == "ok":
                    print(f"Backend is ready after {elapsed:.1f}s ({attempts} probe attempts).\n")
                    return True
        except Exception:
            pass
        time.sleep(poll_interval)
    print(f"WARNING: Backend /health was not ready within {max_wait_seconds:.0f}s. Proceeding to test suite...\n")
    return False


def run_smoke_tests(
    api_url: str,
    frontend_url: Optional[str] = None,
    allowed_origin: Optional[str] = None,
    timeout: float = 25.0,
    wait_for_health: bool = False,
    max_wait: float = 90.0,
) -> bool:
    api_url = api_url.rstrip("/")
    if frontend_url:
        frontend_url = frontend_url.rstrip("/")
    if not allowed_origin and frontend_url:
        allowed_origin = frontend_url

    print("=" * 70)
    print("KERR GEODESICS LAB — POST-DEPLOYMENT SMOKE TESTS")
    print(f"Backend API Target: {api_url}")
    print(f"Frontend Target:    {frontend_url or '(skipped)'}")
    print(f"Approved Origin:    {allowed_origin or '(not specified)'}")
    print(f"Per-Request Timeout:{timeout:.1f}s")
    print(f"Health Poll on Boot:{'Enabled (up to ' + str(max_wait) + 's)' if wait_for_health else 'Disabled'}")
    print("=" * 70 + "\n")

    if wait_for_health:
        poll_health_readiness(api_url, max_wait_seconds=max_wait)

    passed_checks = 0
    total_checks = 0

    def check(name: str, condition: bool, details: str = ""):
        nonlocal passed_checks, total_checks
        total_checks += 1
        status = "PASS" if condition else "FAIL"
        print(f"[{status}] Check {total_checks}: {name}")
        if details:
            print(f"       Details: {details}")
        if condition:
            passed_checks += 1

    # 1. Health & Provenance
    try:
        code, _, body = _http_request(f"{api_url}/health", timeout=timeout)
        data = json.loads(body.decode("utf-8")) if code == 200 else {}
        check(
            "Backend Health & Engine Provenance",
            code == 200 and data.get("status") == "ok" and data.get("commit_hash") == "062b20c80a689640637a2fcd003bdd921a7d4132",
            f"HTTP {code}, status={data.get('status')}, commit={data.get('commit_hash')}",
        )
    except Exception as e:
        check("Backend Health & Engine Provenance", False, str(e))

    # 2. Preset Catalogue
    try:
        code, _, body = _http_request(f"{api_url}/api/v1/presets", timeout=timeout)
        data = json.loads(body.decode("utf-8")) if code == 200 else {}
        presets = data.get("presets", [])
        expected_ids = {
            "schwarzschild_isco_circular",
            "schwarzschild_precession",
            "schwarzschild_photon_sphere",
            "kerr_equatorial_prograde_photon",
            "kerr_equatorial_retrograde_photon",
            "kerr_circular_timelike",
            "kerr_equatorial_scattering",
        }
        found_ids = {p.get("id") for p in presets}
        check(
            "Preset Catalogue (All 7 Presets)",
            code == 200 and expected_ids.issubset(found_ids),
            f"Found {len(found_ids)} presets: {sorted(list(found_ids))}",
        )
    except Exception as e:
        check("Preset Catalogue (All 7 Presets)", False, str(e))

    # 3. Valid Schwarzschild Simulation (Bounded span=10.0 for speed)
    try:
        code, _, body = _http_request(
            f"{api_url}/api/v1/simulations",
            method="POST",
            data={"preset_id": "schwarzschild_isco_circular", "parameters": {"mass": 1.0, "affine_span": 10.0}},
            timeout=timeout,
        )
        data = json.loads(body.decode("utf-8")) if code == 200 else {}
        check(
            "Valid Schwarzschild ISCO Simulation",
            code == 200 and data.get("status") == "completed" and "trajectory" in data,
            f"HTTP {code}, status={data.get('status')}, points={len(data.get('trajectory', {}).get('lambdas', []))}",
        )
    except Exception as e:
        check("Valid Schwarzschild ISCO Simulation", False, str(e))

    # 4. Valid Kerr Simulation (Bounded span=10.0 for speed)
    try:
        code, _, body = _http_request(
            f"{api_url}/api/v1/simulations",
            method="POST",
            data={"preset_id": "kerr_circular_timelike", "parameters": {"mass": 1.0, "spin": 0.5, "radius": 6.0, "affine_span": 10.0}},
            timeout=timeout,
        )
        data = json.loads(body.decode("utf-8")) if code == 200 else {}
        check(
            "Valid Kerr Circular Timelike Simulation",
            code == 200 and data.get("status") == "completed" and "trajectory" in data,
            f"HTTP {code}, status={data.get('status')}, points={len(data.get('trajectory', {}).get('lambdas', []))}",
        )
    except Exception as e:
        check("Valid Kerr Circular Timelike Simulation", False, str(e))

    # 5. Analytical Kerr Shadow
    try:
        code, _, body = _http_request(
            f"{api_url}/api/v1/shadows",
            method="POST",
            data={"mass": 1.0, "spin": 0.9, "observer_inclination": 1.047197551},
            timeout=timeout,
        )
        data = json.loads(body.decode("utf-8")) if code == 200 else {}
        check(
            "Analytical Kerr Shadow Boundary",
            code == 200 and "alpha" in data and "beta" in data and len(data.get("alpha", [])) > 0,
            f"HTTP {code}, points={len(data.get('alpha', []))}, closed={data.get('is_closed')}",
        )
    except Exception as e:
        check("Analytical Kerr Shadow Boundary", False, str(e))

    # 6. Workload Boundary Rejection (HTTP 422 on affine_span=9999.0)
    try:
        code, _, body = _http_request(
            f"{api_url}/api/v1/simulations",
            method="POST",
            data={"preset_id": "schwarzschild_isco_circular", "parameters": {"affine_span": 9999.0}},
            timeout=timeout,
        )
        data = json.loads(body.decode("utf-8")) if code == 422 else {}
        is_val_err = data.get("error_type") == "invalid_request_parameters"
        check(
            "Workload Boundary Rejection (affine_span=9999.0 -> HTTP 422)",
            code == 422 and is_val_err,
            f"HTTP {code}, error_type={data.get('error_type')}",
        )
    except Exception as e:
        check("Workload Boundary Rejection (affine_span=9999.0 -> HTTP 422)", False, str(e))

    # 7 & 8. CORS Preflight Verification
    if allowed_origin:
        # 7. Allowed origin
        try:
            code, headers, _ = _http_request(
                f"{api_url}/api/v1/simulations",
                method="OPTIONS",
                headers={
                    "Origin": allowed_origin,
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "content-type",
                },
                timeout=timeout,
            )
            allow_origin = headers.get("access-control-allow-origin")
            allow_methods = headers.get("access-control-allow-methods", "")
            allow_headers = headers.get("access-control-allow-headers", "")
            methods_ok = "POST" in [m.strip().upper() for m in allow_methods.split(",") if m.strip()]
            headers_ok = "content-type" in [h.strip().lower() for h in allow_headers.split(",") if h.strip()]
            check(
                f"CORS Preflight (Allowed Origin: {allowed_origin})",
                code == 200 and allow_origin == allowed_origin and methods_ok and headers_ok,
                f"HTTP {code}, allow-origin={allow_origin}, allow-methods={allow_methods}, allow-headers={allow_headers}",
            )
        except Exception as e:
            check(f"CORS Preflight (Allowed Origin: {allowed_origin})", False, str(e))

        # 8. Disallowed origin
        try:
            disallowed_origin = "https://unauthorized-evil-origin.com"
            code_dis, headers_dis, _ = _http_request(
                f"{api_url}/api/v1/simulations",
                method="OPTIONS",
                headers={
                    "Origin": disallowed_origin,
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "content-type",
                },
                timeout=timeout,
            )
            dis_allow_origin = headers_dis.get("access-control-allow-origin")
            check(
                "CORS Preflight (Disallowed Origin Rejected)",
                dis_allow_origin is None,
                f"HTTP {code_dis}, allow-origin={dis_allow_origin} (expected None)",
            )
        except Exception as e:
            check("CORS Preflight (Disallowed Origin Rejected)", False, str(e))
    else:
        print("[SKIP] Checks 7-8: CORS Preflight Verification (skipped; neither --origin nor --frontend-url provided)")

    # 9-16. Frontend Route Availability
    routes = ["/", "/about", "/docs", "/explorer", "/gallery", "/mathematics", "/shadows", "/validation"]
    if frontend_url:
        for r in routes:
            try:
                code, _, _ = _http_request(f"{frontend_url}{r}", timeout=timeout)
                check(f"Frontend Route '{r}'", code == 200, f"HTTP {code}")
            except Exception as e:
                check(f"Frontend Route '{r}'", False, str(e))
    else:
        print(f"[SKIP] Checks 9-16: Frontend Routes ({len(routes)} routes skipped; --frontend-url not provided)")

    print("\n" + "=" * 70)
    print(f"SMOKE TEST SUMMARY: {passed_checks}/{total_checks} checks passed.")
    print("=" * 70)
    return passed_checks == total_checks


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Smoke test deployed Kerr Geodesics Lab")
    parser.add_argument("--api-url", required=True, help="Base URL of deployed FastAPI backend")
    parser.add_argument("--frontend-url", default=None, help="Base URL of deployed Vercel frontend")
    parser.add_argument("--origin", default=None, help="Origin to test for CORS preflight (defaults to frontend-url)")
    parser.add_argument("--timeout", type=float, default=25.0, help="Per-request HTTP timeout in seconds (default: 25.0, matching the 25s simulation timeout)")
    parser.add_argument("--wait-for-health", action="store_true", default=False, help="Wait for backend /health endpoint to become ready before executing checks")
    parser.add_argument("--max-wait", type=float, default=90.0, help="Maximum seconds to wait during --wait-for-health polling (default: 90.0)")
    args = parser.parse_args()

    success = run_smoke_tests(
        api_url=args.api_url,
        frontend_url=args.frontend_url,
        allowed_origin=args.origin,
        timeout=args.timeout,
        wait_for_health=args.wait_for_health,
        max_wait=args.max_wait,
    )
    sys.exit(0 if success else 1)
