import { buildRouteMetadata } from "@/lib/metadata";

export const metadata = buildRouteMetadata({
  title: "About",
  description:
    "Background, numerical approach, implemented scope, references, citation, and MIT license for Kerr Geodesics Lab.",
  path: "/about",
});

export default function AboutLayout({ children }: { children: React.ReactNode }) {
  return children;
}
