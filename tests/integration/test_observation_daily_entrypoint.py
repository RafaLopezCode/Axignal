from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.runtime import observation_daily
from tools.runtime.observation_daily import ObservationRuntimeConfigurationError, load_enrollment


def test_entrypoint_is_off_by_default(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.delenv("AXIGNAL_OBSERVATION_RUNTIME_ENABLED", raising=False)
    observation_daily.main([])
    assert json.loads(capsys.readouterr().out) == {"state": "DISABLED"}


def test_enabled_without_server_owned_inputs_fails_closed(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    monkeypatch.setenv("AXIGNAL_OBSERVATION_RUNTIME_ENABLED", "true")
    monkeypatch.setenv("AXIGNAL_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("AXIGNAL_SUBSCRIBER_OBSERVATION_PLAN_FILE", raising=False)
    monkeypatch.delenv("AXIGNAL_OBSERVATION_RUNTIME_ENROLLMENT_FILE", raising=False)
    with pytest.raises(SystemExit):
        observation_daily.main([])
    assert json.loads(capsys.readouterr().out) == {"state": "NOT_CONFIGURED"}


@pytest.mark.parametrize(
    "content",
    [
        "{}",
        '[{"tenantId":"t"}]',
        '[{"tenantId":"t","principalId":" ","focusId":"f"}]',
        '[{"tenantId":"t","principalId":"p","focusId":"f"},{"tenantId":"t","principalId":"p","focusId":"f"}]',
    ],
)
def test_enrollment_is_strict(tmp_path: Path, content: str) -> None:
    path = tmp_path / "enrollment.json"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(ObservationRuntimeConfigurationError):
        load_enrollment(path)
