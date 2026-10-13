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
from dataclasses import dataclass, field
from datetime import datetime
from html import unescape
from html.parser import HTMLParser
from typing import Any
from urllib.parse import unquote, urljoin, urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser

from application.first_observation.registry_ids import registry_identifiers

READER_VERSION = "site-reading.v2"
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
_RESOURCE_RELS = frozenset({"stylesheet", "preconnect", "dns-prefetch", "preload", "modulepreload"})
_SPACE = re.compile(r"\s+")
_IDENTIFIER_KEYS = {
    "leicode": "LEI",
    "vatid": "VAT",
    "taxid": "TAX_ID",
    "duns": "DUNS",
    "iso6523code": "ISO6523",
}


_MAP_HOST = re.compile(
    r"(^|\.)(google\.[a-z.]+|maps\.google\.[a-z.]+|openstreetmap\.org|bing\.com)$"
)
_COORD_PATTERNS = (
    re.compile(r"@(-?\d{1,2}\.\d{3,}),(-?\d{1,3}\.\d{3,})"),  # .../@40.41,-3.70,17z
    re.compile(
        r"[?&](?:q|ll|query|center|daddr|destination)=(-?\d{1,2}\.\d{3,})(?:,|%2C)\s*(-?\d{1,3}\.\d{3,})"
    ),
    re.compile(r"[?&#]mlat=(-?\d{1,2}\.\d{3,})&mlon=(-?\d{1,3}\.\d{3,})"),  # openstreetmap
)
_EMBED_LAT = re.compile(r"!3d(-?\d{1,2}\.\d{3,})")  # Google embed: !2d<lng>!3d<lat>
_EMBED_LNG = re.compile(r"!2d(-?\d{1,3}\.\d{3,})")


def map_coordinates(url: str) -> tuple[float, float] | None:
    """Latitude and longitude carried by a map link or embed the site itself publishes."""
    try:
        host = (urlsplit(url).hostname or "").lower()
    except ValueError:
        return None
    if not _MAP_HOST.search(host) or ("google" in host and "map" not in url.lower()):
        return None
    found: tuple[str, str] | None = None
    lat, lng = _EMBED_LAT.search(url), _EMBED_LNG.search(url)
    if lat and lng:
        found = (lat.group(1), lng.group(1))
    else:
        for pattern in _COORD_PATTERNS:
            match = pattern.search(url)
            if match:
                found = (match.group(1), match.group(2))
                break
    if found is None:
        return None
    latitude, longitude = float(found[0]), float(found[1])
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180) or (latitude, longitude) == (0, 0):
        return None
    return round(latitude, 5), round(longitude, 5)


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
    #: Page-level representation signals (headings, sharing tags, images, entity links),
    #: measured by this reader version; empty for pages read by an earlier version.
    signals: Mapping[str, object] = field(default_factory=dict)

    def metadata_only(self) -> PageReading:
        """The page without its content: URL, time and fingerprint (change detection)."""
        return PageReading(
            url=self.url, observed_at=self.observed_at,
            content_fingerprint=self.content_fingerprint, artifact_ref=self.artifact_ref,
            title="", description="", language=None, alternate_languages=(), headings=(),
            schema_types=(), names=(), legal_names=(), identifiers=(), addresses=(),
            areas_served=(), services=(), text="", links=(),
        )  # fmt: skip

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
            "signals": dict(self.signals),
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
            signals=dict(raw.get("signals") or {}),
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
        self.h1: list[str] = []
        self.coordinates: list[tuple[float, float]] = []
        self.heading_tag: str | None = None
        self.images = 0
        self.images_without_alt = 0
        self.hreflang: dict[str, str] = {}
        #: Hosts whose code, frames or styles the page loads (its observed technology).
        self.resource_hosts: list[str] = []
        #: Image alternative texts with the heading they sit under (logo walls).
        self.alts: list[tuple[str, str]] = []

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
            if len(self.hreflang) < 64:
                self.hreflang.setdefault(
                    values["hreflang"].strip().lower()[:16], values.get("href", "")[:300]
                )
        if tag == "img":
            self.images += 1
            alt = _clean(values.get("alt", ""), 120)
            if alt and len(self.alts) < 160:
                self.alts.append((self.headings[-1] if self.headings else "", alt))
            if not values.get("alt", "").strip() and values.get("role") != "presentation":
                self.images_without_alt += 1
        if tag == "link" and values.get("rel", "").lower() == "canonical" and values.get("href"):
            self.canonical = self.canonical or values["href"].strip()[:500]
        resource = (
            values.get("src") if tag in {"script", "iframe"}
            else values.get("href") if tag == "link" and values.get("rel", "").lower() in _RESOURCE_RELS
            else values.get("action") if tag == "form"
            else None
        )  # fmt: skip
        if resource and len(self.resource_hosts) < 120:
            host = (urlsplit(resource.strip()).hostname or "").lower()
            if host and host not in self.resource_hosts:
                self.resource_hosts.append(host)
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
            self.heading_tag = tag
        if tag == "a" and values.get("href"):
            self.anchor = (values["href"], [])
        for attribute in ("href", "src", "data-src"):
            if tag in {"a", "iframe"} and values.get(attribute) and len(self.coordinates) < 10:
                point = map_coordinates(values[attribute])
                if point is not None and point not in self.coordinates:
                    self.coordinates.append(point)

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
            if self.heading_tag == "h1" and len(self.h1) < 8:
                self.h1.append(text)
            self.heading = None
            self.heading_tag = None
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


