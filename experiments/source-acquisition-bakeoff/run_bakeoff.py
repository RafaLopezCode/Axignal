"""Offline source-acquisition fixture benchmark; no external network access."""

from __future__ import annotations

import argparse
import hashlib
import http.server
import json
import os
import platform
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, ClassVar
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
MAX_RESPONSE_BYTES = 1_000_000


@dataclass(frozen=True)
class SourceRequest:
    research_question_id: str
    target: str
    capability: str
    requested_artifact_types: tuple[str, ...]
    deadline_ms: int
    rights_policy: str
    temporal_requirement: str = "no-stated-freshness"
    source_constraints: dict[str, str] = field(default_factory=dict)
    budget_requests: int = 1


@dataclass(frozen=True)
class SourceObservation:
    research_question_id: str
    source_uri: str
    source_identity: str
    retrieved_at: str
    observed_at: str | None
    acquisition_method: str
    adapter_identity: str
    artifact_type: str
    raw_artifact_reference: str
    content_fingerprint: str | None
    response_metadata: dict[str, Any]
    acquisition_config: dict[str, Any]
    provenance: tuple[str, ...]
    rights_metadata: str
    extraction_metadata: dict[str, Any]
    failure_state: str | None


class FixtureHandler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    fixture_map: ClassVar[dict[str, tuple[int, str, bytes]]] = {}
    request_counts: ClassVar[dict[str, int]] = {}
    byte_counts: ClassVar[dict[str, int]] = {}
    stats_lock: ClassVar[threading.Lock] = threading.Lock()

    def do_GET(self) -> None:
        path = urlsplit(self.path).path
        with self.stats_lock:
            self.request_counts[path] = self.request_counts.get(path, 0) + 1
        if path == "/failure/timeout":
            time.sleep(0.5)
        if path == "/failure/redirect-loop":
            self.send_response(302)
            self.send_header("Location", path)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        if path == "/failure/private-redirect":
            # Deliberately stays on this loopback server: no private or
            # metadata address is contacted during this safety simulation.
            self.send_response(302)
            self.send_header("Location", "/failure/private-destination-simulated")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        if path == "/failure/private-destination-simulated":
            self.send_response(204)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        if path == "/failure/timeout":
            status, content_type, body = 200, "text/html; charset=utf-8", b"<p>delayed response</p>"
        elif path == "/failure/oversized":
            status, content_type, body = (
                200,
                "application/octet-stream",
                b"x" * (MAX_RESPONSE_BYTES + 1),
            )
        elif path == "/failure/malformed":
            status, content_type, body = 200, "text/html; charset=utf-8", b"<html><div><b>broken"
        else:
            status, content_type, body = self.fixture_map.get(
                path, (404, "text/plain; charset=utf-8", b"fixture not found")
            )
        if path == "/w11-restricted":
            status, content_type, body = (
                403,
                "text/plain; charset=utf-8",
                b"fixture policy denial",
            )
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Fixture-Request-Id", path.lstrip("/"))
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            # Expected when a client enforces the timeout fixture's deadline.
            return
        with self.stats_lock:
            self.byte_counts[path] = self.byte_counts.get(path, 0) + len(body)

    def log_message(self, _format: str, *_args: object) -> None:
        return


class QuietThreadingHTTPServer(http.server.ThreadingHTTPServer):
    """Hide expected socket resets from deliberately timed-out fixture clients."""

    def handle_error(self, _request: object, _client_address: object) -> None:
        return


