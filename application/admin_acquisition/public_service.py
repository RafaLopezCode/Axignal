"""Public AO-15 request/consent operations."""

from __future__ import annotations

from datetime import datetime

from application.admin_acquisition.service import (
    AcquisitionStore,
    _append,
    _payload,
    _snapshot,
)
from domain.admin_acquisition import (
    BriefRequestEventKind,
    BriefRequestSnapshot,
    NewsletterConsentState,
    normalize_domain,
    normalize_email,
)


class PublicBriefRequestService:
    def __init__(self, store: AcquisitionStore) -> None:
        self._store = store

    def submit(
        self,
        *,
        request_id: str,
        company_name: str,
        company_domain: str,
        professional_email: str,
        purpose: str,
        request_notice_version: str,
        now: datetime,
        newsletter_consent: bool = False,
        newsletter_notice_version: str | None = None,
    ) -> BriefRequestSnapshot:
        if not company_name.strip() or not purpose.strip() or not request_notice_version.strip():
            raise ValueError("company_name, purpose and request_notice_version are required")
        if newsletter_consent and not newsletter_notice_version:
            raise ValueError("newsletter consent requires a notice version")
        _append(
            self._store,
            event_id=f"{request_id}:submitted",
            request_id=request_id,
            kind=BriefRequestEventKind.REQUEST_SUBMITTED,
            occurred_at=now,
            actor="public-request",
            payload=_payload(
                company_name=company_name.strip(),
                company_domain=normalize_domain(company_domain),
                professional_email=normalize_email(professional_email),
                purpose=purpose.strip(),
                request_notice_version=request_notice_version.strip(),
            ),
        )
        if newsletter_consent:
            _append(
                self._store,
                event_id=f"{request_id}:consent:{newsletter_notice_version}",
                request_id=request_id,
                kind=BriefRequestEventKind.CONSENT_GRANTED,
                occurred_at=now,
                actor="public-request",
                payload=_payload(newsletter_notice_version=newsletter_notice_version),
            )
        return _snapshot(self._store, request_id)

    def withdraw_consent(
        self,
        *,
        request_id: str,
        now: datetime,
    ) -> BriefRequestSnapshot:
        current = _snapshot(self._store, request_id)
        if current.consent_state is NewsletterConsentState.SUPPRESSED:
            return current
        _append(
            self._store,
            event_id=f"{request_id}:consent-withdrawn:{int(now.timestamp())}",
            request_id=request_id,
            kind=BriefRequestEventKind.CONSENT_WITHDRAWN,
            occurred_at=now,
            actor="public-request",
        )
        return _snapshot(self._store, request_id)
