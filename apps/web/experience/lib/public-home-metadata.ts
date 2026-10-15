import type { Locale } from "./languages";

/**
 * Canonical root-page metadata is English at build time. After the visitor's
 * language is resolved, keep the visible document title/description coherent
 * with the displayed landing. This is NOT a replacement for localized SSR
 * landing URLs if market-specific organic search becomes a requirement.
 */
export const HOME_METADATA: Record<Locale, { title: string; description: string }> = {
  es: { title: "AXIGNAL — Qué cambia alrededor de tu empresa y por qué importa", description: "Inteligencia empresarial y económica basada en evidencia pública: AXIGNAL observa las organizaciones que eliges y explica qué cambia, con fuente y fecha." },
  en: { title: "AXIGNAL — What changes around your company, and why it matters", description: "Business and economic intelligence from public evidence: AXIGNAL observes the organizations you choose and shows what changes, with source and date." },
  de: { title: "AXIGNAL — Was sich um dein Unternehmen ändert und warum es zählt", description: "AXIGNAL beobachtet Organisationen anhand öffentlicher Quellen, verfolgt Veränderungen und erklärt sie mit Quelle und Datum." },
  fr: { title: "AXIGNAL — Ce qui change autour de votre entreprise, et son impact", description: "AXIGNAL observe les organisations dans les sources publiques et explique les changements en indiquant leurs sources et leurs dates." },
  it: { title: "AXIGNAL — Cosa cambia intorno alla tua azienda e perché conta", description: "AXIGNAL osserva le organizzazioni nelle fonti pubbliche e spiega i cambiamenti con fonti e date." },
  pt: { title: "AXIGNAL — O que muda à volta da sua empresa e porque importa", description: "AXIGNAL observa organizações em fontes públicas e explica as mudanças com fontes e datas." },
};
