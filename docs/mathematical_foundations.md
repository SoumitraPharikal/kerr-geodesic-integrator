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


---

## 5. Schwarzschild Null-Geodesic Initial Conditions (Stage 1C)

### A. The Null Constraint and Initial Data Construction
For a photon (massless test particle), the trajectory in curved spacetime must be a null geodesic satisfying the Hamiltonian constraint:
$$\mathcal{H}(x, p) = \frac{1}{2} g^{\mu\nu}(x) p_\mu p_\nu = 0$$

In Schwarzschild spacetime with contravariant metric $g^{\mu\nu} = \operatorname{diag}(-f^{-1}, f, r^{-2}, r^{-2}\sin^{-2}\theta)$ where $f(r) = 1 - 2M/r > 0$ for $r > 2M$, the Hamiltonian takes the explicit form:
$$2\mathcal{H} = -\frac{p_0^2}{f(r)} + f(r) p_r^2 + \frac{p_\theta^2}{r^2} + \frac{p_\phi^2}{r^2 \sin^2\theta} = 0$$

Given the conserved energy $E = -p_0 > 0$, conserved axial angular momentum $L_z = p_\phi$, and polar conjugate momentum $p_\theta$, this equation determines the radial momentum $p_r$:
$$p_r^2 = \frac{E^2}{f(r)^2} - \frac{1}{f(r) r^2} \left( p_\theta^2 + \frac{L_z^2}{\sin^2\theta} \right)$$

### B. Inward and Outward Radial Branches
The radial momentum is obtained as:
$$p_r = s \sqrt{\frac{E^2}{f(r)^2} - \frac{1}{f(r) r^2} \left( p_\theta^2 + \frac{L_z^2}{\sin^2\theta} \right)}$$
where the branch sign $s \in \{-1, +1\}$ determines the initial radial velocity:
$$\frac{dr}{d\lambda} = g^{rr} p_r = f(r) p_r$$

Because the Schwarzschild lapse function satisfies $f(r) > 0$ strictly in the exterior domain ($r > 2M$), the sign of the contravariant radial velocity $\dot{r} = dr/d\lambda$ (and the contravariant momentum $p^r = g^{rr} p_r$) matches the sign of the covariant momentum $p_r$:
$$\operatorname{sgn}\left(\frac{dr}{d\lambda}\right) = \operatorname{sgn}(p^r) = \operatorname{sgn}(p_r) = s$$
- **Inward branch ($s = -1$):** $p_r \le 0 \implies \dot{r} \le 0$ (coordinate radius initially decreasing).
- **Outward branch ($s = +1$):** $p_r \ge 0 \implies \dot{r} \ge 0$ (coordinate radius initially increasing).

For purely radial null rays ($L_z = 0, p_\theta = 0$), $p_r = s \frac{E}{f(r)}$ yields a constant radial velocity:
$$\frac{dr}{d\lambda} = f(r) \left(s \frac{E}{f(r)}\right) = s E = \text{constant}$$
Integrating with respect to affine parameter yields the exact analytical solution:
$$r(\lambda) = r_0 + s E (\lambda - \lambda_0)$$
which serves as a rigorous, closed-form benchmark for numerical integration accuracy.

### C. Effective Potential and Classically Allowed Domain
Defining the effective potential barrier for null geodesics:
$$V_{\text{eff}}(r, \theta) \equiv \frac{f(r)}{r^2} \left( p_\theta^2 + \frac{L_z^2}{\sin^2\theta} \right) = \left(1 - \frac{2M}{r}\right) \frac{L^2}{r^2}$$
where $L^2 \equiv p_\theta^2 + L_z^2 / \sin^2\theta$ is the total squared angular momentum, the radicand can be expressed as:
$$R(r, \theta) \equiv \frac{E^2 - V_{\text{eff}}(r, \theta)}{f(r)^2}$$

Physical null geodesics can only exist in the classically allowed region where:
$$E^2 \ge V_{\text{eff}}(r, \theta) \iff R(r, \theta) \ge 0$$
If $E^2 < V_{\text{eff}}$, the radicand is strictly negative; no real null geodesic exists at this coordinate location with these conserved quantities, and the generator strictly raises a `ValueError`.

### D. Radial Turning Points
At a radial turning point $r = r_{\text{turn}}$ where $E^2 = V_{\text{eff}}(r_{\text{turn}}, \theta)$:
$$R(r_{\text{turn}}, \theta) = 0 \implies p_r = 0, \quad \frac{dr}{d\lambda} = 0$$
At this instant, the photon transitions between ingoing and outgoing motion. The inward ($s = -1$) and outward ($s = +1$) branches coincide ($s \cdot 0 = 0$), rendering the branch choice mathematically degenerate.

### E. Affine Momentum Rescaling Invariance
The canonical equations of motion for null geodesics and the Hamiltonian constraint $\mathcal{H}(x, p) = \frac{1}{2}g^{\mu\nu}p_\mu p_\nu = 0$ are homogeneous under arbitrary positive momentum rescalings $p_\mu \to \kappa p_\mu$ with $\kappa > 0$ (corresponding to an affine parameter reparametrization $\lambda \to \lambda / \kappa$). Under this transformation, $E \to \kappa E$, $L_z \to \kappa L_z$, $p_\theta \to \kappa p_\theta$, and both $E^2$ and $V_{\text{eff}}$ scale strictly as $\kappa^2$. Consequently, the turning-point condition $E^2 - V_{\text{eff}} = 0$ and the null constraint are algebraically scale-invariant.

### F. Scope and Limitations
The `schwarzschild_null_initial_state` generator is specifically formulated for Schwarzschild spacetime in standard coordinates. It does not construct Kerr initial conditions, which involve frame-dragging off-diagonal metric components ($g_{t\phi} \ne 0$) and require specifying the Carter constant $Q$ (Stage 2).

---

## 6. Geodesic Termination Events and Boundary Geometry (Stage 1E)

### A. Event Detection Formalism
During numerical integration of the geodesic vector field $\dot{y} = f(y)$, trajectory termination and geometric event monitoring are formulated as root-finding problems along the 1D integral curve $y(\lambda)$:
$$g(\lambda, y(\lambda)) = 0$$
where $g: \mathbb{R} \times \mathbb{R}^8 \to \mathbb{R}$ is a continuously differentiable scalar event function.

An event is characterized by:
1. **Terminal Flag (`terminal` $\in \{\text{True}, \text{False}\}$):** Whether locating a root $g(\lambda^*, y(\lambda^*)) = 0$ halts numerical integration.
2. **Directional Zero-Crossing Filter (`direction` $\in \{-1, 0, +1\}$):**
   - $\text{direction} = -1$: Detects roots where $\frac{dg}{d\lambda} < 0$ (transition from $g > 0$ to $g < 0$).
   - $\text{direction} = +1$: Detects roots where $\frac{dg}{d\lambda} > 0$ (transition from $g < 0$ to $g > 0$).
   - $\text{direction} = 0$: Detects all zero crossings regardless of derivative sign.

### B. Exterior Horizon-Cutoff Event
In standard Schwarzschild coordinates, the event horizon $r_H = 2M$ is a coordinate singularity where coordinate time $t \to \infty$ and radial conjugate momentum $p_r \to \infty$, even though the affine parameter $\lambda$ remains finite. Integrating an infalling geodesic directly into $r = 2M$ causes the numerical step-size controller to shrink toward zero, halting the solver with status `-1`.

To avoid numerical breakdown while capturing trajectories that terminate at the black hole, an exterior cutoff surface is defined at:
$$r_{\text{cut}} \equiv 2M(1 + \epsilon), \quad \epsilon > 0$$
where $\epsilon$ is a non-dimensional exterior buffer parameter (default $\epsilon = 10^{-3}$).

The scalar event function is:
$$g_{\text{horizon}}(y) = r - r_{\text{cut}} = y[1] - 2M(1 + \epsilon)$$
Configured with `direction = -1` (decreasing radius) and `terminal = True`.

**Exact Analytical Benchmark (Inward Radial Null Ray):**
For an inward radial null ray with $L_z = 0, p_\theta = 0$:
$$r(\lambda) = r_0 - E(\lambda - \lambda_0)$$
The root $g_{\text{horizon}} = 0$ is reached at the exact affine parameter:
$$\lambda_{\text{cut}} = \lambda_0 + \frac{r_0 - 2M(1 + \epsilon)}{E}$$

> [!IMPORTANT]
> **Scientific Interpretation:** Reaching $r = r_{\text{cut}}$ is strictly an exterior numerical domain cutoff in coordinate space; it does **not** represent crossing the physical event horizon into the black hole interior.

### C. Escape-Radius Event
To identify photons that propagate outward to the asymptotic spatial boundary, an exterior escape sphere of radius $r_{\text{esc}} > 2M$ is established.

The scalar event function is:
$$g_{\text{escape}}(y) = r - r_{\text{esc}} = y[1] - r_{\text{esc}}$$
Configured with `direction = +1` (increasing radius) and `terminal = True` (or `False` for flux monitoring).

**Exact Analytical Benchmark (Outward Radial Null Ray):**
For an outward radial null ray with $L_z = 0, p_\theta = 0$:
$$r(\lambda) = r_0 + E(\lambda - \lambda_0)$$
The root $g_{\text{escape}} = 0$ is reached at the exact affine parameter:
$$\lambda_{\text{esc}} = \lambda_0 + \frac{r_{\text{esc}} - r_0}{E}$$

> [!NOTE]
> **Scientific Interpretation:** Reaching a finite coordinate radius $r_{\text{esc}}$ confirms only that the trajectory has traversed the sphere $r = r_{\text{esc}}$. Crossing a finite coordinate sphere does not, by itself, establish asymptotic escape to spatial infinity. Depending on the geodesic and the sphere's position relative to the effective-potential barrier, a trajectory may still encounter a later turning point.

### D. Radial Turning-Point Event
A radial turning point occurs where the radial coordinate velocity vanishes:
$$\dot{r} \equiv \frac{dr}{d\lambda} = 0$$

To maintain mathematical generality and prepare for Kerr spacetime (Stage 2), the turning-point event evaluates the exact vector field component directly via `hamiltonian_rhs`:
$$g_{\text{turn}}(y) \equiv [\operatorname{hamiltonian\_rhs}(y, \text{metric})]_r = g^{rr}(x) p_r + g^{r\mu}(x) p_\mu$$
In Schwarzschild spacetime, $g^{r\mu} = 0$ for $\mu \ne r$, reducing to:
$$g_{\text{turn}}(y) = \left(1 - \frac{2M}{r}\right) p_r$$
Because $1 - 2M/r > 0$ everywhere outside the event horizon, $g_{\text{turn}}(y) = 0 \iff p_r = 0$.

### E. Physical Classification of Turning-Point Roots and Numerical Detection
Standard ODE event detection algorithms (including Brent's method in SciPy's `solve_ivp`) detect roots by identifying sign changes across discrete integration steps:
$$g(y_k) \cdot g(y_{k+1}) \le 0$$
Consequently, four physically and mathematically distinct cases must be distinguished:

1. **Ordinary Periapsis Reflection:**
   $$\dot{r} = 0, \quad \ddot{r} > 0$$
   The radial velocity $\dot{r}$ undergoes a genuine transversal sign change from negative (infalling) to positive (outgoing). This is an isolated first-order zero crossing and is detected accurately to root-finder tolerance ($\le 10^{-7}$).
   *Physical Example:* In equatorial Schwarzschild spacetime with $M=1, E=1, L_z=\sqrt{54}M$, an infalling photon starting at $r_0=10M$ reflects at $r_{\text{peri}} = 6.0M$ where $E^2 = V_{\text{eff}}(6.0M)$ and $\ddot{r} = -\frac{1}{2}dV_{\text{eff}}/dr > 0$.

2. **Ordinary Apoapsis Reflection:**
   $$\dot{r} = 0, \quad \ddot{r} < 0$$
   The radial velocity $\dot{r}$ undergoes a genuine transversal sign change from positive (outgoing) to negative (ingoing). This is an isolated first-order zero crossing detected with `direction = -1` or `direction = 0`. (Occurs for bound trajectories in spacetimes with effective-potential wells).

3. **Exact Circular Photon Orbit ($r = 3M$ in Schwarzschild):**
   $$\dot{r} = 0, \quad \ddot{r} = 0 \quad \text{for all } \lambda$$
   For an exact circular null orbit at the photon sphere $r = 3M$ (with $L_z = 3\sqrt{3}ME$), the radial velocity is identically zero everywhere along the trajectory: $\dot{r}(\lambda) \equiv 0$. This is a continuous manifold of roots, **not an isolated zero crossing**. If a trajectory starts on this orbit with $g(\lambda_0, y_0) = 0$, SciPy's bracket test ($g_k \cdot g_{k+1} \le 0$) flags a root on the very first step, halting integration immediately at $\lambda = \lambda_0$ when `terminal = True`. Standard sign-change event finders do not monitor or follow circular orbits.

4. **Critical Geodesic Asymptotic Approach:**
   $$\dot{r} \to 0 \quad \text{only as } \lambda \to \infty$$
   For critical trajectories with impact parameter $b = b_c \equiv 3\sqrt{3}M$ asymptotically spiraling into the photon sphere, $\dot{r} \to 0$ only as $\lambda \to \infty$. At every finite affine parameter $\lambda$, $\dot{r} < 0$ strictly. Because there is no isolated finite-parameter root and no sign change, standard bracketed root finders cannot detect or terminate an asymptotic approach. Trajectories near the photon sphere undergo numerical winding until numerical perturbations eventually trigger escape or plunge.

---

## 7. Schwarzschild Null-Geodesic Analytic Solutions and Physical Validation (Stage 1F)

This section documents the closed-form analytic solutions, conserved quantities, constraint preservation, and physical properties against which the Schwarzschild null-geodesic numerical integrator is verified.

### A. Radial Null Geodesics
Radial null geodesics are characterized by vanishing orbital angular momentum ($L_z = 0$) and vanishing polar momentum ($p_\theta = 0$), remaining confined to a constant angular direction ($\theta = \pi/2$ without loss of generality, $\phi = \text{const}$).

1. **Affine Parameter Evolution of Radius ($r(\lambda)$):**
   Along a null geodesic ($ds^2 = 0$), the canonical Hamiltonian constraint is:
   $$\mathcal{H} = \frac{1}{2} g^{\mu\nu} p_\mu p_\nu = \frac{1}{2}\left(-\frac{E^2}{f(r)} + f(r) p_r^2\right) = 0$$
   where $f(r) = 1 - 2M/r > 0$ in the exterior domain ($r > 2M$).
   This determines the radial conjugate momentum algebraically:
   $$p_r(\lambda) = \pm \frac{E}{f(r(\lambda))}$$
   where $+$ denotes outward propagation and $-$ denotes inward propagation.
   Substituting $p_r$ into the radial Hamiltonian velocity equation:
   $$\dot{r} \equiv \frac{dr}{d\lambda} = g^{rr} p_r = f(r)\left(\pm \frac{E}{f(r)}\right) = \pm E$$
   Integrating with respect to affine parameter $\lambda$ from initial state $(\lambda_0, r_0)$:
   $$r(\lambda) = r_0 \pm E(\lambda - \lambda_0)$$
   Thus, in Schwarzschild coordinates, coordinate radius $r$ is an **exact linear function of affine parameter $\lambda$** for both inward and outward radial null geodesics.

