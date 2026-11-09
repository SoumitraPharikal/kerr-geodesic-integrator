"""Kerr spacetime metric implementation in Boyer-Lindquist coordinates.

Defines the KerrMetric class representing the exterior spacetime of a stationary,
axisymmetric rotating black hole with mass M and signed spin parameter a in
canonical Boyer-Lindquist coordinates:
x^mu = (x0, r, theta, phi) with x0 = t (c = G = 1).

Follows Stage 0 v1.2 specification and Stage 2A requirements.
"""

from typing import Optional
import numpy as np

from geodesics.constants import (
    DEFAULT_MASS,
    IDX_PHI,
    IDX_R,
    IDX_THETA,
    IDX_X0,
)
from geodesics.metrics.base import SpacetimeMetric


class KerrMetric(SpacetimeMetric):
    """Kerr metric in Boyer-Lindquist coordinates (x0, r, theta, phi).

    The line element in geometrized units (G = c = 1) and signature (-+++) is:
        ds^2 = g_{tt} dt^2 + 2 g_{t phi} dt dphi + g_{rr} dr^2 + g_{theta theta} dtheta^2 + g_{phi phi} dphi^2
    where:
        Sigma = r^2 + a^2 cos^2(theta)
        Delta = r^2 - 2 M r + a^2
        A = (r^2 + a^2)^2 - a^2 Delta sin^2(theta)

    Nonzero covariant metric components:
        g_{tt} = -(1 - 2 M r / Sigma)
        g_{t phi} = g_{phi t} = -2 M a r sin^2(theta) / Sigma
        g_{rr} = Sigma / Delta
        g_{theta theta} = Sigma
        g_{phi phi} = A sin^2(theta) / Sigma

    The outer event horizon is located at:
        r_+ = M + sqrt(M^2 - a^2)

    Evaluations are restricted to the regular exterior domain:
        r > r_+,  0 < theta < pi.
    """

    def __init__(self, mass: float = DEFAULT_MASS, spin: float = 0.0) -> None:
        """Initializes the Kerr metric with mass M and signed spin parameter a.

        Parameters
        ----------
        mass : float, optional
            Physical black hole mass M in geometrized units. Must be strictly positive
            and finite. Default is 1.0.
        spin : float, optional
            Signed Kerr spin parameter a = J / M in geometrized units.
            Must be finite and satisfy |a| <= M (sub-extremal or extremal).
            Default is 0.0 (Schwarzschild limit).

        Raises
        ------
        ValueError
            If mass <= 0 or non-finite.
            If spin is non-finite or |a| > M (super-extremal naked singularity).
        """
        if not np.isfinite(mass) or mass <= 0.0:
            raise ValueError(f"Black hole mass M must be positive and finite, got M = {mass}")
        if not np.isfinite(spin):
            raise ValueError(f"Kerr spin parameter a must be finite, got a = {spin}")
        if abs(spin) > mass:
            raise ValueError(
                f"Super-extremal spin |a| = {abs(spin)} > M = {mass} is not a valid black hole "
                f"(naked singularity rejected)."
            )

        self._mass = float(mass)
        self._spin = float(spin)

    @property
    def mass(self) -> float:
        """Physical mass M of the Kerr black hole."""
        return self._mass

    @property
    def spin(self) -> float:
        """Signed Kerr spin parameter a = J / M."""
        return self._spin

    @property
    def horizon_radius(self) -> float:
        """Outer event horizon coordinate radius r_+ = M + sqrt(M^2 - a^2)."""
        radicand = (self._mass - abs(self._spin)) * (self._mass + abs(self._spin))
        # Guard against minor floating-point negative underflow near extremality |a| = M
        radicand_clean = max(0.0, radicand)
        return self._mass + np.sqrt(radicand_clean)

    @property
    def inner_horizon_radius(self) -> float:
        """Inner (Cauchy) horizon coordinate radius r_- = a^2 / r_+ = M - sqrt(M^2 - a^2).

        Evaluated stably via r_- = (|a| / r_+) * |a| using the horizon product identity
        r_+ r_- = a^2. This eliminates catastrophic cancellation for small nonzero spin
        where M - sqrt(M^2 - a^2) would subtract two nearly equal numbers, while avoiding
        intermediate floating-point overflow when squaring large spin values.
        """
        r_plus = self.horizon_radius
        return float((abs(self._spin) / r_plus) * abs(self._spin))

    def isco_radius(self, prograde: bool = True) -> float:
        """Calculates the innermost stable circular orbit (ISCO) radius r_ISCO.

        Parameters
        ----------
        prograde : bool, optional
            Whether the orbit is prograde relative to the black hole spin.
            If True, returns the prograde ISCO radius r_ISCO_pro.
            If False, returns the retrograde ISCO radius r_ISCO_retro.
            Default is True.

        Returns
        -------
        float
            ISCO coordinate radius in Boyer-Lindquist coordinates.
        """
        chi = abs(self._spin) / self._mass
        if chi == 0.0:
            return 6.0 * self._mass
        z1 = 1.0 + ((1.0 - chi * chi) ** (1.0 / 3.0)) * (
            (1.0 + chi) ** (1.0 / 3.0) + (1.0 - chi) ** (1.0 / 3.0)
        )
        z2 = float(np.sqrt(3.0 * chi * chi + z1 * z1))
        term = max(0.0, (3.0 - z1) * (3.0 + z1 + 2.0 * z2))
        sqrt_term = float(np.sqrt(term))
        if prograde:
            return float(self._mass * (3.0 + z2 - sqrt_term))
        return float(self._mass * (3.0 + z2 + sqrt_term))

    @property
    def isco_radius_prograde(self) -> float:
        """Coordinate radius of the prograde ISCO r_ISCO_pro."""
        return self.isco_radius(prograde=True)

    @property
    def isco_radius_retrograde(self) -> float:
        """Coordinate radius of the retrograde ISCO r_ISCO_retro."""
        return self.isco_radius(prograde=False)

    def photon_orbit_radius(self, prograde: bool = True) -> float:
        """Calculates equatorial circular photon orbit radius r_ph.

        Parameters
        ----------
        prograde : bool, optional
            Whether the photon orbit is prograde relative to the spin.
            Default is True.

        Returns
        -------
        float
            Photon orbit coordinate radius in Boyer-Lindquist coordinates.
        """
        chi = abs(self._spin) / self._mass
        if chi == 0.0:
            return 3.0 * self._mass
        if chi == 1.0:
            # Exact-extremal limiting values:
            # Prograde: r_ph = M = r_+ (coincides with event horizon).
            # Retrograde: r_ph = 4M.
            return float(self._mass if prograde else 4.0 * self._mass)
        sign = 1.0 if prograde else -1.0
        cos_arg = max(-1.0, min(1.0, -sign * chi))
        return float(2.0 * self._mass * (1.0 + np.cos((2.0 / 3.0) * np.arccos(cos_arg))))

    @property
    def photon_orbit_radius_prograde(self) -> float:
        """Coordinate radius of the prograde equatorial photon orbit."""
        return self.photon_orbit_radius(prograde=True)

    @property
    def photon_orbit_radius_retrograde(self) -> float:
        """Coordinate radius of the retrograde equatorial photon orbit."""
        return self.photon_orbit_radius(prograde=False)

    def photon_orbit_impact_parameter(self, prograde: bool = True) -> float:
        """Calculates the critical signed impact parameter b_ph = L_z / E for equatorial circular photon orbits.

        Evaluates the closed-form expression:
            b_ph = [ 2 * s * r_ph * sqrt(M * r_ph) - a * (r_ph + M) ] / (r_ph - M)
        where s in {-1, +1} is the azimuthal orientation (s*a > 0 for prograde, s*a < 0 for retrograde).
        For a != 0, this is algebraically identical to:
            b_ph = [ r_ph^2 * (r_ph - 3*M) + a^2 * (r_ph + M) ] / [ a * (M - r_ph) ]
        In the Schwarzschild limit a -> 0, this continuously yields b_ph = s * 3 * sqrt(3) * M.

        Parameters
        ----------
        prograde : bool, optional
            Whether the photon orbit is prograde relative to the black hole spin.
            Default is True.

        Returns
        -------
        float
            Signed critical impact parameter b_ph in geometrized units of M.
        """
        chi = abs(self._spin) / self._mass
        if self._spin == 0.0:
            s_val = 1.0 if prograde else -1.0
            return float(s_val * 3.0 * np.sqrt(3.0) * self._mass)

        if chi == 1.0:
            # Exact-extremal limiting values:
            # Prograde: r_ph = M = r_+. The closed-form expression evaluates to 0/0.
            # Continuous limit is b_ph = 2 * a = 2 * s * M.
            # Retrograde: r_ph = 4M, den = 3M, yielding b_ph = -7 * a = -7 * s * M.
            return float(2.0 * self._spin if prograde else -7.0 * self._spin)

        r_ph = self.photon_orbit_radius(prograde=prograde)
        if self._spin >= 0.0:
            s_val = 1.0 if prograde else -1.0
        else:
            s_val = -1.0 if prograde else 1.0

        num = 2.0 * s_val * r_ph * np.sqrt(self._mass * r_ph) - self._spin * (r_ph + self._mass)
        den = r_ph - self._mass
        return float(num / den)

    @property
    def photon_orbit_impact_parameter_prograde(self) -> float:
        """Critical impact parameter of the prograde equatorial circular photon orbit."""
        return self.photon_orbit_impact_parameter(prograde=True)

    @property
    def photon_orbit_impact_parameter_retrograde(self) -> float:
        """Critical impact parameter of the retrograde equatorial circular photon orbit."""
        return self.photon_orbit_impact_parameter(prograde=False)

    def photon_orbit_frequency(self, prograde: bool = True) -> float:
        """Calculates the coordinate-time angular frequency Omega_ph = dphi / dt for equatorial circular photon orbits.

        Evaluates:
            Omega_ph = s * sqrt(M) / (r_ph^(3/2) + s * a * sqrt(M))
        where s in {-1, +1} is the azimuthal circulation direction.

        Parameters
        ----------
        prograde : bool, optional
            Whether the photon orbit is prograde relative to the black hole spin.
            Default is True.

        Returns
        -------
        float
            Signed orbital frequency Omega_ph = dphi / dt in rad / (geometrized time).
        """
        r_ph = self.photon_orbit_radius(prograde=prograde)
        if self._spin >= 0.0:
            s_val = 1.0 if prograde else -1.0
        else:
            s_val = -1.0 if prograde else 1.0

        num = s_val * np.sqrt(self._mass)
        den = (r_ph ** 1.5) + s_val * self._spin * np.sqrt(self._mass)
        return float(num / den)

    @property
    def photon_orbit_frequency_prograde(self) -> float:
        """Orbital angular frequency of the prograde equatorial circular photon orbit."""
        return self.photon_orbit_frequency(prograde=True)

    @property
    def photon_orbit_frequency_retrograde(self) -> float:
        """Orbital angular frequency of the retrograde equatorial circular photon orbit."""
        return self.photon_orbit_frequency(prograde=False)

    def proper_radial_distance_horizon_to_isco(self, prograde: bool = True) -> float:
        """Calculates the proper radial distance between the outer horizon and ISCO.

        Evaluates the integral:
            Delta_ell = int_{r_+}^{r_ISCO} sqrt(g_{rr}) dr = int_{r_+}^{r_ISCO} [ r / sqrt((r - r_+) (r - r_-)) ] dr
        along a constant-(t, phi, theta=pi/2) Boyer-Lindquist spatial slice using the exact closed-form
        analytic antiderivative:
            Delta_ell = sqrt(Delta(r_ISCO)) + M * ln( [ r_ISCO - M + sqrt(Delta(r_ISCO)) ] / sqrt(M^2 - a^2) )

        Parameters
        ----------
        prograde : bool, optional
            Whether the ISCO is prograde relative to the black hole spin. Default is True.

        Returns
        -------
        float
            Proper radial distance Delta_ell in units of M.

        Raises
        ------
        ValueError
            If the black hole is extremal |a| == M.
        """
        if self.is_extremal:
            raise ValueError(
                f"Proper distance calculation diverges logarithmically in the extremal limit |a| = M = {self._mass}"
            )
        r_isco = self.isco_radius(prograde=prograde)
        delta_isco = self.delta(r_isco)
        sqrt_delta = float(np.sqrt(max(0.0, delta_isco)))
        b_val = float(np.sqrt((self._mass - abs(self._spin)) * (self._mass + abs(self._spin))))
        numerator = (r_isco - self._mass) + sqrt_delta
        return float(sqrt_delta + self._mass * np.log(numerator / b_val))

    @property
    def is_extremal(self) -> bool:
        """Whether the black hole has exact extremal spin |a| == M."""
        return abs(self._spin) == self._mass

    def sigma(self, r: float, theta: float) -> float:
        """Evaluates Sigma(r, theta) = r^2 + a^2 cos^2(theta)."""
        return float(r * r + (self._spin * np.cos(theta)) ** 2)

    def delta(self, r: float) -> float:
        """Evaluates Delta(r) = (r - r_+)(r - r_-) = r^2 - 2 M r + a^2 stably via factorization.

        Factorization eliminates catastrophic cancellation near event horizons,
        particularly for extremal and near-extremal black holes where (r - r_+) and
        (r - r_-) are evaluated without subtracting large nearly-equal polynomial terms.
        """
        return float((r - self.horizon_radius) * (r - self.inner_horizon_radius))

    def A(self, r: float, theta: float) -> float:
        """Evaluates A(r, theta) = (r^2 + a^2)^2 - a^2 Delta sin^2(theta)."""
        r2_plus_a2 = r * r + self._spin * self._spin
        delta_val = self.delta(r)
        sin_theta = np.sin(theta)
        return float((r2_plus_a2 * r2_plus_a2) - (self._spin * self._spin * delta_val * sin_theta * sin_theta))

    def det_cov(self, r: float, theta: float) -> float:
        """Evaluates the exact analytical metric determinant det(g_{mu nu}) = -Sigma^2 sin^2(theta)."""
        self._validate_coordinates(r, theta)
        sigma_val = self.sigma(r, theta)
        sin_theta = np.sin(theta)
        return float(-((sigma_val * sin_theta) ** 2))

    def _validate_radius(self, r: float) -> None:
        """Validates that r is in the regular exterior Boyer-Lindquist domain (r > r_+)."""
        if not np.isfinite(r):
            raise ValueError(f"Radial coordinate r must be finite, got r = {r}")
        if r <= self.horizon_radius:
            raise ValueError(
                f"Radial coordinate r must be strictly outside the outer event horizon "
                f"r_+ = {self.horizon_radius}, got r = {r}"
            )

    def _validate_theta(self, theta: float) -> None:
        """Validates that theta is strictly in the regular domain (0 < theta < pi)."""
        if not np.isfinite(theta):
            raise ValueError(f"Polar angle theta must be finite, got theta = {theta}")
        if theta <= 0.0 or theta >= np.pi:
            raise ValueError(
                f"Polar angle theta must be strictly in the domain (0, pi), got theta = {theta}"
            )

    def _validate_coordinates(self, r: float, theta: float) -> None:
        """Validates both radial and polar coordinates."""
        self._validate_radius(r)
        self._validate_theta(theta)

    def g_cov(self, r: float, theta: float = np.pi / 2.0) -> np.ndarray:
        """Calculates the 4x4 covariant metric tensor g_{mu nu} in Boyer-Lindquist coordinates.

        Coordinate basis: x^mu = (x0, r, theta, phi) where x0 = t.

        Parameters
        ----------
        r : float
            Radial coordinate (r > r_+).
        theta : float, optional
            Polar coordinate in radians (0 < theta < pi). Default is pi/2.

        Returns
        -------
        np.ndarray
            4x4 symmetric array representing g_{mu nu}.
        """
        self._validate_coordinates(r, theta)
        sigma_val = self.sigma(r, theta)
        delta_val = self.delta(r)
        A_val = self.A(r, theta)
        sin_theta = np.sin(theta)
        sin2_theta = sin_theta * sin_theta

        g = np.zeros((4, 4), dtype=np.float64)

        # g_{tt} = -(1 - 2 M r / Sigma)
        g[IDX_X0, IDX_X0] = -(1.0 - (2.0 * self._mass * r) / sigma_val)

        # g_{t phi} = g_{phi t} = -2 M a r sin^2(theta) / Sigma
        g_t_phi = -(2.0 * self._mass * self._spin * r * sin2_theta) / sigma_val
        g[IDX_X0, IDX_PHI] = g_t_phi
        g[IDX_PHI, IDX_X0] = g_t_phi

        # g_{rr} = Sigma / Delta
        g[IDX_R, IDX_R] = sigma_val / delta_val

        # g_{theta theta} = Sigma
        g[IDX_THETA, IDX_THETA] = sigma_val

        # g_{phi phi} = A sin^2(theta) / Sigma
        g[IDX_PHI, IDX_PHI] = (A_val * sin2_theta) / sigma_val

        return g

    def g_contra(self, r: float, theta: float = np.pi / 2.0) -> np.ndarray:
        """Calculates the 4x4 contravariant (inverse) metric tensor g^{mu nu}.

        Analytical closed-form inverse:
            g^{tt} = -A / (Sigma * Delta)
            g^{t phi} = g^{phi t} = -2 M a r / (Sigma * Delta)
            g^{rr} = Delta / Sigma
            g^{theta theta} = 1 / Sigma
            g^{phi phi} = (Delta - a^2 sin^2(theta)) / (Sigma * Delta * sin^2(theta))

        Parameters
        ----------
        r : float
            Radial coordinate (r > r_+).
        theta : float, optional
            Polar coordinate in radians (0 < theta < pi). Default is pi/2.

        Returns
        -------
        np.ndarray
            4x4 symmetric array representing g^{mu nu}.
        """
        self._validate_coordinates(r, theta)
        sigma_val = self.sigma(r, theta)
        delta_val = self.delta(r)
        A_val = self.A(r, theta)
        sin_theta = np.sin(theta)
        sin2_theta = sin_theta * sin_theta
        pi_val = sigma_val * delta_val

        g_inv = np.zeros((4, 4), dtype=np.float64)

        # g^{tt} = -A / (Sigma * Delta)
        g_inv[IDX_X0, IDX_X0] = -A_val / pi_val

        # g^{t phi} = g^{phi t} = -2 M a r / (Sigma * Delta)
        g_inv_t_phi = -(2.0 * self._mass * self._spin * r) / pi_val
        g_inv[IDX_X0, IDX_PHI] = g_inv_t_phi
        g_inv[IDX_PHI, IDX_X0] = g_inv_t_phi

        # g^{rr} = Delta / Sigma
        g_inv[IDX_R, IDX_R] = delta_val / sigma_val

        # g^{theta theta} = 1 / Sigma
        g_inv[IDX_THETA, IDX_THETA] = 1.0 / sigma_val

        # g^{phi phi} = (Delta - a^2 sin^2(theta)) / (Sigma * Delta * sin^2(theta))
        g_inv[IDX_PHI, IDX_PHI] = (delta_val - self._spin * self._spin * sin2_theta) / (pi_val * sin2_theta)

        return g_inv

    def dg_contra_dr(self, r: float, theta: float = np.pi / 2.0) -> np.ndarray:
        """Calculates partial_r g^{alpha beta} analytically.

        Parameters
        ----------
        r : float
            Radial coordinate (r > r_+).
        theta : float, optional
            Polar coordinate in radians (0 < theta < pi). Default is pi/2.

        Returns
        -------
        np.ndarray
            4x4 array containing partial_r g^{alpha beta}.
        """
        self._validate_coordinates(r, theta)
        sigma_val = self.sigma(r, theta)
        delta_val = self.delta(r)
        A_val = self.A(r, theta)
        pi_val = sigma_val * delta_val
        sin_theta = np.sin(theta)
        sin2_theta = sin_theta * sin_theta
        a2 = self._spin * self._spin

        # Component derivatives of building blocks with respect to r
        dsigma_dr = 2.0 * r
        ddelta_dr = 2.0 * (r - self._mass)
        dA_dr = 4.0 * r * (r * r + a2) - 2.0 * a2 * (r - self._mass) * sin2_theta
        dpi_dr = dsigma_dr * delta_val + sigma_val * ddelta_dr

        dg_dr = np.zeros((4, 4), dtype=np.float64)

        # partial_r g^{tt} = (A * dPi/dr - Pi * dA/dr) / Pi^2
        dg_dr[IDX_X0, IDX_X0] = (A_val * dpi_dr - pi_val * dA_dr) / (pi_val * pi_val)

        # partial_r g^{t phi} = 2 M a (r * dPi/dr - Pi) / Pi^2
        dg_t_phi_dr = (2.0 * self._mass * self._spin * (r * dpi_dr - pi_val)) / (pi_val * pi_val)
        dg_dr[IDX_X0, IDX_PHI] = dg_t_phi_dr
        dg_dr[IDX_PHI, IDX_X0] = dg_t_phi_dr

        # partial_r g^{rr} = (dDelta/dr * Sigma - Delta * dSigma/dr) / Sigma^2
        dg_dr[IDX_R, IDX_R] = (ddelta_dr * sigma_val - delta_val * dsigma_dr) / (sigma_val * sigma_val)

        # partial_r g^{theta theta} = -dSigma/dr / Sigma^2
        dg_dr[IDX_THETA, IDX_THETA] = -dsigma_dr / (sigma_val * sigma_val)

        # partial_r g^{phi phi} = -2 r / (Sigma^2 * sin^2(theta)) + a^2 * dPi/dr / Pi^2
        dg_dr[IDX_PHI, IDX_PHI] = (-2.0 * r) / (sigma_val * sigma_val * sin2_theta) + (a2 * dpi_dr) / (pi_val * pi_val)

        return dg_dr

    def dg_contra_dtheta(self, r: float, theta: float = np.pi / 2.0) -> np.ndarray:
        """Calculates partial_theta g^{alpha beta} analytically.

        Parameters
        ----------
        r : float
            Radial coordinate (r > r_+).
        theta : float, optional
            Polar coordinate in radians (0 < theta < pi). Default is pi/2.

        Returns
        -------
        np.ndarray
            4x4 array containing partial_theta g^{alpha beta}.
        """
        self._validate_coordinates(r, theta)
        sigma_val = self.sigma(r, theta)
        delta_val = self.delta(r)
        sin_theta = np.sin(theta)
        cos_theta = np.cos(theta)
        sin2_theta = sin_theta * sin_theta
        sin3_theta = sin2_theta * sin_theta
        a2 = self._spin * self._spin

        # dSigma/dtheta = -2 a^2 sin(theta) cos(theta)
        dsigma_dtheta = -2.0 * a2 * sin_theta * cos_theta
        sigma2_delta = sigma_val * sigma_val * delta_val

        dg_dtheta = np.zeros((4, 4), dtype=np.float64)

        # partial_theta g^{tt} = 2 M r (r^2 + a^2) * dSigma/dtheta / (Sigma^2 * Delta)
        dg_dtheta[IDX_X0, IDX_X0] = (2.0 * self._mass * r * (r * r + a2) * dsigma_dtheta) / sigma2_delta

        # partial_theta g^{t phi} = 2 M a r * dSigma/dtheta / (Sigma^2 * Delta)
        dg_t_phi_dtheta = (2.0 * self._mass * self._spin * r * dsigma_dtheta) / sigma2_delta
        dg_dtheta[IDX_X0, IDX_PHI] = dg_t_phi_dtheta
        dg_dtheta[IDX_PHI, IDX_X0] = dg_t_phi_dtheta

        # partial_theta g^{rr} = -Delta * dSigma/dtheta / Sigma^2
        dg_dtheta[IDX_R, IDX_R] = (-delta_val * dsigma_dtheta) / (sigma_val * sigma_val)

        # partial_theta g^{theta theta} = -dSigma/dtheta / Sigma^2
        dg_dtheta[IDX_THETA, IDX_THETA] = -dsigma_dtheta / (sigma_val * sigma_val)

        # partial_theta g^{phi phi} = -2 cos(theta) (r^2 + a^2 cos(2 theta)) / (Sigma^2 sin^3(theta))
        #                             + a^2 * dSigma/dtheta / (Sigma^2 * Delta)
        term1 = (-2.0 * cos_theta * (r * r + a2 * np.cos(2.0 * theta))) / (sigma_val * sigma_val * sin3_theta)
        term2 = (a2 * dsigma_dtheta) / sigma2_delta
        dg_dtheta[IDX_PHI, IDX_PHI] = term1 + term2

        return dg_dtheta
