"""Persistent-session comparison for P0-SOURCE-01D."""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import socket
import statistics
import subprocess
import time
from pathlib import Path

import psutil
from playwright.sync_api import Browser, Page, sync_playwright
from run_obscura_bakeoff import setup_fixture, workloads

DEFAULT_ROOT = Path(os.environ.get("P0_SOURCE01D_ROOT", "D:/AXIGNAL/_experiments/p0-source01d"))


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_http(port: int, timeout: float = 5.0) -> None:
    import urllib.request

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=0.5):
                return
        except Exception:
            time.sleep(0.05)
    raise TimeoutError("Obscura CDP server did not become ready")


def process_tree_rss(proc: psutil.Process) -> int:
    total = 0
    for item in [proc, *proc.children(recursive=True)]:
        with contextlib.suppress(psutil.NoSuchProcess, psutil.AccessDenied):
            total += item.memory_info().rss
    return total


def process_tree_cpu(proc: psutil.Process) -> float:
    total = 0.0
    for item in [proc, *proc.children(recursive=True)]:
        with contextlib.suppress(psutil.NoSuchProcess, psutil.AccessDenied):
            times = item.cpu_times()
            total += times.user + times.system
    return total


def chrome_descendants() -> list[psutil.Process]:
    root = psutil.Process(os.getpid())
    result: list[psutil.Process] = []
    for item in root.children(recursive=True):
        try:
            name = item.name().casefold()
            exe = (item.exe() or "").casefold()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
        if "chrome" in name or "chrome" in exe:
            result.append(item)
    return result


def chrome_rss() -> int:
    total = 0
    for item in chrome_descendants():
        with contextlib.suppress(psutil.NoSuchProcess, psutil.AccessDenied):
            total += item.memory_info().rss
    return total


def chrome_cpu() -> float:
    total = 0.0
    for item in chrome_descendants():
        with contextlib.suppress(psutil.NoSuchProcess, psutil.AccessDenied):
            times = item.cpu_times()
            total += times.user + times.system
    return total


def visit(page: Page, url: str, tokens: tuple[str, ...], timeout_ms: int) -> dict[str, object]:
    started = time.perf_counter()
    response = page.goto(url, wait_until="load", timeout=timeout_ms)
    page.wait_for_timeout(150)
    html = page.content()
    return {
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
        "status": None if response is None else response.status,
        "recovered_tokens": sum(1 for token in tokens if token in html),
        "expected_tokens": len(tokens),
        "final_url": page.url,
    }