_ENTITY_TYPES = frozenset(
    {"Organization", "Corporation", "LocalBusiness", "ProfessionalService", "Store",
     "OnlineBusiness", "NGO", "EducationalOrganization", "GovernmentOrganization"}
)  # fmt: skip
_ENTITY_FIELDS = (
    "name", "url", "logo", "sameAs", "address", "telephone", "email", "contactPoint",
    "description", "legalName", "vatID", "foundingDate",
)  # fmt: skip


_EMAIL = re.compile(r"[A-Za-z0-9._%+-]{1,64}@[A-Za-z0-9.-]{1,190}\.[A-Za-z]{2,24}")


def _jsonld_emails(documents: list[str]) -> list[str]:
    """schema.org ``email`` values (also inside contactPoint), as the site declares them."""
    found: list[str] = []
    for document in documents:
        for value in re.findall(r'"email"\s*:\s*"([^"]{3,260})"', document):
            found += _EMAIL.findall(unquote(value.removeprefix("mailto:")))
    return found


def _jsonld_errors(documents: list[str]) -> int:
    errors = 0
    for document in documents:
        try:
            json.loads(document)
        except (json.JSONDecodeError, RecursionError):
            errors += 1
    return errors


def _jsonld(documents: list[str]) -> dict[str, list[Any]]:
    out: dict[str, list[Any]] = {
        "types": [], "names": [], "legal": [], "ids": [], "addresses": [], "areas": [],
        "services": [], "same_as": [], "entity_fields": [], "geo": [], "jobs": [],
        "ratings": [],
    }  # fmt: skip
    for node in _nodes(documents):
        types = _types(node)
        out["types"].extend(types)
        if "GeoCoordinates" in types:
            try:
                point = (round(float(node["latitude"]), 5), round(float(node["longitude"]), 5))
            except (KeyError, TypeError, ValueError):
                point = None
            if point and -90 <= point[0] <= 90 and -180 <= point[1] <= 180 and point != (0, 0):
                out["geo"].append(point)
        if "JobPosting" in types and len(out["jobs"]) < 50:
            title = _text_value(node.get("title")) or _text_value(node.get("name"))
            if title:
                posted = node.get("datePosted")
                out["jobs"].append(
                    {
                        "title": title,
                        "datePosted": _clean(posted, 32) if isinstance(posted, str) else None,
                    }
                )
        rating = node.get("aggregateRating")
        if set(types) & _ENTITY_TYPES and isinstance(rating, dict):
            with suppress(TypeError, ValueError):
                score = float(str(rating.get("ratingValue")).replace(",", "."))
                count = int(str(rating.get("reviewCount") or rating.get("ratingCount") or 0))
                best = float(str(rating.get("bestRating") or 5).replace(",", "."))
                if 0 < score <= best <= 100:
                    out["ratings"].append({"value": score, "best": best, "count": count})
        if set(types) & _ENTITY_TYPES:
            same = node.get("sameAs")
            for link in same if isinstance(same, list) else [same]:
                if isinstance(link, str) and link.startswith(("https://", "http://")):
                    out["same_as"].append(link.strip()[:300])
            out["entity_fields"].extend(
                key for key in _ENTITY_FIELDS if node.get(key) not in (None, "", [], {})
            )
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


