/** Registry candidates and the search a person starts from. Suggestions only, never identity. */
export type IdentityCandidate = { lei: string; legalName: string; country: string | null; city: string | null };

/** A first search from what the person already gave: a name as typed, or a website's own name. */
export function identitySearchFrom(name: string, website: string | null): string {
  const label = name.trim();
  const host = (website ?? (/^[\w-]+(\.[\w-]+)+$/.test(label) ? label : "")).toLowerCase().replace(/^www\./, "");
  if (host) return host.split(".")[0].replace(/-/g, " ");
  return label.replace(/^(home|inicio)\s*[-|·]\s*/i, "").replace(/\s*[-|·]\s*(home|inicio)$/i, "");
}

/** The website a pending organization was given, from its observation or its label. */
export function websiteOf(label: string, sourceUrl: string | null | undefined): string | null {
  try { if (sourceUrl) return new URL(sourceUrl).hostname.replace(/^www\./, ""); } catch { /* not a URL */ }
  const text = label.trim().toLowerCase();
  return /^(https?:\/\/)?[\w-]+(\.[\w-]+)+\/?$/.test(text) ? text.replace(/^https?:\/\//, "").replace(/\/$/, "").replace(/^www\./, "") : null;
}


/** Prefix of a web-anchored subject's id (domain.identity.WEB_SUBJECT_PREFIX, ADR-0087 amendment). */
export const WEB_SUBJECT_PREFIX = "org:web:";

/** A subject identified by its own website, not verified by any registry. */
export function isWebSubject(organizationId: string | null | undefined): boolean {
  return typeof organizationId === "string" && organizationId.startsWith(WEB_SUBJECT_PREFIX);
}
