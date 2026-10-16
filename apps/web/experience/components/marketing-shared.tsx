"use client";
import Link from "next/link";
import { INDUSTRY_SRC_SET, INDUSTRY_SIZES, PUBLIC_BODY_FONT, PUBLIC_DISPLAY_FONT } from "@/lib/marketing-media";
import { useState, type ReactNode } from "react";
import {
  ArrowRight,
  ArrowUpRight,
  Globe2,
  MessageCircle,
  Package,
  MapPinned,
  Network,
  Search,
  Activity,
  ChartColumn,
  Building2,
  Compass,
  Plus,
} from "lucide-react";
import type { FamilyId } from "@/lib/projection";
import { locales, type Locale } from "@/lib/languages";
import { useLocale } from "@/lib/locale";
import { marketingPath, marketingCopy, words } from "@/lib/marketing-content";
import { publicCopy as p } from "@/lib/marketing-ui";
import { industries, type PublicIndustry } from "@/lib/marketing-industries";
import {
  EUR_REFERENCE,
  HUMAN_ADVISORY_EUR_MONTHLY_MINOR,
  formatFixedMoney,
  monthlyFixedPriceMinor,
} from "@/lib/commercial-prices";
import { funnelCta, track } from "@/lib/funnel-events";
import { PublicBrandVector } from "./public-brand-vector";
import { PublicShell } from "./public-shell";
import "./marketing.css";

const icons = {
  presence: Globe2,
  reputation: MessageCircle,
  value: Package,
  markets: MapPinned,
  relationships: Network,
  demand: Search,
  activity: Activity,
  economics: ChartColumn,
  organization: Building2,
  context: Compass,
};
export function FamilyIcon({
  family,
  size = 24,
}: {
  family: FamilyId;
  size?: number;
}) {
  const Icon = icons[family];
  return <Icon size={size} strokeWidth={1.6} aria-hidden="true" />;
}

export function MarketingShell({
  children,
  path = "/",
  landing = false,
  className = "",
  localeRoutes,
}: {
  children: ReactNode;
  path?: string;
  landing?: boolean;
  className?: string;
  localeRoutes?: { locale: Locale; href: string }[];
}) {
  return (
    <PublicShell
      landing={landing}
      catalog
      className={`marketing-site ${className}`.trim()}
      footer={<MarketingFooter />}
      localeRoutes={
        localeRoutes ??
        locales.map(({ id }) => ({
          locale: id,
          href: marketingPath(path, id),
        }))
      }
    >
      <link rel="preload" as="font" href={PUBLIC_DISPLAY_FONT} type="font/woff2" crossOrigin="anonymous" />
      <link rel="preload" as="font" href={PUBLIC_BODY_FONT} type="font/woff2" crossOrigin="anonymous" />
      {children}
    </PublicShell>
  );
}

export function MarketingFooter() {
  const { locale } = useLocale();
  return (
    <footer className="marketing-footer">
      <div className="marketing-footer-top">
        <Link prefetch={false} href={marketingPath("/", locale)} aria-label="AXIGNAL">
          <PublicBrandVector />
        </Link>
        <p>{marketingCopy.heroLead[locale]}</p>
      </div>
      <div className="marketing-footer-links">
        <nav aria-label={marketingCopy.observe[locale]}>
          <Link prefetch={false} href={marketingPath("/data", locale)}>
            {marketingCopy.observe[locale]}
          </Link>
          <Link prefetch={false} href={marketingPath("/pricing", locale)}>
            {marketingCopy.price[locale]}
          </Link>
          <Link prefetch={false} href="/demo">{p.example[locale]}</Link>
          <Link prefetch={false} href={`/${locale}/knowledge`}>Knowledge</Link>
          <Link prefetch={false} href={`${marketingPath("/", locale)}#weekly-brief`}>
            Newsletter
          </Link>
        </nav>
        <nav aria-label={marketingCopy.sectors[locale]}>
          {industries.map((i) => (
            <Link prefetch={false}
              key={i.slug}
              href={marketingPath(`/industries/${i.slug}`, locale)}
            >
              {i.title[locale]}
            </Link>
          ))}
        </nav>
        <nav aria-label={p.contact[locale]}>
          <Link prefetch={false} href="/contact">{p.contact[locale]}</Link>
          <Link prefetch={false} href="/policies">{p.trust[locale]}</Link>
          <Link prefetch={false} href="/gdpr">{p.rights[locale]}</Link>
          <a
            className="marketing-social-link"
            href="https://www.linkedin.com/company/axignal/"
            rel="noopener noreferrer"
            target="_blank"
          >
            <img className="marketing-linkedin-logo" src="/brand/linkedin-lucide.svg" width={18} height={18} alt="" loading="lazy" decoding="async" />
            LinkedIn
            <ArrowUpRight size={14} aria-hidden="true" />
          </a>
        </nav>
      </div>
      <div className="marketing-footer-bottom">
        <span>© {new Date().getFullYear()} AXIGNAL</span>
        <span>
          {
            words(
              "Observar. Entender. Decidir.",
              "Observe. Understand. Decide.",
              "Observer. Comprendre. Décider.",
              "Beobachten. Verstehen. Entscheiden.",
              "Osservare. Comprendere. Decidere.",
              "Observar. Compreender. Decidir.",
            )[locale]
          }
        </span>
      </div>
    </footer>
  );
}

