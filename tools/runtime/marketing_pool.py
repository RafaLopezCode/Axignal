"""The marketing pool runner: discover → study → qualify → draft, then send what staff approve.

Autonomous up to the draft, bounded per day, never repeating an organization. Nothing is
sent without an explicit Admin approval, nothing goes to a suppressed domain or address,
and only to markets whose channel policy is EMAIL. A study runs on the governed First
Observation runtime under a staff-only tenant: it creates no Organization and no
canonical state (Admin §5.7: AXIGNAL CRM LEAD != AXIGLAND ORGANIZATION STATE).
"""

from __future__ import annotations

import os
import secrets
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Protocol

from application.marketing_pool.email_template import LABELS, render_html, signature_role
from application.marketing_pool.personas import PERSONAS, PERSONAS_VERSION, best_persona, persona
from application.marketing_pool.policy import (
    CHANNEL_POLICY_VERSION,
    MARKETS,
    Channel,
    channel_for,
)
from application.marketing_pool.prospect import (
    INSTRUCTION,
    SCHEMA,
    accept_draft,
    findings,
    footer,
    gate,
    language_of,
    legal_notice,
    prompt,
    recipient,
    site_text,
)
from cognition.jobs.model import CognitiveJob, JobKind
from domain.admin_access import AdminRiskClass, AdminScope
from pipeline.marketing_pool.discovery import OverpassDiscovery, WikidataDiscovery
from pipeline.marketing_pool.smtp import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    OutgoingMessage,
    SmtpSender,
    SmtpSettings,
)
from pipeline.marketing_pool.sqlite_store import Candidate, SqliteMarketingPool
from tools.runtime.admin_access import AdminHttpAccessGuard

ENABLED_KEY = "AXIGNAL_MARKETING_POOL_ENABLED"
_RETRY = timedelta(days=1)
STUDY_PREFIX = "pool:"
WAITING = {"QUEUED", "OBSERVING_PUBLIC_PRESENCE", None}
FAILED = {"OBSERVATION_FAILED", "SOURCE_UNAVAILABLE", "NO_PUBLIC_WEBSITE"}


class Source(Protocol):
    name: str

    def find(self, persona: Any, market: Any) -> list[Candidate]: ...


class Sender(Protocol):
    @property
    def sender_address(self) -> str: ...

    def send(self, message: OutgoingMessage) -> str: ...


@dataclass(frozen=True, slots=True)
class Operator:
    """Who signs and where to reach them: the published legal identity, nothing else."""

    sender_name: str
    postal_address: str
    public_origin: str
    #: Shown under the name as "<role> of Axignal.com" in the message's language.
    sender_role: str | None = None


@dataclass(frozen=True, slots=True)
class Limits:
    studies_per_day: int = 12
    sends_per_day: int = 20
    min_backlog: int = 40
    rediscover_after: timedelta = timedelta(days=30)
    study_timeout: timedelta = timedelta(days=2)


