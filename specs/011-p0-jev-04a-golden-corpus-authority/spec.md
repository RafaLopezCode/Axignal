# P0-JEV-04A — Golden Corpus Authority

**Status:** Research complete; no corpus admitted.
**Base:** `31045a233baf26884bed38facff7199ff8abf5ba`
**Question:** Can AXIGNAL acquire or construct an adequately natural, independent, reusable, temporally traceable and epistemically valid business corpus for `CES.SUPPORT.vNext.2`; if not, is there a defensible procedural benchmark with explicitly limited conclusions?

## Scope and precedence

This is a documentary research and governance slice. It does not evaluate Jev, create cases, establish live eligibility, conduct human annotation, preregister an experiment, download bulk data, contact a provider, access credentials, or change runtime, contracts, grammar, product, or production. Authority follows the Master Product Model, Constitution, ADR-0011, the current vNext.2 decision contract, the evaluation methodology, then this authority specification. The historical vNext.1 contract and preserved P0-JEV-04 preparation are immutable inputs.

The three routes are distinct: (A) an existing natural business corpus with independently established labels; (B) pre-existing natural claims and evidence with future independent human adjudication; (C) a deterministic procedural business benchmark from authoritative structured source data. Route C can only support controlled semantic-relation claims.

## Hard requirements

1. A case must record claim, evidence and gold provenance separately. A source assertion used both to render a claim/evidence relation and determine its expected class is circular procedural authority, never independent natural gold.
2. Every source must pass source-specific rights, commercial-reuse, privacy, provider-transmission and provenance gates. Public availability does not establish reusable rights. Any non-clear or legally ambiguous gate fails closed.
3. No model may create, rewrite, filter semantically, label, adjudicate or estimate difficulty of cases. Discovery is not gold authority.
4. Natural and procedural strata must never be pooled without explicit reporting. Missing answer classes remain missing; no class is fabricated for balance.
5. Future data must retain source revision, retrieval, publication and valid-time fields where available, plus as-of time when material.
6. Development and held-out separation must account for organization, document, source family, claim family, event, time, near duplicates and (for procedural cases) template family.
7. Personal data is unnecessary. Exclude records that cannot be deterministically reduced to legal-entity-only content without identifiable persons or sensitive data.

## Acceptance gates and decision

The route-specific hard gates are machine-readable in `corpus-candidates.json` and operationalized in `contracts/rights-gate.md`. Natural acceptance requires all natural-route gates, plausible non-fabricated yield (preferably 80 total / 40 held out; minimum 60 / 30), and a frozen independent-human protocol. Procedural acceptance requires real business source data, clear rights including future provider transmission, deterministic versioned transformation and independent deterministic expected-class derivation, leakage tests and explicit limitations.

Research identifies a plausible natural Route B candidate based on company-authored SEC filings plus genuinely final contested SEC findings, with future independent human adjudication. It is not accepted: no bounded sample-yield audit was performed and TypeSafe transmission permission remains unknown under the reviewed terms. GLEIF Level 2 is a plausible procedural source with explicit CC0 terms and large published record counts, but TypeSafe transmission remains unknown and same-record labels would be circular. Therefore neither route passes every hard gate.

**Decision:** `BLOCKED_NO_VALID_CORPUS`. This is not a finding that sources are unavailable; it is a fail-closed acceptance decision because a required future-provider-transmission gate is not unambiguously clear and other feasibility gates are not yet empirically established. No live experiment is authorized. `P0_JEV_04_LIVE_ELIGIBLE=NO`.

## Non-goals

No source sample is admitted; no corpus record, label or preregistration is created; no code, dependency, service, grammar, decision contract, runtime, product or production change is in scope. Do not start P0-JEV-04 or another slice under this decision.
