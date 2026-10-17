# Feature Specification: Demand precision. Another activity under a CPV group, and doubtful calls judged first

**Created**: 2026-10-17

**Status**: Implemented (this PR)

**Input**: CTO, 2026-10-17: "arregla los falsos positivos de demanda". The fix is for every account, not per client.

## What the self-check found (release 82deec4)
1. **axignal.com was offered a social-programme notice.** The notice was coded *social research services* (79315000). In CPV, that code sits under *market research* (79310000), which economic intelligence asks for. Social research is another activity.
2. **biocultor.com was offered building-maintenance and works calls carrying a green-area code** (Hacienda Porzuna, Delegación del Gobierno, Las Colinas firebreak works, backhoe works, river restoration works).
   - PLACSP declares no main code, so codes cannot tell what these calls are mainly about.
   - The daily fit judgment had not judged them. It reached only 538 of 3,271 pairs, newest first.
3. **Measured in isolation** with Jev on these calls (12 calls, $0.0004):
   - Every real green-area call reads **CORE (decided)**.
   - The six flagged calls read **PARTIAL or ADJACENT**, but under the confidence threshold. Until now, that meant unknown, so they were shown among the calls that fit best.

## What changes
- **`CPV_OTHER_ACTIVITY`** (governed data, `findings.py`): CPV descendants that are another activity than the group they sit in.
  - Asking for the group never matches them; asking for the code itself still does.
  - It applies in both code matchers (`world_demand.index` and `observation_intelligence.loop`) and in `classified_as`.
  - First entry: 79310000 excludes 79315000.
- **Doubtful calls are judged first** (`world_demand.fit.doubt`). Levels, judged in this order:
  - **0, mixed object:** no main code, or a main code that is other work, and other work among its codes.
  - **1:** no main code, every code the capability's.
  - **2:** main code the capability's.
  - **3:** additional code only, already labelled as such.

  Newest first within a level. On the production index, all six flagged calls are now in level 0 (389 of 3,268 pairs), within the self-check's budget.
- **A doubtful judgment is never its label.**
  - One leaning to CORE stays unknown, as before.
  - One leaning elsewhere is `UNCERTAIN`: the call goes to "Other possible" with the reason "it is unclear that the main work is its activity". It is ranked after unjudged calls, never set aside and never hidden.
  - Promotion still requires confidence.
- **Self-check.** A call set apart as possibly other work (adjacent or its fit in doubt) is presented truthfully, like an additional code, and is counted as `labelledDoubtful`. A partial fit still counts as presented about the activity.

## Not changed, and why
The Canal de Castilla call (Confederación Hidrográfica del Duero) is still reported against biocultor.com. Its own main CPV is *planting and maintenance of green areas* (77310000), and Jev judged it CORE. The truth's title words do not match its national title. Whether that truth should accept it is a CTO decision, not something to adjust in order to pass.

## Doctrine
- UNKNOWN is never FALSE: a doubtful judgment is not UNRELATED and is never set aside.
- Inference is never promoted: no low-confidence label is shown as the call's fit.
- Python has the last word.
- Opportunities stay POTENTIAL.
