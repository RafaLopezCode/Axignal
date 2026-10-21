# Architecture review

Graphify first locates PublicHeader, LandingLab, Dialog, MarketingShell and existing route/style helpers. Source and rendered geometry identify selector extraction and responsive header constraints as the relevant boundaries. This is presentation and navigation only: no truth mutation, tenant scope change, provider coupling, new runtime dependency, product workflow or private ingress.

The exact immutable style allowlist retains the previous three style URLs during the release transition alongside the new generation. Assets remain explicit paths; no directory wildcard or additional application route is exposed. The production operator must atomically apply only AXIGNAL's public routing file, keep the previous configuration for rollback, retain all five Compose files, and verify the external style assets and product boundaries after cutover.

Implementation is within the existing public presentation contracts and the user's correction. No MASTER or ADR change is required. The existing application demo retains its product navigation and public return/start links rather than receiving a commercial header inside the product frame.
