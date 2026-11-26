/**
 * Direct TypeScript test suite for the frontend API client and error handling.
 * Exercises `frontend/src/lib/api.ts` using Node.js native assert.
 */

import assert from "node:assert";
import http from "node:http";
// @ts-expect-error - Node --experimental-strip-types requires explicit .ts extension
import { ApiError, fetchWithTimeout, DEFAULT_SIMULATION_TIMEOUT_MS, DEFAULT_METADATA_TIMEOUT_MS, COLD_START_TIMEOUT_MS, FAST_PROBE_TIMEOUT_MS, IDLE_FRESHNESS_WINDOW_MS, isBackendAwake, isBackendStale, resetBackendReadiness, markBackendAwake, markBackendStale, ensureBackendReady, postSimulation } from "../src/lib/api.ts";

console.log("Running Frontend API Client TypeScript tests...");

// 1. ApiError Classification Tests
{
  // Timeout error
  const timeoutErr = new ApiError("Request timed out", "timeout_error", 408);
  assert.strictEqual(timeoutErr.isTimeout, true, "Expected isTimeout to be true for timeout_error");
  assert.strictEqual(timeoutErr.isReadinessTimeout, false);
  assert.strictEqual(timeoutErr.isNetworkError, false, "Expected isNetworkError to be false for timeout_error");
  assert.strictEqual(timeoutErr.isValidationError, false);
  assert.strictEqual(timeoutErr.isServerError, false);
  assert.strictEqual(timeoutErr.isAborted, false);

  // Readiness timeout error (Render Free wake-up)
  const readyErr = new ApiError("Backend wake-up timed out", "readiness_timeout", 408);
  assert.strictEqual(readyErr.isTimeout, true, "Expected isTimeout to be true for readiness_timeout");
  assert.strictEqual(readyErr.isReadinessTimeout, true, "Expected isReadinessTimeout to be true");
  assert.strictEqual(readyErr.isNetworkError, false);
  assert.strictEqual(readyErr.isValidationError, false);
  assert.strictEqual(readyErr.isServerError, false);
  assert.strictEqual(readyErr.isAborted, false);

  // Network unreachable
  const netErr = new ApiError("Engine offline", "network_unreachable");
  assert.strictEqual(netErr.isNetworkError, true);
  assert.strictEqual(netErr.isTimeout, false);
  assert.strictEqual(netErr.isValidationError, false);
  assert.strictEqual(netErr.isServerError, false);

  // Validation errors (422)
  const valErr1 = new ApiError("Invalid span", "invalid_request_parameters", 422);
  assert.strictEqual(valErr1.isValidationError, true);
  assert.strictEqual(valErr1.isServerError, false);

  const valErr2 = new ApiError("Unphysical spin", "unphysical_configuration", 422);
  assert.strictEqual(valErr2.isValidationError, true);

  // Server error (500)
  const serverErr = new ApiError("Solver error", "numerical_integration_failure", 500);
  assert.strictEqual(serverErr.isServerError, true);
  assert.strictEqual(serverErr.isValidationError, false);

  // Abort error
  const abortErr = new ApiError("Cancelled", "abort_error", 499);
  assert.strictEqual(abortErr.isAborted, true);
  assert.strictEqual(abortErr.isTimeout, false);

  console.log("✓ Test 1 Passed: ApiError classification getters verified.");
}

// 2. AbortController Cancellation Test (Client-Side)
async function testClientAbort(): Promise<void> {
  const controller = new AbortController();
  controller.abort(); // already aborted

  try {
    await fetchWithTimeout(
      "http://127.0.0.1:9999/test",
      { method: "GET" },
      1000,
      controller.signal
    );
    assert.fail("Should have thrown abort error");
  } catch (err: unknown) {
    assert(err instanceof ApiError, "Expected err to be ApiError");
    assert.strictEqual(err.isAborted, true, "Expected err.isAborted to be true");
    assert.strictEqual(err.statusCode, 499);
  }
  console.log("✓ Test 2 Passed: Pre-aborted request rejected immediately with abort_error.");
}

