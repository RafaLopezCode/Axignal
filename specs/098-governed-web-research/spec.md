# Spec 098 — Governed web research (Reputation and Context)

## Why

Reputation and Context depended on curated press feeds and official journals. Reviews,
complaints, regional press and the pages that frame an activity were not reachable, so
agency clients showed Reputation for 13/20 and Context for 6/20 (panel 2026-10-18).

## What

A web search API (DeepSeek Search, replaceable behind `application.web_research.WebSearch`)
proposes candidate pages. **Nothing it returns is evidence**: its `summary` and `content`
are never kept. AXIGNAL reads each candidate with its governed reader (robots.txt first,
bounded GETs, no authentication, no anti-bot bypass) and keeps a page only when the
page's own text supports the finding.

| Purpose | Query (≤ 3 per organization, in its language) | Kept when | Finding |
|---|---|---|---|
| Reputation | `"<name>" <reviews word> -site:<domain>` and `"<name>" -site:<domain> after:<1y>` | third-party host (not its domain, a same-brand domain or a social profile), relevance ≥ 0.8, its text names it | `MENTION` `REVIEW_PAGE` (review platforms) or `WEB_MENTION`, POTENTIAL, URL and excerpt |
| Context | `"<activity term>" <regulation word> lang:<l> after:<1y>` | its text uses the activity term | `CONTEXT_SIGNAL` `WEB_SECTOR_SOURCE`, POTENTIAL, `notAboutThisOrganization` |

Homonyms: Jev judges the page title with the press attribution question (spec 085);
`ANOTHER_ENTITY` withholds the page, the safe direction. Python keeps the last word.

## Governance

- Off by default: `AXIGNAL_WEB_RESEARCH_ENABLED=true` **and** a readable
  `AXIGNAL_DEEPSEEK_API_KEY_FILE` (mounted secret, `compose.research.override.yml`).
- Never on the read path: reads queue research; a background stage runs it.
- Cost: $0.00075 per billed search (empty answers are free), recorded per search and per
  organization; a global cap of 120 searches per UTC day (≈ $0.09); every query is shared
  by all organizations asking it for 30 days (sector queries are paid once).
- A mention is not an endorsement (MASTER §54); context is about the sector, never the
  organization, and is not legal advice. UNKNOWN stays UNKNOWN: an unreadable page or one
  whose robots.txt cannot be read is not shown.

## Later

Step 2: route the blocked research leads of the daily loop (reviews, hiring, regulation).
Step 3: AXENT governed research through the same port.
