"""Minimum truthful AXIGLAND subscriber projection.

The projection accepts only already-authorized application results. It carries
direct canonical fields and explicit Xeed membership; it does not resolve FAXT
subjects, relationships, evidence, provenance, or historical graph state.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal

from application.xeed_access.organization_reader import AuthorizedXeedOrganization
from application.xeed_knowledge.reader import AuthorizedXeedFaxt
from domain.identity import FaxtId, OrganizationId, XeedId


class ProjectionStatus(StrEnum):
    """Evidence class carried by a field in the projection."""

    CANONICAL_DIRECT = "CANONICAL_DIRECT"
    CANONICAL_DERIVED_DETERMINISTIC = "CANONICAL_DERIVED_DETERMINISTIC"
    PRESENTATION_STATE = "PRESENTATION_STATE"
    UNKNOWN_UNSUPPORTED = "UNKNOWN_UNSUPPORTED"


class ProjectionError(ValueError):
    """An authorized projection input is missing, inconsistent, or unsupported."""


@dataclass(frozen=True)
class ProjectionNode:
    """A canonical node with only the direct fields approved for this slice."""

    identity: OrganizationId | FaxtId
    node_kind: Literal["ORGANIZATION", "FAXT"]
    label: str
    status: ProjectionStatus
    subject_id: str | None = None
    predicate: str | None = None
    object_or_value: str | None = None
    epistemic_state: str | None = None
    currentness: str | None = None
    observed_at: str | None = None
    capabilities: tuple[str, ...] = ()
    markets: tuple[str, ...] = ()
    membership_status: ProjectionStatus = ProjectionStatus.UNKNOWN_UNSUPPORTED
    subject_kind: ProjectionStatus = ProjectionStatus.UNKNOWN_UNSUPPORTED
    subject_resolution: ProjectionStatus = ProjectionStatus.UNKNOWN_UNSUPPORTED
    semantic_relationships: ProjectionStatus = ProjectionStatus.UNKNOWN_UNSUPPORTED
    cardinal_assignment: ProjectionStatus = ProjectionStatus.UNKNOWN_UNSUPPORTED
    evidence_access: ProjectionStatus = ProjectionStatus.UNKNOWN_UNSUPPORTED
    provenance: ProjectionStatus = ProjectionStatus.UNKNOWN_UNSUPPORTED

    @property
    def presentation_key(self) -> str:
        """Disambiguate UI selection while preserving the canonical ID itself."""

        return f"{self.node_kind}:{self.identity}"


@dataclass(frozen=True)
class SubscriberAxiglandProjection:
    """Immutable root and FAXT nodes from one authorized private context."""

    xeed_id: XeedId
    xeed_label: str | None
    organization: ProjectionNode
    faxt_nodes: tuple[ProjectionNode, ...]
    reality_level: str = "TEST_DEV_IN_MEMORY_AUTHORITY"
    semantic_edges: ProjectionStatus = ProjectionStatus.UNKNOWN_UNSUPPORTED
    historical_state: ProjectionStatus = ProjectionStatus.UNKNOWN_UNSUPPORTED


def project_axigland(
    organization_context: AuthorizedXeedOrganization,
    faxt_contexts: tuple[AuthorizedXeedFaxt, ...],
) -> SubscriberAxiglandProjection:
    """Project only objects read through the same AuthorizedXeed instance."""

    if not isinstance(organization_context, AuthorizedXeedOrganization):
        raise ProjectionError("an AuthorizedXeed Organization context is required")
    if not isinstance(faxt_contexts, tuple):
        raise ProjectionError("authorized FAXT contexts must be an immutable tuple")

    authorized_xeed = organization_context.authorized_xeed
    organization = organization_context.organization
    xeed = authorized_xeed.xeed
    if organization.id != xeed.organization_id:
        raise ProjectionError("Organization identity does not match the authorized Xeed")

    organization_node = ProjectionNode(
        identity=organization.id,
        node_kind="ORGANIZATION",
        label=organization.canonical_name,
        status=ProjectionStatus.CANONICAL_DIRECT,
        capabilities=organization.capabilities,
        markets=organization.markets,
        semantic_relationships=ProjectionStatus.UNKNOWN_UNSUPPORTED,
    )

    faxt_nodes: list[ProjectionNode] = []
    seen_ids: set[str] = set()
    for context in faxt_contexts:
        if not isinstance(context, AuthorizedXeedFaxt):
            raise ProjectionError("every FAXT must arrive through an authorized context")
        if context.authorized_xeed is not authorized_xeed:
            raise ProjectionError("all projection inputs must share one AuthorizedXeed")

        faxt = context.faxt
        if context.reference.faxt_id != faxt.id:
            raise ProjectionError("FAXT identity does not match its Xeed reference")
        if context.reference.xeed_id != xeed.id:
            raise ProjectionError("FAXT reference does not belong to the authorized Xeed")
        if faxt.id in seen_ids:
            raise ProjectionError("duplicate FAXT identity in authorized projection")
        seen_ids.add(faxt.id)

        faxt_nodes.append(
            ProjectionNode(
                identity=faxt.id,
                node_kind="FAXT",
                label=f"{faxt.predicate} · {faxt.object_or_value}",
                status=ProjectionStatus.CANONICAL_DERIVED_DETERMINISTIC,
                subject_id=faxt.subject_id,
                predicate=faxt.predicate,
                object_or_value=faxt.object_or_value,
                epistemic_state=faxt.epistemic_state.value,
                currentness=faxt.currentness.value,
                observed_at=faxt.observed_at.isoformat(),
                membership_status=ProjectionStatus.CANONICAL_DIRECT,
            )
        )

    return SubscriberAxiglandProjection(
        xeed_id=xeed.id,
        xeed_label=xeed.label,
        organization=organization_node,
        faxt_nodes=tuple(faxt_nodes),
    )
