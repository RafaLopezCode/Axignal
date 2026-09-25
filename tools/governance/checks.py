"""Deterministic governance checks.

Each check is pure, offline and deterministic. None calls a model. See
``docs/governance/DETERMINISTIC_CI.md``.
"""

from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
import tomllib
from collections.abc import Callable, Iterable
from pathlib import Path

from tools.architecture_guard.guard import run as run_architecture_guard

MASTER_REL = "docs/product/AXIGNAL_MASTER_PRODUCT_MODEL_2026-09-24_V2.md"
MASTER_HASH_REL = "docs/product/AXIGNAL_MASTER_PRODUCT_MODEL_2026-09-24_V2.md.sha256"
ATLAS_REL = "docs/architecture/AXIGNAL_LOGICAL_ARCHITECTURE_ATLAS_V0.1.md"
ATLAS_HASH_REL = f"{ATLAS_REL}.sha256"
ARCHITECTURAL_GAP_LEDGER_REL = "docs/architecture/AXIGNAL_ARCHITECTURAL_GAP_LEDGER_P0_ARCH_01.md"

REQUIRED_PATHS: tuple[str, ...] = (
    "README.md",
    "AGENTS.md",
    "pyproject.toml",
    ".gitignore",
    ".gitattributes",
    ".github/workflows/ci.yml",
    MASTER_REL,
    MASTER_HASH_REL,
    ATLAS_REL,
    ATLAS_HASH_REL,
    ARCHITECTURAL_GAP_LEDGER_REL,
    ".specify/memory/constitution.md",
    ".specify/init-options.json",
    "docs/architecture/OVERVIEW.md",
    "docs/architecture/TERMINOLOGY.md",
    "docs/governance/README.md",
    "docs/governance/DETERMINISTIC_CI.md",
    "docs/governance/ARCHITECTURE_GUARD.md",
    "docs/governance/GRAPHIFY.md",
    "docs/governance/SPEC_KIT.md",
    "docs/adr/README.md",
    "tools/architecture_guard/guard.py",
    "tests/architecture",
    "tests/contracts",
)

ADR_IDS: tuple[str, ...] = (
    "0001",
    "0002",
    "0003",
    "0004",
    "0005",
    "0006",
    "0007",
    "0008",
)

CANONICAL_TERMS: tuple[str, ...] = (
    "AXIGNAL",
    "AXIGLAND",
    "AXENT",
    "XIGNAL",
    "FAXT",
    "INXIGHT",
    "PATHX",
)

FORBIDDEN_IDENTIFIERS: tuple[str, ...] = (
    "EconomicPath",
    "CompanyProfile",
    "ClaimedCompany",
    "EditCompanyProfile",
    "SponsorRanking",
    "PayToRank",
)

FORBIDDEN_DEPENDENCIES: frozenset[str] = frozenset(
    {
        "openai",
        "anthropic",
        "langchain",
        "langchain-core",
        "llama-index",
        "llama_index",
        "crewai",
        "pyautogen",
        "autogen",
        "google-generativeai",
        "google-genai",
        "transformers",
        "litellm",
        "cohere",
        "mistralai",
        "ollama",
        "huggingface-hub",
        "replicate",
        "groq",
    }
)

REQUIRED_IGNORE_PATTERNS: tuple[str, ...] = (
    "graphify-out/",
    "data/raw/",
    "data/working/",
    "data/exports/",
    "__pycache__/",
    ".env",
)

_SOURCE_LAYERS: tuple[str, ...] = ("domain", "pipeline", "cognition")
_MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")

