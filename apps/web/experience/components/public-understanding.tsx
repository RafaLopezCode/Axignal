"use client";

import { useLocale } from "@/lib/locale";
import { useEvidenceLink } from "./evidence-link-context";
import { type PublicUnderstanding, type UnderstandingDimension } from "@/lib/subscriber-contracts";

type T = (es: string, en: string) => string;
export function dimensionCopy(dimension: string, t: T): string {
  if (dimension === "offer") return t("Qué ofrece", "What it offers");
  if (dimension === "audience") return t("Para quién", "For whom");
  return t("Qué resultado comunica", "What outcome it communicates");
}
export function stateCopy(state: string, t: T): string {
  if (state === "STRENGTH") return t("Fortaleza sustentada", "Evidence-backed strength");
  if (state === "CONSTRUCTIVE_GAP") return t("Oportunidad de aclaración", "Opportunity to clarify");
  if (state === "UNRESOLVED") return t("Interpretación sin resolver", "Unresolved interpretation");
  return t("Comprensión incierta", "Uncertain understanding");
}
export function causeCopy(cause: string, t: T): string {
  if (cause === "INSTRUMENT_ERROR") return t("El instrumento falló o no superó sus controles. No permite valorar la comunicación de la empresa.", "The instrument failed or did not pass its controls. It cannot assess the company's communication.");
  if (cause === "PROVIDER_INPUT_NOT_AUTHORIZED") return t("Faltan derechos para enviar estas fuentes al instrumento. La visibilidad pública no concede ese permiso.", "Rights to send these sources to the instrument are missing. Public visibility does not grant that permission.");
  if (cause === "CONTENT_RIGHTS_WITHDRAWN") return t("Ya no hay permiso para conservar o mostrar estas citas, así que se han retirado. Una nueva lectura necesita derechos vigentes y una nueva observación.", "Permission to keep or show these quotations is no longer in place, so they were removed. A new reading needs current rights and a new observation.");
  if (cause === "CONTENT_EXPIRED") return t("Las citas han caducado y se han retirado. Hace falta una nueva observación.", "The citations expired and were removed. A new observation is needed.");
  if (cause === "OBSERVATION_MISS") return t("La adquisición fue insuficiente. Puede faltar una página o un fragmento; esto no demuestra una deficiencia de comunicación.", "Acquisition was insufficient. A page or excerpt may be missing; this does not demonstrate a communication deficiency.");
  if (cause === "CONTRADICTION") return t("El instrumento encontró declaraciones incompatibles. Pueden corresponder a ofertas o momentos distintos; ambas fuentes siguen abiertas a revisión.", "The instrument found incompatible statements. They may concern different offers or periods; both sources remain open to review.");
  if (cause === "AMBIGUITY") return t("El texto admite varias interpretaciones. La causa sigue sin resolverse.", "The text permits multiple interpretations. The cause remains unresolved.");
  if (cause === "BUDGET_EXHAUSTED") return t("No se ejecutó la medición dentro del presupuesto disponible.", "The measurement did not run within the available budget.");
  if (cause === "INSTRUMENT_UNAVAILABLE") return t("El instrumento no está disponible. La clasificación económica no sustituye esta medición.", "The instrument is unavailable. Economic classification does not replace this measurement.");
  if (cause === "EXPLICIT_STATEMENT_SELECTED") return t("El instrumento pudo vincular esta pregunta con una declaración pública explícita. Es una interpretación condicionada, no una verificación del negocio.", "The instrument linked this question to an explicit public statement. This is a conditioned interpretation, not business verification.");
  if (cause === "REPRESENTATION_LIMITATION_POSSIBLE") return t("En las citas inspeccionadas, el instrumento no encontró una respuesta explícita a esta pregunta. El alcance es la muestra, no toda la comunicación de la organización.", "In the inspected quotations, the instrument did not find an explicit answer to this question. The scope is the sample, not all of the organization's communication.");
  return t("La información o el juicio no bastan para concluir. La incertidumbre del instrumento no es un defecto empresarial.", "The information or judgment is insufficient to conclude. Instrument uncertainty is not a business defect.");
}
export function proposalCopy(dimension: string, conflict: boolean, t: T): string {
  if (conflict) return t("Si ambas páginas describen la misma oferta vigente, revisa con sus responsables las declaraciones incompatibles antes de cambiarlas.", "If both pages describe the same current offer, review the incompatible statements with their owners before changing them.");
  if (dimension === "offer") return t("Si quieres hacer pública esta oferta, especifica el producto o servicio junto a la descripción actual, sin añadir capacidades no verificadas.", "If you intend to disclose this offer, specify the product or service alongside the current description, without adding unverified capabilities.");
  if (dimension === "audience") return t("Si quieres comunicar a quién se dirige esta oferta, nombra el grupo de clientes o el caso de uso junto al servicio descrito.", "If you intend to communicate whom this offer serves, name the customer group or use case alongside the described service.");
  return t("Si puedes sustentar el beneficio de esta oferta y quieres comunicarlo, añade un resultado concreto y sus condiciones, sin garantizar lo que no puedes demostrar.", "If you can support this offer's benefit and intend to communicate it, add a concrete outcome and its conditions, without guaranteeing what you cannot demonstrate.");
}

