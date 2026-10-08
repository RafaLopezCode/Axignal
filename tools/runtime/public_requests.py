"""Private service ingress and governed SMTP composition; no canonical writes."""

from __future__ import annotations

import os
import sqlite3
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path

from application.admin_integrations.service import AdminIntegrationService
from application.public_requests.service import (
    ContactDeliveryPort,
    PublicRequestService,
    RequestKind,
    validate_request,
)
from domain.admin_integrations import IntegrationEnvironment
from pipeline.admin_governance import SqliteAdminGovernanceAuditStore
from pipeline.admin_integrations import SqliteAdminIntegrationStore
from pipeline.public_requests.smtp_delivery import SmtpContactDelivery
from pipeline.public_requests.sqlite_store import SqlitePublicRequestStore


class _CredentialFile:
    def __init__(self, path: Path, reference: str):
        self.path = path
        self.reference = reference

    def is_resolvable(self, *, reference: str, environment: IntegrationEnvironment) -> bool:
        return reference == self.reference and self.path.is_file()


def _smtp_values(env: Mapping[str, str]) -> dict[str, str]:
    names = (
        "HOST",
        "SENDER",
        "CONTACT_RECIPIENT",
        "PRIVACY_RECIPIENT",
        "USERNAME",
        "PASSWORD_FILE",
        "CREDENTIAL_REFERENCE",
        "INTEGRATION_ID",
    )
    return {name: env.get("AXIGNAL_CONTACT_SMTP_" + name, "").strip() for name in names}


def _integration_service(data_dir: Path) -> AdminIntegrationService:
    return AdminIntegrationService(
        registry_store=SqliteAdminIntegrationStore(data_dir / "admin-integrations.sqlite3"),
        audit_store=SqliteAdminGovernanceAuditStore(data_dir / "admin-governance-audit.sqlite3"),
    )


def _require_delivery_authority(
    *, data_dir: Path, environment: str, values: Mapping[str, str]
) -> _CredentialFile:
    credential = _CredentialFile(Path(values["PASSWORD_FILE"]), values["CREDENTIAL_REFERENCE"])
    _integration_service(data_dir).require_connection(
        integration_id=values["INTEGRATION_ID"],
        environment=IntegrationEnvironment(environment.upper()),
        now=datetime.now(UTC),
        required_scopes=frozenset({"email:send"}),
        credential_resolver=credential,
    )
    return credential


def delivery_enabled(*, data_dir: Path, environment: str, env: Mapping[str, str]) -> bool:
    """True only when configuration and governed provider authority are both live."""
    values = _smtp_values(env)
    if not all(values.values()):
        return False
    try:
        _require_delivery_authority(data_dir=data_dir, environment=environment, values=values)
    except (PermissionError, ValueError, OSError, sqlite3.Error):
        return False
    return True


def public_request_status(
    *, data_dir: Path, environment: str, env: Mapping[str, str], kind: RequestKind
) -> dict[str, object]:
    """Public, non-secret status contract used before showing a request form."""
    # Controller/country are human product decisions. Public email remains explicitly
    # nullable until an operator publishes a verified channel; never synthesize one.
    public_email = env.get("AXIGNAL_PUBLIC_CONTACT_EMAIL", "").strip() or None
    return {
        "enabled": delivery_enabled(data_dir=data_dir, environment=environment, env=env),
        "controller": "AXIGNAL",
        "country": "Spain",
        "publicEmail": public_email,
    }


def configured_delivery(
    *, data_dir: Path, environment: str, env: Mapping[str, str]
) -> ContactDeliveryPort | None:
    values = _smtp_values(env)
    if not all(values.values()):
        return None

    def authorized_password() -> str:
        credential = _require_delivery_authority(
            data_dir=data_dir, environment=environment, values=values
        )
        return credential.path.read_text(encoding="utf-8").strip()

    return SmtpContactDelivery(
        values["HOST"],
        int(env.get("AXIGNAL_CONTACT_SMTP_PORT", "465")),
        values["SENDER"],
        values["CONTACT_RECIPIENT"],
        values["PRIVACY_RECIPIENT"],
        values["USERNAME"],
        authorized_password,
    )


def submit_public_request(
    *, data_dir: Path, environment: str, payload: object, kind: RequestKind
) -> tuple[int, dict[str, object]]:
    # Fail closed: a visitor must never see a successful receipt for a channel that
    # was not authorized and live when the request arrived.
    if not delivery_enabled(data_dir=data_dir, environment=environment, env=os.environ):
        return 503, {"status": "rejected", "reason": "CHANNEL_UNAVAILABLE"}

    try:
        request = validate_request(payload, kind=kind)
        delivery = configured_delivery(data_dir=data_dir, environment=environment, env=os.environ)
        if delivery is None:
            return 503, {"status": "rejected", "reason": "CHANNEL_UNAVAILABLE"}
        service = PublicRequestService(
            SqlitePublicRequestStore(data_dir / "public-requests.sqlite3"), delivery
        )
        receipt = service.submit(request, now=datetime.now(UTC))
        return 202, receipt.public()
    except ValueError as error:
        code = str(error)
        if code not in {
            "INVALID_REQUEST",
            "INVALID_EMAIL",
            "INVALID_MESSAGE",
            "INVALID_LOCALE",
            "INVALID_CATEGORY",
            "REQUEST_REF_CONFLICT",
            "REQUEST_RATE_LIMITED",
        }:
            code = "REQUEST_UNAVAILABLE"
        status = (
            429
            if code == "REQUEST_RATE_LIMITED"
            else 409
            if code == "REQUEST_REF_CONFLICT"
            else 400
        )
        return status, {"status": "rejected", "reason": code}
    except (OSError, sqlite3.Error):
        return 503, {"status": "rejected", "reason": "REQUEST_UNAVAILABLE"}
