from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from tools.governance import checks


def _configure_graphify(root: Path, *, with_graph: bool) -> None:
    (root / ".graphifyignore").write_text("# configured\n", encoding="utf-8")
    governance = root / "docs" / "governance"
    governance.mkdir(parents=True)
    (governance / "GRAPHIFY.md").write_text("# Graphify\n", encoding="utf-8")
    if with_graph:
        graph = root / "graphify-out" / "graph.json"
        graph.parent.mkdir(parents=True)
        graph.write_text("{}", encoding="utf-8")


def test_graphify_is_required_when_repository_declares_it(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _configure_graphify(tmp_path, with_graph=True)
    monkeypatch.setattr(checks.shutil, "which", lambda _name: None)

    problems = checks.check_graphify(tmp_path)

    assert problems == [
        "graphify is required by AXIGNAL repository configuration, "
        "but the graphify executable is not available on PATH"
    ]


def test_graphify_absence_is_allowed_for_unconfigured_repository(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(checks.shutil, "which", lambda _name: None)

    assert checks.check_graphify(tmp_path) == []


def test_graphify_configured_repository_requires_generated_graph(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _configure_graphify(tmp_path, with_graph=False)
    monkeypatch.setattr(checks.shutil, "which", lambda _name: "C:/tools/graphify.exe")

    assert checks.check_graphify(tmp_path) == [
        "graphify is configured but graphify-out/graph.json is missing; "
        "run graphify update . before governance"
    ]


def test_graphify_check_update_failure_is_reported(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _configure_graphify(tmp_path, with_graph=True)
    monkeypatch.setattr(checks.shutil, "which", lambda _name: "C:/tools/graphify.exe")
    monkeypatch.setattr(
        checks.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(
            returncode=2,
            stdout="",
            stderr="graph is stale",
        ),
    )

    assert checks.check_graphify(tmp_path) == ["graphify check-update failed: graph is stale"]


def test_graphify_check_update_success_passes(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _configure_graphify(tmp_path, with_graph=True)
    monkeypatch.setattr(checks.shutil, "which", lambda _name: "C:/tools/graphify.exe")
    monkeypatch.setattr(
        checks.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(
            returncode=0,
            stdout="",
            stderr="",
        ),
    )

    assert checks.check_graphify(tmp_path) == []
