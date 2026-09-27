"""The repository itself must satisfy the Architecture Guard."""

from __future__ import annotations

from pathlib import Path

from tools.architecture_guard.guard import run

REPO_ROOT = Path(__file__).resolve().parents[2]

FORBIDDEN_LAYER_ROOTS = {"application", "pipeline", "cognition", "apps", "tools"}


def test_repository_passes_architecture_guard() -> None:
    violations = run(REPO_ROOT)
    assert violations == [], "\n".join(
        f"[{violation.rule}] {violation.path}:{violation.line} {violation.detail}"
        for violation in violations
    )


def test_domain_source_has_no_outward_imports() -> None:
    import ast

    domain_dir = REPO_ROOT / "domain"
    offenders: list[str] = []
    for path in domain_dir.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            for name in names:
                if name.split(".")[0] in FORBIDDEN_LAYER_ROOTS:
                    offenders.append(f"{path.relative_to(REPO_ROOT).as_posix()}: {name}")
    assert offenders == []


def test_application_source_depends_only_on_domain_and_stdlib() -> None:
    import ast
    import sys

    application_dir = REPO_ROOT / "application"
    allowed_roots = sys.stdlib_module_names | {"application", "domain"}
    offenders: list[str] = []
    for path in application_dir.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                modules = [node.module or ""]
            else:
                continue
            for module in modules:
                if module.split(".")[0] not in allowed_roots:
                    offenders.append(f"{path.relative_to(REPO_ROOT).as_posix()}: {module}")
    assert offenders == []
