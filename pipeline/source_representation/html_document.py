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

_REPRESENTATION_VERSION = "html-document/0.1"
_NORMALIZATION_VERSION = "visible-text/0.1"
_HIDDEN = frozenset({"script", "style", "noscript", "template", "svg"})
_CHARSET = re.compile(r"charset\s*=\s*[\"']?([^;\s\"']+)", re.IGNORECASE)


class DocumentRepresentationError(ValueError):
    """Source material cannot be represented by this deterministic adapter."""


class _HtmlCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hidden_depth = 0
        self.title_depth = 0
        self.body_depth = 0
        self.text: list[str] = []
        self.title: list[str] = []
        self.language: str | None = None
        self.description: str | None = None
        self.canonical_uri: str | None = None
        self.jsonld: list[str] = []
        self._jsonld_depth = 0
        self._jsonld_buffer: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {key.lower(): value for key, value in attrs}
        lowered = tag.lower()
        if lowered in _HIDDEN:
            self.hidden_depth += 1
        if lowered == "title":
            self.title_depth += 1
        if lowered == "body":
            self.body_depth += 1
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

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        if lowered == "script" and self._jsonld_depth:
            raw = "".join(self._jsonld_buffer).strip()
            if raw:
                self.jsonld.append(raw)
            self._jsonld_depth = 0
            self._jsonld_buffer = []
        if lowered in _HIDDEN and self.hidden_depth:
            self.hidden_depth -= 1
        if lowered == "title" and self.title_depth:
            self.title_depth -= 1
        if lowered == "body" and self.body_depth:
            self.body_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._jsonld_depth:
            self._jsonld_buffer.append(data)
        if self.title_depth:
            self.title.append(data)
        if self.body_depth and not self.hidden_depth:
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
    try:
        decoded = raw.decode(charset, errors="strict")
    except (LookupError, UnicodeDecodeError) as exc:
        raise DocumentRepresentationError(
            "document charset cannot be decoded deterministically"
        ) from exc

    collector = _HtmlCollector()
    collector.feed(decoded)
    collector.close()
    visible_text = normalize_whitespace(" ".join(collector.text))
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
        "schema": "axignal.document-representation/0.1",
        "observation_id": observation_id,
        "subject_id": observation.subject_id,
        "source_ref": observation.final_uri,
        "source_type": request.source_type,
        "observed_at": observation.retrieved_at.isoformat(),
        "source_observation_fingerprint": observation.observation_fingerprint,
        "source_content_fingerprint": observation.body_fingerprint,
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
    )
