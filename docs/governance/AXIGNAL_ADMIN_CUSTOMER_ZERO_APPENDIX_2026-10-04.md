# AXIGNAL Admin Appendix — Customer Zero / Self-Observation Reconciliation

**Status:** CANONICAL IMPLEMENTATION APPENDIX  
**Date:** 2026-10-04  
**Applies to:** AO-24A; AXIGNAL Admin UI/UX; FR-30 first-proof runtime  
**Audience:** Codex / UI-UX implementation  
**Authority:** MASTER PRODUCT MODEL → Engineering Constitution → ADRs → AO-24A → this appendix

## 1. Intent

AXIGNAL Admin must serve two distinct functions without mixing their authority:

1. **Operate AXIGNAL** — private administrative and business controls.
2. **Use AXIGNAL** — run the same governed subscriber product on AXIGNAL itself as Customer Zero.

The second function is not a demo, not an admin analytics view, and not a privileged self-inspection shortcut. It is the real product path for the economic subject `org:axignal`.

## 2. Existing runtime to reuse

Customer Zero MUST consume the existing FR-30 runtime contract:

```text
OrganizationId("org:axignal")
Organization("AXIGNAL")

POST /api/xeeds
GET  /api/subscriber-context
```

The governed path already exists:

```text
https://axignal.com/
→ HttpSourceSensor
→ Observation Memory
→ RichSubjectState / Prime
→ Explainable Basis
→ Xignal
→ EvidenceNarrative
→ Today
→ persisted subscriber-safe projection
```

Codex MUST NOT create a second backend, alternate Customer Zero datastore, client-side Xignal generator, duplicate Brain, or a fixture projection for this surface.

## 3. Admin reconciliation model

The Admin information architecture must explicitly separate:

```text
AXIGNAL Admin
├── Operate
│   ├── acquisition
│   ├── accounts/subscriptions
│   ├── finance
│   ├── integrations
│   ├── Brain observatory
│   ├── governance
│   └── system operations
│
└── Use AXIGNAL
    └── Customer Zero
        ├── self-observation status
        ├── plant/reobserve AXIGNAL
        ├── subscriber projection
        ├── Xignals
        ├── Today
        ├── EvidenceNarrative
        ├── currentness
        └── source lineage
```

Private Admin data and economic evidence must remain visually and semantically distinct.

## 4. Required Customer Zero surface

Add a first-class Admin destination named consistently with the product language, for example:

**AXIGNAL / Customer Zero**

The surface must contain:

### A. State header

Runtime-derived values only:

- organization name;
- organization id;
- current Xeed id/label;
- lifecycle status;
- reality level;
- runtime code SHA where already exposed;
- last observation/projection timestamp;
- currentness state.

The organization identity must come from the runtime projection.

### B. No-Xeed state

When `GET /api/subscriber-context` returns `NO_XEED`:

- explain that AXIGNAL has not yet planted its self-observation Xeed;
- expose one governed primary action: **Plant AXIGNAL**;
- call `POST /api/xeeds` with canonical target `https://axignal.com/`;
- do not fabricate preview data while waiting.

### C. Active product projection

Once a projection exists, render the same subscriber-safe semantic payload the product exposes:

- organization;
- Xeed/context;
- Xignals;
- epistemic state;
- currentness;
- uncertainty;
- Today;
- sourceRefs;
- EvidenceNarrative / “How AXIGNAL knows”.

Where practical, reuse the same product components used in subscriber-facing AXIGNAL instead of maintaining an Admin-specific interpretation.

### D. Reobserve / refresh

A reobservation is a new governed run, not an edit.

The UI may expose an explicit reobserve action, but it must call the governed runtime path and preserve history.

No UI control may mutate prior evidence, canonical FAXT, Xignal state, relationship truth or timestamps.

## 5. Required states

The surface must make these states visibly different:

- `NO_XEED`
- loading current projection
- planting
- governed rejection
- `INSUFFICIENT_EVIDENCE`
- runtime/provider failure
- live projection available
- historical/stale projection
- persisted reload

Do not collapse these into a generic spinner or generic “error”.

## 6. Customer Zero is not Admin truth authority

The following are forbidden:

```text
Admin form → economic truth
Admin edit → FAXT
Admin edit → INXIGHT
Admin edit → RELATIONSHIP
Admin edit → Xignal
Admin preference → OBSERVED
```

The Admin can trigger attention and observation. It cannot supply the conclusion.

AXIGNAL observing AXIGNAL has exactly the same epistemic burden as AXIGNAL observing any external company.

## 7. Remove fixture leakage

The Customer Zero data path must not depend on:

- Norte;
- Atlas;
- demo organizations;
- locally fabricated Xignals;
- static subscriber fixtures;
- hand-written “known facts” about AXIGNAL.

Fixtures can remain elsewhere for development/tests, but must not appear in the live Customer Zero path.

## 8. First product-proof session

Customer Zero becomes the canonical initial real-product test harness.

Required first test:

```text
Admin
→ AXIGNAL / Customer Zero
→ GET /api/subscriber-context
→ NO_XEED
→ Plant AXIGNAL
→ POST /api/xeeds
→ target https://axignal.com/
→ governed acquisition
→ at least one observation-backed Xignal
→ inspect EvidenceNarrative
→ inspect currentness and uncertainty
→ inspect Today
→ reload Admin
→ GET /api/subscriber-context
→ same persisted projection
```

The result must be evaluated as product behavior, not merely backend success.

## 9. Browser QA

Codex must validate in a real browser:

- desktop;
- narrow/mobile;
- loading;
- empty state;
- success state;
- rejected target/state;
- insufficient evidence;
- reload continuity;
- navigation Admin ↔ Customer Zero;
- source/evidence expansion;
- responsive layout;
- no fixture leakage;
- no private Admin data leaking into subscriber projection.

Screenshots alone are not sufficient evidence. Interaction and runtime state must be exercised.

## 10. Acceptance gate

AO-24A cannot be marked DONE until all are true:

```text
IMPLEMENTED
+ runtime-wired
+ no fixture path
+ contract tests
+ browser verified
+ real AXIGNAL self-observation executed
+ persisted reload verified
+ EvidenceNarrative inspected
+ no epistemic bypass
```

A rendered card labelled “Customer Zero” is not completion.

## 11. Relationship to AO-25

AO-25 Founder / Frontier Advisor Workbench remains a later, separate capability.

AO-24A must prove that the base AXIGNAL product works for AXIGNAL itself before premium/advisory synthesis is layered on top.

Customer Zero validates the product substrate; AO-25 consumes that governed substrate.
