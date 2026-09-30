"""Explicit live Jev runner for the evidence-labeled germination corpus.

No live call occurs on import or in CI. Execution requires an explicit API key.
"""

from __future__ import annotations

import json
import os
from collections import Counter
from pathlib import Path
from typing import Any

from experiments.decision_lab.germination_corpus import build_all_cases
from experiments.decision_lab.models import LabError
from experiments.decision_lab.providers.typesafe import TypeSafeLabEvaluator

MODEL = "jev-1.13.0"
RESULT_PATH = (
    Path(__file__).resolve().parent / "results" / "germination-v0.1" / "jev-1.13.0-result.json"
)


def run_live() -> dict[str, Any]:
    api_key = os.environ.get("TYPESAFE_API_KEY")
    if not api_key or not api_key.strip():
        raise LabError("TYPESAFE_API_KEY is unavailable; refusing a fake live result")

    evaluator = TypeSafeLabEvaluator(api_key)
    rows: list[dict[str, Any]] = []
    for case in build_all_cases():
        judgments, failure, meta = evaluator.evaluate(case.request, model=MODEL)
        if failure is not None:
            rows.append(
                {
                    "case_id": case.case_id,
                    "gold": case.gold,
                    "status": "OPERATIONAL_FAILURE",
                    "failure_category": failure.category,
                    "source_url": case.source_url,
                    "meta": meta,
                }
            )
            continue
        if len(judgments) != 1:
            raise LabError(f"{case.case_id}: expected exactly one Jev judgment")
        judgment = judgments[0]
        selected = judgment.value
        rows.append(
            {
                "case_id": case.case_id,
                "gold": case.gold,
                "selected": selected,
                "correct": selected == case.gold,
                "status": "JUDGED",
                "source_url": case.source_url,
                "judgment": judgment.to_dict(),
                "meta": meta,
            }
        )

    judged = [row for row in rows if row["status"] == "JUDGED"]
    confusion = Counter(f"{row['gold']}->{row['selected']}" for row in judged)
    report: dict[str, Any] = {
        "schema_version": "germination-jev-live.v0.1",
        "model": MODEL,
        "corpus_authority": "INDEPENDENTLY_LABELED_PUBLIC_EVIDENCE",
        "promotion_authority": False,
        "cases": len(rows),
        "judged": len(judged),
        "accuracy": (sum(bool(row["correct"]) for row in judged) / len(judged) if judged else None),
        "confusion": dict(sorted(confusion.items())),
        "rows": rows,
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return report


if __name__ == "__main__":
    print(json.dumps(run_live(), indent=2, sort_keys=True, ensure_ascii=False))
