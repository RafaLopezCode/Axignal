"""AO-24 governed KPI and measurement registry application boundary."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from domain.admin_access import AdminAssurance, AdminAuthorizationGrant, AdminScope
from domain.admin_governance import (
    AdminGovernanceAuditRecord,
    AdminGovernanceCommandOutcome,
    AdminGovernanceCommandTarget,
)
from domain.admin_measurements import (
    MeasurementComparison,
    MeasurementComparisonState,
    MeasurementDefinition,
    MeasurementFreshness,
    MeasurementInstrumentAuthority,
    MeasurementObservation,
    MeasurementReadout,
    MeasurementRegistryProjection,
    MeasurementState,
    MeasurementUnit,
)


class MeasurementRegistryStore(Protocol):
    def append_definition(self, definition: MeasurementDefinition) -> bool: ...
    def definitions(self) -> tuple[MeasurementDefinition, ...]: ...
    def append_observation(self, observation: MeasurementObservation) -> bool: ...
    def observations(self) -> tuple[MeasurementObservation, ...]: ...


class AuditStore(Protocol):
    def append(self, record: AdminGovernanceAuditRecord) -> bool: ...


def _require_read(grant: AdminAuthorizationGrant) -> None:
    if AdminScope.ADVISORY_READ not in grant.scopes:
        raise PermissionError("measurement registry requires admin:advisory:read")


def _require_write(grant: AdminAuthorizationGrant) -> None:
    if AdminScope.ADVISORY_WRITE not in grant.scopes:
        raise PermissionError("measurement registry mutation requires admin:advisory:write")
    if grant.assurance is not AdminAssurance.STEP_UP:
        raise PermissionError("measurement registry mutation requires STEP_UP assurance")


def _definition(
    store: MeasurementRegistryStore,
    measure_id: str,
    version: int,
) -> MeasurementDefinition:
    definition = next(
        (
            item
            for item in store.definitions()
            if item.measure_id == measure_id and item.version == version
        ),
        None,
    )
    if definition is None:
        raise ValueError("measurement observation references unregistered definition")
    return definition


def _validate_observation_against_definition(
    definition: MeasurementDefinition,
    observation: MeasurementObservation,
) -> None:
    if observation.instrument_id != definition.instrument_id:
        raise ValueError("observation instrument does not match measurement definition")
    if observation.instrument_version != definition.instrument_version:
        raise ValueError("observation instrument version does not match measurement definition")
    if observation.compatibility_key != definition.compatibility_key:
        raise ValueError("observation compatibility key does not match measurement definition")
    if observation.state is MeasurementState.MEASURED:
        if observation.sample_size is None or observation.informative_sample_size is None:
            raise ValueError("measured observation requires sample sizes")
        if observation.informative_sample_size < definition.minimum_sample_size:
            raise ValueError(
                "sample below definition minimum must be recorded as INSUFFICIENT, not MEASURED"
            )
        if definition.unit is MeasurementUnit.CURRENCY and observation.currency is None:
            raise ValueError("currency measurement requires currency")
        if definition.unit is not MeasurementUnit.CURRENCY and observation.currency is not None:
            raise ValueError("non-currency measurement cannot carry currency")


class MeasurementRegistryService:
    def __init__(self, store: MeasurementRegistryStore, audit_store: AuditStore) -> None:
        self._store = store
        self._audit = audit_store

    def register_definition(
        self,
        *,
        grant: AdminAuthorizationGrant,
        operation_id: str,
        reason: str,
        definition: MeasurementDefinition,
        now: datetime,
    ) -> bool:
        _require_write(grant)
        inserted = self._store.append_definition(definition)
        self._audit.append(
            AdminGovernanceAuditRecord(
                audit_id=f"measurement-audit:{operation_id}",
                command_id=operation_id,
                occurred_at=now,
                actor_principal_id=str(grant.principal_id),
                actor_session_id=str(grant.session_id),
                target=AdminGovernanceCommandTarget.ADVISORY,
                action="measurement.definition.registered",
                reason=reason,
                required_scope=AdminScope.ADVISORY_WRITE.value,
                outcome=AdminGovernanceCommandOutcome.COMPLETED,
                result_code="MEASUREMENT_DEFINITION_RECORDED",
                after_ref=f"{definition.measure_id}:v{definition.version}",
            )
        )
        return inserted

    def record_observation(
        self,
        *,
        grant: AdminAuthorizationGrant,
        operation_id: str,
        reason: str,
        observation: MeasurementObservation,
        now: datetime,
    ) -> bool:
        _require_write(grant)
        definition = _definition(
            self._store,
            observation.measure_id,
            observation.definition_version,
        )
        _validate_observation_against_definition(definition, observation)
        inserted = self._store.append_observation(observation)
        self._audit.append(
            AdminGovernanceAuditRecord(
                audit_id=f"measurement-audit:{operation_id}",
                command_id=operation_id,
                occurred_at=now,
                actor_principal_id=str(grant.principal_id),
                actor_session_id=str(grant.session_id),
                target=AdminGovernanceCommandTarget.ADVISORY,
                action="measurement.observation.recorded",
                reason=reason,
                required_scope=AdminScope.ADVISORY_WRITE.value,
                outcome=AdminGovernanceCommandOutcome.COMPLETED,
                result_code=f"MEASUREMENT_{observation.state.value}",
                after_ref=observation.observation_id,
            )
        )
        return inserted

    def register_instrument_definition(
        self,
        *,
        authority: MeasurementInstrumentAuthority,
        operation_id: str,
        reason: str,
        definition: MeasurementDefinition,
        now: datetime,
    ) -> bool:
        if definition.source_family != authority.source_family:
            raise PermissionError("instrument authority source family mismatch")
        if definition.instrument_id != authority.instrument_id:
            raise PermissionError("instrument authority instrument mismatch")
        existing = next(
            (
                item
                for item in self._store.definitions()
                if item.measure_id == definition.measure_id and item.version == definition.version
            ),
            None,
        )
        if existing is not None:
            if existing != definition:
                raise ValueError(
                    "instrument definition version already exists with different content"
                )
            return False
        inserted = self._store.append_definition(definition)
        self._audit.append(
            AdminGovernanceAuditRecord(
                audit_id=f"measurement-audit:{operation_id}",
                command_id=operation_id,
                occurred_at=now,
                actor_principal_id=f"integration:{authority.integration_id}",
                actor_session_id=f"service:{authority.integration_id}",
                target=AdminGovernanceCommandTarget.INTEGRATION,
                action="measurement.definition.instrument_registered",
                reason=reason,
                required_scope=f"instrument:{authority.instrument_id}",
                outcome=AdminGovernanceCommandOutcome.COMPLETED,
                result_code="MEASUREMENT_DEFINITION_RECORDED",
                after_ref=f"{definition.measure_id}:v{definition.version}",
            )
        )
        return inserted

    def record_instrument_observation(
        self,
        *,
        authority: MeasurementInstrumentAuthority,
        operation_id: str,
        reason: str,
        observation: MeasurementObservation,
        now: datetime,
    ) -> bool:
        definition = _definition(
            self._store,
            observation.measure_id,
            observation.definition_version,
        )
        if definition.source_family != authority.source_family:
            raise PermissionError("instrument authority source family mismatch")
        if observation.instrument_id != authority.instrument_id:
            raise PermissionError("instrument authority instrument mismatch")
        _validate_observation_against_definition(definition, observation)
        inserted = self._store.append_observation(observation)
        self._audit.append(
            AdminGovernanceAuditRecord(
                audit_id=f"measurement-audit:{operation_id}",
                command_id=operation_id,
                occurred_at=now,
                actor_principal_id=f"integration:{authority.integration_id}",
                actor_session_id=f"service:{authority.integration_id}",
                target=AdminGovernanceCommandTarget.INTEGRATION,
                action="measurement.observation.instrument_recorded",
                reason=reason,
                required_scope=f"instrument:{authority.instrument_id}",
                outcome=AdminGovernanceCommandOutcome.COMPLETED,
                result_code=f"MEASUREMENT_{observation.state.value}",
                after_ref=observation.observation_id,
            )
        )
        return inserted


def compare_measurements(
    *,
    store: MeasurementRegistryStore,
    earlier: MeasurementObservation,
    later: MeasurementObservation,
) -> MeasurementComparison:
    earlier_definition = _definition(store, earlier.measure_id, earlier.definition_version)
    later_definition = _definition(store, later.measure_id, later.definition_version)

    if earlier.measure_id != later.measure_id:
        return MeasurementComparison(
            earlier_observation_id=earlier.observation_id,
            later_observation_id=later.observation_id,
            state=MeasurementComparisonState.INCOMPATIBLE,
            reason="different measure identities",
        )
    if earlier_definition.compatibility_key != later_definition.compatibility_key:
        return MeasurementComparison(
            earlier_observation_id=earlier.observation_id,
            later_observation_id=later.observation_id,
            state=MeasurementComparisonState.INCOMPATIBLE,
            reason="definition compatibility keys differ",
        )
    if (
        earlier.instrument_id != later.instrument_id
        or earlier.instrument_version != later.instrument_version
    ):
        return MeasurementComparison(
            earlier_observation_id=earlier.observation_id,
            later_observation_id=later.observation_id,
            state=MeasurementComparisonState.INCOMPATIBLE,
            reason="instrument identity/version differs; no validated bridge exists",
        )
    if (
        earlier.state is not MeasurementState.MEASURED
        or later.state is not MeasurementState.MEASURED
    ):
        return MeasurementComparison(
            earlier_observation_id=earlier.observation_id,
            later_observation_id=later.observation_id,
            state=MeasurementComparisonState.INSUFFICIENT,
            reason="both observations must be MEASURED",
        )
    if earlier.subject_ref != later.subject_ref:
        return MeasurementComparison(
            earlier_observation_id=earlier.observation_id,
            later_observation_id=later.observation_id,
            state=MeasurementComparisonState.INCOMPATIBLE,
            reason="measurement subjects differ",
        )
    return MeasurementComparison(
        earlier_observation_id=earlier.observation_id,
        later_observation_id=later.observation_id,
        state=MeasurementComparisonState.COMPARABLE,
        reason="measure, compatibility key, instrument version and subject match",
    )


def project_measurement_registry(
    *,
    store: MeasurementRegistryStore,
    grant: AdminAuthorizationGrant,
    generated_at: datetime,
) -> MeasurementRegistryProjection:
    _require_read(grant)
    definitions = store.definitions()
    by_key = {(item.measure_id, item.version): item for item in definitions}
    readouts: list[MeasurementReadout] = []
    for observation in store.observations():
        definition = by_key.get((observation.measure_id, observation.definition_version))
        if definition is None:
            continue
        if observation.state is MeasurementState.NOT_MEASURED:
            readouts.append(
                MeasurementReadout(
                    observation=observation,
                    freshness=MeasurementFreshness.NOT_MEASURED,
                    usable=False,
                    reason="instrument produced no measurement; absence is not zero",
                )
            )
            continue
        if observation.state is MeasurementState.INSUFFICIENT:
            readouts.append(
                MeasurementReadout(
                    observation=observation,
                    freshness=MeasurementFreshness.NOT_MEASURED,
                    usable=False,
                    reason="sample/evidence is insufficient under the registered definition",
                )
            )
            continue
        age_seconds = (generated_at - observation.observed_at).total_seconds()
        stale = age_seconds >= definition.freshness_seconds
        readouts.append(
            MeasurementReadout(
                observation=observation,
                freshness=MeasurementFreshness.STALE if stale else MeasurementFreshness.FRESH,
                usable=not stale,
                reason=(
                    "measurement exceeds registered freshness window"
                    if stale
                    else "measurement satisfies registered definition and freshness window"
                ),
            )
        )
    return MeasurementRegistryProjection(
        generated_at=generated_at,
        privacy_class="PRIVATE_GOVERNED_MEASUREMENT_REGISTRY",
        definitions=definitions,
        readouts=tuple(readouts),
        coverage_notes=(
            "Registered definitions, not models, govern KPI authority.",
            "Instrument/version drift breaks historical comparability unless a future validated bridge exists.",
            "NOT_MEASURED and INSUFFICIENT never become numeric zero.",
            "Sample size, uncertainty, scope and interpretation limits remain part of measurement meaning.",
            "Registry observations are private advisory/admin evidence and do not write AXIGLAND.",
        ),
    )
