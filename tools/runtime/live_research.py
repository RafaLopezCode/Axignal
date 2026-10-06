"""Bounded operator-controlled CANARY worker for live governed research."""

from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from application.economic_discovery.async_research_runtime import (
    LiveResearchBudgetPolicy,
    run_async_research_runtime_tick,
)
from application.economic_discovery.research_revalidation import (
    PrimeCurrentnessResearchRevalidator,
)
from application.economic_discovery.research_runtime import (
    ResearchRuntimeMode,
    ResearchRuntimePolicy,
)
from application.economic_discovery.research_scheduler import AutonomousResearchPolicy
from cognition.async_research_canary import AsyncGovernedCanaryCoordinator
from cognition.live_research_runtime import GovernedAsyncResearchRunner
from cognition.providers.openai_batch import DurableBatchTransport
from cognition.providers.openai_sdk_batch import OpenAISdkBatchClient
from cognition.research_result_admission import EvidenceBackedResearchAdmission
from pipeline.continuous_observation.async_canary_store import (
    SqliteDurableCanaryExecutionStore,
)
from pipeline.continuous_observation.live_budget_store import SqliteLiveResearchBudgetStore
from pipeline.continuous_observation.runtime_store import SqliteResearchRuntimeStore
from pipeline.continuous_observation.sqlite_store import SqliteSharedObservationWorkMemory
from pipeline.observation_memory.sqlite_store import SqliteObservationMemory


@dataclass
class LiveResearchCanaryService:
    data_dir: Path
    subject_id: str
    model: str
    max_batch_size: int = 1
    wake_interval: timedelta = timedelta(minutes=5)
    max_global_inflight: int = 1
    max_subject_inflight: int = 1
    max_attempts_per_work: int = 3
    max_batches: int = 3
    max_jobs: int = 3
    max_cost_upper_bound_microunits: int = 1_000_000
    per_batch_cost_upper_bound_microunits: int = 250_000
    transport: DurableBatchTransport | None = None

    def __post_init__(self) -> None:
        self.data_dir = self.data_dir.expanduser().resolve()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        if not self.subject_id.strip() or not self.model.strip():
            raise ValueError("live research canary requires subject and model")
        if self.max_batch_size != 1:
            raise ValueError("PB12 CANARY permits exactly one job per provider batch")
        if self.max_global_inflight != 1 or self.max_subject_inflight != 1:
            raise ValueError("PB12 CANARY permits exactly one inflight batch")

        self.memory = SqliteSharedObservationWorkMemory(self.data_dir / "research-work.sqlite3")
        self.runtime_store = SqliteResearchRuntimeStore(self.data_dir / "research-runtime.sqlite3")
        self.execution_store = SqliteDurableCanaryExecutionStore(
            self.data_dir / "research-canary.sqlite3"
        )
        self.budget_store = SqliteLiveResearchBudgetStore(self.data_dir / "research-budget.sqlite3")
        self.observation_memory = SqliteObservationMemory(
            self.data_dir / "observation-memory.sqlite3"
        )
        transport = self.transport or DurableBatchTransport(OpenAISdkBatchClient())
        self.coordinator = AsyncGovernedCanaryCoordinator(
            memory=self.memory,
            store=self.execution_store,
            transport=transport,
            admission=EvidenceBackedResearchAdmission(),
            authorized_model=self.model,
            lease_for=timedelta(hours=26),
            max_batch_size=1,
        )
        self.runner = GovernedAsyncResearchRunner(
            memory=self.memory,
            ledger=self.memory,
            execution_store=self.execution_store,
            coordinator=self.coordinator,
            revalidator=PrimeCurrentnessResearchRevalidator(
                observation_memory=self.observation_memory,
                research_memory=self.memory,
            ),
            scheduler_policy=AutonomousResearchPolicy(
                policy_id="pb12-live-scheduler",
                version="1",
                max_batch_size=1,
                max_attempts_per_work=self.max_attempts_per_work,
                base_backoff=timedelta(minutes=5),
                max_backoff=timedelta(hours=1),
                lease_for=timedelta(hours=26),
            ),
            budget_store=self.budget_store,
            budget_policy=LiveResearchBudgetPolicy(
                policy_id="pb12-live-budget",
                version="1",
                currency="USD",
                max_cost_upper_bound_microunits=self.max_cost_upper_bound_microunits,
                per_batch_cost_upper_bound_microunits=(self.per_batch_cost_upper_bound_microunits),
                max_batches=self.max_batches,
                max_jobs=self.max_jobs,
            ),
        )
        self.policy = ResearchRuntimePolicy(
            policy_id="pb12-live-runtime",
            version="1",
            mode=ResearchRuntimeMode.CANARY,
            wake_interval=self.wake_interval,
            max_global_inflight=1,
            max_subject_inflight=1,
            inflight_lease_for=timedelta(hours=27),
            canary_subject_ids=frozenset({self.subject_id}),
        )

    def tick(self, *, now: datetime, execution_id: str) -> dict[str, object]:
        tick = run_async_research_runtime_tick(
            store=self.runtime_store,
            runner=self.runner,
            policy=self.policy,
            subject_id=self.subject_id,
            now=now,
            execution_id=execution_id,
        )
        budget = self.budget_store.snapshot(currency="USD")
        return {
            "ran": tick.ran,
            "reason": tick.reason,
            "action": None if tick.cycle is None else tick.cycle.action,
            "provider_batch_id": (None if tick.cycle is None else tick.cycle.provider_batch_id),
            "selected_work_keys": (() if tick.cycle is None else tick.cycle.selected_work_keys),
            "completed_work_keys": (() if tick.cycle is None else tick.cycle.completed_work_keys),
            "released_work_keys": (() if tick.cycle is None else tick.cycle.released_work_keys),
            "kill_switch": tick.snapshot.kill_switch,
            "global_inflight": tick.snapshot.global_inflight,
            "runtime_status": tick.snapshot.status.value,
            "budget_cost_upper_bound_microunits": (budget.total_cost_upper_bound_microunits),
            "budget_committed_batches": budget.committed_batches,
            "budget_committed_jobs": budget.committed_jobs,
            "canonical_write": False,
        }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default=os.getenv("AXIGNAL_DATA_DIR", ""))
    parser.add_argument("--env-file")
    parser.add_argument("--openai-api-key-file")
    parser.add_argument("--subject-id", required=True)
    parser.add_argument("--model", default="gpt-6-luna")
    parser.add_argument("--max-ticks", type=int, default=1)
    parser.add_argument("--interval-seconds", type=int, default=60)
    parser.add_argument("--set-kill-switch", choices=("on", "off"))
    parser.add_argument("--control-only", action="store_true")
    parser.add_argument("--max-batches", type=int, default=3)
    parser.add_argument("--max-jobs", type=int, default=3)
    parser.add_argument("--max-cost-upper-bound-microunits", type=int, default=1_000_000)
    parser.add_argument("--per-batch-cost-upper-bound-microunits", type=int, default=250_000)
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


