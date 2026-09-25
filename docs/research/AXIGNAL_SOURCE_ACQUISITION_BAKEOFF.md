# AXIGNAL Source Acquisition Bakeoff (P0-SOURCE-01)

**Status:** EXPERIMENTAL evidence; architecture accepted-not-implemented;
engine selection open; runtime not implemented
**Research date:** 2026-09-25
**Repository base:** `33298cc45dcb5c17c0401272b72df9d5134d3ef9`
**Purpose:** evaluate acquisition capabilities without implementing a product
Source Router, canonical source contract, JEV, Luna, or Python intelligence.

## Executive finding

The documentary review and isolated candidate-runtime comparison do not identify
a production-ready winner. Five Python runtimes were measured against the same
offline, synthetic, loopback fixture. The results are comparative observations
for this fixture only, not public-source fitness or production performance.

`SOURCE_ACQUISITION_ARCHITECTURE=ACCEPTED_NOT_IMPLEMENTED`
`SOURCE_ENGINE_SELECTION=OPEN_IMPLEMENTATION_DECISION`
`SOURCE_RUNTIME=NOT_IMPLEMENTED`
`CONTRACT_STATUS=EXPERIMENTAL`
`CANDIDATE_ENGINE_RUNTIME_BENCHMARKS=5`

The deferred finding below records the experiment's conclusion that evidence
did not select an engine. The CTO subsequently accepted the architecture
boundary in ADR-0010 without selecting an adapter or authorizing runtime
implementation. The P0-ARCH-01 gap ledger records those current statuses.
Candidate adapters and this bakeoff harness remain experimental.

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

### DOCUMENTARY EVIDENCE

The preceding capability review records official project documentation, package
versions, licensing and operational questions. It is distinct from runtime
results. Agent Reach and ScrapeGraphAI remain specialized documentary-only
candidates; Firecrawl remains a managed/self-hosted service reference and was
not installed or benchmarked. No credentials, live platform integrations,
managed endpoints, or model extraction were used.

### FIXTURE EVIDENCE

#### CANDIDATE RUNTIME EVIDENCE

The reference harness and candidate matrix ran only against local synthetic
routes bound to `127.0.0.1`. Five measured iterations followed one warmup for
each target/candidate. Python was 3.12.11 on Windows 11 (12 logical CPUs,
17,025,171,456 bytes RAM). Candidate package environments were separately
hash-locked; no runtime dependency was added to the product environment.

| Candidate | W2 external JavaScript | Fixture observations / failures | Aggregate runtime and peak RSS | Fixture findings |
|---|---:|---:|---:|---|
| Scrapling 0.4.15 | 5/5 rendered by DynamicFetcher | 110 / 20 | 30,589.2 ms / 673,509,376 B | HTTP W1 median 1.3 ms; browser W2 median 673.5 ms; followed redirect loop to configured 30-hop bound; oversized response had no adapter cap. |
| Crawlee 1.10.2 | 0/5; browser page creation timed out | 110 / 20 | 95,615.8 ms / 342,659,072 B | HTTP path and PDF raw bytes worked; configured redirect bound surfaced `TooManyRedirects`; 100 ms request deadline did not stop delayed response. |
| Crawl4AI 0.9.4 | 5/5 DOM rendered, but flagged anti-bot | 100 / 100 | 26,446.8 ms / 603,656,192 B | Short synthetic content triggered anti-bot/near-empty classification, including W10; the harness withheld Q2 without a valid Q1 basis. W4 raw PDF bytes unavailable. |
| Scrapy 2.19.0 | Unsupported; raw shell retained | 105 / 20 | 5,067.7 ms / 85,983,232 B | Lowest measured footprint here; sub-millisecond W1 timings round to 0.0 ms. Redirect-loop record did not expose a normalized terminal failure. |
| Playwright 1.63.0 | 5/5 rendered | 105 / 35 | 5,894.3 ms / 517,394,432 B | Always-browser reference, W1 median 19.5 ms; explicit timeout and navigation failures; PDF navigation surfaced a download rather than raw PDF bytes. |

Installed footprint in the isolated Python 3.12.11 environments was:

| Candidate | Distributions | Site-packages bytes | Environment bytes |
|---|---:|---:|---:|
| Scrapling | 22 | 243,770,000 | 244,698,081 |
| Crawlee | 32 | 144,757,588 | 145,590,427 |
| Crawl4AI | 96 | 566,573,633 | 568,358,797 |
| Scrapy | 44 | 52,013,024 | 53,318,910 |
| Playwright | 4 | 112,498,991 | 113,093,765 |

