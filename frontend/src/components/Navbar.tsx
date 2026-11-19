"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu, X, Sun, Moon } from "lucide-react";
import { useTheme } from "@/context/ThemeContext";
import { fetchHealth } from "@/lib/api";

interface NavItem {
  name: string;
  href: string;
}

const NAV_ITEMS: NavItem[] = [
  { name: "Explorer", href: "/explorer" },
  { name: "Orbit Gallery", href: "/gallery" },
  { name: "Shadow Lab", href: "/shadows" },
  { name: "Mathematics", href: "/mathematics" },
  { name: "Validation", href: "/validation" },
  { name: "Docs", href: "/docs" },
  { name: "About", href: "/about" },
];

export function Navbar() {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { theme, toggleTheme } = useTheme();
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);

  useEffect(() => {
    let active = true;
    fetchHealth()
      .then(() => {
        if (active) setApiOnline(true);
      })
      .catch(() => {
        if (active) setApiOnline(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const isActive = (href: string) => {
    if (href === "/") return pathname === "/";
    return pathname.startsWith(href);
  };

  return (
    <nav className="sticky top-0 z-40 w-full border-b border-[var(--border)] bg-[var(--surface)] text-[var(--foreground)] transition-colors">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8 h-14">
        {/* Brand / Logo */}
        <div className="flex items-center gap-6">
          <Link
            href="/"
            className="flex items-center gap-2.5 text-[var(--foreground)] hover:opacity-80 transition-opacity"
          >
            {/* Ink-colored precessing orbit glyph */}
            <svg
              width="22"
              height="22"
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
                opacity="0.5"
              />
            </svg>
            <span className="font-serif text-[17px] tracking-tight font-normal text-[var(--foreground)]">
              Kerr Geodesics Lab
            </span>
          </Link>

          {/* Desktop Navigation Links */}
          <div className="hidden lg:flex items-center space-x-1">
            {NAV_ITEMS.map((item) => {
              const active = isActive(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`px-2.5 py-1 text-[13px] font-sans transition-colors rounded-[3px] ${
                    active
                      ? "text-[var(--foreground)] font-medium bg-[var(--surface-subtle)]"
                      : "text-[var(--foreground-secondary)] hover:text-[var(--foreground)] hover:bg-[var(--surface-hover)]"
                  }`}
                >
                  {item.name}
                </Link>
              );
            })}
          </div>
        </div>

        {/* Right Shell Controls: API status dot + Theme Toggle */}
        <div className="hidden md:flex items-center gap-4">
          {/* Subtle Global API status indicator */}
          <div
            className="flex items-center gap-1.5 text-xs text-[var(--foreground-secondary)] font-sans"
            title={
              apiOnline === true
                ? "Computation Engine: Online (v1.0.0)"
                : apiOnline === false
                ? "Computation Engine: Offline"
                : "Checking engine connection..."
            }
          >
            <span
              className={`h-2 w-2 rounded-full ${
                apiOnline === true
                  ? "bg-emerald-600 dark:bg-emerald-400"
                  : apiOnline === false
                  ? "bg-red-600 dark:bg-red-400"
                  : "bg-amber-600 dark:bg-amber-400"
              }`}
              aria-hidden="true"
            />
            <span className="text-[12px] font-mono text-[var(--foreground-secondary)]">
              {apiOnline === true ? "Engine v1.0.0" : apiOnline === false ? "Engine Offline" : "Connecting"}
            </span>
          </div>

          <div className="h-3.5 w-px bg-[var(--border)]" aria-hidden="true" />

          {/* Theme Toggle Button */}
          <button
            type="button"
            onClick={toggleTheme}
            className="flex h-7 w-7 items-center justify-center rounded-[3px] text-[var(--foreground-secondary)] hover:text-[var(--foreground)] hover:bg-[var(--surface-hover)] transition-colors focus:outline-none cursor-pointer"
            aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}
            title={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}
          >
            {theme === "dark" ? (
              <Sun className="h-4 w-4" />
            ) : (
              <Moon className="h-4 w-4" />
            )}
          </button>
        </div>

        {/* Mobile menu trigger */}
        <div className="flex lg:hidden items-center gap-2">
          <button
            type="button"
            onClick={toggleTheme}
            className="p-1 text-[var(--muted)] hover:text-[var(--foreground)]"
            aria-label="Toggle theme"
          >
            {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </button>

          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-1 text-[var(--muted)] hover:text-[var(--foreground)] focus:outline-none"
            aria-expanded={mobileMenuOpen}
            aria-label="Toggle navigation menu"
          >
            {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Menu Dropdown */}
      {mobileMenuOpen && (
        <div className="lg:hidden border-t border-[var(--border)] bg-[var(--surface)] px-4 py-3 space-y-1">
          {NAV_ITEMS.map((item) => {
            const active = isActive(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setMobileMenuOpen(false)}
                className={`block rounded-[3px] px-3 py-1.5 text-sm font-sans ${
                  active
                    ? "font-medium text-[var(--foreground)] bg-[var(--surface-subtle)]"
                    : "text-[var(--muted)] hover:text-[var(--foreground)]"
                }`}
              >
                {item.name}
              </Link>
            );
          })}
          <div className="pt-2 border-t border-[var(--border-subtle)] mt-2 flex items-center justify-between text-xs font-mono text-[var(--muted)] px-3">
            <span>Status:</span>
            <span>{apiOnline ? "Engine v1.0.0 Online" : "Engine Offline"}</span>
          </div>
        </div>
      )}
    </nav>
  );
}

export default Navbar;