class MarketingPoolRunner:
    def __init__(
        self,
        store: SqliteMarketingPool,
        sources: tuple[Source, ...],
        *,
        study: Callable[[str, str, str], str],
        study_result: Callable[[str], tuple[Mapping[str, Any] | None, Mapping[str, Any]]],
        complete: Callable[[CognitiveJob], Any] | None,
        model: str | None,
        operator: Operator,
        sender: Sender | None = None,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        limits: Limits | None = None,
    ) -> None:
        self.store = store
        self._sources = sources
        self._study = study
        self._study_result = study_result
        self._complete = complete
        self._model = model
        self._operator = operator
        self._sender = sender
        self._clock = clock
        self.limits = limits or Limits()

    # ---- one background tick ----------------------------------------------------------
    def tick(self) -> dict[str, int]:
        return {
            "discovered": self.discover(),
            "studying": self.start_studies(),
            "concluded": self.collect(),
            "sent": self.send_approved(),
        }

    def discover(self) -> int:
        """One persona, country and source per tick, while the backlog is short."""
        now = self._clock()
        if len(self.store.in_state("DISCOVERED", limit=self.limits.min_backlog)) >= (
            self.limits.min_backlog
        ):
            return 0
        # Markets whose channel is open come first: a held study cannot be sent.
        markets = sorted(MARKETS, key=lambda m: m.channel is not Channel.EMAIL)
        for market in markets:
            for candidate_persona in PERSONAS:
                for source in self._sources:
                    key = f"{source.name}|{candidate_persona.id}|{market.iso}"
                    last = self.store.discovery_done(key)
                    if last is not None:
                        # A failed search (rate limit, timeout) is retried the next day.
                        wait = self.limits.rediscover_after if last[1] is None else _RETRY
                        if now - datetime.fromisoformat(last[0]) < wait:
                            continue
                    try:
                        found = source.find(candidate_persona, market)
                    except Exception as error:  # a refusing or slow source is skipped
                        self.store.record_discovery(
                            key, now=now, found=0, added=0, error=type(error).__name__
                        )
                        return 0
                    added = self.store.add(found, now=now)
                    self.store.record_discovery(
                        key, now=now, found=len(found), added=added, error=None
                    )
                    return added
        return 0

    def start_studies(self) -> int:
        now = self._clock()
        left = self.limits.studies_per_day - self.store.studies_started_today(
            now.date().isoformat()
        )
        if left <= 0:
            return 0
        waiting = self.store.in_state("DISCOVERED", limit=500)
        waiting.sort(key=lambda p: channel_for(p["country"])[0] is not Channel.EMAIL)
        started = 0
        for prospect in waiting[:left]:
            outcome = self._study(STUDY_PREFIX + prospect["domain"], prospect["website"],
                                  prospect["name"])  # fmt: skip
            if outcome != "QUEUED":
                break  # the runtime's own budget is spent: try again tomorrow
            self.store.move(
                prospect["domain"], "STUDYING", now=now, actor="marketing-pool",
                expected=("DISCOVERED",),
            )  # fmt: skip
            started += 1
        return started

    def collect(self) -> int:
        """Conclude finished studies: qualify, choose the address and draft the message."""
        concluded = 0
        for prospect in self.store.in_state("STUDYING", limit=40):
            if self._conclude(prospect):
                concluded += 1
        return concluded

    def _conclude(self, prospect: Mapping[str, Any]) -> bool:
        now = self._clock()
        domain = str(prospect["domain"])
        view, contact = self._study_result(STUDY_PREFIX + domain)
        state = None if view is None else view.get("state")
        if state in WAITING or view is None:
            started = datetime.fromisoformat(str(prospect["updated_at"]))
            if now - started > self.limits.study_timeout:
                return self.store.move(domain, "STUDY_FAILED", now=now, actor="marketing-pool",
                                       reason="STUDY_TIMED_OUT")  # fmt: skip
            return False
        if state in FAILED:
            return self.store.move(domain, "STUDY_FAILED", now=now, actor="marketing-pool",
                                   reason=str(state))  # fmt: skip
        chosen, words = best_persona(site_text(view), prospect.get("persona"))
        if chosen is None:
            return self.store.move(domain, "NOT_QUALIFIED", now=now, actor="marketing-pool",
                                   reason="NOT_A_TARGET_PERSONA")  # fmt: skip
        selected = findings(view, chosen.lead_families)
        emails = contact.get("emails")
        address = recipient(emails if isinstance(emails, list) else [], domain)
        language = language_of(
            contact.get("language") if isinstance(contact.get("language"), str) else None,
            prospect["country"],
        )
        channel, basis = channel_for(prospect["country"])
        detail: dict[str, object] = {
            "personaEvidence": list(words),
            "personasVersion": PERSONAS_VERSION,
            "findings": [f.to_wire() for f in selected],
            "families": sorted({f.family for f in selected}),
            "recipient": address,
            "language": language,
            "channel": channel.value,
            "channelBasis": basis,
            "channelPolicy": CHANNEL_POLICY_VERSION,
            "studiedAt": view.get("observedAt"),
        }
        reason = gate(selected)
        if reason is not None:
            return self.store.move(domain, "NOT_QUALIFIED", now=now, actor="marketing-pool",
                                   reason=reason, detail=detail, persona=chosen.id)  # fmt: skip
        if self._complete is None:
            return False  # no governed assistant: stays studied until one is configured
        try:
            result = self._complete(
                CognitiveJob(
                    id=f"outreach-draft:{uuid.uuid4().hex}",
                    kind=JobKind.OUTREACH_DRAFT,
                    instruction=INSTRUCTION,
                    context={
                        "schema": SCHEMA,
                        "user": prompt(str(prospect["name"]), language, chosen, selected),
                        "max_output_tokens": 900,
                    },
                )
            )
        except Exception:  # unavailable: concluded on a later tick
            return False
        payload = result.payload if hasattr(result, "payload") else {}
        answer = payload.get("answer") if isinstance(payload, Mapping) else None
        draft = accept_draft(answer if isinstance(answer, Mapping) else {}, selected)
        if draft is None:
            return self.store.move(domain, "NOT_QUALIFIED", now=now, actor="marketing-pool",
                                   reason="DRAFT_NOT_GROUNDED", detail=detail,
                                   persona=chosen.id)  # fmt: skip
        token = secrets.token_urlsafe(16)
        origin = self._operator.public_origin.rstrip("/")
        draft["footer"] = footer(
            language,
            link=f"{origin}/r/{token}",
            sender=self._operator.sender_name,
            address=self._operator.postal_address,
            domain=domain,
            unsubscribe=f"{origin}/r/{token}/unsubscribe",
            signature=self._signature(language),
        )
        draft["legal"] = legal_notice(
            language,
            sender=self._operator.sender_name,
            address=self._operator.postal_address,
            domain=domain,
        )
        draft["model"] = self._model
        detail.update({"draft": draft, "token": token})
        if self.store.is_suppressed(domain) or (address and self.store.is_suppressed(address)):
            return self.store.move(domain, "SUPPRESSED", now=now, actor="marketing-pool",
                                   reason="SUPPRESSED", detail=detail)  # fmt: skip
        if channel is not Channel.EMAIL or address is None:
            why = "CHANNEL_POLICY_HOLD" if channel is not Channel.EMAIL else "NO_ROLE_ADDRESS"
            return self.store.move(domain, "HELD", now=now, actor="marketing-pool",
                                   reason=why, detail=detail, persona=chosen.id)  # fmt: skip
        return self.store.move(domain, "DRAFTED", now=now, actor="marketing-pool",
                               detail=detail, persona=chosen.id)  # fmt: skip

    def send_approved(self) -> int:
        if self._sender is None:
            return 0
        now = self._clock()
        left = self.limits.sends_per_day - self.store.sent_today(now.date().isoformat())
        sent = 0
        for prospect in self.store.in_state("APPROVED", limit=max(0, left)):
            domain, detail = str(prospect["domain"]), prospect["detail"]
            address, draft = detail.get("recipient"), detail.get("draft") or {}
            channel, _basis = channel_for(prospect["country"])
            if (
                not isinstance(address, str)
                or channel is not Channel.EMAIL
                or self.store.is_suppressed(address)
                or self.store.is_suppressed(domain)
            ):
                self.store.move(domain, "HELD", now=now, actor="marketing-pool",
                                reason="NOT_SENDABLE_AT_SEND_TIME")  # fmt: skip
                continue
            origin = self._operator.public_origin.rstrip("/")
            token = str(detail.get("token"))
            html = self.html(prospect)
            try:
                message_id = self._sender.send(
                    OutgoingMessage(
                        to=address,
                        subject=str(draft["subject"]),
                        body=f"{draft['body']}\n\n{draft['footer']}",
                        language=str(detail.get("language") or "en"),
                        unsubscribe_url=f"{origin}/api/marketing/unsubscribe/{token}",  # RFC 8058 POST
                        unsubscribe_mailto=f"mailto:{self._sender.sender_address}"
                        f"?subject=unsubscribe%20{domain}",
                        html=html,
                    )
                )
            except Exception as error:
                self.store.move(domain, "SEND_FAILED", now=now, actor="marketing-pool",
                                reason=type(error).__name__)  # fmt: skip
                continue
            self.store.move(domain, "SENT", now=now, actor="marketing-pool",
                            detail={"messageId": message_id, "sentAt": now.isoformat()})  # fmt: skip
            sent += 1
        return sent

    def _signature(self, language: str) -> str:
        role = signature_role(language, self._operator.sender_role)
        signoff = LABELS.get(language, LABELS["en"])["signoff"]
        return "\n".join(x for x in (signoff, self._operator.sender_name, role) if x)

    def html(self, prospect: Mapping[str, Any]) -> str | None:
        """The exact HTML a recipient gets (also what Admin previews before approving)."""
        detail = prospect["detail"]
        draft = detail.get("draft")
        if not isinstance(draft, Mapping) or not detail.get("token"):
            return None
        origin = self._operator.public_origin.rstrip("/")
        token = str(detail["token"])
        studied = detail.get("studiedAt")
        return render_html(
            language=str(detail.get("language") or "en"),
            domain=str(prospect["domain"]),
            studied_on=studied if isinstance(studied, str) else None,
            subject=str(draft.get("subject") or ""),
            body=str(draft.get("body") or ""),
            findings=list(draft.get("findingsUsed") or []),
            reading_url=f"{origin}/r/{token}",
            unsubscribe_url=f"{origin}/r/{token}/unsubscribe",
            sender_name=self._operator.sender_name,
            sender_role=self._operator.sender_role,
            legal_text=str(draft.get("legal") or ""),
            asset_origin=origin,
        )

    # ---- public reading and opt-out ---------------------------------------------------
    def _by_token(self, token: str) -> Mapping[str, Any] | None:
        if not token or len(token) > 64:
            return None
        for state in ("SENT", "DRAFTED", "APPROVED", "HELD"):
            for prospect in self.store.in_state(state, limit=5000):
                if secrets.compare_digest(str(prospect["detail"].get("token") or ""), token):
                    return prospect
        return None

    def reading(self, token: str) -> dict[str, object] | None:
        """The findings written to it, with sources: what its link opens. Nothing else."""
        prospect = self._by_token(token)
        if prospect is None or prospect["state"] != "SENT":
            return None
        detail = prospect["detail"]
        return {
            "name": prospect["name"],
            "domain": prospect["domain"],
            "language": detail.get("language"),
            "studiedAt": detail.get("studiedAt"),
            "findings": detail.get("findings") or [],
            "authority": "OPERATIONAL_NOT_CANONICAL",
        }

    def unsubscribe(self, token: str) -> bool:
        prospect = self._by_token(token)
        if prospect is None:
            return False
        now = self._clock()
        address = prospect["detail"].get("recipient")
        self.store.suppress(str(prospect["domain"]), reason="RECIPIENT_OPT_OUT", now=now,
                            actor="recipient")  # fmt: skip
        if isinstance(address, str):
            self.store.suppress(address, reason="RECIPIENT_OPT_OUT", now=now, actor="recipient")
        return True

    # ---- admin ------------------------------------------------------------------------
    def snapshot(self) -> dict[str, object]:
        shown = ("DRAFTED", "APPROVED", "SENT", "HELD", "SEND_FAILED", "NOT_QUALIFIED",
                 "STUDYING", "STUDY_FAILED", "SUPPRESSED", "DISCARDED")  # fmt: skip
        return {
            "enabled": True,
            "sending": None if self._sender is None else self._sender.sender_address,
            "drafting": self._complete is not None,
            "limits": {
                "studiesPerDay": self.limits.studies_per_day,
                "sendsPerDay": self.limits.sends_per_day,
            },
            "versions": {"personas": PERSONAS_VERSION, "channelPolicy": CHANNEL_POLICY_VERSION},
            "personas": [{"id": p.id, "label": p.label} for p in PERSONAS],
            "markets": [
                {"iso": m.iso, "channel": m.channel.value, "basis": m.basis} for m in MARKETS
            ],
            "counts": self.store.counts(),
            "prospects": [
                {**_wire(p), "html": self.html(p) if p["state"] in _PREVIEW else None}
                for p in self.store.recent(shown, limit=150)
            ],
            "discovery": self.store.discovery_log(limit=12),
        }

    def decide(self, domain: str, action: str, *, actor: str) -> bool:
        now = self._clock()
        if action == "APPROVE":
            return self.store.move(domain, "APPROVED", now=now, actor=actor,
                                   expected=("DRAFTED",))  # fmt: skip
        if action == "DISCARD":
            return self.store.move(
                domain, "DISCARDED", now=now, actor=actor,
                expected=("DRAFTED", "HELD", "APPROVED", "NOT_QUALIFIED", "STUDY_FAILED"),
            )  # fmt: skip
        if action == "SUPPRESS":
            self.store.suppress(domain, reason="STAFF_DECISION", now=now, actor=actor)
            return True
        raise ValueError("unknown marketing pool action")


