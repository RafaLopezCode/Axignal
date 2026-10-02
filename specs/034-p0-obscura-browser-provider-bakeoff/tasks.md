# P0-SOURCE-01D tasks

- [x] Confirm fit against ADR-0010 and current SourceRequest/SourceObservation boundary.
- [x] Pin reproducible Obscura release assets and checksums for Linux and the executed Windows environment.
- [x] Define forbidden stealth/evasion/authenticated-scraping behavior.
- [x] Define adoption, fallback, rejection and rollback gates.
- [x] Define isolated production shape if a later release is approved.
- [x] Implement isolated Obscura candidate installer/verification script.
- [x] Implement Obscura experimental adapter that cannot emit production SourceObservation while provenance blockers remain.
- [x] Extend synthetic fixture for JS, XHR, oversized subresource, SSRF, redirect, runaway and compatibility cases.
- [x] Implement equivalent Chromium/Playwright baseline measurement.
- [x] Run >=5 measured synthetic iterations after warm-up.
- [x] Run persistent-session comparison to separate engine cost from process-start cost.
- [x] Validate body/subresource bounds, redirect policy, SSRF behavior and required provenance.
- [x] Public corpus decision: NOT AUTHORIZED because the mandatory synthetic safety/provenance gate failed; no public requests were dispatched.
- [x] Produce machine-readable comparison report.
- [x] Produce human technical decision report.
- [x] Decide production adoption for v0.2.3: REJECT; research status remains EXPERIMENTAL_ONLY.
- [x] Do not open a production implementation slice for v0.2.3.
- [ ] Re-run the Upgrade Gate when a newer Obscura release materially improves byte limits, redirect/network provenance or watchdog behavior.
