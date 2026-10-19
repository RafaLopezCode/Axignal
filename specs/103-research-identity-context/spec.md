# Spec 103 — Web research for identity, context without own words, and short names

Step 2 of the governed web research (spec 098), on the path that runs today: when an
observation is read. (The daily loop is off in production until the CTO enables it.)

## Measured before (20 agency clients, 2026-10-19)
Context 7/20 (regulation only researched when the website names its activity in its own
words), Organization 12/20 (no identity verified; 9 declare a legal name), and short
single-word names (Goiko, Huel, Aigle) never researched: the press filter drops them.

## What
- **Identity:** `"<name>" <word> -site:<domain>` with the word each country's directories use
  for an identifier AXIGNAL can verify (ES CIF, FR SIREN, DE Handelsregister, GB company
  number, NO organisasjonsnummer). A page counts only if it names the organization and shows
  one or two identifiers with valid check digits (a list of companies does not). Finding:
  `IDENTITY_HINT` / `IDENTIFIER_IN_DIRECTORY`, POTENTIAL, with page and excerpt; only an
  official register admits an identity.
- **Context without own words:** AXIGNAL's specific classified activity (its English label)
  frames the sector query, in any language. Whole ISIC sections are too broad and are not
  used (they pulled agricultural-vehicle rules into fashion brands). Patent databases are
  never sector context.
- **Short names:** single-word names under six letters are researched (the query quotes the
  name and excludes its website; Jev judges the page title for another entity).

## Measured after (isolated copy, real key, 55 searches, $0.04)
Reputation 18/20 (Goiko from 0 to 5: OCU, Expansión, El Confidencial), identity found for 2
(Ecoalf CIF on a public registry of entities, Huel on Companies House), context pages
relevant (solar grid and VAT rules, ventilation). Most company directories refuse automated
reads: never bypassed.
