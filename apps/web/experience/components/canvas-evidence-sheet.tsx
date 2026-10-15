"use client";

import { useEffect, useRef, type ReactNode } from "react";
import { X } from "lucide-react";
import { useLocale } from "@/lib/locale";
import type { Lane } from "@/lib/observatory";

/** A non-modal proof surface: only its canvas is obscured; AXENT stays usable. */
export function CanvasEvidenceSheet({ title, focusKey, lane, onClose, children }: {
  title: string;
  focusKey: string;
  lane?: Lane;
  onClose: () => void;
  children: ReactNode;
}) {
  const { t } = useLocale();
  const panel = useRef<HTMLElement>(null);
  useEffect(() => {
    panel.current?.querySelector<HTMLElement>("h2")?.focus({ preventScroll: true });
    panel.current?.querySelector<HTMLElement>(".obs-evidence-content")?.scrollTo({ top: 0 });
  }, [focusKey]);
  return <div className="obs-evidence-layer">
    <button className="obs-evidence-scrim" tabIndex={-1} onClick={onClose} aria-label={t("Cerrar evidencias", "Close evidence")}/>
    <section ref={panel} id="obs-depth" className={`obs-depth obs-evidence-sheet${lane ? ` obs-lane-${lane}` : ""}`} role="dialog" aria-labelledby="obs-evidence-title"
      onKeyDown={event => { if (event.key === "Escape" && !event.defaultPrevented) { event.preventDefault(); event.stopPropagation(); onClose(); } }}>
      <header className="obs-evidence-header">
        <h2 id="obs-evidence-title" tabIndex={-1}>{title}</h2>
        <button type="button" className="obs-icon" onClick={onClose} aria-label={t("Cerrar evidencias", "Close evidence")}><X size={20} aria-hidden="true"/></button>
      </header>
      <div className="obs-evidence-content">{children}</div>
    </section>
  </div>;
}
