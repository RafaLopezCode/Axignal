# ADR-0010: AXIGNAL Source Acquisition Architecture

- **Status:** **ACCEPTED** by CTO on 2026-09-25. This accepts the architecture
  boundary only; no production source acquisition implementation is authorized.
- **Date:** 2026-09-25
- **Source doctrine:** MASTER §3, §6, §7, §23, §26, §39, §46;
  Engineering Constitution's evidence, epistemic, security, and provider
  boundary rules.
- **Evidence:** `docs/research/AXIGNAL_SOURCE_ACQUISITION_BAKEOFF.md`;
  `experiments/source-acquisition-bakeoff/results/candidate-runtime/latest-candidate-runtime.json`;
  `experiments/source-acquisition-bakeoff/results/public-web/latest-public-web.json`;
  `experiments/source-acquisition-bakeoff/results/public-web/policy-decisions.json`.

## Context

P0-SOURCE-01B compared five isolated Python acquisition runtimes against a
shared loopback-only fixture. P0-SOURCE-01C then made 11 bounded public GETs
with Scrapy 2.19.0 across Selenium's official site and a W3C WAI test PDF.
The same request/observation shape retained request identity, source and final
URI, timestamps, status, content type, fingerprints, failure state, and a raw
PDF artifact. The public run exercised static documentation, two explicit
same-site pages, a JS test page's initial HTTP response, temporal blog content,
sponsor information, a causally ordered Q1/O1/G1/Q2/O2 loop, an HTTP redirect,
and a 404. This was not a broad crawl.

The public candidate comparison remains incomplete: Scrapling's HTTP API did
not expose a verified streaming response-size cap, and Playwright routing could
not guarantee a hard response-body cap and inspection of every redirect hop.
They were not dispatched. The public run therefore establishes that the
experimental contract and Scrapy path survived these specific public targets;
it does not establish Scrapy's superiority over Scrapling or select a browser
adapter. DNS results were checked before dispatch but not pinned to the
connection; the recorded residual is limited by the exact host/path allowlist
and the nature of this experiment and must be eliminated or explicitly
accepted before a broader trial.

## Decision

AXIGNAL owns the semantics of `SourceRequest` and `SourceObservation`, source
policy, request identity, provenance, and failure semantics. Source policy
executes before acquisition. Raw evidence and its provenance are first-class
outputs of acquisition, which has no canonical truth authority. Third-party
tools may only be replaceable adapters behind this AXIGNAL-owned boundary.

HTTP acquisition and browser rendering are distinct capabilities. Browser
work is requested only when a declared capability need requires it; browser
rendering is not the default. Targeted iterative acquisition is mandatory.
A restricted or denied acquisition is a terminal policy outcome and does not
authorize stealth, anti-bot, or CAPTCHA escalation.

The initial HTTP and browser adapter choices remain `DEFERRED`. P0-SOURCE-01
did not establish a comparative winner: only Scrapy completed the bounded
public-target run, while Scrapling and browser paths were withheld by the
security gate. All candidates remain experimental and replaceable. Adapter
selection may occur during implementation without reopening this ADR unless
the selection changes the accepted architectural boundary. This ADR authorizes
no production dependencies, semantic extraction, evidence admission, or
canonical mutation.

## Alternatives considered

- **Select a single crawler now:** deferred because the public run tested only
  the safety-eligible Scrapy candidate; public comparability with Scrapling is
  incomplete.
- **Treat browser automation as the canonical acquisition contract:** rejected
  because it couples HTTP-only requests to browser cost and lifecycle, while
  omitting crawler and policy semantics. Public browser comparison remains
  open until response and redirect controls cover every request.
- **Let each library define AXIGNAL observations:** rejected because observed
  field and failure differences would leak vendor-specific semantics upward.
- **Defer the ownership boundary itself:** less consistent with the existing
  AXIGNAL evidence and canonical-truth boundaries. This was considered before
  CTO review and was not selected.

## Tradeoffs

AXIGNAL must maintain adapters and validate a stable observation contract.
Separating HTTP and browser capabilities permits targeted composition, but
requires explicit escalation policy, independent resource budgets, and
cross-adapter provenance checks. A replaceable boundary adds integration work
and does not make any candidate safe by itself.

## Consequences

- Candidate package dependencies stay in isolated experiment environments.
- Runtime selection requires a follow-up experiment with an enforceable
  response cap for each HTTP and browser transport, redirect-hop validation,
  and DNS pinning or an equivalent egress boundary. The next trial should
  compare Scrapy and Scrapling on the same policy-approved public workload and
  compare Playwright after the browser boundary satisfies those controls.
- P0-SOURCE-01C selected no initial adapter; browser escalation and the
  always-browser resource delta remain unmeasured on public content.
- Raw fetched content remains untrusted evidence material and cannot itself
  update canonical AXIGLAND state.
- Acceptance records architecture only. It does not supersede the MASTER,
  Constitution, or other accepted ADRs, and it does not establish that a source
  contract, router, provider adapter, or acquisition runtime is implemented.
