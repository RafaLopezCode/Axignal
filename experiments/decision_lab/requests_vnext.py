"""One authoritative assembly and pre-provider gate for V-next decisions."""

from __future__ import annotations

import hashlib
import json
from typing import Any, cast

from experiments.decision_lab.compiler_vnext import canonical_serialize, compile_from_sources
from experiments.decision_lab.contracts_vnext import (
    DECISION_CONTRACTS,
    DecisionFamily,
    deterministic_entity_identifier_result,
    validate_question_binding,
)
from experiments.decision_lab.models import LabError

_SEAL = object()


class ValidatedProviderRequest:
    """Immutable snapshots of the exact canonical JSON sent across the adapter."""

    __slots__ = ("_question_digest", "_question_json", "_seal", "_state_digest", "_state_json")

    def __init__(
        self,
        state_json: str,
        question_json: str,
        state_digest: str,
        question_digest: str,
        *,
        _seal: object,
    ) -> None:
        if _seal is not _SEAL:
            raise LabError("ValidatedProviderRequest must be created by the authoritative gate")
        object.__setattr__(self, "_state_json", state_json)
        object.__setattr__(self, "_question_json", question_json)
        object.__setattr__(self, "_state_digest", state_digest)
        object.__setattr__(self, "_question_digest", question_digest)
        object.__setattr__(self, "_seal", _seal)

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError("ValidatedProviderRequest is immutable")

    def _assert_integrity(self) -> None:
        if self._seal is not _SEAL:
            raise LabError("provider request seal is invalid")
        for payload, expected in (
            (self._state_json, self._state_digest),
            (self._question_json, self._question_digest),
        ):
            actual = hashlib.sha256(payload.encode("utf-8")).hexdigest()
            if actual != expected:
                raise LabError("provider request payload integrity check failed")

    def provider_payload(self) -> tuple[dict[str, Any], dict[str, Any]]:
        self._assert_integrity()
        state = json.loads(self._state_json)
        question = json.loads(self._question_json)
        if not isinstance(state, dict) or not isinstance(question, dict):
            raise LabError("sealed provider payload is not an object")
        return cast(dict[str, Any], state), cast(dict[str, Any], question)


class DeterministicDecisionResult:
    """A rule result with explicit provenance and no provider judgment fields."""

    __slots__ = (
        "contract_version",
        "identifier_namespace",
        "left_identifier",
        "resolution_mode",
        "result",
        "right_identifier",
        "rule_id",
    )

    def __init__(
        self,
        *,
        rule_id: str,
        identifier_namespace: str,
        left_identifier: str,
        right_identifier: str,
        result: str,
        contract_version: str,
    ) -> None:
        self.resolution_mode = "DETERMINISTIC_RESULT"
        self.rule_id = rule_id
        self.identifier_namespace = identifier_namespace
        self.left_identifier = left_identifier
        self.right_identifier = right_identifier
        self.result = result
        self.contract_version = contract_version

    def __setattr__(self, name: str, value: object) -> None:
        if hasattr(self, name):
            raise AttributeError("DeterministicDecisionResult is immutable")
        object.__setattr__(self, name, value)

    def to_dict(self) -> dict[str, str]:
        return {
            "resolution_mode": self.resolution_mode,
            "rule_id": self.rule_id,
            "identifier_namespace": self.identifier_namespace,
            "left_identifier": self.left_identifier,
            "right_identifier": self.right_identifier,
            "result": self.result,
            "contract_version": self.contract_version,
        }


def prepare_provider_request(
    contract_id: str,
    source_state: dict[str, Any],
    question_definition: dict[str, Any],
    evidence_catalog: dict[str, dict[str, Any]],
) -> ValidatedProviderRequest | DeterministicDecisionResult:
    """Assemble, resolve, validate, bind and seal one provider request."""
    contract = DECISION_CONTRACTS.get(contract_id)
    if contract is None:
        raise LabError("INVALID_DECISION_CONTRACT")
    compiled = compile_from_sources(contract_id, source_state, evidence_catalog)
    if compiled.unresolved_references:
        raise LabError("REFERENCE_UNRESOLVED:" + ",".join(compiled.unresolved_references))
    if not compiled.answerability.answerable:
        reasons = ",".join(compiled.answerability.reasons)
        raise LabError(f"NOT_ANSWERABLE:{reasons}")
    state = compiled.payload
    question_errors = validate_question_binding(contract_id, question_definition, state)
    if question_errors:
        raise LabError("QUESTION_OR_PRIMITIVE_CONTRACT_INVALID:" + ",".join(question_errors))

    if contract.family is DecisionFamily.ENTITY_ALIGNMENT:
        deterministic = deterministic_entity_identifier_result(state)
        if deterministic is not None:
            entities = state["entities"]
            left = entities["a"]["canonical_identifier"]
            right = entities["b"]["canonical_identifier"]
            return DeterministicDecisionResult(
                rule_id="entity-alignment.exact-verified-lei.v1",
                identifier_namespace="GLEIF:LEI",
                left_identifier=str(left["value"]),
                right_identifier=str(right["value"]),
                result=deterministic,
                contract_version=contract.version,
            )

    state_json = canonical_serialize(state)
    question_json = canonical_serialize(question_definition)
    return ValidatedProviderRequest(
        state_json,
        question_json,
        hashlib.sha256(state_json.encode("utf-8")).hexdigest(),
        hashlib.sha256(question_json.encode("utf-8")).hexdigest(),
        _seal=_SEAL,
    )