// 3. Mock Server Timeout and Error Classification Tests
async function testMockServerInteractions(): Promise<void> {
  // Start temporary mock HTTP server on an ephemeral port
  const server = http.createServer((req, res) => {
    if (req.url === "/timeout-route") {
      // Intentionally do not respond to simulate slow/hanging engine
      return;
    }
    if (req.url === "/fast-route") {
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ status: "ok" }));
      return;
    }
    res.writeHead(404);
    res.end();
  });

  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", () => resolve()));
  const addr = server.address();
  const port = typeof addr === "object" && addr ? addr.port : 0;
  assert(port > 0, "Server must bind to ephemeral port");

  try {
    // 3a. Fast request succeeds
    const okRes = await fetchWithTimeout(
      `http://127.0.0.1:${port}/fast-route`,
      { method: "GET" },
      1000
    );
    assert.strictEqual(okRes.status, 200);
    console.log("✓ Test 3a Passed: fetchWithTimeout succeeds on responsive route.");

    // 3b. Slow request times out and aborts cleanly
    try {
      await fetchWithTimeout(
        `http://127.0.0.1:${port}/timeout-route`,
        { method: "GET" },
        50 // 50ms timeout
      );
      assert.fail("Should have timed out");
    } catch (err: unknown) {
      assert(err instanceof ApiError, "Expected err to be ApiError");
      assert.strictEqual(err.isTimeout, true, "Expected err.isTimeout to be true");
      assert.strictEqual(err.statusCode, 408, "Expected HTTP 408 timeout status");
      assert(err.message.includes("timed out"), `Expected timeout message, got: ${err.message}`);
    }
    console.log("✓ Test 3b Passed: fetchWithTimeout cleanly times out and aborts connection.");

    // 3c. Active cancellation during in-flight request
    const inFlightController = new AbortController();
    setTimeout(() => inFlightController.abort(), 20); // abort after 20ms
    try {
      await fetchWithTimeout(
        `http://127.0.0.1:${port}/timeout-route`,
        { method: "GET" },
        1000,
        inFlightController.signal
      );
      assert.fail("Should have aborted in-flight");
    } catch (err: unknown) {
      assert(err instanceof ApiError, "Expected err to be ApiError");
      assert.strictEqual(err.isAborted, true, "Expected err.isAborted to be true");
      assert.strictEqual(err.statusCode, 499);
    }
    console.log("✓ Test 3c Passed: In-flight cancellation aborts cleanly.");
  } finally {
    await new Promise<void>((resolve) => server.close(() => resolve()));
  }
}

// 4. Default Timeout Constants Verification
{
  assert.strictEqual(COLD_START_TIMEOUT_MS, 90000, "Cold-start timeout should be 90s");
  assert.strictEqual(DEFAULT_SIMULATION_TIMEOUT_MS, 25000, "Simulation timeout should be 25s for ODE integration on awake backend");
  assert.strictEqual(DEFAULT_METADATA_TIMEOUT_MS, 10000, "Metadata timeout should be 10s for routine metadata");
  assert.strictEqual(FAST_PROBE_TIMEOUT_MS, 2500, "Fast probe timeout should be 2.5s");
  assert.strictEqual(IDLE_FRESHNESS_WINDOW_MS, 60000, "Idle freshness window should be 60s");
  console.log("✓ Test 4 Passed: Timeout constants verified (90s cold start, 25s simulation, 10s metadata, 2.5s fast probe, 60s freshness).");
}

