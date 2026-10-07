"use client";
/**
 * Family-specific cognitive components. Each explains one knowledge shape in its
 * own visual language while speaking the shared grammar. None of them computes
 * epistemic state, currentness or provenance: they render what the facts carry.
 */
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { useLocale } from "@/lib/locale";
import { dateLabel, type FamilyId } from "@/lib/projection";
import { factsAt, type FamilyFacts } from "@/lib/cognition/facts";
import { composeFamily, FAMILY_QUESTION, type Device } from "@/lib/cognition/compose";
import type { CognitiveComponentId, Intent, Layer } from "@/lib/cognition/registry";
import { CurrentnessTag, Headline, LayerSection, Mark, SourceRef, UnknownValue } from "./grammar";

type Props = { facts: FamilyFacts; asOf: string; glance?: boolean };
const byId = (facts: FamilyFacts) => new Map(facts.sources.map((s) => [s.id, s]));

function Frame({ id, title, children }: { id: CognitiveComponentId; title: string; children: ReactNode }) {
  return (
    <article className={"cg-component cg-" + id} data-cognitive-component={id}>
      <h3 className="cg-title">{title}</h3>
      {children}
    </article>
  );
}

/** In layer 1 secondary content waits behind one labelled disclosure. */
function Detail({ glance, children }: { glance?: boolean; children: ReactNode }) {
  const { t } = useLocale();
  if (!glance) return <>{children}</>;
  return (
    <details className="cg-more" data-layer="2">
      <summary>{t("Ver detalle", "See detail")}</summary>
      <div className="cg-more-body">{children}</div>
    </details>
  );
}

