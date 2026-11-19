# Milestone 2F.1 Report: Independent Visual Acceptance Audit

**Document**: `docs/lab/milestone_2f1_visual_acceptance_report.md`
**Date**: 2026-11-19
**Branch**: `feat/kerr-geodesics-lab`
**Release Tag**: `v1.0.0` (Immutable baseline: `062b20c80a689640637a2fcd003bdd921a7d4132`)
**Scope**: Visual QA Review & Verification of Milestone 2F Light Theme Refinements (Zero code changes made during this audit).
**Final Verdict**: **PASS** (with 1 minor cosmetic observation documented for future consideration)

---

## 1. Screenshot Matrix & Inventory

All 15 screenshots were freshly captured from the running production build (`http://localhost:3000`) connected to the live FastAPI engine (`http://127.0.0.1:8000`). Screenshots are archived in the repository under `artifacts/milestone_2f1_visual_acceptance/`:

| # | Page / Route | Viewport | Theme | Screenshot File Path | Dimensions | Size |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | **Home (`/`)** | Desktop (1440×900) | Light | `artifacts/milestone_2f1_visual_acceptance/home_desktop_light.png` | 1024×640 | 89,169 B |
| 2 | **Home (`/`)** | Desktop (1440×900) | Dark | `artifacts/milestone_2f1_visual_acceptance/home_desktop_dark.png` | 1024×640 | 83,876 B |
| 3 | **Home (`/`)** | Mobile (390×844) | Light | `artifacts/milestone_2f1_visual_acceptance/home_mobile_light.png` | 474×1024 | 111,503 B |
| 4 | **Explorer (`/explorer`)** | Desktop (1440×900) | Light | `artifacts/milestone_2f1_visual_acceptance/explorer_desktop_light.png` | 1024×640 | 133,629 B |
| 5 | **Explorer (`/explorer`)** | Desktop (1440×900) | Dark | `artifacts/milestone_2f1_visual_acceptance/explorer_desktop_dark.png` | 1024×640 | 126,493 B |
| 6 | **Explorer (`/explorer`)** | Mobile (390×844) | Light | `artifacts/milestone_2f1_visual_acceptance/explorer_mobile_light.png` | 474×1024 | 128,512 B |
| 7 | **Explorer (`/explorer`)** | Mobile (390×844) | Dark | `artifacts/milestone_2f1_visual_acceptance/explorer_mobile_dark.png` | 474×1024 | 125,090 B |
| 8 | **Orbit Gallery (`/gallery`)**| Desktop (1440×900) | Light | `artifacts/milestone_2f1_visual_acceptance/gallery_desktop_light.png` | 1024×824 | 116,033 B |
| 9 | **Orbit Gallery (`/gallery`)**| Desktop (1440×900) | Dark | `artifacts/milestone_2f1_visual_acceptance/gallery_desktop_dark.png` | 1024×824 | 88,768 B |
| 10| **Orbit Gallery (`/gallery`)**| Mobile (390×844) | Light | `artifacts/milestone_2f1_visual_acceptance/gallery_mobile_light.png` | 474×1024 | 88,083 B |
| 11| **Orbit Gallery (`/gallery`)**| Mobile (390×844) | Dark | `artifacts/milestone_2f1_visual_acceptance/gallery_mobile_dark.png` | 474×1024 | 81,559 B |
| 12| **Docs (`/docs`)** | Desktop (1440×900) | Light | `artifacts/milestone_2f1_visual_acceptance/docs_desktop_light.png` | 1024×640 | 128,844 B |
| 13| **Docs (`/docs`)** | Desktop (1440×900) | Dark | `artifacts/milestone_2f1_visual_acceptance/docs_desktop_dark.png` | 1024×640 | 126,363 B |
| 14| **About (`/about`)** | Desktop (1440×900) | Light | `artifacts/milestone_2f1_visual_acceptance/about_desktop_light.png` | 1024×640 | 179,750 B |
| 15| **Validation (`/validation`)**| Desktop (1440×900) | Light | `artifacts/milestone_2f1_visual_acceptance/validation_desktop_light.png` | 1024×640 | 155,042 B |

---

## 2. Page-by-Page Findings

