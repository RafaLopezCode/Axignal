"""Design-skill installation contract (deterministic, offline, no LLM).

Verifies pinned upstream UI/UX skills and the AXIGNAL-authored graph skill
are discoverable project-locally with reviewable upstream provenance.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = REPO_ROOT / ".opencode" / "skills"
LOCK_FILE = REPO_ROOT / "docs" / "design" / "SKILLS.lock.json"

EXPECTED_SKILLS = {
    "frontend-design",
    "ui-ux-pro-max",
    "design-taste-frontend",
    "web-design-guidelines",
}
EXPECTED_LOCAL_SKILLS = EXPECTED_SKILLS | {"axignal-graph-design"}

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


def test_expected_project_local_skills_are_installed() -> None:
    installed = {path.name for path in SKILLS_DIR.iterdir() if path.is_dir()}
    assert installed == EXPECTED_LOCAL_SKILLS


def test_each_skill_is_discoverable() -> None:
    for name in EXPECTED_LOCAL_SKILLS:
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


def test_additional_design_skills_have_verified_shared_content_and_agent_entries() -> None:
    lock = json.loads(LOCK_FILE.read_text(encoding="utf-8"))
    for skill in lock["skills"]:
        if skill["name"] not in {"design-taste-frontend", "web-design-guidelines"}:
            continue
        corpus = SKILLS_DIR / skill["name"]
        hashes = skill["local_files_sha256"]
        assert hashes["SKILL.md"] == skill["local_sha256"]
        installed = {p.relative_to(corpus).as_posix() for p in corpus.rglob("*") if p.is_file()}
        assert installed == set(hashes)
        for relative_path, expected_hash in hashes.items():
            assert (
                hashlib.sha256((corpus / relative_path).read_bytes()).hexdigest() == expected_hash
            )
        for entrypoint_key in ("codex_entrypoint", "claude_entrypoint"):
            entrypoint = REPO_ROOT / skill[entrypoint_key]
            assert _frontmatter(entrypoint)["name"] == skill["name"]
            assert skill["install_path"] in entrypoint.read_text(encoding="utf-8")
