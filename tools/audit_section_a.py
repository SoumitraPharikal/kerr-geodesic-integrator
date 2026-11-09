import math
import numpy as np
from geodesics.metrics.kerr import KerrMetric
from geodesics.shadow import kerr_shadow_boundary, CRITICAL_INCLINATION_RAD

m_val = 1.0
metric = KerrMetric(mass=m_val, spin=1.0)
theta_crit = CRITICAL_INCLINATION_RAD
print(f"theta_crit = {math.degrees(theta_crit):.6f} deg, pi - theta_crit = {math.degrees(math.pi - theta_crit):.6f} deg\n")

angles = [30.0, 48.0, 60.0, 90.0, 120.0, 132.0, 150.0]
print(f"| {'Inclination':^12} | {'C(theta_o)':^12} | {'Visibility':^22} | {'beta_max / M':^14} |")
print("|" + "-"*14 + "|" + "-"*14 + "|" + "-"*24 + "|" + "-"*16 + "|")

for deg in angles:
    th = math.radians(deg)
    cos2 = math.cos(th)**2
    sin2 = math.sin(th)**2
    C = cos2 * (3.0 + cos2) / sin2
    visible = (C < 3.0)
    beta_max = math.sqrt(max(0.0, 3.0 - C)) if visible else 0.0
    vis_str = "Visible (supercritical)" if visible else "Shielded (subcritical)"
    print(f"| {deg:^12.1f} | {C:^12.6f} | {vis_str:^22} | {beta_max:^14.6f} |")

pairs = [(30.0, 150.0), (48.0, 132.0), (60.0, 120.0)]
print("\nNorth/South Geometric Contour Matching:")
for th1_deg, th2_deg in pairs:
    c1 = kerr_shadow_boundary(metric, observer_inclination=math.radians(th1_deg), n_points=500)
    c2 = kerr_shadow_boundary(metric, observer_inclination=math.radians(th2_deg), n_points=500)
    
    pts1 = np.column_stack([c1.alpha, c1.beta])
    pts2 = np.column_stack([c2.alpha, c2.beta])
    
    dists_1_to_2 = np.min(np.hypot(pts1[:, None, 0] - pts2[None, :, 0], pts1[:, None, 1] - pts2[None, :, 1]), axis=1)
    dists_2_to_1 = np.min(np.hypot(pts2[:, None, 0] - pts1[None, :, 0], pts2[:, None, 1] - pts1[None, :, 1]), axis=1)
    hausdorff = max(float(np.max(dists_1_to_2)), float(np.max(dists_2_to_1)))
    
    area_diff = abs(c1.area - c2.area)
    width_diff = abs(c1.width - c2.width)
    height_diff = abs(c1.height - c2.height)
    
    # Check direct index match (shift = 0)
    direct_max_diff = float(np.max(np.hypot(pts1[:, 0] - pts2[:, 0], pts1[:, 1] - pts2[:, 1])))
    
    print(f"Pair ({th1_deg:.0f} deg, {th2_deg:.0f} deg):")
    print(f"  Hausdorff distance: {hausdorff:.2e} M")
    print(f"  Direct array point-to-point max diff: {direct_max_diff:.2e} M")
    print(f"  Area difference: {area_diff:.2e} M^2 (A1={c1.area:.8f}, A2={c2.area:.8f})")
    print(f"  Width diff: {width_diff:.2e} M, Height diff: {height_diff:.2e} M")
