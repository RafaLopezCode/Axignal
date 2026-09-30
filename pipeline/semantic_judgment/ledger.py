"""Append-only runtime ledger for replayable semantic judgments.

This is process-local plumbing, not canonical persistence and not truth authority.
"""

from __future__ import annotations

from dataclasses import dataclass

from application.xeed_germination import EvidenceSupportJudgment, InvestigationFinding


@dataclass(frozen=True, slots=True)
class SemanticJudgmentRecord:
    faxt_id: str
    evidence_id: str
    claim_proposition: str
    judgment: EvidenceSupportJudgment


class SemanticJudgmentLedger:
    def __init__(self) -> None:
        self._entries: list[SemanticJudgmentRecord] = []

    def append(
        self,
        finding: InvestigationFinding,
        judgment: EvidenceSupportJudgment,
    ) -> None:
        if not isinstance(finding, InvestigationFinding):
            raise TypeError("semantic judgment ledger requires InvestigationFinding")
        if not isinstance(judgment, EvidenceSupportJudgment):
            raise TypeError("semantic judgment ledger requires EvidenceSupportJudgment")
        self._entries.append(
            SemanticJudgmentRecord(
                faxt_id=str(finding.faxt_id),
                evidence_id=finding.evidence.id,
                claim_proposition=finding.claim_proposition,
                judgment=judgment,
            )
        )

    @property
    def entries(self) -> tuple[SemanticJudgmentRecord, ...]:
        return tuple(self._entries)
