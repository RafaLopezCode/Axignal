"""AXIGNAL-owned semantic contracts for the experimental V-next lab path.

These declarations validate information shape and answer-space contracts. They
do not determine whether supplied evidence is true or whether a model is right.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Any


class DecisionFamily(StrEnum):
    CLAIM_EVIDENCE_SUPPORT = "CLAIM_EVIDENCE_SUPPORT"
    ENTITY_ALIGNMENT = "ENTITY_ALIGNMENT"
    ECONOMIC_RELATIONSHIP = "ECONOMIC_RELATIONSHIP"


class Primitive(StrEnum):
    CHOICE = "CHOICE"
    SCORE = "SCORE"
    NOUL = "NOUL"


class Missingness(StrEnum):
    ABSENT = "ABSENT"
    EMPTY = "EMPTY"
    UNKNOWN = "UNKNOWN"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    PRESENT = "PRESENT"


class RequirementCheck(StrEnum):
    PRESENCE = "PRESENCE"
    NON_EMPTY = "NON_EMPTY"
    SEMANTIC_CONTENT = "SEMANTIC_CONTENT"
    CARDINALITY = "CARDINALITY"
    PAIRWISE_ARGUMENTS = "PAIRWISE_ARGUMENTS"
    TEMPORAL_REFERENCE = "TEMPORAL_REFERENCE"
    PROVENANCE = "PROVENANCE"
    DIRECTION = "DIRECTION"
    CLAIM_PROPOSITION = "CLAIM_PROPOSITION"
    EVIDENCE_PASSAGE = "EVIDENCE_PASSAGE"


@dataclass(frozen=True)
class InformationRequirement:
    requirement_id: str
    path: str
    checks: tuple[RequirementCheck, ...]
    minimum_cardinality: int = 1
    unknown_allowed: bool = False
    not_applicable_allowed: bool = False


@dataclass(frozen=True)
class StateContract:
    family: DecisionFamily
    version: str
    requirements: tuple[InformationRequirement, ...]


@dataclass(frozen=True)
class DecisionContract:
    family: DecisionFamily
    version: str
    semantic_target: str
    question_id: str
    question_version: str
    primitive: Primitive
    answer_space: tuple[str, ...]
    state_contract_version: str
    uncertainty_semantics: str
    composition_policy: str
    authority_boundary: str
    evaluation_status: str
    information_requirements: tuple[str, ...]
    question_semantic_fingerprint: str = ""


def _r(
    requirement_id: str,
    path: str,
    *checks: RequirementCheck,
    minimum_cardinality: int = 1,
    unknown_allowed: bool = False,
    not_applicable_allowed: bool = False,
) -> InformationRequirement:
    return InformationRequirement(
        requirement_id,
        path,
        tuple(checks),
        minimum_cardinality,
        unknown_allowed,
        not_applicable_allowed,
    )


STATE_CONTRACTS: dict[DecisionFamily, StateContract] = {
    DecisionFamily.CLAIM_EVIDENCE_SUPPORT: StateContract(
        DecisionFamily.CLAIM_EVIDENCE_SUPPORT,
        "claim-evidence.vNext.1",
        (
            _r(
                "claim-proposition",
                "claim.proposition",
                RequirementCheck.PRESENCE,
                RequirementCheck.NON_EMPTY,
                RequirementCheck.CLAIM_PROPOSITION,
            ),
            _r(
                "evidence-passages",
                "evidence",
                RequirementCheck.PRESENCE,
                RequirementCheck.CARDINALITY,
                minimum_cardinality=1,
            ),
            _r(
                "evidence-content",
                "evidence[*]",
                RequirementCheck.NON_EMPTY,
                RequirementCheck.SEMANTIC_CONTENT,
                RequirementCheck.EVIDENCE_PASSAGE,
            ),
            _r(
                "evidence-provenance",
                "evidence[*].provenance.source_ref",
                RequirementCheck.PRESENCE,
                RequirementCheck.NON_EMPTY,
                RequirementCheck.PROVENANCE,
            ),
        ),
    ),
    DecisionFamily.ENTITY_ALIGNMENT: StateContract(
        DecisionFamily.ENTITY_ALIGNMENT,
        "entity-alignment.vNext.1",
        (
            _r("entity-a", "entities.a", RequirementCheck.PRESENCE, RequirementCheck.NON_EMPTY),
            _r("entity-b", "entities.b", RequirementCheck.PRESENCE, RequirementCheck.NON_EMPTY),
            _r(
                "entity-a-name",
                "entities.a.name",
                RequirementCheck.PRESENCE,
                RequirementCheck.NON_EMPTY,
            ),
            _r(
                "entity-b-name",
                "entities.b.name",
                RequirementCheck.PRESENCE,
                RequirementCheck.NON_EMPTY,
            ),
            _r("pairwise-arguments", "entities", RequirementCheck.PAIRWISE_ARGUMENTS),
            _r(
                "identity-evidence",
                "evidence[*]",
                RequirementCheck.PRESENCE,
                RequirementCheck.NON_EMPTY,
                RequirementCheck.SEMANTIC_CONTENT,
                RequirementCheck.EVIDENCE_PASSAGE,
            ),
            _r(
                "identity-evidence-provenance",
                "evidence[*].provenance.source_ref",
                RequirementCheck.PRESENCE,
                RequirementCheck.NON_EMPTY,
                RequirementCheck.PROVENANCE,
            ),
        ),
    ),
    DecisionFamily.ECONOMIC_RELATIONSHIP: StateContract(
        DecisionFamily.ECONOMIC_RELATIONSHIP,
        "economic-relationship.vNext.1",
        (
            _r(
                "relationship-endpoints",
                "relationship.endpoints",
                RequirementCheck.PRESENCE,
                RequirementCheck.CARDINALITY,
                minimum_cardinality=2,
            ),
            _r(
                "relationship-proposition",
                "relationship.proposition",
                RequirementCheck.PRESENCE,
                RequirementCheck.NON_EMPTY,
            ),
            _r(
                "relationship-direction",
                "relationship.direction",
                RequirementCheck.PRESENCE,
                RequirementCheck.DIRECTION,
            ),
            _r(
                "relationship-evidence",
                "evidence[*]",
                RequirementCheck.PRESENCE,
                RequirementCheck.NON_EMPTY,
                RequirementCheck.SEMANTIC_CONTENT,
                RequirementCheck.EVIDENCE_PASSAGE,
            ),
            _r(
                "relationship-provenance",
                "evidence[*].provenance.source_ref",
                RequirementCheck.PRESENCE,
                RequirementCheck.NON_EMPTY,
                RequirementCheck.PROVENANCE,
            ),
        ),
    ),
}


DECISION_CONTRACTS: dict[str, DecisionContract] = {
    "CES.SUPPORT.vNext": DecisionContract(
        DecisionFamily.CLAIM_EVIDENCE_SUPPORT,
        "decision-contract.vNext.1",
        "Assess the explicit claim proposition against all supplied semantic evidence passages.",
        "CES.SUPPORT.vNext",
        "vNext.1",
        Primitive.CHOICE,
        ("SUPPORTED", "PARTIAL", "NOT_SUPPORTED", "NO_EVIDENCE", "CONFLICTING", "UNRESOLVED"),
        STATE_CONTRACTS[DecisionFamily.CLAIM_EVIDENCE_SUPPORT].version,
        "Missing evidence is not negative evidence; conflicting and partial support remain distinct.",
        "support.vNext.1; preserves raw choice and distribution; no truth threshold.",
        "Experimental judgment only; AXIGNAL policy and EvidenceAdmission retain authority.",
        "OFFLINE_STRUCTURAL_VALIDATION_ONLY",
        tuple(
            item.requirement_id
            for item in STATE_CONTRACTS[DecisionFamily.CLAIM_EVIDENCE_SUPPORT].requirements
        ),
    ),
    "CES.SUPPORT.vNext.2": DecisionContract(
        DecisionFamily.CLAIM_EVIDENCE_SUPPORT,
        "decision-contract.vNext.2",
        "Assess the explicit claim proposition against all supplied semantic evidence passages, distinguishing evidence that refutes the claim from evidence sources that conflict with each other.",
        "CES.SUPPORT.vNext.2",
        "vNext.2",
        Primitive.CHOICE,
        (
            "SUPPORTED",
            "PARTIAL",
            "CONTRADICTED",
            "NOT_SUPPORTED",
            "NO_EVIDENCE",
            "CONFLICTING",
            "UNRESOLVED",
        ),
        STATE_CONTRACTS[DecisionFamily.CLAIM_EVIDENCE_SUPPORT].version,
        "No relevant passage, source-source conflict, direct claim contradiction, and genuine indeterminacy remain distinct.",
        "support.vNext.2; preserves raw choice and distribution; no truth threshold.",
        "Experimental judgment only; AXIGNAL policy and EvidenceAdmission retain authority.",
        "OFFLINE_STRUCTURAL_VALIDATION_ONLY",
        tuple(
            item.requirement_id
            for item in STATE_CONTRACTS[DecisionFamily.CLAIM_EVIDENCE_SUPPORT].requirements
        ),
    ),
    "ENT.ALIGN.vNext": DecisionContract(
        DecisionFamily.ENTITY_ALIGNMENT,
        "decision-contract.vNext.1",
        "Compare two supplied records for same legal entity versus related, distinct, or unresolved.",
        "ENT.ALIGN.vNext",
        "vNext.1",
        Primitive.CHOICE,
        ("SAME_LEGAL_ENTITY", "RELATED_ENTITY", "DISTINCT_ENTITY", "UNRESOLVED"),
        STATE_CONTRACTS[DecisionFamily.ENTITY_ALIGNMENT].version,
        "UNRESOLVED is distinct from DISTINCT_ENTITY; exact identifiers are compared deterministically first.",
        "entity-alignment.vNext.1; retain raw typed judgment.",
        "No entity merge or canonical write; AXIGNAL resolution policy remains authoritative.",
        "OFFLINE_STRUCTURAL_VALIDATION_ONLY",
        tuple(
            item.requirement_id
            for item in STATE_CONTRACTS[DecisionFamily.ENTITY_ALIGNMENT].requirements
        ),
    ),
    "REL.EXISTENCE.vNext": DecisionContract(
        DecisionFamily.ECONOMIC_RELATIONSHIP,
        "decision-contract.vNext.1",
        "Judge whether the explicit directed or undirected relation proposition between two endpoints is evidenced.",
        "REL.EXISTENCE.vNext",
        "vNext.1",
        Primitive.NOUL,
        ("probability_yes",),
        STATE_CONTRACTS[DecisionFamily.ECONOMIC_RELATIONSHIP].version,
        "Probability remains primitive-specific uncertainty and is not canonical truth.",
        "relationship-existence.vNext.1; no implicit cutoff.",
        "Experimental judgment only; canonical admission is separately governed.",
        "OFFLINE_STRUCTURAL_VALIDATION_ONLY",
        tuple(
            item.requirement_id
            for item in STATE_CONTRACTS[DecisionFamily.ECONOMIC_RELATIONSHIP].requirements
        ),
    ),
}


QUESTION_SEMANTIC_FINGERPRINTS = {
    "CES.SUPPORT.vNext": "bdf8d25fce3fa66e5dd71e512085fcd81130109a792c7c7954681408f9c9f35b",
    "CES.SUPPORT.vNext.2": "cc8956ebafb3a13e15185d28b842b76041c84079c8192e342ea5489568b3c27e",
    "CES.SUPPORT_N.vNext": "1718c364c46611b606241c84056ca18515e6c3c9dae7140cb9831516ec676314",
    "CES.SUPPORT_SCORE.vNext": "259d21e39c36356e6bca83170a473939340a9a1864090930ab10a0e02bc1605a",
    "ENT.ALIGN.vNext": "6d6406a2fba11d83b3f2a48a53226f73a38cc348a41450b1eca05ade2a93d865",
    "ENT.MATCH_N.vNext": "490100cae910614c75bdc70dabd37531104a350a424d3691aa64fdb98730892e",
    "ENT.MATCH_SCORE.vNext": "20443d5bd749c8bf958d5a3df6b8d3a5215e12dd9767c8a1dd0ec73fee9af881",
    "REL.EXISTENCE.vNext": "6bf7741af63d21d6736c81ebb6240abcbe15ab3d097875506dbac220a0684508",
    "REL.TYPE.vNext": "86adf61d6297d185f09f4a316d8102340e5007ca22b9c89b316daa9b7238ddb8",
    "REL.TIME.vNext": "0147b19bc28347fad90b947aea748964f315eb2df86c8ecbc4d3602b74836025",
    "REL.CONTRADICTION.vNext": "cdef3e34fb807be837971f69ad1caa71dc217e6f5a0980f9a43c111af9654aa9",
    "CES.SUPPORT.vNext.wording-b": "b00481c397fe5576e4f3e579fc994e1c52e4a7aaf51b7115f778f9d6074adf8d",
    "REL.COMPOUND.vNext": "3ad2e1d73890b952ff6a77171680fdfd1ee37862b38573f2d1b8e7c1452568d6",
}
DECISION_CONTRACTS = {
    question_id: replace(
        contract, question_semantic_fingerprint=QUESTION_SEMANTIC_FINGERPRINTS[question_id]
    )
    for question_id, contract in DECISION_CONTRACTS.items()
}

_SEMANTIC_QUESTION_FIELDS = (
    "question_id",
    "version",
    "family",
    "primitive",
    "semantic_target",
    "instructions",
    "state_contract",
    "information_requirements",
    "uncertainty_semantics",
    "composition_semantics",
    "criteria",
)


def canonical_question_definition(definition: dict[str, Any]) -> str:
    """Serialize provider-visible question meaning with stable object-key order."""
    semantic = {key: definition.get(key) for key in _SEMANTIC_QUESTION_FIELDS}
    return json.dumps(semantic, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def question_semantic_fingerprint(definition: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_question_definition(definition).encode("utf-8")).hexdigest()


def contract_errors(contract: DecisionContract) -> list[str]:
    """Validate stable contract declarations without judging semantic truth."""
    errors: list[str] = []
    if not all(
        (
            contract.version,
            contract.semantic_target,
            contract.question_id,
            contract.question_version,
        )
    ):
        errors.append("CONTRACT_IDENTITY_INCOMPLETE")
    state_contract = STATE_CONTRACTS.get(contract.family)
    if state_contract is None or contract.state_contract_version != state_contract.version:
        errors.append("STATE_CONTRACT_VERSION_MISMATCH")
    elif contract.information_requirements != tuple(
        item.requirement_id for item in state_contract.requirements
    ):
        errors.append("INFORMATION_REQUIREMENTS_MISMATCH")
    if not contract.answer_space or len(set(contract.answer_space)) != len(contract.answer_space):
        errors.append("INVALID_ANSWER_SPACE")
    if len(contract.question_semantic_fingerprint) != 64:
        errors.append("QUESTION_SEMANTIC_FINGERPRINT_MISSING")
    if contract.primitive is Primitive.CHOICE and len(contract.answer_space) < 2:
        errors.append("INVALID_CHOICE_OPTIONS")
    if contract.primitive is Primitive.SCORE and len(contract.answer_space) < 2:
        errors.append("INVALID_SCORE_LEVELS")
    if contract.primitive is Primitive.NOUL and len(contract.answer_space) != 1:
        errors.append("INVALID_NOUL_PROPOSITION")
    if (
        not contract.uncertainty_semantics
        or not contract.composition_policy
        or not contract.authority_boundary
    ):
        errors.append("CONTRACT_BOUNDARY_INCOMPLETE")
    return errors


def validate_primitive_contract(primitive: Primitive, declaration: dict[str, Any]) -> list[str]:
    """Check answer-space declarations; all content remains untrusted data."""
    if primitive is Primitive.CHOICE:
        options = declaration.get("options")
        if not isinstance(options, list) or len(options) < 2:
            return ["INVALID_ANSWER_SPACE"]
        if declaration.get("mutually_exclusive") is not True:
            return ["CHOICE_EXCLUSIVITY_UNDECLARED"]
        if declaration.get("coverage") not in {
            "EXHAUSTIVE_WITH_OTHER",
            "EXHAUSTIVE_WITH_UNRESOLVED",
        }:
            return ["CHOICE_COVERAGE_UNDECLARED"]
        labels: list[str] = []
        for option in options:
            if not isinstance(option, dict) or not isinstance(option.get("id"), str):
                return ["INVALID_ANSWER_SPACE"]
            if not isinstance(option.get("meaning"), str) or not option["meaning"].strip():
                return ["OPTION_MEANING_MISSING"]
            labels.append(option["id"])
        if len(labels) != len(set(labels)):
            return ["DUPLICATE_OPTION"]
        return []
    if primitive is Primitive.SCORE:
        levels = declaration.get("levels")
        if not isinstance(levels, list) or len(levels) < 2:
            return ["INVALID_SCORE_LEVELS"]
        ordinals = [item.get("ordinal") for item in levels if isinstance(item, dict)]
        if len(ordinals) != len(levels) or any(
            not isinstance(value, int) or isinstance(value, bool) for value in ordinals
        ):
            return ["INVALID_SCORE_ORDER"]
        if ordinals != list(range(len(ordinals))):
            return ["INVALID_SCORE_ORDER"]
        if any(
            not isinstance(item.get("meaning"), str) or not item["meaning"].strip()
            for item in levels
        ):
            return ["SCORE_LEVEL_MEANING_MISSING"]
        return []
    if primitive is Primitive.NOUL:
        proposition = declaration.get("proposition")
        args = declaration.get("required_arguments")
        if (
            not isinstance(proposition, str)
            or not proposition.strip()
            or not isinstance(args, list)
            or not args
        ):
            return ["NOUL_PROPOSITION_ARGUMENT_MISSING"]
        return []
    return ["INVALID_PRIMITIVE_CONTRACT"]


def validate_required_arguments(state: dict[str, Any], declaration: dict[str, Any]) -> list[str]:
    """Ensure every declared Noul proposition argument is present and non-empty."""
    args = declaration.get("required_arguments")
    if not isinstance(args, list) or not args or any(not isinstance(path, str) for path in args):
        return ["NOUL_PROPOSITION_ARGUMENT_MISSING"]
    if any(missingness(path_value(state, path)) is not Missingness.PRESENT for path in args):
        return ["NOUL_PROPOSITION_ARGUMENT_MISSING"]
    return []


def validate_question_binding(
    contract_id: str,
    definition: dict[str, Any],
    state: dict[str, Any],
) -> list[str]:
    """Bind provider-visible question semantics to the registered contract."""
    contract = DECISION_CONTRACTS.get(contract_id)
    if contract is None:
        return ["INVALID_DECISION_CONTRACT"]
    errors: list[str] = []
    if question_semantic_fingerprint(definition) != contract.question_semantic_fingerprint:
        errors.append("QUESTION_SEMANTIC_FINGERPRINT_MISMATCH")
    if definition.get("question_id") != contract.question_id:
        errors.append("QUESTION_ID_MISMATCH")
    if definition.get("version") != contract.question_version:
        errors.append("QUESTION_VERSION_MISMATCH")
    if definition.get("family") != contract.family.value:
        errors.append("DECISION_FAMILY_MISMATCH")
    if definition.get("primitive") != contract.primitive.value:
        errors.append("PRIMITIVE_MISMATCH")
    if definition.get("semantic_target") != contract.semantic_target:
        errors.append("SEMANTIC_TARGET_MISMATCH")
    criteria = definition.get("criteria")
    if not isinstance(criteria, dict):
        return [*errors, "INVALID_PRIMITIVE_CONTRACT"]
    errors.extend(validate_primitive_contract(contract.primitive, criteria))
    if contract.primitive is Primitive.CHOICE:
        options = criteria.get("options")
        if isinstance(options, list):
            option_ids = tuple(item.get("id") for item in options if isinstance(item, dict))
            if option_ids != contract.answer_space:
                errors.append("ANSWER_SPACE_CONTRACT_MISMATCH")
    if contract.primitive is Primitive.NOUL:
        if criteria.get("proposition") != contract.semantic_target:
            errors.append("NOUL_PROPOSITION_MISMATCH")
        state_contract = STATE_CONTRACTS[contract.family]
        declared_paths = {item.path for item in state_contract.requirements}
        required_arguments = criteria.get("required_arguments")
        if isinstance(required_arguments, list):
            uncovered = [
                path
                for path in required_arguments
                if not isinstance(path, str)
                or not any(
                    path == declared
                    or declared.startswith(path + ".")
                    or path.startswith(declared + ".")
                    for declared in declared_paths
                )
            ]
            if uncovered:
                errors.append("NOUL_ARGUMENT_NOT_IN_STATE_CONTRACT")
        errors.extend(validate_required_arguments(state, criteria))
    return errors


def validate_grammar_vnext(document: dict[str, Any]) -> list[str]:
    """Validate all V-next question decisions and their declared primitives."""
    errors: list[str] = []
    questions = document.get("questions")
    if document.get("version") != "vNext.1" or not isinstance(questions, list):
        return ["INVALID_GRAMMAR_VERSION_OR_QUESTIONS"]
    allowed_decisions = {
        "KEEP",
        "REWRITE",
        "SPLIT",
        "REPLACE",
        "RETIRE",
        "EXPERIMENTAL_COMPARATOR_ONLY",
    }
    seen: set[str] = set()
    for item in questions:
        if not isinstance(item, dict):
            errors.append("INVALID_QUESTION_ENTRY")
            continue
        question_id = item.get("question_id")
        if not isinstance(question_id, str) or not question_id or question_id in seen:
            errors.append("INVALID_OR_DUPLICATE_QUESTION_ID")
        else:
            seen.add(question_id)
        if item.get("decision") not in allowed_decisions:
            errors.append(f"INVALID_GRAMMAR_DECISION:{question_id}")
        for field in (
            "semantic_target",
            "instructions",
            "criteria",
            "information_requirements",
            "state_contract",
            "uncertainty_semantics",
            "composition_semantics",
            "evaluation_status",
        ):
            if not item.get(field):
                errors.append(f"QUESTION_FIELD_MISSING:{question_id}:{field}")
        family = item.get("family")
        if family in {member.value for member in DecisionFamily}:
            state_contract = STATE_CONTRACTS[DecisionFamily(family)]
            expected_requirements = [
                requirement.requirement_id for requirement in state_contract.requirements
            ]
            if item.get("state_contract") != state_contract.version:
                errors.append(f"STATE_CONTRACT_VERSION_MISMATCH:{question_id}")
            if item.get("information_requirements") != expected_requirements:
                errors.append(f"INFORMATION_REQUIREMENTS_MISMATCH:{question_id}")
        else:
            errors.append(f"INVALID_DECISION_FAMILY:{question_id}")
        raw_primitive = item.get("primitive")
        if not isinstance(raw_primitive, str):
            errors.append(f"INVALID_PRIMITIVE:{question_id}")
            continue
        try:
            primitive = Primitive(raw_primitive)
        except ValueError:
            errors.append(f"INVALID_PRIMITIVE:{question_id}")
            continue
        errors.extend(
            f"{question_id}:{error}"
            for error in validate_primitive_contract(primitive, item.get("criteria", {}))
        )
        expected_fingerprint = QUESTION_SEMANTIC_FINGERPRINTS.get(question_id)
        if expected_fingerprint is None:
            errors.append(f"QUESTION_SEMANTIC_FINGERPRINT_MISSING:{question_id}")
        elif question_semantic_fingerprint(item) != expected_fingerprint:
            errors.append(f"QUESTION_SEMANTIC_FINGERPRINT_MISMATCH:{question_id}")
        registered = DECISION_CONTRACTS.get(question_id)
        if (
            registered is not None
            and registered.question_semantic_fingerprint != expected_fingerprint
        ):
            errors.append(f"CONTRACT_FINGERPRINT_REGISTRY_MISMATCH:{question_id}")
    if len(questions) != 12:
        errors.append("EXPECTED_12_AUDITED_QUESTIONS")
    return errors


def deterministic_entity_identifier_result(state: dict[str, Any]) -> str | None:
    """Use only verified, checksum-valid LEIs under the contract's GLEIF rule."""
    entities = state.get("entities")
    if not isinstance(entities, dict):
        return None
    first = entities.get("a")
    second = entities.get("b")
    if not isinstance(first, dict) or not isinstance(second, dict):
        return None
    first_id = first.get("canonical_identifier")
    second_id = second.get("canonical_identifier")
    if not isinstance(first_id, dict) or not isinstance(second_id, dict):
        return None
    if not _validated_gleif_lei(first_id) or not _validated_gleif_lei(second_id):
        return None
    if first_id["value"] == second_id["value"]:
        return "SAME_LEGAL_ENTITY"
    return "DISTINCT_ENTITY"


