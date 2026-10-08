"""Atomic idempotent intake, durable abuse limits and ninety-day retention."""

from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import cast

from application.public_requests.service import (
    DeliveryStatus,
    PublicRequest,
    RequestKind,
    RequestReceipt,
)


class SqlitePublicRequestStore:
    def __init__(self, path: Path):
        self.path = path
        with sqlite3.connect(path) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS public_requests (
                id TEXT PRIMARY KEY, ref TEXT UNIQUE NOT NULL, fingerprint TEXT NOT NULL,
                created_at TEXT NOT NULL, kind TEXT NOT NULL, email_hash TEXT NOT NULL,
                content TEXT NOT NULL, delivery TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'RECEIVED')""")
            if "status" not in {row[1] for row in db.execute("PRAGMA table_info(public_requests)")}:
                db.execute(
                    "ALTER TABLE public_requests ADD COLUMN status TEXT NOT NULL DEFAULT 'RECEIVED'"
                )
            db.execute(
                "CREATE INDEX IF NOT EXISTS public_requests_created ON public_requests(created_at)"
            )

    @staticmethod
    def _receipt(row: tuple[object, ...]) -> RequestReceipt:
        return RequestReceipt(
            str(row[0]), str(row[1]), cast(RequestKind, row[2]), cast(DeliveryStatus, row[3])
        )

    def receive(self, request: PublicRequest, *, now: datetime) -> tuple[RequestReceipt, bool]:
        import hashlib

        if now.tzinfo is None:
            raise ValueError("timezone required")
        email_hash = hashlib.sha256(request.email.casefold().encode()).hexdigest()
        with sqlite3.connect(self.path, timeout=10) as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute(
                "DELETE FROM public_requests WHERE created_at < ?",
                ((now - timedelta(days=90)).isoformat(),),
            )
            prior = db.execute(
                "SELECT id, created_at, kind, delivery, fingerprint FROM public_requests WHERE ref = ?",
                (request.request_ref,),
            ).fetchone()
            if prior:
                if prior[4] != request.fingerprint:
                    raise ValueError("REQUEST_REF_CONFLICT")
                return self._receipt(prior), False
            since = (now - timedelta(hours=1)).isoformat()
            global_count = db.execute(
                "SELECT count(*) FROM public_requests WHERE created_at >= ?", (since,)
            ).fetchone()[0]
            sender_count = db.execute(
                "SELECT count(*) FROM public_requests WHERE created_at >= ? AND email_hash = ?",
                (since, email_hash),
            ).fetchone()[0]
            if global_count >= 100 or sender_count >= 3:
                raise ValueError("REQUEST_RATE_LIMITED")
            receipt = RequestReceipt(uuid.uuid4().hex, now.isoformat(), request.kind, "PENDING")
            db.execute(
                "INSERT INTO public_requests (id, ref, fingerprint, created_at, kind, email_hash, content, delivery) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    receipt.request_id,
                    request.request_ref,
                    request.fingerprint,
                    receipt.created_at,
                    request.kind,
                    email_hash,
                    json.dumps(asdict(request)),
                    "PENDING",
                ),
            )
            return receipt, True

    def complete(self, receipt: RequestReceipt, *, status: DeliveryStatus) -> RequestReceipt:
        with sqlite3.connect(self.path) as db:
            db.execute(
                "UPDATE public_requests SET delivery = ? WHERE id = ?", (status, receipt.request_id)
            )
        return RequestReceipt(receipt.request_id, receipt.created_at, receipt.kind, status)

    def purge(self, *, now: datetime) -> int:
        with sqlite3.connect(self.path) as db:
            return db.execute(
                "DELETE FROM public_requests WHERE created_at < ?",
                ((now - timedelta(days=90)).isoformat(),),
            ).rowcount
