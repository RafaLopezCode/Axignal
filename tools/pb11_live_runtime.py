"""PB-11 one-tick governed live research runtime.

CANARY only. This command does not enable a continuous autonomous loop and does
not write canonical AXIGLAND state.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

from application.economic_discovery.async_research_runtime import (
    LiveResearchBudgetPolicy,
    run_async_research_runtime_tick,
)
from application.economic_discovery.continuous_observation import SharedObservationIntent
from application.economic_discovery.research_runtime import (
    ResearchRuntimeMode,
    ResearchRuntimePolicy,
)
from application.economic_discovery.research_scheduler import AutonomousResearchPolicy
from cognition.async_research_canary import AsyncGovernedCanaryCoordinator
from cognition.live_research_runtime import (
    CanaryResearchRevalidator,
    GovernedAsyncResearchRunner,
)
from cognition.providers.openai_batch import DurableBatchTransport
from cognition.providers.openai_sdk_batch import OpenAISdkBatchClient
from cognition.research_result_admission import EvidenceBackedResearchAdmission
from pipeline.continuous_observation.async_canary_store import (
    SqliteDurableCanaryExecutionStore,
)
from pipeline.continuous_observation.live_budget_store import SqliteLiveResearchBudgetStore
from pipeline.continuous_observation.runtime_store import SqliteResearchRuntimeStore
from pipeline.continuous_observation.sqlite_store import (
    SqliteSharedObservationWorkMemory,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="D:/AXIGNAL/.runtime/pb11-live")
    parser.add_argument("--env-file")
    parser.add_argument("--model", default="gpt-6-luna")
    parser.add_argument("--subject-id", default="org:axignal")
    parser.add_argument("--set-kill-switch", choices=("on", "off"))
    parser.add_argument("--seed-canary", action="store_true")
    parser.add_argument(
        "--requirement",
        default=(
            "Find current public evidence from https://axignal.com that identifies "
            "AXIGNAL and supports its public product identity."
        ),
    )
    parser.add_argument("--max-batches", type=int, default=3)
    parser.add_argument("--max-jobs", type=int, default=3)
    parser.add_argument(
        "--max-cost-upper-bound-microunits",
        type=int,
        default=1_000_000,
        help="Conservative accounting ceiling, not a provider invoice.",
    )
    parser.add_argument(
        "--per-batch-cost-upper-bound-microunits",
        type=int,
        default=250_000,
        help="Operator-configured conservative charge reserved before each Batch submit.",
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
    runtime_store = SqliteResearchRuntimeStore(root / "runtime.sqlite3")
    execution_store = SqliteDurableCanaryExecutionStore(root / "canary.sqlite3")
    budget_store = SqliteLiveResearchBudgetStore(root / "budget.sqlite3")

    if args.set_kill_switch is not None:
        runtime_store.set_kill_switch(args.set_kill_switch == "on")

    if args.seed_canary:
        intent = SharedObservationIntent(
            subject_id=args.subject_id,
            state_fingerprint="pb11-live-canary:v1",
            dimension_id="public_identity",
            missing_requirements=(args.requirement,),
            research_policy_id="pb11-live-canary",
            research_policy_version="1",
            research_context_fingerprint="axignal-public-web:v1",
        )
        memory.enqueue(intent, "pb11-live-canary")

    coordinator = AsyncGovernedCanaryCoordinator(
        memory=memory,
        store=execution_store,
        transport=DurableBatchTransport(OpenAISdkBatchClient()),
        admission=EvidenceBackedResearchAdmission(),
        authorized_model=args.model,
        lease_for=timedelta(hours=26),
        max_batch_size=1,
    )
    runner = GovernedAsyncResearchRunner(
        memory=memory,
        ledger=memory,
        execution_store=execution_store,
        coordinator=coordinator,
        revalidator=CanaryResearchRevalidator(
            allowed_subject_ids=frozenset({args.subject_id}),
            research_policy_id="pb11-live-canary",
            research_policy_version="1",
        ),
        scheduler_policy=AutonomousResearchPolicy(
            policy_id="pb11-live-scheduler",
            version="1",
            max_batch_size=1,
            max_attempts_per_work=3,
            base_backoff=timedelta(minutes=5),
            max_backoff=timedelta(hours=1),
            lease_for=timedelta(hours=26),
        ),
        budget_store=budget_store,
        budget_policy=LiveResearchBudgetPolicy(
            policy_id="pb11-live-budget",
            version="1",
            currency="USD",
            max_cost_upper_bound_microunits=args.max_cost_upper_bound_microunits,
            per_batch_cost_upper_bound_microunits=args.per_batch_cost_upper_bound_microunits,
            max_batches=args.max_batches,
            max_jobs=args.max_jobs,
        ),
    )
    policy = ResearchRuntimePolicy(
        policy_id="pb11-live-runtime",
        version="1",
        mode=ResearchRuntimeMode.CANARY,
        wake_interval=timedelta(minutes=5),
        max_global_inflight=1,
        max_subject_inflight=1,
        inflight_lease_for=timedelta(hours=27),
        canary_subject_ids=frozenset({args.subject_id}),
    )

    now = datetime.now(UTC)
    tick = run_async_research_runtime_tick(
        store=runtime_store,
        runner=runner,
        policy=policy,
        subject_id=args.subject_id,
        now=now,
        execution_id=f"pb11-live:{now.isoformat()}",
    )
    budget = budget_store.snapshot(currency="USD")
    print(
        json.dumps(
            {
                "ran": tick.ran,
                "reason": tick.reason,
                "action": None if tick.cycle is None else tick.cycle.action,
                "provider_batch_id": (None if tick.cycle is None else tick.cycle.provider_batch_id),
                "selected_work_keys": (() if tick.cycle is None else tick.cycle.selected_work_keys),
                "completed_work_keys": (
                    () if tick.cycle is None else tick.cycle.completed_work_keys
                ),
                "released_work_keys": (() if tick.cycle is None else tick.cycle.released_work_keys),
                "kill_switch": tick.snapshot.kill_switch,
                "global_inflight": tick.snapshot.global_inflight,
                "runtime_status": tick.snapshot.status.value,
                "budget_cost_upper_bound_microunits": budget.total_cost_upper_bound_microunits,
                "budget_committed_batches": budget.committed_batches,
                "budget_committed_jobs": budget.committed_jobs,
                "canonical_write": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
