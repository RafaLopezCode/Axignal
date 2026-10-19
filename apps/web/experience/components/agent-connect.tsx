"use client";

import { useEffect, useState } from "react";
import { Check, Copy, ExternalLink } from "lucide-react";
import { useLocale } from "@/lib/locale";
import { SubscriberMcpConnections } from "./subscriber-mcp-connections";

type Assistant = "claude" | "chatgpt" | "other";

/** Copies a text and says so for a moment; never fails loudly (the text stays selectable). */
export function CopyButton({ text, label, className = "obs-link" }: { text: string; label: string; className?: string }) {
  const { t } = useLocale();
  const [done, setDone] = useState(false);
  async function copy() {
    try { await navigator.clipboard.writeText(text); setDone(true); window.setTimeout(() => setDone(false), 1800); }
    catch { setDone(false); }
  }
  return <button type="button" className={className} onClick={() => void copy()} aria-live="polite">
    {done ? <Check size={14} aria-hidden="true"/> : <Copy size={14} aria-hidden="true"/>}{done ? t("Copiado", "Copied") : label}
  </button>;
}

/**
 * Connect the subscriber's own agent to AXIGNAL through the read-only MCP (ADR-0086,
 * ADR-0095): why it is worth it, how to connect each assistant, what to ask it, and the
 * assistants already connected. The agent reads AXIGNAL's governed findings with their
 * sources and epistemic states; it never changes them.
 */
