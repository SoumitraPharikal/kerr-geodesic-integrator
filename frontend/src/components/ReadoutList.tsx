"use client";

import React, { useState } from "react";
import { Check, Copy } from "lucide-react";

export interface ReadoutItem {
  label: string;
  value: string | number;
  unit?: string;
  tone?: "default" | "prograde" | "retrograde" | "ok" | "warn" | "error";
  copyValue?: string;
}

interface ReadoutListProps {
  items: ReadoutItem[];
  className?: string;
}

export function ReadoutList({ items, className = "" }: ReadoutListProps) {
  const [copiedIdx, setCopiedIdx] = useState<number | null>(null);

  const handleCopy = (idx: number, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedIdx(idx);
    setTimeout(() => setCopiedIdx(null), 1800);
  };

  const toneClass = (tone?: ReadoutItem["tone"]) => {
    switch (tone) {
      case "prograde":
        return "text-[var(--prograde)]";
      case "retrograde":
        return "text-[var(--retrograde)]";
      case "ok":
        return "text-[var(--status-ok)]";
      case "warn":
        return "text-[var(--status-warn)]";
      case "error":
        return "text-[var(--status-error)]";
      default:
        return "text-[var(--foreground)]";
    }
  };

  return (
    <dl className={`divide-y divide-[var(--border-subtle)] text-[13px] font-sans ${className}`}>
      {items.map((item, idx) => (
        <div key={`${item.label}-${idx}`} className="py-2 flex items-baseline justify-between gap-4">
          <dt className="text-[var(--foreground-secondary)]">{item.label}</dt>
          <dd className="flex items-center gap-1.5 text-right tabular-nums">
            <span className={`font-medium ${toneClass(item.tone)}`}>{item.value}</span>
            {item.unit && <span className="text-[var(--muted)]">{item.unit}</span>}
            {item.copyValue && (
              <button
                type="button"
                onClick={() => handleCopy(idx, item.copyValue!)}
                aria-label={`Copy ${item.label}`}
                title={`Copy ${item.label}`}
                className="p-1 text-[var(--muted)] hover:text-[var(--foreground)] rounded-[2px] cursor-pointer"
              >
                {copiedIdx === idx ? (
                  <Check className="h-3.5 w-3.5 text-[var(--status-ok)]" />
                ) : (
                  <Copy className="h-3.5 w-3.5" />
                )}
              </button>
            )}
          </dd>
        </div>
      ))}
    </dl>
  );
}

export default ReadoutList;
