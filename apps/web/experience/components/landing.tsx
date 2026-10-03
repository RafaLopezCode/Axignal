"use client";
import { FramedObserver } from "./observer-frame";
import Link from "next/link";
import { PublicHeader } from "./public-shell";
import {
  UseCaseLens,
  ReferencePricing,
  LandingNotebook,
  TrustProof,
  NewsletterInvitation,
  ChapterNavigation,
} from "./landing-extras";
import { useEffect, useRef, useState } from "react";
import {
  ArrowRight,
  ArrowDown,
  ArrowUpRight,
  Check,
  ScanEye,
  Layers3,
  Clock3,
  MoveRight,
  Building2,
  BookOpen,
  Network,
  ChevronRight,
} from "lucide-react";
import { useLocale } from "@/lib/locale";
import {
  Brand,
  AxentIdentity,
  LocaleToggle,
  Observer,
  Badge,
  DemoLabel,
  Dialog,
  MiniFooter,
} from "./ui";

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
export function LensScene({ compact = false }: { compact?: boolean }) {
  const { t } = useLocale();
  const [mode, setMode] = useState(0);
  return (
    <div
      className={
        "lens-scene " + (compact ? "compact-scene" : "") + " scene-mode-" + mode
      }
    >
      <div className="scene-topline">
        <span className="eyebrow">
          {t("Un mundo. Más contexto.", "One world. More context.")}
        </span>
        <span className="mono">{String(mode + 1).padStart(2, "0")} / 03</span>
      </div>
      <div className="scene-field">
        <div className="orbit orbit-one" />
        <div className="orbit orbit-two" />
        <svg
          className="scene-connections"
          viewBox="0 0 600 500"
          aria-hidden="true"
        >
          <path
            d="M115 135 C230 135 198 270 310 263 S412 125 510 180 M310 263 C335 390 470 373 490 415 M115 135 C90 310 206 425 310 263"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.2"
            strokeDasharray={mode === 0 ? "4 7" : "0"}
          />
        </svg>
        <div className="scene-card capability">
          <span className="card-index">01</span>
          <span className="mono">{t("Organización", "Organization")}</span>
          <h3>Norte Renovable</h3>
          <p>{t("Una capacidad conocida.", "A known capability.")}</p>
          <span className="scene-card-icon">
            <Building2 size={20} strokeWidth={1.5} />
          </span>
        </div>
        <div className="scene-card context">
          <span className="card-index">02</span>
          <span className="mono">{t("Contexto", "Context")}</span>
          <h3>{t("Rehabilitación", "Renovation")}</h3>
          <p>{t("Una necesidad emergente.", "An emerging need.")}</p>
          <span className="scene-card-icon">
            <Layers3 size={20} strokeWidth={1.5} />
          </span>
        </div>
        <button
          className="lens-core"
          onClick={() => setMode((mode + 1) % 3)}
          aria-label={t(
            "Cambiar la capa de observación",
            "Change observation layer",
          )}
        >
          <img src="/brand/isotope.svg" alt="" width="128" height="138" />
          <span>
            {
              [
                t("Observa", "Observe"),
                t("Conecta", "Connect"),
                t("Comprende", "Understand"),
              ][mode]
            }
          </span>
        </button>
        <div className="scene-card possibility">
          <Badge state="POTENTIAL" />
          <h3>{t("Algo merece atención.", "Something deserves attention.")}</h3>
          <p>
            {mode === 2
              ? t(
                  "Una posibilidad. Con evidencia y límites.",
                  "A possibility. With evidence and limits.",
                )
              : t(
                  "Las conexiones cambian lo que ves.",
                  "Connections change what you see.",
                )}
          </p>
          <ArrowUpRight size={18} />
        </div>
        <span className="hand-note scene-note">
          {t("mira un poco más cerca", "look a little closer")}
        </span>
        <Observer className="scene-observer" />
      </div>
      <div className="scene-bottom">
        <div
          className="scene-steps"
          role="group"
          aria-label={t("Capas de observación", "Observation layers")}
        >
          {[
            t("Observar", "Observe"),
            t("Conectar", "Connect"),
            t("Comprender", "Understand"),
          ].map((label, i) => (
            <button
              key={i}
              aria-pressed={mode === i}
              onClick={() => setMode(i)}
            >
              <span>0{i + 1}</span>
              {label}
            </button>
          ))}
        </div>
        <span className="scene-example">
          {t("Ejemplo ilustrativo", "Illustrative example")}
        </span>
      </div>
    </div>
  );
}
export function Landing() {
  const { t } = useLocale();
  const [time, setTime] = useState(2);
  const [useCase, setUseCase] = useState(0);
  const [focuses, setFocuses] = useState(1);
  const [about, setAbout] = useState(false);
  const chapters = [
    t("Qué es", "What it is"),
    t("Cómo empezar", "How to start"),
    t("Qué acumula", "What grows"),
    t("El tiempo", "Time"),
    t("Para quién", "For whom"),
    t("Explora", "Explore"),
    t("Suscripción", "Subscription"),
  ];
  const cases = [
    {
      name: t("Dirección estratégica", "Strategic leadership"),
      title: t("Ver antes de decidir.", "See before deciding."),
      text: t(
        "Entender un cambio, sus conexiones y los límites de lo que sabemos. El contexto económico precede a la decisión.",
        "Understand a change, its connections and the limits of what we know. Economic context comes before a decision.",
      ),
      tag: t("Contexto → Comprensión", "Context → Understanding"),
    },
    {
      name: t("Desarrollo de negocio", "Business development"),
      title: t("Investigar una posibilidad.", "Investigate a possibility."),
      text: t(
        "Reconocer necesidades relacionadas con capacidades, sin convertir una coincidencia en un cliente ni una posibilidad en una promesa.",
        "Recognize needs related to capabilities, without turning an overlap into a customer or a possibility into a promise.",
      ),
      tag: t("Capacidad → Posibilidad", "Capability → Possibility"),
    },
    {
      name: t("Ecosistemas y análisis", "Ecosystems & analysis"),
      title: t("Conectar sin simplificar.", "Connect without oversimplifying."),
      text: t(
        "Explorar actores, relaciones y contexto temporal. Cada camino conserva su significado y su evidencia.",
        "Explore actors, relationships and temporal context. Each path retains its meaning and evidence.",
      ),
      tag: t("Relaciones → Perspectiva", "Relationships → Perspective"),
    },
    {
      name: t("SEO y presencia digital", "SEO & digital presence"),
      title: t("Entender cómo te encuentran.", "Understand how you are found."),
      text: t(
        "Observar cómo buscadores y sistemas generativos representan una organización. Una mención, una cita y una recomendación no son lo mismo; el contexto de medida importa.",
        "Observe how search and generative systems represent an organization. A mention, a citation and an endorsement differ; measurement context matters.",
      ),
      tag: t("Representación → Contexto", "Representation → Context"),
    },
    {
      name: t("Marketing", "Marketing"),
      title: t(
        "Leer el contexto antes del mensaje.",
        "Read the context before the message.",
      ),
      text: t(
        "Comprender necesidades, capacidades y cambios para hacer mejores preguntas. AXIGNAL observa; no ejecuta campañas ni promete resultados.",
        "Understand needs, capabilities and changes to ask better questions. AXIGNAL observes; it does not execute campaigns or promise outcomes.",
      ),
      tag: t("Cambio → Pregunta", "Change → Question"),
    },
    {
      name: t("Comunicación", "Communications"),
      title: t(
        "Separar percepción y evidencia.",
        "Separate perception and evidence.",
      ),
      text: t(
        "Explorar la representación pública y reconocer lo que sostiene una lectura. La visibilidad de una organización no equivale a la verdad de su negocio.",
        "Explore public representation and recognize what supports a reading. An organization's visibility is not its business truth.",
      ),
      tag: t("Representación → Evidencia", "Representation → Evidence"),
    },
    {
      name: t("Investigación", "Research"),
      title: t(
        "Abrir una pregunta con método.",
        "Open a question with method.",
      ),
      text: t(
        "Relacionar actores, fuentes y momentos conservando procedencia, contradicciones y preguntas abiertas. Axent ayuda a investigar sin admitir verdad por su cuenta.",
        "Relate actors, sources and moments while preserving provenance, contradictions and open questions. Axent helps research without admitting truth on its own.",
      ),
      tag: t("Pregunta → Fundamento", "Question → Basis"),
    },
    {
      name: t("Periodismo", "Journalism"),
      title: t(
        "Seguir el hilo hasta la fuente.",
        "Follow the thread to its source.",
      ),
      text: t(
        "Comprender el contexto económico y volver a la evidencia que lo sostiene. Una explicación es un punto de partida para contrastar, no una fuente periodística fabricada.",
        "Understand economic context and return to its supporting evidence. An explanation starts verification; it is not a fabricated journalistic source.",
      ),
      tag: t("Contexto → Verificación", "Context → Verification"),
    },
  ];
  return (
    <div className="landing">
      <PublicHeader landing />
      <main id="main">
        <section className="hero" id="what">
          <div className="hero-copy">
            <span className="eyebrow hero-eyebrow">
              <span className="quiet-dot" />
              {t(
                "Inteligencia económica que observa",
                "Economic intelligence that observes",
              )}
            </span>
            <h1>
              {t("El mundo cambia.", "The world changes.")}
              <br />
              <em>{t("Tu mirada también.", "So does your perspective.")}</em>
            </h1>
            <p className="hero-lead">
              {t(
                "Encuentra sentido en lo que ocurre. Conecta señales, entiende su contexto y descubre qué merece tu atención.",
                "Find meaning in what happens. Connect signals, understand their context and discover what deserves your attention.",
              )}
            </p>
            <div className="hero-actions">
              <Link href="/panorama" className="button primary">
                {t("Descubrir mi Panorama", "Discover my Panorama")}
                <ArrowRight size={18} />
              </Link>
              <a href="#start" className="text-link">
                {t("Acércate un poco", "Look a little closer")}
                <ArrowDown size={16} />
              </a>
            </div>
            <span className="hero-caption">
              {t(
                "Observación continua. Comprensión que se acumula.",
                "Continuous observation. Understanding that compounds.",
              )}
            </span>
          </div>
          <LensScene />
          <div className="hero-bottom">
            <span className="mono">
              AXIGNAL / {t("EL OBSERVADOR ECONÓMICO", "THE ECONOMIC OBSERVER")}
            </span>
            <a
              href="#start"
              aria-label={t("Seguir descubriendo", "Keep discovering")}
            >
              <span>
                {t(
                  "Hay más debajo de la superficie",
                  "There is more beneath the surface",
                )}
              </span>
              <ArrowDown size={17} />
            </a>
          </div>
        </section>
        <section className="chapter start-section" id="start">
          <Reveal className="chapter-heading">
            <span className="eyebrow">02 / {chapters[1]}</span>
            <h2>
              {t(
                "Empieza por una organización.",
                "Start with an organization.",
              )}
              <br />
              <em>
                {t(
                  "Abre la mirada a su mundo.",
                  "Open your view to its world.",
                )}
              </em>
            </h2>
          </Reveal>
          <div className="start-grid">
            <Reveal className="start-illustration">
              <div className="focus-orbit">
                <span className="orbit-label one">
                  {t("Entorno", "Environment")}
                </span>
                <span className="orbit-label two">
                  {t("Capacidades", "Capabilities")}
                </span>
                <span className="orbit-label three">
                  {t("Relaciones", "Relationships")}
                </span>
                <div className="focus-subject">
                  <Building2 size={24} strokeWidth={1.5} />
                  <strong>{t("Tu organización", "Your organization")}</strong>
                  <span>
                    {t("El punto de atención", "The point of attention")}
                  </span>
                </div>
              </div>
              <span className="hand-note">
                {t(
                  "el foco es tuyo; el mundo es compartido",
                  "the focus is yours; the world is shared",
                )}
              </span>
            </Reveal>
            <Reveal className="numbered-story">
              {[
                [
                  t("Selecciona qué observar.", "Choose what to observe."),
                  t(
                    "Una organización orienta un foco persistente de atención. No crea un mundo aislado.",
                    "An organization directs a persistent focus of attention. It does not create an isolated world.",
                  ),
                ],
                [
                  t("Deja que el contexto se conecte.", "Let context connect."),
                  t(
                    "AXIGNAL investiga el entorno y conserva memoria económica, evidencia y temporalidad.",
                    "AXIGNAL investigates the surroundings and preserves economic memory, evidence and time.",
                  ),
                ],
                [
                  t("Comprende lo que emerge.", "Understand what emerges."),
                  t(
                    "Tu Panorama acerca lo relevante. AXENT te ayuda a investigarlo y explicarlo.",
                    "Your Panorama brings what matters closer. AXENT helps you investigate and explain it.",
                  ),
                ],
              ].map(([title, text], i) => (
                <div className="story-line" key={title}>
                  <span className="story-number">0{i + 1}</span>
                  <div>
                    <h3>{title}</h3>
                    <p>{text}</p>
                  </div>
                </div>
              ))}
            </Reveal>
          </div>
        </section>
        <section className="chapter growth-section" id="growth">
          <Reveal className="growth-copy">
            <span className="eyebrow">03 / {chapters[2]}</span>
            <h2>
              {t(
                "Cada observación deja contexto.",
                "Every observation leaves context.",
              )}
              <br />
              <em>
                {t(
                  "El contexto deja comprensión.",
                  "Context leaves understanding.",
                )}
              </em>
            </h2>
            <p>
              {t(
                "AXIGNAL recuerda, contrasta y vuelve a mirar. Lo conocido puede reevaluarse cuando cambian sus fuentes o sus condiciones. La inteligencia crece sin dar por eterna una conclusión.",
                "AXIGNAL remembers, compares and looks again. What is known can be reassessed when its sources or conditions change. Intelligence grows without treating a conclusion as eternal.",
              )}
            </p>
            <div className="growth-key">
              <Layers3 size={20} />
              <span>
                {t(
                  "Una memoria económica compartida. Una perspectiva para ti.",
                  "A shared economic memory. A perspective for you.",
                )}
              </span>
            </div>
          </Reveal>
          <Reveal className="memory-stack">
            <div className="memory-page back">
              <span className="mono">{t("LO CONOCIDO", "WHAT IS KNOWN")}</span>
              <h3>{t("Una capacidad.", "A capability.")}</h3>
              <div className="memory-rule" />
              <div className="memory-rule short" />
            </div>
            <div className="memory-page middle">
              <span className="mono">{t("LO QUE CAMBIA", "WHAT CHANGES")}</span>
              <h3>{t("Un nuevo contexto.", "A new context.")}</h3>
              <div className="memory-rule" />
              <div className="memory-rule short" />
            </div>
            <div className="memory-page front">
              <span className="mono">{t("LO QUE EMERGE", "WHAT EMERGES")}</span>
              <Badge state="POTENTIAL" />
              <h3>
                {t(
                  "Una posibilidad con fundamento.",
                  "A grounded possibility.",
                )}
              </h3>
              <p>
                {t(
                  "Y preguntas que aún merecen respuesta.",
                  "And questions that still deserve answers.",
                )}
              </p>
              <div className="memory-evidence">
                <BookOpen size={15} />
                {t("Conserva su evidencia", "Retains its evidence")}
                <ArrowUpRight size={16} />
              </div>
            </div>
            <span className="hand-note stack-note">
              {t("la comprensión se acumula", "understanding compounds")}
            </span>
          </Reveal>
        </section>
        <section className="chapter time-section" id="time">
          <Reveal className="chapter-heading">
            <span className="eyebrow">04 / {chapters[3]}</span>
            <h2>
              {t("Una señal tiene un antes.", "A signal has a before.")}
              <br />
              <em>
                {t(
                  "Y una razón para importar ahora.",
                  "And a reason to matter now.",
                )}
              </em>
            </h2>
            <p>
              {t(
                "Recorre el tiempo para distinguir lo que ocurrió, lo que conocimos después y lo que todavía no podemos sostener.",
                "Move through time to distinguish what happened, what we learned later and what we cannot yet support.",
              )}
            </p>
          </Reveal>
          <Reveal className="time-demo">
            <div className="time-quote" aria-live="polite">
              <span className="mono">
                {
                  [
                    t(
                      "01 JUL 2026 · CONTEXTO INICIAL",
                      "01 JUL 2026 · INITIAL CONTEXT",
                    ),
                    t(
                      "01 SEP 2026 · NUEVO CONTEXTO",
                      "01 SEP 2026 · NEW CONTEXT",
                    ),
                    t(
                      "03 OCT 2026 · PERSPECTIVA ACTUAL",
                      "03 OCT 2026 · CURRENT VIEW",
                    ),
                  ][time]
                }
              </span>
              <h3>
                {
                  [
                    t(
                      "Sabemos qué capacidad declara.",
                      "We know the capability it declares.",
                    ),
                    t(
                      "Aparece una necesidad relacionada.",
                      "A related need appears.",
                    ),
                    t(
                      "Entendemos qué investigar y qué sigue abierto.",
                      "We understand what to investigate and what remains open.",
                    ),
                  ][time]
                }
              </h3>
              <p>
                {
                  [
                    t(
                      "No conocemos aún el programa. El futuro no entra en esta vista.",
                      "We do not yet know the programme. The future does not enter this view.",
                    ),
                    t(
                      "Una coincidencia temática abre una posibilidad; no demuestra un contrato.",
                      "A thematic overlap opens a possibility; it does not establish a contract.",
                    ),
                    t(
                      "Cada nueva observación vuelve a situar la señal sin borrar sus límites.",
                      "Each new observation reframes the signal without erasing its limits.",
                    ),
                  ][time]
                }
              </p>
            </div>
            <div
              className="teaching-timeline"
              role="group"
              aria-label={t("Explorar el tiempo", "Explore time")}
            >
              {[
                t("Una capacidad", "A capability"),
                t("Un cambio", "A change"),
                t("Una nueva lectura", "A new reading"),
              ].map((label, i) => (
                <button
                  key={i}
                  className={time === i ? "selected" : ""}
                  aria-pressed={time === i}
                  onClick={() => setTime(i)}
                >
                  <span className="timeline-node" />
                  <span className="mono">{["JUL", "SEP", "OCT"][i]} 2026</span>
                  <strong>{label}</strong>
                </button>
              ))}
            </div>
          </Reveal>
        </section>
        <section className="chapter use-section" id="use">
          <Reveal className="use-heading">
            <span className="eyebrow">05 / {chapters[4]}</span>
            <h2>
              {t("Más perspectiva.", "More perspective.")}
              <br />
              <em>{t("Para preguntas mejores.", "For better questions.")}</em>
            </h2>
          </Reveal>
          <UseCaseLens
            names={cases.map((item) => item.name)}
            selected={useCase}
          />
          <div
            className="use-tabs"
            role="tablist"
            aria-label={t("Formas de usar AXIGNAL", "Ways to use AXIGNAL")}
          >
            {cases.map((item, i) => (
              <button
                key={i}
                role="tab"
                id={"case-tab-" + i}
                aria-selected={useCase === i}
                aria-controls="case-panel"
                tabIndex={useCase === i ? 0 : -1}
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
                          ? cases.length - 1
                          : (i + step + cases.length) % cases.length;
                    setUseCase(next);
                    document.getElementById("case-tab-" + next)?.focus();
                  }
                }}
                onClick={() => setUseCase(i)}
              >
                {item.name}
                <ArrowUpRight size={16} />
              </button>
            ))}
          </div>
          <div
            className="use-panel"
            role="tabpanel"
            id="case-panel"
            aria-labelledby={"case-tab-" + useCase}
          >
            <div className="use-panel-content">
            <span className="mono">{cases[useCase].tag}</span>
            <h3>{cases[useCase].title}</h3>
            <p>{cases[useCase].text}</p>
            <Link href="/panorama" className="text-link">
              {t("Ver un ejemplo", "See an example")}
              <ArrowRight size={16} />
            </Link>
            </div>
            <FramedObserver className="use-observer"
              pose={([
                "guiding", "analyzing", "connecting", "pointing",
                "reflecting", "accompanying", "connecting", "pointing",
              ] as const)[useCase]}
            />
          </div>
        </section>
        <section className="chapter explore-section" id="explore">
          <Reveal className="chapter-heading">
            <span className="eyebrow">06 / {chapters[5]}</span>
            <h2>
              {t("La comprensión se siente", "Understanding feels")}
              <br />
              <em>
                {t(
                  "cuando puedes explorar.",
                  "different when you can explore.",
                )}
              </em>
            </h2>
            <p>
              {t(
                "Acerca una familia, abre una señal, vuelve a su evidencia. No necesitas empezar una conversación para entender lo esencial.",
                "Bring a family closer, open a signal, return to its evidence. You do not need to start a conversation to understand what matters.",
              )}
            </p>
          </Reveal>
          <Reveal className="landing-product-preview">
            <div className="preview-chrome">
              <Brand />
              <DemoLabel />
              <Link href="/panorama">
                {t("Abrir experiencia", "Open experience")}
                <ArrowUpRight size={16} />
              </Link>
            </div>
            <div className="preview-content">
              <div className="preview-families">
                <span className="mono">
                  {t("TU MIRADA", "YOUR PERSPECTIVE")}
                </span>
                {[
                  t("Panorama", "Panorama"),
                  t("Mercados", "Markets"),
                  t("Presencia", "Presence"),
                  t("Relaciones", "Relationships"),
                ].map((name, i) => (
                  <Link
                    className={i === 1 ? "selected" : ""}
                    key={name}
                    href={
                      "/panorama?family=" +
                      ["overview", "markets", "presence", "relationships"][i]
                    }
                  >
                    {name}
                    <ChevronRight size={14} />
                  </Link>
                ))}
              </div>
              <div className="preview-signal">
                <span className="eyebrow">
                  {t("Norte Renovable / Mercados", "Norte Renovable / Markets")}
                </span>
                <Badge state="POTENTIAL" />
                <h3>
                  {t(
                    "La rehabilitación abre una nueva conversación.",
                    "Renovation opens a new conversation.",
                  )}
                </h3>
                <p>
                  {t(
                    "Una capacidad conocida encuentra un contexto de demanda. Su encaje comercial sigue abierto.",
                    "A known capability meets a demand context. Its commercial fit remains open.",
                  )}
                </p>
                <Link
                  className="button secondary"
                  href="/panorama?signal=renovation"
                >
                  {t("Entender esta señal", "Understand this signal")}
                  <ArrowRight size={17} />
                </Link>
                <div className="preview-evidence">
                  <BookOpen size={15} />
                  {t(
                    "2 fuentes ilustrativas · límites visibles",
                    "2 illustrative sources · visible limits",
                  )}
                </div>
              </div>
              <div className="preview-axent">
                <AxentIdentity />
                <p>
                  {t(
                    "¿Qué cambia si miramos un poco más cerca?",
                    "What changes if we look a little closer?",
                  )}
                </p>
                <span>
                  {t(
                    "Investiga. Explica. Acompaña.",
                    "Investigates. Explains. Guides.",
                  )}
                </span>
              </div>
            </div>
          </Reveal>
        </section>
        <TrustProof />
        <ReferencePricing focuses={focuses} onChange={setFocuses} />
        <LandingNotebook />
        <NewsletterInvitation />
        <section className="closing-scene">
          <span className="eyebrow">AXIGNAL</span>
          <h2>
            {t("El mundo tiene más que decir.", "The world has more to say.")}
            <br />
            <em>{t("Aprendamos a mirarlo.", "Let’s learn to observe it.")}</em>
          </h2>
          <Link href="/panorama" className="button primary">
            {t("Entrar en el Panorama", "Enter Panorama")}
            <ArrowRight size={18} />
          </Link>
          <Observer className="closing-observer" pose="walking" />
        </section>
      </main>
      <MiniFooter />
      <ChapterNavigation />
      <div className="landing-legal">
        <span>© 2026 AXIGNAL</span>
        <button className="text-link" onClick={() => setAbout(true)}>
          {t("Sobre esta experiencia", "About this experience")}
        </button>
      </div>
      {about && (
        <Dialog
          title={t("Una experiencia para explorar", "An experience to explore")}
          onClose={() => setAbout(false)}
        >
          <p>
            {t(
              "Esta versión local presenta el nuevo lenguaje de AXIGNAL con organizaciones, fuentes y operaciones ficticias. No conecta un modelo de IA ni realiza pagos. Las fuentes de marca son oficiales; la experiencia espera revisión visual humana.",
              "This local version presents AXIGNAL’s new language with fictional organizations, sources and operations. It does not connect an AI model or process payments. Brand assets are official; the experience awaits human visual review.",
            )}
          </p>
          <Link className="button secondary" href="/design">
            {t(
              "Ver el sistema y sus estados",
              "View the system and its states",
            )}
            <ArrowRight size={16} />
          </Link>
        </Dialog>
      )}
    </div>
  );
}
