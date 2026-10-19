"use client";
import { useRouter } from "next/navigation";
import {
  Component,
  lazy,
  Suspense,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import {
  ArrowRight,
  ArrowUp,
  RotateCcw,
  ArrowUpRight,
  BookOpen,
  Check,
  ChevronDown,
  Clock3,
  Menu,
  Search,
  ShieldCheck,
} from "lucide-react";
import { useLocale } from "@/lib/locale";
import { locales, isLocale } from "@/lib/languages";
import { words, marketingPath } from "@/lib/marketing-content";
import type { LandingLabContent } from "@/lib/landing-lab-content";
import {
  exampleInsights,
  EXAMPLE_MOMENTS,
  type ExampleMoment,
} from "@/lib/landing-observatory";
import { labInsight } from "@/lib/landing-lab-model";
import { evidence } from "@/lib/projection";
import { dateLabel, demoOrganizationName } from "@/lib/projection";
import { natureLabel } from "@/lib/nature-label";
import {
  EUR_REFERENCE,
  HUMAN_ADVISORY_EUR_MONTHLY_MINOR,
  formatFixedMoney,
  monthlyFixedPriceMinor,
} from "@/lib/commercial-prices";
import { exampleDepth, funnelCta, track } from "@/lib/funnel-events";
import { NatureMark } from "./nature-mark";
import { InsightSources } from "./insight-sources";
import { SyntheticEvidenceProvider } from "./evidence-link-context";
import { Dialog } from "./dialog";
import labFonts from "@/lib/landing-lab-fonts.json";

// Separate async chunk: essential presentation and controls do not import GSAP.
const NarrativeMotion = lazy(() => import("./landing-lab-motion"));
const FooterBrief = lazy(() =>
  import("./weekly-brief-channel").then((module) => ({
    default: module.WeeklyBriefChannel,
  })),
);
class MotionBoundary extends Component<
  { children: ReactNode },
  { failed: boolean }
> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  render() {
    return this.state.failed ? null : this.props.children;
  }
}
const EXAMPLE_HREF = "/demo";
type Scenario = LandingLabContent["labQuestions"][number]["id"];
const money = (locale: string, amount: number) =>
  formatFixedMoney(locale, EUR_REFERENCE, amount);

