"""V-next failure classes with explicit attribution confidence."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class FailureClass(StrEnum):
    INPUT_STATE_ERROR = "INPUT_STATE_ERROR"
    MISSING_INFORMATION = "MISSING_INFORMATION"
    QUESTION_DESIGN_ERROR = "QUESTION_DESIGN_ERROR"
    PRIMITIVE_SELECTION_ERROR = "PRIMITIVE_SELECTION_ERROR"
    OPTION_SPACE_ERROR = "OPTION_SPACE_ERROR"
    MODEL_JUDGMENT_ERROR = "MODEL_JUDGMENT_ERROR"
    COMPOSITION_ERROR = "COMPOSITION_ERROR"
    POLICY_ERROR = "POLICY_ERROR"
    SDK_ERROR = "SDK_ERROR"
    SERVICE_ERROR = "SERVICE_ERROR"
    NETWORK_ERROR = "NETWORK_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    MODEL_VERSION_DRIFT = "MODEL_VERSION_DRIFT"
    CALIBRATION_ERROR = "CALIBRATION_ERROR"
    EVALUATION_DESIGN_ERROR = "EVALUATION_DESIGN_ERROR"
    GOLDEN_LABEL_ERROR = "GOLDEN_LABEL_ERROR"


class AttributionBasis(StrEnum):
    DETERMINISTICALLY_DETECTED = "DETERMINISTICALLY_DETECTED"
    HUMAN_ADJUDICATED = "HUMAN_ADJUDICATED"
    EXPERIMENTALLY_INFERRED = "EXPERIMENTALLY_INFERRED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class FailureAttribution:
    failure_class: FailureClass
    basis: AttributionBasis
    evidence_ref: str | None = None


def unresolved_attribution() -> FailureAttribution:
    return FailureAttribution(FailureClass.EVALUATION_DESIGN_ERROR, AttributionBasis.UNKNOWN)
