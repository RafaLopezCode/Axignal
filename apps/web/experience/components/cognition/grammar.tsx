"use client";
/**
 * Shared cognitive grammar: the same epistemic language in every family.
 * OBSERVED is solid, POTENTIAL is dashed, UNKNOWN is hatched text (never zero),
 * currentness is always labelled, sources and "why" are always one step away.
 */
import type { ReactNode } from "react";
import { useLocale } from "@/lib/locale";
import type { Epistemic } from "@/lib/projection";
import type { Currentness, FactSource } from "@/lib/cognition/facts";
import type { Layer } from "@/lib/cognition/registry";
import { Badge } from "../ui";
import { dateLabel } from "@/lib/projection";

export function Mark({ state }: { state: Epistemic }) {
  return (
    <span className="cg-mark" data-epistemic={state}>
      <Badge state={state} />
    </span>
  );
}

/** UNKNOWN is named, hatched and never drawn as a zero-length bar. */
export function UnknownValue({ label }: { label?: string }) {
  const { t } = useLocale();
  return (
    <span className="cg-unknown" data-epistemic="UNKNOWN">
      {label ?? t("Desconocido", "Unknown")}
    </span>
  );
}

export function CurrentnessTag({ state }: { state: Currentness }) {
  const { t } = useLocale();
  const label = {
    CURRENT: t("Actual", "Current"),
    STALE: t("Envejecida", "Stale"),
    HISTORICAL: t("Histórica", "Historical"),
    UNKNOWN: t("Vigencia desconocida", "Currentness unknown"),
  }[state];
  return (
    <span className={"badge cg-currentness cg-currentness-" + state.toLowerCase()} data-currentness={state}>
      {label}
    </span>
  );
}

export function SourceRef({ source }: { source: FactSource | undefined }) {
  const { t, copy, locale } = useLocale();
  if (!source)
    return (
      <span className="cg-source-none" data-provenance="none">
        {t("Sin fuente: es una hipótesis", "No source: this is a hypothesis")}
      </span>
    );
  return (
    <details className="cg-source" data-provenance={source.id}>
      <summary>
        {t("Fuente", "Source")}: {copy(source.title)} · {dateLabel(source.observedAt.slice(0, 10), locale)}
      </summary>
      <p>{copy(source.instrument)}</p>
      <p className="cg-limit">{copy(source.limitation)}</p>
    </details>
  );
}

/** Layer 1 is always visible; deeper layers open on demand, labelled by their question. */
export function LayerSection({ layer, children }: { layer: Layer; children: ReactNode }) {
  const { t } = useLocale();
  if (layer === 1)
    return (
      <section className="cg-layer cg-layer-1" data-layer="1">
        {children}
      </section>
    );
  const question =
    layer === 2
      ? t("¿Por qué importa?", "Why does it matter?")
      : layer === 3
        ? t("¿Cómo lo sabe AXIGNAL?", "How does AXIGNAL know?")
        : t("Ver toda la evidencia", "Inspect all the evidence");
  return (
    <details className={"cg-layer cg-layer-" + layer} data-layer={layer}>
      <summary>{question}</summary>
      <div className="cg-layer-body">{children}</div>
    </details>
  );
}

export function Headline({ children }: { children: ReactNode }) {
  return <p className="cg-headline">{children}</p>;
}
