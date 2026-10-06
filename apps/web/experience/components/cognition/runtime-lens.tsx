"use client";

import { useEffect, useMemo, useState } from "react";
import { useLocale } from "@/lib/locale";
import { runtimeFactsAt } from "@/lib/cognition/runtime-facts";
import {
  composeFamily,
  FAMILY_QUESTION,
  validateCognitivePlan,
  type CognitivePlan,
  type Device,
} from "@/lib/cognition/compose";
import type { RuntimeFamilyFacts } from "@/lib/cognition/runtime-facts";
import { families, type FamilyId } from "@/lib/projection";
import type { RuntimeProjection } from "@/lib/runtime-projection";
import { safeSourceLink } from "@/lib/runtime-projection";
import { CognitiveComponent } from "./lenses";
import { CurrentnessTag, LayerSection } from "./grammar";
import type { Intent, Layer } from "@/lib/cognition/registry";

type RuntimeIntent = Extract<Intent, "overview" | "why" | "how_known" | "change">;
export type RuntimeCognitionSelection = {
  family: FamilyId;
  asOf: string;
  intent: RuntimeIntent;
  device: Device;
};
const intents: RuntimeIntent[] = ["overview", "why", "how_known", "change"];

function serverCognitivePlan(
  candidate: unknown,
  revision: string,
  family: FamilyId,
  asOf: string,
  intent: RuntimeIntent,
  device: Device,
  facts: RuntimeFamilyFacts,
): CognitivePlan | null {
  if (typeof candidate !== "object" || candidate === null) return null;
  const envelope = candidate as {
    revision?: unknown;
    cognition?: { request?: unknown; plan?: unknown };
  };
  if (envelope.revision !== revision || typeof envelope.cognition !== "object" || envelope.cognition === null)
    return null;
  const request = envelope.cognition.request;
  if (typeof request !== "object" || request === null) return null;
  const selected = request as Record<string, unknown>;
  if (
    selected.family !== family || selected.asOf !== asOf ||
    selected.intent !== intent || selected.device !== device
  ) return null;
  const proposed = envelope.cognition.plan;
  if (typeof proposed !== "object" || proposed === null) return null;
  const identity = proposed as Partial<CognitivePlan>;
  if (identity.family !== family || identity.intent !== intent) return null;
  const checked = validateCognitivePlan(proposed, facts);
  return checked.success ? checked.plan : null;
}

function useDevice(): Device {
  // Match the accepted FamilyLens behavior: render the conservative mobile
  // composition on the server, then update to the actual viewport.
  const [device, setDevice] = useState<Device>("mobile");
  useEffect(() => {
    const query = window.matchMedia("(max-width: 760px)");
    const update = () => setDevice(query.matches ? "mobile" : "desktop");
    update();
    query.addEventListener("change", update);
    return () => query.removeEventListener("change", update);
  }, []);
  return device;
}

function validCut(value: unknown): value is string {
  return typeof value === "string" && value.length > 0 && Number.isFinite(Date.parse(value));
}

function toUtcDateTimeLocal(value: string | undefined): string {
  if (!value || !validCut(value)) return "";
  return new Date(value).toISOString().replace(/Z$/, "");
}

function utcCutFromDateTimeLocal(value: string): string | null {
  if (!value) return null;
  const instant = Date.parse(`${value}Z`);
  return Number.isFinite(instant) ? new Date(instant).toISOString() : null;
}

