# AXIGNAL — Obscura Browser Provider Study

## Executive finding

Obscura is a credible candidate for AXIGNAL's browser-escalation provider because it aligns with the provider-neutral boundary already accepted in ADR-0010: AXIGNAL owns source policy, request identity, provenance and observation semantics; browser engines are replaceable mechanisms.

The candidate is interesting primarily for unit economics and network/source discovery, not for stealth.

## Confirmed repository facts

As inspected on 2026-10-02:
- Rust workspace with dedicated DOM, SSRF, networking, browser, JS/V8, render, CDP and MCP crates.
- Apache-2.0 license.
- Native JavaScript via V8.
- CDP compatibility intended for Puppeteer/Playwright clients.
- built-in SSRF guard blocking private/internal targets by default.
- render, screenshot, PDF, network inspection and DOM-to-Markdown capabilities.
- Docker image design is distroless/non-root.
- project explicitly recommends OS/container isolation for hostile pages because V8 executes untrusted JavaScript in process.
- latest release inspected: v0.2.3.
- active main development continues beyond v0.2.3.

## Claims AXIGNAL must independently verify

The project's README reports substantial memory/startup/page-load advantages over Chrome. AXIGNAL treats those as project claims until reproduced on AXIGNAL workloads.

## Known maturity risks

Recent project issues show real Chromium compatibility gaps, including pages that consume CPU until the script deadline, navigation-history differences, loopback Secure-cookie differences and incomplete event behavior. Obscura therefore should not initially become an exclusive browser dependency.

## Proposed role

HTTP remains first choice. Obscura is evaluated for BROWSER_REQUIRED escalation. Chromium/Playwright remains the compatibility fallback.

A high-value secondary use is source-method discovery: a browser pass may reveal stable public JSON/XHR endpoints. AXIGNAL Learning Memory can then retain the observation method and future runs can use cheaper deterministic HTTP acquisition rather than repeatedly invoking a browser.

## Security position

Obscura stealth/anti-detection is not authorized. A denied/restricted target does not justify evasion. Obscura's SSRF guard is defense in depth; AXIGNAL's own source policy remains pre-dispatch authority.

If eventually deployed, Obscura must run outside the AXIGNAL runtime trust boundary in a dedicated constrained service/container with no AXIGLAND/data-store mounts or secrets.

## Decision

Proceed with P0-SOURCE-01D isolated bakeoff. Do not add Obscura to production until the bakeoff demonstrates evidence quality, provenance, egress safety, bounded execution and materially better economics than the Chromium baseline.
