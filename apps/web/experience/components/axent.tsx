"use client";
import { useChat, type Chat } from "@ai-sdk/react";

import { useEffect, useId, useRef, useState } from "react";
import {
  ArrowRight,
  ArrowUpRight,
  Send,
  Square,
  RotateCcw,
  BookOpen,
  Info,
} from "lucide-react";
import { useLocale } from "@/lib/locale";
import {
  project,
  families,
  dateLabel,
  type ProjectionContext,
} from "@/lib/projection";
import { validatePlan, type CompositionPlan } from "@/lib/governance";
import type { AxentMessage } from "@/lib/axent-contract";
import { Badge, Observer, AxentIdentity } from "./ui";

export function Axent({
  chat,
  draft,
  onDraft,
  context,
  onSignal,
  onEvidence,
}: {
  chat: Chat<AxentMessage>;
  draft: string;
  onDraft: (value: string) => void;
  context: ProjectionContext;
  onSignal: (id: string) => void;
  onEvidence: (id: string) => void;
}) {
  const { t, copy, locale } = useLocale();
  const fieldId = useId();
  const input = draft;
  const setInput = onDraft;
  const [more, setMore] = useState(false);
  const {
    messages,
    sendMessage,
    status,
    error,
    stop,
    regenerate,
    setMessages,
  } = useChat<AxentMessage>({ chat });
  const messagesRef = useRef<HTMLDivElement>(null);
  const busy = status === "submitted" || status === "streaming";

  useEffect(() => {
    const node = messagesRef.current;
    if (node) node.scrollTop = node.scrollHeight;
  }, [messages, status]);
  const projection = project(context);
  const signal =
    projection.signals.find((s) => s.id === context.signalId) ??
    projection.signals.find((s) => s.family === context.family);
  const family = families.find((f) => f.id === context.family)!;
  const questions = signal
    ? [
        t("¿Por qué merece atención?", "Why does it deserve attention?"),
        t("¿Qué evidencia la sostiene?", "What evidence supports it?"),
      ]
    : [
        t("Explícame este contexto", "Explain this context"),
        t("¿Qué sigue abierto?", "What remains open?"),
      ];
  async function ask(text: string) {
    if (!text.trim() || busy) return;
    setInput("");
    await sendMessage({ text: text.trim() });
  }
  return (
    <div className="axent-panel">
      <header className="axent-header">
        <AxentIdentity />
        <button
          className="icon-button"
          aria-label={t(
            "Nueva conversación contextual",
            "New contextual conversation",
          )}
          title={t("Nueva conversación", "New conversation")}
          onClick={() => {
            void stop();
            setMessages([]);
          }}
        >
          <RotateCcw size={15} />
        </button>
      </header>
      <div className="axent-scope">
        <span className="mono">
          {t(
            "INVESTIGA · EXPLICA · ACOMPAÑA",
            "INVESTIGATES · EXPLAINS · GUIDES",
          )}
        </span>
        <div>
          {projection.organization.name}
          <span>/</span>
          {copy(family.name)}
        </div>
        <small>
          {dateLabel(context.asOf, locale)}
          {context.signalId
            ? " / " + t("Señal seleccionada", "Selected signal")
            : ""}
        </small>
      </div>
      <div
        className="axent-messages"
        ref={messagesRef}
        aria-live="polite"
        aria-relevant="additions text"
      >
        {messages.length === 0 ? (
          <div className="axent-welcome">
            <Observer scene="explain" className="axent-observer" />
            <h2>
              {t(
                "Miremos con un poco más de contexto.",
                "Let’s look with a little more context.",
              )}
            </h2>
            <p>
              {signal
                ? t(
                    "Puedo explicar esta señal, contrastar lo que sostiene y señalar lo que todavía no sabemos.",
                    "I can explain this signal, examine its basis and point to what we do not yet know.",
                  )
                : t(
                    "Te acompaño a investigar y entender esta parte del panorama.",
                    "I help you investigate and understand this part of the panorama.",
                  )}
            </p>
            <span className="axent-example">
              {t(
                "Demo de explicación contextual · sin modelo en vivo",
                "Contextual explanation demo · no live model",
              )}
            </span>
            <div className="axent-questions">
              {questions.map((q) => (
                <button key={q} onClick={() => void ask(q)}>
                  {q}
                  <ArrowRight size={15} />
                </button>
              ))}
            </div>
            <button
              className="text-link axent-more"
              onClick={() => setMore(!more)}
              aria-expanded={more}
            >
              {more
                ? t("Menos preguntas", "Fewer questions")
                : t("Otra perspectiva", "Another perspective")}
            </button>
            {more && (
              <button
                className="axent-extra"
                onClick={() =>
                  void ask(
                    t(
                      "¿Cómo cambia el contexto en el tiempo?",
                      "How does context change over time?",
                    ),
                  )
                }
              >
                {t("¿Qué cambia en el tiempo?", "What changes over time?")}
                <ArrowRight size={14} />
              </button>
            )}
          </div>
        ) : (
          messages.map((message) => (
            <div className={"axent-message " + message.role} key={message.id}>
              <span className="message-author">
                {message.role === "user" ? t("Tú", "You") : "Axent"}
              </span>
              {message.parts.map((part, i) =>
                part.type === "text" ? (
                  <p key={i}>{part.text}</p>
                ) : part.type === "tool-compose" &&
                  part.state === "output-available" ? (
                  <RegisteredComposition
                    key={i}
                    plan={part.output}
                    context={context}
                    onSignal={onSignal}
                    onEvidence={onEvidence}
                  />
                ) : part.type === "tool-compose" &&
                  part.state === "output-error" ? (
                  <div key={i} className="inline-error">
                    {t(
                      "Esta composición no pudo prepararse.",
                      "This composition could not be prepared.",
                    )}
                  </div>
                ) : null,
              )}
            </div>
          ))
        )}
        {busy && (
          <div className="axent-busy">
            <span className="quiet-dot" />
            {t(
              "Preparando explicación del ejemplo…",
              "Preparing the example explanation…",
            )}
          </div>
        )}
        {error && (
          <div className="inline-error" role="alert">
            <Info size={16} />
            <p>
              {t(
                "No pudimos obtener la explicación. Tu contexto sigue intacto.",
                "We could not get the explanation. Your context is preserved.",
              )}
            </p>
            <button className="text-link" onClick={() => void regenerate()}>
              {t("Reintentar", "Retry")}
              <RotateCcw size={14} />
            </button>
          </div>
        )}
      </div>
      <div className="axent-compose">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void ask(input);
          }}
        >
          <label className="sr-only" htmlFor={"axent-input-" + fieldId}>
            {t("Pregunta sobre este contexto", "Ask about this context")}
          </label>
          <textarea
            id={"axent-input-" + fieldId}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            maxLength={1000}
            placeholder={t(
              "Pregunta sobre este contexto…",
              "Ask about this context…",
            )}
            rows={2}
            onKeyDown={(e) => {
              if (
                e.key === "Enter" &&
                !e.shiftKey &&
                !e.nativeEvent.isComposing
              ) {
                e.preventDefault();
                void ask(input);
              }
            }}
          />
          {busy ? (
            <button
              type="button"
              className="send-button"
              onClick={() => void stop()}
              aria-label={t("Detener respuesta", "Stop response")}
            >
              <Square size={13} />
            </button>
          ) : (
            <button
              className="send-button"
              type="submit"
              disabled={!input.trim()}
              aria-label={t("Enviar pregunta", "Send question")}
            >
              <ArrowUpRight size={18} />
            </button>
          )}
        </form>
        <p>
          {t(
            "Explica la evidencia. No decide la verdad.",
            "Explains evidence. Does not decide truth.",
          )}
        </p>
      </div>
    </div>
  );
}
function RegisteredComposition({
  plan,
  context,
  onSignal,
  onEvidence,
}: {
  plan: CompositionPlan;
  context: ProjectionContext;
  onSignal: (id: string) => void;
  onEvidence: (id: string) => void;
}) {
  const { t, copy } = useLocale();
  const validated = validatePlan(plan, context);
  if (!validated.success)
    return (
      <p className="inline-error">
        {t(
          "Composición fuera de contexto. Vuelve a solicitarla.",
          "Composition outside context. Request it again.",
        )}
      </p>
    );
  const p = project(context);
  const registry = {
    signal: (ref: string) => {
      const s = p.signals.find((s) => s.id === ref)!;
      return (
        <button className="generated-signal" onClick={() => onSignal(ref)}>
          <Badge state={s.epistemic} />
          <strong>{copy(s.title)}</strong>
          <span>
            {t("Abrir en el Panorama", "Open in Panorama")}
            <ArrowUpRight size={15} />
          </span>
        </button>
      );
    },
    evidence: (ref: string) => {
      const e = p.evidence.find((e) => e.id === ref)!;
      return (
        <button className="generated-evidence" onClick={() => onEvidence(ref)}>
          <BookOpen size={16} />
          <span>{copy(e.title)}</span>
          <ArrowUpRight size={15} />
        </button>
      );
    },
    context: (_: string) => (
      <div className="generated-context">
        <strong>{p.organization.name}</strong>
        <p>
          {t(
            "El contexto permanece abierto; no hay una conclusión que inventar.",
            "Context remains open; there is no conclusion to invent.",
          )}
        </p>
      </div>
    ),
  };
  return (
    <div className="registered-composition">
      {validated.data.items.map((item) => (
        <div key={item.component + item.ref} data-priority={item.priority}>
          {registry[item.component](item.ref)}
        </div>
      ))}
    </div>
  );
}
