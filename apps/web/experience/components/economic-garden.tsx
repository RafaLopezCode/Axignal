"use client";
/**
 * The economic garden, for people: where a business works, where it could grow, what
 * can affect it from outside, and what is not known yet (spec 059, ADR-0089).
 *
 * Presentation only. It receives places that already carry their epistemic state and
 * provenance; it never decides reach. Exposure is drawn as a path into the business,
 * not as a wider circle: a far-away cause matters only through what the business uses.
 */
import { ArrowDownRight, MapPinned, Sprout } from "lucide-react";
import { useLocale } from "@/lib/locale";
import type { Garden, GardenPlace } from "@/lib/garden";
import { CurrentnessTag, Mark, SourceRef, UnknownValue } from "./cognition/grammar";


function Place({ place }: { place: GardenPlace }) {
  const { copy } = useLocale();
  return (
    <li className="garden-place" data-epistemic={place.state}>
      <span className="garden-place-head">
        <strong>{copy(place.label)}</strong>
        <Mark state={place.state} />
        <CurrentnessTag state={place.currentness} />
      </span>
      {place.basis && <span className="garden-basis">{copy(place.basis)}</span>}
      <SourceRef source={place.source} />
    </li>
  );
}

export function EconomicGarden({
  organization,
  garden,
}: {
  organization: string;
  garden: Garden;
}) {
  const { t, copy } = useLocale();
  return (
    <section className="economic-garden" aria-labelledby="economic-garden-title">
      <header>
        <span className="eyebrow">{t("Su mundo económico", "Its economic world")}</span>
        <h2 id="economic-garden-title">
          {t("Dónde juega {org} y qué le afecta.", "Where {org} plays, and what affects it.").replace("{org}", organization)}
        </h2>
        <p>
          {t(
            "Cada lugar está sostenido por evidencia de la propia organización o queda marcado como desconocido. Lo que ocurre fuera de aquí no se le muestra como oportunidad.",
            "Each place is backed by the organization's own evidence or marked as unknown. What happens outside it is not shown to it as an opportunity.",
          )}
        </p>
      </header>
      <div className="garden-grid">
        <div className="garden-column garden-operating">
          <h3>
            <MapPinned size={18} aria-hidden="true" />
            {t("Dónde trabaja", "Where it works")}
          </h3>
          {garden.operating.length ? (
            <ul>{garden.operating.map((place) => <Place key={place.code} place={place} />)}</ul>
          ) : (
            <UnknownValue label={t("Todavía sin evidencia de dónde trabaja", "No evidence yet of where it works")} />
          )}
        </div>
        <div className="garden-column garden-expansion">
          <h3>
            <Sprout size={18} aria-hidden="true" />
            {t("Dónde podría crecer", "Where it could grow")}
          </h3>
          {garden.expansion.length ? (
            <ul>{garden.expansion.map((place) => <Place key={place.code} place={place} />)}</ul>
          ) : (
            <UnknownValue label={t("Sin señales de expansión", "No expansion signals")} />
          )}
        </div>
        <div className="garden-column garden-exposure">
          <h3>
            <ArrowDownRight size={18} aria-hidden="true" />
            {t("Qué le afecta desde fuera", "What affects it from outside")}
          </h3>
          {garden.exposure.length ? (
            <ul>
              {garden.exposure.map((item) => (
                <li key={item.id} className="garden-path" data-epistemic="POTENTIAL">
                  <span className="garden-place-head">
                    <strong>{copy(item.channel)}</strong>
                    <Mark state="POTENTIAL" />
                  </span>
                  <span className="garden-basis">{copy(item.path)}</span>
                </li>
              ))}
            </ul>
          ) : (
            <UnknownValue label={t("Ninguna vía de exposición conocida", "No known exposure path")} />
          )}
          <p className="garden-note">
            {t(
              "Una exposición no es una oportunidad: explica por dónde puede llegarle un cambio lejano.",
              "Exposure is not an opportunity: it explains how a distant change can reach it.",
            )}
          </p>
        </div>
      </div>
      {garden.unknown.length > 0 && (
        <div className="garden-unknown">
          <span>{t("Aún sin evidencia:", "No evidence yet:")}</span>
          <ul>
            {garden.unknown.map((place) => (
              <li key={place.code} data-epistemic="UNKNOWN">{copy(place.label)}</li>
            ))}
          </ul>
          <span className="garden-note">
            {t("Desconocido no significa que no trabaje allí.", "Unknown does not mean it does not work there.")}
          </span>
        </div>
      )}
    </section>
  );
}