function RuntimeProvenance({ facts, asOf }: { facts: RuntimeFamilyFacts; asOf: string }) {
  const { t, copy, locale } = useLocale();
  const cutTime = Date.parse(asOf);
  const sources = facts.sources;
  return (
    <article
      className="cg-component cg-provenance-trail"
      data-cognitive-component="provenance-trail"
      data-runtime-provenance="true"
    >
      <h3 className="cg-title">{t("Fuentes y vigencia", "Sources and currentness")}</h3>
      <p className="cg-headline">
        {sources.length} {t("fuentes en este corte", "sources in this cut")}
      </p>
      <ol className="cg-provenance">
        {sources.map((source) => {
          const href = source.sourceRef ? safeSourceLink(source.sourceRef) : null;
          return (
            <li key={source.id} data-provenance={source.id}>
              <strong>{copy(source.title)}</strong>
              <span className="cg-meta">
                {new Date(source.observedAt).toLocaleDateString(locale)}
                {" · "}
                {copy(source.instrument)}
              </span>
              <CurrentnessTag state={source.currentness ?? "UNKNOWN"} />
              <span className="cg-limit">{copy(source.limitation)}</span>
              {href ? (
                <a href={href} target="_blank" rel="noopener noreferrer" className="text-link">
                  {t("Abrir fuente original", "Open original source")}
                </a>
              ) : source.sourceRef ? (
                <span className="cg-limit" data-source-navigation="unavailable">
                  {t(
                    "La fuente está registrada, pero su dirección no está disponible para una navegación segura.",
                    "The source is recorded, but its address is unavailable for safe navigation.",
                  )}
                </span>
              ) : null}
              {source.provenanceRef && (
                <span className="cg-meta">
                  {t("Referencia de evidencia", "Evidence reference")}: {source.provenanceRef}
                </span>
              )}
              {source.currentnessEvaluatedAt &&
                Date.parse(source.currentnessEvaluatedAt) <= cutTime && (
                <span className="cg-meta">
                  {t("Vigencia evaluada", "Currentness evaluated")}: {source.currentnessEvaluatedAt}
                </span>
              )}
            </li>
          );
        })}
      </ol>
    </article>
  );
}

function EmptyRuntimeReading({ unavailable }: { unavailable: boolean }) {
  const { t } = useLocale();
  return (
    <p className="cg-unknown" data-epistemic="UNKNOWN" data-runtime-empty={unavailable ? "unavailable" : "unsupported"}>
      {unavailable
        ? t(
            "Esta proyección no incluye una lectura cognitiva gobernada.",
            "This projection does not include a governed cognitive reading.",
          )
        : t(
            "No hay observaciones gobernadas suficientes para responder en este corte. Esto no demuestra ausencia.",
            "There are not enough governed observations to answer at this cut. This does not establish absence.",
          )}
    </p>
  );
}

/**
 * Subscriber-facing cognitive lens over a real runtime projection. It never
 * calls factsAt: only the runtime adapter supplies facts, and only a validated
 * composition reaches the accepted cognitive components.
 */