function Source({ q }: { q: PublicUnderstanding["citations"][number] }) {
  const { t } = useLocale();
  const href = useEvidenceLink().href(q.url);
  return <p className="fo-meta">
    {href ? <a href={href} target="_blank" rel="noopener noreferrer">{q.url}<span className="sr-only">{t("(se abre en otra pestaña)", "(opens in a new tab)")}</span></a> : <span>{q.url}</span>}
    <time dateTime={q.observedAt}>{q.observedAt.slice(0, 10)}</time></p>;
}

// A dimension shows its own quotation only when the basis is specific to it; a basis equal
// to every inspected quotation is shown once for the whole reading, not once per dimension.
function Dimension({ d, report, explain }: { d: UnderstandingDimension; report: PublicUnderstanding; explain: boolean }) {
  const { t } = useLocale();
  const quotes = report.citations.filter(q => d.citationIds.includes(q.id));
  const specific = quotes.length > 0 && (d.state === "STRENGTH" || quotes.length < report.citations.length);
  return <article className="fo-finding pu-dimension">
    <h4>{dimensionCopy(d.dimension, t)}</h4>
    <p className="fo-meta"><span className="fo-state">{stateCopy(d.state, t)}</span></p>
    {specific && quotes.map(q => <div className="pu-citation" key={q.id}><blockquote>{q.quote}</blockquote><Source q={q}/></div>)}
    {explain && d.state !== "STRENGTH" && <p className="fo-why">{causeCopy(d.cause, t)}</p>}
    {d.proposal && <div className="pu-proposal"><h5>{t("Propuesta condicionada", "Conditional proposal")}</h5><p>{proposalCopy(d.dimension, d.cause === "CONTRADICTION", t)}</p></div>}
  </article>;
}

function Dimensions({ report }: { report: PublicUnderstanding }) {
  const seen = new Set<string>();
  return <>{report.dimensions.map(d => {
    const explain = !seen.has(d.cause);
    seen.add(d.cause);
    return <Dimension key={d.dimension} d={d} report={report} explain={explain}/>;
  })}</>;
}

