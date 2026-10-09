"""Deterministic reading of one public web page (spec 063 L1).

Only what the page states: title, description, languages, headings, JSON-LD the site
declares about itself (types, names, identifiers, postal addresses, service areas,
services), readable text and same-site links. Nothing here infers identity, reach or
capability; it extracts, bounds and keeps exact text so later steps can cite it.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterator, Mapping
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urljoin, urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser

READER_VERSION = "site-reading.v1"
USER_AGENT = "AXIGNAL-SourceObserver"
MAX_TEXT_CHARS = 12_000
MAX_LINKS = 200
MAX_JSONLD_DOCUMENTS = 32
MAX_JSONLD_NODES = 400
_MAX_ITEMS = 24

_SKIP_CONTENT = frozenset({"script", "style", "noscript", "template", "svg", "head"})
_BLOCK = frozenset(
    {
        "p", "div", "li", "ul", "ol", "br", "section", "article", "header", "footer",
        "nav", "main", "aside", "h1", "h2", "h3", "h4", "h5", "h6", "td", "th", "tr",
        "table", "dd", "dt", "address", "blockquote", "figcaption", "form", "label",
    }
)  # fmt: skip
_HEADINGS = frozenset({"h1", "h2", "h3"})
_SPACE = re.compile(r"\s+")
_IDENTIFIER_KEYS = {
    "leicode": "LEI",
    "vatid": "VAT",
    "taxid": "TAX_ID",
    "duns": "DUNS",
    "iso6523code": "ISO6523",
}


def _clean(value: object, limit: int = 300) -> str:
    return _SPACE.sub(" ", str(value)).strip()[:limit]


@dataclass(frozen=True, slots=True)
class DeclaredAddress:
    """A postal address the page declares (JSON-LD PostalAddress). Raw values, uncoded."""

    country: str | None
    region: str | None
    locality: str | None

    @property
    def label(self) -> str:
        return ", ".join(part for part in (self.locality, self.region, self.country) if part)


@dataclass(frozen=True, slots=True)
class DeclaredArea:
    """A service area the page declares (``areaServed``)."""

    name: str | None
    nuts: str | None = None


@dataclass(frozen=True, slots=True)
class DeclaredIdentifier:
    scheme: str
    value: str


@dataclass(frozen=True, slots=True)
class PageReading:
    url: str
    observed_at: datetime
    content_fingerprint: str
    artifact_ref: str | None
    title: str
    description: str
    language: str | None
    alternate_languages: tuple[str, ...]
    headings: tuple[str, ...]
    schema_types: tuple[str, ...]
    names: tuple[str, ...]
    legal_names: tuple[str, ...]
    identifiers: tuple[DeclaredIdentifier, ...]
    addresses: tuple[DeclaredAddress, ...]
    areas_served: tuple[DeclaredArea, ...]
    services: tuple[str, ...]
    text: str
    links: tuple[tuple[str, str], ...]
    canonical: str | None = None
    meta_robots: str | None = None

    def readable(self) -> str:
        """Citable content: title, description, JSON-LD declarations, then page text.

        JSON-LD lines are prefixed ``schema.org`` so a citation always says it quotes the
        site's machine-readable self-declaration, not prose.
        """
        lines = [self.title, self.description]
        if self.schema_types:
            lines.append("schema.org @type: " + ", ".join(self.schema_types[:12]))
        lines += [f"schema.org address: {a.label}" for a in self.addresses]
        lines += [f"schema.org areaServed: {a.name or a.nuts}" for a in self.areas_served]
        lines += [f"schema.org service: {name}" for name in self.services[:12]]
        lines.append(self.text)
        return "\n".join(line for line in lines if line)[: MAX_TEXT_CHARS + 4000]

    def lines(self) -> tuple[str, ...]:
        """Exact citable lines of :meth:`readable`, in order."""
        return tuple(line for line in self.readable().split("\n") if line)

    def to_wire(self) -> dict[str, object]:
        return {
            "url": self.url,
            "observedAt": self.observed_at.isoformat(),
            "contentFingerprint": self.content_fingerprint,
            "artifactRef": self.artifact_ref,
            "title": self.title,
            "description": self.description,
            "language": self.language,
            "alternateLanguages": list(self.alternate_languages),
            "headings": list(self.headings),
            "schemaTypes": list(self.schema_types),
            "names": list(self.names),
            "legalNames": list(self.legal_names),
            "identifiers": [[i.scheme, i.value] for i in self.identifiers],
            "addresses": [[a.country, a.region, a.locality] for a in self.addresses],
            "areasServed": [[a.name, a.nuts] for a in self.areas_served],
            "services": list(self.services),
            "text": self.text,
            "links": [list(link) for link in self.links],
            "canonical": self.canonical,
            "metaRobots": self.meta_robots,
        }

    @staticmethod
    def from_wire(raw: Mapping[str, Any]) -> PageReading:
        return PageReading(
            url=str(raw["url"]),
            observed_at=datetime.fromisoformat(str(raw["observedAt"])),
            content_fingerprint=str(raw["contentFingerprint"]),
            artifact_ref=None if raw["artifactRef"] is None else str(raw["artifactRef"]),
            title=str(raw["title"]),
            description=str(raw["description"]),
            language=None if raw["language"] is None else str(raw["language"]),
            alternate_languages=tuple(str(x) for x in raw["alternateLanguages"]),
            headings=tuple(str(x) for x in raw["headings"]),
            schema_types=tuple(str(x) for x in raw["schemaTypes"]),
            names=tuple(str(x) for x in raw["names"]),
            legal_names=tuple(str(x) for x in raw["legalNames"]),
            identifiers=tuple(DeclaredIdentifier(str(s), str(v)) for s, v in raw["identifiers"]),
            addresses=tuple(DeclaredAddress(c, r, loc) for c, r, loc in raw["addresses"]),
            areas_served=tuple(DeclaredArea(n, u) for n, u in raw["areasServed"]),
            services=tuple(str(x) for x in raw["services"]),
            text=str(raw["text"]),
            links=tuple((str(u), str(t)) for u, t in raw["links"]),
            canonical=None if raw.get("canonical") is None else str(raw["canonical"]),
            meta_robots=None if raw.get("metaRobots") is None else str(raw["metaRobots"]),
        )


class _PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.skip_depth = 0
        self.lines: list[str] = []
        self.current: list[str] = []
        self.title: list[str] = []
        self.in_title = False
        self.svg_depth = 0
        self.heading: list[str] | None = None
        self.headings: list[str] = []
        self.meta: dict[str, str] = {}
        self.language: str | None = None
        self.alternates: list[str] = []
        self.canonical: str | None = None
        self.jsonld: list[str] = []
        self.jsonld_chunks: list[str] | None = None
        self.anchor: tuple[str, list[str]] | None = None
        self.anchors: list[tuple[str, str]] = []

    def _flush(self) -> None:
        line = _clean("".join(self.current), 1000)
        if line:
            self.lines.append(line)
        self.current = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): (value or "") for key, value in attrs}
        if tag == "html" and values.get("lang"):
            self.language = values["lang"].strip()[:16] or None
        if tag == "meta":
            key = (values.get("name") or values.get("property") or "").lower()
            if key and "content" in values:
                self.meta.setdefault(key, _clean(values["content"], 500))
        if (
            tag == "link"
            and values.get("rel", "").lower() == "alternate"
            and values.get("hreflang")
        ):
            self.alternates.append(values["hreflang"].strip()[:16])
        if tag == "link" and values.get("rel", "").lower() == "canonical" and values.get("href"):
            self.canonical = self.canonical or values["href"].strip()[:500]
        if tag == "script" and values.get("type", "").lower() == "application/ld+json":
            self.jsonld_chunks = []
        if tag == "svg":
            self.svg_depth += 1
        if tag == "title" and not self.svg_depth and not self.title:
            self.in_title = True  # the document title only, never an <svg><title> icon
        if tag == "body":  # an unclosed <head> or <title> must not swallow the page
            self.skip_depth = 0
            self.in_title = False
        if tag in _SKIP_CONTENT:
            self.skip_depth += 1
            return
        if tag in _BLOCK:
            self._flush()
        if tag in _HEADINGS:
            self.heading = []
        if tag == "a" and values.get("href"):
            self.anchor = (values["href"], [])

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self.jsonld_chunks is not None:
            if len(self.jsonld) < MAX_JSONLD_DOCUMENTS:
                self.jsonld.append("".join(self.jsonld_chunks))
            self.jsonld_chunks = None
        if tag == "title":
            self.in_title = False
        if tag == "svg":
            self.svg_depth = max(0, self.svg_depth - 1)
        if tag in _SKIP_CONTENT:
            self.skip_depth = max(0, self.skip_depth - 1)
            return
        if tag in _HEADINGS and self.heading is not None:
            text = _clean("".join(self.heading), 200)
            if text and len(self.headings) < _MAX_ITEMS:
                self.headings.append(text)
            self.heading = None
        if tag == "a" and self.anchor is not None:
            href, words = self.anchor
            self.anchors.append((href, _clean("".join(words), 120)))
            self.anchor = None
        if tag in _BLOCK:
            self._flush()

    def handle_data(self, data: str) -> None:
        if self.jsonld_chunks is not None:
            self.jsonld_chunks.append(data)
            return
        if self.in_title:
            self.title.append(data)
            return
        if self.skip_depth:
            return
        self.current.append(data)
        if self.heading is not None:
            self.heading.append(data)
        if self.anchor is not None:
            self.anchor[1].append(data)

    def close(self) -> None:
        super().close()
        self._flush()


def _types(node: Mapping[str, Any]) -> tuple[str, ...]:
    raw = node.get("@type")
    values = raw if isinstance(raw, list) else [raw]
    return tuple(_clean(v, 80).rsplit("/", 1)[-1] for v in values if isinstance(v, str) and v)


def _nodes(documents: list[str]) -> Iterator[Mapping[str, Any]]:
    stack: list[object] = []
    for document in documents:
        with suppress(json.JSONDecodeError, RecursionError):
            stack.append(json.loads(document))
    seen = 0
    while stack and seen < MAX_JSONLD_NODES:
        item = stack.pop(0)
        if isinstance(item, list):
            stack.extend(item[:100])
            continue
        if not isinstance(item, dict):
            continue
        seen += 1
        yield item
        for value in item.values():
            if isinstance(value, dict | list):
                stack.append(value)


def _text_value(value: object) -> str | None:
    if isinstance(value, str):
        return _clean(value, 160) or None
    if isinstance(value, dict):
        for key in ("name", "alternateName", "@id"):
            if isinstance(value.get(key), str):
                return _clean(value[key], 160) or None
    return None


def _jsonld(documents: list[str]) -> dict[str, list[Any]]:
    out: dict[str, list[Any]] = {
        "types": [], "names": [], "legal": [], "ids": [], "addresses": [], "areas": [],
        "services": [],
    }  # fmt: skip
    for node in _nodes(documents):
        types = _types(node)
        out["types"].extend(types)
        lowered = {k.lower(): v for k, v in node.items() if isinstance(k, str)}
        for key, scheme in _IDENTIFIER_KEYS.items():
            if isinstance(lowered.get(key), str) and lowered[key].strip():
                out["ids"].append(DeclaredIdentifier(scheme, _clean(lowered[key], 64)))
        identifier = node.get("identifier")
        if isinstance(identifier, dict) and str(identifier.get("propertyID", "")).upper() == "LEI":
            value = identifier.get("value")
            if isinstance(value, str) and value.strip():
                out["ids"].append(DeclaredIdentifier("LEI", _clean(value, 64)))
        if "PostalAddress" in types:
            address = DeclaredAddress(
                _text_value(node.get("addressCountry")),
                _text_value(node.get("addressRegion")),
                _text_value(node.get("addressLocality")),
            )
            if address.label:
                out["addresses"].append(address)
            continue
        if "Service" in types or "Product" in types:
            name = _text_value(node.get("name"))
            if name:
                out["services"].append(name)
        elif isinstance(node.get("legalName"), str) or "address" in node or "areaServed" in node:
            if (name := _text_value(node.get("name"))) is not None:
                out["names"].append(name)
            if (legal := _text_value(node.get("legalName"))) is not None:
                out["legal"].append(legal)
        areas = node.get("areaServed")
        for area in areas if isinstance(areas, list) else [areas]:
            if isinstance(area, str) and area.strip():
                out["areas"].append(DeclaredArea(_clean(area, 120)))
            elif isinstance(area, dict):
                nuts = None
                ident = area.get("identifier")
                if isinstance(ident, dict) and ident.get("propertyID") == "NUTS":
                    value = ident.get("value")
                    nuts = (
                        value
                        if isinstance(value, str) and re.fullmatch(r"[A-Z]{2}[0-9A-Z]{0,3}", value)
                        else None
                    )
                name = _text_value(area)
                if name or nuts:
                    out["areas"].append(DeclaredArea(name, nuts))
    return out


def _unique(values: list[Any], limit: int = _MAX_ITEMS) -> tuple[Any, ...]:
    return tuple(dict.fromkeys(values))[:limit]


def same_site(url: str, origin_host: str) -> bool:
    host = (urlsplit(url).hostname or "").lower()
    bare = origin_host.removeprefix("www.")
    return host in {bare, "www." + bare}


def read_page(
    *,
    url: str,
    html: str,
    observed_at: datetime,
    content_fingerprint: str,
    artifact_ref: str | None,
) -> PageReading:
    """Parse one fetched HTML page into bounded, citable public statements."""

    parser = _PageParser()
    with suppress(AssertionError):  # malformed markup degrades, never raises
        parser.feed(html)
    parser.close()
    data = _jsonld(parser.jsonld)
    host = (urlsplit(url).hostname or "").lower()
    links: list[tuple[str, str]] = []
    for href, text in parser.anchors:
        if href.startswith(("mailto:", "tel:", "javascript:", "#")):
            continue
        absolute = urljoin(url, href)
        parts = urlsplit(absolute)
        if parts.scheme not in ("http", "https") or not same_site(absolute, host):
            continue
        clean = urlunsplit((parts.scheme, parts.netloc, parts.path or "/", parts.query, ""))
        if clean.rstrip("/") != url.rstrip("/"):
            links.append((clean, text))
    text = "\n".join(_unique(parser.lines, 10_000))[:MAX_TEXT_CHARS]
    description = parser.meta.get("description") or parser.meta.get("og:description") or ""
    site_name = parser.meta.get("og:site_name")
    return PageReading(
        url=url,
        observed_at=observed_at,
        content_fingerprint=content_fingerprint,
        artifact_ref=artifact_ref,
        title=_clean("".join(parser.title), 200),
        description=description,
        language=parser.language,
        alternate_languages=_unique(parser.alternates),
        headings=tuple(parser.headings),
        schema_types=_unique(data["types"], 64),
        names=_unique([*data["names"], *([site_name] if site_name else [])]),
        legal_names=_unique(data["legal"]),
        identifiers=_unique(data["ids"]),
        addresses=_unique(data["addresses"]),
        areas_served=_unique(data["areas"]),
        services=_unique(data["services"]),
        text=text,
        links=_unique(links, MAX_LINKS),
        canonical=None if parser.canonical is None else urljoin(url, parser.canonical),
        meta_robots=parser.meta.get("robots"),
    )


@dataclass(frozen=True, slots=True)
class RobotsReading:
    """The site's robots.txt, as observed. ``None`` text means none was published."""

    text: str | None
    observed_at: datetime

    def allows(self, url: str) -> bool:
        if self.text is None:
            return True
        parser = RobotFileParser()
        parser.parse(self.text.splitlines())
        return parser.can_fetch(USER_AGENT, url)

    def sitemaps(self) -> tuple[str, ...]:
        if self.text is None:
            return ()
        return _unique(
            [
                line.split(":", 1)[1].strip()
                for line in self.text.splitlines()
                if line.lower().startswith("sitemap:") and line.split(":", 1)[1].strip()
            ],
            8,
        )


