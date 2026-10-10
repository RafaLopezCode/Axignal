"""AXIGNAL HTTP runtime composition root.

Canonical economic writes remain behind governed application services. Public
Contact/privacy intake writes only to private service operations, never AXIGLAND.
"""

from __future__ import annotations

import contextlib
import html
import json
import mimetypes
import os
import secrets
import sqlite3
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

from application.admin_access import (
    AdminAccessService,
    AdminAuthenticationError,
    AdminAuthorizationError,
)
from application.admin_accounting import (
    AccountingReconciliationProjection,
    project_accounting_reconciliation,
)
from application.admin_acquisition.lifecycle_service import AdminBriefLifecycleService
from application.admin_acquisition.marketing_service import PublicMarketingEventService
from application.admin_acquisition.projection import (
    AdminAcquisitionProjection,
    project_admin_acquisition,
)
from application.admin_acquisition.public_service import PublicBriefRequestService
from application.admin_acquisition.review_service import AdminBriefReviewService
from application.admin_api_operations import ApiOperationsProjection, project_api_operations
from application.admin_brain_observatory import project_brain_provider_observatory
from application.admin_command_center import COMMAND_CENTER_METRICS, project_command_center
from application.admin_commercial import AdminCommercialProjection, project_admin_commercial
from application.admin_customer_accounts import (
    CustomerOperationsProjection,
    project_customer_operations,
)
from application.admin_financial_documents import (
    FinancialDocumentProjection,
    project_financial_documents,
)
from application.admin_fiscal_compliance import (
    FiscalComplianceProjection,
    canonical_es_sif_ruleset,
    project_fiscal_compliance,
)
from application.admin_governance import project_admin_governance
from application.admin_gsc import project_private_gsc
from application.admin_integrations.service import (
    AdminIntegrationProjection,
    project_admin_integrations,
)
from application.admin_measurements import project_measurement_registry
from application.admin_pilot_accounts import PilotAccountsConflict
from application.admin_shell import (
    AdminShellProjection,
    AdminShellRouteDenied,
    AdminShellRouteUnknown,
    project_admin_shell,
)
from application.admin_tax_operations import canonical_es_tax_rules, project_tax_operations
from application.admin_weekly_brief import (
    WEEKLY_BRIEF_PILOT_CURRENTNESS_POLICY,
    MaterialObservationCandidate,
    append_correction,
    approve_issue,
    compose_issue,
)
from application.admin_xeed_observatory import project_xeed_axigland_observatory
from application.economic_discovery.observation_reuse import ObservationReusePolicy
from application.economic_discovery.temporal_currentness import TemporalCurrentnessPolicy
from application.subscriber_access.staff_capacity import StaffCapacityError, StaffCapacityFailure
from application.subscriber_portfolio.models import PortfolioError
from domain.admin_access import AdminAssurance, AdminAuthorizationGrant, AdminRiskClass, AdminScope
from domain.admin_acquisition import MarketingEventKind
from domain.admin_api_operations import ApiOperationObservation
from domain.admin_brain_observatory import BrainProviderObservatory
from domain.admin_command_center import AdminCommandCenterProjection
from domain.admin_governance import AdminGovernanceProjection
from domain.admin_gsc import GscPrivateAnalyticsProjection
from domain.admin_integrations import IntegrationEnvironment
from domain.admin_measurements import MeasurementRegistryProjection
from domain.admin_observability import AdminProjectionId, AdminProjectionSnapshot
from domain.admin_tax_operations import TaxOperationsProjection
from domain.admin_xeed_observatory import XeedAxiglandObservatory
from pipeline.admin_accounting import SqliteAccountingReconciliationStore
from pipeline.admin_acquisition import SqliteAdminAcquisitionStore
from pipeline.admin_api_operations import SqliteApiOperationsStore
from pipeline.admin_billing import SqliteAdminBillingStore
from pipeline.admin_billing.stripe import StripeWebhookDependencyError, StripeWebhookError
from pipeline.admin_commercial import SqliteAdminCommercialStore
from pipeline.admin_customer_accounts import SqliteAdminCustomerAccountStore
from pipeline.admin_financial_documents import SqliteFinancialDocumentStore
from pipeline.admin_fiscal_compliance import SqliteFiscalComplianceStore
from pipeline.admin_governance import SqliteAdminGovernanceAuditStore
from pipeline.admin_gsc import SqliteAdminGscStore
from pipeline.admin_integrations import SqliteAdminIntegrationStore
from pipeline.admin_measurements import SqliteMeasurementRegistryStore
from pipeline.admin_observability import SqliteAdminObservabilityStore
from pipeline.admin_tax_operations import SqliteTaxOperationsStore
from pipeline.admin_weekly_brief import SqliteWeeklyBriefStore
from pipeline.continuous_observation import SqliteSharedObservationWorkMemory
from pipeline.learning_memory import SqliteLearningMemory
from pipeline.observation_memory import SqliteObservationMemory
from pipeline.policy_governance import SqliteActivePolicyStore
from tools.runtime.admin_access import (
    AdminHttpAccessGuard,
    build_validation_only_admin_access,
)
from tools.runtime.admin_pilot_accounts import pilot_accounts_request
from tools.runtime.admin_staff_capacity import ROUTE as STAFF_CAPACITY_ROUTE
from tools.runtime.admin_staff_capacity import staff_capacity_request
from tools.runtime.config import RuntimeConfig
from tools.runtime.first_proof import (
    FirstProofInsufficientEvidence,
    FirstProofService,
    FirstProofStore,
)
from tools.runtime.organization_attention import OrganizationAttention, load_observation_catalog
from tools.runtime.product_mcp import MAX_BODY as PRODUCT_MCP_MAX_BODY
from tools.runtime.product_mcp import ProductMcpHttp
from tools.runtime.public_requests import public_request_status, submit_public_request
from tools.runtime.stripe_billing import StripeWebhookRuntime
from tools.runtime.subscriber_axent import luna_reasoner_from_env
from tools.runtime.subscriber_composition import build_subscriber_facade
from tools.runtime.subscriber_http import SubscriberHttpFacade, is_subscriber_path
from tools.runtime.subscriber_provisioning import (
    SubscriberBillingConfigurationError,
    build_subscriber_billing_inputs,
)


@dataclass(slots=True)
class AxignalRuntime:
    config: RuntimeConfig
    observation_memory: SqliteObservationMemory
    research_work_memory: SqliteSharedObservationWorkMemory
    learning_memory: SqliteLearningMemory
    admin_observability: SqliteAdminObservabilityStore
    governance_policy_store: SqliteActivePolicyStore
    governance_audit_store: SqliteAdminGovernanceAuditStore
    admin_acquisition_store: SqliteAdminAcquisitionStore
    admin_gsc_store: SqliteAdminGscStore
    admin_accounting_store: SqliteAccountingReconciliationStore
    admin_api_operations_store: SqliteApiOperationsStore
    admin_commercial_store: SqliteAdminCommercialStore
    admin_customer_account_store: SqliteAdminCustomerAccountStore
    admin_billing_store: SqliteAdminBillingStore
    admin_financial_document_store: SqliteFinancialDocumentStore
    admin_fiscal_compliance_store: SqliteFiscalComplianceStore
    admin_tax_operations_store: SqliteTaxOperationsStore
    admin_integration_store: SqliteAdminIntegrationStore
    admin_measurement_store: SqliteMeasurementRegistryStore
    admin_weekly_brief_store: SqliteWeeklyBriefStore
    stripe_webhook: StripeWebhookRuntime | None = None
    first_proof: FirstProofService | None = None
    admin_access: AdminAccessService | None = None
    organization_attention: OrganizationAttention | None = None
    subscriber: SubscriberHttpFacade | None = None

    @property
    def observation_db(self) -> Path:
        return self.config.data_dir / "observation-memory.sqlite3"

    @property
    def research_work_db(self) -> Path:
        return self.config.data_dir / "research-work.sqlite3"

    @property
    def learning_db(self) -> Path:
        return self.config.data_dir / "learning-memory.sqlite3"

    def _sqlite_status(self, path: Path, table: str) -> dict[str, object]:
        try:
            with sqlite3.connect(path) as connection:
                integrity = str(connection.execute("PRAGMA quick_check").fetchone()[0])
                count = int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
            return {"status": "ok" if integrity == "ok" else "degraded", "rows": count}
        except (sqlite3.Error, OSError) as exc:
            return {"status": "error", "error": type(exc).__name__}

    def health_payload(self, *, detailed: bool = False) -> dict[str, object]:
        observation = self._sqlite_status(self.observation_db, "observations")
        research = self._sqlite_status(self.research_work_db, "shared_observation_work")
        learning = self._sqlite_status(self.learning_db, "learning_events")
        healthy = all(item.get("status") == "ok" for item in (observation, research, learning))
        if not detailed:
            observation = {"status": observation["status"]}
            research = {"status": research["status"]}
            learning = {"status": learning["status"]}
        return {
            "status": "ok" if healthy else "degraded",
            "service": "axignal-runtime",
            "environment": self.config.environment,
            "code_sha": self.config.code_sha,
            "persistence": {
                "observation_memory": observation,
                "research_work_memory": research,
                "learning_memory": learning,
            },
            "write_surface": (
                "weekly-brief+acquisition-gated"
                if self.config.weekly_brief_requests_enabled
                and self.config.acquisition_events_enabled
                else "weekly-brief-request-gated"
                if self.config.weekly_brief_requests_enabled
                else "acquisition-events-gated"
                if self.config.acquisition_events_enabled
                else "closed"
            ),
            "provider_ingress": (
                "stripe-webhook-gated" if self.stripe_webhook is not None else "closed"
            ),
        }


def build_runtime(config: RuntimeConfig) -> AxignalRuntime:
    observation_db = config.data_dir / "observation-memory.sqlite3"
    research_work_db = config.data_dir / "research-work.sqlite3"
    learning_db = config.data_dir / "learning-memory.sqlite3"
    observation_memory = SqliteObservationMemory(observation_db)
    research_work_memory = SqliteSharedObservationWorkMemory(research_work_db)
    learning_memory = SqliteLearningMemory(learning_db)
    admin_observability = SqliteAdminObservabilityStore(
        config.data_dir / "admin-observability.sqlite3"
    )
    governance_policy_store = SqliteActivePolicyStore(config.data_dir / "policy-governance.sqlite3")
    governance_audit_store = SqliteAdminGovernanceAuditStore(
        config.data_dir / "admin-governance-audit.sqlite3"
    )
    admin_acquisition_store = SqliteAdminAcquisitionStore(
        config.data_dir / "admin-acquisition.sqlite3"
    )
    admin_gsc_store = SqliteAdminGscStore(config.data_dir / "admin-gsc.sqlite3")
    admin_accounting_store = SqliteAccountingReconciliationStore(
        config.data_dir / "admin-accounting-reconciliation.sqlite3"
    )
    admin_api_operations_store = SqliteApiOperationsStore(
        config.data_dir / "admin-api-operations.sqlite3"
    )
    admin_commercial_store = SqliteAdminCommercialStore(
        config.data_dir / "admin-commercial.sqlite3"
    )
    admin_customer_account_store = SqliteAdminCustomerAccountStore(
        config.data_dir / "admin-customer-accounts.sqlite3"
    )
    admin_billing_store = SqliteAdminBillingStore(config.data_dir / "admin-billing.sqlite3")
    admin_financial_document_store = SqliteFinancialDocumentStore(
        config.data_dir / "admin-financial-documents.sqlite3"
    )
    admin_fiscal_compliance_store = SqliteFiscalComplianceStore(
        config.data_dir / "admin-fiscal-compliance.sqlite3"
    )
    admin_tax_operations_store = SqliteTaxOperationsStore(
        config.data_dir / "admin-tax-operations.sqlite3"
    )
    for tax_rule in canonical_es_tax_rules():
        admin_tax_operations_store.append_rule(tax_rule)
    admin_integration_store = SqliteAdminIntegrationStore(
        config.data_dir / "admin-integrations.sqlite3"
    )
    admin_measurement_store = SqliteMeasurementRegistryStore(
        config.data_dir / "admin-measurements.sqlite3"
    )
    admin_weekly_brief_store = SqliteWeeklyBriefStore(
        config.data_dir / "admin-weekly-brief.sqlite3"
    )
    stripe_webhook = None
    if config.stripe_webhook_signing_secret is not None:
        if (
            config.stripe_account_id is None
            or config.stripe_base_price_ref is None
            or config.stripe_additional_xeed_price_ref is None
        ):
            raise ValueError("incomplete Stripe webhook runtime configuration")
        stripe_webhook = StripeWebhookRuntime(
            stripe_account_id=config.stripe_account_id,
            base_price_ref=config.stripe_base_price_ref,
            additional_xeed_price_ref=config.stripe_additional_xeed_price_ref,
            signing_secret=config.stripe_webhook_signing_secret,
            billing_store=admin_billing_store,
            account_store=admin_customer_account_store,
            integration_store=admin_integration_store,
            runtime_environment=IntegrationEnvironment(config.environment.upper()),
            require_livemode=config.environment == "production",
            operations_store=admin_api_operations_store,
            financial_store=admin_financial_document_store,
        )
    first_proof = None
    if config.first_proof_allowed_host is not None:
        from pipeline.source_acquisition import ContentAddressedArtifactStore

        first_proof = FirstProofService(
            code_sha=config.code_sha,
            allowed_host=config.first_proof_allowed_host,
            store=FirstProofStore(config.data_dir / "first-proof.sqlite3"),
            observation_memory=observation_memory,
            research_work_memory=research_work_memory,
            learning_memory=learning_memory,
            artifacts=ContentAddressedArtifactStore(config.data_dir / "artifacts"),
        )
    admin_access = (
        build_validation_only_admin_access(config.data_dir) if config.admin_access_enabled else None
    )
    organization_attention = (
        None
        if first_proof is None
        else OrganizationAttention(
            first_proof,
            load_observation_catalog(config.organization_catalog_path, first_proof.allowed_host),
        )
    )
    subscriber = None
    if config.subscriber_settings is not None and config.subscriber_settings.enabled:
        try:
            stripe_settings, offer_catalogue_reader = build_subscriber_billing_inputs(
                config.subscriber_settings, config.data_dir
            )
        except SubscriberBillingConfigurationError:
            # Billing configuration cannot disable an independently configured login.
            # The facade reports NOT_CONFIGURED and grants no billing authority.
            stripe_settings, offer_catalogue_reader = None, None
        subscriber = build_subscriber_facade(
            config.subscriber_settings,
            config.data_dir,
            observation_memory=observation_memory,
            reuse_policy=ObservationReusePolicy("subscriber-output-reuse", "051-v1"),
            temporal_policy=TemporalCurrentnessPolicy(
                policy_id="subscriber-public-observation-currentness",
                version="051-v1",
                stale_after=timedelta(days=30),
                historical_after=timedelta(days=90),
            ),
            code_sha=config.code_sha,
            stripe_settings=stripe_settings,
            offer_catalogue_reader=offer_catalogue_reader,
            axent_reasoner=luna_reasoner_from_env(
                config.subscriber_settings.values, data_dir=config.data_dir
            ),
        )
    return AxignalRuntime(
        config=config,
        observation_memory=observation_memory,
        research_work_memory=research_work_memory,
        learning_memory=learning_memory,
        admin_observability=admin_observability,
        governance_policy_store=governance_policy_store,
        governance_audit_store=governance_audit_store,
        admin_acquisition_store=admin_acquisition_store,
        admin_gsc_store=admin_gsc_store,
        admin_accounting_store=admin_accounting_store,
        admin_api_operations_store=admin_api_operations_store,
        admin_commercial_store=admin_commercial_store,
        admin_customer_account_store=admin_customer_account_store,
        admin_billing_store=admin_billing_store,
        admin_financial_document_store=admin_financial_document_store,
        admin_fiscal_compliance_store=admin_fiscal_compliance_store,
        admin_tax_operations_store=admin_tax_operations_store,
        admin_integration_store=admin_integration_store,
        admin_measurement_store=admin_measurement_store,
        admin_weekly_brief_store=admin_weekly_brief_store,
        stripe_webhook=stripe_webhook,
        first_proof=first_proof,
        organization_attention=organization_attention,
        admin_access=admin_access,
        subscriber=subscriber,
    )


