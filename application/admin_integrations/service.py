"""AO-18 governed operations over AXIGNAL-owned integration metadata."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from domain.admin_access import (
    AdminAssurance,
    AdminAuthorizationGrant,
    AdminScope,
)
from domain.admin_governance import (
    AdminGovernanceAuditRecord,
    AdminGovernanceCommandOutcome,
    AdminGovernanceCommandTarget,
)
from domain.admin_integrations import (
    CredentialState,
    IntegrationDefinition,
    IntegrationEnvironment,
    IntegrationHealth,
    IntegrationHealthState,
)


class IntegrationRegistryStore(Protocol):
    def append_definition(
        self, *, operation_id: str, occurred_at: datetime, definition: IntegrationDefinition
    ) -> bool: ...

    def append_health(
        self, *, operation_id: str, occurred_at: datetime, observation: IntegrationHealth
    ) -> bool: ...

    def all_definitions(self) -> tuple[IntegrationDefinition, ...]: ...

    def latest_health(
        self, integration_id: str, *, as_of: datetime
    ) -> IntegrationHealth | None: ...


class CredentialResolver(Protocol):
    """Resolve availability only; secret bytes never enter this registry service."""

    def is_resolvable(self, *, reference: str, environment: IntegrationEnvironment) -> bool: ...


class IntegrationAuditStore(Protocol):
    def append(self, record: AdminGovernanceAuditRecord) -> bool: ...


@dataclass(frozen=True, slots=True)
class AdminIntegrationView:
    definition: IntegrationDefinition
    health: IntegrationHealth | None
    health_state: IntegrationHealthState


@dataclass(frozen=True, slots=True)
class AdminIntegrationProjection:
    as_of: datetime
    privacy_class: str
    integrations: tuple[AdminIntegrationView, ...]
    coverage_notes: tuple[str, ...]


class IntegrationConnectionDenied(PermissionError):
    """An integration is not in a state where provider work is permitted."""


_SECRET_LIKE = re.compile(
    r"(?i)(sk_(?:live|test)_[A-Za-z0-9]+|bearer\s+\S+|"
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----|(?:api[_ -]?key|password|token)\s*[:=]\s*\S+)"
)


def _require_safe_audit_input(value: str, name: str) -> None:
    if not value.strip() or len(value) > 300 or _SECRET_LIKE.search(value):
        raise ValueError(f"{name} is missing, too long, or contains credential-like material")


class AdminIntegrationService:
    def __init__(
        self,
        registry_store: IntegrationRegistryStore,
        audit_store: IntegrationAuditStore,
    ) -> None:
        self._registry_store = registry_store
        self._audit_store = audit_store

    @staticmethod
    def _authorize_manage(grant: AdminAuthorizationGrant) -> None:
        if AdminScope.INTEGRATIONS_MANAGE not in grant.scopes:
            raise PermissionError("integration change requires admin:integrations:manage")
        if grant.assurance is not AdminAssurance.STEP_UP:
            raise PermissionError("integration change requires step-up assurance")

    def _audit(
        self,
        *,
        grant: AdminAuthorizationGrant,
        operation_id: str,
        occurred_at: datetime,
        action: str,
        reason: str,
        result_code: str,
        before_ref: str | None = None,
        after_ref: str | None = None,
    ) -> None:
        record = AdminGovernanceAuditRecord(
            audit_id=f"integration-audit:{operation_id}",
            command_id=operation_id,
            occurred_at=occurred_at,
            actor_principal_id=str(grant.principal_id),
            actor_session_id=str(grant.session_id),
            target=AdminGovernanceCommandTarget.INTEGRATION,
            action=action,
            reason=reason,
            required_scope=AdminScope.INTEGRATIONS_MANAGE.value,
            outcome=AdminGovernanceCommandOutcome.COMPLETED,
            result_code=result_code,
            before_ref=before_ref,
            after_ref=after_ref,
        )
        self._audit_store.append(record)

    def register(
        self,
        *,
        grant: AdminAuthorizationGrant,
        operation_id: str,
        reason: str,
        occurred_at: datetime,
        definition: IntegrationDefinition,
    ) -> bool:
        self._authorize_manage(grant)
        _require_safe_audit_input(operation_id, "integration operation id")
        _require_safe_audit_input(reason, "integration operation reason")
        if occurred_at.tzinfo is None or occurred_at.utcoffset() is None:
            raise ValueError("integration operation time must be timezone-aware")
        inserted = self._registry_store.append_definition(
            operation_id=operation_id,
            occurred_at=occurred_at,
            definition=definition,
        )
        # Retry the audit append even when the registry append was already
        # committed. The registry and governance audit use separate stores, so
        # a transient audit failure must be repairable by replaying this same
        # idempotent operation.
        self._audit(
            grant=grant,
            operation_id=operation_id,
            occurred_at=occurred_at,
            action="integration.definition.registered",
            reason=reason,
            result_code="INTEGRATION_DEFINITION_RECORDED",
            before_ref=(
                None
                if definition.version == 1
                else f"{definition.integration_id}:v{definition.version - 1}"
            ),
            after_ref=f"{definition.integration_id}:v{definition.version}",
        )
        return inserted

    def record_health(
        self,
        *,
        grant: AdminAuthorizationGrant,
        operation_id: str,
        reason: str,
        occurred_at: datetime,
        observation: IntegrationHealth,
    ) -> bool:
        self._authorize_manage(grant)
        _require_safe_audit_input(operation_id, "integration operation id")
        _require_safe_audit_input(reason, "integration operation reason")
        if occurred_at.tzinfo is None or occurred_at.utcoffset() is None:
            raise ValueError("integration operation time must be timezone-aware")
        if observation.observed_at > occurred_at:
            raise ValueError("health observation cannot be later than its recorded time")
        if not any(
            item.integration_id == observation.integration_id
            for item in self._registry_store.all_definitions()
        ):
            raise ValueError("cannot record health for an unregistered integration")
        inserted = self._registry_store.append_health(
            operation_id=operation_id,
            occurred_at=occurred_at,
            observation=observation,
        )
        # See register(): retrying the same health operation must also repair
        # an audit append that failed after the health record committed.
        self._audit(
            grant=grant,
            operation_id=operation_id,
            occurred_at=occurred_at,
            action="integration.health.observed",
            reason=reason,
            result_code="INTEGRATION_HEALTH_OBSERVED",
            after_ref=f"{observation.integration_id}:{observation.observed_at.isoformat()}",
        )
        return inserted

    def require_connection(
        self,
        *,
        integration_id: str,
        environment: IntegrationEnvironment,
        now: datetime,
        required_scopes: frozenset[str],
        credential_resolver: CredentialResolver,
    ) -> IntegrationDefinition:
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("connection authorization time must be timezone-aware")
        definition = next(
            (
                item
                for item in self._registry_store.all_definitions()
                if item.integration_id == integration_id
            ),
            None,
        )
        if definition is None:
            raise IntegrationConnectionDenied("integration is not registered")
        if not definition.enabled:
            raise IntegrationConnectionDenied("integration is disabled")
        if definition.environment is not environment:
            raise IntegrationConnectionDenied("integration environment does not match runtime")
        if definition.credential.state in {
            CredentialState.UNKNOWN,
            CredentialState.MISSING,
            CredentialState.EXPIRED,
            CredentialState.REVOKED,
        }:
            raise IntegrationConnectionDenied("integration credential is unavailable")
        if definition.credential.expires_at is not None and definition.credential.expires_at <= now:
            raise IntegrationConnectionDenied("integration credential has expired")
        if definition.credential.reference is None or not credential_resolver.is_resolvable(
            reference=definition.credential.reference,
            environment=environment,
        ):
            raise IntegrationConnectionDenied("integration credential reference cannot be resolved")
        if not required_scopes.issubset(set(definition.scopes)):
            raise IntegrationConnectionDenied("integration scope is not granted")
        health = self._registry_store.latest_health(integration_id, as_of=now)
        if health is None or health.state is not IntegrationHealthState.HEALTHY:
            raise IntegrationConnectionDenied("integration health is not verified healthy")
        if (now - health.observed_at).total_seconds() >= definition.health_freshness_seconds:
            raise IntegrationConnectionDenied("integration health observation is stale")
        return definition


def project_admin_integrations(
    *,
    store: IntegrationRegistryStore,
    grant: AdminAuthorizationGrant,
    as_of: datetime,
) -> AdminIntegrationProjection:
    if AdminScope.INTEGRATIONS_READ not in grant.scopes:
        raise PermissionError("integration projection requires admin:integrations:read")
    if as_of.tzinfo is None or as_of.utcoffset() is None:
        raise ValueError("integration projection as_of must be timezone-aware")
    views = tuple(
        _integration_view(
            definition, store.latest_health(definition.integration_id, as_of=as_of), as_of
        )
        for definition in store.all_definitions()
    )
    return AdminIntegrationProjection(
        as_of=as_of,
        privacy_class="PRIVATE_AXIGNAL_OPERATIONS",
        integrations=views,
        coverage_notes=(
            "Registry definitions, credential lifecycle metadata and provider health are separate records.",
            "Credential material is never part of this projection; references are opaque locators only.",
            "Unknown health or credential state is not healthy or configured.",
            "Health freshness is evaluated at as_of; stale observations remain historical and cannot authorize provider work.",
            "Provider state is operational metadata and never AXIGLAND evidence or business truth.",
        ),
    )


def _integration_view(
    definition: IntegrationDefinition,
    health: IntegrationHealth | None,
    as_of: datetime,
) -> AdminIntegrationView:
    if health is None:
        state = IntegrationHealthState.UNKNOWN
    elif (as_of - health.observed_at).total_seconds() >= definition.health_freshness_seconds:
        state = IntegrationHealthState.STALE
    else:
        state = health.state
    return AdminIntegrationView(definition=definition, health=health, health_state=state)
