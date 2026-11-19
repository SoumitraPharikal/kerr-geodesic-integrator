import React from "react";
import Link from "next/link";

export function Footer() {
  return (
    <footer className="mt-auto border-t border-[var(--border)] bg-[var(--surface)] py-8 text-[var(--foreground-secondary)] font-sans text-xs transition-colors">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col sm:flex-row items-baseline justify-between gap-4">
          <div className="space-y-1">
            <div className="font-serif text-[15px] font-normal text-[var(--foreground)]">
              Kerr Geodesics Lab
            </div>
            <p className="text-[13px] text-[var(--foreground-secondary)] max-w-lg leading-relaxed">
              Numerical geodesic integration in Kerr and Schwarzschild spacetimes via canonical Hamiltonian equations.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-[13px] font-sans text-[var(--foreground-secondary)]">
            <Link href="/explorer" className="hover:text-[var(--foreground)] transition-colors">
              Explorer
            </Link>
            <Link href="/mathematics" className="hover:text-[var(--foreground)] transition-colors">
              Mathematics
            </Link>
            <Link href="/validation" className="hover:text-[var(--foreground)] transition-colors">
              Validation
            </Link>
            <Link href="/docs" className="hover:text-[var(--foreground)] transition-colors">
              Docs
            </Link>
            <a
              href="https://github.com/SoumitraPharikal/kerr-geodesic-integrator"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-[var(--foreground)] transition-colors"
            >
              GitHub
            </a>
          </div>
        </div>

        <div className="mt-6 pt-4 border-t border-[var(--border-subtle)] flex flex-col sm:flex-row items-center justify-between text-xs text-[var(--muted)] font-mono gap-2">
          <div>
            An independent project by Soumitra Pharikal · MIT License
          </div>
          <div className="flex items-center gap-4">
            <span>Commit: 062b20c</span>
            <span>Release: v1.0.0</span>
          </div>
        </div>
      </div>
    </footer>
  );
}

export default Footer;
