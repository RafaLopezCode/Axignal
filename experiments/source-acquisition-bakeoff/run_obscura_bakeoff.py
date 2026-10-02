"""P0-SOURCE-01D synthetic Obscura vs Chromium browser-provider bakeoff.

This runner is intentionally experimental. It uses only the repository fixture
and loopback. Public dispatch is a later phase and is blocked automatically when
mandatory browser-boundary controls are not demonstrated.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import statistics
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import psutil
from run_bakeoff import (
    FixtureHandler,
    QuietThreadingHTTPServer,
    fixture_data,
)

HERE = Path(__file__).resolve().parent
DEFAULT_ROOT = Path(os.environ.get("P0_SOURCE01D_ROOT", "D:/AXIGNAL/_experiments/p0-source01d"))
WINDOWS_ARCHIVE_SHA256 = "781a1b8bd12b65ec5aba95842e75e6f56b3101d360397506c0e35fe3f78536e8"
LINUX_ARCHIVE_SHA256 = "1534d1e6ddaf3d080ec4091eb41d0a4d8cc042a48b607d3c410fc13b482a9eec"


@dataclass(frozen=True)
class Workload:
    workload_id: str
    class_name: str
    path: str
    expected_tokens: tuple[str, ...] = ()
    timeout_seconds: int = 5
    recovery_eligible: bool = True
    expected_failure: bool = False


@dataclass
class ProcessMeasurement:
    returncode: int
    elapsed_ms: float
    peak_rss_bytes: int
    cpu_ms: float
    stdout: str
    stderr: str
    killed_by_parent_timeout: bool


def _tree(process: psutil.Process) -> list[psutil.Process]:
    try:
        return [process, *process.children(recursive=True)]
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return [process]


def run_measured(command: list[str], *, timeout_seconds: float) -> ProcessMeasurement:
    started = time.perf_counter()
    proc = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    root = psutil.Process(proc.pid)
    peak_rss = 0
    cpu_seconds = 0.0
    killed = False
    while proc.poll() is None:
        rss = 0
        cpu = 0.0
        for child in _tree(root):
            try:
                rss += child.memory_info().rss
                times = child.cpu_times()
                cpu += times.user + times.system
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        peak_rss = max(peak_rss, rss)
        cpu_seconds = max(cpu_seconds, cpu)
        if time.perf_counter() - started > timeout_seconds:
            killed = True
            for child in reversed(_tree(root)):
                with contextlib.suppress(psutil.NoSuchProcess, psutil.AccessDenied):
                    child.kill()
            break
        time.sleep(0.02)
    stdout, stderr = proc.communicate(timeout=3)
    elapsed_ms = (time.perf_counter() - started) * 1000
    return ProcessMeasurement(
        returncode=proc.returncode if proc.returncode is not None else -9,
        elapsed_ms=round(elapsed_ms, 3),
        peak_rss_bytes=peak_rss,
        cpu_ms=round(cpu_seconds * 1000, 3),
        stdout=stdout[-4000:],
        stderr=stderr[-4000:],
        killed_by_parent_timeout=killed,
    )


def setup_fixture() -> tuple[QuietThreadingHTTPServer, str]:
    base = fixture_data()
    FixtureHandler.fixture_map = {
        row["path"]: (200, row["type"], row["body"]) for row in base if row["id"] != "W11"
    }
    FixtureHandler.fixture_map.update(
        {
            "/w2.js": (
                200,
                "application/javascript; charset=utf-8",
                b"document.querySelector('#app').textContent='Widget';",
            ),
            "/next-sim": (
                200,
                "text/html; charset=utf-8",
                b"<div id='__next'>Loading</div><script>Promise.resolve().then(()=>document.getElementById('__next').textContent='NextHydrated')</script>",
            ),
            "/vue-sim": (
                200,
                "text/html; charset=utf-8",
                b"<div id='app'>Loading</div><script>queueMicrotask(()=>document.getElementById('app').textContent='VueHydrated')</script>",
            ),
            "/lazy": (
                200,
                "text/html; charset=utf-8",
                b"<div id='lazy'>Loading</div><script>setTimeout(()=>document.getElementById('lazy').textContent='LazyLoaded',60)</script>",
            ),
            "/xhr": (
                200,
                "text/html; charset=utf-8",
                b"<div id='api'>Loading</div><script>fetch('/api/product').then(r=>r.json()).then(x=>document.getElementById('api').textContent=x.product)</script>",
            ),
            "/api/product": (
                200,
                "application/json",
                b'{"product":"API Product"}',
            ),
            "/redirect-start": (
                302,
                "text/plain",
                b"",
            ),
            "/redirect-final": (
                200,
                "text/html; charset=utf-8",
                b"<p>RedirectFinal</p>",
            ),
            "/pdf-link": (
                200,
                "text/html; charset=utf-8",
                b"<a href='/report.pdf'>Annual report PDF</a>",
            ),
            "/report.pdf": (
                200,
                "application/pdf",
                b"%PDF-1.4\n% synthetic report\n%%EOF\n",
            ),
            "/big-page": (
                200,
                "text/html; charset=utf-8",
                b"<div id='big'>Loading</div><script src='/big.js'></script>",
            ),
            "/big.js": (
                200,
                "application/javascript; charset=utf-8",
                b"/*"
                + (b"x" * 1_200_000)
                + b"*/document.getElementById('big').textContent='BigLoaded';",
            ),
            "/history": (
                200,
                "text/html; charset=utf-8",
                b"<div id='hist'></div><script>history.pushState({},'', '?step=2');document.getElementById('hist').textContent='HISTORY='+history.length;</script>",
            ),
            "/runaway": (
                200,
                "text/html; charset=utf-8",
                b"<p>before</p><script>while(true){}</script>",
            ),
        }
    )
    original_do_get = FixtureHandler.do_GET

    def do_get_with_redirect(self: FixtureHandler) -> None:
        from urllib.parse import urlsplit

        path = urlsplit(self.path).path
        if path == "/redirect-start":
            self.send_response(302)
            self.send_header("Location", "/redirect-final")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        original_do_get(self)

    FixtureHandler.do_GET = do_get_with_redirect  # type: ignore[method-assign]
    FixtureHandler.request_counts = {}
    FixtureHandler.byte_counts = {}
    server = QuietThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{server.server_port}"


def workloads() -> tuple[Workload, ...]:
    return (
        Workload("STATIC", "static HTML", "/w1", ("Example Works",)),
        Workload("EXTERNAL_JS", "external JavaScript", "/w2", ("Widget",)),
        Workload("NEXT_SIM", "Next-style hydration", "/next-sim", ("NextHydrated",)),
        Workload("VUE_SIM", "Vue-style hydration", "/vue-sim", ("VueHydrated",)),
        Workload("LAZY", "lazy dynamic content", "/lazy", ("LazyLoaded",)),
        Workload("XHR", "fetch/XHR structured data", "/xhr", ("API Product",)),
        Workload("REDIRECT", "redirect chain", "/redirect-start", ("RedirectFinal",)),
        Workload("PDF_DISCOVERY", "PDF/resource discovery", "/pdf-link", ("report.pdf",)),
        Workload("MALFORMED", "malformed HTML", "/failure/malformed", ("broken",)),
        Workload("HTTP_404", "HTTP 404 explicitness", "/not-found", ("fixture not found",)),
        Workload(
            "RESTRICTED_403", "HTTP 403 explicitness", "/w11-restricted", ("fixture policy denial",)
        ),
        Workload("BIG_SUBRESOURCE", "oversized JS subresource", "/big-page", ("BigLoaded",)),
        Workload("HISTORY", "browser compatibility sentinel", "/history", ("HISTORY=2",)),
        Workload(
            "RUNAWAY",
            "synchronous JavaScript hang",
            "/runaway",
            (),
            timeout_seconds=2,
            recovery_eligible=False,
            expected_failure=True,
        ),
        Workload(
            "REDIRECT_LOOP",
            "redirect loop",
            "/failure/redirect-loop",
            (),
            timeout_seconds=3,
            recovery_eligible=False,
            expected_failure=True,
        ),
    )


def snapshot_server() -> tuple[dict[str, int], dict[str, int]]:
    with FixtureHandler.stats_lock:
        return dict(FixtureHandler.request_counts), dict(FixtureHandler.byte_counts)


def server_delta(before: tuple[dict[str, int], dict[str, int]]) -> dict[str, object]:
    before_requests, before_bytes = before
    with FixtureHandler.stats_lock:
        after_requests = dict(FixtureHandler.request_counts)
        after_bytes = dict(FixtureHandler.byte_counts)
    paths = sorted(set(before_requests) | set(after_requests))
    request_delta = {
        path: after_requests.get(path, 0) - before_requests.get(path, 0)
        for path in paths
        if after_requests.get(path, 0) - before_requests.get(path, 0)
    }
    byte_delta = {
        path: after_bytes.get(path, 0) - before_bytes.get(path, 0)
        for path in paths
        if after_bytes.get(path, 0) - before_bytes.get(path, 0)
    }
    return {
        "request_counts": request_delta,
        "body_bytes_served": byte_delta,
        "total_requests": sum(request_delta.values()),
        "total_body_bytes_served": sum(byte_delta.values()),
    }


def _html_tokens(path: Path, expected: tuple[str, ...]) -> tuple[int, int, str]:
    if not path.exists():
        return 0, len(expected), ""
    text = path.read_text(encoding="utf-8", errors="replace")
    recovered = sum(1 for token in expected if token in text)
    return recovered, len(expected), hashlib.sha256(text.encode("utf-8")).hexdigest()


def run_obscura(
    *,
    exe: Path,
    base_url: str,
    workload: Workload,
    output: Path,
) -> dict[str, object]:
    before = snapshot_server()
    command = [
        str(exe),
        "--allow-private-network",
        "fetch",
        f"{base_url}{workload.path}",
        "--dump",
        "html",
        "--timeout",
        str(workload.timeout_seconds),
        "--output",
        str(output),
    ]
    measurement = run_measured(command, timeout_seconds=workload.timeout_seconds + 4)
    recovered, expected_count, fingerprint = _html_tokens(output, workload.expected_tokens)
    return {
        "provider": "obscura",
        "workload_id": workload.workload_id,
        "class": workload.class_name,
        "returncode": measurement.returncode,
        "elapsed_ms": measurement.elapsed_ms,
        "peak_rss_bytes": measurement.peak_rss_bytes,
        "cpu_ms": measurement.cpu_ms,
        "killed_by_parent_timeout": measurement.killed_by_parent_timeout,
        "stderr_tail": measurement.stderr,
        "rendered_fingerprint": fingerprint or None,
        "recovered_tokens": recovered,
        "expected_tokens": expected_count,
        "server": server_delta(before),
    }


def run_chromium(
    *,
    python: Path,
    chrome: Path,
    base_url: str,
    workload: Workload,
    output: Path,
) -> dict[str, object]:
    before = snapshot_server()
    worker = HERE / "chromium_cold_worker.py"
    command = [
        str(python),
        str(worker),
        "--url",
        f"{base_url}{workload.path}",
        "--output",
        str(output),
        "--chrome",
        str(chrome),
        "--timeout-ms",
        str(workload.timeout_seconds * 1000),
    ]
    measurement = run_measured(command, timeout_seconds=workload.timeout_seconds + 6)
    recovered, expected_count, fingerprint = _html_tokens(output, workload.expected_tokens)
    worker_payload: dict[str, Any] = {}
    lines = [line for line in measurement.stdout.splitlines() if line.strip()]
    if lines:
        try:
            worker_payload = json.loads(lines[-1])
        except json.JSONDecodeError:
            worker_payload = {"parse_error": measurement.stdout[-500:]}
    return {
        "provider": "chromium",
        "workload_id": workload.workload_id,
        "class": workload.class_name,
        "returncode": measurement.returncode,
        "elapsed_ms": measurement.elapsed_ms,
        "peak_rss_bytes": measurement.peak_rss_bytes,
        "cpu_ms": measurement.cpu_ms,
        "killed_by_parent_timeout": measurement.killed_by_parent_timeout,
        "stderr_tail": measurement.stderr,
        "worker": worker_payload,
        "rendered_fingerprint": fingerprint or None,
        "recovered_tokens": recovered,
        "expected_tokens": expected_count,
        "server": server_delta(before),
    }


def check_obscura_ssrf_guard(exe: Path, base_url: str, output_dir: Path) -> dict[str, object]:
    before = snapshot_server()
    output = output_dir / "ssrf-guard.html"
    measurement = run_measured(
        [
            str(exe),
            "fetch",
            f"{base_url}/w1",
            "--dump",
            "html",
            "--timeout",
            "3",
            "--output",
            str(output),
        ],
        timeout_seconds=6,
    )
    delta = server_delta(before)
    return {
        "returncode": measurement.returncode,
        "blocked_before_fixture_contact": measurement.returncode != 0
        and delta["total_requests"] == 0,
        "server": delta,
        "stderr_tail": measurement.stderr,
    }


def aggregate(records: list[dict[str, object]], provider: str) -> dict[str, float]:
    rows = [row for row in records if row["provider"] == provider]
    successful = [row for row in rows if not row["killed_by_parent_timeout"]]
    return {
        "mean_elapsed_ms": round(
            statistics.mean(float(row["elapsed_ms"]) for row in successful), 3
        ),
        "median_elapsed_ms": round(
            statistics.median(float(row["elapsed_ms"]) for row in successful), 3
        ),
        "mean_peak_rss_bytes": round(
            statistics.mean(float(row["peak_rss_bytes"]) for row in successful), 3
        ),
        "mean_cpu_ms": round(statistics.mean(float(row["cpu_ms"]) for row in successful), 3),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument(
        "--obscura",
        type=Path,
        default=DEFAULT_ROOT / "obscura-v0.2.3-windows" / "obscura.exe",
    )
    parser.add_argument(
        "--controller-python",
        type=Path,
        default=DEFAULT_ROOT / "controller" / ".venv" / "Scripts" / "python.exe",
    )
    parser.add_argument(
        "--chrome",
        type=Path,
        default=Path("C:/Program Files/Google/Chrome/Application/chrome.exe"),
    )
    args = parser.parse_args()
    if args.iterations < 5:
        raise ValueError("P0-SOURCE-01D requires at least five measured iterations")
    for required in (args.obscura, args.controller_python, args.chrome):
        if not required.exists():
            raise FileNotFoundError(required)

    output_root = args.root / "results" / time.strftime("%Y%m%d-%H%M%S")
    output_root.mkdir(parents=True, exist_ok=True)
    server, base_url = setup_fixture()
    try:
        ssrf_guard = check_obscura_ssrf_guard(args.obscura, base_url, output_root)
        records: list[dict[str, object]] = []
        corpus = workloads()

        # One excluded warm-up on representative static + dynamic pages.
        for warmup in (corpus[0], corpus[1], corpus[5]):
            run_obscura(
                exe=args.obscura,
                base_url=base_url,
                workload=warmup,
                output=output_root / f"warmup-obscura-{warmup.workload_id}.html",
            )
            run_chromium(
                python=args.controller_python,
                chrome=args.chrome,
                base_url=base_url,
                workload=warmup,
                output=output_root / f"warmup-chromium-{warmup.workload_id}.html",
            )

        for iteration in range(1, args.iterations + 1):
            for workload in corpus:
                obscura_output = output_root / f"obscura-{workload.workload_id}-{iteration}.html"
                chromium_output = output_root / f"chromium-{workload.workload_id}-{iteration}.html"
                obscura = run_obscura(
                    exe=args.obscura,
                    base_url=base_url,
                    workload=workload,
                    output=obscura_output,
                )
                chromium = run_chromium(
                    python=args.controller_python,
                    chrome=args.chrome,
                    base_url=base_url,
                    workload=workload,
                    output=chromium_output,
                )
                obscura["iteration"] = iteration
                chromium["iteration"] = iteration
                records.extend((obscura, chromium))

        eligible = {item.workload_id for item in corpus if item.recovery_eligible}
        obscura_tokens = sum(
            int(row["recovered_tokens"])
            for row in records
            if row["provider"] == "obscura" and row["workload_id"] in eligible
        )
        chromium_tokens = sum(
            int(row["recovered_tokens"])
            for row in records
            if row["provider"] == "chromium" and row["workload_id"] in eligible
        )
        recovery_ratio = 0.0 if chromium_tokens == 0 else round(obscura_tokens / chromium_tokens, 6)

        obscura_agg = aggregate(records, "obscura")
        chromium_agg = aggregate(records, "chromium")
        rss_ratio = (
            obscura_agg["mean_peak_rss_bytes"] / chromium_agg["mean_peak_rss_bytes"]
            if chromium_agg["mean_peak_rss_bytes"]
            else 999.0
        )
        cpu_ratio = (
            obscura_agg["mean_cpu_ms"] / chromium_agg["mean_cpu_ms"]
            if chromium_agg["mean_cpu_ms"]
            else 999.0
        )
        resource_ratio = round((rss_ratio + cpu_ratio) / 2, 6)

        big_rows = [
            row
            for row in records
            if row["provider"] == "obscura" and row["workload_id"] == "BIG_SUBRESOURCE"
        ]
        oversized_bytes_observed = max(
            (int(row["server"]["total_body_bytes_served"]) for row in big_rows), default=0
        )
        hard_cap_demonstrated = oversized_bytes_observed <= 1_000_000

        safety = {
            "stealth_used": False,
            "obscura_default_ssrf_loopback_guard": ssrf_guard,
            "axignal_pre_dispatch_policy_required": True,
            "hard_response_or_subresource_cap_demonstrated": hard_cap_demonstrated,
            "redirect_hop_axignal_policy_interposition_demonstrated": False,
            "public_trial_eligible": False,
            "public_trial_blockers": [
                "hard response/subresource cap not demonstrated by Obscura v0.2.3 CLI"
                if not hard_cap_demonstrated
                else "",
                "AXIGNAL redirect-hop policy interposition not demonstrated for browser transport",
            ],
        }
        safety["public_trial_blockers"] = [item for item in safety["public_trial_blockers"] if item]

        if safety["public_trial_blockers"]:
            disposition = "EXPERIMENTAL_ONLY"
        elif recovery_ratio < 0.95:
            disposition = "REJECT"
        elif resource_ratio <= 0.60:
            disposition = "PRIMARY_WITH_CHROMIUM_FALLBACK"
        else:
            disposition = "OPTIONAL_FALLBACK"

        result = {
            "experiment": "P0-SOURCE-01D",
            "status": "SYNTHETIC_COMPLETE_PUBLIC_BLOCKED"
            if safety["public_trial_blockers"]
            else "SYNTHETIC_COMPLETE",
            "executed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "platform": sys.platform,
            "iterations": args.iterations,
            "warmup_excluded": True,
            "obscura": {
                "version": "0.2.3",
                "executable": str(args.obscura),
            },
            "chromium": {
                "playwright": "1.63.0",
                "executable": str(args.chrome),
            },
            "recovery": {
                "obscura_tokens": obscura_tokens,
                "chromium_tokens": chromium_tokens,
                "ratio": recovery_ratio,
                "required_min": 0.95,
            },
            "resources": {
                "obscura": obscura_agg,
                "chromium": chromium_agg,
                "rss_ratio": round(rss_ratio, 6),
                "cpu_ratio": round(cpu_ratio, 6),
                "aggregate_ratio": resource_ratio,
                "target_max": 0.60,
            },
            "safety": safety,
            "disposition": disposition,
            "records": records,
        }
        result_path = output_root / "result.json"
        result_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
        latest = args.root / "results" / "latest-synthetic.json"
        latest.parent.mkdir(parents=True, exist_ok=True)
        latest.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
        print(
            json.dumps(
                {
                    key: result[key]
                    for key in ("status", "recovery", "resources", "safety", "disposition")
                },
                indent=2,
            )
        )
        print(f"RESULT={result_path}")
        return 0
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
