"""Isolated deployability preflight for the semantic layer (spec 062), inside the image.

Run it in the real subscriber runtime image with ``--network none``. It never calls
TypeSafe or Luna and never prints a credential.

``off``  proves a disabled configuration composes nothing: no SDK import, no
         credential read, no provider call.
``on``   proves the image can run the layer: the pinned SDK is installed, the mounted
         secret is a readable file, the real composition wires the TypeSafe adapter, the
         SDK's own client serialises requests and parses responses (only the network is
         replaced by an in-process transport), the demand screen judges, filters, costs
         and reuses, and Luna escalation stays at zero.

Settings come from the same file the runtime reads (``--settings``).
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from datetime import UTC, datetime, timedelta
from importlib import import_module
from importlib.metadata import version
from pathlib import Path
from typing import Any, cast

from application.observation_intelligence.contracts import (
    OpportunityFamily,
    SourceCapability,
    TaxonomyCode,
    geo,
)
from application.observation_intelligence.findings import ProcurementRecord
from application.observation_intelligence.loop import UNASSESSED_CONTEXT, OpportunityCandidate
from application.semantic_layer.cascade import SemanticCascade
from tools.runtime.semantic_layer import semantic_screen_from_env
from tools.runtime.subscriber_configuration import read_subscriber_settings_file

SDK_MODULES = ("typesafe_sdk", "cognition.providers.typesafe_system_one")


def _candidate(record_id: str, title: str, buyer: str, now: datetime) -> OpportunityCandidate:
    record = ProcurementRecord(
        record_id=record_id,
        source_id="ted-developer-search",
        kind=SourceCapability.PUBLIC_PROCUREMENT_OPPORTUNITIES,
        title=title,
        buyer_name=buyer,
        places=(geo("EU/ES/ES3/ES30/ES300"),),
        demand_codes=(TaxonomyCode("CPV", "09332000"),),
        published_at=now - timedelta(days=3),
        source_url=f"https://ted.europa.eu/en/notice/-/detail/{record_id}",
        deadline=(now + timedelta(days=20)).date().isoformat(),
    )
    return OpportunityCandidate(
        candidate_id=f"preflight:{record_id}",
        xeed_id="xeed:preflight",
        record=record,
        market=geo("EU/ES"),
        capability_ids=("solar-pv-installation",),
        matched_codes=(TaxonomyCode("CPV", "09332000"),),
        why_looked=("preflight",),
        missing_context=UNASSESSED_CONTEXT,
        observed_at=now,
        match_basis=("DIRECT_CAPABILITY_CODE",),
        opportunity_family=OpportunityFamily.PUBLIC_PROCUREMENT,
        demand_form="OPEN_CALL_FOR_TENDER",
    )


def _off(values: dict[str, str]) -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as folder:
        screen = semantic_screen_from_env(values, data_dir=Path(folder))
        created = sorted(p.name for p in Path(folder).iterdir())
    imported = [name for name in SDK_MODULES if name in sys.modules]
    ok = screen is None and not imported and not created
    return {"mode": "off", "ok": ok, "composed": screen is not None, "sdkImported": imported,
            "filesCreated": created, "providerCalls": 0}  # fmt: skip


def _on(values: dict[str, str]) -> dict[str, Any]:
    httpx2 = import_module("httpx2")  # the SDK's own HTTP stack, present only with it

    key_path = Path(values.get("AXIGNAL_TYPESAFE_API_KEY_FILE", ""))
    secret = {
        "path": str(key_path),
        "isFile": key_path.is_absolute() and key_path.is_file(),
        "nonEmpty": key_path.is_file() and key_path.stat().st_size > 0,
    }
    seen: list[dict[str, Any]] = []

    def provider(request: Any) -> Any:  # in-process stand-in for api.typesafe.ai
        body = json.loads(request.content)
        title = str(body["state"]["tender"]["title"]).lower()
        seen.append({"path": request.url.path, "bearer": request.headers.get("authorization", "").startswith("Bearer ") and len(request.headers["authorization"]) > 7, "questions": sorted(body["questions"])})  # fmt: skip
        solar = "fotovolt" in title
        fit = [0.02, 0.03, 0.05, 0.90] if solar else [0.94, 0.03, 0.02, 0.01]
        return httpx2.Response(200, json={
            "model": "jev-1.13.0",
            "usage": {"input_tokens": 300 + len(title), "output_tokens": 0},
            "answers": {
                "tender_capability_fit": {"type": "score", "score": 2.8 if solar else 0.1,
                    "confidence": max(fit), "legend": {str(i): str(i) for i in range(4)},
                    "probabilities": {str(i): p for i, p in enumerate(fit)}},
                "tender_delivery_mode": {"type": "choice", "choice": "CUSTOMER_SITE",
                    "confidence": 0.9, "probabilities": {"CUSTOMER_SITE": 0.9, "SHIPPED": 0.04,
                    "REMOTE_OR_DIGITAL": 0.03, "UNCLEAR": 0.03}},
            },
        })  # fmt: skip

    now = datetime.now(UTC)
    candidates = (
        _candidate(
            "700101-2026",
            "Instalación fotovoltaica de autoconsumo en edificios municipales",
            "Ayuntamiento de Getafe",
            now,
        ),
        _candidate(
            "700777-2026",
            "Servicio de limpieza de edificios municipales",
            "Ayuntamiento de Getafe",
            now,
        ),
    )
    with tempfile.TemporaryDirectory() as folder:
        screen = semantic_screen_from_env(
            values, data_dir=Path(folder), transport=httpx2.MockTransport(provider)
        )
        if screen is None:
            return {"mode": "on", "ok": False, "composed": False, "secret": secret}
        cascade = screen.cascade_factory()
        if not isinstance(cascade, SemanticCascade):
            return {"mode": "on", "ok": False, "composed": True, "secret": secret}
        first = screen.screen(candidates, now=now)
        requests_after_first = len(seen)
        second = screen.screen(candidates, now=now)
        judge = cascade.judge
    solar, cleaning = (first.screens[c.candidate_id] for c in candidates)
    usage_lines = cast(list[dict[str, Any]], first.usage["lines"])
    lines = {line["evaluator"]: line for line in usage_lines}
    result = {
        "mode": "on",
        "sdkVersion": version("typesafe-sdk"),
        "secret": secret,
        "adapter": type(judge).__name__,
        "model": judge.model,
        "reasoningEscalation": cascade.escalation is not None,
        "reasoningCallBudget": cascade.budget.max_reasoning_calls,
        "requests": seen[:requests_after_first],
        "solarFit": solar.best_fit,
        "solarRequiredModes": sorted(m.value for m in solar.required_modes),
        "cleaningUnrelated": cleaning.unrelated,
        "firstRunUsage": first.usage,
        "secondRunNewRequests": len(seen) - requests_after_first,
        "secondRunMemoryHits": second.usage["memoryHits"],
    }
    result["ok"] = bool(
        result["sdkVersion"] == "0.7.1"
        and secret["isFile"] and secret["nonEmpty"]
        and result["adapter"] == "TypeSafeSystemOneJudge"
        and not result["reasoningEscalation"] and result["reasoningCallBudget"] == 0
        and requests_after_first == 2
        and all(r["path"] == "/v1/systemone" and r["bearer"] for r in seen)
        and solar.best_fit == "CORE" and result["solarRequiredModes"] == ["CUSTOMER_SITE"]
        and cleaning.unrelated
        and lines["typesafe-system-one"]["calls"] == 2 and "luna-responses" not in lines
        and result["secondRunNewRequests"] == 0 and int(str(result["secondRunMemoryHits"])) == 4
    )  # fmt: skip
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("off", "on"))
    parser.add_argument("--settings", type=Path, required=True)
    args = parser.parse_args()
    values = read_subscriber_settings_file(args.settings)
    result = _off(values) if args.mode == "off" else _on(values)
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
