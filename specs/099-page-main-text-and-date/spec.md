# Spec 099 — Main text and publication date of the pages web research reads

## Why

Spec 098 kept a page when its text named the organization anywhere, including navigation,
footers and brand lists (a privacy policy listed Vitaldent among its partners), and it
could not say when a page was published, so a 2019 article and yesterday's read the same.

## What

- `pipeline/web_search/article.py` runs trafilatura (with htmldate) on the HTML AXIGNAL
  already fetched: no extra request. Dependency group `web-reading`, installed in the
  subscriber runtime image only.
- A mention must be in the title or the page's main text; a name only in navigation,
  footers or brand lists is NOT_SUPPORTED.
- Findings carry `publishedAt` when the page declares a date; the observatory shows it.
- Without the library (or when nothing is extracted) the whole-page reading of spec 098
  applies unchanged: never fewer guarantees, never an invented date.