def mean(rows: list[dict[str, object]], key: str) -> float:
    return round(statistics.mean(float(row[key]) for row in rows), 3)


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
        "--chrome",
        type=Path,
        default=Path("C:/Program Files/Google/Chrome/Application/chrome.exe"),
    )
    args = parser.parse_args()
    if args.iterations < 5:
        raise ValueError("at least five iterations are required")

    corpus = tuple(
        workload
        for workload in workloads()
        if workload.recovery_eligible and workload.workload_id != "HISTORY"
    )
    fixture, base_url = setup_fixture()
    obscura_port = free_port()
    obscura_proc = subprocess.Popen(
        [
            str(args.obscura),
            "serve",
            "--port",
            str(obscura_port),
            "--allow-private-network",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    obscura_ps = psutil.Process(obscura_proc.pid)
    try:
        wait_http(obscura_port)
        with sync_playwright() as playwright:
            obscura_browser: Browser = playwright.chromium.connect_over_cdp(
                f"http://127.0.0.1:{obscura_port}"
            )
            chrome_browser = playwright.chromium.launch(
                executable_path=str(args.chrome),
                headless=True,
                args=["--disable-gpu", "--no-first-run", "--no-default-browser-check"],
            )
            obscura_context = obscura_browser.contexts[0]
            chrome_context = chrome_browser.new_context()

            # Warm-up excluded.
            for workload in corpus[:3]:
                for context in (obscura_context, chrome_context):
                    page = context.new_page()
                    try:
                        visit(
                            page,
                            f"{base_url}{workload.path}",
                            workload.expected_tokens,
                            workload.timeout_seconds * 1000,
                        )
                    finally:
                        page.close()

            rows: list[dict[str, object]] = []
            obscura_peak = process_tree_rss(obscura_ps)
            chrome_peak = chrome_rss()
            obscura_cpu_start = process_tree_cpu(obscura_ps)
            chrome_cpu_start = chrome_cpu()

            for iteration in range(1, args.iterations + 1):
                for workload in corpus:
                    for provider, context in (
                        ("obscura", obscura_context),
                        ("chromium", chrome_context),
                    ):
                        page = context.new_page()
                        try:
                            row = visit(
                                page,
                                f"{base_url}{workload.path}",
                                workload.expected_tokens,
                                workload.timeout_seconds * 1000,
                            )
                        except Exception as exc:
                            row = {
                                "elapsed_ms": workload.timeout_seconds * 1000.0,
                                "status": None,
                                "recovered_tokens": 0,
                                "expected_tokens": len(workload.expected_tokens),
                                "final_url": None,
                                "error": f"{type(exc).__name__}:{str(exc)[:300]}",
                            }
                        finally:
                            page.close()
                        row.update(
                            {
                                "provider": provider,
                                "iteration": iteration,
                                "workload_id": workload.workload_id,
                            }
                        )
                        rows.append(row)
                        obscura_peak = max(obscura_peak, process_tree_rss(obscura_ps))
                        chrome_peak = max(chrome_peak, chrome_rss())

            obscura_cpu_ms = (process_tree_cpu(obscura_ps) - obscura_cpu_start) * 1000
            chrome_cpu_ms = (chrome_cpu() - chrome_cpu_start) * 1000
            obscura_browser.close()
            chrome_context.close()
            chrome_browser.close()

        obscura_rows = [row for row in rows if row["provider"] == "obscura"]
        chromium_rows = [row for row in rows if row["provider"] == "chromium"]
        obscura_tokens = sum(int(row["recovered_tokens"]) for row in obscura_rows)
        chromium_tokens = sum(int(row["recovered_tokens"]) for row in chromium_rows)
        recovery_ratio = 0.0 if chromium_tokens == 0 else obscura_tokens / chromium_tokens
        result = {
            "experiment": "P0-SOURCE-01D-PERSISTENT",
            "executed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "iterations": args.iterations,
            "eligible_workloads": [workload.workload_id for workload in corpus],
            "recovery": {
                "obscura_tokens": obscura_tokens,
                "chromium_tokens": chromium_tokens,
                "ratio": round(recovery_ratio, 6),
            },
            "obscura": {
                "mean_navigation_ms": mean(obscura_rows, "elapsed_ms"),
                "peak_rss_bytes": obscura_peak,
                "cpu_ms": round(obscura_cpu_ms, 3),
            },
            "chromium": {
                "mean_navigation_ms": mean(chromium_rows, "elapsed_ms"),
                "peak_rss_bytes": chrome_peak,
                "cpu_ms": round(chrome_cpu_ms, 3),
            },
            "ratios": {
                "navigation": round(
                    mean(obscura_rows, "elapsed_ms") / mean(chromium_rows, "elapsed_ms"), 6
                ),
                "peak_rss": round(obscura_peak / chrome_peak, 6) if chrome_peak else None,
                "cpu": round(obscura_cpu_ms / chrome_cpu_ms, 6) if chrome_cpu_ms else None,
            },
            "records": rows,
        }
        output = args.root / "results" / "latest-persistent.json"
        output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
        print(
            json.dumps(
                {key: result[key] for key in ("recovery", "obscura", "chromium", "ratios")},
                indent=2,
            )
        )
        print(f"RESULT={output}")
        return 0
    finally:
        fixture.shutdown()
        fixture.server_close()
        obscura_proc.terminate()
        try:
            obscura_proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            obscura_proc.kill()


if __name__ == "__main__":
    raise SystemExit(main())
