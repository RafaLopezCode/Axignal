# Spec 107 — Markets a third-party page reports it has entered

## Why
Markets had data for 14/20 agency clients. A first idea (pages of stockists on country-code
domains) was measured and not shipped: 1 valid of 4 (news and its own stores at home).

## What
- Query `"<name>" <international expansion> -site:<domain> after:<2 years>` in its language.
- `application/web_research/expansion.py`: a country counts only when the same sentence names
  the organization (word for word: "Bloom & Wild" names "bloom wild"), an entry verb (abre en,
  entra en, launches in, s'implante, eröffnet, apre…) and the country (names in six languages);
  plans, targets and forecasts are left out; the home country is never "entered".
- Finding `DECLARED_SERVICE_AREA` / `ENTRY_REPORTED`, POTENTIAL, countries with up to three
  pages each and the sentence; a market to check, not sales confirmed.
- Also: reported revenue (spec 104) now matches names with symbols word for word.

## Measured (20 agency clients, isolated copy, real key, 80 searches, $0.06)
3/20, all correct: Hawkers → Mexico (Modaes, retail openings), Zitrón → Netherlands (El
Comercio, new plant), Sézane → Spain, United Kingdom (Vogue, its stores). Sézane gains the
Markets family.