def fixture_data() -> list[dict[str, Any]]:
    """Synthetic corpus. Fixtures contain no copied third-party content."""
    return [
        {
            "id": "W1",
            "class": "simple corporate HTML",
            "path": "/w1",
            "slots": ["name", "about"],
            "expected": "success",
            "body": b"<html><title>Example Works</title><p>Independent fixture organization.</p></html>",
            "type": "text/html",
        },
        {
            "id": "W2",
            "class": "JavaScript-rendered page",
            "path": "/w2",
            "slots": ["hydrated_product"],
            "expected": "success_static_shell",
            # The value needed for the evidence slot is delivered by a separate
            # script and is absent from the initial HTML response.
            "body": b"<html><div id='app'>Loading</div><script src='/w2.js'></script></html>",
            "type": "text/html",
        },
        {
            "id": "W3",
            "class": "bounded multi-page crawl",
            "path": "/w3",
            "slots": ["page_1", "page_2"],
            "expected": "success",
            "body": b"<a href='/w3-child'>Child</a><p>Root</p>",
            "type": "text/html",
        },
        {
            "id": "W4",
            "class": "public PDF document",
            "path": "/w4",
            "slots": ["document_bytes"],
            "expected": "success_fixture_pdf",
            "body": b"%PDF-1.4\n% synthetic fixture only\n1 0 obj<</Type/Catalog>>endobj\n%%EOF\n",
            "type": "application/pdf",
        },
        {
            "id": "W5",
            "class": "structured public page",
            "path": "/w5",
            "slots": ["table_rows"],
            "expected": "success",
            "body": b"<table><tr><th>product</th></tr><tr><td>Part A</td></tr></table>",
            "type": "text/html",
        },
        {
            "id": "W6",
            "class": "temporal/news page",
            "path": "/w6",
            "slots": ["publication_date", "title"],
            "expected": "success",
            "body": b"<time datetime='2026-09-20'>2026-09-20</time><h1>Fixture notice</h1>",
            "type": "text/html",
        },
        {
            "id": "W7",
            "class": "relationship evidence",
            "path": "/w7",
            "slots": ["both_parties", "relationship_wording"],
            "expected": "success_observation_only",
            "body": b"<p>Example Works names Sample Supply as a distributor.</p>",
            "type": "text/html",
        },
        {
            "id": "W8",
            "class": "contradictory sources",
            "path": "/w8a",
            "slots": ["source_a_claim"],
            "expected": "two_observations",
            "body": b"<p>Fixture A says founded in 2010.</p>",
            "type": "text/html",
        },
        {
            "id": "W9",
            "class": "targeted research question",
            "path": "/w9",
            "slots": ["targeted_answer_evidence"],
            "expected": "success_targeted",
            "body": b"<p>One requested fact: headquarters city is Madrid.</p>",
            "type": "text/html",
        },
        {
            "id": "W10",
            "class": "follow-up information gap",
            "path": "/w10-first",
            "slots": ["initial_partial"],
            "expected": "two_step_loop",
            "body": b"<p>First observation: address is incomplete.</p>",
            "type": "text/html",
        },
        {
            "id": "W11",
            "class": "restricted/failure explicitness",
            "path": "/w11-restricted",
            "slots": [],
            "expected": "explicit_http_403",
            "body": b"",
            "type": "text/plain",
        },
        {
            "id": "W12",
            "class": "reuse/refetch",
            "path": "/w12",
            "slots": ["content_hash_reuse"],
            "expected": "cache_then_refetch_policy",
            "body": b"<p>Stable reusable fixture.</p>",
            "type": "text/html",
        },
    ]


