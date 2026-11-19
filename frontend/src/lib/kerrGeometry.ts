/**
 * Exact analytical formulas for Kerr black hole characteristic radii in Boyer-Lindquist geometry.
 *
 * Geometric conventions:
 * - Units: Geometrized units (G = c = 1)
 * - Dimensionless spin: chi = a / M in [-1, 1], typically subextremal [0, 0.999]
 * - Polar angle: theta in [0, pi] (thetaDeg in [0, 90] degrees)
 * - Mass: M > 0 (defaults to 1.0)
 */

export interface KerrRadii {
  // Dimensionful radii (scaled with M)
  rPlus: number;
  rMinus: number;
  rErgo: number;
  rPhPro: number;
  rPhRetro: number;
  rIscoPro: number;
  rIscoRetro: number;

  // Normalized dimensionless radii (r / M)
  rPlusNorm: number;
  rMinusNorm: number;
  rErgoNorm: number;
  rPhProNorm: number;
  rPhRetroNorm: number;
  rIscoProNorm: number;
  rIscoRetroNorm: number;
}

/**
 * Calculates the exact Kerr event horizons, static limit, photon orbits, and ISCO radii.
 *
 * @param spin Dimensionless spin parameter chi = a/M in [-1, 1]
 * @param thetaDeg Polar angle in degrees (0 = pole, 90 = equator)
 * @param mass Black hole ADM mass M > 0 (default 1.0)
 * @returns KerrRadii containing dimensionful and normalized radii
 */
export function calculateKerrRadii(
  spin: number,
  thetaDeg: number,
  mass: number = 1.0
): KerrRadii {
  const m = Math.max(1e-12, mass);
  const clampedChi = Math.max(-1.0, Math.min(1.0, spin));
  const thetaRad = (thetaDeg * Math.PI) / 180;
  const cosTheta = Math.cos(thetaRad);

  // 1. Event Horizons: r± = M(1 ± √(1 - χ²))
  const term1MinusChi2 = Math.max(0, 1 - clampedChi * clampedChi);
  const sqrtHorizon = Math.sqrt(term1MinusChi2);
  const rPlusNorm = 1 + sqrtHorizon;
  const rMinusNorm = 1 - sqrtHorizon;

  // 2. Static Limit (Ergosphere boundary): r_ergo(θ) = M(1 + √(1 - χ² cos²θ))
  const rErgoNorm = 1 + Math.sqrt(Math.max(0, 1 - (clampedChi * cosTheta) ** 2));

  // 3. Equatorial Circular Photon Orbits:
  // r_ph^pro = 2M [1 + cos(2/3 arccos(-χ))]
  // r_ph^retro = 2M [1 + cos(2/3 arccos(χ))]
  const rPhProNorm = 2 * (1 + Math.cos((2 / 3) * Math.acos(-clampedChi)));
  const rPhRetroNorm = 2 * (1 + Math.cos((2 / 3) * Math.acos(clampedChi)));

  // 4. Timelike ISCO Radii (Bardeen-Press-Teukolsky 1972):
  // Z1 = 1 + (1 - χ²)^(1/3) [ (1 + χ)^(1/3) + (1 - χ)^(1/3) ]
  // Z2 = √(3 χ² + Z1²)
  // r_ISCO^pro = M [ 3 + Z2 - √((3 - Z1)(3 + Z1 + 2 Z2)) ]
  // r_ISCO^retro = M [ 3 + Z2 + √((3 - Z1)(3 + Z1 + 2 Z2)) ]
  const cbrt1MinusChi2 = Math.cbrt(term1MinusChi2);
  const cbrt1PlusChi = Math.cbrt(1 + clampedChi);
  const cbrt1MinusChi = Math.cbrt(Math.max(0, 1 - clampedChi));
  const z1 = 1 + cbrt1MinusChi2 * (cbrt1PlusChi + cbrt1MinusChi);
  const z2 = Math.sqrt(3 * clampedChi * clampedChi + z1 * z1);
  const iscoRadicand = Math.max(0, (3 - z1) * (3 + z1 + 2 * z2));
  const iscoSqrt = Math.sqrt(iscoRadicand);

  const rIscoProNorm = 3 + z2 - iscoSqrt;
  const rIscoRetroNorm = 3 + z2 + iscoSqrt;

  return {
    rPlus: m * rPlusNorm,
    rMinus: m * rMinusNorm,
    rErgo: m * rErgoNorm,
    rPhPro: m * rPhProNorm,
    rPhRetro: m * rPhRetroNorm,
    rIscoPro: m * rIscoProNorm,
    rIscoRetro: m * rIscoRetroNorm,

    rPlusNorm,
    rMinusNorm,
    rErgoNorm,
    rPhProNorm,
    rPhRetroNorm,
    rIscoProNorm,
    rIscoRetroNorm,
  };
}
