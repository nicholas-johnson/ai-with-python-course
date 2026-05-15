import React from "react";

const INLINE_PATTERN = /(\*\*(.+?)\*\*|\*(.+?)\*|`(.+?)`)/g;

export function parseInlineMarkdown(text) {
  if (typeof text !== "string") return text;

  const parts = [];
  let lastIndex = 0;
  let match;

  while ((match = INLINE_PATTERN.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }

    if (match[2]) {
      parts.push(
        <strong key={match.index} className="font-bold text-white">
          {match[2]}
        </strong>
      );
    } else if (match[3]) {
      parts.push(
        <em key={match.index} className="italic">
          {match[3]}
        </em>
      );
    } else if (match[4]) {
      parts.push(
        <code
          key={match.index}
          className="bg-slate-700 text-amber-300 px-1.5 py-0.5 rounded text-[0.9em] font-mono"
        >
          {match[4]}
        </code>
      );
    }

    lastIndex = match.index + match[0].length;
  }

  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }

  return parts.length === 0 ? text : parts;
}

export function InlineMarkdown({ text }) {
  return <>{parseInlineMarkdown(text)}</>;
}
