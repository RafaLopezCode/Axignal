# Header and mobile folio refinement

Mode PRESERVE for desktop identity/shared shell; EXTEND for the explicitly requested mobile plate. Human annotations identify four scoped concerns: centered global navigation, centered Start text/arrow, a less empty mobile hero and a LinkedIn icon. Current request authorizes this implementation; this new batch is local and awaits human visual acceptance. Previous production release04ad93cdcc6ab7cf723aadf7616872f1db503dd4 remains unchanged.

## Changes

- Symmetric header side tracks and padding center navigation against the whole header. Start centers text and arrow together. Navigation collapses below1440px before six-language labels can collide with the fixed actions; mobile menu/locale/login paths retain existing behavior.
- A separate4:3Observador/newspaper illustration serves only at<=760px using picture/source, responsive content-hashed360/640/960/1448WebP and no new runtime dependency. The approved desktop master and its variants are untouched. Generated art is conceptual and has no economic evidentiary status. Full exact prompt/tool/source provenance: assets/plates/hero-mobile.png.json.
- Three newspaper titles remain actual localized HTML, aria-hidden duplicate of the three accessible linked explanatory annotations. Their mobile sizing overrides desktop language-specific typography. Body and annotations retain their accepted readable scale.
- Tablet wrapper and image share the same clamped height, preventing image/annotation overlap. Canonical Lucide LinkedIn brand asset is18px, decorative and paired with the unchanged text/URL/external-arrow. Current installed Lucide no longer exports brands, so the official0.468.0asset is vendored with license/source/hash and only the stroke color resolved to AXIGNAL blue. Social link has a44px target and3px keyboard focus.
- Manifest/scoped immutable cache now cover14hashed resources. Exactly5new mobile image paths added to the AXIGNAL edge allowlist, never a broad marketing prefix.

## Actual verification

352frontend tests pass; final production build includes TypeScript and534Knowledge/60catalog localized HTML outputs. Explicit typecheck and2437-entry locale inventory pass.8public HTTP checks,28Admin HTTP checks,7production routing contract tests, architecture guard and all8governance gates pass. AST-only Graphify updated22526nodes/62322edges. No backend/domain/auth/private dashboard source changed; full Python suite was previously passed for release04ad93c and was not rerun for this presentation-only refinement.

First bounded inspection found the new tablet wrapper height mismatch and the later narrow German capture exposed a retained higher-specificity desktop font rule. Both are fixed. The extra narrow-language confirmation is justified by that concrete defect, not a new aesthetic pass. No global detector/context rerun, invented CLI receipt or replacement approval round.

Evidence: first-geometry.json records six locales at1440/320before the last font specificity correction; final-geometry.json confirms11structural viewport boundaries320–1650including zero image/annotation overlap in flow below1280. The annotation-overlap value at desktop is not a defect metric: those annotations are intentionally absolute over the plate. Mobile-locales-final.json contains12unique locale/width combinations at320and405, all with headings within their paper-band height and no horizontal overflow. Desktop navigation center difference<=0.008px. Tightest measured localized1440navigation/action gap37.8px. Desktop/CTA screenshot1458x1244; mobile405x1244; German320x1100; tablet900x1100; footer405x1244.

Real mobile navigation opens, Escape closes and returns focus to its opener. LinkedIn SVG loads as200image/svg+xml,44px link is focusable and3px outline visible. No console errors in final tested tabs. Asset-verification.json confirms all14actual local HTTP resources against bytes/SHA256/immutable cache. Publication is not claimed. Final field Core Web Vitals/GSC ranking and human visual acceptance are not inferred.

Status: IMPLEMENTED + AUTOMATED_QA_PASS + VISUAL_EVIDENCE_READY + HUMAN_VISUAL_ACCEPTANCE_PENDING. Independent bounded finish review: disposition SHIP; see finish-verdict.md. This does not replace human visual acceptance or authorize publication of this new local batch.

## Subsequent explicit release authority

On2026-10-16the human requested "Commit, merge y deploy" for this reviewed batch. This explicitly authorizes integration and production publication, superseding the earlier local-only operational restriction. Independent scoped disposition remains SHIP; no universal aesthetic acceptance or historical CLI closure is inferred. Commit/push, branch/main CI and immutable deployment verification are now in progress; completion will be recorded separately against the exact deployed main SHA.
