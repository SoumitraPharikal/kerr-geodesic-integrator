import type { Metadata } from "next";

export const SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL?.replace(/\/+$/, "") ||
  "https://kerr-geodesic-integrator.vercel.app";

export function buildRouteMetadata({
  title,
  description,
  path,
}: {
  title: string;
  description: string;
  path: string;
}): Metadata {
  const fullTitle = `${title} — Kerr Geodesics Lab`;
  const ogImageUrl = `${SITE_URL}/og-image.png`;
  return {
    title,
    description,
    alternates: { canonical: path },
    openGraph: {
      type: "website",
      siteName: "Kerr Geodesics Lab",
      title: fullTitle,
      description,
      url: `${SITE_URL}${path}`,
      images: [
        {
          url: ogImageUrl,
          width: 1200,
          height: 630,
          alt: "Kerr Geodesics Lab — Relativistic Geodesic Integrator",
        },
      ],
    },
    twitter: {
      card: "summary_large_image",
      title: fullTitle,
      description,
      images: [ogImageUrl],
    },
  };
}
