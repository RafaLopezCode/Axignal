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
from application.marketing_pool.playbooks import (
    PLAYBOOKS_VERSION,
    hook_brief,
    hooks,
    playbook_for,
)
from application.marketing_pool.policy import (
    CHANNEL_POLICY_VERSION,
    MARKETS,
    Channel,
    channel_for,
    market,
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
    salutation,
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
_NOT_STUDIED = {"DISCOVERED", "STUDYING", "OPTED_OUT"}
_QUALIFIED = ("DRAFTED", "APPROVED", "SENT", "HELD", "SEND_FAILED")


def _rate(learned: tuple[int, int] | None) -> float:
    """Share of studied prospects that qualified, smoothed so the unknown is not zero."""
    studied, qualified = learned or (0, 0)
    return (qualified + 1) / (studied + 2)


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
    #: Studies cost cents (Jev, GEO probe) and 40% of registry domains no longer load
    #: (pool dry run, 2026-10-17): a larger daily budget keeps drafts flowing; sends stay
    #: capped and approval-gated.
    studies_per_day: int = 40
    sends_per_day: int = 20
    min_backlog: int = 40
    rediscover_after: timedelta = timedelta(days=30)
    study_timeout: timedelta = timedelta(days=2)
    #: How long a studied prospect waits for its segment's hook (background measurements).
    hook_wait: timedelta = timedelta(days=3)


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

    def active_campaigns(self) -> list[dict[str, Any]]:
        """Active campaigns, oldest first; a campaign done, past its date or out of sources ends."""
        now = self._clock()
        active = []
        for campaign in self.store.campaigns():
            if campaign["state"] != "ACTIVE":
                continue
            counts = self.store.campaign_counts(campaign["id"])
            studied = sum(n for state, n in counts.items() if state not in _NOT_STUDIED)
            if studied >= campaign["target"] and not counts.get("STUDYING"):
                self.store.end_campaign(campaign["id"], "COMPLETED", reason="TARGET_REACHED",
                                        actor="marketing-pool", now=now)  # fmt: skip
                continue
            if campaign["ends_at"] and now >= datetime.fromisoformat(campaign["ends_at"]):
                self.store.end_campaign(campaign["id"], "ENDED", reason="END_DATE",
                                        actor="marketing-pool", now=now)  # fmt: skip
                continue
            campaign["studied"] = studied
            campaign["counts"] = counts
            active.append(campaign)
        return active

    def discover(self) -> int:
        """One search per tick: for an active campaign first, else the automatic rotation."""
        campaigns = self.active_campaigns()
        for campaign in campaigns:
            remaining = campaign["target"] - campaign["studied"]
            backlog = campaign["counts"].get("DISCOVERED", 0)
            if remaining <= 0 or backlog >= min(self.limits.min_backlog, remaining * 3):
                continue
            pairs = [
                (found, chosen)
                for iso in campaign["countries"]
                if (found := market(iso)) is not None
                for pid in campaign["personas"]
                if (chosen := persona(pid)) is not None
            ]
            outcome = self._search(pairs, prefix=f"c:{campaign['id']}|", campaign=campaign["id"],
                                   rediscover=False)  # fmt: skip
            if outcome is None and backlog == 0 and not campaign["counts"].get("STUDYING"):
                self.store.end_campaign(campaign["id"], "EXHAUSTED", reason="NO_MORE_CANDIDATES",
                                        actor="marketing-pool", now=self._clock())  # fmt: skip
            if outcome is not None:
                return outcome
        if campaigns:
            return 0  # a directed campaign holds the budget until it ends
        if len(self.store.waiting(None, limit=self.limits.min_backlog)) >= self.limits.min_backlog:
            return 0
        learned = self.store.yields()
        pairs = [(m, p) for m in MARKETS for p in PERSONAS]
        # Open channel first, then what has qualified best (Laplace-smoothed), then rotation.
        pairs.sort(key=lambda pair: (pair[0].channel is not Channel.EMAIL,
                                     -_rate(learned.get((pair[1].id, pair[0].iso)))))  # fmt: skip
        return self._search(pairs, prefix="", campaign=None, rediscover=True) or 0

    def _search(
        self,
        pairs: list[tuple[Any, Any]],
        *,
        prefix: str,
        campaign: str | None,
        rediscover: bool,
    ) -> int | None:
        """Run the first due search; None when every search is done (or waiting to retry)."""
        now = self._clock()
        for market_, persona_ in pairs:
            for source in self._sources:
                key = f"{prefix}{source.name}|{persona_.id}|{market_.iso}"
                last = self.store.discovery_done(key)
                if last is not None:
                    if last[1] is None and not rediscover:
                        continue  # a campaign searches each source once
                    # A failed search (rate limit, timeout) is retried the next day.
                    wait = self.limits.rediscover_after if last[1] is None else _RETRY
                    if now - datetime.fromisoformat(last[0]) < wait:
                        continue
                try:
                    found = source.find(persona_, market_)
                except Exception as error:  # a refusing or slow source is skipped
                    self.store.record_discovery(
                        key, now=now, found=0, added=0, error=type(error).__name__
                    )
                    return 0
                added = self.store.add(found, now=now, campaign_id=campaign)
                self.store.record_discovery(key, now=now, found=len(found), added=added,
                                            error=None)  # fmt: skip
                return added
        return None

    def start_studies(self) -> int:
        """Spend today's study budget: active campaigns first, then the automatic pool."""
        now = self._clock()
        left = self.limits.studies_per_day - self.store.studies_started_today(
            now.date().isoformat()
        )
        if left <= 0:
            return 0
        campaigns = self.active_campaigns()
        queue: list[dict[str, Any]] = []
        for campaign in campaigns:
            room = campaign["target"] - campaign["studied"] - campaign["counts"].get("STUDYING", 0)
            if room > 0:
                waiting = self.store.waiting(campaign["id"], limit=room)
                waiting.sort(key=lambda p: channel_for(p["country"])[0] is not Channel.EMAIL)
                queue += waiting
        if not campaigns:
            learned = self.store.yields()
            waiting = self.store.waiting(None)
            waiting.sort(key=lambda p: (channel_for(p["country"])[0] is not Channel.EMAIL,
                                        -_rate(learned.get((str(p["persona"]), p["country"])))))  # fmt: skip
            queue += waiting
        started = 0
        for prospect in queue[:left]:
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

    # ---- campaigns ----------------------------------------------------------------------
    def create_campaign(
        self,
        *,
        name: str,
        personas: list[str],
        countries: list[str],
        target: int,
        ends_on: str | None,
        actor: str,
    ) -> str:
        """A directed campaign: these personas in these countries, this many studies."""
        now = self._clock()
        clean = name.strip()
        if not 1 <= len(clean) <= 80:
            raise ValueError("campaign name must be 1-80 characters")
        if not personas or any(persona(p) is None for p in personas):
            raise ValueError("unknown persona")
        if not countries or any(market(c) is None for c in countries):
            raise ValueError("unknown or unsupported country")
        if type(target) is not int or not 1 <= target <= 500:
            raise ValueError("target must be 1-500 organizations")
        ends_at = None
        if ends_on:
            ends_at = datetime.fromisoformat(ends_on).replace(tzinfo=UTC) + timedelta(days=1)
            if ends_at <= now:
                raise ValueError("end date is in the past")
        campaign_id = "cmp_" + secrets.token_hex(6)
        self.store.create_campaign(
            campaign_id=campaign_id, name=clean, personas=sorted(set(personas)),
            countries=sorted({c.upper() for c in countries}), target=target, ends_at=ends_at,
            actor=actor, now=now,
        )  # fmt: skip
        return campaign_id

    def cancel_campaign(self, campaign_id: str, *, actor: str) -> bool:
        return self.store.end_campaign(
            campaign_id, "CANCELLED", reason="STAFF_DECISION", actor=actor, now=self._clock()
        )

    def campaign_view(self) -> list[dict[str, object]]:
        self.active_campaigns()  # settle campaigns that are done before showing them
        out: list[dict[str, object]] = []
        for campaign in reversed(self.store.campaigns()):
            counts = self.store.campaign_counts(campaign["id"])
            out.append({
                "id": campaign["id"], "name": campaign["name"], "state": campaign["state"],
                "reason": campaign["reason"], "personas": campaign["personas"],
                "countries": campaign["countries"], "target": campaign["target"],
                "endsAt": campaign["ends_at"], "createdBy": campaign["created_by"],
                "createdAt": campaign["created_at"],
                "progress": {
                    "discovered": sum(counts.values()) - counts.get("OPTED_OUT", 0),
                    "studied": sum(n for st, n in counts.items() if st not in _NOT_STUDIED),
                    "qualified": sum(counts.get(st, 0) for st in _QUALIFIED),
                    "drafted": counts.get("DRAFTED", 0),
                    "approved": counts.get("APPROVED", 0),
                    "sent": counts.get("SENT", 0),
                    "held": counts.get("HELD", 0),
                    "optedOut": counts.get("OPTED_OUT", 0),
                },
            })  # fmt: skip
        return out

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
        held = view.get("discoveries")
        activities = tuple(
            str(d.get("code"))
            for d in (held if isinstance(held, list) else [])
            if isinstance(d, Mapping) and d.get("kind") == "ACTIVITY"
        )
        chosen, words = best_persona(site_text(view), prospect.get("persona"), activities)
        if chosen is None:
            return self.store.move(domain, "NOT_QUALIFIED", now=now, actor="marketing-pool",
                                   reason="NOT_A_TARGET_PERSONA")  # fmt: skip
        playbook = playbook_for(chosen.id)
        opening = hooks(view, playbook) if playbook is not None else []
        if playbook is not None and not opening:
            # Measurements (AI assistants, awards) land in the background: wait a while for
            # a hook; without one the letter would be generic, and it is not written.
            started = datetime.fromisoformat(str(prospect["updated_at"]))
            if now - started <= self.limits.hook_wait:
                return False
            return self.store.move(domain, "NOT_QUALIFIED", now=now, actor="marketing-pool",
                                   reason="NO_SEGMENT_HOOK", persona=chosen.id)  # fmt: skip
        selected = findings(
            view, playbook.families if playbook else chosen.lead_families, first=opening[:1]
        )
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
            "segment": None if playbook is None else playbook.segment,
            "playbooksVersion": PLAYBOOKS_VERSION,
            "hook": None
            if not opening
            else {
                "kind": opening[0].get("kind"),
                "code": opening[0].get("code"),
                "statement": opening[0].get("statement"),
            },
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
                        "user": prompt(
                            str(prospect["name"]),
                            language,
                            chosen,
                            selected,
                            segment=None if playbook is None else playbook.segment,
                            pain=None if playbook is None else playbook.pain,
                            hook=hook_brief(opening[0]) if opening else None,
                        ),
                        "max_output_tokens": 900,
                    },
                )
            )
        except Exception:  # unavailable: concluded on a later tick
            return False
        payload = result.payload if hasattr(result, "payload") else {}
        answer = payload.get("answer") if isinstance(payload, Mapping) else None
        draft = accept_draft(
            answer if isinstance(answer, Mapping) else {}, selected, require_first=bool(opening)
        )
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
        draft["greeting"] = salutation(language, chosen.id, str(prospect["name"]))
        draft["legal"] = legal_notice(
            language,
            sender=self._operator.sender_name,
            address=self._operator.postal_address,
            domain=domain,
        )
        draft["model"] = self._model
        if playbook is not None:
            draft["segment"] = playbook.segment
            draft["anchor"] = playbook.anchor
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
                        body=f"{draft.get('greeting', '')}\n\n{draft['body']}\n\n"
                        f"{draft['footer']}".lstrip(),
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
            greeting=str(draft.get("greeting") or "") or None,
            findings=list(draft.get("findingsUsed") or []),
            reading_url=f"{origin}/r/{token}"
            + (f"#{draft['anchor']}" if draft.get("anchor") else ""),
            unsubscribe_url=f"{origin}/r/{token}/unsubscribe",
            segment=str(draft.get("segment") or "") or None,
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
            "findings": _reading_findings(detail),
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
            "campaigns": self.campaign_view(),
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


