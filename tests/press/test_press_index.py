"""World press index: syndicated headlines, matched to organizations as mentions."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from application.press.contracts import FEEDS, PressFeed
from application.press.mentions import normalized_name, press_discoveries, search_terms
from pipeline.press.rss import UrllibFeedTransport, parse_feed
from pipeline.press.sqlite_store import PressIngestor, SqlitePressIndex

NOW = datetime(2026, 10, 13, 9, tzinfo=UTC)
ES = PressFeed("t-es", "Diario Ejemplo", "https://diario.example/rss", "EU/ES", "es", ("business",))
DE = PressFeed(
    "t-de", "Zeitung Beispiel", "https://zeitung.example/atom", "EU/DE", "de", ("business",)
)

RSS = b"""<?xml version="1.0"?><rss version="2.0"><channel>
<item><title>Prosegur cierra una alianza con Allianz</title><link>https://diario.example/a</link>
<pubDate>Wed, 07 Oct 2026 10:00:00 +0200</pubDate></item>
<item><title>Sin fecha</title><link>https://diario.example/b</link></item>
<item><title>Enlace raro</title><link>javascript:alert(1)</link><pubDate>Wed, 07 Oct 2026 10:00:00 +0200</pubDate></item>
</channel></rss>"""
ATOM = b"""<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Siemens AG baut Werk aus</title>
<link href="https://zeitung.example/x"/><published>2026-10-08T08:00:00Z</published></entry></feed>"""


def test_rss_and_atom_keep_headline_link_and_date_only() -> None:
    (item,) = parse_feed(ES, RSS)
    assert (item.title, item.url, item.outlet) == (
        "Prosegur cierra una alianza con Allianz", "https://diario.example/a", "Diario Ejemplo"
    )  # fmt: skip
    (german,) = parse_feed(DE, ATOM)
    assert german.country == "EU/DE" and german.published_at.year == 2026


def test_names_normalize_across_countries() -> None:
    assert normalized_name("Siemens AG") == "siemens"
    assert normalized_name("Robert Bosch GmbH") == "robert bosch"
    assert normalized_name("Holaluz.com") == "holaluz"
    assert search_terms(["Eulen"]) == []  # too short a single word to attribute alone


class Feeds:
    def __init__(self, answers: dict[str, tuple[int, bytes] | Exception]) -> None:
        self.answers = answers
        self.calls: list[str] = []

    def get(self, url: str) -> tuple[int, bytes]:
        self.calls.append(url)
        answer = self.answers[url]
        if isinstance(answer, Exception):
            raise answer
        return answer


def test_ingestion_reads_each_feed_once_per_period_and_records_refusals(tmp_path: Path) -> None:
    store = SqlitePressIndex(tmp_path / "press.sqlite3")
    refused = PressFeed("t-403", "Bloqueado", "https://bloqueado.example/rss", "EU/ES", "es", ())
    transport = Feeds({ES.url: (200, RSS), DE.url: (200, ATOM), refused.url: (403, b"")})
    clock = [NOW]
    ingestor = PressIngestor((ES, DE, refused), store, transport, clock=lambda: clock[0])
    assert ingestor.run() == 3
    assert ingestor.run() == 0  # nothing due again within the period
    clock[0] = NOW + timedelta(hours=7)
    ingestor.run()
    assert transport.calls.count(refused.url) == 2  # recorded and retried later, never bypassed
    since, held, feeds_ok = store.coverage()
    assert held == 2 and feeds_ok == 2 and since is not None


def test_mentions_are_potential_attributions_with_coverage(tmp_path: Path) -> None:
    store = SqlitePressIndex(tmp_path / "press.sqlite3")
    store.upsert([*parse_feed(ES, RSS), *parse_feed(DE, ATOM)])
    store.mark_read("t-es", at=NOW, status="OK", items=1)
    view = {"target": {"name": "Prosegur"}, "observedAt": NOW.isoformat(), "discoveries": []}
    (mention,) = press_discoveries(view, store, now=NOW, own_domain="prosegur.es")
    assert mention["kind"] == "MENTION" and mention["code"] == "PRESS_MENTION"
    assert mention["epistemicState"] == "POTENTIAL" and mention["detail"]["notEndorsement"] is True  # type: ignore[index]
    german = press_discoveries(
        {"target": {"name": "Siemens AG"}, "discoveries": []}, store, now=NOW, own_domain=None
    )
    assert [d["statement"] for d in german] == ["Siemens AG baut Werk aus"]
    nothing = press_discoveries(
        {"target": {"name": "Empresa Inexistente SL"}, "discoveries": []}, store, now=NOW,
        own_domain=None,
    )  # fmt: skip
    assert [d["code"] for d in nothing] == ["NO_PRESS_MENTION_FOUND"]


def test_the_transport_only_reads_registered_https_feeds() -> None:
    import pytest

    transport = UrllibFeedTransport(FEEDS)
    for url in ("https://evil.example/rss", FEEDS[0].url.replace("https://", "http://")):
        with pytest.raises(ValueError):
            transport.get(url)
    assert {f.country for f in FEEDS} >= {"EU/ES", "EU/DE", "EU/FR", "EU/IT", "EU/PT"}
