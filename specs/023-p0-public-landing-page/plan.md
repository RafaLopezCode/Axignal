# Plan — P0 Public Paginated Landing Page

This plan is subordinate to the canonical Landing Product Contract and delegates detailed execution to `MASTER_EXECUTION_ORDER_V2.md`.

## Sequence

1. Verify repository/runtime/route authority.
2. Verify the external source-master manifest.
3. Review/freeze EN copy.
4. Review/freeze ES copy.
5. Generate deterministic WebP preview derivatives outside repository/runtime.
6. Render and review the 15-chapter storyboard against those preview assets at required breakpoints.
7. Freeze storyboard after desktop/tablet/mobile review.
8. Build required deterministic production WebP derivatives.
9. Evaluate AVIF only when supported and worthwhile; accept it only from browser/quality/size evidence.
10. Implement one chapter model and six locale catalogs.
11. Implement locale resolution: explicit route/selector intent → persisted browser override → governed Principal preference when available → first supported browser language → English fallback.
12. Implement an accessible six-language selector and locale-aware `lang`/metadata.
13. Implement persistent header and accessible pagination.
14. Integrate all 15 chapters.
15. Tune focal treatment at required breakpoints.
16. Wire only truthful existing routes/CTAs.
17. Add minimal SEO and accessibility behavior.
18. Run rendered critique/repair loop and retain browser evidence references.
19. Run deterministic/full repository gates.
20. Open implementation PR.
21. Do not merge or deploy without CTO authorization.

## Rollback

Preproduction artifacts are documentation only. Runtime implementation must remain isolated to its dedicated feature branch and may be reverted without touching canonical product truth.
