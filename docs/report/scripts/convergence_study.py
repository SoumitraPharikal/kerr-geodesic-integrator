"""Numerical convergence analysis of polygonal shadow area and perimeter.

Computes discrete polygonal estimates A_N and P_N across resolutions:
    N = 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192
for:
1. Schwarzschild (a = 0, theta_o = 90 deg) [analytical circle reference]
2. Kerr a = 0.5, theta_o = 90 deg [subextremal smooth]
3. Kerr a = 0.9, theta_o = 90 deg [rapidly rotating, highly asymmetric]
4. Kerr a = 0.9, theta_o = 15 deg [near-polar smooth]
5. Extremal Kerr a = 1.0, theta_o = 90 deg [contains NHEK vertical segment & corner cusps]

Compares observed errors against theoretical scaling:
    P_N - P_cont = - (pi^2 / 6N^2) * I + O(N^-4)
    A_N - A_cont = - (2*pi^2 / 3N^2) * A_cont + O(N^-4)

Outputs:
- docs/report/figures/shadow_convergence.pdf
- docs/report/figures/shadow_convergence.png
- docs/report/scripts/convergence_data.csv
"""

from __future__ import annotations

import math
import os
import csv
from typing import Dict, List, Tuple

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from geodesics.metrics.kerr import KerrMetric
from geodesics.metrics.schwarzschild import SchwarzschildMetric
from geodesics.shadow import kerr_shadow_boundary


def compute_polygon_area_perimeter(alpha: np.ndarray, beta: np.ndarray) -> Tuple[float, float]:
    """Compute polygon area and perimeter under implicit CCW cyclic closure."""
    a_next = np.roll(alpha, -1)
    b_next = np.roll(beta, -1)
    area = 0.5 * abs(float(np.sum(alpha * b_next - a_next * beta)))
    perimeter = float(np.sum(np.hypot(a_next - alpha, b_next - beta)))
    return area, perimeter


def get_richardson_reference(metric, observer_inclination: float, n1: int = 16384, n2: int = 32768) -> Tuple[float, float]:
    """Compute Richardson-extrapolated continuum reference values."""
    c1 = kerr_shadow_boundary(metric, observer_inclination, n_points=n1)
    c2 = kerr_shadow_boundary(metric, observer_inclination, n_points=n2)
    a1, p1 = compute_polygon_area_perimeter(c1.alpha, c1.beta)
    a2, p2 = compute_polygon_area_perimeter(c2.alpha, c2.beta)
    # Richardson extrapolation eliminating leading O(N^-2) error:
    # V_ref = (4 * V(2N) - V(N)) / 3 + O(N^-4)
    a_ref = (4.0 * a2 - a1) / 3.0
    p_ref = (4.0 * p2 - p1) / 3.0
    return a_ref, p_ref