def _load_openai_key_file(path: str | None) -> None:
    if not path:
        return
    value = Path(path).read_text(encoding="utf-8").strip()
    if not value:
        raise SystemExit("OpenAI API key file is empty")
    os.environ["OPENAI_API_KEY"] = value


def main() -> int:
    args = _parser().parse_args()
    _load_env_file(args.env_file)
    _load_openai_key_file(args.openai_api_key_file)
    if not args.data_dir.strip():
        raise SystemExit("AXIGNAL_DATA_DIR or --data-dir is required")
    data_dir = Path(args.data_dir).expanduser().resolve()

    if args.set_kill_switch is not None:
        control = SqliteResearchRuntimeStore(data_dir / "research-runtime.sqlite3")
        enabled = args.set_kill_switch == "on"
        control.set_kill_switch(enabled)
        if args.control_only:
            print(
                json.dumps(
                    {
                        "control_only": True,
                        "kill_switch": enabled,
                        "canonical_write": False,
                    },
                    sort_keys=True,
                ),
                flush=True,
            )
            return 0
    elif args.control_only:
        raise SystemExit("--control-only requires --set-kill-switch")

    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is not available to this process")
    if not 1 <= args.max_ticks <= 60:
        raise SystemExit("--max-ticks must be between 1 and 60")
    if not 5 <= args.interval_seconds <= 3600:
        raise SystemExit("--interval-seconds must be between 5 and 3600")

    service = LiveResearchCanaryService(
        data_dir=data_dir,
        subject_id=args.subject_id,
        model=args.model,
        max_batches=args.max_batches,
        max_jobs=args.max_jobs,
        max_cost_upper_bound_microunits=args.max_cost_upper_bound_microunits,
        per_batch_cost_upper_bound_microunits=args.per_batch_cost_upper_bound_microunits,
    )

    for index in range(args.max_ticks):
        now = datetime.now(UTC)
        payload = service.tick(
            now=now,
            execution_id=f"pb12-live:{now.isoformat()}:{index:02d}",
        )
        print(json.dumps(payload, sort_keys=True), flush=True)
        if index + 1 < args.max_ticks:
            time.sleep(args.interval_seconds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