Problem = str


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def check_hygiene(root: Path) -> list[Problem]:
    problems: list[Problem] = []
    for required in REQUIRED_PATHS:
        if not (root / required).exists():
            problems.append(f"missing required path: {required}")

    for forbidden in (".env", "credentials.json"):
        if (root / forbidden).exists():
            problems.append(f"forbidden file present: {forbidden}")

    skip = {".git", ".venv", "node_modules", "graphify-out", "data"}
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if set(relative.parts) & skip:
            continue
        if path.is_file() and path.stat().st_size > 2 * 1024 * 1024:
            problems.append(f"large file (>2MB) should not be committed: {relative.as_posix()}")
    return problems


def check_terminology(root: Path) -> list[Problem]:
    problems: list[Problem] = []
    terminology = root / "docs/architecture/TERMINOLOGY.md"
    if not terminology.exists():
        return ["docs/architecture/TERMINOLOGY.md is missing"]
    text = _read(terminology)
    for term in CANONICAL_TERMS:
        if term not in text:
            problems.append(f"canonical term not documented: {term}")

    for layer in _SOURCE_LAYERS:
        layer_dir = root / layer
        if not layer_dir.exists():
            continue
        for path in layer_dir.rglob("*.py"):
            source = _read(path)
            for identifier in FORBIDDEN_IDENTIFIERS:
                if re.search(rf"\b{identifier}\b", source):
                    problems.append(
                        f"forbidden identifier {identifier!r} in {path.relative_to(root).as_posix()}"
                    )
    return problems


def _iter_markdown(root: Path) -> Iterable[Path]:
    for path in root.rglob("*.md"):
        relative = path.relative_to(root)
        if set(relative.parts) & {".git", ".venv", "node_modules", "graphify-out"}:
            continue
        yield path


def check_docs_integrity(root: Path) -> list[Problem]:
    problems: list[Problem] = []
    for path in _iter_markdown(root):
        source = _read(path)
        for target in _MARKDOWN_LINK.findall(source):
            if any(target.startswith(prefix) for prefix in ("http://", "https://", "#", "mailto:")):
                continue
            if any(char in target for char in ("{}", "<", ">")):
                continue
            clean = target.split("#", 1)[0].strip()
            if not clean or not clean.endswith(".md"):
                continue
            if not (path.parent / clean).resolve().exists():
                problems.append(
                    f"broken docs link in {path.relative_to(root).as_posix()}: {target}"
                )

    adr_dir = root / "docs/adr"
    for adr_id in ADR_IDS:
        matches = sorted(adr_dir.glob(f"ADR-{adr_id}-*.md"))
        if len(matches) != 1:
            problems.append(f"expected exactly one ADR-{adr_id}-*.md, found {len(matches)}")
            continue
        body = _read(matches[0])
        if "MASTER" not in body:
            problems.append(f"ADR-{adr_id} does not cite the MASTER")
        if f"ADR-{adr_id}" not in _read(adr_dir / "README.md"):
            problems.append(f"ADR index does not link ADR-{adr_id}")
    atlas = root / ATLAS_REL
    atlas_pinned = root / ATLAS_HASH_REL
    if not atlas.exists() or not atlas_pinned.exists():
        problems.append("logical architecture Atlas or its pinned hash file is missing")
    else:
        actual = hashlib.sha256(atlas.read_bytes()).hexdigest()
        expected = _read(atlas_pinned).split()[0].strip()
        if actual != expected:
            problems.append(
                "logical architecture Atlas hash mismatch: the Atlas changed without "
                f"updating {ATLAS_HASH_REL} (actual {actual[:12]}..., "
                f"pinned {expected[:12]}...)"
            )
    return problems


def check_spec_consistency(root: Path) -> list[Problem]:
    problems: list[Problem] = []
    constitution = root / ".specify/memory/constitution.md"
    if not constitution.exists():
        return [".specify/memory/constitution.md is missing"]
    body = _read(constitution)
    for needle in (
        "MASTER PRODUCT MODEL",
        "AXIGNAL_MASTER_PRODUCT_MODEL_2026-09-24_V2.md",
        "One Canonical AXIGLAND",
        "Epistemic Neutrality",
        "Model Provider Abstraction",
        "CLAIM",
        "UNKNOWN != FALSE",
        "IMPLEMENTATION",
        "FAIL CLOSED",
    ):
        if needle not in body:
            problems.append(f"constitution missing required content: {needle!r}")

    init_options = root / ".specify/init-options.json"
    if init_options.exists():
        options = _read(init_options)
        if '"integration": "opencode"' not in options:
            problems.append(".specify/init-options.json integration is not opencode")

    problems.extend(_check_master_hash(root))
    return problems


