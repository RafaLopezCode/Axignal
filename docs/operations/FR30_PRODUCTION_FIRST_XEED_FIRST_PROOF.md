# FR-30 Production E2E ? First Xeed to First Proof

**Status:** IMPLEMENTED_PENDING_PRODUCTION_E2E
**Date:** 2026-10-01

## Product path

FR-30 replaces the synthetic subscriber context for the tested vertical with a governed, persistent first-proof path:

`Plant Xeed -> authorized bootstrap -> real public HTTP observation -> Observation Memory -> deterministic representation/answerability -> OBSERVED representation Xignal -> Today -> focused AXIGLAND -> evidence narrative -> Learning Memory -> reload continuity`.

The first controlled production proof observes AXIGNAL's own public homepage, `https://axignal.com/`. This avoids fabricating a third-party business state while exercising the real production source sensor and persistence.

## Truth boundaries

- The Xeed is private observer context; the Organization remains canonical `org:axignal`.
- The first visible node is a `XIGNAL`, never a FAXT disguised as a Xignal.
- The Xignal is `OBSERVED` only because it binds the exact governed Observation Memory ID.
- The claim is condition-bound: the authorized homepage was reachable and contained visible text at observation time.
- Search, generative, social, reputation and every unobserved surface remain explicit `UNKNOWN`.
- No `EvidenceAdmission` or canonical AXIGLAND write is created by this path.
- The operator-only plant API stays on runtime loopback and is not reverse-proxied publicly before production authentication exists.

## Local production-equivalent evidence

Using the real HTTP sensor against `https://axignal.com/`, the path reached `LIVE`, persisted one governed source observation, emitted one observation-backed representation Xignal, produced Today READY, built an artifact-verified evidence narrative and linked six Learning Memory events.

Chrome E2E verified a fresh runtime from `NO_XEED`: keyboard navigation to Plant Xeed, real plant/observe, Today, keyboard-opened "Show how AXIGNAL knows", exact Observation/Learning/UNKNOWN/source trace, reload continuity, and no demo marker in the live DOM. Mobile smoke at 390x844 had no horizontal overflow and exposed the mobile navigation.

## Production deployment rule

After green merge, deploy the exact canonical main SHA to `/srv/axignal/runtime/releases/<sha>`, add `AXIGNAL_FIRST_PROOF_ALLOWED_HOST=axignal.com` to `/etc/axignal/runtime.env`, restart only `axignal-runtime.service`, and keep nginx public exposure unchanged. Verify through an SSH tunnel to `127.0.0.1:18181`; do not expose `/api/xeeds`, `/api/subscriber-context`, or `/subscriber/` publicly.

FR-30 becomes DONE only after that production-service browser E2E is repeated and the exact production Observation/Learning/Xignal lineage is recorded.
