/**
 * Scientific number formatting utility for Kerr Geodesics Lab.
 *
 * Implements editorial formatting rules:
 * - Proper typographic minus sign (\u2212)
 * - Multiplication sign (\u00D7) and true unicode superscripts for scientific notation
 * - Thin space (\u2009) separating numerical values from physical units
 * - Elimination of floating-point artifacts (e.g., 7.199999999999999 -> 7.20)
 * - Clean tabular display formatting without altering underlying raw floats
 */

const SUPERSCRIPTS: Record<string, string> = {
  "-": "\u207B",
  "0": "\u2070",
  "1": "\u00B9",
  "2": "\u00B2",
  "3": "\u00B3",
  "4": "\u2074",
  "5": "\u2075",
  "6": "\u2076",
  "7": "\u2077",
  "8": "\u2078",
  "9": "\u2079",
};

/**
 * Converts an exponent integer to Unicode superscripts.
 * e.g., -16 -> "⁻¹⁶", 3 -> "³"
 */
export function toSuperscript(exp: number): string {
  const str = String(exp);
  return str
    .split("")
    .map((ch) => SUPERSCRIPTS[ch] || ch)
    .join("");
}

/**
 * Formats a number with true minus sign and rounded to specified decimal places.
 */
export function formatFloat(
  val: number,
  decimals: number = 3,
  fixed: boolean = false
): string {
  if (isNaN(val)) return "NaN";
  if (!isFinite(val)) return val > 0 ? "+∞" : "\u2212∞";

  // Prevent -0
  if (Math.abs(val) < 1e-15) {
    return (0).toFixed(fixed ? decimals : 0);
  }

  const isNeg = val < 0;
  const absVal = Math.abs(val);

  let formatted = fixed ? absVal.toFixed(decimals) : String(Number(absVal.toFixed(decimals)));
  // Eliminate lingering floating-point display artifacts
  if (!fixed && formatted.includes(".")) {
    formatted = formatted.replace(/\.?0+$/, "");
  }

  return (isNeg ? "\u2212" : "") + formatted;
}

/**
 * Formats a floating-point value with an attached physical unit, separated by a thin space.
 * e.g., formatWithUnit(7.2, "M") -> "7.20 M"
 */
export function formatWithUnit(
  val: number,
  unit: string = "M",
  decimals: number = 2
): string {
  const numStr = formatFloat(val, decimals, true);
  return `${numStr}\u2009${unit}`;
}

/**
 * Formats small/large physical quantities into clean scientific notation.
 * e.g., 2.22e-16 -> "2.22 × 10⁻¹⁶"
 * e.g., 0.0 -> "0"
 * e.g., 0.94868359 -> "0.948684"
 */
export function formatScientific(
  val: number,
  options?: {
    sigFigs?: number;
    forceScientificThreshold?: number;
    upperThreshold?: number;
  }
): string {
  if (val === 0) return "0";
  if (isNaN(val)) return "NaN";
  if (!isFinite(val)) return val > 0 ? "+∞" : "\u2212∞";

  const sigFigs = options?.sigFigs ?? 3;
  const forceScientificThreshold = options?.forceScientificThreshold ?? 1e-4;
  const upperThreshold = options?.upperThreshold ?? 1e5;

  const isNeg = val < 0;
  const absVal = Math.abs(val);

  // If within conventional range, display as standard decimal float
  if (absVal >= forceScientificThreshold && absVal < upperThreshold) {
    return formatFloat(val, sigFigs + 1, false);
  }

  // Convert to scientific notation
  const expStr = absVal.toExponential(sigFigs - 1);
  const [mantissaStr, exponentPart] = expStr.split("e");
  const expNum = parseInt(exponentPart, 10);

  const mantissa = parseFloat(mantissaStr);
  const mantissaFormatted = (isNeg ? "\u2212" : "") + mantissa.toFixed(sigFigs - 1);
  const expSuperscript = toSuperscript(expNum);

  return `${mantissaFormatted} \u00D7 10${expSuperscript}`;
}

/**
 * Formats Hamiltonian and Carter constraint drifts.
 * e.g., 2.220446e-16 -> "2.22 × 10⁻¹⁶" or "< 10⁻¹⁵"
 */
export function formatDrift(drift: number): string {
  if (drift === 0 || Math.abs(drift) < 1e-18) {
    return "< 10\u207B\u00B9\u2076";
  }
  return formatScientific(drift, { sigFigs: 3, forceScientificThreshold: 1e-3 });
}

/**
 * Formats coordinates (x, y, r, phi, etc.) for display readouts.
 */
export function formatCoordinate(val: number, decimals: number = 3): string {
  return formatFloat(val, decimals, true);
}
