# AXIGNAL Source Acquisition Bakeoff (P0-SOURCE-01)

**Status:** EXPERIMENTAL; source architecture decision deferred
**Research date:** 2026-09-25
**Repository base:** `33298cc45dcb5c17c0401272b72df9d5134d3ef9`
**Purpose:** evaluate acquisition capabilities without implementing a product
Source Router, canonical source contract, JEV, Luna, or Python intelligence.

## Executive finding

The documentary review finds a broad capability landscape but does not identify
a production-ready winner. No third-party candidate engine was installed or
runtime-benchmarked in this slice. The reproducible harness measures an
offline, synthetic, loopback fixture adapter only; it proves the experimental
request/observation shape, raw-artifact retention, explicit failures and a
two-request information-gain loop. It must not be read as a comparative engine
performance result.

`SOURCE_ARCHITECTURE_DECISION=DEFERRED`
`CONTRACT_STATUS=EXPERIMENTAL`
`CANDIDATE_ENGINE_RUNTIME_BENCHMARKS=0`

This conclusion preserves the open source-acquisition decision recorded in
Atlas §10–11 and the P0-ARCH-01 gap ledger. This experiment does not change
those product implementation status classifications.

## Authority and boundary

The MASTER is semantic authority; the Engineering Constitution and accepted
ADRs remain binding. ADR-0009's renderer boundary is unrelated and unchanged.
The Atlas treats source acquisition as a replaceable organ. The evidence
ledger/admission boundary remains the only path by which evidence can later
support canonical state. The benchmark adapter returns `SourceObservation`
records only; it cannot produce FAXTs, relationships, or canonical truth.

```text
research question → experimental source request → acquisition observation
                  → explicit gap → targeted follow-up observation
```

Acquisition capability is not permission. A successful HTTP response does not
establish source rights, trustworthiness, currentness, or canonical truth.

## Method and limits

Research used candidate-owned repositories, changelogs, documentation and
pricing/billing pages on 2026-09-25. Feature statements below are documentary
findings, not independent product claims. Candidate license statements concern
the candidate software only; the right to retrieve or reuse a target's content
must be separately established. Marketing comparisons were not treated as
evidence.

The fixture set is repository-authored, synthetic HTML/PDF-like bytes and
contains no copied live-site content. It avoids touching external sites,
access controls, user accounts, cookies or proxies. Thus the harness is
reproducible and lawful as a local contract test, but it is not the requested
live acquisition measurement. Browser rendering, external robots policy,
publisher terms, network throughput, candidate installation footprint and
candidate operational costs remain unmeasured.

### Corpus

The corpus has twelve workload classes (W1–W12): simple company HTML; JS shell;
bounded multi-page crawl; synthetic PDF bytes; table/list page; dated notice;
relationship wording; contradictory source pair; narrow targeted question;
partial observation with follow-up; explicit HTTP 403; and identical-content
reuse/refetch. Every fixture is synthetic and clearly labeled. W2 deliberately
records the static shell; the reference adapter does not execute JavaScript.
W4 exercises raw-byte retention only, not PDF text extraction.

### Measured result

Harness: `experiments/source-acquisition-bakeoff/run_bakeoff.py`
Raw observation JSON: `experiments/source-acquisition-bakeoff/results/latest.json`
Raw fixture bytes: `experiments/source-acquisition-bakeoff/results/artifacts/`
Workload count: 12; iterations: 3; local HTTP requests: 42.
Reference outcomes: 3 explicit 403s, 39 raw artifacts across the repeated
workloads, 51 successful evidence-slot instances, and matching W12 content
fingerprints across refetches. These counts describe only the synthetic
reference run. Loopback latency included a startup/outlier effect and is not a
candidate comparison. CPU and OS are recorded; process-level CPU and peak RSS
were not instrumented. External network bytes and monetary costs are zero/not
applicable for this local fixture run; loopback response body byte counts are
recorded per observation. There is no candidate install-footprint result.

### Evidence-yield definition

Report a vector, not a weighted score:

```text
Y = (S, T, B, R, C)
S = successful required observation slots with source identity and lineage
T = wall-clock seconds for the same bounded request set
B = response bytes received
R = acquisition requests
C = marginal monetary cost for that run, if externally billed
```

Report observation-quality dimensions separately: URL identity, source
identity, retrieval/publication timestamps, HTTP status/headers, raw artifact
reference/hash, adapter/config, redirects, rights metadata, extraction
transform, and failure state. Do not sum unlike cost dimensions using arbitrary
weights. For a decision use a Pareto comparison after rights and provenance
minimums are met. This fixture harness recorded `S`, request count, wall time
and loopback body bytes; the cost component is not applicable.

