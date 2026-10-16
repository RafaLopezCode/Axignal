// How big a public call is, as its source publishes it (spec 081): value, lots, smallest lot
// and duration. Observed facts so a person can judge whether it is within reach; never a
// filter, a score or a verdict. Nothing published shows nothing (unknown, never zero).

type Translate = (es: string, en: string) => string;

function money(value: unknown, currency: unknown, locale: string): string | null {
  if (typeof value !== "number" || !Number.isFinite(value) || value <= 0) return null;
  const code = typeof currency === "string" && /^[A-Z]{3}$/.test(currency) ? currency : null;
  return new Intl.NumberFormat(locale, code ? { style: "currency", currency: code, maximumFractionDigits: 0 } : { maximumFractionDigits: 0 }).format(value);
}

function months(value: unknown, t: Translate): string | null {
  if (typeof value !== "number" || !Number.isInteger(value) || value <= 0) return null;
  if (value % 12 === 0) return value === 12 ? t("1 año", "1 year") : t("{n} años", "{n} years").replace("{n}", String(value / 12));
  return value === 1 ? t("1 mes", "1 month") : t("{n} meses", "{n} months").replace("{n}", String(value));
}

export function contractScaleRows(scale: unknown, t: Translate, locale: string): Array<[string, string]> {
  if (!scale || typeof scale !== "object") return [];
  const s = scale as Record<string, unknown>;
  const rows: Array<[string, string]> = [];
  const value = money(s.estimatedValue, s.currency, locale);
  if (value) rows.push([t("Importe estimado publicado", "Published estimated value"), value]);
  const smallest = money(s.smallestLotValue, s.currency, locale);
  if (typeof s.lots === "number" && s.lots > 1) {
    rows.push([t("Lotes", "Lots"), smallest
      ? t("{n} lotes; el menor, {value}", "{n} lots; the smallest, {value}").replace("{n}", String(s.lots)).replace("{value}", smallest)
      : String(s.lots)]);
  }
  const duration = months(s.durationMonths, t);
  if (duration) rows.push([t("Duración publicada", "Published duration"), duration]);
  return rows;
}
