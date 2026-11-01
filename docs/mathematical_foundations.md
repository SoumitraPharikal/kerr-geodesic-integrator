# Mathematical Foundations — Stage 1A

This document records the exact mathematical formulations and conventions implemented in the Schwarzschild metric core of the `kerr-geodesics` framework, consistent with Stage 0 v1.2.

---

## 1. Coordinate Convention and Dimensional Analysis

### A. Coordinate Ordering and Dimensions
We adopt the canonical coordinate basis:
$$x^\mu = (x^0, r, \theta, \phi), \quad \text{where } x^0 \equiv ct$$

In this convention, all spacetime coordinates with non-zero dimensions carry units of length:
$$[x^0] = [L], \quad [r] = [L], \quad [\theta] = 1, \quad [\phi] = 1$$

### B. Metric Line Element
The metric tensor $g_{\mu\nu}$ is defined via the invariant spacetime interval:
$$ds^2 = g_{\mu\nu} dx^\mu dx^\nu = -f(r)(dx^0)^2 + \frac{dr^2}{f(r)} + r^2 d\theta^2 + r^2 \sin^2\theta\, d\phi^2$$
where the lapse function is:
$$f(r) = 1 - \frac{2GM}{c^2 r}$$

Since $[ds] = [L]$, the tensor components have dimensions:
$$[g_{00}] = 1, \quad [g_{rr}] = 1, \quad [g_{\theta\theta}] = [L]^2, \quad [g_{\phi\phi}] = [L]^2$$
The contravariant (inverse) metric components have dimensions:
$$[g^{00}] = 1, \quad [g^{rr}] = 1, \quad [g^{\theta\theta}] = [L]^{-2}, \quad [g^{\phi\phi}] = [L]^{-2}$$

### C. Momenta and Physical Energy
The canonical conjugate momenta are defined by $p_\mu \equiv \frac{\partial S}{\partial x^\mu}$, where $[S] = [M_{\rm mass}][L]^2[T]^{-1}$:
$$[p_0] = \frac{[S]}{[x^0]} = [P_0], \quad [p_r] = \frac{[S]}{[r]} = [P_0], \quad [p_\theta] = [p_\phi] = [L][P_0]$$
where $P_0 \equiv \frac{E_0}{c}$ is the characteristic linear momentum.

For a photon with physical energy $E$, the canonical covariant momentum component conjugate to $x^0$ in SI units is:
$$p_0 = -\frac{E}{c}$$
In geometrized units where $c = 1$, energy and momentum are numerically identified: $p_0 = -E$.

### D. Affine Parameter Scaling
The geodesic Lagrangian is $\mathcal{L}_{\rm lag} = \frac{1}{2} g_{\mu\nu} \frac{dx^\mu}{d\lambda} \frac{dx^\nu}{d\lambda}$.
From $p_r = g_{rr} \frac{dr}{d\lambda}$, the dimension of the affine parameter $\lambda$ is:
$$[\lambda] = \frac{[L]}{[p_r]} = \frac{[L]}{[P_0]} = \frac{[T]}{[M_{\rm mass}]}$$

Defining the gravitational length and momentum scales:
$$\mathcal{L} \equiv \frac{GM}{c^2}, \quad P_0 \equiv \frac{E_0}{c}$$

The dimensionless affine parameter is:
$$\tilde{\lambda} \equiv \lambda \frac{P_0}{\mathcal{L}} = \lambda \frac{E_0 c}{GM}$$

---

## 2. Schwarzschild Metric in Geometrized Units

In geometrized units ($G = c = M = 1$ internally):
$$f(r) = 1 - \frac{2M}{r}$$

### A. Covariant Metric Tensor ($g_{\mu\nu}$)
$$g_{\mu\nu} = 
\begin{pmatrix}
-f(r) & 0 & 0 & 0 \\
0 & \frac{1}{f(r)} & 0 & 0 \\
0 & 0 & r^2 & 0 \\
0 & 0 & 0 & r^2\sin^2\theta
\end{pmatrix}$$