export function RuntimeLens({
  projection,
  revision,
  asOf,
  initialFamily = "presence",
  initialIntent = "overview",
  responsePlan,
  onIntentChange,
}: {
  projection: RuntimeProjection;
  revision: string;
  asOf?: string;
  initialFamily?: FamilyId;
  initialIntent?: RuntimeIntent;
  responsePlan?: unknown;
  onIntentChange?: (selection: RuntimeCognitionSelection) => void;
}) {
  const { t, copy } = useLocale();
  const [family, setFamily] = useState<FamilyId>(initialFamily);
  const [intent, setIntent] = useState<RuntimeIntent>(initialIntent);
  const [selectedCut, setSelectedCut] = useState<{ context: string; value: string } | null>(null);
  const device = useDevice();
  const projectionCut = projection.cognition?.asOf;
  const cutLimit = validCut(projectionCut) ? projectionCut : undefined;
  const context = `${revision}:${projection.organization.id}:${cutLimit ?? ""}:${asOf ?? ""}`;
  const configuredCut = validCut(asOf) ? asOf : cutLimit;
  const initialCut = configuredCut && cutLimit && Date.parse(configuredCut) > Date.parse(cutLimit)
    ? cutLimit
    : configuredCut;
  const cut = selectedCut?.context === context ? selectedCut.value : initialCut;
  const facts = useMemo(
    () => (cut ? runtimeFactsAt(projection, family, cut) : null),
    [projection, revision, family, cut],
  );
  const check = useMemo(() => {
    if (!facts) return null;
    const composed = composeFamily({ family, intent, facts, device });
    const acceptedResponse = cut
      ? serverCognitivePlan(responsePlan, revision, family, cut, intent, device, facts)
      : null;
    const proposed = acceptedResponse ?? composed;
    return {
      proposed,
      source: acceptedResponse ? "response" as const : "local" as const,
      checked: validateCognitivePlan(proposed, facts),
    };
  }, [facts, family, intent, device, responsePlan, revision, cut]);
  const plan = check?.checked.success === true ? check.checked.plan : null;
  const question = copy(FAMILY_QUESTION[family]);

  useEffect(() => {
    if (cut) onIntentChange?.({ family, asOf: cut, intent, device });
  }, [cut, device, family, intent, onIntentChange]);

  useEffect(() => {
    setSelectedCut((current) => current?.context === context ? current : null);
  }, [context]);

  function chooseCut(value: string) {
    if (!value) {
      setSelectedCut(null);
      return;
    }
    const nextCut = utcCutFromDateTimeLocal(value);
    if (!nextCut || !cutLimit || Date.parse(nextCut) > Date.parse(cutLimit)) return;
    setSelectedCut({ context, value: nextCut });
  }

  const intentLabel = (value: RuntimeIntent) => {
    if (value === "overview") return t("Comprender", "Understand");
    if (value === "why") return t("Por qué importa", "Why it matters");
    if (value === "how_known") return t("Cómo lo sabe AXIGNAL", "How AXIGNAL knows");
    return t("Qué ha cambiado", "What changed");
  };

  return (
    <section
      className="cg-lens runtime-cognitive-lens"
      aria-label={t("Lectura cognitiva", "Cognitive reading")}
      data-family={family}
      data-intent={intent}
      data-revision={revision}
      data-as-of={cut}
      data-plan-source={check?.source}
    >
      <div className="subscriber-add runtime-cognitive-controls">
        <label htmlFor={`runtime-family-${revision}`}>
          {t("Perspectiva", "Perspective")}
        </label>
        <select
          id={`runtime-family-${revision}`}
          className="button secondary"
          value={family}
          onChange={(event) => setFamily(event.target.value as FamilyId)}
        >
          {families.map((item) => (
            <option key={item.id} value={item.id}>
              {copy(item.name)}
            </option>
          ))}
        </select>
        <div className="subscriber-row-actions" role="group" aria-label={t("Pregunta", "Question")}>
          {intents.map((item) => (
            <button
              key={item}
              type="button"
              className="text-link"
              aria-pressed={intent === item}
              onClick={() => setIntent(item)}
            >
              {intentLabel(item)}
            </button>
          ))}
        </div>
      </div>

      <div className="subscriber-add runtime-cut-control">
        <label htmlFor={`runtime-cut-${revision}`}>
          {t("Corte de conocimiento (UTC)", "Knowledge cut (UTC)")}
        </label>
        <input
          id={`runtime-cut-${revision}`}
          className="button secondary"
          type="datetime-local"
          step="0.001"
          value={toUtcDateTimeLocal(cut)}
          max={toUtcDateTimeLocal(cutLimit)}
          disabled={!cutLimit}
          aria-describedby={`runtime-cut-help-${revision}`}
          onChange={(event) => chooseCut(event.currentTarget.value)}
          onInput={(event) => chooseCut(event.currentTarget.value)}
          onBlur={(event) => chooseCut(event.currentTarget.value)}
        />
        <p id={`runtime-cut-help-${revision}`} className="cg-meta">
          {t(
            "Introduce la fecha y hora en UTC. El corte no puede superar la última lectura disponible.",
            "Enter a date and time in UTC. The cut cannot exceed the latest available reading.",
          )}
        </p>
      </div>

      <p className="cg-question">{question}</p>
      {cut && (
        <p className="cg-meta" data-runtime-cut="true">
          {t("Corte de conocimiento", "Knowledge cut")}: <time dateTime={cut}>{cut}</time>
        </p>
      )}

      {!facts ? (
        <EmptyRuntimeReading unavailable />
      ) : !plan ? (
        check?.proposed.items.length === 0 ? (
          <EmptyRuntimeReading unavailable={false} />
        ) : (
          <p className="cg-unknown" role="status" data-runtime-plan="rejected">
            {t(
              "La lectura no superó la validación y permanece oculta.",
              "The reading did not pass validation and remains hidden.",
            )}
          </p>
        )
      ) : (
        <>
          {!plan.items.some((item) => item.component !== "provenance-trail") && (
            <EmptyRuntimeReading unavailable={false} />
          )}
          {[1, 2, 3, 4].map((layer) => {
            const items = plan.items.filter((item) => item.layer === layer);
            if (!items.length) return null;
            return (
              <LayerSection key={layer} layer={layer as Layer}>
                {items.map((item) =>
                  item.component === "provenance-trail" ? (
                    <RuntimeProvenance key={item.component} facts={facts} asOf={cut!} />
                  ) : (
                    <CognitiveComponent
                      key={item.component}
                      id={item.component}
                      facts={facts}
                      asOf={cut!}
                      glance={layer === 1}
                    />
                  ),
                )}
              </LayerSection>
            );
          })}
        </>
      )}
    </section>
  );
}
