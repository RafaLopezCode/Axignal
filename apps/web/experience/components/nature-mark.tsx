"use client";
import type { Nature } from "@/lib/observatory";

/** An epistemic or interpretive state as a shape plus its word: never colour alone. */
export function NatureMark({ nature, label }: { nature: Nature; label: string }) {
  const shape = (() => {
    switch (nature) {
      case "OBSERVED": return <circle cx="6" cy="6" r="4" fill="currentColor"/>;
      case "DECLARED": return <><circle cx="6" cy="6" r="4" fill="none" stroke="currentColor" strokeWidth="1.5"/><path d="M6 2a4 4 0 0 1 0 8z" fill="currentColor"/></>;
      case "POTENTIAL": return <circle cx="6" cy="6" r="4" fill="none" stroke="currentColor" strokeWidth="1.5" strokeDasharray="2 1.6"/>;
      case "UNKNOWN": return <><circle cx="6" cy="6" r="4" fill="none" stroke="currentColor" strokeWidth="1.5"/><circle cx="6" cy="6" r="1" fill="currentColor"/></>;
      case "STRENGTH": return <><circle cx="6" cy="6" r="5" fill="currentColor"/><path d="M3.6 6.2 5.3 7.8 8.5 4.4" fill="none" stroke="var(--obs-paper)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></>;
      case "CLARIFY": return <><circle cx="6" cy="6" r="4.5" fill="none" stroke="currentColor" strokeWidth="1.5"/><path d="M6 3.8v4.4M3.8 6h4.4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/></>;
      case "UNRESOLVED": return <><circle cx="6" cy="6" r="4.5" fill="none" stroke="currentColor" strokeWidth="1.5" strokeDasharray="1.4 1.6"/></>;
    }
  })();
  return <span className={`obs-mark obs-mark-${nature.toLowerCase()}`}><svg width="12" height="12" viewBox="0 0 12 12" aria-hidden="true">{shape}</svg>{label}</span>;
}
