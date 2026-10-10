/**
 * MASTER §27 fixed commercial pricing. Never interpolate FX rates.
 * A candidate foreign offer is NOT published unless reviewed, versioned and
 * bound to both provider Price references. No client input authorizes payment.
 */
export type CommercialCurrency = "EUR" | "USD" | "GBP";

export interface ApprovedFixedOffer {
  currency: CommercialCurrency;
  baseMinor: number;
  additionalMinor: number;
  approvalRef: string;
  stripeBasePriceRef?: string;
  stripeAdditionalPriceRef?: string;
}

export const EUR_REFERENCE: Readonly<ApprovedFixedOffer> = Object.freeze({
  currency: "EUR",
  baseMinor: 995,
  additionalMinor: 495,
  approvalRef: "MASTER_PRODUCT_MODEL_V2_SECTION_27",
});

export function approvedPriceBook(offers: readonly ApprovedFixedOffer[]): ReadonlyMap<CommercialCurrency, ApprovedFixedOffer> {
  const table = new Map<CommercialCurrency, ApprovedFixedOffer>();
  for (const offer of offers) {
    if (!["EUR", "USD", "GBP"].includes(offer.currency)
        || !Number.isSafeInteger(offer.baseMinor) || offer.baseMinor <= 0
        || !Number.isSafeInteger(offer.additionalMinor) || offer.additionalMinor <= 0
        || offer.baseMinor > 10_000_000 || offer.additionalMinor > 10_000_000
        || !offer.approvalRef || offer.approvalRef.length > 160) throw new Error("Unapproved commercial offer");
    if (table.has(offer.currency)) throw new Error("Duplicate commercial currency");
    const anyReference = offer.stripeBasePriceRef !== undefined || offer.stripeAdditionalPriceRef !== undefined;
    if (offer.currency !== "EUR" || anyReference) {
      if (!offer.stripeBasePriceRef?.startsWith("price_")
        || !offer.stripeAdditionalPriceRef?.startsWith("price_")
        || offer.stripeBasePriceRef === offer.stripeAdditionalPriceRef)
        throw new Error("Both distinct reviewed Stripe Prices are required");
    }
    table.set(offer.currency, Object.freeze({...offer}));
  }
  const eur = table.get("EUR");
  if (!eur || eur.baseMinor !== 995 || eur.additionalMinor !== 495) throw new Error("EUR master offer is mandatory");
  const refs = [...table.values()].flatMap(offer => [offer.stripeBasePriceRef, offer.stripeAdditionalPriceRef]).filter((ref): ref is string => Boolean(ref));
  if (new Set(refs).size !== refs.length) throw new Error("Stripe Prices cannot be reused across currencies");
  return table;
}

export const PUBLISHED_PRICES = approvedPriceBook([EUR_REFERENCE]);

export function monthlyFixedPriceMinor(offer: ApprovedFixedOffer, organizations: number): number {
  if (!Number.isSafeInteger(organizations) || organizations < 1 || organizations > 100)
    throw new RangeError("Organizations must be an integer from 1 to 100");
  return offer.baseMinor + (organizations - 1) * offer.additionalMinor;
}

export function suggestedCurrency(country: string | null, book = PUBLISHED_PRICES): CommercialCurrency {
  const preferred: CommercialCurrency = country === "US" ? "USD" : country === "GB" ? "GBP" : "EUR";
  return book.has(preferred) ? preferred : "EUR";
}

export function formatFixedMoney(locale: string, offer: ApprovedFixedOffer, minor: number): string {
  if (!Number.isSafeInteger(minor) || minor < 0) throw new RangeError("Invalid minor units");
  return new Intl.NumberFormat(locale, { style: "currency", currency: offer.currency }).format(minor / 100);
}
