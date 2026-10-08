"use client";
import Link from "next/link";
import { ArrowRight, ArrowUpRight, Check } from "lucide-react";
import { useLocale } from "@/lib/locale";
import { monthlyReferenceCents } from "@/lib/presentation";
import { funnelCta, track } from "@/lib/funnel-events";
import { Observer } from "./ui";

/**
 * Pricing answers four questions in one screen: what do I pay, what do I get,
 * what is one organization, what happens when I add more. Prices are the MASTER §27
 * hypothesis; checkout is not open, and the copy says so without "demo" language.
 */
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
    <section className="chapter reference-pricing" id="pricing">
      <div className="pricing-perspective">
        <span className="eyebrow">{t("Precio", "Pricing")}</span>
        <h2>
          {t("Pagas por organización observada.", "You pay per organization observed.")}
          <br />
          <em>{t("No por cada hallazgo.", "Not per finding.")}</em>
        </h2>
        <p>
          {t(
            "Una organización es una empresa que AXIGNAL observa para ti: la tuya, un cliente o un competidor. Todo lo que aparezca a su alrededor —cambios, oportunidades, riesgos— va incluido.",
            "An organization is a company AXIGNAL observes for you: yours, a customer or a competitor. Everything that appears around it — changes, opportunities, risks — is included.",
          )}
        </p>
        <Observer scene="focus" />
      </div>
      <div className="pricing-paper">
        <span className="eyebrow">AXIGNAL</span>
        <div className="reference-price">
          <strong>{money(monthlyReferenceCents(focuses))}</strong>
          <span>/{t("mes", "month")}</span>
        </div>
        <p>
          {focuses}{" "}
          {focuses === 1
            ? t("organización observada", "organization observed")
            : t("organizaciones observadas", "organizations observed")}
        </p>
        <label htmlFor="pricing-focuses">
          {t("¿Cuántas organizaciones quieres observar?", "How many organizations do you want to observe?")}
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
          aria-label={t("Elegir número de organizaciones", "Choose number of organizations")}
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
          {t("al mes incluye la primera organización.", "a month includes the first organization.")}{" "}
          {money(495)}{" "}
          {t("al mes por cada organización adicional.", "a month for each additional organization.")}
        </p>
        <ul>
          {[
            t(
              "El panorama de cada organización, con su historia",
              "Each organization's panorama, with its history",
            ),
            t(
              "Fuente, fecha y vigencia de cada conclusión",
              "Source, date and currentness for every conclusion",
            ),
            t(
              "AXENT para preguntar sobre ese contexto",
              "AXENT to ask about that context",
            ),
            t(
              "Tu contexto también en Claude y otros asistentes compatibles con MCP",
              "Your context in Claude and other MCP-compatible assistants too",
            ),
          ].map((x) => (
            <li key={x}>
              <Check size={16} />
              {x}
            </li>
          ))}
        </ul>
        <Link
          href="/signup"
          className="button primary"
          onClick={() => track({ kind: "CTA_ACTIVATED", surface: "landing", cta: funnelCta.pricingStart })}
        >
          {t("Empieza con tu organización", "Start with your organization")}
          <ArrowRight size={17} />
        </Link>
        <small>
          {t(
            "Precios mensuales sin IVA. El pago en línea aún no está abierto: puedes crear tu cuenta y dejar preparadas tus organizaciones.",
            "Monthly prices excluding VAT. Online payment is not open yet: you can create your account and prepare your organizations.",
          )}
        </small>
      </div>
      <aside className="human-advisory">
        <div>
          <span className="eyebrow">
            {t("Un servicio humano, aparte", "A separate human service")}
          </span>
          <h3>
            {t("AXIGNAL con asesoría humana", "AXIGNAL with human advisory")}
          </h3>
          <p>
            {t(
              "Una persona interpreta la evidencia contigo: una organización dentro del alcance acordado, cuatro actualizaciones semanales y una revisión estratégica al mes.",
              "A person interprets the evidence with you: one organization within the agreed scope, four weekly updates and one strategic review a month.",
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
            {t("Hablar del alcance", "Discuss the scope")}
            <ArrowUpRight size={16} />
          </Link>
        </div>
      </aside>
    </section>
  );
}
