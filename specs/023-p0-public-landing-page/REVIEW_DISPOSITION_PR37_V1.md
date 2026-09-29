# PR #37 — Independent Review Disposition V1

**Reviewer input:** independent Codex read-only review of HEAD `3bf8320067ea205079aac310ad34f078d2331598`
**CTO disposition:** all substantive findings independently checked before repair.

| Finding | Disposition | Repair |
|---|---|---|
| DIGITAL_REPRESENTATION could imply private customer-experience access | ACCEPTED — MAJOR | Copy now says specific/publicly observable customer-experience signals in EN/ES. |
| EN jargon in chapters 03/04/07/13 | ACCEPTED — MINOR | Rewritten into plain human language while preserving epistemic boundaries. |
| ES `No reclama la empresa` | ACCEPTED — MAJOR | Replaced with explicit no-ownership/no-AXIGLAND-edit authority wording. |
| ES translated/formal phrasing in 07/10/13/15 | ACCEPTED — MINOR | Natural European-Spanish wording applied. |
| Storyboard subject placement 08/09/12/15 inaccurate | ACCEPTED — MAJOR | Source-master contact sheet independently inspected; spatial descriptions corrected and mobile crop remains evidence-gated. |
| Per-chapter mobile/text-fit guidance missing | ACCEPTED — MAJOR | Added 15/15 copy-fit target table and fail-safe adjustment order. |
| AVIF accidentally became mandatory | ACCEPTED — MAJOR | WebP remains mandatory; AVIF is optional/evidence-gated in execution order, spec, plan and tasks. |
| STORYBOARD_FREEZE ordered before assets needed to render it | ACCEPTED — BLOCKING | Added external non-runtime WebP preview stage before rendered storyboard review/freeze; production asset pipeline remains after freeze. |
| Pre-freeze `prototype layout` exception too broad | ACCEPTED — MAJOR | Narrowed to disposable non-runtime exploration with zero implementation credit. |
| Browser PASS could lack reviewable evidence | ACCEPTED — MAJOR | Added `BROWSER_QA_EVIDENCE_V1.md`, mandatory evidence references and ledger fields. |
| Canonical image briefs unavailable | NOT A PRODUCT DEFECT | Briefs are present in canonical `AXIGNAL_PUBLIC_LANDING_PAGE_CONTRACT.md` §16; reviewer uncertainty was environmental/retrieval-specific. |

## Independent visual verification

A contact sheet was generated directly from all 15 preserved masters outside the repository.
It confirms the reviewer's spatial finding: chapter 08 explorers are left-of-center; chapter 09 primary subject is left-of-center with reflections right; chapter 12 investigator is center-left and payment offer right; chapter 15 observer is left foreground with economic landscape middle/right.

Exact cover-crop percentages remain `INFERRED` until browser breakpoint evidence exists.

## Remaining human gates

`COPY_FREEZE=PENDING_HUMAN_REVIEW`

`STORYBOARD_FREEZE=PENDING_RENDERED_HUMAN_REVIEW`

No runtime implementation is authorized by this disposition.
