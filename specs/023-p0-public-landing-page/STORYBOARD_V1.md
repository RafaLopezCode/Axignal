# AXIGNAL Public Landing — Storyboard V1

**Status:** PRODUCTION STORYBOARD DRAFT  
**STORYBOARD_FREEZE:** REOPENED — PENDING V2 HUMAN STORYBOARD ACCEPTANCE
**Authority:** MASTER → HFX → Landing Contract → Design System/Brand → this storyboard  
**Image evidence:** spatial subject placement has been checked against a contact sheet generated directly from all 15 approved source masters. Exact crop/focal percentages remain hypotheses and MUST be verified against converted assets at the required browser breakpoints.

## Global frame

- One semantic chapter per viewport on supported desktop layouts.
- Artwork fills the viewport; no card container around the chapter.
- Canonical contrast layer is CSS-only and may be tuned per chapter for AA text contrast.
- Persistent header stays independent of chapter scrolling.
- Desktop content safe zone: left/left-center, max text measure approximately 34–42rem.
- Tablet content safe zone: left 50–58% of viewport where artwork permits.
- Mobile content remains above the fold under the header; do not hide the primary subject behind a full-width opaque panel.
- Use typography scale and brand assets from current Design System/Brand authority.
- No literal AXIGNAL UI screenshots, fake dashboards or synthetic evidence.

## Persistent navigation

Desktop:
- wordmark left;
- semantic links across the upper region;
- Log in and Plant Xeed at the high-emphasis end;
- vertical chapter rail on the right.

Mobile:
- wordmark + compact primary action;
- accessible menu for secondary header links;
- compact actionable chapter indicator with direct chapter access, using at least the governed meta-text scale rather than microtext;
- no 15 tiny inaccessible targets.

Question rail:
- desktop/tablet navigation exposes the human question answered by every chapter beside its marker;
- active question is fully legible and visually primary;
- inactive questions remain directly navigable at deliberately reduced opacity rather than disappearing;
- vertical spacing must make the 15 questions scannable without stealing focus from the active chapter;
- hover/focus temporarily raises one inactive question without raising the whole rail;
- mobile collapses the full rail into the compact chapter control/menu.

## Premium pagination and motion baseline
- Wheel/trackpad pagination is a governed chapter interaction, not raw native document scrolling.
- One deliberate wheel/trackpad gesture advances at most one chapter. Accumulated deltas MUST cross an intent threshold and then enter a short transition lock so inertial scrolling cannot skip chapters.
- Keyboard, question-rail click, compact mobile chapter selection, wheel/trackpad and touch swipe MUST call the same chapter-state transition.
- Standard-motion transition target: approximately 520–620 ms, tuned in browser QA. Outgoing copy fades and travels 10–14px in the navigation direction; artwork crossfades with only a ~1% restrained reframe; incoming copy resolves into place. No cinematic zoom, parallax, spring bounce or generic SaaS slide deck effect.
- The next artwork is preloaded before transition when possible. Motion MUST never conceal asset loading or delay already-available content.
- During the transition, additional inertial wheel events are ignored; a new deliberate gesture after the lock remains responsive.
- Reduced motion uses a short opacity/state swap with no spatial travel or artwork scaling.
- Focus state, active-question state, URL/history state and accessible chapter naming MUST resolve independently of decorative interpolation.

## Responsive baseline

- Desktop focal metadata starts from the values below.
- Tablet/mobile focal positions are hypotheses until browser QA.
- Never crop away the semantic subject to center the image mechanically.
- If a chapter cannot survive mobile crop, create a deterministic responsive derivative; never edit the source master.
- Copy may reduce measure and spacing on mobile; it must not remove epistemic qualifiers merely to fit.
- Fit targets below are design constraints, not proof. If a chapter misses them in browser, first reduce vertical spacing, then use the governed responsive type scale, then demote/reposition a secondary CTA. Never remove epistemic qualifiers or truncate production copy to force a pass.

### Per-chapter copy-fit targets

