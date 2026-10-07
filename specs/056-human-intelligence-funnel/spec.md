# 056 — Human Intelligence Funnel & transversal vocabulary

**Status:** IMPLEMENTED (experience) · **Date:** 2026-10-07

## Problem

The ten canonical families were correct but asked people to guess: SEO hid in
"Presence", opportunities in "Demand", customers in "Relationships", services
in "Value". Nothing on screen used the words a person already has, and the same
depth of explanation had three names (lens layers, signal tabs, Axent).

## Solution

- **One vocabulary authority** (`lib/family-vocabulary.ts`): per family, the
  everyday terms shown to people and extra aliases people type, matched in all
  six languages with case and accents folded. Families are unchanged.
- **Recognition where families appear:** the Atlas tiles and each family header
  show the terms under the name (`SEO · GEO · Visibilidad digital`); every
  family navigation item carries them in its accessible name. Family intros are
  rewritten as one plain sentence each (UX-copy review).
- **Recall without the taxonomy:** a small field in the sidebar's Families
  section filters the same navigation by those words ("clientes" → Relaciones),
  Enter opens the match.
- **Same words in Axent:** when a question names a topic that lives in another
  family ("¿Cómo está mi SEO?" while reading Markets), Axent says where it
  lives and offers an allowlisted `family` card to open it. `validatePlan`
  accepts only canonical family ids. "What changed?" stays with the family in
  view; generic words ("context") never redirect.
- **One funnel, one set of names** (`lib/funnel.ts`): 1 what is happening →
  2 why it matters → 3 how AXIGNAL knows → 4 all the evidence, used by lens
  layers, signal-detail tabs (with the question as their description) and
  Axent's suggested questions.

## Deviations from the brief (and why)

- "Sectores" was proposed for both Markets and Context; one concept must have
  one expression, so Context reads *Regulación · Tendencias · Factores
  externos* and only Markets owns "Sectores".
- Economics uses *Facturación · Empleo · Cifras* instead of "Magnitudes /
  Señales económicas", which are not recognisable to non-specialists.
- No chips or new components: terms reuse the existing `type-meta` role and
  corporate blue; the finder filters existing navigation rather than adding a
  search results surface.
- The Python AXENT lexicon (spec 055, separate PR) should read this vocabulary
  once both are merged; until then they are aligned by hand.

## Not changed

Families, Atlas layout, navigation model, Panorama structure, AXENT rail,
timeline, character, iconography, epistemic badges and global tokens.
