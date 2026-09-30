"""Experimental Jev implementation of the germination evidence-support port.

This adapter is deliberately outside production application/pipeline wiring.
It demonstrates the exact state boundary needed to evaluate Jev without giving
Jev canonical authority.
"""

from __future__ import annotations

import hashlib
import json

from application.xeed_germination import (
    EvidenceSupportClass,
    EvidenceSupportJudgment,
    InvestigationFinding,
)
from experiments.decision_lab.germination_corpus import CONTRACT_ID, load_question
from experiments.decision_lab.models import LabError
from experiments.decision_lab.providers.typesafe import TypeSafeLabEvaluator
from experiments.decision_lab.requests_vnext import (
    ValidatedProviderRequest,
    prepare_provider_request,
)

CONTRACT_VERSION = "CES.SUPPORT.vNext.2"
MODEL = "jev-1.13.0"


class JevEvidenceSupportJudge:
    """Build answerable evidence state, invoke pinned Jev, preserve a replay reference."""

    def __init__(self, evaluator: TypeSafeLabEvaluator, *, model: str = MODEL) -> None:
        self._evaluator = evaluator
        self._model = model
        self._question = load_question()

    def _request(self, finding: InvestigationFinding) -> ValidatedProviderRequest:
        evidence = finding.evidence
        evidence_id = evidence.id
        source_state = {
            "state_contract_version": "claim-evidence.vNext.1",
            "claim": {"proposition": finding.claim_proposition},
            "evidence_refs": [evidence_id],
        }
        evidence_catalog = {
            evidence_id: {
                "content": evidence.extracted_claim,
                "provenance": {
                    "source_ref": evidence.reference,
                    "source": evidence.source,
                    "source_type": evidence.source_type,
                    "observed_at": evidence.observed_at.isoformat(),
                },
            }
        }
        prepared = prepare_provider_request(
            CONTRACT_ID,
            source_state,
            self._question,
            evidence_catalog,
        )
        if not isinstance(prepared, ValidatedProviderRequest):
            raise LabError("claim-evidence support unexpectedly resolved deterministically")
        return prepared

    def judge(self, finding: InvestigationFinding) -> EvidenceSupportJudgment:
        request = self._request(finding)
        state, question = request.provider_payload()
        state_fingerprint = hashlib.sha256(
            json.dumps(state, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
                "utf-8"
            )
        ).hexdigest()
        question_fingerprint = hashlib.sha256(
            json.dumps(question, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
                "utf-8"
            )
        ).hexdigest()
        replay_reference = hashlib.sha256(
            json.dumps(
                {"state": state, "question": question, "model": self._model},
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ).encode("utf-8")
        ).hexdigest()
        judgments, failure, _ = self._evaluator.evaluate(request, model=self._model)
        if failure is not None:
            raise LabError(f"JEV_OPERATIONAL_FAILURE:{failure.category}")
        if len(judgments) != 1:
            raise LabError("JEV_RESPONSE_CARDINALITY_INVALID")
        judgment = judgments[0]
        if judgment.status != "ANSWERED" or not isinstance(judgment.value, str):
            raise LabError("JEV_JUDGMENT_MISSING_OR_MALFORMED")
        try:
            support = EvidenceSupportClass(judgment.value)
        except ValueError as exc:
            raise LabError("JEV_ANSWER_OUTSIDE_AXIGNAL_CONTRACT") from exc
        distribution = tuple(sorted((judgment.distribution or {}).items()))
        return EvidenceSupportJudgment(
            support=support,
            evaluator="typesafe-sdk",
            contract_version=CONTRACT_VERSION,
            model=judgment.resolved_model or self._model,
            distribution=distribution,
            confidence=judgment.confidence,
            state_fingerprint=state_fingerprint,
            question_fingerprint=question_fingerprint,
            raw_reference=replay_reference,
        )
