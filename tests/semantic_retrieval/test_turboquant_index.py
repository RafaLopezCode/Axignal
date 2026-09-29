import pytest

from application.semantic_retrieval import SemanticRepresentation
from pipeline.semantic_retrieval import TurboQuantSemanticIndex


def rep(identifier: str, vector: tuple[float, ...]) -> SemanticRepresentation:
    return SemanticRepresentation(identifier, vector)


def test_retrieval_returns_candidate_ids_not_canonical_objects() -> None:
    index = TurboQuantSemanticIndex(dimension=4, num_bits=8, seed=7)
    index.rebuild(
        [
            rep("cold-storage", (1.0, 0.0, 0.0, 0.0)),
            rep("industrial-pumps", (0.0, 1.0, 0.0, 0.0)),
            rep("food-logistics", (0.9, 0.1, 0.0, 0.0)),
        ]
    )

    candidates = index.search((1.0, 0.0, 0.0, 0.0), k=2)

    assert len(candidates) == 2
    assert candidates[0].representation_id in {"cold-storage", "food-logistics"}
    assert all(isinstance(item.similarity, float) for item in candidates)


def test_rebuild_replaces_disposable_index_state() -> None:
    index = TurboQuantSemanticIndex(dimension=2, num_bits=8)
    index.rebuild([rep("old", (1.0, 0.0))])
    index.rebuild([rep("new", (0.0, 1.0))])

    assert index.size == 1
    assert index.search((0.0, 1.0), k=1)[0].representation_id == "new"


def test_invalid_dimensions_and_duplicate_ids_fail_closed() -> None:
    index = TurboQuantSemanticIndex(dimension=3, num_bits=8)
    with pytest.raises(ValueError, match="unique"):
        index.rebuild([rep("same", (1.0, 0.0, 0.0)), rep("same", (0.0, 1.0, 0.0))])
    with pytest.raises(ValueError, match="dimension"):
        index.rebuild([rep("bad", (1.0, 0.0))])


def test_empty_index_has_no_candidates() -> None:
    index = TurboQuantSemanticIndex(dimension=3, num_bits=8)
    assert index.search((1.0, 0.0, 0.0), k=5) == ()


def test_unvalidated_bit_width_is_rejected() -> None:
    with pytest.raises(ValueError, match="4, 6, or 8"):
        TurboQuantSemanticIndex(dimension=3, num_bits=3)
