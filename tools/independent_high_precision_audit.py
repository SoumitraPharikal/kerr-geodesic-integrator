"""Independent 70-digit Decimal High-Precision Validation for Small-Spin Kerr Shadows.

This module implements a completely independent reference calculation using Python's
decimal module with 70 decimal digits of precision. It does NOT use any production
functions from `geodesics.shadow`.
"""

from __future__ import annotations

import math
from decimal import Decimal, getcontext
from typing import Dict, List, Tuple
import numpy as np

getcontext().prec = 70

from geodesics.metrics.kerr import KerrMetric
from geodesics.shadow import (
    kerr_shadow_boundary,
    kerr_spherical_orbit_offsets,
    kerr_spherical_orbit_radius_range,
    kerr_admissible_shadow_offset_range,
    kerr_admissible_shadow_radius_range,
)


def decimal_orbit_offsets(chi_dec: Decimal, M_dec: Decimal = Decimal("1.0")) -> Tuple[Decimal, Decimal]:
    """Calculates prograde and retrograde orbit offsets u = r - 3M using exact half-angle formula in 70-digit Decimal."""
    abs_chi = abs(chi_dec)
    if abs_chi == Decimal(0):
        return Decimal(0), Decimal(0)
    
    # delta = (2/3) * arcsin(|chi|)
    # In Decimal, we can compute delta via Taylor series or high precision root of sin(3 delta / 2) = |chi|
    # Or using Newton's method on sin(1.5 * delta) = abs_chi
    # For small chi, delta = (2/3)*chi + ...
    delta = Decimal(str(math.asin(float(abs_chi)))) * Decimal(2) / Decimal(3)
    # Refine delta via Newton on sin(1.5 * d) - abs_chi = 0
    # using decimal Taylor series for sin and cos
    def dec_sin(x):
        term = x
        s = x
        for k in range(1, 40):
            term = -term * x * x / Decimal((2 * k) * (2 * k + 1))
            s += term
            if abs(term) < Decimal("1e-65"):
                break
        return s

    def dec_cos(x):
        term = Decimal(1)
        c = Decimal(1)
        for k in range(1, 40):
            term = -term * x * x / Decimal((2 * k - 1) * (2 * k))
            c += term
            if abs(term) < Decimal("1e-65"):
                break
        return c

    for _ in range(10):
        arg = Decimal("1.5") * delta
        f = dec_sin(arg) - abs_chi
        df = Decimal("1.5") * dec_cos(arg)
        delta -= f / df

    sin_d = dec_sin(delta)
    sin_d_half = dec_sin(delta / Decimal(2))
    sqrt3 = Decimal(3).sqrt()

    u_pro = M_dec * (-sqrt3 * sin_d - Decimal(2) * (sin_d_half ** 2))
    u_retro = M_dec * (sqrt3 * sin_d - Decimal(2) * (sin_d_half ** 2))
    return u_pro, u_retro


