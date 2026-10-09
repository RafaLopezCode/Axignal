# 063 — Validation

Branch `feat/first-observation-loop`, base `origin/main` `19018f2`. Everything below ran
locally against the real subscriber composition (identity admission, portfolio,
entitlements, durable jobs, Observation Memory, projection, HTTP facade). Only the network
was replaced: websites, the TED adapter and the System One provider are controlled
stand-ins (`tests/first_observation/harness.py`). No production system was touched, no real
TypeSafe key was used, no Jev, Luna or TED call left this machine.

## Status by phase

| Phase | State |
|---|---|
| IMPLEMENTED | First Observation (spec 063), world demand index, T12 handoff, evidence-native UI |
| TESTED | yes (unit, E2E through the composition, regressions of the adversarial review, frontend) |
| INTEGRATED | no — branch only, PR for CTO review |
| DEPLOYED | no — production unchanged, `AXIGNAL_FIRST_OBSERVATION_ENABLED` absent (= false) |
| VERIFIED E2E | locally, against controlled network; never against live websites, TED or Jev |

## Baseline vs optimized (measured on the harness)

Command: `uv run python -m tests.first_observation.experiments specs/063-first-observation-loop/evidence/experiments.json`.
Counts are measured on the controlled network. Jev tokens are the stand-in's estimate
(3 characters per token), never a measurement of Jev; USD uses the vendor-published
`jev-1.13.0` price on them. TED count includes ingestion pages.

**CURRENT BASELINE (First Observation off = today)**

| Profile | State | First Proof | Evidence-backed | Grounded unknowns | HTTP | TED | Jev calls | Jev tokens (est.) | Luna | Request ms | Job ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A solar installer, Spain | IDENTITY_PENDING | no | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 18.0 | 0.0 |
| B language school, Arkansas | IDENTITY_PENDING | no | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 13.3 | 0.0 |
| C SaaS serving globally | IDENTITY_PENDING | no | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 13.4 | 0.0 |
| D local bakery, France | IDENTITY_PENDING | no | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 12.4 | 0.0 |
| E site without evidence | IDENTITY_PENDING | no | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 15.8 | 0.0 |
| F known canonical organization | CREATED | no | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 38.0 | 0.0 |
| robots.txt forbids | IDENTITY_PENDING | no | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 13.5 | 0.0 |

**OPTIMIZED, content rights registered, semantic layer off**

| Profile | State | First Proof | Evidence-backed | Grounded unknowns | HTTP | TED | Jev calls | Jev tokens (est.) | Luna | Request ms | Job ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A solar installer, Spain | FIRST_PROOF_READY | yes | 8 | 2 | 2 | 2 | 0 | 0 | 0 | 31.8 | 54.1 |
| B language school, Arkansas | NOT_ENOUGH_CAPABILITY_EVIDENCE | no | 3 | 2 | 4 | 0 | 0 | 0 | 0 | 31.8 | 30.1 |
| C SaaS serving globally | FIRST_PROOF_READY | yes | 5 | 3 | 2 | 2 | 0 | 0 | 0 | 33.1 | 51.2 |
| D local bakery, France | FIRST_PROOF_READY | yes | 6 | 3 | 2 | 2 | 0 | 0 | 0 | 28.2 | 59.3 |
| E site without evidence | NOT_ENOUGH_CAPABILITY_EVIDENCE | no | 2 | 2 | 2 | 0 | 0 | 0 | 0 | 28.0 | 25.8 |
| F known canonical organization | FIRST_PROOF_READY | yes | 8 | 1 | 2 | 2 | 0 | 0 | 0 | 43.9 | 92.6 |
| robots.txt forbids | SOURCE_UNAVAILABLE | no | 0 | 2 | 1 | 0 | 0 | 0 | 0 | 31.8 | 24.6 |

**OPTIMIZED, content and input rights registered, semantic layer on (stand-in System One)**

| Profile | State | First Proof | Evidence-backed | Grounded unknowns | HTTP | TED | Jev calls | Jev tokens (est.) | Luna | Request ms | Job ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A solar installer, Spain | FIRST_PROOF_READY | yes | 8 | 2 | 2 | 2 | 0 | 0 | 0 | 27.8 | 71.9 |
| B language school, Arkansas | FIRST_PROOF_READY | yes | 6 | 2 | 4 | 0 | 1 | 1188 | 0 | 28.8 | 33.2 |
| C SaaS serving globally | FIRST_PROOF_READY | yes | 5 | 3 | 2 | 2 | 0 | 0 | 0 | 29.4 | 55.9 |
| D local bakery, France | FIRST_PROOF_READY | yes | 6 | 3 | 2 | 2 | 0 | 0 | 0 | 28.1 | 53.3 |
| E site without evidence | NOT_ENOUGH_CAPABILITY_EVIDENCE | no | 2 | 3 | 2 | 0 | 1 | 540 | 0 | 29.4 | 26.0 |
| F known canonical organization | FIRST_PROOF_READY | yes | 8 | 1 | 2 | 2 | 0 | 0 | 0 | 43.3 | 91.2 |
| robots.txt forbids | SOURCE_UNAVAILABLE | no | 0 | 2 | 1 | 0 | 0 | 0 | 0 | 31.0 | 24.4 |

