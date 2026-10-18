# Spec 100 — Lighthouse of the organization's website (PageSpeed Insights)

## Why

SEO is a pillar agencies judge first. Lighthouse's SEO, performance, accessibility and
best-practices scores are the technical-SEO language every agency already speaks; AXIGNAL
had real-user field data (CrUX) but no lab audit of the page.

## What

- `pipeline/web_quality/pagespeed.py`: PageSpeed Insights API v5 (free, licensed, Google's
  own service), mobile and desktop, four categories. Kept: Lighthouse version, conditions
  (strategy, form factor, throttling), time, the four scores and the failing audits.
- `tools/runtime/pagespeed.py`: queued on read, measured in the background (2 lab runs per
  origin), 14 days shared per origin, 150 origins per UTC day, refusals retried after 6 h.
- Findings: `WEB_REPRESENTATION` / `LIGHTHOUSE_AUDIT`, OBSERVED, one per strategy, with
  instrument and version, conditions, time, sample ("one lab run") and uncertainty
  (MASTER §54). Never a universal score; never presented as a search position or as the
  visitors' experience (CrUX).

## Configuration

On when a Google API key file is mounted: `AXIGNAL_PAGESPEED_API_KEY_FILE`, else the CrUX
key (`AXIGNAL_CRUX_API_KEY_FILE`) of the same Google project, which must allow the
PageSpeed Insights API. `AXIGNAL_PAGESPEED_ENABLED=false` turns it off. Cost: $0.
