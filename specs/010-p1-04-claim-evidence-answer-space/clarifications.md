# Clarification Record: P1-04 Claim Evidence Answer Space

**Date:** 2026-09-26
**Source:** CTO order and repository contracts; no unresolved user decision required.

1. **Empty evidence vs. no relevant evidence:** the state contract still requires at least one supplied passage. With zero passages, deterministic answerability is `NOT_ANSWERABLE`; `NO_EVIDENCE` is reachable only if one or more passages exist and none is relevant to the claim.
2. **Evidence conflict vs. claim contradiction:** `CONFLICTING` denotes materially incompatible supplied evidence assertions about the same proposition/scope/time. `CONTRADICTED` denotes coherent relevant evidence directly refuting one or more material assertions required by the claim.
3. **Compound claims:** resolve evidence-source conflict first; otherwise a direct refutation of any material assertion takes precedence over partial support. `PARTIAL` applies when a material subset is supported and remaining material assertions are neither supported nor refuted.
4. **Version identity:** preserve `CES.SUPPORT.vNext` at `vNext.1`; register `CES.SUPPORT.vNext.2` independently so exact fingerprints continue to bind provider-visible semantics.

No clarification markers remain. These interpretations are constrained by the explicit CTO requirements and do not broaden product scope.
