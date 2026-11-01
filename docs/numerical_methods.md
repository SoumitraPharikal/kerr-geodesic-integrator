# Numerical Methods — Stage 1A

This document details the numerical methods, precision conventions, verification strategies, and tolerances implemented in Stage 1A of the `kerr-geodesics` framework.

---

## 1. Floating-Point Precision and Data Representation

- **Arithmetic Standard:** IEEE 754 standard double-precision floating-point format (`numpy.float64`).
- **Machine Precision:** $\epsilon_{\rm mach} = 2^{-52} \approx 2.2204 \times 10^{-16}$.
- **Array Architecture:** Metric tensors are returned as 2D NumPy arrays of shape `(4, 4)` and `dtype=np.float64`. Spatial coordinate derivatives are returned as 2D NumPy arrays of shape `(4, 4)` for a specified coordinate index or packed as a 3D NumPy array of shape `(4, 4, 4)`.

---

## 2. Finite-Difference Verification Strategy

To verify the exact analytical expressions for contravariant metric derivatives without relying on manual assertion, we implement an independent numerical verification suite using a 4th-order central finite-difference scheme.

### Fourth-Order Central Difference Formulation
For a sufficiently smooth scalar component $F(x) \equiv g^{\alpha\beta}(x)$:
$$\frac{\partial F}{\partial x} = \frac{-F(x + 2h) + 8F(x + h) - 8F(x - h) + F(x - 2h)}{12h} + \mathcal{O}(h^4)$$

### Optimal Step Size Selection
The total numerical error in a 4th-order finite difference is the sum of discretization truncation error and floating-point cancellation error:
$$E_{\rm total}(h) \approx C_1 h^4 + C_2 \frac{\epsilon_{\rm mach}}{h}$$

Minimizing $E_{\rm total}(h)$ with respect to $h$:
$$4 C_1 h^3 - C_2 \frac{\epsilon_{\rm mach}}{h^2} = 0 \implies h_{\rm opt} \sim \epsilon_{\rm mach}^{1/5} \approx (2.22 \times 10^{-16})^{0.2} \approx 7 \times 10^{-4}$$

We choose step size $h = 1.0 \times 10^{-4}$. For this step size, the theoretical truncation error is $\mathcal{O}(h^4) \sim 10^{-16}$, while roundoff error is $\epsilon_{\rm mach} / h \sim 2 \times 10^{-12}$.

### Domain Selection for Numerical Verification
To avoid coordinate and geometric singular points during finite differencing:
- Radial coordinates are sampled strictly in the exterior vacuum region away from the horizon: $r \in [2.5M, 50M]$ with buffer $2h < 0.5M$.
- Polar angles are sampled away from the coordinate poles: $\theta \in [0.1\pi, 0.9\pi]$ with buffer $2h < 0.1\pi$.

---

## 3. Test Tolerances and Rationale

| Verification Test | Mathematical Target | Evaluated Metric | Numerical Tolerance | Justification |
| :--- | :--- | :--- | :--- | :--- |
| **VAL-MET-01** | Metric Inversion | $\|g^{\mu\alpha} g_{\alpha\nu} - \delta^\mu_{\ \nu}\|_\infty$ | $\le 10^{-14}$ | For a diagonal metric, $g^{\mu\mu} g_{\mu\mu} = 1.0$ exactly up to roundoff error ($\approx 2.22 \times 10^{-16}$). A tolerance of $10^{-14}$ accommodates machine precision with safety margin. |
| **VAL-MET-02** | Contravariant Derivatives | $\frac{|\partial_\mu g^{\alpha\beta}_{\rm analytical} - \partial_\mu g^{\alpha\beta}_{\rm FD}|}{|\partial_\mu g^{\alpha\beta}_{\rm analytical}|}$ | $\le 10^{-7}$ | Fourth-order central differences with $h = 10^{-4}$ achieve relative accuracy better than $10^{-8}$ away from singular boundaries. $10^{-7}$ provides a robust pass/fail threshold. |
| **VAL-MET-02 (Sign)** | Derivative Sign | $\partial_r g^{00} > 0$ | Exact positive sign check | Regression test ensuring $-\frac{1}{2}\partial_r g^{00} p_0^2 < 0$ (attractive gravity). |

---

## 4. Current Implementation Scope and Deferred Features

### Currently Implemented (Stage 1A)
- Abstract spacetime metric interface (`SpacetimeMetric`).
- Analytical Schwarzschild metric tensor evaluation ($g_{\mu\nu}$ and $g^{\mu\nu}$).
- Exact non-zero contravariant metric derivatives ($\partial_r g^{00}, \partial_r g^{rr}, \partial_r g^{\theta\theta}, \partial_r g^{\phi\phi}, \partial_\theta g^{\phi\phi}$).
- Input validation: $M > 0$, $r > 2M$, and $\theta \in (0, \pi)$.

### Explicitly Deferred (Subsequent Stages)
- **Stage 1B:** Canonical Hamiltonian vector field evaluator ($\dot{x}^\mu = g^{\mu\nu}p_\nu, \dot{p}_\mu = -\frac{1}{2}\partial_\mu g^{\alpha\beta}p_\alpha p_\beta$).
- **Stage 1C:** Initial condition generators for incoming photons ($p_r = -\frac{E}{f}\sqrt{1 - f b^2/r^2}$).
- **Stage 1D:** Adaptive ODE integration with SciPy `DOP853`, directional event triggers, and horizon stopping surface ($r_{\rm cut} = 2M(1+\epsilon)$).
- **Stage 2:** Comprehensive physical validation (weak-field deflection series, critical impact parameter bisection, photon sphere Lyapunov exponent).
- **Stage 3:** Kerr metric implementation in Boyer–Lindquist coordinates, ergosphere detection, Carter constant tracking.