def _safe_child(root: Path, relative: str) -> Path | None:
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return None
    return candidate


def _resolve_static(web_root: Path, raw_path: str) -> Path | None:
    path = unquote(raw_path)
    exact: dict[str, str] = {
        "/": "landing/index.html",
        "/index.html": "landing/index.html",
        "/storyboard-data.json": "landing/storyboard-data.json",
        "/robots.txt": "landing/robots.txt",
        "/knowledge": "knowledge/index.html",
        "/knowledge/": "knowledge/index.html",
        "/subscriber": "subscriber/index.html",
        "/subscriber/": "subscriber/index.html",
        "/subscriber.css": "subscriber/subscriber.css",
        "/presentation.js": "subscriber/presentation.js",
        "/locale-es.js": "subscriber/locale-es.js",
        "/app.js": "subscriber/app.js",
        "/admin.css": "admin/admin.css",
        "/admin.js": "admin/admin.js",
        "/admin-acquisition.js": "admin/admin-acquisition.js",
        "/newsletter.js": "landing/newsletter.js",
        "/marketing.js": "landing/marketing.js",
    }
    relative = exact.get(path)
    if relative is not None:
        return _safe_child(web_root, relative)
    if path.startswith("/brand/"):
        return _safe_child(web_root, "subscriber/assets" + path)
    if path.startswith("/design-system/"):
        return _safe_child(web_root, path.lstrip("/"))
    if path.startswith("/assets/icons/"):
        return _safe_child(web_root, "subscriber" + path)
    if path.startswith("/assets/"):
        # The public landing owns the remaining root /assets namespace.
        return _safe_child(web_root, "landing" + path)
    if path.startswith("/subscriber/assets/"):
        return _safe_child(web_root, path.lstrip("/"))
    if path.startswith("/landing/") or path.startswith("/knowledge/"):
        relative = path.lstrip("/")
        candidate = _safe_child(web_root, relative)
        if candidate is not None and candidate.is_dir():
            candidate = candidate / "index.html"
        return candidate
    return None


def _admin_slug(request_path: str) -> str | None:
    path = unquote(request_path).rstrip("/")
    if path == "/admin":
        return ""
    if not path.startswith("/admin/"):
        return None
    slug = path[len("/admin/") :]
    if not slug or "/" in slug:
        return None
    return slug


def _command_center_projection(
    runtime: AxignalRuntime, *, now: datetime
) -> AdminCommandCenterProjection:
    current: dict[AdminProjectionId, AdminProjectionSnapshot] = {}
    previous: dict[AdminProjectionId, AdminProjectionSnapshot] = {}
    for definition in COMMAND_CENTER_METRICS:
        projection_id = definition.source_projection_id
        snapshots = runtime.admin_observability.recent_snapshots(
            projection_id, "global", limit=2, through=now
        )
        if snapshots:
            current[projection_id] = snapshots[0]
        if len(snapshots) > 1:
            previous[projection_id] = snapshots[1]
    return project_command_center(
        current=current,
        previous=previous,
        as_of=now,
        generated_at=now,
    )


def _command_center_payload(
    projection: AdminCommandCenterProjection,
) -> dict[str, object]:
    metrics: list[dict[str, object]] = []
    for item in projection.metrics:
        metrics.append(
            {
                "metricId": item.definition.metric_id,
                "label": item.definition.label,
                "group": item.definition.group,
                "purpose": item.definition.purpose,
                "unit": item.definition.unit.value,
                "value": item.value,
                "currency": item.currency,
                "completeness": item.completeness.value,
                "unknownReason": item.unknown_reason,
                "methodologyVersion": item.observed_methodology_version,
                "expectedMethodologyVersion": item.definition.methodology_version,
                "defaultWindow": item.definition.default_window,
                "periodStart": None if item.period_start is None else item.period_start.isoformat(),
                "periodEnd": None if item.period_end is None else item.period_end.isoformat(),
                "sourceProjectionId": str(item.definition.source_projection_id),
                "sourceRecordTypes": list(item.definition.source_record_types),
                "sourceRecordIds": [str(value) for value in item.source_record_ids],
                "comparisonState": item.comparison_state,
                "previousValue": item.previous_value,
            }
        )
    return {
        "asOf": projection.as_of.isoformat(),
        "generatedAt": projection.generated_at.isoformat(),
        "completeness": projection.completeness.value,
        "metrics": metrics,
    }


def _xeed_observatory_projection(
    runtime: AxignalRuntime, *, now: datetime
) -> XeedAxiglandObservatory:
    return project_xeed_axigland_observatory(
        learning_events=runtime.learning_memory.all_events(),
        admin_records=runtime.admin_observability.records_through(now),
        as_of=now,
        generated_at=now,
    )


def _xeed_observatory_payload(
    projection: XeedAxiglandObservatory,
) -> dict[str, object]:
    xeeds: list[dict[str, object]] = []
    for item in projection.xeeds:
        xeeds.append(
            {
                "xeedId": item.xeed_id,
                "subjectIds": list(item.subject_ids),
                "lifecycleState": item.lifecycle_state,
                "lifecycleCompleteness": item.lifecycle_completeness.value,
                "lifecycleReason": item.lifecycle_reason,
                "currentnessState": item.currentness_state,
                "currentnessCompleteness": item.currentness_completeness.value,
                "currentnessReason": item.currentness_reason,
                "observationCoverageState": item.observation_coverage_state,
                "observationCoverageCompleteness": item.observation_coverage_completeness.value,
                "observationCoverageReason": item.observation_coverage_reason,
                "firstActivityAt": None
                if item.first_activity_at is None
                else item.first_activity_at.isoformat(),
                "lastActivityAt": None
                if item.last_activity_at is None
                else item.last_activity_at.isoformat(),
                "firstUsefulXignalAt": None
                if item.first_useful_xignal_at is None
                else item.first_useful_xignal_at.isoformat(),
                "timeToFirstUsefulXignalMs": item.time_to_first_useful_xignal_ms,
                "learningEventCount": item.learning_event_count,
                "failedEventCount": item.failed_event_count,
                "partialEventCount": item.partial_event_count,
                "observationsReused": item.observations_reused,
                "observationsAdded": item.observations_added,
                "reuseRatio": item.reuse_ratio,
                "xignalsEmitted": item.xignals_emitted,
                "canonicalAdmissions": item.canonical_admissions,
                "knownCostsByCurrency": [list(value) for value in item.known_costs_by_currency],
                "unknownCostEventCount": item.unknown_cost_event_count,
                "directCostCompleteness": item.direct_cost_completeness.value,
                "sharedCostCompleteness": item.shared_cost_completeness.value,
                "sharedCostReason": item.shared_cost_reason,
                "triggeredCostCompleteness": item.triggered_cost_completeness.value,
                "triggeredCostReason": item.triggered_cost_reason,
                "revenueAttributionCompleteness": item.revenue_attribution_completeness.value,
                "revenueAttributionReason": item.revenue_attribution_reason,
                "sourceLearningEventIds": list(item.source_learning_event_ids),
                "sourceAdminRecordIds": list(item.source_admin_record_ids),
            }
        )
    axigland = projection.axigland
    return {
        "asOf": projection.as_of.isoformat(),
        "generatedAt": projection.generated_at.isoformat(),
        "completeness": projection.completeness.value,
        "coverageNotes": list(projection.coverage_notes),
        "xeeds": xeeds,
        "axigland": {
            "completeness": axigland.completeness.value,
            "canonicalAdmissionEvents": axigland.canonical_admission_events,
            "observationsReused": axigland.observations_reused,
            "observationsAdded": axigland.observations_added,
            "reuseRatio": axigland.reuse_ratio,
            "growthState": axigland.growth_state,
            "growthCompleteness": axigland.growth_completeness.value,
            "contradictionState": axigland.contradiction_state,
            "contradictionCompleteness": axigland.contradiction_completeness.value,
            "identityResolutionState": axigland.identity_resolution_state,
            "identityResolutionCompleteness": axigland.identity_resolution_completeness.value,
            "currentnessState": axigland.currentness_state,
            "currentnessCompleteness": axigland.currentness_completeness.value,
            "provenanceState": axigland.provenance_state,
            "provenanceCompleteness": axigland.provenance_completeness.value,
            "sourceLearningEventIds": list(axigland.source_learning_event_ids),
            "sourceAdminRecordIds": list(axigland.source_admin_record_ids),
        },
    }


def _brain_observatory_projection(
    runtime: AxignalRuntime, *, now: datetime
) -> BrainProviderObservatory:
    return project_brain_provider_observatory(
        learning_events=runtime.learning_memory.all_events(),
        admin_records=runtime.admin_observability.records_through(now),
        as_of=now,
        generated_at=now,
    )


