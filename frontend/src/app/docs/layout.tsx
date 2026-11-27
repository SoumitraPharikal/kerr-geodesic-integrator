import { buildRouteMetadata } from "@/lib/metadata";

export const metadata = buildRouteMetadata({
  title: "Docs",
  description:
    "FastAPI HTTP API reference, request and response schemas, and examples for the Kerr Geodesics Lab backend.",
  path: "/docs",
});

export default function DocsLayout({ children }: { children: React.ReactNode }) {
  return children;
}
