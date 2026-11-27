import { buildRouteMetadata } from "@/lib/metadata";

export const metadata = buildRouteMetadata({
  title: "Explorer",
  description:
    "Interactive geodesic integrator for Schwarzschild and Kerr spacetimes with conserved-quantity diagnostics and event detection.",
  path: "/explorer",
});

export default function ExplorerLayout({ children }: { children: React.ReactNode }) {
  return children;
}
