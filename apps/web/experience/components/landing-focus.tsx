"use client";
import { useState } from "react";
import { ArrowLeft, ArrowRight, ChevronDown } from "lucide-react";
import { useLocale } from "@/lib/locale";
import { dateLabel, demoOrganizationName } from "@/lib/projection";
import { laneCopy, natureLabel, type Lane } from "@/lib/observatory";
import { EXAMPLE_MOMENTS, exampleInsights, exampleNewSince, selectedExampleInsight, type ExampleMoment } from "@/lib/landing-observatory";
import { InsightBody, NatureMark } from "./observatory";
import { SyntheticEvidenceProvider } from "./evidence-link-context";
import { focusCopy } from "@/lib/landing-focus-copy";
import "./landing-focus.css";

/** The same fictional example, focused on one finding; no new data or authority. */
export function LandingFocus() {
  const { t, copy, locale } = useLocale();
  const words = focusCopy[locale];
  const [moment, setMoment] = useState<ExampleMoment>("2026-10-03");
  const [lane, setLane] = useState<Lane>("matters");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const insights = exampleInsights(moment, copy);
  const selected = selectedExampleInsight(insights, lane, selectedId);
  const items = insights.filter(item => item.lane === lane);
  const index = selected ? items.findIndex(item => item.id === selected.id) : -1;
  const isNew = selected && exampleNewSince(moment).has(selected.id);

  return <figure className="lx-window focus-notebook" aria-label={t("Organización ficticia", "Fictional organization")}>
    <header className="focus-identity">
      <img src="/brand/isotope.svg" alt="" width={28} height={28} />
      <strong>{copy(demoOrganizationName)}</strong>
      <span className="focus-fiction">{t("Organización ficticia", "Fictional organization")}</span>
    </header>
    <div className="focus-time">
      <span>{words.moment}</span>
      <div className="focus-moments" role="group" aria-label={t("Mover el ejemplo en el tiempo", "Move the example through time")}>
        {EXAMPLE_MOMENTS.map(value => <button key={value} type="button" aria-pressed={moment === value} onClick={() => { setMoment(value); setSelectedId(null); }}>
          <time dateTime={value}>{dateLabel(value, locale)}</time>
        </button>)}
      </div>
    </div>
    <div className="focus-lanes" role="group" aria-label={words.attention}>
      {(["matters", "understood", "unknown"] as Lane[]).map(value => <button type="button" key={value} aria-pressed={lane === value} className={`focus-lane focus-lane-${value}`} onClick={() => { setLane(value); setSelectedId(null); }}>
        {laneCopy(value, t).title}
      </button>)}
    </div>
    <div className="focus-reading">
      <div aria-live="polite" aria-atomic="true">
        <div className="focus-content" key={`${moment}:${lane}:${selected?.id ?? "empty"}`}>
        {selected ? <>
          <div className="focus-state">
            <NatureMark nature={selected.nature} label={natureLabel(selected.nature, t)} />
            {selected.observedAt && <time dateTime={selected.observedAt}>{dateLabel(selected.observedAt, locale)}</time>}
            {isNew && <span className="focus-new">{t("Nuevo", "New")}</span>}
          </div>
          <h2>{selected.headline}</h2>
          <p className="focus-meaning">{selected.why}</p>
        </> : <p className="focus-empty">{t("Nada todavía en este momento.", "Nothing yet at this moment.")}</p>}
        </div>
      </div>
      {selected && <details className="focus-evidence" key={`${moment}:${selected.id}`}>
        <summary>{words.proof}<ChevronDown size={17} aria-hidden="true" /></summary>
        <SyntheticEvidenceProvider><InsightBody insight={selected} /></SyntheticEvidenceProvider>
      </details>}
      {items.length > 1 && <nav className="focus-paging" aria-label={words.findings}>
        <button type="button" aria-label={words.previous} disabled={index <= 0} onClick={() => setSelectedId(items[index - 1].id)}><ArrowLeft size={17} aria-hidden="true" /></button>
        <span>{index + 1} / {items.length}</span>
        <button type="button" aria-label={words.next} disabled={index >= items.length - 1} onClick={() => setSelectedId(items[index + 1].id)}><ArrowRight size={17} aria-hidden="true" /></button>
      </nav>}
    </div>
    <figcaption className="focus-invitation"><span className="hand-note">{words.invitation}</span><span>{words.caption}</span></figcaption>
  </figure>;
}
