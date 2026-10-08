"""Subscriber HTTP adapter for tenant-grounded AXENT, plus its composition."""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from application.axent.grounded import (
    AxentService,
    GroundedReasoner,
    RuntimeFamilyCoverage,
    runtime_answer_wire,
)
from application.axent.grounded.cost import CostRates
from application.axent.grounded.model_budget import BudgetedReasoner
from application.axent.grounded.service import AuthorizedReadingPort
from application.xeed_access.reader import TrustedRequestContext
from domain.identity import XeedId

LOCALES = frozenset({"es", "en", "fr", "de", "it", "pt"})


class SubscriberAxent:
    def __init__(self, service: AxentService) -> None:
        self.service = service

    def ask(
        self, context: TrustedRequestContext, focus_id: XeedId, payload: Mapping[str, object]
    ) -> dict[str, object]:
        if set(payload) - {"question", "locale", "memory"}:
            raise ValueError("unexpected AXENT fields")
        question, locale = payload.get("question"), payload.get("locale", "es")
        if not isinstance(question, str) or not question.strip() or len(question) > 1000:
            raise ValueError("invalid AXENT question")
        if locale not in LOCALES:
            raise ValueError("invalid AXENT locale")
        assert isinstance(locale, str)
        turn = self.service.ask(
            context, focus_id, question, memory=payload.get("memory"), locale=locale
        )
        return runtime_answer_wire(turn, locale=locale)


def build_subscriber_axent(
    *,
    reader: AuthorizedReadingPort,
    clock: Callable[[], datetime],
    data_dir: Path,
    reasoner: GroundedReasoner | None = None,
) -> SubscriberAxent:
    """Research requests are always recorded; runtime coverage is read when present."""

    from pipeline.axent import SqliteResearchRequestLedger
    from pipeline.observation_runtime import SqliteObservationRuntimeStore

    runtime_db = data_dir / "observation-runtime.sqlite3"
    return SubscriberAxent(
        AxentService(
            reader=reader,
            clock=clock,
            reasoner=reasoner,
            coverage=(
                RuntimeFamilyCoverage(SqliteObservationRuntimeStore(runtime_db))
                if runtime_db.is_file()
                else None
            ),
            research=SqliteResearchRequestLedger(data_dir / "axent-research.sqlite3"),
            model_audit=reasoner.audit if isinstance(reasoner, BudgetedReasoner) else None,
        )
    )


def luna_reasoner_from_env(
    values: Mapping[str, str] | None = None, *, data_dir: Path | None = None
) -> GroundedReasoner | None:
    """Opt-in only: configured model, readable secret file and known positive rates."""

    values = os.environ if values is None else values
    model = values.get("AXIGNAL_AXENT_LUNA_MODEL", "").strip()
    filename = values.get("AXIGNAL_AXENT_API_KEY_FILE", "").strip()
    if (
        values.get("AXIGNAL_AXENT_GROUNDED", "false").lower() != "true"
        or not model
        or not filename
        or data_dir is None
    ):
        return None
    key_file = Path(filename)
    if not key_file.is_absolute() or not key_file.is_file() or not os.access(key_file, os.R_OK):
        return None
    try:
        input_rate = Decimal(values.get("AXIGNAL_AXENT_INPUT_PER_MILLION", ""))
        output_rate = Decimal(values.get("AXIGNAL_AXENT_OUTPUT_PER_MILLION", ""))
        maximum = Decimal(values.get("AXIGNAL_AXENT_MAX_CALL_COST", ""))
        if not all(v.is_finite() and v > 0 for v in (input_rate, output_rate, maximum)):
            return None
        rates = CostRates(input_rate, output_rate, "USD")
    except (InvalidOperation, ValueError):
        return None
    from cognition.axent_reasoner import CognitiveGroundedReasoner
    from cognition.providers.luna_responses import LunaResponsesProvider
    from cognition.router.router import ModelRouter
    from pipeline.axent.model_audit import SqliteModelAudit

    provider = LunaResponsesProvider(authorized_model=model, key_file=key_file)
    inner = CognitiveGroundedReasoner(
        ModelRouter([provider]), model=model, provider_name=provider.name
    )
    return BudgetedReasoner(
        inner,
        SqliteModelAudit(data_dir / "axent-model-audit.sqlite3"),
        lambda: datetime.now(UTC),
        rates,
        maximum,
        provider.name,
    )
