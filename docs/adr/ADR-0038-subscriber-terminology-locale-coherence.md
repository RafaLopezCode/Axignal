# ADR-0038 — Subscriber Terminology and Locale Coherence

**Status:** Accepted
**Date:** 2026-09-30
**Authority:** MASTER §§9, 22, 25, 26, 55; ADR-0016, ADR-0035, ADR-0037.

## Context

The subscriber surface historically mixed product vocabulary, internal ontology,
synthetic-lab wording and partial locale previews. A resolved locale could
therefore show English and Spanish controls together, while implementation terms
could leak into onboarding even though the canonical model itself remained
correct.

FR-12 separates canonical domain language from subscriber-facing language. The
goal is not to rename the domain. It is to ensure that the human interface uses
the smallest vocabulary needed to understand value and evidence.

## Decision

Subscriber-facing language follows three classes:

1. **Product vocabulary retained:** AXIGNAL, AXIGLAND, Xeed, Xignal and AXENT.
2. **Human descriptive language preferred:** organization, information,
   evidence, market, capability, currentness, observation and relationship.
3. **Internal ontology hidden by default:** FAXT, INXIGHT, PATHX,
   EvidenceAdmission and implementation state names.
Internal terms may appear only in explicitly expert/admin/evidence contexts
where their exact meaning is useful. Hiding a term does not alter its canonical
identity or authority.

English and Spanish are complete subscriber UI catalogs for the current
surface. Spanish is a supported resolved locale, including first-view,
navigation, actions, status, AXENT controls, accessibility labels and synthetic
lab chrome.

German, Japanese and Arabic remain explicit layout-stress profiles only. They
are not represented as complete subscriber languages. The UX lab may expose
them for text expansion, CJK and RTL testing without granting them product
locale authority.

The UX-lab locale preference remains local-browser state only. FR-12 does not
create account-level locale persistence.

## Commercial language boundary

SEO, GEO, AEO and AIO agencies remain a first-class acquisition/use-case
audience under the MASTER and Public Landing Page Contract. This does not make
AXIGNAL an SEO/GEO/AEO tool and does not require agency-specific terminology in
the universal subscriber chrome.

## Invariants

`CANONICAL TERM != REQUIRED SUBSCRIBER LABEL`

`LOCALE FALLBACK != SILENT MIXED-LANGUAGE UI`
`LAYOUT PREVIEW != SUPPORTED PRODUCT LOCALE`

`HIDE INTERNAL JARGON != CHANGE CANONICAL MEANING`

`AGENCY AUDIENCE != SEO TOOL IDENTITY`

## Consequences

- Spanish browser/user resolution now produces Spanish interface copy rather
  than silently resolving to English.
- Complete locale catalogs must maintain key parity with English before they
  become supported locales.
- Static and runtime actions use presentation keys rather than hard-coded
  subscriber strings where FR-12 touches them.
- Synthetic content may retain its source language; interface chrome must not
  disguise content language as locale authority.
- Future launch locales can be promoted only after complete-catalog parity and
  browser validation.

## Non-goals

This ADR does not change canonical schemas, ontology names, evidence admission,
Xeed authority, AXENT reasoning, landing runtime scope, account persistence or
production deployment. It does not declare German, Japanese or Arabic complete
product locales.