def _brain_observatory_payload(
    projection: BrainProviderObservatory,
) -> dict[str, object]:
    providers: list[dict[str, object]] = []
    for item in projection.provider_slices:
        providers.append(
            {
                "provider": item.provider,
                "providerVersion": item.provider_version,
                "operationClass": item.operation_class,
                "policyId": item.policy_id,
                "policyVersion": item.policy_version,
                "comparisonKey": item.comparison_key,
                "eventCount": item.event_count,
                "completedCount": item.completed_count,
                "partialCount": item.partial_count,
                "noChangeCount": item.no_change_count,
                "failedCount": item.failed_count,
                "knownCostsByCurrency": [list(value) for value in item.known_costs_by_currency],
                "unknownCostEventCount": item.unknown_cost_event_count,
                "costCompleteness": item.cost_completeness.value,
                "knownLatencyEventCount": item.known_latency_event_count,
                "totalLatencyMs": item.total_latency_ms,
                "averageLatencyMs": item.average_latency_ms,
                "latencyCompleteness": item.latency_completeness.value,
                "knownInputUnitEventCount": item.known_input_unit_event_count,
                "knownOutputUnitEventCount": item.known_output_unit_event_count,
                "totalInputUnits": item.total_input_units,
                "totalOutputUnits": item.total_output_units,
                "semanticJudgmentsProduced": item.semantic_judgments_produced,
                "researchObjectivesResolved": item.research_objectives_resolved,
                "usefulOutputEventCount": item.useful_output_event_count,
                "sourceLearningEventIds": list(item.source_learning_event_ids),
            }
        )
    control = projection.control
    return {
        "asOf": projection.as_of.isoformat(),
        "generatedAt": projection.generated_at.isoformat(),
        "completeness": projection.completeness.value,
        "coverageNotes": list(projection.coverage_notes),
        "learningEventCount": projection.learning_event_count,
        "cognitiveEventCount": projection.cognitive_event_count,
        "deterministicEventCount": projection.deterministic_event_count,
        "structuredEvaluatorEventCount": projection.structured_evaluator_event_count,
        "adaptiveResearchEventCount": projection.adaptive_research_event_count,
        "governanceEventCount": projection.governance_event_count,
        "completedEventCount": projection.completed_event_count,
        "partialEventCount": projection.partial_event_count,
        "noChangeEventCount": projection.no_change_event_count,
        "failedEventCount": projection.failed_event_count,
        "providerAttributedEventCount": projection.provider_attributed_event_count,
        "providerUnattributedCognitiveEventCount": (
            projection.provider_unattributed_cognitive_event_count
        ),
        "knownCostsByCurrency": [list(value) for value in projection.known_costs_by_currency],
        "unknownCostEventCount": projection.unknown_cost_event_count,
        "costCompleteness": projection.cost_completeness.value,
        "knownLatencyEventCount": projection.known_latency_event_count,
        "totalLatencyMs": projection.total_latency_ms,
        "averageLatencyMs": projection.average_latency_ms,
        "latencyCompleteness": projection.latency_completeness.value,
        "semanticJudgmentsProduced": projection.semantic_judgments_produced,
        "researchObjectivesResolved": projection.research_objectives_resolved,
        "usefulOutputEventCount": projection.useful_output_event_count,
        "providerSlices": providers,
        "control": {
            "researchObjectiveState": control.research_objective_state,
            "researchObjectiveCompleteness": control.research_objective_completeness.value,
            "researchObjectiveReason": control.research_objective_reason,
            "routingState": control.routing_state,
            "routingCompleteness": control.routing_completeness.value,
            "routingReason": control.routing_reason,
            "stopState": control.stop_state,
            "stopCompleteness": control.stop_completeness.value,
            "stopReason": control.stop_reason,
            "budgetState": control.budget_state,
            "budgetCompleteness": control.budget_completeness.value,
            "budgetReason": control.budget_reason,
            "noProgressState": control.no_progress_state,
            "noProgressCompleteness": control.no_progress_completeness.value,
            "noProgressReason": control.no_progress_reason,
            "retryState": control.retry_state,
            "retryCompleteness": control.retry_completeness.value,
            "retryReason": control.retry_reason,
            "abstentionState": control.abstention_state,
            "abstentionCompleteness": control.abstention_completeness.value,
            "abstentionReason": control.abstention_reason,
            "knowledgeFrontierState": control.knowledge_frontier_state,
            "knowledgeFrontierCompleteness": control.knowledge_frontier_completeness.value,
            "knowledgeFrontierReason": control.knowledge_frontier_reason,
            "unresolvedGapState": control.unresolved_gap_state,
            "unresolvedGapCompleteness": control.unresolved_gap_completeness.value,
            "unresolvedGapReason": control.unresolved_gap_reason,
            "sourceAdminRecordIds": list(control.source_admin_record_ids),
            "sourceLearningEventIds": list(control.source_learning_event_ids),
        },
        "sourceLearningEventIds": list(projection.source_learning_event_ids),
    }


def _governance_projection(runtime: AxignalRuntime, *, now: datetime) -> AdminGovernanceProjection:
    return project_admin_governance(
        policy_store=runtime.governance_policy_store,
        learning_events=runtime.learning_memory.all_events(),
        admin_records=runtime.admin_observability.records_through(now),
        audit_records=runtime.governance_audit_store.all(),
        as_of=now,
    )


def _governance_payload(
    projection: AdminGovernanceProjection,
) -> dict[str, object]:
    return {
        "asOf": projection.as_of.isoformat(),
        "completeness": projection.completeness.value,
        "unsupportedCanonicalWriteTargetCount": (
            projection.unsupported_canonical_write_target_count
        ),
        "coverageNotes": list(projection.coverage_notes),
        "policies": [
            {
                "family": item.family.value,
                "policyId": item.policy_id,
                "policyVersion": item.policy_version,
                "codeSha": item.code_sha,
                "effectiveAt": (
                    None if item.effective_at is None else item.effective_at.isoformat()
                ),
                "completeness": item.completeness.value,
                "sourceRefs": list(item.source_refs),
                "changeCount": item.change_count,
            }
            for item in projection.policies
        ],
        "policyChanges": [
            {
                "decisionId": item.decision_id,
                "family": item.family,
                "kind": item.kind,
                "actor": item.actor,
                "beforePolicyId": item.before_policy_id,
                "beforeVersion": item.before_version,
                "afterPolicyId": item.after_policy_id,
                "afterVersion": item.after_version,
                "reason": item.reason,
                "effectiveAt": item.effective_at.isoformat(),
            }
            for item in projection.policy_changes
        ],
        "alerts": [
            {
                "alertClass": item.alert_class.value,
                "count": item.count,
                "completeness": item.completeness.value,
                "reason": item.reason,
                "sourceRefs": list(item.source_refs),
            }
            for item in projection.alerts
        ],
        "auditRecords": [
            {
                "auditId": item.audit_id,
                "commandId": item.command_id,
                "occurredAt": item.occurred_at.isoformat(),
                "actorPrincipalId": item.actor_principal_id,
                "target": item.target.value,
                "action": item.action,
                "reason": item.reason,
                "requiredScope": item.required_scope,
                "outcome": item.outcome.value,
                "resultCode": item.result_code,
                "beforeRef": item.before_ref,
                "afterRef": item.after_ref,
                "approvalRef": item.approval_ref,
            }
            for item in projection.audit_records
        ],
    }


def _acquisition_projection(
    runtime: AxignalRuntime,
    *,
    grant: AdminAuthorizationGrant,
    now: datetime,
) -> AdminAcquisitionProjection:
    return project_admin_acquisition(
        store=runtime.admin_acquisition_store,
        grant=grant,
        generated_at=now,
    )


def _acquisition_payload(projection: AdminAcquisitionProjection) -> dict[str, object]:
    return {
        "privacyClass": projection.privacy_class,
        "generatedAt": projection.generated_at.isoformat(),
        "requestCount": projection.request_count,
        "acceptedCount": projection.accepted_count,
        "consentedCount": projection.consented_count,
        "deliveryEligibleCount": projection.delivery_eligible_count,
        "marketingEventCount": projection.marketing_event_count,
        "anonymousSessionCount": projection.anonymous_session_count,
        "attributedRequestCount": projection.attributed_request_count,
        "sourceCounts": [list(value) for value in projection.source_counts],
        "campaignCounts": [list(value) for value in projection.campaign_counts],
        "attributionModel": projection.attribution_model,
        "piiVisible": projection.pii_visible,
        "coverageNotes": list(projection.coverage_notes),
        "requests": [
            {
                "requestId": item.request_id,
                "companyName": item.company_name,
                "companyDomain": item.company_domain,
                "reviewState": item.review_state,
                "coverageState": item.coverage_state,
                "consentState": item.consent_state,
                "deliveryEligible": item.delivery_eligible,
                "observedSource": item.observed_source,
                "observedCampaign": item.observed_campaign,
                "attributionEventId": item.attribution_event_id,
                "requestedAt": item.requested_at.isoformat(),
                "updatedAt": item.updated_at.isoformat(),
            }
            for item in projection.requests
        ],
    }


def _gsc_projection(runtime: AxignalRuntime, *, now: datetime) -> GscPrivateAnalyticsProjection:
    return project_private_gsc(store=runtime.admin_gsc_store, generated_at=now)


def _gsc_payload(projection: GscPrivateAnalyticsProjection) -> dict[str, object]:
    return {
        "privacyClass": projection.privacy_class,
        "generatedAt": projection.generated_at.isoformat(),
        "propertyRef": projection.property_ref,
        "latestWindowStart": (
            None
            if projection.latest_window_start is None
            else projection.latest_window_start.isoformat()
        ),
        "latestWindowEnd": (
            None
            if projection.latest_window_end is None
            else projection.latest_window_end.isoformat()
        ),
        "latestSyncAt": (
            None if projection.latest_sync_at is None else projection.latest_sync_at.isoformat()
        ),
        "latestRowCount": projection.latest_row_count,
        "breakdownCounts": [list(value) for value in projection.breakdown_counts],
        "coverageNotes": list(projection.coverage_notes),
    }


def _commercial_projection(
    runtime: AxignalRuntime,
    *,
    grant: AdminAuthorizationGrant,
    now: datetime,
) -> AdminCommercialProjection:
    return project_admin_commercial(
        store=runtime.admin_commercial_store,
        grant=grant,
        generated_at=now,
    )


def _commercial_payload(projection: AdminCommercialProjection) -> dict[str, object]:
    return {
        "privacyClass": projection.privacy_class,
        "generatedAt": projection.generated_at.isoformat(),
        "prospectCount": projection.prospect_count,
        "companyCount": projection.company_count,
        "contactCount": projection.contact_count,
        "opportunityCount": projection.opportunity_count,
        "dealCount": projection.deal_count,
        "noteCount": projection.note_count,
        "openTaskCount": projection.open_task_count,
        "originCounts": [list(value) for value in projection.origin_counts],
        "auditCount": projection.audit_count,
        "piiVisible": projection.pii_visible,
        "coverageNotes": list(projection.coverage_notes),
        "companies": [
            {
                "companyId": item.company_id,
                "displayName": item.display_name,
                "acquisitionSource": item.acquisition_source,
                "consentBasis": item.consent_basis,
                "origin": item.origin,
                "observedOrganizationId": item.observed_organization_id,
                "accountId": item.account_id,
                "opportunityCount": item.opportunity_count,
                "openTaskCount": item.open_task_count,
                "noteCount": item.note_count,
                "contactCount": item.contact_count,
            }
            for item in projection.companies
        ],
    }


def _customer_operations_projection(
    runtime: AxignalRuntime,
    *,
    grant: AdminAuthorizationGrant,
    now: datetime,
) -> CustomerOperationsProjection:
    return project_customer_operations(
        store=runtime.admin_customer_account_store,
        grant=grant,
        generated_at=now,
    )


def _customer_operations_payload(
    projection: CustomerOperationsProjection,
) -> dict[str, object]:
    return {
        "privacyClass": projection.privacy_class,
        "generatedAt": projection.generated_at.isoformat(),
        "accountCount": projection.account_count,
        "activeAccountCount": projection.active_account_count,
        "suspendedAccountCount": projection.suspended_account_count,
        "cancelledAccountCount": projection.cancelled_account_count,
        "totalEntitledXeeds": projection.total_entitled_xeeds,
        "mrrEur": projection.mrr_eur,
        "paymentAuthority": projection.payment_authority,
        "coverageNotes": list(projection.coverage_notes),
        "funnelCounts": [list(item) for item in projection.funnel_counts],
        "cohorts": [
            {
                "cohortKey": item.cohort_key,
                "accountCount": item.account_count,
                "activeAccountCount": item.active_account_count,
                "cancelledAccountCount": item.cancelled_account_count,
            }
            for item in projection.cohorts
        ],
        "customers": [
            {
                "accountId": item.account_id,
                "tenantId": item.tenant_id,
                "displayName": item.display_name,
                "signupAt": item.signup_at.isoformat(),
                "accountStatus": item.account_status,
                "subscriptionStatus": item.subscription_status,
                "planCode": item.plan_code,
                "planVersion": item.plan_version,
                "paymentState": item.payment_state,
                "xeedCapacity": item.xeed_capacity,
                "activeXeedCount": item.active_xeed_count,
                "entitledXeedIds": list(item.entitled_xeed_ids),
                "userCount": item.user_count,
                "funnelStages": list(item.funnel_stages),
                "supportRefs": list(item.support_refs),
                "claimReviewRefs": list(item.claim_review_refs),
                "cancellationReason": item.cancellation_reason,
                "mrrEur": item.mrr_eur,
                "pricingHypothesisMonthlyEur": item.pricing_hypothesis_monthly_eur,
                "eventCount": item.event_count,
            }
            for item in projection.customers
        ],
    }


def _financial_document_projection(
    runtime: AxignalRuntime, *, grant: AdminAuthorizationGrant, now: datetime
) -> FinancialDocumentProjection:
    return project_financial_documents(
        store=runtime.admin_financial_document_store,
        grant=grant,
        generated_at=now,
    )


