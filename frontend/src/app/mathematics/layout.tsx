import { buildRouteMetadata } from "@/lib/metadata";

export const metadata = buildRouteMetadata({
  title: "Mathematics",
  description:
    "Boyer–Lindquist metric, canonical Hamiltonian formulation, Killing symmetries, Carter constant, and numerical event detection.",
  path: "/mathematics",
});

export default function MathematicsLayout({ children }: { children: React.ReactNode }) {
  return children;
}
