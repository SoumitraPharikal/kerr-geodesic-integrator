import React from "react";

interface PageHeaderProps {
  title: string;
  badge?: React.ReactNode;
  subtitle?: string;
  description?: string;
  actions?: React.ReactNode;
  className?: string;
}

export function PageHeader({
  title,
  badge,
  subtitle,
  description,
  actions,
  className = "",
}: PageHeaderProps) {
  return (
    <header className={`border-b border-[var(--border)] bg-[var(--surface)]/80 backdrop-blur-xs py-8 px-4 sm:px-6 lg:px-8 transition-colors ${className}`}>
      <div className="mx-auto max-w-7xl">
        <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
          <div className="max-w-3xl">
            {badge && <div className="mb-2.5">{badge}</div>}
            <h1 className="text-3xl sm:text-4xl font-serif font-normal tracking-tight text-[var(--foreground)]">
              {title}
            </h1>
            {subtitle && (
              <p className="mt-1 text-base text-[var(--accent)] font-serif italic">
                {subtitle}
              </p>
            )}
            {description && (
              <p className="mt-2 text-sm leading-relaxed text-[var(--muted)] font-sans max-w-2xl">
                {description}
              </p>
            )}
          </div>
          {actions && <div className="flex items-center gap-3 shrink-0">{actions}</div>}
        </div>
      </div>
    </header>
  );
}

export default PageHeader;
