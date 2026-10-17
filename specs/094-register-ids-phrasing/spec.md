# Feature Specification: Register numbers as legal notices really state them

**Created**: 2026-10-18

**Status**: Implemented (this PR)

**Input**: CTO, 2026-10-18: "continúa" (point 5 of the agency plan: re-measure, then strengthen the weakest family). The fix applies to every account.

## Measured (14 agencies, release f79ea11, isolated copy)
Agencies with sourced findings, out of 14, at minute 0 → a few minutes later:

| Family | Minute 0 | A few minutes later |
|---|---|---|
| Visibilidad | 14 | 14 |
| Reputación | 4 | 7 |
| Valor | 13 | 13 |
| Mercados | 8 | 8 |
| Relaciones | 13 | 13 |
| Demanda | 12 | 12 |
| Actividad | 7 | 7 |
| Economía | 0 | 4 |
| Organización | 8 | 8 |
| Contexto | 4 | 4 |

Since the 17-10 baseline:
- Reputación went from 1 to 4 at minute 0.
- Organización went from 4 to 8.
- Contexto went from 0 to 4.

**Economics is the weakest family.** Only the four large consultancies have it, through Wikidata. A probe of the agencies' legal notices found why:
- **eskimoz.fr** writes "RCS de Paris sous le numéro 528 338 494". The French pattern did not accept "sous le numéro", so the open French register (revenue, profit, employee band, size) was never asked.
- **simon-kucher.com** writes "HRB 3771, AG Bonn". No German register entry was read.
- **Spanish agencies** declare their CIF, which is read. No open Spanish register states figures.

## What changes
- **French register numbers:**
  - The label (SIREN, SIRET, RCS, or "registre du commerce et des sociétés") may now be followed by up to seven words ("de Paris sous le numéro", "de Lyon sous le n°") before the nine digits.
  - The SIREN check digit still rejects any other number.
  - Verified live: SIREN 528338494 is GROUPE YDYLE (the legal name its notice states). The register shows revenue of €16.35M and net profit of €2.26M in 2023, 50–99 employees, SME size, and activity since 2010.
- **German register entries** (`DE_HR`): HRA or HRB, its number and its register court ("HRB 3771, AG Bonn", "Amtsgericht München, HRB 123456").
  - A number without its court is not unique, so it is not read.
  - It is a declared identity anchor (Organización), not an admitted identity.
- **Readable identifiers on the web:** a declared identifier reads as people say it ("CIF B54941729", "German commercial register entry HRB 3771 Bonn"), never as the scheme code ("ES_CIF …"). This is shown in the 6 languages.

## Not changed, and why
- **United Kingdom.** Companies House is read only with a free API key the operator creates. Builtvisible states only its VAT number. Activating Companies House is a CTO step: create the key and add `AXIGNAL_COMPANIES_HOUSE_API_KEY_FILE`.
- **Spain and Germany.** No open register publishes accounts. The CIF and HRB remain identity anchors.

## Doctrine
- A declared identifier is DECLARED, never an admitted identity.
- Register facts carry their register, licence, year and link.
- Nothing is read by name. Only an exact identifier is used.
