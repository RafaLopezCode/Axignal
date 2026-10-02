# P0-SOURCE-01D — Obscura Browser Provider Bakeoff

## Goal

Determine whether Obscura can become AXIGNAL's primary browser-escalation provider behind the existing provider-neutral source-acquisition boundary, with Chromium/Playwright retained as fallback when required.

This slice authorizes an isolated experiment only. It does not add Obscura to production, does not change canonical truth authority and does not authorize stealth, anti-bot bypass, CAPTCHA bypass or authenticated scraping.

## Authority

- MASTER PRODUCT MODEL.
- Engineering Constitution.
- ADR-0010 Source Acquisition Architecture.
- Existing SourceRequest / SourceObservation contracts.
- Existing PublicSourcePolicyGate and bounded acquisition semantics.

## Core invariants

- HTTP acquisition remains the default when sufficient.
- Browser rendering is capability escalation, not the canonical acquisition path.
- Obscura is a replaceable provider, never an AXIGNAL semantic authority.
- Raw/rendered browser output is untrusted source material.
- CLAIM != WRITE and EvidenceAdmission remain unchanged.
- A denied/restricted target is terminal; it never triggers stealth or evasion.
- Obscura stealth mode is forbidden in this experiment.
- Public trials must not use --allow-private-network.
- Synthetic loopback trials may use private-network access only inside the isolated fixture environment.

## Candidate pin

- Project: h4ckf0r0day/obscura
- License: Apache-2.0
- Candidate release: v0.2.3
- Linux x86_64 asset: obscura-x86_64-linux.tar.gz
- Asset SHA-256: 1534d1e6ddaf3d080ec4091eb41d0a4d8cc042a48b607d3c410fc13b482a9eec

A newer release is not substituted automatically. It must enter through the upgrade gate.

## Required comparison

Obscura vs Playwright/Chromium on the same bounded workload and the same AXIGNAL-owned semantic contract.

Required classes:
1. static HTML;
2. JS-injected business content;
3. React/Next-style hydration;
4. Vue/SPA-style hydration;
5. lazy-loaded content;
6. XHR/fetch-backed structured data;
7. redirect chain;
8. PDF/resource discovery;
9. malformed HTML;
10. 404/403;
11. timeout/hang;
12. oversized response/resource;
13. robots/policy denial;
14. private-IP/metadata SSRF attempts;
15. dynamic network endpoint discovery;
16. browser incompatibility fallback case.

## Mandatory measurements

Per request/provider:
- success/failure state;
- useful observation slots recovered;
- requested and final URI;
- redirect chain;
- connected peer/IP evidence when available;
- raw artifact fingerprint;
- rendered DOM/text/markdown fingerprints when produced;
- network requests/assets;
- elapsed wall time;
- CPU time;
- peak process-tree RSS;
- bytes transferred or bounded proxy equivalent;
- timeout/watchdog activation;
- crash/abort state;
- policy decision and instrument/version identity.

## Adoption gate

Obscura may be proposed as PRIMARY only if all mandatory safety/provenance gates pass and:
- useful economic-observation recovery is >= 95% of Chromium on the eligible corpus;
- provenance completeness is 100% for accepted observations;
- policy/SSRF/redirect/body-boundary tests have zero regressions;
- aggregate peak-RSS + CPU cost is materially lower, with target <= 60% of Chromium on the same corpus;
- known incompatibility cases deterministically fall back rather than silently degrading evidence.

If safety/provenance fails, candidate is REJECTED regardless of performance.
If evidence quality passes but efficiency does not materially improve, candidate remains OPTIONAL/FALLBACK.
If both pass, PRIMARY_WITH_CHROMIUM_FALLBACK may be proposed.

## Non-goals

- Replacing PinnedHttpTransport.
- Replacing AXIGNAL source policy with Obscura policy.
- Using Obscura MCP as production truth authority.
- Using screenshots as canonical evidence.
- Forking or vendoring the Obscura codebase.
- Production deployment.
