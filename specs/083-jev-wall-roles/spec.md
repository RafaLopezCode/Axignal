# Feature Specification: Jev reads what the organizations on a logo wall are

**Created**: 2026-10-17

**Status**: Implemented (this PR); measured before promotion

**Input**: CTO, 2026-10-17: Jev with typed context in every family. Relationships was second in the per-family inventory.

## Problem
Logo walls were read as clients or partners from their heading alone, by a governed vocabulary:
- "Partners" over press logos became partners.
- "Ils utilisent nos produits" or "Customer Stories" were never read.

## What changes
- **`application/own_site/wall_roles.py`** asks one Choice question per wall (at most 8) over its heading and the names shown under it. The answers are CLIENTS, PARTNERS, SUPPLIERS_OR_TECHNOLOGY, PRESS, CREDENTIALS, MEMBERSHIPS, FUNDERS, NOT_ORGANIZATIONS and UNCLEAR.
- **Python keeps the last word:**
  - Reading a wall as **clients or partners needs ≥ 0.7** confidence.
  - Reading it as **neither** needs only a usable answer, because that is the safe direction.
  - Uncertain or missing answers leave the vocabulary's reading untouched.
  - Certification walls are never counterparties.
- **Epistemic state:** a role only the evaluator read is **POTENTIAL**. A role both agree on stays DECLARED. Every wall records `roleBy` (VOCABULARY or SEMANTIC_JUDGMENT) and the model.
- **One batch per first observation**, through the same cascade, budget and ledger as the activity batch.

## Measured (production, read-only, 2026-10-17, 10 real sites, 26 walls, $0.00036)
- **New clients found:**
  - Plain Concepts "Customer Stories": Acciona, Mediaset, Ferrovial, Coca-Cola (0.98).
  - Factorial "Historias reales…" (0.94).
  - Zitron project references (0.78).
- **New partners found:** Paradigma "¿Nuestro secreto? Trabajar con los mejores": Google Cloud, Red Hat, AWS, Microsoft (0.75).
- **Rejected as not organizations:** menus ("Submenu, Search, Open menu"), values ("honestidad, cultura") and feature lists (0.64–0.94).
- **Withheld by the 0.7 floor:** "Solution 01, …, Disney." (0.63).

## Tests
`tests/own_site/test_wall_roles.py`: one question per wall; the evaluator decides and uncertainty keeps the vocabulary; promotions need confidence; without judgments the reading is exactly as before.
