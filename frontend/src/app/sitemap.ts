import type { MetadataRoute } from "next";

const SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL?.replace(/\/+$/, "") ||
  "https://kerr-geodesic-integrator.vercel.app";

export default function sitemap(): MetadataRoute.Sitemap {
  const routes = [
    "",
    "/explorer",
    "/gallery",
    "/shadows",
    "/mathematics",
    "/validation",
    "/docs",
    "/about",
  ];

  return routes.map((route) => ({
    url: `${SITE_URL}${route}`,
    changeFrequency: "monthly",
    priority: route === "" ? 1.0 : 0.8,
  }));
}
