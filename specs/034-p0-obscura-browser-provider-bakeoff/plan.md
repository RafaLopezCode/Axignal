# P0-SOURCE-01D implementation plan

## Architecture

Introduce no new product-domain dependency. The experiment implements an isolated BrowserAcquisitionProvider adapter shape that maps AXIGNAL-owned requests into AXIGNAL-owned observations.

Target composition:

SourceRequest
→ SourceDispatchPolicy
→ capability classifier
→ HTTP path OR BrowserAcquisitionProvider
→ ObscuraProvider | ChromiumProvider
→ SourceObservation
→ existing ingestion/runtime

Obscura-specific fields never escape the adapter except as instrument/provenance metadata.

## Phase 1 — Reproducible candidate setup

1. Download exact v0.2.3 Linux x86_64 release asset outside the repository.
2. Verify SHA-256 before execution.
3. Record binary version and executable digest in each run.
4. Keep candidate artifacts, browser state and temporary storage outside AXIGNAL production/runtime paths.
5. Keep Playwright/Chromium baseline pinned to the existing experiment version unless a separate baseline-upgrade decision is made.

## Phase 2 — Synthetic contract bakeoff

Reuse and extend the existing P0-SOURCE-01 fixture.

Synthetic execution may permit loopback only inside the experiment.
Run at least five measured iterations after warm-up.

Add cases for:
- subresource JS;
- fetch/XHR discovery;
- runaway synchronous JS;
- redirect-to-private target;
- oversized document;
- oversized subresource;
- network discovery;
- unsupported browser behavior that must trigger deterministic fallback.

## Phase 3 — Browser-boundary safety validation

The experiment is not eligible for public dispatch until it demonstrates:
- pre-dispatch AXIGNAL allowlist enforcement;
- no direct IP literals;
- no private/link-local/metadata egress;
- redirect-hop validation;
- bounded navigation time;
- bounded response/resource capture;
- deterministic process termination;
- no secret/environment leakage;
- raw/rendered artifacts outside AXIGNAL canonical stores.

Built-in Obscura SSRF is defense in depth, not policy authority.

## Phase 4 — Bounded public corpus

Only explicitly approved public host/path targets.
No login, cookies exported from a user browser, CAPTCHA handling, stealth, residential proxies or anti-bot evasion.

Use a small heterogeneous company-site corpus plus standards/reference targets.
Record failures as evidence; do not retry through a less-governed mode.

## Phase 5 — Decision

Produce one machine-readable comparison and one human technical report.

Possible dispositions:
- REJECT;
- EXPERIMENTAL_ONLY;
- OPTIONAL_FALLBACK;
- PRIMARY_WITH_CHROMIUM_FALLBACK.

No automatic promotion to production.

## Production shape if later approved

Dedicated container/service, non-root, no AXIGNAL secrets, no DB mount, no Docker socket, no AXIGLAND storage, strict CPU/RAM/PID limits, internal-only CDP/API exposure with token, explicit egress boundary and pinned version/digest.

Production adapter upgrades must use the Obscura Upgrade Gate defined in quickstart.md.
