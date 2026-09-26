# Implementation Plan: P1-04 Claim Evidence Answer Space

## Objective and boundaries

Add a separately versioned experimental claim/evidence question and `DecisionContract` for V-next.2, while preserving the V-next.1 grammar, contract fingerprint, state shape, historic replay, and all provider/canonical-authority boundaries. No provider call path or P0-JEV-04 execution is part of this slice.

## Architecture review

**Decision:** Keep the state contract at `claim-evidence.vNext.1` because the input shape is unchanged. Add a new question ID and contract key, `CES.SUPPORT.vNext.2`, with question version `vNext.2`, contract version `decision-contract.vNext.2`, its own semantic fingerprint, and a standalone immutable question artifact. Do not modify the V-next.1 question in `grammar/vnext/grammar.json` or its registry entry.

**Registry strategy:** `DECISION_CONTRACTS` and `QUESTION_SEMANTIC_FINGERPRINTS` are already keyed by question ID. Register V-next.2 under a new key; exact version and fingerprint checks remain centralized in `validate_question_binding`. The existing V-next.1 grammar validator remains locked to the 12-question `vNext.1` artifact and is not repurposed to reinterpret history.

**Answer classification:** Distinguish source-source disagreement (`CONFLICTING`) from a coherent source bundle refuting a material claim assertion (`CONTRADICTED`). Use explicit precedence for compound cases: unresolved material source conflict first; otherwise direct contradiction; full support; partial support; relevant neutral/non-support; no relevant supplied passage; genuinely indeterminate residual case. `NO_EVIDENCE` does not mean that the input contained no passage. The deterministic answerability gate checks declared shape/provenance and does not decide relevance.

**Constitution check:** The change is consistent with epistemic neutrality, claim ≠ write, evidence admission, `UNKNOWN ≠ FALSE`, provider replacement, and historical replay under original contracts. It changes no canonical state, production path, or authority.

## Affected systems

- `experiments/decision_lab/contracts_vnext.py`: additive V-next.2 contract and fingerprint registration.
- `experiments/decision_lab/grammar/vnext/claim-evidence-support.vNext.2.json`: new standalone question artifact.
- `tests/experiments/test_decision_contracts_vnext.py`: V1 immutability, V2 semantics and cross-binding regression coverage.
- `specs/010-p1-04-claim-evidence-answer-space/`: lifecycle, proof, recovery research and validation record.

## Rollback

Revert only the additive V-next.2 artifact, registry entry, tests, and this feature documentation. Preserve the V-next.1 grammar, original registry entry, historical fingerprints, P0-JEV artifacts, and all ignored local artifacts.

## Verification strategy

1. Capture the original V-next.1 question fingerprint, answer-space IDs, and grammar bytes/hash before implementation.
2. Add offline tests for every required semantic state, answerability distinction, semantic drift, and cross-version binding failure.
3. Run frozen sync, Ruff format/check, mypy, full pytest, Architecture Guard, governance, diff check, and Graphify update/diagnose.
4. Do not call any provider, inspect or access credentials, or run P0-JEV-04.
