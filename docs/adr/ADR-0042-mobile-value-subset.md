# ADR-0042 — Mobile Value Subset

**Status:** Accepted
**Date:** 2026-10-01
**Authority:** MASTER §§9, 25, 26, 46, 55; ADR-0035, ADR-0041.

## Context

The desktop subscriber product is spatial and canvas-led. Shrinking AXIGLAND,
its minimap, cognitive-depth rail and precision pan/zoom controls into a phone
viewport would preserve pixels while losing the primary mobile task.

FR-16 therefore treats mobile as a deliberate value subset rather than a
responsive copy of desktop.

## Decision

At <=680 CSS px the subscriber product is reader-first.

The full AXIGLAND canvas, workspace rail and desktop meridian are not part of
the default mobile task. The mobile product instead preserves this path:

Today → Xignal → Why it matters → Evidence → Timeline → contextual AXENT.

### Today and Xignal

Today remains the mobile entry point and exposes the same bounded material
items as desktop. Opening an item enters its reader projection without camera
movement.

The focused Xignal view retains:
- subscriber-facing meaning;
- epistemic state;
- currentness and observation time;
- a visible Why it matters section derived from the same deterministic Today
  explanation policy.

### Evidence

The Evidence route reuses ADR-0041's semantic evidence boundary. It scrolls and
focuses the existing evidence action rather than creating a mobile-only truth
model.

Unsupported evidence remains explicitly unavailable; mobile does not fabricate
provenance.

### Timeline

Mobile exposes a dedicated temporal section for the current focus. It presents
the current observation/currentness state available from the projection.

Where historical timeline authority is not exposed, the UI states that
boundary explicitly instead of inventing historical checkpoints.

### AXENT

AXENT becomes a bottom sheet on mobile.

Opening the sheet preserves the current Xignal scope and the surface the user
came from. Closing it restores that prior mobile surface.

The sheet:
- exposes the same scoped AXENT context as desktop;
- is presented as a modal dialog while open;
- restores focus on close;
- closes with Escape;
- contains keyboard focus with Tab/Shift+Tab;
- is aria-hidden when closed.

### Navigation and input

The mobile bottom navigation exposes Today, Evidence, Timeline and AXENT.

The mobile header preserves Back and the current Xignal label.

Mobile navigation never requires canvas pan precision. Generic focus navigation
does not recenter AXIGLAND while the mobile breakpoint is active.

Touch targets for primary mobile actions are at least 44 CSS px high.

## Invariants

MOBILE != SHRUNK_DESKTOP_AXIGLAND

MOBILE_VALUE_PATH = TODAY_TO_XIGNAL_TO_WHY_TO_EVIDENCE_TO_TIMELINE_TO_AXENT

MOBILE_NAVIGATION != CANVAS_PRECISION

MOBILE_EVIDENCE == SAME_EVIDENCE_BOUNDARY

MOBILE_AXENT_CONTEXT == CURRENT_FOCUS_CONTEXT

SHEET_CLOSE != CONTEXT_LOSS

TIMELINE_UNAVAILABLE != FABRICATED_HISTORY

## Consequences

A phone-sized subscriber session can reach the core governed value without
hover, minimap interaction or spatial navigation.

Desktop AXIGLAND remains unchanged and continues to own the high-density
spatial experience.

FR-16 does not claim a complete independent mobile application or native-app
navigation system. It establishes the minimum deliberate mobile product that
future audits can exercise.

## Non-goals

No new canonical truth, historical authority, relationship authority, evidence
authority, provider behavior, persistence layer, native application or
production deployment is introduced.
