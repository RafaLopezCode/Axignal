# Feature Specification: Is a headline about this organization? (Reputation)

**Created**: 2026-10-17

**Status**: Implemented (this PR)

**Input**: CTO, 2026-10-17: Jev in every family. Reputation was the fourth item in the per-family inventory.

## Problem
A headline that contains the organization's name was shown as a mention whose attribution was "not verified". Homonyms could reach a reputation: another company, a person, a place, or a product that shares the name.

## What changes
- **`application/press/attribution.py`** asks one Choice question per headline over a typed state: the name, the website, the activity and the headline. The answers are ABOUT_IT, ANOTHER_ENTITY and UNCLEAR.
- **The read path never calls a provider.** It recalls remembered judgments and queues the missing ones. The background loop (`judge_press_attribution`) judges them with a 60k-token budget, and the results land in the shared judgment memory.
- **Python keeps the last word:**
  - ANOTHER_ENTITY **withholds** the headline, which is the safe direction, and the count is recorded as `withheldAsAnotherEntity`.
  - ABOUT_IT records who judged it.
  - An uncertain or missing judgment leaves the headline exactly as before.
  - Every mention stays POTENTIAL and is never an endorsement (MASTER §54).
- **The self-check and golden runs** judge attributions in their judgment rounds.

## Measured (production, read-only, 2026-10-17)
- 35 real headlines for Iberdrola, Ferrovial, Mercadona, Santander, Orange and Amazon.
- **No wrongful rejection.** Ambiguous cases stay unjudged: "Holded … documental … en Amazon" and "Amazon sold light…" at low confidence.
- **Cost:** $0.00034 per 18 headlines.
- **Homonym withholding is proven by tests.** The current index held no clear homonyms for these names.