**OPTIMIZED, no content rights registered (production default), semantic layer configured**

| Profile | State | First Proof | Evidence-backed | Grounded unknowns | HTTP | TED | Jev calls | Jev tokens (est.) | Luna | Request ms | Job ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A solar installer, Spain | FIRST_PROOF_READY | yes | 8 | 2 | 2 | 2 | 0 | 0 | 0 | 28.3 | 54.5 |
| B language school, Arkansas | NOT_ENOUGH_CAPABILITY_EVIDENCE | no | 3 | 2 | 4 | 0 | 0 | 0 | 0 | 28.6 | 27.3 |
| C SaaS serving globally | FIRST_PROOF_READY | yes | 5 | 3 | 2 | 2 | 0 | 0 | 0 | 30.6 | 50.6 |
| D local bakery, France | FIRST_PROOF_READY | yes | 6 | 3 | 2 | 2 | 0 | 0 | 0 | 31.1 | 50.9 |
| E site without evidence | NOT_ENOUGH_CAPABILITY_EVIDENCE | no | 2 | 2 | 2 | 0 | 0 | 0 | 0 | 28.1 | 27.6 |
| F known canonical organization | FIRST_PROOF_READY | yes | 8 | 1 | 2 | 2 | 0 | 0 | 0 | 43.4 | 53.6 |
| robots.txt forbids | SOURCE_UNAVAILABLE | no | 0 | 2 | 1 | 0 | 0 | 0 | 0 | 30.6 | 24.6 |

Reading it:

* Today (baseline) every ordinary locator ends `IDENTITY_PENDING` or `NOT_READY` with zero
  observation: cost 0, value 0. The known Organization (F) gets a Focus and nothing else.
* Optimized, semantic layer off: 4 of 6 profiles reach First Proof deterministically with
  2–4 HTTP requests; the other two end in grounded UNKNOWNs (`ACTIVITY_NOT_ESTABLISHED`,
  robots refusal) instead of silence.
* Optimized, semantic layer on: the Arkansas school becomes First Proof with one System One
  call (1,113 estimated input tokens ≈ USD 0.0000467 at the published price, after input
  minimization to controlled routing vocabulary) and an explicit
  `NO_GOVERNED_DEMAND_SOURCE` for Arkansas; the placeholder site costs one call and is
  identified as not an operating business. Luna: 0 everywhere.
* Production default, no content rights registered: the private observation still reaches
  First Proof for 4 of 6 profiles with the same requests; no content is shared, retained or
  sent to a provider (Jev 0), so the Arkansas school stays at grounded UNKNOWN until the
  operator registers rights for its website.
* Request latency grows by ~10–15 ms (enqueue + capacity check); the observation itself
  runs off the request (job ms column).

## Reuse (measured)

| Step | New HTTP | New TED searches | New TED ingestion pages |
|---|---|---|---|
| Tenant 1, Solaria Norte (Spain) | 2 | 2 | 2 (two demanded slices: open notices, awards) |
| Tenant 2, same website | 0 | 0 | 0 |
| Tenant 3, another Spanish solar company | 2 | 0 | 0 (answered by the world index) |

Semantic judgments: a second tenant asking about the Arkansas school paid 0 provider calls
(4 judgment-memory hits).

## Scale (ESTIMATED model, `experiments.json` → `scale`)

Per-Focus pull vs world-slice ingestion, requests/day: 10 Foci 40 vs 6; 100 Foci 400 vs 12;
1,000 Foci 4,000 vs 120; 10,000 Foci 40,000 vs 162. Inputs (2 capabilities, 1 market, 2
demand questions per Focus, daily cadence; 300 new notices per slice per day, 100 per page)
are assumptions, not TED measurements.

## Adversarial review (three independent reviewers) and outcome

All confirmed findings were fixed and have regression tests
(`tests/first_observation/test_review_regressions.py`):

* Doctrine: subscriber-directed websites were seeded as the Organization's GLOBAL_PUBLIC
  evidence → now only registry-verified websites are seeded; subscriber-directed ones stay
  private; a website registered to another Organization is refused. Judgment-routed
  capabilities no longer reach the projection or T12; their cited text is labelled "text
  judged". Pending demand is no longer deleted by the semantic screen (which could also
  escalate to Luna). Evaluator state is person-free (contact/legal pages excluded, e-mail
  and phone patterns redacted). Proofs are checked against the Focus's current Organization.
  The cost ledger and decisions no longer reach subscribers (cross-tenant side channel).
