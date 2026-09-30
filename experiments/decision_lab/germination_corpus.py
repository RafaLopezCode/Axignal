"""Evidence-labeled germination corpus assembly for precise Jev evaluation.

Gold labels and evaluator notes are never provider-visible. Only the explicit
claim, exact bounded evidence passage and provenance cross the Jev boundary.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from experiments.decision_lab.models import LabError
from experiments.decision_lab.requests_vnext import (
    ValidatedProviderRequest,
    prepare_provider_request,
)

ROOT = Path(__file__).resolve().parent
CORPUS_PATH = ROOT / "corpus" / "germination-v0.1" / "cases.json"
QUESTION_PATH = ROOT / "grammar" / "vnext" / "claim-evidence-support.vNext.2.json"
CONTRACT_ID = "CES.SUPPORT.vNext.2"
ALLOWED_GOLD = {
    "SUPPORTED",
    "PARTIAL",
    "CONTRADICTED",
    "NOT_SUPPORTED",
    "NO_EVIDENCE",
    "CONFLICTING",
    "UNRESOLVED",
}


@dataclass(frozen=True, slots=True)
class GerminationJevCase:
    case_id: str
    gold: str
    request: ValidatedProviderRequest
    source_url: str


def _object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise LabError(f"expected JSON object: {path}")
    return cast(dict[str, Any], value)


def load_question() -> dict[str, Any]:
    return _object(QUESTION_PATH)


def load_corpus() -> dict[str, Any]:
    return _object(CORPUS_PATH)


def build_case(raw: dict[str, Any], question: dict[str, Any]) -> GerminationJevCase:
    case_id = raw.get("id")
    claim = raw.get("claim")
    gold = raw.get("gold")
    source = raw.get("source")
    if not isinstance(case_id, str) or not case_id.strip():
        raise LabError("corpus case id is required")
    if not isinstance(claim, str) or not claim.strip():
        raise LabError(f"{case_id}: claim is required")
    if gold not in ALLOWED_GOLD:
        raise LabError(f"{case_id}: invalid gold label")
    if not isinstance(source, dict):
        raise LabError(f"{case_id}: source is required")
    url = source.get("url")
    excerpt = source.get("excerpt")
    publisher = source.get("publisher")
    source_type = source.get("source_type")
    excerpt_sha256 = source.get("excerpt_sha256")
    if not all(
        isinstance(value, str) and value.strip() for value in (url, excerpt, publisher, source_type)
    ):
        raise LabError(f"{case_id}: source metadata and evidence content are required")
    if (
        not isinstance(excerpt_sha256, str)
        or excerpt_sha256 != hashlib.sha256(excerpt.encode("utf-8")).hexdigest()
    ):
        raise LabError(f"{case_id}: evidence excerpt hash mismatch")

    evidence_id = f"{case_id}:e1"
    source_state = {
        "state_contract_version": "claim-evidence.vNext.1",
        "claim": {"proposition": claim},
        "evidence_refs": [evidence_id],
    }
    evidence_catalog = {
        evidence_id: {
            "content": excerpt,
            "provenance": {
                "source_ref": url,
                "publisher": publisher,
                "source_type": source_type,
            },
        }
    }
    prepared = prepare_provider_request(CONTRACT_ID, source_state, question, evidence_catalog)
    if not isinstance(prepared, ValidatedProviderRequest):
        raise LabError(f"{case_id}: claim-evidence case unexpectedly resolved deterministically")
    state, _ = prepared.provider_payload()
    if "gold" in json.dumps(state, sort_keys=True):
        raise LabError(f"{case_id}: gold-label leakage into provider state")
    return GerminationJevCase(case_id, gold, prepared, url)


def build_all_cases() -> tuple[GerminationJevCase, ...]:
    corpus = load_corpus()
    if corpus.get("promotion_authority") is not False:
        raise LabError("germination corpus must not have promotion authority")
    raw_cases = corpus.get("cases")
    if not isinstance(raw_cases, list) or not raw_cases:
        raise LabError("germination corpus requires cases")
    question = load_question()
    built: list[GerminationJevCase] = []
    seen: set[str] = set()
    for raw in raw_cases:
        if not isinstance(raw, dict):
            raise LabError("germination corpus cases must be objects")
        case = build_case(raw, question)
        if case.case_id in seen:
            raise LabError(f"duplicate corpus case: {case.case_id}")
        seen.add(case.case_id)
        built.append(case)
    return tuple(built)