| Chapter | Desktop copy measure | Mobile target | Fit priority |
|---|---:|---:|---|
| 01 OUTSIDE | ≤40rem | ≤88vw | Headline ≤3 lines; body + primary CTA visible in initial viewport |
| 02 OBSERVE | ≤40rem | ≤88vw | Preserve evidence-object body and value line |
| 03 UNDERSTAND | ≤40rem | ≤88vw | Preserve headline/body/value line without squeezing artwork |
| 04 AXIGLAND | ≤40rem | ≤88vw | Keep value line visible; no ontology-heavy overflow |
| 05 XEED | ≤42rem | ≤90vw | Plant-Xeed CTA, germination meaning and Xeed≠Xignal boundary must remain visible |
| 06 FIRST_MAP | ≤42rem | ≤90vw | Preserve completeness qualifier and value line |
| 07 EVIDENCE | ≤42rem | ≤90vw | Primary evidence CTA visible with full uncertainty wording |
| 08 DISCOVER | ≤40rem | ≤88vw | Preserve POTENTIAL qualifier and value line |
| 09 DIGITAL_REPRESENTATION | ≤44rem | ≤92vw | Preserve search/AI-agent representation + agency relevance + representation/reality boundary |
| 10 TIME | ≤40rem | ≤88vw | Preserve currentness/revalidation meaning |
| 11 AXENT | ≤42rem | ≤90vw | Keep truth-authority boundary visible |
| 12 INDEPENDENCE | ≤40rem | ≤88vw | Headline + short body + canonical value line |
| 13 USE_CASES | ≤46rem | ≤92vw | Preserve the SEO/GEO/AEO/AIO agency proposition and independent-observation value line; on mobile split the body into two readable paragraphs rather than shrinking type |
| 14 PRICING | ≤42rem | ≤90vw | Exact Xeed price, additional-Xeed price, non-billable-Xignal value line and CTA visible |
| 15 START | ≤40rem | ≤88vw | Primary CTA visible; secondary CTA may move below primary |

---

## 01 — OUTSIDE

**Narrative beat:** destabilize self-perception and create curiosity.  
**Copy zone:** upper-left / left-center.  
**Artwork focus:** contemporary street and Renaissance figures center-right.  
**Focal baseline:** desktop 68% 50%; tablet 72% 50%; mobile 76% 48%.  
**CTA:** primary Create a Xignal; secondary What is AXIGNAL?  
**Hierarchy:** headline dominant; body two short sentences; CTA visible without scrolling.  
**Transition:** first load from black/brand background into artwork; no dramatic reveal.  
**Risk:** headline must remain readable over street luminance without turning the whole image black.
## 02 — OBSERVE

**Narrative beat:** answer what AXIGNAL actually does.  
**Copy zone:** left-center, slightly higher than vertical center.  
**Artwork focus:** observer/cartographer + modern logistics/factory activity.  
**Focal baseline:** desktop 69% 50%; tablet 72% 50%; mobile 76% 50%.  
**CTA:** none required; narrative progression is primary.  
**Hierarchy:** eyebrow → short headline → evidence-object body → value line.  
**Transition:** subtle copy replacement; pagination advances one state.  
**Risk:** avoid visual language that implies surveillance or “all-seeing AI”.

## 03 — UNDERSTAND

**Narrative beat:** move from observation to economic context.  
**Copy zone:** left-center.  
**Artwork focus:** group of objects/scholars center-right.  
**Focal baseline:** desktop 66% 50%; tablet 69% 50%; mobile 73% 50%.  
**CTA:** none.  
**Hierarchy:** headline carries the conceptual turn; canonical value line closes the chapter.  
**Transition:** no graph animation; context is communicated by composition, not floating nodes.  
**Risk:** copy density must stay low enough to preserve the still-life/scholar composition.
## 04 — AXIGLAND

**Narrative beat:** introduce one canonical temporal world.  
**Copy zone:** left with generous negative space.  
**Artwork focus:** shared world/map, slightly right of center.  
**Focal baseline:** desktop 62% 50%; tablet 64% 50%; mobile 68% 50%.  
**CTA:** optional direct link to AXIGLAND chapter/product explanation only if route exists.  
**Hierarchy:** headline → body → canonical value line.  
**Transition:** calm; this is the conceptual anchor, not a spectacle.  
**Risk:** do not let “many perspectives” look like many customer-owned worlds.

## 05 — XEED

**Narrative beat:** introduce the customer-planted seed and make the germination metaphor operationally truthful.
**Copy zone:** left-center.
**Artwork focus:** hand/seed-marker and emerging economic context right.
**Focal baseline:** desktop 70% 52%; tablet 73% 52%; mobile 76% 54%.
**CTA:** Plant a Xeed.
**Hierarchy:** Plant-a-Xeed eyebrow → headline → seed/germination body → “You plant the Xeed. AXIGNAL follows the evidence.” → CTA.
**Transition:** the chapter change may subtly reframe the marker as the start of observation, but MUST NOT animate a fake network or imply instant germination.
**Risk:** preserve XEED ≠ XIGNAL: the Xeed is the planted persistent context; many Xignals may emerge from Brain work. Never imply claiming, editing or owning the organization.
## 06 — FIRST_MAP

