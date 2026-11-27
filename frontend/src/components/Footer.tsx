import React from "react";
import Link from "next/link";

const REPO_URL = "https://github.com/SoumitraPharikal/kerr-geodesic-integrator";
const RELEASE_TAG = "v1.0.0";
const RELEASE_COMMIT_SHORT = "062b20c";
const RELEASE_COMMIT_FULL = "062b20c80a689640637a2fcd003bdd921a7d4132";

export function Footer() {
  return (
    <footer className="mt-auto border-t border-[var(--border)] bg-[var(--surface)] py-10 text-[var(--foreground-secondary)] font-sans text-xs">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-8">
          <div className="md:col-span-6 space-y-2">
            <div className="font-serif text-[17px] font-normal text-[var(--foreground)]">
              Kerr Geodesics Lab
            </div>
            <p className="text-[13px] text-[var(--foreground-secondary)] max-w-md leading-relaxed">
              Numerical geodesic integration in Schwarzschild and Kerr spacetimes via canonical Hamiltonian equations.
            </p>
          </div>

          <div className="md:col-span-3 space-y-2">
            <div className="text-[11px] font-medium uppercase tracking-wider text-[var(--muted)]">
              Instruments
            </div>
            <ul className="space-y-1.5 text-[13px]">
              <li>
                <Link href="/" className="hover:text-[var(--foreground)]">
                  Home
                </Link>
              </li>
              <li>
                <Link href="/explorer" className="hover:text-[var(--foreground)]">
                  Explorer
                </Link>
              </li>
              <li>
                <Link href="/gallery" className="hover:text-[var(--foreground)]">
                  Gallery
                </Link>
              </li>
              <li>
                <Link href="/shadows" className="hover:text-[var(--foreground)]">
                  Shadow Lab
                </Link>
              </li>
            </ul>
          </div>

          <div className="md:col-span-3 space-y-2">
            <div className="text-[11px] font-medium uppercase tracking-wider text-[var(--muted)]">
              Reference
            </div>
            <ul className="space-y-1.5 text-[13px]">
              <li>
                <Link href="/mathematics" className="hover:text-[var(--foreground)]">
                  Mathematics
                </Link>
              </li>
              <li>
                <Link href="/validation" className="hover:text-[var(--foreground)]">
                  Validation
                </Link>
              </li>
              <li>
                <Link href="/docs" className="hover:text-[var(--foreground)]">
                  Docs
                </Link>
              </li>
              <li>
                <Link href="/about" className="hover:text-[var(--foreground)]">
                  About
                </Link>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-8 pt-5 border-t border-[var(--border-subtle)] flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs text-[var(--muted)] tabular-nums">
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
            <span>Soumitra Pharikal</span>
            <a
              href={REPO_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-[var(--foreground)] underline underline-offset-2"
            >
              GitHub
            </a>
            <a
              href={`${REPO_URL}/blob/master/LICENSE`}
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-[var(--foreground)] underline underline-offset-2"
            >
              MIT License
            </a>
          </div>

          <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
            <span>Results last recorded 2026-11-19</span>
            <a
              href={`${REPO_URL}/releases/tag/${RELEASE_TAG}`}
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-[var(--foreground)] underline underline-offset-2"
            >
              Release {RELEASE_TAG}
            </a>
            <a
              href={`${REPO_URL}/commit/${RELEASE_COMMIT_FULL}`}
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-[var(--foreground)] underline underline-offset-2"
            >
              Commit {RELEASE_COMMIT_SHORT}
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}

export default Footer;
