/**
 * Direct TypeScript test suite for the actual frontend Kerr geometry implementation.
 * Exercises `frontend/src/lib/kerrGeometry.ts` using Node.js native assert.
 */

import assert from "node:assert";
// @ts-expect-error - Node --experimental-strip-types requires explicit .ts extension
import { calculateKerrRadii } from "../src/lib/kerrGeometry.ts";

function approx(actual: number, expected: number, tolerance: number = 1e-12): void {
  const diff = Math.abs(actual - expected);
  assert(
    diff <= tolerance,
    `Expected ${actual} to be approximately ${expected} (diff: ${diff}, tol: ${tolerance})`
  );
}

console.log("Running Kerr Geometry TypeScript tests...");

// 1. Schwarzschild Limit (chi = 0)
{
  const mass = 1.0;
  const res = calculateKerrRadii(0.0, 90.0, mass);

  approx(res.rPlus, 2.0 * mass);
  approx(res.rMinus, 0.0);
  approx(res.rPhPro, 3.0 * mass);
  approx(res.rPhRetro, 3.0 * mass);
  approx(res.rIscoPro, 6.0 * mass);
  approx(res.rIscoRetro, 6.0 * mass);
  approx(res.rErgo, 2.0 * mass);

  // Polar ergosphere at chi = 0
  const resPolar = calculateKerrRadii(0.0, 0.0, mass);
  approx(resPolar.rErgo, 2.0 * mass);
  console.log("✓ Test 1 Passed: Exact Schwarzschild limit (chi = 0)");
}

// 2. High-Spin Ordering and Finiteness (chi = 0.9 and chi = 0.999)
for (const chi of [0.9, 0.999]) {
  const mass = 1.0;
  const res = calculateKerrRadii(chi, 90.0, mass);

  for (const [key, val] of Object.entries(res)) {
    assert(Number.isFinite(val), `Radius ${key} was not finite at chi=${chi}: ${val}`);
  }

  assert(0.0 <= res.rMinus && res.rMinus < res.rPlus, `Horizon ordering violated at chi=${chi}`);
  assert(res.rPlus < res.rPhPro, `r+ not inside prograde photon orbit at chi=${chi}`);
  assert(res.rPhPro < res.rIscoPro, `r_ph_pro not inside prograde ISCO at chi=${chi}`);
  assert(res.rIscoPro < res.rPhRetro, `r_isco_pro not inside retrograde photon at chi=${chi}`);
  assert(res.rPhRetro < res.rIscoRetro, `r_ph_retro not inside retrograde ISCO at chi=${chi}`);
}
console.log("✓ Test 2 Passed: High-spin physical ordering (0 <= r- < r+ < r_ph+ < r_isco+ < r_ph- < r_isco-)");

// 3. Universal Subextremal Ordering (0 < chi < 1)
for (const chi of [0.05, 0.2, 0.5, 0.8, 0.9, 0.999]) {
  const mass = 1.0;
  const res = calculateKerrRadii(chi, 90.0, mass);

  assert(0.0 <= res.rMinus && res.rMinus < res.rPlus, `Horizon ordering violated at chi=${chi}`);
  assert(res.rPlus < res.rPhPro && res.rPhPro < 3.0 * mass && 3.0 * mass < res.rPhRetro, `Photon splitting violated at chi=${chi}`);
  assert(res.rPhPro < res.rIscoPro && res.rIscoPro < 6.0 * mass && 6.0 * mass < res.rIscoRetro, `ISCO splitting violated at chi=${chi}`);
  assert(res.rPhRetro < res.rIscoRetro, `Retrograde photon not inside retrograde ISCO at chi=${chi}`);
}
console.log("✓ Test 3 Passed: Universal subextremal splitting for all 0 < chi < 1");

// 4. Static Limit Boundary Identities (Ergosphere)
for (const chi of [0.0, 0.3, 0.7, 0.9, 0.999]) {
  const mass = 1.0;

  // Equator: theta = 90 deg -> r_ergo == 2M identically
  const resEq = calculateKerrRadii(chi, 90.0, mass);
  approx(resEq.rErgo, 2.0 * mass);

  // Pole: theta = 0 deg -> r_ergo == r+ identically
  const resPole = calculateKerrRadii(chi, 0.0, mass);
  approx(resPole.rErgo, resPole.rPlus);

  // Intermediate angles: r+ <= r_ergo(theta) <= 2M
  for (const deg of [15.0, 30.0, 45.0, 60.0, 75.0]) {
    const res = calculateKerrRadii(chi, deg, mass);
    assert(res.rPlus <= res.rErgo + 1e-12, `r_ergo below r+ at deg=${deg}, chi=${chi}`);
    assert(res.rErgo <= 2.0 * mass + 1e-12, `r_ergo above 2M at deg=${deg}, chi=${chi}`);
  }
}
console.log("✓ Test 4 Passed: Static limit identities (r_ergo(pi/2) == 2M and r_ergo(0) == r+)");

// 5. Linear Mass Scaling
for (const mass of [0.5, 1.0, 2.5, 7.3]) {
  for (const chi of [0.0, 0.5, 0.9, 0.999]) {
    const resUnit = calculateKerrRadii(chi, 45.0, 1.0);
    const resScaled = calculateKerrRadii(chi, 45.0, mass);

    for (const key of ["rPlus", "rMinus", "rErgo", "rPhPro", "rPhRetro", "rIscoPro", "rIscoRetro"] as const) {
      const expected = mass * resUnit[key];
      approx(resScaled[key], expected, 1e-11);
    }
  }
}
console.log("✓ Test 5 Passed: Linear mass scaling r(M) = M * r(1.0)");

// 6. Slider Parameter Grid Domain Safety (zero NaN / Inf)
{
  const spinSteps = Math.round(0.999 / 0.005);
  for (let i = 0; i <= spinSteps; i++) {
    const chi = Math.min(0.999, i * 0.005);
    for (let thetaDeg = 0; thetaDeg <= 90; thetaDeg += 5) {
      const res = calculateKerrRadii(chi, thetaDeg, 1.0);
      for (const [key, val] of Object.entries(res)) {
        assert(!Number.isNaN(val), `NaN encountered at chi=${chi}, theta=${thetaDeg} for ${key}`);
        assert(Number.isFinite(val), `Inf encountered at chi=${chi}, theta=${thetaDeg} for ${key}`);
      }
    }
  }
  console.log("✓ Test 6 Passed: Complete slider grid domain safety (zero NaN or Inf)");
}

console.log("\nALL TYPESCRIPT KERR GEOMETRY TESTS PASSED SUCCESSFULLY.");
