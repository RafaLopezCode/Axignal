"use client";
import { useEffect, useRef, useState } from "react";
import { RotateCcw } from "lucide-react";
import type { RuntimeProjection } from "@/lib/runtime-projection";
import type { RuntimeAnswer } from "@/lib/runtime-axent";
import { useLocale } from "@/lib/locale";
import { AxentIdentity, IconButton } from "./ui";
import { AxentComposer } from "./axent-composer";
export function useRuntimeAxent(
  projection: RuntimeProjection,
  signalId: string | null,
) {
  const { t } = useLocale();
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
  }, [projection.context.id, signalId]);
  async function ask(question: string) {
    if (!question.trim() || busy) return;
    const request = new AbortController();
    controller.current = request;
    setBusy(true);
    setError(false);
    setDraft("");
    try {
      const response = await fetch("/api/axent", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          mode: "runtime",
          prompt: question,
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
  conversation,
}: {
  projection: RuntimeProjection;
  signalId: string | null;
  onEvidence: () => void;
  onSignal: (id: string) => void;
  conversation: ReturnType<typeof useRuntimeAxent>;
}) {
  const { t } = useLocale();
  const { draft, setDraft, busy, error, messages, ask, stop, clear } =
    conversation;
  const questions = [
    t("Qué sabes", "What do you know"),
    t("Qué cambió", "What changed"),
    t("Por qué importa", "Why it matters"),
    t("Qué sigue abierto", "What remains open"),
    t("Cómo lo sabes", "How do you know"),
    t("Qué investigarías después", "What would you investigate next"),
  ];
  return (
    <div className="axent-panel">
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
          {t("CONTEXTO AUTORIZADO", "AUTHORIZED CONTEXT")}
        </span>
        <strong>{projection.organization.name}</strong>
        <small>
          {signalId
            ? t("Señal seleccionada", "Selected signal")
            : t("Panorama", "Panorama")}
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
              {t(
                "Lectura de la evidencia disponible. La investigación nueva requiere herramientas autorizadas.",
                "Reading available evidence. New research requires authorized tools.",
              )}
            </p>
          </div>
        )}
        {messages.map((message, i) => (
          <div key={i}>
            <div className="axent-message user">
              <p>{message.question}</p>
            </div>
            <div className="axent-message">
              <span className="message-author">AXENT</span>
              {message.answer.passages.map((p, j) => (
                <p key={j}>{p}</p>
              ))}
              {message.answer.action === "research-unavailable" && (
                <p>
                  {t(
                    "No hay herramientas de investigación conectadas a esta lectura. Estas preguntas siguen abiertas.",
                    "No research tools are connected to this reading. These questions remain open.",
                  )}
                </p>
              )}
              <button
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
                {t("Ver señal y evidencia", "Read signal and evidence")}
              </button>
            </div>
          </div>
        ))}
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
          {questions.map((q) => (
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
