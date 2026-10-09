---
version: 1
slug: "apps-web-experience-app-account-page-tsx"
primary_target: "apps/web/experience/app/account/page.tsx"
related_targets: ["apps/web/experience/components/subscriber-portfolio.tsx"]
---

# Subscriber workspace — /account

Mode: Operate. Seed: d64b4c02 (surface). Dealt: Morning briefing (lead), Attention desk, Observatory. The user locked a fusion: **Observatorio Económico Vivo**. Challenger fused: gate board ("a change stays lit until you have noticed it").

Audience: direct subscribers (one organization) and agencies (many). Job: know what is happening, what matters, what changed, what could improve, why AXIGNAL says so and where to look, without learning the engine. Must stay untouched: every current capability (add, pause or resume, reobserve, retry, replace, remove, capacity purchase, payment check, assistant connections, sign-out, pilot invite, MCP consent return), epistemic states, tenant isolation, real data only.

## Direction contract

THESIS: One living observatory, not three products. The first viewport is a briefing of the selected organization and what changed since you last looked. Any finding unfolds in place from meaning to proof, never in a modal or on a new page. Refuses the infinite dossier, and refuses a grid of identical metric tiles.

OWN-WORLD: Deep AXIGNAL-ink rail (blue #354F98 darkened to ink), paper workspace, Fraunces only for the organization and the briefing sentence, Manrope for everything else. Three lane tints from the incumbent palette: blue for what matters, sage for how it is understood, lavender for what is unknown. Epistemic marks are shape plus text, never color alone. Brass lamp for lit changes. Lucide icons.

STORY: Orientation (where am I, which organization, when observed), then the briefing sentence, then the three lanes, then depth on demand (meaning, reasoning, proof, AXENT), then explore further (world, evolution, evidence), then back exactly where you were.

FIRST VIEWPORT: Rail with the portfolio and each organization's lens status. Header with the name, identity state, observation time and a reobserve action. Then the briefing sentence in Fraunces, the "since your last visit" lamps, and three lanes of human-language findings.

SIGNATURE: Lit until seen. A changed or new finding carries a brass lamp, and the rail shows a lamp on its organization. Opening the finding dims the lamp over ~600 ms. Lamps are stored per device and labelled as such. Organization switching cross-fades through view transitions, and the depth panel slides from the finding it explains.

RISK: Deriving briefing copy from contracts must never promote POTENTIAL to fact or treat UNKNOWN as negative. A portfolio-wide desk needs one output read per organization (bounded concurrency).
