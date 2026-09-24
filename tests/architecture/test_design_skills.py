"""Design-skill installation contract (deterministic, offline, no LLM).

Verifies the two selected UI/UX super-skills are installed project-locally in a
form OpenCode can discover: ``.opencode/skills/<name>/SKILL.md`` with matching
frontmatter name and a non-empty description. Graph UX is deliberately excluded.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = REPO_ROOT / ".opencode" / "skills"
LOCK_FILE = REPO_ROOT / "docs" / "design" / "SKILLS.lock.json"

EXPECTED_SKILLS = {"frontend-design", "ui-ux-pro-max"}

_FRONTMATTER = re.compile(r"^---\r?\n(.*?)\r?\n---", re.DOTALL)


def _frontmatter(path: Path) -> dict[str, str]:
    match = _FRONTMATTER.match(path.read_text(encoding="utf-8"))
    assert match is not None, f"{path} is missing YAML frontmatter"
    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip().strip('"')
    return fields


def test_exactly_two_skills_are_installed() -> None:
    installed = {path.name for path in SKILLS_DIR.iterdir() if path.is_dir()}
    assert installed == EXPECTED_SKILLS


def test_each_skill_is_discoverable() -> None:
    for name in EXPECTED_SKILLS:
        skill_file = SKILLS_DIR / name / "SKILL.md"
        assert skill_file.is_file(), f"missing SKILL.md for {name}"
        fields = _frontmatter(skill_file)
        assert fields.get("name") == name, f"{name}: frontmatter name must match directory"
        description = fields.get("description", "")
        assert 1 <= len(description) <= 1024, f"{name}: description length out of range"


def test_lock_file_matches_installed_skills() -> None:
    lock = json.loads(LOCK_FILE.read_text(encoding="utf-8"))
    locked = {skill["name"] for skill in lock["skills"]}
    assert locked == EXPECTED_SKILLS
    for skill in lock["skills"]:
        assert skill["install_path"].startswith(".opencode/skills/")
        assert len(skill["upstream_revision"]) == 40, (
            f"{skill['name']}: upstream revision not pinned"
        )
        assert len(skill["local_sha256"]) == 64
