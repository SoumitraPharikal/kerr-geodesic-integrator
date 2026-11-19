import React from "react";

interface ScientificPanelProps {
  title?: React.ReactNode;
  subtitle?: React.ReactNode;
  badge?: React.ReactNode;
  action?: React.ReactNode;
  footer?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  bodyClassName?: string;
}

export function ScientificPanel({
  title,
  subtitle,
  badge,
  action,
  footer,
  children,
  className = "",
  bodyClassName = "",
}: ScientificPanelProps) {
  const hasHeader = title || subtitle || badge || action;

  return (
    <div
      className={`rounded-sm border border-[var(--border)] bg-[var(--surface)] shadow-xs transition-colors overflow-hidden ${className}`}
    >
      {hasHeader && (
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--border-subtle)] px-4 py-3 bg-[var(--surface-subtle)]">
          <div className="space-y-0.5">
            <div className="flex items-center gap-2">
              {title && (
                <h3 className="text-sm font-semibold tracking-tight text-[var(--foreground)] font-sans">
                  {title}
                </h3>
              )}
              {badge}
            </div>
            {subtitle && (
              <p className="text-xs text-[var(--muted)] font-sans">{subtitle}</p>
            )}
          </div>
          {action && <div className="flex items-center gap-2">{action}</div>}
        </div>
      )}
      <div className={`p-4 ${bodyClassName}`}>{children}</div>
      {footer && (
        <div className="border-t border-[var(--border-subtle)] bg-[var(--surface-subtle)] px-4 py-2.5 text-xs text-[var(--muted)] font-sans">
          {footer}
        </div>
      )}
    </div>
  );
}

export default ScientificPanel;