_RCDATA_OPEN = re.compile(r"<(title|textarea)(?=[\s/>])[^>]*>", re.I)


def split_rcdata(html: str) -> tuple[str, str]:
    """(markup without RCDATA elements, the document title).

    ``<title>`` and ``<textarea>`` are RCDATA: newer CPython releases (security fixes in
    3.12.x/3.13.x and 3.14) treat everything up to the closing tag as text, older ones do
    not. An unclosed ``<title>`` would then swallow the whole page on one runtime and not on
    another. Both elements are removed here, before the standard parser runs, so the
    result never depends on the Python version. An unclosed element ends at the next tag.
    The document title is the first ``<title>`` before any ``<svg>`` or ``<body>``.
    """

    out: list[str] = []
    title = ""
    position = 0
    lowered = html.lower()
    while (match := _RCDATA_OPEN.search(html, position)) is not None:
        tag = match.group(1).lower()
        close = lowered.find(f"</{tag}", match.end())
        next_tag = html.find("<", match.end())
        end = close if close >= 0 else (next_tag if next_tag >= 0 else len(html))
        if close >= 0 and next_tag >= 0 and next_tag < close and tag == "title":
            # "<title>Broken<body>..." with a later "</title>": the title still ends at the
            # first tag, as browsers recover, so the body is never swallowed.
            end = next_tag
        content = html[match.end() : end]
        before = lowered[: match.start()]
        if tag == "title" and not title and "<svg" not in before and "<body" not in before:
            title = content
        out.append(html[position : match.start()])
        position = end
        if close >= 0 and end == close:
            closing_end = lowered.find(">", close)
            position = len(html) if closing_end < 0 else closing_end + 1
    out.append(html[position:])
    return "".join(out), title


