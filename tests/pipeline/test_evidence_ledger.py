from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from domain.evidence import Evidence, SourceAuthority, evidence_fingerprint
from pipeline.evidence import EvidenceLedger, EvidenceLedgerConflict

NOW = datetime(2026, 10, 4, 0, 0, tzinfo=UTC)


def _evidence(*, evidence_id: str = "ev:legacy:1") -> Evidence:
    return Evidence(
        id=evidence_id,
        source="fixture:official",
        source_type="web",
        reference="https://example.test/about",
        extracted_claim="ACME manufactures industrial pumps.",
        observed_at=NOW,
        authority=SourceAuthority.OFFICIAL_WEB,
    )


def test_exact_replay_is_idempotent_and_resolves_one_exact_content() -> None:
    ledger = EvidenceLedger()
    evidence = _evidence()

    assert ledger.append(evidence) is True
    assert ledger.append(replace(evidence)) is False

    assert len(ledger) == 1
    assert ledger.entries == (evidence,)
    assert ledger.get(evidence.id) == evidence
    assert evidence_fingerprint(ledger.get(evidence.id)) == evidence_fingerprint(evidence)


@pytest.mark.parametrize(
    "changed",
    [
        lambda evidence: replace(
            evidence,
            extracted_claim="ACME does not manufacture industrial pumps.",
        ),
        lambda evidence: replace(
            evidence,
            observed_at=evidence.observed_at + timedelta(seconds=1),
        ),
        lambda evidence: replace(
            evidence,
            authority=SourceAuthority.CORPORATE_DOCUMENT,
        ),
        lambda evidence: replace(
            evidence,
            reference="https://example.test/changed",
        ),
        lambda evidence: replace(
            evidence,
            source="fixture:changed",
        ),
    ],
)
def test_same_evidence_id_with_changed_immutable_content_fails_closed(changed) -> None:
    ledger = EvidenceLedger()
    original = _evidence()
    assert ledger.append(original) is True

    with pytest.raises(EvidenceLedgerConflict, match="different immutable content"):
        ledger.append(changed(original))

    assert ledger.entries == (original,)
    assert ledger.get(original.id) == original


def test_new_evidence_id_preserves_history_in_append_order() -> None:
    ledger = EvidenceLedger()
    first = _evidence(evidence_id="ev:legacy:1")
    second = replace(
        first,
        id="ev:legacy:2",
        observed_at=first.observed_at + timedelta(days=1),
        extracted_claim="ACME manufactures industrial pumps in Spain.",
    )

    assert ledger.append(first) is True
    assert ledger.append(second) is True

    assert ledger.entries == (first, second)
    assert ledger.get(first.id) == first
    assert ledger.get(second.id) == second
    assert evidence_fingerprint(first) != evidence_fingerprint(second)


def test_unknown_evidence_identity_resolves_none() -> None:
    ledger = EvidenceLedger()

    assert ledger.get("ev:missing") is None
