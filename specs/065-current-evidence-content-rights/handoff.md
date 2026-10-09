# Issue 176 — CTO handoff

## Demonstrated cause

On verified origin/main `987ca9168fcad9a8aa12d43f6ec1386d0ca2abab` (merged
PR175), the real observation loop produced and persisted an opportunity with
`capability.excerpt = "Solartec | photovoltaic installation"` and a `whyPotential`
copy. Removing its registered website grant hid First Proof/POU quotations but
the subscriber response still returned both economic copies. The pre-fix
regression failed on that subscriber assertion; AXENT and MCP use the same
economic read. Temporal refresh reused frozen admission rights, not current
content permission. Raw-memory purge alone did not retire the materialized copy.

## Change and preserved authorities

`CurrentContentRights` is an application-owned port. The runtime adapter consults
the existing reloading website-rights policy at the live clock, independent of
the requested historical cut. The shared economic delivery boundary joins exact
observation/source/time lineage (including source-only legacy descriptors via
scoped metadata-only lookup) and withdraws source text in a copy of every
read, including legacy ledgers, economic evidence/narratives and copied
explanations. Authorized independent sources and canonical identity are preserved.
Subscriber, AXENT and Product MCP receive that same read; no screen patch exists.

The same decision governs raw observation reuse by plan construction, publication
and readonly enrollment. The internal First Proof reader now applies live rights
to both First Proof and POU. HTTP responses remain `no-store`; AXENT's corpus and
dependency fingerprints change, invalidating its existing answer-cache key.
Continuity retains normalized dependency fields instead of verbatim material.
Historical checkpoint questions use the same delivery boundary, joined to their
historical dependency lineage; checkpoints themselves remain immutable.

Recorded content retention days are now part of ObservationReuseAuthority's
optional, backwards-readable payload. Delivery and raw purge use the minimum of
the original and current limits; a wider grant cannot prolong an old observation.
Managed legacy observations without their original bound are `UNKNOWN` for text
delivery/reuse and require reobservation. Missing/invalid/deleted grants fail
closed; provider-only revocation does not withdraw independently permitted human
content. A changed rights basis does not reauthorize an old snapshot.

Economic facts, POTENTIAL/UNKNOWN states, admitted canonical identity, source
references, original admission/provenance, timestamps, fingerprints and immutable
output snapshots remain. Physical raw-memory retirement preserves historical
admission/provenance and records inaccessible material; its explicit
`content_removed` envelope cannot carry raw text/artifacts or become reusable
evidence. Text-bearing observation field rows, including conflicting quotation
copies, are removed in that same purge transaction; normalized fields remain.
This also fixes the old post-purge read failure from invalid empty raw content. There is no canonical fact deletion or new truth authority.

Non-live source families retain their existing registry/admission paths; this
slice binds the current managed website grants implicated in issue 176. No
general licence for an unregistered source is introduced.

## Compatibility and scope

Source text is replaced by an explicit unavailable-content message with a
separate `contentAccess` decision. The existing frontend's required nonempty
string contract remains valid; real before/after HTTP DTOs were parsed by its
unchanged Zod schema. No frontend, landing, subscriber Human First experience,
semantic evaluator/provider, cognition routing or Claude worktree was modified.

Touched contracts: ObservationReuseAuthority's optional original retention,
GovernedObservation's explicitly inaccessible retired-content envelope, current
evidence delivery/reuse port. Runtime wiring: subscriber factory/composition,
First Observation reader/purge, readonly enrollment and scheduled runtime.

## Evidence and validation

All source, registry and evaluator inputs in the new regression are **SYNTHETIC**
RFC 2606 fixtures. The actual identity/membership, EvidenceAdmission/registry
admission, canonical organization store, pilot entitlement, jobs, Observation
Memory, economic snapshot stores, AXENT corpus, OAuth consent + PKCE, MCP server
and HTTP request handler execute. This is not a real Google/provider-quality or
production-source claim.

Reproduce with `uv run pytest tests/first_observation/test_economic_live_rights.py -q`.
Coverage: registered admission → economic publication/persistence → web/AXENT/MCP
positive quote → remove original grant → same running composition/session/client
returns no forbidden quote. It verifies lawful fact/provenance/history retention,
the independent demand source, independent organization, cross-tenant rejection,
unchanged immutable snapshots, legacy materialized economic wire/narratives/ledger,
missing metadata, identical words from an independent permitted source, live-clock
expiry under historical cuts, malformed/deleted/zero/shortened/widened grants,
provider-only withdrawal, changed-basis reobservation and physical raw purge.
Additional regressions cover source-only dated/mismatched/missing/undated
lineage, equivalent timezone formats, raw-field/competing-quote retirement and
old/new continuity checkpoints. The pre-fix purge reproduced retained field
quotations against the previous implementation; normalized fields survive the fix.
One regression sends web, AXENT and MCP requests over a real localhost HTTP socket
on an ephemeral port and stops it afterwards. No canonical production was touched.

Validation results are recorded in `validation.md`; final SHA/CI and run links
are attached to the independent PR and CTO delivery.

Compatibility: the database already used the empty raw-content retirement
representation before this PR. Older unpatched readers already reject that
representation and lack the current-rights delivery boundary. This PR makes the
patched reader load an explicitly inaccessible historic envelope; it does not
fabricate retained content/artifacts to support older unsafe readers. CTO
integration must use the patched runtime for this boundary.

## Integration / deployment state

Implemented on `codex/issue-176-current-rights` in its own managed worktree from
the verified canonical base. Not merged, not integrated into main, not deployed,
no cutover and no production feature flag activated. CTO acceptance remains the
integration authority. No reconciliation/rebase of Claude's work was attempted.

## Remaining live-observation activation boundaries

| Area | What remains before that capability is activated |
| --- | --- |
| Security/rights | CTO integration and deployment acceptance, then production-environment smoke of the configured current-rights policy. Existing managed observations without original bounds must be reobserved before textual reuse; absent grants remain closed. This PR proves the issue176 boundary deterministically, not production activation. |
| Source availability | Actual operator-authorized website/registry/demand sources, their rights bases, robots/access, rate limits and current availability must be confirmed. The regression's sites and source ports are synthetic. |
| JEV evaluation | Real replaceable-instrument quality/calibration and separately authorized transmission must be established for semantic interpretation. Synthetic evaluations do not establish quality. The deterministic observation route can abstain without JEV; this is not a prerequisite for every deterministic observation. |
| Subscriber experience | Claude owns the new Human First experience. Existing contract compatibility is verified here; CTO must reconcile/accept the integrated experience and its live observation states after Claude's PR. No competing UX was produced. |