### A. Home (`/`)
- **Desktop Light & Dark**:
  - Publication headline rendered cleanly in `Newsreader` serif; lead paragraph in `IBM Plex Sans` (15px) is legible with no visual strain.
  - Three primary entry buttons (*Launch Geodesic Explorer*, *Orbit Gallery*, *Validation Record*) have clear hierarchy, terracotta primary accent (`#B94A24`), and subtle border outlines.
  - Figure 1 renders an authentic Schwarzschild relativistic precession orbit with no dark container frames; plot surface is completely continuous with the card panel (`#FFFFFF` in light, `#15181C` in dark).
  - Empirical benchmark summary cards clearly communicate repository metrics (4,440 passing, $|H| \le 10^{-15}$, 7 presets, DOP853 stepper).
- **Mobile Light (390px)**:
  - Header, buttons, and orbit figure stack vertically without horizontal scrollbar (`scrollWidth: 390px`, `0px` overflow).
  - Trajectory SVG scales smoothly with touch-friendly zoom controls.

### B. Geodesic Explorer (`/explorer`)
- **Desktop Light & Dark**:
  - Two-column layout (4-col parameter rail, 8-col plot and diagnostics area) has clear visual hierarchy.
  - Input fields have explicit border outlines, warm light backgrounds (`#F3EFEA` in light mode), and distinct unit indicators (`M`, rad).
  - Parameter labels (`Mass (M)`, `Orbital Radius (r)`, `Radial Perturbation (δp_r)`, `Affine Span`) have high-contrast ink (`--foreground` and `--foreground-secondary`), with default values clearly noted.
  - "Run integration" button uses the terracotta accent (`#B94A24`), providing a strong visual call-to-action with 5.21:1 contrast.
  - Trajectory line is prominent (`strokeWidth="1.75"` in terracotta).
  - Conserved quantities table ($E, L_z, Q, |\Delta H|$) uses tabular monospace numerals and high-contrast table headers.
- **Mobile Light & Dark (390px)**:
  - Responsive single-column flow with parameters on top and plot below. Zero horizontal document overflow (`0px`).
  - Inputs maintain $\ge 44\text{px}$ touch target heights.

### C. Orbit Gallery (`/gallery`)
- **Desktop Light & Dark**:
  - Filter chips (*All (7)*, *Schwarzschild (3)*, *Kerr (4)*, *Timelike*, *Null*) are cleanly styled without neon badges. Active filter has a subtle hairline border and white background.
  - Cards present authentic precomputed trajectories directly from `gallery_trajectories.json`.
  - Orbit type and spacetime are rendered as quiet, readable monospaced metadata (`Schwarzschild · Timelike · a = 0`).
  - Physical configuration parameters and conserved quantities tables are legible ($\ge 12\text{px}$).
  - "Open in Explorer" deep-links function reliably with URL parameterization (`?preset=...`).
- **Mobile Light & Dark (390px)**:
  - Filter bar scrolls horizontally smoothly with zero document-level horizontal overflow (`scrollWidth: 390px`).
  - Cards stack cleanly into single-column cards with generous padding.

### D. Technical Documentation (`/docs`)
- **Desktop Light & Dark**:
  - Rebuilt as peer-reviewed technical reference documentation rather than a commercial SaaS API dashboard.
  - Method tags (`GET`, `POST`) are neutral, understated badges with hairline borders. Bright green and yellow pills have been completely eliminated.
  - Code blocks feature light surfaces in light mode (`bg-[var(--surface-subtle)]` `#F3EFEA` with border `#DEDAD2`), dark in dark mode. Monospace syntax is crisp and legible with syntax differentiation.
  - Functional "Copy" buttons provide instant feedback (`Copied` checkmark).
  - Comprehensive coverage of architecture, `/health`, `/api/v1/presets`, `/api/v1/simulations`, `/api/v1/shadows`, and local CLI commands.

### E. About (`/about`)
- **Desktop Light**:
  - Understated, personal first-person essay explaining the physical motivations behind machine-precision Hamiltonian mechanics and Killing symmetry conservation.
  - Author attribution block: **Soumitra Pharikal**, BS-MS Physics, IISER Berhampur. Dignified and appropriate; does not overwhelm the scientific substance of the application.
  - Working copyable BibTeX citation block for academic referencing.

