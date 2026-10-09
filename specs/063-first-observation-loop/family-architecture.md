# 063 — Family architecture and family matrix

Status words: **IMPLEMENTED** (wired into a runtime path that can execute), **PARTIALLY_IMPLEMENTED**
(code exists for a narrow slice, or exists but is not composed), **DESIGNED** (contract, catalog
entry or doctrine only), **FUTURE** (named, no design). Evidence: code inventory of base
`19018f2` plus this branch. A MASTER concept is never listed as runtime because it is doctrine.

## 1. Decision: one substrate, composable family policies — not a framework, not a monolith

| Option | For | Against | Verdict |
|---|---|---|---|
| Monolithic researcher (crawl → big context → model → report) | simple to start | cost grows with context, no reuse, no per-family stop/refresh, opaque basis, violates MASTER §53 / §56.19 | rejected |
| One `FamilyResearchContract` class per family | explicit | duplicates routing, budgets, currentness, leases that already exist; 30 mini-products | rejected |
| **Composable policies over one shared substrate** (what the code already has, completed) | one AXIGLAND, one Observation Memory, one routing/budget/lease/currentness engine; families differ only in data: questions, source capabilities, entry points, follow-ups, cadence, budgets, refresh | requires keeping policies as governed data and adding adapters per source | **chosen** |

The substrate already exists and is the right shape: `QUESTIONS` per `OpportunityFamily` and the
source catalog (`catalog.py`), `SourceRegistry` routing with information gain, quality, learning
and cost bands (`strategy.py`), `FAMILY_POLICIES` with entry points, follow-up rules, cadence,
budgets and currentness per observation family (`observation_runtime/families.py`), EB-06
currentness, EB-07 shared work, ADR-0089 garden gate. The defect was not its shape but that **one
adapter (TED) is composed**, the website bootstrap is missing, and acquisition is per-Focus pull.
This branch completes the substrate where the multiplier is largest and adds no framework:

* **First Observation** = the bootstrap the family policies lacked (public web representation,
  activity, declared places, identity hints) with its own cheapest-first policy.
* **World demand index** = the acquisition-mode inversion for one opportunity family, reusable by
  any source that can page a world slice (`SliceFeedPort`).
* Discipline lives in data and small ports: questions, vocabularies, check lists, stop/refresh
  per family. Adding a family means catalog entries + an adapter, not a new pipeline.

Cross-family intelligence is a derivation over the same evidence, kept separate from the
evidence: e.g. `ACTIVITY` (prose) + `WEB_REPRESENTATION` (no structured offer) →
`REPRESENTATION_GAP: OFFER_NOT_MACHINE_READABLE` (POTENTIAL, `notCausal: true`, basis kinds kept).

## 2. Acquisition mode per family (the largest economic lever)

`ORGANIZATION_PULL` pays per Focus × capability × market × question and sees one truncated
page. `WORLD_SOURCE_INGESTION` pays per source slice (country × notice kind × day) and matches
every Focus locally. ESTIMATED model (`evidence/experiments.json` → `scale`; inputs labelled
there, notice volume not measured on TED): 10 Foci 40 vs 6 requests/day (~7×); 100 Foci 400 vs
12 (~33×); 1,000 Foci 4,000 vs 120 (~33×); 10,000 Foci 40,000 vs 162 (~250×). The pull model also
sees only one 20-record page per query; the slice sees every notice of its window. Rule adopted:

* Event streams published by an authority (procurement notices, awards, grants, permits,
  regulations): **WORLD_SOURCE_INGESTION**, demand-materialized (a slice is ingested only after
  a Focus question needs it — MASTER §3.2), matched many times.
* Facts about one organization (its website, its registry entry, its reviews): **ORGANIZATION_PULL**
  with world-level reuse keyed by the public object (origin, identifier, review source id).
* Representation measurements (search/generative): **HYBRID** — validated query families are
  shared infrastructure (MASTER §54 instruments), per-organization only the entity checks.

## 3. Family matrix

### A. Economic knowledge domains

