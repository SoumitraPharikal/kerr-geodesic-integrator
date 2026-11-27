import { buildRouteMetadata } from "@/lib/metadata";

export const metadata = buildRouteMetadata({
  title: "Shadow Lab",
  description:
    "Planned frontend extension for Kerr black-hole shadow boundary visualization (backend analytical solver available at /api/v1/shadows).",
  path: "/shadows",
});

export default function ShadowsLayout({ children }: { children: React.ReactNode }) {
  return children;
}
