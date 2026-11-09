# Kerr Circular Photon Orbit Precision Audit

This directory contains the independent high-precision reference solver, verification data, and reproduction scripts for numerical precision audits of Kerr circular photon orbits ($r_{\rm ph}$) and critical impact parameters ($b_{\rm ph}$) evaluated directly against the project codebase (`KerrMetric`).

## 1. Independent Decimal Reference Calculation

The reference standard uses Python's standard-library `decimal` module configured to 100 decimal digits (`getcontext().prec = 100`):
- Solves the depressed cubic condition for circular photon orbits:
  $$P(u) = u^3 - 3u + 2\sigma\chi = 0$$
  where $u = \sqrt{r_{\rm ph}/M}$, $\chi = |a|/M$, and $\sigma = \operatorname{sgn}(s \cdot a) \in \{+1, -1\}$.
- Solution method: Halley's third-order root-finding method:
  $$u_{k+1} = u_k - \frac{2 f(u_k) f'(u_k)}{2 [f'(u_k)]^2 - f(u_k) f''(u_k)}$$
  terminated when the iterative step satisfies $|\Delta u| < 10^{-102}$ using 100-digit precision arithmetic (`prec = 100`).
- Closed-form critical impact parameter (Form B):
  $$b_{\rm ph} = \frac{2 s r_{\rm ph} \sqrt{M r_{\rm ph}} - a(r_{\rm ph} + M)}{r_{\rm ph} - M}$$
  evaluated with 100-digit precision arithmetic.

## 2. Machine Precision Settings

- IEEE 754 float64 machine epsilon: $\epsilon_{\rm mach} = 2^{-52} \approx 2.220446049250313 \times 10^{-16}$.
- Nominal audit benchmark threshold: $100\,\epsilon_{\rm mach} \approx 2.220446049250313 \times 10^{-14}$.

## 3. Reproduction Commands

To execute the full audit suite and regenerate the summary CSVs:
```bash
python tools/precision_audit/precision_audit.py
```

Generated machine-readable CSV outputs:
- `tools/precision_audit/sweep_subextremal_summary.csv`
- `tools/precision_audit/sweep_near_extremal_transitions.csv`

## 4. Reconciliation of Parameter Sweeps

All reported results are derived from fixed, deterministic float64 arithmetic in IEEE 754:

| Sweep Name | Domain / Interval | Sampling Scheme | Total Evals | Max Sampled Error ($b_{\rm ph}$) | Location of Max | First Point $> 100\,\epsilon_{\rm mach}$ |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **135-Point Initial Sweep (Supported)** | $a/M \in [0, 0.9999]$ | Hybrid uniform + log | 135 | $54.76\,\epsilon_{\rm mach}$ ($1.216 \times 10^{-14}$) | $a = 0.999842M$ (pro) | None in $[0, 0.9999]$ |
| **135-Point Initial Sweep (Full Range)** | $a/M \in [0, 0.999999]$ | Hybrid uniform + log | 135 | $293.67\,\epsilon_{\rm mach}$ ($6.521 \times 10^{-14}$) | $a = 0.999997M$ (pro) | $a = 0.99997488M$ ($126.73\,\epsilon_{\rm mach}$) |
| **8,000-Evaluation Dense Sweep** | $|a|/M \in [0, 0.9999]$ | 2,000 pts $\times$ 4 branches | 8,000 | $67.01\,\epsilon_{\rm mach}$ ($1.488 \times 10^{-14}$) | $a = \pm 0.999873M$ (pro) | None in $[0, 0.9999]$ |
| **10,001-Point High-Resolution Sweep** | $a/M \in [0.9990, 0.9999]$ | Uniform ($\Delta a = 9 \times 10^{-8}$) | 10,001 | $96.97\,\epsilon_{\rm mach}$ ($2.153 \times 10^{-14}$) | $a = 0.99989100M$ (pro) | None in $[0.9990, 0.9999]$ |
| **Transition Grid ($N = 100$)** | $a/M \in [0.99990, 0.99999]$ | Uniform ($\Delta a = 9.09 \times 10^{-7}$) | 100 | $100.06\,\epsilon_{\rm mach}$ | $a = 0.99995909M$ | $a = 0.99995909M$ ($100.06\,\epsilon_{\rm mach}$) |
| **Transition Grid ($N = 501$)** | $a/M \in [0.99990, 0.99999]$ | Uniform ($\Delta a = 1.80 \times 10^{-7}$) | 501 | $288.43\,\epsilon_{\rm mach}$ | $a = 0.99998910M$ | $a = 0.99992682M$ ($107.59\,\epsilon_{\rm mach}$) |
| **Transition Grid ($N = 2,001$)** | $a/M \in [0.99990, 0.99999]$ | Uniform ($\Delta a = 4.50 \times 10^{-8}$) | 2,001 | $288.43\,\epsilon_{\rm mach}$ | $a = 0.99998910M$ | $a = 0.99992682M$ ($107.59\,\epsilon_{\rm mach}$) |

## 5. Deterministic ULP Landscape and Empirical Interpretation

- **Determinism:** Floating-point operations in IEEE 754 arithmetic are completely deterministic; there is no stochasticity or random noise.
- **ULP Aliasing:** Because $r_{\rm ph} - M \to 0$ as $a \to M$, single-ULP roundoff in $u$ propagates through the denominator $r_{\rm ph} - M$, creating high-frequency discrete oscillations in relative error (over 990 local extrema per 3,001 sampled points in $[0.9996, 0.9999]$).
- **Sampling Dependence:** Different discrete sampling densities evaluate different points along this high-frequency discrete profile, explaining why the 2,000-point-per-branch grid reports a maximum observed error of $67.01\,\epsilon_{\rm mach}$ at $a = \pm 0.999873M$, while the 10,001-point uniform grid reports a maximum observed error of $96.97\,\epsilon_{\rm mach}$ at $a = +0.99989100M$, and why finer transition grids detect earlier discrete samples above $100\,\epsilon_{\rm mach}$.
- **Empirical Scope and Absence of Continuous Guarantee:** All precision findings are strictly empirical observations over the specific finite sample sets tested. Evaluation on discrete grids does NOT constitute a mathematical or uniform continuous-domain proof across the uncountably infinite real interval $[0, 0.9999]$. No universal $100\,\epsilon_{\rm mach}$ guarantee across the continuous continuum is claimed or implied. For ultra-near-extremal spins $a > 0.9999M$ ($1 - a/M < 10^{-4}$), loss of significance due to catastrophic cancellation in $r_{\rm ph} - M$ is expected and observed.
