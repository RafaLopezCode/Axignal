# P0-SOURCE-01D tasks

- [x] Confirm fit against ADR-0010 and current SourceRequest/SourceObservation boundary.
- [x] Pin reproducible Obscura release asset and checksum.
- [x] Define forbidden stealth/evasion/authenticated-scraping behavior.
- [x] Define adoption, fallback, rejection and rollback gates.
- [x] Define isolated production shape if later approved.
- [ ] Implement isolated Obscura candidate installer/verification script.
- [ ] Implement Obscura experimental adapter.
- [ ] Extend synthetic fixture for browser/resource/SSRF/fallback cases.
- [ ] Implement equivalent Chromium baseline adapter for the new measurements.
- [ ] Run >=5 measured synthetic iterations after warm-up.
- [ ] Validate body/subresource bounds, redirect policy and egress behavior.
- [ ] Approve and run bounded public corpus.
- [ ] Produce machine-readable comparison report.
- [ ] Decide REJECT / EXPERIMENTAL_ONLY / OPTIONAL_FALLBACK / PRIMARY_WITH_CHROMIUM_FALLBACK.
- [ ] If approved, open a separate production implementation slice; do not promote from this experiment directly.
