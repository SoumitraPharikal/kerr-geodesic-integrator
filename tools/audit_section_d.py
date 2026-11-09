import math
import numpy as np
from geodesics.metrics.kerr import KerrMetric
from geodesics.shadow import (
    kerr_shadow_boundary,
    shadow_contour_normals,
    CRITICAL_INCLINATION_RAD,
)

m_val = 1.0
metric_ext = KerrMetric(mass=m_val, spin=1.0)

# 1. Supercritical at 60 deg
curve_60 = kerr_shadow_boundary(metric_ext, observer_inclination=math.radians(60.0), n_points=500)
n_alpha, n_beta = shadow_contour_normals(curve_60)

# Identify indices:
# Exterior smooth: at retrograde intercept (vertex 0)
print("=== Normal Audit at Key Locations (a=1.0, th=60 deg) ===")
print(f"Vertex 0 (Retrograde intercept: alpha={curve_60.alpha[0]:.4f}, beta={curve_60.beta[0]:.4f}):")
print(f"  Normal: ({n_alpha[0]:.6f}, {n_beta[0]:.6f}), magnitude={math.hypot(n_alpha[0], n_beta[0]):.6f}")

# Find NHEK join points (where radius == M)
nhek_indices = np.where(np.abs(curve_60.radius - m_val) < 1e-12)[0]
idx_top_join = nhek_indices[0]
idx_mid_nhek = nhek_indices[len(nhek_indices)//2]
idx_bot_join = nhek_indices[-1]

print(f"\nTop NHEK corner join (idx={idx_top_join}, alpha={curve_60.alpha[idx_top_join]:.4f}, beta={curve_60.beta[idx_top_join]:.4f}):")
print(f"  Normal: ({n_alpha[idx_top_join]:.6f}, {n_beta[idx_top_join]:.6f})")
print(f"  Incoming edge: ({curve_60.alpha[idx_top_join] - curve_60.alpha[idx_top_join-1]:.4f}, {curve_60.beta[idx_top_join] - curve_60.beta[idx_top_join-1]:.4f})")
print(f"  Outgoing edge: ({curve_60.alpha[idx_top_join+1] - curve_60.alpha[idx_top_join]:.4f}, {curve_60.beta[idx_top_join+1] - curve_60.beta[idx_top_join]:.4f})")

print(f"\nMid NHEK vertical line (idx={idx_mid_nhek}, alpha={curve_60.alpha[idx_mid_nhek]:.4f}, beta={curve_60.beta[idx_mid_nhek]:.4f}):")
print(f"  Normal: ({n_alpha[idx_mid_nhek]:.6f}, {n_beta[idx_mid_nhek]:.6f}) -> exactly pointing left (-1, 0)!")

print(f"\nBottom NHEK corner join (idx={idx_bot_join}, alpha={curve_60.alpha[idx_bot_join]:.4f}, beta={curve_60.beta[idx_bot_join]:.4f}):")
print(f"  Normal: ({n_alpha[idx_bot_join]:.6f}, {n_beta[idx_bot_join]:.6f})")

# 2. Critical cusp at theta_crit
curve_crit = kerr_shadow_boundary(metric_ext, observer_inclination=CRITICAL_INCLINATION_RAD, n_points=500)
n_alpha_c, n_beta_c = shadow_contour_normals(curve_crit)
# Find cusp: minimum alpha
idx_cusp = np.argmin(curve_crit.alpha)
print(f"\nCritical Cusp (idx={idx_cusp}, alpha={curve_crit.alpha[idx_cusp]:.4f}, beta={curve_crit.beta[idx_cusp]:.4e}):")
print(f"  Normal: ({n_alpha_c[idx_cusp]:.6f}, {n_beta_c[idx_cusp]:.6f}) -> exactly pointing left (-1, 0) along symmetry axis!")
