# T006 — GLEIF registry source decision and operating contract

Date: 2026-10-07. Authority: MASTER §§15.1–15.4, Constitution VI/X/XIV,
ADR-0087; explicit T006 implementation mandate. Provider selection is reviewable
in this PR. Integration and canonical production activation remain CTO actions.

## Decision and alternatives

Use the official GLEIF Global LEI Repository, by exact checksum-valid LEI only.
GLEIF operates the global LEI repository with accredited issuing organizations;
its LEI/LE-RD record attests legal name and LEI, not universal company existence.
This merits REGISTRY authority for those identity predicates, not for capacity,
business relationships, activity, solvency, ownership or website.

| Source | Technical/legal evidence | T006 decision |
|---|---|---|
| GLEIF | Public production JSON:API, point LEI lookup, LEI/LE-RD under CC0 | First provider; global **LEI-holder** coverage only |
| Spanish Registro Mercantil / Registradores | Human paid information access exists; API Mercantil is evidenced in bilateral agreements, not an open reuse grant; Registradores prohibits incorporating received information in a database for commercialization | No scraping or presumed API/redistribution rights; separate authorized agreement needed |
| Official BOE/BORME | Reusable daily publication API, dated legal acts; signed PDF is authentic publication | Useful future evidence source, but not a bounded exact current-identity lookup; no event-history reconstruction in T006 |
| Commercial/search aggregators | Not the legal register; no justified registry authority in this slice | Excluded |

Primary sources inspected on 2026-10-07:

