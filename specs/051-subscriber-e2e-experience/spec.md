# Subscriber E2E experience and HTTP composition

**Status:** Implemented and locally proved; fresh rendered-browser and external acceptance pending.
**Date:** 2026-10-06
**Authority:** MASTER â†’ Constitution â†’ ADR-0084 and accepted contracts â†’ this feature.

## Human outcome

A subscriber signs in with a configured Google or registered ChatGPT identity,
opens a private portfolio, purchases observation capacity, adds Organizations,
and reads Brain outputs with understandable uncertainty and exact evidence.
Customer Zero remains an internal entry, not subscriber identity or onboarding.

## User stories and acceptance

1. **Secure entry.** Only a valid browser-bound one-time OIDC transaction can
   create an opaque application session. Missing provider configuration gives
   an honest unavailable state. Expired/revoked sessions deny reads. Start and
   logout reject cross-origin requests; callback URLs are fixed server-side.
2. **Private portfolio.** Authenticated portfolio routes list only authorized
   Tenant attention. Add/pause/resume/remove/replace/reobserve reauthorize before
   loading private data and survive reload. An unknown Organization identity
   remains pending; no user input directly becomes canonical truth.
3. **Purchase and expansion.** The subscriber chooses a desired total capacity
   from their own portfolio. One base and total-minus-one addons define initial
   purchase. Expansion uses the existing subscription, provider proration and
   pending payment state. Return URLs never grant capacity. Duplicate clicks,
   failed payment, stale state and unknown capacity have explicit recovery.
4. **Human First outputs.** Meaning precedes technical detail. Each material
   output preserves scope, declared/observed/derived status, time/currentness,
   uncertainty and directly navigable evidence. No fixture output is the data
   source for the new subscriber route. Missing Brain output remains unknown.
5. **Navigation and accessibility.** Empty/loading/failure states, keyboard
   navigation, narrow viewport, reload and stable scoped deep links work without
   altering accepted demo/Admin surfaces. Color alone never conveys truth.
6. **Operational boundary.** Public activation requires real configuration and
   legal publication, not invented defaults. Local readiness and external
   verification remain distinguishable. Existing runtime routes stay compatible.

## Scope

Root owns `tools/runtime/config.py`, `tools/runtime/service.py`, new
`tools/runtime/subscriber_http.py`, subscriber composition tests and the web
experience. Feature 049 owns identity/portfolio services and durable stores;
047 owns billing; 050 owns Brain/read-model outputs. Composition depends on
their typed interfaces and cannot bypass their authorities.

Design mode is **EXTEND** for a subscriber portfolio surface and **PRESERVE**
for login and adjacent accepted grammar. No replacement graph renderer,
arbitrary generated JSX, CRM, psychological profiling or paid ranking is added.

## Required verification and limits

Deterministic Python and web gates, 1/2/100 journey, cross-Tenant negatives,
session replay/revocation, billing pending/confirmed transitions, continuity,
evidence navigation and actual rendered desktop/narrow views are required.
External OAuth client approval, completed live payment, exact production
candidate, recovery drill and representative-user/human visual acceptance are
separate evidence. No implementation checkbox may substitute for them.