def read_page(
    *,
    url: str,
    html: str,
    observed_at: datetime,
    content_fingerprint: str,
    artifact_ref: str | None,
) -> PageReading:
    """Parse one fetched HTML page into bounded, citable public statements."""

    markup, document_title = split_rcdata(html)
    parser = _PageParser()
    with suppress(AssertionError):  # malformed markup degrades, never raises
        parser.feed(markup)
    parser.close()
    data = _jsonld(parser.jsonld)
    host = (urlsplit(url).hostname or "").lower()
    links: list[tuple[str, str]] = []
    external = 0
    external_hosts: set[str] = set()
    emails: list[str] = []
    for href, text in parser.anchors:
        if href.lower().startswith("mailto:"):
            emails += _EMAIL.findall(unquote(href[7:].split("?", 1)[0]))
        if href.startswith(("mailto:", "tel:", "javascript:", "#")):
            continue
        absolute = urljoin(url, href)
        parts = urlsplit(absolute)
        if parts.scheme in ("http", "https") and not same_site(absolute, host):
            external += 1
            if parts.hostname:
                external_hosts.add(parts.hostname.lower())
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
        title=_clean(unescape(document_title), 200),
        description=description,
        language=parser.language,
        alternate_languages=_unique(parser.alternates),
        headings=tuple(parser.headings),
        schema_types=_unique(data["types"], 64),
        names=_unique([*data["names"], *([site_name] if site_name else [])]),
        legal_names=_unique(data["legal"]),
        identifiers=_unique(
            [*data["ids"], *(DeclaredIdentifier(s, v) for s, v in registry_identifiers(text))]
        ),
        addresses=_unique(data["addresses"]),
        areas_served=_unique(data["areas"]),
        services=_unique(data["services"]),
        text=text,
        links=_unique(links, MAX_LINKS),
        canonical=None if parser.canonical is None else urljoin(url, parser.canonical),
        meta_robots=parser.meta.get("robots"),
        signals={
            "h1": parser.h1[:3],
            "h1Count": len(parser.h1),
            "viewport": "viewport" in parser.meta,
            "ogTitle": bool(parser.meta.get("og:title")),
            "ogDescription": bool(parser.meta.get("og:description")),
            "ogImage": bool(parser.meta.get("og:image")),
            "twitterCard": bool(parser.meta.get("twitter:card")),
            "images": parser.images,
            "imagesWithoutAlt": parser.images_without_alt,
            "hreflang": sorted(parser.hreflang)[:32],
            "xDefault": "x-default" in parser.hreflang,
            "jsonldDocuments": len(parser.jsonld),
            "jsonldErrors": _jsonld_errors(parser.jsonld),
            "sameAs": list(_unique(data["same_as"], 16)),
            "resourceHosts": [
                h for h in parser.resource_hosts if not same_site(f"https://{h}/", host)
            ],
            "generator": parser.meta.get("generator"),
            "imageAlts": [list(pair) for pair in _unique(parser.alts, 160)],
            "jobPostings": data["jobs"][:50],
            "ratings": data["ratings"][:3],
            "externalLinkHosts": sorted(external_hosts)[:120],
            "entityFields": sorted(set(data["entity_fields"])),
            "words": len(text.split()),
            "internalLinks": len(links),
            "externalLinks": external,
            "https": urlsplit(url).scheme == "https",
            # Points the site publishes: its own map links/embeds and schema.org geo.
            "coordinates": [[lat, lng, "MAP_LINK"] for lat, lng in parser.coordinates]
            + [[lat, lng, "SCHEMA_GEO"] for lat, lng in _unique(data["geo"], 10)],
            # Addresses the site itself publishes (mailto links, schema.org email).
            "emails": list(
                _unique(
                    [
                        e.lower()
                        for e in [*emails, *_jsonld_emails(parser.jsonld), *_EMAIL.findall(text)]
                    ],
                    10,
                )
            ),
        },
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
    # Where the law makes a company state its register number.
    "LEGAL": (
        "mentions-legales", "mentions", "legales", "aviso-legal", "impressum", "imprint",
        "legal-notice", "legal", "note-legali", "informacoes-legais", "colofon", "colophon",
        "company-information", "company-details",
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


_LANGUAGE_SEGMENT = re.compile(r"^[a-z]{2}(?:[-_][a-z]{2})?$")


def language_entry_link(page: PageReading) -> str | None:
    """The version to read when the homepage is only a language or country selector.

    A splash page (``/es/``, ``/pt/``, ``/us/``…) says nothing of the activity itself; the
    entry matching the page's declared language (region first) is read instead, else the first.
    """
    entries: dict[str, str] = {}
    for url, _text in page.links:
        segment = urlsplit(url).path.casefold().strip("/")
        if _LANGUAGE_SEGMENT.match(segment) and segment not in entries:
            entries[segment] = url
    if len(entries) < 3:
        return None  # a couple of language links is a switcher, not a selector page
    declared = (page.language or "").casefold().replace("_", "-")
    preferred = [declared, *reversed(declared.split("-"))] if declared else []
    for segment in preferred:
        if segment in entries:
            return entries[segment]
    return next(iter(entries.values()))
