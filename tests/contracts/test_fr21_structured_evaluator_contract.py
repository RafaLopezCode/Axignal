"""FR-21 provider-neutral structured evaluator contract."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = ROOT / "application" / "economic_discovery" / "contracts.py"


def test_structured_evaluator_contract_has_explicit_uncertainty_availability() -> None:
    source = CONTRACTS.read_text(encoding="utf-8")

    assert "class DistributionAvailability" in source
    assert "AVAILABLE" in source
    assert "UNAVAILABLE" in source
    assert "class ConfidenceSemantics" in source
    assert "PROVIDER_DEFINED" in source
    assert "unavailable provider distribution must remain empty" in source
    assert "confidence requires provider-defined semantics" in source


def test_selected_choice_does_not_imply_one_hot_distribution() -> None:
    source = CONTRACTS.read_text(encoding="utf-8")

    assert "selected_option" in source
    assert "distribution: tuple[tuple[str, float], ...] = ()" in source
    assert "selected option must be present in available distribution" in source
    assert "((self.selected_option, 1.0)," not in source
    assert "1.0 if" not in source


def test_contract_exposes_replay_and_capability_profile() -> None:
    source = CONTRACTS.read_text(encoding="utf-8")

    assert "class EvaluatorCapabilityProfile" in source
    assert "replay_reference_supported" in source
    assert "replay_reference: str" in source
    assert "structured evaluator must provide a replay reference" in source
    assert "capability profile mismatch" in source


def test_boundary_validates_request_and_judgment_provenance() -> None:
    source = CONTRACTS.read_text(encoding="utf-8")

    assert "class StructuredEvaluationRequest" in source
    assert "structured evaluator decision contract mismatch" in source
    assert "structured evaluator state fingerprint mismatch" in source
    assert "structured evaluator question fingerprint mismatch" in source
    assert "structured evaluator choice-space fingerprint mismatch" in source
    assert "selected option is outside choice space" in source
    assert "distribution is outside choice space" in source


def test_core_contract_contains_no_provider_specific_names() -> None:
    source = CONTRACTS.read_text(encoding="utf-8").lower()

    for provider_name in ("jev", "openai", "luna", "typesafe", "decisions"):
        assert provider_name not in source
