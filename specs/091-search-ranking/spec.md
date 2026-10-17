# Feature Specification: Search ranking measured outside-in, with no setup

**Created**: 2026-10-17

**Status**: Implemented (this PR); off until the API key is mounted

**Input**: CTO, 2026-10-17. The question was "Medimos las palabras claves y posicionamiento?". Search Console was rejected for prospects and agencies because it adds friction to sign-up. Scraping Google was declined (MASTER §54). The CTO's idea: "recreamos nosotros las búsquedas … como lo vería una persona normal y enriquecemos esos datos". The CTO chose the Brave Search API.

## What changes
- **Keywords are never asked of anyone.** They are the lexicon terms the organization's own website uses for each capability it offers:
  - in the language its site declares;
  - plus the country name in that same language, never a mixed-language query;
  - up to 3 searches per organization.

  Example for biocultor.com: «humus de lombriz», «humus de lombriz España», «abono orgánico».
- **Measured per search:**
  - its position among the top 20 organic results, or "not in the top 20";
  - who ranks instead;
  - a **"See this search on Google"** link (`google.com/search?q=…&hl=…&gl=…`). A person can see the same search; AXIGNAL never fetches that URL.
- **Summary measures:**
  - searches where it appears;
  - top-10 count;
  - average position;
  - the websites ranking instead, with counts.
- **Findings:**
  - `SEARCH_VISIBILITY / SEARCH_RANKS_MEASURED` or `SEARCH_NOT_RANKED` in Visibilidad (SEO channel). Each carries its instrument, conditions (keywords, country, language, depth), date, sample and uncertainty.
  - Timeline metric `presence.search_ranked_share`. Its instrument is the engine plus a hash of the conditions, so other keywords never fake a change.
- **Runner** (`tools/runtime/search_rank.py`):
  - queued on read and at minute 0 (`_prime`), measured in the background loop, never inline;
  - each organization at most every 30 days;
  - at most 40 organizations per UTC day;
  - a failure leaves the request queued, with nothing invented;
  - cost recorded (about $0.005 per search, about $0.015 per organization per month).

## Activation (CTO step)
1. Create a Brave Search API key on a plan whose terms allow storing results.
2. Place it on the host at `/etc/axignal/secrets/brave_search_api_key`: root-owned, mode 0440, in the runtime's secret group.
3. Add `AXIGNAL_BRAVE_SEARCH_KEY_FILE=/run/secrets/brave_search_api_key` to the subscriber configuration.
4. Deploy with `compose.search.override.yml`, only when the host file exists.

Without the key, the runtime builds no runner and nothing changes.

## Doctrine
- **MASTER §54.** This is a measurement with its instrument, conditions, time, sample and uncertainty: that engine's ranking on that date and place.
  - It is not what every person sees on Google, which personalizes results.
  - There is no scraping and no anti-bot bypass.
  - Appearing is not an endorsement.
  - There is no universal score.
- **No provider hard-wired into semantics.** The engine is an adapter in `pipeline/search_visibility/`.
