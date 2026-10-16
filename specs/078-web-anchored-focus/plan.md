# Plan: web-anchored Focus (spec 078)

## Constitution check

| Gate | Result |
|---|---|
| MASTER precedence | Pass. §22 and §15.3 describe this; the ADR-0087 amendment records it. |
| Truth boundary | Pass. A web subject is attention only. The FAXT firewall makes canonical writes impossible, and the canonical store is untouched (asserted end to end). |
| A website never admits identity | Pass. ADR-0087 item 4 is unchanged; the subject has no legal name. |
| UNKNOWN ≠ FALSE | Pass. Legal predicates stay UNKNOWN (`IDENTITY_NOT_VERIFIED`). |
| Architecture Guard | Pass. The application layer depends on ports; the store lives in `pipeline/`. |

## Architecture review

1. **Domain.**
   - `domain/identity.py` adds `WEB_SUBJECT_PREFIX` and `is_web_subject`.
   - `domain/faxt/model.py` makes `FAXT.create` refuse a web subject. This is the single choke point of canonical state.
2. **Pipeline.** `pipeline/entity_resolution/web_subjects.py` holds:
   - `SqliteWebSubjectStore`: idempotent `ensure(domain)`, `get_organization`, `organization_by_domain`;
   - `CanonicalOrWebSubjects`: a reader that answers `org:web:` ids from the subject store and everything else from the canonical store. A registry website wins.
3. **Application.** `application/organization_admission/web_anchored.py` adds `WebAnchoredResolution`, which wraps the registry resolution port. Only "no registry answered" plus a website is anchored. The portfolio's add, retry and capacity flows are unchanged: they receive an `Organization`.
4. **Wiring.**
   - The subscriber composition uses the wrapper and the composite reader for portfolio, economic, first-observation and display.
   - The enrollment authority and the daily economic runtime read through the composite reader, so the autonomous loop can enroll web-anchored Foci.
5. **Web.** The `IDENTITY_NOT_VERIFIED` copy says that verification is optional and lists what it adds, in six locales.

## Follow-ups (not in this PR)

- A "Verify identity" action: the subscriber gives an LEI or registry id, and the Focus is re-pointed with the existing `replace` flow while keeping its history.
- National registries behind the same port (a CTO choice per country).
