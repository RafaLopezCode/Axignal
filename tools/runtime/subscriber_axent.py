"""Subscriber HTTP adapter for tenant-grounded AXENT, plus its composition."""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping
from datetime import datetime
from pathlib import Path

from application.axent.grounded import (
    AxentService,
    GroundedReasoner,
    RuntimeFamilyCoverage,
    runtime_answer_wire,
)
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
        )
    )


def luna_reasoner_from_env() -> GroundedReasoner | None:
    """Off unless AXIGNAL_AXENT_LUNA_MODEL is set and an OpenAI key is in the process."""

    model = os.getenv("AXIGNAL_AXENT_LUNA_MODEL", "").strip()
    if not model or not os.getenv("OPENAI_API_KEY"):
        return None
    from cognition.axent_reasoner import CognitiveGroundedReasoner
    from cognition.providers.luna_responses import LunaResponsesProvider
    from cognition.router.router import ModelRouter

    provider = LunaResponsesProvider(authorized_model=model)
    return CognitiveGroundedReasoner(
        ModelRouter([provider]), model=model, provider_name=provider.name
    )
