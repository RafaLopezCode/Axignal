"""Retention and revocation of conditioned understanding (ADR-0015, ADR-0091 §11).

Retention never exceeds what the governed entry authorizes; lost rights withdraw stored
quotations at the next read (subscriber and AXENT) and purge them from storage, while a
provider-only revocation stops new transmission without withdrawing an admitted report.
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from application.economic_discovery.observation_memory import ObservationRightsStatus
from application.first_observation.rights import (
    PRIVATE_CITATION_DAYS,
    ContentRights,
    RegisteredContentRights,
)
from application.first_observation.understanding import public_report, rights_deadline
from domain.identity import XeedId
from tests.first_observation.harness import EXAMPLE_HOSTS, KNOWN, runtime
from tests.first_observation.test_first_observation_e2e import _attend, _view
from tests.first_observation.test_public_understanding import (
    BASE,
    NOW,
    _citation_for,
    _measure,
    _page,
    _site,
)
from tests.first_observation.test_understanding_e2e import controlled_facade
from tools.runtime.first_observation import ReloadingContentRights, website_rights_entry

LINKED = "https://services.manolo.example.com/services"
QUOTE = "We install photovoltaic"


def _rights(days: int, host: str = "manolo.example.com") -> ContentRights:
    entry = website_rights_entry(
        host=host,
        basis="synthetic retention fixture",
        raw_retention_days=days,
        metadata_retention_days=max(days, 1),
    )
    policy = RegisteredContentRights(
        (entry,),
        provider_input=frozenset({entry.source_id}),
        public_offer_input=frozenset({entry.source_id}),
    )
    return policy.rights_for(f"https://{host}/", now=NOW)


@pytest.mark.parametrize("days", [0, 7, 30, 90])
def test_private_citations_never_outlive_the_governed_entry(days: int) -> None:
    assert _rights(days).private_until(NOW) == NOW + timedelta(days=days)


def test_no_entry_keeps_the_bounded_default_and_a_prohibition_keeps_nothing() -> None:
    assert ContentRights(decided_at=NOW).private_until(NOW) == NOW + timedelta(
        days=PRIVATE_CITATION_DAYS
    )
    granted = _rights(90)
    assert granted.entry is not None
    prohibited = ContentRights(
        entry=granted.entry.__class__(
            **{
                **{f: getattr(granted.entry, f) for f in granted.entry.__dataclass_fields__},
                "rights_status": ObservationRightsStatus.PROHIBITED,
            }
        ),
        decided_at=NOW,
    )
    assert prohibited.private_until(NOW) == NOW


@pytest.mark.parametrize(("home", "linked"), [(90, 0), (90, 7), (7, 90), (30, 30), (90, 90)])
def test_a_multi_page_report_is_bounded_by_its_most_restrictive_page(
    home: int, linked: int
) -> None:
    entries = tuple(
        website_rights_entry(
            host=host, basis="synthetic", raw_retention_days=d, metadata_retention_days=max(d, 1)
        )
        for host, d in (("manolo.example.com", home), ("services.manolo.example.com", linked))
    )
    ids = frozenset(e.source_id for e in entries)
    policy = RegisteredContentRights(entries, provider_input=ids, public_offer_input=ids)
    report, _ = _measure(
        _site(
            _page(BASE, "<html><body><p>We repair shoes for households.</p></body></html>"),
            _page(LINKED, "<html><body><p>We restore leather boots.</p></body></html>"),
        ),
        {
            "pu_offer": lambda batch: _citation_for(batch, "repair shoes"),
            "pu_audience": lambda batch: _citation_for(batch, "households"),
            "pu_outcome": "NOT_STATED",
        },
        rights=policy.rights_for(BASE, now=NOW),
        rights_for=lambda url: policy.rights_for(url, now=NOW),
    )
    assert report["status"] == "MEASURED"
    expiry = datetime.fromisoformat(report["contentExpiresAt"])
    assert expiry == NOW + timedelta(days=min(home, linked))
    # Read inside the window shows quotations; at the earliest deadline nothing remains.
    if min(home, linked) > 0:
        assert public_report(report, now=expiry - timedelta(seconds=1))["citations"]
    gone = public_report(report, now=expiry)
    assert gone["citations"] == [] and gone["dimensions"] == []


def _stored_report(days: int = 90) -> tuple[dict[str, Any], RegisteredContentRights]:
    entry = website_rights_entry(
        host="manolo.example.com",
        basis="synthetic",
        raw_retention_days=days,
        metadata_retention_days=max(days, 1),
    )
    policy = RegisteredContentRights(
        (entry,),
        provider_input=frozenset({entry.source_id}),
        public_offer_input=frozenset({entry.source_id}),
    )
    report, _ = _measure(
        _site(_page(BASE, "<html><body><p>We repair shoes for households.</p></body></html>")),
        {
            "pu_offer": lambda batch: _citation_for(batch, "repair shoes"),
            "pu_audience": lambda batch: _citation_for(batch, "households"),
            "pu_outcome": "NOT_STATED",
        },
        rights=policy.rights_for(BASE, now=NOW),
        rights_for=lambda url: policy.rights_for(url, now=NOW),
    )
    assert report["status"] == "MEASURED"
    return report, policy


def test_read_time_rights_shorten_but_never_extend_the_stored_deadline() -> None:
    report, granted = _stored_report(90)
    later = NOW + timedelta(days=8)
    # Unchanged rights: still shown (stale, not withdrawn).
    kept = public_report(report, now=later, rights_for=lambda u: granted.rights_for(u, now=later))
    assert kept["status"] == "MEASURED" and kept["citations"]
    # Entry shortened to 7 days: withdrawn on day 8 although 90 were stored.
    shortened = public_report(report, now=later, rights_for=lambda u: _rights(7))
    assert shortened["cause"] == "CONTENT_RIGHTS_WITHDRAWN" and shortened["citations"] == []
    # Entry removed: the governed basis is gone, withdrawn at once.
    removed = public_report(report, now=NOW, rights_for=lambda u: ContentRights(decided_at=NOW))
    assert removed["cause"] == "CONTENT_RIGHTS_WITHDRAWN" and removed["dimensions"] == []
    # A wider entry later cannot extend what was stored.
    widened = rights_deadline(report, lambda u: _rights(365))
    assert widened is not None
    assert (
        public_report(report, now=NOW + timedelta(days=91), rights_for=lambda u: _rights(365))[
            "cause"
        ]
        == "CONTENT_EXPIRED"
    )


def test_provider_only_revocation_keeps_an_admitted_report() -> None:
    report, _ = _stored_report(90)
    entry = _rights(90).entry
    assert entry is not None
    transmission_revoked = RegisteredContentRights((entry,))  # no provider grants at all
    shown = public_report(
        report, now=NOW, rights_for=lambda u: transmission_revoked.rights_for(u, now=NOW)
    )
    assert shown["status"] == "MEASURED" and shown["citations"]


# ---- the real read path: subscriber HTTP, AXENT and purge, without restart -----------


class _RightsFile:
    """The operator's live rights file (the production ``ReloadingContentRights`` path)."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._tick = 0

    def write(self, *, hosts: tuple[str, ...], days: int = 90, provider: bool = True) -> None:
        rows = [
            {
                "host": host,
                "rightsBasis": "synthetic: fictitious RFC 2606 site",
                "rawRetentionDays": days,
                "metadataRetentionDays": max(days, 365),
                "providerInput": provider,
                "publicOfferInput": provider,
            }
            for host in hosts
        ]
        self.path.write_text(json.dumps(rows), encoding="utf-8")
        self._tick += 1  # coarse filesystem clocks must still see a new version
        stamp = 1_800_000_000_000_000_000 + self._tick * 1_000_000_000
        os.utime(self.path, ns=(stamp, stamp))