### F. Validation Record (`/validation`)
- **Desktop Light**:
  - Rigorous separation between instantaneous pointwise algebraic identities ($|H| \le 10^{-15}$) and trajectory-integrated conservation drift ($|\Delta H| \le 2.22 \times 10^{-16}$).
  - Documented numerical steppers (`DOP853`, `RKCK45`), root-finding tolerances ($< 10^{-10}$), and physical scope boundaries (Boyer-Lindquist singularities, sub-extremal Kerr restrictions).
  - Recorded regression baseline accurately reflects 4,440 passing tests.

---

## 3. PASS / ISSUE Verification Table

| Category | Item Evaluated | Result | Findings / Evidence |
| :--- | :--- | :--- | :--- |
| **Light Readability** | Body text contrast & sizing | **PASS** | IBM Plex Sans 15px, `#20201E` ink on `#FAF9F6` background (15.34:1 contrast, WCAG AAA). |
| **Light Readability** | Secondary labels & metadata | **PASS** | `#55534F` ink on `#FFFFFF` surface (7.75:1 contrast, WCAG AAA); `#68655F` metadata (5.78:1 contrast, WCAG AA). |
| **Light Readability** | Math symbols, units & code | **PASS** | Italic serif and tabular monospace equations; light code blocks (`#F3EFEA`) with crisp ink. |
| **Light Readability** | Disabled controls & readouts | **PASS** | Disabled controls retain 50% opacity with readable text; hover readouts clearly legible in footer bar. |
| **Light Readability** | Links & focus indicators | **PASS** | 2px solid terracotta focus ring (`:focus-visible`); links use high-contrast ink with hover effects. |
| **Plot Presentation** | Visual integration | **PASS** | Plot canvas surface unified with card surface (`#FFFFFF` in light, `#15181C` in dark); nested borders eliminated. |
| **Plot Presentation** | Ticks & legend readability | **PASS** | Grid ticks ($+x/M$, $+y/M$, $2M, 4M$) and legend items elevated to 12px; high-contrast ink. |
| **Plot Presentation** | Reference markings distinguishability | **PASS** | Horizon (solid disc), ISCO (dashed 3-3), Photon sphere (dashed 2-2), $\lambda_0$ (start circle), $\lambda_{\rm end}$ (end circle); distinguishable by geometry/stroke-dash without relying only on color. |
| **Plot Presentation** | Trajectory prominence | **PASS** | Burnt-orange `#B94A24` stroke width 1.75px stands out distinctly against white and dark backgrounds. |
| **Plot Presentation** | Distortion / dark frames | **PASS** | Equal aspect ratio preserved ($600 \times 600$ SVG viewBox); zero extraneous dark frames. |
| **Layout & Quality** | Gallery card grid & spacing | **PASS** | Responsive 12-column split (7-col plot, 5-col metadata); generous padding; no awkward whitespace. |
| **Layout & Quality** | Spacing & typography consistency | **PASS** | Unified serif headlines, sans-serif controls, monospace numbers, and hairline rules across all pages. |
| **Layout & Quality** | Navbar desktop & mobile | **PASS** | Desktop navbar fits all 7 navigation items cleanly; mobile hamburger menu operates reliably. |
| **Layout & Quality** | Engine status indicator | **PASS** | Subtle online dot + "Engine v1.0.0" indicator visible on desktop; operational status in mobile menu. |
| **Layout & Quality** | Author attribution location | **PASS** | Author block appropriately placed in `/about` and quiet attribution in global footer. |
| **Branding & SVG** | Precessing orbit glyph | **PASS** | Exact vector glyph shared identically across navbar brand mark, favicon (`favicon.svg`), and social card (`og-image.png`). |
| **Branding & SVG** | Scalability & crispness | **PASS** | Crisp vector paths, no stroke artifacts, legible at 22×22px in navbar. |
| **Accessibility** | Mobile horizontal overflow | **PASS** | `scrollWidth == innerWidth == 390px` on all mobile routes; **0px horizontal overflow**. |
| **Accessibility** | Console & runtime errors | **PASS** | **0 console errors** across all routes and interactions. |
| **Accessibility** | Reduced motion support | **PASS** | Instant rendering when `prefers-reduced-motion: reduce` is detected. |

