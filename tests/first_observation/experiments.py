"""Spec 063 cost/value experiments: CURRENT BASELINE vs OPTIMIZED, same composition.

Run: ``uv run python -m tests.first_observation.experiments OUT.json``. The network is
the controlled harness (websites, TED, System One); counts are measured from it, the
USD figures use the vendor-published Jev price on the stand-in's token counts (the
stand-in's tokens are an ESTIMATE of real Jev tokens, never a measurement of Jev).
"""

from __future__ import annotations

import json
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path
from typing import Any

from application.first_observation.rights import NoContentRights
from application.world_demand.index import per_focus_requests, world_slice_requests
from pipeline.source_acquisition import ContentAddressedArtifactStore
from tests.first_observation import harness
from tests.first_observation.harness import (
    BAKERY_FR,
    FORBIDDEN,
    KNOWN,
    PLACEHOLDER,
    SAAS_IE,
    SCHOOL_AR,
    SOLAR_ES,
    World,
    build,
    runtime,
)
from tests.integration.test_organization_admission_e2e import _add, _headers, _pilot, _portfolio
from tests.organization_admission.registry_fixture import ControlledRegistry, entity, lei

PROFILES = (
    ("A solar installer, Spain", SOLAR_ES),
    ("B language school, Arkansas", SCHOOL_AR),
    ("C SaaS serving globally", SAAS_IE),
    ("D local bakery, France", BAKERY_FR),
    ("E site without evidence", PLACEHOLDER),
    ("F known canonical organization", KNOWN),
    ("robots.txt forbids", FORBIDDEN),
)


def _registry(root: Path) -> ControlledRegistry:
    artifacts = ContentAddressedArtifactStore(root / "artifacts")
    return ControlledRegistry(
        [
            entity(
                artifacts,
                legal_name="Solartec Energía SL",
                lei_value=lei("SOLARTEC0000000001"),
                websites=(KNOWN,),
            )
        ]
    )


def _run(
    root: Path, *, enabled: bool, semantic: bool, rights: Any = "registered"
) -> list[dict[str, Any]]:
    rows = []
    for label, url in PROFILES:
        world = World()
        base = Path(tempfile.mkdtemp(dir=root))
        facade = build(
            base,
            world,
            enabled=enabled,
            semantic=semantic,
            identity_source=_registry(base),
            rights=rights,
        )
        token, _ = _pilot(facade, base, f"subject:{label}")
        started = time.perf_counter()
        added = _add(facade, token, "add:1", url)
        request_ms = (time.perf_counter() - started) * 1000
        started = time.perf_counter()
        drained = 0 if runtime(facade) is None else runtime(facade).drain()
        job_ms = (time.perf_counter() - started) * 1000
        (item,) = _portfolio(facade, token)
        read = facade.handle(
            "GET", f"/subscriber/organizations/{item['focusId']}/output", _headers(token)
        )
        view = read.body.get("firstObservation") if read.status == 200 else None
        kinds = Counter(d["kind"] for d in (view or {}).get("discoveries", ()))
        proof = None
        if enabled:
            proof = runtime(facade).store.proof(
                str(facade.identity.authenticate(token).tenant_id), item["focusId"]
            )
        ledger = (proof or {}).get("ledger", {})
        rows.append(
            {
                "profile": label,
                "addState": added.body.get("state"),
                "observationState": None if view is None else view.get("state"),
                "firstProofReady": bool(view and view.get("firstProofReady")),
                "discoveries": dict(kinds),
                "evidenceBackedDiscoveries": sum(
                    v for k, v in kinds.items() if k not in {"SIGNIFICANT_UNKNOWN"}
                ),
                "groundedUnknowns": kinds.get("SIGNIFICANT_UNKNOWN", 0),
                "httpRequests": len(world.sites.requests),
                "tedRequests": len(world.ted.queries) + len(world.ted.pages),
                "jevCalls": len(world.judge.calls),
                "jevInputTokensEstimated": ledger.get("jevInputTokens", {}).get("value", 0),
                "jevUsdVendorPublishedPrice": ledger.get("jevUsd", {}).get("value"),
                "lunaCalls": ledger.get("lunaCalls", {}).get("value", 0),
                "jobsRun": drained,
                "requestLatencyMs": round(request_ms, 1),
                "jobLatencyMs": round(job_ms, 1),
                "decisions": ledger.get("decisions", []),
            }
        )
    return rows


