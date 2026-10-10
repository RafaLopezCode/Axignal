# Implementation Plan
Python 3.12 stdlib SQLite/HTTP; existing Next/React/Zod. No dependencies.
## Constitution Check
PASS: MASTER §2.1A internal supplier operations, §5 epistemic firewall;
ADR-0056 Admin plane, ADR-0085 fixed pilot, ADR-0092 independent step-up.
## Architecture review
Graphify query located pilot, AO-09 and AO-01; source confirms contracts.
Extend existing pilot service/storage, additive migration and atomic private
audit/idempotency. Runtime authenticates before access. Next same-origin proxy
binds PRIMARY and STEP_UP identity on each write, dedicated cookie path.
Customer reads join existing membership, portfolio, billing, AO-09 authorities.
## Design brief
EXTEND incumbent customers surface with Invitations, Accounts, Operations.
Compact form, one-time link, explicit revoke confirmation, known lifecycle
text and honest unavailable state. Operational data is private, not economic
knowledge. Incumbent typography/tokens; desktop/mobile keyboard continuity.
## Validation/rollout
Store/security/HTTP tests and #200 integration; web types/tests/i18n; browser
desktop/mobile; full gates; Graphify AST update. Additive schema preserves old
records. Rollback binaries with pilot writes disabled; backup/restore and live
Google/account participation must be verified before production rollout.
