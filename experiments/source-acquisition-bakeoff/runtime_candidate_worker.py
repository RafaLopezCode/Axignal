"""Candidate-specific runtime adapters for the isolated P0-SOURCE-01B trial.

This file is invoked by a pinned candidate environment and speaks JSON on
stdin/stdout. It deliberately has no import from AXIGNAL production modules.
The parent benchmark supplies experimental SourceRequest-shaped records and
normalizes every result to the same SourceObservation-shaped dictionary.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import os
import sys
import time
from datetime import UTC, datetime
from typing import Any, ClassVar
from urllib.parse import urlsplit


def _public_guard(url: str) -> None:
    if os.environ.get("P0_SOURCE01C_PUBLIC_TRIAL") == "1":
        from public_guard import validate_public_url

        validate_public_url(url)


def normalized(
    candidate: str,
    request: dict[str, Any],
    *,
    status: int | None,
    headers: dict[str, Any] | None,
    final_url: str | None,
    body: bytes,
    rendered_html: str | None = None,
    js_executed: bool | None = None,
    error: str | None = None,
    elapsed_ms: float,
    redirect_chain: list[str] | None = None,
    network: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Normalize one engine result without making claims absent from the API."""
    headers = {str(k).lower(): str(v) for k, v in (headers or {}).items()}
    full_error = error
    if error and len(error) > 500:
        error = error[:500] + "…"
    digest = hashlib.sha256(body).hexdigest() if body else None
    return {
        "research_question_id": request["research_question_id"],
        "workload_id": request["workload_id"],
        "iteration": request["iteration"],
        "mode": request["mode"],
        "expected_slots": request.get("expected_slots", 0),
        "expected": request.get("expected"),
        "targeted_gap_input": request.get("targeted_gap_input"),
        "capability_state": request.get("capability_state", "SUPPORTED"),
        "requested_url": request["url"],
        "source_uri": request["url"],
        "request_identity": request["research_question_id"],
        "source_identity": urlsplit(request["url"]).hostname
        if os.environ.get("P0_SOURCE01C_PUBLIC_TRIAL") == "1"
        else "synthetic-repository-fixture",
        "retrieved_at": datetime.now(UTC).isoformat(),
        "observed_at": None,
        "acquisition_method": request["mode"],
        "adapter_identity": f"axignal-experimental-{candidate}-adapter/0.1",
        "artifact_type": headers.get("content-type", "unknown"),
        "raw_body_base64": base64.b64encode(body).decode("ascii") if body else None,
        "content_fingerprint": digest,
        "status": status,
        "headers": headers,
        "final_url": final_url,
        "redirect_chain": redirect_chain,
        "body_bytes": len(body),
        "elapsed_ms": round(elapsed_ms, 3),
        "response_metadata": {
            "status": status,
            "headers": headers,
            "final_url": final_url,
            "redirect_chain": redirect_chain,
            "elapsed_ms": round(elapsed_ms, 3),
            "body_bytes": len(body),
        },
        "acquisition_config": {
            "capability": request["mode"],
            "deadline_ms": request.get("deadline_ms", 8000),
            "rights_policy": "synthetic-fixture-only",
            "cache_policy": "bypass/no cache required",
        },
        "provenance": [
            request["research_question_id"],
            f"axignal-experimental-{candidate}-adapter/0.1",
        ],
        "rights_metadata": "synthetic repository fixture; no external source rights asserted",
        "policy_decision": request.get("policy_decision"),
        "extraction_metadata": {"transform": "none; raw acquisition only", "candidate": candidate},
        "rendered_html": rendered_html,
        "js_execution": (
            False
            if request["workload_id"] == "W2" and request["mode"] == "http" and js_executed is None
            else js_executed
        ),
        "network_provenance": network,
        "failure_state": error
        or (
            f"http_{status}"
            if status is not None and status >= 400
            else "no_observation_returned"
            if status is None and not body
            else None
        ),
        "failure_message_truncated": bool(full_error and full_error != error),
        "provenance_availability": {
            "requested_url": "NATIVE",
            "final_url": "NATIVE" if final_url else "NOT_AVAILABLE",
            "redirect_chain": "ADAPTER_RECOVERABLE" if redirect_chain else "NOT_AVAILABLE",
            "http_status": "NATIVE" if status is not None else "NOT_AVAILABLE",
            "headers": "NATIVE" if headers else "NOT_AVAILABLE",
            "retrieval_time": "ADAPTER_RECOVERABLE",
            "content_type": "NATIVE" if headers.get("content-type") else "NOT_AVAILABLE",
            "raw_response": "NATIVE" if body else "NOT_AVAILABLE",
            "rendered_result": "NATIVE" if rendered_html is not None else "NOT_AVAILABLE",
            "network_provenance": "NATIVE" if network is not None else "NOT_AVAILABLE",
            "content_hash": "ADAPTER_RECOVERABLE" if digest else "NOT_AVAILABLE",
            "adapter_version": "ADAPTER_RECOVERABLE",
            "request_identity": "ADAPTER_RECOVERABLE",
            "failure_state": "NATIVE"
            if error or (status is not None and status >= 400)
            else "NOT_AVAILABLE",
        },
    }


