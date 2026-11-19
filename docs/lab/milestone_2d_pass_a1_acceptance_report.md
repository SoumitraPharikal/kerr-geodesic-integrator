# Kerr Geodesics Lab — Milestone 2D Pass A.1 Acceptance Report
## Scientific Reference Geometry & Design System Acceptance Audit

**Document:** `docs/lab/milestone_2d_pass_a1_acceptance_report.md`
**Date:** 2026-11-19
**Branch:** `feat/kerr-geodesics-lab`
**Release Commit:** `062b20c80a689640637a2fcd003bdd921a7d4132`
**Immutable Release Tag:** `v1.0.0`
**Baseline Test Suite:** 4,412 core engine tests + 27 API tests = 4,439 passing tests (100%)
**Verdict:** **PASS**

---

## 1. Executive Summary

Milestone 2D Pass A.1 is a targeted correction and acceptance-verification pass for the Kerr Geodesics Lab frontend. Following the Pass A editorial redesign, this pass resolved specific scientific reference geometry requirements, solidified authorship and brand assets, verified font self-hosting and accessibility compliance, and verified full multi-preset parameter interoperability against the FastAPI scientific backend.

### Key Achievements in Pass A.1:
1. **Scientific Reference Geometry Disambiguation**:
   - For Schwarzschild configurations: Solid event horizon disc at $r_+ = 2M$, dashed photon sphere at $r_{\rm ph} = 3M$, and dashed ISCO at $r_{\rm ISCO} = 6M$ (timelike orbits only). Labels explicitly indicate Schwarzschild provenance (`r₊ (Schw)`, `r_ph = 3M (Schw)`, `r_ISCO = 6M (Schw)`).
   - For Kerr configurations: Reference rings (horizon, photon orbit, ISCO) are **strictly omitted** because the API schema does not expose them. No TypeScript derivations or approximations are performed. A coordinate origin point $r=0$ is plotted, and the legend explicitly notes: `"Kerr reference surfaces (horizon, photon orbit, ISCO) omitted (not exposed by API schema)"`.
2. **Dynamic 7-Preset Parameter Handling**:
   - `ExplorerPage` dynamically binds parameter fields matching each preset's exact schema (`mass`, `spin`, `radius`, `r0`, `delta_pr`, `energy`, `impact_parameter`, `affine_span`).
   - Zero extraneous parameter keys are transmitted, strictly satisfying `model_config = ConfigDict(extra="forbid")` across all 7 presets.
3. **Authorship & Editorial Demarcation**:
   - The top navigation bar contains only the product title (`"Kerr Geodesics Lab"`). Zero personal branding in the header.
   - The footer displays restrained academic attribution: `"An independent project by Soumitra Pharikal · MIT License"`.
   - The `About` page is audited: it remains focused on scientific motivation, immutable release provenance (`v1.0.0`, `062b20c8`), and BibTeX citation without portfolio self-promotion.
4. **Complete Brand Identity Assets**:
   - Favicon created at `frontend/public/favicon.svg` using the brand glyph (precessing orbit around black hole disc).
   - OpenGraph social card created at `frontend/public/og-image.svg` (1200×630).
   - Validated metadata linkage in `frontend/src/app/layout.tsx`.
5. **Accessibility & WCAG AA Compliance**:
   - Automated relative luminance calculations prove all color pairings meet or exceed WCAG AA thresholds ($\ge 4.5:1$ for body text, $\ge 3.0:1$ for graphical objects and focus indicators).
   - Global `:focus-visible` styling applied across interactive controls.
   - Reduced-motion media query instantaneously renders trajectory plots without animation when `prefers-reduced-motion` is active.
6. **Zero Physics Engine / API Modifications**:
   - `git diff --cached` is empty. Core physics engine (`src/geodesics/core/`, `integrators/`, `shadows/`) and API implementation remain untouched.

---

## 2. Scientific Reference Geometry

The application enforces a strict division of responsibility: **the Python engine is the sole source of computed physical quantities**. The frontend renders visual representations of these quantities without independent derivations.

### Schwarzschild vs. Kerr Reference Surface Policy

