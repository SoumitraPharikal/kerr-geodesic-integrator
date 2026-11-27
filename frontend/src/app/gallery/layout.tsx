import { buildRouteMetadata } from "@/lib/metadata";

export const metadata = buildRouteMetadata({
  title: "Gallery",
  description:
    "Seven recorded geodesic presets across Schwarzschild and Kerr spacetimes with trajectory plots and invariant diagnostics.",
  path: "/gallery",
});

export default function GalleryLayout({ children }: { children: React.ReactNode }) {
  return children;
}