/** What is understood, what to clarify, what stays open, and one next step. */
function Synthesis({ report }: { report: PublicUnderstanding }) {
  const { t } = useLocale();
  const names = (keep: (state: string) => boolean) => report.dimensions.filter(d => keep(d.state)).map(d => dimensionCopy(d.dimension, t));
  const strong = names(s => s === "STRENGTH");
  const clarify = names(s => s === "CONSTRUCTIVE_GAP");
  const open = names(s => s !== "STRENGTH" && s !== "CONSTRUCTIVE_GAP");
  const next = clarify.length
    ? t("Revisa las propuestas de abajo. Si aplicas alguna, vuelve a observar con el mismo instrumento.", "Review the proposals below. If you apply any, reobserve with the same instrument.")
    : open.length
      ? t("Revisa las citas antes de decidir: esta lectura no basta para concluir.", "Review the quotations before deciding: this reading is not enough to conclude.")
      : t("Nada que aclarar en esta muestra. Vuelve a observar cuando cambies estas páginas.", "Nothing to clarify in this sample. Reobserve when you change these pages.");
  return <div className="pu-synthesis" aria-label={t("En resumen", "In short")}>
    <dl>
      {strong.length > 0 && <div><dt>{t("Se entiende bien", "Understood well")}</dt><dd>{strong.join(" · ")}</dd></div>}
      {clarify.length > 0 && <div><dt>{t("Conviene aclarar", "Worth clarifying")}</dt><dd>{clarify.join(" · ")}</dd></div>}
      {open.length > 0 && <div><dt>{t("Sin conclusión todavía", "No conclusion yet")}</dt><dd>{open.join(" · ")}</dd></div>}
      <div><dt>{t("Siguiente paso", "Next step")}</dt><dd>{next}</dd></div>
    </dl>
  </div>;
}

