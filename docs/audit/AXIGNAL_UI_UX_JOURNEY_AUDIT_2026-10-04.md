# AO-24A — UI/UX and navigation journey audit

CURRENT_TASK = AO-24A

Date: 2026-10-04. Mode: PRESERVE. Scope: actual localhost Admin,
Customer Zero, shared runtime subscriber surface, account entry and 404 recovery.
This is an evidence-based implementation audit, not representative-user validation
or a claim that the commercial application is complete.

## Decision

The observation-backed reading is usable. The complete account-to-multiple-focus
journey is not implemented. A polished single-focus runtime must not be reported
as a completed subscriber product. Customer Zero is internal Admin use without
checkout/payment; internal observation authority remains separate from economic
evidence authority. The Admin must not be sent through the commercial purchase
journey to use its own product.

## Questions from both roles

| Human question | Subscriber | Admin / Customer Zero |
| --- | --- | --- |
| I chose one organization during onboarding. How do I add another? | No supported persistent multi-focus journey currently exists. | No supported internal multi-focus journey currently exists either. |
| Must I pay to use it? | Commercial entitlement must come from account authority; it is absent from this projection. | Internal use must not require checkout or payment. |
| What can my account observe? | Visible organization count is not plan capacity. | Service-issued internal authorization, not a browser role or payment, governs additional attention. |
| Can I switch without carrying another organization's conversation/evidence? | Requires authorized tenant/focus inventory and context invalidation. Not proven by a one-focus selector. | The same requirement applies; private operational data cannot become product evidence. |
| How do I know this is real rather than a demo? | Runtime reading and evidence must be clearly distinguished from illustrative routes. | Subscriber view must always open the real shared renderer. |
| How do I get back? | Shared in-product back/forward, explicit return and keyboard dismissal. | Retained Admin navigation; returning to Customer Zero preserves the selected signal. |
| What changed, and what remains unknown? | EvidenceNarrative/currentness/uncertainty, without fabricated historical events. | Exactly the same reading and uncertainty. |

## Findings and disposition

### P0 — Missing organization addition and persisted account inventory: OPEN

The real organization selector exposes only the organization in the authorized
subscriber-safe projection. FR-30 `first_proof.py` admits the allowlisted AXIGNAL
public target only. `service.py` supplies the persisted current projection under
Customer Zero authority; it does not expose a subscriber organization inventory,
capacity or general organization-add command. Public identity providers are
prepared/unavailable; the local account entry expressly does not create sessions.

Root cause: the vertical first-proof runtime is narrower than the complete
subscriber journey, not simply a missing button. Reusing POST /api/xeeds with
arbitrary domains or treating frontend organization choices as authority would
violate the existing contract. No second backend or fixture-based path was added.

The UI now exposes the missing capability with a disabled, explained Add
organization control and a reversible return. This improves comprehension;
**it does not complete organization addition**.

Required governed completion slice:

1. Server-authorized persistent tenant/focus inventory, canonical identity
   resolution and duplicate/ambiguous identity handling.
2. Subscriber account entitlement or separate internal Admin attention grant.
   Admin internal grant requires no commercial checkout. Internal authorization
   does not relax evidence admission, rights, source safety or currentness.
3. Post-onboarding Add organization reachable even with only one focus; show
   scope and any commercial consequences before an external customer's charge.
4. Governed acquisition, insufficient evidence, rejection and retry states.
   No client-built Xignals, profile editing or false success.
5. Focus switch, AXENT request invalidation, evidence and private-context isolation;
   persistence and reload; interruption/resumption with no repeated charge or plant.

### P1 — Admin subscriber link changed meaning by current section: FIXED

Before: Customer Zero linked to /panorama/live, while operating sections linked
to fixture /panorama under the same Subscriber view label. Observed from Accounts
and subscriptions, this silently changed from actual product to illustrative data.
After: all Admin sections link to /panorama/live. Public, explicitly labeled demo
links remain illustrative. Regression test covers the operational entry as well.

### P2 — Organization dialog expressed a contract dead end: FIXED IN PRESENTATION

Before: one focus and technical wording about the contract, with no answer about
adding another. After: Your organizations, real payload identity, explicit return,
explained unavailable addition, no inferred 1/1 plan, separate internal no-payment
copy. Shared component retains one product renderer; no second header/sidebar.
Mobile close target extended to 44px; add/return targets exceed 44px.

### P2 — Mixed-language runtime meaning and raw currentness: OPEN

Spanish chrome displays English persisted narrative and CURRENT. Frontend cannot
translate or invent canonical narrative. A governed localized human reading
contract and presentation labels preserving temporal state need a focused slice.
Technical IDs remain expandable, but source/currentness comprehension warrants
representative-user testing. No claim of full accessibility conformance is made.

