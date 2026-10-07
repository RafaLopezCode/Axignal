"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import {
  ArrowRight,
  ArrowUp,
  ArrowUpRight,
  Pause,
  Play,
  BookOpen,
  ShieldCheck,
  Clock3,
  Check,
  Menu,
} from "lucide-react";
import { useLocale } from "@/lib/locale";
import { articles, readingMinutes } from "@/lib/editorial";
import { Observer, Dialog } from "./ui";
import { DraftForm } from "./drafts";
import { EditorialArt } from "./knowledge";
import { monthlyReferenceCents } from "@/lib/presentation";
export function UseCaseLens({
  names,
  selected,
}: {
  names: string[];
  selected: number;
}) {
  const { t, reducedMotion } = useLocale();
  const [paused, setPaused] = useState(false);
  const still = paused || reducedMotion;
  const strip = (
    <div className="case-strip">
      {[...names, ...names].map((name, i) => (
        <span key={i}>{name}</span>
      ))}
    </div>
  );
  return (
    <div className="use-case-observatory" data-paused={still}>
      <div className="case-belt" aria-hidden="true">
        {strip}
      </div>
      <div className="case-focus" aria-hidden="true">
        {still ? <span className="case-static">{names[selected]}</span> : strip}
      </div>
      <div className="case-aperture" aria-hidden="true">
        <span className="mono">
          {t("Una pregunta, en foco", "A question, in focus")}
        </span>
      </div>
      <div className="case-belt-controls">
        <span>
          {t(
            "Distintas preguntas. El mismo mundo.",
            "Different questions. The same world.",
          )}
        </span>
        <button
          className="text-link"
          onClick={() => setPaused(!paused)}
          aria-pressed={paused}
          disabled={reducedMotion}
        >
          {still ? <Play size={14} /> : <Pause size={14} />}{" "}
          {reducedMotion
            ? t("Movimiento reducido", "Reduced motion")
            : paused
              ? t("Activar movimiento", "Resume motion")
              : t("Pausar movimiento", "Pause motion")}
        </button>
      </div>
    </div>
  );
}
export function ReferencePricing({
  focuses,
  onChange,
}: {
  focuses: number;
  onChange: (n: number) => void;
}) {
  const { t, locale } = useLocale();
  const money = (cents: number) =>
    new Intl.NumberFormat(locale, {
      style: "currency",
      currency: "EUR",
    }).format(cents / 100);
  return (
    <section className="chapter reference-pricing" id="subscription">
      <div className="pricing-perspective">
        <span className="eyebrow">
          07 /{" "}
          {t(
            "Pricing · Observación persistente",
            "Pricing · Persistent observation",
          )}
        </span>
        <h2>
          {t("Elige dónde", "Choose where")}
          <br />
          <em>{t("poner la atención.", "to pay attention.")}</em>
        </h2>
        <p>
          {t(
            "Observas organizaciones con continuidad. Las señales que emergen no se cobran una a una y el mundo económico sigue siendo compartido.",
            "Observe organizations continuously. Emerging signals are not billed individually, and the economic world remains shared.",
          )}
        </p>
        <Observer scene="focus" />
        <span className="hand-note">
          {t(
            "tu atención encuentra su alcance",
            "your attention finds its scope",
          )}
        </span>
      </div>
      <div className="pricing-paper">
        <span className="eyebrow">
          {t("AXIGNAL · Autoservicio", "AXIGNAL · Self-service")}
        </span>
        <div className="reference-price">
          <strong>{money(monthlyReferenceCents(focuses))}</strong>
          <span>/{t("mes", "month")}</span>
        </div>
        <p>
          {focuses}{" "}
          {focuses === 1
            ? t(
                "organización bajo observación",
                "organization under observation",
              )
            : t(
                "organizaciones bajo observación",
                "organizations under observation",
              )}
        </p>
        <label htmlFor="pricing-focuses">
          {t(
            "Organizaciones que quieres observar",
            "Organizations you want to observe",
          )}
          <output htmlFor="pricing-focuses">{focuses}</output>
        </label>
        <input
          id="pricing-focuses"
          type="range"
          min={1}
          max={100}
          value={focuses}
          onChange={(e) => onChange(Number(e.target.value))}
        />
        <div
          className="pricing-shortcuts"
          role="group"
          aria-label={t("Elegir alcance", "Choose scope")}
        >
          {[1, 5, 25, 100].map((n) => (
            <button
              key={n}
              aria-pressed={focuses === n}
              onClick={() => onChange(n)}
            >
              {n}
            </button>
          ))}
        </div>
        <p className="pricing-calculation">
          {money(995)}{" "}
          {t(
            "incluye la primera organización;",
            "includes the first organization;",
          )}{" "}
          {money(495)}{" "}
          {t(
            "por cada observación adicional.",
            "for each additional observation.",
          )}
        </p>
        <ul>
          {[
            t(
              "Panorama contextual y temporal",
              "Contextual, temporal Panorama",
            ),
            t(
              "Evidencia y límites inspeccionables",
              "Inspectable evidence and limits",
            ),
            t(
              "Axent para investigar y comprender",
              "Axent for research and understanding",
            ),
          ].map((x) => (
            <li key={x}>
              <Check size={16} />
              {x}
            </li>
          ))}
        </ul>
        <Link href="/signup" className="button primary">
          {t("Preparar mi acceso", "Prepare my access")}
          <ArrowRight size={17} />
        </Link>
        <small>
          {t(
            "Precios de referencia del modelo de producto, pendientes de validación económica. Impuestos y condiciones de contratación pendientes de publicación. Esta demo no realiza cobros.",
            "Product-model reference prices, pending economic validation. Taxes and contracting terms are pending publication. This demo does not charge you.",
          )}
        </small>
      </div>
      <aside className="human-advisory">
        <div>
          <span className="eyebrow">
            {t("Un servicio humano, separado", "A separate human service")}
          </span>
          <h3>
            {t("AXIGNAL con asesoría humana", "AXIGNAL with human advisory")}
          </h3>
          <p>
            {t(
              "Una organización dentro del alcance acordado, cuatro actualizaciones semanales con evidencia y una revisión estratégica mensual. Las observaciones con trabajo humano adicional requieren un alcance propio.",
              "One organization within the agreed scope, four evidence-backed weekly updates and one monthly strategic review. Additional observation involving human work requires its own scope.",
            )}
          </p>
        </div>
        <div>
          <strong>
            {money(99500)} <span>/{t("mes", "month")}</span>
          </strong>
          <small>
            {t(
              "+ IVA aplicable · precio de lanzamiento",
              "+ applicable VAT · launch price",
            )}
          </small>
          <Link href="/contact" className="text-link">
            {t("Conversar sobre el alcance", "Discuss the scope")}
            <ArrowUpRight size={16} />
          </Link>
        </div>
      </aside>
    </section>
  );
}
export function LandingNotebook() {
  const { t, copy, locale } = useLocale();
  return (
    <section className="chapter landing-notebook" id="knowledge-preview">
      <header>
        <span className="eyebrow">08 / Knowledge</span>
        <h2>
          {t("La curiosidad", "Curiosity")}
          <br />
          <em>{t("también se cultiva.", "grows with care, too.")}</em>
        </h2>
        <Link href="/knowledge" className="text-link">
          {t("Todo el cuaderno", "The whole notebook")}
          <ArrowUpRight size={18} />
        </Link>
      </header>
      <div className="notebook-preview-grid">
        {articles.slice(0, 3).map((a) => (
          <Link href={"/knowledge/" + a.slug} key={a.slug}>
            <EditorialArt kind={a.art} compact />
            <span className="eyebrow">
              {t("Lectura editorial", "Editorial reading")}
            </span>
            <h3>{copy(a.title)}</h3>
            <p>{copy(a.deck)}</p>
            <span className="article-meta">
              <Clock3 size={13} />
              {readingMinutes(a, locale)} min
              <ArrowUpRight size={16} />
            </span>
          </Link>
        ))}
      </div>
    </section>
  );
}
export function TrustProof() {
  const { t } = useLocale();
  const proofs = [
    {
      icon: BookOpen,
      title: t("Una base que puedes leer.", "A basis you can read."),
      body: t(
        "Las ideas del cuaderno llevan a extractos de la doctrina que las sostiene.",
        "Notebook ideas lead to excerpts of the doctrine that supports them.",
      ),
      href: "/knowledge/basis/product-model",
      cta: t("Inspeccionar la base", "Inspect the basis"),
    },
    {
      icon: Clock3,
      title: t(
        "El pasado conserva sus límites.",
        "The past retains its limits.",
      ),
      body: t(
        "Explora una vista histórica de la demo: una fuente posterior no entra en esa lectura.",
        "Explore a historical demo view: a later source does not enter that reading.",
      ),
      href: "/panorama?asOf=2026-07-01",
      cta: t("Explorar julio", "Explore July"),
    },
    {
      icon: ShieldCheck,
      title: t(
        "La confianza empieza por la claridad.",
        "Trust begins with clarity.",
      ),
      body: t(
        "Conoce el alcance de AXIGNAL, sus límites y la información pública del responsable.",
        "Understand AXIGNAL's scope, its limits and the controller's public information.",
      ),
      href: "/policies",
      cta: t("Leer nuestros límites", "Read our limits"),
    },
  ];
  return (
    <section className="chapter trust-proof" id="trust-proof">
      <span className="eyebrow">
        {t("Compruébalo por ti", "See for yourself")}
      </span>
      <h2>
        {t("La confianza", "Trust")}{" "}
        <em>{t("se comprueba.", "can be inspected.")}</em>
      </h2>
      <p>
        {t(
          "Antes de pedirte confianza, te acercamos su fundamento. Esta demo ofrece recorridos inspeccionables; no presenta testimonios ni resultados de clientes sin validar.",
          "Before asking for trust, we bring its basis closer. This demo offers inspectable paths; it does not present unvalidated testimonials or customer results.",
        )}
      </p>
      <div>
        {proofs.map((p) => (
          <article key={p.href}>
            <p.icon size={23} />
            <h3>{p.title}</h3>
            <p>{p.body}</p>
            <Link className="text-link" href={p.href}>
              {p.cta}
              <ArrowUpRight size={16} />
            </Link>
          </article>
        ))}
      </div>
    </section>
  );
}
export function NewsletterInvitation() {
  const { t } = useLocale();
  const [open, setOpen] = useState(false);
  return (
    <section className="chapter newsletter-invitation" id="newsletter">
      <div>
        <span className="eyebrow">
          09 / {t("El brief del Observador", "The Observer's brief")}
        </span>
        <h2>
          {t("Una semana.", "One week.")}
          <br />
          <em>
            {t("Una mirada con contexto.", "A perspective with context.")}
          </em>
        </h2>
        <p>
          {t(
            "Solicita una muestra editorial gratuita alrededor de una organización. Hasta tres señales públicas por semana cuando existan observaciones materiales, con fuente, fecha y límites.",
            "Request a free editorial sample around an organization. Up to three public signals a week when material observations exist, with sources, dates and limits.",
          )}
        </p>
        <p className="newsletter-boundary">
          {t(
            "La solicitud, la aceptación por cobertura y el consentimiento de envío son pasos distintos. No abre un plan gratuito, un foco de observación ni acceso a Axent.",
            "Request, acceptance based on coverage and delivery consent are separate steps. This creates no free plan, observation focus or Axent access.",
          )}
        </p>
        <button className="button primary" onClick={() => setOpen(true)}>
          {t("Preparar mi solicitud", "Prepare my request")}
          <ArrowRight size={17} />
        </button>
        <small>
          {t(
            "La solicitud automática aún no está habilitada. Puedes preparar un borrador local y contactar con AXIGNAL desde el canal público.",
            "Automatic submission is not enabled yet. You can prepare a local draft and contact AXIGNAL through the public channel.",
          )}
        </small>
      </div>
      <div className="newsletter-art">
        <div className="brief-paper">
          <span className="mono">AXIGNAL / BRIEF</span>
          <h3>{t("Menos ruido.", "Less noise.")}</h3>
          <em>{t("Más fundamento.", "More basis.")}</em>
          <i />
          <i />
          <span>
            {t("Fuente · Fecha · Contexto", "Source · Date · Context")}
          </span>
        </div>
        <span className="hand-note">
          {t(
            "si no hay cambios, también lo decimos",
            "if nothing changes, we say so",
          )}
        </span>
      </div>
      {open && (
        <Dialog
          title={t(
            "Solicitar el brief del Observador",
            "Request the Observer's brief",
          )}
          onClose={() => setOpen(false)}
          className="newsletter-request"
        >
          <p>
            {t(
              "Indica la organización o la web que te gustaría observar. La solicitud no se envía desde esta versión; el borrador no acredita aceptación ni consentimiento registrado.",
              "Describe the organization or website you would like to observe. This version does not send the request; the draft proves neither acceptance nor recorded consent.",
            )}
          </p>
          <DraftForm
            subject={t(
              "Solicitud de newsletter de observación",
              "Observation newsletter request",
            )}
          />
        </Dialog>
      )}
    </section>
  );
}
export function ChapterNavigation() {
  const { t } = useLocale();
  const [active, setActive] = useState("what");
  const [open, setOpen] = useState(false);
  const chapters = [
    { id: "what", name: t("Inicio", "Home") },
    { id: "start", name: t("Cómo empezar", "How to start") },
    { id: "growth", name: t("El contexto", "Context") },
    { id: "time", name: t("El tiempo", "Time") },
    { id: "use", name: t("Casos de uso", "Use cases") },
    { id: "explore", name: t("Explora", "Explore") },
    { id: "trust-proof", name: t("El fundamento", "The basis") },
    { id: "subscription", name: "Pricing" },
    { id: "knowledge-preview", name: "Knowledge" },
    { id: "newsletter", name: t("El brief", "The brief") },
  ];
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        for (const e of entries) if (e.isIntersecting) setActive(e.target.id);
      },
      { rootMargin: "-15% 0px -65% 0px" },
    );
    document
      .querySelectorAll("main > section[id]")
      .forEach((n) => observer.observe(n));
    return () => observer.disconnect();
  }, []);
  return (
    <>
      <nav
        className="chapter-wayfinder"
        aria-label={t("Capítulos de la Landing", "Landing chapters")}
      >
        {chapters.map((c, i) => (
          <a
            href={"#" + c.id}
            key={c.id}
            aria-current={active === c.id ? "location" : undefined}
          >
            <span className="mono">{String(i + 1).padStart(2, "0")}</span>
            <span>{c.name}</span>
          </a>
        ))}
      </nav>
      <div className="landing-quick-navigation">
        <button className="button secondary" onClick={() => setOpen(true)}>
          <Menu size={16} />
          {t("Explorar página", "Explore page")}
        </button>
        <a
          href="#what"
          className="icon-button"
          aria-label={t("Volver al inicio de la página", "Back to the top")}
        >
          <ArrowUp size={19} />
        </a>
      </div>
      {open && (
        <Dialog
          title={t("Sigue el hilo", "Follow the thread")}
          onClose={() => setOpen(false)}
          className="chapter-dialog"
        >
          <nav>
            {chapters.map((c) => (
              <a href={"#" + c.id} key={c.id} onClick={() => setOpen(false)}>
                {c.name}
                <ArrowRight size={16} />
              </a>
            ))}
          </nav>
        </Dialog>
      )}
    </>
  );
}
