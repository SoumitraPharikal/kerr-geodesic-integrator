import React from "react";

interface NumericalReadoutProps {
  label: string;
  value: string | number;
  unit?: string;
  uncertainty?: string;
  subtext?: string;
  highlight?: boolean;
  className?: string;
}

export function NumericalReadout({
  label,
  value,
  unit,
  uncertainty,
  subtext,
  highlight = false,
  className = "",
}: NumericalReadoutProps) {
  return (
    <div
      className={`rounded-sm border p-3 transition-colors ${
        highlight
          ? "border-[var(--accent-border)] bg-[var(--accent-light)]"
          : "border-[var(--border)] bg-[var(--surface-subtle)]"
      } ${className}`}
    >
      <div className="flex items-center justify-between text-[11px] text-[var(--muted)] font-sans tracking-wide uppercase">
        <span>{label}</span>
        {uncertainty && (
          <span className="font-mono text-[10px] text-[var(--muted-light)]">
            {uncertainty}
          </span>
        )}
      </div>
      <div className="mt-1 flex items-baseline gap-1.5 font-mono">
        <span
          className={`text-base sm:text-lg font-semibold tracking-tight ${
            highlight ? "text-[var(--accent)]" : "text-[var(--foreground)]"
          }`}
        >
          {value}
        </span>
        {unit && (
          <span className="text-xs text-[var(--muted)] font-sans font-normal">
            {unit}
          </span>
        )}
      </div>
      {subtext && (
        <div className="mt-1 text-[11px] text-[var(--muted)] font-sans leading-tight">
          {subtext}
        </div>
      )}
    </div>
  );
}

export default NumericalReadout;
