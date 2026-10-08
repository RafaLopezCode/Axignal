"use client";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import {
  ArrowRight,
  ArrowUpRight,
  BookOpen,
  CircleHelp,
  Clock3,
  MapPinned,
} from "lucide-react";
import { PublicHeader } from "./public-shell";
import { ReferencePricing } from "./landing-extras";
import { FramedObserver } from "./observer-frame";
import { useLocale } from "@/lib/locale";
import { dateLabel, makeContext, project } from "@/lib/projection";
import {
  funnelCta,
  landingChapters,
  track,
  type FunnelCta,
} from "@/lib/funnel-events";
import { Badge, MiniFooter, Observer } from "./ui";

/** The one public example. Every "show me" on the site lands here. */
export const EXAMPLE_HREF = "/panorama";

function Reveal({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const node = ref.current;
    if (!node) return;
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            node.classList.add("in-view");
            observer.unobserve(node);
          }
        });
      },
      { threshold: 0.12 },
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, []);
  return (
    <div ref={ref} className={"reveal " + className}>
      {children}
    </div>
  );
}

function CtaLink({
  href,
  cta,
  className,
  children,
}: {
  href: string;
  cta: FunnelCta;
  className: string;
  children: React.ReactNode;
}) {
  return (
    <Link
      href={href}
      className={className}
      onClick={() => track({ kind: "CTA_ACTIVATED", surface: "landing", cta })}
    >
      {children}
    </Link>
  );
}

/**
 * A glance at what a subscriber reads, composed from the same fictional example the
 * public example renders (never a second fixture). It shows the three epistemic
 * states side by side because that difference is the product.
 */
function HeroReading() {
  const { t, copy, locale } = useLocale();
  const now = project(makeContext("norte", "markets", "2026-10-03"));
  const order = ["renovation", "representation", "reputation-gap"];
  const shown = order
    .map((id) => now.signals.find((signal) => signal.id === id))
    .filter((signal) => signal !== undefined);
  return (
    <div className="hero-reading">
      <div className="hero-reading-head">
        <span className="hero-reading-org">
          <span className="org-monogram" aria-hidden="true">N</span>
          <span>
            <strong>{now.organization.name}</strong>
            <small>{t("Organización ficticia · ejemplo guiado", "Fictional organization · guided example")}</small>
          </span>
        </span>
        <span className="mono">{dateLabel("2026-10-03", locale)}</span>
      </div>
      <p className="hero-reading-does">{copy(now.organization.does)}</p>
      <h2 className="hero-reading-title">
        {t("Lo que AXIGNAL ve hoy", "What AXIGNAL sees today")}
      </h2>
      <ul>
        {shown.map((signal) => (
          <li key={signal.id}>
            <Badge state={signal.epistemic} />
            <span className="hero-reading-text">{copy(signal.title)}</span>
            <span className="hero-reading-basis">
              {signal.epistemic === "UNKNOWN"
                ? t("Sin evidencia suficiente todavía", "Not enough evidence yet")
                : signal.evidenceIds.length +
                  " " +
                  (signal.evidenceIds.length === 1
                    ? t("fuente", "source")
                    : t("fuentes", "sources")) +
                  " · " +
                  t("observado el", "observed on") +
                  " " +
                  dateLabel(signal.detectedAt, locale)}
            </span>
          </li>
        ))}
      </ul>
      <CtaLink href={EXAMPLE_HREF} cta={funnelCta.heroExample} className="hero-reading-open">
        {t("Abrir el ejemplo completo", "Open the full example")}
        <ArrowRight size={16} />
      </CtaLink>
    </div>
  );
}

function useChapterViews() {
  useEffect(() => {
    track({ kind: "LANDING_VIEWED", surface: "landing" });
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          const chapter = landingChapters[entry.target.id as keyof typeof landingChapters];
          if (entry.isIntersecting && chapter)
            track({ kind: "CHAPTER_VIEWED", surface: "landing", chapter });
        }
      },
      { threshold: 0.35 },
    );
    document
      .querySelectorAll("main > section[id]")
      .forEach((node) => observer.observe(node));
    return () => observer.disconnect();
  }, []);
}

