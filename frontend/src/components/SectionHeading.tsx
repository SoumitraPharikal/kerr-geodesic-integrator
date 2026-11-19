import React from "react";

interface SectionHeadingProps {
  number?: string;
  title: string;
  subtitle?: string;
  className?: string;
}

export function SectionHeading({
  number,
  title,
  subtitle,
  className = "",
}: SectionHeadingProps) {
  return (
    <div className={`border-b border-[var(--border)] pb-2 mb-4 ${className}`}>
      <div className="flex items-baseline gap-2">
        {number && (
          <span className="font-mono text-xs font-semibold text-[var(--accent)] tracking-wider">
            §{number}
          </span>
        )}
        <h2 className="text-xl sm:text-2xl font-serif font-normal text-[var(--foreground)] tracking-tight">
          {title}
        </h2>
      </div>
      {subtitle && (
        <p className="mt-1 text-xs text-[var(--muted)] font-sans">{subtitle}</p>
      )}
    </div>
  );
}

export default SectionHeading;
