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
    def __init__(self, path: Path):
        self.path = path

    def is_resolvable(self, *, reference: str, environment: IntegrationEnvironment) -> bool:
        return reference == str(self.path) and self.path.is_file()


def configured_delivery(
    *, data_dir: Path, environment: str, env: Mapping[str, str]
) -> ContactDeliveryPort | None:
    names = (
        "HOST",
        "SENDER",
        "CONTACT_RECIPIENT",
        "PRIVACY_RECIPIENT",
        "USERNAME",
        "PASSWORD_FILE",
        "INTEGRATION_ID",
    )
    values = {name: env.get("AXIGNAL_CONTACT_SMTP_" + name, "").strip() for name in names}
    if not all(values.values()):
        return None
    credential = _CredentialFile(Path(values["PASSWORD_FILE"]))
    service = AdminIntegrationService(
        registry_store=SqliteAdminIntegrationStore(data_dir / "admin-integrations.sqlite3"),
        audit_store=SqliteAdminGovernanceAuditStore(data_dir / "admin-governance-audit.sqlite3"),
    )

    def authorized_password() -> str:
        service.require_connection(
            integration_id=values["INTEGRATION_ID"],
            environment=IntegrationEnvironment(environment.upper()),
            now=datetime.now(UTC),
            required_scopes=frozenset({"email:send"}),
            credential_resolver=credential,
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
    try:
        request = validate_request(payload, kind=kind)
        try:
            delivery = configured_delivery(
                data_dir=data_dir, environment=environment, env=os.environ
            )
        except (ValueError, OSError, sqlite3.Error):
            # Invalid infrastructure must not discard a valid private request.
            delivery = None
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
        return status, {"stored": False, "code": code}
    except (OSError, sqlite3.Error):
        return 503, {"stored": False, "code": "REQUEST_UNAVAILABLE"}
