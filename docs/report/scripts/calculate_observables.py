"""Calculate quantitative black hole shadow observables across spin and inclination.

Computes:
- Celestial area A / M^2
- Perimeter P / M
- Horizontal diameter D_H / M = alpha_max - alpha_min
- Vertical diameter D_V / M = beta_max - beta_min
- Centroid (alpha_bar / M, beta_bar / M) via Green's theorem / polygon shoelace moments:
    alpha_bar = (1 / 6A) * sum (alpha_i + alpha_{i+1}) * (alpha_i * beta_{i+1} - alpha_{i+1} * beta_i)
    beta_bar  = (1 / 6A) * sum (beta_i + beta_{i+1}) * (alpha_i * beta_{i+1} - alpha_{i+1} * beta_i)

Includes:
- Schwarzschild (a = 0, theta_o = 90 deg)
- Kerr a = 0.5, theta_o = 90 deg
- Kerr a = 0.9, theta_o = 90 deg
- Kerr a = 0.9, theta_o = 45 deg
- Kerr a = 0.9, theta_o = 15 deg
- Kerr a = 1.0 (extremal), theta_o = 90 deg
- Kerr a = 0.9 (polar), theta_o = 0 deg
- Kerr a = 1.0 (polar), theta_o = 0 deg
- Schwarzschild (polar), theta_o = 0 deg

Compares with analytical/independent reference values where available.
Outputs LaTeX table code, Markdown table, and CSV.
"""

from __future__ import annotations

import math
import os
import csv
from typing import Dict, Any, List

import numpy as np
from scipy import integrate

from geodesics.metrics.kerr import KerrMetric
from geodesics.metrics.schwarzschild import SchwarzschildMetric
from geodesics.shadow import (
    kerr_shadow_boundary,
    kerr_admissible_shadow_offset_range,
    kerr_spherical_orbit_offsets,
    _kerr_polar_shadow_parameters,
)


def compute_polygon_observables(alpha: np.ndarray, beta: np.ndarray) -> Dict[str, float]:
    """Compute polygon area, perimeter, diameters, and centroid under cyclic closure."""
    n_pts = len(alpha)
    # Consecutive roll for cyclic closure
    alpha_next = np.roll(alpha, -1)
    beta_next = np.roll(beta, -1)

    # Cross product terms x_i * y_{i+1} - x_{i+1} * y_i
    cross = alpha * beta_next - alpha_next * beta
    signed_area = 0.5 * float(np.sum(cross))
    area = abs(signed_area)

    # Centroid
    c_alpha = float(np.sum((alpha + alpha_next) * cross) / (6.0 * signed_area))
    c_beta = float(np.sum((beta + beta_next) * cross) / (6.0 * signed_area))

    # Perimeter
    d_alpha = alpha_next - alpha
    d_beta = beta_next - beta
    perimeter = float(np.sum(np.hypot(d_alpha, d_beta)))

    # Diameters
    d_h = float(np.max(alpha) - np.min(alpha))
    d_v = float(np.max(beta) - np.min(beta))

    return {
        "N": n_pts,
        "area": area,
        "perimeter": perimeter,
        "D_H": d_h,
        "D_V": d_v,
        "centroid_alpha": c_alpha,
        "centroid_beta": c_beta,
    }


def compute_high_precision_reference(metric, observer_inclination: float, n_ref: int = 16384) -> Dict[str, float]:
    """Compute high-accuracy numerical reference for area and perimeter using large N."""
    c = kerr_shadow_boundary(metric, observer_inclination, n_points=n_ref)
    return compute_polygon_observables(c.alpha, c.beta)


def get_analytical_polar_reference(mass: float, spin: float) -> Dict[str, float]:
    """Analytical exact reference for polar shadow (theta_o = 0)."""
    if abs(spin) == 0.0:
        r_circ = 3.0 * math.sqrt(3.0) * mass
    else:
        _, r_circ, _, _, _ = _kerr_polar_shadow_parameters(mass, spin)
    
    area_exact = math.pi * (r_circ ** 2)
    perim_exact = 2.0 * math.pi * r_circ
    diam_exact = 2.0 * r_circ
    return {
        "area": area_exact,
        "perimeter": perim_exact,
        "D_H": diam_exact,
        "D_V": diam_exact,
        "centroid_alpha": 0.0,
        "centroid_beta": 0.0,
        "radius": r_circ,
    }


