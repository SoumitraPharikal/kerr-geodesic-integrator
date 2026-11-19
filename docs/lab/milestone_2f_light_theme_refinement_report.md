# Milestone 2F Report: Light Theme Visual Refinement & Scientific Editorial Polish

**Date**: 2026-11-19
**Repository**: `Kerr-Geodesic-Integrator`
**Git Branch**: `feat/kerr-geodesics-lab`
**Release Tag**: `v1.0.0` (Immutable baseline: `062b20c80a689640637a2fcd003bdd921a7d4132`)
**Scope**: Frontend design system and light-theme publication polish (Frontend-only; zero engine/API changes).

---

## 1. Executive Summary

Milestone 2F addressed visual deficiencies identified in the initial light theme of Kerr Geodesics Lab. Rather than treating the light theme as an inverted dark mode, the application was art-directed and engineered into a high-contrast, publication-grade scientific research interface reminiscent of peer-reviewed astrophysics journals and precision research instruments.

Key accomplishments:
- **Refined Editorial Token System**: Enacted a warm-paper (`#FAF9F6`) background, crisp white content and plot panels (`#FFFFFF`), near-black ink (`#20201E`), neutral secondary ink (`#55534F`), subtle warm-grey hairline borders (`#DEDAD2`), and a single restrained terracotta/burnt-orange accent (`#B94A24`).
- **Elimination of Nested Dark Frames & Inconsistent Borders**: Removed all pitch-black frames and inner container borders from plot components. In Orbit Gallery, Explorer, and Home, plots now blend seamlessly into their surrounding white card surfaces.
- **Enhanced Typography & Plot Annotations**: Elevated coordinate grid ticks, axis indicators ($+x/M, +y/M$), reference surface labels ($r_{\rm ISCO}, r_{\rm ph}, r_+$), turning point root indicators, and start/end markers ($\lambda_0, \lambda_{\rm end}$) to $\ge 12\text{px}$ with high-contrast inks (`--foreground-secondary` and `--foreground`), resolving faint or unreadable text.
- **Scientific Documentation Restoration**: Replaced the temporary Docs placeholder with a complete, publication-grade API and CLI reference featuring neutral, understated method tags (`GET`, `POST`), light code block surfaces (`#F3EFEA`), syntax highlighting without a rainbow palette, copy-to-clipboard functionality, and full coverage of all endpoints.
- **Verified Authenticity of Gallery Data**: Confirmed that all 7 cards in the Orbit Gallery directly render authentic numerical trajectories computed by the validated Python Hamiltonian engine (DOP853 stepper with $10^{-10}$ tolerances) sourced from `frontend/src/data/gallery_trajectories.json`.
- **Zero Regression / Architectural Invariance**: 4,440/4,440 Python tests passed (`pytest tests/`), TypeScript passed with zero errors (`npx tsc --noEmit`), ESLint passed with zero warnings (`npm run lint`), and Next.js compiled all 9 static routes cleanly (`npm run build`).

---

## 2. Exact Files Changed

All modifications were strictly constrained to the frontend application:

1. `frontend/src/app/globals.css`:
   - Updated light theme design tokens: warm paper (`#FAF9F6`), white surface (`#FFFFFF`), primary ink (`#20201E`), secondary ink (`#55534F`), muted metadata (`#68655F`), hairline border (`#DEDAD2`), terracotta accent (`#B94A24`), and matching plot tokens.
   - Synchronized dark theme tokens to maintain identical component hierarchy without decorative drift.
2. `frontend/src/app/layout.tsx`:
   - Configured default HTML `data-theme="light"` as the primary design target.
   - Fixed text selection highlighting to `selection:bg-[var(--accent)] selection:text-white`.
3. `frontend/src/context/ThemeContext.tsx`:
   - Initialized default theme state to `"light"` when no user preference is cached in `localStorage`.
4. `frontend/src/components/ScientificPlot.tsx`:
   - Implemented conditional border suppression (`border-0 rounded-none`) to prevent nested double borders when embedded in card containers.
   - Bumped coordinate grid labels from 11px to 12px with fill `var(--foreground-secondary)`.
   - Bumped axis indicators (`+x / M`, `+y / M`, `+z / M`) to 12px with fill `var(--foreground-secondary)`.
   - Bumped ISCO, photon sphere, horizon, $\lambda_0$, and $\lambda_{\rm end}$ labels to 12px.
   - Replaced competing hot-pink (`#DB2777`) event root markers with semantic status ink (`var(--status-error)` / `#B91C1C`) at 12px.
   - Elevated hover coordinate readout bar and legend text to 12px (`text-xs`) with `--foreground-secondary`.
