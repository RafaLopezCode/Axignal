# Plan and architecture review

1. Reproduce request byte-limit bypass and wrong upstream-error classification
   against the current Admin handlers; capture failing regression cases.
2. Introduce one Admin-local bounded text/JSON codec. Reuse it for marketing,
   pilot accounts, customer access, staff capacity and projection migration.
   Keep request errors distinct from upstream errors; retain schema parsing in
   each owning boundary. No authentication or domain-policy refactor.
3. Exercise each affected handler through a local Next HTTP harness with
   controlled in-memory upstream transport; do not issue real mutations.
4. Add a frontend CI job matching the existing production Node 22 image. Run
   all existing checks without filters or weakened gates; document local parity.
5. Validate frontend, full deterministic repository gates, build, legacy response
   compatibility and existing real read path. Refresh AST-only Graphify and
   record convergence with the exact measured results.

Constitution/architecture review: PASS. MASTER §2.1A/§5, Constitution private
scope and evidence invariants, ADR-0056/0058 and existing slice 070 boundaries
remain authoritative. This is bounded transport and deterministic validation
infrastructure, not a new domain/read-model or external service. Graphify was
queried before inspecting the affected dependency paths. No shared subscriber
code, credentials, production writes or runtime source of truth is changed.
