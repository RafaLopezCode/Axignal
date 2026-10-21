# Architecture review

Graphify queried first using graph vocabulary public/header/landing/shell/navigation/marketing/dialog. The scoped graph connects PublicShell, LandingLab, useLocale, marketing route helpers and shared UI; graph/source inspection confirms independent header implementations and parent-scoped marketing CSS. Graph truncation was explicit; current source establishes the implementation.

One component owns public navigation, while PublicShell retains body/footer ownership and LandingLab retains narrative state/motion. PublicHeader does not import the synthetic observatory, subscriber UI, marketing content corpus, Dialog or GSAP. Shared CSS is deterministically delivered through existing hashed assets. Native details preserves no-JS navigation; React only adds routing, telemetry and dismissal conveniences. No new package or runtime boundary.

The prior landing chapter observer only fed the removed inline nav; removing it avoids unused scroll/resize work. Back-to-top and funnel chapter observation remain. Locale routes for equivalent editorial articles remain caller-supplied. Public routing and private access boundaries remain unchanged.
