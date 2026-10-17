"""The manual First Proof gives the tick the governed content rights it was configured with.

Found on the biocultor.com canary (2026-10-17): the command passes its configuration by flag,
the tick read rights only from the environment, so every stored First Proof read as
withdrawn and its 9 leads were blocked with NO_OBSERVED_CAPABILITY_CONTEXT.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from application.observation_runtime.materialization import Readiness
from tools.runtime import observation_enrollment


def test_first_proof_passes_the_authoritys_website_rights(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    seen: dict[str, Any] = {}
    rights = object()

    def ready(authority: Any, config_dir: Path) -> dict[str, object]:
        return {"state": Readiness.READY_FOR_MANUAL_TICK.value}

    def tick(**kwargs: Any) -> dict[str, object]:
        seen.update(kwargs)
        return {"state": "COMPLETED", "candidates_new": 0}

    monkeypatch.setattr(observation_enrollment, "check", ready)
    monkeypatch.setattr(observation_enrollment, "run_scheduled_tick", tick)
    monkeypatch.setattr(observation_enrollment, "load_enrollment", lambda path: ())
    authority = SimpleNamespace(root=tmp_path, clock=None, allows=None, website_rights=rights)
    observation_enrollment.first_proof(authority, tmp_path, code_sha="x", source_ports={})  # type: ignore[arg-type]
    assert seen["website_rights"] is rights


def test_first_proof_reads_the_same_demand_sources_as_the_daily_runner(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # biocultor.com canary, 2026-10-17: the manual tick searched TED only, never PLACSP.
    from application.subscriber_identity.runtime import SystemClock

    seen: dict[str, Any] = {}
    monkeypatch.setattr(observation_enrollment, "check",
                        lambda a, c: {"state": Readiness.READY_FOR_MANUAL_TICK.value})  # fmt: skip
    monkeypatch.setattr(observation_enrollment, "run_scheduled_tick",
                        lambda **kw: seen.update(kw) or {"state": "COMPLETED"})  # fmt: skip
    monkeypatch.setattr(observation_enrollment, "load_enrollment", lambda path: ())
    authority = SimpleNamespace(
        root=tmp_path, clock=SystemClock(), allows=None, website_rights=None
    )
    observation_enrollment.first_proof(authority, tmp_path, code_sha="x")  # type: ignore[arg-type]
    assert set(seen["source_ports"]) == {"ted-search-v3", "es-placsp"}