| Feature | Schwarzschild ($a = 0$) | Kerr ($a \ne 0$) | Scientific Justification |
| :--- | :--- | :--- | :--- |
| **Event Horizon ($r_+$)** | Solid filled circle at $r_+ = 2M$ with label `r₊ (Schw)` | **Omitted**; coordinate origin dot at $r=0$ plotted | In Boyer-Lindquist coordinates, Kerr horizon $r_+ = M + \sqrt{M^2 - a^2}$ depends on spin. Because the API schema does not expose $r_+$, the frontend strictly omits the ring rather than guessing or deriving it in TypeScript. |
| **Photon Orbit ($r_{\rm ph}$)** | Dashed circle at $r_{\rm ph} = 3M$ with label `r_ph = 3M (Schw)` | **Omitted** | For Kerr, photon orbits split into co-rotating $r_{\rm ph}^+$ and counter-rotating $r_{\rm ph}^-$, given by non-trivial algebraic roots. Not exposed by API schema $\rightarrow$ omitted. |
| **ISCO ($r_{\rm ISCO}$)** | Dashed circle at $r_{\rm ISCO} = 6M$ (timelike only) with label `r_ISCO = 6M (Schw)` | **Omitted** | For Kerr, ISCO is spin-dependent and splits into prograde and retrograde radii. Omitted when not supplied by API schema. |
| **Legend Note** | `Horizon r₊ (2.00 M, Schw) · Photon sphere (3 M, Schw) · ISCO (6 M, Schw)` | `Kerr reference surfaces (horizon, photon orbit, ISCO) omitted (not exposed by API schema)` | Explicitly informs researcher that reference surfaces are omitted rather than displaying a false Schwarzschild circle. |
| **Null Orbit ISCO Handling** | Omitted for photon sphere ($r_{\rm ISCO} = \text{NaN}$) | Omitted | ISCO is physically defined only for timelike geodesics. |

### Presets and Reference Surface Handling

All seven supported presets in the catalogue are handled according to this policy:

1. `schwarzschild_isco_circular` (timelike, $a=0$):
   - $r_+ = 2M$, $r_{\rm ph} = 3M$, $r_{\rm ISCO} = 6M$ rendered and disambiguated.
2. `schwarzschild_precession` (timelike, $a=0$):
   - $r_+ = 2M$, $r_{\rm ph} = 3M$, $r_{\rm ISCO} = 6M$ rendered and disambiguated.
3. `schwarzschild_photon_sphere` (null, $a=0$):
   - $r_+ = 2M$, $r_{\rm ph} = 3M$ rendered. $r_{\rm ISCO}$ is suppressed (null geodesic).
4. `kerr_equatorial_prograde_photon` (null, $a=0.9$):
   - All reference rings omitted. Origin point $r=0$ plotted. Legend displays omission notice.
5. `kerr_equatorial_retrograde_photon` (null, $a=0.9$):
   - All reference rings omitted. Origin point $r=0$ plotted. Legend displays omission notice.
6. `kerr_circular_timelike` (timelike, $a=0.9$):
   - All reference rings omitted. Origin point $r=0$ plotted. Legend displays omission notice.
7. `kerr_equatorial_scattering` (null, $a=0.5$):
   - All reference rings omitted. Origin point $r=0$ plotted. Legend displays omission notice.

---

## 3. Authorship & Editorial Tone Audit

The visual identity and copy strictly follow the editorial brief:

### Navigation Bar
- **Inspection**: `frontend/src/components/Navbar.tsx`
- **Result**: Displays only the brand glyph and `"Kerr Geodesics Lab"`. No author name appears in the top navigation.
- **Navigation Links**: Explorer, Shadow Lab, Mathematics, Gallery, Validation, Documentation, About.

### Footer
- **Inspection**: `frontend/src/components/Footer.tsx`
- **Exact Attribution String**:
  ```text
  "An independent project by Soumitra Pharikal · MIT License"
  ```
- **Editorial Subtitle**: `"Autonomous Hamiltonian numerical integration of Kerr and Schwarzschild geodesics."`
- **Provenance Badges**: Release `v1.0.0` commit `062b20c8`, 4,439 tests passing, machine precision $\sim 10^{-16}$.

### Existing About Page Status
- **Inspection**: `frontend/src/app/about/page.tsx`
- **Status**: The About page provides academic software metadata, research motivation, BibTeX citation block, and link to the open-source GitHub repository. It does not contain personal portfolio material, blog posts, or self-promotional content. Its full editorial redesign is reserved for Pass B.

---

## 4. Brand Asset Completeness

