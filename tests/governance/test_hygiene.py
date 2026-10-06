from __future__ import annotations

import subprocess
from pathlib import Path

from tools.governance.checks import check_hygiene


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
