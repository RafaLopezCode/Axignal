import type { Locale } from "./languages";

type FocusCopy = { moment: string; attention: string; proof: string; findings: string; previous: string; next: string; invitation: string; caption: string };
export const focusCopy: Record<Locale, FocusCopy> = {
  es: { moment: "Elige un momento", attention: "Qué quieres comprender", proof: "Por qué lo dice AXIGNAL", findings: "Explorar hallazgos", previous: "Hallazgo anterior", next: "Siguiente hallazgo", invitation: "Mira de dónde sale.", caption: "Cambia de fecha. Explora un hallazgo. Abre su evidencia." },
  en: { moment: "Choose a moment", attention: "What you want to understand", proof: "Why AXIGNAL says so", findings: "Explore findings", previous: "Previous finding", next: "Next finding", invitation: "See where it comes from.", caption: "Change the date. Explore a finding. Open its evidence." },
  de: { moment: "Wähle einen Zeitpunkt", attention: "Was du verstehen möchtest", proof: "Warum AXIGNAL das sagt", findings: "Erkenntnisse erkunden", previous: "Vorherige Erkenntnis", next: "Nächste Erkenntnis", invitation: "Sieh nach, woher es kommt.", caption: "Ändere das Datum. Erkunde eine Erkenntnis. Öffne ihre Belege." },
  pt: { moment: "Escolhe um momento", attention: "O que queres compreender", proof: "Porque o diz a AXIGNAL", findings: "Explorar descobertas", previous: "Descoberta anterior", next: "Descoberta seguinte", invitation: "Vê de onde vem.", caption: "Muda a data. Explora uma descoberta. Abre a sua evidência." },
  fr: { moment: "Choisis un moment", attention: "Ce que tu veux comprendre", proof: "Pourquoi AXIGNAL le dit", findings: "Explorer les constats", previous: "Constat précédent", next: "Constat suivant", invitation: "Regarde d’où cela vient.", caption: "Change la date. Explore un constat. Ouvre ses preuves." },
  it: { moment: "Scegli un momento", attention: "Cosa vuoi comprendere", proof: "Perché AXIGNAL lo dice", findings: "Esplora i risultati", previous: "Risultato precedente", next: "Risultato successivo", invitation: "Guarda da dove viene.", caption: "Cambia data. Esplora un risultato. Apri le sue prove." },
};

export const exampleExcerpt: Record<Locale, string> = {
  es: "Selección del ejemplo: un hallazgo por contexto.",
  en: "Example selection: one finding per context.",
  de: "Auswahl aus dem Beispiel: eine Erkenntnis pro Kontext.",
  pt: "Seleção do exemplo: uma descoberta por contexto.",
  fr: "Sélection de l’exemple : un constat par contexte.",
  it: "Selezione dell’esempio: un risultato per contesto.",
};
