"""AXIGNAL HTTP runtime composition root.

The public HTTP surface is deliberately read-only. Canonical/business writes stay
behind governed application services and are not exposed by this host.
"""

from __future__ import annotations

import json
import mimetypes
import sqlite3
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

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
    first_proof: FirstProofService | None = None

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
