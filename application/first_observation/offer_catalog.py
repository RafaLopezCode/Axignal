"""What an organization sells, in its own catalog's words (Value, spec 097).

Measured on 20 typical agency clients (2026-10-18): 10 were read only as "retail trade", a
sector code that says nothing of what they sell. Their own sites say it:

- the catalog its homepage links (``/collections/sunglasses``, ``/product-category/socks``,
  ``/categoria/abonos``): the link texts name its categories, in its language;
- on Shopify storefronts, the public catalog's product types (``/products.json``), counted.

Only category names are kept, never products, prices or descriptions. Promotions, navigation
words, season codes and counts are not categories. DECLARED by its site: what it offers, not
what it sells most.
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from collections.abc import Sequence
from urllib.parse import unquote, urljoin, urlsplit

MAX_CATEGORIES = 10
#: Catalog path segments, any platform or language (the next segment names the category).
_CATALOG = re.compile(
    r"/(?:collections?|categor(?:y|ies|ia|ias|ie|ien)|product-category|produkt-?kategorie|"
    r"kategorie|catalog(?:ue|o)?|c)/([^/?#]+)",
    re.IGNORECASE,
)
#: Words that, inside a label, mark a promotion, a page or the whole catalog.
_NOT_CATEGORY_WORDS = re.compile(
    r"\b(?:all|alle|todo|todos|todas|tout|tous|tutti|tutto|shop|tienda|comprar|buy|kaufen|"
    r"acheter|sale|rebajas|ofertas?|outlet|soldes|promo\w*|saldi|new|nuevo|novedades|neu|"
    r"nouveaut\w*|novit\w*|best ?sellers?|m[aá]s vendidos|top|gift ?cards?|tarjeta regalo|"
    r"carte cadeau|gutschein\w*|geschenk\w*|regalo\w*|gifts?|cadeaux?|special\w*|limited|"
    r"merch|bundle\w*|pack\w*|probier\w*|ver|view|see|voir|mehr|more|m[aá]s|other|otros|"
    r"black friday|cyber|frontpage|home|inicio|collection|colecci[oó]n|kollektion|"
    # Audiences are segments, not what it sells.
    r"mujer|hombre|women|woman|men|man|kids|ni[nñ]os|ni[nñ]as|damen|herren|femme|homme|"
    r"donna|uomo|bambini|unisex)\b",
    re.IGNORECASE,
)
#: Season or drop codes ("AW26", "SS25", "FW24") are not what it sells.
_SEASON = re.compile(r"^(?:AW|SS|FW|PF|HS|FS)\s?\d{2,4}$", re.IGNORECASE)
_GENERIC_TYPES = {"food", "product", "products", "default", "item", "items", "general", "other"}


def _fold(text: str) -> str:
    folded = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().casefold()
    return re.sub(r"\s+", " ", folded).strip()


def _clean(raw: str) -> str | None:
    text = re.sub(r"\(\s*\d+\s*\)", "", raw)  # "Gifts (28)"
    text = re.sub(r"\s+", " ", text).strip(" -|·•>:" + chr(0x203A))
    if not text or len(text) < 3 or len(text) > 40 or any(c.isdigit() for c in text):
        return None
    if _NOT_CATEGORY_WORDS.search(text) or _SEASON.match(text):
        return None
    if _fold(text) in _GENERIC_TYPES:
        return None
    return text[0].upper() + text[1:].lower() if text.isupper() else text[0].upper() + text[1:]


def catalog_categories(links: Sequence[tuple[str, str]], home_url: str) -> list[str]:
    """Its catalog categories, in the order its navigation lists them, at most ten."""
    host = (urlsplit(home_url).hostname or "").lower().removeprefix("www.")
    found: dict[str, str] = {}
    for url, text in links:
        parts = urlsplit(urljoin(home_url, url))
        if (parts.hostname or "").lower().removeprefix("www.") != host:
            continue
        match = _CATALOG.search(parts.path)
        if not match:
            continue
        label = _clean(text) or _clean(unquote(match.group(1)).replace("-", " ").replace("_", " "))
        if label and _fold(label) not in found:
            found[_fold(label)] = label
        if len(found) >= MAX_CATEGORIES:
            break
    return list(found.values())


def product_types(raw: bytes) -> list[tuple[str, int]]:
    """A Shopify public catalog's product types with how many products carry each."""
    try:
        data = json.loads(raw)
    except (ValueError, UnicodeDecodeError):
        return []
    products = data.get("products") if isinstance(data, dict) else None
    counted: Counter[str] = Counter()
    names: dict[str, str] = {}
    for product in products if isinstance(products, list) else []:
        kind = product.get("product_type") if isinstance(product, dict) else None
        label = _clean(kind) if isinstance(kind, str) else None
        if label:
            counted[_fold(label)] += 1
            names.setdefault(_fold(label), label)
    return [(names[key], n) for key, n in counted.most_common(MAX_CATEGORIES)]


def offer_categories(
    from_links: Sequence[str], from_types: Sequence[tuple[str, int]]
) -> tuple[list[str], str] | None:
    """What it sells and how it was read; product types win when they name three or more."""
    if len(from_types) >= 3:
        return [name for name, _n in from_types], "PRODUCT_TYPES"
    if len(from_links) >= 2:
        return list(from_links), "CATALOG_LINKS"
    if from_types:
        return [name for name, _n in from_types], "PRODUCT_TYPES"
    return None


def shopify_catalog_url(home_url: str) -> str:
    return urljoin(home_url, "/products.json?limit=250")
