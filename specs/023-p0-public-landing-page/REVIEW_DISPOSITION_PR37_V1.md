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

## Rendered storyboard hostile review

A second independent Codex read-only review inspected PR #37 at `a2ed7f679e5afad0f6fc86e84710a93b8bb30000`, all six EN/ES contact sheets, key full-resolution screenshots, source manifests and the external preview/evidence directories.

Result: `PR37_RENDERED_REVIEW=REQUIRES_CHANGES`.

The reviewer found no visual, narrative, copy-fit, agency-value or epistemic defect in the rendered storyboard. Two evidence-governance findings were accepted:

| Finding | Disposition | Repair |
|---|---|---|
| 0/90 screenshot SHA-256 values matched the then-current screenshot files | ACCEPTED — BLOCKING | Regenerated the exact 90-capture set through Playwright, regenerated `render-evidence.json`, wrote the corrected current manifest as `BROWSER_QA_EVIDENCE_V2.md`, and independently rechecked 90/90 hashes: mismatch count 0. `BROWSER_QA_EVIDENCE_V1.md` remains historical/superseded for rendered-storyboard hash provenance. |
| Chapter 12 tablet/mobile responsive preview derivatives were unmanifested | ACCEPTED — MINOR | Regenerated deterministic responsive derivatives from the untouched 1920×1080 master; documented dimensions, bytes, SHA-256, transform recipe and review-only purpose. Canonical base preview remains 15/15; actual external review directory is 17 WebPs = 15 base + 2 governed responsive derivatives. |

Chapter 12 responsive review derivatives are not production authority. If still required after implementation QA, production equivalents must be regenerated from the verified source master through the governed production pipeline.

### Follow-up rendered evidence re-review

A follow-up Codex re-review at exact local HEAD `3807dfde06d1eafcf27ecd1030050e5f2df5efa5` verified the repaired screenshot provenance (`90/90`, mismatch `0`) and all layout/console metrics, but found that the Chapter 12 responsive files copied into the rendered-review bundle were older byte variants than the now-governed preview derivatives.

Disposition: **ACCEPTED — BLOCKING evidence provenance defect**.

Repair:
- synchronized the rendered-review Chapter 12 tablet/mobile assets byte-for-byte from the governed preview source directory;
- verified `2/2` source→review SHA-256 equality;
- reran all `90` EN/ES desktop/tablet/mobile captures;
- regenerated `render-evidence.json` and all six contact sheets;
- regenerated `BROWSER_QA_EVIDENCE_V2.md` from the exact rerun;
- independently rechecked `90/90` screenshot hashes with mismatch `0`, `0/90` overflow, `0/90` copy escape, `0/90` console errors, and `0/90` failed fit flags.

## Remaining human gates

`COPY_FREEZE=PASS`

`CTO_RENDERED_STORYBOARD_REVIEW=PASS_BASE_90_EN_ES`

`HUMAN_STORYBOARD_ACCEPTANCE=PENDING`

`STORYBOARD_FREEZE=PENDING_HUMAN_ACCEPTANCE`

No runtime implementation is authorized by this disposition.