## Candidate discovery and eligibility

The complete field-level evidence record for every candidate is
[`candidate-evidence.json`](../../experiments/source-acquisition-bakeoff/candidate-evidence.json).
Version means the latest official release/tag found on the research date, not a
pin approved for adoption. Candidate engine benchmark count is zero.

| Candidate | Version found | Eligibility | Role hypothesis | Material limit |
|---|---:|---|---|---|
| Scrapling | 0.4.15 | CONDITIONALLY_ELIGIBLE | HTTP/browser capability; possible specialized fallback | Stealth/anti-bot options must be disabled unless explicitly policy-approved; provenance still needs adapter validation |
| Crawlee Python | 1.10.2 | ELIGIBLE | General crawler/orchestration candidate | Robots are opt-in by default; redirect/SSRF and persistence semantics need independent controls |
| Crawl4AI | 0.9.4 | CONDITIONALLY_ELIGIBLE | Browser/PDF and raw acquisition capability | Recent Docker/API SSRF and trust-boundary fixes; keep model extraction out of acquisition trial |
| Scrapy | 2.19.0 | ELIGIBLE | Mature deterministic HTTP/crawl foundation | No first-party JS browser; one-shot targeted request lifecycle may need an adapter |
| Agent Reach | 1.5.0 | SPECIALIZED_ONLY | Platform-specific public-source connector/router | Backend churn, auth/cookies and upstream tool/ToS surface; not a corporate web crawler |
| ScrapeGraphAI OSS | 2.2.4 | SPECIALIZED_ONLY | Optional model-driven extraction comparison | Semantic extraction/model spend overlaps AXIGNAL stages and is not provenance-grade acquisition by itself |
| Firecrawl self-host | v2.10 release found | CONDITIONALLY_ELIGIBLE | Broad service/API candidate | AGPL-3.0 core needs distribution/deployment legal review; service is operationally substantial |
| Playwright Python | 1.63.0 | ELIGIBLE | Browser capability complement only | No general crawler, robots policy, or source-rights layer |

### Primary-source register