export function LandingLab({ content }: { content: LandingLabContent }) {
  const {
    c,
    x,
    p,
    newsletterCopy,
    labQuestions,
    labPersonas,
    labFaq,
    marketingFaq,
    trustItems,
    methodSteps,
    industries,
  } = content;
  const { locale, t, copy, reducedMotion, setReducedMotion } = useLocale();
  const router = useRouter();
  const root = useRef<HTMLDivElement>(null);
  const motionRequested = useRef(false);
  const [menu, setMenu] = useState(false);
  const [scenario, setScenario] = useState<Scenario>("renovation");
  const [moment, setMoment] = useState<ExampleMoment>("2026-10-03");
  const [persona, setPersona] = useState(0);
  const [count, setCount] = useState(1);
  const [proofOpen, setProofOpen] = useState(false);
  const [reasonOpen, setReasonOpen] = useState(false);
  const [motion, setMotion] = useState(false);
  const [systemReduced, setSystemReduced] = useState(false);
  const [narrativeRun, setNarrativeRun] = useState(0);
  const [newsletterOpen, setNewsletterOpen] = useState(false);
  const [activeChapter, setActiveChapter] = useState("");
  const [showBackTop, setShowBackTop] = useState(false);
  const selected = labInsight(moment, scenario, copy);
  const heroFinding = exampleInsights("2026-10-03", copy).find(
    (item) => item.id === "renovation",
  )!;
  const label = (key: keyof Omit<typeof c, "benefits">) => c[key][locale];
  const nav = [
    ["#discover", label("discover")],
    ["#audience", label("audience")],
    ["#how", label("how")],
    [
      "#pricing",
      words("Precios", "Pricing", "Tarifs", "Preise", "Prezzi", "Preços")[
        locale
      ],
    ],
  ];
  useEffect(() => {
    track({ kind: "LANDING_VIEWED", surface: "landing" });
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries)
          if (entry.isIntersecting) {
            const chapter = Number(
              (entry.target as HTMLElement).dataset.chapter,
            );
            if (chapter)
              track({ kind: "CHAPTER_VIEWED", surface: "landing", chapter });
            observer.unobserve(entry.target);
          }
      },
      { threshold: 0.18 },
    );
    root.current
      ?.querySelectorAll("[data-chapter]")
      .forEach((node) => observer.observe(node));
    return () => observer.disconnect();
  }, []);
  useEffect(() => {
    const surface = root.current;
    if (!surface) return;
    const visibleChapters = new Set<string>();
    let sectionObserver: IntersectionObserver | undefined;
    const watchChapters = () => {
      sectionObserver?.disconnect();
      visibleChapters.clear();
      const first = surface.querySelector("#discover");
      const padding =
        parseFloat(
          getComputedStyle(document.documentElement).scrollPaddingTop,
        ) || 0;
      const margin = first
        ? parseFloat(getComputedStyle(first).scrollMarginTop) || 0
        : 0;
      // A pixel band follows the native anchor position. Percentage root margins
      // depend on root width and can collapse on wide, short viewports.
      const line = Math.min(
        window.innerHeight - 2,
        Math.round(padding + margin + 2),
      );
      sectionObserver = new IntersectionObserver(
        (entries) => {
          for (const entry of entries) {
            if (entry.isIntersecting) visibleChapters.add(entry.target.id);
            else visibleChapters.delete(entry.target.id);
          }
          const current = [...visibleChapters]
            .map((id) => surface.querySelector<HTMLElement>("#" + id))
            .filter((node): node is HTMLElement => node !== null)
            .sort(
              (a, b) =>
                b.getBoundingClientRect().top - a.getBoundingClientRect().top,
            )[0];
          setActiveChapter(current ? "#" + current.id : "");
        },
        {
          rootMargin: `-${line}px 0px -${Math.max(0, window.innerHeight - line - 2)}px 0px`,
          threshold: 0,
        },
      );
      surface
        .querySelectorAll("#discover, #audience, #how, #pricing")
        .forEach((node) => sectionObserver?.observe(node));
    };
    watchChapters();
    window.addEventListener("resize", watchChapters, { passive: true });
    const hero = surface.querySelector(".lab-hero-copy");
    const topObserver = new IntersectionObserver((entries) => {
      setShowBackTop(!entries[0].isIntersecting);
      if (entries[0].isIntersecting) setActiveChapter("");
    });
    if (hero) topObserver.observe(hero);
    return () => {
      sectionObserver?.disconnect();
      topObserver.disconnect();
      window.removeEventListener("resize", watchChapters);
    };
  }, []);
  useEffect(() => {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    let idle: number | undefined;
    let timer: ReturnType<typeof setTimeout> | undefined;
    let frame: number | undefined;
    let generation = 0;
    const cancel = () => {
      ++generation;
      if (idle !== undefined) window.cancelIdleCallback(idle);
      if (timer !== undefined) clearTimeout(timer);
      if (frame !== undefined) cancelAnimationFrame(frame);
    };
    const update = () => {
      cancel();
      setSystemReduced(media.matches);
      if (media.matches || reducedMotion) {
        setMotion(false);
        return;
      }
      if (!motionRequested.current || document.readyState !== "complete")
        return;
      const current = generation;
      // Let essential fonts paint before even downloading the optional engine.
      void document.fonts.ready.then(() => {
        if (current !== generation) return;
        frame = requestAnimationFrame(() => {
          frame = requestAnimationFrame(() => {
            if (current !== generation) return;
            if ("requestIdleCallback" in window)
              idle = window.requestIdleCallback(() => setMotion(true), {
                timeout: 2200,
              });
            else timer = setTimeout(() => setMotion(true), 0);
          });
        });
      });
    };
    const explore = () => {
      motionRequested.current = true;
      update();
      window.removeEventListener("scroll", explore);
      window.removeEventListener("pointerdown", explore);
      window.removeEventListener("keydown", explore);
    };
    const sceneObserver = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          motionRequested.current = true;
          update();
          sceneObserver.disconnect();
        }
      },
      { threshold: 0.12 },
    );
    const scene = root.current?.querySelector(".lab-world");
    if (scene) sceneObserver.observe(scene);
    update();
    // Prepare after first paint while the actual scene is still visible.
    window.addEventListener("scroll", explore, { passive: true });
    window.addEventListener("pointerdown", explore, { once: true });
    window.addEventListener("keydown", explore, { once: true });
    window.addEventListener("load", update, { once: true });
    media.addEventListener("change", update);
    return () => {
      cancel();
      sceneObserver.disconnect();
      window.removeEventListener("scroll", explore);
      window.removeEventListener("pointerdown", explore);
      window.removeEventListener("keydown", explore);
      window.removeEventListener("load", update);
      media.removeEventListener("change", update);
    };
  }, [reducedMotion, narrativeRun]);
  const depth = (chapter: number) =>
    track({ kind: "CHAPTER_VIEWED", surface: "example", chapter });
  const choose = (value: Scenario) => {
    setScenario(value);
    setProofOpen(false);
    setReasonOpen(false);
    depth(exampleDepth.signal);
  };
  const useHero = () => {
    choose("renovation");
    setMoment("2026-10-03");
  };
  const localeSelector = (
    <label className="lab-locale">
      <span className="sr-only">{label("language")}</span>
      <select
        aria-label={label("language")}
        value={locale}
        onChange={(event) => {
          const value = event.target.value;
          if (isLocale(value))
            router.push(`/${value}/landing-lab` + window.location.hash);
        }}
      >
        {locales.map((item) => (
          <option key={item.id} value={item.id} lang={item.id}>
            {item.name}
          </option>
        ))}
      </select>
    </label>
  );
  const stepImages = ["focus", "explain", "memory"];
  return (
    <div className="landing-lab" ref={root} id="lab-top">
      {labFonts.fonts.slice(0, 2).map((font) => (
        <link
          key={font.url}
          rel="preload"
          as="font"
          href={font.url}
          type="font/woff2"
          crossOrigin="anonymous"
        />
      ))}
      <header className="lab-header">
        <a
          href={marketingPath("/", locale)}
          className="lab-brand"
          aria-label="AXIGNAL"
        >
          <img
            className="public-brand-vector"
            src="/brand/logo-light.svg"
            width={147}
            height={43}
            alt=""
            fetchPriority="low"
            decoding="async"
          />
        </a>
        <nav aria-label={label("menu")}>
          {nav.map(([href, name], index) => (
            <a
              key={href}
              href={href}
              aria-current={activeChapter === href ? "location" : undefined}
              onClick={() => setActiveChapter(href)}
            >
              <span className="lab-nav-number" aria-hidden="true">
                0{index + 1}
              </span>
              {name}
            </a>
          ))}
        </nav>
        <div className="lab-header-actions">
          {localeSelector}
          <a className="lab-signin" href="/login">
            {label("signIn")}
          </a>
          <a
            className="lab-button lab-small"
            href="/signup"
            onClick={() =>
              track({
                kind: "CTA_ACTIVATED",
                surface: "landing",
                cta: funnelCta.headerStart,
              })
            }
          >
            {label("start")}
            <ArrowUpRight size={16} aria-hidden="true" />
          </a>
          <button
            type="button"
            className="lab-menu-button"
            aria-label={label("menu")}
            aria-expanded={menu}
            onClick={() => setMenu(true)}
          >
            <Menu size={22} aria-hidden="true" />
          </button>
        </div>
      </header>
      <main id="main" tabIndex={-1}>
        <section className="lab-hero" aria-labelledby="lab-heading">
          <div className="lab-hero-copy">
            <p className="lab-eyebrow">
              <span className="lab-dot" aria-hidden="true" />
              {label("kicker")}
            </p>
            <h1 id="lab-heading" tabIndex={-1}>
              {label("heroFirst")} <span>{label("heroSecond")}</span>
            </h1>
            <p className="lab-lead">{label("heroLead")}</p>
            <div className="lab-actions">
              <a
                className="lab-button"
                href="#discover"
                onClick={() => {
                  useHero();
                  track({
                    kind: "CTA_ACTIVATED",
                    surface: "landing",
                    cta: funnelCta.heroExample,
                  });
                }}
              >
                {label("example")}
                <ArrowRight size={18} aria-hidden="true" />
              </a>
              <a
                className="lab-text-link"
                href="/signup"
                onClick={() =>
                  track({
                    kind: "CTA_ACTIVATED",
                    surface: "landing",
                    cta: funnelCta.heroStart,
                  })
                }
              >
                {label("start")}
                <ArrowUpRight size={16} aria-hidden="true" />
              </a>
            </div>
            <p className="lab-micro">
              <Check size={14} aria-hidden="true" />
              {label("noAccount")}
              <span>{label("invitation")}</span>
            </p>
          </div>
          <div className="lab-world" aria-label={label("openCase")}>
            <div className="lab-case-caption">
              <span>{label("openCase")}</span>
              <small>{label("fiction")}</small>
            </div>
            <svg
              className="lab-world-wires lab-world-wires-narrow"
              viewBox="0 0 620 530"
              preserveAspectRatio="none"
              aria-hidden="true"
            >
              <path
                className="lab-world-line"
                d="M145 140 C145 235 306 160 312 260"
              />
              <path
                className="lab-world-line"
                d="M485 130 C485 220 330 170 312 260"
              />
              <path
                className="lab-world-line"
                d="M312 285 C312 320 260 310 260 365"
                strokeDasharray="4 5"
              />
            </svg>
            <svg
              className="lab-world-wires lab-world-wires-wide"
              viewBox="0 0 1200 390"
              preserveAspectRatio="none"
              aria-hidden="true"
            >
              <path
                className="lab-world-line"
                d="M250 175 C325 175 350 285 565 285"
              />
              <path
                className="lab-world-line"
                d="M510 220 C510 260 525 285 565 285"
              />
              <path
                className="lab-world-line"
                d="M630 285 C740 285 760 160 835 160"
                strokeDasharray="4 5"
              />
            </svg>
            <div className="lab-clue lab-clue-one" data-world-node>
              <span className="lab-label">{label("declared")}</span>
              <BookOpen size={17} strokeWidth={1.5} aria-hidden="true" />
              <p>
                {copy(
                  evidence.find((item) => item.id === "capabilities")!.body,
                ).split(". ")[0] + "."}
              </p>
              <time dateTime={heroFinding.sources[0]?.observedAt ?? ""}>
                {dateLabel(heroFinding.sources[0]?.observedAt ?? "", locale)}
              </time>
            </div>
            <div className="lab-clue lab-clue-two" data-world-node>
              <span className="lab-label">{label("context")}</span>
              <Search size={17} strokeWidth={1.5} aria-hidden="true" />
              <p>{heroFinding.sources[1]?.quote}</p>
              <time dateTime={heroFinding.sources[1]?.observedAt ?? ""}>
                {dateLabel(heroFinding.sources[1]?.observedAt ?? "", locale)}
              </time>
            </div>
            <div className="lab-connection" data-world-node>
              <img src="/brand/isotope.svg" width={34} height={34} alt="" />
              <span>{label("connection")}</span>
            </div>
            <a
              className="lab-hero-finding"
              data-world-node
              href="#discover"
              onClick={() => {
                useHero();
                setReasonOpen(true);
              }}
            >
              <NatureMark nature="POTENTIAL" label={label("potential")} />
              <strong>{heroFinding.headline}</strong>
              <span>
                {label("lookCloser")}
                <ArrowUpRight size={17} aria-hidden="true" />
              </span>
            </a>
            <div className="lab-hero-observer">
              <img
                data-observer
                src="/marketing/focus.webp"
                width={640}
                height={413}
                alt=""
                loading="lazy"
                fetchPriority="low"
                decoding="async"
              />
              <span className="lab-hand">{label("heroNote")}</span>
            </div>
          </div>
          <div className="lab-world-controls">
            <button
              type="button"
              className="lab-replay"
              disabled={reducedMotion || systemReduced}
              onClick={() => {
                motionRequested.current = true;
                setNarrativeRun((value) => value + 1);
              }}
            >
              <RotateCcw size={15} aria-hidden="true" />
              {x.replay[locale]}
            </button>
          </div>
        </section>
        <nav className="lab-benefits" aria-label={label("discover")}>
          {c.benefits.map((item, index) => (
            <a href={["#how", "#audience", "#discover"][index]} key={item.en}>
              {
                [
                  <Search key="search" size={19} />,
                  <ArrowUpRight key="context" size={19} />,
                  <Clock3 key="time" size={19} />,
                ][index]
              }
              {item[locale]}
              <ArrowRight size={16} aria-hidden="true" />
            </a>
          ))}
        </nav>
        <section
          className="lab-discovery lab-section"
          id="discover"
          aria-labelledby="lab-discovery-title"
          data-chapter="3"
        >
          <div className="lab-section-heading">
            <p className="lab-eyebrow">{label("example")}</p>
            <h2 id="lab-discovery-title">{label("discoveryTitle")}</h2>
            <p>{label("discoveryLead")}</p>
          </div>
          <div className="lab-investigation">
            <div
              className="lab-questions"
              role="group"
              aria-label={label("question")}
            >
              <span className="lab-label">{label("question")}</span>
              {labQuestions.map((item) => (
                <button
                  type="button"
                  key={item.id}
                  aria-pressed={scenario === item.id}
                  aria-controls="lab-finding"
                  onClick={() => choose(item.id)}
                >
                  <span>{item.label[locale]}</span>
                  <ArrowUpRight size={16} aria-hidden="true" />
                </button>
              ))}
            </div>
            <div className="lab-reading">
              <div className="lab-reading-heading">
                <strong>{copy(demoOrganizationName)}</strong>
                <span>{label("fiction")}</span>
              </div>
              <div
                id="lab-finding"
                className="lab-finding"
                aria-live="polite"
                aria-atomic="true"
              >
                <div className="lab-finding-copy" key={scenario + moment}>
                  {selected ? (
                    <>
                      <div className="lab-finding-state">
                        <NatureMark
                          nature={selected.nature}
                          label={natureLabel(selected.nature, t)}
                        />
                        <time dateTime={selected.observedAt ?? undefined}>
                          {selected.observedAt &&
                            dateLabel(selected.observedAt, locale)}
                        </time>
                      </div>
                      <h3>{selected.headline}</h3>
                      <p>{selected.meaning[0]}</p>
                    </>
                  ) : (
                    <>
                      <span className="lab-label">{label("history")}</span>
                      <h3>{label("noFinding")}</h3>
                      <p>{label("noFindingBody")}</p>
                    </>
                  )}
                </div>
              </div>
              {selected && (
                <div className="lab-proof" key={selected.id + moment}>
                  <details
                    open={reasonOpen}
                    onToggle={(event) => {
                      setReasonOpen(event.currentTarget.open);
                      if (event.currentTarget.open)
                        depth(exampleDepth.evidence);
                    }}
                  >
                    <summary>
                      {label("reasoning")}
                      <ChevronDown size={18} aria-hidden="true" />
                    </summary>
                    <div className="lab-reasoning">
                      <p>{selected.why}</p>
                      {selected.reasoning.map((text) => (
                        <p key={text}>{text}</p>
                      ))}
                    </div>
                  </details>
                  <details
                    open={proofOpen}
                    onToggle={(event) => {
                      const open = event.currentTarget.open;
                      setProofOpen(open);
                      if (open) depth(exampleDepth.evidence);
                    }}
                  >
                    <summary>
                      {label("sources")}
                      <span className="lab-source-count">
                        {selected.sources.length}
                      </span>
                      <ChevronDown size={18} aria-hidden="true" />
                    </summary>
                    <div className="lab-sources" data-proof>
                      {selected.sources.length ? (
                        <SyntheticEvidenceProvider>
                          <InsightSources
                            sources={selected.sources}
                            proof={selected.proof}
                          />
                        </SyntheticEvidenceProvider>
                      ) : (
                        <p>{label("noSources")}</p>
                      )}
                    </div>
                  </details>
                </div>
              )}
              <div className="lab-time">
                <div>
                  <Clock3 size={17} aria-hidden="true" />
                  <span>{label("time")}</span>
                  <small>
                    {moment === EXAMPLE_MOMENTS[2]
                      ? label("latest")
                      : label("history")}
                  </small>
                </div>
                <div
                  className="lab-moments"
                  role="group"
                  aria-label={label("time")}
                >
                  {EXAMPLE_MOMENTS.map((value) => (
                    <button
                      type="button"
                      aria-pressed={value === moment}
                      key={value}
                      onClick={() => {
                        setMoment(value);
                        setProofOpen(false);
                        depth(exampleDepth.history);
                      }}
                    >
                      <span aria-hidden="true" />
                      <time dateTime={value}>{dateLabel(value, locale)}</time>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
          <div className="lab-demo-bridge">
            <p>{label("demoBridge")}</p>
            <a
              href={EXAMPLE_HREF}
              className="lab-text-link"
              onClick={() =>
                track({
                  kind: "CTA_ACTIVATED",
                  surface: "landing",
                  cta: funnelCta.proofExample,
                })
              }
            >
              {label("fullExample")}
              <ArrowUpRight size={18} aria-hidden="true" />
            </a>
          </div>
        </section>
        <section
          className="lab-audience lab-section"
          id="audience"
          aria-labelledby="lab-audience-title"
          data-chapter="4"
        >
          <div className="lab-section-heading">
            <p className="lab-eyebrow">{label("audience")}</p>
            <h2 id="lab-audience-title">{label("audienceTitle")}</h2>
          </div>
          <div
            className="lab-persona-picker"
            role="group"
            aria-label={label("audience")}
          >
            {labPersonas.map((item, index) => (
              <button
                type="button"
                key={item.id}
                aria-pressed={persona === index}
                aria-controls={"lab-persona-" + index}
                onClick={() => setPersona(index)}
              >
                {item.title[locale]}
              </button>
            ))}
          </div>
          {labPersonas.map((item, index) => (
            <div
              className="lab-workflow"
              id={"lab-persona-" + index}
              key={item.id}
              hidden={persona !== index}
            >
              <div className="lab-before">
                <span className="lab-label">{label("before")}</span>
                <p>{item.before[locale]}</p>
              </div>
              <div className="lab-after">
                <span className="lab-label">{label("after")}</span>
                <p>{item.after[locale]}</p>
                <div className="lab-deliverable">
                  <span>{label("output")}</span>
                  <strong>{item.output[locale]}</strong>
                </div>
                <a
                  className="lab-text-link"
                  href="#discover"
                  onClick={() => {
                    choose(item.scenario);
                    setMoment("2026-10-03");
                  }}
                >
                  {label("example")}
                  <ArrowRight size={17} aria-hidden="true" />
                </a>
              </div>
            </div>
          ))}
        </section>
        <section
          className="lab-method lab-section"
          id="how"
          aria-labelledby="lab-how-title"
          data-chapter="2"
        >
          <div className="lab-section-heading">
            <p className="lab-eyebrow">{label("how")}</p>
            <h2 id="lab-how-title">{label("methodTitle")}</h2>
            <p>{label("methodLead")}</p>
          </div>
          <ol className="lab-method-loop">
            {methodSteps.map((item, index) => (
              <li key={item.image}>
                <div className="lab-method-art">
                  <img
                    data-observer
                    src={"/marketing/" + stepImages[index] + ".webp"}
                    width={640}
                    height={640}
                    alt=""
                    loading="lazy"
                    decoding="async"
                  />
                </div>
                <div>
                  <span className="lab-step">
                    {String(index + 1).padStart(2, "0")}
                  </span>
                  <h3>{item.title[locale]}</h3>
                  <p>{item.body[locale]}</p>
                </div>
              </li>
            ))}
          </ol>
          <p className="lab-method-limit">{label("timing")}</p>
        </section>
        <section
          className="lab-difference lab-section"
          aria-labelledby="lab-difference-title"
        >
          <div className="lab-section-heading">
            <h2 id="lab-difference-title">{label("differenceTitle")}</h2>
            <p>{label("differenceLead")}</p>
          </div>
          <div className="lab-memory-argument">
            {trustItems.map((item, index) => (
              <article key={item.title.en}>
                <span className="lab-argument-mark" aria-hidden="true">
                  {index === 0 ? (
                    <BookOpen size={21} />
                  ) : index === 1 ? (
                    <Search size={21} />
                  ) : (
                    <ShieldCheck size={21} />
                  )}
                </span>
                <h3>{item.title[locale]}</h3>
                <p>{item.body[locale]}</p>
              </article>
            ))}
          </div>
        </section>
        <section
          className="lab-trust lab-section"
          id="trust"
          aria-labelledby="lab-trust-title"
          data-chapter="5"
        >
          <figure className="lab-trust-note">
            <img
              data-trust-observer
              src="/marketing/explain.webp"
              width={640}
              height={640}
              loading="lazy"
              decoding="async"
              alt=""
            />
            <figcaption className="lab-hand">{x.trustNote[locale]}</figcaption>
          </figure>
          <div>
            <h2 id="lab-trust-title">{label("trustTitle")}</h2>
            <p>{label("trustLead")}</p>
            <p>{label("privacy")}</p>
            <div className="lab-actions">
              <a
                href="#discover"
                className="lab-text-link"
                onClick={() => {
                  useHero();
                  setProofOpen(true);
                }}
              >
                {label("sources")}
                <ArrowRight size={17} aria-hidden="true" />
              </a>
              <a className="lab-text-link" href="/policies">
                {p.trust[locale]}
                <ArrowUpRight size={17} aria-hidden="true" />
              </a>
            </div>
          </div>
        </section>
        <section
          className="lab-pricing lab-section"
          id="pricing"
          aria-labelledby="lab-price-title"
          data-chapter="6"
        >
          <div className="lab-section-heading">
            <p className="lab-eyebrow">{p.pricingTitle[locale]}</p>
            <h2 id="lab-price-title">{label("priceTitle")}</h2>
            <p>{label("included")}</p>
          </div>
          <div className="lab-price-options">
            <div className="lab-price-desk">
              <div className="lab-price-base">
                <span>{p.first[locale]}</span>
                <p>
                  <strong>{money(locale, EUR_REFERENCE.baseMinor)}</strong>
                  <span>/ {p.month[locale]}</span>
                </p>
                <div className="lab-price-add">
                  <span>{p.extra[locale]}</span>
                  <p>
                    <b>+{money(locale, EUR_REFERENCE.additionalMinor)}</b>
                    <span>/ {p.month[locale]}</span>
                  </p>
                </div>
                <p className="lab-micro">{p.taxes[locale]}</p>
              </div>
              <div className="lab-price-portfolio">
                <label htmlFor="lab-count">
                  {label("countLabel")}
                  <output htmlFor="lab-count">{count}</output>
                </label>
                <input
                  id="lab-count"
                  type="range"
                  min="1"
                  max="100"
                  step="1"
                  value={count}
                  onChange={(event) => setCount(Number(event.target.value))}
                />
                <div
                  className="lab-presets"
                  role="group"
                  aria-label={label("countLabel")}
                >
                  {[1, 5, 25, 100].map((value) => (
                    <button
                      type="button"
                      key={value}
                      aria-pressed={value === count}
                      onClick={() => setCount(value)}
                    >
                      {value}
                    </button>
                  ))}
                </div>
                <p
                  className="lab-price-total"
                  aria-live="polite"
                  aria-atomic="true"
                >
                  <strong>
                    {money(
                      locale,
                      monthlyFixedPriceMinor(EUR_REFERENCE, count),
                    )}
                  </strong>
                  <span>/ {p.month[locale]}</span>
                </p>
                <p>{p.access[locale]}</p>
                <a
                  className="lab-button"
                  href="/contact"
                  onClick={() =>
                    track({
                      kind: "CTA_ACTIVATED",
                      surface: "landing",
                      cta: funnelCta.pricingStart,
                    })
                  }
                >
                  {p.request[locale]}
                  <ArrowUpRight size={17} aria-hidden="true" />
                </a>
              </div>
            </div>
            <article
              className="lab-advisory"
              aria-labelledby="lab-advisory-title"
            >
              <p className="lab-eyebrow">{x.advisoryKicker[locale]}</p>
              <h3 id="lab-advisory-title">
                {
                  words(
                    "¿Buscas asesoría humana?",
                    "Looking for human advisory?",
                    "Vous cherchez un conseil humain ?",
                    "Suchen Sie persönliche Beratung?",
                    "Cerchi consulenza umana?",
                    "Procura aconselhamento humano?",
                  )[locale]
                }
              </h3>
              <div className="lab-advisory-price">
                <strong>
                  {money(locale, HUMAN_ADVISORY_EUR_MONTHLY_MINOR)}
                </strong>
                <span>/ {p.month[locale]}</span>
              </div>
              <p>
                {
                  words(
                    "Servicio separado: una organización en el alcance acordado, cuatro actualizaciones semanales y una revisión estratégica al mes. Precio de lanzamiento, más impuestos aplicables. El pago no influye en las conclusiones.",
                    "Separate service: one organization in the agreed scope, four weekly updates and one strategic review a month. Launch price, plus applicable tax. Payment does not influence conclusions.",
                    "Service distinct : une organisation dans le périmètre convenu, quatre mises à jour hebdomadaires et une revue stratégique par mois. Prix de lancement, taxes en sus. Le paiement n’influence pas les conclusions.",
                    "Separater Service: eine Organisation im vereinbarten Umfang, vier wöchentliche Updates und eine strategische Prüfung im Monat. Einführungspreis zuzüglich Steuern. Zahlung beeinflusst keine Schlussfolgerungen.",
                    "Servizio separato: un’organizzazione nell’ambito concordato, quattro aggiornamenti settimanali e una revisione strategica al mese. Prezzo di lancio, imposte escluse. Il pagamento non influenza le conclusioni.",
                    "Serviço separado: uma organização no âmbito acordado, quatro atualizações semanais e uma revisão estratégica mensal. Preço de lançamento, mais impostos. O pagamento não influencia conclusões.",
                  )[locale]
                }
              </p>
              <a className="lab-text-link" href="/contact">
                {p.contact[locale]}
                <ArrowUpRight size={17} aria-hidden="true" />
              </a>
            </article>
          </div>
        </section>
        <section
          className="lab-faq lab-section"
          aria-labelledby="lab-faq-title"
        >
          <h2 id="lab-faq-title">{label("faqTitle")}</h2>
          <div>
            {[...labFaq, ...marketingFaq].map((item) => (
              <details key={item.question.en}>
                <summary>
                  {item.question[locale]}
                  <ChevronDown size={18} aria-hidden="true" />
                </summary>
                <p>{item.answer[locale]}</p>
              </details>
            ))}
          </div>
        </section>
        <section className="lab-closing">
          <div>
            <p className="lab-eyebrow">{label("kicker")}</p>
            <h2>{label("closing")}</h2>
            <div className="lab-actions">
              <a
                href="/contact"
                className="lab-button"
                onClick={() =>
                  track({
                    kind: "CTA_ACTIVATED",
                    surface: "landing",
                    cta: funnelCta.closingStart,
                  })
                }
              >
                {p.request[locale]}
                <ArrowUpRight size={18} aria-hidden="true" />
              </a>
              <a href={EXAMPLE_HREF} className="lab-text-link">
                {label("example")}
                <ArrowRight size={17} aria-hidden="true" />
              </a>
            </div>
            <p className="lab-micro">{label("invitation")}</p>
          </div>
          <div className="lab-closing-art">
            <img
              src="/marketing/memory.webp"
              width={640}
              height={640}
              alt=""
              loading="lazy"
              decoding="async"
            />
            <span className="lab-hand">{label("closingNote")}</span>
          </div>
        </section>
      </main>
      <footer className="lab-footer">
        <div className="lab-footer-intro">
          <div className="lab-footer-brand-story">
            <a
              className="lab-brand"
              href={marketingPath("/", locale)}
              aria-label="AXIGNAL"
            >
              <img
                className="public-brand-vector"
                src="/brand/logo-light.svg"
                width={195}
                height={57}
                alt=""
                loading="lazy"
                decoding="async"
              />
            </a>
            <p>{label("heroLead")}</p>
            <span className="lab-hand">{label("methodTitle")}</span>
          </div>
          <section
            className="lab-footer-newsletter"
            aria-labelledby="lab-newsletter-title"
          >
            <p className="lab-eyebrow">Newsletter · AXIGNAL</p>
            <h2 id="lab-newsletter-title">{newsletterCopy.title[locale]}</h2>
            <p>{newsletterCopy.lead[locale]}</p>
            <details
              className="lab-newsletter-request"
              onToggle={(event) => setNewsletterOpen(event.currentTarget.open)}
            >
              <summary>
                {x.newsletterAction[locale]}
                <ArrowRight size={18} aria-hidden="true" />
              </summary>
              <p className="lab-newsletter-boundary">
                {newsletterCopy.boundary[locale]}
              </p>
              {newsletterOpen && (
                <Suspense fallback={<p>{newsletterCopy.checking[locale]}</p>}>
                  <FooterBrief variant="footer" />
                </Suspense>
              )}
              <a href={marketingPath("/", locale) + "#weekly-brief"}>
                {x.openChannel[locale]}
                <ArrowUpRight size={15} aria-hidden="true" />
              </a>
            </details>
          </section>
        </div>
        <div className="lab-footer-grid">
          <nav aria-label={label("discover")}>
            <h3>{x.footerProduct[locale]}</h3>
            <a href="#discover">{label("discover")}</a>
            <a href={EXAMPLE_HREF}>{label("example")}</a>
            <a href={marketingPath("/pricing", locale)}>
              {t("Precio", "Pricing")}
            </a>
            <a href={marketingPath("/data", locale)}>
              {
                words(
                  "Qué observa",
                  "What it observes",
                  "Ce qu’il observe",
                  "Was es beobachtet",
                  "Cosa osserva",
                  "O que observa",
                )[locale]
              }
            </a>
            <a href={"/" + locale + "/knowledge"}>Knowledge</a>
          </nav>
          <nav aria-label={label("audience")}>
            <h3>{label("audience")}</h3>
            {industries.map((item) => (
              <a
                href={marketingPath("/industries/" + item.slug, locale)}
                key={item.slug}
              >
                {item.title[locale]}
              </a>
            ))}
          </nav>
          <nav aria-label={p.trust[locale]}>
            <h3>{x.footerTrust[locale]}</h3>
            <a href="/contact">{p.contact[locale]}</a>
            <a href="/policies">{p.trust[locale]}</a>
            <a href="/policies/privacy">{t("Privacidad", "Privacy")}</a>
            <a href="/policies/terms">
              {
                words(
                  "Términos",
                  "Terms",
                  "Conditions",
                  "Bedingungen",
                  "Termini",
                  "Termos",
                )[locale]
              }
            </a>
            <a href="/gdpr">{p.rights[locale]}</a>
            <a
              href="https://www.linkedin.com/company/axignal/"
              target="_blank"
              rel="noopener noreferrer"
            >
              LinkedIn
              <ArrowUpRight size={14} aria-hidden="true" />
            </a>
          </nav>
        </div>
        <div className="lab-footer-bottom">
          <span>© {new Date().getFullYear()} AXIGNAL</span>
          <a className="lab-backtop-footer" href="#lab-heading">
            {x.backTop[locale]}
            <ArrowUp size={16} aria-hidden="true" />
          </a>
          <button
            type="button"
            className="lab-motion-control"
            aria-pressed={reducedMotion}
            onClick={() => setReducedMotion(!reducedMotion)}
          >
            {
              words(
                "Reducir movimiento",
                "Reduce motion",
                "Réduire le mouvement",
                "Bewegung reduzieren",
                "Riduci movimento",
                "Reduzir movimento",
              )[locale]
            }
          </button>
          {localeSelector}
        </div>
      </footer>
      {menu && (
        <Dialog
          title={label("menu")}
          onClose={() => setMenu(false)}
          className="lab-menu"
        >
          <nav>
            {nav.map(([href, name], index) => (
              <a key={href} href={href} onClick={() => setMenu(false)}>
                <span className="lab-menu-index" aria-hidden="true">
                  0{index + 1}
                </span>
                {name}
                <ArrowRight size={18} aria-hidden="true" />
              </a>
            ))}
            <a href={EXAMPLE_HREF}>{label("example")}</a>
            <a href="/login" className="lab-signin">
              {label("signIn")}
            </a>
            <a href="/signup">{label("start")}</a>
          </nav>
        </Dialog>
      )}
      {showBackTop && (
        <a
          className="lab-backtop"
          href="#lab-heading"
          aria-label={x.backTop[locale]}
        >
          <ArrowUp size={19} aria-hidden="true" />
          <span>{x.backTop[locale]}</span>
        </a>
      )}
      {motion && (
        <MotionBoundary>
          <Suspense fallback={null}>
            <NarrativeMotion
              root={root}
              revision={scenario + moment}
              proofOpen={proofOpen}
              replay={narrativeRun}
            />
          </Suspense>
        </MotionBoundary>
      )}
    </div>
  );
}
