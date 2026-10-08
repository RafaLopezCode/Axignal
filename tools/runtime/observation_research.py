"""Existing subscriber entitlement and EB-07 authority for private research attention."""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from application.axent.grounded.answer import ResearchRequest
from application.economic_discovery.continuous_observation import SharedObservationWorkMemory
from application.observation_runtime.families import FAMILY_POLICY_VERSION
from application.subscriber_access.pilot import PilotAccessService
from application.subscriber_identity.runtime import Clock
from application.subscriber_portfolio.models import FocusStatus, PortfolioError
from application.xeed_access.reader import TrustedRequestContext
from domain.evidence.epistemics import Currentness
from domain.identity import XeedId
from pipeline.admin_billing.subscriber_store import SqliteSubscriberBillingStore
from pipeline.subscriber_access.sqlite_store import SqlitePilotAccessStore
from pipeline.subscriber_portfolio.sqlite_store import SqliteSubscriberPortfolioStore
from tools.runtime.subscriber_composition import _ProjectionEntitlements
from tools.runtime.subscriber_configuration import load_subscriber_settings
from tools.runtime.subscriber_provisioning import _ACCOUNT_REF, _ENVIRONMENT_REF


def configured_research_access(
    root: Path, clock: Clock
) -> Callable[[TrustedRequestContext, XeedId, datetime], bool]:
    """No payment/provider secret is needed to recheck an already verified entitlement."""
    filename = os.getenv("AXIGNAL_SUBSCRIBER_CONFIGURATION_FILE", "").strip()
    settings = load_subscriber_settings(
        os.environ, configuration_file=Path(filename) if filename else None
    )
    values = settings.values
    environment = (
        _ENVIRONMENT_REF
        if values.get("AXIGNAL_STRIPE_LIVE_ENABLED") == "true"
        and values.get("AXIGNAL_STRIPE_ACCOUNT_ID") == _ACCOUNT_REF
        else None
    )
    entitlements = _ProjectionEntitlements(
        SqliteSubscriberBillingStore(root / "subscriber-billing.sqlite3"),
        clock,
        environment,
        PilotAccessService(SqlitePilotAccessStore(root / "subscriber-pilot.sqlite3"))
        if settings.pilot_enabled
        else None,
    )
    portfolio = SqliteSubscriberPortfolioStore(root / "subscriber-runtime.sqlite3")

    def authorized(context: TrustedRequestContext, focus: XeedId, now: datetime) -> bool:
        if not settings.enabled:
            return False
        snapshot = entitlements.snapshot(context.tenant_id)
        if snapshot.currentness is not Currentness.CURRENT or not snapshot.capacity:
            return False
        try:
            active = sorted(
                (e for e in portfolio.list_authorized(context) if e.status is FocusStatus.ACTIVE),
                key=lambda e: (e.created_at, e.focus_id),
            )[: snapshot.capacity]
        except PortfolioError:
            return False
        return any(e.focus_id == focus for e in active)

    return authorized


def shared_scope(item: ResearchRequest) -> str:
    """Public server-owned compatibility contract; never carries tenant or prompt text."""
    return hashlib.sha256(
        json.dumps(
            [
                item.organization_id,
                str(item.family),
                sorted(item.geographies),
                FAMILY_POLICY_VERSION,
            ]
        ).encode()
    ).hexdigest()


def compatible_shared_key(shared: SharedObservationWorkMemory, item: ResearchRequest) -> str | None:
    authority = shared.prime_authority(item.organization_id)
    if authority is None:
        return None
    for key in sorted(authority.authorized_work_keys):
        work = shared.get(key)
        if (
            work is not None
            and work.intent.dimension_id == str(item.family)
            and work.intent.research_context_fingerprint == shared_scope(item)
        ):
            return key
    return None