def _reuse(root: Path) -> dict[str, Any]:
    """Tenant 2 asks for the same site; tenant 3 a different company in the same country."""
    world = World()
    base = Path(tempfile.mkdtemp(dir=root))
    harness.PAGES["https://sol-levante.example.com/"] = harness.PAGES[SOLAR_ES].replace(
        "Solaria Norte", "Sol Levante"
    )
    facade = build(base, world)
    steps = []
    for subject, url in (
        ("t1", SOLAR_ES),
        ("t2", SOLAR_ES),
        ("t3", "https://sol-levante.example.com/"),
    ):
        before = (len(world.sites.requests), len(world.ted.queries), len(world.ted.pages))
        token, _ = _pilot(facade, base, f"subject:{subject}")
        _add(facade, token, "add:1", url)
        runtime(facade).drain()
        if subject == "t1":
            runtime(facade).ingest_demanded()
        after = (len(world.sites.requests), len(world.ted.queries), len(world.ted.pages))
        steps.append(
            {
                "tenant": subject,
                "site": url,
                "newHttpRequests": after[0] - before[0],
                "newTedSearches": after[1] - before[1],
                "newTedIngestionPages": after[2] - before[2],
            }
        )
    return {"steps": steps}


def _scale() -> dict[str, Any]:
    rows = []
    for foci in (10, 100, 1000, 10000):
        pull = per_focus_requests(foci=foci, capabilities=2, markets=1, questions=2, cadence_days=1)
        slices = world_slice_requests(
            slices=min(2 * 27, 2 * max(1, foci // 50)), daily_notices_per_slice=300, page_size=100
        )
        rows.append(
            {"foci": foci, "perFocusPullRequestsPerDay": pull, "worldSliceRequestsPerDay": slices}
        )
    return {
        "basis": "ESTIMATED",
        "assumptions": {
            "capabilitiesPerFocus": 2,
            "marketsPerFocus": 1,
            "demandQuestions": 2,
            "demandCadenceDays": 1,
            "slices": "2 notice kinds x countries touched (at most 27 EU members); one country per 50 Foci",
            "newNoticesPerSlicePerDay": "300 (ESTIMATED, not measured on TED)",
            "pageSize": 100,
        },
        "rows": rows,
    }


def main(out: str) -> None:
    root = Path(tempfile.mkdtemp())
    result = {
        "baseline": _run(root, enabled=False, semantic=False),
        "optimizedSemanticOff": _run(root, enabled=True, semantic=False),
        "optimizedSemanticOn": _run(root, enabled=True, semantic=True),
        # Production default: no governed content rights registered for any website.
        "optimizedNoContentRights": _run(
            root, enabled=True, semantic=True, rights=NoContentRights()
        ),
        "reuse": _reuse(root),
        "scale": _scale(),
    }
    Path(out).write_text(json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8")
    for key in (
        "baseline",
        "optimizedSemanticOff",
        "optimizedSemanticOn",
        "optimizedNoContentRights",
    ):
        print(key)
        for row in result[key]:
            print(
                f"  {row['profile']:32} {row['observationState']!s:32} ready={row['firstProofReady']!s:5} "
                f"evid={row['evidenceBackedDiscoveries']:2} unk={row['groundedUnknowns']} http={row['httpRequests']} "
                f"ted={row['tedRequests']} jev={row['jevCalls']} req_ms={row['requestLatencyMs']} job_ms={row['jobLatencyMs']}"
            )
    print(json.dumps(result["reuse"]))


if __name__ == "__main__":
    main(sys.argv[1])
