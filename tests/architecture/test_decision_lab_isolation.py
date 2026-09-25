"""Architecture boundaries for experimental decision-lab code."""

from __future__ import annotations

import tomllib
from pathlib import Path

from tools.architecture_guard.guard import _apply_rules


def test_typesafe_sdk_is_allowed_only_in_exact_lab_adapter() -> None:
    assert not _apply_rules(
        "experiments.decision_lab.providers.typesafe",
        "experiments/decision_lab/providers/typesafe.py",
        "typesafe_sdk",
        1,
    )
    violations = _apply_rules(
        "experiments.decision_lab.cli", "experiments/decision_lab/cli.py", "typesafe_sdk", 1
    )
    assert any(item.rule == "PROVIDER_SDK_IMPORT" for item in violations)
    violations = _apply_rules(
        "cognition.providers.typesafe",
        "cognition/providers/typesafe.py",
        "typesafe_sdk",
        1,
    )
    assert any(item.rule == "PROVIDER_SDK_IMPORT" for item in violations)
    violations = _apply_rules(
        "experiments.decision_lab.providers.typesafe",
        "experiments/decision_lab/providers/typesafe.py",
        "openai",
        2,
    )
    assert any(item.rule == "PROVIDER_SDK_IMPORT" for item in violations)


def test_lab_cannot_import_production_packages() -> None:
    for target in ("domain.faxt.model", "pipeline.research", "cognition.router"):
        violations = _apply_rules(
            "experiments.decision_lab.cli", "experiments/decision_lab/cli.py", target, 4
        )
        assert any(item.rule == "LAB_PRODUCTION_IMPORT" for item in violations)


def test_production_core_cannot_import_lab() -> None:
    violations = _apply_rules(
        "domain.faxt.model", "domain/faxt/model.py", "experiments.decision_lab", 8
    )
    assert any(item.rule == "PRODUCTION_LAB_IMPORT" for item in violations)


def test_typesafe_dependency_is_optional_and_lab_only() -> None:
    root = Path(__file__).resolve().parents[2]
    project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    assert "typesafe-sdk" not in project["project"]["dependencies"]
    assert all("typesafe-sdk" not in item for item in project["dependency-groups"]["dev"])
    assert project["dependency-groups"]["decision-lab-live"] == ["typesafe-sdk==0.7.1"]
