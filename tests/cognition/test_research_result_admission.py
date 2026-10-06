from __future__ import annotations

from datetime import UTC, datetime, timedelta

from application.economic_discovery.batch_research import claim_research_batch
from application.economic_discovery.continuous_observation import SharedObservationIntent
from cognition.jobs.model import StructuredResult
from cognition.research_result_admission import EvidenceBackedResearchAdmission
from pipeline.continuous_observation.sqlite_store import SqliteSharedObservationWorkMemory

NOW = datetime(2026, 10, 6, 8, 0, tzinfo=UTC)


def _claimed(tmp_path):
    memory = SqliteSharedObservationWorkMemory(tmp_path / "work.sqlite3")
    intent = SharedObservationIntent(
        subject_id="org:axignal",
        state_fingerprint="state:1",
        dimension_id="seo",
        missing_requirements=("seo title evidence", "geo public evidence"),
        research_policy_id="research-value",
        research_policy_version="1",
        research_context_fingerprint="ctx:1",
    )
    memory.enqueue(intent, "prime:test")
    return claim_research_batch(
        memory,
        work_keys=(intent.work_key,),
        now=NOW,
        lease_for=timedelta(minutes=5),
        max_batch_size=1,
    )[0]


def _result(research):
    return StructuredResult(
        job_id="research:test",
        provider="openai-batch",
        payload={"provider_version": "gpt-5.6-luna", "research": research},
    )


def test_admits_only_when_all_requirements_have_public_provenance(tmp_path) -> None:
    work = _claimed(tmp_path)
    research = {
        "status": "EVIDENCE_FOUND",
        "evidence_candidates": [
            {
                "requirement": "seo title evidence",
                "source_url": "https://axignal.com/",
                "excerpt": "Public title evidence",
            },
            {
                "requirement": "geo public evidence",
                "source_url": "https://axignal.com/about",
                "excerpt": "Public geographic evidence",
            },
        ],
        "unresolved_requirements": [],
    }
    assert EvidenceBackedResearchAdmission().admit(work=work, result=_result(research)) is True


def test_partial_or_explicitly_unresolved_result_is_not_admitted(tmp_path) -> None:
    work = _claimed(tmp_path)
    research = {
        "status": "EVIDENCE_FOUND",
        "evidence_candidates": [
            {
                "requirement": "seo title evidence",
                "source_url": "https://axignal.com/",
                "excerpt": "Public title evidence",
            }
        ],
        "unresolved_requirements": ["geo public evidence"],
    }
    assert EvidenceBackedResearchAdmission().admit(work=work, result=_result(research)) is False


def test_non_public_or_malformed_provenance_fails_closed(tmp_path) -> None:
    work = _claimed(tmp_path)
    base = {
        "status": "EVIDENCE_FOUND",
        "evidence_candidates": [
            {
                "requirement": "seo title evidence",
                "source_url": "http://localhost/private",
                "excerpt": "not public",
            },
            {
                "requirement": "geo public evidence",
                "source_url": "https://axignal.com/about",
                "excerpt": "Public geographic evidence",
            },
        ],
        "unresolved_requirements": [],
    }
    assert EvidenceBackedResearchAdmission().admit(work=work, result=_result(base)) is False
    assert (
        EvidenceBackedResearchAdmission().admit(
            work=work,
            result=_result(
                {"status": "NO_EVIDENCE", "evidence_candidates": [], "unresolved_requirements": []}
            ),
        )
        is False
    )
    assert EvidenceBackedResearchAdmission().admit(work=work, result=_result({})) is False