The shared Playwright browser installation used 739,902,209 bytes. Lockfiles
record exact candidate and transitive package hashes. These footprints exclude
source/runtime data outside the isolated Python environments and are not
deployment image sizes.

Totals combine mixed request types, warm/cold process lifecycles, and framework
instrumentation; use per-workload rows for interpretation. They are not a fair
production throughput ranking. Six synthetic failure cases were exercised:
404, delayed timeout, redirect loop, loopback-only simulated forbidden
redirect, oversized response, and malformed body. `file:` was rejected in
preflight without dispatch. Redirect-loop fixture request counts show why a
strict redirect budget and destination revalidation must be enforced above
candidate defaults. The simulated forbidden redirect never connected to an
actual private or external destination.

W3 used an explicit bounded root and child URL pair, not link discovery. W4
checked raw PDF transport only, not PDF text extraction. W5–W9 exercised raw
page acquisition only, not semantic extraction. Robots and rights decisions
were not inferred from local fixtures. Failure normalization and raw artifact
hash/lineage fields are preserved in the timestamped JSON and content-addressed
artifact directory.

### TARGETED INFORMATION-GAIN AND COMPOSITION EVIDENCE

The harness derived G1 from each returned Q1 fingerprint and dispatched Q2 only for a successful Q1 observation. Scrapling, Crawlee, Scrapy, and Playwright each completed five targeted Q1→G1→Q2 iterations with the G1 basis carried into Q2. Crawl4AI returned anti-bot-classified Q1 results in all five iterations, so no Q2 request was issued.
Per-candidate W10 observation totals were:

| Candidate | W10 state | Requests / bytes | Required slots | Median observation time |
|---|---|---:|---:|---:|
| Scrapling | Supported | 10 / 535 B | 10 | 12.817 ms |
| Crawlee | Supported | 10 / 535 B | 10 | 5.442 ms |
| Crawl4AI | Failed (anti-bot classification) | 5 / 435 B | 0 | 252.897 ms |
| Scrapy | Supported | 10 / 535 B | 10 | 0.000 ms (timer resolution) |
| Playwright | Supported | 10 / 535 B | 10 | 18.154 ms |

The harness derived G1 from each returned Q1 fingerprint and dispatched Q2
only for a successful Q1 observation. Scrapling, Crawlee, Scrapy, and Playwright
each completed five targeted Q1→G1→Q2 iterations with the G1 basis carried into
Q2. Crawl4AI returned anti-bot-classified Q1 results in all five iterations,
so no Q2 request was issued. Candidate aggregate request totals were Scrapling
590, Crawlee 131, Crawl4AI 205, Scrapy 108, and Playwright 210, including
W1–W12 and failure fixtures.

The experiment composed Scrapy HTTP with Playwright browser escalation for the
five Q1 requests whose initial HTML lacked the JavaScript-rendered `Widget`:
5/5 escalated only when the declared predicate required it, with the same
request identity and a preserved provenance chain. The observed yield vector
was `S=5, T=28.741 ms median per pair, B=977 bytes, R=16 fixture requests,
C=0, M=374,411,264 B peak RSS, P=2.0625 CPU seconds`. Sequential worker cold
startup was 2,517.450 ms. Here C is local compute cost (not a monetary cost), B
is fixture transfer bytes, and R includes a robots request. These are local
harness measurements, not service-level budgets.

### INFERENCE

The runs demonstrate that distinct HTTP and browser adapters can produce the
same experimental observation shape and can be composed without losing the
request/provenance chain on the tested path. They also show material
candidate-specific differences in JS behavior, timeouts, redirects, response
limits, and resource use. Synthetic loopback evidence cannot settle source
policy, operational fit, reliability on public sites, or a production winner.

### EXPERIMENT-TIME ARCHITECTURE DECISION

`P0_SOURCE_01_EXPERIMENT_CONCLUSION=DEFERRED_ENGINE_SELECTION`
`SOURCE_CONTRACT_STATUS=EXPERIMENTAL`
`SOURCE_BOUNDARY_PROPOSAL=AXIGNAL_OWNED_REPLACEABLE_ADAPTERS`
`ADR-0010_AT_EXPERIMENT_CONCLUSION=PROPOSED`

