import math
import numpy as np
from geodesics.metrics.kerr import KerrMetric
from geodesics.shadow import kerr_shadow_boundary

m_val = 1.0
a_pos = 0.8
a_neg = -0.8
th = math.radians(60.0)

metric_pos = KerrMetric(mass=m_val, spin=a_pos)
metric_neg = KerrMetric(mass=m_val, spin=a_neg)

c_pos = kerr_shadow_boundary(metric_pos, observer_inclination=th, n_points=500)
c_neg = kerr_shadow_boundary(metric_neg, observer_inclination=th, n_points=500)

# Check signed areas
print(f"c_pos raw signed area: {c_pos.area:.12f}")
print(f"c_neg raw signed area: {c_neg.area:.12f}")
print(f"Area difference: {abs(c_pos.area - c_neg.area):.2e}")

# Reflection of positive spin contour: (-alpha, beta)
pts_pos_reflected = np.column_stack([-c_pos.alpha, c_pos.beta])
pts_neg = np.column_stack([c_neg.alpha, c_neg.beta])

# Note on traversal:
# For +a, c_pos starts at r_plus (rightmost point: alpha > 0, beta = 0).
# Reflected (-alpha, beta) therefore starts at the leftmost point (-alpha < 0, beta = 0),
# and moves along beta > 0 towards the right (clockwise!).
# In contrast, c_neg is constructed and reversed in shadow.py to be strictly CCW,
# so c_neg starts at its rightmost point and moves leftward along beta > 0!
# Therefore, direct raw-array indexing (pts_pos_reflected[i] == pts_neg[i]) CANNOT match!
raw_array_max_diff = np.max(np.hypot(pts_pos_reflected[:, 0] - pts_neg[:, 0], pts_pos_reflected[:, 1] - pts_neg[:, 1]))
print(f"Raw array indexing max difference: {raw_array_max_diff:.4f} M (confirms raw arrays do not share index 0)")

# Geometric set matching: Hausdorff distance between the two continuous polygonal curves
dists_refl_to_neg = np.min(np.hypot(pts_pos_reflected[:, None, 0] - pts_neg[None, :, 0], pts_pos_reflected[:, None, 1] - pts_neg[None, :, 1]), axis=1)
dists_neg_to_refl = np.min(np.hypot(pts_neg[:, None, 0] - pts_pos_reflected[None, :, 0], pts_neg[:, None, 1] - pts_pos_reflected[None, :, 1]), axis=1)
hausdorff = max(float(np.max(dists_refl_to_neg)), float(np.max(dists_neg_to_refl)))
print(f"Hausdorff distance between S(-a) and Reflected(S(a)): {hausdorff:.2e} M")

# Parameterized arc-length matching
# Find optimal cyclic shift and orientation matching
shifts = []
for s in range(len(pts_neg)):
    # compare pts_neg against shifted reversed reflected points (both CCW)
    diff = np.max(np.hypot(pts_neg[:, 0] - np.roll(pts_pos_reflected[::-1, 0], s),
                           pts_neg[:, 1] - np.roll(pts_pos_reflected[::-1, 1], s)))
    shifts.append(diff)

min_cyclic_diff = min(shifts)
best_s = np.argmin(shifts)
print(f"Optimal cyclic alignment discrepancy (shift={best_s}): {min_cyclic_diff:.2e} M")
