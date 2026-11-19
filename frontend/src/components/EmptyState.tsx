import React from "react";
import { Info } from "lucide-react";

interface EmptyStateProps {
  title: string;
  description: string;
  badge?: string;
  roadmapNotice?: string;
  action?: React.ReactNode;
  icon?: React.ReactNode;
  className?: string;
}

export function EmptyState({
  title,
  description,
  badge,
  roadmapNotice,
  action,
  icon,
  className = "",
}: EmptyStateProps) {
  return (
    <div
      className={`rounded-sm border border-dashed border-[var(--border)] bg-[var(--surface-subtle)]/70 p-8 text-center transition-colors ${className}`}
    >
      <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-sm bg-[var(--surface)] text-[var(--accent)] border border-[var(--border)] shadow-xs">
        {icon || <Info className="h-5 w-5" />}
      </div>
      {badge && (
        <span className="mt-3 inline-block rounded-xs bg-[var(--accent-light)] px-2 py-0.5 font-mono text-[10px] text-[var(--accent)] border border-[var(--accent-border)] uppercase tracking-wider font-semibold">
          {badge}
        </span>
      )}
      <h3 className="mt-2.5 text-base font-serif font-medium text-[var(--foreground)]">
        {title}
      </h3>
      <p className="mx-auto mt-1 max-w-md text-xs leading-relaxed text-[var(--muted)] font-sans">
        {description}
      </p>
      {roadmapNotice && (
        <div className="mx-auto mt-4 max-w-lg rounded-sm border border-[var(--accent-border)] bg-[var(--accent-light)] p-2.5 text-left text-xs text-[var(--foreground)] font-sans">
          <div className="flex items-start gap-2">
            <span className="font-mono text-[10px] font-bold text-[var(--accent)] uppercase tracking-wider shrink-0 mt-0.5">
              Architectural Guard:
            </span>
            <span className="text-[var(--muted)] text-[11px] leading-relaxed">{roadmapNotice}</span>
          </div>
        </div>
      )}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

export default EmptyState;
