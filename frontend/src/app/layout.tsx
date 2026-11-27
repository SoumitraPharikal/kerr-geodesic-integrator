import type { Metadata, Viewport } from "next";
import { Newsreader, Hanken_Grotesk, IBM_Plex_Mono } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import { ThemeProvider } from "@/context/ThemeContext";

const SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL?.replace(/\/+$/, "") ||
  "https://kerr-geodesic-integrator.vercel.app";

const newsreader = Newsreader({
  variable: "--font-newsreader",
  subsets: ["latin"],
  style: ["normal", "italic"],
  display: "swap",
});

const hankenGrotesk = Hanken_Grotesk({
  variable: "--font-hanken-grotesk",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  display: "swap",
});

const ibmPlexMono = IBM_Plex_Mono({
  variable: "--font-ibm-plex-mono",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  display: "swap",
});

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#EEF0F2" },
    { media: "(prefers-color-scheme: dark)", color: "#0B1016" },
  ],
};

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: "Kerr Geodesics Lab",
    template: "%s — Kerr Geodesics Lab",
  },
  description:
    "Numerical integration of timelike and null geodesics in Kerr and Schwarzschild spacetimes via canonical Hamiltonian equations.",
  alternates: {
    canonical: "/",
  },
  icons: {
    icon: "/favicon.svg",
  },
  openGraph: {
    type: "website",
    url: SITE_URL,
    siteName: "Kerr Geodesics Lab",
    title: "Kerr Geodesics Lab",
    description:
      "Numerical integration of timelike and null geodesics in Kerr and Schwarzschild spacetimes via canonical Hamiltonian equations.",
    images: [
      {
        url: `${SITE_URL}/og-image.png`,
        width: 1200,
        height: 630,
        alt: "Kerr Geodesics Lab — Relativistic Geodesic Integrator",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Kerr Geodesics Lab",
    description:
      "Numerical integration of timelike and null geodesics in Kerr and Schwarzschild spacetimes via canonical Hamiltonian equations.",
    images: [`${SITE_URL}/og-image.png`],
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      data-theme="light"
      className={`${newsreader.variable} ${hankenGrotesk.variable} ${ibmPlexMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-[var(--background)] text-[var(--foreground)] selection:bg-[var(--accent)] selection:text-white">
        <ThemeProvider>
          <Navbar />
          <main className="flex-1 flex flex-col">{children}</main>
          <Footer />
        </ThemeProvider>
      </body>
    </html>
  );
}
