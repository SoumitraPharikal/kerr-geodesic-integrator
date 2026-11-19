import type { Metadata } from "next";
import { Newsreader, IBM_Plex_Sans, IBM_Plex_Mono } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import { ThemeProvider } from "@/context/ThemeContext";

const newsreader = Newsreader({
  variable: "--font-newsreader",
  subsets: ["latin"],
  style: ["normal", "italic"],
});

const ibmPlexSans = IBM_Plex_Sans({
  variable: "--font-ibm-plex-sans",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

const ibmPlexMono = IBM_Plex_Mono({
  variable: "--font-ibm-plex-mono",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
});

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000"),
  title: "Kerr Geodesics Lab",
  description:
    "Numerical integration of timelike and null geodesics in Kerr and Schwarzschild spacetimes via canonical Hamiltonian equations.",
  icons: {
    icon: "/favicon.svg",
  },
  openGraph: {
    title: "Kerr Geodesics Lab",
    description:
      "Numerical integration of timelike and null geodesics in Kerr and Schwarzschild spacetimes via canonical Hamiltonian equations.",
    images: [
      {
        url: "/og-image.png",
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
    images: ["/og-image.png"],
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
      className={`${newsreader.variable} ${ibmPlexSans.variable} ${ibmPlexMono.variable} h-full antialiased`}
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