| Domain | Status | Acquisition / scope | Deterministic | Jev | Luna/AXENT | Stop / refresh | Output + basis | Gaps |
|---|---|---|---|---|---|---|---|---|
| Identity | IMPLEMENTED (registry: GLEIF exact LEI) | pull; canonical (world) | locator parse, admission, bindings | — | — | per request; registry cache | pending reason; IDENTITY_HINT (declared LEI/legal name, never admitted) | no domain/name registry; national registers FUTURE |
| Economic DNA / activity | PARTIALLY_IMPLEMENTED (First Observation) | pull website; reading world-level, hypothesis per target | lexicon, schema.org types→ISIC | ISIC/CPV/NAICS/customers/delivery/operating (one batch) | none | stop when activity + place evidenced; ≤2 extra pages; re-check 7 d if unknown | ACTIVITY with exact quote, method, model, confidence | products/services taxonomy; T12 VALUE family not acquired |
| Capabilities | IMPLEMENTED narrow (lexicon) + PARTIALLY (open classification, routing codes) | as above | lexicon codes | classification codes (routing only) | — | as above | basis cites Organization observation | capability ≠ classifier; certifications not fed to gate |
| Markets / attention | PARTIALLY_IMPLEMENTED | declared address/areaServed/text mention → POTENTIAL attention | place coding table | location confirmation among mentioned candidates | — | with site reading | DECLARED_LOCATION / SERVICE_AREA, attention scopes | user-directed widening FUTURE |
| Economic reach (ADR-0089) | IMPLEMENTED (deterministic garden) | derived from observations | cues, gate | — | — | per projection | gate dimensions | relevance gate families mostly UNRESOLVED |
| Needs / value chain | PARTIALLY_IMPLEMENTED | — | exposure channel exists | — | — | — | — | drivers never composed |
| Certifications | PARTIALLY_IMPLEMENTED | — | extracted | — | — | — | — | not fed to gate |
| Corporate structure | FUTURE | — | — | — | — | — | — | GLEIF level-2 not used |
| Observed / potential relationships | IMPLEMENTED narrow (TED award co-appearance, buyer demand) | per-Focus pull → index for open notices | buyer/winner parse | — | — | T12 cadence | "not a relationship" kept | other sources FUTURE |
| Competitive neighbourhood, evidence diversity | FUTURE | — | — | — | — | — | — | — |
| Public observability | PARTIALLY_IMPLEMENTED | First Observation web checks + unknown codes | checks | — | — | with site reading | WEB_REPRESENTATION checks | search/generative surfaces DESIGNED |
| Currentness (EB-06) | IMPLEMENTED | all | temporal policy | — | — | policy | currentness on evidence | — |

### B. Opportunity families

| Family | Status | Event observed | Primary sources | Mode (adopted) | Normalize once / match many | Jev | Luna/AXENT | Currentness / stop | Gaps |
|---|---|---|---|---|---|---|---|---|---|
| PUBLIC_PROCUREMENT | **IMPLEMENTED** (TED, EU) | call for tender / award | TED (adopted); PLACSP, BOAMP, SAM.gov, USAspending (candidates) | **WORLD_SOURCE_INGESTION** (this branch) + live fallback | records once (index), CPV hierarchy + place + window locally | FIT + DELIVERY screen (spec 062) | material ambiguity only (escalable FIT/DELIVERY) | 60 d open / 365 d awards windows; slice fresh 26 h; incomplete slice fails closed | below-threshold national feeds; US adapter; page-depth limits TO_VERIFY |
| GRANTS_AND_SUBSIDIES | DESIGNED | call / award of funding | EU F&T portal, BDNS (candidates) | world ingestion (designed) | same index contract | eligibility typing | eligibility research | call windows | rights/adapter |
| PUBLIC_INVESTMENT | DESIGNED | budgeted public project | none known | world ingestion | — | requirement relevance | source discovery | — | no source |
| PLANNING_AND_PERMITS | DESIGNED | permit / planning decision | fr-installations-classees (candidate) | world ingestion | — | requirement relevance | — | — | adapter |
| PRIVATE_PROJECT_SIGNALS | DESIGNED | announced private project | none | hybrid | — | relevance | research | — | no source |
| REGULATION_DRIVEN_DEMAND | DESIGNED | regulation creating demand | none | world ingestion | — | regulatory eligibility | synthesis | — | no source |
| BUYER_EXPANSION_SIGNALS | DESIGNED | buyer hiring / facility | none | hybrid | — | relevance | research | — | no source |

Each implemented family keeps: question → routed sources (`RoutingDecision` reasons), POTENTIAL
candidates with source URL, publication time and matched codes, and grounded gaps
(`NO_GOVERNED_DEMAND_SOURCE:<jurisdiction>`, `NO_RELEVANT_DEMAND_FOUND`).