At the experiment conclusion, ADR-0010 proposed AXIGNAL ownership of
request/observation semantics and policy, with HTTP and browser as separate
replaceable capabilities. That experiment-time status is retained as history;
the CTO later accepted the architecture in ADR-0010 without selecting an
engine. No candidate is production-approved.

### Open questions and next experiment

Before selecting an engine, repair and repeat the Crawlee browser path, measure
explicit deadlines and redirect/egress enforcement, and compare on a CTO-approved
small set of lawfully public representative sources under documented rights,
robots, and retention policy. Include an approved JS page, bounded link
following, PDF bytes and extraction as separate stages, and request/resume
behavior. Keep network egress constrained and verify redirects at every hop.
Resolve candidate-specific installation and transitive license notices before
any product distribution. Do not infer these answers from this fixture.
## Reproducibility / validation

Run instructions and limits are in the experiment README. The raw result is
recorded separately from this narrative. The harness has five contract tests
covering W1–W12 inventory, observation-only schema, loopback confinement,
failure/artifact handling and iterative provenance. The P0-SOURCE-01C exact
target/DNS guard has its own unit tests.

## P0-SOURCE-01C public-web validation (2026-09-25)

This section adds the CTO-authorized public trial without changing the
historical P0-SOURCE-01A/B results above. The target policy manifest was
written before candidate requests. Machine-readable evidence is in
[`latest-public-web.json`](../../experiments/source-acquisition-bakeoff/results/public-web/latest-public-web.json)
and [`policy-decisions.json`](../../experiments/source-acquisition-bakeoff/results/public-web/policy-decisions.json).

### DOCUMENTARY EVIDENCE

