import React from "react";
import katex from "katex";

interface MathBlockProps {
  math: string;
  display?: boolean;
  className?: string;
  ariaLabel?: string;
}

export function MathBlock({
  math,
  display = true,
  className = "",
  ariaLabel,
}: MathBlockProps) {
  let html = "";
  try {
    html = katex.renderToString(math, {
      displayMode: display,
      throwOnError: false,
      output: "htmlAndMathml",
    });
  } catch (err) {
    console.error("KaTeX error:", err);
    html = `<code class="text-rose-400 font-mono text-xs">${math}</code>`;
  }

  if (display) {
    return (
      <div
        className={`my-3 overflow-x-auto py-1 text-center font-serif text-[var(--foreground)] ${className}`}
        aria-label={ariaLabel || math}
        dangerouslySetInnerHTML={{ __html: html }}
      />
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
