"""Deterministic normalization tests."""

from __future__ import annotations

from pipeline.normalization.text import normalize_name, normalize_whitespace


def test_normalize_whitespace_collapses_runs() -> None:
    assert normalize_whitespace("  ACME   Industrial \n Pumps ") == "ACME Industrial Pumps"


def test_normalize_name_preserves_accents_scripts_and_punctuation() -> None:
    assert normalize_name("Café  S.A.") == "café s.a."
    assert normalize_name("ACME, Inc.") == "acme, inc."
    assert normalize_name("Cafe\u0301") == normalize_name("Café")
    assert normalize_name("東京") == "東京"
    assert normalize_name("Café") != normalize_name("Cafe")


def test_normalize_name_is_stable() -> None:
    assert normalize_name("ACME") == normalize_name("  acme  ")