_PREVIEW = {"DRAFTED", "APPROVED", "HELD", "SENT"}


def _wire(prospect: Mapping[str, Any]) -> dict[str, object]:
    detail = prospect["detail"]
    draft = detail.get("draft") if isinstance(detail.get("draft"), Mapping) else None
    found = persona(str(prospect.get("persona") or ""))
    return {
        "domain": prospect["domain"],
        "name": prospect["name"],
        "website": prospect["website"],
        "country": prospect["country"],
        "persona": None if found is None else found.label,
        "source": prospect["source"],
        "sourceRef": prospect["source_ref"],
        "state": prospect["state"],
        "reason": prospect["reason"],
        "updatedAt": prospect["updated_at"],
        "recipient": detail.get("recipient"),
        "language": detail.get("language"),
        "channel": detail.get("channel"),
        "channelBasis": detail.get("channelBasis"),
        "families": detail.get("families") or [],
        "findings": detail.get("findings") or [],
        "draft": None
        if draft is None
        else {
            "subject": draft.get("subject"),
            "body": draft.get("body"),
            "footer": draft.get("footer"),
        },
        "sentAt": detail.get("sentAt"),
    }


def marketing_pool_request(
    guard: AdminHttpAccessGuard,
    runner: MarketingPoolRunner | None,
    *,
    authorization: str | None,
    now: datetime,
    payload: dict[str, object] | None = None,
) -> dict[str, object]:
    write = payload is not None
    grant = guard.authorize_header(
        authorization,
        required_scope=AdminScope.ACQUISITION_WRITE if write else AdminScope.ACQUISITION_READ,
        risk=AdminRiskClass.WRITE if write else AdminRiskClass.READ,
        now=now,
    )
    if runner is None:
        return {"enabled": False}
    if payload is not None:
        if set(payload) != {"domain", "action"}:
            raise ValueError("invalid marketing pool fields")
        domain, action = payload["domain"], payload["action"]
        if not isinstance(domain, str) or action not in {"APPROVE", "DISCARD", "SUPPRESS"}:
            raise ValueError("invalid marketing pool values")
        if not runner.decide(domain.strip().lower(), str(action), actor=str(grant.principal_id)):
            raise LookupError("prospect not in a state that allows this")
    return runner.snapshot()