5. `frontend/src/app/gallery/page.tsx`:
   - Passed `className="border-0 rounded-none h-full"` to seamlessly merge plot canvases into their parent cards without black frames.
   - Replaced colored pills with quiet, readable monospaced metadata (`Schwarzschild · Timelike · a = 0`).
   - Increased card spacing and elevated physical parameter and conserved quantity table text sizes to 12px (`text-xs`) with high-contrast keys and values.
6. `frontend/src/app/docs/page.tsx`:
   - Rebuilt technical documentation page with neutral method tags (`GET`, `POST`), light code block surfaces (`bg-[var(--surface-subtle)]`), copy-to-clipboard controls, and complete schemas for `/health`, `/api/v1/presets`, `/api/v1/simulations`, `/api/v1/shadows`, and CLI workflows.
7. `frontend/src/app/explorer/page.tsx`:
   - Enhanced contrast on parameter input labels, default indicators, input boundaries, conserved quantities table headers, and run summary metrics.
8. `frontend/src/app/page.tsx`:
   - Embedded hero orbit figure seamlessly without duplicate borders.
   - Improved text contrast across editorial copy and updated empirical benchmark baseline to 4,440 passing tests.
9. `frontend/src/app/validation/page.tsx`:
   - Elevated text contrast for table and notes (`--foreground-secondary`), updated test baseline count to 4,440.
10. `frontend/src/app/about/page.tsx`:
    - Elevated text contrast across editorial prose and author blocks.
11. `frontend/src/components/Navbar.tsx`:
    - Elevated inactive navigation links to `--foreground-secondary` for crisp legibility in light mode.
    - Improved contrast on API connection indicator text.
12. `frontend/src/components/Footer.tsx`:
    - Elevated footer description and navigation link text to `--foreground-secondary`.

---

## 3. Design Decisions & Rationale

| Area | Before (Deficiency) | After (Refinement) | Scientific & Editorial Rationale |
| :--- | :--- | :--- | :--- |
| **Color System** | Inconsistent off-whites with low-contrast grey text and multiple competing accent hues. | Warm paper (`#FAF9F6`), crisp white surface (`#FFFFFF`), near-black ink (`#20201E`), secondary ink (`#55534F`), hairline border (`#DEDAD2`), and a single terracotta accent (`#B94A24`). | Evokes physical paper in academic monographs (ApJ, PRD); ensures all text exceeds WCAG AA/AAA contrast ratios. |
| **Plot Panels** | Inner plots had dark frames or duplicate borders inside parent card containers. | Seamless white plot canvases with matching borders (`border-0 rounded-none` when embedded). | Integrates plots organically into article cards rather than looking like embedded iframes or separate widgets. |
| **Typography Scale** | Grid tick labels and reference ring annotations were 10–11px, rendering faint on high-DPI screens. | All grid ticks, axis indicators, and reference surface labels bumped to $\ge 12\text{px}$ in semibold/regular monospace. | Ensures numerical coordinates are instantly legible during interactive inspection and figure review. |
| **Event Roots** | Turning point roots were rendered in competing hot-pink (`#DB2777`). | Rendered in restrained semantic red (`#B91C1C`) at 12px with clean dot markers. | Prevents decorative distraction; preserves terracotta accent exclusively for the trajectory line. |
| **Docs Page** | Was a placeholder; previous iteration had API dashboard neon badges and pitch-black codeboxes. | Rebuilt as publication technical documentation: neutral method tags (`GET`/`POST`), light code panels (`#F3EFEA`), copy button. | Documentation feels like an appendix to a scientific paper rather than a commercial SaaS developer portal. |
| **Gallery Metadata** | Bright green "Timelike" and orange pills gave an "e-commerce badge" feel. | Quiet, neutral monospaced line: `Schwarzschild · Timelike · a = 0`. | Establishes quiet authority; respects editorial typography hierarchy. |

---

## 4. Contrast Ratios & Accessibility Audit

Automated color-contrast evaluation for light-theme token pairings (evaluated against both white `#FFFFFF` surface and `#FAF9F6` paper background):