def _financial_document_payload(
    projection: FinancialDocumentProjection,
) -> dict[str, object]:
    totals: dict[str, int] = {}
    for row in projection.exports:
        totals[row.currency] = totals.get(row.currency, 0) + row.signed_gross_minor
    return {
        "generatedAt": projection.generated_at.isoformat(),
        "privacyClass": projection.privacy_class,
        "coverageNotes": list(projection.coverage_notes),
        "netDocumentFlowByCurrencyMinor": totals,
        "records": [
            {
                "recordId": record.record_id,
                "accountId": record.account_id,
                "kind": record.kind.value,
                "state": record.state.value,
                "occurredAt": record.occurred_at.isoformat(),
                "currency": record.currency,
                "grossMinor": record.gross_minor,
                "sourceSystem": record.source.system,
                "sourceObjectRef": record.source.object_ref,
                "sourceEventRef": record.source.event_ref,
                "adapterRef": record.source.adapter_ref,
                "billingEventId": record.billing_event_id,
                "documentNumber": record.document_number,
                "taxBasisState": record.tax_basis_state.value,
                "netMinor": record.net_minor,
                "taxMinor": record.tax_minor,
                "correctsRecordId": record.corrects_record_id,
            }
            for record in projection.records
        ],
    }


def _accounting_reconciliation_projection(
    runtime: AxignalRuntime, *, grant: AdminAuthorizationGrant, now: datetime
) -> AccountingReconciliationProjection:
    return project_accounting_reconciliation(
        store=runtime.admin_accounting_store,
        financial_store=runtime.admin_financial_document_store,
        integration_store=runtime.admin_integration_store,
        grant=grant,
        generated_at=now,
    )


def _accounting_reconciliation_payload(
    projection: AccountingReconciliationProjection,
) -> dict[str, object]:
    return {
        "generatedAt": projection.generated_at.isoformat(),
        "privacyClass": projection.privacy_class,
        "adapterStrategy": projection.adapter_strategy,
        "configuredIntegrations": list(projection.configured_integrations),
        "coverageNotes": list(projection.coverage_notes),
        "totals": [
            {
                "currency": item.currency,
                "billedMinor": item.billed_minor,
                "paidMinor": item.paid_minor,
                "refundedMinor": item.refunded_minor,
                "creditNoteMinor": item.credit_note_minor,
                "settledGrossMinor": item.settled_gross_minor,
                "processorFeeMinor": item.processor_fee_minor,
                "settledNetMinor": item.settled_net_minor,
                "accountedMinor": item.accounted_minor,
                "infrastructureCostMinor": item.infrastructure_cost_minor,
                "businessExpenseMinor": item.business_expense_minor,
            }
            for item in projection.totals
        ],
        "mappings": [
            {
                "mappingId": item.mapping_id,
                "integrationId": item.integration_id,
                "category": item.category.value,
                "accountCode": item.account_code,
                "effectiveAt": item.effective_at.isoformat(),
                "version": item.version,
            }
            for item in projection.mappings
        ],
        "issues": [
            {
                "issueId": item.issue_id,
                "kind": item.kind.value,
                "state": item.state.value,
                "openedAt": item.opened_at.isoformat(),
                "currency": item.currency,
                "expectedMinor": item.expected_minor,
                "observedMinor": item.observed_minor,
                "financialRecordId": item.financial_record_id,
                "accountingEntryId": item.accounting_entry_id,
                "settlementId": item.settlement_id,
                "resolvedAt": (None if item.resolved_at is None else item.resolved_at.isoformat()),
                "resolutionRef": item.resolution_ref,
            }
            for item in projection.issues
        ],
        "periods": [
            {
                "periodId": item.period_id,
                "periodStart": item.period_start.isoformat(),
                "periodEnd": item.period_end.isoformat(),
                "state": item.state.value,
                "evaluatedAt": item.evaluated_at.isoformat(),
                "closedAt": None if item.closed_at is None else item.closed_at.isoformat(),
                "sourceRef": item.source_ref,
            }
            for item in projection.periods
        ],
    }


def _fiscal_compliance_projection(
    runtime: AxignalRuntime, *, grant: AdminAuthorizationGrant, now: datetime
) -> FiscalComplianceProjection:
    from pipeline.source_acquisition import (
        ContentAddressedArtifactIntegrityAdapter,
        ContentAddressedArtifactStore,
    )

    return project_fiscal_compliance(
        store=runtime.admin_fiscal_compliance_store,
        integration_store=runtime.admin_integration_store,
        ruleset=canonical_es_sif_ruleset(),
        grant=grant,
        generated_at=now,
        artifact_integrity=ContentAddressedArtifactIntegrityAdapter(
            ContentAddressedArtifactStore(runtime.config.data_dir / "artifacts")
        ),
    )


def _fiscal_compliance_payload(
    projection: FiscalComplianceProjection,
) -> dict[str, object]:
    return {
        "generatedAt": projection.generated_at.isoformat(),
        "route": projection.route.value,
        "state": projection.state.value,
        "integrationId": projection.integration_id,
        "providerVersion": projection.provider_version,
        "adapterVersion": projection.adapter_version,
        "integrationDefinitionVersion": projection.integration_definition_version,
        "approvalEffective": projection.approval_effective,
        "liveEnablementAllowed": projection.live_enablement_allowed,
        "complianceClaimAllowed": projection.compliance_claim_allowed,
        "evidenceKinds": [item.value for item in projection.evidence_kinds],
        "missingEvidence": [item.value for item in projection.missing_evidence],
        "invalidReasons": list(projection.invalid_reasons),
        "coverageNotes": list(projection.coverage_notes),
        "ruleset": {
            "rulesetId": projection.ruleset.ruleset_id,
            "jurisdiction": projection.ruleset.jurisdiction,
            "effectiveAt": projection.ruleset.effective_at.isoformat(),
            "corporateDeadline": projection.ruleset.corporate_deadline.isoformat(),
            "otherTaxpayerDeadline": (projection.ruleset.other_taxpayer_deadline.isoformat()),
            "sourceRefs": list(projection.ruleset.source_refs),
        },
    }


def _tax_operations_projection(
    runtime: AxignalRuntime, *, grant: AdminAuthorizationGrant, now: datetime
) -> TaxOperationsProjection:
    return project_tax_operations(
        store=runtime.admin_tax_operations_store,
        grant=grant,
        generated_at=now,
    )


def _tax_operations_payload(projection: TaxOperationsProjection) -> dict[str, object]:
    return {
        "generatedAt": projection.generated_at.isoformat(),
        "privacyClass": projection.privacy_class,
        "rulesetVersion": projection.ruleset_version,
        "coverageNotes": list(projection.coverage_notes),
        "obligations": [
            {
                "obligationId": item.obligation.obligation_id,
                "taxpayerRef": item.obligation.taxpayer_ref,
                "ruleId": item.obligation.rule_id,
                "modelCode": item.obligation.model_code,
                "periodStart": item.obligation.period_start.isoformat(),
                "periodEnd": item.obligation.period_end.isoformat(),
                "dueAt": item.obligation.due_at.isoformat(),
                "deadlineSourceRef": item.obligation.deadline_source_ref,
                "applicability": item.obligation.applicability.value,
                "state": item.state.value,
                "overdue": item.overdue,
                "complete": item.complete,
                "evidenceKinds": [kind.value for kind in item.evidence_kinds],
                "missingEvidence": [kind.value for kind in item.missing_evidence],
            }
            for item in projection.obligations
        ],
    }


def _measurement_registry_projection(
    runtime: AxignalRuntime, *, grant: AdminAuthorizationGrant, now: datetime
) -> MeasurementRegistryProjection:
    return project_measurement_registry(
        store=runtime.admin_measurement_store,
        grant=grant,
        generated_at=now,
    )


def _measurement_registry_payload(
    projection: MeasurementRegistryProjection,
) -> dict[str, object]:
    return {
        "generatedAt": projection.generated_at.isoformat(),
        "privacyClass": projection.privacy_class,
        "coverageNotes": list(projection.coverage_notes),
        "definitions": [
            {
                "measureId": item.measure_id,
                "version": item.version,
                "label": item.label,
                "questionServed": item.question_served,
                "decisionServed": item.decision_served,
                "formulaOrCodingRule": item.formula_or_coding_rule,
                "unit": item.unit.value,
                "sourceFamily": item.source_family,
                "instrumentId": item.instrument_id,
                "instrumentVersion": item.instrument_version,
                "subjectScope": item.subject_scope,
                "defaultWindow": item.default_window,
                "freshnessSeconds": item.freshness_seconds,
                "minimumSampleSize": item.minimum_sample_size,
                "uncertaintyPolicy": item.uncertainty_policy,
                "compatibilityKey": item.compatibility_key,
                "interpretationLimits": list(item.interpretation_limits),
                "evaluationCases": list(item.evaluation_cases),
                "effectiveAt": item.effective_at.isoformat(),
            }
            for item in projection.definitions
        ],
        "readouts": [
            {
                "observationId": item.observation.observation_id,
                "measureId": item.observation.measure_id,
                "definitionVersion": item.observation.definition_version,
                "subjectRef": item.observation.subject_ref,
                "instrumentId": item.observation.instrument_id,
                "instrumentVersion": item.observation.instrument_version,
                "state": item.observation.state.value,
                "observedAt": item.observation.observed_at.isoformat(),
                "windowStart": item.observation.window_start.isoformat(),
                "windowEnd": item.observation.window_end.isoformat(),
                "sampleSize": item.observation.sample_size,
                "informativeSampleSize": item.observation.informative_sample_size,
                "value": item.observation.value,
                "currency": item.observation.currency,
                "uncertainty": item.observation.uncertainty,
                "sourceRefs": list(item.observation.source_refs),
                "freshness": item.freshness.value,
                "usable": item.usable,
                "reason": item.reason,
            }
            for item in projection.readouts
        ],
    }


def _integration_projection(
    runtime: AxignalRuntime, *, grant: AdminAuthorizationGrant, now: datetime
) -> AdminIntegrationProjection:
    return project_admin_integrations(
        store=runtime.admin_integration_store,
        grant=grant,
        as_of=now,
    )


def _api_operations_projection(
    runtime: AxignalRuntime, *, grant: AdminAuthorizationGrant, now: datetime
) -> ApiOperationsProjection:
    return project_api_operations(
        store=runtime.admin_api_operations_store,
        grant=grant,
        generated_at=now,
    )


def _api_operations_payload(projection: ApiOperationsProjection) -> dict[str, object]:
    return {
        "generatedAt": projection.generated_at.isoformat(),
        "privacyClass": projection.privacy_class,
        "coverageNotes": list(projection.coverage_notes),
        "webhooks": {
            "received": projection.webhook_received_count,
            "succeeded": projection.webhook_success_count,
            "retryPending": projection.webhook_retry_pending_count,
            "deadLetter": projection.webhook_dead_letter_count,
            "rejected": projection.webhook_rejected_count,
        },
        "deadLetters": [
            {
                "integrationId": item.integration_id,
                "providerEventId": item.provider_event_id,
                "eventType": item.event_type,
                "receivedAt": item.received_at.isoformat(),
                "attemptCount": item.attempt_count,
                "maxAttempts": item.max_attempts,
                "failureCategory": item.failure_category,
            }
            for item in projection.dead_letters
        ],
        "endpoints": [
            {
                "endpointId": item.endpoint.endpoint_id,
                "method": item.endpoint.method,
                "pathTemplate": item.endpoint.path_template,
                "exposure": item.endpoint.exposure.value,
                "direction": item.endpoint.direction.value,
                "schemaVersion": item.endpoint.schema_version,
                "integrationId": item.endpoint.integration_id,
                "authorityBoundary": item.endpoint.authority_boundary,
                "requestCount": item.request_count,
                "errorCount": item.error_count,
                "errorRate": item.error_rate,
                "averageLatencyMs": item.average_latency_ms,
                "lastStatusCode": item.last_status_code,
                "lastObservedAt": (
                    None if item.last_observed_at is None else item.last_observed_at.isoformat()
                ),
                "quotaRemaining": item.quota_remaining,
                "rateLimited": item.rate_limited,
            }
            for item in projection.endpoints
        ],
    }


def _integration_payload(projection: AdminIntegrationProjection) -> dict[str, object]:
    return {
        "asOf": projection.as_of.isoformat(),
        "privacyClass": projection.privacy_class,
        "coverageNotes": list(projection.coverage_notes),
        "integrations": [
            {
                "integrationId": item.definition.integration_id,
                "provider": item.definition.provider,
                "purpose": item.definition.purpose,
                "owner": item.definition.owner,
                "environment": item.definition.environment.value,
                "enabled": item.definition.enabled,
                "credentialState": item.definition.credential.state.value,
                "credentialConfigured": item.definition.credential.reference is not None,
                "rotationAt": (
                    None
                    if item.definition.credential.last_rotated_at is None
                    else item.definition.credential.last_rotated_at.isoformat()
                ),
                "expiresAt": (
                    None
                    if item.definition.credential.expires_at is None
                    else item.definition.credential.expires_at.isoformat()
                ),
                "revokedAt": (
                    None
                    if item.definition.credential.revoked_at is None
                    else item.definition.credential.revoked_at.isoformat()
                ),
                "scopes": list(item.definition.scopes),
                "direction": item.definition.direction.value,
                "authorityBoundary": item.definition.authority_boundary,
                "webhookCapable": item.definition.webhook_capable,
                "webhookConfigured": item.definition.webhook_endpoint is not None,
                "rateLimitPosture": item.definition.rate_limit_posture,
                "healthFreshnessSeconds": item.definition.health_freshness_seconds,
                "health": (item.health_state.value),
                "lastVerifiedAt": None
                if item.health is None
                else item.health.observed_at.isoformat(),
                "lastSuccessAt": (
                    None
                    if item.health is None or item.health.last_success_at is None
                    else item.health.last_success_at.isoformat()
                ),
                "lastFailureAt": (
                    None
                    if item.health is None or item.health.last_failure_at is None
                    else item.health.last_failure_at.isoformat()
                ),
                "failureCategory": None if item.health is None else item.health.failure_category,
                "sourceRef": None if item.health is None else item.health.source_ref,
            }
            for item in projection.integrations
        ],
    }


