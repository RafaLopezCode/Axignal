# Potential buyers: the sector route (ADR-0099 v1.2), golden set, 2026-10-14

**How it was measured.**
- 30 organizations in 8 countries.
- The deployed image `fca75b4`, with the branch's files overlaid read-only, run on an isolated copy of production data.
- Raw report: `golden-2026-10-14-sector-route.json`.

## Coverage

| | v1.1 (deployed) | v1.2, first pass | v1.2, final |
|---|---|---|---|
| Organizations with candidates | 4 (13%) | 14 (47%) | **20 (67%)** |
| Countries with at least one organization covered | 2 of 8 | 6 of 8 | **8 of 8** |

Final, by country: FR 4/4, DE 3/4, US 3/4, ES 3/5, CA 2/3, NO 2/3, GB 2/4, AU 1/3.

## Human review of the sector-route candidates

- **Sensible.**
  - Personio: Deloitte, METRO, Würth.
  - Vipps: Sparebank 1, Euronext, Gjensidige.
  - Lightspeed: The Beer Store, Gap, MTY Food Group.
  - Impression and SmartSites: Unilever, PepsiCo, Sysco.
  - Lendlease: Woolworths, Coles, Stockland.
  - Trumpf: Hochtief, PERI, Heidelberg Materials.
- **Noise from Wikidata classification.** These are a minority, mostly in wholesale trade: "Global Airlines", "Tiedemanns Tobaksfabrik", "American Apparel" listed in Australia.
- **Bias.** The most documented organizations come first, so the list leans to large groups. That fits enterprise sellers better than small ones.
- **Own sector still misread for two organizations.** Saint-Gobain and Alan are read as IT services. Their Wikidata industry is either missing or not in the curated table, so the website activity codes decide, and those are wrong for them. This also affects their value-chain findings.

## Still without candidates (10)

- **Construction groups:** Turner, PCL, Veidekke, Balfour Beatty.
- **No industry or country could be read:** Colegio Estudio, JVM, Plexus, Octopus Energy, Canva, Atlassian.

## Next

1. **Read customer pages** (/customers, /case-studies). Those routes are stronger than the sector route.
2. **Fix own-sector misreadings for large groups.**
3. **v2 sources:** grants, register events, OpenStreetMap establishments.
