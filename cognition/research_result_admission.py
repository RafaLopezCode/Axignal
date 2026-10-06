"""Fail-closed admission for PB-10 research results.

This gate only decides whether governed research work was resolved enough to
leave the observation queue. It never admits canonical AXIGLAND truth.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from urllib.parse import urlparse

from application.economic_discovery.batch_research import ClaimedResearchWork
from cognition.jobs.model import StructuredResult


class EvidenceBackedResearchAdmission:
    """Resolve work only when every governed requirement has public provenance."""

    def admit(self, *, work: ClaimedResearchWork, result: StructuredResult) -> bool:
        payload = result.payload.get("research")
        if not isinstance(payload, Mapping):
            return False
        if payload.get("status") != "EVIDENCE_FOUND":
            return False

        candidates = payload.get("evidence_candidates")
        unresolved = payload.get("unresolved_requirements")
        if not isinstance(candidates, Sequence) or isinstance(candidates, (str, bytes)):
            return False
        if not isinstance(unresolved, Sequence) or isinstance(unresolved, (str, bytes)):
            return False
        if unresolved:
            return False

        required = set(work.work.intent.missing_requirements)
        covered: set[str] = set()
        for candidate in candidates:
            if not isinstance(candidate, Mapping):
                return False
            requirement = candidate.get("requirement")
            source_url = candidate.get("source_url")
            excerpt = candidate.get("excerpt")
            if (
                not isinstance(requirement, str)
                or requirement not in required
                or not isinstance(source_url, str)
                or not self._public_http_url(source_url)
                or not isinstance(excerpt, str)
                or not excerpt.strip()
            ):
                return False
            covered.add(requirement)
        return covered == required

    @staticmethod
    def _public_http_url(value: str) -> bool:
        try:
            parsed = urlparse(value)
        except ValueError:
            return False
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            return False
        host = parsed.hostname.lower()
        return host not in {"localhost", "127.0.0.1", "::1"}
