"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu, X, Sun, Moon } from "lucide-react";
import { useTheme } from "@/context/ThemeContext";
import { ensureBackendReady, isBackendAwake } from "@/lib/api";

interface NavItem {
  name: string;
  href: string;
}

const INSTRUMENT_ITEMS: NavItem[] = [
  { name: "Explorer", href: "/explorer" },
  { name: "Gallery", href: "/gallery" },
  { name: "Shadow Lab", href: "/shadows" },
];

const REFERENCE_ITEMS: NavItem[] = [
  { name: "Mathematics", href: "/mathematics" },
  { name: "Validation", href: "/validation" },
  { name: "Docs", href: "/docs" },
  { name: "About", href: "/about" },
];

type EngineStatus = "online" | "waking" | "unreachable";

export function Navbar() {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { theme, toggleTheme } = useTheme();
  const [engineStatus, setEngineStatus] = useState<EngineStatus>(() =>
    isBackendAwake() ? "online" : "waking"
  );

  // Engine status is shown only on routes that actively invoke the Python engine
  const isEngineRoute = pathname.startsWith("/explorer");

  useEffect(() => {
    if (!isEngineRoute) return;

    const controller = new AbortController();
    let active = true;

    if (isBackendAwake()) {
      queueMicrotask(() => {
        if (active) setEngineStatus("online");
      });
    } else {
      queueMicrotask(() => {
        if (active) setEngineStatus("waking");
      });
    }

    ensureBackendReady({ signal: controller.signal })
      .then(() => {
        if (active) setEngineStatus("online");
      })
      .catch(() => {
        if (active && !controller.signal.aborted) {
          setEngineStatus("unreachable");
        }
      });

    return () => {
      active = false;
      controller.abort();
    };
  }, [isEngineRoute, pathname]);

  const isActive = (href: string) => {
    if (href === "/") return pathname === "/";
    return pathname.startsWith(href);
  };

  const statusText =
    engineStatus === "online"
      ? "Engine online, v1.0.0"
      : engineStatus === "waking"
      ? "Waking the engine, this can take a moment"
      : "Engine unreachable";

  const statusDotClass =
    engineStatus === "online"
      ? "bg-[var(--status-ok)]"
      : engineStatus === "waking"
      ? "bg-[var(--status-warn)]"
      : "bg-[var(--status-error)]";

  return (
    <nav
      aria-label="Primary"
      className="sticky top-0 z-40 w-full border-b border-[var(--border)] bg-[var(--surface)] text-[var(--foreground)]"
    >
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8 h-14">
        {/* Brand + Grouped Navigation */}
        <div className="flex items-center gap-7">
          <Link
            href="/"
            className="flex items-center gap-2.5 text-[var(--foreground)] hover:opacity-80"
          >
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.25"
              className="text-[var(--foreground)] shrink-0"
              aria-hidden="true"
            >
              <circle cx="12" cy="12" r="2.25" fill="currentColor" stroke="none" />
              <ellipse cx="12" cy="12" rx="9" ry="3.75" transform="rotate(-25 12 12)" />
              <ellipse
                cx="12"
                cy="12"
                rx="9"
                ry="3.75"
                transform="rotate(35 12 12)"
                strokeDasharray="2 2"
                opacity="0.55"
              />
            </svg>
            <span className="font-serif text-[17px] tracking-tight font-normal text-[var(--foreground)] whitespace-nowrap">
              Kerr Geodesics Lab
            </span>
          </Link>

          {/* Desktop Navigation: Instruments | Reference */}
          <div className="hidden lg:flex items-center gap-5">
            <div className="flex items-center gap-4" aria-label="Instruments">
              {INSTRUMENT_ITEMS.map((item) => {
                const active = isActive(item.href);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    aria-current={active ? "page" : undefined}
                    className={`py-1 text-[13px] font-sans border-b-2 ${
                      active
                        ? "border-[var(--foreground)] text-[var(--foreground)] font-medium"
                        : "border-transparent text-[var(--foreground-secondary)] hover:text-[var(--foreground)]"
                    }`}
                  >
                    {item.name}
                  </Link>
                );
              })}
            </div>

            <div className="h-3.5 w-px bg-[var(--border)]" aria-hidden="true" />

            <div className="flex items-center gap-4" aria-label="Reference">
              {REFERENCE_ITEMS.map((item) => {
                const active = isActive(item.href);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    aria-current={active ? "page" : undefined}
                    className={`py-1 text-[13px] font-sans border-b-2 ${
                      active
                        ? "border-[var(--foreground)] text-[var(--foreground)] font-medium"
                        : "border-transparent text-[var(--foreground-secondary)] hover:text-[var(--foreground)]"
                    }`}
                  >
                    {item.name}
                  </Link>
                );
              })}
            </div>
          </div>
        </div>

        {/* Desktop Right Controls (>=1024px): Engine status (only where active) + Theme Toggle */}
        <div className="hidden lg:flex items-center gap-3">
          {isEngineRoute && (
            <>
              <div
                className="flex items-center gap-2 text-xs font-sans text-[var(--foreground-secondary)]"
                role="status"
                aria-live="polite"
              >
                <span className={`h-2 w-2 rounded-full shrink-0 ${statusDotClass}`} aria-hidden="true" />
                <span className="whitespace-nowrap">{statusText}</span>
              </div>
              <div className="h-3.5 w-px bg-[var(--border)]" aria-hidden="true" />
            </>
          )}

          <button
            type="button"
            onClick={toggleTheme}
            className="flex h-7 w-7 items-center justify-center rounded-[2px] text-[var(--foreground-secondary)] hover:text-[var(--foreground)] hover:bg-[var(--surface-hover)] cursor-pointer"
            aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}
            title={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}
          >
            {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </button>
        </div>

        {/* Mobile / Tablet Controls (<1024px): Single Theme Toggle + Menu Trigger */}
        <div className="flex lg:hidden items-center gap-2">
          <button
            type="button"
            onClick={toggleTheme}
            className="flex h-7 w-7 items-center justify-center rounded-[2px] text-[var(--foreground-secondary)] hover:text-[var(--foreground)] cursor-pointer"
            aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}
          >
            {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </button>

          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="flex h-7 w-7 items-center justify-center rounded-[2px] text-[var(--foreground-secondary)] hover:text-[var(--foreground)] cursor-pointer"
            aria-expanded={mobileMenuOpen}
            aria-label="Toggle navigation menu"
          >
            {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {/* Mobile / Tablet Dropdown Menu (<1024px) */}
      {mobileMenuOpen && (
        <div className="lg:hidden border-t border-[var(--border)] bg-[var(--surface)] px-4 py-4 space-y-4">
          <div className="space-y-1">
            <div className="px-2 text-[11px] font-sans font-medium uppercase tracking-wider text-[var(--muted)]">
              Instruments
            </div>
            {INSTRUMENT_ITEMS.map((item) => {
              const active = isActive(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMobileMenuOpen(false)}
                  aria-current={active ? "page" : undefined}
                  className={`block px-2 py-1.5 text-sm font-sans ${
                    active
                      ? "font-medium text-[var(--foreground)] underline underline-offset-4"
                      : "text-[var(--foreground-secondary)] hover:text-[var(--foreground)]"
                  }`}
                >
                  {item.name}
                </Link>
              );
            })}
          </div>

          <div className="space-y-1 border-t border-[var(--border-subtle)] pt-3">
            <div className="px-2 text-[11px] font-sans font-medium uppercase tracking-wider text-[var(--muted)]">
              Reference
            </div>
            {REFERENCE_ITEMS.map((item) => {
              const active = isActive(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMobileMenuOpen(false)}
                  aria-current={active ? "page" : undefined}
                  className={`block px-2 py-1.5 text-sm font-sans ${
                    active
                      ? "font-medium text-[var(--foreground)] underline underline-offset-4"
                      : "text-[var(--foreground-secondary)] hover:text-[var(--foreground)]"
                  }`}
                >
                  {item.name}
                </Link>
              );
            })}
          </div>

          {isEngineRoute && (
            <div className="pt-3 border-t border-[var(--border-subtle)] flex items-center gap-2 text-xs font-sans text-[var(--foreground-secondary)] px-2">
              <span className={`h-2 w-2 rounded-full shrink-0 ${statusDotClass}`} aria-hidden="true" />
              <span>{statusText}</span>
            </div>
          )}
        </div>
      )}
    </nav>
  );
}

export default Navbar;
