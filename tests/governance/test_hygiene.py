from __future__ import annotations

import subprocess
from pathlib import Path

from tools.governance.checks import (
    REQUIRED_IGNORE_PATTERNS,
    check_hygiene,
    check_no_generated_data,
)


def _large_file_problems(root: Path) -> list[str]:
    return [problem for problem in check_hygiene(root) if "large file (>2MB)" in problem]


def test_hygiene_ignores_gitignored_large_files_but_reports_commit_candidates(
    tmp_path: Path,
) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / ".gitignore").write_text(".mypy_cache/\n", encoding="utf-8")

    ignored = tmp_path / ".mypy_cache" / "cache.db"
    ignored.parent.mkdir()
    ignored.write_bytes(b"x" * (2 * 1024 * 1024 + 1))

    candidate = tmp_path / "accidental-large.bin"
    candidate.write_bytes(b"x" * (2 * 1024 * 1024 + 1))

    assert _large_file_problems(tmp_path) == [
        "large file (>2MB) should not be committed: accidental-large.bin"
    ]


def test_repo_local_only_paths_are_ignored_without_deleting_files() -> None:
    root = Path(__file__).resolve().parents[2]
    for relative in (
        ".secrets/example.json",
        ".tmp-example/artifact.txt",
        ".tmp_probe.py",
        ".tmp_replay.sh",
        ".pb11_pytest_out.log",
        ".claude/settings.local.json",
    ):
        result = subprocess.run(
            ["git", "-C", str(root), "check-ignore", "-q", "--", relative],
            check=False,
        )
        assert result.returncode == 0, f"local-only path is not ignored: {relative}"


def test_governance_rejects_forcibly_tracked_private_scratch(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / ".gitignore").write_text(
        "\n".join(REQUIRED_IGNORE_PATTERNS) + "\n", encoding="utf-8"
    )
    local_paths = (
        ".secrets/example.json",
        ".tmp-example/artifact.txt",
        ".tmp_probe.py",
        ".tmp_replay.sh",
        ".pb11_pytest_out.log",
        ".claude/settings.local.json",
    )
    for relative in local_paths:
        candidate = tmp_path / relative
        candidate.parent.mkdir(parents=True, exist_ok=True)
        fixture_content = (
            "# fixture-only; no credentials\n"
            if candidate.suffix == ".py"
            else "fixture-only; no credentials"
        )
        candidate.write_text(fixture_content, encoding="utf-8")
        subprocess.run(["git", "add", "-f", "--", relative], cwd=tmp_path, check=True)
    problems = check_no_generated_data(tmp_path)
    for relative in local_paths:
        assert f"local-only file must not be tracked: {relative}" in problems


def test_governance_accepts_untracked_ignored_private_scratch(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / ".gitignore").write_text(
        "\n".join(REQUIRED_IGNORE_PATTERNS) + "\n", encoding="utf-8"
    )
    candidate = tmp_path / ".secrets" / "local-only.json"
    candidate.parent.mkdir(parents=True, exist_ok=True)
    candidate.write_text("fixture-only; no credentials", encoding="utf-8")
    assert check_no_generated_data(tmp_path) == []
