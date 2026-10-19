# Spec 104 — Revenue a third-party page reports (Economics)

## Why
Economics had data for 14/20 agency clients, mostly Wikidata and sector figures. Agencies ask
"how big is this client?": revenue is reported in press and finance pages AXIGNAL can read.

## What
- Query `"<name>" <revenue word> -site:<domain> after:<2 years>` in the client's language
  (facturación, revenue, Umsatz, chiffre d'affaires, fatturato, faturação, omzet).
- `application/web_research/money.py` reads, deterministically, a figure only when, in the
  page's own text, **the same sentence** names the organization, a revenue word **leads to**
  the amount (≤ 80 chars), and the amount has scale and currency ("12,5 millones de euros",
  "£214m", "60 Mio. Euro").
- Left out, found while measuring on the 20-client panel:
  - a market's figure in the same paragraph ("el mercado factura 1.200 millones; Ecoalf crece");
  - targets and forecasts (Donte Group "aspira a duplicar su facturación, hasta 750 millones");
  - cumulative totals (Bombas "USD 2 billion in lifetime sales");
  - another figure between the word and the amount (profit, EBITDA, valuation, funding, debt);
  - figures without a year or more than three years old (Huel "£20m when he joined in 2017");
  - amounts without currency or with unreadable numbers.
- Finding `ECONOMIC_FACT` / `REPORTED:revenue`, POTENTIAL, `sourceKind: THIRD_PARTY_REPORT`,
  with value, currency, year, page and sentence; the most recent year among the pages read,
  never a sum or an average. Not an official account.

## Measured (isolated copy, real key, 75 searches, $0.06)
Revenue for 5/20, each checked against its sentence: Hawkers €36m (2023, accounts filed in the
Registro Mercantil, via Modaes), Holaluz €158.9m (2025), Ingeteam €914.3m (2024, Expansión),
mymuesli $31m (2024, CB Insights estimate), plus correct rejections listed above.