export function AgentConnectView({ portfolioSize, illustrative = false }: { portfolioSize: number; illustrative?: boolean }) {
  const { t } = useLocale();
  const [endpoint, setEndpoint] = useState("");
  const [assistant, setAssistant] = useState<Assistant>("claude");
  useEffect(() => { setEndpoint(`${window.location.origin}/mcp`); }, []);
  const agency = portfolioSize > 1;
  const steps: Record<Assistant, { name: string; steps: string[]; help: string | null }> = {
    claude: { name: "Claude", help: "https://claude.com/docs/connectors/custom/add-unlisted", steps: [
      t("En Claude, abre Ajustes (o Personalizar) → Conectores → Añadir → Añadir conector personalizado.", "In Claude, open Settings (or Customize) → Connectors → Add → Add custom connector."),
      t("Ponle un nombre (AXIGNAL) y pega la dirección de arriba como URL del servidor MCP remoto.", "Name it (AXIGNAL) and paste the address above as the remote MCP server URL."),
      t("Pulsa Conectar e inicia sesión en AXIGNAL para autorizar la lectura.", "Click Connect and sign in to AXIGNAL to authorize reading."),
      t("En planes de equipo, quien administra la organización añade el conector y cada persona lo conecta con su cuenta.", "On team plans, the organization's admin adds the connector and each person connects it with their own account."),
    ] },
    chatgpt: { name: "ChatGPT", help: "https://help.openai.com/en/articles/12584461-developer-mode-and-mcp-apps-in-chatgpt", steps: [
      t("En ChatGPT, añade un servidor MCP personalizado desde la sección de aplicaciones o plugins (en algunos planes requiere activar el modo desarrollador).", "In ChatGPT, add a custom MCP server from the apps or plugins section (on some plans it requires turning on developer mode)."),
      t("Pega la dirección de arriba como URL del servidor y elige OAuth como autenticación.", "Paste the address above as the server URL and choose OAuth as authentication."),
      t("Acepta el aviso y inicia sesión en AXIGNAL para autorizar la lectura.", "Accept the notice and sign in to AXIGNAL to authorize reading."),
      t("Los menús de ChatGPT cambian a menudo: si no los encuentras, sigue su guía oficial.", "ChatGPT's menus change often: if you cannot find them, follow its official guide."),
    ] },
    other: { name: t("Otro agente MCP", "Another MCP agent"), help: null, steps: [
      t("Cualquier cliente compatible con MCP remoto (HTTP) y OAuth puede conectarse con la misma dirección.", "Any client supporting remote MCP (HTTP) with OAuth can connect with the same address."),
      t("Al conectar, inicia sesión en AXIGNAL y autoriza la lectura.", "When connecting, sign in to AXIGNAL and authorize reading."),
    ] },
  };
  const prompts = [
    t("Con AXIGNAL, resume la visibilidad en buscadores y en respuestas de IA de mi organización y dime qué tres cosas mejorar primero.", "Using AXIGNAL, summarize my organization's visibility in search engines and AI answers and tell me the three things to improve first."),
    t("Con AXIGNAL, ¿qué ha cambiado en mi organización desde la última observación y qué importa de ello?", "Using AXIGNAL, what has changed in my organization since the last observation, and what of it matters?"),
    t("Con AXIGNAL, lista las oportunidades de demanda abiertas que encajan con mi actividad, con su plazo y su fuente.", "Using AXIGNAL, list the open demand opportunities that fit my activity, with their deadline and source."),
    ...(agency ? [
      t("Con AXIGNAL, compara la visibilidad GEO de todos mis clientes y dime cuál necesita atención esta semana y por qué.", "Using AXIGNAL, compare the GEO visibility of all my clients and tell me which needs attention this week and why."),
      t("Con AXIGNAL, prepara un informe mensual para cada cliente con lo observado en sus diez familias, citando las fuentes.", "Using AXIGNAL, prepare a monthly report for each client with what was observed across its ten families, citing the sources."),
    ] : []),
  ];
  const step = steps[assistant];
  return <section className="obs-agent" aria-labelledby="agent-title">
    <header className="obs-agent-head">
      <span className="eyebrow">{t("Tu agente", "Your agent")}</span>
      <h1 id="agent-title">{agency
        ? t("Pregunta a tu agente por todos tus clientes a la vez", "Ask your agent about all your clients at once")
        : t("Interpreta tu AXIGNAL con tu propio agente", "Interpret your AXIGNAL with your own agent")}</h1>
      <p>{t("Conecta AXIGNAL a Claude, ChatGPT u otro agente mediante MCP. Tu agente lee lo que AXIGNAL ha observado y razona con ello donde ya trabajas.", "Connect AXIGNAL to Claude, ChatGPT or another agent through MCP. Your agent reads what AXIGNAL has observed and reasons with it where you already work.")}</p>
    </header>
    <ul className="obs-agent-value">
      <li><strong>{t("Las diez familias y su historia", "The ten families and their history")}</strong><span>{t("Visibilidad, reputación, valor, mercados, relaciones, demanda, actividad, economía, organización y contexto, con lo que ha cambiado entre observaciones.", "Visibility, reputation, value, markets, relationships, demand, activity, economics, organization and context, with what changed between observations.")}</span></li>
      <li><strong>{agency ? fill(t("Tus {n} organizaciones", "Your {n} organizations"), portfolioSize) : t("Toda tu cartera", "Your whole portfolio")}</strong><span>{t("Tu agente puede comparar organizaciones y preparar informes de cada una; una agencia, de todos sus clientes.", "Your agent can compare organizations and prepare reports on each; an agency, on all its clients.")}</span></li>
      <li><strong>{t("Con fuente y estado", "With source and state")}</strong><span>{t("Cada dato llega con su fuente, su fecha y si es observado, potencial o desconocido: tu agente cita en lugar de inventar.", "Each fact arrives with its source, date and whether it is observed, potential or unknown: your agent cites instead of inventing.")}</span></li>
      <li><strong>{t("Solo lectura, bajo tu control", "Read-only, under your control")}</strong><span>{t("Tú autorizas la conexión y puedes retirarla aquí. Tu agente no puede cambiar ningún dato de AXIGNAL.", "You authorize the connection and can withdraw it here. Your agent cannot change any AXIGNAL data.")}</span></li>
    </ul>
    <section className="obs-agent-card" aria-labelledby="agent-connect-title">
      <h2 id="agent-connect-title">{t("1. Copia la dirección de AXIGNAL", "1. Copy AXIGNAL's address")}</h2>
      {endpoint && <p className="obs-agent-endpoint"><code className="mcp-endpoint">{endpoint}</code><CopyButton text={endpoint} label={t("Copiar", "Copy")}/></p>}
      <h2>{t("2. Añádela en tu agente", "2. Add it in your agent")}</h2>
      <div className="obs-agent-tabs" role="tablist" aria-label={t("Agente", "Agent")}>
        {(Object.keys(steps) as Assistant[]).map(key => <button key={key} type="button" role="tab" aria-selected={assistant === key} className="obs-agent-tab" onClick={() => setAssistant(key)}>{steps[key].name}</button>)}
      </div>
      <ol className="obs-agent-steps" role="tabpanel">{step.steps.map(s => <li key={s}>{s}</li>)}</ol>
      {step.help && <p><a className="obs-link" href={step.help} target="_blank" rel="noopener noreferrer">{fill(t("Guía oficial de {name}", "{name}'s official guide"), step.name)}<ExternalLink size={13} aria-hidden="true"/><span className="sr-only">{t("(se abre en otra pestaña)", "(opens in a new tab)")}</span></a></p>}
      <h2>{t("3. Pregúntale", "3. Ask it")}</h2>
      <ul className="obs-agent-prompts">{prompts.map(p => <li key={p}><p>{p}</p><CopyButton text={p} label={t("Copiar pregunta", "Copy question")}/></li>)}</ul>
    </section>
    <section className="obs-agent-card" aria-labelledby="agent-vs-title">
      <h2 id="agent-vs-title">{t("Axent o tu agente", "Axent or your agent")}</h2>
      <p>{t("Axent responde dentro de AXIGNAL, junto a la evidencia que estás viendo. Tu agente es para explorar con libertad, comparar organizaciones, combinar AXIGNAL con tus documentos y redactar informes.", "Axent answers inside AXIGNAL, beside the evidence you are looking at. Your agent is for exploring freely, comparing organizations, combining AXIGNAL with your documents and writing reports.")}</p>
    </section>
    <section className="obs-agent-card">{illustrative
      ? <p>{t("Esto es un ejemplo guiado: la conexión se autoriza con tu cuenta y lee solo tus organizaciones.", "This is a guided example: the connection is authorized with your account and reads only your organizations.")}</p>
      : <SubscriberMcpConnections compact/>}</section>
  </section>;
}

function fill(text: string, value: string | number): string {
  return text.replace(/\{[a-z]+\}/, String(value));
}
