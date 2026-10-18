# Feature Specification: Activity and Markets from the client's own website

**Created**: 2026-10-18

**Status**: Implemented (this PR)

**Input**: CTO, 2026-10-18. The goal is a tool so powerful across families that SEO/GEO agencies and consultancies find it irresistible for observing their clients. The quality panel is therefore 20 typical agency clients, not agencies: ES, FR, DE, IT, PT, GB, NL and US across ecommerce, restaurants, clinics, energy, B2B SaaS, industry and food, with Biocultor included. On that panel, Activity had data for 5 of 20 (a hiring channel only) and Markets for 10 of 20. The CTO's decision: "arranca con Actividad y Mercados".

## What changes
- **Activity: its own channel.**
  - **Which feed is read:**
    1. The news feed its homepage declares (RSS/Atom alternate), on its own site and never a comments feed.
    2. If none is declared, one conventional guess for its platform: the Shopify blog its homepage links (`/blogs/<handle>.atom`, else `news`), or WordPress `/feed/`.
  - **How it is read:** one more request, within the site request budget, with robots respected before and after redirects. Only titles, links and dates are kept, never the articles' text.
  - **What it adds:**
    - `OPERATING_SIGNAL/PUBLISHING_CADENCE` (OBSERVED): posts in the last 30, 90 and 365 days, and the latest date. A quiet channel says when it last posted, and it is never read as the organization being idle.
    - Up to 5 `MENTION/OWN_PUBLICATION` (OBSERVED, its own voice).
    - The timeline metric `activity.publications_90d`.
- **Markets: its site versions per country.**
  - `DECLARED_SERVICE_AREA/SITE_VERSIONS_FOR_COUNTRIES` (DECLARED), with each country and its evidence:
    - `HREFLANG`: language-region tags such as fr-FR or en-GB, never a bare language or es-419;
    - `COUNTRY_PATH`: country paths such as /es-es/ or /it_it/ on its own host;
    - `COUNTRY_DOMAIN`: country domains of the same brand, such as brand.fr, but never generic ones like .co or .io.
  - It is where it says it sells or serves, not proof of sales.
- **Family value:** Activity picks its publishing pace first, and Markets its site versions after group countries.
- **Web:** copy in the 6 languages.

## Measured on the real sites of the 20 clients (2026-10-18)
- **Country versions:** 11 of 20 declare them, for example Hawkers 21 countries, Velasca 26, Claus Porto 31 and Tony's 13.
- **Own channel with dated posts:** 7 of the 16 sites that answered.
  - Ecoalf: 12 posts in 90 days.
  - Brooklinen: 20 posts in 90 days.
  - Zitrón, mymuesli, einhorn and Tony's: some posts in 90 days.
  - Goiko: quiet since 2025-12.
- **Not readable:** 4 sites refused or timed out (Sézane, Aigle, Bombas, Ingeteam). Their families stay unknown.

## Doctrine
- Its own channel is its own voice: a post is OBSERVED, but what it says is the organization's claim.
- Country versions are DECLARED, never sales.
- A guessed feed that does not exist is simply no feed: there is no retry and nothing is invented.
- No text is kept beyond titles.
