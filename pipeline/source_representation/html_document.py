"""Deterministic HTML document representation for acquired source material."""

from __future__ import annotations

import hashlib
import json
import re
from html.parser import HTMLParser
from urllib.parse import urljoin

from application.source_acquisition import SourceObservation, SourceRequest, source_observation_id
from application.source_representation import DocumentRepresentation
from pipeline.normalization import normalize_whitespace
from pipeline.source_acquisition import ContentAddressedArtifactStore

_REPRESENTATION_VERSION = "html-document/0.2"
_NORMALIZATION_VERSION = "visible-text/0.2"
_HIDDEN = frozenset(
    {
        "script",
        "style",
        "noscript",
        "template",
        "svg",
        "head",
        "title",
        "iframe",
        "object",
        "canvas",
    }
)
_VOID = frozenset(
    {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }
)
_BLOCK = frozenset(
    {
        "address",
        "article",
        "aside",
        "blockquote",
        "br",
        "div",
        "dl",
        "dt",
        "dd",
        "footer",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "header",
        "hr",
        "li",
        "main",
        "nav",
        "ol",
        "p",
        "pre",
        "section",
        "table",
        "td",
        "th",
        "tr",
        "ul",
    }
)
_CHARSET = re.compile(r"charset\s*=\s*[\"']?([^;\s\"']+)", re.IGNORECASE)


class DocumentRepresentationError(ValueError):
    """Source material cannot be represented by this deterministic adapter."""


def _hidden_style(style: str) -> bool:
    style = re.sub(r"/\*.*?\*/", "", style, flags=re.DOTALL)
    if "/*" in style or "*/" in style:
        raise DocumentRepresentationError("stylesheet visibility comment is unresolved")
    for declaration in style.split(";"):
        key, separator, value = declaration.partition(":")
        if not separator:
            continue
        key = key.strip().casefold()
        value = value.split("!", 1)[0].strip().casefold()
        if "var(" in value or "\\" in declaration:
            raise DocumentRepresentationError("inline stylesheet visibility is unresolved")
        if key in {"opacity", "font-size"} and "(" in value:
            raise DocumentRepresentationError("computed stylesheet visibility is unresolved")
        if key in {
            "clip",
            "clip-path",
            "transform",
            "filter",
            "mask",
            "position",
            "animation",
            "animation-name",
        }:
            raise DocumentRepresentationError("layout stylesheet visibility is unresolved")
        if (
            (key == "display" and value == "none")
            or (key == "visibility" and value in {"hidden", "collapse"})
            or (key == "content-visibility" and value == "hidden")
            or (
                key in {"opacity", "font-size"}
                and re.fullmatch(r"[+-]?(?:0+(?:\.0*)?|\.0+)(?:[a-z%]+)?", value) is not None
            )
            or (key == "color" and value == "transparent")
        ):
            return True
        allowed_values = {
            "display": {
                "block",
                "inline",
                "inline-block",
                "contents",
                "flex",
                "inline-flex",
                "grid",
                "inline-grid",
                "table",
                "table-row",
                "table-cell",
                "list-item",
                "flow-root",
            },
            "visibility": {"visible"},
            "content-visibility": {"visible"},
        }
        if key in allowed_values and value in allowed_values[key]:
            continue
        if key == "opacity" and re.fullmatch(r"(?:\d+(?:\.\d*)?|\.\d+)%?", value):
            continue
        if key == "font-size" and (
            value in {"xx-small", "x-small", "small", "medium", "large", "x-large", "xx-large"}
            or re.fullmatch(r"(?:\d+(?:\.\d*)?|\.\d+)(?:px|em|rem|pt|pc|in|cm|mm|%)", value)
        ):
            continue
        raise DocumentRepresentationError("stylesheet visibility declaration is unresolved")
    return False