def _measured(tmp_path: Path, monkeypatch: Any) -> tuple[Any, _RightsFile, str, str]:
    rights = _RightsFile(tmp_path / "content-rights.json")
    rights.write(hosts=EXAMPLE_HOSTS)
    facade, _world = controlled_facade(
        tmp_path, monkeypatch, rights=ReloadingContentRights(rights.path)
    )
    token, added = _attend(facade, tmp_path, "synthetic:revocation", KNOWN)
    focus = str(added["focusId"])
    assert runtime(facade).drain() == 1
    report = _view(facade, token, focus)["publicUnderstanding"]
    assert report["status"] == "MEASURED" and QUOTE in json.dumps(report)
    return facade, rights, token, focus


def _axent_understanding(facade: Any, token: str, focus: str) -> dict[str, Any]:
    context = facade.identity.authenticate(token)
    read = facade.axent.service.reader.read(context, XeedId(focus), datetime.now(UTC))
    return dict(read.projection["publicUnderstanding"])


def test_live_revocation_withdraws_quotes_in_subscriber_axent_and_storage(
    tmp_path: Path, monkeypatch: Any
) -> None:
    facade, rights, token, focus = _measured(tmp_path, monkeypatch)
    assert QUOTE in json.dumps(_axent_understanding(facade, token, focus))

    # Operator removes the site's entry; no restart, no purge yet.
    rights.write(hosts=tuple(h for h in EXAMPLE_HOSTS if h != "solartec.example.com"))
    shown = _view(facade, token, focus)["publicUnderstanding"]
    assert shown["cause"] == "CONTENT_RIGHTS_WITHDRAWN" and shown["currentness"] == "EXPIRED"
    assert shown["citations"] == [] and shown["dimensions"] == []
    assert QUOTE not in json.dumps(shown)
    axent = _axent_understanding(facade, token, focus)
    assert axent["cause"] == "CONTENT_RIGHTS_WITHDRAWN" and QUOTE not in json.dumps(axent)
    reply = facade.handle(
        "POST",
        f"/subscriber/organizations/{focus}/axent",
        {**_headers(token)},
        {"question": "What does the public offer say?", "locale": "en"},
    )
    assert reply.status == 200
    # No quoted conditioned signal can ground an answer after the withdrawal.
    assert not any(str(r).startswith("public-understanding:") for r in reply.body["signalIds"])

    # Governed purge removes the stored bytes, not only the presentation.
    runtime(facade).purge()
    context = facade.identity.authenticate(token)
    internal = runtime(facade).store.proof(str(context.tenant_id), focus)["publicUnderstanding"]
    assert internal["cause"] == "CONTENT_RIGHTS_WITHDRAWN"
    assert "trace" not in internal and QUOTE not in json.dumps(internal)
    with sqlite3.connect(runtime(facade).store._path) as db:
        rows = db.execute("SELECT report FROM fo_understanding_history").fetchall()
    assert not any(QUOTE in row[0] for row in rows)


