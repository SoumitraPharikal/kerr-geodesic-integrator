import math
from decimal import Decimal, getcontext
import numpy as np

getcontext().prec = 70

from geodesics.metrics.kerr import KerrMetric
from geodesics.shadow import kerr_shadow_boundary

def solve_equatorial_radii_decimal(M_dec, a_dec):
    """Solve r^3 - 6M r^2 + 9M^2 r - 4M a^2 = 0 to 60+ digits."""
    # Two roots around 3M:
    # r_pro < 3M, r_retro > 3M
    # Newton-Raphson
    sqrt3 = Decimal(3).sqrt()
    chi = a_dec / M_dec
    r_pro_0 = Decimal(3) * M_dec - (Decimal(2) / sqrt3) * abs(chi) * M_dec
    r_ret_0 = Decimal(3) * M_dec + (Decimal(2) / sqrt3) * abs(chi) * M_dec
    
    def newton(r_init):
        r = r_init
        for _ in range(25):
            f = r**3 - Decimal(6)*M_dec*(r**2) + Decimal(9)*(M_dec**2)*r - Decimal(4)*M_dec*(a_dec**2)
            f_prime = Decimal(3)*(r**2) - Decimal(12)*M_dec*r + Decimal(9)*(M_dec**2)
            diff = f / f_prime
            r = r - diff
            if abs(diff) < Decimal("1e-62"):
                break
        return r
    
    r_pro = newton(r_pro_0)
    r_ret = newton(r_ret_0)
    if r_pro > r_ret:
        r_pro, r_ret = r_ret, r_pro
    return r_pro, r_ret

def compute_intercepts_decimal(M_dec, a_dec, theta_o_rad):
    """Compute exact alpha_min, alpha_max, beta_max in Decimal."""
    sin_th = Decimal(str(math.sin(theta_o_rad)))
    cos_th = Decimal(str(math.cos(theta_o_rad)))
    cot2 = (cos_th / sin_th)**2
    cos2 = cos_th**2
    
    r_pro, r_ret = solve_equatorial_radii_decimal(M_dec, a_dec)
    
    def xi_dec(r):
        delta = r**2 - Decimal(2)*M_dec*r + a_dec**2
        return (M_dec*(r**2 - a_dec**2) - r*delta) / (a_dec * (r - M_dec))
    
    def eta_dec(r):
        num = Decimal(4)*M_dec*(a_dec**2) - r*((r - Decimal(3)*M_dec)**2)
        return (r**3)*num / ((a_dec**2)*((r - M_dec)**2))
    
    # At equatorial theta_o = 90 deg:
    # prograde:
    xi_p = xi_dec(r_pro)
    xi_r = xi_dec(r_ret)
    
    alpha_p = -xi_p / sin_th
    alpha_r = -xi_r / sin_th
    
    # At r = 3M: eta = 27M^2 exactly
    # beta(3M) = sqrt(27 M^2 + a^2 cos^2 - xi^2 cot^2)
    xi_3m = xi_dec(Decimal(3)*M_dec)
    beta_sq = Decimal(27)*(M_dec**2) + (a_dec**2)*cos2 - (xi_3m**2)*cot2
    beta_max = beta_sq.sqrt()
    
    return min(alpha_p, alpha_r), max(alpha_p, alpha_r), beta_max

M_val = 1.0
M_dec = Decimal("1.0")

spins = [1e-6, 1.001e-6, 1.01e-6, 1e-5, 1e-4]
# also negative spins
spins_all = spins + [-s for s in spins]

print("=== Independent High-Precision Decimal Audit (60 digits) ===")
print(f"{'Spin chi':^12} | {'th (deg)':^8} | {'alpha_min rel err':^18} | {'alpha_max rel err':^18} | {'beta_max rel err':^18} | {'Width rel err':^18}")
print("-" * 105)

for s in [1e-6, 1.001e-6, 1.01e-6, 1e-5, 1e-4, -1e-6, -1e-4]:
    a_dec = Decimal(str(s))
    for th_deg in [90.0, 60.0]:
        th_rad = math.radians(th_deg)
        ref_amin, ref_amax, ref_bmax = compute_intercepts_decimal(M_dec, a_dec, th_rad)
        
        metric = KerrMetric(mass=M_val, spin=s)
        curve = kerr_shadow_boundary(metric, observer_inclination=th_rad, n_points=1000)
        
        act_amin = float(np.min(curve.alpha))
        act_amax = float(np.max(curve.alpha))
        act_bmax = float(np.max(curve.beta))
        
        # relative errors against 60-digit decimal reference
        err_amin = abs(act_amin - float(ref_amin)) / abs(float(ref_amin))
        err_amax = abs(act_amax - float(ref_amax)) / abs(float(ref_amax))
        err_bmax = abs(act_bmax - float(ref_bmax)) / abs(float(ref_bmax))
        
        ref_width = float(ref_amax - ref_amin)
        act_width = float(curve.width)
        err_width = abs(act_width - ref_width) / ref_width
        
        print(f"{s:^12.2e} | {th_deg:^8.1f} | {err_amin:^18.2e} | {err_amax:^18.2e} | {err_bmax:^18.2e} | {err_width:^18.2e}")
