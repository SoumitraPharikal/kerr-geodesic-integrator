"""Reproducible Precision Audit for Kerr Circular Photon Orbits.

This module independently validates double-precision (float64) circular photon orbit
radii (r_ph) and critical impact parameters (b_ph) from KerrMetric against an
independent 100-digit Decimal reference solver using Halley's third-order method.

It reproduces and reconciles all parameter sweeps across:
1. The 135-point initial audit sweep (54.76 eps supported, 126.73 eps at 0.99997488).
2. The 8,000-evaluation dense sweep across 4 spin/orientation branches (84.46 eps).
3. The 10,001-point high-resolution sweep in [0.9990, 0.9999] (98.72 eps).
4. The 100-, 501-, and 2,001-point transition sweeps in [0.99990, 0.99999].
"""

import csv
from decimal import Decimal, getcontext
import os
import sys
from typing import Dict, List, Tuple

import numpy as np

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src")))
from geodesics.metrics.kerr import KerrMetric

# Set Decimal precision context to 100 decimal digits
getcontext().prec = 100

EPS_MACH = float(np.finfo(np.float64).eps)  # 2.220446049250313e-16
THRESHOLD_100_EPS = 100.0 * EPS_MACH       # 2.220446049250313e-14

D1 = Decimal(1)
D2 = Decimal(2)
D3 = Decimal(3)


def decimal_halley_root(chi: Decimal, sigma: int) -> Decimal:
    """Solves P(u) = u^3 - 3u + 2*sigma*chi = 0 using Halley's method to 100 digits."""
    if chi == Decimal(0):
        return D3.sqrt()

    if sigma == 1:
        u = D1 + (D3.sqrt() - D1) * (Decimal(1) - chi)
    else:
        u = D3.sqrt() + (D2 - D3.sqrt()) * chi

    two_sig_chi = Decimal(2 * sigma) * chi
    for _ in range(50):
        u2 = u * u
        f = u * u2 - D3 * u + two_sig_chi
        df = D3 * u2 - D3
        d2f = Decimal(6) * u
        denom = D2 * df * df - f * d2f
        if denom == Decimal(0):
            break
        step = (D2 * f * df) / denom
        u = u - step
        if abs(step) < Decimal("1e-102"):
            break
    return u


def reference_r_and_b(mass: float, spin: float, prograde: bool) -> Tuple[Decimal, Decimal]:
    """Computes exact reference r_ph and b_ph using 100-digit Decimal arithmetic."""
    M_dec = Decimal(str(mass))
    a_dec = Decimal(str(spin))
    chi = abs(a_dec) / M_dec

    if a_dec >= Decimal(0):
        s_val = 1 if prograde else -1
    else:
        s_val = -1 if prograde else 1

    if a_dec == Decimal(0):
        r_ph_dec = D3 * M_dec
        b_ph_dec = Decimal(s_val) * D3 * D3.sqrt() * M_dec
        return r_ph_dec, b_ph_dec

    sigma = 1 if (s_val * a_dec > Decimal(0)) else -1
    u_dec = decimal_halley_root(chi, sigma)
    r_ph_dec = u_dec * u_dec * M_dec

    # Form B: b_ph = [ 2 * s * r_ph * sqrt(M * r_ph) - a * (r_ph + M) ] / (r_ph - M)
    num = D2 * Decimal(s_val) * r_ph_dec * (M_dec * r_ph_dec).sqrt() - a_dec * (r_ph_dec + M_dec)
    den = r_ph_dec - M_dec
    b_ph_dec = num / den
    return r_ph_dec, b_ph_dec


def float64_r_and_b(mass: float, spin: float, prograde: bool) -> Tuple[float, float]:
    """Computes float64 r_ph and b_ph using the actual KerrMetric implementation."""
    m = KerrMetric(mass=mass, spin=spin)
    r_ph = m.photon_orbit_radius(prograde=prograde)
    b_ph = m.photon_orbit_impact_parameter(prograde=prograde)
    return r_ph, b_ph


def rel_err_eval(spin: float, prograde: bool, mass: float = 1.0) -> Tuple[float, float]:
    """Evaluates relative error in r_ph and b_ph between KerrMetric and 100-digit Decimal."""
    r_dec, b_dec = reference_r_and_b(mass, spin, prograde)
    r_flt, b_flt = float64_r_and_b(mass, spin, prograde)

    err_r = float(abs(Decimal(str(r_flt)) - r_dec) / r_dec)
    err_b = float(abs(Decimal(str(b_flt)) - b_dec) / abs(b_dec))
    return err_r, err_b


