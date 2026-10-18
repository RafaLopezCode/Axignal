"""The manual First Proof passes its configuration to everything the tick builds.

biocultor.com canary (2026-10-18): the configuration came by flag, the economic runtime
read it only from the environment, so it ran without website rights; the stored website
text was not reusable and every demand lead blocked with NO_OBSERVED_CAPABILITY_CONTEXT
(0 of 4 executed). With the configuration passed on: 15 leads, 76 candidates, 160 evidence.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from tools.runtime import observation_daily, observation_enrollment


def test_first_proof_forwards_its_configuration_to_the_tick(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: dict[str, Any] = {}
    monkeypatch.setattr(
        observation_enrollment, "check", lambda *_: {"state": "READY_FOR_MANUAL_TICK"}
    )
    monkeypatch.setattr(observation_enrollment, "load_enrollment", lambda _path: ())

    def tick(**kwargs: Any) -> dict[str, object]:
        seen.update(kwargs)
        return {"state": "COMPLETED"}

    monkeypatch.setattr(observation_enrollment, "run_scheduled_tick", tick)
    conf = tmp_path / "subscriber.conf"
    authority = SimpleNamespace(
        root=tmp_path, clock=None, allows=lambda *_: True, website_rights=object(),
        configuration_file=conf,
    )  # fmt: skip
    observation_enrollment.first_proof(authority, tmp_path, code_sha="x", source_ports={})  # type: ignore[arg-type]
    assert seen["configuration_file"] == conf
    assert seen["website_rights"] is authority.website_rights


def test_the_economic_runtime_reads_the_configuration_it_is_given(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("AXIGNAL_SUBSCRIBER_CONFIGURATION_FILE", raising=False)
    read: list[Path | None] = []
    from tools.runtime import subscriber_configuration

    real = subscriber_configuration.load_subscriber_settings

    def spy(environ: Any, *, configuration_file: Path | None = None) -> Any:
        read.append(configuration_file)
        return real(environ, configuration_file=None)

    monkeypatch.setattr(subscriber_configuration, "load_subscriber_settings", spy)
    conf = tmp_path / "subscriber.conf"
    observation_daily.build_economic_runtime(tmp_path, code_sha="x", configuration_file=conf)
    observation_daily.build_economic_runtime(tmp_path, code_sha="x")
    assert read == [conf, None]  # given → used; none given and none in the environment → none
