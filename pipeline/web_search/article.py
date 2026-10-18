"""Main text and publication date of a third-party page AXIGNAL has read (spec 099).

A page that names an organization only in its navigation, footer or a list of brands (a
privacy policy that lists its partners) says nothing about it. trafilatura keeps the
page's main content and htmldate its publication date, so a mention must be in the title
or the article itself, and a finding can say when the page was published. Both run on
the HTML AXIGNAL already fetched: no request is made here. Without the library (the
``web-reading`` dependency group) the caller keeps reading the whole page, as before.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

INSTRUMENT = "trafilatura"


@dataclass(frozen=True, slots=True)
class ArticleReading:
    text: str
    title: str
    published: str | None  # ISO date, as the page declares it
    instrument: str


def read_article(html: str, url: str) -> ArticleReading | None:
    """The page's main text and date, or None when unavailable or nothing was extracted."""
    try:
        import trafilatura
    except ImportError:  # the web-reading group is not installed
        return None
    try:
        raw = trafilatura.extract(
            html,
            url=url,
            output_format="json",
            with_metadata=True,
            include_comments=False,
            include_tables=False,
            favor_precision=True,
            deduplicate=True,
        )
    except Exception:  # malformed markup degrades to the whole-page reading, never raises
        return None
    if not raw:
        return None
    data = json.loads(raw)
    text = str(data.get("text") or "").strip()
    if not text:
        return None
    date = data.get("date")
    version = getattr(trafilatura, "__version__", "")
    return ArticleReading(
        text=text,
        title=str(data.get("title") or ""),
        published=str(date)[:10] if date else None,
        instrument=f"{INSTRUMENT}/{version}" if version else INSTRUMENT,
    )