| Text / Element | Background Surface | Contrast Ratio | WCAG 2.1 Level | Role |
| :--- | :--- | :--- | :--- | :--- |
| Primary Ink (`#20201E`) | Surface (`#FFFFFF`) | **16.32 : 1** | AAA (Pass) | Headings, primary values, equations |
| Primary Ink (`#20201E`) | Paper (`#FAF9F6`) | **15.50 : 1** | AAA (Pass) | Page titles, article lead paragraphs |
| Secondary Ink (`#55534F`) | Surface (`#FFFFFF`) | **7.67 : 1** | AAA (Pass) | Body prose, table keys, axis labels |
| Secondary Ink (`#55534F`) | Paper (`#FAF9F6`) | **7.29 : 1** | AAA (Pass) | Nav links, section introductions |
| Muted Metadata (`#68655F`) | Surface (`#FFFFFF`) | **5.81 : 1** | AA (Pass) | Captions, footnotes, timestamps |
| Muted Metadata (`#68655F`) | Paper (`#FAF9F6`) | **5.52 : 1** | AA (Pass) | Secondary metadata lines |
| White Text (`#FFFFFF`) | Accent Button (`#B94A24`) | **5.16 : 1** | AA (Pass) | Primary action buttons |
| Trajectory Stroke (`#B94A24`) | Plot Canvas (`#FFFFFF`) | **5.16 : 1** | AA (Pass) | Principal orbital trajectory line |
| Photon Sphere (`#8C4418`) | Plot Canvas (`#FFFFFF`) | **7.10 : 1** | AAA (Pass) | Dashed photon sphere circle $r_{\rm ph} = 3M$ |
| ISCO Circle (`#55534F`) | Plot Canvas (`#FFFFFF`) | **7.67 : 1** | AAA (Pass) | Dashed ISCO boundary circle $r_{\rm ISCO} = 6M$ |
| Event Root (`#B91C1C`) | Plot Canvas (`#FFFFFF`) | **6.01 : 1** | AA (Pass) | Root markers (radial turning point) |

- **Keyboard Navigation**: Focus rings use `:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }` across all inputs and buttons.
- **Reduced Motion**: Honored via `@media (prefers-reduced-motion: reduce)` in `globals.css` with instant transitions and zero animation durations.
- **Horizontal Overflow**: Verified at 0px horizontal scroll across both 1440px desktop and 390px mobile viewports.

---

## 5. Orbit Gallery Trajectory Authenticity Verification

The 7 preset items rendered in the Orbit Gallery were verified to be directly loaded from `frontend/src/data/gallery_trajectories.json`, generated by `scripts/generate_gallery_data.py`:

```typescript
import galleryData from "@/data/gallery_trajectories.json";
// ...
const sim = item.simulation as unknown as SimulationResponse;
<ScientificPlot simulationData={sim} ... />
```

1. **Preset 1 (`schwarzschild_isco_circular`)**: Marginally stable circular orbit at $r=6.0M$, timelike, $E=0.942809$, $L_z=3.464102$, $|\Delta H| \le 2.22 \times 10^{-16}$.
2. **Preset 2 (`schwarzschild_precession`)**: Eccentric precessing bound orbit at $r_0=8.0M$, timelike, $E=0.957427$, $L_z=3.464102$, $|\Delta H| \le 2.22 \times 10^{-16}$.
3. **Preset 3 (`schwarzschild_photon_sphere`)**: Circular unstable null orbit at $r=3.0M$, null, $E=1.0$, $L_z=5.196152$, $|\Delta H| \le 3.55 \times 10^{-15}$.
4. **Preset 4 (`kerr_equatorial_prograde_photon`)**: Relativistic light deflection around Kerr $a=0.90M$, null, $b=10.0M$, $|\Delta H| \le 8.88 \times 10^{-16}$.
5. **Preset 5 (`kerr_equatorial_retrograde_photon`)**: Retrograde photon scattering around Kerr $a=0.90M$, null, $b=-10.0M$, $|\Delta H| \le 8.88 \times 10^{-16}$.
6. **Preset 6 (`kerr_circular_timelike`)**: Direct prograde circular orbit outside horizon at $r=3.0M$, $a=0.90M$, timelike, $E=0.887357$, $L_z=2.457813$, $|\Delta H| \le 4.44 \times 10^{-16}$.
7. **Preset 7 (`kerr_equatorial_scattering`)**: Strong-field equatorial scattering around Kerr $a=0.90M$, timelike, $r_0=15.0M$, $|\Delta H| \le 8.88 \times 10^{-16}$.

