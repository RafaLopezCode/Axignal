"""One-pass, exact-target public trial for P0-SOURCE-01C (Scrapy only)."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results" / "public-web"
TEMP_ROOT = Path(os.environ.get("P0_SOURCE01B_ROOT", ""))
CONTROLLER = TEMP_ROOT / "controller" / ".venv" / "Scripts" / "python.exe"
SCRAPY_PYTHON = TEMP_ROOT / "scrapy" / ".venv" / "Scripts" / "python.exe"

ALLOWLIST = {
    "www.selenium.dev": [
        "/documentation/",
        "/selenium/web/",
        "/sponsor/",
        "/blog/",
        "/__p0-source-01c-not-found__",
        "/",
    ],
    "www.w3.org": ["/WAI/ER/tests/xhtml/testfiles/resources/pdf/"],
}

TARGETS = [
    (
        "P1",
        "https://www.selenium.dev/documentation/about/copyright/",
        "static project identity and license",
    ),
    ("P2", "https://www.selenium.dev/documentation/", "bounded site page 1 of 2"),
    ("P2", "https://www.selenium.dev/documentation/webdriver/", "bounded site page 2 of 2"),
    (
        "P3",
        "https://www.selenium.dev/selenium/web/dynamic.html",
        "JS test page; HTTP baseline only",
    ),
    (
        "P4",
        "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
        "public test PDF; preserve original bytes",
    ),
    ("P5", "https://www.selenium.dev/blog/", "dated temporal project publication page"),
    ("P6", "https://www.selenium.dev/sponsor/", "public sponsor / relationship evidence page"),
    (
        "P7-Q1",
        "https://www.selenium.dev/documentation/about/copyright/",
        "organization overview; initial observation",
    ),
    ("P7-Q2", "https://www.selenium.dev/sponsor/", "targeted second source after explicit G1"),
    (
        "P8-REDIRECT",
        "http://www.selenium.dev/",
        "one HTTP-to-HTTPS redirect; do not follow automatically",
    ),
    (
        "P8-FAILURE",
        "https://www.selenium.dev/__p0-source-01c-not-found__/",
        "one explicit not-found observation",
    ),
]


def main() -> int:
    if not TEMP_ROOT.is_dir() or not CONTROLLER.is_file() or not SCRAPY_PYTHON.is_file():
        raise SystemExit(
            "isolated controller/Scrapy environment missing; no public request dispatched"
        )
    sys.path.insert(0, str(ROOT))
    from public_guard import validate_public_url
    from run_candidate_bakeoff import MeasuredProcess

    os.environ["P0_SOURCE01C_ALLOWED_TARGETS"] = json.dumps(ALLOWLIST, separators=(",", ":"))
    for _, url, _ in TARGETS:
        validate_public_url(url)

    stamp = datetime.now(UTC).isoformat()
    policy = {
        "experiment": "P0-SOURCE-01C",
        "decided_at": stamp,
        "targets": {
            "https://www.selenium.dev/": {
                "robots": "https robots.txt returned 200 with User-agent: * and no disallow; HTTP robots.txt returned 301 to the HTTPS robots URL, then verified there.",
                "rights": "Selenium's official copyright page says Selenium-origin website documentation is Apache-2.0.",
                "decision": "PERMITTED_FOR_ONE_LOW_RATE_TECHNICAL_GET_PER_EXACT_ALLOWLISTED_PATH",
                "evidence": [
                    "https://www.selenium.dev/robots.txt",
                    "https://www.selenium.dev/documentation/about/copyright/",
                ],
            },
            "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf": {
                "robots": "W3C robots.txt has no disallow matching this exact /WAI/ER/tests path.",
                "rights": "WAI material-use policy permits copying complete WAI documents with attribution; preserve source URL and copyright metadata.",
                "decision": "PERMITTED_FOR_ONE_LOW_RATE_PDF_GET_AND_RAW_BYTE_RETENTION_WITH_ATTRIBUTION",
                "evidence": [
                    "https://www.w3.org/robots.txt",
                    "https://www.w3.org/WAI/about/using-wai-material/",
                ],
            },
        },
        "exclusions": {
            "httpbin": "excluded because robots/terms policy was unavailable; unnecessary for redirect/failure workload.",
            "python.org": "excluded to keep the matrix on the two explicitly policy-screened sources.",
            "scrapling": "not dispatched until a verified streaming/body-size cap is available.",
            "browser": "not dispatched until a hard response cap and redirect-hop enforcement can be guaranteed.",
        },
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "policy-decisions.json").write_text(
        json.dumps(policy, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    records = []
    for index, (workload, url, purpose) in enumerate(TARGETS, 1):
        if workload == "P7-Q2":
            continue
        records.append(
            {
                "research_question_id": f"P0-SOURCE-01C-{workload}-{index:02d}",
                "workload_id": workload,
                "iteration": 1,
                "url": url,
                "mode": "http",
                "deadline_ms": 8000,
                "expected_slots": 1,
                "expected": purpose,
                "policy_decision": "PERMITTED_FOR_SINGLE_BOUNDED_GET; robots and rights basis recorded in report",
            }
        )

    worker_dir = TEMP_ROOT / "worker-cwd" / "p0-source-01c-public"
    worker_dir.mkdir(parents=True, exist_ok=True)
    env = {key: os.environ[key] for key in ("PATH", "SYSTEMROOT", "WINDIR") if key in os.environ}
    env.update(
        {
            "P0_SOURCE01B_ROOT": str(TEMP_ROOT),
            "P0_SOURCE01B_WORKDIR": str(worker_dir),
            "P0_SOURCE01C_PUBLIC_TRIAL": "1",
            "P0_SOURCE01C_ALLOWED_TARGETS": json.dumps(ALLOWLIST, separators=(",", ":")),
            "PYTHONNOUSERSITE": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "TEMP": str(worker_dir),
            "TMP": str(worker_dir),
            "USERPROFILE": str(worker_dir),
            "APPDATA": str(worker_dir),
            "LOCALAPPDATA": str(worker_dir),
        }
    )
    payload = {"candidate": "scrapy", "requests": records}
    process = MeasuredProcess()
    response, resource = process.run(
        [str(SCRAPY_PYTHON), str(ROOT / "runtime_candidate_worker.py")], payload, env
    )
    observations = response.get("observations", [])
    by_id = {o.get("request_identity"): o for o in observations}

    q1_id = "P0-SOURCE-01C-P7-Q1-08"
    q2_id = "P0-SOURCE-01C-P7-Q2-09"
    q1 = by_id.get(q1_id, {})
    q2 = {}
    q2_response = None
    q2_resource = None
    if q1.get("status") == 200 and q1.get("content_fingerprint"):
        q2_record = {
            "research_question_id": q2_id,
            "workload_id": "P7-Q2",
            "iteration": 1,
            "url": TARGETS[8][1],
            "mode": "http",
            "deadline_ms": 8000,
            "expected_slots": 1,
            "expected": "targeted second public resource after the explicit G1 gap",
            "targeted_gap_input": {
                "gap_id": "P0-SOURCE-01C-G1",
                "basis_observation_hash": q1["content_fingerprint"],
            },
            "policy_decision": "PERMITTED_FOR_SINGLE_BOUNDED_GET; policy manifest recorded before dispatch",
        }
        q2_env = dict(env)
        q2_dir = TEMP_ROOT / "worker-cwd" / "p0-source-01c-followup"
        q2_dir.mkdir(parents=True, exist_ok=True)
        q2_env["P0_SOURCE01B_WORKDIR"] = str(q2_dir)
        q2_response, q2_resource = process.run(
            [str(SCRAPY_PYTHON), str(ROOT / "runtime_candidate_worker.py")],
            {"candidate": "scrapy", "requests": [q2_record]},
            q2_env,
        )
        observations.extend(q2_response.get("observations", []))
        by_id = {o.get("request_identity"): o for o in observations}
        q2 = by_id.get(q2_id, {})
    artifacts = RESULTS / "artifacts"
    artifacts.mkdir(exist_ok=True)
    for observation in observations:
        observation["source_identity"] = urlsplit(observation["source_uri"]).hostname
        observation["rights_metadata"] = (
            "P0-SOURCE-01C limited public technical trial; policy basis is recorded in latest-public-web.json"
        )
        observation["acquisition_config"]["rights_policy"] = observation.get("policy_decision")
        encoded = observation.get("raw_body_base64")
        body = base64.b64decode(encoded) if encoded else b""
        if body:
            digest = hashlib.sha256(body).hexdigest()
            observation["content_fingerprint"] = digest
        if body and observation.get("artifact_type", "").lower().startswith("application/pdf"):
            artifact = artifacts / f"{digest}.pdf"
            artifact.write_bytes(body)
            observation["raw_artifact"] = str(artifact.relative_to(RESULTS)).replace("\\", "/")
        observation.pop("raw_body_base64", None)
        observation["retrieved_at"] = observation.get("retrieved_at") or stamp

    followup = {
        "Q1": {
            "request_id": q1_id,
            "url": TARGETS[7][1],
            "observation_hash": q1.get("content_fingerprint"),
        },
        "O1": {"status": q1.get("status"), "failure_state": q1.get("failure_state")},
        "G1": {
            "gap_id": "P0-SOURCE-01C-G1",
            "definition": "O1 is an organization overview; sponsor/relationship details require a targeted second public resource",
            "basis_hash": q1.get("content_fingerprint"),
        },
        "Q2": {"request_id": q2_id, "url": TARGETS[8][1], "derived_from_gap": "P0-SOURCE-01C-G1"},
        "O2": {
            "status": q2.get("status"),
            "failure_state": q2.get("failure_state"),
            "observation_hash": q2.get("content_fingerprint"),
        },
        "semantic_truth_claimed": False,
        "q2_dispatch_condition": "Q1 succeeded with status 200 and a content fingerprint",
        "q2_dispatched": q2_response is not None,
        "lineage_preserved": bool(
            q1.get("content_fingerprint")
            and q2.get("content_fingerprint")
            and q2.get("targeted_gap_input", {}).get("basis_observation_hash")
            == q1.get("content_fingerprint")
        ),
    }

    result = {
        "experiment": "P0-SOURCE-01C",
        "captured_at": stamp,
        "candidate": "Scrapy 2.19.0",
        "candidate_scope": "only candidate satisfying the enforced 256 KiB response cap; Scrapling is not dispatched because its public Fetcher API exposes no streaming/body-size cap",
        "policy_basis": {
            "selenium_https_robots": "GET 200, User-agent: * with no disallow; retrieved immediately before target trial.",
            "selenium_http_robots": "GET 301 to https://www.selenium.dev/robots.txt; redirect destination policy separately retrieved as allow-all.",
            "w3c_robots": "official robots.txt does not disallow selected /WAI/ER/tests/ path; web source checked 2026-09-25",
            "content_rights": "Selenium-origin docs are Apache-2.0; WAI material permits complete-document reuse with attribution; only one PDF retained with source URL/hash metadata.",
            "httpbin": "excluded; no robots/terms decision recorded, not needed because P8 uses the approved Selenium HTTP-to-HTTPS redirect and one explicit 404 target.",
        },
        "targets": [{"workload": w, "url": u, "purpose": p} for w, u, p in TARGETS],
        "security_controls": {
            "schemes": ["http", "https"],
            "host_and_path_allowlist": ALLOWLIST,
            "public_dns_resolution_before_dispatch": True,
            "automatic_redirects": False,
            "redirects_followed": 0,
            "deadline_ms": 8000,
            "response_max_bytes": 262144,
            "concurrency": 1,
            "candidate_cookies": False,
            "environment": "minimal clean process env; no proxies, repo credentials, browser, or account cookies",
            "file_urls_or_executable_downloads": False,
            "content_handling": "untrusted data; no execution or semantic extraction",
            "dns_pinning": False,
        },
        "run": response,
        "q2_run": q2_response,
        "resource": resource,
        "q2_resource": q2_resource,
        "observations": observations,
        "targeted_followup": followup,
        "browser_and_scrapling_browser": {
            "status": "NOT_DISPATCHED",
            "reason": "Playwright route interception cannot enforce a hard response-body cap or inspect every redirect hop; Scrapling DynamicFetcher does not offer a per-response body cap in this adapter. Public browser acquisition is deferred until a bounded transport guard is available.",
        },
        "other_candidates": {
            "scrapling": "NOT_DISPATCHED: no verified hard response-size enforcement in its public HTTP Fetcher interface",
            "crawlee": "EXCLUDED per CTO order; previous fixture evidence shows no material reason to reopen",
            "crawl4ai": "EXCLUDED per CTO order; previous anti-bot classification and missing raw PDF issue remain unresolved",
            "playwright": "NOT_DISPATCHED: public browser cap/redirect guard not sufficient",
        },
    }
    path = RESULTS / "latest-public-web.json"
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "result": str(path),
                "status": response.get("candidate"),
                "observations": len(observations),
                "resource": resource,
                "adapter_error": response.get("adapter_error"),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