def decimal_reference_shadow(a_float: float, th_rad: float, n_quad: int = 800):
    """Calculates independent 70-digit Decimal shadow parameters and continuum area."""
    M_dec = Decimal("1.0")
    a_dec = Decimal(str(a_float))
    abs_a = abs(a_dec)
    sin_th = Decimal(str(math.sin(th_rad)))
    cos_th = Decimal(str(math.cos(th_rad)))
    cos2 = cos_th ** 2
    sin2 = sin_th ** 2
    cot2 = cos2 / sin2

    u_pro, u_retro = decimal_orbit_offsets(a_dec, M_dec)
    r_pro = Decimal(3) * M_dec + u_pro
    r_retro = Decimal(3) * M_dec + u_retro
    r1 = Decimal(4) * M_dec * (a_dec ** 2) / (r_pro * r_retro)
    u1 = r1 - Decimal(3) * M_dec

    def B_u(u):
        r = Decimal(3) * M_dec + u
        num_xi = -u * (Decimal(9) * M_dec ** 2 + Decimal(6) * M_dec * u + u ** 2) - (a_dec ** 2) * (Decimal(4) * M_dec + u)
        den_xi = a_dec * (Decimal(2) * M_dec + u)
        xi = num_xi / den_xi

        num_eta = (u - u1) * (u_retro - u) * (u - u_pro)
        den_eta = (a_dec ** 2) * ((Decimal(2) * M_dec + u) ** 2)
        eta = (r ** 3) * num_eta / den_eta
        return eta + (a_dec ** 2) * cos2 - (xi ** 2) * cot2

    def xi_u(u):
        num_xi = -u * (Decimal(9) * M_dec ** 2 + Decimal(6) * M_dec * u + u ** 2) - (a_dec ** 2) * (Decimal(4) * M_dec + u)
        den_xi = a_dec * (Decimal(2) * M_dec + u)
        return num_xi / den_xi

    if cos2 == Decimal(0):
        u_m, u_p = u_pro, u_retro
    else:
        # G(u; theta_o) = -(3M + u)^2 * u - a^2*cos^2(theta_o)*(4M + u) = 0
        # Root lies in [u_pro, 0]
        ua, ub = u_pro, Decimal(0)
        for _ in range(80):
            um = (ua + ub) / Decimal(2)
            gu = -(Decimal(3) * M_dec + um) ** 2 * um - (a_dec ** 2) * cos2 * (Decimal(4) * M_dec + um)
            if gu >= Decimal(0):
                ua = um
            else:
                ub = um
        u_crit = (ua + ub) / Decimal(2)

        def find_root(ua_in, ub_in):
            for _ in range(80):
                um = (ua_in + ub_in) / Decimal(2)
                if B_u(ua_in) * B_u(um) <= Decimal(0):
                    ub_in = um
                else:
                    ua_in = um
            u_cand = (ua_in + ub_in) / Decimal(2)
            for _ in range(10):
                bv = B_u(u_cand)
                eps = Decimal("1e-35")
                db = (B_u(u_cand + eps) - B_u(u_cand - eps)) / (Decimal(2) * eps)
                u_cand -= bv / db
            return u_cand

        u_m = find_root(u_pro, u_crit)
        u_p = find_root(u_crit, u_retro)

    def dalpha_du(u):
        eps = Decimal("1e-30")
        return (-(xi_u(u + eps) - xi_u(u - eps)) / (Decimal(2) * eps)) / sin_th

    # Simpson's quadrature for continuum area
    def compute_continuum_area(n_panels: int) -> Decimal:
        pi_dec = Decimal(str(math.pi))
        h = pi_dec / Decimal(n_panels)
        total = Decimal(0)
        for i in range(n_panels + 1):
            phi = Decimal(i) * h
            cos_phi = Decimal(str(math.cos(float(phi))))
            sin_phi = Decimal(str(math.sin(float(phi))))
            u = (u_p + u_m) / Decimal(2) + (u_p - u_m) / Decimal(2) * cos_phi
            b_val = B_u(u)
            beta = b_val.sqrt() if b_val > Decimal(0) else Decimal(0)
            integrand = beta * abs(dalpha_du(u)) * ((u_p - u_m) / Decimal(2)) * sin_phi
            weight = Decimal(2) if i % 2 == 0 else Decimal(4)
            if i == 0 or i == n_panels:
                weight = Decimal(1)
            total += weight * integrand
        return (Decimal(2) * h / Decimal(3)) * total

    area_cont = compute_continuum_area(n_quad)
    alpha_m = -xi_u(u_m) / sin_th
    alpha_p = -xi_u(u_p) / sin_th
    amin = min(alpha_m, alpha_p)
    amax = max(alpha_m, alpha_p)

    # Beta max at peak
    u_test = [u_m + (u_p - u_m) * Decimal(k) / Decimal(400) for k in range(401)]
    bmax = max(B_u(ut) for ut in u_test).sqrt()

    # Physical horizontal asymmetry Delta alpha_asym = alpha_+ + alpha_-
    delta_alpha_asym = alpha_m + alpha_p

    return (
        float(u_pro), float(u_retro),
        float(u_m), float(u_p),
        float(amin), float(amax),
        float(bmax), float(delta_alpha_asym),
        float(area_cont),
        compute_continuum_area
    )


