from datetime import UTC, datetime, timedelta

from application.subscriber_projection.today import (
    TodayCandidate,
    TodayDisposition,
    TodayPolicy,
    project_today,
)
from application.subscriber_projection.xignal import (
    ExplainableXignalProjection,
    ExplanationStepKind,
    XignalExplanationStep,
    XignalExplanationTrail,
)
from domain.evidence import Currentness
from domain.xignal import Xignal, XignalEpistemicState, XignalKind

NOW = datetime(2026, 9, 30, 20, 30, tzinfo=UTC)


def _projection(
    suffix: str,
    *,
    state: XignalEpistemicState = XignalEpistemicState.POTENTIAL,
    observed_at: datetime = NOW,
) -> ExplainableXignalProjection:
    xignal = Xignal(
        xignal_id=f"xignal:{suffix}",
        xeed_id="xeed:1",
        subject_id="org:acme",
        candidate_id=f"candidate:{suffix}",
        kind=XignalKind.SUPPLY,
        epistemic_state=state,
        title=f"Material development {suffix}",
        why_attention=f"This matters because {suffix} changes the economic picture.",
        basis_ref=f"basis:{suffix}",
        emitted_at=observed_at,
        currentness=Currentness.CURRENT,
        policy_version="xignal-v1",
        unknowns=("One material unknown remains.",),
    )
    trail = XignalExplanationTrail(
        xignal_id=xignal.xignal_id,
        basis_id=xignal.basis_ref,
        steps=(
            XignalExplanationStep(
                step_id=f"step:{suffix}",
                kind=ExplanationStepKind.XIGNAL,
                ref=xignal.xignal_id,
                label=xignal.why_attention,
            ),
        ),
    )
    return ExplainableXignalProjection(
        xignal=xignal,
        semantic_target="TODAY_SIGNAL",
        interpretation="Material development worth attention.",
        uncertainty="One unknown remains.",
        source_refs=("https://example.test",),
        source_types=("OFFICIAL_WEB",),
        first_observed_at=observed_at,
        last_observed_at=observed_at,
        trail=trail,
    )


def test_today_surfaces_at_most_three_material_items_without_score() -> None:
    candidates = tuple(
        TodayCandidate(
            projection=_projection(str(index), observed_at=NOW - timedelta(hours=index)),
            focus_ref=f"FAXT:faxt-{index}",
            changed_at=NOW - timedelta(minutes=index),
        )
        for index in range(5)
    )

    projection = project_today(candidates=candidates, policy=TodayPolicy("today", "1"))

    assert projection.disposition is TodayDisposition.READY
    assert len(projection.items) == 3
    assert [item.xignal_id for item in projection.items] == [
        "xignal:0",
        "xignal:1",
        "xignal:2",
    ]
    assert "score" not in TodayPolicy.__dataclass_fields__
    assert "node_count" not in TodayPolicy.__dataclass_fields__


def test_today_excludes_non_material_items_and_preserves_deep_links() -> None:
    projection = project_today(
        candidates=(
            TodayCandidate(
                projection=_projection("material"),
                focus_ref="FAXT:faxt-material",
                changed_at=NOW,
                material=True,
            ),
            TodayCandidate(
                projection=_projection("context"),
                focus_ref="FAXT:faxt-context",
                changed_at=NOW,
                material=False,
            ),
        ),
        policy=TodayPolicy("today", "1"),
    )

    assert len(projection.items) == 1
    item = projection.items[0]
    assert item.focus_ref == "FAXT:faxt-material"
    assert item.show_how_ref == "xignal:material"
    assert item.what_changed == "Material development material"
    assert "changes the economic picture" in item.why_it_matters


def test_today_partial_and_empty_states_are_explicit() -> None:
    partial = project_today(
        candidates=(
            TodayCandidate(
                projection=_projection("not-material"),
                focus_ref="FAXT:faxt-context",
                changed_at=None,
                material=False,
            ),
        ),
        policy=TodayPolicy("today", "1"),
    )
    empty = project_today(candidates=(), policy=TodayPolicy("today", "1"))

    assert partial.disposition is TodayDisposition.PARTIAL
    assert partial.items == ()
    assert empty.disposition is TodayDisposition.EMPTY
    assert empty.items == ()
    assert "current observed state" in empty.message.lower()


def test_today_item_preserves_state_time_and_currentness() -> None:
    observed = NOW - timedelta(days=2)
    source = _projection(
        "unknown",
        state=XignalEpistemicState.UNKNOWN,
        observed_at=observed,
    )
    today = project_today(
        candidates=(
            TodayCandidate(
                projection=source,
                focus_ref="FAXT:faxt-unknown",
                changed_at=None,
            ),
        ),
        policy=TodayPolicy("today", "1"),
    )

    item = today.items[0]
    assert item.epistemic_state is XignalEpistemicState.UNKNOWN
    assert item.currentness is Currentness.CURRENT
    assert item.observed_at == observed
    assert item.changed_at is None
