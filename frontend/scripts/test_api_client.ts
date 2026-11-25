/**
 * Direct TypeScript test suite for the frontend API client and error handling.
 * Exercises `frontend/src/lib/api.ts` using Node.js native assert.
 */

import assert from "node:assert";
import http from "node:http";
// @ts-expect-error - Node --experimental-strip-types requires explicit .ts extension
import { ApiError, fetchWithTimeout, DEFAULT_SIMULATION_TIMEOUT_MS, DEFAULT_METADATA_TIMEOUT_MS } from "../src/lib/api.ts";

console.log("Running Frontend API Client TypeScript tests...");

// 1. ApiError Classification Tests
{
  // Timeout error
  const timeoutErr = new ApiError("Request timed out", "timeout_error", 408);
  assert.strictEqual(timeoutErr.isTimeout, true, "Expected isTimeout to be true for timeout_error");
  assert.strictEqual(timeoutErr.isNetworkError, false, "Expected isNetworkError to be false for timeout_error");
  assert.strictEqual(timeoutErr.isValidationError, false);
  assert.strictEqual(timeoutErr.isServerError, false);
  assert.strictEqual(timeoutErr.isAborted, false);

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
  assert.strictEqual(DEFAULT_SIMULATION_TIMEOUT_MS, 25000, "Simulation timeout should be 25s");
  assert.strictEqual(DEFAULT_METADATA_TIMEOUT_MS, 10000, "Metadata timeout should be 10s");
  console.log("✓ Test 4 Passed: Timeout constants verified (25s simulation, 10s metadata).");
}

async function run(): Promise<void> {
  await testClientAbort();
  await testMockServerInteractions();
  console.log("All Frontend API Client tests passed successfully.");
}

run().catch((err) => {
  console.error("Test failure:", err);
  process.exit(1);
});
