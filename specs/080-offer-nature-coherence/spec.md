# Feature Specification: Offer-nature coherence (seller ≠ what its buyers do)

**Created**: 2026-10-16

**Status**: Implemented (this PR); measured after deploy

**Input**: CTO, 2026-10-16:
> "Repito, es una tienda de venta de Té de Humus de Lombriz." "Landscaping and green-area maintenance es uno de los muchos casos de uso del Té de Humus de lombriz."
>
> "Pero estás arreglando el caso concreto de Biocultor. Debemos encontrar la forma de que esto no pase en ningún caso."

## Measured problem
biocultor.com sells a fertiliser, but it was read as **landscaping**, one of the uses of its product. It was then offered 95 gardening-services tenders. There are three general causes, and none is specific to Biocultor:

1. **The catalog had no entry for what it sells**, and the catalog question let the evaluator pick the closest entry. It picked the activity of the product's buyers.
2. **Nothing checked the nature of the offer.** A goods seller (SUPPLIES) was given a services activity (CPV 77) and a services CPV division.
3. **The lexicon read purpose phrases as offers.** In "abono para mantenimiento de jardines" or "software for cleaning companies", what follows the purpose preposition is the buyer's activity.

## What changes (for every organization)
1. **Nature is structural.** `offer_natures(entry)` reads SUPPLIES, SERVICES or WORKS from each catalog entry's own CPV codes (divisions 03–44 and 48 are supplies, 45 is works, the rest are services). No manual tagging, and no CPV means unknown.
2. **New question `fo_offer_nature`** (SUPPLIES, SERVICES, WORKS, MIXED or UNCLEAR) is asked together with the catalog question.
3. **Python coherence gate in `interpret_activity`.** When the nature is known, a judged catalog activity or CPV division of another nature is withheld (`NATURE_CONFLICT`): it becomes unknown, never the nearest activity. MIXED and UNCLEAR never withhold anything.
4. **Typed questions v2.**
   - The catalog criteria state each activity's nature.
   - The instructions exclude what customers do with the product and who buys it, and require NONE over the closest entry.
   - NONE is logged as `catalogGap` so the catalog grows from evidence.
   - The CPV division question classifies goods by the goods, never by their uses.
5. **Purpose rule in the lexicon** (six languages): a term named only after a purpose preposition in its clause is a use, not an offer. "For our team" stays the organization's own.
6. **Catalog gap filled:** `fertilisers-soil-amendments` (CPV 24440000, NAICS 325314/424910).

## Tests
- `tests/first_observation/test_offer_nature.py`: a deliberately wrong evaluator picks every services activity in the catalog for a goods seller, and all of them are withheld. A services CPV division is withheld for a goods seller. Coherent and unknown natures keep the judgment.
- `lexicon_traps.json`: use-of-product traps in ES, EN, FR, DE, IT and PT. Grow it with every new case; never delete one.

## Success criteria
- **SC-001:** on the next self-check, biocultor.com reads as fertilisers and gets no landscaping-services tenders. The other truth-set organizations lose no accuracy.
- **SC-002:** across the golden set, no SUPPLIES organization keeps a SERVICES-only catalog activity.