Every card includes the solver diagnostics ($n_{\rm fev}$, samples, tolerances $10^{-10}$, engine version `v1.0.0`, release commit `062b20c`, and SHA-256 configuration hash), confirming complete absence of hand-drawn or synthetic SVG approximations.

---

## 6. Fresh Browser QA Screenshot Evidence

The latest Next.js production build (`npx next start -p 3000`) connected to the live FastAPI engine (`127.0.0.1:8000`) was tested and captured across all 7 required viewports and themes:

| # | Viewport / Theme | Page | Screenshot Path | Visual Verification Notes |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **1440px Light** | Docs (`/docs`) | `pass_f_screenshots/docs_1440_light.png` | Warm paper background, neutral `GET` tag, light code panels (`#F3EFEA`), clean copy buttons, zero neon badges. |
| 2 | **1440px Light** | Orbit Gallery (`/gallery`) | `pass_f_screenshots/gallery_1440_light.png` | Seamless white plot canvas, quiet metadata (`Schwarzschild · Timelike · a = 0`), legible 12px ticks/ISCO rings, high-contrast tables. |
| 3 | **1440px Light** | Explorer (`/explorer`) | `pass_f_screenshots/explorer_1440_light.png` | Clean control rail with clear input boxes, terracotta action button, seamless white plot, 12px turning point marker, tabular conserved quantities. |
| 4 | **1440px Light** | Home (`/`) | `pass_f_screenshots/home_1440_light.png` | Editorial headline, high-contrast descriptions, real precomputed orbit figure, 4,440 passing test summary cards. |
| 5 | **390px Light** | Orbit Gallery (`/gallery`) | `pass_f_screenshots/gallery_390_light.png` | Fully responsive 390px single-column layout, horizontal scroll filter bar, 0px document overflow, readable annotations. |
| 6 | **390px Light** | Explorer (`/explorer`) | `pass_f_screenshots/explorer_390_light.png` | Responsive mobile layout, readable parameter inputs with distinct backgrounds and units, prominent run button. |
| 7 | **1440px Dark** | Orbit Gallery (`/gallery`) | `pass_f_screenshots/gallery_1440_dark.png` | Symmetrical dark theme execution, deep graphite surfaces, copper/amber trajectory accents, all 7 presets fully legible. |

---

## 7. Verification & Test Suite Execution

### A. TypeScript Type Check
```bash
cd frontend && npx tsc --noEmit
# Exit code: 0 (Zero errors)
```

### B. ESLint
```bash
cd frontend && npm run lint
# Exit code: 0 (Zero warnings, zero errors)
```

### C. Production Build
```bash
cd frontend && npm run build
# Exit code: 0
# Route (app) - 9/9 pages statically prerendered:
#   / (Home)
#   /_not-found
#   /about
#   /docs
#   /explorer
#   /gallery
#   /mathematics
#   /shadows
#   /validation
```

### D. Python Regression Test Suite
```bash
pytest tests/
# Output:
# ================= 4440 passed, 1 warning in 146.64s (0:02:26) =================
# Exit code: 0
```

### E. Git Repository Integrity
- Release commit `062b20c80a689640637a2fcd003bdd921a7d4132` and release tag `v1.0.0` remain untouched.
- Core physics implementations (`src/geodesics/core/`, `integrators/`, `shadows/`) and existing test files (`tests/test_*.py`) remain completely untouched.
- API adapter contracts and Pydantic schemas (`src/geodesics/api/`) remain completely untouched.
- Staged git changes (`git diff --cached`) remain empty.

---

## 8. Limitations & Forward Roadmap

- **Kerr Analytical Reference Circles**: In accordance with Rule 4, Kerr reference surfaces (outer horizon $r_+$, frame-dragging photon orbit, and Kerr ISCO) are not derived in TypeScript and are omitted from the plot legend until explicit closed-form endpoints are exposed by the API schema.
- **Shadow Lab & Mathematics Pages**: These routes display clean, publication-grade editorial notes indicating planned engine extensions; they do not perform unverified client-side approximations.
- **Local Storage Preference**: Users can toggle between light and dark themes at any time; light mode is the primary default for new visitors.
