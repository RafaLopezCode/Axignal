"""Press mentions of an organization, from the world press index.

A headline that names the organization is an OBSERVED mention: the publisher published
it. Whether it is about *this* organization is attribution: a distinctive name (several
words, or a rare single word with its legal name declared) is POTENTIAL attribution with
its headline as basis; it is never presented as certain. A mention is not a citation and
a citation is not an endorsement (MASTER §54). The organization's own channels (items
published on its own domain) are its own voice, kept apart from third-party press.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta
from typing import Protocol
from urllib.parse import urlsplit

from application.press.contracts import PressItem

#: Legal forms across the EU countries the press index covers (ES, DE, FR, IT, PT).
_LEGAL_FORMS = re.compile(
    r"\b(s\.?\s?a\.?\s?u?|s\.?\s?l\.?\s?u?|s\.?\s?l\.?\s?l|s\.?\s?coop|lda|"
    r"sociedad (anonima|limitada)( unipersonal)?|ltd|limited|gmbh|ag|kg|se|sas|sarl|srl|spa|"
    r"s\.?\s?p\.?\s?a|bv|nv|inc)\b\.?"
)
#: A website address typed as a name ("holaluz.com") keeps only its name.
_DOMAIN_SUFFIX = re.compile(r"\.(com|es|de|fr|it|pt|net|org|eu|global|io|info)\s*$")


def normalized_name(name: str) -> str:
    """A comparable name: no accents, case, punctuation, domain or legal form (S.A., GmbH)."""
    folded = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().casefold()
    folded = _DOMAIN_SUFFIX.sub("", folded.strip())
    return " ".join(re.findall(r"[a-z0-9]+", _LEGAL_FORMS.sub(" ", folded)))


WINDOW = timedelta(days=180)
MAX_SHOWN = 25
#: Single words too common to attribute a headline on their own.
_MIN_SINGLE_WORD = 6


class PressStore(Protocol):
    def items_matching(
        self, terms: Sequence[str], *, since: datetime, limit: int = 500
    ) -> tuple[PressItem, ...]: ...

    def coverage(self) -> tuple[datetime | None, int, int]: ...


def _fold(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().casefold()


def search_terms(names: Sequence[str]) -> list[str]:
    """Distinctive forms of the organization's names (no legal form, folded)."""
    out: list[str] = []
    for name in names:
        norm = normalized_name(name)
        if not norm:
            continue
        words = norm.split()
        if len(words) == 1 and len(words[0]) < _MIN_SINGLE_WORD:
            continue  # too common to attribute alone
        out.append(norm)
    return list(dict.fromkeys(out))


def mentions(title: str, term: str) -> bool:
    folded = " " + " ".join(re.findall(r"[a-z0-9]+", _fold(title))) + " "
    return f" {term} " in folded


def press_discoveries(
    view: Mapping[str, object], store: PressStore, *, now: datetime, own_domain: str | None
) -> list[dict[str, object]]:
    names: list[str] = []
    target = view.get("target")
    if isinstance(target, Mapping) and isinstance(target.get("name"), str):
        names.append(str(target["name"]))
    for d in view.get("discoveries", []) or []:  # type: ignore[attr-defined]
        if isinstance(d, Mapping) and d.get("code") == "LEGAL_NAME_DECLARED" and d.get("statement"):
            names.append(str(d["statement"]))
    terms = search_terms(names)
    if not terms:
        return []
    since, items_held, feeds = store.coverage()
    coverage = {
        "coverageSince": None if since is None else since.isoformat(),
        "itemsInIndex": items_held,
        "feeds": feeds,
        "limitation": "Headlines syndicated by the indexed publishers only; absence here is "
        "not absence of coverage elsewhere.",
    }
    found = [
        item
        for item in store.items_matching(terms, since=now - WINDOW)
        if any(mentions(item.title, t) for t in terms)
    ]
    own = (own_domain or "").removeprefix("www.")
    observed_at = str(view.get("observedAt") or now.isoformat())
    out: list[dict[str, object]] = []
    for item in sorted(found, key=lambda i: i.published_at, reverse=True)[:MAX_SHOWN]:
        host = (urlsplit(item.url).hostname or "").removeprefix("www.")
        owned = bool(own) and (host == own or host.endswith("." + own))
        out.append(
            {
                "kind": "MENTION",
                "code": "OWN_PUBLICATION" if owned else "PRESS_MENTION",
                "statement": item.title,
                "epistemicState": "POTENTIAL",
                "sourceUrl": item.url,
                "excerpt": None,
                "observedAt": item.published_at.isoformat(),
                "detail": {
                    "outlet": item.outlet,
                    "publishedAt": item.published_at.isoformat(),
                    "language": item.language,
                    "attribution": "Headline names the organization; that it is about this "
                    "organization is not verified.",
                    "notEndorsement": True,
                    **coverage,
                },
            }
        )
    if not out and items_held:
        out.append(
            {
                "kind": "SIGNIFICANT_UNKNOWN", "code": "NO_PRESS_MENTION_FOUND",
                "statement": "No indexed headline names this organization.",
                "epistemicState": "UNKNOWN", "sourceUrl": None, "excerpt": None,
                "observedAt": observed_at, "detail": coverage,
            }
        )  # fmt: skip
    return out
