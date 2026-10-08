# ADR-0091: Attention starts public observation; identity still only through a registry

- **Status:** Proposed (CTO review)
- **Date:** 2026-10-08
- **Amends:** ADR-0087 §7 ("no Focus, observation or canonical write happens until identity resolves") — only the word *observation*, narrowly, as below. ADR-0087 §§1–6 and §8 are unchanged.
- **Refines:** spec 058 ("no HQ/address/domain/country inference or default market").
- **Authority:** MASTER §6.1 (perspective is a query), §7.4, §8, §9 (a never-seen company, construcción visible), §15.1, §15.3 (official website → declared products/capabilities; registry → legal identity), §15.4, §31.3, §53; Constitution I, V, VI, VIII, X, XVI, XVII; ADR-0087, ADR-0088, ADR-0089, ADR-0090; spec 063.

## Context

With GLEIF configured exactly as ADR-0087 intended, a subscriber who types a website or a
name — what ordinary subscribers type — is `IDENTITY_SOURCE_UNAVAILABLE` forever, and ADR-0087
§7 then forbids any observation. The product never starts. Separately, nothing in the
subscriber path acquires the first public website observation (T12 needs one to exist), the
website acquirer keys observations by Focus instead of by subject, and markets require an
operator JSON or NUTS-coded schema.org markup that ordinary websites do not publish.

MASTER §15.3 already assigns different authorities per predicate: the official website is
the source for *declared* products and capabilities; a registry is the source for *legal
identity*. ADR-0087 implemented the second; nothing implemented the first for an
unresolved identity.

## Decision

1. **Attention may start public observation before identity resolves.** For a pending
   attention entry whose locator contains a public website, AXIGNAL may observe that
   website: robots honoured, governed HTTP policy limited to that host, bounded budget,
   rights recorded. This creates **no Organization, no Focus, no FAXT, no identity
   binding**. Identity still resolves only through a registry record that attests the
   subscriber's signal (ADR-0087 §4). A website declaring an identifier or a legal name is
   an `IDENTITY_HINT`, shown as such, never admitted.
2. **Two levels of state.** The *site reading* (robots decision, pages, fingerprints,
   deterministic extraction) is world-level public observation keyed by website origin and
   reused by every tenant. The *First Proof* (discoveries, demand fit, states, cost) is
   tenant-private operational state keyed by the attention target. Neither is AXIGLAND truth.
3. **Focus seeds are written under the Organization subject.** For a Focus, the reading is
   appended once per content fingerprint to Observation Memory under the canonical
   Organization id, with `identityLink` `REGISTRY_VERIFIED` (the registry recorded that
   website) or `SUBSCRIBER_DIRECTED` (attention only, shown to the subscriber). Existing
   readers, the projection evidence check and EB-06 currentness apply unchanged.
4. **Declared locations may direct attention, never reach.** A postal address or
   `areaServed` the organization declares is DECLARED operating-reach evidence and may
   derive POTENTIAL attention scopes (where to look). It never becomes OBSERVED reach;
   spec 059's gate still downgrades unevidenced channel reach to `UNRESOLVED_REACH`.
   Remote or digital delivery without a declared area stays UNKNOWN, never "global".
5. **Open capability discovery.** Lexicon, schema.org self-declared types and (when the
   semantic layer is enabled) typed judgments over the public reading produce POTENTIAL
   hypotheses with exact excerpt basis. CPV, NAICS and ISIC codes are routing indexes,
   not the organization's economic reality. Judgments are non-authoritative (ADR-0090).
6. **First Observation is asynchronous and durable.** The HTTP request only validates and
   enqueues. A leased, idempotent, attempt-bounded job runs the cheapest-first cascade
   (spec 063 §4) under a deterministic, versioned value policy that records why each
   optional step ran or was skipped. It is operational prioritization, not a relevance or
   truth score (MASTER §53). The existing daily runtime remains the only scheduler: it
   drains due re-checks; no second scheduler is introduced.
7. **Capacity bounds observation.** Pending targets consume observation only within the
   tenant's current capacity (active + paused Foci + observed pending targets ≤ capacity),
   with per-job and per-day request budgets (MASTER §31.3).
8. **Off by default.** `AXIGNAL_FIRST_OBSERVATION_ENABLED=false` keeps current behaviour.

## Consequences

- An ordinary locator produces visible, evidence-backed First Proof or a grounded UNKNOWN,
  without weakening identity admission.
- Public website work is paid once per origin and reused across tenants and Foci.
- Removing the semantic layer or Luna leaves a deterministic First Proof (lexicon,
  schema.org types, locations, languages, presence); only open activity recall drops.
- New operational stores (site readings, jobs, First Proof) need retention and an
  operator view; they hold public data and tenant-private derived state only.
- Rejected alternatives: admitting a provisional Organization from domain + name (violates
  CLAIM ≠ WRITE and ADR-0087 §4); running First Observation inside the HTTP request
  (latency, retries, abuse); waiting for the daily tick (a day of silence for a new
  subscriber); a hand-maintained attention JSON (operator knowledge in the product path).