def smtp_from_values(values: Mapping[str, str]) -> SmtpSender | None:
    """The operator's mailbox; off unless every setting and the secret file exist."""
    address = values.get("AXIGNAL_MARKETING_POOL_SMTP_FROM", "").strip()
    filename = values.get("AXIGNAL_MARKETING_POOL_SMTP_PASSWORD_FILE", "").strip()
    if values.get("AXIGNAL_MARKETING_POOL_SEND", "false").strip().lower() != "true":
        return None
    if "@" not in address or not filename:
        return None
    password = Path(filename)
    if not password.is_absolute() or not password.is_file() or not os.access(password, os.R_OK):
        return None
    try:
        port = int(values.get("AXIGNAL_MARKETING_POOL_SMTP_PORT", str(DEFAULT_PORT)))
    except ValueError:
        return None
    return SmtpSender(
        SmtpSettings(
            host=values.get("AXIGNAL_MARKETING_POOL_SMTP_HOST", DEFAULT_HOST).strip()
            or DEFAULT_HOST,
            port=port,
            username=values.get("AXIGNAL_MARKETING_POOL_SMTP_USER", address).strip() or address,
            password_file=password,
            sender_name=values.get("AXIGNAL_MARKETING_POOL_SENDER_NAME", "AXIGNAL").strip()
            or "AXIGNAL",
            sender_address=address,
            reply_to=values.get("AXIGNAL_MARKETING_POOL_REPLY_TO", "").strip() or None,
        )
    )


