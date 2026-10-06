"""Operational PB-10 live Batch canary.

This tool only exercises governed research work. It does not write canonical
AXIGLAND state.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime
from pathlib import Path

from application.economic_discovery.continuous_observation import SharedObservationIntent
from cognition.async_research_canary import AsyncGovernedCanaryCoordinator
from cognition.providers.openai_batch import DurableBatchTransport
from cognition.providers.openai_sdk_batch import OpenAISdkBatchClient
from cognition.research_result_admission import EvidenceBackedResearchAdmission
from pipeline.continuous_observation.async_canary_store import (
    SqliteDurableCanaryExecutionStore,
)
from pipeline.continuous_observation.sqlite_store import (
    SqliteSharedObservationWorkMemory,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="D:/AXIGNAL/.runtime/pb10-canary")
    parser.add_argument("--env-file")
    parser.add_argument("--model", default="gpt-6-luna")
    parser.add_argument("--subject-id", default="org:axignal")
    parser.add_argument("--dimension-id", default="public_identity")
    parser.add_argument(
        "--requirement",
        default=(
            "Find current public evidence from https://axignal.com that identifies "
            "AXIGNAL and supports its public product identity."
        ),
    )
    return parser


def _load_env_file(path: str | None) -> None:
    if not path:
        return
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        os.environ[name.strip()] = value.strip()


def main() -> int:
    args = _parser().parse_args()
    _load_env_file(args.env_file)
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is not available to this process")

    root = Path(args.root)
    root.mkdir(parents=True, exist_ok=True)
    memory = SqliteSharedObservationWorkMemory(root / "work.sqlite3")
    store = SqliteDurableCanaryExecutionStore(root / "canary.sqlite3")

    intent = SharedObservationIntent(
        subject_id=args.subject_id,
        state_fingerprint="pb10-live-canary:v1",
        dimension_id=args.dimension_id,
        missing_requirements=(args.requirement,),
        research_policy_id="pb10-live-canary",
        research_policy_version="1",
        research_context_fingerprint="axignal-public-web:v1",
    )
    memory.enqueue(intent, "pb10-live-canary")

    coordinator = AsyncGovernedCanaryCoordinator(
        memory=memory,
        store=store,
        transport=DurableBatchTransport(OpenAISdkBatchClient()),
        admission=EvidenceBackedResearchAdmission(),
        authorized_model=args.model,
        max_batch_size=1,
    )
    now = datetime.now(UTC)
    tick = coordinator.tick(
        subject_id=args.subject_id,
        execution_id=f"pb10-live:{now.isoformat()}",
        work_keys=(intent.work_key,),
        now=now,
    )
    work = memory.get(intent.work_key)
    print(
        json.dumps(
            {
                "action": tick.action,
                "provider_batch_id": tick.provider_batch_id,
                "completed_work_keys": tick.completed_work_keys,
                "released_work_keys": tick.released_work_keys,
                "work_state": None if work is None else work.state.value,
                "canonical_write": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