#: Path/anchor words, by what a page is likely to answer (en, es, fr, de, it, pt).
#: Governed routing hints for *which page to read next*, never a fact about the site.
INFORMATION_PAGES: dict[str, tuple[str, ...]] = {
    "ACTIVITY": (
        "services", "service", "servicios", "servicio", "products", "productos", "solutions",
        "soluciones", "what-we-do", "que-hacemos", "prestations", "leistungen", "servizi",
        "prodotti", "produits", "produkte", "servicos", "produtos", "courses", "cursos",
        "offer", "oferta",
    ),
    "ABOUT": (
        "about", "about-us", "quienes-somos", "sobre-nosotros", "nosotros", "empresa",
        "company", "qui-sommes-nous", "a-propos", "ueber-uns", "uber-uns", "unternehmen",
        "chi-siamo", "azienda", "sobre", "quem-somos",
    ),
    "LOCATION": (
        "contact", "contacto", "contactanos", "kontakt", "contatti", "contato", "locations",
        "ubicaciones", "donde-estamos", "oficinas", "offices", "standorte", "sedi", "agences",
    ),
}  # fmt: skip


def rank_information_links(
    page: PageReading, needs: tuple[str, ...], *, limit: int
) -> tuple[tuple[str, str], ...]:
    """Same-site links that most likely answer ``needs`` (ordered), with the need served."""

    ranked: list[tuple[int, int, str, str]] = []
    for position, (url, text) in enumerate(page.links):
        path = urlsplit(url).path.casefold().strip("/")
        if path.count("/") > 2 or any(path.endswith(ext) for ext in (".pdf", ".jpg", ".png")):
            continue
        words = set(re.split(r"[/_\-.]+", path)) | set(re.split(r"\W+", text.casefold()))
        for rank, need in enumerate(needs):
            terms = INFORMATION_PAGES.get(need, ())
            if path in terms or words & set(terms) or any(t in path for t in terms if "-" in t):
                ranked.append((rank, position, url, need))
                break
    best: dict[str, str] = {}  # need -> first (best-placed) link answering it
    for _rank, _position, url, need in sorted(ranked):
        if need not in best and url not in best.values():
            best[need] = url
    return tuple((best[need], need) for need in needs if need in best)[:limit]
