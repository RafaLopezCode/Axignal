"""GEO measurement runner: asks the routed assistant the fixed probe questions, off the read path.

Requests are queued when an observation is read; a background stage runs a few per tick
under a global daily cap, through the model router (no SDK hard-wired here). Each
organization is measured at most once every 30 days; the result is stored with its
instrument, conditions, cost and date, and only then shown.
"""

from __future__ import annotations

import json
import os
import sqlite3
import uuid
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from application.generative_visibility.probe import (
    INSTRUCTION,
    SCHEMA,
    ProbeSubject,
    evaluate,
    questions,
)
from cognition.jobs.model import CognitiveJob, JobKind

TTL = timedelta(days=30)
MAX_PER_DAY = 40  # organizations measured per UTC day, all tenants together
MAX_OUTPUT_TOKENS = 700


class GenerativeProbeRunner:
    def __init__(
        self,
        complete: Callable[[CognitiveJob], Any],
        model: str,
        database_path: str | Path,
        *,
        rates: tuple[Decimal, Decimal] | None = None,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        max_per_day: int = MAX_PER_DAY,
    ) -> None:
        self._complete = complete
        self._model = model
        self._rates = rates
        self._clock = clock
        self._max_per_day = max_per_day
        self._path = Path(database_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute(
                """CREATE TABLE IF NOT EXISTS geo_probes (
                    subject_key TEXT PRIMARY KEY, subject TEXT NOT NULL, state TEXT NOT NULL,
                    measurement TEXT, requested_at TEXT NOT NULL, measured_at TEXT)"""
            )

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self._path, timeout=10)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def measurement(self, subject: ProbeSubject) -> Mapping[str, object] | None:
        with self._connect() as db:
            row = db.execute(
                "SELECT measurement FROM geo_probes WHERE subject_key=? AND state='MEASURED'",
                (subject.key,),
            ).fetchone()
        return None if row is None else dict(json.loads(row["measurement"]))

    def request(self, subject: ProbeSubject) -> None:
        """Queue a measurement unless a fresh one exists or one is already queued."""
        now = self._clock()
        with self._connect() as db:
            row = db.execute(
                "SELECT state, measured_at FROM geo_probes WHERE subject_key=?", (subject.key,)
            ).fetchone()
            if row is not None and (
                row["state"] == "QUEUED"
                or (row["measured_at"] and now - datetime.fromisoformat(row["measured_at"]) < TTL)
            ):
                return
            db.execute(
                """INSERT INTO geo_probes (subject_key, subject, state, requested_at)
                VALUES (?,?,'QUEUED',?) ON CONFLICT(subject_key) DO UPDATE SET
                state='QUEUED', requested_at=excluded.requested_at""",
                (subject.key, json.dumps(_wire(subject)), now.isoformat()),
            )

    def run(self, *, max_runs: int = 2) -> int:
        now = self._clock()
        day = now.date().isoformat()
        with self._connect() as db:
            done_today = db.execute(
                "SELECT COUNT(*) FROM geo_probes WHERE substr(measured_at,1,10)=?", (day,)
            ).fetchone()[0]
            queued = db.execute(
                "SELECT subject_key, subject FROM geo_probes WHERE state='QUEUED' ORDER BY requested_at LIMIT ?",
                (max(0, min(max_runs, self._max_per_day - done_today)),),
            ).fetchall()
        ran = 0
        for row in queued:
            subject = ProbeSubject(**json.loads(row["subject"]))
            answers: list[Mapping[str, object]] = []
            tokens_in = tokens_out = 0
            try:
                for question in questions(subject):
                    result = self._complete(
                        CognitiveJob(
                            id=f"geo-probe:{uuid.uuid4().hex}",
                            kind=JobKind.GENERATIVE_PROBE,
                            instruction=INSTRUCTION,
                            context={
                                "schema": SCHEMA,
                                "user": question,
                                "max_output_tokens": MAX_OUTPUT_TOKENS,
                            },
                        )
                    )
                    payload = result.payload if hasattr(result, "payload") else {}
                    answer = payload.get("answer") if isinstance(payload, Mapping) else None
                    answers.append(answer if isinstance(answer, Mapping) else {})
                    tokens_in += int(payload.get("input_tokens") or 0)
                    tokens_out += int(payload.get("output_tokens") or 0)
            except Exception:  # unavailable: stays queued for a later tick, nothing invented
                continue
            measurement = {
                "instrument": {
                    "model": self._model,
                    "router": "cognition/router",
                    "kind": JobKind.GENERATIVE_PROBE.value,
                },
                "language": subject.language,
                "measuredAt": self._clock().isoformat(),
                "result": evaluate(subject, answers),
                "cost": self._cost(tokens_in, tokens_out),
            }
            with self._connect() as db:
                db.execute(
                    "UPDATE geo_probes SET state='MEASURED', measurement=?, measured_at=? WHERE subject_key=?",
                    (json.dumps(measurement), measurement["measuredAt"], row["subject_key"]),
                )
            ran += 1
        return ran

    def _cost(self, tokens_in: int, tokens_out: int) -> dict[str, object]:
        if self._rates is None:
            return {"inputTokens": tokens_in, "outputTokens": tokens_out, "usd": None}
        usd = (
            Decimal(tokens_in) * self._rates[0] + Decimal(tokens_out) * self._rates[1]
        ) / Decimal(1_000_000)
        return {"inputTokens": tokens_in, "outputTokens": tokens_out, "usd": float(round(usd, 6))}


def _wire(subject: ProbeSubject) -> dict[str, object]:
    return {
        "name": subject.name, "domain": subject.domain, "activity": subject.activity,
        "place": subject.place, "language": subject.language,
    }  # fmt: skip


def generative_probe_from_values(
    values: Mapping[str, str], root: Path
) -> GenerativeProbeRunner | None:
    """Configured from the same governed assistant settings as AXENT; off otherwise."""
    model = values.get("AXIGNAL_AXENT_LUNA_MODEL", "").strip()
    filename = values.get("AXIGNAL_AXENT_API_KEY_FILE", "").strip()
    if values.get("AXIGNAL_AXENT_GROUNDED", "false").lower() != "true" or not model or not filename:
        return None
    key_file = Path(filename)
    if not key_file.is_absolute() or not key_file.is_file() or not os.access(key_file, os.R_OK):
        return None
    try:
        rates = (
            Decimal(values.get("AXIGNAL_AXENT_INPUT_PER_MILLION", "")),
            Decimal(values.get("AXIGNAL_AXENT_OUTPUT_PER_MILLION", "")),
        )
    except InvalidOperation:
        rates = None
    from cognition.providers.luna_responses import LunaResponsesProvider
    from cognition.router.router import ModelRouter

    router = ModelRouter([LunaResponsesProvider(authorized_model=model, key_file=key_file)])
    return GenerativeProbeRunner(router.route, model, root / "geo-probes.sqlite3", rates=rates)
