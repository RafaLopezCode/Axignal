# Public SEO delivery audit — 2026-10-20

Scope: the deployed public site and its canonical sitemap, compared with main
`ed1e1250ee0ddade4fbe46c2ffda052cf989dc51`. This is a repair to the existing
spec 056 discovery contract, not a new product feature or a change of homepage.
Authority: Constitution; ADR-0014/0015; BRAND_ASSET_AUTHORITY_V2. Design mode:
PRESERVE. No subscriber semantics, corpus, accepted visuals or security policy
changes. No merge or production deployment is authorized by this audit.

## Findings from unauthenticated production HTTP

- The current sitemap contains 596 unique HTTPS URLs on `axignal.com`.
- All 596 returned HTTP 200 without redirects in this bounded crawl. Each
  contained one H1, a title, description, a self canonical and the expected
  HTML language; none declared noindex. Every hreflang destination belongs to
  the sitemap and every sitemap URL has an incoming crawlable HTML link.
- The root, `/es`, robots and sitemap respond successfully. HTTP and www
  normalize to the canonical HTTPS origin. `robots.txt` permits public pages
  and `/brand/`, while protecting private application/API paths.
- Metadata currently declares only the source SVG icon and Apple touch PNG.
  The original SVG's 901 x 900 viewBox must remain untouched as official art.
  The explicit square search PNG and ICO browser fallback required by the
  brand contract were missing from the root metadata. The approved raster
  derivatives already exist; regeneration is unnecessary.
- `/favicon.ico` at the root returns 404, but that is not a blocker: the
  documented favicon URL is `/brand/favicon.ico`. Google accepts relative URLs.
- Old procurement/acquisition URLs shown in historical indexing data are not
  part of the current sitemap; sampled retired URLs return 404. Do not blanket
  redirect them to the homepage or restore unsupported product claims.

The audit is an HTTP sample at a point in time, not a guarantee of future
uptime or Google's indexing decisions. It does not establish content quality,
rankings, field performance or that all historical exclusions remain broken.
Private Search Console reports remain outside Git; the user-facing audit
distinguishes historical coverage from a current live Google inspection.

## Repair

Declare the existing 96 x 96 PNG explicitly, retain the official SVG, add the
existing multi-size ICO fallback, and label the Apple/application icons with
their MIME types and true dimensions. All bytes and public URLs remain stable.
Tests check actual root metadata wiring, PNG IHDR dimensions, the provenance
manifest hashes and existing robots/ingress access. No dependency is added.

## Recovery and release boundary

After an approved deploy: fetch the root and each language's SSR head; verify
the declared icons return their correct image types; run a live homepage URL
Inspection and request recrawling through Search Console. Recheck canonical
selection and the favicon after Google processes the new crawl. Do not mark
all old 5xx examples fixed merely because today's homepage fetch succeeds.
Map retired pages only where an editorially equivalent destination exists.

Google controls indexing and search-result appearance. Neither successful
fetching nor sitemap submission guarantees either outcome:

- https://developers.google.com/search/docs/essentials/technical
- https://developers.google.com/search/docs/appearance/favicon-in-search
- https://developers.google.com/search/docs/crawling-indexing/troubleshoot-crawling-errors

## Verification

Verification details follow in verification.md.
