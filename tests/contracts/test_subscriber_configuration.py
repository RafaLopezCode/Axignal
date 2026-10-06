from pathlib import Path

import pytest

from tools.runtime.subscriber_configuration import (
    SubscriberConfigurationError,
    load_subscriber_settings,
)


def test_explicit_file_ignores_model_keys_and_never_expands(tmp_path: Path) -> None:
    path = tmp_path / "axignal.env"
    path.write_text("OPENAI_API_KEY=never-load\nAXIGNAL_GOOGLE_CLIENT_ID=$(unsafe)\n")
    result = load_subscriber_settings({}, configuration_file=path)
    assert "OPENAI_API_KEY" not in result.values
    assert result.values["AXIGNAL_GOOGLE_CLIENT_ID"] == "$(unsafe)"
    assert "unsafe" not in repr(result)
    assert not result.provider_ready("google")


def test_environment_override_and_exact_registered_callback(tmp_path: Path) -> None:
    path = tmp_path / "axignal.env"
    path.write_text("AXIGNAL_SUBSCRIBER_ENABLED=false\n")
    env = {
        "AXIGNAL_SUBSCRIBER_ENABLED": "true",
        "AXIGNAL_EXPERIENCE_ORIGIN": "https://axignal.com",
        "AXIGNAL_GOOGLE_CLIENT_ID": "client",
        "AXIGNAL_GOOGLE_REGISTERED": "true",
        "AXIGNAL_GOOGLE_REDIRECT_URI": "https://axignal.com/api/auth/callback/google",
    }
    assert load_subscriber_settings(env, configuration_file=path).provider_ready("google")
    env["AXIGNAL_GOOGLE_REDIRECT_URI"] += "?return=external"
    assert not load_subscriber_settings(env).provider_ready("google")


def test_operator_name_alone_does_not_publish_contracting() -> None:
    assert not load_subscriber_settings(
        {
            "AXIGNAL_SUBSCRIBER_ENABLED": "true",
            "AXIGNAL_SUBSCRIBER_CONTRACTING_ENABLED": "true",
            "AXIGNAL_LEGAL_OPERATOR_NAME": "Axignal SLU",
        }
    ).contracting_enabled


@pytest.mark.parametrize(
    "origin",
    [
        "https://axignal.com/path",
        "http://axignal.com",
        "https://u:p@axignal.com",
        "https://axignal.com#x",
    ],
)
def test_rejected_public_origins(origin: str) -> None:
    with pytest.raises(SubscriberConfigurationError):
        load_subscriber_settings({"AXIGNAL_EXPERIENCE_ORIGIN": origin})


def test_duplicate_allowed_keys_fail_closed(tmp_path: Path) -> None:
    path = tmp_path / "axignal.env"
    path.write_text("AXIGNAL_SUBSCRIBER_ENABLED=true\nAXIGNAL_SUBSCRIBER_ENABLED=false\n")
    with pytest.raises(SubscriberConfigurationError):
        load_subscriber_settings({}, configuration_file=path)
