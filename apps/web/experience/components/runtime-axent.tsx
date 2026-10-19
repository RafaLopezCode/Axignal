"use client";
import { productGuideCatalog } from "@/lib/axent-product-guide";
import { useEffect, useRef, useState } from "react";
import { RotateCcw } from "lucide-react";
import { safeSourceLink, type RuntimeProjection } from "@/lib/runtime-projection";
import { explainIllustrative, type RuntimeAnswer } from "@/lib/runtime-axent";
import { useLocale } from "@/lib/locale";
import { presentRuntimeCode, presentRuntimePassage } from "@/lib/runtime-presentation";
import { AxentIdentity, IconButton } from "./ui";
import { AxentComposer } from "./axent-composer";
import { acceptsReadingPlan, type CognitiveReadingRequest } from "@/lib/subscriber-presentation";
import { runtimeFactsAt } from "@/lib/cognition/runtime-facts";
import { CognitiveComponent } from "./cognition/lenses";
/** One answer as shown: every section in the reader's language, no sentence twice. */
function presentAnswer(answer: RuntimeAnswer, projection: RuntimeProjection, locale: Parameters<typeof presentRuntimePassage>[2]) {
  const seen = new Set<string>([answer.summary.trim()]);
  const section = (values: string[] | undefined) => (values ?? [])
    .map(value => presentRuntimePassage(value, projection, locale).trim())
    .filter(value => value && !seen.has(value) && (seen.add(value), true));
  const passages = section(answer.passages);
  const known = section(answer.known);
  const open = section(answer.openQuestions);
  const basis = section(answer.evidenceBasis);
  const limits = section(answer.evidenceLimits);
  return { passages, known, open, basis, limits };
}

