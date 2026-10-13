# ADR-0098: A recent public archive copy when the live homepage refuses automated reading

**Status:** Proposed (needs CTO acceptance before integration; CTO asked for it on 2026-10-13).
**Date:** 2026-10-14
**Authority:** MASTER §15.4 (UNKNOWN ≠ FALSE), §20 (temporality, currentness), §21 (observability); AGENTS.md (robots.txt respected; no authenticated scraping or anti-bot bypass by default); ADR-0014/0015 (instrument, time and provenance on every observation); roadmap phase A/B.

## Context

In the 8-country golden pass, 9 of 30 large organizations' homepages refused our reader from the production server: HTTP 403 or 5xx, timeouts, anti-bot walls. That happened even though their robots.txt allows reading the homepage. Some of them (Alan, TRUMPF) read fine from elsewhere, so the refusal targets automated or datacenter traffic, not the content. Those organizations then lost their website-based families. The Wikidata and register fallbacks (#240) cover only part of that.

## Decision

1. **Only behind an allowing robots.txt.**
   - The archive is consulted only after the organization's own robots.txt was read **and allows** the homepage, and the live homepage then failed for a reason other than TLS verification.
   - A robots refusal, an unreadable robots.txt (RFC 9309: not allowed) or a TLS failure **never** reach the archive.
   - This is not a way around a site that asks not to be read.
2. **Source:** the Internet Archive (Wayback Machine).
   - Its CDX index (latest HTTP-200 capture), and its availability service when the index is temporarily offline.
   - Raw capture (`id_`), read through the same governed source sensor and policy gate.
3. **Recent and dated.**
   - The capture must be at most **180 days** old.
   - The page is read **as of its capture time**, not as of today.
   - It is cited by its archive URL, and records `archivedAt`, `archivedFrom` and the archive source.
   - The website-presence finding states the limitation: *the live website refused automated reading; this is a public archive copy dated by its capture.*
4. **Homepage only.** No further pages are requested from the origin.
5. **Rights unchanged.** Content retention and provider input follow the organization's site rights exactly as for a live read.

## Consequences

- Organizations whose live site walls off datacenter traffic keep their website-based families: presence, value, own-site signals, markets and activity, at the currentness of the capture. Example: Doctolib from its 13/10 capture.
- Coverage depends on the archive's availability and holdings. The CDX index is intermittently offline, and some sites are not archived recently or at all (TRUMPF, Saint-Gobain). Then the homepage stays UNAVAILABLE, never guessed.
- Changes measured from an archived page compare captures, not live reads. The capture date makes that visible.
