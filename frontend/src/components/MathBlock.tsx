"use client";

import React, { useState } from "react";
import katex from "katex";
import { Check, Copy } from "lucide-react";

interface MathBlockProps {
  math: string;
  display?: boolean;
  className?: string;
  ariaLabel?: string;
  number?: string;
  id?: string;
}

export function MathBlock({
  math,
  display = true,
  className = "",
  ariaLabel,
  number,
  id,
}: MathBlockProps) {
  const [copied, setCopied] = useState(false);

  let html = "";
  try {
    html = katex.renderToString(math, {
      displayMode: display,
      throwOnError: false,
      output: "htmlAndMathml",
    });
  } catch (err) {
    console.error("KaTeX error:", err);
    html = `<code class="text-[var(--status-error)] font-mono text-xs">${math}</code>`;
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(math);
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  };

  if (display) {
    return (
      <div
        id={id}
        className={`group relative my-4 flex items-center justify-between gap-4 border-y border-[var(--border-subtle)] bg-[var(--surface)]/50 px-3 py-2 ${className}`}
      >
        <div
          className="flex-1 overflow-x-auto py-1 text-center font-serif text-[var(--foreground)]"
          aria-label={ariaLabel || math}
          dangerouslySetInnerHTML={{ __html: html }}
        />
        <div className="flex items-center gap-2 shrink-0">
          {number && (
            <a
              href={id ? `#${id}` : undefined}
              className="text-xs font-sans text-[var(--muted)] hover:text-[var(--foreground)] tabular-nums"
              aria-label={`Equation ${number}`}
            >
              ({number})
            </a>
          )}
          <button
            type="button"
            onClick={handleCopy}
            aria-label="Copy LaTeX"
            title="Copy LaTeX"
            className="opacity-0 group-hover:opacity-100 focus:opacity-100 focus-visible:opacity-100 p-1 text-[var(--muted)] hover:text-[var(--foreground)] rounded-[2px] cursor-pointer"
          >
            {copied ? (
              <Check className="h-3.5 w-3.5 text-[var(--status-ok)]" />
            ) : (
              <Copy className="h-3.5 w-3.5" />
            )}
          </button>
        </div>
      </div>
    );
  }

  return (
    <span
      className={`inline-block font-serif text-[var(--foreground)] ${className}`}
      aria-label={ariaLabel || math}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}

export default MathBlock;