def run_135_point_sweep() -> Dict[str, float]:
    """Reproduces the exact 135-point sweep from Stage 3D initial audit."""
    spins_coarse = list(np.linspace(0.0, 0.90, 19))
    spins_fine = list(np.linspace(0.90, 0.99, 10))
    log_epsilons = np.linspace(-2.0, -6.0, 41)  # 1 - a from 10^-2 to 10^-6
    spins_near_ext = [1.0 - 10**float(x) for x in log_epsilons]
    all_spins = sorted(list(set(spins_coarse + spins_fine + spins_near_ext)))

    max_err_b_supp = 0.0
    max_err_b_supp_loc = 0.0
    max_err_b_all = 0.0
    max_err_b_all_loc = 0.0
    first_cross = None

    for a in all_spins:
        for prograde in [True, False]:
            if a == 0.0 and not prograde:
                continue
            err_r, err_b = rel_err_eval(a, prograde)
            if a <= 0.9999 + 1e-8:
                if err_b > max_err_b_supp:
                    max_err_b_supp = err_b
                    max_err_b_supp_loc = a
            if err_b > max_err_b_all:
                max_err_b_all = err_b
                max_err_b_all_loc = a
            if err_b > THRESHOLD_100_EPS and first_cross is None:
                first_cross = (a, err_b)

    return {
        "n_samples": len(all_spins) * 2 - 1,
        "max_err_b_supp": max_err_b_supp,
        "max_err_b_supp_loc": max_err_b_supp_loc,
        "max_err_b_all": max_err_b_all,
        "max_err_b_all_loc": max_err_b_all_loc,
        "first_cross_a": first_cross[0] if first_cross else None,
        "first_cross_err": first_cross[1] if first_cross else None,
    }


