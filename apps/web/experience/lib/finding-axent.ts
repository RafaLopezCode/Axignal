/**
 * AXENT about one finding: every answer is built from that finding's own reading — what was
 * measured, where and when, by which criterion, what to do and what remains open — in the
 * reader's language. Deterministic: no model, no runtime round trip, nothing borrowed from
 * another signal. Used for every finding of every family, so a question about a finding is
 * never answered with the organization's generic narrative.
 */
import type { FamilyId } from "./projection";
import { fill, type Insight } from "./observatory";
import { intentOf, type RuntimeAnswer } from "./runtime-axent";

type Translate = (es: string, en: string) => string;

function unique(values: Array<string | null | undefined>, exclude: Set<string> = new Set()): string[] {
  const seen = new Set(exclude);
  const out: string[] = [];
  for (const value of values) {
    const clean = value?.trim();
    if (!clean || seen.has(clean)) continue;
    seen.add(clean);
    out.push(clean);
  }
  return out;
}

const clip = (value: string, max = 220) => (value.length <= max ? value : `${value.slice(0, max - 1).trimEnd()}…`);

/** A concrete next step when the finding brings none of its own. */
function nextStep(family: FamilyId | null, t: Translate): string {
  switch (family) {
    case "presence": return t("Corrige lo que indica el hallazgo en tu web y vuelve a observar para comprobar si cambia.", "Fix what the finding points to on your website, then observe again to check whether it changes.");
    case "reputation": return t("Revisa las menciones y opiniones citadas en su fuente y vuelve a observar dentro de unas semanas para ver su evolución.", "Review the mentions and reviews cited at their source, and observe again in a few weeks to see how they evolve.");
    case "value": return t("Comprueba que la web describe con claridad lo que ofrece; si falta algo, publícalo y vuelve a observar.", "Check that the website clearly describes what it offers; if something is missing, publish it and observe again.");
    case "markets": return t("Indica en «Dónde buscar demanda» los mercados que te interesan para observarlos de forma directa.", "Set the markets you care about under “Where to look for demand” so they are observed directly.");
    case "relationships": return t("Abre la fuente de cada relación y valida si sigue vigente; una relación declarada no es una confirmada.", "Open the source of each relationship and check whether it still holds; a declared relationship is not a confirmed one.");
    case "demand": return t("Abre la fuente de la oportunidad o del comprador y valora si encaja antes de actuar; es potencial, no un cliente.", "Open the source of the opportunity or buyer and judge the fit before acting; it is potential, not a customer.");
    case "activity": return t("Sigue los cambios con el tiempo en «Evolución»; una sola lectura no muestra una tendencia.", "Follow the changes over time in “Evolution”; a single reading does not show a trend.");
    case "economics": return t("Contrasta la cifra con su fuente y su fecha; si es antigua, búscala en el registro oficial más reciente.", "Check the figure against its source and date; if it is old, look for it in the latest official register.");
    case "organization": return t("Verifica la identidad legal en un registro oficial; hasta entonces, los datos describen la web, no una entidad verificada.", "Verify the legal identity in an official register; until then, the data describes the website, not a verified entity.");
    case "context": return t("Lee la norma o noticia en su fuente y valora si afecta a esta organización.", "Read the rule or news item at its source and judge whether it affects this organization.");
    default: return t("Abre su fuente y vuelve a observar más adelante para comprobar si cambia.", "Open its source and observe again later to check whether it changes.");
  }
}

function sourceLine(source: Insight["sources"][number], locale: string, t: Translate): string {
  const when = source.observedAt ? new Date(source.observedAt).toLocaleString(locale, { dateStyle: "medium", timeStyle: "short" }) : null;
  const head = when ? `${source.label} · ${when}` : source.label;
  return source.quote ? `${head} — «${clip(source.quote)}»` : `${head}${source.url ? "" : ` (${t("sin enlace público", "no public link")})`}`;
}