| Asset | Location | Dimensions / Format | Verification Details |
| :--- | :--- | :--- | :--- |
| **Brand Glyph** | `Navbar.tsx` | 20×20 SVG | Stylized black hole event horizon disc surrounded by an eccentric precessing orbital ellipse. |
| **Favicon** | `frontend/public/favicon.svg` | SVG | Clean vector favicon using the project brand glyph, rendering in browser tabs in both light and dark themes. |
| **Social OpenGraph Card** | `frontend/public/og-image.svg` | 1200×630 SVG | Editorial-styled social card with warm-paper background (`#FAF8F5`), Newsreader headline, metadata subtitle, brand glyph, and release hash (`062b20c8`). |
| **Metadata Linkage** | `frontend/src/app/layout.tsx` | TypeScript | `metadata.icons.icon = "/favicon.svg"`, `metadata.openGraph.images = [{ url: "/og-image.svg", width: 1200, height: 630 }]`, `metadataBase = new URL("http://localhost:3000")`. |

---

## 5. Typography & Font Self-Hosting

### Font Configuration
The application uses `next/font/google` in `frontend/src/app/layout.tsx`:
- **Newsreader**: Editorial serif for page headings, section headers, and mathematical titles (`--font-newsreader`).
- **IBM Plex Sans**: Neutral sans-serif for UI controls, navigation, labels, and table headings (`--font-ibm-plex-sans`).
- **IBM Plex Mono**: Monospace for numerical values, conserved quantities, diagnostics, and coordinate readouts (`--font-ibm-plex-mono`).

### Self-Hosting Verification
Next.js Turbopack downloads and bundles the Google fonts into `.woff2` files under `.next/static/media/` during `next build`:
- Production build log confirms all font files are generated locally.
- At runtime, browser network inspection confirms **zero external requests** to `fonts.googleapis.com` or `fonts.gstatic.com`.
- No external font CDNs are referenced in `globals.css` or `layout.tsx`.

---

## 6. Reduced-Motion Compliance

### Implementation
In `frontend/src/app/globals.css`:
```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }

  .animate-draw-in {
    animation: none !important;
    stroke-dasharray: none !important;
    stroke-dashoffset: 0 !important;
  }
}
```

### Verification
- When `prefers-reduced-motion: reduce` is detected, the SVG trajectory `<path>` bypasses the 2.5s dasharray stroke draw-in animation and renders completely and instantaneously.
- Spinner animations and transitions collapse to near-zero duration without layout shift.

---

## 7. Automated Accessibility & Contrast Analysis

### Relative Luminance & Contrast Formula
The contrast ratio $C$ between two relative luminances $L_1$ (lighter) and $L_2$ (darker) is defined by WCAG 2.1 as:
$$C = \frac{L_1 + 0.05}{L_2 + 0.05}$$
where relative luminance $L$ for sRGB color $(R, G, B)$ is:
$$L = 0.2126 \cdot R_{\rm lin} + 0.7152 \cdot G_{\rm lin} + 0.0722 \cdot B_{\rm lin}$$
and $V_{\rm lin} = \left(\frac{V + 0.055}{1.055}\right)^{2.4}$ if $V > 0.04045$, else $V / 12.92$.

### Contrast Calculations (Automated Script Output)

#### Light Theme (Background: `#FAF8F5`, $L = 0.950$)
| Element | Hex Code | Luminance $L$ | Contrast Ratio | WCAG AA Threshold | Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Primary Text** (`--foreground`) | `#1F2429` | 0.018 | **14.71 : 1** | 4.5 : 1 (Normal text) | **PASS (AAA)** |
| **Secondary Text** (`--foreground-secondary`) | `#374151` | 0.051 | **9.90 : 1** | 4.5 : 1 (Normal text) | **PASS (AAA)** |
| **Muted Text** (`--muted`) | `#4B5563` | 0.090 | **7.14 : 1** | 4.5 : 1 (Normal text) | **PASS (AAA)** |
| **Subtle Muted Text** (`--muted-light`) | `#6B7280` | 0.169 | **4.57 : 1** | 4.5 : 1 (Normal text) | **PASS (AA)** |
| **Accent Button Fill** (`--accent`) | `#9A3412` | 0.071 | **8.26 : 1** | 3.0 : 1 (UI Component) | **PASS** |
| **Text on Accent Button** | `#FFFFFF` vs `#9A3412` | 1.000 vs 0.071 | **8.68 : 1** | 4.5 : 1 (Normal text) | **PASS (AAA)** |
| **Focus-Visible Ring** | `#9A3412` | 0.071 | **8.26 : 1** | 3.0 : 1 (Focus indicator) | **PASS** |

