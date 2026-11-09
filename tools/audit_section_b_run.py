import math
from decimal import Decimal, getcontext
import numpy as np

getcontext().prec = 70

from geodesics.metrics.kerr import KerrMetric
from geodesics.shadow import (
    kerr_spherical_orbit_radius_range,
    kerr_spherical_photon_orbit_parameters,
    kerr_shadow_boundary,
)

# Reference in Decimal
def solve_equatorial_radii_decimal(M_dec, a_dec):
    sqrt3 = Decimal(3).sqrt()
    chi = a_dec / M_dec
    r_pro_0 = Decimal(3) * M_dec - (Decimal(2) / sqrt3) * abs(chi) * M_dec
    r_ret_0 = Decimal(3) * M_dec + (Decimal(2) / sqrt3) * abs(chi) * M_dec
    for _ in range(30):
        f_p = r_pro_0**3 - Decimal(6)*M_dec*(r_pro_0**2) + Decimal(9)*(M_dec**2)*r_pro_0 - Decimal(4)*M_dec*(a_dec**2)
        df_p = Decimal(3)*(r_pro_0**2) - Decimal(12)*M_dec*r_pro_0 + Decimal(9)*(M_dec**2)
        r_pro_0 -= f_p / df_p
        f_r = r_ret_0**3 - Decimal(6)*M_dec*(r_ret_0**2) + Decimal(9)*(M_dec**2)*r_ret_0 - Decimal(4)*M_dec*(a_dec**2)
        df_r = Decimal(3)*(r_ret_0**2) - Decimal(12)*M_dec*r_ret_0 + Decimal(9)*(M_dec**2)
        r_ret_0 -= f_r / df_r
    if r_pro_0 > r_ret_0:
        r_pro_0, r_ret_0 = r_ret_0, r_pro_0
    return r_pro_0, r_ret_0

def decimal_reference(M_dec, a_dec, theta_o_rad):
    sin_th = Decimal(str(math.sin(theta_o_rad)))
    cos_th = Decimal(str(math.cos(theta_o_rad)))
    cot2 = (cos_th / sin_th)**2
    cos2 = cos_th**2
    
    r_pro, r_ret = solve_equatorial_radii_decimal(M_dec, a_dec)
    
    def xi_dec(r):
        delta = r**2 - Decimal(2)*M_dec*r + a_dec**2
        return (M_dec*(r**2 - a_dec**2) - r*delta) / (a_dec * (r - M_dec))
    
    # At equatorial:
    xi_p = xi_dec(r_pro)
    xi_r = xi_dec(r_ret)
    
    alpha_p = -xi_p / sin_th
    alpha_r = -xi_r / sin_th
    
    # Maximum vertical coordinate: at r = 3M
    xi_3m = xi_dec(Decimal(3)*M_dec)
    beta_sq = Decimal(27)*(M_dec**2) + (a_dec**2)*cos2 - (xi_3m**2)*cot2
    beta_max = beta_sq.sqrt()
    
    return float(min(alpha_p, alpha_r)), float(max(alpha_p, alpha_r)), float(beta_max)

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
    
    ref_amin, ref_amax, ref_bmax = decimal_reference(M_dec, a_dec, th_rad)
    
    metric = KerrMetric(mass=M_val, spin=s)
    curve = kerr_shadow_boundary(metric, observer_inclination=th_rad, n_points=1000)
    
    act_amin = float(np.min(curve.alpha))
    act_amax = float(np.max(curve.alpha))
    act_bmax = float(np.max(curve.beta))
    
    err_amin = abs(act_amin - ref_amin) / abs(ref_amin)
    err_amax = abs(act_amax - ref_amax) / abs(ref_amax)
    err_bmax = abs(act_bmax - ref_bmax) / abs(ref_bmax)
    
    print(f"{s:^12.2e} | {th_deg:^6.1f} | {ref_amin:^16.8f} | {act_amin:^16.8f} | {err_amin:^18.2e} | {err_amax:^18.2e} | {err_bmax:^18.2e}")
