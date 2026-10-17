"""The legal name a legal notice states in its text (Organization family, minute 0).

EU law makes a website state who runs it (aviso legal, Impressum, mentions légales, note
legali, termos legais), usually as a company name ending in its legal form, rarely as
structured data. Measured on 14 agencies (2026-10-17): only 4 declared a legal name as
structured data, while their notices said "DIGILAB TEAM, S.L.", "ATREVIA CORPORACIÓN
S.L.U.", "Groupe Ydyle, S.A." or "Builtvisible Limited" in plain text.

High precision first: legal-notice pages only; a name must end in a legal form; the words
of the sentence around it are trimmed; well-known service providers the notice also names
(analytics, hosting, payments) are never taken for the organization; names next to a
registry identifier or sharing the site's brand come first. DECLARED by the site itself,
never an admitted identity.
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from collections.abc import Sequence

_FORM = (
    r"S\.?\s?L\.?\s?U?\.?|S\.?\s?A\.?\s?U?\.?|S\.?\s?L\.?\s?L\.?|S\.?\s?Coop\.?|SAS|SASU|SARL|"
    r"EURL|S\.?\s?R\.?\s?L\.?|S\.?\s?p\.?\s?A\.?|GmbH|AG|KG|UG|Ltd\.?|Limited|LLP|LLC|Inc\.?|"
    r"B\.?\s?V\.?|N\.?\s?V\.?|AB|ApS|A/S|Oy|Lda\.?|Ltda\.?|plc"
)
#: A name: capitalised or uppercase words (with connectors) right before a legal form.
_NAME = re.compile(
    r"((?:[A-ZÁÉÍÓÚÑÀÈÌÒÙÂÊÎÔÛÄËÏÖÜÇ0-9][\w&'"
    "\u2019"
    r".\-]*"
    r"(?:\s+(?:de|del|la|las|los|y|e|et|und|&|of|the|di|da|do|dos|das))?[\s,]+){1,6}?)"
    rf"({_FORM})(?![\w])"
)
#: Providers a notice names for its own operations, never the organization itself.
_PROVIDERS = re.compile(
    r"\b(google|alphabet|meta|facebook|microsoft|amazon|aws|apple|cloudflare|hostinger|"
    r"ionos|ovh|godaddy|wix|squarespace|automattic|wordpress|hubspot|mailchimp|stripe|paypal|"
    r"linkedin|twitter|x corp|youtube|vimeo|hotjar|salesforce|zendesk|shopify|adobe|oracle)\b",
    re.IGNORECASE,
)
_LEAD_WORDS = re.compile(
    r"^(?:(?:le|la|el|the|die|der|il|o|a|site|sitio|web|website|this|este|cette|est|is|ist|"
    r"édité|editado|operated|betrieben|par|por|by|von|da|di|société|sociedad|company|"
    r"empresa|firma|titular|propietario|owner)\s+)+",
    re.IGNORECASE,
)
MAX_NAMES = 2


def _fold(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().casefold()


def _clean(raw: str, form: str) -> str | None:
    words = raw.strip(" ,").split()
    # The name is the trailing run of capitalised words: drop the sentence before it.
    keep: list[str] = []
    for word in reversed(words):
        bare = word.strip(",")
        if (
            bare[:1].isupper()
            or bare[:1].isdigit()
            or bare.lower() in {"de", "del", "y", "&", "of", "e", "et", "und", "di", "da"}
        ):
            keep.insert(0, word)
        else:
            break
    while keep and keep[0].strip(",").lower() in {
        "de",
        "del",
        "y",
        "&",
        "of",
        "e",
        "et",
        "und",
        "di",
        "da",
    }:
        keep.pop(0)
    name = _LEAD_WORDS.sub("", " ".join(keep)).strip(" ,")
    # "Madrid y GABINETE DE PRENSA S.L.U.": an uppercase name after title-case words keeps
    # only its uppercase run (a place or a sentence word precedes it).
    tokens = name.split()
    caps = [t for t in tokens if t.strip(",.&").isupper() and len(t.strip(",.&")) > 1]
    if caps and not all(t.strip(",.&").isupper() or len(t.strip(",.&")) <= 1 for t in tokens):
        run: list[str] = []
        for token in reversed(tokens):
            bare = token.strip(",.&")
            if bare.isupper() or bare == "&":
                run.insert(0, token)
            else:
                break
        if run:
            name = " ".join(run).strip(" ,")
    if not name or len(name) > 70 or len(name.split()) > 7:
        return None
    comma = "," if raw.rstrip().endswith(",") else ""
    return f"{name}{comma} {form}"


def legal_names_in_text(
    text: str, *, brand: str | None = None, identifiers: Sequence[str] = ()
) -> list[str]:
    """Up to two legal names a legal notice states, best first; [] when none is clear."""
    found: Counter[str] = Counter()
    first_at: dict[str, int] = {}
    near_id: set[str] = set()
    for match in _NAME.finditer(text):
        name = _clean(match.group(1), match.group(2).strip())
        if name is None or _PROVIDERS.search(name):
            continue
        found[name] += 1
        first_at.setdefault(name, match.start())
        window = text[max(0, match.start() - 160) : match.end() + 160]
        if any(i and i in window for i in identifiers):
            near_id.add(name)
    if not found:
        return []
    brand_key = _fold(brand or "")

    def rank(name: str) -> tuple[int, int, int, int]:
        shares_brand = bool(brand_key) and brand_key in _fold(name).replace(" ", "")
        return (-(name in near_id), -shares_brand, -found[name], first_at[name])

    ordered: list[str] = []
    bases: set[str] = set()
    for name in sorted(found, key=rank):
        base = _fold(re.sub(rf"[\s,]+(?:{_FORM})$", "", name))
        if base in bases:
            continue  # "Builtvisible Limited" and "Builtvisible Ltd." are one organization
        bases.add(base)
        ordered.append(name)
    return ordered[:MAX_NAMES]