// 5. Cold-Start Readiness Gating & Deduplication Tests
async function testColdStartReadinessGating(): Promise<void> {
  let healthHitCount = 0;
  let simHitCount = 0;
  let delayHealthMs = 0;

  const server = http.createServer((req, res) => {
    if (req.url === "/health") {
      healthHitCount++;
      if (delayHealthMs > 0) {
        setTimeout(() => {
          res.writeHead(200, { "Content-Type": "application/json" });
          res.end(JSON.stringify({
            status: "ok",
            engine: "kerr-geodesics",
            version: "1.0.0",
            commit_hash: "062b20c80a689640637a2fcd003bdd921a7d4132",
          }));
        }, delayHealthMs);
        return;
      }
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify({
        status: "ok",
        engine: "kerr-geodesics",
        version: "1.0.0",
        commit_hash: "062b20c80a689640637a2fcd003bdd921a7d4132",
      }));
      return;
    }
    if (req.url === "/api/v1/simulations") {
      simHitCount++;
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify({
        preset_id: "schwarzschild_isco_circular",
        config_hash: "mock",
        status: "completed",
        termination_reason: "completed",
        solver_diagnostics: { method: "DOP853", nfev: 10, rtol: 1e-10, atol: 1e-12 },
        trajectory: {
          lambdas: [0, 1],
          coordinates: { t: [0, 1], r: [6, 6], theta: [1.57, 1.57], phi: [0, 0.1] },
          momenta: { p_t: [-1, -1], p_r: [0, 0], p_theta: [0, 0], p_phi: [3.46, 3.46] },
        },
        conserved_quantities: {
          energy: 0.94,
          angular_momentum: 3.46,
          carter_constant: null,
          hamiltonian_drift_max: 1e-14,
        },
        triggered_events: [],
        provenance: {
          engine: "kerr-geodesics",
          version: "1.0.0",
          commit_hash: "062b20c80a689640637a2fcd003bdd921a7d4132",
        },
      }));
      return;
    }
    res.writeHead(404);
    res.end();
  });

  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", () => resolve()));
  const addr = server.address();
  const port = typeof addr === "object" && addr ? addr.port : 0;
  assert(port > 0, "Server must bind to ephemeral port");
  const baseUrl = `http://127.0.0.1:${port}`;

  try {
    // 5a. Cold start: when backendIsAwake is false, postSimulation calls /health first, then /simulations
    resetBackendReadiness();
    assert.strictEqual(isBackendAwake(), false);
    markBackendAwake();
    assert.strictEqual(isBackendAwake(), true);
    resetBackendReadiness();
    assert.strictEqual(isBackendAwake(), false);
    healthHitCount = 0;
    simHitCount = 0;

    const res = await postSimulation(
      { preset_id: "schwarzschild_isco_circular" },
      { baseUrl }
    );
    assert.strictEqual(res.status, "completed");
    assert.strictEqual(healthHitCount, 1, "Expected exactly 1 /health probe on cold start");
    assert.strictEqual(simHitCount, 1, "Expected exactly 1 simulation execution");
    assert.strictEqual(isBackendAwake(), true, "backendIsAwake should now be true");
    console.log("✓ Test 5a Passed: Cold-start postSimulation gates on /health probe and completes.");

    // 5b. Warm simulation: subsequent calls when backendIsAwake is true do NOT call /health
    await postSimulation(
      { preset_id: "schwarzschild_isco_circular" },
      { baseUrl }
    );
    assert.strictEqual(healthHitCount, 1, "Health probe count should remain 1 on warm request");
    assert.strictEqual(simHitCount, 2, "Simulation count should increment to 2");
    console.log("✓ Test 5b Passed: Warm simulation does not re-probe /health.");

    // 5c. Deduplication: concurrent ensureBackendReady calls share a single in-flight promise
    resetBackendReadiness();
    healthHitCount = 0;
    delayHealthMs = 30; // 30ms delay to ensure in-flight sharing
    const [ready1, ready2, ready3] = await Promise.all([
      ensureBackendReady({ baseUrl }),
      ensureBackendReady({ baseUrl }),
      ensureBackendReady({ baseUrl }),
    ]);
    assert.strictEqual(ready1.status, "ok");
    assert.strictEqual(ready2.status, "ok");
    assert.strictEqual(ready3.status, "ok");
    assert.strictEqual(healthHitCount, 1, "Concurrent ensureBackendReady should deduplicate into 1 request");
    assert.strictEqual(isBackendAwake(), true);
    delayHealthMs = 0;
    console.log("✓ Test 5c Passed: Concurrent ensureBackendReady calls deduplicated.");

    // 5d. Readiness timeout: when /health fails/times out, classified as readiness_timeout and simulation is never submitted
    resetBackendReadiness();
    healthHitCount = 0;
    simHitCount = 0;
    delayHealthMs = 200; // 200ms delay, exceed with 30ms timeout

    let didThrowTimeout = false;
    try {
      await ensureBackendReady({ baseUrl, timeoutMs: 30, fastProbeTimeoutMs: 15, pollIntervalMs: 20 });
    } catch (err: unknown) {
      didThrowTimeout = true;
      assert(err instanceof ApiError, `Expected ApiError, got: ${String(err)}`);
      assert.strictEqual(err.isReadinessTimeout, true);
      assert.strictEqual(err.isTimeout, true);
      assert.strictEqual(err.statusCode, 408);
      assert(err.message.includes("Render Free"), "Error message should mention Render Free tier");
    }
    assert.strictEqual(didThrowTimeout, true, "Should have thrown readiness timeout");
    assert.strictEqual(simHitCount, 0, "Simulation was never submitted after readiness failure");
    delayHealthMs = 0;
    console.log("✓ Test 5d Passed: Readiness timeout classified cleanly, simulation never submitted.");

    // 5e. Cancellation during readiness probe
    resetBackendReadiness();
    const abortCtrl = new AbortController();
    abortCtrl.abort(); // already aborted
    try {
      await postSimulation(
        { preset_id: "schwarzschild_isco_circular" },
        { baseUrl, signal: abortCtrl.signal }
      );
      assert.fail("Should have aborted");
    } catch (err: unknown) {
      assert(err instanceof ApiError, "Expected ApiError");
      assert.strictEqual(err.isAborted, true);
      assert.strictEqual(err.statusCode, 499);
    }
    assert.strictEqual(simHitCount, 0, "Simulation never dispatched when aborted");
    console.log("✓ Test 5e Passed: AbortSignal cancels readiness check before simulation submission.");
  } finally {
    await new Promise<void>((resolve) => server.close(() => resolve()));
  }
}