**Narrative beat:** establish first-value expectation without claiming completeness.  
**Copy zone:** upper-left, leaving company/context visible.  
**Artwork focus:** company center-right plus supplier/market/logistics context.  
**Focal baseline:** desktop 68% 50%; tablet 71% 50%; mobile 74% 50%.  
**CTA:** none required.  
**Hierarchy:** headline → one body paragraph → “Useful depth. Explicit limits.”  
**Transition:** plain chapter movement; do not simulate a fake graph materializing.  
**Risk:** this chapter must not visually imply MAP_READINESS=complete world coverage.

## 07 — EVIDENCE

**Narrative beat:** convert interest into epistemic trust.  
**Copy zone:** left-center, compact.  
**Artwork focus:** evidence examination and experts center-right.  
**Focal baseline:** desktop 69% 50%; tablet 72% 50%; mobile 75% 50%.  
**CTA:** Show me how AXIGNAL knows.  
**Hierarchy:** CTA is a major interaction, almost equal to headline.  
**Transition:** if routed to a demo/explanation, it must be real; otherwise anchor to truthful public explanation.  
**Risk:** no fake evidence wall, no generated explanation presented as stored provenance.
## 08 — DISCOVER

**Narrative beat:** introduce potential relevance and productive surprise.  
**Copy zone:** upper-left dark field only; do not extend into the explorers below/left of center.
**Artwork focus:** explorers sit left of center while the economic route/landscape extends across the right. Both are semantically useful.
**Focal baseline:** desktop 56% 48% (hypothesis); tablet 58% 48% (hypothesis); mobile requires rendered decision and MAY require a deterministic responsive derivative to preserve explorer + route context.
**CTA:** none required.  
**Hierarchy:** headline → body → explicit POTENTIAL value line.  
**Transition:** no animated glowing route; geography and activity carry the metaphor.  
**Risk:** “discover” must never become “find your next customer”.

## 09 — DIGITAL_REPRESENTATION

**Narrative beat:** make search/AI-agent representation a first-class value surface and explicitly qualify the SEO/GEO/AEO/AIO audience.
**Copy zone:** extreme-left dark curtain/negative field only; do not cover the primary figure left of center.
**Artwork focus:** the real subject sits left of center; contextual reflections occupy the right. The subject/reflection contrast is the semantic point.
**Focal baseline:** desktop 56% 50% (hypothesis); tablet 58% 50% (hypothesis); mobile requires rendered decision and MAY require a deterministic responsive derivative because losing either the subject or reflections weakens the chapter.
**CTA:** none.
**Hierarchy:** search/AI-agent question headline → concise independent-observation body → agency value line. The representation≠reality qualifier remains explicit in body/guardrail even when the agency proposition is foregrounded.
**Transition:** crossfade/reframe should make the reflected contexts feel like a change of viewpoint, not an animated mirror gimmick.
**Risk:** no universal rank, context-free model opinion, GEO score or objective reputation score. Do not imply AXIGNAL performs SEO/GEO/AEO/AIO.
## 10 — TIME

**Narrative beat:** explain recurring value through preserved change/currentness.  
**Copy zone:** left-center.  
**Artwork focus:** continuous company/place across temporal states.  
**Focal baseline:** desktop 62% 50%; tablet 65% 50%; mobile 68% 50%.  
**CTA:** none.  
**Hierarchy:** headline → body → temporal value line.  
**Transition:** avoid clocks/timeline widgets; chapter movement itself is enough.  
**Risk:** emerging visual states cannot read as prediction.

## 11 — AXENT

**Narrative beat:** position AXENT as cognitive navigator, not chatbot/truth authority.  
**Copy zone:** left-center.  
**Artwork focus:** investigator navigating real archives/evidence center-right.  
**Focal baseline:** desktop 68% 50%; tablet 71% 50%; mobile 74% 50%.  
**CTA:** optional “Explore AXENT” only if a truthful route exists.  
**Hierarchy:** “Not another chatbot” lead; body establishes research/orchestration; value line closes authority boundary.  
**Transition:** no chat bubbles, robot reveal or glowing AI animation.  
**Risk:** AXENT must not appear to author canonical truth by itself.
## 12 — INDEPENDENCE

**Narrative beat:** make the trust model memorable.  
**Copy zone:** far-left/upper-left dark margin, narrower than the global default; do not cover the seated investigator.
**Artwork focus:** the independent investigator/cartographer is center-left while the payment offer enters from the right. Their tension must remain visible together.
**Responsive art direction:** desktop uses the canonical landscape master at approximately 54% 50%. Tablet and mobile MUST use deterministic responsive derivatives regenerated from the untouched master so the investigator and the recognizable payment offer remain visible together. The reviewed preview derivatives use 768×1024 and 390×844 canvases with the source composition retained in the upper field and copy-safe black space below; production derivatives must be regenerated after STORYBOARD_FREEZE from the verified master rather than promoted from preview assets.
**CTA:** none.  
**Hierarchy:** headline and canonical value line are the memorable pair; body is short.  
**Transition:** restrained; no moralizing/villain animation.  
**Risk:** avoid sounding anti-customer; the point is independence, not hostility.

