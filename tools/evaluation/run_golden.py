"""Run the golden set through the deployed runtime, isolated, and dump each subscriber view.

Meant for a throwaway container started from the production image with the runtime data
mounted **read-only** at ``/src`` (it is copied, never written) and the same secret
group as the runtime (the assistant key). Real public sources, real assistant; nothing
written to production. Prints a JSON list for ``tools.evaluation.excellence``.

    docker run --rm --network <runtime network> --group-add <secret gid> \\
      -v /var/lib/axignal/runtime:/src:ro -v /etc/axignal:/etc/axignal:ro \\
      --env-file <runtime env> axignal-runtime:<sha> \\
      python -m tools.evaluation.run_golden > views.json
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Any

SOURCE = Path(os.environ.get("AXIGNAL_GOLDEN_SOURCE", "/src"))
WORK = Path(os.environ.get("AXIGNAL_GOLDEN_WORK", "/tmp/axignal-golden"))
#: The set to observe: the golden set, or another (the self set, after each deploy).
GOLDEN = Path(os.environ.get("AXIGNAL_GOLDEN_SET") or Path(__file__).with_name("golden_set.json"))
MAX_JUDGMENT_ROUNDS = 12


def _log(*parts: object) -> None:
    print(*parts, file=sys.stderr, flush=True)


def main() -> int:
    shutil.copytree(
        SOURCE, WORK, ignore=shutil.ignore_patterns("tmp", "first-observation-artifacts")
    )
    os.environ.update(
        {
            "AXIGNAL_DATA_DIR": str(WORK),
            "AXIGNAL_FIRST_OBSERVATION_WORKER": "inline",
            "AXIGNAL_AWARDS_BACKFILL_MONTHS": "0",
            "AXIGNAL_MARKETING_POOL_ENABLED": "false",
        }
    )
    from tools.runtime.config import RuntimeConfig
    from tools.runtime.service import build_runtime

    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))["organizations"]
    runtime = build_runtime(RuntimeConfig.from_env())
    outputs: Any = getattr(runtime.subscriber, "outputs", None)
    observing: Any = getattr(outputs, "_first_observation", None)
    if observing is None:
        _log("first observation is disabled in this runtime")
        return 2
    # One evaluation tenant studies the whole set: the per-tenant daily cap protects
    # subscribers, not this isolated copy.
    observing._tenant_daily_jobs = len(golden) + 10
    refs: dict[str, dict[str, str]] = {}
    for org in golden:
        ref = f"golden:{org['domain']}"
        refs[ref] = org
        _log("study", org["domain"], observing.study(ref, f"https://{org['domain']}/", org["name"]))
    started = time.time()
    while observing.run_next():
        _log("observed", round(time.time() - started), "s")
    for ref in refs:
        observing.study_result(ref)  # first reads queue GEO, sector context and regulation
    # Sources the runtime reads on its own thread (inline here): notoriety, job boards.
    for _ in range(10):
        if not observing.read_notoriety() + observing.read_job_boards():
            break
    for ref in refs:
        observing.study_result(ref)  # boards are known after the first read of each view
    observing.read_job_boards()
    for round_ in range(MAX_JUDGMENT_ROUNDS):
        ran = (
            observing.measure_geo()
            + observing.judge_sector_context()
            + observing.judge_regulation()
        )
        _log("judgment round", round_, ran)
        if not ran and round_ > 2:
            break
    # Spec 075: judge the fit of the open demand the observed activities match (bounded,
    # in this isolated copy), so the views below read it as subscribers do.
    from tools.runtime.demand_fit import run_demand_fit

    activities = sorted({
        str(d.get("code")) for ref in refs for d in (observing.study_result(ref)[0] or {}).get("discoveries") or []
        if isinstance(d, dict) and d.get("kind") == "ACTIVITY"
    })  # fmt: skip
    if activities:
        _log("demand fit", run_demand_fit(WORK, capabilities=activities))
    # Potential buyers (ADR-0099): reading a view requests its customers' lookups, and a
    # resolved customer then requests organizations like it: two rounds, read inline here.
    for _ in range(2):
        for ref in refs:
            observing.study_result(ref)
        for _ in range(30):
            if not observing.read_buyer_lookups():
                break
    rows = []
    for ref, org in refs.items():
        view, _contact = observing.study_result(ref)
        rows.append({**org, "view": view})
    print(json.dumps(rows, ensure_ascii=False, default=str))
    _log("done", round(time.time() - started), "s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
