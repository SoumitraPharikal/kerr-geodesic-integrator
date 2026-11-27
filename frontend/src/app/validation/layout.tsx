import { buildRouteMetadata } from "@/lib/metadata";

export const metadata = buildRouteMetadata({
  title: "Validation",
  description:
    "Recorded validation baseline, per-preset Hamiltonian drift measurements, solver diagnostics, and scope limitations.",
  path: "/validation",
});

export default function ValidationLayout({ children }: { children: React.ReactNode }) {
  return children;
}
