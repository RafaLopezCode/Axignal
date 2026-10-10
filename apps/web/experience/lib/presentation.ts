/** MASTER §27 reference economics. Never bills, converts or grants access. */
import { EUR_REFERENCE, formatFixedMoney, monthlyFixedPriceMinor } from "./commercial-prices";

export function monthlyReferenceCents(focuses: number): number {
  return monthlyFixedPriceMinor(EUR_REFERENCE, focuses);
}

export function formatReferenceMoney(locale: string, cents: number): string {
  return formatFixedMoney(locale, EUR_REFERENCE, cents);
}
