# ADR-0040 — Motion and Input Ownership Contract

**Status:** Accepted
**Date:** 2026-09-30
**Authority:** MASTER §§9, 25, 26, 46, 55; ADR-0016, ADR-0037, ADR-0039.

## Context

FR-13 made AXIGLAND spatial density semantic, but the field still treated every
wheel gesture as zoom and did not explicitly govern the boundary between
canvas input, surrounding scrollable UI, trackpad gestures, pointer panning and
keyboard control. The public landing also had chapter motion with an 820 ms
lock and no explicit direction for backward navigation.

That ambiguity made correct behavior depend too much on device and pointer
position.

## Decision

### AXIGLAND input ownership

The AXIGLAND field owns an input only when the event originates in the field
and is not inside a dedicated field control, focus locator or minimap.

- wheel/trackpad without modifiers pans the camera;
- Ctrl/Command + wheel is zoom/pinch and remains anchored to the pointer;
- Shift + primarily vertical wheel input becomes horizontal pan;
- wheel input over canvas controls is not prevented by the field;
- UI outside the field keeps native scrolling;
- wheel deltas are normalized for pixel, line and page delta modes.
Pointer panning uses direct primary-button drag on empty canvas. Middle-button
drag can pan through map nodes without activating them. Node primary click
continues to mean focus/navigation.

The field becomes keyboard focusable. When the field itself owns keyboard
focus:

- arrows pan;
- Shift + arrows pan by a larger step;
- +/= zoom in;
- -/_ zoom out;
- 0 fits the world;
- Home centers the organization;
- R resets the field.

These keyboard routes invoke the same camera/focus mechanisms as pointer
controls.

### Motion

Camera focus motion has one explicit duration: 440 ms, aligned with the Design
System focus-motion token. Direct wheel, trackpad, keyboard pan and drag remain
immediate because they are continuous input, not cinematic transitions.

When prefers-reduced-motion is active, programmatic camera focus changes apply
their target state immediately without an animation frame loop.

### Landing chapter navigation

The landing remains a deliberate full-screen chapter experience rather than a
native scrolling document. Wheel/trackpad, keyboard, touch and direct controls
all converge on the same goTo chapter state machine.

A wheel gesture uses threshold plus quiet-period hysteresis. Once a gesture
advances a chapter, inertial events cannot advance further chapters until the
gesture has gone quiet. A later deliberate gesture can advance again.
Forward and backward navigation have opposite spatial direction. The complete
standard chapter transition is 640 ms, with a 620 ms artwork motion interval
and copy timings that finish within the same transition window.

Reduced motion removes spatial travel completely. Artwork changes through a
short 120 ms opacity transition, copy motion animations are disabled, and
content state remains immediately available.

## Invariants

CANVAS_INPUT != GLOBAL_PAGE_INPUT

PLAIN_WHEEL_TRACKPAD = PAN

CTRL_OR_COMMAND_WHEEL = POINTER_ANCHORED_ZOOM

CONTROL_WHEEL != CANVAS_CAPTURE

CONTINUOUS_INPUT != CINEMATIC_ANIMATION

ONE_WHEEL_GESTURE <= ONE_LANDING_CHAPTER

BACKWARD_NAVIGATION != FORWARD_MOTION_DIRECTION

REDUCED_MOTION != SPATIAL_TRAVEL

KEYBOARD_PATH == SAME_CAMERA_AUTHORITY

## Consequences

AXIGLAND behaves consistently across mouse, trackpad and keyboard without
turning all wheel activity into zoom. Surrounding panels remain scrollable.
Landing pagination is directional and resistant to trackpad inertia without a
long cooldown.

FR-15 still owns the complete non-graph accessibility projection. FR-16 still
owns the mobile product subset.

## Non-goals

This ADR does not add touch-first AXIGLAND gestures, mobile layout policy,
canonical graph semantics, persistence, provider behavior or production
deployment.
