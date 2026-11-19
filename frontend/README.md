# Kerr Geodesics Lab — Frontend

Interactive web client and scientific research instrument for Kerr Geodesics Lab. Built with Next.js (App Router), React, TypeScript, Tailwind CSS, and KaTeX.

The frontend serves as an editorial presentation layer, educational laboratory, and interactive visual interface. All numerical integrations, Hamiltonian dynamics, event detection root-finding, and shadow calculations are performed strictly by the Python physics engine via the FastAPI backend adapter.

---

## Architecture & Local Development Topology

Kerr Geodesics Lab operates as a two-tier application:

- **Frontend Client:** Next.js application running on `http://localhost:3000`
- **Backend API:** FastAPI scientific adapter running on `http://127.0.0.1:8000`

### API Connectivity & Environment Variables

By default, the client communicates with the backend at `http://127.0.0.1:8000`. To point the frontend to an alternate backend address, define:

```bash
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

---

## Prerequisites

- **Node.js:** v20.x or v22.x (Node 22 recommended for native TypeScript test execution)
- **npm:** v10.x or higher
- **Python:** 3.10+ with `kerr-geodesics[api,dev]` installed from the repository root

---

## Getting Started

### 1. Install Dependencies

From the `frontend/` directory:

```bash
npm install
```

### 2. Start the Backend API

From the repository root (in a separate terminal):

```bash
uvicorn geodesics.api.app:app --host 127.0.0.1 --port 8000
```

Verify backend health:
```bash
curl http://127.0.0.1:8000/health
```

### 3. Start the Frontend Development Server

From the `frontend/` directory:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## Available Scripts

Run all scripts from the `frontend/` directory:

- `npm run dev`: Starts the Next.js development server on port 3000.
- `npm run build`: Compiles the optimized production build using Next.js and Turbopack.
- `npm run start`: Starts the Next.js production server on port 3000 (run `npm run build` first).
- `npm run lint`: Runs ESLint to verify code style and TypeScript rules.
- `npm test`: Runs the direct TypeScript test runner (`frontend/scripts/test_kerr_geometry.ts`) using Node.js native type stripping.
- `npx tsc --noEmit`: Performs static TypeScript type-checking across all application and script files without emitting JS.

---

## Testing

### Direct Frontend Tests
From the `frontend/` directory:

```bash
npm test
```
Exercises `src/lib/kerrGeometry.ts` directly, verifying Schwarzschild limits, subextremal branch splittings, ergosphere boundaries, and numeric domain safety.

### Backend & API Tests
From the repository root:

```bash
pytest tests/test_api.py
pytest tests/test_mathematics_lab_calculator.py
pytest tests/
```
