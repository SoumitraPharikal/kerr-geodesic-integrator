import React from "react";

interface DerivationToggleProps {
  summary: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
  className?: string;
}

export function DerivationToggle({
  summary,
  children,
  defaultOpen = false,
  className = "",
}: DerivationToggleProps) {
  return (
    <details
      open={defaultOpen}
      className={`border-y border-[var(--border-subtle)] py-2.5 text-sm font-sans ${className}`}
    >
      <summary className="cursor-pointer select-none font-medium text-[var(--foreground-secondary)] hover:text-[var(--foreground)] py-1">
        {summary}
      </summary>
      <div className="pt-3 pb-1 text-[var(--foreground-secondary)] space-y-3">{children}</div>
    </details>
  );
}

export default DerivationToggle;