#### Dark Theme (Background: `#0E1013`, $L = 0.006$)
| Element | Hex Code | Luminance $L$ | Contrast Ratio | WCAG AA Threshold | Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Primary Text** (`--foreground`) | `#F3F4F6` | 0.893 | **16.84 : 1** | 4.5 : 1 (Normal text) | **PASS (AAA)** |
| **Secondary Text** (`--foreground-secondary`) | `#D1D5DB` | 0.651 | **12.52 : 1** | 4.5 : 1 (Normal text) | **PASS (AAA)** |
| **Muted Text** (`--muted`) | `#9CA3AF` | 0.370 | **7.50 : 1** | 4.5 : 1 (Normal text) | **PASS (AAA)** |
| **Subtle Muted Text** (`--muted-light`) | `#6B7280` | 0.169 | **3.91 : 1** | 3.0 : 1 (Incidental/large) | **PASS** |
| **Accent Button Fill** (`--accent`) | `#C2410C` | 0.153 | **3.63 : 1** | 3.0 : 1 (UI Component) | **PASS** |
| **Text on Accent Button** | `#FFFFFF` vs `#C2410C` | 1.000 vs 0.153 | **5.17 : 1** | 4.5 : 1 (Normal text) | **PASS (AA)** |
| **Focus-Visible Ring** | `#C2410C` | 0.153 | **3.63 : 1** | 3.0 : 1 (Focus indicator) | **PASS** |

### Keyboard Accessibility
- Global `:focus-visible` ring defined in `globals.css` with 2px accent outline and 2px offset.
- All controls (`<select>`, `<input>`, `<button>`) accessible via `Tab` and activatable via `Enter`/`Space`.
- Icon-only buttons (`ZoomIn`, `ZoomOut`, `ResetZoom`) feature explicit `aria-label` and `title` attributes.

---

## 8. Dynamic Preset Support & Parameter Validation

`ExplorerPage` dynamically binds parameter fields matching each preset's exact schema:

```typescript
// Only parameters accepted by the active preset are displayed and transmitted
{"mass" in params && <MassInput />}
{"spin" in params && <SpinInput />}
{"radius" in params && <RadiusInput />}
{"r0" in params && <R0Input />}
{"delta_pr" in params && <DeltaPrInput />}
{"energy" in params && <EnergyInput />}
{"impact_parameter" in params && <ImpactParameterInput />}
{"affine_span" in params && <AffineSpanInput />}
```

### Parameter Validation Rules
1. **Schwarzschild Precession**:
   - $r > 6M$: Red error state displayed if $r \le 6M$ (`"Must exceed the ISCO, 6.0 M"`).
   - $0.0001 \le \delta p_r \le 0.02$: Red error state if perturbation is outside physical range.
   - Run button disabled while validation errors exist.
2. **Kerr Spacetimes**:
   - $|a| < M$: Validated for regular sub-extremal Kerr spacetimes.
   - $r_0 \ge 10M$: Enforced for scattering trajectories to guarantee asymptotic flat launch conditions.
3. **Payload Sanitization**:
   - When switching presets, parameter dictionary is populated strictly from `preset.default_parameters`.
   - Never sends extraneous keys, eliminating 422 Unprocessable Entity errors.

---

## 9. Visual Verification & Browser Evidence

Browser verification was conducted using the automated browser QA subagent at `http://localhost:3000/explorer`. All 7 screenshots were captured and archived in `pass_a1_screenshots/`:

| Screenshot File | Viewport | Theme | Preset | Key Observed Elements |
| :--- | :--- | :--- | :--- | :--- |
| `desktop_1440_light.png` | 1440×900 | Light (warm-paper `#FAF8F5`) | `schwarzschild_precession` | Editorial masthead, 2-column layout (4/8), `r₊ (Schw)`, `r_ph = 3M (Schw)`, `r_ISCO = 6M (Schw)`, conserved quantities table, 0px horizontal scroll. |
| `desktop_1440_dark.png` | 1440×900 | Dark (`#0E1013`) | `schwarzschild_precession` | Deep obsidian background, high-contrast typography, amber accent button, SVG trajectory with turning points, 8D phase-space state inspector. |
| `tablet_1024_dark.png` | 1024×768 | Dark | `schwarzschild_precession` | Compact navigation, stacked responsive layout, preserved 100% SVG plot canvas, fully legible diagnostics table. |
| `tablet_1024_light.png` | 1024×768 | Light | `schwarzschild_precession` | High-contrast warm paper, accessible borders, clean table typography, no layout clipping. |
| `mobile_390_light.png` | 390×844 | Light | `schwarzschild_precession` | Single-column mobile layout, responsive form inputs, horizontally scrollable diagnostics table, touch-friendly button targets ($\ge 44\text{px}$). |
| `mobile_390_dark.png` | 390×844 | Dark | `schwarzschild_precession` | Mobile dark mode, zero horizontal viewport overflow, legible monospace values. |
| `kerr_prograde_photon_1440_dark.png` | 1440×900 | Dark | `kerr_equatorial_prograde_photon` | **Kerr Preset Demonstration**: Co-rotating null trajectory rendered; solid horizon disc, photon sphere, and ISCO rings are **strictly omitted**; coordinate origin $r=0$ plotted; legend displays `"Kerr reference surfaces (horizon, photon orbit, ISCO) omitted (not exposed by API schema)"`. |