### C. Digital representation (MASTER §54; ADR-0014/0015)

| Family | Status | Instrument / conditions | Mode | Rights | Output | Gaps |
|---|---|---|---|---|---|---|
| Public web representation | **PARTIALLY_IMPLEMENTED** (this branch) | `site-reading.v1`, robots + pages read, time | pull, world-level by origin, zero extra requests | robots honoured; public pages | WEB_REPRESENTATION checks (robots, sitemaps, canonical, noindex, structured data, languages); REPRESENTATION_GAP (POTENTIAL, not causal) | conditional GET (ETag) not in governed transport; no sitemap fetch |
| Search representation | DESIGNED (AXIGNAL's own GSC/CrUX are private first-party, IMPLEMENTED only for axignal.com) | query family × geography × language × device × time | hybrid | provider terms TO_VERIFY | — | no public search instrument |
| Generative representation | DESIGNED | product UI vs API vs grounded mode are different instruments | hybrid | provider terms | — | no instrument |
| Social / public conversation | FUTURE | — | — | not authorized | — | — |
| Public reputation / experience | DESIGNED (policy only) | per platform native scale | pull per review source | not authorized (fail closed) | — | no adapter; ADR-0015 forbids by default |

### D. Economic reasoning families (MASTER §53.7)

| Family | Status | Authority today | Notes |
|---|---|---|---|
| CAPABILITY_DEMAND_ALIGNMENT | IMPLEMENTED | DETERMINISTIC (code containment) + STRUCTURED_EVALUATOR (spec 062 FIT, off by default) | First Observation adds open routing codes; fit stays POTENTIAL |
| GEOGRAPHIC_ECONOMIC_REACH | IMPLEMENTED | DETERMINISTIC (ADR-0089 gate) | attention scopes never enter reach |
| LOGISTICS_FEASIBILITY | IMPLEMENTED (UNRESOLVED/N/A) | DETERMINISTIC | — |
| REGULATORY_ELIGIBILITY | PARTIALLY_IMPLEMENTED | DETERMINISTIC | no stated requirements fed |
| PROCUREMENT_ELIGIBILITY | FUTURE | — | — |
| MARKET_ACCESS_FEASIBILITY | IMPLEMENTED narrow | DETERMINISTIC | — |
| TEMPORAL_ACTIONABILITY | IMPLEMENTED | DETERMINISTIC (dates, windows) | — |
| PROJECT_REQUIREMENT_RELEVANCE | PARTIALLY_IMPLEMENTED | STRUCTURED_EVALUATOR (DELIVERY) | — |
| PATHX_ECONOMIC_COHERENCE | FUTURE | — | — |
| OPPORTUNITY_RESEARCH_PRIORITY | IMPLEMENTED | DETERMINISTIC (`ActionPriority`, First Observation value policy) | ordering, not a score |

## 4. Per-family research attack (First Observation, the family this branch executes)

1. **Target**: what the organization offers, where it is and serves, how it is represented, whether governed demand exists.
2. **Questions**: activity, place, customers, delivery mode, operating site, identity hints, demand.
3. **Information requirements**: a CURRENT reading of its own public website.
4. **Source universe**: its website (robots, homepage, ≤2 high-information pages); adopted demand sources by jurisdiction.
5. **Routing**: unknowns open → page kind most likely to resolve them; demand only for coded capability × scope with an adopted source.
6. **Acquisition**: governed GET (policy-pinned host, size/time/redirect bounds); world index first for demand.
7. **Deterministic**: HTML/JSON-LD parse, lexicon, schema.org types, place coding, web checks, routing.
8. **Semantic typing**: one Jev batch, only the questions whose answer can change the result.
9. **Adaptive investigation**: none here; AXENT stays user-directed.
10. **Completion**: activity and place evidenced, or the open unknowns are grounded.
11. **Stop**: no unknown left that a page can resolve; site request ceiling; research budget 4.
12. **Refresh**: reading reused 7 d; unchanged site backs off 7→14→30 d; unknown activity 7 d; failure 2 d.
13. **Output**: evidence-native discoveries (finding, why, state, source link, basis).
14. **Basis**: exact quote, method, instrument, model + confidence, codes, observed time — persisted, never regenerated.
15. **Economics**: measured requests/bytes/hits per job; Jev USD at vendor-published price; reuse counted (site readings, replayed/indexed source answers, judgment memory hits).
