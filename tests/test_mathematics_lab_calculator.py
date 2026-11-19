"""Independent Python Reference Tests for Kerr Horizon and Orbit-Radius Mathematics.

Provides an independent Python benchmark for the general relativistic formulas,
limits, ordering, and domain safety implemented in the Mathematics Lab.
Note: This module validates the underlying analytical equations in Python; the actual
TypeScript browser implementation is tested directly via `frontend/scripts/test_kerr_geometry.ts`.
"""

import math
import pytest


def calculate_kerr_radii_reference(chi: float, theta_deg: float, mass: float = 1.0) -> dict:
    """Independent Python benchmark implementation of the Kerr radius equations.

    Formulas:
        r± = M * (1 ± sqrt(1 - chi^2))
        r_ergo(theta) = M * (1 + sqrt(1 - chi^2 * cos^2(theta)))
        r_ph_pro = 2M * (1 + cos(2/3 * arccos(-chi)))
        r_ph_retro = 2M * (1 + cos(2/3 * arccos(chi)))
        Z1 = 1 + (1 - chi^2)^(1/3) * ((1 + chi)^(1/3) + (1 - chi)^(1/3))
        Z2 = sqrt(3 * chi^2 + Z1^2)
        r_isco_pro = M * (3 + Z2 - sqrt(max(0, (3 - Z1) * (3 + Z1 + 2 * Z2))))
        r_isco_retro = M * (3 + Z2 + sqrt(max(0, (3 - Z1) * (3 + Z1 + 2 * Z2))))
    """
    clamped_chi = max(-1.0, min(1.0, chi))
    theta_rad = math.radians(theta_deg)
    cos_theta = math.cos(theta_rad)

    term_1_minus_chi2 = max(0.0, 1.0 - clamped_chi**2)
    sqrt_horizon = math.sqrt(term_1_minus_chi2)

    r_plus = mass * (1.0 + sqrt_horizon)
    r_minus = mass * (1.0 - sqrt_horizon)

    r_ergo = mass * (1.0 + math.sqrt(max(0.0, 1.0 - (clamped_chi * cos_theta)**2)))

    # Equatorial photon circular-orbit radii
    r_ph_pro = 2.0 * mass * (1.0 + math.cos((2.0 / 3.0) * math.acos(-clamped_chi)))
    r_ph_retro = 2.0 * mass * (1.0 + math.cos((2.0 / 3.0) * math.acos(clamped_chi)))

    # Timelike ISCO radii (Bardeen-Press-Teukolsky 1972)
    cbrt_1_minus_chi2 = term_1_minus_chi2**(1.0 / 3.0)
    cbrt_1_plus_chi = (1.0 + clamped_chi)**(1.0 / 3.0)
    cbrt_1_minus_chi = max(0.0, 1.0 - clamped_chi)**(1.0 / 3.0)

    z1 = 1.0 + cbrt_1_minus_chi2 * (cbrt_1_plus_chi + cbrt_1_minus_chi)
    z2 = math.sqrt(3.0 * clamped_chi**2 + z1**2)

    isco_radicand = max(0.0, (3.0 - z1) * (3.0 + z1 + 2.0 * z2))
    isco_sqrt = math.sqrt(isco_radicand)

    r_isco_pro = mass * (3.0 + z2 - isco_sqrt)
    r_isco_retro = mass * (3.0 + z2 + isco_sqrt)

    return {
        "r_plus": r_plus,
        "r_minus": r_minus,
        "r_ergo": r_ergo,
        "r_ph_pro": r_ph_pro,
        "r_ph_retro": r_ph_retro,
        "r_isco_pro": r_isco_pro,
        "r_isco_retro": r_isco_retro,
    }


