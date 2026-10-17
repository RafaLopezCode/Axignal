# Feature Specification: Organization and economics from minute 0

**Created**: 2026-10-17

**Status**: Implemented (this PR)

**Input**: CTO, 2026-10-17: be extremely strong in every family from minute 0, to sell to SEO/GEO agencies and consultancies.

## Measured problem (14 real agencies and consultancies)
At the first reading:
- **Organization was 4/14.** Ten had only "unknown" findings.
- **Economics was 0/14.**

There were two causes:
1. **The legal name was taken only from structured data.** Their legal notices (aviso legal, Impressum, mentions légales) state it in plain text.
2. **Per-organization lookups waited.** Wikidata and Wikipedia (founding, headquarters, staff, revenue), job boards and buyers ran on a source thread that woke every 10 minutes.

## What changes
- **`legal_names_in_text`**, on legal-notice pages only:
  - It reads names that end in a legal form (S.L., S.A., GmbH, Ltd, SAS, S.r.l., Lda…) and trims the surrounding sentence.
  - It never takes well-known service providers named for operations (analytics, hosting, payments).
  - Names next to a registry identifier, or sharing the site's brand, come first.
  - At most two names.
  - The result is DECLARED by the site (`method: LEGAL_NOTICE_TEXT`) and never an admitted identity.
- **The source thread waits on a signal instead of sleeping.**
  - A fresh observation wakes it for the per-organization lookups.
  - Press and official journals keep their 10-minute ingestion clock.

## Measured (production copy, one production pass after observing)
| Family | Production, first minute | This PR, first minute |
|---|---|---|
| **Organization** | **4/14** | **8/14** |

Economics needs the source thread, which the isolated simulation does not run. In production it now runs at once instead of after up to 10 minutes.
