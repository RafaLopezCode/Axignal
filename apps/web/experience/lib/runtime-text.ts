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
    pattern: /^The authorized public homepage was reachable and contained deterministic document text when (.+) observed it\. Visual visibility remains UNKNOWN when external stylesheet effects are unresolved\.$/,
    es: m => `La página pública era accesible y su texto se pudo leer cuando ${m[1]} la observó. No se ha comprobado cómo cambian su aspecto los estilos externos.`,
  },
  {
    pattern: /^This (?:observation|signal) covers only the authorized public homepage at this observation time\. (?:Search, generative, social, reputation and other public surfaces remain UNKNOWN|Search, AI assistants, reputation and other surfaces are read by their own instruments, in their families)\.$/,
    es: () => "Esta señal cubre solo la página pública en el momento de la observación. La búsqueda, los asistentes de IA, la reputación y otras superficies se miden con sus propios instrumentos, en sus familias.",
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
