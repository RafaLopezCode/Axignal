"use client";
/**
 * Thematic navigation of the Observatory: the ten observation families and, inside Presence, the SEO, GEO / AI
 * and Web channels. It only selects what is shown; the selection travels in the URL and across the Summary,
 * Evolution and Evidence views. It never creates a finding, a count without data or a button without a place to go.
 */
import { useEffect, useRef } from "react";
import { useLocale } from "@/lib/locale";
import { families } from "@/lib/projection";
import { CHANNEL_ORDER, FAMILY_ORDER, NO_FACET, type Channel, type Facet } from "@/lib/observation-families";
import { fill, type Translate } from "@/lib/observatory";
import type { FamilyId } from "@/lib/projection";

export function channelLabel(channel: Channel, t: Translate): string {
  if (channel === "SEO") return t("SEO", "SEO");
  if (channel === "GEO") return t("GEO / IA", "GEO / AI");
  return t("Web", "Web");
}

const familyOf = (id: FamilyId) => families.find(family => family.id === id)!;

export type FacetScope = { title: string; intro: string; emptyTitle: string; emptyBody: string };

/** What a selected family or channel is, and what its honest empty state says. */
export function scopeCopy(facet: Facet, t: Translate, copy: (value: { es: string; en: string }) => string): FacetScope | null {
  if (!facet.family) return null;
  const family = familyOf(facet.family);
  const name = copy(family.name);
  if (facet.family === "presence" && facet.channel === "SEO") return {
    title: `${name} · ${channelLabel("SEO", t)}`,
    intro: t("Cómo se encuentra la organización en buscadores. Solo se muestran mediciones con su consulta, sus condiciones y su fecha.", "How the organization is found in search engines. Only measurements with their query, conditions and date are shown."),
    emptyTitle: t("Todavía no hay mediciones de SEO", "There are no SEO measurements yet"),
    emptyBody: t("AXIGNAL aún no ha medido su visibilidad en buscadores. No significa que no sea visible: significa que no hay una observación admitida que mostrar.", "AXIGNAL has not measured its search visibility yet. It does not mean it is not visible: it means there is no admitted observation to show."),
  };
  if (facet.family === "presence" && facet.channel === "GEO") return {
    title: `${name} · ${channelLabel("GEO", t)}`,
    intro: t("Cómo aparece en respuestas de asistentes de IA. Mencionar no es citar, y citar no es recomendar.", "How it appears in AI assistant answers. A mention is not a citation, and a citation is not an endorsement."),
    emptyTitle: t("Todavía no hay mediciones de GEO / IA", "There are no GEO / AI measurements yet"),
    emptyBody: t("AXIGNAL aún no ha medido si aparece en respuestas de asistentes de IA. Sin medición no hay conclusión: desconocido no es negativo.", "AXIGNAL has not measured whether it appears in AI assistant answers. Without a measurement there is no conclusion: unknown is not negative."),
  };
  if (facet.family === "presence" && facet.channel === "WEB") return {
    title: `${name} · ${channelLabel("WEB", t)}`,
    intro: t("Qué muestra su propia web: estructura, idiomas y acceso para buscadores y asistentes.", "What its own website shows: structure, languages and access for search engines and assistants."),
    emptyTitle: t("Todavía no hay observaciones de su web", "There are no observations of its website yet"),
    emptyBody: t("Cuando AXIGNAL lea su web pública, aparecerá aquí con sus fuentes y sus límites.", "When AXIGNAL reads its public website, it will appear here with its sources and limits."),
  };
  return {
    title: name,
    intro: copy(family.intro),
    emptyTitle: t("Todavía no hay hallazgos en esta familia", "There are no findings in this family yet"),
    emptyBody: t("Una familia sin hallazgos no es una familia sin actividad: significa que aún no hay evidencia admitida.", "A family without findings is not a family without activity: it means there is no admitted evidence yet."),
  };
}

type Counts = { families: Record<FamilyId, number>; channels: Record<Channel, number> };

export function FamilyNav({ facet, counts, lit, onSelect }: {
  facet: Facet; counts: Counts; lit: Record<FamilyId, number>; onSelect: (facet: Facet) => void;
}) {
  const { t, copy } = useLocale();
  const root = useRef<HTMLDivElement>(null);
  // On a narrow screen the chips scroll sideways: keep the selected one in view.
  useEffect(() => {
    const selected = root.current?.querySelector<HTMLElement>("[aria-pressed='true']");
    selected?.scrollIntoView?.({ inline: "center", block: "nearest" });
  }, [facet.family, facet.channel]);
  const litLabel = (n: number) => n === 1 ? t("1 nuevo", "1 new") : fill(t("{n} nuevos", "{n} new"), { n });
  return <div className="obs-facets" ref={root}>
    <nav className="obs-facet-nav" aria-label={t("Familias de observación", "Observation families")}>
      <ul>
        <li><button className="obs-facet" aria-pressed={!facet.family} onClick={() => onSelect(NO_FACET)}>{t("Todas", "All")}</button></li>
        {FAMILY_ORDER.map(id => <li key={id}>
          <button className="obs-facet" aria-pressed={facet.family === id} onClick={() => onSelect({ family: id, channel: null })}>
            {copy(familyOf(id).name)}
            {counts.families[id] > 0 && <span className="obs-facet-count">{counts.families[id]}</span>}
            {lit[id] > 0 && <span className="obs-facet-lamp" role="img" aria-label={litLabel(lit[id])}/>}
          </button>
        </li>)}
      </ul>
    </nav>
    {facet.family === "presence" && <nav className="obs-channel-nav" aria-label={t("Canales de presencia digital", "Digital presence channels")}>
      <ul>
        <li><button className="obs-facet obs-facet-channel" aria-pressed={!facet.channel} onClick={() => onSelect({ family: "presence", channel: null })}>{t("Todo", "All")}</button></li>
        {CHANNEL_ORDER.map(channel => <li key={channel}>
          <button className="obs-facet obs-facet-channel" aria-pressed={facet.channel === channel} onClick={() => onSelect({ family: "presence", channel })}>
            {channelLabel(channel, t)}
            {counts.channels[channel] > 0 && <span className="obs-facet-count">{counts.channels[channel]}</span>}
          </button>
        </li>)}
      </ul>
    </nav>}
  </div>;
}
