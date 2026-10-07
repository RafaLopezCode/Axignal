"""Subscriber Product MCP: a read-only JSON-RPC surface over governed Xeed readings.

Every request is already bound to one authenticated grant (principal + tenant +
client). Each call re-resolves the tenant's effective entitlement and the Xeeds
it authorizes before reading anything; a Xeed id from a client, a cursor or a
resource URI grants nothing by itself. No tool writes, admits evidence, starts
research or calls a model: AXIGNAL serves memory, the client's model reasons.
"""

from __future__ import annotations

import base64
import json
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol

from application.product_mcp import views
from application.product_mcp.oauth import McpGrant
from application.xeed_access.reader import TrustedRequestContext

SERVER_NAME = "axignal"
SERVER_VERSION = "1.0.0"
PROTOCOL_VERSIONS = ("2025-11-25", "2025-06-18", "2025-03-26")
INSTRUCTIONS = (
    "AXIGNAL is the governed economic memory of the organizations this subscriber observes. "
    "Start with list_xeeds, then get_xeed_overview; use get_xeed_evidence and get_xeed_timeline "
    "to trace and date each conclusion. Answer only from these tools for facts about the "
    "organization; keep OBSERVED, POTENTIAL and UNKNOWN as labelled. This server is read-only."
)


class McpDenied(Exception):
    """A read the caller is not entitled to. The code never reveals whether a Xeed exists."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True, slots=True)
class XeedSummary:
    xeed_id: str
    organization: str


class SubscriberMemoryPort(Protocol):
    """The subscriber runtime: membership, tenant, entitlement and ownership live behind it."""

    def authorized_xeeds(
        self, context: TrustedRequestContext, *, now: datetime
    ) -> tuple[XeedSummary, ...]:
        """Xeeds this tenant may read now; raises McpDenied when no entitlement is current."""

    def reading(
        self, context: TrustedRequestContext, xeed_id: str, *, now: datetime
    ) -> Mapping[str, Any]:
        """The authorized subscriber reading wire for one Xeed."""


@dataclass(frozen=True, slots=True)
class McpAuditEvent:
    at: datetime
    principal_id: str
    tenant_id: str
    client_id: str
    method: str
    target: str | None
    xeed_id: str | None
    outcome: str
    reason: str | None
    duration_ms: int
    response_bytes: int
    #: Structural: this surface has no model dependency; kept explicit for unit economics.
    model_calls: int = 0


class McpAuditSink(Protocol):
    def record(self, event: McpAuditEvent) -> None: ...


_READ_ONLY = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": False,
}
_XEED_ARG = {"xeed_id": {"type": "string", "description": "An id returned by list_xeeds."}}

TOOLS: tuple[dict[str, object], ...] = (
    {
        "name": "list_xeeds",
        "title": "List observed organizations",
        "description": "Organizations (Xeeds) this subscriber is entitled to read now.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        "annotations": _READ_ONLY,
    },
    {
        "name": "get_xeed_overview",
        "title": "What AXIGNAL knows",
        "description": (
            "Current governed reading of one Xeed: signals, POTENTIAL opportunities, recent "
            "changes and explicit UNKNOWNs, each with epistemic state, currentness and evidence."
        ),
        "inputSchema": {
            "type": "object",
            "properties": _XEED_ARG,
            "required": ["xeed_id"],
            "additionalProperties": False,
        },
        "annotations": _READ_ONLY,
    },
    {
        "name": "get_xeed_evidence",
        "title": "Evidence and provenance",
        "description": "Sources behind the reading: URL, observation time, currentness, instrument and limits. Paged.",
        "inputSchema": {
            "type": "object",
            "properties": {
                **_XEED_ARG,
                "cursor": {"type": "string", "description": "next_cursor from a previous page."},
            },
            "required": ["xeed_id"],
            "additionalProperties": False,
        },
        "annotations": _READ_ONLY,
    },
    {
        "name": "get_xeed_timeline",
        "title": "What changed over time",
        "description": "Observation history: current vs previous state, material changes and currentness.",
        "inputSchema": {
            "type": "object",
            "properties": _XEED_ARG,
            "required": ["xeed_id"],
            "additionalProperties": False,
        },
        "annotations": _READ_ONLY,
    },
)
_VIEWS = {
    "overview": "get_xeed_overview",
    "evidence": "get_xeed_evidence",
    "timeline": "get_xeed_timeline",
}
TEMPLATE = "axignal://xeeds/{xeed_id}/{view}"


def _cursor(xeed_id: str, offset: int) -> str:
    raw = json.dumps({"x": xeed_id, "o": offset}, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _offset(cursor: object, xeed_id: str) -> int:
    """A cursor only continues the same Xeed's listing; anything else is rejected."""
    if cursor is None:
        return 0
    if not isinstance(cursor, str) or len(cursor) > 200:
        raise McpDenied("INVALID_CURSOR")
    try:
        data = json.loads(base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)))
    except (ValueError, json.JSONDecodeError) as error:
        raise McpDenied("INVALID_CURSOR") from error
    if not isinstance(data, dict) or data.get("x") != xeed_id or not isinstance(data.get("o"), int):
        raise McpDenied("INVALID_CURSOR")
    offset = data["o"]
    if not 0 <= offset <= 10_000:
        raise McpDenied("INVALID_CURSOR")
    return int(offset)


