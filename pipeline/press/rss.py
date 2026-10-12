"""Bounded reading of publisher RSS/Atom feeds into press items (headline, link, date)."""

from __future__ import annotations

import urllib.request
import xml.etree.ElementTree as ET
from collections.abc import Sequence
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit

from application.press.contracts import PressFeed, PressItem

MAX_FEED_BYTES = 5_000_000
USER_AGENT = "AXIGNAL-SourceObserver/0.2 (+https://axignal.com)"


class UrllibFeedTransport:
    """HTTPS GET to a registered feed URL only; bounded in time and size; no evasion."""

    def __init__(self, feeds: Sequence[PressFeed], *, timeout_s: float = 20.0) -> None:
        self._allowed = {feed.url for feed in feeds}
        self._timeout_s = timeout_s

    def get(self, url: str) -> tuple[int, bytes]:
        if url not in self._allowed or urlsplit(url).scheme != "https":
            raise ValueError("press transport only reads registered https feeds")
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=self._timeout_s) as response:
            body = response.read(MAX_FEED_BYTES + 1)
            if len(body) > MAX_FEED_BYTES:
                raise ValueError("feed too large")
            return int(response.status), body


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _date(value: str | None) -> datetime | None:
    if not value:
        return None
    value = value.strip()
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


def parse_feed(feed: PressFeed, body: bytes) -> tuple[PressItem, ...]:
    """RSS 2.0 items or Atom entries with a title, an http(s) link and a date."""
    root = ET.fromstring(body)
    out: list[PressItem] = []
    for node in root.iter():
        if _local(node.tag) not in {"item", "entry"}:
            continue
        title = link = published = None
        for child in node:
            name = _local(child.tag)
            if name == "title" and child.text:
                title = " ".join(child.text.split())[:400]
            elif name == "link":
                link = (child.get("href") or child.text or "").strip() or link
            elif (
                name in {"pubDate", "published", "updated", "date"} and child.text and not published
            ):
                published = child.text
        when = _date(published)
        if not title or not link or when is None or urlsplit(link).scheme not in {"https", "http"}:
            continue
        out.append(
            PressItem(feed.feed_id, feed.outlet, title, link, when, feed.language, feed.country)
        )
    return tuple(out)
