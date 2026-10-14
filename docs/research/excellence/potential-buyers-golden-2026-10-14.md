# Potential buyers v1 on the golden set (2026-10-14, image eece008)

These are the results of the first measurement of ADR-0099 on the golden set: 30 organizations in 8 countries. The run used the deployed image on an isolated, read-only copy of production data. Raw report: `golden-2026-10-14-eece008.json`.

## Results

- 7 of 30 organizations get candidates (23%). The median is 22 candidates, and 3 organizations have a candidate backed by 2 or more kinds of signal.
- 23 of 30 get the `NO_BUYER_SIGNALS` unknown:
  - **21** have no customer profile: no client is visible on their website and they have no public awards;
  - **2** have customers but no route (SmartSites, Mailchimp). In both cases the "customers" are false positives (see below).
- By country, the share of organizations with candidates is: ES 3/5, CA 2/3, GB 1/4, NO 1/3, and 0 in DE, FR, US and AU.
- One factor inflates the portfolio-peer route: the 30 organizations share one evaluation tenant, so each one's "portfolio" is the other 29.

## Human review of candidates

| Organization | Route | Verdict |
|---|---|---|
| prosegur.es, rubau.com, humanlevel.com | Public award to a competitor plus public buyer of the category | **Good**: real public buyers of security, works and media, through named competitors. Candidates with two kinds of signal come first. |
| shopify.com | Similar to customers (Wikidata) | **Mostly good**. Williams-Sonoma and At Home sell home goods, like its customer Lulu and Georgia. Hotel chains reached through Momofuku are weaker: Wikidata classifies Momofuku's industry broadly. |
| kahoot.com | Group of customer (GLEIF) | **Weak**. Worldwide subsidiaries of HP and Amazon (Turkey, India). Group size makes this noise unless it is limited to the subscriber's countries. |
| impression.co.uk, lightspeedhq.com | Client shown on a peer's website | **Wrong**. The "clients" are SmartSites' badges and awards ("Google Partner", "BBB A+ rating", "Inc. 5000 honoree"). Lightspeed (point-of-sale software) also counts as a peer of an SEO agency because the industry match is too coarse. |

## Root causes and fixes (v1.1, before v2)

1. **Logo-wall extraction lets badges, awards and social icons through as clients.** This affects Relationships as well, not only buyers. Fix: reject partner badges, ratings, awards, case-study captions, social-network links and policy labels; require a name-like alt text.
2. **The peer match is too coarse.** It uses one broad industry, such as "IT services". Fix: also require overlapping activity codes at class level.
3. **The customer-group route is too broad.** Fix: keep only entities in the subscriber's countries, plus the ultimate parent.
4. **Few customer profiles: 21 of 30.**
   - Large organizations show customers on dedicated pages (/customers, /case-studies) or as logos without readable text, and the reader does not catch them.
   - Customers are also not the only route. A route that does not depend on visible customers (organizations in the sectors that buy from its sector, in its countries) would give global coverage.

## Decision

Fix 1–3 first; it is cheap and removes the wrong candidates. Then address coverage (4). Those two lines of work decide the order of v2.
