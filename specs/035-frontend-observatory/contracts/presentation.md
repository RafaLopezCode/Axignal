# Governed frontend contracts
## GET /api/projection
Presentation-only illustration endpoint. Known organization/asOf only; unknown input 400. Returns demo projection and mode FIXTURE_ONLY. No backend authority inferred. Future live bridge must retrieve after authorization and map existing projection losslessly; no automatic fixture fallback masquerading as real data.
## POST /api/axent
Same-origin local demonstration. Body contains messages and known context; max 32KB. Unknown organization/date/family/signal or unauthorized signal-context combination returns 400. Stream is AI SDK UI v1; text explicitly grounded in read-only demo, custom data-composition contains validated plan. No provider/model or canonical-write tool.
Client transport binds revision and resets component/thread on context changes; old in-flight responses are aborted and keyed out.
## POST /api/admin/action
Always denies real operation (403 AUTHORITY_REQUIRED). Cannot be granted by browser role/state. UI previews action and owning-service requirement; no mutation, no fake operational success.
## Component registry
Keys signal/evidence/context map to compiled React components. A plan selects refs and hierarchy only. Content/state/time/source are loaded from authorized projection. Reject extra keys, wrong version/revision, unknown/disallowed refs, duplicates or unknown component. Deterministic fallback remains visible.
## Commercial boundary
Pricing describes focus allocation without numbers or invented entitlements. Subscription changes and account/session authority belong to existing operational service.
