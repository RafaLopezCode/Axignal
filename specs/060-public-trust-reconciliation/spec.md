# Scope — private public-request backend

The latest human coordination instruction overrides the original shared-UX scope.
Claude owns public narrative, navigation, presentation, translations and dashboard.
This branch implements only private CONTACT / PRIVACY_RIGHTS runtime ingress.
No shared frontend or edge wiring is included in this backend PR.

Shared UI work was preserved separately at b20a8a90e88ad13c1c81484c435955f855afbd89,
branch codex/public-trust-shared-ui-review:
SHARED_UI_CONFLICT — DO NOT INTEGRATE BEFORE CLAUDE REVIEW.

Input is service operations, never canonical economic truth. Requirements:
POST validation, exact origin, bounded bodies, durable private receipts, idempotence,
rate limiting, 90-day retention, governed provider-neutral delivery and safe errors.
Categories access/rectification/erasure/restriction/objection/portability/other.
No subscriber entitlement, newsletter consent, economic evidence or legal resolution.
No production deployment or flag change. Runtime delivery absence must be explicit.

After CTO integration of Claude's public UX, rebase onto actual origin/main and inspect
that UX before adding only the remaining functional frontend/edge wiring.