def build_marketing_pool(
    values: Mapping[str, str],
    root: Path,
    *,
    study: Callable[[str, str, str], str],
    study_result: Callable[[str], tuple[Mapping[str, Any] | None, Mapping[str, Any]]],
    complete: Callable[[CognitiveJob], Any] | None,
    model: str | None,
) -> MarketingPoolRunner | None:
    if values.get(ENABLED_KEY, "false").strip().lower() != "true":
        return None
    operator = Operator(
        # The signature (e.g. a person's usual name); the legal name otherwise.
        sender_name=values.get("AXIGNAL_MARKETING_POOL_SIGNATURE", "").strip()
        or values.get("AXIGNAL_LEGAL_OPERATOR_NAME", "").strip()
        or "AXIGNAL",
        postal_address=values.get("AXIGNAL_LEGAL_ADDRESS", "").strip(),
        public_origin=values.get("AXIGNAL_PUBLIC_ORIGIN", "https://axignal.com").strip(),
        sender_role=values.get("AXIGNAL_MARKETING_POOL_SIGNATURE_ROLE", "").strip() or None,
    )
    if not operator.postal_address:
        return None  # a commercial message must identify its sender and postal address
    try:
        limits = Limits(
            studies_per_day=int(values.get("AXIGNAL_MARKETING_POOL_STUDIES_PER_DAY", "12")),
            sends_per_day=int(values.get("AXIGNAL_MARKETING_POOL_SENDS_PER_DAY", "20")),
        )
    except ValueError:
        limits = Limits()
    return MarketingPoolRunner(
        SqliteMarketingPool(root / "marketing-pool.sqlite3"),
        (OverpassDiscovery(), WikidataDiscovery()),
        study=study,
        study_result=study_result,
        complete=complete,
        model=model,
        operator=operator,
        sender=smtp_from_values(values),
        limits=limits,
    )


def main(argv: list[str] | None = None) -> None:
    """Read-only view of the pool for agents and operators (never decides, never sends).

    python -m tools.runtime.marketing_pool status --data-dir /path
    python -m tools.runtime.marketing_pool show <domain> --data-dir /path
    python -m tools.runtime.marketing_pool drafts --data-dir /path
    """
    import argparse
    import json

    parser = argparse.ArgumentParser(prog="marketing-pool")
    parser.add_argument("command", choices=("status", "show", "drafts"))
    parser.add_argument("domain", nargs="?")
    parser.add_argument("--data-dir", required=True, type=Path)
    args = parser.parse_args(argv)
    path = args.data_dir / "marketing-pool.sqlite3"
    if not path.is_file():
        raise SystemExit("no marketing pool at that data directory")
    store = SqliteMarketingPool(path)
    if args.command == "status":
        out: object = {"counts": store.counts(), "discovery": store.discovery_log(limit=10)}
    elif args.command == "show":
        found = store.get(str(args.domain or "").lower())
        out = None if found is None else _wire(found)
    else:
        out = [_wire(p) for p in store.recent(("DRAFTED", "HELD", "APPROVED"), limit=50)]
    print(json.dumps(out, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
