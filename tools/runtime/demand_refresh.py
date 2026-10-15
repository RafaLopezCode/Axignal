"""Read the open-demand window again so stored calls carry what adapters now read.

Daily ingestion only fetches what was published since the last run, so a fact an adapter
learns to read later (a call's main object and contract nature) reaches stored calls only
as they are replaced. This one-off command re-reads each complete, already ingested
open-demand slice and updates its records; it never changes a slice's state, so reads stay
exactly as they were if it stops early. Operator-run only: it is not part of the schedule.

Usage: AXIGNAL_DATA_DIR=... python -m tools.runtime.demand_refresh [--max-pages 60] [--only ES]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

from application.observation_intelligence.contracts import SourceCapability
from application.world_demand.index import WorldDemandIngestor


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-pages", type=int, default=60, help="Bound per slice")
    parser.add_argument("--only", action="append", default=[], help="ISO country, repeatable")
    args = parser.parse_args(argv)
    data = os.getenv("AXIGNAL_DATA_DIR", "").strip()
    if not data:
        print(json.dumps({"state": "NOT_CONFIGURED"}))
        sys.exit(2)
    from pipeline.observation_intelligence import TedSearchAdapter, UrllibTedTransport
    from pipeline.observation_intelligence.placsp import (
        PLACSP_SOURCE_ID,
        PlacspFeedAdapter,
        UrllibPlacspTransport,
    )
    from pipeline.world_demand.sqlite_store import SqliteWorldDemandIndex

    def clock() -> datetime:
        return datetime.now(UTC)

    index = SqliteWorldDemandIndex(Path(data).resolve() / "world-demand-index.sqlite3")
    ingestor = WorldDemandIngestor(
        feeds={
            "ted-search-v3": TedSearchAdapter(UrllibTedTransport(), clock=clock),
            # Awards are not re-read: only the open calls' own facts are refreshed.
            PLACSP_SOURCE_ID: PlacspFeedAdapter(UrllibPlacspTransport(), clock=clock),
        },
        store=index,
        clock=clock,
    )
    only = {c.upper() for c in args.only}
    reports = [
        ingestor.refresh_records(state.slice, max_pages=args.max_pages)
        for state in index.demanded()
        if state.complete
        and state.ingested_at is not None
        and state.slice.kind is SourceCapability.PUBLIC_PROCUREMENT_OPPORTUNITIES
        and (not only or state.slice.jurisdiction.rsplit("/", 1)[-1] in only)
    ]
    print(
        json.dumps(
            {
                "state": "DONE",
                "slices": [
                    {
                        "slice": r.slice_key,
                        "pages": r.pages,
                        "records": r.records,
                        "complete": r.complete,
                        "failure": r.failure,
                    }
                    for r in reports
                ],
            }
        )
    )


if __name__ == "__main__":
    main()
