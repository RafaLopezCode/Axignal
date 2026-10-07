"""SQLite persistence for Product MCP authorization and usage audit.

Tokens and codes are stored only as SHA-256 digests; nothing here can be used
to call the MCP. Audit rows hold identifiers, timings, sizes and outcomes —
never request or response payloads. Not AXIGLAND state.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import closing, contextmanager
from datetime import UTC, datetime
from pathlib import Path

from application.product_mcp.oauth import AuthorizationRequest, IssuedCode, McpClient, McpGrant
from application.product_mcp.server import McpAuditEvent
from domain.identity import PrincipalId, TenantId

_SCHEMA = (
    "CREATE TABLE IF NOT EXISTS mcp_clients (client_id TEXT PRIMARY KEY, client_name TEXT NOT NULL, redirect_uris TEXT NOT NULL, created_at TEXT NOT NULL)",
    """CREATE TABLE IF NOT EXISTS mcp_requests (request_id TEXT PRIMARY KEY, client_id TEXT NOT NULL, redirect_uri TEXT NOT NULL,
        state TEXT, code_challenge TEXT NOT NULL, scope TEXT NOT NULL, resource TEXT NOT NULL, created_at TEXT NOT NULL, expires_at TEXT NOT NULL)""",
    """CREATE TABLE IF NOT EXISTS mcp_grants (grant_id TEXT PRIMARY KEY, principal_id TEXT NOT NULL, tenant_id TEXT NOT NULL,
        client_id TEXT NOT NULL, scope TEXT NOT NULL, resource TEXT NOT NULL, created_at TEXT NOT NULL, revoked_at TEXT)""",
    """CREATE TABLE IF NOT EXISTS mcp_codes (code_digest TEXT PRIMARY KEY, grant_id TEXT NOT NULL, client_id TEXT NOT NULL,
        redirect_uri TEXT NOT NULL, code_challenge TEXT NOT NULL, resource TEXT NOT NULL, expires_at TEXT NOT NULL)""",
    """CREATE TABLE IF NOT EXISTS mcp_tokens (token_digest TEXT PRIMARY KEY, kind TEXT NOT NULL, grant_id TEXT NOT NULL,
        expires_at TEXT NOT NULL, used INTEGER NOT NULL DEFAULT 0)""",
    "CREATE INDEX IF NOT EXISTS mcp_tokens_grant ON mcp_tokens (grant_id)",
    """CREATE TABLE IF NOT EXISTS mcp_audit (seq INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT NOT NULL, principal_id TEXT NOT NULL,
        tenant_id TEXT NOT NULL, client_id TEXT NOT NULL, method TEXT NOT NULL, target TEXT, xeed_id TEXT, outcome TEXT NOT NULL,
        reason TEXT, duration_ms INTEGER NOT NULL, response_bytes INTEGER NOT NULL, model_calls INTEGER NOT NULL)""",
)


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        raise ValueError("MCP store times must be timezone-aware")
    return value.astimezone(UTC).isoformat()


def _time(value: object) -> datetime:
    return datetime.fromisoformat(str(value))


class SqliteProductMcpStore:
    def __init__(self, database_path: str | Path) -> None:
        self._path = Path(database_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._tx() as db:
            for statement in _SCHEMA:
                db.execute(statement)

    @contextmanager
    def _tx(self) -> Iterator[sqlite3.Connection]:
        with closing(sqlite3.connect(self._path, isolation_level=None)) as db:
            db.row_factory = sqlite3.Row
            db.execute("BEGIN IMMEDIATE")
            try:
                yield db
            except BaseException:
                db.execute("ROLLBACK")
                raise
            db.execute("COMMIT")

    def _one(self, sql: str, args: tuple[object, ...]) -> sqlite3.Row | None:
        with closing(sqlite3.connect(self._path)) as db:
            db.row_factory = sqlite3.Row
            row: sqlite3.Row | None = db.execute(sql, args).fetchone()
            return row

    # Clients
    def put_client(self, client: McpClient) -> None:
        with self._tx() as db:
            db.execute(
                "INSERT INTO mcp_clients VALUES (?, ?, ?, ?)",
                (
                    client.client_id,
                    client.client_name,
                    json.dumps(list(client.redirect_uris)),
                    _iso(client.created_at),
                ),
            )

    def client(self, client_id: str) -> McpClient | None:
        row = self._one("SELECT * FROM mcp_clients WHERE client_id=?", (client_id,))
        if row is None:
            return None
        return McpClient(
            row["client_id"],
            row["client_name"],
            tuple(json.loads(row["redirect_uris"])),
            _time(row["created_at"]),
        )

    # Authorization requests (single use)
    def put_request(self, request: AuthorizationRequest) -> None:
        with self._tx() as db:
            db.execute(
                "INSERT INTO mcp_requests VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    request.request_id, request.client_id, request.redirect_uri, request.state,
                    request.code_challenge, request.scope, request.resource,
                    _iso(request.created_at), _iso(request.expires_at),
                ),
            )  # fmt: skip

    @staticmethod
    def _request(row: sqlite3.Row) -> AuthorizationRequest:
        return AuthorizationRequest(
            row["request_id"], row["client_id"], row["redirect_uri"], row["state"], row["code_challenge"],
            row["scope"], row["resource"], _time(row["created_at"]), _time(row["expires_at"]),
        )  # fmt: skip

    def request(self, request_id: str) -> AuthorizationRequest | None:
        row = self._one("SELECT * FROM mcp_requests WHERE request_id=?", (request_id,))
        return None if row is None else self._request(row)

    def take_request(self, request_id: str) -> AuthorizationRequest | None:
        with self._tx() as db:
            row = db.execute(
                "SELECT * FROM mcp_requests WHERE request_id=?", (request_id,)
            ).fetchone()
            if row is None:
                return None
            db.execute("DELETE FROM mcp_requests WHERE request_id=?", (request_id,))
            return self._request(row)

    # Grants
    def put_grant(self, grant: McpGrant) -> None:
        with self._tx() as db:
            db.execute(
                "INSERT INTO mcp_grants VALUES (?, ?, ?, ?, ?, ?, ?, NULL)",
                (
                    grant.grant_id,
                    grant.principal_id,
                    grant.tenant_id,
                    grant.client_id,
                    grant.scope,
                    grant.resource,
                    _iso(grant.created_at),
                ),
            )

    @staticmethod
    def _grant(row: sqlite3.Row) -> McpGrant:
        return McpGrant(
            row["grant_id"], PrincipalId(row["principal_id"]), TenantId(row["tenant_id"]), row["client_id"],
            row["scope"], row["resource"], _time(row["created_at"]),
            None if row["revoked_at"] is None else _time(row["revoked_at"]),
        )  # fmt: skip

    def grant(self, grant_id: str) -> McpGrant | None:
        row = self._one("SELECT * FROM mcp_grants WHERE grant_id=?", (grant_id,))
        return None if row is None else self._grant(row)

    def grants_for(self, principal_id: PrincipalId, tenant_id: TenantId) -> tuple[McpGrant, ...]:
        with closing(sqlite3.connect(self._path)) as db:
            db.row_factory = sqlite3.Row
            rows = db.execute(
                "SELECT * FROM mcp_grants WHERE principal_id=? AND tenant_id=? ORDER BY created_at",
                (principal_id, tenant_id),
            ).fetchall()
        return tuple(self._grant(r) for r in rows)

    def revoke_grant(self, grant_id: str, *, revoked_at: datetime) -> bool:
        with self._tx() as db:
            cursor = db.execute(
                "UPDATE mcp_grants SET revoked_at=? WHERE grant_id=? AND revoked_at IS NULL",
                (_iso(revoked_at), grant_id),
            )
            # Revocation ends every token of the grant immediately.
            db.execute("DELETE FROM mcp_tokens WHERE grant_id=?", (grant_id,))
            return cursor.rowcount == 1

    # Codes (single use)
    def put_code(self, code: IssuedCode) -> None:
        with self._tx() as db:
            db.execute(
                "INSERT INTO mcp_codes VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    code.code_digest,
                    code.grant_id,
                    code.client_id,
                    code.redirect_uri,
                    code.code_challenge,
                    code.resource,
                    _iso(code.expires_at),
                ),
            )

    def take_code(self, code_digest: str) -> IssuedCode | None:
        with self._tx() as db:
            row = db.execute(
                "SELECT * FROM mcp_codes WHERE code_digest=?", (code_digest,)
            ).fetchone()
            if row is None:
                return None
            db.execute("DELETE FROM mcp_codes WHERE code_digest=?", (code_digest,))
            return IssuedCode(
                row["code_digest"], row["grant_id"], row["client_id"], row["redirect_uri"],
                row["code_challenge"], row["resource"], _time(row["expires_at"]),
            )  # fmt: skip

    # Tokens
    def put_token(
        self, token_digest: str, *, kind: str, grant_id: str, expires_at: datetime
    ) -> None:
        with self._tx() as db:
            db.execute(
                "INSERT INTO mcp_tokens VALUES (?, ?, ?, ?, 0)",
                (token_digest, kind, grant_id, _iso(expires_at)),
            )

    def token(self, token_digest: str, *, kind: str) -> tuple[str, datetime, bool] | None:
        row = self._one(
            "SELECT * FROM mcp_tokens WHERE token_digest=? AND kind=?", (token_digest, kind)
        )
        return (
            None if row is None else (row["grant_id"], _time(row["expires_at"]), bool(row["used"]))
        )

    def mark_used(self, token_digest: str) -> bool:
        with self._tx() as db:
            cursor = db.execute(
                "UPDATE mcp_tokens SET used=1 WHERE token_digest=? AND kind='refresh' AND used=0",
                (token_digest,),
            )
            return cursor.rowcount == 1

    # Audit (identifiers, timings and sizes only)
    def record(self, event: McpAuditEvent) -> None:
        with self._tx() as db:
            db.execute(
                "INSERT INTO mcp_audit (at, principal_id, tenant_id, client_id, method, target, xeed_id, outcome, reason, duration_ms, response_bytes, model_calls) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    _iso(event.at), event.principal_id, event.tenant_id, event.client_id, event.method,
                    event.target, event.xeed_id, event.outcome, event.reason, event.duration_ms,
                    event.response_bytes, event.model_calls,
                ),
            )  # fmt: skip

    def recent_activity(self, limit: int = 100) -> tuple[dict[str, object], ...]:
        with closing(sqlite3.connect(self._path)) as db:
            db.row_factory = sqlite3.Row
            rows = db.execute(
                "SELECT * FROM mcp_audit ORDER BY seq DESC LIMIT ?", (max(1, min(limit, 500)),)
            ).fetchall()
        return tuple({k: v for k, v in dict(row).items() if k != "seq"} for row in rows)

    def active_grants(self) -> tuple[McpGrant, ...]:
        with closing(sqlite3.connect(self._path)) as db:
            db.row_factory = sqlite3.Row
            rows = db.execute(
                "SELECT * FROM mcp_grants WHERE revoked_at IS NULL ORDER BY created_at DESC"
            ).fetchall()
        return tuple(self._grant(r) for r in rows)

    def client_names(self) -> dict[str, str]:
        with closing(sqlite3.connect(self._path)) as db:
            return {
                r[0]: r[1]
                for r in db.execute("SELECT client_id, client_name FROM mcp_clients").fetchall()
            }
