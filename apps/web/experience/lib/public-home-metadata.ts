import type { Locale } from "./languages";

/**
 * Canonical root-page metadata is English at build time. After the visitor's
 * language is resolved, keep the visible document title/description coherent
 * with the displayed landing. This is NOT a replacement for localized SSR
 * landing URLs if market-specific organic search becomes a requirement.
 */
export const HOME_METADATA: Record<Locale, { title: string; description: string }> = {
  es: { title: "AXIGNAL — ¿Qué está cambiando alrededor de tu empresa, y por qué importa?", description: "AXIGNAL observa continuamente las organizaciones que eliges en fuentes públicas, recuerda lo que encuentra y explica qué cambia, con fuente y fecha." },
  en: { title: "AXIGNAL — What is changing around your company, and why does it matter?", description: "AXIGNAL continuously observes the organizations you choose in public sources, remembers what it finds, and shows what changes, with source and date." },
  de: { title: "AXIGNAL — Was verändert sich rund um dein Unternehmen, und warum ist das wichtig?", description: "AXIGNAL beobachtet Organisationen anhand öffentlicher Quellen, verfolgt Veränderungen und erklärt sie mit Quelle und Datum." },
  fr: { title: "AXIGNAL — Qu'est-ce qui change autour de votre entreprise, et pourquoi est-ce important ?", description: "AXIGNAL observe les organisations dans les sources publiques et explique les changements en indiquant leurs sources et leurs dates." },
  it: { title: "AXIGNAL — Cosa sta cambiando intorno alla tua azienda, e perché è importante?", description: "AXIGNAL osserva le organizzazioni nelle fonti pubbliche e spiega i cambiamenti con fonti e date." },
  pt: { title: "AXIGNAL — O que está a mudar à volta da sua empresa, e porque importa?", description: "AXIGNAL observa organizações em fontes públicas e explica as mudanças com fontes e datas." },
};
