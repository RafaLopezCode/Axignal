"""AXIGNAL HTTP runtime composition root.

The public HTTP surface is deliberately read-only. Canonical/business writes stay
behind governed application services and are not exposed by this host.
"""

from __future__ import annotations

import html
import json
import mimetypes
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

from application.admin_access import (
    AdminAccessService,
    AdminAuthenticationError,
    AdminAuthorizationError,
)
from application.admin_command_center import COMMAND_CENTER_METRICS, project_command_center
from application.admin_shell import (
    AdminShellProjection,
    AdminShellRouteDenied,
    AdminShellRouteUnknown,
    project_admin_shell,
)
from application.admin_xeed_observatory import project_xeed_axigland_observatory
from domain.admin_command_center import AdminCommandCenterProjection
from domain.admin_observability import AdminProjectionId, AdminProjectionSnapshot
from domain.admin_xeed_observatory import XeedAxiglandObservatory
from pipeline.admin_observability import SqliteAdminObservabilityStore
from pipeline.learning_memory import SqliteLearningMemory
from pipeline.observation_memory import SqliteObservationMemory
from tools.runtime.config import RuntimeConfig
from tools.runtime.first_proof import (
    FirstProofInsufficientEvidence,
    FirstProofService,
    FirstProofStore,
)


@dataclass(slots=True)
class AxignalRuntime:
    config: RuntimeConfig
    observation_memory: SqliteObservationMemory
    learning_memory: SqliteLearningMemory
    admin_observability: SqliteAdminObservabilityStore
    first_proof: FirstProofService | None = None
    admin_access: AdminAccessService | None = None

    @property
    def observation_db(self) -> Path:
        return self.config.data_dir / "observation-memory.sqlite3"

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
        learning = self._sqlite_status(self.learning_db, "learning_events")
        healthy = observation.get("status") == "ok" and learning.get("status") == "ok"
        if not detailed:
            observation = {"status": observation["status"]}
            learning = {"status": learning["status"]}
        return {
            "status": "ok" if healthy else "degraded",
            "service": "axignal-runtime",
            "environment": self.config.environment,
            "code_sha": self.config.code_sha,
            "persistence": {"observation_memory": observation, "learning_memory": learning},
            "write_surface": "closed",
        }


def build_runtime(config: RuntimeConfig) -> AxignalRuntime:
    observation_db = config.data_dir / "observation-memory.sqlite3"
    learning_db = config.data_dir / "learning-memory.sqlite3"
    observation_memory = SqliteObservationMemory(observation_db)
    learning_memory = SqliteLearningMemory(learning_db)
    admin_observability = SqliteAdminObservabilityStore(
        config.data_dir / "admin-observability.sqlite3"
    )
    first_proof = None
    if config.first_proof_allowed_host is not None:
        from pipeline.source_acquisition import ContentAddressedArtifactStore

        first_proof = FirstProofService(
            code_sha=config.code_sha,
            allowed_host=config.first_proof_allowed_host,
            store=FirstProofStore(config.data_dir / "first-proof.sqlite3"),
            observation_memory=observation_memory,
            learning_memory=learning_memory,
            artifacts=ContentAddressedArtifactStore(config.data_dir / "artifacts"),
        )
    return AxignalRuntime(
        config=config,
        observation_memory=observation_memory,
        learning_memory=learning_memory,
        admin_observability=admin_observability,
        first_proof=first_proof,
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


def _admin_projection_payload(
    projection: AdminShellProjection,
    *,
    command_center: AdminCommandCenterProjection | None = None,
    xeed_observatory: XeedAxiglandObservatory | None = None,
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
    return payload


def _render_admin_shell(
    web_root: Path,
    projection: AdminShellProjection,
    *,
    command_center: AdminCommandCenterProjection | None = None,
    xeed_observatory: XeedAxiglandObservatory | None = None,
) -> bytes:
    template = (web_root / "admin" / "index.html").read_text(encoding="utf-8")
    payload = html.escape(
        json.dumps(
            _admin_projection_payload(
                projection,
                command_center=command_center,
                xeed_observatory=xeed_observatory,
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

        def log_message(self, fmt: str, *args: object) -> None:
            # Keep default stderr access logging but never log headers/bodies/secrets.
            super().log_message(fmt, *args)

        def _json(self, payload: dict[str, object], status: HTTPStatus = HTTPStatus.OK) -> None:
            encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(encoded)

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
            request_path = urlsplit(self.path).path
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
                    rendered = _render_admin_shell(
                        runtime.config.web_root,
                        admin_projection,
                        command_center=command_center,
                        xeed_observatory=xeed_observatory,
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
            if request_path == "/api/subscriber-context":
                if runtime.first_proof is None:
                    self._json({"state": "NO_XEED", "realityLevel": "LIVE_PRODUCTION_FIRST_PROOF"})
                    return
                projection = runtime.first_proof.current_projection()
                if projection is None:
                    self._json({"state": "NO_XEED", "realityLevel": "LIVE_PRODUCTION_FIRST_PROOF"})
                else:
                    self._json(projection)
                return
            static_path = _resolve_static(runtime.config.web_root, request_path)
            if static_path is None or not static_path.is_file():
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            self._static(static_path)

        def do_POST(self) -> None:
            request_path = urlsplit(self.path).path
            if request_path == "/api/xeeds" and runtime.first_proof is not None:
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
                    projection = runtime.first_proof.plant(
                        label=str(payload.get("label", "")),
                        target_uri=str(payload.get("targetUri", "")),
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
                self._json(projection, HTTPStatus.CREATED)
                return
            self._json(
                {"status": "rejected", "reason": "PUBLIC_WRITE_SURFACE_CLOSED"},
                HTTPStatus.METHOD_NOT_ALLOWED,
            )

        do_PUT = do_POST
        do_PATCH = do_POST
        do_DELETE = do_POST

    return Handler


def serve(runtime: AxignalRuntime) -> None:
    handler = make_handler(runtime)
    with ThreadingHTTPServer((runtime.config.bind_host, runtime.config.port), handler) as server:
        server.serve_forever()
