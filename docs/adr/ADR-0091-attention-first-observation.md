# ADR-0091: Attention starts public observation; identity still only through a registry

- **Status:** Accepted (CTO, 2026-10-09)
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
   rights recorded. The observation may include deterministic extraction, one bounded
   semantic routing judgment over a controlled economic vocabulary (no free page text or
   source URLs to the evaluator; ADR-0090 input rights) and a lookup of adopted public demand sources;
   nothing else. This creates **no Organization, no Focus, no FAXT, no identity
   binding**. Identity still resolves only through a registry record that attests the
   subscriber's signal (ADR-0087 §4). A website declaring an identifier or a legal name is
   an `IDENTITY_HINT`, shown as such, never admitted.
2. **Two levels of state.** The *site reading* (robots decision, pages, fingerprints,
   deterministic extraction) is world-level public observation keyed by website (origin and
   path: two sites hosted on one host never share a reading); its *content* is kept and
   reused across tenants only under governed content rights (§11), otherwise only its
   fingerprints and robots decision are. The *First Proof* (discoveries, demand fit, states, cost) is
   tenant-private operational state keyed by the attention target. Neither is AXIGLAND truth.
3. **Only a registry-recorded website speaks for the Organization.** For a Focus whose
   website a registry records for that Organization (`REGISTRY_VERIFIED`, MASTER §15.3
   "official website") and whose content a governed rights decision lets AXIGNAL retain
   (§11), the reading is appended once per content fingerprint to Observation
   Memory under the canonical Organization id; existing readers, the projection evidence
   check and EB-06 currentness apply unchanged, and the result may hand over to T12. A
   website the subscriber merely directed (`SUBSCRIBER_DIRECTED`) is observed privately:
   nothing is written under the Organization, its First Proof stays tenant-private and is
   labelled as not registry-verified. A website a registry records for a *different*
   Organization is not observed as this one (`WEBSITE_OF_ANOTHER_ORGANIZATION`).
4. **Declared locations may direct attention; only the garden derives reach.** A postal
   address or `areaServed` the organization declares is DECLARED evidence. First Observation
   uses it only to derive POTENTIAL attention scopes (where to look); attention scopes never
   enter the Economic Operating Model. Reach is derived exclusively by ADR-0089's garden from
   the organization's own observations (where a PROVIDER_PREMISES channel may treat premises
   as reach by ADR-0089's rules); spec 059's gate still downgrades unevidenced channel reach
   to `UNRESOLVED_REACH`. When nothing is declared, a place the page text names and a
   judgment confirms among deterministic candidates may also direct attention (POTENTIAL,
   shown as "mentioned on its website", never as declared). Remote or digital delivery
   without a declared area stays UNKNOWN, never "global".
5. **Open capability discovery.** Lexicon, schema.org self-declared types and (when the
   semantic layer is enabled) typed judgments over the public reading produce POTENTIAL
   hypotheses with exact excerpt basis. CPV, NAICS and ISIC codes are routing indexes,
   not the organization's economic reality. Judgments are non-authoritative (ADR-0090): a
   judged classification may choose *where to look* in a tenant-private First Proof (its
   demand stays POTENTIAL and carries its routing method), but it never founds a capability
   on the canonical projection path, is never handed to T12, and the separate source excerpt is shown as
   "source excerpt", not as proof that the evaluator saw the original free text.
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
9. **Authority event streams are ingested once per slice, on demand.** A source that
   publishes events for many organizations (procurement notices first) is read as a world
   slice (source × country × notice kind) only after a Focus question needs that slice
   (MASTER §3.2 demand-materialization), stored once as public records, and matched locally
   for every Focus while fresh and complete. An incomplete or stale slice never answers; the
   live per-query adapter does. The slice never records which tenant or Focus asked.
10. **Families are policies over one substrate.** Family-specific behaviour (questions,
   sources, entry points, stop and refresh rules, check lists, vocabularies) is governed data
   and small ports over the existing routing, budget, lease and currentness engine — not a
   per-family pipeline and not a monolithic researcher (spec 063 `family-architecture.md`).
11. **Content rights, retention and evaluator input are governed, never inferred.** Public
   visibility and robots.txt allow *observing* (fetch under robots, bounded GETs) but are not
   authority to reuse, retain or transmit content (ADR-0015). The authority is a governed
   `SourceRegistryEntry` for the website (rights basis, reuse scope, raw and metadata
   retention), registered by the operator; none exists by default.
   * Without it: the requesting tenant's private observation still runs; raw bodies are
     discarded after the run (a dedicated artifact store), the world-level site record keeps
     only fingerprints and robots, other tenants re-observe instead of reusing content,
     nothing is seeded under the Organization, and nothing is sent to a semantic provider.
   * With it: shared content and seeds follow the entry's retention; the decision is taken
     again at every use, so lost rights or expired retention purge shared content before any
     reuse. Seeds carry the entry's rights, scope, provenance and retention references.
   * Private First Proof citations are kept for at most the entry's raw retention or 30 days
     without one, then removed (`contentExpiredAt`).
   * Evaluator input needs an explicit input-rights decision (ADR-0090 §5). In this
     routing-only slice it receives a bounded projection of developer-controlled economic
     terms and listed places, never original free text, URLs, page titles or names.
     Such a projection is not a complete measure of public comprehension and may omit
     useful context; the future perceptual product must evaluate that limitation separately.
   * Provider confidence is kept in the authorized trace and never shown to subscribers as a
     number (ADR-0047: not a probability of truth).

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
