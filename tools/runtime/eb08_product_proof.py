"""Operational EB-08 store/load/recovery harness.

The harness exercises the real FirstProofStore persistence contract with
isolated subscriber projections. It measures work; it does not invent SLA claims.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

from tools.runtime.first_proof import FirstProofStore


@dataclass(frozen=True, slots=True)
class ProductProofLoadResult:
    organization_count: int
    write_ms: float
    read_ms: float
    database_bytes: int
    recovered_count: int
    backup_ms: float
    backup_bytes: int
    backup_recovered_count: int
    isolated: bool


def _projection(index: int) -> dict[str, object]:
    organization_id = f"org:eb08:{index:03d}"
    xeed_id = f"xeed:eb08:{index:03d}"
    signal_id = f"xignal:eb08:{index:03d}"
    return {
        "realityLevel": "EB08_SYNTHETIC_LOAD_HARNESS",
        "runtimeCodeSha": "synthetic-load-harness",
        "lifecycleStatus": "LIVE",
        "context": {"id": xeed_id, "label": f"Organization {index:03d}"},
        "organization": {"id": organization_id, "name": f"Organization {index:03d}"},
        "nodes": [
            {
                "id": signal_id,
                "nodeKind": "XIGNAL",
                "title": f"Signal {index:03d}",
                "whyAttention": "Synthetic load-harness signal; not economic truth.",
                "interpretation": "Synthetic isolation proof only.",
                "uncertainty": "No economic claim is made by this harness.",
                "epistemicState": "UNKNOWN",
                "currentness": "UNKNOWN",
                "observedAt": datetime(2026, 10, 5, 10, 0, tzinfo=UTC).isoformat(),
                "evidenceAccess": "UNAVAILABLE",
                "sourceRefs": [],
                "observationSupportRefs": [],
                "unknowns": ["Synthetic load harness."],
                "evidenceNarrative": {
                    "xignalId": signal_id,
                    "focusStepId": f"{signal_id}:step",
                    "steps": [
                        {
                            "id": f"{signal_id}:step",
                            "kind": "XIGNAL",
                            "label": "Synthetic isolation proof only.",
                            "sourceRef": None,
                            "observedAt": None,
                            "currentness": "UNKNOWN",
                            "artifactVerified": None,
                        }
                    ],
                },
            }
        ],
        "temporalHistory": {"disposition": "EMPTY", "items": []},
        "memberships": [{"from": xeed_id, "to": signal_id, "meaning": "Xeed observes Xignal"}],
        "today": {"disposition": "EMPTY", "items": []},
        "reloadContinuity": "PERSISTED_RUNTIME_READ_MODEL",
    }


def backup_first_proof_store(
    source_path: str | Path,
    backup_path: str | Path,
) -> float:
    """Create one consistent SQLite backup and return measured duration in ms."""

    source = Path(source_path)
    destination = Path(backup_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        destination.unlink()
    started = perf_counter()
    with sqlite3.connect(source) as source_db, sqlite3.connect(destination) as backup_db:
        source_db.backup(backup_db)
    return (perf_counter() - started) * 1000


def run_store_load_harness(
    database_path: str | Path,
    *,
    organization_count: int,
) -> ProductProofLoadResult:
    """Measure isolated persistence/recovery for 1/2/100-style product contexts."""

    if organization_count < 1:
        raise ValueError("organization_count must be positive")
    path = Path(database_path)
    if path.exists():
        path.unlink()

    store = FirstProofStore(path)
    started = perf_counter()
    for index in range(1, organization_count + 1):
        projection = _projection(index)
        context = projection["context"]
        assert isinstance(context, dict)
        store.append(
            xeed_id=str(context["id"]),
            created_at=datetime(2026, 10, 5, 10, index % 60, tzinfo=UTC),
            target_uri=f"https://example.invalid/{index:03d}",
            projection=projection,
        )
    write_ms = (perf_counter() - started) * 1000

    read_started = perf_counter()
    isolated = True
    for index in range(1, organization_count + 1):
        xeed_id = f"xeed:eb08:{index:03d}"
        stored_projection = store.get(xeed_id)
        if stored_projection is None:
            isolated = False
            continue
        organization = stored_projection.get("organization")
        nodes = stored_projection.get("nodes")
        if not isinstance(organization, dict) or organization.get("id") != f"org:eb08:{index:03d}":
            isolated = False
        if (
            not isinstance(nodes, list)
            or len(nodes) != 1
            or not isinstance(nodes[0], dict)
            or nodes[0].get("id") != f"xignal:eb08:{index:03d}"
        ):
            isolated = False
    read_ms = (perf_counter() - read_started) * 1000

    reopened = FirstProofStore(path)
    recovered_count = sum(
        reopened.get(f"xeed:eb08:{index:03d}") is not None
        for index in range(1, organization_count + 1)
    )

    backup_path = path.with_name(f"{path.stem}.backup{path.suffix}")
    backup_ms = backup_first_proof_store(path, backup_path)
    restored = FirstProofStore(backup_path)
    backup_recovered_count = sum(
        restored.get(f"xeed:eb08:{index:03d}") is not None
        for index in range(1, organization_count + 1)
    )
    return ProductProofLoadResult(
        organization_count=organization_count,
        write_ms=write_ms,
        read_ms=read_ms,
        database_bytes=path.stat().st_size,
        recovered_count=recovered_count,
        backup_ms=backup_ms,
        backup_bytes=backup_path.stat().st_size,
        backup_recovered_count=backup_recovered_count,
        isolated=isolated,
    )