class OfflineFixtureAdapter:
    """Experimental adapter with an explicit loopback-only fixture target."""

    identity = "axignal-offline-fixture-adapter/0.1"

    def __init__(
        self, base_url: str, artifact_dir: Path, max_bytes: int = MAX_RESPONSE_BYTES
    ) -> None:
        parsed_base = urlsplit(base_url)
        if (
            parsed_base.scheme != "http"
            or parsed_base.hostname != "127.0.0.1"
            or parsed_base.port is None
            or parsed_base.path
            or parsed_base.query
            or parsed_base.fragment
            or parsed_base.username
            or parsed_base.password
        ):
            raise ValueError("fixture adapter accepts only its explicit loopback server")
        self.base_url = base_url
        self.artifact_dir = artifact_dir
        self.max_bytes = max_bytes

    def acquire(self, request: SourceRequest, fixture_id: str) -> SourceObservation:
        started = time.perf_counter()
        uri = f"{self.base_url}{request.target}"
        status: int | None = None
        headers: dict[str, str] = {}
        payload = b""
        failure: str | None = None
        final_uri = uri
        try:
            with urlopen(uri, timeout=max(request.deadline_ms / 1000, 0.1)) as response:
                status = response.status
                headers = {k.lower(): v for k, v in response.headers.items()}
                final_uri = response.geturl()
                payload = response.read(self.max_bytes + 1)
            if len(payload) > self.max_bytes:
                payload = b""
                failure = "response_too_large"
        except HTTPError as error:
            status = error.code
            headers = {k.lower(): v for k, v in error.headers.items()}
            final_uri = error.geturl()
            failure = f"http_{error.code}"
        except TimeoutError:
            failure = "timeout"
        except URLError as error:
            failure = f"transport_error:{type(error.reason).__name__}"

        digest = hashlib.sha256(payload).hexdigest() if payload else None
        artifact_ref: str | None = None
        if payload:
            self.artifact_dir.mkdir(parents=True, exist_ok=True)
            artifact_path = self.artifact_dir / f"{fixture_id}-{digest}.bin"
            artifact_path.write_bytes(payload)
            artifact_ref = artifact_path.relative_to(ROOT).as_posix()

        retrieved_at = datetime.now(UTC).isoformat()
        return SourceObservation(
            research_question_id=request.research_question_id,
            source_uri=uri,
            source_identity="synthetic-repository-fixture",
            retrieved_at=retrieved_at,
            observed_at=None,
            acquisition_method="local_http_get",
            adapter_identity=self.identity,
            artifact_type=headers.get("content-type", "unknown"),
            raw_artifact_reference=artifact_ref or "",
            content_fingerprint=digest,
            response_metadata={
                "status": status,
                "headers": headers,
                "final_uri": final_uri,
                "redirect_chain": [uri] if final_uri == uri else [uri, final_uri],
                "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
                "body_bytes": len(payload),
            },
            acquisition_config={
                "requested_artifact_types": list(request.requested_artifact_types),
                "deadline_ms": request.deadline_ms,
                "max_response_bytes": self.max_bytes,
                "rights_policy": request.rights_policy,
                "temporal_requirement": request.temporal_requirement,
                "source_constraints": request.source_constraints,
            },
            provenance=("source-request", fixture_id, self.identity),
            rights_metadata="synthetic fixture; no external source rights asserted",
            extraction_metadata={"transform": "none", "candidate_engine": None},
            failure_state=failure,
        )