Versions, feature boundaries and risks were checked against candidate-owned
sources: [Scrapling changelog](https://github.com/D4Vinci/Scrapling/blob/main/CHANGELOG.md)
and [repository](https://github.com/MacOS/scrapling);
[Crawlee Python releases](https://github.com/apify/crawlee-python/releases),
[storage](https://crawlee.dev/python/docs/guides/storages), and
[security guidance](https://crawlee.dev/python/docs/next/guides/security-of-web-scraping);
[Crawl4AI changelog](https://github.com/unclecode/crawl4ai/blob/main/CHANGELOG.md),
[license](https://github.com/unclecode/crawl4ai/blob/main/LICENSE), and
[README](https://github.com/unclecode/crawl4ai);
[Scrapy releases](https://github.com/scrapy/scrapy/releases),
[component model](https://docs.scrapy.org/en/latest/topics/concepts.html),
[robots/retry settings](https://docs.scrapy.org/en/latest/topics/settings.html),
and [feed exports](https://docs.scrapy.org/en/master/topics/feed-exports.html);
[Agent Reach releases](https://github.com/Panniantong/Agent-Reach/releases)
and [English README](https://github.com/Panniantong/Agent-Reach/blob/main/docs/README_en.md);
[ScrapeGraphAI releases](https://github.com/ScrapeGraphAI/Scrapegraph-ai/releases)
and [OSS/managed comparison](https://github.com/ScrapeGraphAI/Scrapegraph-ai/blob/main/README.md);
[Firecrawl releases](https://github.com/firecrawl/firecrawl/releases),
[license description](https://github.com/firecrawl/firecrawl),
[billing](https://github.com/firecrawl/firecrawl-docs/blob/main/billing.mdx),
and [pricing](https://www.firecrawl.dev/pricing);
[Playwright Python releases](https://github.com/microsoft/playwright-python/releases)
and [license/package metadata](https://github.com/microsoft/playwright-python/blob/main/pyproject.toml).

These sources establish project-published facts only. Capability fields not
explicitly evidenced in project sources are marked as not verified or
backend-dependent in the candidate JSON; do not treat them as product claims.

Eligibility means “may proceed to a controlled experiment after the stated
conditions,” not “approved for AXIGNAL.” No candidate is INELIGIBLE from this
documentary screen. Firecrawl hosted service is assessed separately from its
AGPL self-hosted code: managed service adds vendor, data-flow and credit
dependency and has not been benchmarked.

## Candidate-specific questions

### Scrapling

Adaptive element matching and browser fetchers may help when page structure
changes or JS is required. Its own project exposes stealth-oriented modes and
anti-bot solving; that increases rights, publisher-policy, fingerprinting and
security risk. Do not make stealth the fallback for a denied request. Raw page
material appears accessible, but stable redirect, timestamp and source lineage
must be verified by an adapter test. It remains a conditional capability
candidate, not a general-engine finding.

### Crawlee Python

Its typed crawler abstractions, request queues, storage clients, HTTP/browser
variants, retries and throttling can support bounded and resumable research.
Named stores persist; default unnamed stores are temporary. These facilities
may be more orchestration than a single targeted question needs. The official
security guide documents robots opt-in defaults and a redirect-intermediate
hop concern; a separate source-policy and egress boundary is mandatory.
Candidate-specific runtime testing is required before calling it the stronger
production foundation.

### Crawl4AI

Its browser, PDF and content-filter capabilities are useful to examine, but
LLM extraction is redundant with AXIGNAL's future deterministic/model stages
and cannot replace raw source lineage. Keep LLM features disabled in any future
acquisition comparison. Its 0.9.4 release is explicitly a security release
covering coordinated Docker/API SSRF and trust-boundary issues. This is a
reason to pin and isolate any future trial, not a conclusion that the project
is unsafe after the fix.

### Scrapy

Scrapy's request/response model, middleware, scheduler, retries, throttling and
raw bodies make it a credible deterministic HTTP candidate. It lacks a
first-party browser, so a JS workload needs a separate browser capability and
adapter. `ROBOTSTXT_OBEY` fallback defaults to false (generated projects enable
it), which must be set explicitly. Its mature crawl lifecycle may make targeted
Q1/Q2 invocations more involved than direct fetch libraries.

### Agent Reach

Its 1.5.0 release describes ordered backend routing across specialized
platforms. This may be useful for public platform sources such as GitHub,
YouTube, Reddit or social channels where separately permitted. Some routes use
local logged-in browser state/cookies or upstream CLI tools; these create
credential, supply-chain, source-terms, and variable-provenance risks. Treat it
as `SPECIALIZED_ONLY`. Never use authenticated accounts in this benchmark.

### ScrapeGraphAI

The OSS Python library and managed API are different deployment/cost choices.
The OSS library supports user-controlled model/provider configurations; the
managed API is a paid service. Natural-language JSON extraction may accelerate
experiments but introduces model cost and a semantic layer before AXIGNAL's
own evidence pipeline. Model-generated fields cannot stand in for raw
artifacts, observation provenance, or canonical FAXTs.

### Firecrawl

The upstream self-hosted core is primarily AGPL-3.0; SDKs and some UI pieces
are MIT. This is not a blanket ban on commercial use, but AGPL obligations
depend on the actual distribution/service arrangement and warrant counsel
review before adoption. Managed Firecrawl is a separate vendor-dependent option
with USD credit billing. Official billing describes 1 credit/page for scrape
and crawl, 1 credit/call for map, 2 credits per 10 search results, plus option
and PDF-page charges; check current plan pricing at purchase time. Managed
question/structured results can involve a vendor model chain and should be
excluded from raw acquisition comparison. Technical breadth alone does not
outweigh legal, provenance and operational questions.

### Playwright

Playwright is a browser automation library, not a crawler or source-policy
system. It is included as a browser reference for W2 and a potential
complement to an HTTP crawler. Network traces and browser event data can
support provenance collection, but AXIGNAL would need to preserve them
explicitly. Browser binaries and sandboxed execution add memory, lifecycle and
security burden.

## Targeted information-gain loop

The harness records a deterministic mock loop:

```text
FIRST_REQUEST       = W10-Q1 → /w10-first
FIRST_OBSERVATION   = raw HTML bytes; status 200; SHA-256 and request lineage
STRUCTURED_GAP      = G1; missing_fields=[complete_address]; based on O1 hash
SECOND_REQUEST      = W10-Q2 → /w10-followup (targeted URL)
SECOND_OBSERVATION  = raw HTML bytes; status 200; new SHA-256 and request lineage
PROVENANCE_CHAIN_PRESERVED = true
```

This proves invocation shape only. It does not implement JEV, Luna, a
Research Planner, a Source Router, or semantic gap detection.

## Rights and source policy

Candidate licenses govern candidate code, not target content. The experiment
uses synthetic repository fixtures and performs no live fetch, so no publisher
permission, robots decision, or content license is inferred. A future policy
layer must evaluate rights/terms and robots policy before dispatch, record the
policy decision and version, and preserve a distinction between
`TECHNICALLY_FETCHABLE` and `POLICY_PERMITTED_TO_FETCH`. A robots allow result
does not itself grant a copyright license, terms permission, or redistribution
right. A 401/403, explicit denial, or challenge is a terminal policy/safety
signal; no stealth/proxy escalation is authorized by this experiment.

Candidate software license screen is preliminary, not legal advice. Before
commercial distribution, audit exact package versions, transitive dependency
licenses, attribution notices and any AGPL service/distribution arrangement.
Source-specific contractual review is required for nontrivial/high-volume
acquisition and retention.

## Minimum future security boundary

Treat all fetched material as untrusted data, never as agent instructions.
Before any live candidate experiment, require: explicit `https`/`http` scheme
allowlist; public-host and DNS validation; revalidation on every redirect and
connection; egress firewall blocking loopback/private/link-local/reserved and
metadata ranges; strict redirect count; compressed and decompressed byte caps;
timeouts/concurrency budgets; content-type and parser isolation; no `file:` or
script URLs; no execution of downloads; browser sandbox with no repository,
credential or host filesystem access; no inherited cookies; robots/rights gate
separate from the fetcher; immutable raw artifact/hash and explicit failure
record; prompt-injection-resistant handling that keeps page content as quoted
data. These are future experiment prerequisites, not a production security
subsystem implemented here.

## Cost model

No prices are invented for local open-source tools. Their fixed costs include
runtime/container capacity, browser images and binaries, storage, outbound
networking, monitoring and operator time. Marginal costs must be measured as
HTTP compute/network/storage; browser CPU/RAM/time; optional proxy; model calls;
and retries. For a managed API, current prices are volatile and usage depends
on options. As of 2026-09-25, Firecrawl's official pricing page showed Hobby
5,000 credits/month at USD 16/month billed annually, with additional-credit
terms shown on that page; official billing documents endpoint credit rates.
These are reference values only, not a recommendation or cost estimate for
AXIGNAL's unknown workload. ScrapeGraphAI's managed API is separately billed;
no stable price suitable for a comparable estimate was collected. Storage
costs depend on retention, artifact size, replication and provider, none of
which are fixed by this experiment.

| Cost component | Current evidence / treatment |
|---|---|
| Fixed infrastructure | Not priced; varies by chosen hosting, crawler topology, and concurrency |
| Marginal HTTP | Local open-source compute/network; measure per workload, no zero-cost assumption |
| Marginal browser | Browser CPU, memory, binary/container and wall time; not measured here |
| Proxy | Not needed for this fixture run; no proxy escalation authorized |
| Model | Zero in the harness; optional extraction creates additional provider cost and semantic coupling |
| Managed API | Firecrawl endpoint credits documented; ScrapeGraphAI managed service billed separately, exact comparable cost not captured |
| Storage | Synthetic artifacts are local; production retention/replication cost unknown |
| Operations | Local tool maintenance, security patching, observability and source-policy support unpriced |

## Evidence / inference / decision / open questions

**Evidence:** official sources document multiple suitable but heterogeneous
HTTP, browser, crawling, platform, model-extraction and managed API
capabilities. The fixture reference retains hashes/artifact paths, source URI,
status/headers, request IDs, retrieval time, adapter identity and explicit
failure. Candidate implementations were not run.

**Inference:** no single reviewed tool's documented feature list proves it
meets AXIGNAL's rights, provenance, safety, targeted iteration and operational
requirements. General HTTP/crawl and browser capabilities are naturally
separable; specialized platforms and model extraction have different risk and
value profiles. A capability-routed portfolio is plausible, but this is not
yet empirically established.

**Decision:** `SOURCE_ARCHITECTURE_DECISION=DEFERRED`;
`SOURCE_CAPABILITY_CONTRACT=EXPERIMENTAL`. No ADR-0010 is created. No specific
engine is selected or production-approved.

**Open questions:** candidate-runtime comparison under common adapters;
actual raw/redirect/provenance retention; browser security/performance; PDF
text extraction; source-specific rights and retention; source policy rules;
robots behavior; state and resume semantics; operational/dependency footprint;
measured CPU/RSS/network; managed API total cost; Firecrawl AGPL applicability;
whether targeted requests are simpler on direct HTTP than crawler frameworks;
and whether specialized platforms are needed at all for the initial product.

## Reproducibility / validation

Run instructions and limits are in the experiment README. The raw result is
recorded separately from this narrative. The harness has five contract tests
covering W1–W12 inventory, observation-only schema, loopback confinement,
failure/artifact handling and iterative provenance.
