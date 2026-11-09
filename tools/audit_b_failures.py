import math
from decimal import Decimal, getcontext
import numpy as np

getcontext().prec = 70

from geodesics.metrics.kerr import KerrMetric
from geodesics.shadow import (
    kerr_spherical_orbit_radius_range,
    kerr_admissible_shadow_radius_range,
    kerr_shadow_boundary
)

m_val = 1.0
print("Testing kerr_admissible_shadow_radius_range at th = 90 deg:")
for s in [1e-6, 1.001e-6, 1.01e-6, 1e-5, 1e-4, 1e-3, 1e-2]:
    metric = KerrMetric(mass=m_val, spin=s)
    r_pro, r_retro = kerr_spherical_orbit_radius_range(metric)
    
    # Calculate eta at r_retro
    denom = (s**2) * ((r_retro - m_val)**2)
    num = 4*m_val*(s**2) - r_retro*((r_retro - 3*m_val)**2)
    eta_ret = (r_retro**3) * num / denom
    
    status_90 = "OK"
    try:
        rng = kerr_admissible_shadow_radius_range(metric, math.radians(90.0))
    except Exception as e:
        status_90 = f"FAILED: {type(e).__name__}: {e}"
        
    status_60 = "OK"
    try:
        rng60 = kerr_admissible_shadow_radius_range(metric, math.radians(60.0))
    except Exception as e:
        status_60 = f"FAILED: {type(e).__name__}: {e}"
        
    print(f"chi = {s:10.2e} | eta(r_retro) = {eta_ret:14.6e} | th=90: {status_90} | th=60: {status_60}")
