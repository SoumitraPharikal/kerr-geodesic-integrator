import React from "react";

export type StatusVariant = "validated" | "ready" | "prototype" | "active" | "info" | "immutable";

interface StatusIndicatorProps {
  status: StatusVariant;
  label?: string;
  size?: "sm" | "md";
  className?: string;
}

const variantStyles: Record<
  StatusVariant,
  { bg: string; text: string; border: string; dot: string; defaultLabel: string }
> = {
  validated: {
    bg: "bg-[var(--emerald-light)]",
    text: "text-[var(--emerald)]",
    border: "border-emerald-500/30",
    dot: "bg-emerald-400",
    defaultLabel: "Validated v1.0.0",
  },
  ready: {
    bg: "bg-[var(--accent-light)]",
    text: "text-[var(--accent)]",
    border: "border-[var(--accent-border)]",
    dot: "bg-amber-400",
    defaultLabel: "Stateless API Ready",
  },
  prototype: {
    bg: "bg-[var(--cyan-light)]",
    text: "text-[var(--cyan)]",
    border: "border-cyan-500/30",
    dot: "bg-cyan-400",
    defaultLabel: "Illustrative Preview",
  },
  active: {
    bg: "bg-[var(--crimson-light)]",
    text: "text-[var(--crimson)]",
    border: "border-[var(--crimson-border)]",
    dot: "bg-rose-500",
    defaultLabel: "Live Simulation Active",
  },
  immutable: {
    bg: "bg-[var(--surface-subtle)]",
    text: "text-[var(--muted)]",
    border: "border-[var(--border)]",
    dot: "bg-zinc-500",
    defaultLabel: "Immutable Release",
  },
  info: {
    bg: "bg-[var(--surface-subtle)]",
    text: "text-[var(--muted)]",
    border: "border-[var(--border)]",
    dot: "bg-zinc-400",
    defaultLabel: "Information",
  },
};

export function StatusIndicator({
  status,
  label,
  size = "sm",
  className = "",
}: StatusIndicatorProps) {
  const conf = variantStyles[status] || variantStyles.info;
  const displayLabel = label || conf.defaultLabel;

  const sizeClasses = size === "sm" ? "px-2 py-0.5 text-xs" : "px-2.5 py-1 text-xs font-medium";

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-sm border font-mono tracking-tight transition-colors ${conf.bg} ${conf.text} ${conf.border} ${sizeClasses} ${className}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${conf.dot}`} aria-hidden="true" />
      <span>{displayLabel}</span>
    </span>
  );
}

export default StatusIndicator;
