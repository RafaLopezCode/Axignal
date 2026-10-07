import type { Copy } from "./languages";

const c = (es: string, en: string): Copy => ({ es, en });

/**
 * The Human Intelligence Funnel: one reading, four depths, the same names everywhere.
 *
 * 1 what is happening (a short human sentence) → 2 why it matters → 3 how AXIGNAL
 * knows it (source, method, time) → 4 all the evidence (provenance, currentness,
 * uncertainty). Lenses, signal tabs and Axent's suggested questions all use these
 * words, so a person meets the same depth with the same name wherever they are.
 */
export const funnelLayers = {
  1: { label: c("Síntesis", "Glance"), question: c("¿Qué está pasando?", "What is happening?") },
  2: { label: c("Comprender", "Understand"), question: c("¿Por qué importa?", "Why does it matter?") },
  3: { label: c("Razonamiento", "Reasoning"), question: c("¿Cómo lo sabe AXIGNAL?", "How does AXIGNAL know?") },
  4: { label: c("Evidencia", "Evidence"), question: c("Ver toda la evidencia", "Inspect all the evidence") },
} as const;

export type FunnelLayer = keyof typeof funnelLayers;
