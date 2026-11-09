"""Generate visual figures and numerical CSV datasets for Stage 3E-B Kerr Black Hole Shadow.

Publication-quality scientific visualization styling:
- Consistent font hierarchy and clean sans-serif typography.
- Unclipped titles with structured subtitles for physical parameters.
- Compact, unobtrusive legends placed clear of shadow geometry.
- Balanced axes with equal aspect ratio and subtle gridlines.
- Clear, readable annotations for features such as the NHEK vertical segment.

Outputs:
    output/shadow/schwarzschild_shadow.png / .pdf
    output/shadow/kerr_shadow_a05.png / .pdf
    output/shadow/kerr_shadow_a09.png / .pdf
    output/shadow/kerr_shadow_extremal.png / .pdf
    output/shadow/kerr_shadow_inclination_comparison.png / .pdf
    output/shadow/exact_polar_shadow.png / .pdf
    output/shadow/shadow_contour_data.csv
    output/shadow/shadow_generating_data.csv
"""

import math
import os
import csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from geodesics.metrics.kerr import KerrMetric
from geodesics.metrics.schwarzschild import SchwarzschildMetric
from geodesics.shadow import (
    kerr_shadow_boundary,
    kerr_spherical_orbit_radius_range,
    kerr_spherical_photon_orbit_parameters,
)

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output", "shadow")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def setup_plot_style():
    """Configure matplotlib rcParams for publication-quality scientific styling."""
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans", "Helvetica", "Arial"],
        "mathtext.fontset": "dejavusans",
        "font.size": 11,
        "axes.titlesize": 15,
        "axes.labelsize": 13,
        "xtick.labelsize": 10.5,
        "ytick.labelsize": 10.5,
        "legend.fontsize": 9.5,
        "legend.title_fontsize": 10,
        "figure.titlesize": 16,
        "lines.linewidth": 2.2,
        "lines.markersize": 6,
        "grid.alpha": 0.25,
        "grid.linestyle": ":",
        "grid.color": "#888888",
    })


def plot_single_shadow(
    curve,
    main_title: str,
    subtitle: str,
    filename_base: str,
    color: str = "#1f77b4",
    annotation_text: str = None,
    annotation_xy: tuple = None,
    annotation_xytext: tuple = None,
):
    """Plot an individual black hole shadow boundary with clean publication styling."""
    fig, ax = plt.subplots(figsize=(8.0, 7.2), dpi=300)
    ax.set_aspect("equal", adjustable="box")

    # Plot closed boundary (CCW)
    alpha_closed = np.append(curve.alpha, curve.alpha[0])
    beta_closed = np.append(curve.beta, curve.beta[0])

    ax.plot(alpha_closed, beta_closed, color=color, linewidth=2.2, label="Shadow boundary")
    ax.fill(alpha_closed, beta_closed, color=color, alpha=0.12)

    # Plot centroid
    c_alpha, c_beta = curve.centroid
    ax.plot(c_alpha, c_beta, marker="o", color=color, markersize=5, linestyle="None", label=f"Centroid ({c_alpha:.2f}, {c_beta:.2f})")

    # Plot black hole origin
    ax.plot(0, 0, marker="+", color="#111111", markersize=8, markeredgewidth=1.6, linestyle="None", label="Origin (0, 0)")

    # Optional feature annotation (e.g. NHEK segment)
    if annotation_text and annotation_xy and annotation_xytext:
        ax.annotate(
            annotation_text,
            xy=annotation_xy,
            xytext=annotation_xytext,
            arrowprops=dict(arrowstyle="->", color="#333333", lw=1.2, connectionstyle="arc3,rad=-0.12"),
            fontsize=9.5,
            bbox=dict(boxstyle="round,pad=0.35", facecolor="#ffffff", edgecolor="#cccccc", alpha=0.92),
        )

    # Coordinated axis labels and limits
    ax.set_xlabel(r"$\alpha / M$ (Horizontal Celestial Coordinate)")
    ax.set_ylabel(r"$\beta / M$ (Vertical Celestial Coordinate)")
    ax.set_xlim(-7.8, 7.8)
    ax.set_ylim(-6.8, 6.8)
    ax.grid(True)

    # Two-level unclipped title
    ax.set_title(f"{main_title}\n" + r"$\mathregular{" + subtitle + "}$", pad=12, fontsize=14, linespacing=1.35)

    # Compact unobtrusive legend in upper right
    ax.legend(loc="upper right", framealpha=0.90, edgecolor="#cccccc", fancybox=True, borderpad=0.5, handlelength=1.4)

    fig.tight_layout()
    png_path = os.path.join(OUTPUT_DIR, f"{filename_base}.png")
    pdf_path = os.path.join(OUTPUT_DIR, f"{filename_base}.pdf")
    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {png_path} and {pdf_path}")


