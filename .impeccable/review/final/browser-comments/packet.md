# Human browser comments and vector-logo followup — 2026-10-16

Scope: seven browser annotations, newsletter invitation and subsequent direct-SVG request, same independent codex/public-landing-ecosystem branch. No merge/deploy or private UI/backend changes.

## Resolved presentation

- Family strip:36px separation from the upper heading/intro on desktop; existing mobile reading spacing retained.
- Sector artwork: replaced the shared industries.webp with a hero-matched cream-paper folio and blue-gray ink panorama. Original industry meaning and conceptual disclaimer preserved. All consumers use this single301870-byte2007×784WebP; full image now visible instead of cropping the Observer and sectors. Built-in image_gen, full prompt/reference/master provenance at public/marketing/industries.webp.json. Original source and earlier version preserved outside repository.
- Knowledge hub and every localized article use MarketingShell with their existing exact localeRoutes and marketing-reading, retaining their reading layout. Header/footer match the public catalog; Knowledge links retain current language. Public-only server render import keeps metadata tests deterministic. Root layout remains unchanged.
- Header:147×43desktop/tablet logo; login and signup both148px, login transparent/borderless. Compact header1280–1519fits all six languages. Under480 annotations become readable rows; price shortcuts wrap at the narrowest size. German Knowledge card min-content overflow at320resolved with scoped word containment.
- Newsletter: restored home invitation plus footer entry via existing WeeklyBriefChannel marketing variant. Existing AO-15 request, notice versions, receipt validation and independent optional AO-16 newsletter consent retained. Real status has loading, explicit pause, unknown/unavailable and retry. Runtime http://127.0.0.1:18182 and preview BFF both confirmed enabled:false; no setting toggled, submission or email sent. Enabled form behavior remains covered by existing request/consent contract tests; no live successful subscription is claimed.
- Logo clarification: served logo-light.svg was already the exact canonical two-path SVG, not a PNG/JPG wrapper. Subsequent human request is implemented through PublicBrandVector: exact approved path geometry/transforms/fills rendered inline in catalog header and MarketingFooter. Canonical and distributed SHA2563df29aa09f405b6a5de898841c90c7775909dfbdf344e17a5b6dc73a39c4e8b4 verified; source SVGs and private Brand unchanged. No live-font recreation, tracing or recoloring. Parity and no-raster tests pass.

## Explicit pending item

Human requested testimonials, then synthetic testimonials. Public Landing Contract§13 prohibits fake social proof and fabricated testimonials; Communication Strategy§31 and feature truth constraints agree. Conflict was reported. No fabricated quote/name/logo/result was published. Real authorized testimonials remain pending. Do not mark this requirement fulfilled.

## Evidence and acceptance

Root inspected desktop/mobile home, artwork, Knowledge/header/footer and actual newsletter pause. Footer screenshot includes browser selection chrome over the mark, not a product element. Native menu navigation from Knowledge to sectors and newsletter retry were exercised.48home width/locale samples,12final Knowledge samples and4post-inline vector widths show no tested overflow. Final SVG DOM:2paths,0images per logo; header147×43, footer195×57. Captures from immediately before the inline-logo followup retain unchanged surrounding-layout evidence; latest home/header captures plus vector JSON and HTTP render checks establish final vector reproduction. Do not claim every old screenshot was recaptured after every source-only change.

Validation:349frontend tests; TypeScript and production build pass,534Knowledge+60public HTML language outputs; i18n2437entries/no missing;6production HTTP tests including Knowledge hubs/articles, newsletter and inline SVG; Architecture Guard and all8governance categories pass. Prior full Python2461passed/7skipped remains baseline; no backend edits or unnecessary repeat. Graphify AST update was run again after vector code. Existing SyntaxWarning in production SEO test remains unrelated.

Automatic review refused a proposed global CSS import because private routes are outside scope. It was never executed. Safer public-only server-render loading was implemented; app/layout.tsx and private UI have no diff. No gate weakened. No detector rerun, new HTML facade, false CLI receipt or automatic-phase closure. Human-approved real-app checkpoint override and historical CLI OPEN remain; final human visual acceptance PENDING.

Independent review requested only for this annotated scope: spacing/header/frame continuity, illustration style consistency, newsletter fidelity and canonical vector reproduction. Preserve earlier verdicts; write this packet's separate finish-verdict.md.