export function explainFinding({ insight, related, prompt, organizationId, contextId, t, locale }: {
  insight: Insight;
  /** The other findings of the same reading: changes and unknowns of the same family. */
  related: Insight[];
  prompt: string;
  organizationId: string;
  contextId: string;
  t: Translate;
  locale: string;
}): RuntimeAnswer {
  const intent = intentOf(prompt);
  const family = related.filter(i => i.id !== insight.id && i.family !== null && i.family === insight.family);
  const changes = family.filter(i => i.id.startsWith("CHANGE:") || i.previous !== null);
  const familyUnknowns = family.filter(i => i.lane === "unknown");
  // Internal codes (SCREAMING_CASE) never reach a reader: such rows are left out.
  const proof = insight.proof.filter(p => !/[A-Z][A-Z0-9]*_[A-Z0-9_]+/.test(p.value)).map(p => `${p.label}: ${p.value}`);
  const limits = unique([...insight.reasoning, ...(insight.limits ?? [])]);
  const sources = insight.sources.map(s => sourceLine(s, locale, t));
  const step = insight.proposal ?? nextStep(insight.family, t);

  let summary: string;
  let known: string[] = [];
  let open: string[] = [];
  let basis: string[] = [];
  switch (intent) {
    case "why":
      summary = insight.why || insight.headline;
      known = unique([...insight.meaning], new Set([summary]));
      open = limits;
      break;
    case "changed":
      summary = insight.previous !== null
        ? fill(t("Antes: {before}. Ahora: {now}.", "Before: {before}. Now: {now}."), { before: insight.previous, now: insight.headline })
        : changes.length
          ? t("No hay una lectura anterior comparable de este hallazgo; en su familia cambió lo siguiente:", "There is no comparable earlier reading of this finding; in its family, the following changed:")
          : t("No hay una lectura anterior comparable de este hallazgo, así que no se declara ningún cambio.", "There is no comparable earlier reading of this finding, so no change is declared.");
      known = changes.map(i => i.headline);
      break;
    case "unknown":
      summary = limits.length || familyUnknowns.length
        ? t("Esto es lo que sigue abierto sobre este hallazgo:", "This is what remains open about this finding:")
        : t("No hay nada abierto declarado sobre este hallazgo en esta lectura.", "Nothing open is declared about this finding in this reading.");
      open = unique([...limits, ...familyUnknowns.map(i => i.headline)]);
      break;
    case "evidence":
      summary = sources.length
        ? sources.length === 1
          ? t("Lo sabemos por esta fuente, con lo que se midió y cuándo:", "We know it from this source, with what was measured and when:")
          : fill(t("Lo sabemos por estas {n} fuentes, con lo que se midió y cuándo:", "We know it from these {n} sources, with what was measured and when:"), { n: sources.length })
        : t("Este hallazgo no tiene una fuente pública enlazable; esto es lo que se midió:", "This finding has no linkable public source; this is what was measured:");
      known = proof;
      basis = sources;
      open = limits;
      break;
    case "research":
      summary = t("Lo siguiente que conviene hacer:", "What to do next:");
      known = [step];
      open = limits;
      break;
    default:
      summary = insight.headline;
      known = unique([insight.why, ...insight.meaning, ...proof], new Set([summary]));
      open = limits;
  }
  // No sentence appears twice in one answer.
  const shown = new Set([summary]);
  known = unique(known, shown); known.forEach(v => shown.add(v));
  basis = unique(basis, shown); basis.forEach(v => shown.add(v));
  open = unique(open, shown);
  return {
    organizationId, contextId, signalIds: [], intent, summary,
    known, openQuestions: open, evidenceBasis: basis, evidenceLimits: [],
    researchPlan: [], passages: [],
    action: intent === "evidence" ? "evidence" : "focus",
    sourceRefs: unique(insight.sources.map(s => s.url ?? "")),
    observedAt: [], currentness: [],
  };
}
