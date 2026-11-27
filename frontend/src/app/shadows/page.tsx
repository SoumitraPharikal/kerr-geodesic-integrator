import Link from "next/link";
import { ArrowRight } from "lucide-react";
import MathBlock from "@/components/MathBlock";
import MarginNote from "@/components/MarginNote";

export default function ShadowsPage() {
  return (
    <div className="flex flex-col flex-1 pb-24">
      {/* Header */}
      <header className="border-b border-[var(--border)] bg-[var(--surface)] py-10 sm:py-12 px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-6xl space-y-4">
          <div className="font-mono text-xs uppercase tracking-[0.14em] text-[var(--muted)]">
            Planned UI · Backend endpoint available
          </div>
          <h1 className="font-serif text-3xl sm:text-4xl lg:text-[42px] font-normal text-[var(--foreground)] tracking-tight leading-[1.15]">
            Black Hole Shadow Lab
          </h1>
          <p className="prose-notebook text-[var(--foreground-secondary)]">
            Research preview and planned extension for visualizing analytical Kerr critical curves
            in Bardeen celestial coordinates. The interactive frontend interface is not yet wired;
            this page documents the current implementation boundary and the underlying physics.
          </p>
          <div className="flex flex-wrap items-center gap-3 pt-1 font-sans">
            <Link
              href="/explorer"
              className="inline-flex items-center gap-2 rounded-[2px] bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white px-4 py-2 text-sm font-medium"
            >
              <span>Open Explorer</span>
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="/docs#shadows"
              className="inline-flex items-center gap-2 rounded-[2px] border border-[var(--border)] bg-[var(--background)] hover:bg-[var(--surface-hover)] text-[var(--foreground)] px-4 py-2 text-sm font-medium"
            >
              <span>Read shadow API spec</span>
            </Link>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-6xl w-full px-4 sm:px-6 lg:px-8 mt-12 space-y-14">
        {/* 1. Feature Status */}
        <section className="grid grid-cols-1 lg:grid-cols-12 gap-8 border-t border-[var(--border)] pt-8">
          <div className="lg:col-span-4 space-y-3">
            <h2 className="font-serif text-2xl font-normal text-[var(--foreground)]">
              Current status
            </h2>
            <MarginNote label="Frontend vs. API">
              This route is a planned placeholder: it makes no shadow API calls and performs no
              browser-side ray tracing. Saved trajectories in{" "}
              <Link href="/gallery" className="underline underline-offset-2 hover:text-[var(--foreground)]">
                Gallery
              </Link>{" "}
              are geodesic orbits, not shadow boundaries.
            </MarginNote>
          </div>

          <div className="lg:col-span-8 grid grid-cols-1 sm:grid-cols-2 gap-8 text-sm font-sans text-[var(--foreground-secondary)] leading-relaxed">
            <div className="space-y-2">
              <h3 className="font-serif text-lg text-[var(--foreground)]">
                Frontend interface (Planned)
              </h3>
              <ul className="list-disc pl-4 space-y-1.5">
                <li>No interactive shadow canvas, spin slider, or inclination control is active</li>
                <li>Not yet wired to the backend shadow endpoint</li>
                <li>No client-side geodesic ray tracing or fabricated shadow plots</li>
              </ul>
            </div>

            <div className="space-y-2">
              <h3 className="font-serif text-lg text-[var(--foreground)]">
                Backend solver (Implemented)
              </h3>
              <ul className="list-disc pl-4 space-y-1.5">
                <li>
                  <span className="font-mono text-xs text-[var(--foreground)]">
                    POST /api/v1/shadows
                  </span>{" "}
                  is implemented in the Python FastAPI service
                </li>
                <li>
                  Accepts <span className="font-mono text-xs">mass &gt; 0</span>,{" "}
                  <span className="font-mono text-xs">|spin| &le; mass</span>,{" "}
                  <span className="font-mono text-xs">observer_inclination</span>{" "}
                  <MathBlock math="\theta_o \in [0, \pi]" display={false} />, and{" "}
                  <span className="font-mono text-xs">num_points</span>{" "}
                  <MathBlock math="\in [3, 2000]" display={false} />
                </li>
                <li>
                  Returns analytical boundary vertices{" "}
                  <MathBlock math="(\alpha, \beta)" display={false} /> and geometric observables (
                  <span className="font-mono text-xs">area</span>,{" "}
                  <span className="font-mono text-xs">centroid</span>,{" "}
                  <span className="font-mono text-xs">width</span>,{" "}
                  <span className="font-mono text-xs">height</span>)
                </li>
              </ul>
            </div>
          </div>
        </section>

        {/* 2. Physical Concept */}
        <section className="grid grid-cols-1 lg:grid-cols-12 gap-8 border-t border-[var(--border)] pt-8">
          <div className="lg:col-span-4 space-y-3">
            <h2 className="font-serif text-2xl font-normal text-[var(--foreground)]">
              What a Kerr shadow represents
            </h2>
            <MarginNote label="Not a physical surface">
              The shadow boundary is an apparent capture region on a distant observer&apos;s
              celestial screen—determined by unstable spherical photon orbits rather than the event
              horizon <MathBlock math="r_+" display={false} /> directly.
            </MarginNote>
          </div>

          <div className="lg:col-span-8 space-y-4 prose-notebook text-[var(--foreground-secondary)]">
            <p>
              In Kerr spacetime (<MathBlock math="a \neq 0" display={false} />), a single equatorial
              circular photon orbit does not determine the full shadow. Instead, three distinct
              concepts enter the calculation:
            </p>
            <ul className="space-y-3 text-sm font-sans leading-relaxed list-disc pl-5">
              <li>
                <strong className="text-[var(--foreground)] font-medium">Photon region:</strong>{" "}
                Unstable spherical null geodesics at constant Boyer–Lindquist radius{" "}
                <MathBlock math="r_0" display={false} /> span a radial shell between the{" "}
                <span className="text-[var(--prograde)] font-medium">prograde</span> (
                <MathBlock math="r_{\rm ph}^+" display={false} />) and{" "}
                <span className="text-[var(--retrograde)] font-medium">retrograde</span> (
                <MathBlock math="r_{\rm ph}^-" display={false} />) equatorial photon radii, with
                non-zero Carter constant <MathBlock math="\mathcal{Q}" display={false} /> for
                off-equatorial orbits.
              </li>
              <li>
                <strong className="text-[var(--foreground)] font-medium">Critical curve:</strong>{" "}
                Backward-traced null rays from a distant observer at polar inclination{" "}
                <MathBlock math="\theta_o" display={false} /> that asymptotically approach this
                photon region trace a closed critical curve{" "}
                <MathBlock math="(\alpha, \beta)" display={false} /> on the celestial screen,
                separating captured rays from rays that scatter back to infinity.
              </li>
              <li>
                <strong className="text-[var(--foreground)] font-medium">Observed shadow:</strong>{" "}
                The apparent capture region enclosed by the critical curve. Its silhouette is
                circular only for Schwarzschild (<MathBlock math="a = 0" display={false} />) or
                polar observers (<MathBlock math="\theta_o = 0, \pi" display={false} />); for
                spinning black holes viewed off-axis, frame dragging shifts and flattens the
                prograde edge. Astrophysical images also depend on surrounding emission geometry,
                which is outside this analytical boundary model.
              </li>
            </ul>

            <div className="py-2">
              <MathBlock
                math="\alpha = -\frac{\xi}{\sin\theta_o}, \qquad \beta = \pm\sqrt{\eta + a^2 \cos^2\theta_o - \xi^2 \cot^2\theta_o}"
                display={true}
              />
            </div>
            <p className="text-sm font-sans text-[var(--muted)] leading-relaxed">
              Here <MathBlock math="\xi = L_z / E" display={false} /> and{" "}
              <MathBlock math="\eta = \mathcal{Q} / E^2" display={false} /> are the reduced
              impact parameters along the admissible family of unstable spherical photon orbits.
            </p>
          </div>
        </section>

        {/* 3. Where to go next */}
        <section className="grid grid-cols-1 md:grid-cols-3 gap-6 border-t border-[var(--border)] pt-8">
          <Link
            href="/mathematics"
            className="group block border-t border-[var(--border)] pt-4 space-y-1.5"
          >
            <div className="font-serif text-lg text-[var(--foreground)] group-hover:text-[var(--accent)] flex items-center justify-between">
              <span>Mathematics</span>
              <ArrowRight className="h-4 w-4 text-[var(--muted)] group-hover:text-[var(--accent)]" />
            </div>
            <p className="text-xs font-sans text-[var(--muted)] leading-relaxed">
              Boyer–Lindquist metric, Hamilton&apos;s equations, and conserved quantities{" "}
              <MathBlock math="(E, L_z, \mathcal{Q})" display={false} />.
            </p>
          </Link>

          <Link
            href="/docs#shadows"
            className="group block border-t border-[var(--border)] pt-4 space-y-1.5"
          >
            <div className="font-serif text-lg text-[var(--foreground)] group-hover:text-[var(--accent)] flex items-center justify-between">
              <span>API Reference</span>
              <ArrowRight className="h-4 w-4 text-[var(--muted)] group-hover:text-[var(--accent)]" />
            </div>
            <p className="text-xs font-sans text-[var(--muted)] leading-relaxed">
              Request parameters, validation rules, and JSON schema for{" "}
              <span className="font-mono">POST /api/v1/shadows</span>.
            </p>
          </Link>

          <Link
            href="/explorer"
            className="group block border-t border-[var(--border)] pt-4 space-y-1.5"
          >
            <div className="font-serif text-lg text-[var(--foreground)] group-hover:text-[var(--accent)] flex items-center justify-between">
              <span>Geodesic Explorer</span>
              <ArrowRight className="h-4 w-4 text-[var(--muted)] group-hover:text-[var(--accent)]" />
            </div>
            <p className="text-xs font-sans text-[var(--muted)] leading-relaxed">
              Run live numerical integrations of equatorial Kerr and Schwarzschild trajectories.
            </p>
          </Link>
        </section>
      </div>
    </div>
  );
}
