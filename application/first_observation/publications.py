"""What an organization publishes on its own channel, and how often (Activity, spec 096).

Its website declares its news feed (``<link rel="alternate" type="application/rss+xml">``);
reading that feed says what it has been doing (news, launches, articles) and at what pace,
from minute 0 and for any organization that keeps a blog or a newsroom. Only titles, links
and dates are kept: never the articles' text. A feed with nothing in a year is itself a
signal (a quiet channel), never an absence of activity.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from urllib.parse import urljoin, urlsplit

MAX_ITEMS = 20
SHOWN = 5
_ATOM = "{http://www.w3.org/2005/Atom}"
FEED_TYPES = ("application/rss+xml", "application/atom+xml")


def _when(text: str | None) -> datetime | None:
    if not text or not text.strip():
        return None
    raw = text.strip()
    try:
        moment = parsedate_to_datetime(raw)  # RSS: RFC 822
    except (TypeError, ValueError, IndexError):
        try:
            moment = datetime.fromisoformat(raw.replace("Z", "+00:00"))  # Atom: RFC 3339
        except ValueError:
            return None
    return moment if moment.tzinfo else moment.replace(tzinfo=UTC)


def parse_feed(raw: bytes, base_url: str) -> list[dict[str, str]]:
    """Its items, newest first: title, link and publication date (ISO). [] when unreadable."""
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        return []
    found: list[tuple[datetime, dict[str, str]]] = []
    for item in root.iter("item"):  # RSS 2.0
        title, link = (item.findtext("title") or "").strip(), (item.findtext("link") or "").strip()
        when = _when(
            item.findtext("pubDate") or item.findtext("{http://purl.org/dc/elements/1.1/}date")
        )
        if title and when:
            found.append((when, {"title": title[:200], "url": urljoin(base_url, link)[:500]}))
    for entry in root.iter(f"{_ATOM}entry"):  # Atom
        title = (entry.findtext(f"{_ATOM}title") or "").strip()
        node = entry.find(f"{_ATOM}link")
        link = node.get("href", "") if node is not None else ""
        when = _when(entry.findtext(f"{_ATOM}published") or entry.findtext(f"{_ATOM}updated"))
        if title and when:
            found.append((when, {"title": title[:200], "url": urljoin(base_url, link)[:500]}))
    found.sort(key=lambda pair: pair[0], reverse=True)
    return [{**item, "publishedAt": when.isoformat()} for when, item in found[:MAX_ITEMS]]


def own_feed(feeds: Sequence[str], home_url: str) -> str | None:
    """The first feed it declares on its own site (a feed on another host is not its own)."""
    host = (urlsplit(home_url).hostname or "").removeprefix("www.")
    for feed in feeds:
        url = urljoin(home_url, feed)
        other = (urlsplit(url).hostname or "").removeprefix("www.")
        same = bool(host) and (
            other == host or other.endswith("." + host) or host.endswith("." + other)
        )
        # A comments feed says nothing of its activity.
        if same and "comments" not in url.lower():
            return url
    return None


def conventional_feed(platform: object, home_url: str, links: Sequence[str]) -> str | None:
    """The feed its platform publishes by convention when its homepage declares none: a
    Shopify blog's ``.atom`` (the blog its homepage links, else ``news``), WordPress ``/feed/``.
    One guess only; a 404 is simply no feed."""
    host = (urlsplit(home_url).hostname or "").removeprefix("www.")
    if platform == "SHOPIFY":
        for link in links:
            parts = urlsplit(urljoin(home_url, link))
            if (parts.hostname or "").removeprefix("www.") != host:
                continue
            segments = [s for s in parts.path.split("/") if s]
            if len(segments) >= 2 and segments[-2] == "blogs" and segments[-1].isascii():
                return urljoin(home_url, "/" + "/".join(segments) + ".atom")
        return urljoin(home_url, "/blogs/news.atom")
    if platform == "WORDPRESS":
        return urljoin(home_url, "/feed/")
    return None


def cadence(items: Sequence[Mapping[str, str]], now: datetime) -> dict[str, object]:
    """How many it published in the last 30, 90 and 365 days, and when it last did."""
    dates = [d for i in items if (d := _when(i.get("publishedAt")))]
    return {
        "last30Days": sum(1 for d in dates if now - d <= timedelta(days=30)),
        "last90Days": sum(1 for d in dates if now - d <= timedelta(days=90)),
        "last365Days": sum(1 for d in dates if now - d <= timedelta(days=365)),
        "lastPublishedAt": max(dates).isoformat() if dates else None,
        "itemsRead": len(items),
        "capped": len(items) >= MAX_ITEMS,
    }
