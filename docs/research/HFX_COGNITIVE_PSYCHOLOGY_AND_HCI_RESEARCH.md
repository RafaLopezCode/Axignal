# HFX Cognitive Psychology & HCI Research Synthesis

**Status:** dated literature synthesis supporting P0-HFX-00  
**Research reviewed:** 2026-09-26  
**Role:** Evidence and design constraints; subordinate to MASTER/Constitution/ADRs  
**No AXIGNAL user study has been run or is claimed in this document.**

## How to interpret this synthesis

The external CTO package in `D:\AXIGNAL\HFX-RESEARCH-INPUT\` was read as
reference input. It is not copied into this repository and is not canonical
authority. Its assertions were checked against primary research, W3C material
and official PostgreSQL/pgvector documentation where applicable.

This document distinguishes four classes:

| Class | Status |
|---|---|
| **Empirical HCI evidence** | Result in a specific study or synthesis; generalize only with stated limitations. |
| **Established guidance** | W3C standard, working-group guidance or interaction heuristic; not a proof of causal benefit. |
| **AXIGNAL inference** | A design implication that fits evidence and product doctrine, still requiring product validation. |
| **CTO hypothesis** | A proposed AXIGNAL outcome not established by external literature. |

Research can constrain the design and research method. It cannot establish that
AXIGNAL users will understand faster, make better decisions, trust more
appropriately, or return more often.

## Evidence reviewed and bounded implications

| Topic and primary source | What the source supports | AXIGNAL implication and limit |
|---|---|---|
| Working memory: Cowan, 2001, [Behavioral and Brain Sciences](https://pubmed.ncbi.nlm.nih.gov/11515286/) | Review argues that capacity under controlled conditions is closer to about four chunks than the popular “7±2,” with chunking and task conditions mattering. | **Inference:** do not use user working memory as AXIGNAL's storage layer; keep comparison context visible. **Limit:** four is not a screen-card limit or universal capacity law. |
| Representation/task fit: Vessey, 1991, [Decision Sciences](https://doi.org/10.1111/j.1540-5915.1991.tb00344.x) | Cognitive-fit theory describes when graphical/spatial vs tabular/symbolic representations match task demands; outcomes vary with task/process/representation fit. | **Inference:** choose a trend, table, graph/path or trace by user question. **Limit:** does not canonize a representation for any AXIGNAL object; validate real tasks. |
| External representations: Scaife & Rogers, 1996, [International Journal of Human-Computer Studies](https://doi.org/10.1006/ijhc.1996.0048) | Review critiques assumptions that graphical technology automatically improves cognition and frames the relation between external and internal representations. | **Inference:** a graph or visual treatment must make relevant structure easier to reason about; spectacle is not evidence of cognitive benefit. |
| Visual clutter: Rosenholtz, Li & Nakano, 2007, [Journal of Vision](https://doi.org/10.1167/7.2.17) | Studies visual clutter measures and discusses how clutter can impair search, recognition or segmentation under studied conditions. | **Inference:** test first-scan and search tasks, not just preference. **Limit:** no universal density threshold or “one question per screen” result follows. |
| Interruptions/resumption: Trafton et al., 2003, [International Journal of Human-Computer Studies](https://doi.org/10.1016/S1071-5819(03)00023-5) | A lab study found an 8-second warning/interruption lag condition prepared more and resumed faster than immediate interruption; practice also mattered. | **Inference:** preserve task goal and useful checkpoint cues. **Limit:** lab task and short interruption do not establish the optimum AXIGNAL checkpoint or 30-day return design. |
| Uncertainty display: Riveiro et al., 2014, [Computers & Graphics](https://doi.org/10.1016/j.cag.2014.02.006) | Study of 22 air-traffic operators found uncertainty visualization changed some attempts/priority selections but did not significantly change classification performance or stated confidence/workload in that scenario. | **Inference:** uncertainty should not be hidden, and its presentation must be tested for interpretation. **Limit:** encoding and safety-critical task do not transfer directly to economic intelligence. |
| Analytics dashboards: Hjelle et al., 2024, [Information & Management](https://doi.org/10.1016/j.im.2024.104011) | Experiment with mock-up dashboards and 524 participants reported indirect effects of information format, currency and completeness through information satisfaction/task-complexity perceptions. | **Inference:** currentness, scope and useful completeness can affect comprehension. **Limit:** recruited sample, fictional scenarios and mock-ups are not AXIGNAL-specific causal evidence. |
| Human-AI interaction: Amershi et al., 2019, [CHI paper from Microsoft Research](https://www.microsoft.com/en-us/research/wp-content/uploads/2019/01/Guidelines-for-Human-AI-Interaction-camera-ready.pdf) | Research synthesis and evaluation produced guidelines for human-AI interaction across design stages. | **Inference:** make system capability/limits and user control legible; treat as guidance. It does not guarantee appropriate reliance in AXIGNAL. |
| Verifiability and AI explanations: Fok et al., 2024, [AI Magazine](https://doi.org/10.1002/aaai.12182) | Argues that explanations rarely enable complementary human-AI decision performance unless they support verification; fluency alone does not make an explanation verifiable. | **Inference:** AXENT “why” must lead to persisted supporting state and evidence. **Limit:** theoretical framing and examined tasks do not validate a specific AXIGNAL trace UI. |
| Cognitive accessibility: [W3C COGA Working Group Note](https://www.w3.org/TR/coga-usable/) | Supplemental patterns cover clear purpose, language, navigation, memory demands, numerical alternatives, personalization and testing with users. W3C labels it a Working Group Note, not a WCAG conformance requirement. | **Inference:** plan cognitive accessibility beyond automated checks and include affected users. Follow guidance contextually, not as a guarantee. |
| Web accessibility: [WCAG 2.2 Recommendation](https://www.w3.org/TR/WCAG22/) | Testable technology-neutral success criteria; W3C describes conformance as combining automated and human evaluation and notes that needs are not all met by the criteria. | **Canonical target:** future production surfaces target AA. WCAG conformance does not equal complete cognitive usability. |

The external evidence supports constraints and questions. It does **not** prove
the CTO's product mechanisms as universal laws. In particular, “Cognitive
Jevons,” Interpretation Debt, Human Cognitive Amortization and expertise-tax
reduction are AXIGNAL product hypotheses/concepts.

## Research domains and disciplined use

- **Working memory, chunking and external cognition:** preserve task context and
  make useful relationships visible; never infer a fixed card/chunk count.
- **Recognition and recall:** keep current scope, object identity, comparisons
  and routes to inspected evidence recoverable. Nielsen's “recognition rather
  than recall” is an established usability heuristic, not a primary experiment.
- **Cognitive fit, Gestalt grouping, preattentive attention and visual memory:**
  treat grouping and visual cues as task-specific candidates; reserve salient
  channels and validate them. Do not claim a cue is universally preattentive.
- **Progressive disclosure, semantic zoom and focus+context:** make first
  meaning available and detail inspectable, with direct jumps and orientation.
  Avoid deep nesting. These are design hypotheses for HFX, not a validated
  product geometry.
- **Information foraging/scent and spatial memory:** labels should communicate
  what information lies behind them; stable positions may aid orientation but
  must not override responsive or accessible design.
- **Change blindness and comparisons:** keep comparable states juxtaposed and
  identify period, scope and instrument; users should not have to compare
  separated values from memory.
- **Numeracy and uncertainty:** explain denominator and scope, distinguish
  missing knowledge from negative evidence, and test whether people confuse
  unknown with false or potential with observed.
- **Trust calibration and automation bias:** the goal is appropriate reliance,
  not maximum trust. Test supported, unknown, stale, contradicted and potential
  claims, including whether participants challenge an unsupported conclusion.
- **Decision framing and dashboard cognition:** preserve enough completeness and
  currentness for the task without making every available metric equally
  prominent. Do not claim the dashboard study proves an AXIGNAL layout.
- **Accessibility cognition:** include keyboard/screen-reader alternatives,
  clear purpose, stable structure, plain language, numerical explanations,
  reduced motion and users with diverse cognitive/accessibility needs.

## AXIGNAL-specific hypotheses (not findings)

The following require representative product tests before they can be stated as
AXIGNAL outcomes:

1. A prioritized Today projection identifies a material change faster and more
   accurately than a conventional KPI layout.
2. Semantic depth and horizontal relationship navigation reduce navigation
   recall without obscuring relevant context.
3. Plain-language meaning first supports non-specialists while preserving
   expert access to methods and evidence.
4. Stable multimodal epistemic cues improve distinction among observed,
   inferred, potential, unknown, stale and contradicted states.
5. Private cognitive continuity reduces return/resumption errors and time after
   meaningful interruptions.
6. Recorded provenance makes “why was I following this?” answerable without
   fabricated retrospective explanations.
7. AXENT navigation reaches inspectable state with less reorientation than
   prose-only interaction and does not make chat a prerequisite.
8. Human Cognitive Amortization reduces repeated reconstruction while privacy,
   consent, deletion and retention remain understandable.
9. “No mental joins” improves meaning accuracy when AXIGNAL already governs the
   relevant dependency graph.
10. Clear uncertainty and evidence paths improve calibrated reliance rather
    than simply increasing stated trust.

## Research instrument cautions

Candidate methods are selected by question, not cargo-culted:

- **Task behavior:** success, meaning/epistemic accuracy, time to first correct
  meaning, evidence retrieval, scope/comparison errors, navigation/backtracking
  and resumption lag.
- **SEQ:** task-level perceived ease after each benchmark task.
- **UMUX-LITE / SUS:** perceived usefulness/usability at a defined study
  milestone; neither measures epistemic comprehension by itself.
- **NASA-TLX / Paas effort rating:** workload or perceived mental effort when
  the task and protocol make that construct relevant; do not treat it as
  comprehension.

Pre-register which question an instrument answers, use consistent protocols,
and pair self-report with observed correctness. No universal HFX threshold is
canonized before a baseline.

## Technical and architecture evidence

This work did not select or implement a production persistence stack. Current
official documentation supports the following bounded observations:

- [PostgreSQL row-security policies](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
  require a policy for normal access when RLS is enabled; no applicable policy
  is default-deny. Table owners typically bypass RLS unless separately forced,
  and privileged roles require careful control. This is a security mechanism,
  not proof a multi-tenant architecture is safe.
- [PostgreSQL recursive queries](https://www.postgresql.org/docs/current/queries-with.html)
  support recursive traversal over relational edges. This makes SQL a plausible
  initial place to evaluate provenance paths; no workload benchmark proves it
  will remain sufficient.
- [pgvector](https://github.com/pgvector/pgvector) supports exact search and
  approximate HNSW/IVFFlat indexes. Its documentation notes that approximate
  index filtering occurs after index scanning and can yield fewer results for
  selective filters. Retrieval scoping and RLS must therefore be benchmarked
  under real client cardinality; vector similarity is never authorization,
  identity, causality or canonical truth.
- No measured HFX workload establishes need for a separate vector store, graph
  database, search cluster or distributed cache. Simplicity favors evaluating
  the current PostgreSQL direction first, but **PostgreSQL + pgvector remains a
  CTO architecture hypothesis, not a canonical vendor selection or production
  decision**.

## Source register

Primary/official sources reviewed for this synthesis:

1. Cowan (2001), “The magical number 4 in short-term memory,” DOI
   `10.1017/S0140525X01003922`, [PubMed record](https://pubmed.ncbi.nlm.nih.gov/11515286/).
2. Vessey (1991), “Cognitive Fit,” DOI
   `10.1111/j.1540-5915.1991.tb00344.x`, [publisher record](https://doi.org/10.1111/j.1540-5915.1991.tb00344.x).
3. Scaife & Rogers (1996), “External cognition,” DOI
   `10.1006/ijhc.1996.0048`, [publisher record](https://doi.org/10.1006/ijhc.1996.0048).
4. Rosenholtz, Li & Nakano (2007), “Measuring visual clutter,” DOI
   `10.1167/7.2.17`, [Journal of Vision](https://doi.org/10.1167/7.2.17).
5. Trafton et al. (2003), “Preparing to resume an interrupted task,” DOI
   `10.1016/S1071-5819(03)00023-5`, [publisher record](https://doi.org/10.1016/S1071-5819(03)00023-5).
6. Riveiro et al. (2014), “Effects of visualizing uncertainty,” DOI
   `10.1016/j.cag.2014.02.006`, [publisher record](https://doi.org/10.1016/j.cag.2014.02.006).
7. Hjelle et al. (2024), “Organizational decision making and analytics,” DOI
   `10.1016/j.im.2024.104011`, [publisher record](https://doi.org/10.1016/j.im.2024.104011).
8. Amershi et al. (2019), “Guidelines for Human-AI Interaction,” DOI
   `10.1145/3290605.3300233`, [paper](https://www.microsoft.com/en-us/research/wp-content/uploads/2019/01/Guidelines-for-Human-AI-Interaction-camera-ready.pdf).
9. Fok et al. (2024), “In search of verifiability,” DOI
   `10.1002/aaai.12182`, [AI Magazine](https://doi.org/10.1002/aaai.12182).
10. W3C, [WCAG 2.2](https://www.w3.org/TR/WCAG22/) and [Making Content Usable
    for People with Cognitive and Learning Disabilities](https://www.w3.org/TR/coga-usable/).
11. PostgreSQL, [Row Security Policies](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
    and [WITH Queries](https://www.postgresql.org/docs/current/queries-with.html).
12. pgvector, [official project documentation](https://github.com/pgvector/pgvector).

Additional navigation guidance such as Nielsen's recognition heuristic,
progressive disclosure, information scent and focus+context is classified as
design guidance in HFX, not as a substitute for primary study evidence. Source
identifiers and links in the CTO package were not adopted as proof without
checking their stated scope.
