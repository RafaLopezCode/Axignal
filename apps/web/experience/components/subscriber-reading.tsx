"use client";
import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport } from "ai";
import { useEffect, useMemo, useRef, useState } from "react";
import { useLocale } from "@/lib/locale";
import { acceptsReadingPlan, type ReadingPlan, type SubscriberReadingMessage } from "@/lib/subscriber-presentation";
import type { RuntimeProjection } from "@/lib/runtime-projection";
import { RuntimeEvidenceJourney, RuntimeSignalReading } from "./runtime-product";
export function SubscriberReading({ projection, revision }: { projection: RuntimeProjection; revision: string }) {
  const { t, locale } = useLocale();
  const [plan, setPlan] = useState<ReadingPlan | null>(null);
  const requested = useRef<ReadingPlan["intent"]>("summary");
  const transport = useMemo(() => new DefaultChatTransport<SubscriberReadingMessage>({ api: "/api/subscriber/reading",
    prepareSendMessagesRequest: () => ({ body: { focusId: projection.context.id, revision, intent: requested.current, locale } }),
  }), [projection.context.id, revision, locale]);
  const chat = useChat<SubscriberReadingMessage>({ transport, onData: part => {
    if (part.type === "data-presentation" && acceptsReadingPlan(part.data, projection, revision)) setPlan(part.data);
  } });
  const stop = chat.stop;
  useEffect(() => () => { void stop(); }, [stop]);
  async function ask(intent: ReadingPlan["intent"]) {
    if (chat.status === "submitted" || chat.status === "streaming") return;
    requested.current = intent; setPlan(null); chat.setMessages([]);
    await chat.sendMessage({ text: intent });
  }
  const readingNodes = plan ? projection.nodes.filter(item => plan.refs.includes(item.id)) : projection.nodes;
  return <div><div className="subscriber-row-actions" aria-label={t("Tu lectura", "Your reading")}>
    <button className="text-link" onClick={() => void ask("summary")} disabled={chat.status === "submitted" || chat.status === "streaming"}>{t("Comprender", "Understand")}</button>
    <button className="text-link" onClick={() => void ask("evidence")} disabled={chat.status === "submitted" || chat.status === "streaming"}>{t("Cómo lo sabe AXIGNAL", "How AXIGNAL knows")}</button>
    <button className="text-link" onClick={() => void ask("limits")} disabled={chat.status === "submitted" || chat.status === "streaming"}>{t("Lo que sigue abierto", "What remains open")}</button>
  </div><div aria-live="polite">{chat.status === "submitted" || chat.status === "streaming" ? <p>{t("Leyendo las evidencias…", "Reading the evidence…")}</p> : null}
    {chat.error && <p role="alert">{t("La lectura ha cambiado o no está disponible. Actualiza el contexto antes de continuar.", "The reading has changed or is unavailable. Refresh the context before continuing.")}</p>}
    {chat.messages.filter(item => item.role === "assistant").map(item => <div key={item.id}>{item.parts.map((part, index) => part.type === "text" ? <p key={index}>{part.text}</p> : null)}</div>)}
  </div>{readingNodes.map(node => plan?.intent === "evidence" ? <RuntimeEvidenceJourney key={node.id} signal={node} organizationName={projection.organization.name}/> : <RuntimeSignalReading key={node.id} signal={node} organizationName={projection.organization.name}/>)}
  </div>;
}
