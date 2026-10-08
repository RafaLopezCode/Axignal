"use client";
/**
 * The public example's story after "its economic world": what changed (dated, in the
 * order AXIGNAL learned it) and what is still left to find out. Both read the same
 * temporal example facts as the lenses, so a historical cut never shows the future.
 */
import { CalendarClock, CircleHelp } from "lucide-react";
import { useLocale } from "@/lib/locale";
import { factsAt } from "@/lib/cognition/facts";
import { dateLabel, type Signal } from "@/lib/projection";
import { Badge } from "./ui";

const KIND = {
  EVIDENCE_ARRIVED: { es: "Nueva evidencia", en: "New evidence" },
  HYPOTHESIS_UPDATED: { es: "Lectura actualizada", en: "Reading updated" },
  MATERIAL_CHANGE: { es: "Cambio relevante", en: "Material change" },
  BECAME_STALE: { es: "Deja de estar vigente", en: "No longer current" },
} as const;

export function ExampleChanges({ organizationId, asOf }: { organizationId: string; asOf: string }) {
  const { t, copy, locale } = useLocale();
  const events = [...(factsAt(organizationId, asOf).change?.events ?? [])].reverse();
  return (
    <section className="example-story" aria-labelledby="example-changes-title">
      <span className="eyebrow">
        <CalendarClock size={14} aria-hidden="true" /> {t("Qué ha cambiado", "What changed")}
      </span>
      <h2 id="example-changes-title">
        {t("Lo último que AXIGNAL ha observado.", "The latest AXIGNAL has observed.")}
      </h2>
      {events.length ? (
        <ol className="example-changes">
          {events.map((event) => (
            <li key={event.date + event.kind + event.label.en}>
              <span className="mono">{dateLabel(event.date, locale)}</span>
              <span className={"change-kind change-" + event.kind.toLowerCase()}>
                {t(KIND[event.kind].es, KIND[event.kind].en)}
              </span>
              <strong>{copy(event.label)}</strong>
            </li>
          ))}
        </ol>
      ) : (
        <p className="example-quiet">
          {t(
            "No hay cambios materiales en este corte. Que no pase nada también es información.",
            "No material changes at this point in time. Nothing happening is information too.",
          )}
        </p>
      )}
    </section>
  );
}

export function ExampleOpenQuestions({ signals, onOpen }: { signals: Signal[]; onOpen: (signal: Signal) => void }) {
  const { t, copy } = useLocale();
  if (!signals.length) return null;
  return (
    <section className="example-story" aria-labelledby="example-open-title">
      <span className="eyebrow">
        <CircleHelp size={14} aria-hidden="true" /> {t("Lo que queda por averiguar", "What is left to find out")}
      </span>
      <h2 id="example-open-title">
        {t("Cada lectura dice qué le falta.", "Every reading says what it is missing.")}
      </h2>
      <ul className="example-open">
        {signals.map((signal) => (
          <li key={signal.id}>
            <Badge state={signal.epistemic} />
            <button className="text-link" onClick={() => onOpen(signal)}>
              {copy(signal.title)}
            </button>
            <span>{copy(signal.limitation)}</span>
            <span className="example-next">
              <strong>{t("Siguiente paso:", "Next step:")}</strong> {copy(signal.next)}
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}
