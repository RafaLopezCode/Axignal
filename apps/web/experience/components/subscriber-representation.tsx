"use client";

import { useLocale } from "@/lib/locale";
import { safeSourceLink, type RuntimeProjection } from "@/lib/runtime-projection";

export function SubscriberRepresentation({ measurement }: { measurement: NonNullable<RuntimeProjection["digitalRepresentation"]> }) {
  const { t, locale } = useLocale();
  const unavailable = "state" in measurement;
  const recorded = unavailable ? measurement.recordedMeasurement : measurement;
  const name = recorded?.fields.find(field => field.name === "canonical_organization_name_in_page_title");
  const link = recorded && safeSourceLink(recorded.resourceRef);
  const condition = (value: string) => value === "UNKNOWN" ? t("Sin determinar", "Undetermined") : value;
  return <section className="subscriber-representation" aria-labelledby="representation-title">
    <span className="eyebrow">{t("Representación pública", "Public representation")}</span>
    <h3 id="representation-title">{t("Qué se pudo observar en la página", "What could be observed on the page")}</h3>
    <p>{unavailable ? t("Medición no disponible. Esto no demuestra que la organización no tenga presencia pública.", "Measurement unavailable. This does not establish that the organization has no public presence.")
      : name?.state === "PRESENT" ? t("El título capturado contiene el nombre de la organización.", "The captured title contains the organization name.")
      : name?.state === "MEASURED_ABSENCE_WITHIN_SCOPE" ? t("El nombre no aparece en el título de esta página. La causa es desconocida.", "The name does not appear in this page title. The cause is unknown.")
      : t("El título no permite concluir si aparece el nombre.", "The title does not support a conclusion about the name.")}</p>
    <p className="limit-note">{t("El alcance es una página. No mide la presencia en buscadores, respuestas de IA o redes sociales, ni la calidad del SEO o GEO.", "The scope is one page. It does not measure presence in search, AI answers or social media, or SEO or GEO quality.")}</p>
    {!unavailable && recorded?.representationGap?.contextRecommendation && <div className="subscriber-notice">
      <h4>{t("Antes de recomendar un cambio", "Before recommending a change")}</h4>
      <p>{t("Falta confirmar para qué sirve esta página y qué nombre público debe utilizar. Si identifica a la organización y el nombre esperado coincide con el comparado, puedes revisar el título con el equipo responsable.", "The purpose of this page and its expected public name still need confirmation. If it identifies the organization and the expected name matches the name compared, you can review the title with the responsible team.")}</p>
      <p className="limit-note">{t("La recomendación requiere contexto y revisión humana. No se ha demostrado una mejora de rendimiento.", "The recommendation requires context and human review. No performance improvement has been established.")}</p>
    </div>}
    {recorded && <details><summary>{t("Ver cómo se midió", "See how it was measured")}{unavailable && ` · ${t("Registro anterior", "Previous record")}`}</summary>
      {link && <p><a className="text-link" href={link} target="_blank" rel="noopener noreferrer">{t("Abrir fuente pública", "Open public source")}</a></p>}
      <dl><dt>{t("Fecha de observación", "Observation date")}</dt><dd>{new Date(recorded.observedAt).toLocaleString(locale)}</dd>
        <dt>{t("Vigencia", "Currentness")}</dt><dd>{unavailable || recorded.currentness === "UNKNOWN" ? t("Desconocida", "Unknown") : recorded.currentness === "CURRENT" ? t("Actual", "Current") : recorded.currentness === "STALE" ? t("Desactualizada", "Stale") : t("Histórica", "Historical")}</dd>
        <dt>{t("Muestra", "Sample")}</dt><dd>{recorded.sample.informative} / {recorded.sample.eligible}</dd>
        <dt>{t("Instrumento y versión", "Instrument and version")}</dt><dd>{recorded.instrument.ref} · {recorded.instrument.version}</dd>
        <dt>{t("Condiciones de observación", "Observation conditions")}</dt><dd>{condition(recorded.conditions.language)} · {condition(recorded.conditions.geography)} · {condition(recorded.conditions.deviceContext)}</dd>
        <dt>{t("Derechos y acceso", "Rights and access")}</dt><dd>{recorded.source.rightsStatus === "PERMITTED" ? t("Uso de fuente permitido", "Source use permitted") : recorded.source.rightsStatus === "PROHIBITED" ? t("Uso de fuente prohibido", "Source use prohibited") : t("Derechos sin determinar", "Rights undetermined")} · {recorded.source.accessStatus === "ACCESSIBLE" ? t("Fuente accesible", "Source accessible") : recorded.source.accessStatus === "INACCESSIBLE" ? t("Fuente inaccesible", "Source inaccessible") : t("Acceso sin determinar", "Access undetermined")}</dd>
      </dl><p>{t("Una página puede ser incompleta o poco representativa. No permite explicar las causas ni generalizar a toda la organización.", "One page may be incomplete or unrepresentative. It cannot explain causes or support conclusions about the whole organization.")}</p>
    </details>}
  </section>;
}
