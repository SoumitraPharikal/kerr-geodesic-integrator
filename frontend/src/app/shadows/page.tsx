"use client";

import React from "react";
import Link from "next/link";
import { Compass, ArrowRight } from "lucide-react";

export default function ShadowsPage() {
  return (
    <div className="flex flex-col flex-1 pb-20">
      <div className="border-b border-[var(--border)] py-8 px-4 sm:px-6 lg:px-8 bg-[var(--surface)]">
        <div className="mx-auto max-w-4xl">
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-[3px] border border-[var(--border)] bg-[var(--surface-subtle)] text-xs font-mono text-[var(--muted)] mb-3">
            <span>In Development</span>
            <span className="text-[var(--border)]">·</span>
            <span>Planned Extension</span>
          </div>

          <h1 className="font-serif text-2xl sm:text-3xl lg:text-4xl font-normal text-[var(--foreground)] tracking-tight">
            Black Hole Shadow Lab
          </h1>
          <p className="text-xs sm:text-sm text-[var(--muted)] font-sans mt-2 max-w-2xl leading-relaxed">
            Interactive visualization of Bardeen celestial coordinates and analytical Kerr black hole shadow boundaries via the validated Python engine is currently in development.
          </p>
        </div>
      </div>

      <div className="mx-auto max-w-4xl w-full px-4 sm:px-6 lg:px-8 mt-12">
        <div className="rounded-[4px] border border-[var(--border)] bg-[var(--surface)] p-8 text-center space-y-4 shadow-xs">
          <p className="text-xs sm:text-sm text-[var(--muted)] font-sans max-w-md mx-auto leading-relaxed">
            In accordance with our scientific architecture principles, the browser does not independently compute general relativistic shadow physics. The shadow interface will be activated when wired directly to the engine&apos;s analytical boundary solver.
          </p>

          <div className="pt-2">
            <Link
              href="/explorer"
              className="inline-flex items-center gap-2 rounded-[3px] bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white px-4 py-2 text-xs font-sans font-medium transition-colors cursor-pointer shadow-xs"
            >
              <Compass className="h-4 w-4" />
              <span>Launch Geodesic Explorer</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
