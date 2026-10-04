"use client";
import { useLocale } from "@/lib/locale";
import {
  safeSourceLink,
  type RuntimeProjection,
  type RuntimeSignal,
} from "@/lib/runtime-projection";
import { Badge } from "./ui";

export function RuntimeSignalReading({ signal }: { signal: RuntimeSignal }) {
  const { t, locale } = useLocale();
  return (
    <article className="runtime-signal" id={signal.id} tabIndex={-1}>
      <div className="runtime-status">
        <Badge state={signal.epistemicState} />
        <span className="operation-status">{signal.currentness}</span>
      </div>
      <h3>{signal.title}</h3>
      <p>{signal.whyAttention}</p>
      <p>{signal.interpretation}</p>
      <div className="limit-note">
        <div>
          <strong>{t("Lo que sigue abierto", "What remains open")}</strong>
          <p>{signal.uncertainty}</p>
        </div>
      </div>
      <p className="runtime-date">
        {t("Observado", "Observed")}{" "}
        <time dateTime={signal.observedAt}>
          {new Date(signal.observedAt).toLocaleString(locale)}
        </time>
      </p>
      <details className="runtime-narrative">
        <summary>{t("Cómo lo sabe AXIGNAL", "How AXIGNAL knows")}</summary>
        <ol>
          {signal.evidenceNarrative.steps.map((step) => (
            <li key={step.id}>
              <span className="mono">{step.kind}</span>
              <p>{step.label}</p>
              {step.currentness && <small>{step.currentness}</small>}
              {step.observedAt && (
                <time dateTime={step.observedAt}>
                  {new Date(step.observedAt).toLocaleString(locale)}
                </time>
              )}
              {step.artifactVerified !== null && (
                <p>
                  {step.artifactVerified
                    ? t("Artefacto verificado", "Artifact verified")
                    : t("Artefacto no verificado", "Artifact not verified")}
                </p>
              )}
              {step.sourceRef && <SourceReference reference={step.sourceRef} />}
            </li>
          ))}
        </ol>
        <details>
          <summary>
            {t("Identificadores de trazabilidad", "Lineage identifiers")}
          </summary>
          <dl>
            <dt>Signal</dt>
            <dd>{signal.id}</dd>
            <dt>Observations</dt>
            <dd>{signal.observationSupportRefs.join("\n")}</dd>
            <dt>EvidenceNarrative</dt>
            <dd>{signal.evidenceNarrative.focusStepId}</dd>
          </dl>
        </details>
      </details>
      <details className="runtime-sources">
        <summary>
          {t("Fuentes y límites", "Sources and limits")} (
          {signal.sourceRefs.length})
        </summary>
        <ul>
          {signal.sourceRefs.map((ref) => (
            <li key={ref}>
              <SourceReference reference={ref} />
            </li>
          ))}
        </ul>
        <ul>
          {signal.unknowns.map((unknown) => (
            <li key={unknown}>{unknown}</li>
          ))}
        </ul>
      </details>
    </article>
  );
}
function SourceReference({ reference }: { reference: string }) {
  const href = safeSourceLink(reference);
  return href ? (
    <a href={href} target="_blank" rel="noopener noreferrer">
      {reference}
    </a>
  ) : (
    <span className="runtime-reference">{reference}</span>
  );
}
export function RuntimeProductProjection({
  projection,
}: {
  projection: RuntimeProjection;
}) {
  const { t } = useLocale();
  return (
    <section
      className="runtime-product"
      aria-label={t("Proyección de producto", "Product projection")}
    >
      <header>
        <span className="eyebrow">
          {t("OBSERVACIÓN ECONÓMICA", "ECONOMIC OBSERVATION")}
        </span>
        <h2>{projection.organization.name}</h2>
        <p>{projection.context.label}</p>
        <div className="runtime-status">
          <span>{projection.lifecycleStatus}</span>
          <span>
            {t(
              "Proyección persistida del runtime",
              "Persisted runtime projection",
            )}
          </span>
        </div>
        <details>
          <summary>{t("Contexto y versión", "Context and version")}</summary>
          <dl>
            <dt>Organization</dt>
            <dd>{projection.organization.id}</dd>
            <dt>Observation focus</dt>
            <dd>{projection.context.id}</dd>
            <dt>Reality level</dt>
            <dd>{projection.realityLevel}</dd>
            <dt>Runtime SHA</dt>
            <dd>{projection.runtimeCodeSha}</dd>
            <dt>Reload</dt>
            <dd>{projection.reloadContinuity}</dd>
          </dl>
        </details>
      </header>
      <section className="runtime-today" aria-label="Today">
        <h3>{t("Hoy", "Today")}</h3>
        <span>{projection.today.disposition}</span>
        {projection.today.items.length ? (
          projection.today.items.map((item) => (
            <article key={item.xignalId}>
              <h4>{item.whatChanged}</h4>
              <p>{item.whyItMatters}</p>
              <button
                className="text-link"
                aria-controls={item.xignalId}
                onClick={() => {
                  const target = document.getElementById(item.xignalId);
                  target?.scrollIntoView({ block: "start" });
                  target?.focus({ preventScroll: true });
                }}
              >
                {t("Ver señal y evidencia", "Read signal and evidence")}
              </button>
            </article>
          ))
        ) : (
          <p>
            {t(
              "El runtime no tiene señales vigentes para Hoy. Esto no convierte las observaciones anteriores en falsas.",
              "The runtime has no current signals for Today. Earlier observations do not become false.",
            )}
          </p>
        )}
      </section>
      <section aria-label={t("Señales", "Signals")}>
        <h3>{t("Señales", "Signals")}</h3>
        {projection.nodes.map((signal) => (
          <RuntimeSignalReading key={signal.id} signal={signal} />
        ))}
      </section>
    </section>
  );
}