def _check_master_hash(root: Path) -> list[Problem]:
    master = root / MASTER_REL
    pinned = root / MASTER_HASH_REL
    if not master.exists() or not pinned.exists():
        return ["MASTER or its pinned hash file is missing"]
    actual = hashlib.sha256(master.read_bytes()).hexdigest()
    expected = _read(pinned).split()[0].strip()
    if actual != expected:
        return [
            "MASTER hash mismatch: the MASTER changed without updating "
            f"{MASTER_HASH_REL} (actual {actual[:12]}..., pinned {expected[:12]}...)"
        ]
    return []


def check_forbidden_dependencies(root: Path) -> list[Problem]:
    pyproject = root / "pyproject.toml"
    if not pyproject.exists():
        return ["pyproject.toml is missing"]
    data = tomllib.loads(_read(pyproject))
    project = data.get("project", {})
    dependencies = project.get("dependencies", [])
    problems: list[Problem] = []
    if not isinstance(dependencies, list):
        return ["[project].dependencies must be a list"]
    for dependency in dependencies:
        if not isinstance(dependency, str):
            continue
        name = re.split(r"[<>=!~\[; ]", dependency.strip(), maxsplit=1)[0].lower()
        if name in FORBIDDEN_DEPENDENCIES:
            problems.append(f"forbidden runtime dependency: {dependency}")
    return problems


GENERATED_PREFIXES: tuple[str, ...] = (
    "graphify-out/",
    "data/raw/",
    "data/working/",
    "data/exports/",
)


def _tracked(root: Path, prefix: str) -> list[str]:
    completed = subprocess.run(
        ["git", "-C", str(root), "ls-files", "--", prefix],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        return []
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def check_no_generated_data(root: Path) -> list[Problem]:
    problems: list[Problem] = []
    gitignore = root / ".gitignore"
    if not gitignore.exists():
        return [".gitignore is missing"]
    text = _read(gitignore)
    for pattern in REQUIRED_IGNORE_PATTERNS:
        if pattern not in text:
            problems.append(f".gitignore missing pattern: {pattern}")
    for prefix in GENERATED_PREFIXES:
        tracked = _tracked(root, prefix)
        if tracked:
            problems.append(f"generated/raw data must not be tracked: {tracked[0]}")
    if _tracked(root, ".env"):
        problems.append("secret file .env must not be tracked")
    if (root / ".env").exists() and not (root / ".env").is_symlink():
        problems.append("secret file .env must not be present")
    return problems


def check_architecture(root: Path) -> list[Problem]:
    return [
        f"[{violation.rule}] {violation.path}:{violation.line} {violation.detail}"
        for violation in run_architecture_guard(root)
    ]


def check_graphify(root: Path) -> list[Problem]:
    executable = shutil.which("graphify")
    if executable is None:
        return []
    completed = subprocess.run(
        [executable, "check-update", str(root)],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stdout.strip() or completed.stderr.strip()
        return [f"graphify check-update failed: {detail}"]
    return []


CHECKS: dict[str, Callable[[Path], list[Problem]]] = {
    "hygiene": check_hygiene,
    "terminology": check_terminology,
    "docs": check_docs_integrity,
    "spec": check_spec_consistency,
    "deps": check_forbidden_dependencies,
    "no-generated-data": check_no_generated_data,
    "architecture": check_architecture,
    "graphify": check_graphify,
}