def generate_all_plots():
    setup_plot_style()
    m_val = 1.0

    # 1. Schwarzschild Shadow (a = 0, M = 1)
    metric_schw = SchwarzschildMetric(mass=m_val)
    curve_schw = kerr_shadow_boundary(metric_schw, observer_inclination=math.radians(90.0), n_points=500)
    plot_single_shadow(
        curve_schw,
        main_title="Schwarzschild Black Hole Shadow",
        subtitle=r"a/M = 0.00 \quad | \quad \theta_o = 90^\circ \quad | \quad R_{\rm shadow} = 3\sqrt{3}M \approx 5.196 M",
        filename_base="schwarzschild_shadow",
        color="#2ca02c",
    )

    # 2. Kerr Shadow a/M = 0.5 (M = 1, theta_o = 90 deg)
    metric_a05 = KerrMetric(mass=m_val, spin=0.5)
    curve_a05 = kerr_shadow_boundary(metric_a05, observer_inclination=math.radians(90.0), n_points=500)
    plot_single_shadow(
        curve_a05,
        main_title="Kerr Black Hole Shadow",
        subtitle=r"a/M = 0.50 \quad | \quad \theta_o = 90^\circ \quad | \quad M = 1.0",
        filename_base="kerr_shadow_a05",
        color="#1f77b4",
    )

    # 3. Kerr Shadow a/M = 0.9 (M = 1, theta_o = 90 deg)
    metric_a09 = KerrMetric(mass=m_val, spin=0.9)
    curve_a09 = kerr_shadow_boundary(metric_a09, observer_inclination=math.radians(90.0), n_points=500)
    plot_single_shadow(
        curve_a09,
        main_title="Rapidly Rotating Kerr Black Hole Shadow",
        subtitle=r"a/M = 0.90 \quad | \quad \theta_o = 90^\circ \quad | \quad M = 1.0",
        filename_base="kerr_shadow_a09",
        color="#ff7f0e",
    )

    # 4. Exact-Extremal Kerr Shadow a/M = 1.0 (M = 1, theta_o = 90 deg)
    metric_ext = KerrMetric(mass=m_val, spin=1.0)
    curve_ext = kerr_shadow_boundary(metric_ext, observer_inclination=math.radians(90.0), n_points=500)
    plot_single_shadow(
        curve_ext,
        main_title="Extremal Kerr Black Hole Shadow",
        subtitle=r"a/M = 1.00 \quad | \quad \theta_o = 90^\circ \quad | \quad M = 1.0",
        filename_base="kerr_shadow_extremal",
        color="#d62728",
        annotation_text="NHEK vertical segment\n" + r"$\alpha = -2M, \; |\beta| \leq \sqrt{3}M$",
        annotation_xy=(-2.0, 0.0),
        annotation_xytext=(-6.8, 2.5),
    )

    # 5. Inclination Comparison (a/M = 0.9, theta_o = 15, 45, 90 deg)
    fig, ax = plt.subplots(figsize=(8.0, 7.2), dpi=300)
    ax.set_aspect("equal", adjustable="box")
    colors = ["#9467bd", "#1f77b4", "#d62728"]
    inclinations = [15.0, 45.0, 90.0]

    for inc_deg, col in zip(inclinations, colors):
        c = kerr_shadow_boundary(metric_a09, observer_inclination=math.radians(inc_deg), n_points=500)
        a_c = np.append(c.alpha, c.alpha[0])
        b_c = np.append(c.beta, c.beta[0])
        ax.plot(a_c, b_c, color=col, linewidth=2.2, label=f"$\\theta_o = {inc_deg:.0f}^\\circ$ (Area: {c.area:.2f} $M^2$)")

    ax.plot(0, 0, marker="+", color="#111111", markersize=8, markeredgewidth=1.6, linestyle="None", label="Origin (0, 0)")
    ax.set_xlabel(r"$\alpha / M$ (Horizontal Celestial Coordinate)")
    ax.set_ylabel(r"$\beta / M$ (Vertical Celestial Coordinate)")
    ax.set_xlim(-7.8, 7.8)
    ax.set_ylim(-6.8, 6.8)
    ax.grid(True)
    ax.set_title(
        "Kerr Shadow Inclination Comparison\n" + r"$\mathregular{a/M = 0.90 \quad | \quad M = 1.0}$",
        pad=12,
        fontsize=14,
        linespacing=1.35,
    )
    ax.legend(loc="upper right", framealpha=0.90, edgecolor="#cccccc", fancybox=True, borderpad=0.5, handlelength=1.4)
    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, "kerr_shadow_inclination_comparison.png"), dpi=300, bbox_inches="tight")
    fig.savefig(os.path.join(OUTPUT_DIR, "kerr_shadow_inclination_comparison.pdf"), bbox_inches="tight")
    plt.close(fig)
    print("Saved: kerr_shadow_inclination_comparison.png and .pdf")

    # 6. Exact-Polar Circular Shadow (theta_o = 0 deg, various spins)
    fig, ax = plt.subplots(figsize=(8.0, 7.2), dpi=300)
    ax.set_aspect("equal", adjustable="box")
    spins = [0.0, 0.5, 0.9, 1.0]
    p_colors = ["#2ca02c", "#1f77b4", "#ff7f0e", "#d62728"]

    for sp, col in zip(spins, p_colors):
        m = KerrMetric(mass=m_val, spin=sp) if sp > 0 else SchwarzschildMetric(mass=m_val)
        c = kerr_shadow_boundary(m, observer_inclination=0.0, n_points=500)
        a_c = np.append(c.alpha, c.alpha[0])
        b_c = np.append(c.beta, c.beta[0])
        r_p = c.width / 2.0
        ax.plot(a_c, b_c, color=col, linewidth=2.2, label=f"$a/M = {sp:.1f}$: $R_{{\\rm pole}} = {r_p:.3f}M$")

    ax.plot(0, 0, marker="+", color="#111111", markersize=8, markeredgewidth=1.6, linestyle="None", label="Origin (0, 0)")
    ax.set_xlabel(r"$\alpha / M$ (Horizontal Celestial Coordinate)")
    ax.set_ylabel(r"$\beta / M$ (Vertical Celestial Coordinate)")
    ax.set_xlim(-7.8, 7.8)
    ax.set_ylim(-6.8, 6.8)
    ax.grid(True)
    ax.set_title(
        "Exact-Polar Observer Shadow Circles\n" + r"$\mathregular{\theta_o = 0^\circ \text{ (polar observer)} \quad | \quad M = 1.0}$",
        pad=12,
        fontsize=14,
        linespacing=1.35,
    )
    ax.legend(loc="upper right", framealpha=0.90, edgecolor="#cccccc", fancybox=True, borderpad=0.5, handlelength=1.4)
    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, "exact_polar_shadow.png"), dpi=300, bbox_inches="tight")
    fig.savefig(os.path.join(OUTPUT_DIR, "exact_polar_shadow.pdf"), bbox_inches="tight")
    plt.close(fig)
    print("Saved: exact_polar_shadow.png and .pdf")


