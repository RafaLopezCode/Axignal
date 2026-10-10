"use client";
/**
 * The real subscriber interface, working on the one public example, annotated by
 * El Observador. Cards, marks and the finding body are the product's own components;
 * the handwritten notes explain what the visitor is looking at. Nothing here is a
 * screenshot or a claim about a real organization: the example is fictional and says so.
 */
import { useEffect, useMemo, useRef, useState } from "react";
import { ArrowRight, Plus, X } from "lucide-react";
import { useLocale } from "@/lib/locale";
import { dateLabel, demoOrganizationName } from "@/lib/projection";
import { laneCopy, type Insight, type Lane } from "@/lib/observatory";
import { EXAMPLE_MOMENTS, exampleInsights, exampleNewSince, exampleOrganization, type ExampleMoment } from "@/lib/landing-observatory";
import { InsightBody, InsightCard } from "./observatory";

export type DemoMode = "glance" | "add" | "observing" | "briefing" | "evidence" | "unknown" | "time";

/** A handwritten note with a hand-drawn arrow that draws itself in. */
function Note({ children, side = "right", tone = "blue" }: { children: React.ReactNode; side?: "right" | "left" | "top" | "bottom"; tone?: "blue" | "brass" }) {
  return <span className={`lx-note lx-note-${side} lx-note-${tone}`}>
    <svg className="lx-note-arrow" viewBox="0 0 64 40" aria-hidden="true"><path d="M60 6 C 40 4, 18 10, 8 30 M8 30 l 2 -10 M8 30 l 9 -4" /></svg>
    <span className="lx-note-text">{children}</span>
  </span>;
}

function Lanes({ insights, lit, focus, open, onOpen, notes }: {
  insights: Insight[]; lit: Set<string>; focus: Lane | null; open: string | null;
  onOpen: (insight: Insight) => void; notes: boolean;
}) {
  const { t } = useLocale();
  return <div className="lx-lanes">
    {(["matters", "understood", "unknown"] as Lane[]).map(lane => {
      const items = insights.filter(i => i.lane === lane);
      return <section key={lane} className={`lx-lane obs-lane-${lane}${focus && focus !== lane ? " lx-dim" : ""}`} aria-label={laneCopy(lane, t).title}>
        <h4>{laneCopy(lane, t).title}<span>{items.length}</span></h4>
        {items.map(insight => <div className="lx-anchor" key={insight.id}>
          <InsightCard insight={insight} lit={lit.has(insight.id)} active={open === insight.id} onOpen={() => onOpen(insight)}/>
          {notes && insight.nature === "POTENTIAL" && <Note side="bottom">{t("posible, no un contrato", "possible, not a contract")}</Note>}
          {notes && insight.nature === "UNKNOWN" && <Note side="bottom">{t("desconocido no es falso", "unknown is not false")}</Note>}
          {notes && insight.id === "capability" && <Note side="bottom">{t("con su fuente y su fecha", "with its source and date")}</Note>}
          {lit.has(insight.id) && <Note side="top" tone="brass">{t("nuevo: se enciende hasta que lo ves", "new: lit until you see it")}</Note>}
        </div>)}
        {!items.length && <p className="lx-empty">{t("Nada todavía en este momento.", "Nothing yet at this moment.")}</p>}
      </section>;
    })}
  </div>;
}