def scrapling(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    from scrapling.fetchers import DynamicFetcher, Fetcher

    output: list[dict[str, Any]] = []
    for record in records:
        start = time.perf_counter()
        try:
            _public_guard(record["url"])
            if record["mode"] == "browser":
                response = DynamicFetcher.fetch(
                    record["url"],
                    headless=True,
                    timeout=record.get("deadline_ms", 8000),
                    wait=0.15,
                    disable_resources=True,
                )
                html = str(response.html_content)
                body = html.encode("utf-8")
                status = int(getattr(response, "status", 200))
                headers = dict(getattr(response, "headers", {}) or {})
                final = str(getattr(response, "url", record["url"]))
                output.append(
                    normalized(
                        "scrapling",
                        record,
                        status=status,
                        headers=headers,
                        final_url=final,
                        body=body,
                        rendered_html=html,
                        js_executed="Widget" in html,
                        elapsed_ms=(time.perf_counter() - start) * 1000,
                        redirect_chain=[record["url"], final]
                        if final != record["url"]
                        else [final],
                    )
                )
            else:
                response = Fetcher.get(
                    record["url"],
                    timeout=record.get("deadline_ms", 8000) / 1000,
                    follow_redirects=os.environ.get("P0_SOURCE01C_PUBLIC_TRIAL") != "1",
                )
                body = (
                    response.body
                    if isinstance(response.body, bytes)
                    else str(response.body).encode()
                )
                if os.environ.get("P0_SOURCE01C_PUBLIC_TRIAL") == "1" and len(body) > 262_144:
                    raise ValueError("response_size_limit_exceeded")
                final = str(response.url)
                output.append(
                    normalized(
                        "scrapling",
                        record,
                        status=int(getattr(response, "status", 0)) or None,
                        headers=dict(getattr(response, "headers", {}) or {}),
                        final_url=final,
                        body=body,
                        elapsed_ms=(time.perf_counter() - start) * 1000,
                        redirect_chain=[record["url"], final]
                        if final != record["url"]
                        else [final],
                    )
                )
        except Exception as exc:  # each record yields an explicit adapter failure
            output.append(
                normalized(
                    "scrapling",
                    record,
                    status=None,
                    headers=None,
                    final_url=None,
                    body=b"",
                    error=f"{type(exc).__name__}:{exc}",
                    elapsed_ms=(time.perf_counter() - start) * 1000,
                )
            )
    return output


async def crawlee(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    from crawlee.crawlers import HttpCrawler, PlaywrightCrawler
    from crawlee.http_clients import ImpitHttpClient

    output: list[dict[str, Any]] = []
    for mode in ("http", "browser"):
        selected = [r for r in records if r["mode"] == mode]
        if not selected:
            continue
        current: dict[str, dict[str, Any]] = {}
        started = {r["url"]: time.perf_counter() for r in selected}
        if mode == "http":
            crawler = HttpCrawler(
                max_requests_per_crawl=len(selected),
                max_request_retries=0,
                max_session_rotations=0,
                respect_robots_txt_file=False,
                ignore_http_error_status_codes=[403, 404],
                configure_logging=False,
                keep_alive=False,
                http_client=ImpitHttpClient(timeout=0.1, max_redirects=5),
            )

            @crawler.router.default_handler
            async def on_http(
                context: Any, current: dict[str, Any] = current, started: dict[str, float] = started
            ) -> None:
                body = await context.http_response.read()
                response = context.http_response
                key = context.request.url
                current[key] = {
                    "status": response.status_code,
                    "headers": dict(response.headers),
                    "body": body,
                    "final_url": key,
                    "redirect_chain": [key],
                    "elapsed_ms": (time.perf_counter() - started.get(key, time.perf_counter()))
                    * 1000,
                }

            @crawler.failed_request_handler
            async def failed_http(
                context: Any, error: Exception, current: dict[str, Any] = current
            ) -> None:
                current[context.request.url] = {"error": f"{type(error).__name__}:{error}"}

            @crawler.pre_navigation_hook
            async def mark_http_request(context: Any, started: dict[str, float] = started) -> None:
                started[context.request.url] = time.perf_counter()

            try:
                await crawler.run([r["url"] for r in selected])
            except Exception as exc:
                for r in selected:
                    current.setdefault(r["url"], {"error": f"{type(exc).__name__}:{exc}"})
        else:
            crawler = PlaywrightCrawler(
                max_requests_per_crawl=len(selected),
                max_request_retries=0,
                headless=True,
                browser_type="chromium",
                configure_logging=False,
                respect_robots_txt_file=False,
                navigation_timeout=__import__("datetime").timedelta(seconds=8),
            )

            @crawler.router.default_handler
            async def on_browser(
                context: Any, current: dict[str, Any] = current, started: dict[str, float] = started
            ) -> None:
                html = await context.page.content()
                current[context.request.url] = {
                    "status": None,
                    "headers": {},
                    "body": b"",
                    "final_url": context.page.url,
                    "html": html,
                    "network": None,
                    "redirect_chain": [context.request.url, context.page.url],
                    "js": "Widget" in html,
                    "elapsed_ms": (
                        time.perf_counter() - started.get(context.request.url, time.perf_counter())
                    )
                    * 1000,
                }

            @crawler.failed_request_handler
            async def failed_browser(
                context: Any, error: Exception, current: dict[str, Any] = current
            ) -> None:
                current[context.request.url] = {"error": f"{type(error).__name__}:{error}"}

            @crawler.pre_navigation_hook
            async def mark_browser_request(
                context: Any, started: dict[str, float] = started
            ) -> None:
                started[context.request.url] = time.perf_counter()

            try:
                await crawler.run([r["url"] for r in selected])
            except Exception as exc:
                for r in selected:
                    current.setdefault(r["url"], {"error": f"{type(exc).__name__}:{exc}"})

        for record in selected:
            value = current.get(record["url"], {})
            output.append(
                normalized(
                    "crawlee",
                    record,
                    status=value.get("status"),
                    headers=value.get("headers"),
                    final_url=value.get("final_url"),
                    body=value.get("body", b""),
                    rendered_html=value.get("html"),
                    js_executed=value.get("js"),
                    error=value.get("error"),
                    elapsed_ms=value.get("elapsed_ms", value.get("batch_completion_ms", 0.0)),
                    redirect_chain=value.get("redirect_chain"),
                    network=value.get("network"),
                )
            )
    return output


async def crawl4ai(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig

    output: list[dict[str, Any]] = []
    config = BrowserConfig(
        browser_type="chromium",
        headless=True,
        verbose=False,
        enable_stealth=False,
        java_script_enabled=True,
    )
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        page_timeout=8000,
        wait_until="domcontentloaded",
        delay_before_return_html=0.1,
        max_retries=0,
        capture_network_requests=True,
        check_robots_txt=False,
    )
    async with AsyncWebCrawler(
        config=config, base_directory=os.environ["CRAWL4_AI_BASE_DIRECTORY"], verbose=False
    ) as crawler:
        for record in records:
            start = time.perf_counter()
            try:
                request_config = run_config.clone(page_timeout=record.get("deadline_ms", 8000))
                result = await crawler.arun(record["url"], config=request_config)
                html = str(result.html or "")
                body = html.encode("utf-8")
                final = str(result.redirected_url or result.url or record["url"])
                network = [
                    {
                        key: event[key]
                        for key in (
                            "event_type",
                            "url",
                            "status",
                            "method",
                            "resource_type",
                            "timestamp",
                            "is_navigation_request",
                        )
                        if key in event
                    }
                    for event in (result.network_requests or [])
                ]
                output.append(
                    normalized(
                        "crawl4ai",
                        record,
                        status=result.status_code,
                        headers=result.response_headers,
                        final_url=final,
                        body=body,
                        rendered_html=html,
                        js_executed="Widget" in html,
                        error=None if result.success else result.error_message,
                        elapsed_ms=(time.perf_counter() - start) * 1000,
                        redirect_chain=[record["url"], final]
                        if final != record["url"]
                        else [final],
                        network=network,
                    )
                )
            except Exception as exc:
                output.append(
                    normalized(
                        "crawl4ai",
                        record,
                        status=None,
                        headers=None,
                        final_url=None,
                        body=b"",
                        error=f"{type(exc).__name__}:{exc}",
                        elapsed_ms=(time.perf_counter() - start) * 1000,
                    )
                )
    return output


async def playwright(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    from playwright.async_api import async_playwright

    output: list[dict[str, Any]] = []
    async with async_playwright() as playwright_api:
        browser = await playwright_api.chromium.launch(headless=True)
        context = await browser.new_context(service_workers="block", accept_downloads=False)

        async def guard_browser_request(route: Any) -> None:
            url = route.request.url
            if os.environ.get("P0_SOURCE01C_PUBLIC_TRIAL") == "1":
                try:
                    _public_guard(url)
                    if route.request.resource_type not in {"document", "script", "stylesheet"}:
                        await route.abort()
                        return
                    await route.continue_()
                except Exception:
                    await route.abort()
                return
            if url.startswith("http://127.0.0.1:"):
                await route.continue_()
            else:
                await route.abort()

        await context.route("**/*", guard_browser_request)
        page = await context.new_page()
        network: list[dict[str, Any]] = []
        page.on(
            "response",
            lambda response: (
                network.append({"url": response.url[:500], "status": response.status})
                if len(network) < 20
                else None
            ),
        )
        for record in records:
            start = time.perf_counter()
            try:
                _public_guard(record["url"])
                response = await page.goto(
                    record["url"],
                    wait_until="domcontentloaded",
                    timeout=record.get("deadline_ms", 8000),
                )
                html = await page.content()
                body = await response.body() if response else b""
                if os.environ.get("P0_SOURCE01C_PUBLIC_TRIAL") == "1" and len(body) > 262_144:
                    raise ValueError("response_size_limit_exceeded")
                output.append(
                    normalized(
                        "playwright",
                        record,
                        status=response.status if response else None,
                        headers=await response.all_headers() if response else None,
                        final_url=page.url,
                        body=body,
                        rendered_html=html,
                        js_executed="Widget" in html,
                        elapsed_ms=(time.perf_counter() - start) * 1000,
                        redirect_chain=[record["url"], page.url],
                        network=list(network),
                    )
                )
            except Exception as exc:
                output.append(
                    normalized(
                        "playwright",
                        record,
                        status=None,
                        headers=None,
                        final_url=page.url or None,
                        body=b"",
                        error=f"{type(exc).__name__}:{exc}",
                        elapsed_ms=(time.perf_counter() - start) * 1000,
                        network=list(network),
                    )
                )
    return output


def scrapy(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    import scrapy
    from scrapy.crawler import CrawlerProcess

    output: list[dict[str, Any]] = []

    class RuntimeSpider(scrapy.Spider):
        name = "axignal_runtime_fixture"
        custom_settings: ClassVar[dict[str, Any]] = {
            "LOG_ENABLED": False,
            "ROBOTSTXT_OBEY": os.environ.get("P0_SOURCE01C_PUBLIC_TRIAL") != "1",
            "COOKIES_ENABLED": os.environ.get("P0_SOURCE01C_PUBLIC_TRIAL") != "1",
            "REFERER_ENABLED": os.environ.get("P0_SOURCE01C_PUBLIC_TRIAL") != "1",
            "RETRY_ENABLED": False,
            "DOWNLOAD_TIMEOUT": 8,
            "DOWNLOAD_MAXSIZE": 262_144
            if os.environ.get("P0_SOURCE01C_PUBLIC_TRIAL") == "1"
            else 1_000_000,
            "REDIRECT_MAX_TIMES": 5,
            "CONCURRENT_REQUESTS": 1,
        }

        async def start(self):
            for record in records:
                _public_guard(record["url"])
                yield scrapy.Request(
                    record["url"],
                    callback=self.parse,
                    errback=self.failed,
                    dont_filter=True,
                    meta={
                        "axignal_record": record,
                        "started": time.perf_counter(),
                        "handle_httpstatus_all": True,
                        "download_timeout": record.get("deadline_ms", 8000) / 1000,
                        "dont_redirect": os.environ.get("P0_SOURCE01C_PUBLIC_TRIAL") == "1",
                    },
                )

        def parse(self, response):
            record = response.meta["axignal_record"]
            elapsed = (time.perf_counter() - response.meta["started"]) * 1000
            body = bytes(response.body)
            output.append(
                normalized(
                    "scrapy",
                    record,
                    status=response.status,
                    headers=dict(response.headers.to_unicode_dict()),
                    final_url=response.url,
                    body=body,
                    elapsed_ms=float(response.meta.get("download_latency", elapsed / 1000)) * 1000,
                    redirect_chain=[
                        record["url"],
                        *response.request.meta.get("redirect_urls", []),
                        response.url,
                    ],
                )
            )

        def failed(self, failure):
            request = failure.request
            record = request.meta["axignal_record"]
            output.append(
                normalized(
                    "scrapy",
                    record,
                    status=None,
                    headers=None,
                    final_url=None,
                    body=b"",
                    error=failure.type.__name__,
                    elapsed_ms=(time.perf_counter() - request.meta["started"]) * 1000,
                )
            )

    process = CrawlerProcess(
        settings={
            "LOG_ENABLED": False,
            "ROBOTSTXT_OBEY": os.environ.get("P0_SOURCE01C_PUBLIC_TRIAL") != "1",
            "COOKIES_ENABLED": os.environ.get("P0_SOURCE01C_PUBLIC_TRIAL") != "1",
            "REFERER_ENABLED": os.environ.get("P0_SOURCE01C_PUBLIC_TRIAL") != "1",
            "RETRY_ENABLED": False,
            "DOWNLOAD_TIMEOUT": 8,
            "DOWNLOAD_MAXSIZE": 262_144
            if os.environ.get("P0_SOURCE01C_PUBLIC_TRIAL") == "1"
            else 1_000_000,
            "CONCURRENT_REQUESTS": 1,
        }
    )
    process.crawl(RuntimeSpider)
    process.start()
    return output


async def run_async(candidate: str, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if candidate == "crawlee":
        return await crawlee(records)
    if candidate == "crawl4ai":
        return await crawl4ai(records)
    if candidate == "playwright":
        return await playwright(records)
    raise ValueError(candidate)


def main() -> None:
    payload = json.load(sys.stdin)
    candidate = payload["candidate"]
    records = payload["requests"]
    start = time.perf_counter()
    try:
        if candidate == "scrapling":
            results = scrapling(records)
        elif candidate == "scrapy":
            results = scrapy(records)
        else:
            results = asyncio.run(run_async(candidate, records))
        response = {
            "candidate": candidate,
            "startup_and_batch_ms": round((time.perf_counter() - start) * 1000, 3),
            "observations": results,
        }
    except Exception as exc:
        response = {
            "candidate": candidate,
            "startup_and_batch_ms": round((time.perf_counter() - start) * 1000, 3),
            "adapter_error": f"{type(exc).__name__}:{exc}",
            "observations": [],
        }
    json.dump(response, sys.stdout, separators=(",", ":"))


if __name__ == "__main__":
    main()
