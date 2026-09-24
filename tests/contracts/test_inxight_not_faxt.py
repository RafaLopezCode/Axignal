"""INXIGHT is derived knowledge, never a FAXT (MASTER §4.6, §18, §46.21)."""

from __future__ import annotations

import dataclasses
from datetime import datetime

import pytest

from domain.faxt.model import FAXT
from domain.inxight.model import INXIGHT, InxightError


def _inxight(**overrides: object) -> INXIGHT:
    payload: dict[str, object] = {
        "id": "inx-1",
        "subject_scope": "org-acme",
        "statement": "ACME is unusually well positioned in certified suppliers.",
        "supporting_faxt_refs": ("faxt-1", "faxt-2"),
        "derived_at": datetime(2026, 1, 1),
    }
    payload.update(overrides)
    return INXIGHT(**payload)  # type: ignore[arg-type]


def test_inxight_is_not_a_faxt() -> None:
    assert not issubclass(INXIGHT, FAXT)
    field_names = {field.name for field in dataclasses.fields(INXIGHT)}
    assert "predicate" not in field_names
    assert "supporting_faxt_refs" in field_names


def test_inxight_requires_supporting_faxts() -> None:
    with pytest.raises(InxightError):
        _inxight(supporting_faxt_refs=())


def test_inxight_is_explainable() -> None:
    assert _inxight().is_explainable is True
