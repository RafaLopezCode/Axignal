r"""Offline audit probes. No network, secrets, persistence, or production mutations.

Run from the repository root:
    .\.venv\Scripts\python.exe docs/audits/brain-2026-10-04/reproduce_evidence_and_budget.py

These probes intentionally display current behavior rather than assert the fix.
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))


def probe_evidence_semantic_binding() -> dict[str, object]:
    from domain.evidence.admission import (
        AdmissionRequest,
        Evidence,
        EvidenceAdmission,
        GroundedClaim,
        SourceAuthority,
    )

    claim = "ACME manufactures industrial pumps."
    evidence = Evidence(
        id="audit-offline-evidence",
        source="ACME official web",
        source_type="OFFICIAL_WEB",
        reference="https://acme.example",
        extracted_claim=claim,
        observed_at=datetime(2026, 10, 4, tzinfo=UTC),
        authority=SourceAuthority.OFFICIAL_WEB,
        observation_subject_id="org:acme",
        grounded_claim=GroundedClaim(
            subject_id="org:acme",
            predicate="manufactures",
            object_or_value="industrial pumps",
            subject_mention="ACME",
            predicate_mention="manufactures",
            object_mention="industrial pumps",
            supporting_excerpt=claim,
        ),
    )
    request = AdmissionRequest(
        evidence=evidence,
        subject_id="org:unrelated",
        predicate="manufactures",
        object_or_value="nuclear weapons",
        claim_proposition=claim,
    )
    decision = EvidenceAdmission.admit_claim(request)
    return {
        "probe": "semantic_tuple_not_established_by_evidence",
        "evidence_claim": claim,
        "wrong_tuple_admitted": decision.admitted,
        "rejection_reason": decision.reason,
        "persisted": False,
    }


def probe_budget_unknown_cost_recovery() -> dict[str, object]:
    from application.economic_discovery.execution_budget import (
        ExecutionBudgetDelta,
        ExecutionBudgetPolicy,
        ExecutionBudgetState,
        advance_execution_budget,
    )

    policy = ExecutionBudgetPolicy(
        policy_id="audit-budget",
        version="1",
        currency="EUR",
        max_amount_microunits=10,
    )
    initial = ExecutionBudgetState(amount_microunits=7, currency="EUR")
    unknown = advance_execution_budget(policy=policy, state=initial, delta=ExecutionBudgetDelta())
    later_known = advance_execution_budget(
        policy=policy,
        state=unknown,
        delta=ExecutionBudgetDelta(amount_microunits=1, currency="EUR"),
    )
    return {
        "probe": "unknown_accumulated_cost_becomes_partial_known_sum",
        "initial_cost": initial.amount_microunits,
        "after_unknown_delta": unknown.amount_microunits,
        "after_unknown_complete": unknown.cost_complete,
        "after_later_known_delta": later_known.amount_microunits,
        "after_later_known_complete": later_known.cost_complete,
        "known_spending_lower_bound": 8,
        "correct_total_is_unknown": not later_known.cost_complete,
        "persisted": False,
    }


if __name__ == "__main__":
    print(json.dumps(probe_evidence_semantic_binding(), sort_keys=True))
    print(json.dumps(probe_budget_unknown_cost_recovery(), sort_keys=True))
