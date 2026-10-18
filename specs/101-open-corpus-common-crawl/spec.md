# Spec 101 — Is the website in the open corpus AI models learn from? (Common Crawl)

## Why

GEO is a pillar. Common Crawl's monthly crawls are an open web corpus that many language
models are trained on; whether a crawl captured a client's site, and how much of it, is a
GEO signal an agency can act on (robots.txt rules for CCBot, crawlability, internal links).
No cheap competitor shows it.

## What

- `pipeline/open_corpus/common_crawl.py`: the public CDX index (free, no key). Per domain
  (subdomains included): captures and HTTP 200 captures in the latest crawl (up to 1,000),
  and whether each of the two previous crawls captured it. A 404 is a crawl without
  captures; a 5xx or a timeout is UNKNOWN, never absence.
- `tools/runtime/common_crawl.py`: queued on read, one domain per tick, 30 days shared per
  domain, a busy index retried after 3 h.
- Findings: `GENERATIVE_VISIBILITY` / `OPEN_CORPUS_CAPTURED` or `OPEN_CORPUS_NOT_CAPTURED`,
  OBSERVED, with instrument, crawl, date, sample and uncertainty (MASTER §54): being
  captured does not mean a model learned or cites it; not being captured may be sampling,
  robots.txt or size.
- On unless `AXIGNAL_COMMON_CRAWL_ENABLED=false`. Cost: $0.
