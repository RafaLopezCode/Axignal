"use client";

/**
 * Published prices, from the governed price book (MASTER §27, ADR-0093). It says plainly how access
 * works today; it never offers a purchase that is not open.
 */
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { useLocale } from "@/lib/locale";
import { EUR_REFERENCE, formatFixedMoney, monthlyFixedPriceMinor } from "@/lib/commercial-prices";
import { fill } from "@/lib/observatory";
import { PublicShell } from "./public-shell";

export function Pricing() {
  const { t, locale } = useLocale();
  const money = (minor: number) => formatFixedMoney(locale, EUR_REFERENCE, minor);
  const examples = [1, 3, 10];
  return <PublicShell className="pricing-page">
    <section className="pricing">
      <span className="eyebrow">{t("Precios", "Pricing")}</span>
      <h1>{t("Un precio por organización observada", "One price per observed organization")}</h1>
      <p className="pricing-lead">{t("Sin niveles ni funciones reservadas: cada organización que observas recibe la misma lectura, con sus fuentes, su memoria y lo que aún no se sabe.",
        "No tiers and no reserved features: every organization you observe gets the same reading, with its sources, its memory and what is not known yet.")}</p>
      <div className="pricing-cards">
        <article className="pricing-card">
          <h2>{t("Primera organización", "First organization")}</h2>
          <p className="pricing-amount"><strong>{money(EUR_REFERENCE.baseMinor)}</strong> <span>{t("al mes", "per month")}</span></p>
        </article>
        <article className="pricing-card">
          <h2>{t("Cada organización adicional", "Each additional organization")}</h2>
          <p className="pricing-amount"><strong>{money(EUR_REFERENCE.additionalMinor)}</strong> <span>{t("al mes", "per month")}</span></p>
        </article>
      </div>
      <ul className="pricing-examples" aria-label={t("Ejemplos", "Examples")}>
        {examples.map(n => <li key={n}>{fill(n === 1 ? t("{n} organización: {price} al mes", "{n} organization: {price} per month") : t("{n} organizaciones: {price} al mes", "{n} organizations: {price} per month"),
          { n, price: money(monthlyFixedPriceMinor(EUR_REFERENCE, n)) })}</li>)}
      </ul>
      <p className="pricing-note">{t("Precios sin impuestos; el total con impuestos se muestra antes de confirmar cualquier pago.", "Prices exclude tax; the total with tax is shown before any payment is confirmed.")}</p>
      <section className="pricing-access">
        <h2>{t("Cómo se accede hoy", "How access works today")}</h2>
        <p>{t("AXIGNAL está en su programa Design Partner: el acceso es por invitación y, durante el programa, sin pago. Cuéntanos qué quieres observar y te responderemos.",
          "AXIGNAL is in its Design Partner programme: access is by invitation and, during the programme, without payment. Tell us what you want to observe and we will reply.")}</p>
        <div className="pricing-actions">
          <Link className="button primary" href="/contact">{t("Solicitar acceso", "Request access")}<ArrowRight size={16} aria-hidden="true"/></Link>
          <Link className="button secondary" href="/demo">{t("Ver el ejemplo guiado", "See the guided example")}</Link>
        </div>
      </section>
    </section>
  </PublicShell>;
}