export function IndustryList({
  items = industries,
}: {
  items?: readonly PublicIndustry[];
}) {
  const { locale } = useLocale();
  return (
    <div className="marketing-industry-list">
      {items.map((i) => (
        <details key={i.slug}>
          <summary>
            <span>{i.title[locale]}</span>
            <Plus size={23} strokeWidth={1.5} aria-hidden="true" />
          </summary>
          <div className="marketing-industry-reveal">
            <p>{i.intro[locale]}</p>
            <ul>
              {i.questions.map((q) => (
                <li key={q.en}>{q[locale]}</li>
              ))}
            </ul>
            <Link prefetch={false}
              className="marketing-text-link"
              href={marketingPath(`/industries/${i.slug}`, locale)}
            >
              {p.sectorLink[locale]}
              <ArrowRight size={18} aria-hidden="true" />
            </Link>
          </div>
        </details>
      ))}
    </div>
  );
}

export function IndustryArt() {
  const { locale } = useLocale();
  return (
    <figure className="marketing-industry-art">
      <img
        src="/marketing/industries.webp"
        srcSet={INDUSTRY_SRC_SET}
        sizes={INDUSTRY_SIZES}
        decoding="async"
        width={2007}
        height={784}
        alt=""
        loading="lazy"
      />
      <figcaption>{p.artNote[locale]}</figcaption>
    </figure>
  );
}

export function MarketingClosing() {
  const { locale } = useLocale();
  return (
    <section className="marketing-closing">
      <h2>{p.closingTitle[locale]}</h2>
      <div>
        <Link prefetch={false}
          className="marketing-button"
          href="/contact"
          onClick={() =>
            track({
              kind: "CTA_ACTIVATED",
              surface: "landing",
              cta: funnelCta.closingStart,
            })
          }
        >
          {p.request[locale]}
          <ArrowRight size={18} aria-hidden="true" />
        </Link>
        <Link prefetch={false}
          className="marketing-text-link"
          href="/demo"
          onClick={() =>
            track({
              kind: "CTA_ACTIVATED",
              surface: "landing",
              cta: funnelCta.closingExample,
            })
          }
        >
          {p.example[locale]}
          <ArrowRight size={18} aria-hidden="true" />
        </Link>
      </div>
      <p>{p.access[locale]}</p>
    </section>
  );
}