### B. Contravariant Metric Tensor ($g^{\mu\nu}$)
Because $g_{\mu\nu}$ is diagonal, the exact matrix inverse is obtained directly by inverting diagonal elements:
$$g^{\mu\nu} = 
\begin{pmatrix}
-\frac{1}{f(r)} & 0 & 0 & 0 \\
0 & f(r) & 0 & 0 \\
0 & 0 & \frac{1}{r^2} & 0 \\
0 & 0 & 0 & \frac{1}{r^2\sin^2\theta}
\end{pmatrix}$$

By definition, $g^{\mu\alpha} g_{\alpha\nu} = \delta^\mu_{\ \nu}$.

---

## 3. Exact Analytical Derivatives of the Inverse Metric

The canonical Hamiltonian equations of motion require spatial derivatives of the contravariant metric:
$$\frac{dp_\mu}{d\lambda} = -\frac{1}{2} \left(\frac{\partial g^{\alpha\beta}}{\partial x^\mu}\right) p_\alpha p_\beta$$

Because the metric is stationary ($\partial_0 g^{\alpha\beta} = 0$) and axisymmetric ($\partial_\phi g^{\alpha\beta} = 0$), the only non-vanishing derivatives are with respect to $r$ and $\theta$.

### Derivation of $\frac{\partial g^{00}}{\partial r}$
$$g^{00} = -\left(1 - \frac{2M}{r}\right)^{-1}$$
Applying the single-variable chain rule:
$$\frac{\partial g^{00}}{\partial r} = -(-1)\left(1 - \frac{2M}{r}\right)^{-2} \frac{d}{dr}\left(1 - \frac{2M}{r}\right) = +\frac{1}{f(r)^2} \left(+\frac{2M}{r^2}\right) = +\frac{2M}{r^2 f(r)^2}$$

### Complete Set of Non-Zero Contravariant Derivatives
$$\frac{\partial g^{00}}{\partial r} = +\frac{2M}{r^2 f(r)^2}$$
$$\frac{\partial g^{rr}}{\partial r} = \frac{d}{dr}\left(1 - \frac{2M}{r}\right) = +\frac{2M}{r^2}$$
$$\frac{\partial g^{\theta\theta}}{\partial r} = \frac{d}{dr}\left(r^{-2}\right) = -\frac{2}{r^3}$$
$$\frac{\partial g^{\phi\phi}}{\partial r} = \frac{\partial}{\partial r}\left(r^{-2}\csc^2\theta\right) = -\frac{2}{r^3\sin^2\theta}$$
$$\frac{\partial g^{\phi\phi}}{\partial \theta} = \frac{\partial}{\partial \theta}\left(r^{-2}\csc^2\theta\right) = -\frac{2\cos\theta}{r^2\sin^3\theta} = -\frac{2\cot\theta}{r^2\sin^2\theta}$$

All other derivatives $\frac{\partial g^{\alpha\beta}}{\partial x^\mu}$ are identically zero.

### Physical Consequence for the Radial Hamiltonian Equation
In the equatorial plane ($\theta = \pi/2, p_\theta = 0$), the radial momentum equation is:
$$\frac{dp_r}{d\lambda} = -\frac{1}{2} \left[ \left(\frac{\partial g^{00}}{\partial r}\right) p_0^2 + \left(\frac{\partial g^{rr}}{\partial r}\right) p_r^2 + \left(\frac{\partial g^{\phi\phi}}{\partial r}\right) p_\phi^2 \right]$$

Substituting $p_0 = -E$ and $p_\phi = L_z$:
$$\frac{dp_r}{d\lambda} = -\frac{1}{2} \left[ \left(+\frac{2M}{r^2 f(r)^2}\right) E^2 + \left(+\frac{2M}{r^2}\right) p_r^2 - \left(\frac{2}{r^3}\right) L_z^2 \right] = -\frac{M E^2}{r^2 f(r)^2} - \frac{M}{r^2} p_r^2 + \frac{L_z^2}{r^3}$$