class ProductMcpServer:
    def __init__(
        self,
        memory: SubscriberMemoryPort,
        *,
        clock: Callable[[], datetime],
        audit: McpAuditSink | None = None,
    ) -> None:
        self._memory = memory
        self._clock = clock
        self._audit = audit

    def handle(self, message: object, *, grant: McpGrant) -> dict[str, object] | None:
        """One JSON-RPC message. Returns the response, or None for a notification."""

        started = time.monotonic()
        trace: dict[str, str | None] = {
            "target": None,
            "xeed_id": None,
            "outcome": "OK",
            "reason": None,
        }
        response = self._dispatch(message, grant=grant, trace=trace)
        method = message.get("method") if isinstance(message, dict) else None
        if (
            self._audit is not None
            and response is not None
            and method not in {"initialize", "ping"}
        ):
            self._audit.record(
                McpAuditEvent(
                    at=self._clock(),
                    principal_id=grant.principal_id,
                    tenant_id=grant.tenant_id,
                    client_id=grant.client_id,
                    method=str(method),
                    target=trace["target"],
                    xeed_id=trace["xeed_id"],
                    outcome=str(trace["outcome"])
                    if "error" not in response
                    else trace["outcome"] or "INVALID",
                    reason=trace["reason"],
                    duration_ms=int((time.monotonic() - started) * 1000),
                    response_bytes=len(json.dumps(response, ensure_ascii=False).encode("utf-8")),
                )
            )
        return response

    def _dispatch(
        self, message: object, *, grant: McpGrant, trace: dict[str, str | None]
    ) -> dict[str, object] | None:
        if (
            not isinstance(message, dict)
            or message.get("jsonrpc") != "2.0"
            or not isinstance(message.get("method"), str)
        ):
            return _error(None, -32600, "Invalid Request")
        method = message["method"]
        request_id = message.get("id")
        if "id" not in message:
            return None  # notifications (e.g. notifications/initialized) need no answer
        params = message.get("params") or {}
        if not isinstance(params, dict):
            return _error(request_id, -32602, "params must be an object")
        context = TrustedRequestContext(grant.principal_id, grant.tenant_id)
        try:
            if method == "initialize":
                asked = params.get("protocolVersion")
                result: dict[str, object] = {
                    "protocolVersion": asked
                    if asked in PROTOCOL_VERSIONS
                    else PROTOCOL_VERSIONS[0],
                    "capabilities": {
                        "tools": {"listChanged": False},
                        "resources": {"listChanged": False},
                    },
                    "serverInfo": {
                        "name": SERVER_NAME,
                        "title": "AXIGNAL",
                        "version": SERVER_VERSION,
                    },
                    "instructions": INSTRUCTIONS,
                }
            elif method == "ping":
                result = {}
            elif method == "tools/list":
                result = {"tools": list(TOOLS)}
            elif method == "tools/call":
                target = params.get("name") if isinstance(params.get("name"), str) else None
                trace["target"] = target
                arguments = params.get("arguments") or {}
                if not isinstance(arguments, dict):
                    return _error(request_id, -32602, "arguments must be an object")
                raw_xeed = arguments.get("xeed_id")
                trace["xeed_id"] = raw_xeed[:160] if isinstance(raw_xeed, str) else None
                try:
                    data = self._tool(context, target, arguments)
                except McpDenied as denied:
                    trace["outcome"], trace["reason"] = "DENIED", denied.code
                    data = {
                        "error": denied.code,
                        "message": _DENIAL_TEXT.get(denied.code, "Not available."),
                    }
                    result = _tool_result(data, is_error=True)
                else:
                    result = _tool_result(data)
            elif method == "resources/list":
                result = {
                    "resources": [
                        {
                            "uri": TEMPLATE.format(xeed_id=x.xeed_id, view="overview"),
                            "name": f"{x.organization} — overview",
                            "mimeType": "application/json",
                        }
                        for x in self._memory.authorized_xeeds(context, now=self._clock())
                    ]
                }
            elif method == "resources/templates/list":
                result = {
                    "resourceTemplates": [
                        {
                            "uriTemplate": "axignal://xeeds/{xeed_id}/" + view,
                            "name": f"Xeed {view}",
                            "mimeType": "application/json",
                        }
                        for view in _VIEWS
                    ]
                }
            elif method == "resources/read":
                uri = params.get("uri")
                target = uri[:300] if isinstance(uri, str) else None
                trace["target"] = target
                xeed_id, view = _parse_uri(target)
                trace["xeed_id"] = xeed_id
                data = self._tool(context, _VIEWS[view], {"xeed_id": xeed_id})
                result = {
                    "contents": [
                        {
                            "uri": target,
                            "mimeType": "application/json",
                            "text": json.dumps(data, ensure_ascii=False),
                        }
                    ]
                }
            else:
                trace["outcome"], trace["reason"] = "INVALID", "METHOD_NOT_FOUND"
                return _error(request_id, -32601, "Method not found")
        except McpDenied as denied:
            # Resource reads and listings fail closed with a protocol error and no data.
            trace["outcome"], trace["reason"] = "DENIED", denied.code
            return _error(
                request_id,
                -32002,
                _DENIAL_TEXT.get(denied.code, "Not available."),
                {"reason": denied.code},
            )
        return {"jsonrpc": "2.0", "id": request_id, "result": result}

    def _authorized(self, context: TrustedRequestContext, xeed_id: object) -> str:
        if not isinstance(xeed_id, str) or not 0 < len(xeed_id) <= 160:
            raise McpDenied("XEED_NOT_AVAILABLE")
        allowed = {x.xeed_id for x in self._memory.authorized_xeeds(context, now=self._clock())}
        if xeed_id not in allowed:
            raise McpDenied("XEED_NOT_AVAILABLE")
        return xeed_id

    def _tool(
        self, context: TrustedRequestContext, name: str | None, arguments: Mapping[str, Any]
    ) -> dict[str, object]:
        now = self._clock()
        if name == "list_xeeds":
            return {
                "xeeds": [
                    {"xeed_id": x.xeed_id, "organization": x.organization}
                    for x in self._memory.authorized_xeeds(context, now=now)
                ],
                "how_to_read": views.HOW_TO_READ,
            }
        if name not in {"get_xeed_overview", "get_xeed_evidence", "get_xeed_timeline"}:
            raise McpDenied("UNKNOWN_TOOL")
        unexpected = set(arguments) - {"xeed_id", "cursor"}
        if unexpected:
            raise McpDenied("INVALID_ARGUMENTS")
        xeed_id = self._authorized(context, arguments.get("xeed_id"))
        if name == "get_xeed_evidence":
            offset = _offset(arguments.get("cursor"), xeed_id)
        wire = self._memory.reading(context, xeed_id, now=now)
        if name == "get_xeed_overview":
            return views.overview(xeed_id, wire)
        if name == "get_xeed_timeline":
            return views.timeline(xeed_id, wire)
        page, following = views.evidence(xeed_id, wire, offset=offset)
        return {**page, "next_cursor": None if following is None else _cursor(xeed_id, following)}


