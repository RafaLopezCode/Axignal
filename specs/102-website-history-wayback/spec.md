# Spec 102 — The archived history of the organization's website (Wayback)

## Why

How old a website is and how often its home page changes are activity signals an agency
reads at a glance (a living site, a recent rebrand, a stale one). The Internet Archive
publishes them for free.

## What

- `pipeline/web_history/wayback.py`: the Wayback CDX index (free, no key), one capture
  per month of the home page: dates, HTTP status, content digest. No archived page is
  fetched.
- `application/web_history`: first and last capture, home-page versions (distinct digests
  among successful captures), overall and in the last 12 months.
- Findings: `OPERATING_SIGNAL` / `WEBSITE_HISTORY` or `WEBSITE_NOT_ARCHIVED` (Activity),
  OBSERVED, with instrument, conditions, sample and uncertainty: the first capture dates
  the domain, which may have had an earlier owner (huel.com and bombas.com have captures
  from 2000-2001), never the organization's founding date; without a successful capture in
  the last 12 months (a redirecting home page) recent changes are UNKNOWN, never zero.
- Background runner: two hosts per tick, 30 days shared per host, an outage retried after
  3 h (UNKNOWN, never "no history"). On unless `AXIGNAL_WAYBACK_ENABLED=false`. Cost: $0.