def _admin_projection_payload(
    projection: AdminShellProjection,
    *,
    command_center: AdminCommandCenterProjection | None = None,
    xeed_observatory: XeedAxiglandObservatory | None = None,
    brain_observatory: BrainProviderObservatory | None = None,
    governance: AdminGovernanceProjection | None = None,
    acquisition: AdminAcquisitionProjection | None = None,
    gsc: GscPrivateAnalyticsProjection | None = None,
    commercial: AdminCommercialProjection | None = None,
    customer_operations: CustomerOperationsProjection | None = None,
    integrations: AdminIntegrationProjection | None = None,
    api_operations: ApiOperationsProjection | None = None,
    financial_documents: FinancialDocumentProjection | None = None,
    accounting_reconciliation: AccountingReconciliationProjection | None = None,
    fiscal_compliance: FiscalComplianceProjection | None = None,
    tax_operations: TaxOperationsProjection | None = None,
    measurement_registry: MeasurementRegistryProjection | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "mode": projection.mode,
        "principalId": projection.principal_id,
        "roles": list(projection.roles),
        "scopes": list(projection.scopes),
        "currentSlug": projection.current_slug,
        "navigation": [
            {
                "slug": item.slug,
                "label": item.label,
                "eyebrow": item.eyebrow,
                "description": item.description,
            }
            for item in projection.navigation
        ],
    }
    if command_center is not None:
        payload["commandCenter"] = _command_center_payload(command_center)
    if xeed_observatory is not None:
        payload["xeedObservatory"] = _xeed_observatory_payload(xeed_observatory)
    if brain_observatory is not None:
        payload["brainObservatory"] = _brain_observatory_payload(brain_observatory)
    if governance is not None:
        payload["governance"] = _governance_payload(governance)
    if acquisition is not None:
        payload["acquisition"] = _acquisition_payload(acquisition)
    if gsc is not None:
        payload["gsc"] = _gsc_payload(gsc)
    if commercial is not None:
        payload["commercial"] = _commercial_payload(commercial)
    if customer_operations is not None:
        payload["customerOperations"] = _customer_operations_payload(customer_operations)
    if integrations is not None:
        payload["integrations"] = _integration_payload(integrations)
    if api_operations is not None:
        payload["apiOperations"] = _api_operations_payload(api_operations)
    if financial_documents is not None:
        payload["financialDocuments"] = _financial_document_payload(financial_documents)
    if accounting_reconciliation is not None:
        payload["accountingReconciliation"] = _accounting_reconciliation_payload(
            accounting_reconciliation
        )
    if fiscal_compliance is not None:
        payload["fiscalCompliance"] = _fiscal_compliance_payload(fiscal_compliance)
    if tax_operations is not None:
        payload["taxOperations"] = _tax_operations_payload(tax_operations)
    if measurement_registry is not None:
        payload["measurementRegistry"] = _measurement_registry_payload(measurement_registry)
    return payload


def _render_admin_shell(
    web_root: Path,
    projection: AdminShellProjection,
    *,
    command_center: AdminCommandCenterProjection | None = None,
    xeed_observatory: XeedAxiglandObservatory | None = None,
    brain_observatory: BrainProviderObservatory | None = None,
    governance: AdminGovernanceProjection | None = None,
    acquisition: AdminAcquisitionProjection | None = None,
    gsc: GscPrivateAnalyticsProjection | None = None,
    commercial: AdminCommercialProjection | None = None,
    customer_operations: CustomerOperationsProjection | None = None,
    integrations: AdminIntegrationProjection | None = None,
    api_operations: ApiOperationsProjection | None = None,
    financial_documents: FinancialDocumentProjection | None = None,
    accounting_reconciliation: AccountingReconciliationProjection | None = None,
    fiscal_compliance: FiscalComplianceProjection | None = None,
    tax_operations: TaxOperationsProjection | None = None,
    measurement_registry: MeasurementRegistryProjection | None = None,
) -> bytes:
    template = (web_root / "admin" / "index.html").read_text(encoding="utf-8")
    payload = html.escape(
        json.dumps(
            _admin_projection_payload(
                projection,
                command_center=command_center,
                xeed_observatory=xeed_observatory,
                brain_observatory=brain_observatory,
                governance=governance,
                acquisition=acquisition,
                gsc=gsc,
                commercial=commercial,
                customer_operations=customer_operations,
                integrations=integrations,
                api_operations=api_operations,
                financial_documents=financial_documents,
                accounting_reconciliation=accounting_reconciliation,
                fiscal_compliance=fiscal_compliance,
                tax_operations=tax_operations,
                measurement_registry=measurement_registry,
            ),
            sort_keys=True,
            separators=(",", ":"),
        ),
        quote=False,
    )
    marker = "__AXIGNAL_ADMIN_BOOTSTRAP_JSON__"
    if template.count(marker) != 1:
        raise RuntimeError("Admin shell template bootstrap marker is invalid")
    return template.replace(marker, payload).encode("utf-8")


