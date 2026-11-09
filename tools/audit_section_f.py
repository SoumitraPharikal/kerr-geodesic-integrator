import os
import csv
import math
import numpy as np
from PIL import Image
import pypdf

output_dir = os.path.join("output", "shadow")

print("=== IMAGE AND PDF FILE INTEGRITY AUDIT ===")
files = sorted(os.listdir(output_dir))

for f in files:
    full_path = os.path.join(output_dir, f)
    size_bytes = os.path.getsize(full_path)
    
    if f.endswith(".png"):
        with Image.open(full_path) as img:
            width, height = img.size
            dpi = img.info.get("dpi", (None, None))
            print(f"PNG: {f:<38} | {size_bytes:>8} bytes | {width}x{height} px | DPI: {dpi}")
            
    elif f.endswith(".pdf"):
        reader = pypdf.PdfReader(full_path)
        num_pages = len(reader.pages)
        page = reader.pages[0]
        box = page.mediabox
        w_pt, h_pt = float(box.width), float(box.height)
        w_in, h_in = w_pt / 72.0, h_pt / 72.0
        print(f"PDF: {f:<38} | {size_bytes:>8} bytes | {num_pages} page(s) | {w_pt:.1f}x{h_pt:.1f} pt ({w_in:.2f}x{h_in:.2f} in)")

print("\n=== CSV DATASET AUDIT ===")
for f in ["shadow_contour_data.csv", "shadow_generating_data.csv"]:
    full_path = os.path.join(output_dir, f)
    size_bytes = os.path.getsize(full_path)
    with open(full_path, "r", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        header = next(reader)
        rows = list(reader)
        num_rows = len(rows)
        
        # Check finiteness
        data = np.array([[float(val) for val in row] for row in rows])
        all_finite = bool(np.all(np.isfinite(data)))
        
        print(f"\nCSV: {f} ({size_bytes} bytes, {num_rows} data rows, all_finite={all_finite})")
        print(f"Header: {header}")
        for col_idx, col_name in enumerate(header):
            col_vals = data[:, col_idx]
            print(f"  Col '{col_name}': min = {np.min(col_vals):.6e}, max = {np.max(col_vals):.6e}")

print("\n=== PHYSICAL BENCHMARK VERIFICATION ===")
# 1. Schwarzschild radius 3*sqrt(3)*M
r_schw_exact = 3.0 * math.sqrt(3.0)
from geodesics.metrics.schwarzschild import SchwarzschildMetric
from geodesics.shadow import kerr_shadow_boundary
curve_schw = kerr_shadow_boundary(SchwarzschildMetric(mass=1.0), 0.5 * math.pi, n_points=500)
radii_schw = np.hypot(curve_schw.alpha, curve_schw.beta)
err_schw = np.max(np.abs(radii_schw - r_schw_exact))
print(f"Schwarzschild radius: exact = {r_schw_exact:.14f}, max err = {err_schw:.2e} M")

# 2. Exact-polar radii:
# a = 0: 3*sqrt(3)
# a = 1.0: 2*(1 + sqrt(2)) = 4.82842712474619
from geodesics.metrics.kerr import KerrMetric
curve_p0 = kerr_shadow_boundary(SchwarzschildMetric(mass=1.0), 0.0, n_points=500)
curve_p1 = kerr_shadow_boundary(KerrMetric(mass=1.0, spin=1.0), 0.0, n_points=500)
r_p0 = np.hypot(curve_p0.alpha, curve_p0.beta)
r_p1 = np.hypot(curve_p1.alpha, curve_p1.beta)
r_p1_exact = 2.0 * (1.0 + math.sqrt(2.0))
print(f"Polar a=0 radius: exact = {r_schw_exact:.14f}, max err = {np.max(np.abs(r_p0 - r_schw_exact)):.2e} M")
print(f"Polar a=1 radius: exact = {r_p1_exact:.14f}, max err = {np.max(np.abs(r_p1 - r_p1_exact)):.2e} M")

# 3. Extremal equatorial NHEK segment: alpha = -2.0, beta in [-sqrt(3), +sqrt(3)]
curve_ext = kerr_shadow_boundary(KerrMetric(mass=1.0, spin=1.0), 0.5 * math.pi, n_points=500)
nhek_mask = np.abs(curve_ext.radius - 1.0) < 1e-12
nhek_alpha = curve_ext.alpha[nhek_mask]
nhek_beta = curve_ext.beta[nhek_mask]
sqrt3 = math.sqrt(3.0)
print(f"Extremal NHEK segment (th=90 deg):")
print(f"  alpha: min = {np.min(nhek_alpha):.14f}, max = {np.max(nhek_alpha):.14f} (exact = -2.0, err = {np.max(np.abs(nhek_alpha - (-2.0))):.2e} M)")
print(f"  beta: min = {np.min(nhek_beta):.14f}, max = {np.max(nhek_beta):.14f} (exact = [{-sqrt3:.14f}, {sqrt3:.14f}], err = {max(abs(np.min(nhek_beta) - (-sqrt3)), abs(np.max(nhek_beta) - sqrt3)):.2e} M)")
