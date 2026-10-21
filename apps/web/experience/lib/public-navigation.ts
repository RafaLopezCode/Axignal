import { words, marketingPath, PUBLIC_EDITORIAL_LABEL } from "./marketing-locale";
import type { Locale } from "./languages";

export type PublicLocaleRoute = { locale: Locale; href: string };

// Presentation and existing public destinations only. Never import product/demo navigation.
export const publicNavigationCopy = {
  menu: words("Menú", "Menu", "Menu", "Menü", "Menu", "Menu"),
  explore: words("Explora AXIGNAL", "Explore AXIGNAL", "Explorez AXIGNAL", "AXIGNAL entdecken", "Esplora AXIGNAL", "Explora AXIGNAL"),
  discover: words("Qué puedes descubrir", "What you can discover", "Ce que vous pouvez découvrir", "Was Sie entdecken können", "Cosa puoi scoprire", "O que pode descobrir"),
  audience: words("Para quién", "Who it is for", "Pour qui", "Für wen", "Per chi", "Para quem"),
  how: words("Cómo funciona", "How it works", "Comment ça marche", "So funktioniert es", "Come funziona", "Como funciona"),
  pricing: words("Precios", "Pricing", "Tarifs", "Preise", "Prezzi", "Preços"),
  observe: words("Qué observa", "What it observes", "Ce qu’il observe", "Was es beobachtet", "Cosa osserva", "O que observa"),
  sectors: words("Para tu sector", "For your industry", "Pour votre secteur", "Für Ihre Branche", "Per il tuo settore", "Para o seu setor"),
  example: words("Explorar un ejemplo", "Explore an example", "Explorer un exemple", "Beispiel erkunden", "Esplora un esempio", "Explorar um exemplo"),
  start: words("Empezar con una empresa", "Start with a company", "Commencer avec une entreprise", "Mit einem Unternehmen starten", "Inizia con un’azienda", "Começar com uma empresa"),
  signIn: words("Acceder", "Sign in", "Se connecter", "Anmelden", "Accedi", "Entrar"),
  language: words("Idioma", "Language", "Langue", "Sprache", "Lingua", "Idioma"),
  contact: words("Contacto", "Contact", "Contact", "Kontakt", "Contatto", "Contacto"),
  resources: words("Más sobre AXIGNAL", "More about AXIGNAL", "En savoir plus sur AXIGNAL", "Mehr über AXIGNAL", "Scopri AXIGNAL", "Mais sobre AXIGNAL"),
  trust: words("Confianza y políticas", "Trust and policies", "Confiance et politiques", "Vertrauen und Richtlinien", "Fiducia e politiche", "Confiança e políticas"),
  rights: words("Tus datos y derechos", "Your data and rights", "Vos données et droits", "Ihre Daten und Rechte", "I tuoi dati e diritti", "Os seus dados e direitos"),
};

export function publicNavigation(locale: Locale, preview = false) {
  const c = publicNavigationCopy;
  const home = marketingPath(preview ? "/landing-lab" : "/", locale);
  return {
    home,
    chapters: [
      { href: home + "#discover", label: c.discover[locale] },
      { href: home + "#audience", label: c.audience[locale] },
      { href: home + "#how", label: c.how[locale] },
      { href: home + "#pricing", label: c.pricing[locale] },
    ],
    pages: [
      { href: marketingPath("/data", locale), label: c.observe[locale] },
      { href: marketingPath("/industries", locale), label: c.sectors[locale] },
      { href: marketingPath("/knowledge", locale), label: PUBLIC_EDITORIAL_LABEL },
      { href: "/contact", label: c.contact[locale] },
    ],
    trust: [
      { href: "/policies", label: c.trust[locale] },
      { href: "/gdpr", label: c.rights[locale] },
      { href: home + "#weekly-brief", label: "Newsletter" },
    ],
  };
}