- Selenium's official copyright page licenses Selenium-originating website
  documentation under Apache 2.0. Its HTTPS robots file returned `200` with
  `User-agent: *` and no disallow. Its HTTP robots URL returned `301` to the
  HTTPS robots file, which was separately read before any HTTP-origin target
  request. Selenium documents the selected dynamic page as a WebDriver test
  resource where interaction creates content absent before the action.
  Sources: [Selenium copyright and license](https://www.selenium.dev/documentation/about/copyright/),
  [Selenium waiting-strategy test description](https://www.selenium.dev/documentation/en/webdriver/waits/).
- W3C's robots file contains no disallow matching the selected WAI test PDF
  path. WAI's material-use page permits copying complete WAI documents with
  attribution and no modification. Sources: [W3C robots.txt](https://www.w3.org/robots.txt),
  [WAI material-use policy](https://www.w3.org/WAI/about/using-wai-material/).
- httpbin was excluded because its source-policy state was not verified; the
  approved Selenium HTTP-to-HTTPS redirect and one deliberate 404 target
  covered P8.
- Crawlee had no material capability likely to change the P0-SOURCE-01B
  result and was not repeated. Crawl4AI's fixture anti-bot classification and
  unavailable raw PDF remain unresolved. Agent Reach, ScrapeGraphAI, and
  Firecrawl stayed outside this general-engine trial as directed.

### SYNTHETIC FIXTURE EVIDENCE

Historical P0-SOURCE-01A/B outcomes remain as recorded above, including the
five-engine loopback comparison and 5/5 fixture HTTP-to-browser escalations.
They are not reclassified as public-web evidence.

### PUBLIC-WEB EVIDENCE

The trial made **11 bounded Scrapy requests across 9 unique URLs**: one static
Selenium project/license page; two explicitly listed same-site documentation
pages; Selenium's JS test page via HTTP only; one W3C WAI test PDF; Selenium's
dated blog index; its sponsor page; a causally dispatched Q1/O1/G1/Q2/O2 loop;
one HTTP-to-HTTPS redirect response; and one deliberate 404. No discovered-link
traversal ran. Results were 9 HTTP 200 responses, one 301, and one 404. Every
observation records request identity, requested/final URI, retrieval time,
status, headers/content type, body length/hash, adapter, and failure state.
HTML bodies were not mirrored.

The PDF acquisition boundary is separate from PDF extraction. The original
13,264-byte PDF was retained without transformation at
[`3df79d34abbca99308e79cb94461c1893582604d68329a41fd4bec1885e6adb4.pdf`](../../experiments/source-acquisition-bakeoff/results/public-web/artifacts/3df79d34abbca99308e79cb94461c1893582604d68329a41fd4bec1885e6adb4.pdf).
SHA-256 is `3df79d34abbca99308e79cb94461c1893582604d68329a41fd4bec1885e6adb4`,
content type was `application/pdf`, and `EXTRACTION_PERFORMED=NO`. The evidence
record carries the source URL and attribution/policy basis.

The targeted sequence completed as `Q1 → O1 → G1 → Q2 → O2`. Q1 succeeded
with a SHA-256 basis. G1 was experiment-defined: the project/license page did
not answer the targeted sponsor/relationship question. Only then was Q2 sent
to the Selenium sponsor page. The gap-basis hash and both observations are
linked in the JSON. This tests acquisition lineage, not semantic truth or
canonical admission.

P8 recorded the HTTP origin's `301` and `Location` header without automatically
following it, and recorded the deliberate `404` as `failure_state=http_404`.
The requests ran sequentially with Scrapy 2.19.0, one concurrent request, an
8-second timeout, a 256 KiB maximum response size, retries disabled, cookies
and referer middleware disabled, and a clean process environment without
proxy variables, repository credentials, or browser cookies. Each requested
URL was restricted by a host/path allowlist and checked for public DNS answers
immediately before dispatch. Redirects were not followed. Content was treated
as data: no scripts or downloads were executed, no semantic extraction ran,
and no FAXT or canonical mutation was produced. DNS was checked but not pinned
to the candidate connection; this residual is documented in the raw evidence.

The one-pass Scrapy measurement was 86,990,848 bytes peak RSS, 1.828125 CPU
seconds, and two processes. Q2 used a separate worker with 84,541,440 bytes
peak RSS and 1.578125 CPU seconds. Per-page elapsed values are preserved in the
JSON but are single observations, not a latency ranking or service budget.
There were 11 candidate requests; PDF transfer was 13,264 bytes. No external
monetary cost was billed or measured.

Scrapling 0.4.15 was **not dispatched**: its public HTTP Fetcher did not expose
a verified streaming response-size cap in the inspected request interface.
Checking length after full retrieval would not enforce the transfer bound.
Playwright 1.63.0 and Scrapling's browser path were **not dispatched**: the
available route controls did not establish both a hard response-body limit
and validation of every redirect hop. P3 therefore contains only an initial
HTTP observation; its post-interaction DOM was not acquired. Browser
candidates, browser resource cost, and public HTTP-first escalation savings
remain unmeasured.

### INFERENCE

The experimental AXIGNAL-shaped observation carried identity, provenance,
failure state, and the original PDF through this small public workload using
Scrapy. Static and multi-page documentation, temporal material, a relationship
resource, the targeted follow-up, a redirect response, and a 404 produced
explicit observations. P3 proves only that the HTTP path retrieved the test
shell; it does not validate browser-rendered content. No conclusion is drawn
about company truth, source reliability, or the meaning of the sponsor page.

The fixture comparison and public trial do not establish Scrapy as a
comparative winner because Scrapling and browser candidates were withheld by
the safety gate. Scrapy's low synthetic footprint and successful public
handling make it the only HTTP candidate that completed this bounded trial,
not a proven superior provider.

### EXPERIMENT-TIME PROPOSED DECISION (HISTORICAL)

`P0_SOURCE_01C_ENGINE_SELECTION_FINDING=DEFERRED`
`INITIAL_HTTP_ADAPTER=DEFERRED`
`INITIAL_BROWSER_ADAPTER=DEFERRED`
`AXIGNAL_OWNS_SOURCE_CONTRACT=PROPOSED_AT_EXPERIMENT_CONCLUSION`
`CANDIDATE_ADAPTERS=EXPERIMENTAL`
`PRODUCTION_SOURCE_ROUTER=ABSENT`

The following recommendation is retained as written to preserve the experiment
record. CTO acceptance of ADR-0010 supersedes its proposed architecture status;
the recommendation's adapter-selection finding remains current. A follow-up
comparison needs an experiment-local
transport that enforces a hard byte cap for Scrapling and browser responses,
validates every redirect hop and DNS destination, then runs the same
policy-approved target set for Scrapy, Scrapling, and Playwright. Until then,
do not infer public browser-escalation savings or select an initial engine.
Scrapling stealth, anti-bot, and CAPTCHA capabilities remain prohibited as
automatic fallback behavior; a denied request is a terminal policy outcome.