def _reading_findings(detail: Mapping[str, Any]) -> list[dict[str, object]]:
    """What the reading shows: the letter's findings in its language first, then the rest."""
    draft = detail.get("draft") if isinstance(detail.get("draft"), Mapping) else {}
    used = [dict(f) for f in (draft or {}).get("findingsUsed") or [] if isinstance(f, Mapping)]
    shown = {(f.get("kind"), f.get("code")) for f in used}
    rest = [
        dict(f) for f in detail.get("findings") or []
        if isinstance(f, Mapping) and (f.get("kind"), f.get("code")) not in shown
    ]  # fmt: skip
    return [{**f, "statement": f.get("text") or f.get("statement")} for f in [*used, *rest]]


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
        "campaign": prospect.get("campaign_id"),
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
        actor = str(grant.principal_id)
        action = payload.get("action")
        if action == "CREATE_CAMPAIGN":
            if set(payload) != {"action", "name", "personas", "countries", "target", "endsOn"}:
                raise ValueError("invalid campaign fields")
            personas, countries = payload["personas"], payload["countries"]
            name, target, ends_on = payload["name"], payload["target"], payload["endsOn"]
            if (
                not isinstance(name, str)
                or not isinstance(personas, list)
                or not isinstance(countries, list)
                or not all(isinstance(x, str) for x in [*personas, *countries])
                or type(target) is not int
                or not (ends_on is None or isinstance(ends_on, str))
            ):
                raise ValueError("invalid campaign values")
            runner.create_campaign(
                name=name, personas=[str(x) for x in personas],
                countries=[str(x) for x in countries], target=target, ends_on=ends_on,
                actor=actor,
            )  # fmt: skip
        elif action == "CANCEL_CAMPAIGN":
            if set(payload) != {"action", "campaign"} or not isinstance(payload["campaign"], str):
                raise ValueError("invalid campaign fields")
            if not runner.cancel_campaign(payload["campaign"], actor=actor):
                raise LookupError("campaign is not active")
        else:
            if set(payload) != {"domain", "action"}:
                raise ValueError("invalid marketing pool fields")
            domain = payload["domain"]
            if not isinstance(domain, str) or action not in {"APPROVE", "DISCARD", "SUPPRESS"}:
                raise ValueError("invalid marketing pool values")
            if not runner.decide(domain.strip().lower(), str(action), actor=actor):
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
            studies_per_day=int(values.get("AXIGNAL_MARKETING_POOL_STUDIES_PER_DAY", "40")),
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
    parser.add_argument(
        "command", choices=("status", "show", "drafts", "campaign-create", "campaign-cancel")
    )
    parser.add_argument("domain", nargs="?", help="domain (show) or campaign id (cancel)")
    parser.add_argument("--data-dir", required=True, type=Path)
    parser.add_argument("--name")
    parser.add_argument("--personas", help="comma-separated persona ids")
    parser.add_argument("--countries", help="comma-separated ISO codes")
    parser.add_argument("--target", type=int)
    parser.add_argument("--ends-on", help="YYYY-MM-DD, inclusive")
    parser.add_argument("--actor", help="who asks, e.g. codex:rafael or claude:rafael")
    args = parser.parse_args(argv)
    path = args.data_dir / "marketing-pool.sqlite3"
    if not path.is_file():
        raise SystemExit("no marketing pool at that data directory")
    store = SqliteMarketingPool(path)
    if args.command in {"campaign-create", "campaign-cancel"}:
        if not args.actor or ":" not in args.actor:
            raise SystemExit("--actor agent:person is required (it is audited)")
        runner = MarketingPoolRunner(
            store, (), study=lambda *_: "NOT_READY", study_result=lambda _r: (None, {}),
            complete=None, model=None, operator=Operator("AXIGNAL", "-", "https://axignal.com"),
        )  # fmt: skip
        if args.command == "campaign-cancel":
            ok = runner.cancel_campaign(str(args.domain or ""), actor=args.actor)
            print(json.dumps({"cancelled": ok}))
            return
        campaign_id = runner.create_campaign(
            name=args.name or "", personas=(args.personas or "").split(","),
            countries=(args.countries or "").split(","), target=args.target or 0,
            ends_on=args.ends_on, actor=args.actor,
        )  # fmt: skip
        print(json.dumps({"campaign": campaign_id}))
        return
    if args.command == "status":
        out: object = {
            "counts": store.counts(),
            "campaigns": [
                {k: c[k] for k in ("id", "name", "state", "target", "personas", "countries")}
                | {"counts": store.campaign_counts(c["id"])}
                for c in store.campaigns()
            ],
            "discovery": store.discovery_log(limit=10),
        }
    elif args.command == "show":
        found = store.get(str(args.domain or "").lower())
        out = None if found is None else _wire(found)
    else:
        out = [_wire(p) for p in store.recent(("DRAFTED", "HELD", "APPROVED"), limit=50)]
    print(json.dumps(out, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