2. **Radial Conjugate Momentum ($p_r(\lambda)$):**
   Evaluating along the linear trajectory $r(\lambda)$:
   $$p_r(\lambda) = \pm \frac{E}{1 - \frac{2M}{r_0 \pm E(\lambda - \lambda_0)}}$$
   For outward rays, $p_r > 0$ monotonically decreases toward $E$ as $r \to \infty$. For inward rays, $p_r < 0$ and $|p_r| \to \infty$ as $r \to 2M$.

3. **Coordinate Time Evolution ($t(\lambda)$):**
   From the canonical velocity equation for coordinate time $x^0 = t$:
   $$\frac{dt}{d\lambda} = g^{00} p_0 = \left(-\frac{1}{f(r)}\right)(-E) = \frac{E}{f(r(\lambda))}$$
   Because $E > 0$ and $f(r) > 0$ outside the horizon, $\frac{dt}{d\lambda} > 0$ strictly, ensuring future-directed physical propagation.
   Relating coordinate time directly to coordinate radius:
   $$\frac{dt}{dr} = \frac{dt/d\lambda}{dr/d\lambda} = \frac{E / f(r)}{\pm E} = \pm \frac{1}{f(r)} = \pm \left(1 + \frac{2M}{r - 2M}\right)$$
   Integrating analytically yields the exact closed-form coordinate time differences:
   - **Outward Branch ($+$, $r \ge r_0 > 2M$):**
     $$t(r) - t(r_0) = \int_{r_0}^r \left(1 + \frac{2M}{r' - 2M}\right) dr' = (r - r_0) + 2M \ln\left(\frac{r - 2M}{r_0 - 2M}\right)$$
   - **Inward Branch ($-$, $2M < r \le r_0$):**
     $$t(r) - t(r_0) = -\int_{r_0}^r \left(1 + \frac{2M}{r' - 2M}\right) dr' = (r_0 - r) + 2M \ln\left(\frac{r_0 - 2M}{r - 2M}\right)$$
   In both cases, $t(r) - t(r_0) > 0$ for $\lambda > \lambda_0$. As $r \to 2M$ along an inward ray, $t \to +\infty$ logarithmically, capturing the infinite coordinate time delay at the event horizon.

### B. Conserved Quantities from Spacetime Symmetries
By Noether's theorem, every continuous isometry generated by a Killing vector field $\xi^\mu$ guarantees a conserved canonical conjugate momentum $C_\xi \equiv \xi^\mu p_\mu$ along geodesics ($\frac{dC_\xi}{d\lambda} = 0$).

1. **Stationarity (Time-Translation Symmetry):**
   Schwarzschild spacetime admits the timelike Killing vector $\xi_{(t)}^\mu = \delta^\mu_0$.
   $$\frac{dp_0}{d\lambda} = -\frac{1}{2} (\partial_0 g^{\alpha\beta}) p_\alpha p_\beta = 0 \implies p_0(\lambda) = -E = \text{constant}$$
   Physical photon energy $E$ at spatial infinity is strictly conserved along every trajectory.

2. **Axisymmetry (Rotational Symmetry about Polar Axis):**
   Schwarzschild spacetime admits the axial Killing vector $\xi_{(\phi)}^\mu = \delta^\mu_\phi$.
   $$\frac{dp_\phi}{d\lambda} = -\frac{1}{2} (\partial_\phi g^{\alpha\beta}) p_\alpha p_\beta = 0 \implies p_\phi(\lambda) = L_z = \text{constant}$$
   Axial angular momentum $L_z$ is strictly conserved along every trajectory.

3. **Spherical Symmetry and 3D Trajectories:**
   Full spherical symmetry ensures total orbital angular momentum vector $\mathbf{L}$ is conserved:
   $$L^2 = p_\theta^2 + \frac{p_\phi^2}{\sin^2\theta} = \text{constant}$$
   For planar (equatorial) geodesics, $\theta(\lambda) = \pi/2$ and $p_\theta(\lambda) = 0$ identically.
   For non-equatorial (inclined 3D) trajectories ($\theta_0 \ne \pi/2$ or $p_{\theta, 0} \ne 0$), $\theta$ and $p_\theta$ vary dynamically according to:
   $$\dot{\theta} = \frac{p_\theta}{r^2}, \quad \dot{p}_\theta = \frac{\cos\theta}{\sin^3\theta} \frac{L_z^2}{r^2}$$
   while $p_0 = -E$, $p_\phi = L_z$, and total $L^2$ remain conserved.

### C. Null Hamiltonian Constraint and Scale-Invariant Normalization
The canonical Hamiltonian for null geodesics is an exact constant of motion:
$$\mathcal{H}(x, p) = \frac{1}{2} g^{\mu\nu}(x) p_\mu p_\nu \equiv 0$$

In numerical integration with finite solver tolerance, truncation and roundoff errors yield a non-zero residual $\mathcal{H}_{\rm num} \ne 0$. Because $\mathcal{H}$ is quadratic in momenta, the absolute residual $|\mathcal{H}|$ scales as $E^2$.

To evaluate constraint satisfaction objectively across varying physical energy scales without dimensional distortion, we define the characteristic Hamiltonian scale:
$$\mathcal{S}_{\rm norm}(r, E) \equiv \frac{E^2}{f(r)}$$
- **Positivity and Boundedness:** In the exterior region $r > 2M$, $0 < f(r) < 1$. Thus, for any physical photon ($E > 0$):
  $$\mathcal{S}_{\rm norm}(r, E) > E^2 > 0$$
  The normalization scale is strictly bounded away from zero everywhere along exterior geodesics, eliminating division-by-zero or artificial amplification.
- **Normalized Residual:**
  $$\epsilon_{\mathcal{H}}(\lambda) \equiv \frac{|\mathcal{H}(x(\lambda), p(\lambda))|}{\mathcal{S}_{\rm norm}(r(\lambda), E)} = \frac{|\frac{1}{2} g^{\mu\nu} p_\mu p_\nu|}{E^2 / (1 - 2M/r)}$$
  $\epsilon_{\mathcal{H}}$ is scale-invariant and bounded by solver tolerance $\mathcal{O}(\text{rtol})$.

### D. Schwarzschild Photon Sphere at $r = 3M$
The Schwarzschild photon sphere represents the unstable circular orbit for massless particles.

1. **Effective Potential and Orbit Location:**
   In equatorial coordinates ($\theta = \pi/2, p_\theta = 0$), the radial equation of motion is:
   $$\dot{r}^2 = E^2 - V_{\rm eff}(r), \quad V_{\rm eff}(r) = \left(1 - \frac{2M}{r}\right) \frac{L_z^2}{r^2}$$
   A circular orbit requires simultaneously:
   - Zero radial velocity: $\dot{r} = 0 \implies E^2 = V_{\rm eff}(r)$
   - Zero radial acceleration: $\ddot{r} = -\frac{1}{2} V_{\rm eff}'(r) = 0$
   Differentiating $V_{\rm eff}(r)$:
   $$V_{\rm eff}'(r) = \frac{2M}{r^2}\frac{L_z^2}{r^2} - \frac{2 L_z^2}{r^3}\left(1 - \frac{2M}{r}\right) = \frac{2 L_z^2}{r^3}\left(\frac{3M}{r} - 1\right) = 0 \implies r_{\rm ph} = 3M$$

2. **Critical Impact Parameter:**
   Evaluating $V_{\rm eff}$ at $r = 3M$:
   $$E^2 = V_{\rm eff}(3M) = \left(1 - \frac{2}{3}\right) \frac{L^2}{9M^2} = \frac{L^2}{27 M^2} \implies b_{\rm crit} \equiv \frac{|L|}{E} = 3\sqrt{3}M \approx 5.1961524227 M$$
   For planar equatorial trajectories, $L = |L_z|$, with benchmark value $L_z = +3\sqrt{3}ME$.

3. **Phase-Space Fixed Point:**
   At $(r = 3M, p_r = 0, \theta = \pi/2, p_\theta = 0, p_0 = -E, p_\phi = 3\sqrt{3}ME)$, the radial Hamiltonian equations of motion satisfy:
   $$\dot{r} = g^{rr}(3M) p_r = \left(1 - \frac{2}{3}\right)(0) = 0$$
   $$\dot{p}_r = -\frac{1}{2}\left[\left(\frac{\partial g^{00}}{\partial r}\right) p_0^2 + \left(\frac{\partial g^{\phi\phi}}{\partial r}\right) p_\phi^2\right] = -\frac{1}{2}\left[\frac{2M}{(3M)^2 (1/3)^2} E^2 - \frac{2}{(3M)^3}(27 M^2 E^2)\right] = -\frac{1}{2}\left[\frac{2}{M}E^2 - \frac{2}{M}E^2\right] = 0$$
   Both phase-space radial coordinates $(r, p_r)$ have identically vanishing derivatives, confirming $(3M, 0)$ as an exact fixed point of the radial Hamiltonian vector field.

4. **Orbital Frequency:**
   $$\Omega \equiv \frac{d\phi}{dt} = \frac{\dot{\phi}}{\dot{t}} = \frac{g^{\phi\phi} p_\phi}{g^{00} p_0} = \frac{L_z / (3M)^2}{E / f(3M)} = \frac{3\sqrt{3}ME / 9M^2}{3E} = \frac{1}{3\sqrt{3}M}$$
   The coordinate period of revolution is $T = 2\pi / \Omega = 6\sqrt{3}\pi M \approx 32.65 M$, and the affine period is $\Delta \lambda = 2\pi / \dot{\phi} = 2\sqrt{3}\pi M \approx 10.88 M$.

5. **Orbital Instability ($V_{\rm eff}''(3M) < 0$):**
   The second radial derivative of the effective potential at $r = 3M$ is:
   $$V_{\rm eff}''(3M) = \left. \frac{d}{dr}\left[\frac{2 L_z^2}{r^3}\left(\frac{3M}{r} - 1\right)\right]\right|_{r=3M} = -\frac{2 L_z^2}{(3M)^4} = -\frac{2(27 M^2 E^2)}{81 M^4} = -\frac{2 E^2}{3 M^2} < 0$$
   Because $V_{\rm eff}''(3M) < 0$, the photon sphere is a local maximum of $V_{\rm eff}$, making the orbit dynamically unstable.
   Linearized radial perturbations satisfy:
   $$\delta \ddot{r} = -\frac{1}{2} V_{\rm eff}''(3M) \delta r = +\frac{E^2}{3 M^2} \delta r \implies \delta r(\lambda) = c_1 e^{+\gamma \lambda} + c_2 e^{-\gamma \lambda}, \quad \gamma = \frac{E}{\sqrt{3}M}$$
   Any infinitesimal numerical truncation or roundoff error ($\delta r \sim 10^{-15}$) grows exponentially with affine parameter $\lambda$, eventually causing the ray to either escape to infinity (if perturbed outward, $\delta r > 0$) or plunge into the black hole (if perturbed inward, $\delta r < 0$).

   **Distinction Between Initial-Value Problems and Threshold Semantics:**
   It is crucial to distinguish two distinct initial-value problems:
   - **Exact Circular Photon Orbit:** Initialized directly on the photon sphere ($r(0) = 3M, p_r(0) = 0$). In the ideal unperturbed problem, it remains bounded at $r = 3M$ for all affine time.
   - **Incoming Trajectory from Asymptotic Infinity:** Initialized far from the black hole ($r(0) \to \infty, p_r(0) < 0$) with impact parameter $b = L_z / E$:
     - *Scattering:* $|b| > b_{\rm crit} = 3\sqrt{3}M$. The photon encounters an outer radial turning point at $r_{\rm turn} > 3M$ and scatters back to infinity.
     - *Capture:* $|b| < b_{\rm crit}$. The photon encounters no turning point outside $r = 2M$ and plunges across the event horizon.
     - *Critical Separatrix (Equality Case):* $|b| = b_{\rm crit}$. In the ideal exact geodesic equations, the incoming trajectory asymptotically approaches the unstable circular photon orbit at $r = 3M$ as $\lambda \to \infty$ ($t \to \infty$), winding infinitely many times around the black hole as $r \to 3M^+$. It is therefore neither an ordinary scattering trajectory (it never reverses $p_r$) nor an ordinary capture trajectory (it never crosses the event horizon in finite affine time).

   Therefore, numerical propagation on the photon sphere over a finite affine interval validates the local accuracy of the vector field and step-size controller, but is not a test of global orbital stability.


---

## 8. Kerr Metric in Boyer–Lindquist Coordinates (Stage 2A)

This section documents the exact mathematical formulation, coordinate conventions, metric tensor components, inverse metric, determinant identity, and exact analytic derivatives for the Kerr spacetime describing a stationary, axisymmetric, rotating uncharged black hole in Boyer–Lindquist coordinates.

### A. Coordinate System and Dimensional Conventions
We adopt standard Boyer–Lindquist coordinates:
$$x^\mu = (x^0, r, \theta, \phi) = (t, r, \theta, \phi)$$
in geometrized units where $c = G = 1$, with metric signature $(-, +, +, +)$.

### B. Parameters and Physical Regimes
The spacetime geometry is determined completely by two global parameters:
1. **Black Hole Mass ($M > 0$):** Total ADM mass of the spacetime.
2. **Signed Spin Parameter ($a \in [-M, M]$):** Specific angular momentum $a \equiv J / M$.
   - $a > 0$: Prograde black hole rotation relative to increasing azimuthal coordinate $+d\phi / d\lambda$.
   - $a < 0$: Retrograde black hole rotation.
   - $a = 0$: Non-rotating Schwarzschild spacetime limit.
   - $|a| = M$: Extremal Kerr black hole.
   - $|a| > M$: Super-extremal regime (naked singularity), strictly rejected by parameter validation.

### C. Auxiliary Functions and Geometric Horizons
The Kerr metric components are expressed via standard auxiliary functions:
$$\Sigma(r, \theta) \equiv r^2 + a^2 \cos^2\theta$$
$$\Delta(r) \equiv r^2 - 2Mr + a^2 = (r - r_+)(r - r_-)$$
$$A(r, \theta) \equiv (r^2 + a^2)^2 - a^2 \Delta(r) \sin^2\theta$$
$$\Pi(r, \theta) \equiv \Sigma(r, \theta) \Delta(r)$$

The roots of $\Delta(r) = 0$ define the event horizons:
- **Outer Event Horizon:** $r_+ \equiv M + \sqrt{M^2 - a^2}$
- **Inner Cauchy Horizon:** $r_- \equiv M - \sqrt{M^2 - a^2}$

For an extremal black hole ($|a| = M$), the two horizons coalesce: $r_+ = r_- = M$.
For a non-rotating black hole ($a = 0$), $r_+ = 2M$ and $r_- = 0$.

**Useful Algebraic Identity:**
Expanding $A$ and subtracting $\Pi$:
$$A - \Pi = (r^2 + a^2)^2 - a^2 \Delta \sin^2\theta - (r^2 + a^2 \cos^2\theta)\Delta$$
Using $\cos^2\theta + \sin^2\theta = 1$:
$$A - \Pi = (r^2 + a^2)^2 - (r^2 + a^2)\Delta = (r^2 + a^2)[(r^2 + a^2) - (r^2 - 2Mr + a^2)] = 2Mr(r^2 + a^2)$$
This identity simplifies the analytic polar derivatives of the contravariant metric.

### D. Coordinate-Domain Validity and Coordinate Singularities
The Boyer–Lindquist coordinate chart is regular on the open exterior spatial domain:
$$\mathcal{D} = \{(r, \theta) \in \mathbb{R}^2 \mid r > r_+ \text{ and } 0 < \theta < \pi\}$$
- **Outer Horizon Singularity ($r \le r_+$):** At $r = r_+$, $\Delta(r_+) = 0$, causing $g_{rr} = \Sigma / \Delta \to \infty$ and $g^{tt}, g^{t\phi}, g^{\phi\phi} \to \infty$. This is a coordinate singularity of the Boyer–Lindquist slicing (the physical curvature invariant $R_{\alpha\beta\gamma\delta} R^{\alpha\beta\gamma\delta}$ remains finite at $r_+$). Points at or inside the horizon ($r \le r_+$) are outside the valid coordinate domain and are rejected.
- **Polar Axis Coordinate Singularity ($\theta = 0, \pi$):** On the rotation axis, $\sin\theta = 0$, causing azimuthal degeneracy. The coordinate domain is restricted to $0 < \theta < \pi$.
- **Ring Singularity ($r = 0, \theta = \pi/2$):** $\Sigma(0, \pi/2) = 0$ is the genuine physical curvature ring singularity, lying deep in the interior $r < r_+$.

### E. Covariant Metric Tensor ($g_{\mu\nu}$)
The invariant line element in Boyer–Lindquist coordinates is:
$$ds^2 = g_{tt} dt^2 + 2 g_{t\phi} dt d\phi + g_{rr} dr^2 + g_{\theta\theta} d\theta^2 + g_{\phi\phi} d\phi^2$$

The non-zero components of the symmetric covariant metric tensor $g_{\mu\nu}$ are:
$$g_{tt} = -\left(1 - \frac{2Mr}{\Sigma}\right)$$
$$g_{t\phi} = g_{\phi t} = -\frac{2Mar \sin^2\theta}{\Sigma}$$
$$g_{rr} = \frac{\Sigma}{\Delta}$$
$$g_{\theta\theta} = \Sigma$$
$$g_{\phi\phi} = \frac{A \sin^2\theta}{\Sigma} = \left(r^2 + a^2 + \frac{2Ma^2 r \sin^2\theta}{\Sigma}\right) \sin^2\theta$$

All other components vanish identically:
$$g_{tr} = g_{t\theta} = g_{r\theta} = g_{r\phi} = g_{\theta\phi} = 0$$

### F. Contravariant Inverse Metric Tensor ($g^{\mu\nu}$)
Because the metric tensor is block-diagonal (decoupling into a $2\times 2$ $(t, \phi)$ block and two $1\times 1$ diagonal blocks for $r$ and $\theta$), the exact analytical matrix inverse $g^{\mu\nu}$ satisfies $g^{\mu\alpha} g_{\alpha\nu} = \delta^\mu_{\ \nu}$.

Evaluating the $2\times 2$ block inverse:
$$\det \begin{pmatrix} g_{tt} & g_{t\phi} \\ g_{\phi t} & g_{\phi\phi} \end{pmatrix} = g_{tt} g_{\phi\phi} - g_{t\phi}^2 = -\Delta \sin^2\theta$$

The non-zero components of $g^{\mu\nu}$ are:
$$g^{tt} = \frac{g_{\phi\phi}}{-\Delta \sin^2\theta} = -\frac{A}{\Sigma \Delta}$$
$$g^{t\phi} = g^{\phi t} = -\frac{g_{t\phi}}{-\Delta \sin^2\theta} = -\frac{2Mar}{\Sigma \Delta}$$
$$g^{rr} = \frac{1}{g_{rr}} = \frac{\Delta}{\Sigma}$$
$$g^{\theta\theta} = \frac{1}{g_{\theta\theta}} = \frac{1}{\Sigma}$$
$$g^{\phi\phi} = \frac{g_{tt}}{-\Delta \sin^2\theta} = \frac{\Delta - a^2 \sin^2\theta}{\Sigma \Delta \sin^2\theta} = \frac{1}{\Sigma \sin^2\theta} - \frac{a^2}{\Sigma \Delta}$$

All other components vanish identically:
$$g^{tr} = g^{t\theta} = g^{r\theta} = g^{r\phi} = g^{\theta\phi} = 0$$

### G. Metric Determinant Identity
The exact 4D determinant of the metric tensor is:
$$\det(g_{\mu\nu}) = (g_{tt} g_{\phi\phi} - g_{t\phi}^2) g_{rr} g_{\theta\theta} = (-\Delta \sin^2\theta) \left(\frac{\Sigma}{\Delta}\right) \Sigma = -\Sigma^2 \sin^2\theta$$
This identity holds identically everywhere in the manifold and is independent of $\Delta$.

### H. Exact Coordinate Derivatives of the Inverse Metric
The canonical Hamiltonian equations of motion require spatial derivatives of the contravariant metric components:
$$\dot{p}_\mu = -\frac{1}{2}\left(\frac{\partial g^{\alpha\beta}}{\partial x^\mu}\right) p_\alpha p_\beta$$

Because Kerr spacetime is stationary ($\partial_t g^{\alpha\beta} = 0$) and axisymmetric ($\partial_\phi g^{\alpha\beta} = 0$), the only non-vanishing derivatives are with respect to $r$ and $\theta$.

#### 1. Radial Derivatives ($\partial_r g^{\alpha\beta}$)
First, compute the radial derivatives of the auxiliary functions:
$$\frac{\partial \Sigma}{\partial r} = 2r$$
$$\frac{\partial \Delta}{\partial r} = 2(r - M)$$
$$\frac{\partial A}{\partial r} = 4r(r^2 + a^2) - 2a^2(r - M)\sin^2\theta$$
$$\frac{\partial \Pi}{\partial r} = \frac{\partial(\Sigma\Delta)}{\partial r} = \left(\frac{\partial \Sigma}{\partial r}\right)\Delta + \Sigma\left(\frac{\partial \Delta}{\partial r}\right) = 2r\Delta + 2(r - M)\Sigma$$

Differentiating the contravariant metric components via the quotient rule:
$$\frac{\partial g^{tt}}{\partial r} = -\frac{\partial}{\partial r}\left(\frac{A}{\Pi}\right) = \frac{A \frac{\partial \Pi}{\partial r} - \ Pi \frac{\partial A}{\partial r}}{\Pi^2}$$
$$\frac{\partial g^{t\phi}}{\partial r} = \frac{\partial g^{\phi t}}{\partial r} = -2Ma \frac{\partial}{\partial r}\left(\frac{r}{\Pi}\right) = \frac{2Ma\left(r \frac{\partial \Pi}{\partial r} - \Pi\right)}{\Pi^2}$$
$$\frac{\partial g^{rr}}{\partial r} = \frac{\frac{\partial \Delta}{\partial r}\Sigma - \Delta \frac{\partial \Sigma}{\partial r}}{\Sigma^2} = \frac{2(r - M)\Sigma - 2r\Delta}{\Sigma^2}$$
$$\frac{\partial g^{\theta\theta}}{\partial r} = -\frac{1}{\Sigma^2}\frac{\partial \Sigma}{\partial r} = -\frac{2r}{\Sigma^2}$$
$$\frac{\partial g^{\phi\phi}}{\partial r} = -\frac{2r}{\Sigma^2 \sin^2\theta} + \frac{a^2 \frac{\partial \Pi}{\partial r}}{\Pi^2}$$

#### 2. Polar Angle Derivatives ($\partial_\theta g^{\alpha\beta}$)
First, compute polar derivatives of the auxiliary functions:
$$\frac{\partial \Sigma}{\partial \theta} = -2a^2 \sin\theta \cos\theta$$
$$\frac{\partial \Delta}{\partial \theta} = 0$$
$$\frac{\partial \Pi}{\partial \theta} = \Delta \frac{\partial \Sigma}{\partial \theta} = -2a^2 \Delta \sin\theta \cos\theta$$
$$\frac{\partial A}{\partial \theta} = -2a^2 \Delta \sin\theta \cos\theta = \frac{\partial \Pi}{\partial \theta}$$

Using the identity $A - \Pi = 2Mr(r^2 + a^2)$ derived in Section 8.C:
$$\frac{\partial g^{tt}}{\partial \theta} = -\frac{\frac{\partial A}{\partial \theta}\Pi - A \frac{\partial \Pi}{\partial \theta}}{\Pi^2} = \frac{(A - \Pi)\frac{\partial \Pi}{\partial \theta}}{\Pi^2} = \frac{2Mr(r^2 + a^2)\Delta \frac{\partial \Sigma}{\partial \theta}}{\Sigma^2 \Delta^2} = \frac{2Mr(r^2 + a^2)\frac{\partial \Sigma}{\partial \theta}}{\Sigma^2 \Delta}$$

$$\frac{\partial g^{t\phi}}{\partial \theta} = \frac{\partial g^{\phi t}}{\partial \theta} = -2Mar \left(-\frac{1}{\Pi^2}\frac{\partial \Pi}{\partial \theta}\right) = \frac{2Mar \Delta \frac{\partial \Sigma}{\partial \theta}}{\Sigma^2 \Delta^2} = \frac{2Mar \frac{\partial \Sigma}{\partial \theta}}{\Sigma^2 \Delta}$$

$$\frac{\partial g^{rr}}{\partial \theta} = \Delta \left(-\frac{1}{\Sigma^2}\frac{\partial \Sigma}{\partial \theta}\right) = -\frac{\Delta \frac{\partial \Sigma}{\partial \theta}}{\Sigma^2}$$

$$\frac{\partial g^{\theta\theta}}{\partial \theta} = -\frac{1}{\Sigma^2}\frac{\partial \Sigma}{\partial \theta}$$

For $g^{\phi\phi} = \frac{1}{\Sigma \sin^2\theta} - \frac{a^2}{\Pi}$:
$$\frac{\partial}{\partial \theta}\left(\frac{1}{\Sigma \sin^2\theta}\right) = -\frac{\frac{\partial \Sigma}{\partial \theta}\sin^2\theta + 2\Sigma \sin\theta \cos\theta}{\Sigma^2 \sin^4\theta} = -\frac{-2a^2 \sin^3\theta \cos\theta + 2(r^2 + a^2 \cos^2\theta)\sin\theta \cos\theta}{\Sigma^2 \sin^4\theta}$$
Factorizing the numerator:
$$-2a^2 \sin^2\theta \cos\theta + 2(r^2 + a^2 \cos^2\theta)\cos\theta = 2\cos\theta [r^2 + a^2(\cos^2\theta - \sin^2\theta)] = 2\cos\theta [r^2 + a^2 \cos(2\theta)]$$
Thus:
$$\frac{\partial}{\partial \theta}\left(\frac{1}{\Sigma \sin^2\theta}\right) = -\frac{2\cos\theta [r^2 + a^2 \cos(2\theta)]}{\Sigma^2 \sin^3\theta}$$
Adding the second term $-\frac{\partial}{\partial \theta}\left(\frac{a^2}{\Pi}\right) = \frac{a^2 \frac{\partial \Pi}{\partial \theta}}{\Pi^2} = \frac{a^2 \frac{\partial \Sigma}{\partial \theta}}{\Sigma^2 \Delta}$:
$$\frac{\partial g^{\phi\phi}}{\partial \theta} = -\frac{2\cos\theta [r^2 + a^2 \cos(2\theta)]}{\Sigma^2 \sin^3\theta} + \frac{a^2 \frac{\partial \Sigma}{\partial \theta}}{\Sigma^2 \Delta}$$

### I. Schwarzschild Limit ($a = 0$)
When $a = 0$:
- $\Sigma(r, \theta) = r^2$
- $\Delta(r) = r^2 - 2Mr = r^2 f(r)$
- $A(r, \theta) = r^4$
- $\Pi(r, \theta) = r^4 f(r)$
- $r_+ = 2M, r_- = 0$
- $g_{t\phi} = g^{\phi t} = 0$
- $g_{tt} = -f(r), g_{rr} = 1 / f(r), g_{\theta\theta} = r^2, g_{\phi\phi} = r^2 \sin^2\theta$
- $g^{tt} = -1 / f(r), g^{rr} = f(r), g^{\theta\theta} = 1 / r^2, g^{\phi\phi} = 1 / (r^2 \sin^2\theta)$
- $\det(g) = -r^4 \sin^2\theta$
- $\partial_\theta \Sigma = 0 \implies \partial_\theta g^{tt} = \partial_\theta g^{t\phi} = \partial_\theta g^{rr} = \partial_\theta g^{\theta\theta} = 0$
- $\partial_\theta g^{\phi\phi} = -\frac{2\cos\theta r^2}{r^4 \sin^3\theta} = -\frac{2\cot\theta}{r^2 \sin^2\theta}$

All covariant and contravariant components, determinants, and derivatives reduce identically to the Schwarzschild expressions in Section 2 and Section 3 to machine precision ($\le 10^{-14}$).

### J. Parity Transformation Under Spin Reversal ($a \to -a$)
Under the parity transformation $a \to -a$:
- $\Sigma(r, \theta; -a) = \Sigma(r, \theta; a)$ (even)
- $\Delta(r; -a) = \Delta(r; a)$ (even)
- $A(r, \theta; -a) = A(r, \theta; a)$ (even)
- Horizon radii: $r_\pm(-a) = r_\pm(a)$ (even)
- Diagonal covariant components: $g_{\mu\mu}(-a) = g_{\mu\mu}(a)$ (even)
- Diagonal contravariant components: $g^{\mu\mu}(-a) = g^{\mu\mu}(a)$ (even)
- Off-diagonal cross terms: $g_{t\phi}(-a) = -g_{t\phi}(a)$ (strictly odd)
- Off-diagonal inverse cross terms: $g^{t\phi}(-a) = -g^{t\phi}(a)$ (strictly odd)
- Coordinate derivatives of diagonals: $\partial_r g^{\mu\mu}(-a) = \partial_r g^{\mu\mu}(a)$, $\partial_\theta g^{\mu\mu}(-a) = \partial_\theta g^{\mu\mu}(a)$ (even)
- Coordinate derivatives of cross terms: $\partial_r g^{t\phi}(-a) = -\partial_r g^{t\phi}(a)$, $\partial_\theta g^{t\phi}(-a) = -\partial_\theta g^{t\phi}(a)$ (odd)

---

## 9. Carter Constant and Hamilton–Jacobi Separability in Kerr Spacetime

### A. Separation of the Hamilton–Jacobi Equation
In stationary, axisymmetric Kerr spacetime, the geodesic equations of motion for a test particle of rest mass $\mu$ ($\mu = 1$ for unit-mass timelike geodesics, $\mu = 0$ for null geodesics) are governed by the super-Hamiltonian:
$$\mathcal{H} = \frac{1}{2} g^{\mu\nu} p_\mu p_\nu = -\frac{1}{2} \mu^2$$

The corresponding Hamilton–Jacobi equation for the Jacobi action $S(x^\mu, \lambda)$ is:
$$\frac{\partial S}{\partial \lambda} + \frac{1}{2} g^{\mu\nu} \frac{\partial S}{\partial x^\mu} \frac{\partial S}{\partial x^\nu} = 0$$

Because $\mathcal{H}$ does not depend explicitly on affine parameter $\lambda$ or cyclic coordinates $t$ and $\phi$, the action separates via Carter's ansatz (Carter 1968):
$$S(t, r, \theta, \phi, \lambda) = \frac{1}{2} \mu^2 \lambda - E t + L_z \phi + S_r(r) + S_\theta(\theta)$$
where:
$$E = -p_t = -p_0 \quad (\text{conserved specific energy})$$
$$L_z = p_\phi \quad (\text{conserved axial angular momentum})$$
$$p_r = \frac{d S_r}{dr}, \quad p_\theta = \frac{d S_\theta}{d\theta}$$

Substituting the contravariant metric components into $g^{\mu\nu} p_\mu p_\nu = -\mu^2$ and multiplying through by $\Sigma = r^2 + a^2 \cos^2\theta$:
$$\Sigma g^{\mu\nu} p_\mu p_\nu = -\mu^2 \Sigma = -\mu^2 (r^2 + a^2 \cos^2\theta)$$

Expanding the metric contraction:
$$\Sigma \left[ g^{tt} E^2 - 2 g^{t\phi} E L_z + g^{\phi\phi} L_z^2 + g^{rr} p_r^2 + g^{\theta\theta} p_\theta^2 \right] = -\mu^2 (r^2 + a^2 \cos^2\theta)$$

Using the contravariant component identities:
$$\Sigma g^{rr} p_r^2 = \Delta p_r^2$$
$$\Sigma g^{\theta\theta} p_\theta^2 = p_\theta^2$$
and the $(t, \phi)$ sector algebraic identity:
$$\Sigma \left( g^{tt} E^2 - 2 g^{t\phi} E L_z + g^{\phi\phi} L_z^2 \right) = -\frac{\left[(r^2 + a^2)E - a L_z\right]^2}{\Delta} + \left( \frac{L_z}{\sin\theta} - a E \sin\theta \right)^2$$

Substituting these into the mass-shell equation yields:
$$-\frac{\left[(r^2 + a^2)E - a L_z\right]^2}{\Delta} + \Delta p_r^2 + p_\theta^2 + \left( \frac{L_z}{\sin\theta} - a E \sin\theta \right)^2 = -\mu^2 r^2 - a^2 \mu^2 \cos^2\theta$$

Rearranging so that all terms dependent exclusively on $\theta$ appear on the left, and all terms dependent exclusively on $r$ appear on the right:
$$p_\theta^2 + \left( \frac{L_z}{\sin\theta} - a E \sin\theta \right)^2 + a^2 \mu^2 \cos^2\theta = \frac{\left[(r^2 + a^2)E - a L_z\right]^2}{\Delta} - \Delta p_r^2 - \mu^2 r^2$$

Because the left-hand side is independent of $(r, p_r)$ and the right-hand side is independent of $(\theta, p_\theta)$, both sides must equal a constant of motion, denoted the polar separation constant $\mathcal{K}$:
$$\mathcal{K} \equiv p_\theta^2 + \left( \frac{L_z}{\sin\theta} - a E \sin\theta \right)^2 + a^2 \mu^2 \cos^2\theta$$
$$\mathcal{K} \equiv \frac{\left[(r^2 + a^2)E - a L_z\right]^2}{\Delta} - \Delta p_r^2 - \mu^2 r^2$$

### B. Carter Constant Definition ($\mathcal{Q}$)
In the Kerr Geodesic Integrator project convention, the Carter constant $\mathcal{Q}$ is defined by subtracting the square of the difference $(L_z - aE)$ from the separation constant $\mathcal{K}$:
$$\boxed{\mathcal{Q} \equiv \mathcal{K} - (L_z - aE)^2}$$

To show the algebraic equivalence with the polar angular form:
$$\left( \frac{L_z}{\sin\theta} - a E \sin\theta \right)^2 - (L_z - aE)^2 = \frac{L_z^2}{\sin^2\theta} - 2 a E L_z + a^2 E^2 \sin^2\theta - \left( L_z^2 - 2 a E L_z + a^2 E^2 \right)$$
$$-2 a E L_z \text{ cancels identically}, \text{ leaving:}$$
$$= L_z^2 \left( \frac{1}{\sin^2\theta} - 1 \right) - a^2 E^2 (1 - \sin^2\theta) = L_z^2 \frac{\cos^2\theta}{\sin^2\theta} - a^2 E^2 \cos^2\theta = \cos^2\theta \left[ \frac{L_z^2}{\sin^2\theta} - a^2 E^2 \right]$$

Adding the mass term $a^2 \mu^2 \cos^2\theta$:
$$\mathcal{Q} = p_\theta^2 + \cos^2\theta \left[ \frac{L_z^2}{\sin^2\theta} - a^2 E^2 \right] + a^2 \mu^2 \cos^2\theta = \boxed{p_\theta^2 + \cos^2\theta \left[ a^2(\mu^2 - E^2) + \frac{L_z^2}{\sin^2\theta} \right]}$$

Both mathematical definitions are algebraically identical and evaluate to the same value within floating-point roundoff ($\le 10^{-14}$).

### C. Equatorial Limit ($\theta = \pi/2, p_\theta = 0$)
For motion confined to the equatorial plane:
$$\theta = \frac{\pi}{2} \implies \cos\theta = 0, \quad \sin\theta = 1$$
$$p_\theta = 0$$

Evaluating the explicit expression for $\mathcal{Q}$:
$$\mathcal{Q} = 0^2 + 0^2 \cdot \left[ a^2(\mu^2 - E^2) + L_z^2 \right] = 0$$
Thus, $\mathcal{Q} \equiv 0$ identically for all equatorial trajectories, regardless of spin $a$, energy $E$, axial angular momentum $L_z$, or rest mass $\mu$.
In this limit, the separation constant evaluates directly to:
$$\mathcal{K}_{\rm equatorial} = (L_z - aE)^2$$

### D. Independent Radial Representation of $\mathcal{K}$ and $\mathcal{Q}$
From the right-hand side of the separated Hamilton–Jacobi equation, the separation constant is evaluated using strictly radial and Killing components:
$$\mathcal{K}_{\rm radial} = \frac{\left[(r^2 + a^2)E - a L_z\right]^2}{\Delta(r)} - \Delta(r) p_r^2 - \mu^2 r^2$$
where $\Delta(r) = (r - r_+)(r - r_-) = r^2 - 2Mr + a^2$.
The radial Carter constant is:
$$\mathcal{Q}_{\rm radial} = \mathcal{K}_{\rm radial} - (L_z - aE)^2$$
This provides a completely independent mathematical channel to evaluate $\mathcal{K}$ and $\mathcal{Q}$ without referencing $\theta$ or $p_\theta$. For any physical exterior state ($r > r_+$) satisfying the mass-shell constraint $\mathcal{H} = -\frac{1}{2}\mu^2$, $\mathcal{K}_{\rm radial}$ and $\mathcal{K}_{\rm polar}$ agree to within $\le 10^{-12}$.

### E. Schwarzschild Limit ($a = 0$)
When spin $a = 0$, spacetime becomes spherically symmetric:
$$\mathcal{Q}_{a=0} = p_\theta^2 + \cos^2\theta \left[ \frac{L_z^2}{\sin^2\theta} \right] = p_\theta^2 + L_z^2 \cot^2\theta$$

In Schwarzschild geometry, spherical symmetry yields conservation of the total 3D angular momentum vector $\mathbf{L}$:
$$L^2 = p_\theta^2 + \frac{p_\phi^2}{\sin^2\theta} = p_\theta^2 + \frac{L_z^2}{\sin^2\theta}$$

Subtracting the axial component $L_z^2$:
$$L^2 - L_z^2 = p_\theta^2 + L_z^2 \left( \frac{1}{\sin^2\theta} - 1 \right) = p_\theta^2 + L_z^2 \cot^2\theta = \mathcal{Q}_{a=0}$$

Physically, $\mathbf{L}^2 = L_x^2 + L_y^2 + L_z^2$, so:
$$\mathcal{Q}_{a=0} = L_x^2 + L_y^2$$
Thus, in the Schwarzschild limit, the Carter constant $\mathcal{Q}$ reduces to the squared magnitude of the transverse angular momentum vector orthogonal to the polar symmetry axis.

### F. Spin-Sign Parity ($a \to -a$)
Under spin reversal $a \to -a$ with fixed phase-space coordinates and momenta $(x, p)$:
- In the polar expression for $\mathcal{Q}$:
  $$\mathcal{Q} = p_\theta^2 + \cos^2\theta \left[ a^2(\mu^2 - E^2) + \frac{L_z^2}{\sin^2\theta} \right]$$
  the spin parameter $a$ enters exclusively as $a^2$.
  Consequently:
  $$\mathcal{Q}(-a) = \mathcal{Q}(a)$$
  The Carter constant $\mathcal{Q}$ is strictly even under spin reversal at fixed phase-space state.
- Conversely, the separation constant $\mathcal{K} = \mathcal{Q} + (L_z - aE)^2$ contains the cross-term $-2a E L_z$:
  $$\mathcal{K}(-a) = \mathcal{Q} + (L_z + aE)^2 \neq \mathcal{K}(a) \quad (\text{unless } a E L_z = 0)$$
- Along dynamically integrated trajectories:
  The orbital trajectory itself differs under $a \to -a$ at fixed $L_z$ due to the reversal of frame dragging (prograde motion becomes retrograde). Under the joint discrete parity reflection $(a, L_z, \phi) \to (-a, -L_z, -\phi)$, the canonical equations of motion and $\mathcal{Q}$ are jointly invariant.

---

## 8. Schwarzschild Physical Circular Orbits and Orbital Stability (Stage 3A)

### A. Geodesic Effective Potential
In standard Schwarzschild coordinates $x^\mu = (t, r, \theta, \phi)$ with $G = c = 1$, the line element in the exterior vacuum ($r > 2M$) is:
$$ds^2 = -f(r) dt^2 + f(r)^{-1} dr^2 + r^2 d\theta^2 + r^2 \sin^2\theta d\phi^2, \quad f(r) = 1 - \frac{2M}{r}$$

Restricting without loss of generality to the equatorial plane $\theta = \pi/2$ ($p_\theta = 0, \sin\theta = 1$), the super-Hamiltonian is:
$$2\mathcal{H} = g^{\mu\nu} p_\mu p_\nu = -\frac{E^2}{f(r)} + f(r) p_r^2 + \frac{L^2}{r^2} = -\mu^2$$
where $\mu$ is the rest mass ($\mu = 1$ for timelike geodesics, $\mu = 0$ for null geodesics), $E = -p_t$ is the conserved energy, and $L = p_\phi$ is the axial angular momentum.

Multiplying by $f(r)$ and using the canonical velocity relation $\dot{r} = dr/d\lambda = g^{rr} p_r = f(r) p_r$:
$$\dot{r}^2 + f(r) \left( \mu^2 + \frac{L^2}{r^2} \right) = E^2$$

We define the radial effective potential $V_{\rm eff}(r)$:
$$\dot{r}^2 + V_{\rm eff}(r) = E^2$$
where:
$$V_{\rm eff}(r) \equiv \left( 1 - \frac{2M}{r} \right) \left( \mu^2 + \frac{L^2}{r^2} \right) = \mu^2 - \frac{2M\mu^2}{r} + \frac{L^2}{r^2} - \frac{2M L^2}{r^3}$$

### B. Timelike Circular Geodesics ($\mu = 1$)
For timelike particles ($\mu = 1$), the effective potential is:
$$V_{\rm eff}(r) = 1 - \frac{2M}{r} + \frac{L^2}{r^2} - \frac{2M L^2}{r^3}$$

An exact circular orbit at radius $r$ requires:
1. Vanishing radial velocity: $\dot{r} = 0 \implies E^2 = V_{\rm eff}(r)$.
2. Vanishing radial acceleration: $\ddot{r} = -\frac{1}{2} V_{\rm eff}'(r) = 0 \implies V_{\rm eff}'(r) = 0$.

Computing the first radial derivative:
$$V_{\rm eff}'(r) = \frac{2M}{r^2} - \frac{2L^2}{r^3} + \frac{6ML^2}{r^4} = \frac{2}{r^2} \left[ M - \frac{L^2}{r} \left( 1 - \frac{3M}{r} \right) \right]$$

Setting $V_{\rm eff}'(r) = 0$:
$$M = \frac{L^2}{r} \left( 1 - \frac{3M}{r} \right) \implies L_c^2 = \frac{M r^2}{r - 3M} = \frac{Mr}{1 - 3M/r}$$

Because $L_c^2 > 0$ and $M > 0, r > 2M$, the existence of a real circular angular momentum requires:
$$r > 3M$$
Thus, timelike circular orbits exist if and only if $r > 3M$. The angular momentum is:
$$L_c = \pm \frac{\sqrt{Mr}}{\sqrt{1 - 3M/r}}$$

Substituting $L_c^2$ into $E_c^2 = V_{\rm eff}(r)$:
$$1 + \frac{L_c^2}{r^2} = 1 + \frac{M/r}{1 - 3M/r} = \frac{1 - 2M/r}{1 - 3M/r}$$
$$E_c^2 = \left( 1 - \frac{2M}{r} \right) \left( \frac{1 - 2M/r}{1 - 3M/r} \right) = \frac{(1 - 2M/r)^2}{1 - 3M/r}$$

Taking the positive square root ($E > 0$ for future-directed motion):
$$E_c = \frac{1 - 2M/r}{\sqrt{1 - 3M/r}}$$

The coordinate-time angular velocity is:
$$\Omega_\phi \equiv \frac{d\phi}{dt} = \frac{d\phi/d\tau}{dt/d\tau} = \frac{\dot{\phi}}{\dot{t}} = \frac{g^{\phi\phi} L_c}{-g^{tt} E_c} = \frac{f(r) L_c}{r^2 E_c}$$
Substituting $E_c$ and $L_c$:
$$\Omega_\phi = \frac{f(r) \frac{\sqrt{Mr}}{\sqrt{1 - 3M/r}}}{r^2 \frac{f(r)}{\sqrt{1 - 3M/r}}} = \frac{\sqrt{Mr}}{r^2} = \sqrt{\frac{M}{r^3}}$$
This reproduces Kepler's third law in Schwarzschild spacetime for all circular orbits.

### C. Null Circular Orbits (Photon Sphere at $r = 3M$)
For null geodesics ($\mu = 0$):
$$V_{\rm eff}(r) = \left( 1 - \frac{2M}{r} \right) \frac{L^2}{r^2} = L^2 \left( \frac{1}{r^2} - \frac{2M}{r^3} \right)$$
Setting $V_{\rm eff}'(r) = 0$:
$$V_{\rm eff}'(r) = L^2 \left( -\frac{2}{r^3} + \frac{6M}{r^4} \right) = -\frac{2L^2}{r^3} \left( 1 - \frac{3M}{r} \right) = 0$$
Since $L \neq 0$ and $r > 2M$:
$$r_{\rm ph} = 3M$$
At $r = 3M$, $f(3M) = 1/3$, and the null condition $\dot{r} = 0 \implies E^2 = V_{\rm eff}(3M)$ requires:
$$E^2 = \frac{1}{3} \frac{L^2}{9M^2} = \frac{L^2}{27M^2} \implies L_c = \pm 3\sqrt{3} M E$$
The critical impact parameter is:
$$b_{\rm crit} = \frac{|L_c|}{E} = 3\sqrt{3} M \approx 5.1961524227 M$$

The orbital rates are:
- Coordinate-time frequency: $\Omega_\phi = \frac{d\phi}{dt} = \frac{1}{3\sqrt{3}M} = \sqrt{\frac{M}{(3M)^3}}$.
- Affine-parameter angular rate: $\frac{d\phi}{d\lambda} = g^{\phi\phi} L_c = \frac{3\sqrt{3}ME}{9M^2} = \frac{E}{\sqrt{3}M}$.
- Affine-parameter coordinate-time rate: $\frac{dt}{d\lambda} = -g^{tt} E = \frac{E}{f(3M)} = 3E$.

### D. Radial Stability and the ISCO ($r_{\rm ISCO} = 6M$)
A circular orbit at $r_c$ subjected to a small radial perturbation $r(\tau) = r_c + \delta r(\tau)$ satisfies:
$$\delta \ddot{r} = -\frac{1}{2} V_{\rm eff}''(r_c) \delta r + \mathcal{O}(\delta r^2)$$

Computing the second radial derivative of $V_{\rm eff}(r)$:
$$V_{\rm eff}''(r) = -\frac{4M}{r^3} + \frac{6L^2}{r^4} - \frac{24ML^2}{r^5} = \frac{2}{r^3} \left[ -2M + \frac{3L^2}{r} \left( 1 - \frac{4M}{r} \right) \right]$$

Evaluating $V_{\rm eff}''(r)$ along the family of circular orbits by substituting $L^2 = L_c^2(r) = \frac{M r^2}{r - 3M}$:
$$V_{\rm eff}''(r) = \frac{2}{r^3} \left[ -2M + \frac{3Mr}{r - 3M} \left( \frac{r - 4M}{r} \right) \right]$$
$$= \frac{2M}{r^3} \left[ \frac{-2(r - 3M) + 3(r - 4M)}{r - 3M} \right] = \frac{2M(r - 6M)}{r^3(r - 3M)}$$

For all circular orbits in the physical domain $r > 3M$:
- The denominator $r^3 (r - 3M) > 0$.
- The sign of $V_{\rm eff}''(r)$ is strictly governed by $(r - 6M)$:
  1. **$r > 6M$:** $V_{\rm eff}''(r) > 0 \implies$ Potential minimum; **stable circular orbit** undergoing bounded radial epicyclic oscillations with frequency $\omega_r = \sqrt{\frac{1}{2} V_{\rm eff}''(r)}$.
  2. **$r = 6M$:** $V_{\rm eff}''(r) = 0 \implies$ Inflection point; **marginal stability (Innermost Stable Circular Orbit, ISCO)**.
3. **$3M < r < 6M$:** $V_{\rm eff}''(r) < 0 \implies$ Potential maximum; **unstable circular orbit**.

At the ISCO ($r = 6M$):
$$E_{\rm ISCO} = \frac{1 - 2/6}{\sqrt{1 - 3/6}} = \frac{2/3}{\sqrt{1/2}} = \frac{2\sqrt{2}}{3} \approx 0.94280904$$
Binding energy efficiency: $1 - E_{\rm ISCO} = 1 - \frac{2\sqrt{2}}{3} \approx 5.72\%$.
$$L_{\rm ISCO} = \frac{\sqrt{6}M}{\sqrt{1/2}} = 2\sqrt{3}M \approx 3.46410162 M$$

#### Leading-Order Variations at the ISCO: Cubic Potential vs. Quadratic Force
At fixed angular momentum $L = L_{\rm ISCO} = 2\sqrt{3}M$, the effective potential simplifies to:
$$V_{\rm eff}(r) = \left(1 - \frac{2M}{r}\right)\left(1 + \frac{12M^2}{r^2}\right) = 1 - \frac{2M}{r} + \frac{12M^2}{r^2} - \frac{24M^3}{r^3}$$
Its exact first derivative is:
$$V_{\rm eff}'(r) = \frac{2M}{r^4}(r - 6M)^2 \ge 0 \quad \text{for all } r > 2M$$
Hence $V_{\rm eff}'(6M) = 0$ and $V_{\rm eff}''(6M) = 0$, while $V_{\rm eff}'''(6M) = \frac{1}{324 M^3} > 0$.

1. **Cubic Potential Profile:**
   The Taylor series of $V_{\rm eff}(r)$ about $r = 6M$ with displacement $\Delta r = r - 6M$ has leading nonconstant variation:
   $$V_{\rm eff}(r) - V_{\rm eff}(6M) \approx \frac{1}{6} V_{\rm eff}'''(6M) (\Delta r)^3 = \frac{1}{1944 M^3} (r - 6M)^3 = \mathcal{O}((\Delta r)^3)$$
   The local effective potential variation is strictly **cubic** in radial displacement.

2. **Quadratic Inward Radial Acceleration (Force):**
   The radial equation of motion $\ddot{r} = -\frac{1}{2} V_{\rm eff}'(r)$ yields:
   $$\ddot{r} = -\frac{M}{r^4}(r - 6M)^2 \approx -\frac{1}{1296 M^3} (r - 6M)^2 = -\mathcal{O}((\Delta r)^2) \le 0$$
   The radial force is **quadratic** in radial displacement and strictly **non-positive (inward-directed)** everywhere. It is **not** a restoring force that would produce bounded epicyclic oscillations.

3. **Perturbation Dynamics from Constraint-Preserving Initial Data:**
   For a perturbed state with initial radial momentum $\delta p_r \neq 0$ at $r = 6M$, exact Hamiltonian constraint preservation requires:
   $$E_{\rm pert}^2 = E_{\rm ISCO}^2 + \left(1 - \frac{2M}{6M}\right)^2 (\delta p_r)^2 = \frac{8}{9} + \frac{4}{9} (\delta p_r)^2 > V_{\rm eff}(6M)$$
   - **Outward kick ($\delta p_r > 0$):** Initially $\dot{r}(0) > 0$. Because $\ddot{r} \le 0$ acts inward and $V_{\rm eff}(r)$ increases for $r > 6M$, the particle decelerates until reaching an outer turning point where $V_{\rm eff}(r_{\rm turn}) = E_{\rm pert}^2$:
     - For $\delta p_r = 10^{-3}$, the exact algebraic root is $r_{\rm turn} = 6.09678036 M$ (reached at $\tau_{\rm turn} \approx 204.31 M$).
     - For $\delta p_r = 10^{-4}$, the exact algebraic root is $r_{\rm turn} = 6.02059013 M$ (reached at $\tau_{\rm turn} \approx 433.41 M$).
     Leading-order cubic expansion approximates this as:
     $$r_{\rm turn} - 6M \approx \left(864 M^3 (\delta p_r)^2\right)^{1/3} = \mathcal{O}((\delta p_r)^{2/3})$$
     giving $0.09524 M$ for $10^{-3}$ and $0.02052 M$ for $10^{-4}$.
     At $r_{\rm turn}$, $\dot{r} = 0$ while $\ddot{r} < 0$. The particle turns around, falls back through $r = 6M$ with nonzero inward velocity $\dot{r} = -\frac{2}{3}\delta p_r < 0$, and subsequently plunges.
   - **Inward kick ($\delta p_r < 0$):** Initially $\dot{r}(0) < 0$. For all $r < 6M$, $V_{\rm eff}(r) < V_{\rm eff}(6M) < E_{\rm pert}^2$. No inner turning point exists, and the particle accelerates directly into the event horizon ($r \to 2M$).


---

## 9. Kerr Equatorial Circular Timelike Orbits and ISCO (Stage 3B)

### A. Equatorial Geometry and Hamiltonian Reduction
In Boyer–Lindquist coordinates $x^\mu = (t, r, \theta, \phi)$ with $G = c = 1$, the Kerr line element in the equatorial plane $\theta = \pi/2$ ($\cos\theta = 0, \sin\theta = 1, \rho^2 = r^2$) simplifies significantly:
$$ds^2 = -\left(1 - \frac{2M}{r}\right) dt^2 - \frac{4Ma}{r} dt\,d\phi + \frac{r^2}{\Delta} dr^2 + \left(r^2 + a^2 + \frac{2Ma^2}{r}\right) d\phi^2$$
where $\Delta(r) = r^2 - 2Mr + a^2$.

The non-zero components of the inverse metric $g^{\mu\nu}$ on the equatorial plane are:
$$g^{tt} = -\frac{(r^2 + a^2)^2 - a^2\Delta}{r^2\Delta} = -\frac{r^3 + a^2 r + 2Ma^2}{r\Delta}$$
$$g^{t\phi} = -\frac{2Ma}{r\Delta}$$
$$g^{\phi\phi} = \frac{\Delta - a^2}{r^2\Delta} = \frac{r - 2M}{r\Delta}$$
$$g^{rr} = \frac{\Delta}{r^2}$$
$$g^{\theta\theta} = \frac{1}{r^2}$$

For motion confined to the equatorial plane ($\theta = \pi/2, p_\theta = 0$), the super-Hamiltonian is:
$$2\mathcal{H} = g^{\mu\nu} p_\mu p_\nu = g^{tt} p_t^2 + 2g^{t\phi} p_t p_\phi + g^{\phi\phi} p_\phi^2 + g^{rr} p_r^2 = -\mu^2$$
Using the constants of motion $E = -p_t$ (conserved energy) and $L_z = p_\phi$ (conserved axial angular momentum), and defining rest mass $\mu = 1$ for timelike geodesics:
$$2\mathcal{H} = g^{tt} E^2 - 2g^{t\phi} E L_z + g^{\phi\phi} L_z^2 + \frac{\Delta}{r^2} p_r^2 = -1$$

Multiplying by $r^2 \Delta$ and noting that $\dot{r} = dr/d\tau = g^{rr} p_r = \frac{\Delta}{r^2} p_r$, so $p_r^2 = \frac{r^4}{\Delta^2} \dot{r}^2$:
$$r^4 \dot{r}^2 = [E(r^2 + a^2) - aL_z]^2 - \Delta [r^2 + (L_z - aE)^2] \equiv R(r)$$
where $R(r)$ is the Carter radial potential specialized to equatorial timelike motion ($\mathcal{Q} = 0, \mu = 1$).

### B. Circular Orbit Conditions
An equatorial circular timelike orbit at radius $r_c$ requires that the orbit remain at constant radius without radial velocity or acceleration:
1. Vanishing radial velocity: $\dot{r} = 0 \iff R(r_c) = 0$.
2. Vanishing radial acceleration: $\ddot{r} = 0 \iff R'(r_c) = 0$.

Alternatively, circular orbits correspond to extremizing the four-velocity components subject to the geodesic equation $\nabla_u u^\mu = 0$. In Boyer–Lindquist coordinates, the Euler–Lagrange equations for circular motion $\dot{r} = \ddot{r} = 0$ yield the angular velocity with respect to coordinate time:
$$\Omega_\phi \equiv \frac{d\phi}{dt} = \frac{\dot{\phi}}{\dot{t}}$$
From the geodesic equation $\Gamma^r_{\mu\nu} \dot{x}^\mu \dot{x}^\nu = 0$, with $\dot{\theta} = \dot{r} = 0$:
$$\Gamma^r_{tt} + 2\Gamma^r_{t\phi} \Omega_\phi + \Gamma^r_{\phi\phi} \Omega_\phi^2 = 0$$
Using the Christoffel symbols of the Kerr metric at $\theta = \pi/2$:
$$\Gamma^r_{tt} = \frac{M\Delta}{r^4}, \quad \Gamma^r_{t\phi} = -\frac{Ma\Delta}{r^4}, \quad \Gamma^r_{\phi\phi} = -\frac{\Delta(r^3 - Ma^2)}{r^4}$$
Dividing out the common factor $\Delta / r^4$:
$$M - 2Ma \Omega_\phi - (r^3 - Ma^2) \Omega_\phi^2 = 0$$
$$(r^3 - Ma^2) \Omega_\phi^2 + 2Ma \Omega_\phi - M = 0$$
This quadratic equation in $\Omega_\phi$ factors cleanly:
$$\left((r^{3/2} \pm a\sqrt{M}) \Omega_\phi \mp \sqrt{M}\right) \left((r^{3/2} \mp a\sqrt{M}) \Omega_\phi \pm \sqrt{M}\right) = 0$$
The physically valid solutions for prograde and retrograde orbital frequencies are:
$$\Omega_\phi = \frac{s\sqrt{M}}{r^{3/2} + sa\sqrt{M}}$$
where $s \in \{+1, -1\}$ denotes the coordinate orbital direction ($\operatorname{sgn}(d\phi/dt)$):
- $s = +1$: counter-clockwise orbital motion ($d\phi/dt > 0$).
- $s = -1$: clockwise orbital motion ($d\phi/dt < 0$).

Physical prograde vs. retrograde motion is defined relative to the black hole spin $a$:
- **Prograde:** $sa > 0$ (orbital angular momentum aligned with hole spin).
- **Retrograde:** $sa < 0$ (orbital angular momentum anti-aligned with hole spin).

### C. Conserved Specific Energy $E$ and Axial Angular Momentum $L_z$
The four-velocity $u^\mu = \dot{t} (1, 0, 0, \Omega_\phi)$ satisfies the timelike normalization $u^\mu u_\mu = -1$:
$$\dot{t}^2 \left( g_{tt} + 2g_{t\phi} \Omega_\phi + g_{\phi\phi} \Omega_\phi^2 \right) = -1$$
Evaluating the metric combination with $\Omega_\phi$:
$$g_{tt} + 2g_{t\phi} \Omega_\phi + g_{\phi\phi} \Omega_\phi^2 = -\frac{r^{3/2} - 3M\sqrt{r} + 2sa\sqrt{M}}{\sqrt{r}(r^{3/2} + sa\sqrt{M})}$$
Since $\dot{t} > 0$ for future-directed motion:
$$\dot{t} = \frac{r^{3/2} + sa\sqrt{M}}{r^{3/4}\sqrt{r^{3/2} - 3M\sqrt{r} + 2sa\sqrt{M}}}$$
The conserved energy $E = -u_t = -(g_{tt}\dot{t} + g_{t\phi}\dot{\phi}) = -\dot{t}(g_{tt} + g_{t\phi}\Omega_\phi)$ yields:
$$E = \frac{r^{3/2} - 2M\sqrt{r} + sa\sqrt{M}}{r^{3/4}\sqrt{r^{3/2} - 3M\sqrt{r} + 2sa\sqrt{M}}}$$
Similarly, the conserved axial angular momentum $L_z = u_\phi = g_{t\phi}\dot{t} + g_{\phi\phi}\dot{\phi} = \dot{t}(g_{t\phi} + g_{\phi\phi}\Omega_\phi)$ yields:
$$L_z = \frac{s\sqrt{M}(r^2 - 2sa\sqrt{Mr} + a^2)}{r^{3/4}\sqrt{r^{3/2} - 3M\sqrt{r} + 2sa\sqrt{M}}}$$

### D. Existence Domain: Equatorial Photon Orbit $r_{\rm ph}$
The denominator of $E$ and $L_z$ features the square root of:
$$D(r) \equiv r^{3/2} - 3M\sqrt{r} + 2sa\sqrt{M}$$
For a real, physical timelike circular orbit, we strictly require $D(r) > 0$. The boundary $D(r) = 0$ corresponds to the circular null orbit (photon orbit), where $E \to \infty$ and $L_z \to \infty$.

Setting $u = \sqrt{r/M}$, the equation $D(r) = 0$ becomes:
$$u^3 - 3u + 2\frac{sa}{M} = 0$$
Using the trigonometric identity $\cos(3\alpha) = 4\cos^3\alpha - 3\cos\alpha$, the substitution $u = 2\cos\alpha$ yields $\cos(3\alpha) = -sa/M$. The physical exterior root gives the equatorial photon orbit radius:
$$r_{\rm ph} = 2M \left[ 1 + \cos\left( \frac{2}{3} \arccos\left(-\frac{sa}{M}\right) \right) \right]$$
- For prograde motion ($sa > 0$): $r_{\rm ph}^{\rm pro} < 3M$. In the extremal limit $a \to M$, $r_{\rm ph}^{\rm pro} \to M$.
- For retrograde motion ($sa < 0$): $r_{\rm ph}^{\rm retro} > 3M$. In the extremal limit $a \to M$, $r_{\rm ph}^{\rm retro} \to 4M$.
- In the Schwarzschild limit ($a = 0$): $r_{\rm ph} = 2M[1 + \cos(2\pi/6)] = 2M(1 + 1/2) = 3M$.

Timelike circular orbits exist if and only if $r > r_{\rm ph}$.

### E. Marginal Stability and the ISCO
Physical radial stability requires that small perturbations away from circularity oscillate rather than diverge. In terms of the Carter radial potential $R(r)$:
- Circular orbit: $R(r_c) = 0$ and $\left(\frac{\partial R}{\partial r}\right)_{E, L_z}(r_c) = 0$.
- Stability condition: $\left(\frac{\partial^2 R}{\partial r^2}\right)_{E, L_z}(r_c) \le 0$, holding conserved specific energy $E$ and axial angular momentum $L_z$ fixed during differentiation.
  (Note the sign convention: $\dot{r}^2 = R(r)/r^4 \ge 0$, so $R(r) \le 0$ everywhere outside the orbit. A local potential well in the effective potential corresponds to a local maximum of $R(r)$, i.e. $R''(r_c) < 0$).
- Marginal stability (ISCO): $\left(\frac{\partial^2 R}{\partial r^2}\right)_{E, L_z}(r_{\rm ISCO}) = 0$.

Computing the partial radial derivatives of $R(r) = [E(r^2+a^2) - aL_z]^2 - \Delta(r)[r^2 + (L_z - aE)^2]$ holding $E$ and $L_z$ strictly constant:
$$\left(\frac{\partial R}{\partial r}\right)_{E, L_z} = 4 r E [E(r^2+a^2) - aL_z] - 2(r - M)[r^2 + (L_z - aE)^2] - 2r\Delta(r)$$
$$\left(\frac{\partial^2 R}{\partial r^2}\right)_{E, L_z} = 8(rE)^2 + 4E[E(r^2+a^2) - aL_z] - 2[r^2 + (L_z - aE)^2] - 8r(r - M) - 2\Delta(r)$$

Evaluating this second derivative along the circular-orbit family by substituting $E = E_c(r)$ and $L_z = L_c(r)$ yields:
$$\left(\frac{\partial^2 R}{\partial r^2}\right)_{E_c, L_c} = -\frac{2(r^2 - 2sa\sqrt{Mr} + a^2)}{r^{3/2} - 3M\sqrt{r} + 2sa\sqrt{M}} \left( r^2 - 6Mr + 8sa\sqrt{Mr} - 3a^2 \right)$$
Since $r^2 - 2sa\sqrt{Mr} + a^2 > 0$ and $r^{3/2} - 3M\sqrt{r} + 2sa\sqrt{M} > 0$ for all physical circular orbits outside the photon sphere ($r > r_{\rm ph}$), the marginal stability condition $\left(\frac{\partial^2 R}{\partial r^2}\right)_{E, L_z} = 0$ is governed identically by the vanishing of the bracketed term:
$$r^2 - 6Mr + 8sa\sqrt{Mr} - 3a^2 = 0$$
Dividing by $M^2$ and substituting $x = \sqrt{r/M}$:
$$x^4 - 6x^2 + 8\left(\frac{sa}{M}\right)x - 3\left(\frac{a}{M}\right)^2 = 0$$

Bardeen, Press, and Teukolsky (1972) derived the exact closed-form algebraic solution:
$$r_{\rm ISCO} = M \left( 3 + Z_2 \mp \sqrt{(3 - Z_1)(3 + Z_1 + 2Z_2)} \right)$$
where the minus sign applies to prograde orbits ($sa > 0$) and the plus sign to retrograde orbits ($sa < 0$), with:
$$Z_1 \equiv 1 + \left(1 - \frac{a^2}{M^2}\right)^{1/3} \left[ \left(1 + \frac{a}{M}\right)^{1/3} + \left(1 - \frac{a}{M}\right)^{1/3} \right]$$
$$Z_2 \equiv \sqrt{3\frac{a^2}{M^2} + Z_1^2}$$

Key limiting behaviors:
- **Schwarzschild limit ($a \to 0$):** $Z_1 = 1 + 1(1 + 1) = 3$, $Z_2 = \sqrt{0 + 9} = 3$.
  $$r_{\rm ISCO} = M(3 + 3 \mp \sqrt{0}) = 6M$$
- **Extremal prograde limit ($a \to +M, s = +1$):** $Z_1 = 1$, $Z_2 = 2$.
  $$r_{\rm ISCO}^{\rm pro} = M(3 + 2 - \sqrt{(2)(3 + 1 + 4)}) = M(5 - \sqrt{16}) = 1.0M = r_+$$
- **Extremal retrograde limit ($a \to +M, s = -1$):**
  $$r_{\rm ISCO}^{\rm retro} = M(3 + 2 + \sqrt{16}) = 9.0M$$

For any subextremal spin $0 < |a| < M$, the horizon, photon sphere, and ISCO form a strictly nested radial hierarchy:
$$r_- < r_+ < r_{\rm ph}^{\rm pro} < r_{\rm ISCO}^{\rm pro} < 6M < r_{\rm ISCO}^{\rm retro} < r_{\rm ph}^{\rm retro}$$
(More precisely: $r_+ < r_{\rm ph}^{\rm pro} < r_{\rm ISCO}^{\rm pro} < 6M < r_{\rm ISCO}^{\rm retro}$, while $r_+ < r_{\rm ph}^{\rm pro} < 3M < r_{\rm ph}^{\rm retro} < r_{\rm ISCO}^{\rm retro} \le 9M$).

### F. Exact Constraint-Preserving Perturbations
To test dynamical radial stability without introducing spurious numerical constraint violations, an initial radial momentum perturbation $p_r = \delta p_r \neq 0$ is injected at $r = r_c$.
To guarantee that the perturbed state lies strictly on the timelike mass shell $\mathcal{H} = -0.5$ ($\mu = 1$):
$$2\mathcal{H} = g^{tt} E^2 - 2g^{t\phi} E L_z + g^{\phi\phi} L_z^2 + g^{rr} (\delta p_r)^2 = -1$$
$$-g^{tt} E^2 + 2g^{t\phi} L_z E - \left( 1 + g^{\phi\phi} L_z^2 + g^{rr} (\delta p_r)^2 \right) = 0$$
This is a quadratic equation in $E$:
$$A E^2 - 2 B E + C = 0$$
with:
$$A = -g^{tt} > 0, \quad B = -g^{t\phi} L_z, \quad C = 1 + g^{\phi\phi} L_z^2 + g^{rr} (\delta p_r)^2$$
Solving for the physical future-directed root ($E > 0$):
$$E_{\rm pert} = \frac{B + \sqrt{B^2 + A C}}{A} = \frac{-g^{t\phi} L_z + \sqrt{(g^{t\phi} L_z)^2 - g^{tt} \left( 1 + g^{\phi\phi} L_z^2 + g^{rr} (\delta p_r)^2 \right)}}{-g^{tt}}$$
This formula is exact for any equatorial Kerr state, reducing in the limit $a \to 0$ ($g^{t\phi} = 0, g^{tt} = -1/f(r), g^{rr} = f(r)$) to the Stage 3A Schwarzschild expression:
$$E_{\rm pert} = \sqrt{E_c^2 + f(r)^2 (\delta p_r)^2}$$
By construction, $\mathcal{H}(y_{0, \rm pert}) = -0.5 \pm 5 \times 10^{-16}$.

### G. Radial Epicyclic Frequency ($\omega_r$ and $\Omega_r$)
Small radial perturbations $\delta r$ about a stable equatorial circular timelike orbit at radius $r_c > r_{\rm ISCO}$ execute harmonic libration:
$$\frac{d^2(\delta r)}{d\tau^2} + \omega_r^2 \delta r = 0 \quad (\text{proper time } \tau)$$
$$\frac{d^2(\delta r)}{dt^2} + \Omega_r^2 \delta r = 0 \quad (\text{Boyer--Lindquist coordinate time } t)$$

1. **Proper-Time Frequency $\omega_r$:**
   From the equatorial radial velocity equation $\dot{r}^2 = R(r)/r^4$, defining effective potential $\mathcal{V}(r) \equiv -\frac{R(r)}{2r^4}$ such that $\frac{1}{2}\dot{r}^2 + \mathcal{V}(r) = 0$:
   $$\ddot{r} = -\mathcal{V}'(r) = \frac{R'(r)}{2r^4} - \frac{2R(r)}{r^5}$$
   For a circular orbit $R(r_c) = 0$ and $R'(r_c) = 0$, so $\mathcal{V}''(r_c) = -\frac{1}{2r_c^4}\left(\frac{\partial^2 R}{\partial r^2}\right)_{E, L_z}$.
   Hence, the radial epicyclic frequency with respect to proper time $\tau$ is:
   $$\omega_r = \sqrt{-\frac{1}{2r_c^4} \left(\frac{\partial^2 R}{\partial r^2}\right)_{E, L_z}}$$

2. **Coordinate-Time Frequency $\Omega_r$:**
   In Boyer–Lindquist coordinate time $t$, using $d/d\tau = \dot{t} \, d/dt$ with $\dot{t} = u^t = -g^{tt}E_c + g^{t\phi}L_c$:
   $$\Omega_r = \frac{\omega_r}{\dot{t}} = \frac{1}{\dot{t}} \sqrt{-\frac{1}{2r_c^4} \left(\frac{\partial^2 R}{\partial r^2}\right)_{E, L_z}}$$
   Analytically, this evaluates to the classic expression (Aliev & Galtsov 1981; Kato 1990):
   $$\Omega_r^2 = \Omega_\phi^2 \left( 1 - \frac{6M}{r} + \frac{8sa\sqrt{M}}{r^{3/2}} - \frac{3a^2}{r^2} \right)$$
   where $\Omega_\phi = \frac{s\sqrt{M}}{r^{3/2} + sa\sqrt{M}}$ is the circular orbital angular frequency.
   At the ISCO, the polynomial bracket vanishes identically, so $\Omega_r(r_{\rm ISCO}) = 0$ and $\omega_r(r_{\rm ISCO}) = 0$.

### H. Near-Extremal Proper Radial Distance on Boyer–Lindquist Spatial Slices
The proper radial distance between the outer event horizon $r_+$ and the prograde ISCO $r_{\rm ISCO}^{\rm pro}$ evaluated along an equatorial spatial slice ($dt = d\theta = d\phi = 0$) in Boyer–Lindquist coordinates is:
$$\Delta\ell = \int_{r_+}^{r_{\rm ISCO}^{\rm pro}} \sqrt{g_{rr}}\,dr = \int_{r_+}^{r_{\rm ISCO}^{\rm pro}} \frac{r}{\sqrt{\Delta(r)}}\,dr = \int_{r_+}^{r_{\rm ISCO}^{\rm pro}} \frac{r}{\sqrt{(r - r_+)(r - r_-)}}\,dr$$

1. **Exact Closed-Form Antiderivative:**
   Setting $u = r - M$ and $b = \sqrt{M^2 - a^2}$, $\Delta(r) = u^2 - b^2$, so:
   $$\int \frac{r}{\sqrt{\Delta(r)}}\,dr = \int \frac{u + M}{\sqrt{u^2 - b^2}}\,du = \sqrt{\Delta(r)} + M \ln\left| r - M + \sqrt{\Delta(r)} \right| \equiv F(r)$$
   Evaluating between $r = r_+$ (where $\Delta(r_+) = 0$ and $r_+ - M = \sqrt{M^2 - a^2}$) and $r = r_{\rm ISCO}^{\rm pro}$:
   $$\Delta\ell = F(r_{\rm ISCO}) - F(r_+) = \sqrt{\Delta(r_{\rm ISCO})} + M \ln\left( \frac{r_{\rm ISCO} - M + \sqrt{\Delta(r_{\rm ISCO})}}{\sqrt{M^2 - a^2}} \right)$$
   This closed-form expression is exact for all subextremal Kerr spacetimes ($|a| < M$).

2. **Asymptotic Behavior as $a/M \to 1^-$:**
   Let $\epsilon \equiv \sqrt{1 - a^2/M^2}$. In the near-extremal limit $\epsilon \to 0^+$:
   - Outer horizon: $r_+ = M(1 + \epsilon)$
   - Inner horizon: $r_- = M(1 - \epsilon)$
   - Horizon separation: $r_+ - r_- = 2M\epsilon \approx 2\sqrt{2}M(1 - a/M)^{1/2}$
   - Prograde ISCO: $r_{\rm ISCO}^{\rm pro} \approx M(1 + (2\epsilon^2)^{1/3}) = M(1 + (4(1 - a/M))^{1/3})$
   - Coordinate separation: $r_{\rm ISCO}^{\rm pro} - r_+ \approx M(2\epsilon^2)^{1/3} \to 0$
   - Radicand at ISCO: $\Delta(r_{\rm ISCO}) \approx M^2 (2\epsilon^2)^{2/3}$, so $\sqrt{\Delta(r_{\rm ISCO})} \approx M (2\epsilon^2)^{1/3} \to 0$
   - Argument of the logarithm:
     $$\frac{r_{\rm ISCO} - M + \sqrt{\Delta(r_{\rm ISCO})}}{\sqrt{M^2 - a^2}} \approx \frac{2 M (2\epsilon^2)^{1/3}}{M\epsilon} = 2^{4/3} \epsilon^{-1/3} = \frac{2^{4/3}}{(1 - a^2/M^2)^{1/6}}$$
   Consequently, the proper distance exhibits a logarithmic divergence in the extremal limit:
   $$\Delta\ell \sim M \left[ \frac{4}{3}\ln 2 + \frac{1}{6}\ln\left(\frac{1}{1 - a^2/M^2}\right) \right] \sim \frac{M}{6}\ln\left(\frac{1}{2(1 - a/M)}\right) + \frac{4}{3}M\ln 2 \to +\infty$$

3. **Slicing-Dependence:**
   This logarithmic divergence is a geometric property of the Boyer–Lindquist $t = \mathrm{constant}$ spatial foliation, where spatial distance stretches into an infinite throat (the NHEK throat) as $a \to M$. In general relativity, spatial distance between two surfaces is foliation-dependent and does not represent a unique, slicing-independent invariant spacetime distance.

## 10. Stage 3C: Kerr Equatorial Circular Photon Orbits and Critical Impact Parameters

### A. Null Radial Potential and Equatorial Geometry
For null geodesics ($\mu = 0$) confined to the equatorial plane ($\theta = \pi/2$, $p_\theta = 0$), the Carter constant vanishes identically:
$$\mathcal{Q} = 0, \quad \mathcal{K} = (L_z - aE)^2$$
The separated radial motion is governed by the Carter radial potential $R(r)$ via:
$$\Sigma^2 \left(\frac{dr}{d\lambda}\right)^2 = R(r)$$
where for $\theta = \pi/2$, $\Sigma = r^2$. For null trajectories ($\mu = 0$), the radial potential simplifies to:
$$R(r) = P(r)^2 - \Delta(r)(L_z - aE)^2$$
with:
$$P(r) \equiv E(r^2 + a^2) - a L_z, \quad \Delta(r) \equiv r^2 - 2Mr + a^2$$
Defining the impact parameter $b \equiv L_z / E$, the radial potential scales quadratically with photon energy $E$:
$$R(r) = E^2 \left[ (r^2 + a^2 - ab)^2 - \Delta(r)(b - a)^2 \right]$$

### B. Circularity Conditions and Analytic Orbit Radii
Circular null geodesics require simultaneously vanishing radial velocity and radial acceleration:
$$R(r_{\rm ph}) = 0 \quad \text{and} \quad R'(r_{\rm ph}) = \left(\frac{\partial R}{\partial r}\right)_{E, L_z}\Bigg|_{r_{\rm ph}} = 0$$

1. **Equatorial Photon Orbit Radius Polynomial:**
   Eliminating the impact parameter $b$ between $R(r) = 0$ and $R'(r) = 0$ yields the fundamental photon orbit polynomial:
   $$r_{\rm ph}^2 - 3 M r_{\rm ph} + 2 s a \sqrt{M r_{\rm ph}} = 0$$
   where $s = +1$ denotes prograde orbits (co-rotating with the black hole) and $s = -1$ denotes retrograde orbits (counter-rotating).

2. **Exact Closed-Form Solution:**
   Using the trigonometric cubic solution (Bardeen, Press, & Teukolsky 1972):
   $$r_{\rm ph} = 2 M \left[ 1 + \cos\left( \frac{2}{3} \arccos\left( -\frac{s a}{M} \right) \right) \right]$$
   For any subextremal spin $|a| < M$, the roots satisfy the strict physical bounds:
   $$r_+ < r_{\rm ph}^{\rm pro} \le 3M \le r_{\rm ph}^{\rm retro} < 4M$$

### C. Critical Signed Impact Parameter
For incoming equatorial null geodesics originating from asymptotic infinity, the critical signed impact parameter $b_{\rm ph} = L_z / E$ defines the phase-space threshold between capture by the black hole and scattering back to infinity.

1. **Standard Expression and Removable Singularity:**
   Directly solving $R(r_{\rm ph}) = 0$ or $R'(r_{\rm ph}) = 0$ gives:
   $$b_{\rm ph} = \frac{r_{\rm ph}^2(r_{\rm ph} - 3M) + a^2(r_{\rm ph} + M)}{a(M - r_{\rm ph})}$$
   In the Schwarzschild limit $a \to 0$, $r_{\rm ph} \to 3M$, creating a $0/0$ indeterminate form that suffers catastrophic numerical cancellation as $a \to 0$.

2. **Numerically Stable Formulation and Exact-Extremal Limit:**
   Using the defining identity of the photon orbit polynomial $r_{\rm ph}(r_{\rm ph} - 3M) = -2 s a \sqrt{M r_{\rm ph}}$, we divide numerator and denominator by $a$:
   $$b_{\rm ph} = \frac{-2 s r_{\rm ph} \sqrt{M r_{\rm ph}} + a(r_{\rm ph} + M)}{M - r_{\rm ph}} = \frac{2 s r_{\rm ph} \sqrt{M r_{\rm ph}} - a(r_{\rm ph} + M)}{r_{\rm ph} - M}$$
   This formulation is mathematically identical, evaluated in $\mathcal{O}(1)$ operations, and avoids catastrophic cancellation across the subextremal interior $a/M \in (-1, 1)$.

   *Exact-Extremal Boundary Behavior ($|a| = M$):*
   At exact extremality, the prograde photon orbit coincides with the event horizon: $r_{\rm ph} = r_+ = M$. Substituting $r_{\rm ph} = M$ into this expression causes both numerator and denominator to vanish simultaneously ($0/0$ form):
   $$\lim_{r_{\rm ph} \to M} \left[2 s r_{\rm ph} \sqrt{M r_{\rm ph}} - a(r_{\rm ph} + M)\right] = 2 s M^2 - 2 a M = 2M(sM - a) = 0 \quad (\text{since } s \cdot a > 0 \text{ for prograde})$$
   $$\lim_{r_{\rm ph} \to M} (r_{\rm ph} - M) = 0$$
   Consequently, the closed-form expression cannot be evaluated by direct floating-point division at $r_{\rm ph} = M$. The exact mathematical limit obtained from $C(M) = 0$ and $C'(M) = 0$ yields:
   $$\lim_{a \to \pm M} b_{\rm ph}^{\rm pro} = 2a = \pm 2M$$
   For retrograde orbits at exact extremality, $r_{\rm ph} = 4M$, so the denominator $r_{\rm ph} - M = 3M \ne 0$ remains strictly positive and regular:
   $$\lim_{a \to \pm M} b_{\rm ph}^{\rm retro} = -7a = \mp 7M$$
   The codebase explicitly implements these exact-extremal limits as special branches, avoiding $0/0$ division and runtime warnings. In numerical trajectory integration, because the Boyer-Lindquist coordinate singularity at $r_+$ requires an exterior cutoff $r_{\rm cut} = r_+(1 + \epsilon) > r_{\rm ph}$, incoming prograde critical trajectories terminate at $r_{\rm cut}$ and are faithfully classified as `CRITICAL` with numerical outcome `HORIZON_CUTOFF`.

### D. Coordinate Angular Frequency ($\Omega_{\rm ph}$)
The orbital coordinate angular frequency of the circular null geodesic is:
$$\Omega_{\rm ph} \equiv \frac{d\phi}{dt} = \frac{g^{t\phi} p_t + g^{\phi\phi} p_\phi}{g^{tt} p_t + g^{t\phi} p_\phi}\Bigg|_{r_{\rm ph}} = \frac{s\sqrt{M}}{r_{\rm ph}^{3/2} + sa\sqrt{M}}$$
The orbital period with respect to coordinate time is $T_t = 2\pi / |\Omega_{\rm ph}|$.
Along an affine-parameterized geodesic, $dt / d\lambda = -g^{tt} E + g^{t\phi} L_z$, which relates the coordinate period to the affine period $\Delta\lambda_{\rm orb} = T_t / (dt/d\lambda)$.

### E. Schwarzschild Limit and Parity Symmetry
1. **Continuous Schwarzschild Reduction ($a \to 0$):**
   In the limit $a \to 0$:
   $$\lim_{a \to 0} r_{\rm ph} = 2M\left[1 + \cos(2\pi/3)\right] = 3M$$
   $$\lim_{a \to 0} b_{\rm ph} = \frac{2 s (3M) \sqrt{3M^2}}{3M - M} = s 3\sqrt{3}M$$
   $$\lim_{a \to 0} \Omega_{\rm ph} = \frac{s\sqrt{M}}{(3M)^{3/2}} = \frac{s}{3\sqrt{3}M}$$
   which matches the Schwarzschild photon sphere $r = 3M$ with impact parameter $b = \pm 3\sqrt{3}M$.

2. **Discrete Spin-Reversal Parity:**
   Under simultaneous reversal of spin sign and orientation flag $(a, s) \to (-a, -s)$:
   - The product $s a$ is strictly invariant: $(-s)(-a) = sa$.
   - $r_{\rm ph}(-a, -s) = r_{\rm ph}(a, s)$.
   - $b_{\rm ph}(-a, -s) = -b_{\rm ph}(a, s)$.
   - $\Omega_{\rm ph}(-a, -s) = -\Omega_{\rm ph}(a, s)$.
   This guarantees complete consistency regardless of whether spin is parameterized as signed or orientation is selected via prograde/retrograde flags.

### F. Physical Instability of Circular Photon Orbits
The stability of circular orbits is determined by the sign of the radial effective potential curvature. With $\frac{1}{2}\left(\frac{dr}{d\lambda}\right)^2 + V_{\rm eff}(r) = 0$, where $V_{\rm eff}(r) \equiv -\frac{R(r)}{2r^4}$:
$$V_{\rm eff}''(r_{\rm ph}) = -\frac{R''(r_{\rm ph})}{2r_{\rm ph}^4}$$
Evaluating the second derivative of the radial potential holding the conserved constants of motion $(E, L_z)$ strictly fixed (with equatorial Carter constant $\mathcal{Q} = 0$):
$$R''(r) = \left(\frac{\partial^2 R}{\partial r^2}\right)_{E, L_z} = \frac{\partial^2}{\partial r^2}\left[ P^2 - \Delta(L_z - aE)^2 \right] = 8(rE)^2 + 4EP - 2(L_z - aE)^2$$
At $r = r_{\rm ph}$, substituting $L_z = b_{\rm ph}E$:
$$R''(r_{\rm ph}) = 8 r_{\rm ph}^2 E^2 + 4 E^2 [r_{\rm ph}^2 + a^2 - a b_{\rm ph}] - 2 E^2 (b_{\rm ph} - a)^2 > 0$$
Since $R''(r_{\rm ph}) > 0$ strictly for all subextremal spins:
$$V_{\rm eff}''(r_{\rm ph}) < 0$$
This proves that equatorial circular photon orbits in Kerr spacetime are always local maxima of the effective potential (unstable saddle points in the $(r, p_r)$ phase plane).

**Refined Physical Interpretation:**
1. **Local Radial Instability at Fixed $(E, L_z)$:** A small radial displacement $\delta r$ away from the circular orbit radius $r_{\rm ph}$ with the critical parameters $(E, L_z = b_{\rm ph}E, \mathcal{Q}=0)$ held strictly fixed causes the null geodesic to depart monotonically from $r_{\rm ph}$:
   - If perturbed outward ($\delta r > 0$), $V_{\rm eff}(r) < 0$ for $r > r_{\rm ph}$, allowing the photon to escape to asymptotic infinity ($r \to \infty$).
   - If perturbed inward ($\delta r < 0$), $V_{\rm eff}(r) < 0$ for $r < r_{\rm ph}$, allowing the photon to plunge across the outer event horizon ($r \to r_+$).

2. **Distinction Between Initial-Value Problems:**
   It is essential to distinguish two distinct physical initial-value problems:
   - **Exact Circular Photon Orbit:** Initialized directly on the photon orbit radius ($r(0) = r_{\rm ph}, p_r(0) = 0$). In the ideal unperturbed case, it remains confined to $r = r_{\rm ph}$ for all affine parameter $\lambda$, executing closed periodic motion at coordinate frequency $\Omega_{\rm ph}$.
   - **Incoming Critical Trajectory from Asymptotic Infinity:** Initialized at $r(0) \to \infty$ with $p_r(0) < 0$ and critical impact parameter $b = b_{\rm ph}$. This trajectory is unbounded initially and asymptotically spirals toward $r = r_{\rm ph}$ as $\lambda \to \infty$.

3. **Orientation-Dependent Thresholds and Equality Case for Incoming Photons:**
   For incoming equatorial null geodesics originating from asymptotic infinity ($r \to \infty, p_r < 0, \theta = \pi/2, p_\theta = 0, \mathcal{Q} = 0$), varying $b = L_z / E$ alters the centrifugal barrier height. The corresponding capture, critical, and scattering outcomes are defined by strict inequalities and a unique equality separatrix:

   **For positive spin ($a > 0$):**
   - **Prograde branch ($s = +1, sa > 0$, where $b_{\rm ph} > 0$):**
     - *Scattering side:* $b > b_{\rm ph}$ (or magnitude $|b| > |b_{\rm ph}|$). The photon encounters an outer radial turning point at $r_{\rm turn} > r_{\rm ph}$ where $p_r = 0$, reverses direction, and scatters back to infinity.
     - *Capture side:* $0 < b < b_{\rm ph}$ (or magnitude $|b| < |b_{\rm ph}|$). The photon encounters no turning point outside the horizon ($R(r) > 0$ for all $r > r_+$) and plunges across the event horizon.
     - *Critical separatrix (Equality Case):* $b = b_{\rm ph}$ (or magnitude $|b| = |b_{\rm ph}|$). The trajectory lies exactly on the boundary between capture and scattering. In the ideal exact geodesic equations, it asymptotically approaches the unstable circular photon orbit at $r = r_{\rm ph}$ as $\lambda \to \infty$ (and $t \to \infty$), winding an infinite number of times as $r \to r_{\rm ph}^+$. It is therefore neither an ordinary scattering trajectory (it never encounters an outer turning point where $p_r$ reverses) nor an ordinary captured trajectory (it never crosses the event horizon in finite affine time).
   - **Retrograde branch ($s = -1, sa < 0$, where $b_{\rm ph} < 0$):**
     - *Scattering side:* $b < b_{\rm ph}$ (or magnitude $|b| > |b_{\rm ph}|$, since both $b$ and $b_{\rm ph}$ are negative, e.g. $b = -7M < b_{\rm ph} \approx -6.14M$). The photon encounters a radial turning point outside $r_{\rm ph}$ and scatters back to infinity.
     - *Capture side:* $b > b_{\rm ph}$ (or magnitude $|b| < |b_{\rm ph}|$, e.g. $b = -5M > b_{\rm ph} \approx -6.14M$). The photon encounters no turning point and plunges across the event horizon.
     - *Critical separatrix (Equality Case):* $b = b_{\rm ph}$ (or magnitude $|b| = |b_{\rm ph}|$). The incoming retrograde photon asymptotically spirals onto the retrograde circular photon orbit at $r = r_{\rm ph}^{\rm retro}$ as $\lambda \to \infty$.

   **Unified Positive Magnitude Formulation:**
   Using the circulation orientation sign $s = \mathrm{sgn}(L_z) = \mathrm{sgn}(b) \in \{-1, +1\}$ such that $s b = |b| > 0$ and $s b_{\rm ph} = |b_{\rm ph}| > 0$, the exact classification for any equatorial orientation is:
   $$\text{Scattering} \iff s b > s b_{\rm ph} \iff |b| > |b_{\rm ph}|$$
   $$\text{Critical Separatrix} \iff s b = s b_{\rm ph} \iff |b| = |b_{\rm ph}|$$
   $$\text{Capture} \iff s b < s b_{\rm ph} \iff |b| < |b_{\rm ph}|$$

   **Negative Black-Hole Spin ($a < 0$):**
   When $a < 0$, the black hole frame-dragging direction is reversed ($-\phi$). Physical orientation is determined by the sign of $sa$, not by coordinate circulation alone:
   - Prograde ($sa > 0 \implies s = -1, b_{\rm ph} < 0$): Scattering occurs for $b < b_{\rm ph}$ ($|b| > |b_{\rm ph}|$); critical separatrix at $b = b_{\rm ph}$ ($|b| = |b_{\rm ph}|$); capture occurs for $b > b_{\rm ph}$ ($|b| < |b_{\rm ph}|$).
   - Retrograde ($sa < 0 \implies s = +1, b_{\rm ph} > 0$): Scattering occurs for $b > b_{\rm ph}$ ($|b| > |b_{\rm ph}|$); critical separatrix at $b = b_{\rm ph}$ ($|b| = |b_{\rm ph}|$); capture occurs for $b < b_{\rm ph}$ ($|b| < |b_{\rm ph}|$).

   **Domain and Scope Qualification:**
   These conditions apply strictly to incoming equatorial null geodesics originating from asymptotic infinity. They do not describe outgoing rays emitted from the strong-field region ($r < r_{\rm ph}$), non-equatorial spherical photon orbits with non-zero Carter constant ($\mathcal{Q} > 0$), or timelike particles ($\mu > 0$). The circular photon orbit at $b = b_{\rm ph}$ forms the critical separatrix between these open scattering and capture basins, whose global structure across parameter space is systematically investigated in Stage 3D.

### G. Near-Extremal Limiting Values ($a \to M^-$)
In the near-extremal limit $a/M \to 1^-$ ($\epsilon = \sqrt{1 - a^2/M^2} \to 0$):
- **Prograde ($s = +1$):**
  $$r_{\rm ph}^{\rm pro} \to M^+, \quad b_{\rm ph}^{\rm pro} \to 2M^+, \quad \Omega_{\rm ph}^{\rm pro} \to \frac{1}{2M}^-$$
  The coordinate separation $r_{\rm ph}^{\rm pro} - r_+$ scales as $\frac{4}{\sqrt{3}} M \epsilon \approx \frac{4\sqrt{2}}{\sqrt{3}} M \sqrt{1 - a/M} > 0$, remaining strictly outside the event horizon for all subextremal spins.
- **Retrograde ($s = -1$):**
  $$r_{\rm ph}^{\rm retro} \to 4M^-, \quad b_{\rm ph}^{\rm retro} \to -7M^-, \quad \Omega_{\rm ph}^{\rm retro} \to -\frac{1}{7M}^+$$


---

# 11. Equatorial Kerr Photon Capture, Scattering, and Critical-Boundary Dynamics (Stage 3D)

## A. Radial Separation Equation for Equatorial Null Geodesics
In Kerr spacetime, the geodesic equations of motion decouple under Carter separation. For a null ray ($\mu = 0$) confined strictly to the equatorial plane ($\theta = \pi / 2$, $p_\theta = 0$), the Carter separation constant satisfies $\mathcal{Q} = 0$, and the Boyer-Lindquist radial coordinate evolution is governed by:
$$\Sigma^2 \left(\frac{dr}{d\lambda}\right)^2 = R(r)$$
On the equatorial plane, $\Sigma(r, \pi/2) = r^2$, reducing the radial equation to:
$$r^4 \left(\frac{dr}{d\lambda}\right)^2 = R(r)$$
where the radial potential $R(r)$ is:
$$R(r) = [E(r^2 + a^2) - a L_z]^2 - \Delta(r) (L_z - a E)^2$$
with $\Delta(r) = r^2 - 2Mr + a^2$.

Introducing the signed impact parameter $b \equiv L_z / E$, where $E = -p_0 > 0$ and $L_z = p_\phi$, the radial potential factors proportionally to $E^2$:
$$\frac{R(r)}{E^2} = [(r^2 + a^2) - ab]^2 - (r^2 - 2Mr + a^2)(b - a)^2$$

Expanding each squared term:
$$[(r^2 + a^2) - ab]^2 = r^4 + 2r^2 a(a - b) + a^2(a - b)^2$$
$$(r^2 - 2Mr + a^2)(b - a)^2 = r^2(b - a)^2 - 2Mr(b - a)^2 + a^2(a - b)^2$$
Subtracting the two expressions, the constant terms $a^2(a - b)^2$ cancel identically:
$$\frac{R(r)}{E^2} = r^4 + [2a(a - b) - (b - a)^2] r^2 + 2M(b - a)^2 r$$
Noting that $2a(a - b) - (b - a)^2 = -(b^2 - a^2)$, this simplifies to:
$$\frac{R(r)}{E^2} = r^4 - (b^2 - a^2) r^2 + 2M(b - a)^2 r$$

Because $R(0) = 0$ identically, $r > 0$ can be factored out, yielding the exact depressed cubic polynomial:
$$\frac{R(r)}{E^2} = r \cdot C(r)$$
where:
$$C(r) \equiv r^3 - (b^2 - a^2) r + 2M(b - a)^2$$

## B. Critical Points, Turning Points, and Discriminant Analysis
Physical radial motion requires $(dr/d\lambda)^2 = R(r)/r^4 \ge 0$, which for $r > 0$ is equivalent to $C(r) \ge 0$. Outer radial turning points (periapses) where an incoming photon from infinity reverses its radial motion satisfy:
$$R(r_{\rm turn}) = 0 \iff C(r_{\rm turn}) = 0 \quad \text{with} \quad C'(r_{\rm turn}) > 0$$

Differentiating the depressed cubic $C(r)$ with respect to $r$:
$$C'(r) = 3r^2 - (b^2 - a^2)$$
$$C''(r) = 6r$$

Because $C''(r) > 0$ for all $r > 0$, any stationary point of $C(r)$ on the positive real axis is a strict local minimum:
1. **Case $b^2 \le a^2$:**
   $C'(r) = 3r^2 + (a^2 - b^2) \ge 0$ for all $r \ge 0$. Since $C(0) = 2M(b - a)^2 \ge 0$ and $C'(r) \ge 0$, $C(r)$ is strictly positive for all $r > 0$. Therefore, $R(r) > 0$ everywhere outside the event horizon $r_+$. An incoming photon encounters no turning point and is captured unconditionally.
2. **Case $b^2 > a^2$:**
   $C'(r) = 0$ has a unique positive critical point:
   $$r_{\rm min} = \sqrt{\frac{b^2 - a^2}{3}}$$
   Evaluating the depressed cubic at this minimum:
   $$C(r_{\rm min}) = r_{\rm min}^3 - (3 r_{\rm min}^2) r_{\rm min} + 2M(b - a)^2 = 2 \left[ M(b - a)^2 - \left(\frac{b^2 - a^2}{3}\right)^{3/2} \right]$$

The sign of $C(r_{\rm min})$ completely classifies the radial phase portrait of equatorial null geodesics:
- **Supercritical ($C(r_{\rm min}) < 0 \iff |b| > |b_{\rm ph}|$):**
  Since $C(r_{\rm min}) < 0$ and $C(r) \to +\infty$ as $r \to +\infty$, the Intermediate Value Theorem guarantees a unique real root $r_{\rm turn} > r_{\rm min} \ge r_{\rm ph} > r_+$. Since $C'(r) > 0$ for $r > r_{\rm min}$, $C'(r_{\rm turn}) > 0$, confirming that $r_{\rm turn}$ is a genuine turning point. Photons incoming from infinity reflect off this potential barrier and scatter back to infinity (`SCATTERED`).
- **Critical Separatrix ($C(r_{\rm min}) = 0 \iff |b| = |b_{\rm ph}|$):**
  $r_{\rm min}$ is a double root of $C(r)$, satisfying $C(r_{\rm min}) = 0$ and $C'(r_{\rm min}) = 0$. This occurs precisely at the circular photon orbit radius $r_{\rm min} = r_{\rm ph}$ with critical impact parameter $b = b_{\rm ph}$. An incoming ray asymptotically approaches $r_{\rm ph}$ as $\lambda \to \infty$ without reaching a finite turning point or crossing the horizon (`CRITICAL`).
- **Subcritical ($C(r_{\rm min}) > 0 \iff |b| < |b_{\rm ph}|$):**
  $C(r) > 0$ for all $r > 0$. No turning point exists anywhere outside the horizon. The photon overcomes the centrifugal barrier and crosses the outer horizon $r_+$ (`CAPTURED`).

## C. Equivalence of Hamiltonian Constraint and Separated Radial Equation
The initial radial conjugate momentum $p_r$ for an incoming equatorial photon can be constructed through two equivalent formalisms:
1. **Canonical Hamiltonian Constraint:**
   Setting $\mathcal{H} = \frac{1}{2} g^{\mu\nu} p_\mu p_\nu = 0$ with $p_0 = -E$, $p_\theta = 0$, $p_\phi = bE$:
   $$g^{rr} p_r^2 + g^{00} E^2 - 2g^{0\phi} E(bE) + g^{\phi\phi}(bE)^2 = 0$$
   Solving for the inward branch ($p_r \le 0$):
   $$p_r^{\rm Ham} = -\sqrt{-\frac{g^{00}E^2 - 2g^{0\phi} b E^2 + g^{\phi\phi} b^2 E^2}{g^{rr}}}$$
2. **Carter Separated Equation:**
   Using the metric components on the equatorial plane $\Sigma = r^2$, $g^{rr} = \Delta / r^2$, and $r^4 (dr/d\lambda)^2 = R(r)$:
   $$p_r = g_{rr} \frac{dr}{d\lambda} = \frac{r^2}{\Delta} \left(-\frac{\sqrt{R(r)}}{r^2}\right) = -\frac{\sqrt{R(r)}}{\Delta(r)}$$

Both expressions are mathematically identical and agree to machine precision ($|p_r^{\rm Ham} - p_r^{\rm pot}| < 10^{-16}$) across all subextremal Kerr spacetimes.

## D. Critical Separatrix Dynamics and Logarithmic Affine Dwell Scaling
Near the unstable circular photon orbit $r_{\rm ph}$, linearizing the radial geodesic equation $d^2 r / d\lambda^2 = \frac{1}{2 r^4} R'(r)$ around $r = r_{\rm ph}$ with $R(r_{\rm ph}) = 0$ and $R'(r_{\rm ph}) = 0$:
$$\frac{d^2(\delta r)}{d\lambda^2} \approx \gamma^2 \delta r, \quad \text{where} \quad \gamma \equiv \frac{\sqrt{R''(r_{\rm ph})}}{\sqrt{2} r_{\rm ph}^2} > 0$$
where $\gamma$ is the Lyapunov instability exponent of the photon orbit with respect to affine parameter $\lambda$.

Using the exact factorization $R(r) = E^2 r \cdot C(r)$, the second radial derivative holding conserved constants $(E, L_z)$ fixed is:
$$R''(r) = E^2 [2C'(r) + r C''(r)]$$
At the circular photon orbit $r = r_{\rm ph}$ with critical impact parameter $b = b_{\rm ph}$, $C'(r_{\rm ph}) = 0$ identically, while $C''(r) = 6r$. Consequently:
$$R''(r_{\rm ph}) = E^2 r_{\rm ph} C''(r_{\rm ph}) = 6 E^2 r_{\rm ph}^2$$
This yields an exact algebraic formula for the Lyapunov exponent across all equatorial circular photon orbits in Kerr and Schwarzschild spacetimes:
$$\gamma = \frac{\sqrt{6 E^2 r_{\rm ph}^2}}{\sqrt{2} r_{\rm ph}^2} = \frac{\sqrt{3} E}{r_{\rm ph}}$$
Notice that $\gamma$ is proportional to the chosen energy scale $E$ through the affine parameter normalization $p^0 = dt / d\lambda \to E$ at infinity. For standard unit-energy geodesics ($E = 1.0$), this reduces to $\gamma = \sqrt{3} / r_{\rm ph}$.

For an incoming ray with near-critical impact parameter $b = b_{\rm ph}(1 + \delta)$ with $0 < \delta \ll 1$, the turning point periapsis displacement scales quadratically as:
$$x_{\rm turn} \equiv r_{\rm turn} - r_{\rm ph} \propto \sqrt{\delta}$$
Integrating the linearized radial phase portrait $(dx/d\lambda)^2 \approx \gamma^2(x^2 - x_{\rm turn}^2)$ from an exterior radius $x_0 \gg x_{\rm turn}$ down to periapsis $x_{\rm turn}$:
$$\lambda_{\rm turn}(\delta) \approx \lambda_0 + \frac{1}{\gamma} \ln\left(\frac{2x_0}{x_{\rm turn}}\right) = \lambda_0 + \frac{1}{2\gamma} \ln\left(\frac{1}{\delta}\right) = \lambda_0 + \frac{r_{\rm ph}}{2\sqrt{3} E} \ln\left(\frac{1}{\delta}\right)$$

Notice that the theoretical arrival slope with respect to $\ln(1/\delta)$ is:
$$S_{\rm theo} = \frac{1}{2\gamma} = \frac{r_{\rm ph}}{2\sqrt{3} E}$$
The factor of $1/2$ arises because the incoming trajectory traverses only the exterior half of the potential barrier down to periapsis, rather than completing transmission across the barrier crest. For $E = 1.0$, $S_{\rm theo} = r_{\rm ph} / (2\sqrt{3})$.

**Empirical Verification and Fitting Parameters:**
Numerical integrations over a 13-point geometric grid $\delta \in [10^{-6}, 10^{-2}]$ ($N = 13$ points: $10^{-2}, 5\times 10^{-3}, \dots, 10^{-6}$) confirm this theoretical slope across tested spins and orientations:
- **Schwarzschild ($a = 0, r_{\rm ph} = 3M$):** $S_{\rm theo} = \frac{\sqrt{3}}{2} \approx 0.866025M$; linear fit $S_{\rm fit} = 0.862943M$ (relative discrepancy $0.36\%$, max residual $0.0201M$). In the asymptotic near-critical window $\delta \in [10^{-6}, 10^{-4}]$, the error shrinks below $0.05\%$.
- **Kerr ($a = +0.5M$ Prograde, $r_{\rm ph} \approx 2.347296M$):** $S_{\rm theo} \approx 0.677606M$; linear fit $S_{\rm fit} = 0.675048M$ (relative discrepancy $0.38\%$, max residual $0.0168M$).
- **Kerr ($a = +0.5M$ Retrograde, $r_{\rm ph} \approx 3.532089M$):** $S_{\rm theo} \approx 1.019626M$; linear fit $S_{\rm fit} = 1.016102M$ (relative discrepancy $0.35\%$, max residual $0.0229M$).
- **Kerr ($a = +0.99M$ Prograde, $r_{\rm ph} \approx 1.167642M$):** $S_{\rm theo} \approx 0.337069M$; linear fit $S_{\rm fit} = 0.335748M$ (relative discrepancy $0.39\%$, max residual $0.0084M$).
- **Kerr ($a = +0.99M$ Retrograde, $r_{\rm ph} \approx 3.991103M$):** $S_{\rm theo} \approx 1.152132M$; linear fit $S_{\rm fit} = 1.148217M$ (relative discrepancy $0.34\%$, max residual $0.0253M$).

*Scope Qualification:* This logarithmic scaling applies strictly to incoming equatorial null geodesics traversing the unstable barrier peak in subextremal Kerr spacetimes ($|a| < M$). It is not asserted as universal for supercritical captures or non-equatorial trajectories.

## E. Parity and Sign-Reversal Symmetry
Under simultaneous reversal of black-hole spin and impact parameter:
$$(a, b) \longleftrightarrow (-a, -b)$$
the depressed cubic polynomial transforms as:
$$C(r; -a, -b) = r^3 - ((-b)^2 - (-a)^2)r + 2M(-b - (-a))^2 = r^3 - (b^2 - a^2)r + 2M(b - a)^2 = C(r; a, b)$$
The radial potential $R(r)$ and its roots $r_{\rm turn}$ are strictly invariant under this parity transformation. Numerical simulations confirm that the radial trajectories $r(\lambda)$ for $(a, b)$ and $(-a, -b)$ are bit-for-bit identical.
