"""Run the controlled candidate-specific fixture bakeoff in isolated envs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import statistics
import subprocess
import threading
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from run_bakeoff import FixtureHandler, QuietThreadingHTTPServer, fixture_data

ROOT = Path(__file__).resolve().parent
EXPERIMENT_ROOT = ROOT.parent.parent
RESULTS = ROOT / "results" / "candidate-runtime"
TEMP_ROOT = Path(os.environ.get("P0_SOURCE01B_ROOT", ""))

PYTHONS = {
    name: TEMP_ROOT / name / ".venv" / "Scripts" / "python.exe"
    for name in ("scrapling", "crawlee", "crawl4ai", "scrapy", "playwright")
}


class MeasuredProcess:
    """Run a candidate while sampling process-tree RSS and CPU using psutil."""

    def __init__(self) -> None:
        try:
            import psutil
        except ImportError:
            self.psutil = None
        else:
            self.psutil = psutil

    def run(
        self, command: list[str], payload: dict[str, Any], env: dict[str, str]
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        input_data = json.dumps(payload, separators=(",", ":"))
        workdir = Path(env["P0_SOURCE01B_WORKDIR"]).resolve()
        if not workdir.is_relative_to(TEMP_ROOT.resolve()):
            raise ValueError("candidate worker directory must stay under P0_SOURCE01B_ROOT")
        workdir.mkdir(parents=True, exist_ok=True)
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            cwd=str(workdir),
            encoding="utf-8",
            errors="replace",
        )
        peak_rss = 0
        peak_process_count = 0
        cpu_start = 0.0
        cpu_last = 0.0
        monitor_error = None
        if self.psutil:
            try:
                parent = self.psutil.Process(process.pid)
                cpu_start = parent.cpu_times().user + parent.cpu_times().system
                cpu_last = cpu_start
            except Exception as exc:  # instrumentation failure does not lose result
                monitor_error = f"{type(exc).__name__}:{exc}"
                parent = None
        else:
            parent = None
            monitor_error = "psutil unavailable in benchmark controller"

        def sample() -> None:
            nonlocal peak_rss, peak_process_count, cpu_last
            while process.poll() is None:
                if parent is not None:
                    try:
                        family = [parent, *parent.children(recursive=True)]
                        peak_process_count = max(
                            peak_process_count, sum(p.is_running() for p in family)
                        )
                        total = sum(p.memory_info().rss for p in family if p.is_running())
                        peak_rss = max(peak_rss, total)
                        cpu_last = sum(
                            p.cpu_times().user + p.cpu_times().system
                            for p in family
                            if p.is_running()
                        )
                    except Exception:
                        pass
                time.sleep(0.02)

        monitor = threading.Thread(target=sample, daemon=True)
        monitor.start()
        stdout, stderr = process.communicate(input_data, timeout=240)
        monitor.join(timeout=1)
        if process.returncode:
            return {
                "adapter_error": f"worker_exit_{process.returncode}",
                "stderr_tail": stderr[-3000:],
            }, {
                "peak_rss_bytes": peak_rss or None,
                "peak_process_count": peak_process_count or None,
                "cpu_seconds": None,
                "monitor_error": monitor_error,
            }
        try:
            response = json.loads(stdout)
        except json.JSONDecodeError as exc:
            response = {
                "adapter_error": f"invalid_worker_json:{exc}",
                "stdout_tail": stdout[-1000:],
                "stderr_tail": stderr[-3000:],
            }
        cpu_seconds = round(max(0.0, cpu_last - cpu_start), 6) if parent is not None else None
        stderr = stderr or ""
        response["worker_stderr_tail"] = stderr[-1000:] if stderr.strip() else None
        return response, {
            "peak_rss_bytes": peak_rss or None,
            "peak_process_count": peak_process_count or None,
            "cpu_seconds": cpu_seconds,
            "monitor_error": monitor_error,
        }


def build_requests(
    base_url: str, candidates: list[str], iterations: int
) -> dict[str, list[dict[str, Any]]]:
    data = fixture_data()
    requests: dict[str, list[dict[str, Any]]] = {}
    for candidate in candidates:
        rows: list[dict[str, Any]] = []
        modes = ["browser"] if candidate in {"crawl4ai", "playwright"} else ["http"]
        for iteration in range(1, iterations + 1):
            for row in data:
                if row["id"] == "W10":
                    continue  # the explicit Q1→G1→Q2 sequence below is W10
                if row["id"] == "W11":
                    path = row["path"]
                else:
                    path = f"{row['path']}?p0b_iteration={iteration}"
                for mode in modes:
                    effective_slots = (
                        0 if row["id"] == "W2" and mode == "http" else len(row["slots"])
                    )
                    rows.append(
                        {
                            "research_question_id": f"{row['id']}-Q1-i{iteration}-{mode}",
                            "workload_id": row["id"],
                            "iteration": iteration,
                            "url": f"{base_url}{path}",
                            "mode": mode,
                            "expected_slots": effective_slots,
                            "expected": row["expected"],
                            "capability_state": "UNSUPPORTED"
                            if row["id"] == "W2" and mode == "http"
                            else "SUPPORTED",
                        }
                    )
            # Bounded child and contradictory second source are explicit
            # separate observations within their synthetic request budget.
            for wid, path, rid in (("W3", "/w3-child", "W3-child"), ("W8", "/w8b", "W8-source-B")):
                for mode in modes:
                    rows.append(
                        {
                            "research_question_id": f"{rid}-i{iteration}-{mode}",
                            "workload_id": wid,
                            "iteration": iteration,
                            "url": f"{base_url}{path}?p0b_iteration={iteration}",
                            "mode": mode,
                            "expected_slots": 1,
                            "expected": "additional_observation",
                        }
                    )
            for case, path in (
                ("404", "/failure/404"),
                ("timeout", "/failure/timeout"),
                ("redirect_loop", "/failure/redirect-loop"),
                ("private_redirect_simulated", "/failure/private-redirect"),
                ("oversized", "/failure/oversized"),
                ("malformed", "/failure/malformed"),
            ):
                for mode in modes:
                    rows.append(
                        {
                            "research_question_id": f"FAIL-{case}-i{iteration}-{mode}",
                            "workload_id": f"FAIL-{case.upper()}",
                            "iteration": iteration,
                            "url": f"{base_url}{path}?p0b_iteration={iteration}",
                            "mode": mode,
                            "deadline_ms": 100 if case == "timeout" else 8000,
                            "expected_slots": 0,
                            "expected": f"synthetic failure case: {case}",
                            "capability_state": "SUPPORTED",
                        }
                    )
        if candidate in {"scrapling", "crawlee"}:
            for iteration in range(1, iterations + 1):
                rows.append(
                    {
                        "research_question_id": f"W2-browser-i{iteration}",
                        "workload_id": "W2",
                        "iteration": iteration,
                        "url": f"{base_url}/w2?p0b_iteration={iteration}&p0b_mode=browser",
                        "mode": "browser",
                        "expected_slots": 1,
                        "expected": "js_rendered",
                    }
                )
        requests[candidate] = rows
    return requests


def configure_fixtures() -> tuple[Any, threading.Thread, str]:
    rows = fixture_data()
    FixtureHandler.fixture_map = {
        row["path"]: (200, row["type"], row["body"]) for row in rows if row["id"] != "W11"
    }
    FixtureHandler.fixture_map["/w2.js"] = (
        200,
        "application/javascript; charset=utf-8",
        b"document.querySelector('#app').textContent='Widget';",
    )
    FixtureHandler.fixture_map["/w3-child"] = (
        200,
        "text/html",
        b"<p>Bounded discovered child.</p>",
    )
    FixtureHandler.fixture_map["/w8b"] = (
        200,
        "text/html",
        b"<p>Fixture B says founded in 2012.</p>",
    )
    FixtureHandler.fixture_map["/w10-followup"] = (
        200,
        "text/html",
        b"<p>Follow-up proves address is Calle Falsa 123, Madrid.</p>",
    )
    FixtureHandler.request_counts = {}
    FixtureHandler.byte_counts = {}
    server = QuietThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread, f"http://127.0.0.1:{server.server_port}"


def summarize(candidate_runs: dict[str, Any], iterations: int) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for candidate, run in candidate_runs.items():
        rows = run.get("observations", [])
        by_workload: dict[str, list[dict[str, Any]]] = {}
        for observation in rows:
            by_workload.setdefault(observation["workload_id"], []).append(observation)
        workload_summary: dict[str, Any] = {}
        for workload, values in by_workload.items():
            times = sorted(
                float(v["elapsed_ms"]) for v in values if v.get("elapsed_ms") is not None
            )
            workload_summary[workload] = {
                "state": (
                    "SUPPORTED"
                    if any(
                        v.get("capability_state") == "SUPPORTED" and not v.get("failure_state")
                        for v in values
                    )
                    else "UNSUPPORTED"
                    if all(v.get("capability_state") == "UNSUPPORTED" for v in values)
                    else "FAILED"
                ),
                "capability_states": sorted(
                    {v.get("capability_state", "SUPPORTED") for v in values}
                ),
                "measured_iterations": len(
                    {int(v["iteration"]) for v in values if int(v["iteration"]) > 0}
                ),
                "median_ms": round(statistics.median(times), 3) if times else None,
                "p95_ms": round(times[min(int(len(times) * 0.95), len(times) - 1)], 3)
                if times
                else None,
                "requests_included": len(values),
                "bytes_received": sum(int(v.get("body_bytes") or 0) for v in values),
                "successful_slots": sum(
                    int(v.get("expected_slots", 0)) for v in values if not v.get("failure_state")
                ),
                "js_rendered_iterations": sum(v.get("js_execution") is True for v in values),
            }
        summary[candidate] = {
            "adapter_error": run.get("adapter_error"),
            "startup_and_batch_ms": run.get("startup_and_batch_ms"),
            "resource": run.get("resource", {}),
            "workloads": workload_summary,
            "observation_count": len(rows),
            "failure_count": sum(bool(v.get("failure_state")) for v in rows),
            "total_fixture_requests": run.get("fixture_requests"),
            "total_fixture_bytes_sent": run.get("fixture_bytes_sent"),
            "total_time_ms_including_startup": run.get("startup_and_batch_ms"),
        }
    return summary


def run(iterations: int = 5, candidates: list[str] | None = None) -> dict[str, Any]:
    if iterations < 5:
        raise ValueError("P0-SOURCE-01B requires at least five measured iterations")
    candidates = candidates or ["scrapling", "crawlee", "crawl4ai", "scrapy", "playwright"]
    if not TEMP_ROOT or not TEMP_ROOT.is_dir():
        raise RuntimeError("P0_SOURCE01B_ROOT must point to the isolated environment directory")
    for candidate in candidates:
        if not PYTHONS[candidate].is_file():
            raise FileNotFoundError(PYTHONS[candidate])
    server, thread, base_url = configure_fixtures()
    runtime_records = build_requests(base_url, candidates, iterations)
    runner = MeasuredProcess()
    runs: dict[str, Any] = {}
    targeted_loops: dict[str, Any] = {}
    composition: dict[str, Any] | None = None
    try:
        # One explicitly excluded warm-up request per candidate, before any
        # measured workload batch. Candidate-specific result is retained.
        for candidate in candidates:
            warmup = {
                "candidate": candidate,
                "requests": [
                    {
                        "research_question_id": "W1-WARMUP",
                        "workload_id": "W1-WARMUP",
                        "iteration": 0,
                        "url": f"{base_url}/w1",
                        "mode": "browser" if candidate in {"crawl4ai", "playwright"} else "http",
                        "expected_slots": 0,
                        "expected": "warmup",
                    }
                ],
            }
            env = os.environ.copy()
            env["PLAYWRIGHT_BROWSERS_PATH"] = str(TEMP_ROOT / "browsers")
            env["CRAWL4_AI_BASE_DIRECTORY"] = str(TEMP_ROOT / "crawl4ai-data")
            env["CRAWLEE_STORAGE_DIR"] = str(TEMP_ROOT / "crawlee-storage" / f"{candidate}-warmup")
            env["P0_SOURCE01B_WORKDIR"] = str(TEMP_ROOT / "worker-cwd" / f"{candidate}-warmup")
            response, _ = runner.run(
                [str(PYTHONS[candidate]), str(ROOT / "runtime_candidate_worker.py")], warmup, env
            )
            runs[candidate] = {"warmup": response}
        for candidate in candidates:
            env = os.environ.copy()
            env["PLAYWRIGHT_BROWSERS_PATH"] = str(TEMP_ROOT / "browsers")
            env["CRAWL4_AI_BASE_DIRECTORY"] = str(TEMP_ROOT / "crawl4ai-data")
            env["CRAWLEE_STORAGE_DIR"] = str(
                TEMP_ROOT / "crawlee-storage" / f"{candidate}-{time.time_ns()}"
            )
            env["P0_SOURCE01B_WORKDIR"] = str(
                TEMP_ROOT / "worker-cwd" / f"{candidate}-{time.time_ns()}"
            )
            payload = {"candidate": candidate, "requests": runtime_records[candidate]}
            before_requests = dict(FixtureHandler.request_counts)
            before_bytes = dict(FixtureHandler.byte_counts)
            response, resource = runner.run(
                [str(PYTHONS[candidate]), str(ROOT / "runtime_candidate_worker.py")], payload, env
            )
            response["fixture_requests"] = sum(FixtureHandler.request_counts.values()) - sum(
                before_requests.values()
            )
            response["fixture_bytes_sent"] = sum(FixtureHandler.byte_counts.values()) - sum(
                before_bytes.values()
            )
            response["resource"] = resource
            # Keep one copy of each raw observation; duplicate expansion made
            # the evidence artifact needlessly exceed repository size policy.
            runs[candidate].update(response)
            runs[candidate]["resource"] = resource
        # Execute the targeted research loop as two causally ordered calls.
        # Q2 is constructed only from Q1's returned observation fingerprint.
        for candidate in candidates:
            mode = "browser" if candidate in {"crawl4ai", "playwright"} else "http"
            before_requests = sum(FixtureHandler.request_counts.values())
            before_bytes = sum(FixtureHandler.byte_counts.values())
            q1_requests = [
                {
                    "research_question_id": f"W10-Q1-i{i}",
                    "workload_id": "W10",
                    "iteration": i,
                    "url": f"{base_url}/w10-first?p0b_iteration={i}",
                    "mode": mode,
                    "expected_slots": 1,
                    "expected": "targeted_initial_observation",
                }
                for i in range(1, iterations + 1)
            ]
            env_q1 = os.environ.copy()
            env_q1["PLAYWRIGHT_BROWSERS_PATH"] = str(TEMP_ROOT / "browsers")
            env_q1["CRAWL4_AI_BASE_DIRECTORY"] = str(TEMP_ROOT / "crawl4ai-data")
            env_q1["P0_SOURCE01B_WORKDIR"] = str(
                TEMP_ROOT / "worker-cwd" / f"{candidate}-targeted-q1"
            )
            q1_stage, q1_resource = runner.run(
                [str(PYTHONS[candidate]), str(ROOT / "runtime_candidate_worker.py")],
                {"candidate": candidate, "requests": q1_requests},
                env_q1,
            )
            q1_observations = q1_stage.get("observations", [])
            q1_by_id = {o["research_question_id"]: o for o in q1_observations}
            gap_inputs: list[dict[str, Any]] = []
            q2_requests: list[dict[str, Any]] = []
            loop_iterations: list[dict[str, Any]] = []
            for request in q1_requests:
                observation = q1_by_id.get(request["research_question_id"])
                encoded = observation.get("raw_body_base64") if observation else None
                initial = __import__("base64").b64decode(encoded) if encoded else b""
                rendered = (observation or {}).get("rendered_html") or ""
                incomplete = b"Calle Falsa 123" not in initial and "Calle Falsa 123" not in rendered
                gap = (
                    {
                        "gap_id": "G1",
                        "missing_fields": ["complete_address"],
                        "basis_observation": observation.get("content_fingerprint"),
                        "basis_request_identity": request["research_question_id"],
                    }
                    if observation
                    and not observation.get("failure_state")
                    and observation.get("content_fingerprint")
                    and incomplete
                    else None
                )
                if gap:
                    gap_inputs.append(gap)
                    q2_requests.append(
                        {
                            **request,
                            "research_question_id": request["research_question_id"].replace(
                                "W10-Q1", "W10-Q2"
                            ),
                            "url": f"{base_url}/w10-followup?p0b_iteration={request['iteration']}",
                            "expected": "targeted_followup_observation",
                            "targeted_gap_input": gap,
                        }
                    )
                loop_iterations.append(
                    {
                        "iteration": request["iteration"],
                        "q1_request_identity": request["research_question_id"],
                        "q1_observation_received": observation is not None,
                        "gap_input_accepted_by_harness": gap is not None,
                        "gap_input": gap,
                        "q2_targeted_invocation": bool(gap),
                        "state_reuse": False,
                    }
                )
            q2_observations: list[dict[str, Any]] = []
            q2_resource: dict[str, Any] = {}
            q2_stage: dict[str, Any] = {}
            if q2_requests:
                env_q2 = os.environ.copy()
                env_q2["PLAYWRIGHT_BROWSERS_PATH"] = str(TEMP_ROOT / "browsers")
                env_q2["CRAWL4_AI_BASE_DIRECTORY"] = str(TEMP_ROOT / "crawl4ai-data")
                env_q2["P0_SOURCE01B_WORKDIR"] = str(
                    TEMP_ROOT / "worker-cwd" / f"{candidate}-targeted-q2"
                )
                q2_stage, q2_resource = runner.run(
                    [str(PYTHONS[candidate]), str(ROOT / "runtime_candidate_worker.py")],
                    {"candidate": candidate, "requests": q2_requests},
                    env_q2,
                )
                q2_observations = q2_stage.get("observations", [])
            q2_by_id = {o["research_question_id"]: o for o in q2_observations}
            for row in loop_iterations:
                q2_id = row["q1_request_identity"].replace("W10-Q1", "W10-Q2")
                q2_observation = q2_by_id.get(q2_id)
                row["q2_observation_received"] = q2_observation is not None
                row["provenance_chain_preserved"] = bool(
                    row["gap_input_accepted_by_harness"]
                    and q2_observation
                    and row["gap_input"]["basis_observation"]
                    and q2_observation.get("targeted_gap_input") == row["gap_input"]
                )
            runs[candidate]["observations"].extend(q1_observations)
            runs[candidate]["observations"].extend(q2_observations)
            candidate_resource = runs[candidate]["resource"]
            candidate_resource["peak_rss_bytes"] = (
                max(
                    candidate_resource.get("peak_rss_bytes") or 0,
                    q1_resource.get("peak_rss_bytes") or 0,
                    q2_resource.get("peak_rss_bytes") or 0,
                )
                or None
            )
            if candidate_resource.get("cpu_seconds") is not None:
                candidate_resource["cpu_seconds"] = round(
                    candidate_resource["cpu_seconds"]
                    + (q1_resource.get("cpu_seconds") or 0)
                    + (q2_resource.get("cpu_seconds") or 0),
                    6,
                )
            runs[candidate]["startup_and_batch_ms"] = round(
                runs[candidate]["startup_and_batch_ms"]
                + float(q1_stage.get("startup_and_batch_ms") or 0)
                + float(q2_stage.get("startup_and_batch_ms") or 0),
                3,
            )
            runs[candidate]["fixture_requests"] += (
                sum(FixtureHandler.request_counts.values()) - before_requests
            )
            runs[candidate]["fixture_bytes_sent"] += (
                sum(FixtureHandler.byte_counts.values()) - before_bytes
            )
            targeted_loops[candidate] = {
                "execution_order": "Q1 observations -> structured G1 -> Q2 request construction -> Q2 observations",
                "iterations": loop_iterations,
                "q1_observations": q1_observations,
                "q2_observations": q2_observations,
                "q2_dispatched_count": len(q2_requests),
                "q2_success_count": sum(not o.get("failure_state") for o in q2_observations),
                "unwanted_recrawl": "Q2 used the targeted follow-up URL only; no whole-site recrawl was invoked",
                "total_requests": sum(FixtureHandler.request_counts.values()) - before_requests,
                "total_bytes": sum(FixtureHandler.byte_counts.values()) - before_bytes,
                "total_time_ms": round(
                    float(q1_stage.get("startup_and_batch_ms") or 0)
                    + float(q2_stage.get("startup_and_batch_ms") or 0),
                    3,
                ),
                "state_reuse": "no cross-request browser/cache state was relied upon",
            }
        if {"scrapy", "playwright"} <= set(candidates):
            composition_requests = [
                {
                    "research_question_id": f"COMPOSE-W2-i{i}",
                    "workload_id": "W2",
                    "iteration": i,
                    "url": f"{base_url}/w2?p0b_composition={i}",
                    "mode": "http",
                    "expected_slots": 1,
                    "expected": "Widget is absent from the initial HTML; JS capability required",
                    "capability_state": "SUPPORTED",
                }
                for i in range(1, iterations + 1)
            ]
            before_requests = sum(FixtureHandler.request_counts.values())
            before_bytes = sum(FixtureHandler.byte_counts.values())
            env_http = os.environ.copy()
            env_http["P0_SOURCE01B_WORKDIR"] = str(TEMP_ROOT / "worker-cwd" / "composition-http")
            http_stage, http_resource = runner.run(
                [str(PYTHONS["scrapy"]), str(ROOT / "runtime_candidate_worker.py")],
                {"candidate": "scrapy", "requests": composition_requests},
                env_http,
            )
            http_observations = http_stage.get("observations", [])
            escalations: list[dict[str, Any]] = []
            for request, observation in zip(composition_requests, http_observations, strict=False):
                encoded = observation.get("raw_body_base64")
                initial = __import__("base64").b64decode(encoded) if encoded else b""
                observation["escalation_predicate"] = b"Widget" not in initial
                if observation["escalation_predicate"]:
                    escalations.append(
                        {
                            **request,
                            "mode": "browser",
                            "expected": "browser escalation after required value absent in O1",
                        }
                    )
            env_browser = os.environ.copy()
            env_browser["PLAYWRIGHT_BROWSERS_PATH"] = str(TEMP_ROOT / "browsers")
            env_browser["P0_SOURCE01B_WORKDIR"] = str(
                TEMP_ROOT / "worker-cwd" / "composition-browser"
            )
            before_browser_requests = sum(FixtureHandler.request_counts.values())
            before_browser_bytes = sum(FixtureHandler.byte_counts.values())
            browser_stage, browser_resource = runner.run(
                [str(PYTHONS["playwright"]), str(ROOT / "runtime_candidate_worker.py")],
                {"candidate": "playwright", "requests": escalations},
                env_browser,
            )
            browser_observations = browser_stage.get("observations", [])
            by_id = {o["research_question_id"]: o for o in browser_observations}
            matched = [
                (http, by_id.get(http["research_question_id"])) for http in http_observations
            ]
            composed_ok = all(
                http.get("status") == 200
                and http.get("escalation_predicate")
                and browser is not None
                and browser.get("js_execution") is True
                and http.get("research_question_id") == browser.get("research_question_id")
                for http, browser in matched
            )
            pair_times = [
                float(http.get("elapsed_ms") or 0) + float((browser or {}).get("elapsed_ms") or 0)
                for http, browser in matched
            ]
            composition = {
                "strategy": "Scrapy HTTP → deterministic JS_REQUIRED predicate → Playwright browser",
                "execution": "two sequential isolated candidate worker stages; the browser stage only receives Q1 records whose raw HTML omitted Widget",
                "iterations_after_warmup": iterations,
                "http_observations": http_observations,
                "browser_observations": browser_observations,
                "all_escalated_only_when_required": len(escalations) == iterations,
                "composition_success": composed_ok,
                "provenance_chain_preserved": composed_ok
                and all(
                    http.get("request_identity") == browser.get("request_identity")
                    and http.get("content_fingerprint")
                    and browser.get("content_fingerprint")
                    for http, browser in matched
                    if browser is not None
                ),
                "evidence_yield": {
                    "S_slots": sum(
                        1
                        for _, browser in matched
                        if browser and browser.get("js_execution") is True
                    ),
                    "T_median_per_pair_ms": round(statistics.median(pair_times), 3)
                    if pair_times
                    else None,
                    "T_total_sequential_worker_ms": round(
                        float(http_stage.get("startup_and_batch_ms") or 0)
                        + float(browser_stage.get("startup_and_batch_ms") or 0),
                        3,
                    ),
                    "B_fixture_bytes_sent": sum(FixtureHandler.byte_counts.values()) - before_bytes,
                    "R_fixture_requests": sum(FixtureHandler.request_counts.values())
                    - before_requests,
                    "C_marginal_cost": "0; synthetic loopback only",
                    "M_peak_rss_bytes": max(
                        http_resource.get("peak_rss_bytes") or 0,
                        browser_resource.get("peak_rss_bytes") or 0,
                    ),
                    "P_cpu_seconds": round(
                        (http_resource.get("cpu_seconds") or 0)
                        + (browser_resource.get("cpu_seconds") or 0),
                        6,
                    ),
                },
                "browser_stage_fixture_requests": sum(FixtureHandler.request_counts.values())
                - before_browser_requests,
                "browser_stage_fixture_bytes": sum(FixtureHandler.byte_counts.values())
                - before_browser_bytes,
            }
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
    rows = [o for run_value in runs.values() for o in run_value.get("observations", [])]
    if composition:
        rows.extend(composition["http_observations"])
        rows.extend(composition["browser_observations"])
    artifact_dir = RESULTS / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    for row in rows:
        raw = row.pop("raw_body_base64", None)
        if raw:
            data = __import__("base64").b64decode(raw)
            digest = hashlib.sha256(data).hexdigest()
            path = artifact_dir / f"{row['workload_id']}-{row['iteration']}-{digest}.bin"
            path.write_bytes(data)
            row["raw_artifact_reference"] = path.relative_to(EXPERIMENT_ROOT).as_posix()
            row["content_fingerprint"] = digest
    metadata = {
        "date_utc": datetime.now(UTC).isoformat(),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "cpu_count": os.cpu_count(),
        "ram_bytes": runner.psutil.virtual_memory().total if runner.psutil else None,
        "ram_measurement": "psutil host memory inventory; exact available memory varies with system load",
        "browser": "Chrome for Testing 153.0.8010.12 (Playwright Chromium v1243)",
        "fixture_origin": "127.0.0.1 only",
        "external_targets": 0,
        "iterations_after_warmup": iterations,
        "warmup_iterations_excluded": 1,
        "candidates": candidates,
        "runtime_boundary": "experimental SourceRequest-shaped inputs and SourceObservation-shaped results",
        "candidate_environment_root": "isolated task directory, outside AXIGNAL repository and production virtualenv",
        "fixture_request_counts": dict(FixtureHandler.request_counts),
        "fixture_bytes_sent": dict(FixtureHandler.byte_counts),
        "unsafe_network_executed": False,
        "unsupported_scheme_test": "AXIGNAL experimental harness preflight rejected file:// for every candidate without dispatch",
        "failure_cases": [
            "403",
            "404",
            "timeout",
            "redirect_loop",
            "loopback-only forbidden-destination redirect simulation",
            "oversized",
            "malformed",
        ],
    }
    install_metrics: dict[str, Any] = {}
    for candidate in candidates:
        environment = TEMP_ROOT / candidate / ".venv"
        package_bytes = sum(
            p.stat().st_size
            for p in (environment / "Lib" / "site-packages").rglob("*")
            if p.is_file()
        )
        package_count = sum(1 for p in (environment / "Lib" / "site-packages").glob("*.dist-info"))
        install_metrics[candidate] = {
            "environment_disk_bytes": sum(
                p.stat().st_size for p in environment.rglob("*") if p.is_file()
            ),
            "site_packages_bytes": package_bytes,
            "distribution_count": package_count,
        }
    metadata["candidate_install_metrics"] = install_metrics
    metadata["shared_browser_disk_bytes"] = sum(
        p.stat().st_size for p in (TEMP_ROOT / "browsers").rglob("*") if p.is_file()
    )
    result = {
        "run_metadata": metadata,
        "candidate_runs": runs,
        "engine_composition_test": composition,
        "unsupported_scheme_preflight": {
            candidate: {
                "source_request_target": "file:///synthetic-not-dispatched",
                "source_observation_failure_state": "unsupported_scheme",
                "dispatched_to_candidate": False,
                "candidate_network_requests": 0,
                "status": "UNSUPPORTED",
            }
            for candidate in candidates
        },
        "summary": summarize(runs, iterations),
        "targeted_loop": targeted_loops,
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--candidate", action="append", choices=PYTHONS.keys())
    args = parser.parse_args()
    result = run(args.iterations, args.candidate)
    RESULTS.mkdir(parents=True, exist_ok=True)
    output = args.output or RESULTS / f"candidate-runtime-{datetime.now(UTC):%Y%m%dT%H%M%SZ}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n"
    output.write_text(serialized, encoding="utf-8")
    (RESULTS / "latest-candidate-runtime.json").write_text(serialized, encoding="utf-8")
    print(f"wrote {output}")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
