# Technical plan

1. Separate PublicHeader from PublicShell and make LandingLab consume it; render outside page skin wrappers so marketing/landing CSS cannot change its composition.
2. Centralize existing destination groups and six-language labels in a small pure presentation module. Keep article-specific locale route contracts and preview/public home routing.
3. Implement native details/summary navigation, progressive Escape/outside/focus cleanup, current-page/location indication and existing CTA telemetry. Reuse canonical Lucide and official logo SVG.
4. Deliver one scoped public-header stylesheet in both existing immutable foundation/lab and legacy outputs, with no extra blocking request. Remove obsolete landing-menu/header rules without changing the hero or footer.
5. Verify links against actual sitemap/route contracts; test the delivered CSS/global component usage and SSR links. Run frontend and mandatory repository gates, build, Graphify AST update and real browser QA once access is restored. Retain exact previous style URLs for safe integration. Create a reviewable PR with evidence and explicit limitations.

Constitution check: presentation state only; no canonical writes, providers, runtime integrations, permission changes, universal scores or commercial claims. No gate weakening.
