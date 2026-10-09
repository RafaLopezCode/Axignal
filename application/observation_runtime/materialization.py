"""Derived operational snapshots; subscriber/canonical stores remain authority."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from html.parser import HTMLParser
from typing import Protocol

from application.economic_discovery.observation_memory import GovernedObservation
from application.first_observation.derived import derived_capabilities, derived_scopes
from application.observation_intelligence import (
    EvidenceCoverageMap,
    MarketRole,
    MarketScope,
    ObservationBudget,
    OperationalLearning,
    SourceRegistry,
    XeedObservationContext,
    build_strategy,
    derive_families,
    detect_capabilities,
)
from application.observation_intelligence.catalog import eu_nuts
from application.subscriber_portfolio.models import EntitlementSnapshot, FocusStatus, PortfolioEntry
from application.xeed_access.reader import TrustedRequestContext
from domain.evidence.epistemics import Currentness
from domain.identity import PrincipalId, XeedId
from domain.xignal import XignalEpistemicState


class Readiness(StrEnum):
    NO_ELIGIBLE_FOCUS = "NO_ELIGIBLE_FOCUS"
    ATTENTION_NOT_READY = "ATTENTION_NOT_READY"
    READY_FOR_MANUAL_TICK = "READY_FOR_MANUAL_TICK"
    INVALID_MATERIALIZATION = "INVALID_MATERIALIZATION"


class Authority(Protocol):
    def contexts(self) -> tuple[TrustedRequestContext, ...]: ...
    def entitlement(self, context: TrustedRequestContext) -> EntitlementSnapshot: ...
    def pilot_principal(self, context: TrustedRequestContext) -> PrincipalId | None: ...
    def focuses(self, context: TrustedRequestContext) -> tuple[PortfolioEntry, ...]: ...
    def seed(
        self, context: TrustedRequestContext, focus: XeedId, now: datetime
    ) -> tuple[str, tuple[tuple[GovernedObservation, Currentness], ...]] | None: ...


@dataclass(frozen=True)
class EnrolledFocus:
    context: TrustedRequestContext
    focus_id: XeedId
    organization_id: str
    markets: tuple[MarketScope, ...]


@dataclass(frozen=True)
class DesiredObservation:
    state: Readiness
    entries: tuple[EnrolledFocus, ...]
    reasons: tuple[tuple[str, int], ...]
    eligible_focuses: int

    def summary(self) -> dict[str, object]:
        ready = sum(bool(e.markets) for e in self.entries)
        return {
            "state": self.state.value,
            "eligible_focuses": self.eligible_focuses,
            "enrolled_focuses": len(self.entries),
            "attention_ready": ready,
            "attention_not_ready": len(self.entries) - ready,
            "reasons": dict(self.reasons),
            "model_calls": 0,
            "provider_calls": 0,
        }


class _PublicServiceParser(HTMLParser):
    """Only explicit public Service declarations; addresses/HQ never infer a market."""

    def __init__(self) -> None:
        super().__init__()
        self.active = False
        self.chunks: list[str] = []
        self.documents: list[object] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "script" and dict(attrs).get("type") == "application/ld+json":
            self.active = True
            self.chunks = []

    def handle_data(self, data: str) -> None:
        if self.active:
            self.chunks.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self.active:
            self.active = False
            if len(self.documents) < 32:
                with suppress(json.JSONDecodeError):
                    self.documents.append(json.loads("".join(self.chunks)))


def explicit_public_scopes(observation: GovernedObservation) -> tuple[MarketScope, ...]:
    text = observation.raw_content or ""
    if len(text.encode("utf-8")) > 65536 or observation.record.source_type != "PUBLIC_WEBSITE":
        return ()
    parser = _PublicServiceParser()
    parser.feed(text)
    nodes: list[object] = []
    for document in parser.documents:
        if isinstance(document, dict):
            graph = document.get("@graph")
            nodes.extend(graph if isinstance(graph, list) else [document])
        elif isinstance(document, list):
            nodes.extend(document)
    scopes: set[tuple[str, MarketRole]] = set()
    roles = {
        "government": MarketRole.PUBLIC_BUYERS,
        "business": MarketRole.PRIVATE_BUSINESSES,
        "consumer": MarketRole.CONSUMERS,
    }
    for node in nodes[:100]:
        if not isinstance(node, dict) or node.get("@type") != "Service":
            continue
        # Scope must describe the same observed service capability, not an unrelated address.
        name = node.get("name")
        if not isinstance(name, str) or not detect_capabilities(
            text=name,
            observation_id=observation.record.observation_id,
            source_ref=observation.record.source_ref,
            observed_at=observation.record.observed_at,
        ):
            continue
        audience = node.get("audience")
        if not isinstance(audience, dict):
            continue
        role = roles.get(str(audience.get("audienceType", "")).casefold())
        if role is None:
            continue
        areas = node.get("areaServed")
        for area in areas if isinstance(areas, list) else [areas]:
            if not isinstance(area, dict) or area.get("@type") not in {
                "Country",
                "AdministrativeArea",
            }:
                continue
            identifier = area.get("identifier")
            if not isinstance(identifier, dict) or identifier.get("propertyID") != "NUTS":
                continue
            value = identifier.get("value")
            if isinstance(value, str) and re.fullmatch(r"[A-Z]{2}[0-9A-Z]{0,3}", value):
                scopes.add((eu_nuts(value).code, role))
    return tuple(
        MarketScope(
            eu_nuts(code.replace("EU/", "").split("/")[-1]),
            frozenset({role}),
            XignalEpistemicState.POTENTIAL,
        )
        for code, role in sorted(scopes, key=lambda pair: (pair[0], pair[1].value))
    )


def derive_observation(
    authority: Authority,
    *,
    now: datetime,
    source_ids: frozenset[str] = frozenset({"ted-search-v3"}),
) -> DesiredObservation:
    grouped: dict[str, list[TrustedRequestContext]] = defaultdict(list)
    for context in authority.contexts():
        grouped[str(context.tenant_id)].append(context)
    entries: list[EnrolledFocus] = []
    reasons: Counter[str] = Counter()
    eligible = 0
    for tenant in sorted(grouped):
        contexts = grouped[tenant]
        pilot = authority.pilot_principal(contexts[0])
        selected = [c for c in contexts if c.principal_id == pilot] if pilot else contexts
        if len(selected) != 1:
            reasons["PRINCIPAL_AUTHORITY_AMBIGUOUS_OR_REVOKED"] += 1
            continue
        context = selected[0]
        entitlement = authority.entitlement(context)
        if entitlement.currentness is not Currentness.CURRENT or not entitlement.capacity:
            reasons["ENTITLEMENT_NOT_CURRENT"] += 1
            continue
        active = sorted(
            (f for f in authority.focuses(context) if f.status is FocusStatus.ACTIVE),
            key=lambda f: (f.created_at, f.focus_id),
        )[: entitlement.capacity]
        for focus in active:
            seed = authority.seed(context, focus.focus_id, now)
            if seed is None:
                reasons["NO_CANONICAL_ORGANIZATION"] += 1
                continue
            eligible += 1
            if eligible > 100:
                raise ValueError("observation Focus bound exceeded")
            organization_id, history = seed
            usable = sorted(
                (
                    o
                    for o, currentness in history
                    if currentness is Currentness.CURRENT
                    and o.raw_content
                    and o.record.source_type == "PUBLIC_WEBSITE"
                ),
                key=lambda o: (o.record.observed_at, o.record.observation_id),
                reverse=True,
            )
            markets: tuple[MarketScope, ...] = ()
            if not usable:
                reasons["NO_CURRENT_PUBLIC_SEED"] += 1
            else:
                # Keep the plan reader's existing latest-evidence cut, never mix stale scopes.
                source = usable[0]
                capabilities = detect_capabilities(
                    text=source.raw_content or "",
                    observation_id=source.record.observation_id,
                    source_ref=source.record.source_ref,
                    observed_at=source.record.observed_at,
                )
                candidate_scopes = explicit_public_scopes(source)
                # Spec 063: a Focus's First Observation supplies open capabilities and
                # POTENTIAL attention scopes when the narrow explicit bootstrap has none.
                reader = getattr(authority, "first_observation", None)
                derived = None if reader is None else reader(context, focus.focus_id)
                capabilities = capabilities or derived_capabilities(derived, organization_id)
                candidate_scopes = candidate_scopes or derived_scopes(derived, organization_id)
                if not capabilities:
                    reasons["CAPABILITY_UNKNOWN"] += 1
                elif not candidate_scopes:
                    reasons["MARKET_SCOPE_UNKNOWN"] += 1
                else:
                    observation_context = XeedObservationContext(
                        str(focus.focus_id),
                        now,
                        capabilities,
                        derive_families(capabilities),
                        candidate_scopes,
                    )
                    strategy = build_strategy(
                        observation_context,
                        coverage=EvidenceCoverageMap(max_age=timedelta(days=30)),
                        budget=ObservationBudget(
                            max_requests=8, max_amount_microunits=0, max_actions=8, max_depth=2
                        ),
                        registry=SourceRegistry(),
                        learning=OperationalLearning(),
                    )
                    allowed = {
                        a.query.geographies[0].code
                        for a in strategy.actions
                        if a.source_id in source_ids and a.query.geographies
                    }
                    markets = tuple(m for m in candidate_scopes if m.geography.code in allowed)
                    if not markets:
                        reasons["NO_ROUTABLE_SOURCE_OR_UNKNOWN_COST"] += 1
            entries.append(EnrolledFocus(context, focus.focus_id, organization_id, markets))
    state = (
        Readiness.NO_ELIGIBLE_FOCUS
        if not entries
        else Readiness.ATTENTION_NOT_READY
        if any(not e.markets for e in entries)
        else Readiness.READY_FOR_MANUAL_TICK
    )
    return DesiredObservation(state, tuple(entries), tuple(sorted(reasons.items())), eligible)
