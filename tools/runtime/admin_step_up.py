"""Independent root-operator TOTP evidence for time-limited Admin step-up.

Only the SSH CLI calls this. The HTTP runtime never reads or accepts OTP seeds.
Counter reuse and brute-force attempts are serialized durably across processes.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import struct
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

PERIOD = 30
DIGITS = 6
MAX_FAILURES = 5
LOCK_SECONDS = 300


class StepUpDenied(PermissionError):
    """The proof is absent, reused, locked, or invalid (no factor information leaked)."""


def _secret(path: Path, principal_id: str) -> bytes:
    if path.is_symlink():
        raise StepUpDenied("step-up factor unavailable")
    stat = path.stat()
    if os.name == "posix" and stat.st_mode & 0o077:
        raise StepUpDenied("step-up factor unavailable")
    try:
        raw = json.loads(path.read_text(encoding="ascii"))
        if not isinstance(raw, dict) or raw.get("principalId") != principal_id:
            raise ValueError("factor is bound to another operator")
        seed = base64.b32decode(raw["secret"], casefold=False)
    except (OSError, ValueError, KeyError, TypeError, UnicodeError) as exc:
        raise StepUpDenied("step-up factor unavailable") from exc
    if len(seed) < 20:
        raise StepUpDenied("step-up factor unavailable")
    return seed


def _code(seed: bytes, counter: int) -> str:
    digest = hmac.new(seed, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    number = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    return f"{number % (10**DIGITS):0{DIGITS}d}"


def enroll_factor(secret_file: Path, provisioning_file: Path, *, principal_id: str) -> None:
    """Explicit enrollment only. Both sensitive outputs are exclusive mode 0600.

    Operator scans provisioning_file locally and removes it after enrollment.
    Never print the secret or URI to the shell.
    """
    from tools.runtime.admin_session import _write_token_exclusive

    if not principal_id.strip() or secret_file.exists() or provisioning_file.exists():
        raise ValueError("enrollment requires a new factor and a principal")
    seed = base64.b32encode(secrets.token_bytes(20)).decode("ascii")
    uri = (
        f"otpauth://totp/AXIGNAL:{quote(principal_id, safe='')}?"
        f"secret={seed}&issuer=AXIGNAL&algorithm=SHA1&digits=6&period=30"
    )
    _write_token_exclusive(secret_file, json.dumps({"principalId": principal_id, "secret": seed}))
    _write_token_exclusive(provisioning_file, uri)


def verify_totp(
    *,
    data_dir: Path,
    secret_file: Path,
    principal_id: str,
    otp: str,
    now: datetime,
) -> None:
    """Consume one verified counter, even if downstream issuance fails.

    A database-wide write lock ensures two concurrent operator processes
    cannot reuse the same TOTP. Invalid attempts are also durable.
    """
    # Malformed code attempts count toward the durable brute-force lockout too.
    if now.tzinfo is None or now.utcoffset() is None:
        raise StepUpDenied("step-up authentication denied")
    seed = _secret(secret_file, principal_id)
    timestamp = int(now.timestamp())
    current = timestamp // PERIOD
    matched: int | None = None
    well_formed = isinstance(otp, str) and len(otp) == DIGITS and otp.isascii() and otp.isdigit()
    for counter in (current - 1, current, current + 1):
        if counter >= 0 and well_formed and hmac.compare_digest(otp, _code(seed, counter)):
            matched = counter
    path = data_dir / "admin-step-up.sqlite3"
    with sqlite3.connect(path, timeout=10) as db:
        db.execute("PRAGMA busy_timeout=10000")
        db.execute(
            """CREATE TABLE IF NOT EXISTS step_up_otp_state (
                principal TEXT PRIMARY KEY,
                last_counter INTEGER NOT NULL DEFAULT -1,
                failed INTEGER NOT NULL DEFAULT 0,
                locked_until INTEGER NOT NULL DEFAULT 0
            )"""
        )
        db.execute("BEGIN IMMEDIATE")
        row = db.execute(
            "SELECT last_counter, failed, locked_until FROM step_up_otp_state WHERE principal=?",
            (principal_id,),
        ).fetchone()
        last, failed, locked = (-1, 0, 0) if row is None else row
        if timestamp < locked:
            raise StepUpDenied("step-up authentication denied")
        if matched is None or matched <= last:
            failures = int(failed) + 1
            db.execute(
                """INSERT INTO step_up_otp_state(principal, last_counter, failed, locked_until)
                   VALUES (?, ?, ?, ?) ON CONFLICT(principal) DO UPDATE SET
                   failed=excluded.failed, locked_until=excluded.locked_until""",
                (
                    principal_id,
                    last,
                    0 if failures >= MAX_FAILURES else failures,
                    timestamp + LOCK_SECONDS if failures >= MAX_FAILURES else 0,
                ),
            )
            db.commit()
            raise StepUpDenied("step-up authentication denied")
        db.execute(
            """INSERT INTO step_up_otp_state(principal, last_counter, failed, locked_until)
               VALUES (?, ?, 0, 0) ON CONFLICT(principal) DO UPDATE SET
               last_counter=excluded.last_counter, failed=0, locked_until=0""",
            (principal_id, matched),
        )
        db.commit()
