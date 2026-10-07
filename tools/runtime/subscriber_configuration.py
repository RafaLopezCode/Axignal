"""Explicit, non-expanding subscriber configuration; never evaluates an env file."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

_KEYS = frozenset(
    {
        "AXIGNAL_EXPERIENCE_ORIGIN",
        "AXIGNAL_SUBSCRIBER_ENABLED",
        "AXIGNAL_SUBSCRIBER_CONTRACTING_ENABLED",
        "AXIGNAL_SUBSCRIBER_PILOT_ENABLED",
        "AXIGNAL_LEGAL_OPERATOR_NAME",
        "AXIGNAL_LEGAL_OPERATOR_KIND",
        "AXIGNAL_LEGAL_TAX_ID",
        "AXIGNAL_LEGAL_ADDRESS",
        "AXIGNAL_LEGAL_CONTACT",
        "AXIGNAL_LEGAL_TERMS_VERSION",
        "AXIGNAL_STRIPE_LIVE_ENABLED",
        "AXIGNAL_STRIPE_API_VERSION",
        "AXIGNAL_STRIPE_ACCOUNT_ID",
        "AXIGNAL_STRIPE_API_KEY_FILE",
        "AXIGNAL_STRIPE_WEBHOOK_SIGNING_SECRET_FILE",
        "AXIGNAL_STRIPE_BASE_PRICE_REF",
        "AXIGNAL_STRIPE_ADDITIONAL_XEED_PRICE_REF",
        "AXIGNAL_SUBSCRIBER_OBSERVATION_PLAN_FILE",
        *(
            f"AXIGNAL_{provider}_{suffix}"
            for provider in ("GOOGLE", "CHATGPT")
            for suffix in ("CLIENT_ID", "CLIENT_SECRET_FILE", "REDIRECT_URI", "REGISTERED")
        ),
    }
)


class SubscriberConfigurationError(ValueError):
    """Safe error: never contains a setting's value or credential path."""


def read_subscriber_settings_file(path: Path) -> dict[str, str]:
    """Read only declared subscriber settings; unrelated API keys are ignored."""
    if path.stat().st_size > 65536:
        raise SubscriberConfigurationError("configuration file is too large")
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        key, separator, value = stripped.partition("=")
        key = key.strip()
        if key not in _KEYS:
            continue
        if not separator or key in values:
            raise SubscriberConfigurationError("ambiguous subscriber configuration")
        value = value.strip()
        if value[:1] in {"'", '"'}:
            if len(value) < 2 or value[-1] != value[0]:
                raise SubscriberConfigurationError("invalid quoted configuration")
            value = value[1:-1]
        if any(ord(char) < 32 for char in value):
            raise SubscriberConfigurationError("invalid configuration characters")
        values[key] = value
    return values


def _flag(value: str) -> bool:
    if value not in {"", "false", "true"}:
        raise SubscriberConfigurationError("flags require true or false")
    return value == "true"


def _origin(value: str) -> str:
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as exc:
        raise SubscriberConfigurationError("invalid experience origin") from exc
    local = parsed.hostname in {"127.0.0.1", "localhost", "::1"}
    if (
        not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
        or (parsed.scheme != "https" and not (local and parsed.scheme == "http"))
        or (not local and port not in {None, 443})
    ):
        raise SubscriberConfigurationError("experience origin rejected")
    return value.rstrip("/")


@dataclass(frozen=True, slots=True)
class SubscriberSettings:
    enabled: bool
    contracting_requested: bool
    origin: str
    values: Mapping[str, str] = field(repr=False)

    @property
    def legal_ready(self) -> bool:
        return all(
            self.values.get(f"AXIGNAL_LEGAL_{key}", "").strip()
            for key in ("OPERATOR_NAME", "TAX_ID", "ADDRESS", "CONTACT", "TERMS_VERSION")
        )

    @property
    def contracting_enabled(self) -> bool:
        return self.enabled and self.contracting_requested and self.legal_ready

    @property
    def pilot_enabled(self) -> bool:
        return self.enabled and _flag(self.values.get("AXIGNAL_SUBSCRIBER_PILOT_ENABLED", "false"))

    def provider_ready(self, provider: str) -> bool:
        prefix = {"google": "GOOGLE", "openai": "CHATGPT"}.get(provider)
        if prefix is None or not self.enabled:
            return False
        client = self.values.get(f"AXIGNAL_{prefix}_CLIENT_ID", "")
        callback = self.values.get(f"AXIGNAL_{prefix}_REDIRECT_URI", "")
        registered = _flag(self.values.get(f"AXIGNAL_{prefix}_REGISTERED", "false"))
        return bool(
            client and registered and callback == f"{self.origin}/api/auth/callback/{provider}"
        )


def load_subscriber_settings(
    environment: Mapping[str, str], *, configuration_file: Path | None = None
) -> SubscriberSettings:
    values = read_subscriber_settings_file(configuration_file) if configuration_file else {}
    values.update({key: value for key, value in environment.items() if key in _KEYS})
    return SubscriberSettings(
        enabled=_flag(values.get("AXIGNAL_SUBSCRIBER_ENABLED", "false")),
        contracting_requested=_flag(values.get("AXIGNAL_SUBSCRIBER_CONTRACTING_ENABLED", "false")),
        origin=_origin(values.get("AXIGNAL_EXPERIENCE_ORIGIN", "http://127.0.0.1:3810")),
        values=values,
    )
