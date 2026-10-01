from datetime import UTC, datetime, timedelta

from application.admin_xeed_observatory import project_xeed_axigland_observatory
from application.economic_discovery.learning_memory import (
    LearningCost,
    LearningEvent,
    LearningEventKind,
    LearningMechanism,
    LearningOutcome,
    LearningYield,
)
from domain.admin_observability import (
    AdminEventEnvelope,
    AdminPrivacyClass,
    AdminRecordClass,
    AdminRecordId,
    DataCompleteness,
)

NOW = datetime(2026, 10, 1, 21, 30, tzinfo=UTC)


def _event(
    event_id: str,
    *,
    xeed_id: str = "xeed-1",
    occurred_at: datetime = NOW,
    outcome: LearningOutcome = LearningOutcome.COMPLETED,
    reused: int = 0,
    added: int = 0,
    xignals: int = 0,
    admissions: int = 0,
    cost: int | None = None,
) -> LearningEvent:
    return LearningEvent(
        event_id=event_id,
        kind=LearningEventKind.DETERMINISTIC_EVALUATION,
        outcome=outcome,
        occurred_at=occurred_at,
        subject_id="org-1",
        activity_ref=f"activity:{event_id}",
        policy_id="policy",
        policy_version="1",
        code_sha="a" * 40,
        mechanism=LearningMechanism.DETERMINISTIC,
        input_fingerprint=f"input:{event_id}",
        reason_code="TEST",
        xeed_id=xeed_id,
        cost=LearningCost(
            amount_microunits=cost,
            currency=None if cost is None else "EUR",
        ),
        yield_=LearningYield(
            observations_reused=reused,
            observations_added=added,
            xignals_emitted=xignals,
            canonical_admissions=admissions,
        ),
    )


def _record(
    record_id: str,
    record_type: str,
    outcome: str,
    *,
    xeed_id: str | None = None,
    completeness: DataCompleteness = DataCompleteness.KNOWN,
    recorded_at: datetime = NOW,
    unknown_reason: str | None = None,
) -> AdminEventEnvelope:
    return AdminEventEnvelope(
        record_id=AdminRecordId(record_id),
        record_type=record_type,
        record_class=AdminRecordClass.ADMIN_METRIC_OBSERVATION,
        schema_version=1,
        producer="test-owner",
        owning_domain="test-domain",
        recorded_at=recorded_at,
        outcome_state=outcome,
        completeness=completeness,
        privacy_class=AdminPrivacyClass.INTERNAL,
        subject_refs=() if xeed_id is None else (f"xeed-id:{xeed_id}",),
        provenance_refs=(f"source:{record_id}",),
        unknown_reason=unknown_reason,
    )


def test_empty_sources_are_partial_not_zero_xeed_claim() -> None:
    result = project_xeed_axigland_observatory(
        learning_events=(),
        admin_records=(),
        as_of=NOW,
        generated_at=NOW,
    )

    assert result.completeness is DataCompleteness.PARTIAL
    assert result.xeeds == ()
    assert result.axigland.currentness_completeness is DataCompleteness.UNKNOWN
    assert result.axigland.canonical_admission_events == 0
    assert "not current FAXT cardinality" in result.coverage_notes[1]


def test_reuse_is_separate_from_new_observation_and_canonical_growth() -> None:
    result = project_xeed_axigland_observatory(
        learning_events=(
            _event("e1", reused=3, added=1, admissions=1),
            _event("e2", reused=2, added=0, admissions=0),
        ),
        admin_records=(),
        as_of=NOW,
        generated_at=NOW,
    )

    xeed = result.xeeds[0]
    assert xeed.observations_reused == 5
    assert xeed.observations_added == 1
    assert xeed.canonical_admissions == 1
    assert xeed.reuse_ratio == "0.8333"
    assert result.axigland.canonical_admission_events == 1


def test_unknown_cost_is_not_free_and_scopes_remain_distinct() -> None:
    result = project_xeed_axigland_observatory(
        learning_events=(
            _event("known", cost=1200),
            _event("unknown", cost=None),
        ),
        admin_records=(),
        as_of=NOW,
        generated_at=NOW,
    )

    xeed = result.xeeds[0]
    assert xeed.known_costs_by_currency == (("EUR", 1200),)
    assert xeed.unknown_cost_event_count == 1
    assert xeed.direct_cost_completeness is DataCompleteness.PARTIAL
    assert xeed.shared_cost_completeness is DataCompleteness.UNKNOWN
    assert xeed.triggered_cost_completeness is DataCompleteness.UNKNOWN
    assert xeed.shared_cost_reason != xeed.triggered_cost_reason


def test_lifecycle_first_value_and_failure_diagnosis_preserve_lineage() -> None:
    events = (
        _event("first", occurred_at=NOW - timedelta(minutes=4)),
        _event(
            "useful",
            occurred_at=NOW - timedelta(minutes=1),
            xignals=1,
            outcome=LearningOutcome.PARTIAL,
        ),
    )
    lifecycle = _record("life-1", "xeed.lifecycle", "LIVE", xeed_id="xeed-1")
    result = project_xeed_axigland_observatory(
        learning_events=events,
        admin_records=(lifecycle,),
        as_of=NOW,
        generated_at=NOW,
    )

    xeed = result.xeeds[0]
    assert xeed.lifecycle_state == "LIVE"
    assert xeed.lifecycle_completeness is DataCompleteness.KNOWN
    assert xeed.time_to_first_useful_xignal_ms == 180_000
    assert xeed.partial_event_count == 1
    assert xeed.source_learning_event_ids == ("first", "useful")
    assert xeed.source_admin_record_ids == ("life-1",)


def test_axigland_quality_states_are_explicit_not_inferred_from_learning() -> None:
    records = (
        _record("c", "axigland.contradiction", "2_OPEN"),
        _record("i", "axigland.identity_resolution", "HEALTHY"),
        _record(
            "n",
            "axigland.currentness",
            "UNKNOWN",
            completeness=DataCompleteness.UNKNOWN,
            unknown_reason="NO_POLICY_COVERAGE",
        ),
        _record("p", "axigland.provenance", "COMPLETE"),
    )
    result = project_xeed_axigland_observatory(
        learning_events=(_event("e"),),
        admin_records=records,
        as_of=NOW,
        generated_at=NOW,
    )

    assert result.axigland.contradiction_state == "2_OPEN"
    assert result.axigland.identity_resolution_state == "HEALTHY"
    assert result.axigland.currentness_state == "UNKNOWN"
    assert result.axigland.currentness_completeness is DataCompleteness.UNKNOWN
    assert result.axigland.provenance_state == "COMPLETE"
    assert result.axigland.completeness is DataCompleteness.PARTIAL


def test_future_evidence_cannot_contaminate_current_observatory() -> None:
    result = project_xeed_axigland_observatory(
        learning_events=(
            _event("current", admissions=1),
            _event("future", occurred_at=NOW + timedelta(hours=1), admissions=99),
        ),
        admin_records=(
            _record(
                "future-life",
                "xeed.lifecycle",
                "LIVE",
                xeed_id="xeed-1",
                recorded_at=NOW + timedelta(hours=1),
            ),
        ),
        as_of=NOW,
        generated_at=NOW,
    )

    xeed = result.xeeds[0]
    assert xeed.canonical_admissions == 1
    assert xeed.lifecycle_state is None
    assert xeed.lifecycle_completeness is DataCompleteness.UNKNOWN
