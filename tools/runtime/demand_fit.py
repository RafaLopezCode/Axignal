"""Judge the fit of open demand off the read path (spec 075), then live demand reads memory.

Runs after the daily ingestion (``observation_daily``) and in isolated golden and self-check
passes (``run_golden``). Off unless the semantic layer is configured; bounded by
``AXIGNAL_SEMANTIC_FIT_TOKEN_BUDGET``. World-level: public notices and catalog capabilities
only, never an organization's or a tenant's data.

Usage: AXIGNAL_DATA_DIR=... python -m tools.runtime.demand_fit [--capability ID ...]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path

from application.observation_intelligence.contracts import SourceCapability
from application.world_demand.fit import catalog_capabilities, judge_pairs, open_pairs


def run_demand_fit(
    root: Path,
    *,
    values: Mapping[str, str] | None = None,
    now: datetime | None = None,
    capabilities: Sequence[str] = (),
) -> dict[str, object]:
    from pipeline.world_demand.sqlite_store import SqliteWorldDemandIndex
    from tools.runtime.semantic_layer import fit_cascade_factory_from_env

    if values is None:
        # The runtime's own settings: the subscriber configuration file, then environment.
        from tools.runtime.subscriber_configuration import load_subscriber_settings

        configuration = os.getenv("AXIGNAL_SUBSCRIBER_CONFIGURATION_FILE")
        values = load_subscriber_settings(
            os.environ, configuration_file=Path(configuration) if configuration else None
        ).values
    factory = fit_cascade_factory_from_env(values, data_dir=root)
    if factory is None:
        return {"state": "LAYER_DISABLED"}
    moment = now or datetime.now(UTC)
    index = SqliteWorldDemandIndex(root / "world-demand-index.sqlite3")
    records = [
        record
        for state in index.demanded()
        if state.complete
        and state.ingested_at is not None
        and state.slice.kind is SourceCapability.PUBLIC_PROCUREMENT_OPPORTUNITIES
        for record in index.records(state.slice)
    ]
    pairs = open_pairs(records, catalog_capabilities(capabilities), today=moment.date().isoformat())
    run = judge_pairs(pairs, factory(), now=moment)
    return {"state": "DONE", **run.to_wire()}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capability", action="append", default=[])
    args = parser.parse_args(argv)
    data = os.getenv("AXIGNAL_DATA_DIR", "").strip()
    if not data:
        print(json.dumps({"state": "NOT_CONFIGURED"}))
        sys.exit(2)
    print(json.dumps(run_demand_fit(Path(data).resolve(), capabilities=args.capability)))


if __name__ == "__main__":
    main()