## 13 — USE_CASES

**Narrative beat:** put SEO/GEO/AEO/AIO agencies visibly in the foreground while retaining the broader same-world decision value.
**Copy zone:** upper-left.
**Artwork focus:** group portrait around one world, center/right.
**Focal baseline:** desktop 63% 50%; tablet 66% 50%; mobile 70% 50%.
**CTA:** optional role exploration only if it remains one canonical world.
**Hierarchy:** agency-focused headline → SEO/GEO/AEO/AIO independent-observation paragraph → broader leadership/sales/procurement/export/consultancy sentence → agency value line. On mobile, preserve agency wording at governed body scale; split ideas rather than shrinking type.
**Transition:** no role tabs required for P0. The chapter should feel like a deliberate commercial turn toward who benefits, not a generic persona carousel.
**Risk:** AXIGNAL observes independently; it does not execute agency work. Before/after observation does not establish causation without compatible instruments, queries, surfaces, versions, conditions and time coverage.
## 14 — PRICING

**Narrative beat:** convert understanding into proportional value using the corrected billable unit.
**Copy zone:** left-center, with price highly scannable but not sale-like.
**Artwork focus:** balance scale/seed-marker/evidence right-center.
**Focal baseline:** desktop 68% 50%; tablet 70% 50%; mobile 74% 50%.
**CTA:** Plant a Xeed.
**Hierarchy:** headline → €9.95 one-Xeed price → €4.95 additional-Xeed price → “one Xeed can produce many Xignals” value line → CTA.
**Transition:** no pricing-card carousel; pricing remains one chapter in the story.
**Risk:** Xignals are not billable units. No invented trial, annual plan, tax promise, discount or checkout state.
## 15 — START

**Narrative beat:** close with the product's concrete seed metaphor and one low-friction action.
**Copy zone:** upper-left dark field around/above the observer, never over the observer’s face or marker hand.
**Artwork focus:** the observer/seed-marker is on the left foreground; the company and wider economic landscape extend through the middle/right distance. Both must remain legible as one beginning-to-world composition.
**Focal baseline:** desktop 56% 50% (hypothesis); tablet 58% 50% (hypothesis); mobile requires rendered decision and MAY require a deterministic responsive derivative if the observer/landscape relationship cannot survive cover cropping.
**CTA:** Plant a Xeed; secondary How AXIGNAL knows.
**Hierarchy:** final headline → one body paragraph naming Xignals/map/evidence/time → primary CTA; secondary remains quieter.
**Transition:** the arrival should feel resolved and invitational, not celebratory; no confetti, bounce or hype.
**Risk:** CTA route must be truthful; if signup/billing is absent, route to the real next available step rather than fake completion.
---

## Storyboard freeze decision record

```text
CHAPTERS_DEFINED=15/15
DESKTOP_COMPOSITION=DEFINED_DRAFT
TABLET_COMPOSITION=DEFINED_DRAFT
MOBILE_COMPOSITION=DEFINED_DRAFT
SOURCE_MASTER_SPATIAL_PLACEMENT=CONFIRMED_CONTACT_SHEET_15_OF_15
FOCAL_METADATA=INFERRED_PENDING_BROWSER_BREAKPOINT_QA
ACTUAL_CONVERTED_ASSET_VISUAL_VERIFICATION=PENDING
INDEPENDENT_REVIEW_FINDINGS=REPAIRED_PRIOR_VERSION
V2_XEED_AGENCY_COPY=UPDATED
PREMIUM_WHEEL_TRANSITION=SPECIFIED_PENDING_RENDER
QUESTION_RAIL=SPECIFIED_PENDING_RENDER
CANONICAL_LOGO_GLOBAL_CSS_FONT_REVIEW=REQUIRED_IN_RENDER
READY_FOR_RENDERED_REVIEW=YES_AFTER_V2_COPY_REVIEW
RENDERED_BROWSER_REVIEW=STALE_AFTER_V2_COPY_AND_MOTION_CHANGE
RENDERED_EVIDENCE_NEXT=BROWSER_QA_EVIDENCE_V3.md
HUMAN_VISUAL_REVIEW=PENDING_V2
STORYBOARD_FREEZE=REOPENED_PENDING_V2_HUMAN_ACCEPTANCE
```

No focal percentage becomes canonical until browser evidence confirms the subject is preserved at the required breakpoints.

[executed on device: DESKTOP-7L6CMEJ (d615520f-0404-49b0-83c7-620cc18c31f4)]