export function MarketingPricing({
  heading = "h2",
}: {
  heading?: "h1" | "h2";
}) {
  const { locale } = useLocale();
  const [count, setCount] = useState(1);
  const Heading = heading;
  const Subheading = heading === "h1" ? "h2" : "h3";
  const money = (n: number) => formatFixedMoney(locale, EUR_REFERENCE, n);
  return (
    <section className="marketing-pricing marketing-section" id="pricing">
      <div className="marketing-pricing-intro">
        <Heading>{p.pricingTitle[locale]}</Heading>
        <p>{p.pricingLead[locale]}</p>
        <dl className="marketing-price-basis">
          <div>
            <dt>{p.first[locale]}</dt>
            <dd>
              {money(EUR_REFERENCE.baseMinor)} <span>/ {p.month[locale]}</span>
            </dd>
          </div>
          <div>
            <dt>{p.extra[locale]}</dt>
            <dd>
              {money(EUR_REFERENCE.additionalMinor)}{" "}
              <span>/ {p.month[locale]}</span>
            </dd>
          </div>
        </dl>
        <p className="marketing-small">{p.taxes[locale]}</p>
      </div>
      <div className="marketing-price-calculator">
        <label htmlFor="marketing-count">
          {p.count[locale]}
          <output htmlFor="marketing-count">
            {new Intl.NumberFormat(locale).format(count)}
          </output>
        </label>
        <input
          id="marketing-count"
          type="range"
          min="1"
          max="100"
          step="1"
          value={count}
          onChange={(e) => setCount(Number(e.target.value))}
        />
        <div
          className="marketing-price-shortcuts"
          role="group"
          aria-label={p.count[locale]}
        >
          {[1, 5, 25, 100].map((n) => (
            <button
              type="button"
              key={n}
              aria-pressed={count === n}
              onClick={() => setCount(n)}
            >
              {n}
            </button>
          ))}
        </div>
        <div
          className="marketing-price-total"
          aria-live="polite"
          aria-atomic="true"
        >
          <strong>{money(monthlyFixedPriceMinor(EUR_REFERENCE, count))}</strong>
          <span>{p.month[locale]}</span>
        </div>
        <Subheading>{p.accessTitle[locale]}</Subheading>
        <p>{p.access[locale]}</p>
        <Link prefetch={false}
          href="/contact"
          className="marketing-button"
          onClick={() =>
            track({
              kind: "CTA_ACTIVATED",
              surface: "landing",
              cta: funnelCta.pricingStart,
            })
          }
        >
          {p.request[locale]}
          <ArrowRight size={18} aria-hidden="true" />
        </Link>
      </div>
      <aside className="marketing-advisory" id="human-advisory">
        <div>
          <Subheading>
            {
              words(
                "AXIGNAL con asesoría humana",
                "AXIGNAL with human advisory",
                "AXIGNAL avec conseil humain",
                "AXIGNAL mit persönlicher Beratung",
                "AXIGNAL con consulenza umana",
                "AXIGNAL com aconselhamento humano",
              )[locale]
            }
          </Subheading>
          <p>
            {
              words(
                "Un servicio humano, aparte: una organización dentro del alcance acordado, cuatro actualizaciones semanales y una revisión estratégica al mes.",
                "A separate human service: one organization within the agreed scope, four weekly updates and one strategic review a month.",
                "Un service humain distinct : une organisation dans le périmètre convenu, quatre mises à jour hebdomadaires et une revue stratégique par mois.",
                "Ein separater persönlicher Service: eine Organisation im vereinbarten Umfang, vier wöchentliche Aktualisierungen und eine strategische Prüfung pro Monat.",
                "Un servizio umano separato: un’organizzazione nell’ambito concordato, quattro aggiornamenti settimanali e una revisione strategica al mese.",
                "Um serviço humano separado: uma organização no âmbito acordado, quatro atualizações semanais e uma revisão estratégica por mês.",
              )[locale]
            }
          </p>
        </div>
        <div>
          <div className="marketing-advisory-price">
            <strong>{money(HUMAN_ADVISORY_EUR_MONTHLY_MINOR)}</strong>
            <span>{p.month[locale]}</span>
          </div>
          <small>
            {
              words(
                "Más impuestos aplicables · precio de lanzamiento",
                "Plus applicable tax · launch price",
                "Taxes applicables en sus · prix de lancement",
                "Zuzüglich geltender Steuern · Einführungspreis",
                "Più imposte applicabili · prezzo di lancio",
                "Mais impostos aplicáveis · preço de lançamento",
              )[locale]
            }
          </small>
          <Link prefetch={false}
            href="/contact"
            className="marketing-button marketing-advisory-button"
          >
            {
              words(
                "Hablar del alcance",
                "Discuss the scope",
                "Discuter du périmètre",
                "Umfang besprechen",
                "Parliamo dell’ambito",
                "Conversar sobre o âmbito",
              )[locale]
            }
            <ArrowUpRight size={18} aria-hidden="true" />
          </Link>
        </div>
      </aside>
    </section>
  );
}