class TestKerrCalculatorFormulas:
    """Verification suite for Kerr radius calculator formulas and limits."""

    def test_zero_spin_schwarzschild_limit(self) -> None:
        """At chi = 0, all quantities must reduce exactly to Schwarzschild values:
        - Outer horizon r+ = 2M
        - Inner horizon r- = 0M
        - Both photon circular-orbit radii = 3M
        - Both ISCO radii = 6M
        - Ergosphere r_ergo(theta) = 2M everywhere.
        """
        mass = 1.0
        res = calculate_kerr_radii_reference(chi=0.0, theta_deg=90.0, mass=mass)

        assert pytest.approx(res["r_plus"], abs=1e-14) == 2.0 * mass
        assert pytest.approx(res["r_minus"], abs=1e-14) == 0.0
        assert pytest.approx(res["r_ph_pro"], abs=1e-14) == 3.0 * mass
        assert pytest.approx(res["r_ph_retro"], abs=1e-14) == 3.0 * mass
        assert pytest.approx(res["r_isco_pro"], abs=1e-14) == 6.0 * mass
        assert pytest.approx(res["r_isco_retro"], abs=1e-14) == 6.0 * mass
        assert pytest.approx(res["r_ergo"], abs=1e-14) == 2.0 * mass

        # Check polar ergosphere at chi = 0
        res_polar = calculate_kerr_radii_reference(chi=0.0, theta_deg=0.0, mass=mass)
        assert pytest.approx(res_polar["r_ergo"], abs=1e-14) == 2.0 * mass

    @pytest.mark.parametrize("chi", [0.9, 0.999])
    def test_high_spin_ordering_and_finiteness(self, chi: float) -> None:
        """For chi = 0.9 and chi = 0.999, all calculated radii must be finite and follow the physical ordering:
        0 <= r- < r+ < r_ph_pro < r_isco_pro < r_ph_retro < r_isco_retro
        """
        mass = 1.0
        res = calculate_kerr_radii_reference(chi=chi, theta_deg=90.0, mass=mass)

        # Finiteness check
        for name, val in res.items():
            assert math.isfinite(val), f"Radius {name} was not finite for chi={chi}: {val}"

        # Strict high-spin physical ordering
        r_minus = res["r_minus"]
        r_plus = res["r_plus"]
        r_ph_pro = res["r_ph_pro"]
        r_isco_pro = res["r_isco_pro"]
        r_ph_retro = res["r_ph_retro"]
        r_isco_retro = res["r_isco_retro"]

        assert 0.0 <= r_minus < r_plus, f"Horizon ordering violated at chi={chi}"
        assert r_plus < r_ph_pro, f"Outer horizon not inside prograde photon orbit at chi={chi}"
        assert r_ph_pro < r_isco_pro, f"Prograde photon orbit not inside prograde ISCO at chi={chi}"
        assert r_isco_pro < r_ph_retro, f"Prograde ISCO not inside retrograde photon orbit at chi={chi}"
        assert r_ph_retro < r_isco_retro, f"Retrograde photon not inside retrograde ISCO at chi={chi}"

    @pytest.mark.parametrize("chi", [0.05, 0.2, 0.5, 0.8, 0.9, 0.999])
    def test_universal_subextremal_ordering(self, chi: float) -> None:
        """For any subextremal spin 0 < chi < 1:
        - 0 <= r- < r+
        - r+ < r_ph_pro < 3M < r_ph_retro
        - r_ph_pro < r_isco_pro < 6M < r_isco_retro
        - r_ph_retro < r_isco_retro
        """
        mass = 1.0
        res = calculate_kerr_radii_reference(chi=chi, theta_deg=90.0, mass=mass)

        assert 0.0 <= res["r_minus"] < res["r_plus"]
        assert res["r_plus"] < res["r_ph_pro"] < 3.0 * mass < res["r_ph_retro"]
        assert res["r_ph_pro"] < res["r_isco_pro"] < 6.0 * mass < res["r_isco_retro"]
        assert res["r_ph_retro"] < res["r_isco_retro"]

    @pytest.mark.parametrize("chi", [0.0, 0.3, 0.7, 0.9, 0.999])
    def test_static_limit_boundary_identities(self, chi: float) -> None:
        """Verifies that for any spin:
        - r_ergo(pi/2) == 2M (equator)
        - r_ergo(0) == r+ (poles)
        - r+ <= r_ergo(theta) <= 2M for all intermediate angles.
        """
        mass = 1.0

        # Equator: theta = 90 deg
        res_eq = calculate_kerr_radii_reference(chi=chi, theta_deg=90.0, mass=mass)
        assert pytest.approx(res_eq["r_ergo"], abs=1e-14) == 2.0 * mass

        # Pole: theta = 0 deg
        res_pole = calculate_kerr_radii_reference(chi=chi, theta_deg=0.0, mass=mass)
        assert pytest.approx(res_pole["r_ergo"], abs=1e-14) == res_pole["r_plus"]

        # Intermediate angles
        for deg in [15.0, 30.0, 45.0, 60.0, 75.0]:
            res = calculate_kerr_radii_reference(chi=chi, theta_deg=deg, mass=mass)
            assert res["r_plus"] <= res["r_ergo"] <= 2.0 * mass + 1e-14

    @pytest.mark.parametrize("mass", [0.5, 1.0, 2.5, 7.3])
    @pytest.mark.parametrize("chi", [0.0, 0.5, 0.9, 0.999])
    def test_linear_mass_scaling(self, mass: float, chi: float) -> None:
        """Verifies that all radii scale strictly and linearly with mass M:
        r(M, chi, theta) = M * r(1.0, chi, theta)
        """
        res_unit = calculate_kerr_radii_reference(chi=chi, theta_deg=45.0, mass=1.0)
        res_scaled = calculate_kerr_radii_reference(chi=chi, theta_deg=45.0, mass=mass)

        for key in res_unit:
            expected = mass * res_unit[key]
            assert pytest.approx(res_scaled[key], rel=1e-13) == expected, (
                f"Radius {key} failed linear mass scaling for M={mass}, chi={chi}"
            )

    def test_slider_domain_safety(self) -> None:
        """Sweeps entire slider parameter grid to ensure zero NaN/Inf or math domain errors."""
        # Spin slider: 0.0 to 0.999 with step 0.005
        # Angle slider: 0 to 90 with step 1
        spin_steps = int(round(0.999 / 0.005))
        for i in range(spin_steps + 1):
            chi = min(0.999, i * 0.005)
            for theta_deg in range(0, 91, 5):
                res = calculate_kerr_radii_reference(chi=chi, theta_deg=float(theta_deg), mass=1.0)
                for name, val in res.items():
                    assert not math.isnan(val), f"NaN encountered at chi={chi}, theta={theta_deg} for {name}"
                    assert not math.isinf(val), f"Inf encountered at chi={chi}, theta={theta_deg} for {name}"
