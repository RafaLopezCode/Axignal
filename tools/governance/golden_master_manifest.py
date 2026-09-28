"""Verify the byte identity of the active DeepSeek V2 source inputs.

This records source identity only. It does not claim visual, behavioral,
product, accessibility, or build-output correctness.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any


class ManifestError(ValueError):
    """The configured Golden Master source tree does not match its manifest."""


def _validated_paths(manifest: dict[str, Any]) -> tuple[list[str], list[str]]:
    included = manifest.get("included_paths")
    roots = manifest.get("recursive_source_roots")
    if not isinstance(included, list) or not all(isinstance(path, str) for path in included):
        raise ManifestError("included_paths must be a list of relative POSIX paths")
    if not isinstance(roots, list) or not all(isinstance(path, str) for path in roots):
        raise ManifestError("recursive_source_roots must be a list of relative POSIX paths")

    for value in [*included, *roots]:
        path = PurePosixPath(value)
        windows_path = PureWindowsPath(value)
        if (
            not value
            or "\\" in value
            or ":" in value
            or path.is_absolute()
            or windows_path.is_absolute()
            or windows_path.drive
            or path.as_posix() != value
            or any(part in {"", ".", ".."} for part in path.parts)
        ):
            raise ManifestError(f"invalid relative POSIX path: {value!r}")
    if len(included) != len(set(included)):
        raise ManifestError("included_paths contains duplicates")
    if len(roots) != len(set(roots)):
        raise ManifestError("recursive_source_roots contains duplicates")
    return sorted(included), sorted(roots)


def _reject_symlinks(path: Path, relative: str) -> None:
    if path.is_symlink():
        raise ManifestError(f"symlinks are forbidden in the manifest scope: {relative}")


def collect_file_records(root: Path, manifest: dict[str, Any]) -> list[dict[str, Any]]:
    """Hash exact bytes for the explicit inventory and reject active-root drift."""

    if root.is_symlink():
        raise ManifestError("Golden Master root must not be a symlink")
    if not root.is_dir():
        raise ManifestError("Golden Master root is not a directory")
    included, source_roots = _validated_paths(manifest)
    expected = set(included)

    for source_root in source_roots:
        directory = root.joinpath(*PurePosixPath(source_root).parts)
        _reject_symlinks(directory, source_root)
        if not directory.is_dir():
            raise ManifestError(f"required source root is missing: {source_root}")
        for candidate in directory.rglob("*"):
            relative = candidate.relative_to(root).as_posix()
            _reject_symlinks(candidate, relative)
            if candidate.is_file() and relative not in expected:
                raise ManifestError(f"unexpected source file: {relative}")

    records: list[dict[str, Any]] = []
    for relative in included:
        path = root.joinpath(*PurePosixPath(relative).parts)
        _reject_symlinks(path, relative)
        if not path.is_file():
            raise ManifestError(f"required input is missing or not a file: {relative}")
        content = path.read_bytes()
        records.append(
            {
                "path": relative,
                "size_bytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        )
    return records


def aggregate_digest(records: list[dict[str, Any]]) -> str:
    """Hash sorted UTF-8 records: path NUL size NUL per-file SHA-256 LF."""

    ordered = sorted(records, key=lambda record: record["path"])
    stream = bytearray()
    for record in ordered:
        stream.extend(record["path"].encode("utf-8"))
        stream.extend(b"\0")
        stream.extend(str(record["size_bytes"]).encode("ascii"))
        stream.extend(b"\0")
        stream.extend(record["sha256"].encode("ascii"))
        stream.extend(b"\n")
    return hashlib.sha256(stream).hexdigest()


def build_current_manifest(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    records = collect_file_records(root, manifest)
    return {
        **manifest,
        "files": records,
        "aggregate_sha256": aggregate_digest(records),
    }


def verify_manifest(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    expected_records = manifest.get("files")
    aggregate = manifest.get("aggregate_sha256")
    if not isinstance(expected_records, list):
        raise ManifestError("files must be a list of per-file digest records")
    for record in expected_records:
        if (
            not isinstance(record, dict)
            or set(record) != {"path", "size_bytes", "sha256"}
            or not isinstance(record.get("path"), str)
            or not isinstance(record.get("size_bytes"), int)
            or isinstance(record.get("size_bytes"), bool)
            or record["size_bytes"] < 0
            or not isinstance(record.get("sha256"), str)
            or re.fullmatch(r"[0-9a-f]{64}", record["sha256"]) is None
        ):
            raise ManifestError("invalid per-file digest record")
    if not isinstance(aggregate, str) or re.fullmatch(r"[0-9a-f]{64}", aggregate) is None:
        raise ManifestError("aggregate_sha256 must be a lowercase SHA-256 digest")
    current = build_current_manifest(root, manifest)
    if current["files"] != expected_records:
        expected_by_path = {record.get("path"): record for record in expected_records}
        current_by_path = {record["path"]: record for record in current["files"]}
        changed = sorted(
            path
            for path in set(expected_by_path) | set(current_by_path)
            if expected_by_path.get(path) != current_by_path.get(path)
        )
        raise ManifestError("source digest mismatch: " + ", ".join(changed))
    if current["aggregate_sha256"] != manifest.get("aggregate_sha256"):
        raise ManifestError("aggregate digest mismatch")
    return current


def _write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    rendered = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    path.write_text(rendered, encoding="utf-8", newline="\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True, help="external Golden Master root")
    parser.add_argument(
        "--manifest", type=Path, required=True, help="versioned repository manifest"
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--verify", action="store_true", help="verify against recorded file digests")
    mode.add_argument("--write-baseline", action="store_true", help="record current source digests")
    args = parser.parse_args(argv)

    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
            raise ManifestError("unsupported manifest schema")
        current = build_current_manifest(args.root, manifest)
        if args.write_baseline:
            _write_manifest(args.manifest, current)
        else:
            verify_manifest(args.root, manifest)
        print("MANIFEST_VERSION=1")
        print(f"FILE_COUNT={len(current['files'])}")
        print(f"AGGREGATE_SHA256={current['aggregate_sha256']}")
        print("STATUS=PASS")
        return 0
    except (OSError, json.JSONDecodeError, ManifestError) as error:
        print(f"STATUS=FAIL: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
