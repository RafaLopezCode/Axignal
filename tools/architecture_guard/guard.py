"""Architecture Guard.

Deterministic, AST-based enforcement of AXIGNAL's dependency direction and
forbidden drift. No LLM, no network. Exit code is non-zero on any violation.

Doctrine: MASTER via the Engineering Constitution
(``.specify/memory/constitution.md``), "Canonical Dependency Direction" and
"Architectural Constraints". See ``docs/governance/ARCHITECTURE_GUARD.md``.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from collections.abc import Iterator, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

from tools.architecture_guard import rules

_ = rules  # re-export surfaced for tests

SKIP_DIRECTORIES: frozenset[str] = frozenset(
    {
        ".git",
        ".specify",
        ".opencode",
        ".venv",
        "venv",
        "__pycache__",
        ".mypy_cache",
        ".ruff_cache",
        ".pytest_cache",
        "graphify-out",
        "node_modules",
        "dist",
        "build",
        "data",
    }
)


@dataclass(frozen=True)
class Violation:
    """One architecture rule violation."""

    rule: str
    path: str
    line: int
    detail: str


def iter_python_files(root: Path) -> Iterator[Path]:
    for path in sorted(root.rglob("*.py")):
        relative = path.relative_to(root)
        if set(relative.parts[:-1]) & SKIP_DIRECTORIES:
            continue
        yield path


def module_name(root: Path, path: Path) -> str:
    relative = path.relative_to(root)
    parts = list(relative.with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _is_within(module: str, package: str) -> bool:
    return module == package or module.startswith(package + ".")


def _matches_any(target: str, prefixes: Sequence[str]) -> bool:
    return any(target == prefix or target.startswith(prefix + ".") for prefix in prefixes)


def _resolve_import_from(module: str, is_package: bool, node: ast.ImportFrom) -> str:
    base_parts = module.split(".") if module else []
    if not is_package and base_parts:
        base_parts = base_parts[:-1]
    level = node.level
    if level:
        keep = len(base_parts) - (level - 1)
        base_parts = base_parts[: max(keep, 0)]
    imported = node.module or ""
    if not level:
        return imported
    if imported:
        base_parts = base_parts + imported.split(".")
    return ".".join(base_parts)


def imported_modules(module: str, is_package: bool, tree: ast.AST) -> list[tuple[str, int]]:
    results: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                results.append((alias.name, node.lineno))
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module is None:
                continue
            resolved = _resolve_import_from(module, is_package, node)
            if not resolved:
                continue
            results.append((resolved, node.lineno))
            for alias in node.names:
                if alias.name == "*":
                    continue
                results.append((f"{resolved}.{alias.name}", node.lineno))
    return results


def _apply_rules(module: str, relative: str, target: str, line: int) -> list[Violation]:
    violations: list[Violation] = []
    root_pkg = target.split(".")[0]

    if _is_within(module, rules.DOMAIN_PACKAGE) and root_pkg in rules.DOMAIN_FORBIDDEN_IMPORTS:
        violations.append(
            Violation(
                "LAYER_IMPORT",
                relative,
                line,
                f"domain must not import inner-outward layer: {target}",
            )
        )

    if not _is_within(module, rules.PROVIDER_PACKAGE) and _matches_any(
        target, rules.PROVIDER_SDK_PREFIXES
    ):
        violations.append(
            Violation(
                "PROVIDER_SDK_IMPORT",
                relative,
                line,
                f"model-provider SDK import outside cognition/providers: {target}",
            )
        )

    for segment in target.split("."):
        if segment in rules.FORBIDDEN_MODULE_SEGMENTS:
            violations.append(
                Violation(
                    "FORBIDDEN_DOMAIN_PACKAGE",
                    relative,
                    line,
                    f"forbidden CRM/workflow/sponsored package segment {segment!r}: {target}",
                )
            )
            break

    if _is_within(module, rules.XIGNAL_PACKAGE) and _is_within(target, rules.ORGANIZATIONS_PACKAGE):
        violations.append(
            Violation(
                "XIGNAL_ISOLATION",
                relative,
                line,
                f"xignal must not import canonical organizations: {target}",
            )
        )

    if any(_is_within(module, package) for package in rules.PROJECTION_PACKAGES) and _matches_any(
        target, rules.CANONICAL_WRITER_MODULES
    ):
        violations.append(
            Violation(
                "PROJECTION_CANONICAL_WRITE",
                relative,
                line,
                f"projection package must not import canonical writer: {target}",
            )
        )

    if _is_within(module, rules.PROVIDER_PACKAGE) and _matches_any(
        target, rules.CANONICAL_WRITER_MODULES
    ):
        violations.append(
            Violation(
                "PROVIDER_CANONICAL_WRITE",
                relative,
                line,
                f"provider adapters must not touch canonical writers: {target}",
            )
        )

    return violations


def check_file(root: Path, path: Path) -> list[Violation]:
    module = module_name(root, path)
    relative = path.relative_to(root).as_posix()
    violations: list[Violation] = []

    for part in path.relative_to(root).parts[:-1]:
        if part in rules.FORBIDDEN_MODULE_SEGMENTS:
            violations.append(
                Violation(
                    "FORBIDDEN_DOMAIN_PACKAGE",
                    relative,
                    0,
                    f"forbidden package directory {part!r}",
                )
            )

    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        violations.append(Violation("PARSE_ERROR", relative, exc.lineno or 0, str(exc)))
        return violations

    is_package = path.name == "__init__.py"
    for target, line in imported_modules(module, is_package, tree):
        violations.extend(_apply_rules(module, relative, target, line))
    return violations


def run(root: Path) -> list[Violation]:
    violations: list[Violation] = []
    for path in iter_python_files(root):
        violations.extend(check_file(root, path))
    return violations


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="architecture-guard",
        description="Enforce AXIGNAL dependency direction and forbidden drift.",
    )
    parser.add_argument("--root", default=".", help="repository root to scan")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    violations = run(root)

    if args.json:
        sys.stdout.write(json.dumps([asdict(v) for v in violations], indent=2) + "\n")
    elif violations:
        sys.stdout.write(f"Architecture Guard: {len(violations)} violation(s)\n")
        for violation in violations:
            sys.stdout.write(
                f"  [{violation.rule}] {violation.path}:{violation.line} {violation.detail}\n"
            )
    else:
        sys.stdout.write("Architecture Guard: OK (no violations)\n")

    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
