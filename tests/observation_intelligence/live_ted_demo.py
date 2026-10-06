"""Live, read-only demonstration against the public TED Search API. Not run in CI.

    uv run python -m tests.observation_intelligence.live_ted_demo [xeed:solartec]

It plans from the generalist homepage observation, executes only the strategy's
routable actions (anonymous, bounded, one request per action) and prints the
Human First brief. Nothing is persisted and nothing becomes canonical.
"""

from __future__ import annotations

import sys
from dataclasses import replace
from datetime import UTC, datetime

from application.observation_intelligence import (
    ObservationBudget,
    OperationalLearning,
    build_brief,
    build_strategy,
    run_observation_loop,
)
from pipeline.observation_intelligence import TedSearchAdapter, UrllibTedTransport
from tests.observation_intelligence.scenarios import context_for


def main(xeed_id: str = "xeed:solartec") -> None:
    now = datetime.now(UTC)
    context, coverage = context_for(xeed_id)
    context = replace(context, as_of=now)
    strategy = build_strategy(
        context,
        coverage=coverage,
        budget=ObservationBudget(
            max_requests=6, max_amount_microunits=0, max_depth=2, max_actions=6
        ),
    )
    learning = OperationalLearning()
    result = run_observation_loop(
        strategy,
        context,
        adapters={
            "ted-search-v3": TedSearchAdapter(UrllibTedTransport(), clock=lambda: now, limit=20)
        },
        coverage=coverage,
        learning=learning,
    )
    for step in result.steps:
        print(
            f"[step] {step.action.action_id} new={step.new_records} "
            f"candidates+={step.candidates_added} follow_ups={len(step.follow_ups)} "
            f"failure={step.failure}"
        )
    print(f"[stop] {result.stop_reason.value}: {result.stop_detail} · requests={result.requests}")
    stats = learning.for_source("ted-search-v3")
    print(
        f"[learning] attempts={stats.attempts} records={stats.records} latency_ms={stats.latency_ms}"
    )
    print()
    print(
        build_brief(
            context=context, strategy=strategy, result=result, coverage=coverage
        ).render_es()
    )


if __name__ == "__main__":
    main(*sys.argv[1:])