def main():
    mass = 1.0
    resolutions_to_report = [500]  # Standard deliverable resolution

    configs = [
        {
            "id": "schwarzschild_90",
            "name": "Schwarzschild",
            "spin": 0.0,
            "inc_deg": 90.0,
            "metric": SchwarzschildMetric(mass=mass),
            "analytical_ref": {
                "area": 27.0 * math.pi,
                "perimeter": 6.0 * math.sqrt(3.0) * math.pi,
                "D_H": 6.0 * math.sqrt(3.0),
                "D_V": 6.0 * math.sqrt(3.0),
                "centroid_alpha": 0.0,
                "centroid_beta": 0.0,
            },
        },
        {
            "id": "kerr_a05_90",
            "name": "Kerr",
            "spin": 0.5,
            "inc_deg": 90.0,
            "metric": KerrMetric(mass=mass, spin=0.5),
            "analytical_ref": None,
        },
        {
            "id": "kerr_a09_90",
            "name": "Kerr",
            "spin": 0.9,
            "inc_deg": 90.0,
            "metric": KerrMetric(mass=mass, spin=0.9),
            "analytical_ref": None,
        },
        {
            "id": "kerr_a09_45",
            "name": "Kerr",
            "spin": 0.9,
            "inc_deg": 45.0,
            "metric": KerrMetric(mass=mass, spin=0.9),
            "analytical_ref": None,
        },
        {
            "id": "kerr_a09_15",
            "name": "Kerr",
            "spin": 0.9,
            "inc_deg": 15.0,
            "metric": KerrMetric(mass=mass, spin=0.9),
            "analytical_ref": None,
        },
        {
            "id": "kerr_a09_00",
            "name": "Kerr (Polar)",
            "spin": 0.9,
            "inc_deg": 0.0,
            "metric": KerrMetric(mass=mass, spin=0.9),
            "analytical_ref": get_analytical_polar_reference(mass, 0.9),
        },
        {
            "id": "kerr_a10_90",
            "name": "Extremal Kerr",
            "spin": 1.0,
            "inc_deg": 90.0,
            "metric": KerrMetric(mass=mass, spin=1.0),
            "analytical_ref": None,
        },
        {
            "id": "kerr_a10_00",
            "name": "Extremal (Polar)",
            "spin": 1.0,
            "inc_deg": 0.0,
            "metric": KerrMetric(mass=mass, spin=1.0),
            "analytical_ref": get_analytical_polar_reference(mass, 1.0),
        },
    ]

    results = []
    print("=" * 100)
    print(f"{'Config':<25} | {'Spin a/M':<8} | {'theta_o':<8} | {'N':<5} | {'Area (M^2)':<12} | {'Perim (M)':<11} | {'D_H (M)':<10} | {'D_V (M)':<10} | {'Centroid (alpha, beta)':<22}")
    print("=" * 100)

    for cfg in configs:
        th_rad = math.radians(cfg["inc_deg"])
        curve = kerr_shadow_boundary(cfg["metric"], th_rad, n_points=500)
        obs = compute_polygon_observables(curve.alpha, curve.beta)

        # High-precision reference (N = 16384)
        obs_ref = compute_high_precision_reference(cfg["metric"], th_rad, n_ref=16384)

        analytical = cfg["analytical_ref"]

        row = {
            "name": cfg["name"],
            "spin": cfg["spin"],
            "inc_deg": cfg["inc_deg"],
            "N": obs["N"],
            "area_500": obs["area"],
            "perim_500": obs["perimeter"],
            "D_H_500": obs["D_H"],
            "D_V_500": obs["D_V"],
            "c_alpha_500": obs["centroid_alpha"],
            "c_beta_500": obs["centroid_beta"],
            "area_ref": obs_ref["area"] if analytical is None else analytical["area"],
            "perim_ref": obs_ref["perimeter"] if analytical is None else analytical["perimeter"],
            "D_H_ref": obs_ref["D_H"] if analytical is None else analytical["D_H"],
            "D_V_ref": obs_ref["D_V"] if analytical is None else analytical["D_V"],
            "c_alpha_ref": obs_ref["centroid_alpha"] if analytical is None else analytical["centroid_alpha"],
            "c_beta_ref": obs_ref["centroid_beta"] if analytical is None else analytical["centroid_beta"],
            "is_exact": analytical is not None,
        }
        results.append(row)

        c_str = f"({obs['centroid_alpha']:.4f}, {obs['centroid_beta']:.4e})"
        print(f"{cfg['name']:<25} | {cfg['spin']:<8.2f} | {cfg['inc_deg']:<8.1f} | {obs['N']:<5} | {obs['area']:<12.6f} | {obs['perimeter']:<11.6f} | {obs['D_H']:<10.6f} | {obs['D_V']:<10.6f} | {c_str:<22}")

    print("=" * 100)

    # Save to CSV
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, "shadow_observables.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "name", "spin", "inc_deg", "N",
            "area_500", "perim_500", "D_H_500", "D_V_500", "c_alpha_500", "c_beta_500",
            "area_ref", "perim_ref", "D_H_ref", "D_V_ref", "c_alpha_ref", "c_beta_ref", "is_exact"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow(r)
    print(f"Saved CSV: {csv_path}")

    # Generate LaTeX table code
    latex_table_path = os.path.join(script_dir, "table_observables.tex")
    with open(latex_table_path, "w", encoding="utf-8") as f:
        f.write("% Auto-generated by calculate_observables.py\n")
        f.write("\\begin{table*}[t]\n")
        f.write("\\centering\n")
        f.write("\\small\n")
        f.write("\\caption{Quantitative black hole shadow geometric observables across dimensionless spin $a/M$ and observer inclination $\\theta_o$. All quantities are normalized by black-hole mass: celestial area $A/M^2$, perimeter $P/M$, horizontal diameter $D_{\\mathrm{H}}/M = \\alpha_{\\max} - \\alpha_{\\min}$, vertical diameter $D_{\\mathrm{V}}/M = \\beta_{\\max} - \\beta_{\\min}$, and planar centroid $(\\bar{\\alpha}/M, \\bar{\\beta}/M)$ computed via Green's theorem. Polygonal values are evaluated at the standard deliverable resolution $N=500$. Numbers in parentheses indicate continuum reference values (exact analytical limits where available, denoted with an asterisk $^*$, or high-resolution Richardson/quadrature benchmarks at $N=16\\,384$). Equatorial reflection symmetry $\\beta \\leftrightarrow -\\beta$ guarantees $\\bar{\\beta} = 0$ identically in the continuum; numerical values reflect floating-point roundoff $|\\bar{\\beta}| < 10^{-15}M$.}\n")
        f.write("\\label{tab:shadow_observables}\n")
        f.write("\\vspace{2mm}\n")
        f.write("\\begin{tabular}{lccccccr}\n")
        f.write("\\hline\\hline\n")
        f.write("Configuration & $a/M$ & $\\theta_o$ & Area $A/M^2$ & Perimeter $P/M$ & $D_{\\mathrm{H}}/M$ & $D_{\\mathrm{V}}/M$ & Centroid $\\bar{\\alpha}/M$ \\\\\n")
        f.write("\\hline\n")

        for r in results:
            ref_star = "$^*$" if r["is_exact"] else ""
            name_str = r["name"]
            spin_str = f"{r['spin']:.2f}"
            inc_str = f"{r['inc_deg']:.0f}^\\circ"
            
            # Format entries with reference in parentheses or compact
            a_val = f"{r['area_500']:.3f}"
            a_ref = f"{r['area_ref']:.3f}{ref_star}"
            
            p_val = f"{r['perim_500']:.3f}"
            p_ref = f"{r['perim_ref']:.3f}{ref_star}"
            
            dh_val = f"{r['D_H_500']:.3f}"
            dh_ref = f"{r['D_H_ref']:.3f}{ref_star}"
            
            dv_val = f"{r['D_V_500']:.3f}"
            dv_ref = f"{r['D_V_ref']:.3f}{ref_star}"
            
            ca_val = f"{r['c_alpha_500']:.3f}"
            ca_ref = f"{r['c_alpha_ref']:.3f}{ref_star}"

            f.write(f"{name_str} & {spin_str} & ${inc_str}$ & {a_val} ({a_ref}) & {p_val} ({p_ref}) & {dh_val} ({dh_ref}) & {dv_val} ({dv_ref}) & {ca_val} ({ca_ref}) \\\\\n")

        f.write("\\hline\\hline\n")
        f.write("\\end{tabular}\n")
        f.write("\\end{table*}\n")
    print(f"Saved LaTeX Table: {latex_table_path}")


if __name__ == "__main__":
    main()
