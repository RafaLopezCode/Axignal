"""The Admin's organizations get the ten-family First Observation a subscriber gets."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from tools.runtime.service import _admin_first_observation, _admin_reference, _admin_study


class Observing:
    def __init__(self) -> None:
        self.studied: list[tuple[str, str, str]] = []
        self.views: dict[str, dict[str, Any]] = {}

    def study(self, ref: str, website: str, name: str) -> str:
        self.studied.append((ref, website, name))
        self.views[ref] = {"state": "QUEUED", "discoveries": []}
        return "QUEUED"

    def study_result(self, ref: str) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        return self.views.get(ref), {}


def test_admin_reference_is_the_bare_host() -> None:
    assert _admin_reference("https://www.axignal.com/es") == "admin:axignal.com"
    assert _admin_reference("not a url") is None


def test_an_admin_organization_is_studied_once_and_its_view_returned() -> None:
    observing = Observing()
    runtime = SimpleNamespace(subscriber=SimpleNamespace(first_observation=observing))
    view = _admin_first_observation(runtime, "AXIGNAL", "https://www.axignal.com/")
    assert view == {"state": "QUEUED", "discoveries": []}
    assert observing.studied == [("admin:axignal.com", "https://axignal.com/", "AXIGNAL")]
    _admin_first_observation(runtime, "AXIGNAL", "https://www.axignal.com/")
    assert len(observing.studied) == 1  # read again: never re-studied on every read
    _admin_study(runtime, "AXIGNAL", "https://axignal.com/")
    assert len(observing.studied) == 2  # an explicit 'observe again' studies again


def test_without_first_observation_the_admin_reading_is_unchanged() -> None:
    runtime = SimpleNamespace(subscriber=None)
    assert _admin_first_observation(runtime, "X", "https://x.example/") is None
    _admin_study(runtime, "X", "https://x.example/")  # no error
