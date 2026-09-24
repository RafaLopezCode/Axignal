"""Deterministic normalization tests."""

from __future__ import annotations

from pipeline.normalization.text import normalize_name, normalize_whitespace


def test_normalize_whitespace_collapses_runs() -> None:
    assert normalize_whitespace("  ACME   Industrial \n Pumps ") == "ACME Industrial Pumps"


def test_normalize_name_folds_accents_case_and_punctuation() -> None:
    assert normalize_name("Café  S.A.") == "cafe s a"
    assert normalize_name("ACME, Inc.") == "acme inc"


def test_normalize_name_is_stable() -> None:
    assert normalize_name("ACME") == normalize_name("  acme  ")