export function PublicUnderstandingView({ report }: { report: PublicUnderstanding }) {
  const { t } = useLocale();
  return <section className="pu-view" aria-labelledby={`pu-${report.reportId}`}>
    <h3 id={`pu-${report.reportId}`} tabIndex={-1}>{t("Cómo se entiende tu oferta pública", "How your public offer is understood")}</h3>
    <p className="fo-authority">{t("Una lectura de las páginas inspeccionadas mediante un instrumento de interpretación. No representa a todos los clientes, buscadores ni asistentes, y no verifica la realidad del negocio.", "A reading of the inspected pages through an interpretation instrument. It does not represent all customers, search engines or assistants, and does not verify business reality.")}</p>
    <p className="fo-meta"><time dateTime={report.measuredAt}>{report.measuredAt.slice(0, 10)}</time>
      {report.currentness === "STALE" && <strong>{t("Lectura pendiente de reobservación", "Reading awaiting reobservation")}</strong>}
      {report.execution === "EXACT_JUDGMENT_REUSE" && <span>{t("Juicio reutilizado sobre la misma evidencia; no es una réplica independiente.", "Judgment reused over the same evidence; not an independent replica.")}</span>}
    </p>
    {report.status !== "MEASURED" ? <p className="fo-why" role="status">{causeCopy(report.cause, t)}</p> : <>
      <Synthesis report={report}/>
      <Dimensions report={report}/>
      {report.dimensions.some(d => d.state !== "STRENGTH") && <p className="fo-why">{t("También puede haber una divulgación limitada deliberadamente, información fuera de esta muestra o un error del evaluador. Revisa la evidencia antes de decidir.", "There may also be deliberately limited disclosure, information outside this sample or an evaluator error. Review the evidence before deciding.")}</p>}
      {report.citations.length > 0 && <details className="fo-basis"><summary>{t("Ver citas y fundamento", "Inspect quotations and basis")} ({report.citations.length})</summary>
        {report.citations.map(q => <div className="pu-citation" key={q.id}><blockquote>{q.quote}</blockquote><Source q={q}/></div>)}
        <p className="fo-why">{t("Después de una revisión humana, vuelve a observar las mismas páginas con el mismo instrumento. Un cambio de interpretación no demuestra por sí solo una mejora comercial.", "After human review, reobserve the same pages with the same instrument. An interpretation change alone does not prove a business improvement.")}</p>
      </details>}
    </>}
    {report.comparison && <div className="pu-comparison"><h4>{t("Qué cambió desde la lectura anterior", "What changed since the previous reading")}</h4>
      <p className="fo-why">{report.comparison.state === "COMPARABLE" ? t("Instrumento y alcance comparables. El cambio corresponde a la interpretación, no a un resultado comercial demostrado.", "Comparable instrument and scope. The change concerns interpretation, not a demonstrated business result.") : t("Estas lecturas no son comparables: cambió el instrumento, el alcance o la disponibilidad de medición.", "These readings are not comparable: the instrument, scope or measurement availability changed.")}</p>
      {report.comparison.state === "COMPARABLE" && report.comparison.changes.length === 0 && <p>{t("Sin cambio en las dimensiones interpretadas.", "No change in the interpreted dimensions.")}</p>}
      {report.comparison.changes.map(change => <div key={change.dimension}>
        <p>{dimensionCopy(change.dimension, t)}: {change.kind === "INTERPRETATION_BASIS_CHANGED" ? t("Cambió el fundamento citado; el estado de interpretación se mantiene.", "The cited basis changed; the interpretation state remains the same.") : <>{stateCopy(change.before, t)} → {stateCopy(change.after, t)}</>}</p>
        {(change.beforeQuotations?.length || change.afterQuotations?.length) ? <details className="fo-basis"><summary>{t("Ver citas y fundamento", "Inspect quotations and basis")}</summary>
          <p>{t("Antes", "Before")}</p>{change.beforeQuotations?.map((quote, i) => <blockquote key={`before-${i}`}>{quote}</blockquote>)}
          <p>{t("Ahora", "Now")}</p>{change.afterQuotations?.map((quote, i) => <blockquote key={`after-${i}`}>{quote}</blockquote>)}
        </details> : null}
      </div>)}
    </div>}
    <details className="fo-basis"><summary>{t("Instrumento, alcance e historial", "Instrument, scope and history")}</summary>
      <dl><div><dt>{t("Instrumento", "Instrument")}</dt><dd>{report.instrument.id} {report.instrument.version} · {report.instrument.model ?? t("No disponible", "Unavailable")}</dd></div>
        <div><dt>{t("Alcance", "Scope")}</dt><dd>{t("Sitio web propio; lector sin contexto privado; una ejecución o reutilización exacta. Mercado no conocido.", "Own website; reader without private context; one execution or exact reuse. Market unknown.")}</dd></div>
        <div><dt>{t("Cobertura", "Coverage")}</dt><dd>{report.coverage === "BOUNDED_COMPLETE" ? t("Páginas seleccionadas inspeccionadas; no es un censo del sitio.", "Selected pages inspected; not a site census.") : t("Adquisición o representación incompleta.", "Incomplete acquisition or representation.")}</dd></div>
        {report.conditions && <div><dt>{t("Idioma de las fuentes y muestra", "Source language and sample")}</dt><dd>{report.conditions.languages.join(", ")} · {report.conditions.sampleSize}</dd></div>}
        {report.sourceObservedAt && <div><dt>{t("Fuentes adquiridas desde", "Sources acquired since")}</dt><dd><time dateTime={report.sourceObservedAt}>{report.sourceObservedAt}</time></dd></div>}
        {report.validUntil && <div><dt>{t("Reobservación prevista antes de", "Reobservation due before")}</dt><dd><time dateTime={report.validUntil}>{report.validUntil}</time></dd></div>}
        {report.contentExpiresAt && <div><dt>{t("Conservación de citas hasta", "Citation retention until")}</dt><dd><time dateTime={report.contentExpiresAt}>{report.contentExpiresAt}</time></dd></div>}
        <div><dt>{t("Método de representación e interpretación", "Representation and interpretation method")}</dt><dd>{report.instrument.representationVersion} · {report.instrument.interpretationVersion}</dd></div>
      </dl>
      {report.sourceRights?.map(right => <p className="fo-meta" key={right.url}>{right.url} · {right.basisRef ?? t("No disponible", "Unavailable")}</p>)}
      {report.history?.length ? report.history.map(old => <details className="pu-history" key={old.reportId} id={`pu-${old.reportId}`} tabIndex={-1}><summary>{t("Lectura anterior", "Previous reading")} {old.measuredAt.slice(0, 10)}</summary>
        <p>{old.instrument.id} {old.instrument.version} · {old.instrument.model}</p>
        {old.status !== "MEASURED" ? <p>{causeCopy(old.cause, t)}</p> : <Dimensions report={old}/>}
      </details>) : <p>{t("Todavía no hay otra lectura conservada para comparar.", "No other retained reading is available to compare yet.")}</p>}
    </details>
  </section>;
}
