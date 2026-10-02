# P0-SOURCE-01D — Obscura Browser Provider Bakeoff Result

## Decision

**Obscura v0.2.3 is REJECTED for AXIGNAL production adoption.**

It remains **EXPERIMENTAL_ONLY** as a candidate to re-evaluate when upstream releases close the browser-boundary gaps.

This is not a performance rejection. It is a safety/provenance rejection under the gate defined before execution.

## Reproducibility

Candidate:
- Obscura v0.2.3.
- Windows x86_64 archive SHA-256: `781a1b8bd12b65ec5aba95842e75e6f56b3101d360397506c0e35fe3f78536e8`.
- Linux x86_64 archive SHA-256: `1534d1e6ddaf3d080ec4091eb41d0a4d8cc042a48b607d3c410fc13b482a9eec`.
- Chromium baseline: local Google Chrome controlled through Playwright 1.63.0.
- Five measured iterations after excluded warm-up.
- No stealth, CAPTCHA bypass, anti-bot bypass, authenticated scraping or public private-network access.

The first attempted cold run was discarded because the experimental runner incorrectly passed fractional `--wait 0.2` to a CLI option that accepts integer seconds. That run performed no Obscura network acquisition and is not evidence.

## Semantic recovery

### Cold acquisition

On the 12 neutral semantic workloads:

| Provider | Useful tokens |
| --- | ---: |
| Obscura | 60 / 60 |
| Chromium | 60 / 60 |

Mean cold measurements:

| Provider | Elapsed | Peak RSS | CPU |
| --- | ---: | ---: | ---: |
| Obscura | 95.394 ms | 19,549,935 B | 32.552 ms |
| Chromium | 1,713.031 ms | 583,304,602 B | 2,648.698 ms |

The browser-history sentinel is excluded from semantic recovery because its expected `history.length` value is implementation-context dependent rather than economic evidence.

### Persistent browser session

| Metric | Obscura | Chromium | Obscura/Chromium |
| --- | ---: | ---: | ---: |
| Useful recovery | 59 / 60 | 60 / 60 | 98.33% |
| Mean navigation | 273.277 ms | 209.294 ms | 1.306x |
| Peak RSS | 34,426,880 B | 404,983,808 B | 0.085x |
| CPU | 1,656.25 ms | 17,031.25 ms | 0.097x |

Obscura is therefore not consistently faster once both engines remain warm, but it is dramatically lighter in memory and CPU on this synthetic workload.

The one persistent semantic miss was `BIG_SUBRESOURCE` iteration 5, which timed out at 5 seconds. The preceding four iterations recovered the expected content.

## Safety and provenance

### PASS — default SSRF guard

Without `--allow-private-network`, Obscura rejected loopback before the fixture received any request.

This is useful defense in depth, but AXIGNAL source policy remains authoritative.

### FAIL — response/subresource hard cap

The 1.2 MB JavaScript subresource was fetched completely. Obscura v0.2.3 CLI does not expose the hard byte budget required by `SourceDispatchPolicy.max_response_bytes`.

### FAIL — redirect-hop authority

Obscura can follow redirects, but AXIGNAL cannot interpose its source policy on every browser redirect hop through the evaluated boundary.

### FAIL — required network provenance

`SourceObservation` requires redirect lineage and connected peer IP evidence.

Through Obscura v0.2.3 CDP/Playwright on a redirect:
- final URL was available;
- response status was null;
- redirect chain was empty;
- server address / peer IP was null;
- response headers were null.

Therefore the evaluated adapter cannot produce a valid production `SourceObservation` without an additional governed network boundary.

### FAIL FOR PRODUCTION — synchronous runaway JavaScript

For the synthetic infinite synchronous loop, the parent watchdog terminated Obscura around 6 seconds for a 2-second workload. Chromium returned an explicit failure around 3.3 seconds.

OS/container-level watchdogs remain mandatory even if a future Obscura version is adopted.

### PASS — redirect loop failure

Obscura detected the redirect loop and failed explicitly rather than hanging indefinitely.

## Public corpus

**Not executed.**

The predeclared gate requires the synthetic safety/provenance boundary to pass before any bounded public dispatch. Because hard response limits, redirect-hop policy and required provenance failed, running the public corpus would have violated the experiment contract.

## Interpretation

The economic signal is strong:

- semantic recovery exceeds the 95% threshold;
- memory use is roughly one-twelfth of Chromium in the persistent run;
- CPU use is roughly one-tenth;
- cold-start economics are especially favorable.

However, AXIGNAL prioritizes provenance and bounded acquisition over compute savings.

The correct result is therefore:

```text
production_adoption_v0_2_3 = REJECT
research_status             = EXPERIMENTAL_ONLY
chromium_fallback           = REMAINS CURRENT BROWSER PATH
```

## Re-evaluation trigger

Re-run P0-SOURCE-01D when a newer Obscura release materially changes one or more of:

1. response/subresource byte limiting;
2. CDP redirect/response lineage;
3. server/peer address provenance;
4. per-navigation watchdog behavior;
5. browser network interception sufficient for AXIGNAL redirect-hop policy.

Do not promote a newer release automatically. The Upgrade Gate remains mandatory.


## Repository validation

Final AXIGNAL validation after recording the experiment:
- ruff format/check: PASS;
- mypy strict: PASS;
- Architecture Guard: PASS;
- axignal-governance: PASS;
- git diff --check: PASS;
- full pytest: 883 PASS.

No production runtime, deployment manifest or live source-dispatch configuration was changed by P0-SOURCE-01D.
