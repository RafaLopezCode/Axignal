"""Fail-closed environment configuration for the AXIGNAL production runtime."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True, slots=True)
class RuntimeConfig:
    environment: str
    bind_host: str
    port: int
    code_sha: str
    data_dir: Path
    web_root: Path
    first_proof_allowed_host: str | None = None
    containerized: bool = False
    stripe_account_id: str | None = None
    stripe_base_price_ref: str | None = None
    stripe_additional_xeed_price_ref: str | None = None
    stripe_webhook_signing_secret: str | None = field(default=None, repr=False)
    weekly_brief_requests_enabled: bool = False
    acquisition_events_enabled: bool = False
    organization_catalog_path: Path | None = None

    @classmethod
    def from_env(cls) -> RuntimeConfig:
        environment = os.getenv("AXIGNAL_ENV", "development").strip().lower()
        bind_host = os.getenv("AXIGNAL_BIND_HOST", "127.0.0.1").strip()
        port = int(os.getenv("AXIGNAL_PORT", "8765"))
        code_sha = os.getenv("AXIGNAL_CODE_SHA", "UNKNOWN").strip()
        data_raw = os.getenv("AXIGNAL_DATA_DIR", "").strip()
        web_raw = os.getenv("AXIGNAL_WEB_ROOT", "").strip()
        first_proof_allowed_host = (
            os.getenv("AXIGNAL_FIRST_PROOF_ALLOWED_HOST", "").strip().lower() or None
        )
        containerized = os.getenv("AXIGNAL_CONTAINERIZED", "").strip().lower() in {
            "1",
            "true",
            "yes",
        }
        stripe_account_id = os.getenv("AXIGNAL_STRIPE_ACCOUNT_ID", "").strip() or None
        stripe_base_price_ref = os.getenv("AXIGNAL_STRIPE_BASE_PRICE_REF", "").strip() or None
        stripe_additional_xeed_price_ref = (
            os.getenv("AXIGNAL_STRIPE_ADDITIONAL_XEED_PRICE_REF", "").strip() or None
        )
        stripe_webhook_signing_secret = (
            os.getenv("AXIGNAL_STRIPE_WEBHOOK_SIGNING_SECRET", "").strip() or None
        )
        weekly_brief_requests_enabled = os.getenv(
            "AXIGNAL_WEEKLY_BRIEF_REQUESTS_ENABLED", ""
        ).strip().lower() in {"1", "true", "yes"}
        acquisition_events_enabled = os.getenv(
            "AXIGNAL_ACQUISITION_EVENTS_ENABLED", ""
        ).strip().lower() in {"1", "true", "yes"}

        if not bind_host:
            raise ValueError("AXIGNAL_BIND_HOST cannot be empty")
        if not 1 <= port <= 65535:
            raise ValueError("AXIGNAL_PORT must be a valid TCP port")
        if not data_raw:
            raise ValueError("AXIGNAL_DATA_DIR is required")
        if not web_raw:
            raise ValueError("AXIGNAL_WEB_ROOT is required")
        if environment == "production" and code_sha == "UNKNOWN":
            raise ValueError("AXIGNAL_CODE_SHA is required in production")
        if (
            environment == "production"
            and bind_host not in {"127.0.0.1", "::1"}
            and not (containerized and bind_host == "0.0.0.0")
        ):
            raise ValueError(
                "production runtime must bind to loopback unless explicitly containerized"
            )

        stripe_values = (
            stripe_account_id,
            stripe_base_price_ref,
            stripe_additional_xeed_price_ref,
            stripe_webhook_signing_secret,
        )
        if any(value is not None for value in stripe_values) and not all(
            value is not None for value in stripe_values
        ):
            raise ValueError(
                "Stripe webhook runtime requires account, both price refs and signing secret"
            )
        if stripe_account_id is not None and not stripe_account_id.startswith("acct_"):
            raise ValueError("AXIGNAL_STRIPE_ACCOUNT_ID must be a Stripe account id")

        data_dir = Path(data_raw).expanduser().resolve()
        web_root = Path(web_raw).expanduser().resolve()
        if not web_root.is_dir():
            raise ValueError("AXIGNAL_WEB_ROOT must exist and be a directory")
        data_dir.mkdir(parents=True, exist_ok=True)
        return cls(
            environment,
            bind_host,
            port,
            code_sha,
            data_dir,
            web_root,
            first_proof_allowed_host,
            containerized,
            stripe_account_id,
            stripe_base_price_ref,
            stripe_additional_xeed_price_ref,
            stripe_webhook_signing_secret,
            weekly_brief_requests_enabled,
            acquisition_events_enabled,
            Path(os.environ["AXIGNAL_ORGANIZATION_CATALOG"]).expanduser().resolve()
            if os.getenv("AXIGNAL_ORGANIZATION_CATALOG")
            else None,
        )
