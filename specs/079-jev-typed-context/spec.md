# Feature Specification: Jev with typed context

**Created**: 2026-10-16

**Status**: Implemented (this PR); measured after deploy

**Input**: CTO, 2026-10-16:
> "Creo que la clave es Jev, que con suficiente contexto tipado va a darnos unos outputs limpios… el éxito del motor de AXIGNAL depende de usar Jev a la perfección."
>
> "Estamos utilizando datos públicos, no veo el problema."

## Measured problem
- **Activity verification (T013) changed nothing.** It ran with 11 OFFERED, 4 UNVERIFIED and **0 rejected**: SmartSites "legal services" and Lightspeed "web design" stayed. Jev saw only AXIGNAL's vocabulary.
- **The canary pilot had no activity.** The title of biocultor.com is "Comprar té de humus y servicios para jardines", yet nothing was established. Its earlier false "solar" reading came from a bare word.

## What changes
1. **Typed public text per page** in the activity batch (`_state`): kind, title, description, headings, services and body. It is minimized by `public_text`: no contact data, no sentences about people, no legal pages, and about/careers pages send no body.
2. **`fo_catalog_activity` (Choice over AXIGNAL's catalog, plus NONE and UNCLEAR)** is asked with sector when the lexicon finds nothing. Python turns a catalog answer into a catalog activity with its demand codes. NONE and UNCLEAR establish nothing.
3. **`activity_offered`** receives the public sentence where the activity is named (minimized), not a vocabulary projection.
4. **ADR-0090 amendment 2026-10-16** (in this PR).

## Not in this PR (CTO decision)
- **Seeding the autonomous loop from a Jev-judged activity.** Today spec 063 forbids it ("a judgment chooses where to look, it never founds a capability"), so a site only Jev can read (the canary) cannot start the daily loop.
- **Enabling `activity_offered` by default.** This is re-measured on the truth sets with the new state first (FR-008 of spec 075).

## Success criteria
- **SC-001:** on the next self-check and golden run, biocultor.com has an activity, and the 42 known organizations do not lose accuracy.
- **SC-002:** activity verification with context rejects the known false positives (SmartSites legal services, Lightspeed web design) and keeps the true ones.
- **SC-003:** the privacy tests prove that no contact data, URL, sentence about people or legal page reaches the provider.