The positive sign of $\partial_r g^{00}$ ensures that $-\frac{1}{2}(\partial_r g^{00}) p_0^2 = -\frac{M E^2}{r^2 f(r)^2} < 0$, which yields an attractive gravitational acceleration directed inward toward the black hole. A negative sign would erroneously generate a repulsive gravitational force.


---

## 4. Canonical Hamiltonian and Geodesic Vector Field (Stage 1B)

### A. The Canonical Hamiltonian
The Hamiltonian describing geodesic motion of a particle in curved spacetime is defined as:
$$\mathcal{H}(x, p) = \frac{1}{2} g^{\mu\nu}(x) p_\mu p_\nu$$
where $x^\mu = (x^0, r, \theta, \phi)$ are contravariant coordinates and $p_\mu = (p_0, p_r, p_\theta, p_\phi)$ are covariant canonical momenta conjugate to $x^\mu$.

### B. Eight-Dimensional State Ordering Convention
The state vector $y$ is ordered strictly as:
$$y = (x^0, r, \theta, \phi, p_0, p_r, p_\theta, p_\phi)^T \in \mathbb{R}^8$$
- Indices $0 \dots 3$: Contravariant spacetime coordinates $x^\mu$ with $x^0 = ct$.
- Indices $4 \dots 7$: Covariant canonical momenta $p_\mu$.

### C. The Canonical Equations of Motion
The continuous first-order Hamilton equations are:
$$\frac{dx^\mu}{d\lambda} = \frac{\partial \mathcal{H}}{\partial p_\mu} = g^{\mu\nu}(x) p_\nu$$
$$\frac{dp_\mu}{d\lambda} = -\frac{\partial \mathcal{H}}{\partial x^\mu} = -\frac{1}{2} \left(\frac{\partial g^{\alpha\beta}}{\partial x^\mu}\right) p_\alpha p_\beta$$
where $\lambda$ is the affine parameter.

### D. Conservation of $p_0$ and $p_\phi$ in Schwarzschild Spacetime
In Schwarzschild spacetime:
- **Stationarity:** The metric tensor does not depend on coordinate time $x^0$, i.e., $\partial_0 g^{\alpha\beta} \equiv 0$. Consequently:
  $$\frac{dp_0}{d\lambda} = -\frac{1}{2} \left(\partial_0 g^{\alpha\beta}\right) p_\alpha p_\beta = 0 \implies p_0 = \text{constant} = -E$$
  This yields conservation of energy.
- **Axisymmetry:** The metric tensor does not depend on azimuth $\phi$, i.e., $\partial_\phi g^{\alpha\beta} \equiv 0$. Consequently:
  $$\frac{dp_\phi}{d\lambda} = -\frac{1}{2} \left(\partial_\phi g^{\alpha\beta}\right) p_\alpha p_\beta = 0 \implies p_\phi = \text{constant} = L_z$$
  This yields conservation of the axial component of angular momentum.

### E. The Null-Geodesic Condition vs. General Hamiltonian Definition
- **General Hamiltonian Definition:** The function $\mathcal{H}(x, p) = \frac{1}{2} g^{\mu\nu} p_\mu p_\nu$ is physically well-defined for arbitrary state vectors $(x, p)$. For timelike particles with rest mass $\mu$, $\mathcal{H} = -\frac{1}{2}\mu^2 < 0$; for spacelike trajectories, $\mathcal{H} > 0$.
- **Null Constraint:** For photons (massless particles), trajectories must lie on the null sub-manifold:
  $$\mathcal{H}(x, p) = 0$$
The production Hamiltonian functions (`hamiltonian_value` and `hamiltonian_rhs`) evaluate $\mathcal{H}$ and $\dot{y}$ for arbitrary valid states without artificially imposing or assuming $\mathcal{H} = 0$. The condition $\mathcal{H} = 0$ is a physical constraint on the initial data and an invariant to be monitored numerically during integration.
