/**
 * The governed runtime words its signals in English. Where the reader reads Spanish, the sentences it is known
 * to emit are shown in Spanish; anything else is shown exactly as the runtime wrote it. Nothing is invented,
 * reworded or completed: a sentence not listed here is never translated by guesswork.
 */
type Template = { pattern: RegExp; es: (match: RegExpMatchArray) => string };

const TEMPLATES: Template[] = [
  { pattern: /^(.+)'s public homepage is observable from the outside$/, es: m => `La web pública de ${m[1]} es observable desde fuera` },
  {
    pattern: /^(.+) retrieved the public homepage through the governed source sensor and can trace this Xignal back to the stored observation\.$/,
    es: m => `${m[1]} obtuvo la web pública mediante el sensor de fuentes gobernado y puede rastrear este Xignal hasta la observación almacenada.`,
  },
  {
    pattern: /^The authorized public homepage was reachable and contained visible text when (.+) observed it\.$/,
    es: m => `La web pública autorizada era accesible y contenía texto visible cuando ${m[1]} la observó.`,
  },
  {
    pattern: /^This observation covers only the authorized public homepage at this observation time\. Search, generative, social, reputation and other public surfaces remain UNKNOWN\.$/,
    es: () => "Esta observación cubre solo la web pública autorizada en el momento de la observación. La búsqueda, la generativa, las redes sociales, la reputación y otras superficies públicas siguen siendo DESCONOCIDAS.",
  },
];

export function runtimeText(text: string, locale: string): string {
  if (locale !== "es") return text;
  for (const { pattern, es } of TEMPLATES) {
    const match = text.match(pattern);
    if (match) return es(match);
  }
  return text;
}