def make_handler(runtime: AxignalRuntime) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = "AXIGNALRuntime/1"

        def _customer_zero_authority(
            self, *, write: bool = False
        ) -> AdminAuthorizationGrant | None:
            if runtime.admin_access is None:
                self._json(
                    {"status": "rejected", "reason": "ADMIN_NOT_COMPOSED"}, HTTPStatus.NOT_FOUND
                )
                return None
            try:
                return AdminHttpAccessGuard(runtime.admin_access).authorize_header(
                    self.headers.get("Authorization"),
                    required_scope=AdminScope.RESEARCH_OPERATE if write else AdminScope.XEEDS_READ,
                    risk=AdminRiskClass.WRITE if write else AdminRiskClass.READ,
                    now=datetime.now(UTC),
                )
            except AdminAuthenticationError:
                self._json(
                    {"status": "rejected", "reason": "ADMIN_SESSION_REQUIRED"},
                    HTTPStatus.UNAUTHORIZED,
                )
                return None
            except AdminAuthorizationError:
                self._json(
                    {"status": "rejected", "reason": "ADMIN_SCOPE_REQUIRED"}, HTTPStatus.FORBIDDEN
                )
                return None

        def log_message(self, fmt: str, *args: object) -> None:
            # Keep default stderr access logging but never log headers/bodies/secrets.
            if ProductMcpHttp.handles(urlsplit(self.path).path):
                # OAuth queries carry state/challenges; log the path only.
                super().log_message("product-mcp %s %s", self.command, urlsplit(self.path).path)
                return
            if (
                is_subscriber_path(self.path)
                or urlsplit(self.path).path == "/internal/webhooks/subscriber-stripe"
                or urlsplit(self.path).path == "/internal/admin/pilot-test-accounts"
            ):
                # The default request line includes query strings; redact callbacks.
                super().log_message("subscriber request %s", self.command)
            else:
                super().log_message(fmt, *args)

        def _product_mcp(self, method: str) -> None:
            edge = getattr(runtime.subscriber, "mcp_http", None)
            if not isinstance(edge, ProductMcpHttp):
                self._json({"error": "not_found"}, HTTPStatus.NOT_FOUND)
                return
            body = b""
            if method == "POST":
                if self.headers.get("Transfer-Encoding") is not None:
                    self._json({"error": "invalid_request"}, HTTPStatus.BAD_REQUEST)
                    return
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                except ValueError:
                    length = -1
                if not 0 <= length <= PRODUCT_MCP_MAX_BODY:
                    self._json({"error": "invalid_request"}, HTTPStatus.REQUEST_ENTITY_TOO_LARGE)
                    return
                body = self.rfile.read(length)
            if len(self.headers.get_all("Authorization") or []) > 1:
                # Ambiguous credentials are never resolved by picking one.
                self._json({"error": "invalid_request"}, HTTPStatus.BAD_REQUEST)
                return
            headers = {name.lower(): value for name, value in self.headers.items()}
            result = edge.handle(method, self.path, headers, body)
            self.send_response(result.status)
            for name, value in result.headers:
                self.send_header(name, value)
            self.send_header("Content-Length", str(len(result.body)))
            self.end_headers()
            if method != "HEAD":
                self.wfile.write(result.body)

        def do_DELETE(self) -> None:
            if ProductMcpHttp.handles(urlsplit(self.path).path):
                self._product_mcp("DELETE")
                return
            # Every other DELETE keeps the existing POST-path handling.
            self.do_POST()

        def _pilot_accounts(self, *, write: bool = False) -> None:
            if runtime.admin_access is None:
                self._json({"reason": "ADMIN_NOT_COMPOSED"}, HTTPStatus.NOT_FOUND)
                return
            try:
                guard = AdminHttpAccessGuard(runtime.admin_access)
                guard.authorize_header(
                    self.headers.get("Authorization"),
                    required_scope=AdminScope.CUSTOMERS_WRITE
                    if write
                    else AdminScope.CUSTOMERS_READ,
                    risk=AdminRiskClass.WRITE if write else AdminRiskClass.READ,
                    now=datetime.now(UTC),
                )
                payload = None
                if write:
                    if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                        self._json({"reason": "JSON_REQUIRED"}, HTTPStatus.UNSUPPORTED_MEDIA_TYPE)
                        return
                    length = int(self.headers.get("Content-Length", "0"))
                    if length < 2 or length > 2048:
                        self._json({"reason": "BODY_LIMIT"}, HTTPStatus.REQUEST_ENTITY_TOO_LARGE)
                        return
                    payload = json.loads(self.rfile.read(length).decode("utf-8"))
                    if not isinstance(payload, dict):
                        raise ValueError("invalid pilot preparation")
                self._json(
                    pilot_accounts_request(
                        guard,
                        authorization=self.headers.get("Authorization"),
                        data_dir=runtime.config.data_dir,
                        now=datetime.now(UTC),
                        payload=payload,
                    )
                )
            except AdminAuthenticationError:
                self._json({"reason": "ADMIN_SESSION_REQUIRED"}, HTTPStatus.UNAUTHORIZED)
            except AdminAuthorizationError:
                self._json({"reason": "ADMIN_SCOPE_REQUIRED"}, HTTPStatus.FORBIDDEN)
            except PilotAccountsConflict:
                self._json({"reason": "REVISION_CONFLICT"}, HTTPStatus.CONFLICT)
            except (ValueError, UnicodeError):
                self._json({"reason": "INVALID_PILOT_ACCOUNTS"}, HTTPStatus.BAD_REQUEST)
            except (OSError, sqlite3.Error):
                self._json({"reason": "PILOT_ACCOUNTS_UNAVAILABLE"}, HTTPStatus.SERVICE_UNAVAILABLE)

        def _staff_capacity(self, action: str | None) -> None:
            """Staff-provisioned capacity (issue #177); every write needs step-up."""
            staff = (
                None if runtime.subscriber is None else getattr(runtime.subscriber, "staff", None)
            )
            if runtime.admin_access is None or staff is None:
                self._json({"reason": "STAFF_CAPACITY_DISABLED"}, HTTPStatus.SERVICE_UNAVAILABLE)
                return
            try:
                payload: dict[str, object] | None = None
                if action is not None:
                    if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                        self._json({"reason": "JSON_REQUIRED"}, HTTPStatus.UNSUPPORTED_MEDIA_TYPE)
                        return
                    length = int(self.headers.get("Content-Length", "0"))
                    if length < 2 or length > 4096:
                        self._json({"reason": "BODY_LIMIT"}, HTTPStatus.REQUEST_ENTITY_TOO_LARGE)
                        return
                    raw = json.loads(self.rfile.read(length).decode("utf-8"))
                    if not isinstance(raw, dict):
                        raise ValueError("staff capacity request must be an object")
                    payload = raw
                query = {k: v[0] for k, v in parse_qs(urlsplit(self.path).query).items() if v}
                self._json(
                    staff_capacity_request(
                        AdminHttpAccessGuard(runtime.admin_access),
                        staff,
                        authorization=self.headers.get("Authorization"),
                        action=action or "read",
                        query=query,
                        payload=payload,
                        now=datetime.now(UTC),
                    )
                )
            except AdminAuthenticationError:
                self._json({"reason": "ADMIN_SESSION_REQUIRED"}, HTTPStatus.UNAUTHORIZED)
            except AdminAuthorizationError as error:
                reason = "STEP_UP_REQUIRED" if "step-up" in str(error) else "ADMIN_SCOPE_REQUIRED"
                self._json({"reason": reason}, HTTPStatus.FORBIDDEN)
            except StaffCapacityError as error:
                status = {
                    StaffCapacityFailure.SCOPE_REQUIRED: HTTPStatus.FORBIDDEN,
                    StaffCapacityFailure.STEP_UP_REQUIRED: HTTPStatus.FORBIDDEN,
                    StaffCapacityFailure.GRANT_NOT_FOUND: HTTPStatus.NOT_FOUND,
                    StaffCapacityFailure.TENANT_UNKNOWN: HTTPStatus.NOT_FOUND,
                    StaffCapacityFailure.IDEMPOTENCY_CONFLICT: HTTPStatus.CONFLICT,
                }.get(error.failure, HTTPStatus.BAD_REQUEST)
                self._json({"reason": error.failure.value, "detail": str(error)}, status)
            except PortfolioError as error:
                self._json({"reason": error.failure.value}, HTTPStatus.CONFLICT)
            except (ValueError, UnicodeError):
                self._json({"reason": "INVALID_STAFF_CAPACITY_REQUEST"}, HTTPStatus.BAD_REQUEST)
            except (OSError, sqlite3.Error):
                self._json({"reason": "STAFF_CAPACITY_UNAVAILABLE"}, HTTPStatus.SERVICE_UNAVAILABLE)

        def _subscriber(self, method: str, path: str) -> None:
            if runtime.subscriber is None:
                self._json(
                    {"state": "rejected", "code": "SUBSCRIBER_RUNTIME_DISABLED"},
                    HTTPStatus.SERVICE_UNAVAILABLE,
                )
                return
            for name in ("Origin", "Authorization", "Content-Length", "Content-Type"):
                if len(self.headers.get_all(name, [])) > 1:
                    self._json(
                        {"state": "rejected", "code": "AMBIGUOUS_HEADERS"}, HTTPStatus.BAD_REQUEST
                    )
                    return
            payload: dict[str, object] | None = None
            if method == "POST":
                if self.headers.get("Transfer-Encoding") is not None:
                    self._json(
                        {"state": "rejected", "code": "TRANSFER_ENCODING_REJECTED"},
                        HTTPStatus.BAD_REQUEST,
                    )
                    return
                if self.headers.get("Content-Type", "").split(";")[0].strip() != "application/json":
                    self._json(
                        {"state": "rejected", "code": "JSON_REQUIRED"},
                        HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
                    )
                    return
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    if not 0 < length <= 8192:
                        self._json(
                            {"state": "rejected", "code": "BODY_LIMIT"},
                            HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                        )
                        return
                    self.connection.settimeout(10)
                    raw_body = self.rfile.read(length)
                    if len(raw_body) != length:
                        raise ValueError("truncated body")
                    decoded = json.loads(raw_body.decode("utf-8"))
                    if not isinstance(decoded, dict) or any(
                        not isinstance(key, str) for key in decoded
                    ):
                        raise ValueError("invalid payload")
                    payload = decoded
                except (ValueError, UnicodeError, OSError):
                    self._json(
                        {"state": "rejected", "code": "INVALID_REQUEST"}, HTTPStatus.BAD_REQUEST
                    )
                    return
            try:
                result = runtime.subscriber.handle(
                    method, path, dict(self.headers.items()), payload
                )
                self._json(result.body, HTTPStatus(result.status))
            except Exception:
                # Internal failures must not disclose SQLite paths, tokens or user input.
                self._json(
                    {"state": "rejected", "code": "SUBSCRIBER_RUNTIME_UNAVAILABLE"},
                    HTTPStatus.SERVICE_UNAVAILABLE,
                )

        def _subscriber_stripe_webhook(self) -> None:
            if runtime.subscriber is None:
                self._json(
                    {"accepted": False, "disposition": "NOT_CONFIGURED"},
                    HTTPStatus.SERVICE_UNAVAILABLE,
                )
                return
            try:
                for name in ("Stripe-Signature", "Content-Length", "Content-Type"):
                    if len(self.headers.get_all(name, [])) != 1:
                        raise ValueError("ambiguous webhook header")
                if self.headers.get("Transfer-Encoding") is not None:
                    raise ValueError("unsupported transport")
                if self.headers.get("Content-Type", "").split(";")[0].strip() != "application/json":
                    raise ValueError("JSON required")
                length = int(self.headers["Content-Length"])
                signature = self.headers["Stripe-Signature"]
                if not 0 < length <= 1_000_000 or not signature or len(signature) > 4096:
                    raise ValueError("webhook bounds")
                self.connection.settimeout(10)
                raw = self.rfile.read(length)
                if len(raw) != length:
                    raise ValueError("truncated body")
                result = runtime.subscriber.handle_webhook(raw, signature)
                self._json(result.body, HTTPStatus(result.status))
            except (ValueError, UnicodeError):
                self._json(
                    {"accepted": False, "disposition": "INVALID_REQUEST"}, HTTPStatus.BAD_REQUEST
                )
            except Exception:
                self._json(
                    {"accepted": False, "disposition": "INGRESS_UNAVAILABLE"},
                    HTTPStatus.SERVICE_UNAVAILABLE,
                )

        def _operation_endpoint_id(self) -> str | None:
            path = urlsplit(self.path).path
            exact = {
                "/healthz": "public.healthz",
                "/runtimez": "public.runtimez",
                "/api/acquisition/events": "public.acquisition.events",
                "/api/weekly-brief/requests": "public.weekly-brief.requests",
                "/internal/webhooks/stripe": "internal.stripe.webhook",
            }
            if path in exact:
                return exact[path]
            if _admin_slug(path) is not None:
                return "admin.shell"
            return None

        def _observe_http(self, status: HTTPStatus) -> None:
            endpoint_id = self._operation_endpoint_id()
            if endpoint_id is None:
                return
            started = getattr(self, "_request_started_ns", None)
            latency_ms = (
                None
                if started is None
                else max(0, (time.perf_counter_ns() - int(started)) // 1_000_000)
            )
            with contextlib.suppress(Exception):
                runtime.admin_api_operations_store.append_observation(
                    ApiOperationObservation(
                        observation_id=f"apiobs:{secrets.token_hex(12)}",
                        endpoint_id=endpoint_id,
                        occurred_at=datetime.now(UTC),
                        latency_ms=latency_ms,
                        status_code=status.value,
                        error_category=None if status.value < 400 else f"HTTP_{status.value}",
                    )
                )

        def _json(self, payload: dict[str, object], status: HTTPStatus = HTTPStatus.OK) -> None:
            encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(encoded)
            self._observe_http(status)

        def _html(self, data: bytes, status: HTTPStatus = HTTPStatus.OK) -> None:
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'",
            )
            self.end_headers()
            self.wfile.write(data)
            self._observe_http(status)

        def _admin_error(self, status: HTTPStatus, message: str) -> None:
            encoded = (
                "<!doctype html><meta charset='utf-8'><title>AXIGNAL Admin</title>"
                f"<h1>{status.value}</h1><p>{message}</p>"
            ).encode()
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            if status is HTTPStatus.UNAUTHORIZED:
                self.send_header("WWW-Authenticate", 'Bearer realm="AXIGNAL Admin"')
            self.end_headers()
            self.wfile.write(encoded)

        def _static(self, path: Path) -> None:
            try:
                data = path.read_bytes()
            except (OSError, ValueError):
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self) -> None:
            self._request_started_ns = time.perf_counter_ns()
            request_path = urlsplit(self.path).path
            if ProductMcpHttp.handles(request_path):
                self._product_mcp("GET")
                return
            if is_subscriber_path(request_path):
                self._subscriber("GET", request_path)
                return
            if request_path == "/healthz":
                payload = runtime.health_payload()
                status = (
                    HTTPStatus.OK if payload["status"] == "ok" else HTTPStatus.SERVICE_UNAVAILABLE
                )
                self._json(payload, status)
                return
            if request_path == "/runtimez":
                payload = runtime.health_payload(detailed=True)
                payload["capabilities"] = {
                    "observation_memory": "sqlite-append-only",
                    "learning_memory": "sqlite-append-only",
                    "first_xeed_runtime": "application-contract-loaded",
                    "public_write_api": False,
                    "canonical_economic_write_api": False,
                    "public_service_request_api": True,
                    "loopback_first_proof_api": runtime.first_proof is not None,
                }
                self._json(payload)
                return
            admin_slug = _admin_slug(request_path)
            if admin_slug is not None:
                if runtime.admin_access is None:
                    self.send_error(HTTPStatus.NOT_FOUND)
                    return
                authorization = self.headers.get("Authorization")
                if authorization is None:
                    self._admin_error(HTTPStatus.UNAUTHORIZED, "Admin authentication required.")
                    return
                scheme, separator, token = authorization.partition(" ")
                if separator != " " or scheme != "Bearer" or not token.strip():
                    self._admin_error(
                        HTTPStatus.UNAUTHORIZED, "Invalid Admin authorization credential."
                    )
                    return
                try:
                    grant = runtime.admin_access.session_grant(token.strip(), now=datetime.now(UTC))
                    admin_projection = project_admin_shell(grant, requested_slug=admin_slug or None)
                    now = datetime.now(UTC)
                    command_center = (
                        _command_center_projection(runtime, now=now)
                        if admin_projection.current_slug == "command-center"
                        else None
                    )
                    xeed_observatory = (
                        _xeed_observatory_projection(runtime, now=now)
                        if admin_projection.current_slug in {"xeeds", "axigland-quality"}
                        else None
                    )
                    brain_observatory = (
                        _brain_observatory_projection(runtime, now=now)
                        if admin_projection.current_slug == "axent-brain"
                        else None
                    )
                    governance = (
                        _governance_projection(runtime, now=now)
                        if admin_projection.current_slug == "governance"
                        else None
                    )
                    acquisition = (
                        _acquisition_projection(runtime, grant=grant, now=now)
                        if admin_projection.current_slug == "acquisition"
                        else None
                    )
                    gsc = (
                        _gsc_projection(runtime, now=now)
                        if admin_projection.current_slug == "acquisition"
                        else None
                    )
                    commercial = (
                        _commercial_projection(runtime, grant=grant, now=now)
                        if admin_projection.current_slug == "customers-crm"
                        else None
                    )
                    customer_operations = (
                        _customer_operations_projection(runtime, grant=grant, now=now)
                        if admin_projection.current_slug == "customers-crm"
                        else None
                    )
                    integrations = (
                        _integration_projection(runtime, grant=grant, now=now)
                        if admin_projection.current_slug == "integrations"
                        else None
                    )
                    api_operations = (
                        _api_operations_projection(runtime, grant=grant, now=now)
                        if admin_projection.current_slug == "integrations"
                        else None
                    )
                    financial_documents = (
                        _financial_document_projection(runtime, grant=grant, now=now)
                        if admin_projection.current_slug == "finance-fiscal"
                        else None
                    )
                    accounting_reconciliation = (
                        _accounting_reconciliation_projection(runtime, grant=grant, now=now)
                        if admin_projection.current_slug == "finance-fiscal"
                        else None
                    )
                    fiscal_compliance = (
                        _fiscal_compliance_projection(runtime, grant=grant, now=now)
                        if admin_projection.current_slug == "finance-fiscal"
                        else None
                    )
                    tax_operations = (
                        _tax_operations_projection(runtime, grant=grant, now=now)
                        if admin_projection.current_slug == "finance-fiscal"
                        else None
                    )
                    measurement_registry = (
                        _measurement_registry_projection(runtime, grant=grant, now=now)
                        if admin_projection.current_slug == "frontier-advisor"
                        else None
                    )
                    rendered = _render_admin_shell(
                        runtime.config.web_root,
                        admin_projection,
                        command_center=command_center,
                        xeed_observatory=xeed_observatory,
                        brain_observatory=brain_observatory,
                        governance=governance,
                        acquisition=acquisition,
                        gsc=gsc,
                        commercial=commercial,
                        customer_operations=customer_operations,
                        integrations=integrations,
                        api_operations=api_operations,
                        financial_documents=financial_documents,
                        accounting_reconciliation=accounting_reconciliation,
                        fiscal_compliance=fiscal_compliance,
                        tax_operations=tax_operations,
                        measurement_registry=measurement_registry,
                    )
                except AdminAuthenticationError:
                    self._admin_error(HTTPStatus.UNAUTHORIZED, "Admin authentication failed.")
                    return
                except (AdminAuthorizationError, AdminShellRouteDenied):
                    self._admin_error(HTTPStatus.FORBIDDEN, "Admin scope denied for this domain.")
                    return
                except AdminShellRouteUnknown:
                    self.send_error(HTTPStatus.NOT_FOUND)
                    return
                except (OSError, RuntimeError):
                    self.send_error(HTTPStatus.SERVICE_UNAVAILABLE)
                    return
                self._html(rendered)
                return
            if request_path in {"/api/contact/status", "/api/gdpr/status"}:
                self._json(
                    public_request_status(
                        data_dir=runtime.config.data_dir,
                        environment=runtime.config.environment,
                        env=os.environ,
                        kind="CONTACT"
                        if request_path == "/api/contact/status"
                        else "PRIVACY_RIGHTS",
                    )
                )
                return
            if request_path == "/api/weekly-brief/status":
                self._json({"enabled": runtime.config.weekly_brief_requests_enabled})
                return
            if request_path == "/api/acquisition/status":
                self._json(
                    {
                        "enabled": runtime.config.acquisition_events_enabled,
                        "model": "OBSERVED_TOUCH_V1",
                    }
                )
                return
            if request_path == "/internal/admin/customer-zero/access":
                customer_zero_grant = self._customer_zero_authority()
                if customer_zero_grant is None:
                    return
                self._json(
                    {
                        "authorized": True,
                        "canObserve": AdminScope.RESEARCH_OPERATE in customer_zero_grant.scopes,
                    }
                )
                return
            if request_path == "/internal/admin/pilot-test-accounts":
                self._pilot_accounts()
                return
            if request_path == STAFF_CAPACITY_ROUTE:
                self._staff_capacity(None)
                return
            if request_path == "/api/subscriber-context":
                reading_grant = None
                if runtime.admin_access is not None:
                    reading_grant = self._customer_zero_authority()
                    if reading_grant is None:
                        return
                if runtime.first_proof is None:
                    self._json({"state": "NO_XEED", "realityLevel": "LIVE_PRODUCTION_FIRST_PROOF"})
                    return
                projection = (
                    runtime.organization_attention.projection(str(reading_grant.principal_id))
                    if runtime.organization_attention is not None and reading_grant is not None
                    else runtime.first_proof.current_projection()
                )
                if projection is None:
                    self._json({"state": "NO_XEED", "realityLevel": "LIVE_PRODUCTION_FIRST_PROOF"})
                else:
                    self._json(projection)
                return
            if request_path == "/api/organizations":
                inventory_grant = self._customer_zero_authority()
                if inventory_grant is None:
                    return
                if runtime.organization_attention is None:
                    self._json(
                        {"state": "failure", "reason": "RUNTIME_NOT_CONFIGURED"},
                        HTTPStatus.SERVICE_UNAVAILABLE,
                    )
                    return
                self._json(
                    runtime.organization_attention.inventory(
                        str(inventory_grant.principal_id),
                        can_observe=AdminScope.RESEARCH_OPERATE in inventory_grant.scopes,
                    )
                )
                return
            static_path = _resolve_static(runtime.config.web_root, request_path)
            if static_path is None or not static_path.is_file():
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            self._static(static_path)

        def do_POST(self) -> None:
            self._request_started_ns = time.perf_counter_ns()
            request_path = urlsplit(self.path).path
            if request_path in {"/api/contact", "/api/privacy/request"}:
                expected_origin = os.getenv("AXIGNAL_EXPERIENCE_ORIGIN") or (
                    "https://axignal.com"
                    if runtime.config.environment == "production"
                    else "http://127.0.0.1:3810"
                )
                if self.headers.get("Origin") != expected_origin:
                    self.close_connection = True
                    self._json(
                        {"status": "rejected", "reason": "ORIGIN_REJECTED"}, HTTPStatus.FORBIDDEN
                    )
                    return
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    if not 2 <= length <= 16384:
                        raise ValueError("size")
                    if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                        raise ValueError("type")
                    payload = json.loads(self.rfile.read(length).decode("utf-8"))
                except (ValueError, UnicodeDecodeError):
                    self.close_connection = True
                    self._json(
                        {"status": "rejected", "reason": "INVALID_REQUEST"}, HTTPStatus.BAD_REQUEST
                    )
                    return
                status, receipt = submit_public_request(
                    data_dir=runtime.config.data_dir,
                    environment=runtime.config.environment,
                    payload=payload,
                    kind="CONTACT" if request_path == "/api/contact" else "PRIVACY_RIGHTS",
                )
                self._json(receipt, HTTPStatus(status))
                return
            if ProductMcpHttp.handles(request_path):
                self._product_mcp("POST")
                return
            if request_path == "/internal/admin/pilot-test-accounts":
                self._pilot_accounts(write=True)
                return
            if request_path.startswith(STAFF_CAPACITY_ROUTE + "/") and request_path.count("/") == 4:
                self._staff_capacity(request_path.rsplit("/", 1)[1])
                return
            if request_path == "/internal/webhooks/subscriber-stripe":
                self._subscriber_stripe_webhook()
                return
            if is_subscriber_path(request_path):
                self._subscriber("POST", request_path)
                return
            weekly_brief_prefix = "/internal/admin/weekly-brief/issues"
            if request_path == weekly_brief_prefix or request_path.startswith(
                weekly_brief_prefix + "/"
            ):
                if runtime.admin_access is None:
                    self.send_error(HTTPStatus.NOT_FOUND)
                    return
                authorization = self.headers.get("Authorization")
                if authorization is None:
                    self._admin_error(HTTPStatus.UNAUTHORIZED, "Admin authentication required.")
                    return
                scheme, auth_separator, token = authorization.partition(" ")
                if auth_separator != " " or scheme != "Bearer" or not token.strip():
                    self._admin_error(
                        HTTPStatus.UNAUTHORIZED, "Invalid Admin authorization credential."
                    )
                    return
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                except ValueError:
                    length = 0
                if length < 2 or length > 16384:
                    self._json(
                        {"status": "rejected", "reason": "INVALID_REQUEST_SIZE"},
                        HTTPStatus.BAD_REQUEST,
                    )
                    return
                try:
                    payload = json.loads(self.rfile.read(length).decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    self._json(
                        {"status": "rejected", "reason": "INVALID_JSON"},
                        HTTPStatus.BAD_REQUEST,
                    )
                    return
                if not isinstance(payload, dict):
                    self._json(
                        {"status": "rejected", "reason": "INVALID_REQUEST"},
                        HTTPStatus.BAD_REQUEST,
                    )
                    return
                try:
                    now = datetime.now(UTC)
                    grant = runtime.admin_access.session_grant(token.strip(), now=now)
                    if (
                        AdminScope.ACQUISITION_WRITE not in grant.scopes
                        or grant.assurance is not AdminAssurance.STEP_UP
                    ):
                        raise PermissionError("weekly brief mutation requires acquisition STEP_UP")
                    if request_path == weekly_brief_prefix:
                        raw_candidates = payload.get("candidates", [])
                        if not isinstance(raw_candidates, list):
                            raise ValueError("weekly brief candidates must be a list")
                        candidates = tuple(
                            MaterialObservationCandidate(
                                observation_id=str(item["observationId"]),
                                why_may_matter=str(item["whyMayMatter"]),
                                unknowns=tuple(str(value) for value in item["unknowns"]),
                            )
                            for item in raw_candidates
                            if isinstance(item, dict) and isinstance(item.get("unknowns"), list)
                        )
                        if len(candidates) != len(raw_candidates):
                            raise ValueError("weekly brief candidate structure is invalid")
                        issue = compose_issue(
                            store=runtime.admin_weekly_brief_store,
                            acquisition_store=runtime.admin_acquisition_store,
                            observation_memory=runtime.observation_memory,
                            request_id=str(payload.get("requestId", "")),
                            issue_id=str(payload.get("issueId", "")),
                            issue_version=str(payload.get("issueVersion", "")),
                            candidates=candidates,
                            currentness_policy=WEEKLY_BRIEF_PILOT_CURRENTNESS_POLICY,
                            now=now,
                        )
                        self._json(
                            {
                                "status": "composed",
                                "issueId": issue.issue_id,
                                "kind": issue.kind.value,
                                "itemCount": len(issue.items),
                                "evidenceFingerprint": issue.evidence_fingerprint,
                                "humanApprovalRequired": True,
                            },
                            HTTPStatus.CREATED,
                        )
                        return

                    tail = request_path[len(weekly_brief_prefix) + 1 :]
                    encoded_issue_id, separator, action = tail.rpartition("/")
                    if (
                        separator != "/"
                        or not encoded_issue_id
                        or action not in {"approve", "correct"}
                    ):
                        self.send_error(HTTPStatus.NOT_FOUND)
                        return
                    issue_id = unquote(encoded_issue_id)
                    if action == "approve":
                        approval = approve_issue(
                            store=runtime.admin_weekly_brief_store,
                            grant=grant,
                            issue_id=issue_id,
                            now=now,
                        )
                        self._json(
                            {
                                "status": "approved",
                                "issueId": approval.issue_id,
                                "reviewerPrincipalId": approval.reviewer_principal_id,
                                "approvedAt": approval.approved_at.isoformat(),
                            }
                        )
                        return
                    correction = append_correction(
                        store=runtime.admin_weekly_brief_store,
                        grant=grant,
                        correction_id=str(payload.get("correctionId", "")),
                        issue_id=issue_id,
                        reason=str(payload.get("reason", "")),
                        note=str(payload.get("note", "")),
                        now=now,
                    )
                    self._json(
                        {
                            "status": "corrected",
                            "issueId": correction.issue_id,
                            "correctionId": correction.correction_id,
                            "occurredAt": correction.occurred_at.isoformat(),
                        }
                    )
                    return
                except AdminAuthenticationError:
                    self._admin_error(HTTPStatus.UNAUTHORIZED, "Admin authentication failed.")
                    return
                except (AdminAuthorizationError, PermissionError):
                    self._admin_error(
                        HTTPStatus.FORBIDDEN,
                        "Admin scope, consent or assurance denied for this action.",
                    )
                    return
                except LookupError:
                    self.send_error(HTTPStatus.NOT_FOUND)
                    return
                except (KeyError, TypeError, ValueError):
                    self._json(
                        {"status": "rejected", "reason": "WEEKLY_BRIEF_STATE_CONFLICT"},
                        HTTPStatus.CONFLICT,
                    )
                    return

            acquisition_admin_prefix = "/internal/admin/acquisition/requests/"
            if request_path.startswith(acquisition_admin_prefix):
                if runtime.admin_access is None:
                    self.send_error(HTTPStatus.NOT_FOUND)
                    return
                tail = request_path[len(acquisition_admin_prefix) :]
                encoded_request_id, separator, action = tail.rpartition("/")
                if (
                    separator != "/"
                    or not encoded_request_id
                    or action not in {"accept", "decline", "clarify", "suppress"}
                ):
                    self.send_error(HTTPStatus.NOT_FOUND)
                    return
                authorization = self.headers.get("Authorization")
                if authorization is None:
                    self._admin_error(HTTPStatus.UNAUTHORIZED, "Admin authentication required.")
                    return
                scheme, auth_separator, token = authorization.partition(" ")
                if auth_separator != " " or scheme != "Bearer" or not token.strip():
                    self._admin_error(
                        HTTPStatus.UNAUTHORIZED, "Invalid Admin authorization credential."
                    )
                    return
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                except ValueError:
                    length = 0
                if length < 2 or length > 8192:
                    self._json(
                        {"status": "rejected", "reason": "INVALID_REQUEST_SIZE"},
                        HTTPStatus.BAD_REQUEST,
                    )
                    return
                try:
                    payload = json.loads(self.rfile.read(length).decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    self._json(
                        {"status": "rejected", "reason": "INVALID_JSON"},
                        HTTPStatus.BAD_REQUEST,
                    )
                    return
                if not isinstance(payload, dict):
                    self._json(
                        {"status": "rejected", "reason": "INVALID_REQUEST"},
                        HTTPStatus.BAD_REQUEST,
                    )
                    return
                try:
                    grant = runtime.admin_access.session_grant(token.strip(), now=datetime.now(UTC))
                    request_id = unquote(encoded_request_id)
                    reason = str(payload.get("reason", "")).strip()
                    now = datetime.now(UTC)
                    if action == "accept":
                        snapshot = AdminBriefReviewService(runtime.admin_acquisition_store).accept(
                            grant=grant,
                            request_id=request_id,
                            subject_reference=str(payload.get("subjectReference", "")),
                            reason=reason,
                            now=now,
                        )
                    elif action == "decline":
                        snapshot = AdminBriefReviewService(runtime.admin_acquisition_store).decline(
                            grant=grant,
                            request_id=request_id,
                            reason=reason,
                            now=now,
                        )
                    elif action == "clarify":
                        snapshot = AdminBriefLifecycleService(
                            runtime.admin_acquisition_store
                        ).require_clarification(
                            grant=grant,
                            request_id=request_id,
                            reason=reason,
                            now=now,
                        )
                    else:
                        snapshot = AdminBriefLifecycleService(
                            runtime.admin_acquisition_store
                        ).block_delivery(
                            grant=grant,
                            request_id=request_id,
                            reason=reason,
                            now=now,
                        )
                except AdminAuthenticationError:
                    self._admin_error(HTTPStatus.UNAUTHORIZED, "Admin authentication failed.")
                    return
                except (AdminAuthorizationError, PermissionError):
                    self._admin_error(
                        HTTPStatus.FORBIDDEN, "Admin scope or assurance denied for this action."
                    )
                    return
                except LookupError:
                    self.send_error(HTTPStatus.NOT_FOUND)
                    return
                except ValueError:
                    self._json(
                        {"status": "rejected", "reason": "ACQUISITION_STATE_CONFLICT"},
                        HTTPStatus.CONFLICT,
                    )
                    return
                self._json(
                    {
                        "status": "accepted",
                        "requestId": str(snapshot.request_id),
                        "reviewState": snapshot.review_state.value,
                        "coverageState": snapshot.coverage_state.value,
                        "consentState": snapshot.consent_state.value,
                        "deliveryEligible": snapshot.delivery_eligible,
                    }
                )
                return
            if request_path == "/api/acquisition/events":
                if not runtime.config.acquisition_events_enabled:
                    self.send_error(HTTPStatus.NOT_FOUND)
                    return
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                except ValueError:
                    length = 0
                if length < 2 or length > 8192:
                    self._json(
                        {"status": "rejected", "reason": "INVALID_REQUEST_SIZE"},
                        HTTPStatus.BAD_REQUEST,
                    )
                    return
                try:
                    payload = json.loads(self.rfile.read(length).decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    self._json(
                        {"status": "rejected", "reason": "INVALID_JSON"},
                        HTTPStatus.BAD_REQUEST,
                    )
                    return
                if not isinstance(payload, dict):
                    self._json(
                        {"status": "rejected", "reason": "INVALID_REQUEST"},
                        HTTPStatus.BAD_REQUEST,
                    )
                    return
                forbidden = {
                    "email",
                    "professionalEmail",
                    "companyName",
                    "companyDomain",
                    "purpose",
                    "name",
                    "userId",
                    "principalId",
                }
                if forbidden.intersection(payload):
                    self._json(
                        {"status": "rejected", "reason": "PII_NOT_ALLOWED"},
                        HTTPStatus.BAD_REQUEST,
                    )
                    return
                try:
                    kind = MarketingEventKind(str(payload.get("kind", "")))
                    occurred_at = datetime.fromisoformat(str(payload.get("occurredAt", "")))
                    inserted = PublicMarketingEventService(runtime.admin_acquisition_store).ingest(
                        event_id=str(payload.get("eventId", "")),
                        session_ref=str(payload.get("sessionRef", "")),
                        kind=kind,
                        occurred_at=occurred_at,
                        received_at=datetime.now(UTC),
                        surface=str(payload.get("surface", "landing")),
                        locale=str(payload.get("locale", "en")),
                        path=str(payload.get("path", "/")),
                        chapter=(
                            int(payload["chapter"]) if payload.get("chapter") is not None else None
                        ),
                        cta=(str(payload["cta"]) if payload.get("cta") is not None else None),
                        referrer=(
                            str(payload["referrer"])
                            if payload.get("referrer") is not None
                            else None
                        ),
                        utm_source=(
                            str(payload["utmSource"])
                            if payload.get("utmSource") is not None
                            else None
                        ),
                        utm_medium=(
                            str(payload["utmMedium"])
                            if payload.get("utmMedium") is not None
                            else None
                        ),
                        utm_campaign=(
                            str(payload["utmCampaign"])
                            if payload.get("utmCampaign") is not None
                            else None
                        ),
                        utm_content=(
                            str(payload["utmContent"])
                            if payload.get("utmContent") is not None
                            else None
                        ),
                        utm_term=(
                            str(payload["utmTerm"]) if payload.get("utmTerm") is not None else None
                        ),
                    )
                except (TypeError, ValueError):
                    self._json(
                        {"status": "rejected", "reason": "INVALID_MARKETING_EVENT"},
                        HTTPStatus.BAD_REQUEST,
                    )
                    return
                self._json(
                    {"status": "accepted", "replayed": not inserted},
                    HTTPStatus.ACCEPTED,
                )
                return
            if request_path == "/api/weekly-brief/requests":
                if not runtime.config.weekly_brief_requests_enabled:
                    self.send_error(HTTPStatus.NOT_FOUND)
                    return
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                except ValueError:
                    length = 0
                if length < 2 or length > 16_384:
                    self._json(
                        {"status": "rejected", "reason": "INVALID_REQUEST_SIZE"},
                        HTTPStatus.BAD_REQUEST,
                    )
                    return
                try:
                    payload = json.loads(self.rfile.read(length).decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    self._json(
                        {"status": "rejected", "reason": "INVALID_JSON"},
                        HTTPStatus.BAD_REQUEST,
                    )
                    return
                if not isinstance(payload, dict):
                    self._json(
                        {"status": "rejected", "reason": "INVALID_REQUEST"},
                        HTTPStatus.BAD_REQUEST,
                    )
                    return
                if payload.get("requestProcessingAcknowledged") is not True:
                    self._json(
                        {"status": "rejected", "reason": "REQUEST_NOTICE_REQUIRED"},
                        HTTPStatus.BAD_REQUEST,
                    )
                    return
                if payload.get("requestNoticeVersion") != "weekly-brief-request-v1":
                    self._json(
                        {"status": "rejected", "reason": "REQUEST_NOTICE_VERSION_INVALID"},
                        HTTPStatus.BAD_REQUEST,
                    )
                    return
                if (
                    payload.get("newsletterConsent") is True
                    and payload.get("newsletterNoticeVersion") != "weekly-newsletter-consent-v1"
                ):
                    self._json(
                        {"status": "rejected", "reason": "NEWSLETTER_NOTICE_VERSION_INVALID"},
                        HTTPStatus.BAD_REQUEST,
                    )
                    return
                try:
                    snapshot = PublicBriefRequestService(runtime.admin_acquisition_store).submit(
                        request_id=f"brief:{secrets.token_hex(12)}",
                        company_name=str(payload.get("companyName", "")),
                        company_domain=str(payload.get("companyDomain", "")),
                        professional_email=str(payload.get("professionalEmail", "")),
                        purpose=str(payload.get("purpose", "")),
                        request_notice_version=str(payload.get("requestNoticeVersion", "")),
                        newsletter_consent=payload.get("newsletterConsent") is True,
                        newsletter_notice_version=(
                            str(payload["newsletterNoticeVersion"])
                            if payload.get("newsletterConsent") is True
                            and payload.get("newsletterNoticeVersion") is not None
                            else None
                        ),
                        now=datetime.now(UTC),
                    )
                except ValueError:
                    self._json(
                        {"status": "rejected", "reason": "INVALID_REQUEST"},
                        HTTPStatus.BAD_REQUEST,
                    )
                    return
                if runtime.config.acquisition_events_enabled:
                    session_ref = payload.get("acquisitionSessionRef")
                    if isinstance(session_ref, str) and session_ref:
                        linked_at = datetime.now(UTC)
                        with contextlib.suppress(ValueError):
                            PublicMarketingEventService(
                                runtime.admin_acquisition_store
                            ).link_brief_request(
                                event_id=f"mkt:req:{secrets.token_hex(12)}",
                                session_ref=session_ref,
                                request_id=str(snapshot.request_id),
                                occurred_at=linked_at,
                                received_at=linked_at,
                                surface="landing",
                                locale=str(payload.get("acquisitionLocale", "en")),
                                path=str(payload.get("acquisitionPath", "/")),
                            )
                self._json(
                    {
                        "status": "received",
                        "requestId": str(snapshot.request_id),
                        "reviewState": snapshot.review_state.value,
                    },
                    HTTPStatus.ACCEPTED,
                )
                return
            if request_path == "/internal/webhooks/stripe":
                if runtime.stripe_webhook is None:
                    self.send_error(HTTPStatus.NOT_FOUND)
                    return
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                except ValueError:
                    length = 0
                if length < 1 or length > 1_048_576:
                    self._json(
                        {"status": "rejected", "reason": "INVALID_REQUEST_SIZE"},
                        HTTPStatus.BAD_REQUEST,
                    )
                    return
                signature = self.headers.get("Stripe-Signature", "")
                if not signature:
                    self._json(
                        {"status": "rejected", "reason": "MISSING_STRIPE_SIGNATURE"},
                        HTTPStatus.BAD_REQUEST,
                    )
                    return
                payload = self.rfile.read(length)
                try:
                    result = runtime.stripe_webhook.handle(
                        payload=payload,
                        signature_header=signature,
                        received_at=datetime.now(UTC),
                    )
                except StripeWebhookDependencyError:
                    self._json(
                        {"status": "retry", "reason": "STRIPE_DEPENDENCY_NOT_READY"},
                        HTTPStatus.SERVICE_UNAVAILABLE,
                    )
                    return
                except StripeWebhookError:
                    self._json(
                        {"status": "rejected", "reason": "INVALID_STRIPE_WEBHOOK"},
                        HTTPStatus.BAD_REQUEST,
                    )
                    return
                except LookupError:
                    self._json(
                        {"status": "retry", "reason": "BILLING_ACCOUNT_NOT_READY"},
                        HTTPStatus.SERVICE_UNAVAILABLE,
                    )
                    return
                except ValueError:
                    self._json(
                        {"status": "rejected", "reason": "BILLING_CONTRACT_CONFLICT"},
                        HTTPStatus.CONFLICT,
                    )
                    return
                self._json(
                    {
                        "status": "accepted",
                        "eventId": result.event_id,
                        "replayed": result.replayed,
                    }
                )
                return
            if request_path == "/api/xeeds" and runtime.first_proof is not None:
                if self.command != "POST":
                    self._json(
                        {"status": "rejected", "reason": "METHOD_NOT_ALLOWED"},
                        HTTPStatus.METHOD_NOT_ALLOWED,
                    )
                    return
                command_grant = None
                if runtime.admin_access is not None:
                    command_grant = self._customer_zero_authority(write=True)
                    if command_grant is None:
                        return
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                except ValueError:
                    length = 0
                if length < 1 or length > 8192:
                    self._json(
                        {"status": "rejected", "reason": "INVALID_REQUEST_SIZE"},
                        HTTPStatus.BAD_REQUEST,
                    )
                    return
                try:
                    payload = json.loads(self.rfile.read(length).decode("utf-8"))
                    if not isinstance(payload, dict):
                        raise ValueError("body must be an object")
                    if not all(isinstance(value, str) for value in payload.values()):
                        raise ValueError("INVALID_COMMAND_FIELDS")
                    if "action" in payload:
                        if command_grant is None or runtime.organization_attention is None:
                            raise ValueError("INTERNAL_ATTENTION_AUTHORITY_REQUIRED")
                        principal = str(command_grant.principal_id)
                        action = payload["action"]
                        if action == "add" and set(payload) == {"action", "name", "targetUri"}:
                            projection = runtime.organization_attention.add(
                                principal, payload["name"], payload["targetUri"]
                            )
                        elif action == "select" and set(payload) == {"action", "id"}:
                            projection = runtime.organization_attention.select(
                                principal, payload["id"]
                            )
                        elif action == "reobserve" and set(payload) == {"action", "id"}:
                            projection = runtime.organization_attention.reobserve(
                                principal, payload["id"]
                            )
                        else:
                            raise ValueError("INVALID_ATTENTION_COMMAND")
                    else:
                        if set(payload) != {"label", "targetUri"}:
                            raise ValueError("INVALID_LEGACY_COMMAND")
                        projection = runtime.first_proof.plant(
                            label=payload["label"], target_uri=payload["targetUri"]
                        )
                        if command_grant is not None and runtime.organization_attention is not None:
                            runtime.organization_attention.record_legacy(
                                str(command_grant.principal_id), projection
                            )
                except ValueError as exc:
                    self._json({"status": "rejected", "reason": str(exc)}, HTTPStatus.BAD_REQUEST)
                    return
                except FirstProofInsufficientEvidence as exc:
                    self._json(
                        {"state": "INSUFFICIENT_EVIDENCE", "reason": str(exc)},
                        HTTPStatus.UNPROCESSABLE_ENTITY,
                    )
                    return
                except Exception as exc:
                    self._json(
                        {"status": "failed", "reason": f"FIRST_PROOF_FAILED:{type(exc).__name__}"},
                        HTTPStatus.BAD_GATEWAY,
                    )
                    return
                self._json(
                    projection,
                    HTTPStatus.ACCEPTED
                    if projection.get("state") == "IDENTITY_UNRESOLVED"
                    else HTTPStatus.CREATED,
                )
                return
            self._json(
                {"status": "rejected", "reason": "PUBLIC_WRITE_SURFACE_CLOSED"},
                HTTPStatus.METHOD_NOT_ALLOWED,
            )

        do_PUT = do_POST
        do_PATCH = do_POST

    return Handler


def serve(runtime: AxignalRuntime) -> None:
    handler = make_handler(runtime)
    from pipeline.public_requests.sqlite_store import SqlitePublicRequestStore

    store = SqlitePublicRequestStore(runtime.config.data_dir / "public-requests.sqlite3")

    class PublicRequestRetentionServer(ThreadingHTTPServer):
        last_purge = 0.0

        def service_actions(self) -> None:
            if time.monotonic() - self.last_purge >= 3600:
                self.last_purge = time.monotonic()
                # A private queue storage outage must not stop the HTTP runtime.
                with contextlib.suppress(sqlite3.Error):
                    store.purge(now=datetime.now(UTC))

    with PublicRequestRetentionServer(
        (runtime.config.bind_host, runtime.config.port), handler
    ) as server:
        server.serve_forever()
