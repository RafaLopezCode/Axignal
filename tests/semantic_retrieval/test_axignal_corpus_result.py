import json
from pathlib import Path

RESULT = (
    Path(__file__).parents[2]
    / "experiments"
    / "semantic_retrieval"
    / "results"
    / "axignal_corpus_latest.json"
)


def test_synthetic_corpus_cannot_promote_turboquant() -> None:
    report = json.loads(RESULT.read_text(encoding="utf-8"))

    assert report["corpus"]["kind"] == "SYNTHETIC_AXIGNAL_SHAPED"
    assert report["corpus"]["promotion_authority"] is False
    assert report["corpus"]["candidates"] == 576
    assert report["corpus"]["queries"] == 72


def test_corpus_exposes_why_retrieval_budget_must_precede_structured_filtering() -> None:
    report = json.loads(RESULT.read_text(encoding="utf-8"))

    assert report["exact"]["germination_recall@10"] < 0.25
    assert report["exact"]["germination_recall@50"] == 1.0
    assert report["turboquant"]["8"]["germination_recall@50"] == 1.0
    assert report["turboquant"]["8"]["recall@10"] > 0.90
