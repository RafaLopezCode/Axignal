"""Adversarial tests for the external Golden Master source identity recipe."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from tools.governance.golden_master_manifest import (
    ManifestError,
    build_current_manifest,
    verify_manifest,
)


def _source_tree(root: Path) -> dict[str, object]:
    (root / "src" / "v2").mkdir(parents=True)
    (root / "index.html").write_bytes(b"<!doctype html>\n")
    (root / "src" / "v2" / "app.tsx").write_bytes(b"export const app = 1\n")
    return {
        "schema_version": 1,
        "included_paths": ["index.html", "src/v2/app.tsx"],
        "recursive_source_roots": ["src/v2"],
        "excluded_paths": [".git/", "node_modules/", "dist/", "coverage/"],
        "files": [],
        "aggregate_sha256": "",
    }


def test_manifest_is_repeatable_and_omits_absolute_root(tmp_path: Path) -> None:
    spec = _source_tree(tmp_path)

    first = build_current_manifest(tmp_path, spec)
    second = build_current_manifest(tmp_path, spec)

    assert first == second
    assert first["aggregate_sha256"] == second["aggregate_sha256"]
    assert tmp_path.as_posix() not in str(first)


def test_manifest_order_is_stable_independent_of_input_order(tmp_path: Path) -> None:
    spec = _source_tree(tmp_path)
    reversed_spec = deepcopy(spec)
    reversed_spec["included_paths"] = list(reversed(spec["included_paths"]))  # type: ignore[arg-type]

    first = build_current_manifest(tmp_path, spec)
    second = build_current_manifest(tmp_path, reversed_spec)

    assert first["files"] == second["files"]
    assert first["aggregate_sha256"] == second["aggregate_sha256"]


def test_source_byte_change_changes_digest(tmp_path: Path) -> None:
    spec = _source_tree(tmp_path)
    before = build_current_manifest(tmp_path, spec)
    (tmp_path / "src" / "v2" / "app.tsx").write_bytes(b"export const app = 2\n")

    after = build_current_manifest(tmp_path, spec)

    assert before["aggregate_sha256"] != after["aggregate_sha256"]


def test_line_ending_change_is_a_source_change(tmp_path: Path) -> None:
    spec = _source_tree(tmp_path)
    before = build_current_manifest(tmp_path, spec)
    (tmp_path / "index.html").write_bytes(b"<!doctype html>\r\n")

    after = build_current_manifest(tmp_path, spec)

    assert before["aggregate_sha256"] != after["aggregate_sha256"]


def test_generated_output_and_dependencies_are_excluded(tmp_path: Path) -> None:
    spec = _source_tree(tmp_path)
    before = build_current_manifest(tmp_path, spec)
    (tmp_path / "dist").mkdir()
    (tmp_path / "dist" / "bundle.js").write_bytes(b"generated")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "dependency.js").write_bytes(b"installed")

    after = build_current_manifest(tmp_path, spec)

    assert before["aggregate_sha256"] == after["aggregate_sha256"]


def test_missing_required_input_fails_closed(tmp_path: Path) -> None:
    spec = _source_tree(tmp_path)
    (tmp_path / "index.html").unlink()

    with pytest.raises(ManifestError, match="required input is missing"):
        build_current_manifest(tmp_path, spec)


def test_unexpected_file_under_active_source_root_fails_closed(tmp_path: Path) -> None:
    spec = _source_tree(tmp_path)
    (tmp_path / "src" / "v2" / "extra.ts").write_bytes(b"unexpected")

    with pytest.raises(ManifestError, match="unexpected source file"):
        build_current_manifest(tmp_path, spec)


@pytest.mark.parametrize("unsafe_path", ["../outside", "C:/outside", "src/./file"])
def test_noncanonical_or_escaping_paths_fail_closed(tmp_path: Path, unsafe_path: str) -> None:
    spec = _source_tree(tmp_path)
    spec["included_paths"] = [unsafe_path]

    with pytest.raises(ManifestError, match="invalid relative POSIX path"):
        build_current_manifest(tmp_path, spec)


def test_verification_rejects_source_drift(tmp_path: Path) -> None:
    spec = _source_tree(tmp_path)
    baseline = build_current_manifest(tmp_path, spec)
    (tmp_path / "src" / "v2" / "app.tsx").write_bytes(b"changed")

    with pytest.raises(ManifestError, match="source digest mismatch"):
        verify_manifest(tmp_path, baseline)
