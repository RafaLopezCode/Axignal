# FIRST VIEW — 10-Second Comprehension Protocol

**Status:** Active UX acceptance protocol
**Date:** 2026-09-30
**Applies to:** FR-09 Insight-First Today

## Goal

A first-time subscriber should understand the practical value of the current AXIGNAL view before learning AXIGNAL's internal vocabulary or parsing the full AXIGLAND canvas.

## Setup

Use a realistic Xeed with one of these governed states:

1. 1–3 material Today items;
2. useful partial evidence with no material item ready;
3. empty / insufficient-evidence state.

Do not coach the participant on Xeed, Xignal, FAXT, PATHX, EvidenceAdmission, AXENT, or AXIGLAND before the timed exposure.

## Timed test

Expose the default Today view for **10 seconds**. Then hide it and ask, in ordinary language:

1. **What deserves attention?**
2. **Why does it matter?**
3. **How certain/current did it appear?**
4. **What would you click to see why AXIGNAL says that?**
5. **What would you click to inspect it in the map?**

## PASS

PASS requires the participant to identify, without internal AXIGNAL terminology:

- at least one material issue when one exists;
- a materially correct reason it matters;
- the visible epistemic/currentness cue or an honest uncertainty statement;
- **Show how AXIGNAL knows** as the evidence action;
- **View in map** as the spatial/deep-link action.

For partial/empty states, PASS requires the participant to understand that observation is still underway and that absence of a surfaced item is not a claim that nothing exists.

## FAIL

FAIL if the participant must first understand the map, cardinal zones, internal object names, governance mechanics, or implementation vocabulary to identify why the view matters.

FAIL if the first screen implies a change that was not temporally established.

FAIL if more than three material items compete for primary attention.

FAIL if a deep link resets spatial context unnecessarily.

## Product invariants

`TODAY != DASHBOARD`

`TODAY ITEM COUNT <= 3`

`NO TEMPORAL DELTA != "CHANGED TODAY"`

`SHOW HOW AXIGNAL KNOWS = PRIMARY PROOF ACTION`

`VIEW IN MAP = CONTEXT-PRESERVING SPATIAL ACTION`

`EMPTY != FALSE`
