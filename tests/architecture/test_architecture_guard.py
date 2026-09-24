"""Architecture Guard unit tests, including deliberate negative tests.

These tests build synthetic source trees, not grep comments: the AST guard must
reject the violations. See Phase 11 of the bootstrap mission.
"""

from __future__ import annotations

from pathlib import Path

from tools.architecture_guard.guard import Violation, imported_modules, run


def _scan(root: Path, files: dict[str, str]) -> list[Violation]:
    for relative, content in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return run(root)


def _rules(violations: list[Violation]) -> set[str]:
    return {violation.rule for violation in violations}


def test_clean_domain_has_no_violations(tmp_path: Path) -> None:
    violations = _scan(
        tmp_path,
        {
            "domain/sample/model.py": (
                "from __future__ import annotations\n"
                "from domain.evidence.admission import Evidence\n"
                "value = Evidence\n"
            ),
        },
    )
    assert violations == []


def test_domain_importing_cognition_is_rejected(tmp_path: Path) -> None:
    violations = _scan(
        tmp_path,
        {"domain/bad.py": "from cognition.providers.base import CognitiveProvider\n"},
    )
    assert "LAYER_IMPORT" in _rules(violations)


def test_domain_importing_pipeline_is_rejected(tmp_path: Path) -> None:
    violations = _scan(
        tmp_path,
        {"domain/bad.py": "import pipeline.normalization.text\n"},
    )
    assert "LAYER_IMPORT" in _rules(violations)


def test_xignal_importing_organizations_is_rejected(tmp_path: Path) -> None:
    violations = _scan(
        tmp_path,
        {
            "domain/xignal/bad.py": (
                "from domain.organizations.model import Organization\n"
                "from ..organizations.model import Organization as Org2\n"
            ),
        },
    )
    assert "XIGNAL_ISOLATION" in _rules(violations)


def test_projection_importing_canonical_writer_is_rejected(tmp_path: Path) -> None:
    violations = _scan(
        tmp_path,
        {"domain/pathx/bad.py": "from domain.faxt.model import FAXT\n"},
    )
    assert "PROJECTION_CANONICAL_WRITE" in _rules(violations)


def test_provider_sdk_outside_providers_is_rejected(tmp_path: Path) -> None:
    violations = _scan(
        tmp_path,
        {"pipeline/discovery/bad.py": "import openai\n"},
    )
    assert "PROVIDER_SDK_IMPORT" in _rules(violations)


def test_provider_adapter_writing_canonical_state_is_rejected(tmp_path: Path) -> None:
    violations = _scan(
        tmp_path,
        {"cognition/providers/bad.py": "from domain.faxt.model import FAXT\n"},
    )
    assert "PROVIDER_CANONICAL_WRITE" in _rules(violations)


def test_crm_package_is_rejected(tmp_path: Path) -> None:
    violations = _scan(
        tmp_path,
        {"domain/crm/model.py": "VALUE = 1\n"},
    )
    assert "FORBIDDEN_DOMAIN_PACKAGE" in _rules(violations)


def test_workflow_package_is_rejected(tmp_path: Path) -> None:
    violations = _scan(
        tmp_path,
        {"pipeline/workflow/model.py": "VALUE = 1\n"},
    )
    assert "FORBIDDEN_DOMAIN_PACKAGE" in _rules(violations)


def test_relative_import_resolution(tmp_path: Path) -> None:
    source = (
        "from __future__ import annotations\n"
        "from ..organizations.model import Organization\n"
        "from .sibling import helper\n"
        "import domain.faxt.model\n"
    )
    path = tmp_path / "domain" / "xignal" / "observation_seed.py"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")
    import ast

    tree = ast.parse(source)
    resolved = {name for name, _ in imported_modules("domain.xignal.observation_seed", False, tree)}
    assert "domain.organizations.model" in resolved
    assert "domain.xignal.sibling" in resolved
    assert "domain.faxt.model" in resolved
