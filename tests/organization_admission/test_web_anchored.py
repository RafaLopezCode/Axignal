"""ADR-0087 amendment: a website no registry attests is observed, never admitted as identity."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from application.organization_admission.web_anchored import WebAnchoredResolution
from application.subscriber_portfolio.models import (
    OrganizationIdentityPending,
    OrganizationIdentityRejected,
)
from domain.evidence.epistemics import EpistemicState
from domain.faxt.model import FAXTCreationError
from domain.identity import is_web_subject
from domain.organizations.model import Organization
from pipeline.entity_resolution.web_subjects import (
    CanonicalOrWebSubjects,
    SqliteWebSubjectStore,
    web_subject_id,
)

NOW = datetime(2026, 10, 16, 12, tzinfo=UTC)


class Inner:
    def __init__(self, answer: object) -> None:
        self.answer = answer

    def resolve(self, locator: str) -> object:
        return self.answer


def test_only_a_missing_registry_answer_with_a_website_is_anchored(tmp_path: Path) -> None:
    store = SqliteWebSubjectStore(tmp_path / "web-subjects.sqlite3")
    for reason in ("IDENTITY_SOURCE_UNAVAILABLE", "NOT_FOUND_IN_IDENTITY_SOURCE"):
        found = WebAnchoredResolution(
            Inner(OrganizationIdentityPending(reason)), store, lambda: NOW
        )
        anchored = found.resolve("https://www.biocultor.example.com/tienda")  # type: ignore[arg-type]
        assert isinstance(anchored, Organization) and is_web_subject(anchored.id)
        assert anchored.canonical_name == "biocultor.example.com"  # the domain, never a legal name
    for kept in (OrganizationIdentityPending("AMBIGUOUS:X"), OrganizationIdentityPending("CONFLICT:Y"),
                 OrganizationIdentityRejected("INVALID_INPUT")):  # fmt: skip
        assert (
            WebAnchoredResolution(Inner(kept), store, lambda: NOW).resolve("https://a.example.com/")
            is kept
        )  # type: ignore[arg-type]
    bare = OrganizationIdentityPending("NOT_FOUND_IN_IDENTITY_SOURCE")
    assert WebAnchoredResolution(Inner(bare), store, lambda: NOW).resolve("Biocultor SL") is bare  # type: ignore[arg-type]


def test_one_domain_one_subject_and_a_registry_website_wins(tmp_path: Path) -> None:
    store = SqliteWebSubjectStore(tmp_path / "web-subjects.sqlite3")
    first = store.ensure("www.Shop.example.com", "https://www.shop.example.com/", NOW)
    again = store.ensure("shop.example.com", "shop.example.com", NOW)
    assert first.id == again.id == web_subject_id("shop.example.com")

    class Canonical:
        def get_organization(self, organization_id: str) -> None:
            return None

        def websites_for(self, organization_id: str) -> tuple[str, ...]:
            return ("verified.example.com",)

        def organization_by_domain(self, domain: str) -> str | None:
            return "org:id:verified" if domain == "verified.example.com" else None

    reader = CanonicalOrWebSubjects(Canonical(), store)
    assert reader.get_organization(first.id) == first
    assert reader.websites_for(first.id) == ("shop.example.com",)
    assert reader.organization_by_domain("shop.example.com") == first.id
    store.ensure("verified.example.com", "verified.example.com", NOW)
    assert reader.organization_by_domain("verified.example.com") == "org:id:verified"


def test_a_web_anchored_subject_can_never_hold_canonical_state() -> None:
    from domain.faxt.model import FAXT

    with pytest.raises(FAXTCreationError, match="web-anchored"):
        FAXT.create(  # type: ignore[call-arg]
            faxt_id="faxt:1", subject_id=str(web_subject_id("shop.example.com")),
            predicate="legal_name", object_or_value="Shop SL", evidence=None, decision=None,
            epistemic_state=EpistemicState.OBSERVED,
        )  # fmt: skip