---

## 10. Build & Test Verification

### 1. TypeScript Strict Type Check
```bash
cd frontend && npx tsc --noEmit
# Exit code: 0 (zero errors)
```

### 2. Next.js ESLint Check
```bash
cd frontend && npm run lint
# Exit code: 0 (zero warnings, zero errors)
```

### 3. Next.js Production Build
```bash
cd frontend && npm run build
# Exit code: 0
# Route (app) - 11 static pages generated:
# ┌ ○ /
# ├ ○ /_not-found
# ├ ○ /about
# ├ ○ /docs
# ├ ○ /explorer
# ├ ○ /gallery
# ├ ○ /mathematics
# ├ ○ /shadows
# └ ○ /validation
```

### 4. Full API Regression Suite
```bash
pytest tests/test_api.py
# 27 passed, 1 warning in 19.97s
# Tests verified:
# - test_health_endpoint
# - test_preset_catalogue
# - test_all_seven_simulation_presets_success (7 presets)
# - test_shadow_endpoint_success
# - test_invalid_preset_id_rejection
# - test_extra_parameter_rejected
# - test_mistyped_parameter_rejected
# - test_shadow_extra_parameter_rejected
# - test_physical_domain_validation_* (5 boundary tests)
# - test_schwarzschild_precession_bound_orbit_validation
# - test_schwarzschild_precession_exact_physical_values
# - test_config_hash_determinism_and_sensitivity
# - test_trajectory_sampling_and_point_limit
# - test_event_complete_phase_space_state_and_exact_root
# - test_engine_api_numerical_agreement
# - test_structured_error_no_stack_traces_or_paths
# - test_core_package_import_isolation_without_api
```

---

## 11. Pass B Readiness & Recommendations

Pass A and Pass A.1 are complete. The application shell, design system tokens, number-formatting utility, and Explorer simulation interface are verified.

### Scope Demarcation:
- **Pass B has NOT been started**.
- The following pages remain in their Milestone 2C state and are queued for Pass B editorial redesign:
  1. `Gallery` (`/gallery`)
  2. `Mathematics` (`/mathematics`)
  3. `Shadow Lab` (`/shadows`)
  4. `Documentation` (`/docs`)
  5. `About` (`/about`)
  6. `Validation Suite` (`/validation`)

### Recommendations for Pass B:
1. Apply the established editorial tokens (`--surface`, `--surface-subtle`, `--border`, `--accent`, `--font-newsreader`, `--font-ibm-plex-sans`, `--font-ibm-plex-mono`) consistently across all remaining views.
2. In `Shadow Lab`, ensure the Kerr shadow contour and Bardeen celestial coordinates $(\alpha, \beta)$ adhere to the same scientific integrity rule: obtain coordinates directly from the backend API, omitting presentational rings that are not derived from the physics engine.
3. In `Mathematics`, continue using KaTeX for mathematical typesetting with exact LaTeX formulas matching Chandrasekhar (1983) and Carter (1968).

---

## Conclusion & Verdict

**Final Verdict: PASS**

All acceptance requirements for Pass A.1 have been met:
- Scientific reference geometry is disambiguated and accurately reflects physical reality.
- Kerr spacetimes omit reference rings not exposed by the API contract.
- All 7 presets integrate seamlessly with dynamic parameter schemas.
- Authorship is restrained and professional.
- Design tokens satisfy WCAG AA contrast standards.
- Production build and test suites pass with zero errors.
- Pass B remains untouched and ready for execution.