---

## 4. Remaining Observations & Non-Blocking Defects

During thorough inspection of rendered SVG plots, one minor cosmetic observation was noted:

### Observation 1: Turning Point Label Collision on Equatorial Orbits
- **Location**: `frontend/src/components/ScientificPlot.tsx` (SVG Event Marker Layer, line ~425).
- **Description**: When a simulation event root (such as `radial_turning_point`) occurs directly on or near the positive horizontal axis (e.g. $y \approx 0$ at $x \approx 6.0M$ or $x \approx 8.0M$), the event label text (`Turning pt`) positioned at $(x + 6, y - 4)$ can visually touch or slightly overlap the concentric coordinate grid ring label (`6 M` / `8 M`) or the axis direction indicator (`+x / M`).
- **Severity**: **Cosmetic / Minor** (does not impede simulation execution, data export, or reading numerical diagnostics).
- **Recommended Smallest Correction** *(for future polish; no code modified in this audit)*:
  In a future refinement pass, add an SVG background mask/pill or check if $|y| < 0.5$, applying an adaptive vertical offset ($y + 12$ instead of $y - 4$) to avoid collision with horizontal grid tick labels.

---

## 5. Measured Contrast Ratios (Rendered Interface)

| Element Pair | Token Pair | Measured Contrast Ratio | WCAG 2.1 Standard | Status |
| :--- | :--- | :--- | :--- | :--- |
| Primary Body Text on Surface | `#20201E` on `#FFFFFF` | **16.13 : 1** | AAA ($\ge 7.0 : 1$) | **PASS** |
| Primary Text on Page Background | `#20201E` on `#FAF9F6` | **15.34 : 1** | AAA ($\ge 7.0 : 1$) | **PASS** |
| Secondary Labels on Surface | `#55534F` on `#FFFFFF` | **7.75 : 1** | AAA ($\ge 7.0 : 1$) | **PASS** |
| Secondary Labels on Background | `#55534F` on `#FAF9F6` | **7.37 : 1** | AAA ($\ge 7.0 : 1$) | **PASS** |
| Muted Footnotes on Surface | `#68655F` on `#FFFFFF` | **5.78 : 1** | AA ($\ge 4.5 : 1$) | **PASS** |
| Muted Footnotes on Background | `#68655F` on `#FAF9F6` | **5.50 : 1** | AA ($\ge 4.5 : 1$) | **PASS** |
| Action Button (White text on Terracotta) | `#FFFFFF` on `#B94A24` | **5.21 : 1** | AA ($\ge 4.5 : 1$) | **PASS** |
| Trajectory Line on White Surface | `#B94A24` on `#FFFFFF` | **5.21 : 1** | AA graphical ($\ge 3.0 : 1$) | **PASS** |
| Dark Mode Primary Text on Dark Surface | `#ECEFF1` on `#15181C` | **15.41 : 1** | AAA ($\ge 7.0 : 1$) | **PASS** |
| Dark Mode Secondary Text on Dark Surface | `#B0B5BF` on `#15181C` | **8.68 : 1** | AAA ($\ge 7.0 : 1$) | **PASS** |
| Dark Mode Trajectory on Dark Surface | `#EA580C` on `#15181C` | **4.69 : 1** | AA graphical ($\ge 3.0 : 1$) | **PASS** |

---

## 6. Audit Confirmation & Final Verdict

- **Constraint Adherence**:
  - No application code, styling, or configuration was modified during this review.
  - The Python physics engine, API contracts, schemas, and existing tests remain 100% untouched.
  - No git staging, commits, or pushes were performed (`git diff --cached` remains empty).
  - All 4,440 Python regression tests remain passing.
  - 0 console errors and 0px mobile horizontal overflow verified across all 15 matrix viewports.

### **Final Verdict**: **PASS**

Milestone 2F has successfully resolved the previous light-theme deficiencies, delivering an authentic, readable, and visually coherent scientific research application.