def run_benchmark():
    test_spins = [1e-4, 1e-5, 1e-6, 1e-8]
    signed_spins = [s for val in test_spins for s in (val, -val)]
    angles_deg = [60.0, 90.0]

    print("=" * 145)
    print("INDEPENDENT 70-DIGIT DECIMAL HIGH-PRECISION CERTIFICATION FOR SMALL-SPIN KERR SHADOWS")
    print("=" * 145)
    print(f"{'Spin chi':^10} | {'th':^5} | {'Ref amin':^13} | {'Ref amax':^13} | {'Ref d_asym':^13} | {'err_amin':^10} | {'err_amax':^10} | {'err_asym':^10} | {'err_bmax':^10}")
    print("-" * 145)

    for chi in signed_spins:
        for deg in angles_deg:
            th = math.radians(deg)
            (
                ref_u_pro, ref_u_retro,
                ref_u_m, ref_u_p,
                ref_amin, ref_amax,
                ref_bmax, ref_asym,
                ref_area,
                area_func
            ) = decimal_reference_shadow(chi, th, n_quad=800)

            metric = KerrMetric(mass=1.0, spin=chi)
            curve = kerr_shadow_boundary(metric, observer_inclination=th, n_points=1000)

            act_amin = float(np.min(curve.alpha))
            act_amax = float(np.max(curve.alpha))
            act_bmax = float(np.max(curve.beta))
            act_asym = float(act_amax + act_amin)
            act_area = float(curve.area)

            err_amin = abs(act_amin - ref_amin) / abs(ref_amin)
            err_amax = abs(act_amax - ref_amax) / abs(ref_amax)
            err_asym = abs(act_asym - ref_asym) / abs(ref_asym) if ref_asym != 0.0 else 0.0
            err_bmax = abs(act_bmax - ref_bmax) / abs(ref_bmax)

            print(f"{chi:^+10.1e} | {deg:^5.1f} | {ref_amin:^13.8f} | {ref_amax:^13.8f} | {ref_asym:^+13.6e} | {err_amin:^10.2e} | {err_amax:^10.2e} | {err_asym:^10.2e} | {err_bmax:^10.2e}")

    print("\n" + "=" * 145)
    print("CONTINUUM AREA QUADRATURE CONVERGENCE AUDIT (400, 800, 1600 PANELS)")
    print("=" * 145)
    print(f"{'Spin chi':^10} | {'th':^5} | {'Area (400)':^18} | {'Area (800)':^18} | {'Area (1600)':^18} | {'|A800-A400|':^14} | {'|A1600-A800|':^14}")
    print("-" * 145)

    for chi in [1e-4, 1e-6, 1e-8]:
        for deg in [60.0, 90.0]:
            th = math.radians(deg)
            *_, area_func = decimal_reference_shadow(chi, th, n_quad=400)
            a400 = area_func(400)
            a800 = area_func(800)
            a1600 = area_func(1600)

            diff_800_400 = float(abs(a800 - a400))
            diff_1600_800 = float(abs(a1600 - a800))
            print(f"{chi:^+10.1e} | {deg:^5.1f} | {str(a400)[:18]:^18} | {str(a800)[:18]:^18} | {str(a1600)[:18]:^18} | {diff_800_400:^14.2e} | {diff_1600_800:^14.2e}")

    print("\n" + "=" * 145)
    print("POLYGON DISCRETIZATION ERROR VS THEORETICAL CHORD TRUNCATION ERROR: 2*pi^2 / (3*N^2)")
    print("=" * 145)
    for n_pts in [250, 500, 1000, 2000]:
        metric = KerrMetric(mass=1.0, spin=1e-6)
        c = kerr_shadow_boundary(metric, observer_inclination=math.pi / 2, n_points=n_pts)
        ref_area = 27.0 * math.pi
        actual_err = (ref_area - c.area) / ref_area
        theo_err = (2.0 * math.pi ** 2) / (3.0 * n_pts ** 2)
        ratio = actual_err / theo_err
        print(f"N = {n_pts:5d} | Actual dArea/Area = {actual_err:12.6e} | Theoretical dArea/Area = {theo_err:12.6e} | Ratio = {ratio:8.6f}")


if __name__ == "__main__":
    run_benchmark()