def run(iterations: int = 3) -> dict[str, Any]:
    run_started = time.perf_counter()
    data = fixture_data()
    FixtureHandler.fixture_map = {
        row["path"]: (200, row["type"], row["body"]) for row in data if row["id"] != "W11"
    }
    FixtureHandler.fixture_map["/w3-child"] = (
        200,
        "text/html",
        b"<p>Bounded discovered child page.</p>",
    )
    FixtureHandler.fixture_map["/w10-followup"] = (
        200,
        "text/html",
        b"<p>Follow-up proves address is Calle Falsa 123, Madrid.</p>",
    )
    FixtureHandler.fixture_map["/w8b"] = (
        200,
        "text/html",
        b"<p>Fixture B says founded in 2012.</p>",
    )
    FixtureHandler.fixture_map["/w2.js"] = (
        200,
        "application/javascript; charset=utf-8",
        b"document.querySelector('#app').textContent='Widget';",
    )
    server = QuietThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
    FixtureHandler.request_counts = {}
    FixtureHandler.byte_counts = {}
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"
    try:
        observations: list[dict[str, Any]] = []
        latencies: list[float] = []
        artifacts = ROOT / "results" / "artifacts"
        adapter = OfflineFixtureAdapter(base_url, artifacts)
        for iteration in range(1, iterations + 1):
            for row in data:
                request = SourceRequest(
                    research_question_id=f"{row['id']}-Q1",
                    target=row["path"],
                    capability="GENERAL_HTTP",
                    requested_artifact_types=(row["type"],),
                    deadline_ms=1500,
                    rights_policy="synthetic-fixture-only",
                )
                obs = adapter.acquire(request, f"{row['id']}-i{iteration}")
                entry = asdict(obs)
                entry.update(
                    {
                        "workload_id": row["id"],
                        "iteration": iteration,
                        "expected": row["expected"],
                        "evidence_slots": len(row["slots"]),
                    }
                )
                observations.append(entry)
                if obs.response_metadata.get("elapsed_ms") is not None:
                    latencies.append(float(obs.response_metadata["elapsed_ms"]))
                if row["id"] == "W3":
                    child_request = SourceRequest(
                        "W3-Q1",
                        "/w3-child",
                        "SITE_CRAWL",
                        ("text/html",),
                        1500,
                        "synthetic-fixture-only",
                    )
                    child = adapter.acquire(child_request, f"W3-child-i{iteration}")
                    child_entry = asdict(child)
                    child_entry.update(
                        {
                            "workload_id": "W3",
                            "iteration": iteration,
                            "expected": "bounded_child",
                            "evidence_slots": 1,
                        }
                    )
                    observations.append(child_entry)
                if row["id"] == "W8":
                    other_request = SourceRequest(
                        "W8-Q1",
                        "/w8b",
                        "TARGETED_URL",
                        ("text/html",),
                        1500,
                        "synthetic-fixture-only",
                    )
                    other = adapter.acquire(other_request, f"W8b-i{iteration}")
                    other_entry = asdict(other)
                    other_entry.update(
                        {
                            "workload_id": "W8",
                            "iteration": iteration,
                            "expected": "contradictory_observation",
                            "evidence_slots": 1,
                        }
                    )
                    observations.append(other_entry)

        # Deterministic Q1 -> partial O1 -> structured gap -> targeted Q2 -> O2.
        first_request = SourceRequest(
            "W10-Q1", "/w10-first", "TARGETED_URL", ("text/html",), 1500, "synthetic-fixture-only"
        )
        first = adapter.acquire(first_request, "loop-Q1")
        gap = {
            "gap_id": "G1",
            "missing_fields": ["complete_address"],
            "basis_observation": first.content_fingerprint,
        }
        second_request = SourceRequest(
            "W10-Q2",
            "/w10-followup",
            "TARGETED_URL",
            ("text/html",),
            1500,
            "synthetic-fixture-only",
        )
        second = adapter.acquire(second_request, "loop-Q2")
        loop = {
            "FIRST_REQUEST": asdict(first_request),
            "FIRST_OBSERVATION": asdict(first),
            "STRUCTURED_GAP": gap,
            "SECOND_REQUEST": asdict(second_request),
            "SECOND_OBSERVATION": asdict(second),
            "PROVENANCE_CHAIN_PRESERVED": bool(
                first.provenance
                and second.provenance
                and gap["basis_observation"] == first.content_fingerprint
                and first.research_question_id == first_request.research_question_id
                and second.research_question_id == second_request.research_question_id
            ),
        }
        durations = sorted(latencies)
        return {
            "run_metadata": {
                "date_utc": datetime.now(UTC).isoformat(),
                "python": platform.python_version(),
                "platform": platform.platform(),
                "cpu_count": os.cpu_count(),
                "adapter": adapter.identity,
                "iterations": iterations,
                "warm_cold_state": "loopback server warmed before iteration 1; no browser, cache, or candidate engine state",
                "workload_count": len(data),
                "external_network_used": False,
                "candidate_engines_installed": [],
                "candidate_engines_benchmarked": [],
                "result_kind": "offline_fixture_contract_and_transport_reference_only",
            },
            "measurement_summary": {
                "requests": len(observations),
                "wall_seconds": round(time.perf_counter() - run_started, 6),
                "cpu_count": os.cpu_count(),
                "network_bytes_received": sum(
                    int(row["response_metadata"].get("body_bytes", 0)) for row in observations
                ),
                "explicit_failures": sum(bool(row["failure_state"]) for row in observations),
                "raw_artifacts_written": sum(
                    bool(row["raw_artifact_reference"]) for row in observations
                ),
                "observed_slot_count": sum(
                    row["evidence_slots"] for row in observations if not row["failure_state"]
                ),
                "reuse_refetch_hashes_match": len(
                    {
                        row["content_fingerprint"]
                        for row in observations
                        if row["workload_id"] == "W12"
                    }
                )
                <= 1,
                "latency_ms_median_including_loopback": durations[len(durations) // 2]
                if durations
                else None,
                "latency_ms_p95_including_loopback": durations[
                    min(int(len(durations) * 0.95), len(durations) - 1)
                ]
                if durations
                else None,
                "latency_scope": "local HTTP fixture only; not comparative candidate performance",
                "evidence_yield": "vector: successful required observation slots; wall seconds; bytes received; requests; marginal monetary cost (not applicable to synthetic fixtures). No weighted composite.",
            },
            "information_gain_loop": loop,
            "observations": observations,
        }
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=3)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    if args.iterations < 1 or args.iterations > 100:
        parser.error("--iterations must be between 1 and 100")
    result = run(args.iterations)
    RESULTS.mkdir(parents=True, exist_ok=True)
    output = args.output or RESULTS / "latest.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"wrote {output}")
    print(json.dumps(result["measurement_summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
