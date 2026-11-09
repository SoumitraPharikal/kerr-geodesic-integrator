import math
from decimal import Decimal, getcontext
import numpy as np

getcontext().prec = 70

from geodesics.metrics.kerr import KerrMetric
from geodesics.shadow import kerr_shadow_boundary

def decimal_roots_B(M_dec, a_dec, theta_o_rad):
    sin_th = Decimal(str(math.sin(theta_o_rad)))
    cos_th = Decimal(str(math.cos(theta_o_rad)))
    sin2 = sin_th**2
    cos2 = cos_th**2
    cot2 = cos2 / sin2
    
    # B(r) = eta(r) + a^2 cos^2 - xi(r)^2 cot^2
    def B(r):
        delta = r**2 - Decimal(2)*M_dec*r + a_dec**2
        xi = (M_dec*(r**2 - a_dec**2) - r*delta) / (a_dec * (r - M_dec))
        num = Decimal(4)*M_dec*(a_dec**2) - r*((r - Decimal(3)*M_dec)**2)
        eta = (r**3)*num / ((a_dec**2)*((r - M_dec)**2))
        return eta + (a_dec**2)*cos2 - (xi**2)*cot2
    
    # Near r = 3M, B(r) is concave down with maximum near 3M
    # Solve B(r) = 0 for r_minus < 3M and r_plus > 3M via bisection + Newton
    def find_root(r_a, r_b):
        # bisection to bracket closely
        for _ in range(50):
            r_mid = (r_a + r_b) / Decimal(2)
            if B(r_a) * B(r_mid) <= 0:
                r_b = r_mid
            else:
                r_a = r_mid
        return (r_a + r_b) / Decimal(2)
    
    r_mid = Decimal(3) * M_dec
    # span is of order a
    delta = abs(a_dec) * Decimal(2)
    r_minus = find_root(r_mid - delta, r_mid)
    r_plus = find_root(r_mid, r_mid + delta)
    
    def xi_val(r):
        delta = r**2 - Decimal(2)*M_dec*r + a_dec**2
        return (M_dec*(r**2 - a_dec**2) - r*delta) / (a_dec * (r - M_dec))
    
    alpha_1 = -xi_val(r_minus) / sin_th
    alpha_2 = -xi_val(r_plus) / sin_th
    
    # Vertical coordinate at r = 3M
    xi_3 = xi_val(r_mid)
    beta_max = (Decimal(27)*(M_dec**2) + (a_dec**2)*cos2 - (xi_3**2)*cot2).sqrt()
    
    return float(min(alpha_1, alpha_2)), float(max(alpha_1, alpha_2)), float(beta_max)

M_val = 1.0
M_dec = Decimal("1.0")

spins = [1e-6, 1.001e-6, 1.01e-6, 1e-5, 1e-4]
spins_all = spins + [-s for s in spins]

print(f"{'Spin chi':^12} | {'th':^6} | {'Ref alpha_min':^16} | {'Act alpha_min':^16} | {'Rel Err alpha_min':^18} | {'Rel Err alpha_max':^18} | {'Rel Err beta_max':^18}")
print("-" * 115)

for s in spins_all:
    a_dec = Decimal(str(s))
    th_deg = 60.0
    th_rad = math.radians(th_deg)
    
    ref_amin, ref_amax, ref_bmax = decimal_roots_B(M_dec, a_dec, th_rad)
    
    metric = KerrMetric(mass=M_val, spin=s)
    curve = kerr_shadow_boundary(metric, observer_inclination=th_rad, n_points=1000)
    
    act_amin = float(np.min(curve.alpha))
    act_amax = float(np.max(curve.alpha))
    act_bmax = float(np.max(curve.beta))
    
    err_amin = abs(act_amin - ref_amin) / abs(ref_amin)
    err_amax = abs(act_amax - ref_amax) / abs(ref_amax)
    err_bmax = abs(act_bmax - ref_bmax) / abs(ref_bmax)
    
    print(f"{s:^12.2e} | {th_deg:^6.1f} | {ref_amin:^16.8f} | {act_amin:^16.8f} | {err_amin:^18.2e} | {err_amax:^18.2e} | {err_bmax:^18.2e}")
