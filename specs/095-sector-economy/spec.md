# Feature Specification: Economics in context, its sector in its markets

**Created**: 2026-10-18

**Status**: Implemented (this PR)

**Input**:
- CTO, 2026-10-18: "Economía está contextualizada con el mercado del Suscriptor, verdad?" It was not: Economics showed the organization's own figures and one crossing with public contracts, never its sector or its markets.
- The CTO then asked: "¿cómo va a saber Axignal la facturación?" Its own revenue is public only for some organizations: open registers (FR, NO, US-listed, UK with key) and Wikidata. It is unknown for most SMEs, for example in Spain.
- CTO decision: "arranca así". Give every account the size and trend of its market, and compare its own figures only when they exist.

## What changes
- **Official table** (`application/sector_economy/eu_sbs.json`), built by `tools/data/build_sector_economy.py` from Eurostat's structural business statistics (`sbs_ovw_act`, `sbs_sc_ovw`; CC BY 4.0).
  - **Coverage:** EU-27, Norway, Iceland and Switzerland, about 80 NACE divisions each, with the latest year per cell (2024).
  - **Per division:** enterprises, persons employed, net turnover, turnover per person, employment growth and gross operating rate.
  - **By size class:** enterprises and turnover.
  - Missing or confidential cells stay absent: unknown, never zero.
  - It is versioned in the repository, so there is no network call on the read path.
- **`SECTOR_MARKET:<country>`** (Economics), one per market: its own country first, then the markets it looks at, at most five.
  - **Statement:** "Its sector in France: 139,348 enterprises turn over €104B and employ 560,858 people (2024)", plus the sector's employment change over the last year.
  - **The sector** is the one every family already reads (`company_industry`: register code, Wikidata, website activity, CPV).
  - **Epistemic state:** DECLARED when read from the register's activity code, POTENTIAL when read from its activity.
  - It is marked `aboutSector` and `notAboutThisOrganization`, so no consumer takes it for the organization's own figure.
- **INXIGHT `economics:SIZE_IN_SECTOR`**, only with its own figures:
  - its reported revenue against the average enterprise of its size class and of the whole sector;
  - the share of the sector's enterprises that are its size or larger.

  Verified on real figures: Eskimoz reports €16.4M (2023) with 50–249 people. That is about 0.7 times the average French IT services firm of its size, and among the roughly 0.7% of firms its size or larger. Figures of different years are compared as an order of magnitude.
- **Family value:** Economics picks the organization's own register figures, then Wikidata, then its sector's market.
- **Web:** copy and basis rows (NACE activities, turnover per person, where the sector was read from) in the 6 languages.

## Not done yet (next)
- Monthly sector trend (Eurostat short-term statistics).
- Equivalents outside Europe: US Census SUSB and UK ONS ABS.
- A rebuild cadence for the table (yearly).

## Doctrine
- Official statistics describe the sector, never the organization.
- A sector read from its activity is POTENTIAL.
- UNKNOWN is never zero, and no revenue is estimated.
- There is no universal score: a comparison is an order of magnitude with its years and classes shown.