def _validated_gleif_lei(identifier: dict[str, Any]) -> bool:
    """Validate the LEI namespace declaration and ISO 17442 check digits."""
    value = identifier.get("value")
    if (
        identifier.get("scheme") != "LEI"
        or identifier.get("authority") != "GLEIF"
        or identifier.get("validation_status") != "VERIFIED"
        or not isinstance(value, str)
        or len(value) != 20
        or not value.isascii()
        or not value.isalnum()
        or not value.isupper()
    ):
        return False
    expanded = "".join(str(ord(char) - 55) if char.isalpha() else char for char in value)
    return int(expanded) % 97 == 1


def missingness(value: Any) -> Missingness:
    """Classify explicit sentinels without coercing missingness to false."""
    if value is _ABSENT:
        return Missingness.ABSENT
    if value is None or value == "" or value == [] or value == {}:
        return Missingness.EMPTY
    if isinstance(value, dict) and value.get("status") in {
        Missingness.UNKNOWN.value,
        Missingness.UNAVAILABLE.value,
        Missingness.NOT_APPLICABLE.value,
    }:
        return Missingness(value["status"])
    return Missingness.PRESENT


class _Absent:
    pass


_ABSENT = _Absent()


def path_value(root: Any, path: str) -> Any:
    """Resolve a simple dotted path; wildcard paths return matching values."""
    pieces = path.split(".")
    values = [root]
    wildcard = False
    wildcard_found = False
    for piece in pieces:
        if piece.endswith("[*]"):
            wildcard = True
            key = piece[:-3]
            next_values: list[Any] = []
            for value in values:
                child = value.get(key, _ABSENT) if isinstance(value, dict) else _ABSENT
                if isinstance(child, list):
                    wildcard_found = True
                    next_values.extend(child)
            values = next_values
        else:
            values = [
                value.get(piece, _ABSENT) if isinstance(value, dict) else _ABSENT
                for value in values
            ]
    if wildcard:
        return values if values else ([] if wildcard_found else _ABSENT)
    return values[0] if values else _ABSENT
