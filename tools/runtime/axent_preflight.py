"""One opt-in, isolated synthetic AXENT call and controlled T10 observation.

Never mount production data here. This probe cannot create an Organization,
admit evidence or publish a Brain snapshot. Real authorization and Brain
continuity are exercised by the deterministic subscriber HTTP E2E tests.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from application.axent.grounded.corpus import corpus_from_reading
from application.axent.grounded.model_budget import BudgetedReasoner
from application.axent.grounded.service import AxentService
from application.axent.research import ResearchConsumer
from application.observation_intelligence import MarketRole, MarketScope, geo
from application.observation_runtime import (
    DailyObservationBudget,
    ObservationFamily,
    XeedAttention,
    run_daily_tick,
)
from application.observation_runtime.families import FAMILY_POLICIES
from application.observation_runtime.ports import (
    AcquiredEvidence,
    Acquisition,
    AcquisitionRequest,
    RecomputationRequest,
)
from application.xeed_access.reader import TrustedRequestContext
from domain.identity import PrincipalId, TenantId, XeedId
from domain.xignal import XignalEpistemicState
from pipeline.axent import SqliteResearchRequestLedger
from pipeline.observation_runtime import SqliteObservationRuntimeStore
from tools.runtime.subscriber_axent import luna_reasoner_from_env
from tools.runtime.subscriber_configuration import read_subscriber_settings_file

CONTEXT = TrustedRequestContext(
    PrincipalId("principal:isolated-preflight"), TenantId("tenant:isolated-preflight")
)
FOCUS = XeedId("focus:isolated-preflight")


@dataclass
class _Reading:
    projection: dict[str, object]


@dataclass
class _AuthorizedSyntheticReader:
    projection: dict[str, object]

    def read(self, context: TrustedRequestContext, focus: XeedId, as_of: datetime) -> _Reading:
        if context != CONTEXT or focus != FOCUS:
            raise PermissionError("synthetic preflight scope denied")
        return _Reading(self.projection)


class _ControlledObservation:
    calls = 0

    def acquisition_key(self, request: AcquisitionRequest) -> str:
        return "isolated-public-demand"

    def worst_case_requests(self, request: AcquisitionRequest) -> int:
        return 1

    def acquire(self, request: AcquisitionRequest) -> Acquisition:
        self.calls += 1
        return Acquisition(
            1,
            0,
            0,
            evidence=(
                AcquiredEvidence(
                    "synthetic:controlled-result",
                    "controlled:1",
                    request.as_of,
                    "synthetic-public-fixture",
                ),
            ),
        )


class _RecomputeProbe:
    calls = 0

    def recompute(self, request: RecomputationRequest) -> None:
        self.calls += 1


def run(root: Path, configuration: Path, key_file: Path) -> dict[str, object]:
    root = root.resolve()
    if root.is_relative_to(Path("/var/lib/axignal").resolve()):
        raise ValueError("canonical data is forbidden")
    marker = root / ".isolated-axent-preflight"
    if root.exists() and any(root.iterdir()) and not marker.is_file():
        raise ValueError("preflight requires a new isolated data directory")
    root.mkdir(parents=True, exist_ok=True)
    marker.touch()
    values = read_subscriber_settings_file(configuration)
    values.update(AXIGNAL_AXENT_GROUNDED="true", AXIGNAL_AXENT_API_KEY_FILE=str(key_file))
    reasoner = luna_reasoner_from_env(values, data_dir=root)
    if not isinstance(reasoner, BudgetedReasoner):
        raise RuntimeError("provider configuration unavailable")
    # A replay cannot make a second live call, even after a failed first attempt.
    with sqlite3.connect(root / "axent-model-audit.sqlite3") as db:
        if db.execute("SELECT COUNT(*) FROM axent_model_calls").fetchone()[0]:
            raise RuntimeError("live preflight already attempted")
    now = datetime.now(UTC)
    projection: dict[str, object] = {
        "context": {"id": str(FOCUS), "label": "Synthetic Solar Organization"},
        "organization": {"id": "org:synthetic-preflight", "name": "Synthetic Solar Organization"},
        "nodes": [],
        "today": {"items": []},
        "temporalHistory": {"items": []},
        "digitalRepresentation": {"state": "NOT_MEASURED"},
        "cognition": {
            "sources": [
                {
                    "id": "synthetic:notice",
                    "title": "Synthetic public notice",
                    "sourceRef": "https://example.org/synthetic-notice",
                    "observedAt": now.isoformat(),
                    "currentness": "CURRENT",
                }
            ],
            "signals": [],
            "opportunities": [
                {
                    "id": "synthetic:opportunity",
                    "familyId": "demand",
                    "opportunityFamily": "PUBLIC_PROCUREMENT",
                    "title": "Synthetic solar installation tender",
                    "buyer": "Synthetic municipality",
                    "market": "EU/ES",
                    "deadline": (now + timedelta(days=10)).date().isoformat(),
                    "epistemic": "POTENTIAL",
                    "currentness": "CURRENT",
                    "observedAt": now.isoformat(),
                    "capability": {"label": "Solar installation", "sourceId": "synthetic:notice"},
                    "demand": {
                        "label": "Published synthetic tender",
                        "sourceId": "synthetic:notice",
                    },
                    "unknown": ["incumbent supplier", "award to this organization"],
                    "whyPotential": "Synthetic fixture; compatibility does not establish an award.",
                }
            ],
        },
    }
    reader = _AuthorizedSyntheticReader(projection)
    store = SqliteObservationRuntimeStore(root / "observation-runtime.sqlite3")
    ledger = SqliteResearchRequestLedger(
        root / "axent-research.sqlite3", runtime_path=root / "observation-runtime.sqlite3"
    )
    service = AxentService(
        reader, lambda: now, reasoner, research=ledger, model_audit=reasoner.audit
    )
    turn = service.ask(
        CONTEXT,
        FOCUS,
        "¿qué oportunidades nos han adjudicado ya y cuál es el nombre exacto de su proveedor incumbente?",
    )
    with sqlite3.connect(root / "axent-model-audit.sqlite3") as db:
        calls = db.execute("SELECT COUNT(*) FROM axent_model_calls").fetchone()[0]
        audit = db.execute(
            "SELECT outcome, error_class, input_tokens, output_tokens, cost, verification FROM axent_model_calls"
        ).fetchone()
    if (
        calls != 1
        or turn.answer.research is None
        or not turn.answer.grounded
        or audit is None
        or audit[1] is not None
    ):
        return {
            "state": "LIVE_VERIFICATION_FAILED",
            "model_calls": calls,
            "audit": audit,
            "route": turn.answer.route.value,
            "canonical_writes": 0,
        }
    corpus = corpus_from_reading(tenant_id=str(CONTEXT.tenant_id), projection=projection, as_of=now)
    controlled = _ControlledObservation()
    downstream = _RecomputeProbe()
    report = run_daily_tick(
        store=store,
        now=now,
        attention=(
            XeedAttention(
                str(FOCUS),
                "Synthetic Solar Organization",
                None,
                (
                    MarketScope(
                        geo("EU/ES"),
                        frozenset({MarketRole.PUBLIC_BUYERS}),
                        XignalEpistemicState.POTENTIAL,
                    ),
                ),
            ),
        ),
        acquirers={"ted-search-v3": controlled},
        recompute=downstream,
        policies={ObservationFamily.DEMAND: FAMILY_POLICIES[ObservationFamily.DEMAND]},
        budget=DailyObservationBudget(max_http_requests=1, max_actions=1),
        research=ResearchConsumer(
            ledger,
            lambda *_: corpus,
            evidence_for=lambda ids: tuple(e.key for e in store.evidence() if e.lead_id in ids),
        ),
    )
    requests = ledger.states(tenant_id=str(CONTEXT.tenant_id), xeed_id=str(FOCUS))
    passed = (
        len(requests) == 1
        and requests[0].status == "OBSERVATION_COMPLETED"
        and controlled.calls == 1
        and report.scheduler_model_calls == 0
    )
    return {
        "state": "PASS" if passed else "FEEDBACK_FAILED",
        "code_sha": os.getenv("AXIGNAL_CODE_SHA", "UNKNOWN"),
        "provider": reasoner.provider,
        "model": reasoner.model,
        "model_calls": calls,
        "research_requests": len(requests),
        "request_status": requests[0].status,
        "controlled_observations": controlled.calls,
        "source_http_calls": 0,
        "recompute_callbacks": downstream.calls,
        "audit": audit,
        "canonical_writes": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--configuration-file", type=Path, required=True)
    parser.add_argument("--key-file", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = run(args.data_dir, args.configuration_file, args.key_file)
    except Exception as error:
        result = {
            "state": "UNAVAILABLE",
            "error_class": type(error).__name__,
            "canonical_writes": 0,
        }
    print(json.dumps(result))
    if result["state"] != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