- [GLEIF API](https://www.gleif.org/en/lei-data/gleif-api),
  [documentation](https://api.gleif.org/docs),
  [LEI data terms](https://www.gleif.org/en/meta/lei-data-terms-of-use).
- [Registradores mercantile information](https://sede.registradores.org/site/mercantil?lang=es_ES),
  [commercial reuse restriction](https://www.registradores.org/-/%C2%BFesta-permitido-comerciar-con-la-informacio-n-registral-obtenida-),
  [API Mercantil agreement example](https://www.boe.es/boe/dias/2024/11/28/pdfs/BOE-A-2024-24833.pdf).
- [BOE BORME FAQ](https://www.boe.es/datosabiertos/faq/borme.php),
  [official daily-summary API](https://www.boe.es/datosabiertos/api/api.php?lang=es).

GLEIF terms II permit point lookup/download and provide LEI/LE-RD under CC0-1.0:
fetching, extracted facts, immutable response snapshots and reuse/redistribution
of these data are permitted. CC0 has no mandatory attribution, but AXIGNAL retains
provider, source URL and rights basis. Do not use GLEIF trademarks/logos without
permission, claim proprietary rights over its data, imply endorsement, bypass
technical restrictions or claim GLEIF guarantees correctness/currentness. No key
or credentials are required. This selection does not authorize bulk harvesting.
The official pages inspected did not establish a numeric API quota: it remains
UNKNOWN; do not present third-party “60/minute” claims as an official guarantee.
AXIGNAL's stricter local rolling limits are **30/minute and 500/24 hours**, shared
across workers in one operational SQLite store. A provider 429 stops without retry.

## Composition, network and claims

`tools/runtime/organization_registry.py` composes
`pipeline/entity_resolution/gleif_registry.py` behind the unchanged
`RegistryIdentitySource`. Subscriber settings must explicitly contain both:

```text
AXIGNAL_ORGANIZATION_REGISTRY_PROVIDER=gleif
AXIGNAL_ORGANIZATION_REGISTRY_RIGHTS=https://www.gleif.org/en/meta/lei-data-terms-of-use
```

These keys work through the existing server-owned subscriber configuration file
or declared environment overrides. Missing provider/rights, unknown provider or
unusable local prerequisites compose `UnavailableRegistrySource`; no login/runtime
crash or invented identity. Default configuration performs no registry HTTP work.
An explicitly injected source retains precedence for deterministic tests.

Allowlist: **api.gleif.org**, HTTPS 443, `/api/v1/lei-records/<LEI>`.
Reuse `PublicSourcePolicyGate`, `PinnedHttpTransport`, `HttpSourceSensor` and CAS:
public pinned DNS addresses, verified TLS, 5-second dispatch deadline, 256 KiB raw
response, identity encoding, no redirects/pagination/application retries. The
existing transport may try validated addresses within that deadline. DNS policy
is reused as-is; no new arbitrary egress client or provider SDK. Compressed bodies
are never decompressed; unsupported/malformed bytes fail parsing.

One exact GET may return FOUND with one record. Legal-name and website searches
are unsupported and return UNAVAILABLE (coverage UNKNOWN), with zero dispatch.
A combined LEI+website cannot be attested and is also withheld. No official website
is produced. A JSON:API 404 error for this exact endpoint is NOT_FOUND **within
LEI coverage**, never global nonexistence; malformed/empty 404 is UNAVAILABLE.
Timeout, 429/5xx, TLS/DNS/policy failures, malformed/duplicate JSON keys, wrong
identifier/type, mixed/list subjects, invalid name, INACTIVE/LAPSED or expired/
future registration dates are UNAVAILABLE and keep identity pending.

Deterministic extraction copies only `attributes.lei` and
`attributes.entity.legalName.name` into a versioned text representation. Both
`data.id` and `attributes.lei` must equal the requested LEI. No fuzzy match, first
result, generated value or model. The existing registry-record builder supplies
unique proposition spans; spans are rebound to the final provenance fingerprint.
Raw JSON, sensor observation, provider/rights/query/parser/time metadata and field
representation are retained content-addressed. Raw JSON and metadata are direct
representation integrity references, checked again by canonical admission/store.
The adapter never writes a canonical Organization. EvidenceAdmission and the
existing admission service still own subject binding, decisions and writes.

## Reuse, limits and observability

`gleif-registry.sqlite3` is operational only: shared attempt counters and successful
response references. Cache keys include LEI, provider-specific store, parser, rights
and observation time. Reuse lasts at most one hour and never beyond next renewal;
every reuse rechecks CAS integrity, metadata and current registration dates. Expired
cache rows are pruned. NOT_FOUND/UNAVAILABLE are not cached as durable truth.
Canonical identity reuse remains the existing admitted-index contract; this source
does not add an active-business assertion or perpetual currentness guarantee.
Observation timestamps survive admission; continuous canonical reevaluation is
not silently redesigned here.

One subscriber resolution performs zero/one source request. No shared request
coalescer is added: concurrent misses may fetch twice, but canonical uniqueness
and tenant-private Foci remain the existing service/store responsibilities.
Logs contain provider, lookup type, outcome, latency, HTTP category, record count
and parser only; never identifiers, subscriber scope, payload or exception text.

## Evidence and handoff boundary

Recorded public response fixture: LEI `5493001KJTIIGC8Y1R12`, Bloomberg Finance L.P.,
retrieved 2026-10-07 via this governed adapter. Raw GLEIF LEI/LE-RD is CC0; the
fixture is static, and CI never needs GLEIF connectivity. Offline tests exercise
the real transport seam/sensor/parser through Principal→Tenant→PilotGrant→
admission→canonical Organization→Focus, failures, corruption and two concurrent
Tenants. Production-settings selection is tested without injecting a source.
Name ambiguity remains tested at the unchanged admission layer; a point LEI
endpoint cannot validly return several records, so lists are schema errors rather
than first-match candidates.

Live smoke is separate from deterministic gates: exact known LEI, HTTP 200,
FOUND/one parsed record; **no canonical writes**. Candidate preflight and exact
SHA/gate totals are recorded in the PR. No canonical production mounts, unit
changes, scheduler activation, `current`/`DEPLOYED_SHA` changes, merge or cutover.