class _StylesheetCollector(HTMLParser):
    """Bounded static visibility: unresolved stylesheet rules fail closed."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_style = False
        self.styles: list[str] = []
        self.external = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values: dict[str, str | None] = {}
        for key, value in attrs:
            values.setdefault(key, value)
        if tag == "style":
            self.in_style = True
        if tag == "link" and "stylesheet" in (values.get("rel") or "").casefold().split():
            self.external = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "style":
            self.in_style = False

    def handle_data(self, data: str) -> None:
        if self.in_style:
            self.styles.append(data)

    def hidden_selectors(self) -> tuple[str, ...]:
        if self.external:
            raise DocumentRepresentationError("external stylesheet visibility is unresolved")
        css = re.sub(r"/\*.*?\*/", "", "".join(self.styles), flags=re.DOTALL)
        rules = re.findall(r"([^{}]+)\{([^{}]*)\}", css)
        if re.sub(r"[^{}]+\{[^{}]*\}", "", css).strip():
            raise DocumentRepresentationError("stylesheet visibility is unresolved")
        selectors: list[str] = []
        for raw_selectors, declarations in rules:
            if not _hidden_style(declarations):
                continue
            for raw_selector in raw_selectors.split(","):
                selector = raw_selector.strip()
                if not re.fullmatch(r"(?:[.#][\w-]+|[a-zA-Z][\w-]*|\*)", selector):
                    raise DocumentRepresentationError(
                        "stylesheet visibility selector is unresolved"
                    )
                selectors.append(selector)
        return tuple(selectors)


class _HtmlCollector(HTMLParser):
    def __init__(self, hidden_selectors: tuple[str, ...]) -> None:
        super().__init__(convert_charrefs=True)
        self._stack: list[tuple[str, bool]] = []
        self._hidden_selectors = hidden_selectors
        self.text: list[str] = []
        self.title: list[str] = []
        self.language: str | None = None
        self.description: str | None = None
        self.canonical_uri: str | None = None
        self.jsonld: list[str] = []
        self._jsonld_depth = 0
        self._jsonld_buffer: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes: dict[str, str | None] = {}
        for key, value in attrs:
            attributes.setdefault(key.lower(), value)
        lowered = tag.lower()
        hidden = (
            (bool(self._stack) and self._stack[-1][1])
            or lowered in _HIDDEN
            or "hidden" in attributes
            or (lowered in {"details", "dialog"} and "open" not in attributes)
            or (attributes.get("aria-hidden") or "").strip().casefold() == "true"
            or _hidden_style(attributes.get("style") or "")
            or any(
                selector == "*"
                or selector.casefold() == lowered
                or (
                    selector.startswith(".")
                    and selector[1:] in (attributes.get("class") or "").split()
                )
                or (selector.startswith("#") and selector[1:] == attributes.get("id"))
                for selector in self._hidden_selectors
            )
        )
        if lowered in _BLOCK:
            self.text.append(" ")
        if lowered not in _VOID:
            self._stack.append((lowered, hidden))
        if lowered == "html" and self.language is None:
            self.language = attributes.get("lang")
        if lowered == "meta" and self.description is None:
            name = (attributes.get("name") or "").casefold()
            if name == "description":
                self.description = attributes.get("content")
        if lowered == "link" and self.canonical_uri is None:
            rel = (attributes.get("rel") or "").casefold().split()
            if "canonical" in rel:
                self.canonical_uri = attributes.get("href")
        if lowered == "script":
            script_type = (attributes.get("type") or "").split(";", 1)[0].strip().casefold()
            if script_type == "application/ld+json":
                self._jsonld_depth = 1
                self._jsonld_buffer = []

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag not in _VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        if lowered == "script" and self._jsonld_depth:
            raw = "".join(self._jsonld_buffer).strip()
            if raw:
                self.jsonld.append(raw)
            self._jsonld_depth = 0
            self._jsonld_buffer = []
        for index in range(len(self._stack) - 1, -1, -1):
            if self._stack[index][0] == lowered:
                if any(hidden for _, hidden in self._stack[index + 1 :]):
                    raise DocumentRepresentationError(
                        "malformed hidden ancestry visibility is unresolved"
                    )
                del self._stack[index:]
                break
        if lowered in _BLOCK:
            self.text.append(" ")

    def handle_data(self, data: str) -> None:
        if self._jsonld_depth:
            self._jsonld_buffer.append(data)
        if any(tag == "title" for tag, _ in self._stack):
            self.title.append(data)
        if any(tag == "body" for tag, _ in self._stack) and not self._stack[-1][1]:
            self.text.append(data)


def _charset(content_type: str) -> str:
    match = _CHARSET.search(content_type)
    return match.group(1).strip().lower() if match else "utf-8"


def _canonical_jsonld(values: list[str]) -> tuple[str, ...]:
    normalized: list[str] = []
    for raw in values:
        try:
            decoded = json.loads(raw)
        except json.JSONDecodeError:
            continue
        normalized.append(
            json.dumps(decoded, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        )
    return tuple(normalized)


def represent_html_observation(
    *,
    request: SourceRequest,
    observation: SourceObservation,
    artifacts: ContentAddressedArtifactStore,
) -> DocumentRepresentation:
    """Represent successful HTML bytes without granting evidence or truth authority."""

    observation_id = source_observation_id(request, observation)
    if observation.subject_id != request.subject_id:
        raise DocumentRepresentationError("source observation/request subject mismatch")
    if observation.body_artifact_ref is None or observation.body_fingerprint is None:
        raise DocumentRepresentationError("source observation has no body to represent")
    if observation.failure_state is not None:
        raise DocumentRepresentationError("failed source observation is not representable")
    content_type = observation.content_type or ""
    media_type = content_type.split(";", 1)[0].strip().casefold()
    if media_type not in {"text/html", "application/xhtml+xml"}:
        raise DocumentRepresentationError(
            f"unsupported document media type: {media_type or 'unknown'}"
        )

    charset = _charset(content_type)
    raw = artifacts.read(observation.body_artifact_ref)
    if f"sha256:{hashlib.sha256(raw).hexdigest()}" != observation.body_fingerprint:
        raise DocumentRepresentationError("source bytes do not match observation fingerprint")
    try:
        decoded = raw.decode(charset, errors="strict")
    except (LookupError, UnicodeDecodeError) as exc:
        raise DocumentRepresentationError(
            "document charset cannot be decoded deterministically"
        ) from exc

    styles = _StylesheetCollector()
    styles.feed(decoded)
    styles.close()
    collector = _HtmlCollector(styles.hidden_selectors())
    collector.feed(decoded)
    collector.close()
    visible_text = normalize_whitespace("".join(collector.text))
    if not visible_text:
        raise DocumentRepresentationError("document has no visible text")

    title = normalize_whitespace(" ".join(collector.title)) or None
    description = normalize_whitespace(collector.description) if collector.description else None
    language = collector.language.strip().lower() if collector.language else None
    canonical_uri = (
        urljoin(observation.final_uri, collector.canonical_uri) if collector.canonical_uri else None
    )
    structured_data = _canonical_jsonld(collector.jsonld)
    text_fingerprint = f"sha256:{hashlib.sha256(visible_text.encode('utf-8')).hexdigest()}"

    envelope = {
        "schema": "axignal.document-representation/0.2",
        "observation_id": observation_id,
        "subject_id": observation.subject_id,
        "source_ref": observation.final_uri,
        "source_type": request.source_type,
        "observed_at": observation.retrieved_at.isoformat(),
        "source_observation_fingerprint": observation.observation_fingerprint,
        "source_content_fingerprint": observation.body_fingerprint,
        "source_artifact_ref": observation.body_artifact_ref,
        "source_observation_artifact_ref": observation.raw_observation_ref,
        "media_type": media_type,
        "charset": charset,
        "title": title,
        "language": language,
        "description": description,
        "canonical_uri": canonical_uri,
        "visible_text": visible_text,
        "visible_text_fingerprint": text_fingerprint,
        "structured_data": structured_data,
        "representation_version": _REPRESENTATION_VERSION,
        "normalization_version": _NORMALIZATION_VERSION,
    }
    artifact_ref = artifacts.put_json(envelope)
    representation_fingerprint = hashlib.sha256(
        json.dumps(envelope, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
            "utf-8"
        )
    ).hexdigest()

    return DocumentRepresentation(
        representation_id=f"document:{observation_id}:{representation_fingerprint[:24]}",
        observation_id=observation_id,
        subject_id=observation.subject_id,
        source_ref=observation.final_uri,
        source_type=request.source_type,
        observed_at=observation.retrieved_at,
        source_observation_fingerprint=observation.observation_fingerprint,
        source_content_fingerprint=observation.body_fingerprint,
        media_type=media_type,
        charset=charset,
        title=title,
        language=language,
        description=description,
        canonical_uri=canonical_uri,
        visible_text=visible_text,
        visible_text_fingerprint=text_fingerprint,
        structured_data=structured_data,
        representation_version=_REPRESENTATION_VERSION,
        normalization_version=_NORMALIZATION_VERSION,
        artifact_ref=artifact_ref,
        source_artifact_ref=observation.body_artifact_ref,
        source_observation_artifact_ref=observation.raw_observation_ref,
    )
