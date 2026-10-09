"""Bind current economic evidence delivery to the existing live website grants."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

from application.economic_discovery.observation_memory import (
    ObservationAccessMetadata,
)
from application.first_observation.rights import ContentRightsPolicy
from application.subscriber_projection.evidence_delivery import (
    ContentAccess,
    RecordedContentRights,
    recorded_content_access,
)


@dataclass(frozen=True, slots=True)
class LiveEvidenceContentRights:
    rights: ContentRightsPolicy
    clock: Callable[[], datetime]

    def decision(self, metadata: ObservationAccessMetadata) -> ContentAccess:
        record, authority = metadata.record, metadata.reuse_authority
        managed = record.observation_id.startswith("fo:") or (
            record.source_type == "PUBLIC_WEBSITE"
            and (authority.provenance_ref or "").startswith("source-registry:website:")
        )
        if not managed:
            return RecordedContentRights().decision(metadata)
        recorded = recorded_content_access(metadata)
        if recorded is not ContentAccess.PERMITTED:
            return recorded
        now = self.clock()
        grant = self.rights.rights_for(record.source_ref, now=now)
        if grant.entry is None:
            return ContentAccess.UNKNOWN
        if not grant.reuse_permitted or grant.raw_retention_days <= 0:
            return ContentAccess.WITHHELD
        # A changed grant cannot widen the historical permission. Reobserve under
        # the new grant; this also handles legacy snapshots without an expiry field.
        if authority.provenance_ref != grant.basis_ref:
            return ContentAccess.WITHHELD
        if authority.content_retention_days is None:
            return ContentAccess.UNKNOWN  # Legacy metadata cannot establish its original limit.
        days = min(grant.raw_retention_days, authority.content_retention_days)
        if now < record.observed_at or now >= record.observed_at + timedelta(days=days):
            return ContentAccess.WITHHELD
        return ContentAccess.PERMITTED