export function Landing() {
  const { t, locale } = useLocale();
  const [time, setTime] = useState(2);
  const [audience, setAudience] = useState(0);
  const [focuses, setFocuses] = useState(1);
  useChapterViews();
  const audiences = [
    {
      name: t("Diriges una empresa", "You run a business"),
      title: t(
        "Lo que pasa a tu alrededor, sin buscarlo cada semana.",
        "What happens around you, without searching every week.",
      ),
      text: t(
        "Cambios en clientes, competencia y mercado, y demanda pública que encaja con lo que haces y con dónde trabajas. Una posibilidad sigue siendo una posibilidad hasta que la evidencia diga más.",
        "Changes in customers, competitors and markets, and public demand that fits what you do and where you work. A possibility stays a possibility until the evidence says more.",
      ),
      family: "demand",
      scene: "strategy" as const,
    },
    {
      name: t("Ventas y desarrollo de negocio", "Sales and business development"),
      title: t(
        "Qué cuentas conviene mirar, y por qué.",
        "Which accounts deserve a look, and why.",
      ),
      text: t(
        "Sigue a tus clientes y a tus cuentas objetivo. AXIGNAL muestra qué ha cambiado y qué capacidad conecta con qué necesidad, sin convertir una coincidencia en un cliente.",
        "Follow your customers and target accounts. AXIGNAL shows what changed and which capability meets which need, without turning an overlap into a customer.",
      ),
      family: "relationships",
      scene: "business" as const,
    },
    {
      name: t("Consultoras y agencias", "Consultancies and agencies"),
      title: t(
        "Una organización por cliente. El contexto, ya preparado.",
        "One organization per client. The context, already prepared.",
      ),
      text: t(
        "Observa a cada cliente con continuidad y llega a cada reunión sabiendo qué ha cambiado desde la anterior. Cada organización adicional cuesta 4,95 € al mes.",
        "Observe each client continuously and arrive at every meeting knowing what changed since the last one. Each additional organization costs €4.95 a month.",
      ),
      family: "activity",
      scene: "research" as const,
    },
    {
      name: t("SEO y presencia digital", "SEO and digital presence"),
      title: t(
        "Cómo te representan los buscadores y la IA.",
        "How search engines and AI represent you.",
      ),
      text: t(
        "Observa cómo aparece una organización en buscadores y respuestas generativas, con fecha, condiciones y muestra. Una mención no es una cita, y una cita no es una recomendación.",
        "Observe how an organization appears in search and generative answers, with date, conditions and sample. A mention is not a citation, and a citation is not an endorsement.",
      ),
      family: "presence",
      scene: "representation" as const,
    },
  ];
  const moments = [
    {
      date: "2026-07-01",
      title: t("Sabe qué hace.", "It knows what the company does."),
      text: t(
        "Su ficha pública describe lo que hace: aislar edificios para que gasten menos energía. Es lo único observado: lo que llegará después no entra en esta vista.",
        "Its public sheet describes what it does: insulating buildings so they use less energy. That is all that has been observed: what comes later does not enter this view.",
      ),
    },
    {
      date: "2026-09-01",
      title: t("Aparece algo nuevo.", "Something new appears."),
      text: t(
        "Se publica un programa público de ayudas para edificios más eficientes. AXIGNAL lo conecta con lo que la empresa hace: una posibilidad, no un contrato.",
        "A public grant programme for more efficient buildings is published. AXIGNAL connects it with what the company does: a possibility, not a contract.",
      ),
    },
    {
      date: "2026-10-03",
      title: t("Lo que sigue vigente.", "What is still current."),
      text: t(
        "Cada observación nueva actualiza la lectura. Lo que envejece deja de contar como actual; nada se borra.",
        "Each new observation updates the reading. What ages stops counting as current; nothing is erased.",
      ),
    },
  ];
  const selectedAudience = audiences[audience];
  return (
    <div className="landing funnel-landing">
      <PublicHeader landing />
      <main id="main">
        <section className="hero funnel-hero" id="what">
          <div className="hero-copy">
            <span className="eyebrow hero-eyebrow">
              <span className="quiet-dot" />
              {t(
                "Observación económica continua",
                "Continuous economic observation",
              )}
            </span>
            <h1>
              {t(
                "¿Qué está cambiando alrededor de tu empresa?",
                "Know what changes around your business.",
              )}
              <br />
              <em>{t("¿Y por qué importa?", "And why it matters to you.")}</em>
            </h1>
            <p className="hero-lead">
              {t(
                "AXIGNAL observa de forma continua las organizaciones que eliges —la tuya, tus clientes, tu competencia— en fuentes públicas. Recuerda lo que encuentra, detecta lo que cambia y separa lo que importa a ese negocio del ruido. Siempre con la fuente y la fecha.",
                "AXIGNAL continuously observes the organizations you choose — yours, your customers, your competitors — in public sources. It remembers what it finds, notices what changes and separates what matters to that business from the noise. Always with the source and the date.",
              )}
            </p>
            <div className="hero-actions">
              <CtaLink href={EXAMPLE_HREF} cta={funnelCta.heroExample} className="button primary">
                {t("Ver un ejemplo", "See an example")}
                <ArrowRight size={18} />
              </CtaLink>
              <CtaLink href="/signup" cta={funnelCta.heroStart} className="button secondary">
                {t("Empieza con tu organización", "Start with your organization")}
              </CtaLink>
            </div>
            <span className="hero-caption">
              {t(
                "Para quien dirige o hace crecer una empresa, y para las consultoras y agencias que acompañan a varias. 9,95 € al mes por organización.",
                "For people who run or grow a business, and for the consultancies and agencies that support several. €9.95 a month per organization.",
              )}
            </span>
          </div>
          <HeroReading />
        </section>

        <section className="chapter funnel-how" id="how">
          <Reveal className="chapter-heading">
            <span className="eyebrow">{t("Cómo funciona", "How it works")}</span>
            <h2>
              {t("Eliges qué observar.", "You choose what to observe.")}{" "}
              <em>{t("AXIGNAL no deja de mirar.", "AXIGNAL keeps looking.")}</em>
            </h2>
          </Reveal>
          <Reveal className="funnel-steps">
            {[
              {
                title: t("Eliges una organización.", "You choose an organization."),
                text: t(
                  "La tuya, un cliente, un competidor o cualquier empresa que te importe. Un nombre o su web bastan para empezar.",
                  "Yours, a customer, a competitor or any company you care about. A name or its website is enough to start.",
                ),
              },
              {
                title: t("AXIGNAL observa y recuerda.", "AXIGNAL observes and remembers."),
                text: t(
                  "Lee fuentes públicas —su web, registros oficiales, licitaciones— y guarda cada hallazgo con su fuente y su fecha. No tienes que reconstruir cada semana qué ha cambiado.",
                  "It reads public sources — its website, official registers, public tenders — and keeps each finding with its source and date. You no longer rebuild what changed every week.",
                ),
              },
              {
                title: t("Ves lo que importa y por qué.", "You see what matters and why."),
                text: t(
                  "Oportunidades, riesgos y cambios, filtrados por lo que ese negocio hace y por dónde trabaja. Cada uno explica por qué aparece y qué falta por saber.",
                  "Opportunities, risks and changes, filtered by what that business does and where it works. Each one explains why it appears and what is still unknown.",
                ),
              },
            ].map((step, i) => (
              <div className="funnel-step" key={step.title}>
                <span className="story-number">0{i + 1}</span>
                <h3>{step.title}</h3>
                <p>{step.text}</p>
              </div>
            ))}
          </Reveal>
          <Reveal className="funnel-axent">
            <p>
              <strong>AXENT</strong>{" "}
              {t(
                "te deja preguntar sobre todo ese contexto acumulado. Responde con sus fuentes y te dice cuándo no lo sabe. AXIGNAL observa y recuerda; AXENT te ayuda a entenderlo.",
                "lets you ask about all that accumulated context. It answers with its sources and tells you when it does not know. AXIGNAL observes and remembers; AXENT helps you understand it.",
              )}
            </p>
          </Reveal>
        </section>

        <section className="chapter funnel-proof" id="proof">
          <Reveal className="chapter-heading">
            <span className="eyebrow">{t("Por qué es distinto", "Why it is different")}</span>
            <h2>
              {t("No es otro chat que empieza de cero.", "Not another chat that starts from scratch.")}{" "}
              <em>{t("Es memoria con evidencia.", "It is memory with evidence.")}</em>
            </h2>
          </Reveal>
          <div className="proof-grid">
            <Reveal className="proof-card proof-reach">
              <MapPinned size={22} aria-hidden="true" />
              <h3>{t("Sabe dónde juega cada negocio.", "It knows where each business plays.")}</h3>
              <p>
                {t(
                  "Distingue dónde trabaja, hacia dónde podría crecer y qué le afecta desde fuera. Lo que ocurre lejos de su mercado no se convierte en una oportunidad.",
                  "It tells apart where a business works, where it could grow and what affects it from outside. What happens far from its market does not become an opportunity.",
                )}
              </p>
              <CtaLink href={EXAMPLE_HREF + "?family=markets"} cta={funnelCta.proofExample} className="text-link">
                {t("Ver su alcance en el ejemplo", "See its reach in the example")}
                <ArrowUpRight size={16} />
              </CtaLink>
            </Reveal>
            <Reveal className="proof-card proof-evidence">
              <BookOpen size={22} aria-hidden="true" />
              <h3>{t("Enseña de dónde sale cada conclusión.", "It shows where each conclusion comes from.")}</h3>
              <p>
                {t(
                  "Fuente, fecha de observación y vigencia, a un clic. Sin consolas técnicas ni cajas negras.",
                  "Source, observation date and currentness, one click away. No technical consoles, no black boxes.",
                )}
              </p>
              <CtaLink href={EXAMPLE_HREF + "?signal=renovation&depth=prove"} cta={funnelCta.proofExample} className="text-link">
                {t("Abrir una evidencia", "Open a piece of evidence")}
                <ArrowUpRight size={16} />
              </CtaLink>
            </Reveal>
            <Reveal className="proof-card proof-unknown">
              <CircleHelp size={22} aria-hidden="true" />
              <h3>{t("Dice lo que todavía no sabe.", "It says what it does not know yet.")}</h3>
              <p>
                {t(
                  "Si la evidencia no basta, lo marca como desconocido en vez de adivinar. Desconocido no es falso: es una pregunta abierta.",
                  "When evidence is not enough, it marks it as unknown instead of guessing. Unknown is not false: it is an open question.",
                )}
              </p>
              <CtaLink href={EXAMPLE_HREF + "?signal=reputation-gap"} cta={funnelCta.proofExample} className="text-link">
                {t("Ver una pregunta abierta", "See an open question")}
                <ArrowUpRight size={16} />
              </CtaLink>
            </Reveal>
          </div>
          <Reveal className="time-demo funnel-time">
            <div className="funnel-time-copy">
              <Clock3 size={22} aria-hidden="true" />
              <h3>{t("Recuerda cuándo supo cada cosa.", "It remembers when it learned each thing.")}</h3>
              <p>
                {t(
                  "Separa lo que ocurrió, cuándo se supo y lo que ya no está vigente. Puedes volver a cualquier fecha y ver solo lo que se sabía entonces.",
                  "It separates what happened, when it became known and what is no longer current. You can go back to any date and see only what was known then.",
                )}
              </p>
            </div>
            <div className="time-quote" aria-live="polite">
              <span className="mono">{dateLabel(moments[time].date, locale)}</span>
              <h3>{moments[time].title}</h3>
              <p>{moments[time].text}</p>
            </div>
            <div
              className="teaching-timeline"
              role="group"
              aria-label={t("Recorrer el tiempo del ejemplo", "Move through the example's time")}
            >
              {moments.map((moment, i) => (
                <button
                  key={moment.date}
                  className={time === i ? "selected" : ""}
                  aria-pressed={time === i}
                  onClick={() => setTime(i)}
                >
                  <span className="timeline-node" />
                  <span className="mono">{dateLabel(moment.date, locale)}</span>
                  <strong>{moment.title}</strong>
                </button>
              ))}
            </div>
            <CtaLink href={EXAMPLE_HREF + "?asOf=2026-07-01"} cta={funnelCta.proofExample} className="text-link">
              {t("Volver a julio en el ejemplo", "Go back to July in the example")}
              <ArrowUpRight size={16} />
            </CtaLink>
          </Reveal>
        </section>

        <section className="chapter use-section funnel-audience" id="audience">
          <Reveal className="use-heading">
            <span className="eyebrow">{t("Para quién", "Who it is for")}</span>
            <h2>
              {t("Pensado para quien necesita contexto", "Built for people who need context")}{" "}
              <em>{t("antes de decidir.", "before deciding.")}</em>
            </h2>
          </Reveal>
          <div
            className="use-tabs"
            role="tablist"
            aria-label={t("Situaciones en las que AXIGNAL ayuda", "Situations where AXIGNAL helps")}
          >
            {audiences.map((item, i) => (
              <button
                key={item.family}
                role="tab"
                id={"audience-tab-" + i}
                aria-selected={audience === i}
                aria-controls="audience-panel"
                tabIndex={audience === i ? 0 : -1}
                onKeyDown={(e) => {
                  const step =
                    e.key === "ArrowRight" || e.key === "ArrowDown"
                      ? 1
                      : e.key === "ArrowLeft" || e.key === "ArrowUp"
                        ? -1
                        : 0;
                  if (step || e.key === "Home" || e.key === "End") {
                    e.preventDefault();
                    const next =
                      e.key === "Home"
                        ? 0
                        : e.key === "End"
                          ? audiences.length - 1
                          : (i + step + audiences.length) % audiences.length;
                    setAudience(next);
                    document.getElementById("audience-tab-" + next)?.focus();
                  }
                }}
                onClick={() => setAudience(i)}
              >
                {item.name}
              </button>
            ))}
          </div>
          <div
            className="use-panel"
            role="tabpanel"
            id="audience-panel"
            aria-labelledby={"audience-tab-" + audience}
          >
            <div className="use-panel-content">
              <h3>{selectedAudience.title}</h3>
              <p>{selectedAudience.text}</p>
              <CtaLink
                href={EXAMPLE_HREF + "?family=" + selectedAudience.family}
                cta={funnelCta.audienceExample}
                className="text-link"
              >
                {t("Verlo en el ejemplo", "See it in the example")}
                <ArrowRight size={16} />
              </CtaLink>
            </div>
            <FramedObserver className="use-observer" scene={selectedAudience.scene} />
          </div>
        </section>

        <section className="chapter funnel-trust" id="trust">
          <Reveal className="chapter-heading">
            <span className="eyebrow">{t("Confianza", "Trust")}</span>
            <h2>
              {t("Lo que AXIGNAL no hará.", "What AXIGNAL will not do.")}
            </h2>
          </Reveal>
          <Reveal className="trust-commitments">
            {[
              {
                title: t("Inventar conclusiones.", "Make up conclusions."),
                text: t(
                  "Lo observado se marca como observado; lo posible, como posible; lo desconocido, como desconocido.",
                  "What was observed is marked as observed; what is possible, as possible; what is unknown, as unknown.",
                ),
              },
              {
                title: t("Vender lo que dice.", "Sell what it says."),
                text: t(
                  "Nadie puede pagar para cambiar lo que AXIGNAL dice de una organización, tampoco quien la observa.",
                  "Nobody can pay to change what AXIGNAL says about an organization, including whoever observes it.",
                ),
              },
              {
                title: t("Mezclar tu cuenta con el mundo.", "Mix your account with the world."),
                text: t(
                  "Lo que observas y lo que preguntas es privado. Lo que AXIGNAL sabe del mundo procede de fuentes públicas.",
                  "What you observe and what you ask stays private. What AXIGNAL knows about the world comes from public sources.",
                ),
              },
            ].map((item) => (
              <div key={item.title}>
                <h3>{item.title}</h3>
                <p>{item.text}</p>
              </div>
            ))}
          </Reveal>
          <div className="trust-links">
            <Link className="text-link" href="/policies">
              {t("Cómo tratamos los datos", "How we handle data")}
              <ArrowUpRight size={16} />
            </Link>
            <Link className="text-link" href="/knowledge/basis/product-model">
              {t("El método, explicado", "The method, explained")}
              <ArrowUpRight size={16} />
            </Link>
          </div>
        </section>

        <ReferencePricing focuses={focuses} onChange={setFocuses} />

        <section className="closing-scene funnel-closing">
          <span className="eyebrow">AXIGNAL</span>
          <h2>
            {t("Empieza por una organización.", "Start with one organization.")}{" "}
            <em>{t("AXIGNAL seguirá mirando.", "AXIGNAL will keep looking.")}</em>
          </h2>
          <div className="hero-actions">
            <CtaLink href="/signup" cta={funnelCta.closingStart} className="button primary">
              {t("Empieza con tu organización", "Start with your organization")}
              <ArrowRight size={18} />
            </CtaLink>
            <CtaLink href={EXAMPLE_HREF} cta={funnelCta.closingExample} className="button secondary">
              {t("Ver un ejemplo", "See an example")}
            </CtaLink>
          </div>
          <Observer className="closing-observer" scene="journey" />
        </section>
      </main>
      <MiniFooter />
    </div>
  );
}