// 6. Regression Test: Stale Backend-Awake State Recovery After Render Free Idle
async function testStaleBackendAwakeRecovery(): Promise<void> {
  let healthHitCount = 0;
  let simHitCount = 0;
  let backendSleeping = false;
  let failHealthAttempts = 0;

  const server = http.createServer((req, res) => {
    if (req.url === "/health") {
      healthHitCount++;
      if (backendSleeping && failHealthAttempts > 0) {
        failHealthAttempts--;
        // Return 503 simulating container currently spinning up
        res.writeHead(503, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ error_type: "starting", message: "Container spinning up" }));
        return;
      }
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify({
        status: "ok",
        engine: "kerr-geodesics",
        version: "1.0.0",
        commit_hash: "062b20c80a689640637a2fcd003bdd921a7d4132",
      }));
      return;
    }

    if (req.url === "/api/v1/simulations") {
      simHitCount++;
      if (backendSleeping && failHealthAttempts > 0) {
        // If simulation was called while backend was sleeping, fail loudly!
        res.writeHead(502, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ error_type: "bad_gateway", message: "Container not ready" }));
        return;
      }
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify({
        preset_id: "schwarzschild_isco_circular",
        config_hash: "mock",
        status: "completed",
        termination_reason: "completed",
        solver_diagnostics: { method: "DOP853", nfev: 10, rtol: 1e-10, atol: 1e-12 },
        trajectory: {
          lambdas: [0, 1],
          coordinates: { t: [0, 1], r: [6, 6], theta: [1.57, 1.57], phi: [0, 0.1] },
          momenta: { p_t: [-1, -1], p_r: [0, 0], p_theta: [0, 0], p_phi: [3.46, 3.46] },
        },
        conserved_quantities: {
          energy: 0.94,
          angular_momentum: 3.46,
          carter_constant: null,
          hamiltonian_drift_max: 1e-14,
        },
        triggered_events: [],
        provenance: {
          engine: "kerr-geodesics",
          version: "1.0.0",
          commit_hash: "062b20c80a689640637a2fcd003bdd921a7d4132",
        },
      }));
      return;
    }
    res.writeHead(404);
    res.end();
  });

  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", () => resolve()));
  const addr = server.address();
  const port = typeof addr === "object" && addr ? addr.port : 0;
  assert(port > 0, "Server must bind to ephemeral port");
  const baseUrl = `http://127.0.0.1:${port}`;

  try {
    // Step 1: Health check succeeds and frontend marks backend awake
    resetBackendReadiness();
    const initReady = await ensureBackendReady({ baseUrl });
    assert.strictEqual(initReady.status, "ok");
    assert.strictEqual(isBackendAwake(), true, "Backend should be marked awake");
    assert.strictEqual(isBackendStale(), false, "Backend should be fresh");
    assert.strictEqual(healthHitCount, 1);

    // Warm request check: within freshness window, simulation executes immediately with 0 extra health checks
    simHitCount = 0;
    const warmSim = await postSimulation(
      { preset_id: "schwarzschild_isco_circular" },
      { baseUrl }
    );
    assert.strictEqual(warmSim.status, "completed");
    assert.strictEqual(healthHitCount, 1, "Warm simulation should not make extra health checks");
    assert.strictEqual(simHitCount, 1);

    // Step 2: Backend subsequently becomes unavailable/sleeps (simulates 15m idle spin down)
    backendSleeping = true;
    failHealthAttempts = 2; // will fail first 2 health probes, then wake up
    // Mark state as stale (simulates user keeping tab open past 60s / 15m)
    markBackendStale();
    assert.strictEqual(isBackendStale(), true, "Backend should be detected as stale");

    // Step 3 & 4: A new simulation is requested while frontend had been previously awake
    // Frontend detects staleness, performs lightweight probe, detects sleeping backend,
    // recoverably waits for readiness, then executes simulation
    simHitCount = 0;
    const recoveredSim = await postSimulation(
      { preset_id: "schwarzschild_isco_circular" },
      { baseUrl, pollIntervalMs: 50, fastProbeTimeoutMs: 50 }
    );

    // Step 5: Simulation is submitted exactly once after readiness succeeds
    assert.strictEqual(recoveredSim.status, "completed");
    assert.strictEqual(simHitCount, 1, "Simulation must be submitted exactly once after readiness recovery");
    assert.strictEqual(isBackendAwake(), true, "Backend is now awake and fresh");
    assert.strictEqual(isBackendStale(), false);
    console.log("✓ Test 6 Passed: Stale backend-awake state detected after idle; readiness recovered and simulation submitted exactly once.");
  } finally {
    await new Promise<void>((resolve) => server.close(() => resolve()));
  }
}

async function run(): Promise<void> {
  await testClientAbort();
  await testMockServerInteractions();
  await testColdStartReadinessGating();
  await testStaleBackendAwakeRecovery();
  console.log("All Frontend API Client tests passed successfully.");
}

run().catch((err) => {
  console.error("Test failure:", err);
  process.exit(1);
});
