"""Opt-in mixed proof: live licensed public sources, controlled subscriber identity.

Not a production or Google-login certification. No model or paid provider is used.
Must use a new empty directory; canonical production data is never opened.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import threading
from datetime import UTC, datetime, timedelta
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

from application.observation_intelligence import QuerySpec, SourceCapability
from application.observation_intelligence.contracts import geo
from pipeline.entity_resolution.gleif_registry import RIGHTS
from pipeline.observation_intelligence import TedSearchAdapter, UrllibTedTransport
from tests.contracts.test_product_mcp_http_socket import _send
from tests.integration.test_organization_admission_e2e import _pilot
from tests.integration.test_product_mcp_e2e import Client
from tests.integration.test_subscriber_composition import _build
from tools.runtime.organization_registry import build_registry_source
from tools.runtime.service import RuntimeConfig, build_runtime, make_handler


def run(root: Path, sha: str) -> dict[str, object]:
    root.mkdir(parents=True, exist_ok=False)
    registry = build_registry_source(
        {
            "AXIGNAL_ORGANIZATION_REGISTRY_PROVIDER": "gleif",
            "AXIGNAL_ORGANIZATION_REGISTRY_RIGHTS": RIGHTS,
        },
        root,
    )
    facade = _build(root, pilot=True, identity_source=registry)
    token, _tenant = _pilot(facade, root, "synthetic:frontier-live-identity")
    host = build_runtime(
        RuntimeConfig(
            environment="production",
            bind_host="127.0.0.1",
            port=0,
            code_sha=sha,
            data_dir=root / "host",
            web_root=Path(__file__).resolve().parents[3] / "apps" / "web",
        )
    )
    host.subscriber = facade
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(host))
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    address = str(server.server_address[0]), int(server.server_address[1])
    headers = [
        ("Authorization", f"Bearer {token}"),
        ("Origin", "https://axignal.com"),
        ("Content-Type", "application/json"),
    ]

    def http(method, path, payload=None):
        status, response_headers, body = _send(
            address,
            method,
            path,
            None if payload is None else json.dumps(payload).encode(),
            headers,
        )
        return status, response_headers, json.loads(body)

    try:
        status, _, added = http(
            "POST",
            "/subscriber/portfolio",
            {
                "action": "add",
                "requestRef": "live:gleif:first",
                "locator": "LEI 5493001KJTIIGC8Y1R12",
            },
        )
        result = {
            "at": datetime.now(UTC).isoformat(),
            "sourceSha": sha,
            "identityProvider": "CONTROLLED_SYNTHETIC_OIDC",
            "pilotAuthority": "SYNTHETIC_INVITATION_REAL_REDEMPTION",
            "registry": "LIVE_GLEIF_CC0",
            "addedStatus": status,
            "added": added,
            "externalModels": 0,
            "productionTouched": False,
        }
        if status == 200 and "focusId" in added:
            focus = str(added["focusId"])
            status, cache, output = http("GET", f"/subscriber/organizations/{focus}/output")
            axent_status, _, axent = http(
                "POST",
                f"/subscriber/organizations/{focus}/axent",
                {
                    "question": "What economic opportunities and evidence are known?",
                    "locale": "en",
                },
            )
            client = Client(facade)
            client.connect(token)
            mcp = client.call("get_xeed_overview", xeed_id=focus)
            restarted = _build(
                root,
                pilot=True,
                identity_source=build_registry_source(
                    {
                        "AXIGNAL_ORGANIZATION_REGISTRY_PROVIDER": "gleif",
                        "AXIGNAL_ORGANIZATION_REGISTRY_RIGHTS": RIGHTS,
                    },
                    root,
                ),
            )
            after = restarted.handle(
                "GET",
                f"/subscriber/organizations/{focus}/output",
                {
                    "Authorization": f"Bearer {token}",
                },
            )
            assert status == axent_status == after.status == 200
            assert "no-store" in cache["Cache-Control"] and not mcp["error"]
            assert axent["grounding"]["modelCalls"] == 0
            assert output["projection"]["organization"] == after.body["projection"]["organization"]
            result.update(
                {
                    "subscriberStatus": status,
                    "subscriber": output,
                    "axentStatus": axent_status,
                    "axent": axent,
                    "mcp": mcp,
                    "restartStatus": after.status,
                    "websiteBinding": "UNKNOWN_NO_REGISTRY_ATTESTATION",
                    "capabilityAndFit": "UNKNOWN_NO_ADMITTED_CAPABILITY",
                }
            )
        else:
            result["identityAdmission"] = "UNAVAILABLE_OR_PENDING_NO_FABRICATED_CANONICAL_WRITE"
        with sqlite3.connect(root / "canonical-organizations.sqlite3") as db:
            result["canonicalIdentities"] = db.execute(
                "SELECT COUNT(*) FROM canonical_legal_identities"
            ).fetchone()[0]
        now = datetime.now(UTC)
        query = QuerySpec(
            (),
            (geo("EU/ES"),),
            frozenset({SourceCapability.PUBLIC_PROCUREMENT_OPPORTUNITIES}),
            published_since=now - timedelta(days=7),
        )
        demand = TedSearchAdapter(
            UrllibTedTransport(timeout_s=5), clock=lambda: now, limit=3
        ).search(query, page=1)
        result["independentLiveDemand"] = {
            "failure": demand.failure,
            "requests": demand.requests,
            "costMicrounits": demand.amount_microunits,
            "totalAvailable": demand.total_available,
            "relationToOrganization": "UNKNOWN_NOT_A_FIT_ASSERTION",
            "notices": [
                {
                    "id": r.record_id,
                    "title": r.title,
                    "source": r.source_url,
                    "publishedAt": r.published_at.isoformat(),
                }
                for r in demand.records
            ],
        }
        (root / "proof.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return result
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--public-source-probe", action="store_true", required=True)
    args = parser.parse_args()
    # Do not inherit any optional production/provider flags, configurations or secrets.
    safe_env = {
        k: v
        for k, v in os.environ.items()
        if k.upper()
        in {
            "PATH",
            "SYSTEMROOT",
            "WINDIR",
            "TEMP",
            "TMP",
            "OPENSSL_CONF",
            "SSL_CERT_FILE",
            "SSL_CERT_DIR",
        }
    }
    with patch.dict(os.environ, safe_env, clear=True):
        proof = run(args.data_dir.resolve(), args.sha)
    print(
        json.dumps(
            {k: proof[k] for k in proof if k not in {"subscriber", "axent", "mcp", "added"}},
            indent=2,
            ensure_ascii=False,
        )
    )