* Economics/security: per-host reading shared across paths → keyed by origin + path;
  dead targets starved re-checks → `next_due_at` cleared on final failure; slices over the
  page cap never completed → resumable cursor; one tenant could exhaust the daily cap →
  one open job per target and a per-tenant daily cap; broken credential lost the proof →
  semantic failures are skipped; redirects could reach robots-disallowed paths → final URL
  re-checked; robots parsed up to 512 KB; site budget reserves the redirect worst case;
  `requestsAvoided` relabelled ESTIMATED; ledger counts requests actually sent.
* Correctness: job stuck RUNNING after its last attempt → FAILED and visible as
  `OBSERVATION_FAILED`; retries back off; "check again" creates a real new job; UTC
  everywhere; title parsing (svg icons, unclosed title); `UK`/`EL` country codes; quoted
  charsets; ingestion due order; frontend polling re-arms on every read.
* Verified OK by the reviewers: SSRF protection (policy gate pins global addresses, ports
  80/443, same-site redirects, size/time bounds); no TED special-casing in domain semantics;
  world-level stores hold no tenant identifiers.

## CTO review of `3dbf144` and resolution

1. **Linux CI red (`test_parser_and_place_edge_cases`).** Root cause: CPython security
   releases (3.12.15 on CI, 3.13.x, 3.14) parse `<title>`/`<textarea>` as RCDATA, older ones
   do not; an unclosed `<title>` swallowed the whole page on CI only. Fix: `split_rcdata`
   removes both elements before the standard parser runs (an unclosed one ends at the next
   tag), so parsing is identical on every runtime. The regression test is unchanged and
   passes on 3.12.11 and 3.14.7 locally and on CI.
2. **Rights and retention.** Robots and public visibility no longer authorize reuse,
   retention or seeding (ADR-0015). Authority is a governed `SourceRegistryEntry` per website
   (`AXIGNAL_FIRST_OBSERVATION_CONTENT_RIGHTS_FILE`, none by default). Without it: raw bodies
   discarded from a dedicated artifact store, world record keeps fingerprints and robots only,
   no cross-tenant content reuse, no seeds, private citations expire after 30 days. With it:
   seeds carry the entry's rights/scope/provenance/retention; rights are re-decided at every
   use; lost rights or expiry purge shared content before reuse; `purge()` enforces retention
   (worker stage). Tests: unknown rights, lost rights, expiry, body discard, verified website
   without rights (`tests/first_observation/test_rights_and_minimization.py`).
3. **Jev confidence in UI.** Removed from the subscriber view and UI; the basis shows the
   evaluator and "non-authoritative judgment, not a probability of truth"; the original value
   stays in the stored (authorized) trace. Tests: Python public view and frontend `basisRows`.
4. **Evaluator input minimization.** No page text reaches a provider without an explicit
   input-rights decision. With it, state excludes people/contact/legal/team pages and replaces
   e-mails, phones, honorific + name, role + name and capitalized name runs that are neither
   the organization's declared names nor listed places. Test with names, e-mail and phone on an
   about page: none reach the batch; places and the organization's name survive.

## Browser verification

Real Next.js app (`apps/web/experience`) against a QA-only runtime stand-in serving First
Proofs produced by the real Python service. Desktop, tablet (768×1024) and mobile (375×812):
no horizontal overflow; states QUEUED, FIRST_PROOF_READY (with TED evidence link),
NOT_ENOUGH_CAPABILITY_EVIDENCE, SOURCE_UNAVAILABLE; runtime down → "No pudimos leer tu
contexto" → recovery after "Volver a comprobar". All 8 external evidence links open with
`target="_blank" rel="noopener noreferrer"`. "Cómo lo sabe AXIGNAL" shows the persisted basis
(matching codes, place searched, source, buyer, deadline, observed date).

## Gates

| Gate | Result |
|---|---|
| `uv sync --frozen` | OK |
| `uv run ruff format --check .` | 1331 files formatted |
| `uv run ruff check .` | all checks passed |
| `uv run mypy` | no issues, 471 source files |
| `uv run pytest` | 1972 passed, 6 skipped (5 POSIX-only, 1 real-SDK test without the optional group); First Observation suite also on CPython 3.14.7: 35 passed |
| `uv run architecture-guard --root .` | OK, no violations |
| `uv run axignal-governance` | 8/8 PASS (after `graphify update .`) |
| frontend `npm test` / `tsc --noEmit` / `check:i18n` | 147 pass / clean / 0 missing (1482 entries) |

## Not verified / known limits

* No live run against real websites, TED or Jev (requires CTO activation).
* Whether a TED expert query on a CPV division returns descendant codes is TO_VERIFY; the
  world index matches CPV hierarchically, the live adapter and replay exactly.
* TED result ordering during paging is not documented; the resumable cursor tolerates
  duplicates (upsert) but completeness under concurrent publication is TO_VERIFY.
* HTTP conditional requests (ETag/Last-Modified) are not in the governed transport yet.
* US demand sources (SAM.gov, USAspending) are not adapted; the slice contract is ready.