export function useRuntimeAxent(
  projection: RuntimeProjection,
  signalId: string | null,
  subscriber?: { revision: string; cognition?: CognitiveReadingRequest },
  illustrative = false,
  /** Answers some questions without a round trip (a selected finding); null asks as usual. */
  local?: (question: string) => RuntimeAnswer | null,
  /** What the reader is looking at, named in the question the runtime receives. */
  frame?: (question: string) => string,
) {
  const { t, locale } = useLocale();
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(false);
  const [messages, setMessages] = useState<
    { question: string; answer: RuntimeAnswer }[]
  >([]);
  const controller = useRef<AbortController | null>(null);
  useEffect(() => {
    controller.current?.abort();
    setMessages([]);
    setBusy(false);
    setError(false);
    setDraft("");
    return () => controller.current?.abort();
  }, [projection.context.id, signalId, subscriber?.revision, subscriber?.cognition?.family, subscriber?.cognition?.asOf]);
  async function ask(question: string) {
    if (!question.trim() || busy) return;
    const request = new AbortController();
    controller.current = request;
    setBusy(true);
    setError(false);
    setDraft("");
    try {
      const answered = local?.(question);
      if (answered) {
        setMessages(previous => [...previous, { question, answer: answered }]);
        return;
      }
      if (illustrative) {
        const answer = explainIllustrative(projection, question, signalId ?? undefined, locale);
        setMessages(previous => [...previous, { question, answer }]);
        return;
      }
      const response = await fetch(subscriber ? "/api/subscriber/axent" : "/api/axent", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...(subscriber
            ? {
                revision: subscriber.revision,
                cognition: subscriber.cognition,
                ...(messages.at(-1)?.answer.memory ? { memory: messages.at(-1)?.answer.memory } : {}),
              }
            : { mode: "runtime" }),
          prompt: frame ? frame(question) : question,
          contextId: projection.context.id,
          locale,
          ...(signalId ? { signalId } : {}),
        }),
        signal: request.signal,
      });
      if (!response.ok) throw new Error("UNAVAILABLE");
      const answer = (await response.json()) as RuntimeAnswer;
      // Ignore results from a reobserved/different scope rather than reusing trust.
      if (
        answer.contextId !== projection.context.id ||
        answer.organizationId !== projection.organization.id
      )
        throw new Error("CONTEXT_CHANGED");
      if (subscriber) {
        const candidate = answer as RuntimeAnswer & { revision?: string; cognition?: unknown };
        if (candidate.revision !== subscriber.revision || !acceptsReadingPlan({
          version: 1, revision: subscriber.revision, intent: "summary", refs: answer.signalIds,
          method: "DETERMINISTIC_EVIDENCE_PRESENTATION",
          ...(candidate.cognition ? { cognition: candidate.cognition } : {}),
        }, projection, subscriber.revision)) throw new Error("READING_CHANGED");
      }
      if (!request.signal.aborted)
        setMessages((previous) => [...previous, { question, answer }]);
    } catch {
      if (!request.signal.aborted) setError(true);
    } finally {
      if (!request.signal.aborted) setBusy(false);
    }
  }
  const stop = () => {
    controller.current?.abort();
    setBusy(false);
  };
  return {
    draft,
    setDraft,
    busy,
    error,
    messages,
    ask,
    stop,
    clear: () => {
      stop();
      setMessages([]);
    },
  };
}
export function RuntimeAxent({
  projection,
  signalId,
  onEvidence,
  onSignal,
  onPublicUnderstanding,
  conversation,
  focusLabel,
  illustrative = false,
  onWiden,
  widenLabel,
  suggestions,
}: {
  projection: RuntimeProjection;
  signalId: string | null;
  onEvidence: () => void;
  onSignal: (id: string) => void;
  onPublicUnderstanding?: (reportId: string) => void;
  conversation: ReturnType<typeof useRuntimeAxent>;
  focusLabel?: string;
  /** Widens the context one level (finding → family → organization). */
  onWiden?: () => void;
  widenLabel?: string;
  /** Questions that fit the current context; the general ones otherwise. */
  suggestions?: string[];
  illustrative?: boolean;
}) {
  const { t, locale } = useLocale();
  const { draft, setDraft, busy, error, messages, ask, stop, clear } =
    conversation;
  const panelRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    // A guide button is replaced by follow-ups. Retain keyboard orientation when that
    // replacement removes the focused control; typing in the composer keeps its focus.
    if (messages.at(-1)?.answer.productGuide && document.activeElement === document.body) {
      panelRef.current?.querySelector<HTMLButtonElement>(".axent-questions button")?.focus({ preventScroll: true });
    }
  }, [messages]);
  const questions = suggestions ?? [
    ...productGuideCatalog.locales[locale].questions.slice(0, 2),
    t("Qué sabes", "What do you know"),
    t("Qué cambió", "What changed"),
    t("Por qué importa", "Why it matters"),
    t("Qué sigue abierto", "What remains open"),
    t("Cómo lo sabes", "How do you know"),
    t("Qué investigarías después", "What would you investigate next"),
    t("Qué puedo hacer", "What can I do"),
  ];
  return (
    <div ref={panelRef} className="axent-panel">
      <header className="axent-header">
        <AxentIdentity />
        <IconButton
          label={t(
            "Nueva conversación contextual",
            "New contextual conversation",
          )}
          onClick={clear}
        >
          <RotateCcw size={15} />
        </IconButton>
      </header>
      <div className="axent-scope">
        <span className="mono">
          {illustrative ? productGuideCatalog.locales[locale].illustrationLabel : t("CONTEXTO AUTORIZADO", "AUTHORIZED CONTEXT")}
        </span>
        <strong>{projection.organization.name}</strong>
        <small className="axent-focus">
          {focusLabel ??
            (signalId
              ? t("Señal seleccionada", "Selected signal")
              : t("Panorama", "Panorama"))}
          {onWiden && widenLabel && <button type="button" className="axent-widen" onClick={onWiden} aria-label={widenLabel} title={widenLabel}>×</button>}
        </small>
      </div>
      <div className="axent-messages" aria-live="polite" aria-busy={busy}>
        {!messages.length && (
          <div className="axent-welcome">
            <h2>
              {t(
                "Miremos con un poco más de contexto.",
                "Let’s look with a little more context.",
              )}
            </h2>
            <p>
              {illustrative ? productGuideCatalog.locales[locale].illustrationNotice : t(
                "Lectura de la evidencia disponible. La investigación nueva requiere herramientas autorizadas.",
                "Reading available evidence. New research requires authorized tools.",
              )}
            </p>
          </div>
        )}
        {messages.map((message, i) => { const shown = presentAnswer(message.answer, projection, locale); return (
          <div key={i}>
            <div className="axent-message user">
              <p>{message.question}</p>
            </div>
            <div className="axent-message">
              <span className="message-author">AXENT</span>
              {message.answer.productGuide && <small className="axent-example">{message.answer.productGuide.label}</small>}
              <p className="axent-synthesis">{message.answer.summary}</p>
              {message.answer.cognition && <div className="cg-lens">{message.answer.cognition.plan.items.map(item => <CognitiveComponent
                key={item.component} id={item.component}
                facts={runtimeFactsAt(projection, message.answer.cognition!.request.family, message.answer.cognition!.request.asOf)}
                asOf={message.answer.cognition!.request.asOf} glance={item.layer === 1}
              />)}</div>}
              {["changed", "why"].includes(message.answer.intent) &&
                shown.passages.length > 0 && (
                  <section className="axent-answer-section">
                    <strong>{t("Lectura focal", "Focused reading")}</strong>
                    {shown.passages.map((value, j) => (
                      <p key={j}>{value}</p>
                    ))}
                  </section>
                )}
              {shown.known.length > 0 && (
                <section className="axent-answer-section">
                  <strong>{message.answer.intent === "act" ? t("Qué puedes hacer", "What you can do")
                    : message.answer.intent === "research" ? t("Qué investigaría", "What I would look into")
                    : t("Lo que sabemos", "What we know")}</strong>
                  {shown.known.map((value, j) => (
                    <p key={j}>{value}</p>
                  ))}
                </section>
              )}
              {shown.open.length > 0 && (
                <section className="axent-answer-section">
                  <strong>{t("Lo que sigue abierto", "What remains open")}</strong>
                  {shown.open.map((value, j) => (
                    <p key={j}>{value}</p>
                  ))}
                </section>
              )}
              {message.answer.action === "evidence" && shown.basis.length > 0 && (
                <section className="axent-answer-section">
                  <strong>{t("En qué se basa", "What it rests on")}</strong>
                  {shown.basis.map((value, j) => (
                    <p key={j}>{value}</p>
                  ))}
                </section>
              )}
              {!!message.answer.grounding && message.answer.action !== "evidence" && shown.basis.length > 0 && <details className="axent-answer-section">
                <summary>{t("Ver fundamento y límites", "Inspect basis and limits")}</summary>
                {shown.basis.map((value, j) => <p key={j}>{value}</p>)}
                {shown.limits.map((value, j) => <p key={`limit-${j}`}>{value}</p>)}
              </details>}
              {message.answer.action === "evidence" && shown.limits.map((value, j) => <p key={`limit-${j}`}>{value}</p>)}
              {message.answer.action === "research-unavailable" && (
                <section className="axent-answer-section proposed-research">
                  <strong>{t("Investigación propuesta", "Proposed research")}</strong>
                  {message.answer.researchPlan.map((step) => <p key={step}>{step}</p>)}
                  <small>
                    {t(
                      "Propuesta de investigación; no ejecutada.",
                      "Research proposal; not executed.",
                    )}
                  </small>
                </section>
              )}
              {message.answer.sourceRefs.length > 0 && (
                <section className="axent-answer-section axent-provenance">
                  <strong>{t("Fuentes", "Sources")}</strong>
                  {message.answer.sourceRefs.map((ref) => <p key={ref}>{safeSourceLink(ref)
                    ? <a href={safeSourceLink(ref)!} target="_blank" rel="noopener noreferrer">{ref}</a>
                    : ref}</p>)}
                  {message.answer.observedAt.map((value) => (
                    <p key={value}>{new Date(value).toLocaleString(locale)}</p>
                  ))}
                  {message.answer.currentness.map((value) => (
                    <p key={value}>{presentRuntimeCode(value, locale)}</p>
                  ))}
                </section>
              )}
              {(message.answer.publicUnderstandingReportId && onPublicUnderstanding) ? <button className="text-link"
                onClick={() => onPublicUnderstanding(message.answer.publicUnderstandingReportId!)}>
                {t("Ver citas y fundamento", "Inspect quotations and basis")}
              </button> : (message.answer.signalIds.length > 0 || message.answer.action === "evidence") && <button
                className="text-link"
                onClick={
                  message.answer.action === "evidence"
                    ? onEvidence
                    : () => {
                        if (message.answer.signalIds[0])
                          onSignal(message.answer.signalIds[0]);
                      }
                }
              >
                {message.answer.action === "evidence" && !message.answer.signalIds.length
                  ? t("Abrir evidencias disponibles", "Open available evidence")
                  : t("Ver señal y evidencia", "Read signal and evidence")}
              </button>}
            </div>
          </div>
        ); })}
        {busy && (
          <p>
            {t(
              "Leyendo el contexto autorizado…",
              "Reading authorized context…",
            )}
          </p>
        )}
        {error && (
          <p role="alert">
            {t(
              "La explicación no está disponible. Puedes volver a intentarlo.",
              "The explanation is unavailable. You can try again.",
            )}
          </p>
        )}
        <div className="axent-questions">
          {(messages.at(-1)?.answer.productGuide?.followUps ?? questions).map((q) => (
            <button key={q} disabled={busy} onClick={() => void ask(q)}>
              {q}
            </button>
          ))}
        </div>
      </div>
      <AxentComposer
        value={draft}
        onChange={setDraft}
        onSubmit={() => void ask(draft)}
        busy={busy}
        onStop={stop}
      />
    </div>
  );
}
