# Feature Specification: Presence — what the site communicates vs what it is

**Created**: 2026-10-17

**Status**: Implemented (this PR)

**Input**:
- The CTO on biocultor.com: "está en la web y Jev está haciendo bien su trabajo".
- The per-family inventory, third item: make "your site communicates X" an explicit Presence finding.

## What changes
1. **`OFFER_NATURE_UNCLEAR` (REPRESENTATION_GAP, POTENTIAL, derived, not causal).**
   - **When:** `fo_offer_nature` was asked and its answer was uncertain or UNCLEAR.
   - **Biocultor:** MIXED 0.59 vs SUPPLIES 0.41.
   - **Message:** the site does not make clear whether it sells products, performs services or carries out works.
   - **Never emitted for:**
     - a clear MIXED answer: it does both, and says so;
     - a parked or placeholder site.
   - **Proposal shown:** say in the title and the first sentence what you sell or do, present any secondary service separately, and observe again afterwards.
   - The web copy is in all 6 languages.
2. **The noindex audit judges only pages that carry the offer.**
   - **Found on axignal.com:** reading its contact page (#296) raised `NO_NOINDEX_ON_READ_PAGES` with HIGH impact. Legal and contact pages are often kept out of search on purpose, and their noindex says nothing about how the offer is found.
   - **The check now skips:** legal pages (`LEGAL_PAGE`) and contact or location pages (the same governed vocabulary as page selection).

## Doctrine
MASTER §54: Digital Representation Intelligence is observation, not SEO execution. A RepresentationGap is derived, not a FAXT. The judgment is non-authoritative and never shown as a probability.

## Tests
- **Unit:** uncertain and UNCLEAR are named; a clear MIXED or SUPPLIES is not.
- **End to end:**
  - an unclear site gets the gap, a parked one does not;
  - a noindex contact page leaves the check at PASS, and that test fails on main.
- **Web:** the copy is shown in the reader's language.
