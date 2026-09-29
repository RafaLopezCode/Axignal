# AXIGNAL Public Landing — Storyboard V1

**Status:** PRODUCTION STORYBOARD DRAFT  
**STORYBOARD_FREEZE:** PENDING HUMAN STORYBOARD ACCEPTANCE
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
- Log in and + Xignal at the high-emphasis end;
- vertical chapter rail on the right.

Mobile:
- wordmark + compact primary action;
- accessible menu for secondary header links;
- compact actionable chapter indicator with direct chapter access, using at least the governed meta-text scale rather than microtext;
- no 15 tiny inaccessible targets.

## Motion baseline
- Native scroll-snap/state transition is preferred.
- Active chapter copy may enter with opacity + <=8px translation.
- Transition duration should remain restrained and should never delay navigation.
- Artwork itself remains mostly static; no cinematic zoom/parallax.
- Reduced motion removes translation and nonessential interpolation.
- Focus state and URL/history state must never depend on animation.

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
| 05 XIGNAL | ≤42rem | ≤90vw | Primary CTA and ownership boundary must remain visible |
| 06 FIRST_MAP | ≤42rem | ≤90vw | Preserve completeness qualifier and value line |
| 07 EVIDENCE | ≤42rem | ≤90vw | Primary evidence CTA visible with full uncertainty wording |
| 08 DISCOVER | ≤40rem | ≤88vw | Preserve POTENTIAL qualifier and value line |
| 09 DIGITAL_REPRESENTATION | ≤42rem | ≤90vw | Preserve representation/reality boundary in full |
| 10 TIME | ≤40rem | ≤88vw | Preserve currentness/revalidation meaning |
| 11 AXENT | ≤42rem | ≤90vw | Keep truth-authority boundary visible |
| 12 INDEPENDENCE | ≤40rem | ≤88vw | Headline + short body + canonical value line |
| 13 USE_CASES | ≤46rem | ≤92vw | Preserve the SEO/GEO/AEO/AIO agency proposition and independent-observation value line; on mobile split the body into two readable paragraphs rather than shrinking type |
| 14 PRICING | ≤40rem | ≤90vw | Exact price, additional-Xignal price, value line and CTA visible |
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

## 05 — XIGNAL

**Narrative beat:** explain the paid unit and attention model.  
**Copy zone:** left-center.  
**Artwork focus:** hand/marker and emerging economic context right.  
**Focal baseline:** desktop 70% 52%; tablet 73% 52%; mobile 76% 54%.  
**CTA:** Create a Xignal.  
**Hierarchy:** persistent-observation eyebrow → headline → explanatory body → canonical value line → CTA.  
**Transition:** a subtle state advance may emphasize the marker; no growing neon network.  
**Risk:** never imply claiming, editing or owning the organization.
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

**Narrative beat:** distinguish digital representations from the organization itself.  
**Copy zone:** extreme-left dark curtain/negative field only; do not cover the primary figure left of center.
**Artwork focus:** the real subject sits left of center; contextual reflections occupy the right. The subject/reflection contrast is the semantic point.
**Focal baseline:** desktop 56% 50% (hypothesis); tablet 58% 50% (hypothesis); mobile requires rendered decision and MAY require a deterministic responsive derivative because losing either the subject or reflections weakens the chapter.
**CTA:** none.  
**Hierarchy:** headline should do most of the work; body stays concise; canonical value line visible.  
**Transition:** simple cross-state; no mirror animation required.  
**Risk:** no universal score/rank/model opinion.
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

**Narrative beat:** broaden relevance without fragmenting the product, and make the agency multiplier use case explicit.
**Copy zone:** upper-left.  
**Artwork focus:** group portrait around one world, center/right.  
**Focal baseline:** desktop 63% 50%; tablet 66% 50%; mobile 70% 50%.  
**CTA:** optional direct role exploration only if it remains one canonical world.  
**Hierarchy:** headline → general decision-use paragraph → SEO/GEO/AEO/AIO agency paragraph → canonical agency value line. On mobile the two body ideas MUST render as separate paragraphs at the governed normal mobile body scale; do not compress them into a dense role list or shrink only this chapter to make it fit.
**Transition:** no role tabs required for P0 unless they improve comprehension measurably.  
**Risk:** do not make AXIGNAL look like an SEO/GEO/AEO/AIO execution tool or imply causal attribution from a before/after observation. The agency value is independent observation of representation and change.
## 14 — PRICING

**Narrative beat:** convert understanding into proportional value.  
**Copy zone:** left-center, with price highly scannable but not sale-like.  
**Artwork focus:** balance scale/marker/evidence right-center.  
**Focal baseline:** desktop 68% 50%; tablet 70% 50%; mobile 74% 50%.  
**CTA:** Create a Xignal.  
**Hierarchy:** headline → exact current price → additional-Xignal price → value line → CTA.  
**Transition:** no pricing card carousel; this remains part of the story.  
**Risk:** no invented trial, annual plan, tax promise, discount or checkout state.

## 15 — START

**Narrative beat:** close with one concrete low-friction action.  
**Copy zone:** upper-left dark field around/above the observer, never over the observer’s face or marker hand.
**Artwork focus:** the observer/marker is on the left foreground; the company and wider economic landscape extend through the middle/right distance. Both must remain legible as one beginning-to-world composition.
**Focal baseline:** desktop 56% 50% (hypothesis); tablet 58% 50% (hypothesis); mobile requires rendered decision and MAY require a deterministic responsive derivative if the observer/landscape relationship cannot survive cover cropping.
**CTA:** Create a Xignal; secondary How AXIGNAL knows.  
**Hierarchy:** final headline → one body paragraph → primary CTA; secondary remains quieter.  
**Transition:** no confetti or hype; the chapter should feel like a beginning.  
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
INDEPENDENT_REVIEW_FINDINGS=REPAIRED
READY_FOR_RENDERED_REVIEW=YES
RENDERED_BROWSER_REVIEW=CTO_PASS_BASE_90_EN_ES
RENDERED_EVIDENCE=BROWSER_QA_EVIDENCE_V1.md
HUMAN_VISUAL_REVIEW=PENDING
STORYBOARD_FREEZE=PENDING_HUMAN_ACCEPTANCE
```

No focal percentage becomes canonical until browser evidence confirms the subject is preserved at the required breakpoints.
