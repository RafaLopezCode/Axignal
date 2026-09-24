"""UNKNOWN must never become FALSE (MASTER §15.4, §46.23)."""

from __future__ import annotations

import pytest

from domain.evidence.epistemics import (
    EpistemicState,
    UnknownIsNotFalseError,
    require_boolean,
    truth_value,
)


def test_unknown_returns_none_not_false() -> None:
    assert truth_value(EpistemicState.UNKNOWN) is None


@pytest.mark.parametrize(
    "state",
    [
        EpistemicState.UNKNOWN,
        EpistemicState.STALE,
        EpistemicState.INFERRED,
        EpistemicState.CONTRADICTED,
        EpistemicState.DECLARED,
    ],
)
def test_only_justified_states_are_true(state: EpistemicState) -> None:
    assert truth_value(state) is None
    with pytest.raises(UnknownIsNotFalseError):
        require_boolean(state)


def test_observed_and_corroborated_are_true() -> None:
    assert truth_value(EpistemicState.OBSERVED) is True
    assert truth_value(EpistemicState.CORROBORATED) is True
    assert require_boolean(EpistemicState.OBSERVED) is True