_DENIAL_TEXT = {
    "XEED_NOT_AVAILABLE": "That Xeed is not available to this subscription. Use list_xeeds.",
    "ENTITLEMENT_INACTIVE": "This subscription has no current access (pilot or plan). Nothing can be read.",
    "INVALID_CURSOR": "The cursor is not valid for this Xeed. Start again without a cursor.",
    "INVALID_ARGUMENTS": "Unexpected arguments.",
    "UNKNOWN_TOOL": "Unknown tool.",
    "INVALID_URI": "Unknown resource. Use axignal://xeeds/{xeed_id}/overview|evidence|timeline.",
}


def _parse_uri(uri: str | None) -> tuple[str, str]:
    prefix = "axignal://xeeds/"
    if not uri or not uri.startswith(prefix):
        raise McpDenied("INVALID_URI")
    parts = uri.removeprefix(prefix).split("/")
    if len(parts) != 2 or parts[1] not in _VIEWS or not parts[0]:
        raise McpDenied("INVALID_URI")
    return parts[0], parts[1]


def _tool_result(data: dict[str, object], *, is_error: bool = False) -> dict[str, object]:
    return {
        "content": [{"type": "text", "text": json.dumps(data, ensure_ascii=False)}],
        "structuredContent": data,
        "isError": is_error,
    }


def _error(request_id: object, code: int, message: str, data: object = None) -> dict[str, object]:
    error: dict[str, object] = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {"jsonrpc": "2.0", "id": request_id, "error": error}