def run_all_audits(output_dir: str):
    """Executes all sweeps, prints reconciliation, and saves CSV summaries."""
    os.makedirs(output_dir, exist_ok=True)
    print("=" * 80)
    print("REPRODUCIBLE KERR PHOTON ORBIT PRECISION AUDIT (KERMETRIC CODEBASE)")
    print("=" * 80)

    # 1. 135-point sweep reconciliation
    res_135 = run_135_point_sweep()
    print("\n1. 135-Point Initial Sweep:")
    print(f"   Evaluations: {res_135['n_samples']}")
    print(f"   Supported Domain (a <= 0.9999): Max rel err b = {res_135['max_err_b_supp']/EPS_MACH:.2f} eps at a = {res_135['max_err_b_supp_loc']:.6f}")
    print(f"   Full Range (up to a = 0.999999): Max rel err b = {res_135['max_err_b_all']/EPS_MACH:.2f} eps at a = {res_135['max_err_b_all_loc']:.6f}")
    print(f"   First sampled point > 100 eps: a = {res_135['first_cross_a']:.8f} (err = {res_135['first_cross_err']/EPS_MACH:.2f} eps)")

    # 2. 8,000-evaluation sweep across 4 branches
    grid1 = np.linspace(0.0, 0.99, 1001)
    grid2 = 1.0 - np.logspace(np.log10(1e-2), np.log10(1e-4), 1000)
    a_mags = np.unique(np.concatenate([grid1, grid2]))
    print(f"\n2. 8,000-Evaluation Dense Sweep (|a|/M <= 0.9999):")
    print(f"   Samples per branch: {len(a_mags)} | Total across 4 branches: {4 * len(a_mags)}")

    summary_rows = []
    summary_rows.append({
        "sweep": "135_point_initial_supported",
        "branch": "spin=pos_pro",
        "n_points": 135,
        "max_rel_err_b_eps": round(res_135['max_err_b_supp'] / EPS_MACH, 2),
        "max_rel_err_b_raw": f"{res_135['max_err_b_supp']:.5e}",
        "location_a": f"{res_135['max_err_b_supp_loc']:.6f}",
    })
    summary_rows.append({
        "sweep": "135_point_initial_full_range",
        "branch": "spin=pos_pro",
        "n_points": 135,
        "max_rel_err_b_eps": round(res_135['max_err_b_all'] / EPS_MACH, 2),
        "max_rel_err_b_raw": f"{res_135['max_err_b_all']:.5e}",
        "location_a": f"{res_135['max_err_b_all_loc']:.6f}",
    })

    for sign_a in [1.0, -1.0]:
        for prograde in [True, False]:
            branch_max_b = 0.0
            branch_max_a = 0.0
            for chi in a_mags:
                a_val = float(sign_a * chi)
                _, eb = rel_err_eval(a_val, prograde)
                if eb > branch_max_b:
                    branch_max_b = eb
                    branch_max_a = a_val
            b_name = f"spin={'pos' if sign_a > 0 else 'neg'}_{'pro' if prograde else 'retro'}"
            print(f"   Branch {b_name:<16}: Max rel err b = {branch_max_b/EPS_MACH:6.2f} eps at a = {branch_max_a:+.6f}")
            summary_rows.append({
                "sweep": "8000_eval_dense",
                "branch": b_name,
                "n_points": len(a_mags),
                "max_rel_err_b_eps": round(branch_max_b / EPS_MACH, 2),
                "max_rel_err_b_raw": f"{branch_max_b:.5e}",
                "location_a": f"{branch_max_a:+.6f}",
            })

    # 3. 10,001-point uniform sweep in [0.9990, 0.9999]
    print(f"\n3. 10,001-Point High-Resolution Sweep in [0.9990, 0.9999]:")
    dense_10k_grid = np.linspace(0.9990, 0.9999, 10001)
    dense_10k_errs = [rel_err_eval(s, prograde=True)[1] for s in dense_10k_grid]
    max_10k_idx = int(np.argmax(dense_10k_errs))
    max_10k_err = dense_10k_errs[max_10k_idx]
    max_10k_a = dense_10k_grid[max_10k_idx]
    print(f"   Max rel err b = {max_10k_err/EPS_MACH:.2f} eps at a = {max_10k_a:.8f}")
    summary_rows.append({
        "sweep": "10001_point_uniform",
        "branch": "spin=pos_pro",
        "n_points": 10001,
        "max_rel_err_b_eps": round(max_10k_err / EPS_MACH, 2),
        "max_rel_err_b_raw": f"{max_10k_err:.5e}",
        "location_a": f"{max_10k_a:.8f}",
    })

    # Save summary CSV
    csv_path_summary = os.path.join(output_dir, "sweep_subextremal_summary.csv")
    with open(csv_path_summary, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["sweep", "branch", "n_points", "max_rel_err_b_eps", "max_rel_err_b_raw", "location_a"])
        writer.writeheader()
        writer.writerows(summary_rows)
    print(f"\nSaved subextremal sweep summary: {csv_path_summary}")

    # 4. Near-extremal transition grids in [0.99990, 0.99999]
    print(f"\n4. Transition Grids in [0.99990, 0.99999]:")
    trans_rows = []
    for N in [100, 501, 2001]:
        spins = np.linspace(0.99990, 0.99999, N)
        above = []
        for i, a in enumerate(spins):
            _, eb = rel_err_eval(float(a), prograde=True)
            if eb >= THRESHOLD_100_EPS:
                above.append((i, float(a), eb))
        if above:
            first_i, first_a, first_eb = above[0]
            prev_a = float(spins[first_i - 1]) if first_i > 0 else 0.0
            prev_eb = rel_err_eval(prev_a, prograde=True)[1]
            print(f"   Grid N = {N:4d}: First excursion at a = {first_a:.8f} ({first_eb/EPS_MACH:.2f} eps) | Prior a = {prev_a:.8f} ({prev_eb/EPS_MACH:.2f} eps)")
            trans_rows.append({
                "grid_n": N,
                "step_size": f"{spins[1]-spins[0]:.2e}",
                "first_excursion_a": f"{first_a:.8f}",
                "first_excursion_eps": round(first_eb / EPS_MACH, 2),
                "prior_sample_a": f"{prev_a:.8f}",
                "prior_sample_eps": round(prev_eb / EPS_MACH, 2),
                "crossing_interval": f"[{prev_a:.8f}, {first_a:.8f}]",
            })

    csv_path_trans = os.path.join(output_dir, "sweep_near_extremal_transitions.csv")
    with open(csv_path_trans, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["grid_n", "step_size", "first_excursion_a", "first_excursion_eps", "prior_sample_a", "prior_sample_eps", "crossing_interval"])
        writer.writeheader()
        writer.writerows(trans_rows)
    print(f"Saved transition grid summary: {csv_path_trans}")


if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
    run_all_audits(out_dir)
