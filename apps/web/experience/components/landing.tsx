"use client";
import Link from "next/link";
import { useEffect } from "react";
import { ArrowRight, ArrowDown } from "lucide-react";
import { FAMILY_ORDER } from "@/lib/observation-families";
import { useLocale } from "@/lib/locale";
import {
  familyNames,
  familyQuestions,
  marketingCopy as m,
  marketingPath,
} from "@/lib/marketing-content";
import { funnelCta, landingChapters, track } from "@/lib/funnel-events";
import { MarketingShell, FamilyIcon } from "./marketing-shared";
import { MarketingHomeBody } from "./marketing-home-body";
import { HERO_SRC_SET, HERO_SIZES } from "@/lib/marketing-media";
import "./marketing.css";

export const EXAMPLE_HREF = "/demo";
export function Landing() {
  const { locale } = useLocale();
  useEffect(() => {
    track({ kind: "LANDING_VIEWED", surface: "landing" });
  }, []);
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (!entry.isIntersecting) continue;
          const chapter =
            landingChapters[entry.target.id as keyof typeof landingChapters];
          if (chapter)
            track({ kind: "CHAPTER_VIEWED", surface: "landing", chapter });
          observer.unobserve(entry.target);
        }
      },
      { threshold: 0.15 },
    );
    for (const id of Object.keys(landingChapters)) {
      const node = document.getElementById(id);
      if (node) observer.observe(node);
    }
    return () => observer.disconnect();
  }, []);
  const annotations = [
    { key: "offer", title: m.offer, body: m.offerNote, family: "value" },
    {
      key: "audience",
      title: m.audience,
      body: m.audienceNote,
      family: "markets",
    },
    {
      key: "understood",
      title: m.understood,
      body: m.understoodNote,
      family: "presence",
    },
  ] as const;
  return (
    <MarketingShell landing>
      <section className="marketing-hero" aria-labelledby="marketing-heading">
        <img
          className="marketing-hero-art"
          src="/marketing/hero-art.webp"
          srcSet={HERO_SRC_SET}
          sizes={HERO_SIZES}
          loading="eager"
          decoding="async"
          width={1931}
          height={814}
          alt=""
          fetchPriority="high"
        />
        <div className="marketing-hero-copy">
          <p className="marketing-kicker">{m.observation[locale]}</p>
          <h1 id="marketing-heading">
            <span>{m.heroFirst[locale]}</span>
            <span>{m.heroSecond[locale]}</span>
            <span>{m.heroThird[locale]}</span>
          </h1>
          <p className="marketing-hero-lead">{m.heroLead[locale]}</p>
          <div className="marketing-hero-actions">
            <Link prefetch={false}
              className="marketing-button"
              href={EXAMPLE_HREF}
              onClick={() =>
                track({
                  kind: "CTA_ACTIVATED",
                  surface: "landing",
                  cta: funnelCta.heroExample,
                })
              }
            >
              {m.example[locale]}
              <ArrowRight size={18} aria-hidden="true" />
            </Link>
            <a
              className="marketing-button marketing-button-secondary"
              href="#how"
            >
              {m.how[locale]}
            </a>
          </div>
        </div>
        <div className="marketing-annotations">
          {annotations.map(({ key, title, body, family }) => (
            <Link prefetch={false}
              key={key}
              className={`marketing-annotation marketing-annotation-${key}`}
              href={`${marketingPath("/data", locale)}#${family}`}
            >
              <strong>{title[locale]}</strong>
              <span>{body[locale]}</span>
            </Link>
          ))}
        </div>
        <svg
          className="marketing-annotation-connectors"
          viewBox="0 0 1505 635"
          preserveAspectRatio="none"
          aria-hidden="true"
          focusable="false"
        >
          <path d="M577 135 C553 169 559 205 591 246 M583 243 L591 246 L589 237" />
          <path d="M742 205 C720 233 719 263 734 295 M726 289 L734 295 L735 285" />
          <path d="M1267 153 C1238 179 1248 211 1269 248 C1280 271 1286 288 1283 302 M1277 294 L1283 302 L1289 293" />
        </svg>
        <div className="marketing-folio-labels" aria-hidden="true">
          {annotations.map(({ key, title }) => (
            <span key={key} className={`marketing-folio-${key}`}>
              {title[locale]}
            </span>
          ))}
        </div>
        <a
          className="marketing-continue"
          href="#families"
          aria-label={m.exploreFamilies[locale]}
        >
          <ArrowDown size={20} aria-hidden="true" />
        </a>
      </section>
      <section
        className="marketing-families-opening"
        id="families"
        aria-labelledby="families-heading"
      >
        <div className="marketing-family-heading">
          <p className="marketing-kicker">{m.wider[locale]}</p>
          <h2 id="families-heading">
            {m.familyFirst[locale]}
            <br />
            {m.familySecond[locale]}
          </h2>
        </div>
        <p className="marketing-family-intro">{m.familyIntro[locale]}</p>
        <nav
          className="marketing-family-strip"
          aria-label={m.exploreFamilies[locale]}
        >
          {FAMILY_ORDER.map((family) => (
            <Link prefetch={false}
              key={family}
              href={`${marketingPath("/data", locale)}#${family}`}
            >
              <span className="marketing-family-symbol">
                <FamilyIcon family={family} />
              </span>
              <strong>{familyNames[family][locale]}</strong>
              <span>{familyQuestions[family][locale]}</span>
            </Link>
          ))}
        </nav>
      </section>
      <MarketingHomeBody />
    </MarketingShell>
  );
}