export function LandingObservatory({ mode, asOf = "2026-10-03", onAsOf, className = "", footer }: {
  mode: DemoMode; asOf?: ExampleMoment; onAsOf?: (moment: ExampleMoment) => void; className?: string; footer?: React.ReactNode;
}) {
  const { t, copy, locale } = useLocale();
  const organization = exampleOrganization();
  const insights = useMemo(() => exampleInsights(asOf, copy), [asOf, copy]);
  const lit = mode === "time" ? exampleNewSince(asOf) : new Set<string>();
  const [open, setOpen] = useState<string | null>(null);
  const forced = mode === "evidence" ? "renovation" : null;
  const shown = insights.find(i => i.id === (open ?? forced)) ?? null;
  const sheet = useRef<HTMLDivElement>(null);
  useEffect(() => { setOpen(null); }, [mode]);
  useEffect(() => { if (open) sheet.current?.querySelector<HTMLElement>("h2")?.focus(); }, [open]);
  const notes = mode === "glance" || mode === "briefing";
  return <figure className={`lx-window lx-mode-${mode} ${className}`} aria-label={t("La interfaz real de AXIGNAL, con la organización ficticia del ejemplo", "The real AXIGNAL interface, with the example's fictional organization")}>
    <div className="lx-chrome">
      <img src="/brand/isotope.svg" alt="" width={18} height={18}/>
      <span className="lx-crumb">{t("Tu cartera", "Your portfolio")} <span aria-hidden="true">›</span> <strong>{mode === "add" ? t("Añadir organización", "Add organization") : copy(demoOrganizationName)}</strong></span>
      <span className="lx-fiction">{t("Organización ficticia", "Fictional organization")}</span>
    </div>
    <div className="lx-screen">
      {mode === "add" && <div className="lx-add">
        <p className="lx-add-q">{t("¿Qué organización quieres comprender?", "Which organization do you want to understand?")}</p>
        <div className="lx-add-row"><span className="lx-input"><span className="lx-typed">{copy(demoOrganizationName)}</span></span><span className="lx-go"><Plus size={14} aria-hidden="true"/>{t("Empezar a observar", "Start observing")}</span></div>
        <Note side="bottom">{t("un nombre o su web bastan", "a name or its website is enough")}</Note>
      </div>}
      {mode === "observing" && <div className="lx-observing">
        <div className="lx-scan" aria-hidden="true"><svg viewBox="0 0 120 120"><circle className="lx-scan-ring" cx="60" cy="60" r="44"/><circle className="lx-scan-sweep" cx="60" cy="60" r="44"/></svg><img src="/brand/isotope.svg" alt="" width={44} height={44}/></div>
        <ol>
          <li className="done">{t("Identidad buscada en un registro", "Identity looked up in a registry")}</li>
          <li className="current">{t("Observando su presencia pública", "Observing its public presence")}</li>
          <li>{t("Primera lectura con evidencias", "First reading with evidence")}</li>
        </ol>
        <Note side="left">{t("el estado real, sin barras de carga fingidas", "the real state, no fake loading bars")}</Note>
      </div>}
      {mode !== "add" && mode !== "observing" && <>
        <header className="lx-org">
          <h3>{copy(demoOrganizationName)}</h3>
          <p>{t("Observada", "Observed")} {dateLabel(asOf, locale)} · {copy(organization.sector)}</p>
        </header>
        <p className="lx-brief">{copy(organization.does)}</p>
        {mode === "time" && <div className="lx-time" role="group" aria-label={t("Mover el ejemplo en el tiempo", "Move the example through time")}>
          {EXAMPLE_MOMENTS.map(moment => <button key={moment} aria-pressed={asOf === moment} onClick={() => onAsOf?.(moment)}>
            <span className="lx-time-dot" aria-hidden="true"/>{dateLabel(moment, locale)}</button>)}
        </div>}
        <Lanes insights={insights} lit={lit} focus={mode === "unknown" ? "unknown" : null} open={shown?.id ?? null} onOpen={insight => setOpen(insight.id)} notes={notes}/>
        {shown && <div ref={sheet} className={`lx-sheet obs-lane-${shown.lane}`} role="region" aria-label={t("Por qué lo dice AXIGNAL", "Why AXIGNAL says so")}>
          {open && <button className="lx-sheet-close" onClick={() => setOpen(null)} aria-label={t("Cerrar", "Close")}><X size={16} aria-hidden="true"/></button>}
          <InsightBody insight={shown}/>
          {mode === "evidence" && <Note side="left">{t("la prueba, a un clic de la conclusión", "the proof, one click from the conclusion")}</Note>}
        </div>}
      </>}
    </div>
    {footer && <figcaption className="lx-footer">{footer}</figcaption>}
  </figure>;
}
