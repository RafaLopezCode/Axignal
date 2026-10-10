/** Landing defaults never override a deep link explicitly selected by the visitor. */
export function shouldApplyLandingFacet(query: URLSearchParams): boolean {
  return !query.has("family") && !query.has("channel");
}