def generate_csv_datasets():
    m_val = 1.0
    metric_a09 = KerrMetric(mass=m_val, spin=0.9)
    curve = kerr_shadow_boundary(metric_a09, observer_inclination=math.radians(90.0), n_points=500)

    # 1. shadow_contour_data.csv
    contour_path = os.path.join(OUTPUT_DIR, "shadow_contour_data.csv")
    with open(contour_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "index",
            "alpha_over_M",
            "beta_over_M",
            "radius_over_M",
            "xi_over_M",
            "eta_over_M2",
            "dalpha_dlambda",
            "dbeta_dlambda",
        ])
        for i in range(len(curve.alpha)):
            writer.writerow([
                i,
                f"{curve.alpha[i]:.12e}",
                f"{curve.beta[i]:.12e}",
                f"{curve.radius[i]:.12e}",
                f"{curve.xi[i]:.12e}",
                f"{curve.eta[i]:.12e}",
                f"{curve.dalpha_dlambda[i]:.12e}",
                f"{curve.dbeta_dlambda[i]:.12e}",
            ])
    print(f"Saved: {contour_path} ({len(curve.alpha)} rows)")

    # 2. shadow_generating_data.csv (spherical orbit samples across [r_pro, r_retro])
    r_pro, r_retro = kerr_spherical_orbit_radius_range(metric_a09)
    r_samples = np.linspace(r_pro, r_retro, 200)

    gen_path = os.path.join(OUTPUT_DIR, "shadow_generating_data.csv")
    with open(gen_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "index",
            "radius_over_M",
            "xi_over_M",
            "eta_over_M2",
            "theta_min_rad",
            "theta_min_deg",
            "theta_max_rad",
            "theta_max_deg",
        ])
        for idx, r in enumerate(r_samples):
            orb = kerr_spherical_photon_orbit_parameters(metric_a09, r)
            writer.writerow([
                idx,
                f"{orb.radius:.12e}",
                f"{orb.xi:.12e}",
                f"{orb.eta:.12e}",
                f"{orb.theta_min:.12e}",
                f"{math.degrees(orb.theta_min):.8f}",
                f"{orb.theta_max:.12e}",
                f"{math.degrees(orb.theta_max):.8f}",
            ])
    print(f"Saved: {gen_path} ({len(r_samples)} rows)")


if __name__ == "__main__":
    generate_all_plots()
    generate_csv_datasets()