### Functional boundary — Operational Admin is illustrative: OPEN / DISCLOSED

Accounts and subscriptions explicitly shows private illustrative read models and
no real privileged operations. This is not a working commercial account editor.
The review did not change operational authority or convert private data to FAXTs.

## Browser evidence and performed interactions

Evidence directory: `apps/web/experience/qa/037-customer-zero/journey-audit/`.
Screenshots accompany actual clicks, route transitions and DOM measurements;
screenshots alone are not the E2E proof.

1. Admin Customer Zero → organization selector: observed only current focus
   (`02-organizations-before.png`).
2. Today → actual signal → How AXIGNAL knows: inspected narrative, official
   public source https://axignal.com/, uncertainty and currentness
   (`03-today.png`, `04-evidence.png`). Escape returned keyboard focus to opener.
3. Expand Operate AXIGNAL → Accounts and subscriptions → Customer Zero:
   private illustrative state disclosed; selected real signal retained on return
   (`05-admin-accounts.png`). Before repair, subscriber href pointed to demo.
4. /login: access unavailable explicitly disclosed, demo link explicitly labeled
   (`06-login.png`). No provider login, account creation or checkout was executed.
5. Updated Admin organization dialog at 1280px (`07-organizations-admin-after.png`):
   internal no-payment explanation, actual payload name, no fake addition.
6. 390×844 viewport: Admin menu → organization selector → Escape; dialog width
   370px within viewport390, document scrollWidth390, no horizontal overflow,
   return focus to mobile navigation (`08-organizations-mobile.png`).
7. Missing route → branded 404 → Open notebook → /knowledge. Main skip target
   exists, no horizontal overflow at390 (`09-recovery-mobile.png`).
8. Shared subscriber /panorama/live, organization explanation and reload verified
   against the same persisted observation (see final QA completion below).

No fresh planting/reobservation was performed for this audit. Existing persisted
Xignal `xignal:90740fa6582e8e841c93f619180d89e7`, observed 4 October2026 at15:41:26
Europe/Madrid, was inspected. Only the public homepage is established; other
surfaces remain UNKNOWN. No multi-organization behavior can be verified against
the current contract. Full authentication, checkout, production, session expiry
and multi-tenant switch journeys remain outside verified browser coverage.

## Integration boundary

Changes are on canonical main. Preserve concurrent valid main updates. Required
gates and browser results are recorded at completion; material visual acceptance
still belongs to the human under the Design Director skill. AO-24A is not marked
DONE by this audit, and multi-organization readiness is not declared.

## Final validation

- `uv sync --frozen`: passed.
- Ruff format/check, mypy (258 source files), Architecture Guard: passed.
- `uv run pytest`: 1035 passed in140.05s. Initial execution hit inaccessible
  Windows temp storage; repeated using TEMP/TMP under D:/AXIGNAL. One intervening
  run had a transient AO-15 HTTP failure; isolated test and final full run passed.
- `uv run axignal-governance`: all8 checks passed. An intervening hygiene check
  reported a generated mypy cache, absent on final checks; no gate was weakened.
- Frontend: 36 tests passed, typecheck passed, build35 routes passed,
  locale inventory988 entries with no missing translations. No lint script exists.
- Graphify AST-only update completed; no LLM labeling or network dependency added.
- Subscriber organization dialog contains no internal free-use grant;
  `10-organizations-subscriber.png` shows unknown commercial capacity.
- Actual subscriber signal ID before/after browser reload was identical:
  `xignal:90740fa6582e8e841c93f619180d89e7`; runtime main contained no Norte/Atlas.
  Reading selection resets to Panorama on full reload; economic projection persists.
- Browser 404 mobile reached /knowledge through the visible recovery control;
  main#main exists and document width equals viewport390.

Status: audit completed and bounded repairs validated; P0 multiple-organization
journey and representative-user/visual acceptance remain open. This is not a
production deployment or an assertion that the account onboarding premise works.

## Follow-up implementation: persistent internal attention

The above audit describes the pre-extension finding. Human authorization then
requested runtime implementation, with no second real organization now.
The internal Admin portion of P0 is implemented for already-canonical authorized
targets: persisted inventory, add/select/reobserve, duplicate handling, unresolved
identity, failure/insufficiency and Axent scope isolation. No checkout is used.
Controlled browser QA and runtime restart are recorded in
specs/037-admin-customer-zero/organizations-validation.md.

The complete external account/onboarding journey remains OPEN. Internal Admin
authority is not commercial entitlement; unknown identities cannot be admitted
merely by typing a name/domain. The former disabled-button repair is superseded
by the functional shared dialog. Human visual acceptance remains pending.
