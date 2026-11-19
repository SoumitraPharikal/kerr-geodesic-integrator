"""Generate high-resolution 1200x630 raster social preview image for Kerr Geodesics Lab."""

from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

def create_og_image():
    out_path = Path("frontend/public/og-image.png")

    # 1200 x 630 at 100 dpi
    fig = plt.figure(figsize=(12, 6.3), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1200)
    ax.set_ylim(0, 630)
    ax.axis("off")

    # Background warm-paper
    bg = patches.Rectangle((0, 0), 1200, 630, facecolor="#FAF8F5", edgecolor="none")
    ax.add_patch(bg)

    # Inner card
    card = patches.Rectangle((40, 40), 1120, 550, facecolor="#FFFFFF", edgecolor="#E2DDD5", linewidth=1.5)
    ax.add_patch(card)

    # Subtle grid lines
    ax.plot([100, 1100], [315, 315], color="#F0ECE4", lw=1)
    ax.plot([600, 600], [80, 550], color="#F0ECE4", lw=1)

    # Coordinate rings
    circle1 = patches.Circle((600, 315), 180, fill=False, edgecolor="#F0ECE4", lw=1, ls=(0, (4, 4)))
    circle2 = patches.Circle((600, 315), 90, fill=False, edgecolor="#F0ECE4", lw=1, ls=(0, (2, 3)))
    ax.add_patch(circle1)
    ax.add_patch(circle2)

    # Center Glyph: Horizon disc & orbits
    cx, cy = 600, 390
    bh = patches.Circle((cx, cy), 28, facecolor="#18191B", edgecolor="none", zorder=5)
    ax.add_patch(bh)

    # Precessing ellipses
    e1 = patches.Ellipse((cx, cy), 180, 84, angle=-25, fill=False, edgecolor="#18191B", lw=2.5, zorder=6)
    e2 = patches.Ellipse((cx, cy), 180, 84, angle=35, fill=False, edgecolor="#18191B", lw=2, ls=(0, (4, 4)), zorder=6)
    e3 = patches.Ellipse((cx, cy), 180, 84, angle=95, fill=False, edgecolor="#C2410C", lw=3, zorder=6)
    ax.add_patch(e1)
    ax.add_patch(e2)
    ax.add_patch(e3)

    # Orbiting particle
    pt = patches.Circle((cx + 75, cy - 42), 7, facecolor="#C2410C", edgecolor="none", zorder=7)
    ax.add_patch(pt)

    # Typography
    ax.text(600, 210, "Kerr Geodesics Lab", fontfamily="serif", fontsize=38, fontweight="normal",
            color="#18191B", ha="center", va="center")

    ax.text(600, 165, "Numerical integration of timelike and null geodesics in Kerr and Schwarzschild spacetimes",
            fontfamily="sans-serif", fontsize=15, color="#4B5563", ha="center", va="center")

    # Separator
    ax.plot([450, 750], [130, 130], color="#E2DDD5", lw=1)

    # Provenance
    ax.text(600, 95, "v1.0.0 · Commit 062b20c · MIT License · An independent project by Soumitra Pharikal",
            fontfamily="monospace", fontsize=11, color="#6B7280", ha="center", va="center")

    fig.savefig(out_path, dpi=100, format="png")
    plt.close(fig)
    print(f"Generated {out_path} ({out_path.stat().st_size} bytes)")

if __name__ == "__main__":
    create_og_image()
