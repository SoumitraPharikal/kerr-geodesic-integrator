import React from "react";

interface MarginNoteProps {
  label?: string;
  children: React.ReactNode;
  className?: string;
}

export function MarginNote({ label, children, className = "" }: MarginNoteProps) {
  return (
    <aside
      className={`border-l-2 border-[var(--border)] pl-3.5 py-0.5 text-[13px] font-sans text-[var(--muted)] leading-relaxed ${className}`}
    >
      {label && (
        <div className="text-[11px] font-medium uppercase tracking-wider text-[var(--foreground-secondary)] mb-1">
          {label}
        </div>
      )}
      <div>{children}</div>
    </aside>
  );
}

export default MarginNote;