def main():
    # Setup styling matching technical report
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif", "Computer Modern Roman"],
        "mathtext.fontset": "cm",
        "font.size": 11,
        "axes.titlesize": 13,
        "axes.labelsize": 12,
        "xtick.labelsize": 10.5,
        "ytick.labelsize": 10.5,
        "legend.fontsize": 9.5,
        "lines.linewidth": 1.8,
        "lines.markersize": 5.5,
        "grid.alpha": 0.35,
        "grid.linestyle": ":",
    })

    mass = 1.0
    resolutions = [32, 64, 128, 256, 512, 1024, 2048, 4096, 8192]

    # Analytical reference for Schwarzschild
    r_schw = 3.0 * math.sqrt(3.0) * mass
    a_ref_schw = 27.0 * math.pi * (mass ** 2)
    p_ref_schw = 6.0 * math.sqrt(3.0) * math.pi * mass

    series_info = [
        {
            "id": "schw_90",
            "label": r"Schwarzschild ($a=0, \theta_o=90^\circ$)",
            "metric": SchwarzschildMetric(mass=mass),
            "inc_rad": math.pi / 2.0,
            "a_ref": a_ref_schw,
            "p_ref": p_ref_schw,
            "color": "#2ca02c",  # Green
            "marker": "o",
            "is_exact": True,
        },
        {
            "id": "kerr_a05_90",
            "label": r"Kerr ($a=0.5M, \theta_o=90^\circ$)",
            "metric": KerrMetric(mass=mass, spin=0.5),
            "inc_rad": math.pi / 2.0,
            "color": "#1f77b4",  # Blue
            "marker": "s",
            "is_exact": False,
        },
        {
            "id": "kerr_a09_90",
            "label": r"Kerr ($a=0.9M, \theta_o=90^\circ$)",
            "metric": KerrMetric(mass=mass, spin=0.9),
            "inc_rad": math.pi / 2.0,
            "color": "#ff7f0e",  # Orange
            "marker": "^",
            "is_exact": False,
        },
        {
            "id": "kerr_a09_15",
            "label": r"Kerr ($a=0.9M, \theta_o=15^\circ$)",
            "metric": KerrMetric(mass=mass, spin=0.9),
            "inc_rad": math.radians(15.0),
            "color": "#9467bd",  # Purple
            "marker": "d",
            "is_exact": False,
        },
        {
            "id": "kerr_a10_90",
            "label": r"Extremal ($a=1.0M, \theta_o=90^\circ$)",
            "metric": KerrMetric(mass=mass, spin=1.0),
            "inc_rad": math.pi / 2.0,
            "color": "#d62728",  # Red
            "marker": "v",
            "is_exact": False,
        },
    ]

    # Precompute references for subextremal / extremal cases
    for s in series_info:
        if not s.get("is_exact", False):
            print(f"Computing high-precision reference for {s['id']}...")
            a_ref, p_ref = get_richardson_reference(s["metric"], s["inc_rad"])
            s["a_ref"] = a_ref
            s["p_ref"] = p_ref
            print(f"  Reference A={a_ref:.8f} M^2, P={p_ref:.8f} M")

    all_data = []

    # Run sweeps
    for s in series_info:
        s["ns"] = []
        s["err_a"] = []
        s["err_p"] = []
        s["areas"] = []
        s["perims"] = []

        for n in resolutions:
            c = kerr_shadow_boundary(s["metric"], s["inc_rad"], n_points=n)
            n_actual = len(c.alpha)
            area, perim = compute_polygon_area_perimeter(c.alpha, c.beta)
            err_a = abs(area - s["a_ref"])
            err_p = abs(perim - s["p_ref"])

            s["ns"].append(n_actual)
            s["areas"].append(area)
            s["perims"].append(perim)
            s["err_a"].append(err_a)
            s["err_p"].append(err_p)

            all_data.append({
                "series_id": s["id"],
                "target_N": n,
                "actual_N": n_actual,
                "area": area,
                "perim": perim,
                "err_a": err_a,
                "err_p": err_p,
                "ratio_a_n2": err_a * (n_actual ** 2),
                "ratio_p_n2": err_p * (n_actual ** 2),
            })

    # Save convergence data CSV
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, "convergence_data.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["series_id", "target_N", "actual_N", "area", "perim", "err_a", "err_p", "ratio_a_n2", "ratio_p_n2"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for d in all_data:
            writer.writerow(d)
    print(f"Saved CSV: {csv_path}")

    # Plot 2-panel figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.0, 5.2), dpi=300)

    # Panel (a): Area Discretization Error
    for s in series_info:
        ax1.loglog(
            s["ns"],
            s["err_a"],
            color=s["color"],
            marker=s["marker"],
            label=s["label"],
            alpha=0.92,
        )

    # Theoretical N^-2 reference line for Area
    n_guide = np.array([40, 8000], dtype=np.float64)
    # Match Schwarzschild leading asymptotic ~ 558 / N^2
    err_guide_a = 558.11 / (n_guide ** 2)
    ax1.loglog(n_guide, err_guide_a, "k--", linewidth=1.5, alpha=0.75, label=r"Asymptotic $\mathcal{O}(N^{-2})$ reference")

    ax1.set_xlabel(r"Contour resolution $N$ (number of vertices)")
    ax1.set_ylabel(r"Area Discretization Error $\epsilon_A = |A_N - A_{\rm cont}| / M^2$")
    ax1.set_title(r"(a) Shadow Area Convergence", pad=10)
    ax1.grid(True, which="both")
    ax1.set_xlim(25, 12000)
    ax1.legend(loc="upper right", framealpha=0.92, edgecolor="#cccccc")

    # Panel (b): Perimeter Discretization Error
    for s in series_info:
        ax2.loglog(
            s["ns"],
            s["err_p"],
            color=s["color"],
            marker=s["marker"],
            label=s["label"],
            alpha=0.92,
        )

    # Theoretical N^-2 reference line for Perimeter
    # Match Schwarzschild leading asymptotic ~ 53.7 / N^2
    err_guide_p = 53.70 / (n_guide ** 2)
    ax2.loglog(n_guide, err_guide_p, "k--", linewidth=1.5, alpha=0.75, label=r"Asymptotic $\mathcal{O}(N^{-2})$ reference")

    ax2.set_xlabel(r"Contour resolution $N$ (number of vertices)")
    ax2.set_ylabel(r"Perimeter Discretization Error $\epsilon_P = |P_N - P_{\rm cont}| / M$")
    ax2.set_title(r"(b) Shadow Perimeter Convergence", pad=10)
    ax2.grid(True, which="both")
    ax2.set_xlim(25, 12000)
    ax2.legend(loc="upper right", framealpha=0.92, edgecolor="#cccccc")

    fig.tight_layout()

    report_dir = os.path.dirname(script_dir)
    figures_dir = os.path.join(report_dir, "figures")
    os.makedirs(figures_dir, exist_ok=True)

    pdf_out = os.path.join(figures_dir, "shadow_convergence.pdf")
    png_out = os.path.join(figures_dir, "shadow_convergence.png")

    fig.savefig(pdf_out, bbox_inches="tight")
    fig.savefig(png_out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {pdf_out}")
    print(f"Saved: {png_out}")


if __name__ == "__main__":
    main()
