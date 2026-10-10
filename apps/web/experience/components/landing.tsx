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
import { LandingObservatory, type DemoMode } from "./landing-observatory";
import type { ExampleMoment } from "@/lib/landing-observatory";
import { PublicHeader } from "./public-shell";
import { ReferencePricing } from "./landing-extras";
import { FramedObserver } from "./observer-frame";
import { useLocale } from "@/lib/locale";
import {
  funnelCta,
  landingChapters,
  track,
  type FunnelCta,
} from "@/lib/funnel-events";
import { MiniFooter, Observer } from "./ui";

/** The one public example. Every "show me" on the site lands here. */
export const EXAMPLE_HREF = "/demo";

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
 * The first viewport shows the product working, not a picture of it: the real subscriber
 * interface on the one public example (fictional, and labelled so), annotated by El Observador.
 */
function HeroReading() {
  const { t } = useLocale();
  return <LandingObservatory mode="glance" className="lx-hero-window" footer={
    <CtaLink href={EXAMPLE_HREF} cta={funnelCta.heroExample} className="lx-open">
      {t("Abrir el ejemplo completo", "Open the full example")}
      <ArrowRight size={16} />
    </CtaLink>
  }/>;
}

/** Scroll position chooses the window's state; it never moves the page for the visitor. */
function useActiveStep() {
  const [active, setActive] = useState(0);
  useEffect(() => {
    let frame = 0;
    const measure = () => {
      frame = 0;
      const middle = window.innerHeight / 2;
      document.querySelectorAll<HTMLElement>(".lx-step[data-step]").forEach((node) => {
        const box = node.getBoundingClientRect();
        if (box.top <= middle && box.bottom > middle) setActive(Number(node.dataset.step));
      });
    };
    const schedule = () => { if (!frame) frame = window.requestAnimationFrame(measure); };
    measure();
    window.addEventListener("scroll", schedule, { passive: true });
    window.addEventListener("resize", schedule);
    return () => { window.removeEventListener("scroll", schedule); window.removeEventListener("resize", schedule); if (frame) window.cancelAnimationFrame(frame); };
  }, []);
  return active;
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
  const [time, setTime] = useState(0);
  const [proof, setProof] = useState(1);
  const activeStep = useActiveStep();
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
  const moments: ExampleMoment[] = ["2026-07-01", "2026-09-01", "2026-10-03"];
  const proofs = [
    {
      id: "reach",
      icon: <MapPinned size={20} aria-hidden="true" />,
      title: t("Sabe dónde juega cada negocio.", "It knows where each business plays."),
      text: t(
        "Distingue dónde trabaja, hacia dónde podría crecer y qué le afecta desde fuera. Lo que ocurre lejos de su mercado no se convierte en una oportunidad.",
        "It tells apart where a business works, where it could grow and what affects it from outside. What happens far from its market does not become an opportunity.",
      ),
      cta: t("Ver su alcance en el ejemplo", "See its reach in the example"),
      example: "?family=markets",
    },
    {
      id: "evidence",
      icon: <BookOpen size={20} aria-hidden="true" />,
      title: t("Enseña de dónde sale cada conclusión.", "It shows where each conclusion comes from."),
      text: t(
        "Fuente, fecha de observación y vigencia, a un clic. Sin consolas técnicas ni cajas negras.",
        "Source, observation date and currentness, one click away. No technical consoles, no black boxes.",
      ),
      cta: t("Abrir una evidencia", "Open a piece of evidence"),
      example: "?signal=renovation&depth=prove",
    },
    {
      id: "unknown",
      icon: <CircleHelp size={20} aria-hidden="true" />,
      title: t("Dice lo que todavía no sabe.", "It says what it does not know yet."),
      text: t(
        "Si la evidencia no basta, lo marca como desconocido en vez de adivinar. Desconocido no es falso: es una pregunta abierta.",
        "When evidence is not enough, it marks it as unknown instead of guessing. Unknown is not false: it is an open question.",
      ),
      cta: t("Ver una pregunta abierta", "See an open question"),
      example: "?signal=reputation-gap",
    },
    {
      id: "time",
      icon: <Clock3 size={20} aria-hidden="true" />,
      title: t("Recuerda cuándo supo cada cosa.", "It remembers when it learned each thing."),
      text: t(
        "Separa lo que ocurrió, cuándo se supo y lo que ya no está vigente. Mueve el ejemplo de julio a octubre: lo nuevo se enciende hasta que lo ves.",
        "It separates what happened, when it became known and what is no longer current. Move the example from July to October: what is new stays lit until you see it.",
      ),
      cta: t("Volver a julio en el ejemplo", "Go back to July in the example"),
      example: "?asOf=2026-07-01",
    },
  ];
  const steps = [
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
  ];
  const stepModes: DemoMode[] = ["add", "observing", "briefing"];
  const proofModes: DemoMode[] = ["briefing", "evidence", "unknown", "time"];
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
                "Para quien dirige o hace crecer una empresa, y para las consultoras y agencias que acompañan a varias. 9,95 € al mes con una organización incluida y 4,95 € por cada organización adicional.",
                "For people who run or grow a business, and for the consultancies and agencies that support several. €9.95 a month with one organization included, and €4.95 for each additional organization.",
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
          <div className="lx-scrolly">
            <ol className="lx-steps">
              {steps.map((step, i) => (
                <li className={"lx-step" + (activeStep === i ? " is-active" : "")} key={step.title} data-step={i}>
                  <span className="lx-step-mark" aria-hidden="true">{i + 1}</span>
                  <h3>{step.title}</h3>
                  <p>{step.text}</p>
                  <LandingObservatory mode={stepModes[i]} className="lx-step-window" />
                </li>
              ))}
            </ol>
            <div className="lx-sticky" aria-hidden="true">
              <LandingObservatory mode={stepModes[activeStep]} />
            </div>
          </div>
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
          <div className="lx-proof">
            <div className="lx-proof-tabs" role="tablist" aria-label={t("Cuatro pruebas en el ejemplo", "Four proofs in the example")}>
              {proofs.map((item, i) => (
                <button
                  key={item.id}
                  role="tab"
                  id={"proof-tab-" + i}
                  aria-selected={proof === i}
                  aria-controls="proof-panel"
                  tabIndex={proof === i ? 0 : -1}
                  className="lx-proof-tab"
                  onClick={() => setProof(i)}
                  onKeyDown={(e) => {
                    const step = e.key === "ArrowDown" || e.key === "ArrowRight" ? 1 : e.key === "ArrowUp" || e.key === "ArrowLeft" ? -1 : 0;
                    if (step) {
                      e.preventDefault();
                      const next = (i + step + proofs.length) % proofs.length;
                      setProof(next);
                      document.getElementById("proof-tab-" + next)?.focus();
                    }
                  }}
                >
                  {item.icon}
                  <span><strong>{item.title}</strong><small>{item.text}</small></span>
                </button>
              ))}
            </div>
            <div className="lx-proof-stage" role="tabpanel" id="proof-panel" aria-labelledby={"proof-tab-" + proof}>
              <LandingObservatory
                mode={proofModes[proof]}
                asOf={proofModes[proof] === "time" ? moments[time] : "2026-10-03"}
                onAsOf={(moment) => setTime(moments.indexOf(moment))}
                footer={
                  <CtaLink href={EXAMPLE_HREF + proofs[proof].example} cta={funnelCta.proofExample} className="lx-open">
                    {proofs[proof].cta}
                    <ArrowUpRight size={16} />
                  </CtaLink>
                }
              />
            </div>
          </div>
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