def test_live_provider_only_revocation_keeps_the_report_everywhere(
    tmp_path: Path, monkeypatch: Any
) -> None:
    facade, rights, token, focus = _measured(tmp_path, monkeypatch)
    rights.write(hosts=EXAMPLE_HOSTS, provider=False)
    shown = _view(facade, token, focus)["publicUnderstanding"]
    assert shown["status"] == "MEASURED" and QUOTE in json.dumps(shown)
    assert _axent_understanding(facade, token, focus)["status"] == "MEASURED"
    runtime(facade).purge()
    assert _view(facade, token, focus)["publicUnderstanding"]["status"] == "MEASURED"


def test_live_retention_cut_to_zero_withdraws_at_the_next_read(
    tmp_path: Path, monkeypatch: Any
) -> None:
    facade, rights, token, focus = _measured(tmp_path, monkeypatch)
    rights.write(hosts=EXAMPLE_HOSTS, days=0)
    shown = _view(facade, token, focus)["publicUnderstanding"]
    assert shown["cause"] == "CONTENT_RIGHTS_WITHDRAWN" and shown["citations"] == []
    assert _axent_understanding(facade, token, focus)["citations"] == []


def _headers(token: str) -> dict[str, str]:
    from tests.integration.test_organization_admission_e2e import _headers as headers

    return dict(headers(token))