function TrendChart({ facts, glance }: Props) {
  const { t, copy, locale } = useLocale();
  const trend = facts.trend!;
  const observed = trend.points.filter((p) => p.value !== null);
  const first = observed[0];
  const last = observed[observed.length - 1];
  const delta = first && last ? (last.value as number) - (first.value as number) : null;
  const max = Math.max(40, ...observed.map((p) => p.value as number));
  const x = (i: number) => 16 + (i * 288) / Math.max(1, trend.points.length - 1);
  const y = (v: number) => 96 - (v / max) * 80;
  const segments: string[] = [];
  trend.points.forEach((p, i) => {
    const prev = trend.points[i - 1];
    if (p.value !== null && prev && prev.value !== null)
      segments.push(`M${x(i - 1)},${y(prev.value)} L${x(i)},${y(p.value)}`);
  });
  const summary =
    first && last && delta !== null
      ? t("Visibilidad en la muestra", "Visibility in the sample") +
        `: ${first.value}% → ${last.value}% (${delta >= 0 ? "+" : ""}${delta} ${t("puntos", "points")})`
      : t("Todavía no hay dos mediciones comparables.", "There are not yet two comparable measurements.");
  return (
    <Frame id="trend-chart" title={t("Presencia en búsqueda", "Search presence")}>
      <Headline>{summary}</Headline>
      <svg viewBox="0 0 320 110" className="cg-trend" role="img" aria-label={summary}>
        <defs>
          <pattern id="cg-hatch-pattern" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
            <line x1="0" y1="0" x2="0" y2="6" className="cg-hatch-stroke" />
          </pattern>
        </defs>
        <line x1="16" x2="304" y1="96" y2="96" className="cg-axis" />
        {segments.map((d) => (
          <path key={d} d={d} className="cg-line-observed" />
        ))}
        {trend.points.map((p, i) =>
          p.value === null ? (
            <g key={p.date} data-epistemic="UNKNOWN">
              <rect x={x(i) - 9} y={20} width={18} height={76} className="cg-hatch" />
              <text x={x(i)} y={14} textAnchor="middle" className="cg-svg-label">?</text>
            </g>
          ) : (
            <circle key={p.date} cx={x(i)} cy={y(p.value)} r={4} className="cg-dot-observed" data-epistemic="OBSERVED" />
          ),
        )}
      </svg>
      <table className="cg-sr">
        <caption>{copy(trend.measure)}</caption>
        <tbody>
          {trend.points.map((p) => (
            <tr key={p.date}>
              <th scope="row">{dateLabel(p.date, locale)}</th>
              <td>{p.value === null ? t("Desconocido", "Unknown") : `${p.value}%`}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <Detail glance={glance}>
        <p className="cg-meta">
          {copy(trend.measure)} · {copy(trend.sample)}
        </p>
      </Detail>
    </Frame>
  );
}

function TopicDeltas({ facts }: Props) {
  const { t, copy } = useLocale();
  const trend = facts.trend!;
  const pageLabel = {
    GAINED: t("gana presencia", "gains presence"),
    LOST: t("pierde presencia", "loses presence"),
    STABLE: t("estable", "stable"),
    UNKNOWN: t("sin medición", "not measured"),
  };
  return (
    <Frame id="topic-deltas" title={t("Dónde gana o pierde", "Where it gains or loses")}>
      <ul className="cg-deltas">
        {trend.topics.map((topic) => (
          <li key={topic.label.es}>
            <span>{copy(topic.label)}</span>
            {topic.delta === null ? (
              <UnknownValue label={t("Sin medición", "Not measured")} />
            ) : (
              <span className={"cg-delta " + (topic.delta >= 0 ? "cg-up" : "cg-down")} data-epistemic="OBSERVED">
                <span className="cg-delta-bar" style={{ width: `${Math.min(100, Math.abs(topic.delta) * 6)}%` }} />
                {topic.delta >= 0 ? "+" : ""}
                {topic.delta} {t("puntos", "points")}
              </span>
            )}
          </li>
        ))}
      </ul>
      <ul className="cg-pages">
        {trend.pages.map((page) => (
          <li key={page.path} data-epistemic={page.change === "UNKNOWN" ? "UNKNOWN" : "OBSERVED"}>
            <code>{page.path}</code> {pageLabel[page.change]}
          </li>
        ))}
      </ul>
    </Frame>
  );
}

function AnswerSpaceMatrix({ facts, glance }: Props) {
  const { t, copy } = useLocale();
  const space = facts.answerSpace!;
  const observedSurfaces = space.surfaces.filter((s) => s.observedAt);
  const present = space.questions.filter((q) =>
    observedSurfaces.some((s) => ["CITED", "MENTIONED"].includes(q.cells[s.id])),
  ).length;
  const label = {
    CITED: t("Citada", "Cited"),
    MENTIONED: t("Mencionada", "Mentioned"),
    ABSENT: t("Ausente", "Absent"),
    NOT_OBSERVED: t("No observado", "Not observed"),
  };
  return (
    <Frame id="answer-space-matrix" title={t("Presencia en respuestas generativas", "Presence in generative answers")}>
      <Headline>
        {t("Aparece en", "Appears in")} {present}/{space.questions.length}{" "}
        {t("preguntas observadas", "observed questions")}
        {space.surfaces.length > observedSurfaces.length
          ? " · " + t("hay superficies sin observar", "some surfaces are unobserved")
          : ""}
      </Headline>
      <ul className="cg-surfaces">
        {space.surfaces.map((s) => {
          const seen = space.questions.filter((q) => ["CITED", "MENTIONED"].includes(q.cells[s.id])).length;
          return s.observedAt ? (
            <li key={s.id} data-epistemic="OBSERVED">
              <strong>{copy(s.label)}</strong> {seen}/{space.questions.length}
            </li>
          ) : (
            <li key={s.id}>
              <strong>{copy(s.label)}</strong> <UnknownValue label={t("No observado", "Not observed")} />
            </li>
          );
        })}
      </ul>
      <Detail glance={glance}>
      <div className="cg-scroll">
        <table className="cg-matrix">
          <thead>
            <tr>
              <th scope="col">{t("Pregunta", "Question")}</th>
              {space.surfaces.map((s) => (
                <th scope="col" key={s.id}>
                  {copy(s.label)}
                  <small>{s.sample ? `n=${s.sample}` : t("sin muestra", "no sample")}</small>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {space.questions.map((q) => (
              <tr key={q.text.es}>
                <th scope="row">{copy(q.text)}</th>
                {space.surfaces.map((s) => (
                  <td key={s.id} className={"cg-cell cg-cell-" + q.cells[s.id].toLowerCase()} data-epistemic={q.cells[s.id] === "NOT_OBSERVED" ? "UNKNOWN" : "OBSERVED"}>
                    {label[q.cells[s.id]]}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="cg-meta">
        {t("Aparece junto a", "Appears alongside")}: {space.coOccurring.map((e) => `${e.name} (${e.questions})`).join(", ")}
      </p>
      </Detail>
    </Frame>
  );
}

function ClaimSupport({ facts }: Props) {
  const { t, copy } = useLocale();
  const sources = byId(facts);
  const label = {
    SUPPORTED: t("Respaldada por evidencia", "Supported by evidence"),
    UNSUPPORTED: t("Sin respaldo observado", "No observed support"),
    CONTRADICTED: t("Contradicha", "Contradicted"),
    UNKNOWN: t("No verificable aún", "Not yet verifiable"),
  };
  return (
    <Frame id="claim-support" title={t("Cómo la describen", "How it is described")}>
      <ul className="cg-claims">
        {facts.answerSpace!.claims.map((claim) => (
          <li key={claim.text.es} className={"cg-claim cg-claim-" + claim.support.toLowerCase()} data-epistemic={claim.support === "UNKNOWN" ? "UNKNOWN" : "OBSERVED"}>
            <span>«{copy(claim.text)}»</span>
            <strong>{label[claim.support]}</strong>
            {claim.sourceId && <SourceRef source={sources.get(claim.sourceId)} />}
          </li>
        ))}
      </ul>
    </Frame>
  );
}

function OpportunityBrief({ facts, asOf, glance }: Props) {
  const { t, copy, locale } = useLocale();
  const items = facts.opportunities!;
  return (
    <Frame id="opportunity-brief" title={t("Dónde puede existir valor", "Where value may exist")}>
      <Headline>
        {items.length} {t("oportunidades potenciales; ninguna confirmada.", "potential opportunities; none confirmed.")}
      </Headline>
      <ul className="cg-opportunities">
        {items.map((o) => (
          <li key={o.id} className="cg-opportunity" data-epistemic={o.epistemic}>
            <Mark state={o.epistemic} />
            <strong>{copy(o.title)}</strong>
            <span className="cg-meta">
              {copy(o.buyer)} · {copy(o.market)} · {copy(o.form)} ·{" "}
              {o.deadline ? (
                <>
                  {t("Plazo", "Deadline")} {dateLabel(o.deadline, locale)}
                  {o.deadline < asOf ? " · " + t("cerrado", "closed") : ""}
                </>
              ) : (
                <UnknownValue label={t("Plazo desconocido", "Deadline unknown")} />
              )}
            </span>
            <Detail glance={glance}>
              <span className="cg-why">{copy(o.whyPotential)}</span>
            </Detail>
          </li>
        ))}
      </ul>
    </Frame>
  );
}

function CapabilityDemandMatch({ facts }: Props) {
  const { t, copy } = useLocale();
  const sources = byId(facts);
  return (
    <Frame id="capability-demand-match" title={t("Por qué encaja", "Why it fits")}>
      {facts.opportunities!.map((o) => (
        <div key={o.id} className="cg-match">
          <div className="cg-match-side">
            <span className="cg-eyebrow">{t("La empresa declara", "The company declares")}</span>
            <strong>{copy(o.capability.label)}</strong>
            <q>{copy(o.capability.excerpt)}</q>
            <SourceRef source={sources.get(o.capability.sourceId)} />
          </div>
          <span className="cg-match-link" aria-hidden="true">⇄</span>
          <div className="cg-match-side">
            <span className="cg-eyebrow">{t("El comprador pide", "The buyer asks for")}</span>
            <strong>{copy(o.demand.label)}</strong>
            {o.demand.code ? <code>{o.demand.code}</code> : <UnknownValue label={t("Sin código publicado", "No published code")} />}
            <SourceRef source={sources.get(o.demand.sourceId)} />
          </div>
        </div>
      ))}
    </Frame>
  );
}

function RequirementMatrix({ facts }: Props) {
  const { t, copy } = useLocale();
  return (
    <Frame id="requirement-matrix" title={t("Lo que sabemos y lo que no", "What we know and what we do not")}>
      {facts.opportunities!.map((o) => (
        <div key={o.id} className="cg-requirements" data-epistemic={o.epistemic}>
          <div className="cg-requirement-heading">
            <Mark state={o.epistemic} />
            <strong>{copy(o.title)}</strong>
          </div>
          <p className="cg-limit">
            {t(
              "La relevancia potencial no confirma una relación comercial. Los datos conocidos no demuestran encaje ni una oportunidad observada.",
              "Potential relevance does not confirm a commercial relationship. Known details do not establish fit or an observed opportunity.",
            )}
          </p>
          <ul>
            {o.known.map((k) => (
              <li key={k.label.es}>
                {copy(k.label)}: {copy(k.value)}
              </li>
            ))}
            {o.unknown.map((u) => (
              <li key={u.es}>
                <UnknownValue label={copy(u)} />
              </li>
            ))}
          </ul>
        </div>
      ))}
    </Frame>
  );
}

function RelationshipNetwork({ facts, glance }: Props) {
  const { t, copy, locale } = useLocale();
  const network = facts.network!;
  const sources = byId(facts);
  const name = new Map(network.nodes.map((n) => [n.id, n]));
  const observed = network.edges.filter((e) => e.state === "OBSERVED");
  const potential = network.edges.filter((e) => e.state === "POTENTIAL");
  const subject = network.nodes[0];
  const lane = (edge: (typeof network.edges)[number]) =>
    edge.from === subject.id ? edge.to : edge.from;
  // Each row (observed above, potential below) spreads its own nodes, and crowded rows
  // stagger vertically, so names never overlap.
  const pos = new Map(
    (["OBSERVED", "POTENTIAL"] as const).flatMap((state) => {
      const row = network.edges.filter((edge) => edge.state === state).map(lane);
      return row.map((id, i) => [
        id,
        { x: 40 + (i + 0.5) * (240 / row.length), y: (state === "OBSERVED" ? 28 : 78) + (row.length > 2 && i % 2 ? 14 : 0) },
      ] as const);
    }),
  );
  const summary =
    `${observed.length} ${t("relaciones observadas", "observed relationships")} · ` +
    `${potential.length} ${t("potenciales por investigar", "potential to investigate")}`;
  const row = (edge: (typeof network.edges)[number]) => (
    <li key={edge.from + edge.to} data-epistemic={edge.state}>
      <Mark state={edge.state} />
      <span>
        {name.get(edge.from)?.label} {copy(edge.kind)} {name.get(edge.to)?.label}
        {edge.since ? ` · ${t("desde", "since")} ${dateLabel(edge.since, locale)}` : ""}
      </span>
      <span className="cg-why">{copy(edge.reason)}</span>
      <SourceRef source={edge.sourceId ? sources.get(edge.sourceId) : undefined} />
    </li>
  );
  return (
    <Frame id="relationship-network" title={t("Relaciones", "Relationships")}>
      <Headline>{summary}</Headline>
      <svg viewBox="0 0 320 150" className="cg-network" role="img" aria-label={summary}>
        <text x="160" y="142" textAnchor="middle" className="cg-svg-node">{subject.label}</text>
        {/* Lines first, names last: a name is never crossed by another relationship's line. */}
        {network.edges.map((edge) => {
          const other = pos.get(lane(edge))!;
          return (
            <line key={"l" + edge.from + edge.to} data-epistemic={edge.state} x1="160" y1="124" x2={other.x} y2={other.y + 8} className={edge.state === "OBSERVED" ? "cg-edge-observed" : "cg-edge-potential"} />
          );
        })}
        {network.edges.map((edge) => {
          const other = pos.get(lane(edge))!;
          return (
            <text key={"t" + edge.from + edge.to} x={other.x} y={other.y} textAnchor="middle" className="cg-svg-node cg-svg-label-halo">{name.get(lane(edge))?.label}</text>
          );
        })}
      </svg>
      <Detail glance={glance}>
        <h4>{t("Observadas, con evidencia", "Observed, with evidence")}</h4>
        <ul className="cg-edges">{observed.map(row)}</ul>
        <h4>{t("Potenciales: hipótesis por investigar", "Potential: hypotheses to investigate")}</h4>
        <ul className="cg-edges cg-edges-potential">{potential.map(row)}</ul>
      </Detail>
    </Frame>
  );
}

function TerritoryMatrix({ facts, glance }: Props) {
  const { t, copy } = useLocale();
  const sources = byId(facts);
  const markets = facts.territory!.markets;
  const count = (s: string) => markets.filter((m) => m.state === s).length;
  return (
    <Frame id="territory-matrix" title={t("Mercados", "Markets")}>
      <Headline>
        {count("OBSERVED")} {t("con evidencia", "with evidence")} · {count("POTENTIAL")}{" "}
        {t("potenciales", "potential")} · {count("UNKNOWN")} {t("desconocidos", "unknown")}
      </Headline>
      <ul className="cg-territory">
        {markets.map((m) => (
          <li key={m.code} className={"cg-tile cg-tile-" + m.state.toLowerCase()} data-epistemic={m.state}>
            <Mark state={m.state} />
            <strong>{copy(m.label)}</strong>
            <CurrentnessTag state={m.currentness} />
            <div className="cg-tile-detail">
              <Detail glance={glance}>
                {m.signal ? <span>{copy(m.signal)}</span> : <UnknownValue label={t("Sin evidencia observada", "No observed evidence")} />}
                {m.sourceId && <SourceRef source={sources.get(m.sourceId)} />}
              </Detail>
            </div>
          </li>
        ))}
      </ul>
    </Frame>
  );
}

function DiscourseMap({ facts, glance }: Props) {
  const { t, copy, locale } = useLocale();
  const discourse = facts.discourse!;
  const contradicted = new Set(discourse.statements.map((s) => s.contradicts).filter(Boolean));
  const materiality = { LOW: t("baja", "low"), MEDIUM: t("media", "medium"), HIGH: t("alta", "high") };
  return (
    <Frame id="discourse-map" title={t("Qué se dice", "What is being said")}>
      <Headline>
        {discourse.statements.length} {t("afirmaciones públicas observadas", "observed public statements")}
        {contradicted.size ? " · " + t("con contradicciones", "with contradictions") : ""} ·{" "}
        {t("no es una medida de opinión general", "not a measure of general opinion")}
      </Headline>
      <ul className="cg-statements">
        {discourse.statements.map((s) => (
          <li key={s.id} data-epistemic="OBSERVED" className={s.contradicts || contradicted.has(s.id) ? "cg-contested" : ""}>
            <strong>«{copy(s.text)}»</strong>
            <Detail glance={glance}>
              <span className="cg-meta">
                {copy(s.where)} · {dateLabel(s.date, locale)} · {copy(s.sample)} · {t("materialidad", "materiality")}{" "}
                {materiality[s.materiality]}
              </span>
            </Detail>
            {s.contradicts && (
              <span className="cg-why">{t("Contradice otra afirmación observada", "Contradicts another observed statement")}</span>
            )}
          </li>
        ))}
      </ul>
      <ul className="cg-absences">
        {discourse.absences.map((a) => (
          <li key={a.es}>
            <UnknownValue label={copy(a)} />
          </li>
        ))}
      </ul>
    </Frame>
  );
}

function ChangeTimeline({ facts, glance }: Props) {
  const { t, copy, locale } = useLocale();
  const sources = byId(facts);
  const kind = {
    EVIDENCE_ARRIVED: t("Llega evidencia", "Evidence arrives"),
    MATERIAL_CHANGE: t("Cambio material", "Material change"),
    BECAME_STALE: t("Envejece", "Becomes stale"),
    HYPOTHESIS_UPDATED: t("Hipótesis actualizada", "Hypothesis updated"),
  };
  const events = facts.change!.events;
  return (
    <Frame id="change-timeline" title={t("Qué ha cambiado", "What changed")}>
      <Headline>
        {events.length} {t("cambios en este corte", "changes in this cut")}; {t("el más reciente", "the latest")}:{" "}
        {copy(events[events.length - 1].label)}
      </Headline>
      {glance && (
        <ol className="cg-timeline cg-timeline-recent">
          {events.slice(-3).map((e, i) => (
            <li key={e.date + i} className={"cg-event cg-event-" + e.kind.toLowerCase()}>
              <time dateTime={e.date}>{dateLabel(e.date, locale)}</time>
              <span>
                <strong>{kind[e.kind]}</strong> · {copy(e.label)}
              </span>
            </li>
          ))}
        </ol>
      )}
      <Detail glance={glance}>
      <ol className="cg-timeline">
        {events.map((e, i) => (
          <li key={e.date + i} className={"cg-event cg-event-" + e.kind.toLowerCase()}>
            <time dateTime={e.date}>T{i} · {dateLabel(e.date, locale)}</time>
            <strong>{kind[e.kind]}</strong>
            <span>{copy(e.label)}</span>
            {e.sourceId && <SourceRef source={sources.get(e.sourceId)} />}
          </li>
        ))}
      </ol>
      </Detail>
    </Frame>
  );
}

function ProvenanceTrail({ facts, asOf, glance }: Props) {
  const { t, copy, locale } = useLocale();
  return (
    <Frame id="provenance-trail" title={t("Cómo lo sabe AXIGNAL", "How AXIGNAL knows")}>
      <Headline>
        {facts.sources.length} {t("fuentes en este corte", "sources in this cut")}
      </Headline>
      {glance && (
        <ul className="cg-source-names">
          {facts.sources.map((s) => (
            <li key={s.id}>{copy(s.title)}</li>
          ))}
        </ul>
      )}
      <Detail glance={glance}>
      <ol className="cg-provenance">
        {[...facts.sources]
          .sort((a, b) => a.observedAt.localeCompare(b.observedAt))
          .map((s) => (
            <li key={s.id} data-provenance={s.id}>
              <strong>{copy(s.title)}</strong>
              <span className="cg-meta">
                {dateLabel(s.observedAt, locale)} · {copy(s.instrument)}
              </span>
              <CurrentnessTag state={s.currentness ?? "UNKNOWN"} />
              <span className="cg-limit">{copy(s.limitation)}</span>
            </li>
          ))}
      </ol>
      </Detail>
    </Frame>
  );
}

const RENDER: Record<CognitiveComponentId, (props: Props) => ReactNode> = {
  "trend-chart": TrendChart,
  "topic-deltas": TopicDeltas,
  "answer-space-matrix": AnswerSpaceMatrix,
  "claim-support": ClaimSupport,
  "opportunity-brief": OpportunityBrief,
  "capability-demand-match": CapabilityDemandMatch,
  "requirement-matrix": RequirementMatrix,
  "relationship-network": RelationshipNetwork,
  "territory-matrix": TerritoryMatrix,
  "discourse-map": DiscourseMap,
  "change-timeline": ChangeTimeline,
  "provenance-trail": ProvenanceTrail,
};

export function CognitiveComponent({ id, facts, asOf, glance }: { id: CognitiveComponentId } & Props) {
  const Render = RENDER[id];
  return <Render facts={facts} asOf={asOf} glance={glance} />;
}

function useDevice(): Device {
  // Server rendering starts from the conservative mobile composition so small
  // screens never flash a denser desktop first layer before hydration.
  const [device, setDevice] = useState<Device>("mobile");
  useEffect(() => {
    const query = window.matchMedia("(max-width: 760px)");
    const update = () => setDevice(query.matches ? "mobile" : "desktop");
    update();
    query.addEventListener("change", update);
    return () => query.removeEventListener("change", update);
  }, []);
  return device;
}

/** The family's cognitive composition with progressive disclosure. */
export function FamilyLens({
  organizationId,
  family,
  asOf,
  intent = "overview",
}: {
  organizationId: string;
  family: FamilyId;
  asOf: string;
  intent?: Intent;
}) {
  const { copy } = useLocale();
  const device = useDevice();
  const facts = useMemo(() => factsAt(organizationId, asOf), [organizationId, asOf]);
  const plan = useMemo(() => composeFamily({ family, intent, facts, device }), [family, intent, facts, device]);
  const layers = [1, 2, 3, 4].map((layer) => plan.items.filter((item) => item.layer === layer));
  const question = FAMILY_QUESTION[family];
  return (
    <div className="cg-lens" data-family={family} data-intent={intent}>
      <p className="cg-question">{copy(question)}</p>
      {layers.map(
        (items, index) =>
          items.length > 0 && (
            <LayerSection key={index} layer={(index + 1) as Layer}>
              {items.map((item) => (
                <CognitiveComponent
                  key={item.component}
                  id={item.component}
                  facts={facts}
                  asOf={asOf}
                  glance={index === 0}
                />
              ))}
            </LayerSection>
          ),
      )}
    </div>
  );
}
